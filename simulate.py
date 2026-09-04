"""
STAGE 3 -- Season simulation.

Give this module a harvest ORDER (a list of field names) and it plays out the
whole season day by day, returning two numbers we care about:

    fire_risk_score  -- sum over every day of the season of "the size, in
                        hectares, of the largest connected block of fields that
                        are STILL STANDING". Lower is safer.

    travel_cost_km   -- total distance the harvester drives between consecutively
                        harvested fields. Lower is cheaper.

THE MODEL, STATED PLAINLY (and its simplifications):

  * One harvester works one field at a time, at HARVEST_RATE_HA_PER_DAY.
    A field of A hectares occupies ceil(A / rate) whole days.

  * A field is either STANDING (full of dry wheat = fuel) or HARVESTED (stubble
    = firebreak). It flips only when it is COMPLETELY cut. A field half-cut on
    day 3 still counts as full fuel. This is deliberately CONSERVATIVE -- it
    never lets us claim a safety benefit we haven't actually earned yet.

  * Risk on day d is measured from the fields standing DURING day d, i.e. at the
    START of the day, before that day's work lands. A fire that breaks out on
    the morning of day d burns the fuel that is there in the morning. This is
    why day 1 always shows the full-map risk and the last day still shows the
    last field.

  * Fire spreads only between ADJACENT standing fields (see graph.py). Harvested
    fields block it. So the "largest connected component" of the standing
    subgraph is the worst single fire that could happen that day.

  * Travel cost is straight-line centroid-to-centroid, summed over consecutive
    pairs in the order. There is no depot: we don't charge for getting to the
    first field or going home from the last, because every ordering would pay
    a similar amount and it would just add a constant.
"""

import math
from dataclasses import dataclass, field as dataclass_field

import networkx as nx

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# How much a single combine harvester can cut in one working day, in hectares.
# ~8 ha/day is a realistic figure for one mid-size combine in smallholder terrain
# with transport time between plots. Raising this shortens the season and
# therefore lowers every fire_risk_score -- so only ever compare scores that
# were produced with the SAME rate.
HARVEST_RATE_HA_PER_DAY = 8.0


# ---------------------------------------------------------------------------
# RESULT CONTAINERS
# ---------------------------------------------------------------------------

@dataclass
class DayState:
    """A snapshot of one day of the season -- everything the animation needs."""

    day: int                     # 1-indexed day of the season
    working_on: str              # which field the harvester is cutting today
    standing: set                # names of fields still full of dry wheat
    harvested: set               # names of fields already cut (firebreaks)
    largest_block: set           # names forming the biggest connected standing block
    largest_block_ha: float      # its size in hectares == today's fire risk
    cumulative_risk: float       # running total of fire risk up to and including today


@dataclass
class SeasonResult:
    """The outcome of simulating one harvest order."""

    label: str                                   # e.g. "naive", "balanced w2=0.5"
    order: list                                  # field names, harvest sequence
    days: list = dataclass_field(default_factory=list)   # list[DayState]
    fire_risk_score: float = 0.0                 # sum of daily largest-block ha
    travel_cost_km: float = 0.0                  # sum of hops between fields
    season_days: int = 0                         # total length of the season

    @property
    def peak_risk_ha(self):
        """The single worst day of the season."""
        return max(d.largest_block_ha for d in self.days) if self.days else 0.0

    @property
    def mean_risk_ha(self):
        """Average daily exposure -- easier to explain in a video than the sum."""
        return self.fire_risk_score / self.season_days if self.season_days else 0.0


# ---------------------------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------------------------

def harvest_days(area_ha, rate=HARVEST_RATE_HA_PER_DAY):
    """
    How many whole days one field takes.

    ceil() because you cannot use a fraction of a day: a 2.7 ha field still
    ties the harvester up for a full day (moving the machine, setup, etc.).
    """
    return max(1, math.ceil(area_ha / rate))


def largest_standing_block(G, standing):
    """
    Among the fields still STANDING, find the biggest connected block of fuel.

    Returns (set_of_field_names, total_hectares). Returns (empty set, 0.0) once
    everything has been harvested.

    This is THE core measurement of the whole project: it is the worst-case
    single fire that could happen today.
    """
    if not standing:
        return set(), 0.0

    # Look only at the standing fields; harvested fields are removed from the
    # graph entirely, which is exactly how a firebreak behaves.
    sub = G.subgraph(standing)

    best_block, best_ha = set(), -1.0
    for comp in nx.connected_components(sub):
        ha = sum(G.nodes[n]["area_ha"] for n in comp)
        # Tie-break on sorted name so repeated runs give identical output.
        if ha > best_ha or (ha == best_ha and sorted(comp) < sorted(best_block)):
            best_block, best_ha = set(comp), ha

    return best_block, best_ha


def travel_cost(order, matrix, index):
    """Total km driven between consecutively harvested fields."""
    return sum(
        matrix[index[a]][index[b]]
        for a, b in zip(order, order[1:])
    )


# ---------------------------------------------------------------------------
# THE SIMULATION
# ---------------------------------------------------------------------------

def simulate_season(order, G, matrix, index, label="", rate=HARVEST_RATE_HA_PER_DAY):
    """
    Play out an entire harvest season for one ordering.

    Returns a SeasonResult holding per-day snapshots plus the two headline scores.
    """
    _validate_order(order, G)

    # --- work out which days belong to which field.
    # Field i occupies days [start_i .. end_i]; it becomes HARVESTED on day end_i + 1.
    end_day = {}          # field name -> last day it is being worked
    working_on = {}       # day number -> field being worked that day
    day = 0
    for name in order:
        for _ in range(harvest_days(G.nodes[name]["area_ha"], rate)):
            day += 1
            working_on[day] = name
        end_day[name] = day
    season_days = day

    # --- step through the season one day at a time
    result = SeasonResult(label=label or "unnamed", order=list(order),
                          season_days=season_days)
    cumulative = 0.0

    for d in range(1, season_days + 1):
        # STANDING = every field not yet finished. A field finished on day 5 is
        # standing on days 1-5 and harvested from day 6 -- see the module docstring.
        standing = {n for n in G.nodes if end_day[n] >= d}
        harvested = set(G.nodes) - standing

        block, block_ha = largest_standing_block(G, standing)
        cumulative += block_ha

        result.days.append(
            DayState(
                day=d,
                working_on=working_on[d],
                standing=standing,
                harvested=harvested,
                largest_block=block,
                largest_block_ha=block_ha,
                cumulative_risk=cumulative,
            )
        )

    result.fire_risk_score = cumulative
    result.travel_cost_km = travel_cost(order, matrix, index)
    return result


def _validate_order(order, G):
    """Catch the classic bugs: a missing field, a duplicate, or an unknown name."""
    if len(order) != len(set(order)):
        raise ValueError(f"harvest order contains duplicates: {order}")
    unknown = set(order) - set(G.nodes)
    if unknown:
        raise ValueError(f"harvest order names fields not in the graph: {unknown}")
    missing = set(G.nodes) - set(order)
    if missing:
        raise ValueError(f"harvest order is missing fields: {missing}")


# ---------------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------------

def print_day_by_day(result, G, max_rows=None):
    """Print the full season table -- used to eyeball that the model behaves."""
    print(f"DAY-BY-DAY SEASON: {result.label}")
    print(f"order: {' -> '.join(result.order)}")
    print("-" * 92)
    print(f"{'DAY':>4}{'CUTTING':>9}{'STANDING':>10}{'RISK (ha)':>12}"
          f"{'CUMULATIVE':>13}   LARGEST STANDING BLOCK")
    print("-" * 92)
    rows = result.days if max_rows is None else result.days[:max_rows]
    for d in rows:
        members = ", ".join(sorted(d.largest_block, key=lambda s: (not s.isdigit(), s)))
        print(f"{d.day:>4}{d.working_on:>9}{len(d.standing):>10}"
              f"{d.largest_block_ha:>12.2f}{d.cumulative_risk:>13.1f}   {members}")
    if max_rows is not None and len(result.days) > max_rows:
        print(f"     ... {len(result.days) - max_rows} more days ...")
    print("-" * 92)
    print(f"SEASON LENGTH   : {result.season_days} days")
    print(f"FIRE RISK SCORE : {result.fire_risk_score:.1f} ha-days "
          f"(peak {result.peak_risk_ha:.1f} ha, mean {result.mean_risk_ha:.1f} ha/day)")
    print(f"TRAVEL COST     : {result.travel_cost_km:.2f} km")
    print()


def print_harvest_schedule(G, order=None, rate=HARVEST_RATE_HA_PER_DAY):
    """Show how many days each field costs -- the raw input to the season length."""
    names = order if order else sorted(G.nodes, key=lambda s: (not s.isdigit(), s))
    print(f"HARVEST DURATION PER FIELD (at {rate:.0f} ha/day)")
    print("-" * 46)
    print(f"{'FIELD':<8}{'AREA (ha)':>12}{'DAYS':>8}")
    total_days = 0
    for n in names:
        a = G.nodes[n]["area_ha"]
        d = harvest_days(a, rate)
        total_days += d
        print(f"{n:<8}{a:>12.2f}{d:>8}")
    print("-" * 46)
    print(f"{'TOTAL':<8}{sum(G.nodes[n]['area_ha'] for n in names):>12.2f}"
          f"{total_days:>8}  <- season length, same for every ordering")
    print()


# ---------------------------------------------------------------------------
# SELF-TEST: run `python simulate.py` to check Stage 3 on its own.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parse import load_fields
    from graph import build_adjacency_graph, distance_matrix_km

    fields = load_fields(verbose=False)
    G = build_adjacency_graph(fields)
    matrix, index = distance_matrix_km(fields)

    print("=" * 92)
    print("STAGE 3 -- SEASON SIMULATION")
    print("=" * 92)
    print_harvest_schedule(G)

    # Three hand-made orders, purely to prove the simulation reacts to ORDER.
    #   A: biggest fields first
    #   B: exactly the reverse of A
    #   C: A, but rotated (start from the middle of the list)
    #
    # HEADS UP -- A and B are guaranteed to have the SAME travel cost. Driving a
    # route backwards covers exactly the same hops, so the sum of consecutive
    # distances is identical. That is arithmetic, not a bug. Order C exists to
    # prove travel cost really does respond to a genuinely different route.
    big_first = sorted(G.nodes, key=lambda n: -G.nodes[n]["area_ha"])
    small_first = list(reversed(big_first))
    rotated = big_first[5:] + big_first[:5]

    ra = simulate_season(big_first, G, matrix, index, label="TEST A: biggest field first")
    rb = simulate_season(small_first, G, matrix, index, label="TEST B: smallest field first")
    rc = simulate_season(rotated, G, matrix, index, label="TEST C: rotated order")
    print_day_by_day(ra, G)
    print_day_by_day(rb, G)
    print(f"TEST C ({' -> '.join(rc.order)}):")
    print(f"  fire risk {rc.fire_risk_score:.1f} ha-days, travel {rc.travel_cost_km:.2f} km")
    print()

    # --- sanity assertions: if any of these trip, the model is wrong.
    print("SANITY CHECKS")
    print("-" * 60)
    checks = []

    checks.append(("both orders give the same season length",
                   ra.season_days == rb.season_days))
    checks.append(("day 1 risk == the whole day-0 largest block, for both",
                   abs(ra.days[0].largest_block_ha - rb.days[0].largest_block_ha) < 1e-9))
    checks.append(("risk never increases within an order (harvesting only helps)",
                   all(ra.days[i].largest_block_ha >= ra.days[i + 1].largest_block_ha
                       for i in range(len(ra.days) - 1))))
    checks.append(("last day still has exactly one standing field",
                   len(ra.days[-1].standing) == 1))
    checks.append(("ORDER CHANGES THE FIRE SCORE (the whole premise of the project)",
                   abs(ra.fire_risk_score - rb.fire_risk_score) > 1e-6))
    checks.append(("reversing an order leaves travel cost unchanged (expected arithmetic)",
                   abs(ra.travel_cost_km - rb.travel_cost_km) < 1e-9))
    checks.append(("a genuinely different route DOES change travel cost",
                   abs(ra.travel_cost_km - rc.travel_cost_km) > 1e-6))
    checks.append(("every field harvested exactly once",
                   sorted(ra.order) == sorted(G.nodes)))

    for text, ok in checks:
        print(f"  [{'OK ' if ok else 'FAIL'}] {text}")
    print("  ==> " + ("ALL SANITY CHECKS PASSED"
                      if all(ok for _, ok in checks) else "SOMETHING IS WRONG -- DEBUG"))
