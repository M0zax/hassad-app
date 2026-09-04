# Harvest-Sequencing Optimizer

**FIRST Global Challenge 2026 — reducing wheat-fire risk in Lebanon's Bekaa Valley
by choosing the ORDER in which neighbouring fields get harvested.**

## The idea in one paragraph

A field of standing dry wheat is fuel. A harvested field is short stubble — a
firebreak. Fire spreads through *connected* standing fields, so the biggest fire
that can happen on any given day is the size of the largest **connected block**
of fields that are still standing. That block changes shape every day as the
harvester works, and *the order the fields are cut in decides how fast it shrinks*.
This project finds an order that shrinks it fast, without making the harvester
drive a ridiculous distance.

Two objectives, both minimised:

| metric | meaning | units |
| --- | --- | --- |
| `fire_risk_score` | size of the largest connected standing block, summed over every day of the season | ha-days |
| `travel_cost_km` | distance driven between consecutively harvested fields | km |

## Headline result

11 fields, 141 ha, a 24-day season.

> **Read this before quoting any number.** Every result here depends on one
> unresolved input — the adjacency threshold (see below). We report two figures:
> one that holds no matter how that question resolves, and one that is larger but
> conditional. Quoting the conditional number as if it were settled would be wrong.

### The claim that holds either way

```
ROBUST SCHEDULE:  13 -> nte -> 9 -> 12 -> 6 -> 8 -> 10 -> 11 -> 5 -> 7 -> 4
```

**5.5% less season-long fire exposure** than the naive largest-first baseline —
and it delivers that whether the true adjacency rule turns out to be 100 m or
175 m. Purely by reordering the harvest. No new equipment.

### The larger claim, if the 175 m rule is confirmed

| strategy | fire risk (ha-days) | vs naive | travel (km) | vs naive |
| --- | --- | --- | --- | --- |
| (a) naive — largest field first | 1093.4 | — | 19.51 | — |
| (b) fire-only greedy | 853.8 | **+21.9%** | 25.18 | −29.1% |
| (c) balanced greedy (w2=5) | 908.8 | **+16.9%** | 15.76 | **+19.2%** |

**17% less fire exposure *and* 3.7 km less driving.** But that same schedule scores
**−2.9%** — worse than doing nothing — if the 100 m rule is the correct one. See
the robustness section before using these figures.

**Why the optimizers work:** the naive order starts with field 13 — the biggest
field, but an isolated one whose removal disconnects nothing. Under the 175 m rule
the optimizers instead start with `nte`, the *hinge* holding the 75.5 ha block
together, splitting it on day 4 instead of day 11.

## Running it

Needs Python 3.9+ and:

```bash
pip install shapely networkx numpy matplotlib pillow
```

Run everything:

```bash
python main.py
```

Takes about 25 seconds and writes all output files. Each stage also runs on its
own with its own self-test, so teammates can work in parallel:

```bash
python parse.py
```
```bash
python graph.py
```
```bash
python simulate.py
```
```bash
python optimize.py
```
```bash
python animate.py
```

## Files

| file | stage | owner | what it does |
| --- | --- | --- | --- |
| `parse.py` | 1 | | Reads the KML, projects lon/lat to metres, computes area + centroid, drops outlier fields |
| `graph.py` | 2 | | Builds the adjacency (fire-spread) graph and the travel-distance matrix; draws `map_adjacency.png` |
| `simulate.py` | 3 | | Plays a harvest order out day by day and scores it |
| `optimize.py` | 4 | | The three order generators + the comparison table and trade-off sweep |
| `animate.py` | 5 | | The three-panel GIF and the still frames |
| `sensitivity.py` | — | | Tests every schedule under both adjacency rules; builds the robust schedule |
| `main.py` | — | | Runs everything in order |

**Added in Phase 2** (see `SOFTWARE_CHANGELOG.md` for the full before/after):

| file | what it does | run it |
| --- | --- | --- |
| `exact.py` | The certified-optimal solver (subset dynamic programming) and `reoptimize()` for mid-season replanning. Self-test brute-forces every order of a 7-field sub-problem to prove optimality. | `python exact.py` |
| `satellite.py` | Sentinel-2 check of the contested field gaps at harvest time (three summers), per-year adjacency verdicts, and field-state detection. Anonymous access to the open archive — no account. | `python satellite.py` (~15 min, downloads ~MBs) |
| `firms.py` | NASA FIRMS thermal-anomaly archive for Lebanon, clipped to the Bekaa: seasonality and proximity to our fields. | `python firms.py` |
| `app_logic.py` | The app's brain, Streamlit-free so it can be tested: plan, replan, "why this field" sentences, exports. | `python app_logic.py` |
| `app.py` | The farmer-facing app, built for a phone, in Arabic or English (toggle): tap your fields on the satellite map — or draw your own farm with the pencil tool — → "Make my plan" → a Today card (which field, how long, why) → "Field 5 is cut" re-plans automatically; tap a field to mark it cut/not cut; Undo; WhatsApp and Print. Judges' numbers and the economics live in a collapsed section (`?judge=1` opens it; `?mode=draw` opens drawing mode; `?lang=ar` opens in Arabic). | `streamlit run app.py` |
| `i18n.py` | Every string the app shows, English and Arabic side by side — the file Team C reviews. | — |
| `FARMER_TEST.md` | The 20-minute farmer test script and how to put the app on a farmer's phone. | — |

Install: `pip install -r requirements.txt` for the app, plus
`-r requirements-evidence.txt` for the satellite and fire-history scripts.
**Hosting the app online (free):** see `DEPLOY.md`. The app has an
**About / questions-and-answers page** (`?page=about`, or the button under the
title) with everything a judge, mentor or farmer could ask — including the
mentor's questions and our answers.

Outputs: `map_adjacency.png`, `harvest_comparison.gif`, `frame_dayNN.png`,
`sensitivity_thresholds.png`, `satellite_gaps.png`, `satellite_fields.png`,
`satellite_gaps_results.json`, `firms_bekaa.png`.

## The constants — what each one means and when to change it

### `parse.py`

**`ANCHOR_FIELD = "nte"`** — the field the study area is measured from.

**`STUDY_RADIUS_KM = 6.0`** — a field is only included if its centroid is within
this distance of the anchor. Our KML contained two fields (`nte 2` at 23.6 km and
`nte3` at 16.9 km) traced far outside the farmland we care about. Fire cannot
spread between fields tens of km apart, so leaving them in would corrupt the model.
The script *prints* what it excluded and why — never silently drops data.

### `graph.py`

**`ADJACENCY_THRESHOLD_M = 175.0`** — two fields count as adjacent (fire can jump
between them) if their traced boundaries come within this many metres.

This is the single most important number in the project, so here is the reasoning.
It is not 0 because hand-traced polygons have false gaps — a road, a hedgerow, a
sloppy click. We measured every pair of fields and the gaps come in two clumps:

```
fields that clearly touch:      7 – 12 m
fields that clearly do not:   114 m and up
                              ^^^^^^^^^^^^ nothing at all in between
```

A 100 m rule lands in that empty band and falls **14 m short** of connecting `nte`
to the 4-5-6-7 chain, shattering the map into 6 tiny islands where harvest order
barely matters. 175 m sits safely past the real neighbours:

| threshold | edges | components | largest block |
| --- | --- | --- | --- |
| 100 m | 5 | 6 | 45.9 ha |
| **175 m** | **12** | **3** | **75.5 ha** |
| 400 m | 17 | 3 | 75.5 ha |

Run `print_threshold_sensitivity()` in `graph.py` to regenerate that table.
**If you re-trace the fields, re-check this number before trusting any result.**

**This choice is not settled, and it matters more than any other input.** See the
robustness section below — we treat it as an open question rather than pretending
175 m is proven.

### `simulate.py`

**`HARVEST_RATE_HA_PER_DAY = 8.0`** — how much one combine cuts per working day.
A field of area *A* takes `ceil(A / 8)` whole days. Raising this shortens the
season and therefore lowers *every* fire risk score, so **only compare scores
produced with the same rate.**

### `optimize.py`

**`W1_FIRE = 1.0`** — weight on fire risk (hectares of the largest block).

**`W2_TRAVEL`** — weight on travel (km to reach the next field). The balanced
optimizer picks whichever field minimises `w1 * block_ha + w2 * travel_km`.

**Mind the units.** These are added together but are not on the same scale: the
largest block starts at ~75 ha while the longest single drive is only ~5.6 km. At
`w2 = 0.5` travel can move the score by at most ~2.8 out of ~75 — so it behaves
almost identically to pure fire-only. The real trade-off lives between **w2 = 2 and
w2 = 10**, and saturates past 25:

```
      w2   FIRE RISK    vs naive    TRAVEL    vs naive
     0.0       853.8      +21.9%     25.18      -29.1%
     2.0       857.0      +21.6%     20.07       -2.9%
     5.0       908.8      +16.9%     15.76      +19.2%   <-- our chosen setting
    10.0      1096.2       -0.3%     12.62      +35.3%
    25.0      1223.8      -11.9%     11.17      +42.8%
```

**`W2_CHOSEN = 5.0`** in `main.py` is the setting we present, because it is the
only one that beats the baseline on *both* objectives at once.

### `animate.py`

**`FPS = 2`** — each harvest day is on screen for 0.5 s, so a 24-day season plays
in 12 s. **`HOLD_FRAMES = 8`** freezes the final numbers for 4 s at the end.
(Pillow merges those identical frames into one long frame, so the GIF reports 24
frames with a 4.5 s last frame. Nothing is missing.)

## Reading the animation

| colour | meaning |
| --- | --- |
| red field | standing dry wheat — fuel |
| green field | harvested — stubble, acts as a firebreak |
| **yellow outline** | the largest connected block of standing fuel *right now* — the number we're minimising |
| white **X** + dashes | the field being cut today |
| grey line | fields are adjacent — fire can spread along this |
| red line | adjacency *inside* the highlighted block |

The chart underneath races the three cumulative risk totals against each other.

## Robustness: the assumption we could not settle

`python sensitivity.py`

We measured every pair of fields. The gaps fall into two clumps — fields that
clearly touch (7–12 m) and fields that clearly don't (114 m and up) — with
**nothing in between**. Both readings of that data are defensible:

- **100 m** — the 114–121 m gaps are real barriers. Map splits into 6 islands.
- **175 m** — those gaps are tracing slop or crossable margins. Map has 3 blocks.

We tried to settle it from satellite imagery and couldn't. Google Earth's high-res
imagery for this area is dated December, when the fields are bare and ploughed, so
it shows the *permanent* features but says nothing about *summer* fuel in the gaps.
The gap features themselves are 6–9 m vegetated ditches — which would carry fire
rather than stop it, but we can't confirm their June state.

So instead of guessing, we build a schedule in each world and test every schedule
in **both**:

```
SCHEDULE                            tested @ 100 m    tested @ 175 m   robust?
naive (largest first)                     baseline          baseline   --
fire-only built @ 100 m                       6.2%              2.2%   marginal
balanced(w2=5) built @ 100 m                 -7.4%             -2.9%   NO
fire-only built @ 175 m                     -17.6%             21.9%   NO
balanced(w2=5) built @ 175 m                -33.3%             16.9%   NO
robust (hedges both worlds)                   5.5%              5.5%   YES
```

**Optimising for the wrong world is worse than not optimising at all.** A schedule
built at 175 m scores −17.6% if 100 m is the truth. The two worlds want opposite
opening moves:

- At **100 m** the biggest block is field 13 *alone* (45.9 ha). A single field
  can't be split, so you must start cutting it immediately.
- At **175 m** the biggest block is the 75.5 ha cluster `{nte,4,5,6,7,8,9,10}`,
  and the winning move is cutting `nte` first to snap it in half — 13 can wait.

### The robust schedule

`greedy_robust()` in `sensitivity.py` asks, at every step, *"if I cut this field
next, how bad is the result in the **worse** of the two worlds?"* and minimises
that. Each world's block size is divided by its own day-0 block first, because a
175 m world has inherently bigger blocks and raw hectares aren't comparable.

```
13 -> nte -> 9 -> 12 -> 6 -> 8 -> 10 -> 11 -> 5 -> 7 -> 4     +5.5% in both worlds
```

It opens with 13 *and* takes `nte` second, covering both failure modes. It is the
only schedule that is positive under either assumption — a **minimax** choice, the
standard way to decide when an input can't be pinned down.

### How to close this out

`print_inspection_list()` in `sensitivity.py` prints the complete checklist — it
runs as part of `python sensitivity.py` and `python main.py`. There are exactly
**7 undecided pairs**: gaps wider than 100 m but no wider than 175 m. Every other
pair is adjacent under both rules or separate under both, so resolving these seven
closes the question entirely.

```
PAIR                GAP   MIDPOINT (lat, lon)
nte -- 6        114.2 m   33.738472, 35.881284
nte -- 5        117.4 m   33.735531, 35.883449
nte -- 4        121.2 m   33.731141, 35.886675
5 -- 8          153.1 m   33.735445, 35.886194
9 -- 10         155.9 m   33.734150, 35.894846
4 -- 9          156.2 m   33.731935, 35.888854
5 -- 9          158.3 m   33.731961, 35.888822
```

The function also emits a ready-made Google Earth link per pair, framed at 1500 m
range so **both** fields are in view — zooming in further shows only one field at a
time, which is the mistake we made on our first attempt.

At each location, ask **what is in the gap?**

| what you see | meaning | rule |
| --- | --- | --- |
| paved road, open canal, buildings | real firebreak | **100 m** |
| dry grass, scrub, vegetated ditch | fire crosses it | **175 m** |

Use **both** imagery sources — they answer different halves of the question.
Google Earth's high-res pass here is dated December (bare fields): good for
*permanent* features, useless for summer fuel. For crop state use Sentinel-2 via
[Copernicus Browser](https://browser.dataspace.copernicus.eu/?zoom=15&lat=33.7331&lng=35.8832),
which images the Bekaa every 5 days at 10 m, free — set the date to mid-May–mid-June
and switch to the NDVI layer, where standing wheat is bright and stubble is pale.
10 m pixels won't resolve a 6–9 m ditch, so use Google Earth for the gap feature
itself.

If dry vegetation bridges those gaps → 175 m holds, and the conditional 16.9%
becomes the headline. If a road or canal separates them → 100 m holds, and the
robust schedule is the right answer.

## Two questions the mentor asked

### Does it work for other crops, or just wheat?

Any crop that is **fuel while standing dry** and whose **harvest removes that
fuel**. The model never looks at the crop itself — only at areas, harvest
durations, and which fields touch — so it transfers unchanged:

| crop | in the model |
| --- | --- |
| wheat | fuel — the case we built and measured |
| barley, oats, rye | fuel — same season, same machines, same model |
| lentils, chickpeas | fuel when dry at harvest (lighter load) |
| sunflower | fuel late season — stalks stand after seed harvest |
| hay / dry pasture | fuel — cutting order of meadows works the same way |
| potato, vegetables (irrigated) | **barrier**, not fuel — green and wet at harvest |
| orchards, vines | partial — treat as barrier unless the understorey is dry |

Our own June 2026 imagery proved the barrier case: two of our "wheat" fields
carried an irrigated summer crop that year and acted as firebreaks. In the app,
a mixed farm is handled by not selecting the green fields (they become
barriers in the graph). A per-field crop label with a fuel factor is a small
Phase 3 addition. The only per-crop parameter is the harvest rate (`rate=`
in the solver).

### How much does it save?

We say *exposure reduced*, not *money saved*, because no one has measured the
chance that a fire reaches a given cluster in a season. What the model gives
exactly is the burnable block a fire would find on a **random day** (the
season-average largest connected block):

| world | schedule | burnable block, usual order → plan | less exposed per fire event |
| --- | --- | --- | --- |
| 175 m (cured gaps, e.g. 2025) | exact optimum | 45.6 → 30.4 ha | **15.1 ha ≈ $13,200** |
| 175 m | robust | 45.6 → 43.1 ha | 2.5 ha ≈ $2,200 |
| 100 m (green gaps) | exact optimum | 24.6 → 23.0 ha | 1.5 ha ≈ $1,300 |
| 100 m | robust | 24.6 → 23.2 ha | 1.3 ha ≈ $1,200 |

(at an assumed 3.5 t/ha × $250/t). Expected saving per season = that figure ×
the chance of a fire event; the app's Numbers section has a slider for that
chance so the assumption stays visible. The farmer's cost is $0 either way.

## Modelling assumptions (state these if a judge asks)

1. **One harvester**, working one field at a time at a constant rate.
2. **A field is fuel until it is 100% cut.** A half-cut field still counts as full
   fuel. Deliberately conservative — never claims safety we haven't earned.
3. **Risk on day *d* is measured at the start of the day**, from the fuel standing
   *during* that day. So day 1 always shows the full-map risk and the last day
   still counts the final field.
4. **Travel is straight-line centroid-to-centroid.** A real harvester follows farm
   tracks, so true distance is longer — but for *comparing orderings* it's a fair
   proxy. No depot: getting to the first field and driving home aren't charged,
   since they'd add a near-constant to every ordering.
5. **Fire spreads only between adjacent standing fields.** No wind direction, no
   slope, no ignition probability. A richer model would weight edges by prevailing
   wind — an obvious next step.

## Honest limitations

- **The optimizers are greedy, not optimal.** Each takes the locally best step and
  never backtracks. With 11 fields there are 11! ≈ 39.9 million possible orders, too
  many to check exhaustively. We benchmarked against 4,000 random orders: the median
  random order scores 1096.6 (i.e. the naive baseline is no better than chance),
  and only **0.38%** of random orders beat our balanced result — but the best random
  order found scored 774.2, so **a better schedule than ours exists.** Honest claim:
  *"near-optimal, found in milliseconds."*
- **Peak daily risk (75.5 ha) is identical for every possible ordering**, because on
  day 1 nothing is cut yet. Only the *sum over the season* is controllable. Quote
  total or mean daily exposure, never peak.
- **At w2 = 0.5, balanced (825.0) slightly beat fire-only (853.8) on fire risk.**
  That is not extra intelligence — a pure fire optimizer cannot be beaten on fire by
  adding a competing objective. It is greedy myopia: the small travel term broke a
  tie differently and landed in a better basin. Reproducible, but don't over-claim it.
- **Polygons are hand-traced** in Google Earth, so areas are approximate and
  adjacency depends on tracing quality. Areas are well validated: Google Earth
  reports field 6 as 56,195.15 m² and our parser computes 56,200 m² — agreement to
  about 5 m², independent of our own hand measurements.
- **The adjacency threshold is unresolved and dominates everything.** The spread
  between the best and worst outcome for a single schedule (+21.9% to −17.6%) is
  far larger than the spread between strategies within one world. Fixing this one
  input is worth more than any further optimizer work.

## What we'd do next

1. **Settle the adjacency question** with summer Sentinel-2 imagery — highest value
   by a wide margin.
2. **Replace the global threshold with a verified edge list.** "We checked each
   boundary against satellite imagery" is a stronger claim than any single number.
3. **Weight edges by prevailing wind.** Fire spreads downwind far faster; the Bekaa
   has a consistent summer westerly. This would make the graph directed.
4. **Beat the greedy.** Random sampling found an order scoring 774.2 versus our
   825.0, so better schedules exist. Simulated annealing or a genetic algorithm
   over 11! orderings is very tractable at this size.
