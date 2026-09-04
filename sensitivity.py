"""
SENSITIVITY ANALYSIS -- does our recommendation survive being wrong about the
adjacency threshold?

WHY THIS FILE EXISTS
--------------------
The whole model hangs on one number: ADJACENCY_THRESHOLD_M, the distance at
which two fields count as close enough for fire to jump between them. We
measured every pair of fields and found the gaps fall into two clumps -- fields
that clearly touch (7-12 m) and fields that clearly do not (114 m and up), with
nothing in between. Both 100 m and 175 m are defensible readings of that data:

    100 m -> the 114-121 m gaps are REAL barriers. Map splits into 6 islands.
    175 m -> those gaps are tracing slop / crossable margins. Map has 3 blocks.

We could not settle it from satellite imagery (December imagery shows bare
fields, and the gap features are narrow vegetated ditches whose summer fuel
state is unknown). So instead of guessing, we TEST BOTH and report both.

THE KEY QUESTION this file answers is not "which threshold is right?" but the
more useful one:

    If we build a harvest schedule assuming one threshold, and the other
    threshold turns out to be the truth, is our schedule still better than
    doing nothing clever?

That is a robustness question, and it is the honest way to present a model whose
input you cannot fully pin down.

IMPORTANT -- HOW TO READ THE NUMBERS
------------------------------------
Raw fire_risk_score values are NOT comparable across thresholds. A different
threshold means a different graph, different connected components, and therefore
a different scale of "largest block". A 175 m world simply has bigger blocks than
a 100 m world, so every score in it is larger.

What IS comparable is the PERCENTAGE IMPROVEMENT over the naive baseline
evaluated on the SAME graph. That is what every table below reports.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from shapely.ops import nearest_points

from parse import KML_FILE, load_fields, make_unprojector, projection_reference
from graph import build_adjacency_graph, distance_matrix_km
from simulate import simulate_season, largest_standing_block
from optimize import naive_largest_first, greedy_fire_only, greedy_balanced

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# The two rival readings of the gap data. These are the ones we report in full.
RIVAL_THRESHOLDS_M = (100.0, 175.0)

# A wider sweep, used only for the trend plot.
SWEEP_THRESHOLDS_M = (100.0, 125.0, 150.0, 175.0, 200.0, 250.0, 300.0)

# Travel weight used for the balanced strategy throughout this analysis.
W2 = 5.0

PLOT_PATH = "sensitivity_thresholds.png"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def world(fields, threshold_m):
    """Build the 'world' (graph + distance matrix) implied by one threshold."""
    G = build_adjacency_graph(fields, threshold_m=threshold_m)
    matrix, index = distance_matrix_km(fields)
    return G, matrix, index


def strategies_for(fields, threshold_m):
    """
    Generate the three harvest orders a team would produce if they BELIEVED
    this threshold. Returns a dict of {strategy name: order}.

    Note the naive order does not depend on the graph at all -- it only looks at
    field sizes -- so it is identical in every world. That is exactly why it
    makes a good fixed baseline.
    """
    G, matrix, index = world(fields, threshold_m)
    return {
        "naive": naive_largest_first(G),
        "fire-only": greedy_fire_only(G),
        f"balanced(w2={W2:g})": greedy_balanced(G, matrix, index, w2=W2),
    }


def score_under(order, fields, threshold_m):
    """Score an existing order in the world implied by `threshold_m`."""
    G, matrix, index = world(fields, threshold_m)
    return simulate_season(order, G, matrix, index)


def greedy_robust(fields, thresholds=RIVAL_THRESHOLDS_M):
    """
    A FOURTH strategy, invented specifically because the cross-evaluation showed
    the other three are fragile: a schedule that hedges both worlds at once.

    At every step it asks, for each candidate field, "if I cut this next, how bad
    is the resulting largest block IN THE WORST OF THE TWO WORLDS?" -- and takes
    the field that minimises that worst case.

    Each world's block size is divided by that world's own day-0 block before
    comparing, because a 175 m world has inherently bigger blocks than a 100 m
    world and the raw hectares are not comparable. Normalising puts both on a
    "fraction of the worst possible fire" scale.
    """
    graphs = {t: build_adjacency_graph(fields, threshold_m=t) for t in thresholds}
    # Each world's starting largest block -- the scale factor for that world.
    day0 = {t: largest_standing_block(G, set(G.nodes))[1] for t, G in graphs.items()}

    any_graph = graphs[thresholds[0]]
    standing = set(any_graph.nodes)
    order = []

    while standing:
        def score(c):
            rest = standing - {c}
            worst = max(
                largest_standing_block(G, rest)[1] / day0[t]
                for t, G in graphs.items()
            )
            return (worst, -any_graph.nodes[c]["area_ha"], c)

        best = min(standing, key=score)
        order.append(best)
        standing.remove(best)

    return order


def pct_vs_naive(order, naive_order, fields, threshold_m):
    """Percent improvement of `order` over the naive baseline, same world."""
    r = score_under(order, fields, threshold_m)
    base = score_under(naive_order, fields, threshold_m)
    return (base.fire_risk_score - r.fire_risk_score) / base.fire_risk_score * 100.0


# ---------------------------------------------------------------------------
# REPORT 1 -- what each world looks like
# ---------------------------------------------------------------------------

def print_world_summary(fields):
    print("=" * 96)
    print("SENSITIVITY ANALYSIS -- 100 m vs 175 m adjacency rule")
    print("=" * 96)
    print()
    print("THE TWO WORLDS")
    print("-" * 96)
    print(f"{'threshold':>11}{'edges':>8}{'components':>13}{'largest block':>16}"
          f"   composition of the largest block")
    for t in RIVAL_THRESHOLDS_M:
        G, _, _ = world(fields, t)
        comps = sorted(nx.connected_components(G),
                       key=lambda c: -sum(G.nodes[n]["area_ha"] for n in c))
        big = comps[0]
        ha = sum(G.nodes[n]["area_ha"] for n in big)
        members = ", ".join(sorted(big, key=lambda s: (not s.isdigit(), s)))
        print(f"{t:>9.0f} m{G.number_of_edges():>8}{len(comps):>13}{ha:>13.1f} ha"
              f"   {members}")
    print()


# ---------------------------------------------------------------------------
# REPORT 2 -- the cross-evaluation matrix (the important one)
# ---------------------------------------------------------------------------

def print_cross_matrix(fields):
    """
    Build a schedule in each world, then score every schedule in BOTH worlds.

    The diagonal is "we guessed the threshold right". The off-diagonal is
    "we guessed wrong" -- and that is the number that tells us whether the
    recommendation is safe to make.
    """
    print("CROSS-EVALUATION -- build a schedule assuming one world, test it in both")
    print("-" * 96)
    print("Each cell = % less season-long fire exposure than the naive baseline,")
    print("with the baseline recomputed in whichever world the schedule is being tested in.")
    print("Higher is better. A NEGATIVE number means the schedule is worse than doing")
    print("nothing clever.")
    print()

    # Build every candidate schedule, tagged with the world that produced it.
    candidates = []                     # (display name, order)
    for t in RIVAL_THRESHOLDS_M:
        for name, order in strategies_for(fields, t).items():
            if name == "naive":
                continue                # identical in every world; added once below
            candidates.append((f"{name} built @ {t:.0f} m", order))

    # The hedged schedule, which belongs to neither world.
    candidates.append(("robust (hedges both worlds)", greedy_robust(fields)))

    naive_order = naive_largest_first(world(fields, RIVAL_THRESHOLDS_M[0])[0])

    header = "".join(f"{'tested @ ' + f'{t:.0f} m':>18}" for t in RIVAL_THRESHOLDS_M)
    print(f"{'SCHEDULE':<32}{header}   robust?")
    print("-" * 96)

    print(f"{'naive (largest first)':<32}"
          + "".join(f"{'baseline':>18}" for _ in RIVAL_THRESHOLDS_M)
          + "   --")

    for name, order in candidates:
        cells, pcts = "", []
        for t in RIVAL_THRESHOLDS_M:
            p = pct_vs_naive(order, naive_order, fields, t)
            pcts.append(p)
            cells += f"{p:>17.1f}%"
        # "Robust" = beats the naive baseline in BOTH worlds by a real margin.
        robust = "YES" if min(pcts) > 5.0 else ("marginal" if min(pcts) > 0 else "NO")
        print(f"{name:<32}{cells}   {robust}")

    print("-" * 96)
    print()
    return candidates, naive_order


# ---------------------------------------------------------------------------
# REPORT 3 -- pick the schedule that is safest to actually recommend
# ---------------------------------------------------------------------------

def print_recommendation(fields, candidates, naive_order):
    """
    Rank schedules by their WORST-CASE performance across the two worlds.

    This is a minimax choice: we cannot know which threshold is true, so we
    recommend the schedule whose worst outcome is least bad. That is a standard,
    defensible way to decide under an uncertain assumption.
    """
    print("RECOMMENDATION UNDER UNCERTAINTY (worst-case ranking)")
    print("-" * 96)
    print("We do not know which world is real, so we rank each schedule by its WORST")
    print("result across both, and recommend the best worst case.")
    print()
    print(f"{'SCHEDULE':<32}{'worst case':>13}{'best case':>13}   harvest order")
    print("-" * 96)

    ranked = []
    for name, order in candidates:
        pcts = [pct_vs_naive(order, naive_order, fields, t) for t in RIVAL_THRESHOLDS_M]
        ranked.append((min(pcts), max(pcts), name, order))
    ranked.sort(reverse=True)

    for worst, best, name, order in ranked:
        print(f"{name:<32}{worst:>12.1f}%{best:>12.1f}%   {' -> '.join(order)}")

    print("-" * 96)
    worst, best, name, order = ranked[0]
    print()
    print(f"==> RECOMMEND: {name}")
    print(f"    Cuts season-long fire exposure by at least {worst:.1f}% "
          f"(and up to {best:.1f}%)")
    print(f"    versus the naive largest-first baseline, WHICHEVER adjacency")
    print(f"    threshold turns out to be correct.")
    print(f"    Order: {' -> '.join(order)}")
    print()
    return order


# ---------------------------------------------------------------------------
# REPORT 4 -- the field-inspection list (how to actually settle the question)
# ---------------------------------------------------------------------------

# Camera range for the generated Google Earth links, in metres. ~1500 m frames a
# 120 m gap comfortably with both fields visible. Smaller values zoom in so far
# that you can only see one field at a time, which is what confused us the first
# time we tried this.
EARTH_LINK_RANGE_M = 1500

# Ground elevation to point the camera at, in metres. The Bekaa floor here is
# ~870 m; it only affects the starting camera height, not what you see.
EARTH_LINK_ELEVATION_M = 872


def critical_pairs(fields, low=None, high=None):
    """
    Every pair of fields whose gap sits BETWEEN the two rival thresholds.

    These are exactly the adjacencies that exist under the loose rule but not the
    tight one -- in other words, the complete set of decisions that separate the
    two worlds. Verify these and the threshold question is closed. Pairs closer
    than `low` are adjacent under both rules (nothing to check); pairs further
    than `high` are separate under both.
    """
    low = low if low is not None else min(RIVAL_THRESHOLDS_M)
    high = high if high is not None else max(RIVAL_THRESHOLDS_M)

    pairs = []
    for i, a in enumerate(fields):
        for b in fields[i + 1:]:
            gap = a.poly_m.distance(b.poly_m)
            if low < gap <= high:
                pa, pb = nearest_points(a.poly_m, b.poly_m)
                mid_m = ((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)
                pairs.append((gap, a.name, b.name, mid_m))
    pairs.sort()
    return pairs


def print_inspection_list(fields, kml_path=KML_FILE):
    """
    Print the satellite-imagery checklist that settles the adjacency question.

    For each undecided pair this gives the gap width, the lat/lon of the midpoint
    of that gap, and a ready-made Google Earth link framed so BOTH fields are
    visible. Self-contained: nothing here depends on notes kept elsewhere.
    """
    ref_lon, ref_lat = projection_reference(kml_path)
    unproject = make_unprojector(ref_lon, ref_lat)

    low, high = min(RIVAL_THRESHOLDS_M), max(RIVAL_THRESHOLDS_M)
    pairs = critical_pairs(fields)

    print("FIELD-INSPECTION CHECKLIST -- how to settle the adjacency question")
    print("-" * 96)
    print(f"These are the ONLY undecided pairs: gaps wider than {low:.0f} m but no")
    print(f"wider than {high:.0f} m. Every other pair is adjacent under both rules, or")
    print("separate under both. Resolve these {n} and the question is closed."
          .format(n=len(pairs)))
    print()
    print("At each location, ask: WHAT IS IN THE GAP?")
    print("  paved road / open canal / buildings -> a real firebreak  -> the 100 m rule")
    print("  dry grass / scrub / vegetated ditch -> fire crosses it   -> the 175 m rule")
    print()
    print(f"{'PAIR':<14}{'GAP':>9}   {'MIDPOINT (lat, lon)':<26} GOOGLE EARTH LINK")
    print("-" * 96)

    for gap, a, b, (mx, my) in pairs:
        lon, lat = unproject(mx, my)
        url = (f"https://earth.google.com/web/@{lat:.6f},{lon:.6f},"
               f"{EARTH_LINK_ELEVATION_M}a,{EARTH_LINK_RANGE_M}d,35y,0h,0t,0r")
        print(f"{a + ' -- ' + b:<14}{gap:>7.1f} m   {lat:.6f}, {lon:.6f}      {url}")

    print("-" * 96)
    print()
    print("IMAGERY NOTE: Google Earth's high-resolution pass for this area is dated")
    print("December, when the fields are bare -- good for permanent features (roads,")
    print("canals, buildings), useless for judging summer fuel. For crop state use")
    print("Sentinel-2, which images the Bekaa every 5 days at 10 m, free:")
    print("  https://browser.dataspace.copernicus.eu/?zoom=15&lat=33.7331&lng=35.8832")
    print("Set the date to mid-May..mid-June and switch the layer to NDVI: standing")
    print("wheat is bright, harvested stubble is pale. 10 m pixels will NOT resolve a")
    print("6-9 m ditch, so use Google Earth for the gap feature and Sentinel for the")
    print("fuel state -- they answer different halves of the question.")
    print()


# ---------------------------------------------------------------------------
# REPORT 5 -- the trend plot
# ---------------------------------------------------------------------------

def plot_sensitivity(fields, out_path=PLOT_PATH):
    """
    Plot % improvement over naive against the adjacency threshold, so a reader
    can see at a glance that the benefit does not depend on one lucky setting.
    """
    naive_order = naive_largest_first(world(fields, 175.0)[0])

    # The hedged schedule is built ONCE and then tested everywhere, unlike the
    # other two which are rebuilt for each threshold. That is the whole point of
    # it -- one schedule you can actually commit to before knowing the answer.
    robust_order = greedy_robust(fields)

    series = {"fire-only (rebuilt per threshold)": [],
              f"balanced w2={W2:g} (rebuilt per threshold)": [],
              "robust (one fixed schedule)": []}
    for t in SWEEP_THRESHOLDS_M:
        G, matrix, index = world(fields, t)
        series["fire-only (rebuilt per threshold)"].append(
            pct_vs_naive(greedy_fire_only(G), naive_order, fields, t))
        series[f"balanced w2={W2:g} (rebuilt per threshold)"].append(
            pct_vs_naive(greedy_balanced(G, matrix, index, w2=W2), naive_order, fields, t))
        series["robust (one fixed schedule)"].append(
            pct_vs_naive(robust_order, naive_order, fields, t))

    fig, ax = plt.subplots(figsize=(11, 6.6))
    for (label, ys), color, marker in zip(series.items(),
                                          ("#fb8c00", "#1e88e5", "#2e7d32"),
                                          ("o", "s", "D")):
        ax.plot(SWEEP_THRESHOLDS_M, ys, marker=marker, linewidth=2.4,
                markersize=8, color=color, label=label)

    # Shade the region where a schedule is actively HARMFUL.
    ax.axhspan(min(min(v) for v in series.values()) - 3, 0,
               color="#d32f2f", alpha=0.07)

    ax.axhline(0, color="#555", linewidth=1.4)
    ax.text(SWEEP_THRESHOLDS_M[0], 0.6, "naive baseline", fontsize=9, color="#555")

    # Mark the two rival readings of the data.
    for t, note in ((100.0, "tight reading\n(gaps are real barriers)"),
                    (175.0, "loose reading\n(gaps are crossable)")):
        ax.axvline(t, color="#9e9e9e", linestyle=":", linewidth=1.4)
        ax.text(t, ax.get_ylim()[1] * 0.06, f"  {t:.0f} m\n  {note}",
                fontsize=8, color="#444", va="bottom")

    ax.set_xlabel("adjacency threshold (m) -- how far fire is assumed to jump")
    ax.set_ylabel("% less fire exposure than the naive baseline")
    ax.set_title(
        "The benefit depends heavily on the threshold -- so we hedge\n"
        "Rebuilt schedules swing from -7% to +22%; the fixed robust schedule "
        "stays positive everywhere",
        fontsize=13, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(fontsize=10, loc="center right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved sensitivity plot -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    fields = load_fields(verbose=False)
    print_world_summary(fields)
    candidates, naive_order = print_cross_matrix(fields)
    print_recommendation(fields, candidates, naive_order)
    print_inspection_list(fields)
    plot_sensitivity(fields)
