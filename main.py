"""
Harvest-Sequencing Optimizer -- run the whole pipeline end to end.

    python main.py

Runs all five stages in order and writes every output file. Each stage also
runs standalone (python parse.py, python graph.py, ...) if you only want to
work on your own part.

FIRST Global Challenge 2026 -- reducing wheat-fire risk in the Bekaa Valley
by choosing the ORDER in which neighbouring fields get harvested.
"""

import math
import time

from exact import exact_fire_only
from simulate import simulate_season
from parse import load_fields, ANCHOR_FIELD, STUDY_RADIUS_KM
from graph import (
    ADJACENCY_THRESHOLD_M,
    build_adjacency_graph,
    distance_matrix_km,
    plot_adjacency_map,
    print_graph_report,
    print_threshold_sensitivity,
)
from simulate import HARVEST_RATE_HA_PER_DAY, print_harvest_schedule, print_day_by_day
from optimize import W1_FIRE, run_all, print_comparison, print_w2_sweep
from sensitivity import (
    RIVAL_THRESHOLDS_M,
    greedy_robust,
    plot_sensitivity,
    print_cross_matrix,
    print_inspection_list,
    print_recommendation,
    print_world_summary,
    score_under,
)
from animate import make_animation, save_key_frames

# The travel weight we settled on after looking at the trade-off curve in
# Stage 4. w2=5 is the setting that beats the naive baseline on BOTH objectives
# IF the 175 m adjacency rule is correct. (w2=0.5 is so small next to the
# hectare numbers that it behaves almost identically to fire-only.)
W2_CHOSEN = 5.0


def banner(text):
    print()
    print("#" * 92)
    print(f"#  {text}")
    print("#" * 92)


def main():
    t0 = time.time()

    print("HARVEST-SEQUENCING OPTIMIZER -- Bekaa Valley, Lebanon")
    print("FIRST Global Challenge 2026 prototype")
    print()
    print("Settings in force for this run:")
    print(f"  study area          : fields within {STUDY_RADIUS_KM} km of "
          f"field '{ANCHOR_FIELD}'")
    print(f"  adjacency threshold : {ADJACENCY_THRESHOLD_M:.0f} m between boundaries")
    print(f"  harvester rate      : {HARVEST_RATE_HA_PER_DAY:.0f} ha/day")
    print(f"  balance weights     : w1={W1_FIRE} (fire), w2={W2_CHOSEN} (travel)")

    # ---------------- STAGE 1 ----------------
    banner("STAGE 1 -- parse the KML, project to metres, filter the study area")
    fields = load_fields(verbose=True)

    # ---------------- STAGE 2 ----------------
    banner("STAGE 2 -- adjacency graph and travel-distance matrix")
    G = build_adjacency_graph(fields)
    matrix, index = distance_matrix_km(fields)
    print_graph_report(G, fields, matrix, index)
    print_threshold_sensitivity(fields)
    plot_adjacency_map(fields, G)

    # ---------------- STAGE 3 ----------------
    banner("STAGE 3 -- season simulation")
    print_harvest_schedule(G)

    # ---------------- STAGE 4 ----------------
    banner("STAGE 4 -- the three optimizers")
    naive, fire, balanced = run_all(G, matrix, index, w1=W1_FIRE, w2=W2_CHOSEN)
    print_comparison(naive, fire, balanced)
    print_w2_sweep(G, matrix, index, naive, w1=W1_FIRE)

    # Show the day-by-day table for the two ends of the comparison, so the
    # numbers in the table above can be traced back to individual days.
    print_day_by_day(naive, G)
    print_day_by_day(balanced, G)

    # ---------------- ROBUSTNESS ----------------
    banner("ROBUSTNESS -- is the recommendation safe if our 175 m guess is wrong?")
    print("The Stage 4 numbers above are CONDITIONAL on the 175 m adjacency rule.")
    print("We could not settle 100 m vs 175 m from satellite imagery, so instead of")
    print("guessing we test every schedule in BOTH worlds. See sensitivity.py.")
    print()
    print_world_summary(fields)
    candidates, naive_order = print_cross_matrix(fields)
    robust_order = print_recommendation(fields, candidates, naive_order)
    print_inspection_list(fields)
    plot_sensitivity(fields)

    # ---------------- EXACT OPTIMUM (Phase 2) ----------------
    banner("EXACT OPTIMUM -- the provably best order (exact.py)")
    opt_cost, opt_order = exact_fire_only(G)
    optimal = simulate_season(opt_order, G, matrix, index,
                              label="(c) exact optimum (Phase 2)")
    print(f"  best of all {math.factorial(len(G.nodes)):,} orders: "
          f"{opt_cost:.1f} ha-days  "
          f"({(naive.fire_risk_score - opt_cost) / naive.fire_risk_score * 100:+.1f}% vs naive)")
    print(f"  order: {' -> '.join(opt_order)}")
    print("  (run `python exact.py` for the brute-force proof)")

    # ---------------- STAGE 5 ----------------
    banner("STAGE 5 -- the three-panel demo animation")
    naive.label, fire.label = "(a) naive: largest field first", "(b) greedy (Phase 1)"
    make_animation([naive, fire, optimal], G, fields)
    save_key_frames([naive, fire, optimal], G, fields)

    # ---------------- WRAP UP ----------------
    banner("DONE")
    print("Output files:")
    print("  map_adjacency.png          -- Stage 2 map, check against Google Earth")
    print("  harvest_comparison.gif     -- Stage 5, the competition video centrepiece")
    print("  frame_dayNN.png            -- stills of the three panels, for the poster")
    print("  sensitivity_thresholds.png -- how the benefit depends on the 100/175 m rule")
    print()

    # ---- the claim we can make WITHOUT resolving the adjacency threshold.
    robust_pcts = []
    for t in RIVAL_THRESHOLDS_M:
        r = score_under(robust_order, fields, t)
        b = score_under(naive_order, fields, t)
        robust_pcts.append((b.fire_risk_score - r.fire_risk_score)
                           / b.fire_risk_score * 100.0)

    print("HEADLINE RESULT -- what we can claim without further fieldwork")
    print("-" * 88)
    print(f"  Robust schedule: {' -> '.join(robust_order)}")
    print(f"  Cuts season-long fire exposure by {min(robust_pcts):.1f}% "
          f"versus the naive largest-first")
    print(f"  baseline, and does so whether the true adjacency rule is "
          f"{RIVAL_THRESHOLDS_M[0]:.0f} m or {RIVAL_THRESHOLDS_M[1]:.0f} m.")
    print("  Purely by changing the ORDER of the harvest. No new equipment.")
    print()

    # ---- the bigger claim, and exactly what it costs to earn it.
    drop = (naive.fire_risk_score - balanced.fire_risk_score) / naive.fire_risk_score * 100
    km_saved = naive.travel_cost_km - balanced.travel_cost_km
    print("CONDITIONAL RESULT -- only valid if the 175 m rule is confirmed")
    print("-" * 88)
    print(f"  naive baseline           {naive.fire_risk_score:>8.1f} ha-days   "
          f"{naive.travel_cost_km:>6.2f} km")
    print(f"  fire-only greedy         {fire.fire_risk_score:>8.1f} ha-days   "
          f"{fire.travel_cost_km:>6.2f} km")
    print(f"  balanced (w2={W2_CHOSEN:g})          {balanced.fire_risk_score:>8.1f} ha-days   "
          f"{balanced.travel_cost_km:>6.2f} km")
    print(f"  => {drop:.1f}% less fire exposure AND {km_saved:.1f} km less driving.")
    print()
    print("  WARNING: that same balanced schedule scores -2.9% -- WORSE than doing")
    print("  nothing -- if the 100 m rule turns out to be the correct one. Do not")
    print("  quote the conditional number without confirming the adjacency rule first.")
    print()
    print("  To confirm it, inspect the 114-121 m gaps between field 'nte' and")
    print("  fields 4/5/6 in satellite imagery. If dry vegetation bridges them, the")
    print("  175 m rule holds and the conditional result becomes the headline.")
    print()
    print(f"(total runtime {time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
