"""
EXACT OPTIMIZER -- the provably best harvest order, replacing Stage 4's greedy.

THE INSIGHT THAT MAKES THIS POSSIBLE
------------------------------------
While one field is being cut, the set of standing fields never changes: it is
"every field not yet completed" for every one of that field's harvest days.
So the season's fire risk splits cleanly into per-field chunks:

    fire_risk(order) = SUM over k of  duration(f_k) * LCC(standing before f_k)

where LCC(X) is the hectares of the largest connected component of the
still-standing fields X. The chunk for f_k depends only on WHICH fields are
already done -- not on the order they were done in. That is exactly the
structure dynamic programming over subsets (Held-Karp) needs:

    cost(S) = min over f in S of  cost(S \\ {f}) + duration(f) * LCC(V \\ (S\\{f}))

With 11 fields there are 2^11 = 2,048 subsets: the true optimum over all
11! = 39,916,800 orders falls out in milliseconds. Adding travel cost needs
one more piece of state -- the last field harvested -- because the next hop's
length depends on where the machine is standing.

WHAT "PROVABLY OPTIMAL" MEANS HERE (say it exactly like this to judges)
-----------------------------------------------------------------------
Optimal for OUR MODEL: the deterministic day-by-day simulation in simulate.py,
one harvester, a fixed adjacency graph, and (for the weighted version) the
single number w1*fire + w2*travel. It is not a claim about nature. And the
w2-sweep does NOT trace the complete fire/travel Pareto frontier -- weighted
sums can only find its convex-hull points (verified with a counterexample).

The self-test at the bottom PROVES the implementation against brute force:
it enumerates every one of the 5,040 possible orders of a 7-field
sub-problem with the independent simulator and confirms the DP finds the
same minimum. Run `python exact.py` to see it pass.

SCALING: the fire-only DP is 2^n subsets -- n≈20 fields is its practical limit
in Python. The weighted DP carries (subset, last-field) state, 2^n * n, so its
comfortable limit is n≈16 (n=20 would mean minutes and ~0.5-1 GB, not
milliseconds). Beyond those sizes (whole-village maps), use this module as the
calibration standard for a heuristic like simulated annealing.
"""

import itertools
import time

from simulate import HARVEST_RATE_HA_PER_DAY, harvest_days, simulate_season

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Refuse to run the exact solvers above these sizes: the state space blows up.
# The weighted DP has n-times more states than the fire-only DP, hence the
# lower limit.
MAX_EXACT_FIELDS = 20
MAX_EXACT_FIELDS_WEIGHTED = 16

# Brute-force self-check size: 7 fields -> 5,040 permutations, a few seconds.
BRUTE_FORCE_FIELDS = 7


# ---------------------------------------------------------------------------
# THE BITMASK MACHINERY
# ---------------------------------------------------------------------------
# Fields are numbered 0..n-1; a SUBSET of fields is one integer whose bit i
# says "field i is in the set". This makes "all 2,048 subsets" just the
# numbers 0..2047, and set operations single CPU instructions.

def _setup(G, rate=HARVEST_RATE_HA_PER_DAY):
    """Fixed field numbering + durations + neighbour bitmasks for graph G."""
    names = sorted(G.nodes)                       # fixed, deterministic order
    if len(names) > MAX_EXACT_FIELDS:
        raise ValueError(
            f"{len(names)} fields is too many for exact subset DP "
            f"(limit {MAX_EXACT_FIELDS}); use a heuristic and calibrate it "
            f"on a smaller instance.")
    pos = {nm: i for i, nm in enumerate(names)}
    area = [G.nodes[nm]["area_ha"] for nm in names]
    # The harvest rate changes ceil() durations NON-proportionally, which can
    # change which order is optimal -- so the solver must be told the same
    # rate the results will be simulated/animated at.
    dur = [harvest_days(a, rate) for a in area]
    nbr = [0] * len(names)
    for nm in names:
        for other in G[nm]:
            nbr[pos[nm]] |= 1 << pos[other]
    return names, pos, area, dur, nbr


def _lcc_table(names, area, nbr):
    """
    lcc[mask] = hectares of the largest connected component among exactly the
    fields in `mask`. Computed once for every subset by bitmask flood-fill.
    """
    n = len(names)
    lcc = [0.0] * (1 << n)
    for mask in range(1, 1 << n):
        best, seen, m = 0.0, 0, mask
        while m:
            b = m & (-m)
            i = b.bit_length() - 1
            if not (seen >> i) & 1:
                comp, frontier = b, b
                while frontier:
                    nxt, fm = 0, frontier
                    while fm:
                        fb = fm & (-fm)
                        j = fb.bit_length() - 1
                        fm ^= fb
                        nxt |= nbr[j] & mask & ~comp
                    comp |= nxt
                    frontier = nxt
                seen |= comp
                ha = sum(area[k] for k in range(n) if (comp >> k) & 1)
                best = max(best, ha)
            m ^= b
        lcc[mask] = best
    return lcc


# ---------------------------------------------------------------------------
# THE SOLVERS
# ---------------------------------------------------------------------------

def exact_fire_only(G, rate=HARVEST_RATE_HA_PER_DAY):
    """
    The order that provably minimises fire_risk_score, ignoring travel.
    Returns (fire_risk_score, order as a list of field names).

    `rate` MUST match the rate any downstream simulation/animation uses --
    an order optimal at 8 ha/day can be measurably suboptimal at another rate.
    """
    names, _, area, dur, nbr = _setup(G, rate)
    n, FULL = len(names), (1 << len(names)) - 1
    lcc = _lcc_table(names, area, nbr)

    INF = float("inf")
    cost = [INF] * (1 << n)
    parent = [-1] * (1 << n)
    cost[0] = 0.0
    # Plain ascending order is a valid schedule: removing a bit always gives a
    # smaller number, so cost[mask ^ bit] is final before cost[mask] is built.
    for mask in range(1, 1 << n):
        m = mask
        while m:
            b = m & (-m)
            f = b.bit_length() - 1
            m ^= b
            prev = mask ^ b
            c = cost[prev] + dur[f] * lcc[FULL ^ prev]
            # strict < : ties keep the first candidate found, which makes
            # repeated runs byte-identical without giving up any exactness
            if c < cost[mask]:
                cost[mask] = c
                parent[mask] = f

    order, mask = [], FULL
    while mask:
        f = parent[mask]
        order.append(names[f])
        mask ^= 1 << f
    order.reverse()
    return cost[FULL], order


def exact_weighted(G, matrix, index, w1=1.0, w2=0.0, start_position=None,
                   rate=HARVEST_RATE_HA_PER_DAY):
    """
    The order that provably minimises  w1 * fire_risk + w2 * travel_km.

    State = (set of completed fields, last field harvested), because the next
    hop's length depends on where the harvester is standing. The first field
    costs no travel -- unless `start_position` names a field/location the
    machine is already at, in which case the first hop is charged from there.

    Returns (total_cost, order).
    """
    if len(G.nodes) == 0:
        return 0.0, []
    if len(G.nodes) > MAX_EXACT_FIELDS_WEIGHTED:
        raise ValueError(
            f"{len(G.nodes)} fields is too many for the weighted DP "
            f"(limit {MAX_EXACT_FIELDS_WEIGHTED}: its state space is 2^n * n); "
            f"use a heuristic calibrated against this solver on a smaller map.")
    if start_position is not None and start_position not in index:
        raise ValueError(f"unknown start_position {start_position!r}; "
                         f"known fields: {sorted(index)}")
    names, pos, area, dur, nbr = _setup(G, rate)
    n, FULL = len(names), (1 << len(names)) - 1
    lcc = _lcc_table(names, area, nbr)

    def dist(a, b):
        return matrix[index[a]][index[b]]

    INF = float("inf")
    cost = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    for f in range(n):
        first_travel = 0.0 if start_position is None else dist(start_position, names[f])
        cost[1 << f][f] = w1 * dur[f] * lcc[FULL] + w2 * first_travel

    for mask in range(1, 1 << n):
        for f in range(n):
            base = cost[mask][f]
            if base == INF:
                continue
            fire_next = lcc[FULL ^ mask]          # standing set after `mask` done
            rest = FULL & ~mask
            m = rest
            while m:
                b = m & (-m)
                g = b.bit_length() - 1
                m ^= b
                c = base + w2 * dist(names[f], names[g]) + w1 * dur[g] * fire_next
                if c < cost[mask | b][g]:
                    cost[mask | b][g] = c
                    parent[mask | b][g] = f

    best_f = min(range(n), key=lambda f: cost[FULL][f])
    total = cost[FULL][best_f]
    order, mask, f = [], FULL, best_f
    while f != -1:
        order.append(names[f])
        pf = parent[mask][f]
        mask ^= 1 << f
        f = pf
    order.reverse()
    return total, order


# ---------------------------------------------------------------------------
# RE-OPTIMIZE FROM ANY MID-SEASON STATE (Jad & Ali's toggle)
# ---------------------------------------------------------------------------

def reoptimize(G, matrix, index, harvested, position=None, w1=1.0, w2=0.0,
               rate=HARVEST_RATE_HA_PER_DAY):
    """
    Real seasons go off-plan: weather, machinery, a farmer's own priorities.
    Given the fields ALREADY harvested (in any order, for any reason) and
    where the machine currently is, recompute the provably best order for
    everything still standing. Harvested fields act as firebreaks: they are
    simply gone from the fire graph.

    Returns {"order", "total_cost", "fire_risk", "travel_km"} for the
    REMAINING season only.
    """
    if isinstance(harvested, str):
        raise TypeError(
            "harvested must be a collection of field names (e.g. ['13'] or "
            "{'4', '7'}), not a single string -- a bare string would be read "
            "as its individual characters and silently mark the wrong fields")
    harvested = set(harvested)
    unknown = harvested - set(G.nodes)
    if unknown:
        raise ValueError(f"unknown fields marked harvested: {unknown}")
    if position is not None and position not in index:
        raise ValueError(f"unknown position {position!r}; "
                         f"known fields: {sorted(index)}")
    remaining = set(G.nodes) - harvested
    if not remaining:
        return {"order": [], "total_cost": 0.0, "fire_risk": 0.0, "travel_km": 0.0}

    H = G.subgraph(remaining).copy()
    total, order = exact_weighted(H, matrix, index, w1=w1, w2=w2,
                                  start_position=position, rate=rate)

    # Recompute the two components separately for honest reporting.
    names, _, area, dur, nbr = _setup(H, rate)
    lcc = _lcc_table(names, area, nbr)
    pos = {nm: i for i, nm in enumerate(names)}
    FULL = (1 << len(names)) - 1
    fire, mask = 0.0, 0
    for nm in order:
        fire += harvest_days(H.nodes[nm]["area_ha"], rate) * lcc[FULL ^ mask]
        mask |= 1 << pos[nm]
    travel = sum(matrix[index[a]][index[b]] for a, b in zip(order, order[1:]))
    if position is not None:
        travel += matrix[index[position]][index[order[0]]]
    return {"order": order, "total_cost": total,
            "fire_risk": fire, "travel_km": travel}


# ---------------------------------------------------------------------------
# SELF-TEST: `python exact.py`
# ---------------------------------------------------------------------------
# The one check that matters most: on a sub-problem small enough to try EVERY
# order, the independent day-by-day simulator must agree that the DP's answer
# is the true minimum. If this passes, the decomposition and the code are
# both right -- no trust required.

if __name__ == "__main__":
    from parse import load_fields
    from graph import build_adjacency_graph, distance_matrix_km
    from optimize import naive_largest_first, greedy_fire_only

    fields = load_fields(verbose=False)
    matrix, index = distance_matrix_km(fields)

    print("=" * 88)
    print("EXACT OPTIMIZER -- subset DP over all possible harvest orders")
    print("=" * 88)

    checks = []

    for thr in (175.0, 100.0):
        G = build_adjacency_graph(fields, threshold_m=thr)

        t0 = time.time()
        opt_cost, opt_order = exact_fire_only(G)
        ms = (time.time() - t0) * 1000

        sim = simulate_season(opt_order, G, matrix, index)
        naive = simulate_season(naive_largest_first(G), G, matrix, index)
        greedy = simulate_season(greedy_fire_only(G), G, matrix, index)
        pct = (naive.fire_risk_score - opt_cost) / naive.fire_risk_score * 100

        print(f"\n--- {thr:.0f} m world ---")
        print(f"naive {naive.fire_risk_score:8.1f}   greedy {greedy.fire_risk_score:8.1f}   "
              f"EXACT {opt_cost:8.1f}  ({pct:+.1f}% vs naive, solved in {ms:.0f} ms)")
        print(f"order: {' -> '.join(opt_order)}")

        checks.append((f"{thr:.0f} m: DP cost equals the simulator's score for the DP order",
                       abs(sim.fire_risk_score - opt_cost) < 1e-6))
        checks.append((f"{thr:.0f} m: exact beats or matches greedy",
                       opt_cost <= greedy.fire_risk_score + 1e-9))

    # ---- brute force: every order of a 7-field sub-problem, via the simulator
    G175 = build_adjacency_graph(fields, threshold_m=175.0)
    sub_names = sorted(G175.nodes)[:BRUTE_FORCE_FIELDS]
    H = G175.subgraph(sub_names).copy()

    print(f"\nBRUTE FORCE CHECK on {len(sub_names)} fields "
          f"({len(sub_names)}! = {len(list(itertools.permutations(range(len(sub_names))))):,} orders): "
          f"{', '.join(sub_names)}")

    t0 = time.time()
    best_bf, best_bf_order = float("inf"), None
    best_bfw = float("inf")
    W1, W2 = 1.0, 5.0
    for perm in itertools.permutations(sub_names):
        r = simulate_season(list(perm), H, matrix, index)
        if r.fire_risk_score < best_bf:
            best_bf, best_bf_order = r.fire_risk_score, list(perm)
        wcost = W1 * r.fire_risk_score + W2 * r.travel_cost_km
        best_bfw = min(best_bfw, wcost)
    bf_secs = time.time() - t0

    dp_cost, dp_order = exact_fire_only(H)
    dpw_cost, _ = exact_weighted(H, matrix, index, w1=W1, w2=W2)

    print(f"  fire-only : brute force {best_bf:.4f}  vs DP {dp_cost:.4f}   "
          f"(brute force took {bf_secs:.1f} s; DP took milliseconds)")
    print(f"  weighted  : brute force {best_bfw:.4f}  vs DP {dpw_cost:.4f}   (w1={W1}, w2={W2})")

    checks.append(("brute force (all orders, independent simulator) matches DP, fire-only",
                   abs(best_bf - dp_cost) < 1e-6))
    checks.append(("brute force matches DP, weighted fire+travel",
                   abs(best_bfw - dpw_cost) < 1e-6))

    # ---- the start_position path: the configuration a mid-season replan hits.
    # Mutation-tested: a sign error or transposed dist() here passes every
    # check above, so these two checks exist specifically to catch that.
    start = sorted(set(G175.nodes) - set(sub_names))[0]
    best_bfs = float("inf")
    for perm in itertools.permutations(sub_names):
        r = simulate_season(list(perm), H, matrix, index)
        best_bfs = min(best_bfs,
                       W1 * r.fire_risk_score
                       + W2 * (matrix[index[start]][index[perm[0]]]
                               + r.travel_cost_km))
    dps_cost, _ = exact_weighted(H, matrix, index, w1=W1, w2=W2,
                                 start_position=start)
    print(f"  from '{start}' : brute force {best_bfs:.4f}  vs DP {dps_cost:.4f}   "
          f"(start_position charged on the first hop)")
    checks.append(("brute force matches DP when a start position charges the first hop",
                   abs(best_bfs - dps_cost) < 1e-6))

    done7 = sorted(set(G175.nodes) - set(sub_names))
    rp = reoptimize(G175, matrix, index, harvested=done7, position=done7[0],
                    w1=W1, w2=W2)
    checks.append(("re-optimize with position and w2>0 matches that brute force too",
                   abs(rp["total_cost"] - best_bfs) < 1e-6
                   if done7[0] == start else True))
    checks.append(("re-optimize's reported fire/travel split adds up to its total",
                   abs(W1 * rp["fire_risk"] + W2 * rp["travel_km"]
                       - rp["total_cost"]) < 1e-6))

    # ---- non-default harvest rate: durations ceil() differently, so the
    # optimal order can change; solver and simulator must agree at ANY rate.
    RATE2 = 16.0
    _, r8_order = exact_fire_only(G175)                     # optimal at 8 ha/day
    dp16_cost, dp16_order = exact_fire_only(G175, rate=RATE2)
    sim16 = simulate_season(dp16_order, G175, matrix, index, rate=RATE2)
    rate8_order_at16 = simulate_season(r8_order, G175, matrix, index, rate=RATE2)
    print(f"\nRATE CHECK at {RATE2:.0f} ha/day: DP {dp16_cost:.1f} vs simulator "
          f"{sim16.fire_risk_score:.1f}; the 8 ha/day order scores "
          f"{rate8_order_at16.fire_risk_score:.1f} at this rate")
    checks.append((f"DP and simulator agree at a non-default rate ({RATE2:.0f} ha/day)",
                   abs(sim16.fire_risk_score - dp16_cost) < 1e-6))
    checks.append(("the rate-aware solve beats or matches the rate-8 order at that rate",
                   dp16_cost <= rate8_order_at16.fire_risk_score + 1e-9))

    # ---- re-optimize consistency (Bellman: the tail of an optimal plan is optimal)
    full_cost, full_order = exact_fire_only(G175)
    done, position = full_order[:2], full_order[1]
    tail = full_order[2:]
    names_all, _, area_all, dur_all, nbr_all = _setup(G175)
    lcc_all = _lcc_table(names_all, area_all, nbr_all)
    pos_all = {nm: i for i, nm in enumerate(names_all)}
    FULL = (1 << len(names_all)) - 1
    mask = (1 << pos_all[done[0]]) | (1 << pos_all[done[1]])
    tail_cost, m = 0.0, mask
    for nm in tail:
        tail_cost += harvest_days(G175.nodes[nm]["area_ha"]) * lcc_all[FULL ^ m]
        m |= 1 << pos_all[nm]
    re = reoptimize(G175, matrix, index, harvested=done, position=position, w2=0.0)
    print(f"\nRE-OPTIMIZE CHECK: after harvesting {done}, replanned fire risk "
          f"{re['fire_risk']:.1f} vs optimal tail {tail_cost:.1f}")
    checks.append(("re-optimize reproduces the optimal tail when the season is on plan",
                   abs(re["fire_risk"] - tail_cost) < 1e-6))
    checks.append(("re-optimize with nothing harvested equals the full solve",
                   abs(reoptimize(G175, matrix, index, harvested=set())["fire_risk"]
                       - full_cost) < 1e-6))

    print("\nSELF-TEST")
    print("-" * 88)
    for text, ok in checks:
        print(f"  [{'OK ' if ok else 'FAIL'}] {text}")
    print("  ==> " + ("ALL CHECKS PASSED -- the word 'optimal' is earned"
                      if all(ok for _, ok in checks) else "SOMETHING FAILED -- DO NOT CLAIM OPTIMALITY"))
