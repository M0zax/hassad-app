"""
STAGE 4 -- The three harvest-order generators.

All three answer the same question -- "which field do we cut next?" -- with a
different amount of intelligence:

  (a) naive     : biggest field first. No fire logic at all. This is what a
                  farmer plausibly does anyway (get the big earner in the barn),
                  so it is our honest baseline to beat.

  (b) fire_only : at every step, look at every field still standing, ask "if I
                  finished THIS one next, how big would the largest connected
                  block of standing fuel be afterwards?", and take the field that
                  makes that number smallest. Ignores driving distance entirely.

  (c) balanced  : same idea, but the score also charges for the drive:
                      score = w1 * (resulting largest block, ha)
                            + w2 * (km from where the harvester is now)
                  and we take the lowest score. w1/w2 tune the trade-off.

IMPORTANT -- these are GREEDY heuristics, not proofs of optimality. Each one
takes the locally best step and never backtracks, so a cleverer sequence may
exist. With 11 fields there are 11! = 39,916,800 possible orders, far too many
to check exhaustively in a prototype. Greedy is the standard, explainable
approach for this kind of problem and it is what we present in the video.
"""

from simulate import largest_standing_block, simulate_season

# ---------------------------------------------------------------------------
# CONSTANTS -- the trade-off weights
# ---------------------------------------------------------------------------

# w1 weights FIRE RISK, measured in hectares of the largest standing block.
W1_FIRE = 1.0

# w2 weights TRAVEL, measured in kilometres driven to reach the next field.
#
# MIND THE UNITS. These two numbers are added together, but they are not on the
# same scale in our study area: the largest block starts at ~75 ha, while the
# longest single drive is only ~5.6 km. So with w1=1.0 a w2 of 0.5 changes the
# score by at most ~2.8 -- basically nothing. To actually see travel start to
# win, w2 has to climb into the tens. That is what the sweep below demonstrates.
W2_TRAVEL = 0.5

# Values of w2 we print so the team can see the whole trade-off curve, not just
# one point. w2=0 is pure fire; large w2 is nearly pure "drive as little as possible".
W2_SWEEP = (0.0, 0.5, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0)


# ---------------------------------------------------------------------------
# (a) NAIVE BASELINE
# ---------------------------------------------------------------------------

def naive_largest_first(G, matrix=None, index=None):
    """
    Harvest the biggest field first, then the next biggest, and so on.

    A plausible real-world default: the big fields are the big pay-cheques, and
    a farmer with one machine wants them safe in the barn first. Contains zero
    knowledge of which fields touch which.
    """
    return sorted(G.nodes, key=lambda n: (-G.nodes[n]["area_ha"], n))


# ---------------------------------------------------------------------------
# SHARED GREEDY MACHINERY
# ---------------------------------------------------------------------------

def _resulting_block_ha(G, standing, candidate):
    """
    If we finished `candidate` next, how big would the largest connected block
    of STILL-STANDING fuel be afterwards? (in hectares)

    This is the single number every greedy step is trying to push down.
    """
    _, ha = largest_standing_block(G, standing - {candidate})
    return ha


def greedy_fire_only(G, matrix=None, index=None):
    """
    (b) Pure fire-risk greedy. Distance is not considered at all.

    TIE-BREAKING: lots of fields give an identical resulting block (e.g. every
    field that isn't in the biggest block leaves that block untouched). When
    scores tie we prefer the LARGER field -- it takes more total fuel off the
    map, which helps on later days -- and then the name, purely so that repeated
    runs produce byte-identical output.
    """
    standing = set(G.nodes)
    order = []

    while standing:
        best = min(
            standing,
            key=lambda c: (
                _resulting_block_ha(G, standing, c),   # 1. smallest resulting block
                -G.nodes[c]["area_ha"],                # 2. then take more fuel off
                c,                                     # 3. then alphabetical (determinism)
            ),
        )
        order.append(best)
        standing.remove(best)

    return order


def greedy_balanced(G, matrix, index, w1=W1_FIRE, w2=W2_TRAVEL):
    """
    (c) Balanced greedy: trade fire risk against driving distance.

        score(candidate) = w1 * (resulting largest block in ha)
                         + w2 * (km from the harvester's current field)

    The FIRST field is chosen with travel = 0 for everybody, because the machine
    has no "current position" yet -- there is nowhere to drive from. After that,
    travel is the centroid-to-centroid distance from the field just finished.
    """
    standing = set(G.nodes)
    order = []
    current = None                 # where the harvester is standing right now

    while standing:
        def score(c):
            fire = _resulting_block_ha(G, standing, c)
            travel = 0.0 if current is None else matrix[index[current]][index[c]]
            return (w1 * fire + w2 * travel, -G.nodes[c]["area_ha"], c)

        best = min(standing, key=score)
        order.append(best)
        standing.remove(best)
        current = best

    return order


# ---------------------------------------------------------------------------
# RUNNING AND COMPARING THEM ALL
# ---------------------------------------------------------------------------

def run_all(G, matrix, index, w1=W1_FIRE, w2=W2_TRAVEL):
    """
    Build and simulate the three headline strategies.
    Returns (naive_result, fire_result, balanced_result).
    """
    naive = simulate_season(naive_largest_first(G), G, matrix, index,
                            label="(a) naive: largest field first")
    fire = simulate_season(greedy_fire_only(G), G, matrix, index,
                           label="(b) fire-only greedy")
    bal = simulate_season(greedy_balanced(G, matrix, index, w1, w2), G, matrix, index,
                          label=f"(c) balanced greedy (w1={w1}, w2={w2})")
    return naive, fire, bal


def _pct_change(new, base):
    """Percent improvement of `new` over `base`. Positive = better (lower)."""
    if base == 0:
        return 0.0
    return (base - new) / base * 100.0


def print_comparison(naive, fire, balanced):
    """The headline table: does the clever ordering actually pay off?"""
    print("=" * 92)
    print("STAGE 4 -- OPTIMIZER COMPARISON")
    print("=" * 92)

    rows = [naive, fire, balanced]

    print(f"{'STRATEGY':<38}{'FIRE RISK':>12}{'vs (a)':>9}"
          f"{'TRAVEL':>10}{'vs (a)':>9}{'MEAN/DAY':>11}")
    print(f"{'':<38}{'(ha-days)':>12}{'':>9}{'(km)':>10}{'':>9}{'(ha)':>11}")
    print("-" * 92)
    for r in rows:
        if r is naive:
            fire_pct = travel_pct = "  --"
        else:
            fire_pct = f"{_pct_change(r.fire_risk_score, naive.fire_risk_score):+6.1f}%"
            travel_pct = f"{_pct_change(r.travel_cost_km, naive.travel_cost_km):+6.1f}%"
        print(f"{r.label:<38}{r.fire_risk_score:>12.1f}{fire_pct:>9}"
              f"{r.travel_cost_km:>10.2f}{travel_pct:>9}{r.mean_risk_ha:>11.1f}")
    print("-" * 92)
    print("(positive % = better than the naive baseline; lower is better for both metrics)")
    print()

    print("HARVEST ORDERS")
    print("-" * 92)
    for r in rows:
        print(f"  {r.label}")
        print(f"      {' -> '.join(r.order)}")
    print()


def print_w2_sweep(G, matrix, index, naive, w1=W1_FIRE, w2_values=W2_SWEEP):
    """
    Print the trade-off curve: as we care more about fuel in the tractor (w2 up),
    fire risk should get worse and travel should get better.

    This is the table that shows the project is a genuine two-objective problem
    and not just "one right answer".
    """
    print("TRADE-OFF CURVE -- sweeping w2 (the travel weight), w1 fixed at "
          f"{w1}")
    print("-" * 92)
    print(f"{'w2':>8}{'FIRE RISK':>12}{'vs (a)':>10}{'TRAVEL':>10}{'vs (a)':>10}"
          f"   HARVEST ORDER")
    print("-" * 92)

    seen_orders = {}
    for w2 in w2_values:
        order = greedy_balanced(G, matrix, index, w1=w1, w2=w2)
        r = simulate_season(order, G, matrix, index, label=f"w2={w2}")
        fire_pct = _pct_change(r.fire_risk_score, naive.fire_risk_score)
        travel_pct = _pct_change(r.travel_cost_km, naive.travel_cost_km)
        print(f"{w2:>8.1f}{r.fire_risk_score:>12.1f}{fire_pct:>9.1f}%"
              f"{r.travel_cost_km:>10.2f}{travel_pct:>9.1f}%   {' -> '.join(r.order)}")
        seen_orders.setdefault(tuple(order), w2)

    print("-" * 92)
    print(f"{len(seen_orders)} distinct orderings appear across {len(w2_values)} "
          f"weight settings.")
    print("Reading the table: w2=0 is pure fire-safety. As w2 grows the optimizer")
    print("starts refusing long drives, so travel falls and fire risk rises.")
    print()


# ---------------------------------------------------------------------------
# SELF-TEST: run `python optimize.py` to check Stage 4 on its own.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parse import load_fields
    from graph import build_adjacency_graph, distance_matrix_km

    fields = load_fields(verbose=False)
    G = build_adjacency_graph(fields)
    matrix, index = distance_matrix_km(fields)

    naive, fire, bal = run_all(G, matrix, index)
    print_comparison(naive, fire, bal)
    print_w2_sweep(G, matrix, index, naive)

    # --- sanity assertions
    print("SANITY CHECKS")
    print("-" * 70)
    checks = [
        ("fire-only beats or matches naive on fire risk",
         fire.fire_risk_score <= naive.fire_risk_score),
        ("all three orders are valid permutations of the 11 fields",
         all(sorted(r.order) == sorted(G.nodes) for r in (naive, fire, bal))),
        ("all three seasons are the same length",
         naive.season_days == fire.season_days == bal.season_days),
        ("w2=0 balanced reproduces the fire-only order exactly",
         greedy_balanced(G, matrix, index, w2=0.0) == greedy_fire_only(G)),
        ("a very large w2 drives travel cost below the naive baseline",
         simulate_season(greedy_balanced(G, matrix, index, w2=100.0), G, matrix,
                         index).travel_cost_km < naive.travel_cost_km),
    ]
    for text, ok in checks:
        print(f"  [{'OK ' if ok else 'FAIL'}] {text}")
    print("  ==> " + ("ALL SANITY CHECKS PASSED"
                      if all(ok for _, ok in checks) else "SOMETHING IS WRONG -- DEBUG"))
