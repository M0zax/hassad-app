"""
SATELLITE GAP CHECK -- the Phase 2 evidence that settles the adjacency question.

THE QUESTION THIS FILE ANSWERS
------------------------------
Seven gaps between our fields (114-158 m wide) decide whether the fire graph
uses the 100 m rule (gaps are barriers) or the 175 m rule (gaps are crossable
fuel). December imagery couldn't answer it: every field looks the same when
bare. What matters is the state of those gaps DURING HARVEST WEEKS (June):

    corridor stays GREEN in June  -> living, moist vegetation -> fire-resistant
    corridor is CURED (dry) in June -> dead fine fuel -> fire crosses it

We measure that with NDVI (plant "greenness", from red + near-infrared light)
and NDMI (plant water content, from near-infrared + shortwave-infrared) using
free Sentinel-2 imagery (10 m pixels, revisit every ~5 days).

HONESTY NOTE, for judges and for ourselves: NDVI low does not automatically
mean "fuel" -- asphalt and water are also low-NDVI but they are barriers. Our
December inspection already showed these specific gaps are vegetated
ditches/margins, not roads or canals, so for THESE gaps "cured" does mean
"dead plant material", i.e. fuel. We print that caveat rather than hiding it.

DATA ACCESS
-----------
Sentinel-2 L2A scenes from the AWS Open Data archive through the Earth Search
STAC API (element84). Both are public: no account, no key, no cost. We read
only small windows around our fields from the cloud-optimised GeoTIFFs, so a
full run downloads a few megabytes, not gigabytes.
"""

import json
import math

import numpy as np
import requests
import rasterio
from rasterio.windows import from_bounds
from rasterio.features import geometry_mask
from pyproj import Transformer
from shapely.geometry import LineString, mapping
from shapely.ops import nearest_points, transform as shp_transform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from parse import load_fields, make_unprojector, projection_reference

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

STAC_API = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-c1-l2a"      # the maintained Sentinel-2 collection

# The two rival adjacency thresholds (must match graph.py / sensitivity.py).
GAP_MIN_M, GAP_MAX_M = 100.0, 175.0

# Harvest-season window we sample each year: wheat in the Bekaa is cut in
# June, so this is when standing fuel, stubble and gap vegetation coexist.
SEASON_START, SEASON_END = "06-01", "07-05"
YEARS = (2024, 2025, 2026)
MAX_SCENES_PER_YEAR = 3               # lowest-cloud scenes per summer
MAX_CLOUD_PCT = 20.0

# Corridor geometry: we sample a strip across each gap, this wide (metres) on
# each side of the line joining the two fields' closest points...
CORRIDOR_HALF_WIDTH_M = 30.0
# ...and we push the strip this far away from each field's edge, so 10 m
# pixels that straddle a field boundary don't contaminate the corridor.
FIELD_EDGE_MARGIN_M = 12.0

# NDVI verdict thresholds (median over corridor pixels).
#   Bare soil / senescent (dead) vegetation is typically < 0.2-0.25;
#   healthy green vegetation is typically > 0.4. Between = sparse/mixed.
NDVI_GREEN = 0.40
NDVI_CURED = 0.25

# Sentinel-2 L2A surface reflectance scaling (values are ints of 1e-4,
# with a +0.1 offset baked in since the 2022 processing baseline).
S2_SCALE, S2_OFFSET = 1.0e-4, -0.1

# Scene Classification Layer classes we EXCLUDE as invalid pixels.
SCL_INVALID = {0, 1, 3, 8, 9, 10, 11}   # nodata, saturated, shadow, clouds, cirrus, snow

FIGURE_PATH = "satellite_gaps.png"
RESULTS_JSON = "satellite_gaps_results.json"


# ---------------------------------------------------------------------------
# STEP 1 -- the seven corridors, as lon/lat polygons
# ---------------------------------------------------------------------------

def build_corridors():
    """
    For every pair of fields whose gap is between GAP_MIN_M and GAP_MAX_M
    (the undecided pairs), build the corridor polygon we will sample:
    a strip across the gap, trimmed clear of both fields' edges.

    Returns a list of dicts: {pair, gap_m, poly_ll (lon/lat polygon)}.
    """
    fields = load_fields(verbose=False)
    ref_lon, ref_lat = projection_reference()
    unproject = make_unprojector(ref_lon, ref_lat)

    corridors = []
    for i, a in enumerate(fields):
        for b in fields[i + 1:]:
            gap = a.poly_m.distance(b.poly_m)
            if not (GAP_MIN_M < gap <= GAP_MAX_M):
                continue
            pa, pb = nearest_points(a.poly_m, b.poly_m)
            strip = LineString([pa, pb]).buffer(CORRIDOR_HALF_WIDTH_M, cap_style="flat")
            # keep the strip away from the fields themselves
            strip = strip.difference(a.poly_m.buffer(FIELD_EDGE_MARGIN_M))
            strip = strip.difference(b.poly_m.buffer(FIELD_EDGE_MARGIN_M))
            poly_ll = shp_transform(lambda x, y, z=None: unproject(x, y), strip)
            corridors.append({"pair": f"{a.name}--{b.name}", "gap_m": gap,
                              "poly_ll": poly_ll})
    corridors.sort(key=lambda c: c["gap_m"])
    return corridors


# ---------------------------------------------------------------------------
# STEP 2 -- find good harvest-season scenes for each year
# ---------------------------------------------------------------------------

def find_scenes(bbox):
    """
    Ask the Earth Search STAC API for low-cloud scenes in the harvest window
    of each year. Returns {year: [item, ...]} with at most MAX_SCENES_PER_YEAR
    items per year, deduplicated by date (lowest cloud first).
    """
    out = {}
    for year in YEARS:
        body = {
            "collections": [COLLECTION],
            "bbox": bbox,
            "datetime": f"{year}-{SEASON_START}T00:00:00Z/{year}-{SEASON_END}T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": MAX_CLOUD_PCT}},
            "limit": 100,
        }
        items = requests.post(STAC_API, json=body, timeout=60).json()["features"]

        # Spread the picks across the harvest window instead of just taking the
        # least cloudy dates: three scenes from the same week would miss a
        # harvest that happens the week after. Split the window into
        # MAX_SCENES_PER_YEAR equal date-bins and take the lowest-cloud scene
        # in each bin.
        from datetime import date as _date
        start = _date.fromisoformat(f"{year}-{SEASON_START}")
        end = _date.fromisoformat(f"{year}-{SEASON_END}")
        span = max((end - start).days, 1)

        bins = {}
        for it in items:
            d = _date.fromisoformat(it["properties"]["datetime"][:10])
            k = min(int((d - start).days / span * MAX_SCENES_PER_YEAR),
                    MAX_SCENES_PER_YEAR - 1)
            best = bins.get(k)
            if best is None or (it["properties"].get("eo:cloud_cover", 100.0)
                                < best["properties"].get("eo:cloud_cover", 100.0)):
                bins[k] = it

        picked = sorted(bins.values(), key=lambda it: it["properties"]["datetime"])
        out[year] = picked
    return out


def _asset_href(item, *names):
    """Return the first matching asset href (asset names differ per collection)."""
    for n in names:
        if n in item["assets"]:
            return item["assets"][n]["href"]
    raise KeyError(f"none of {names} in assets: {list(item['assets'])[:12]}")


def _scene_epsg(item):
    p = item["properties"]
    if "proj:epsg" in p:
        return int(p["proj:epsg"])
    if "proj:code" in p:
        return int(str(p["proj:code"]).split(":")[-1])
    raise KeyError("scene has no proj:epsg / proj:code")


# ---------------------------------------------------------------------------
# STEP 3 -- read the pixels and score each corridor
# ---------------------------------------------------------------------------

def _read_window(href, bounds_utm, out_shape=None):
    """
    Read one band inside a UTM bounding box straight from the cloud-optimised
    GeoTIFF on AWS -- only the needed bytes travel over the network.
    Returns (array, window transform).
    """
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
        with rasterio.open(href) as src:
            win = from_bounds(*bounds_utm, transform=src.transform)
            data = src.read(1, window=win,
                            out_shape=out_shape,
                            boundless=True, fill_value=0)
            tr = src.window_transform(win)
            if out_shape is not None:
                # window_transform describes the native grid; rescale for out_shape
                sx = win.width / out_shape[1]
                sy = win.height / out_shape[0]
                tr = tr * tr.scale(sx, sy)
    return data.astype("float32"), tr


def score_scene(item, corridors_ll, pad_m=200.0):
    """
    For one scene: read red / NIR / SWIR16 / SCL windows covering all
    corridors, compute NDVI + NDMI, and return per-corridor statistics.
    """
    epsg = _scene_epsg(item)
    to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True).transform

    corridors = [dict(c, poly_utm=shp_transform(to_utm, c["poly_ll"]))
                 for c in corridors_ll]

    xs, ys = [], []
    for c in corridors:
        x0, y0, x1, y1 = c["poly_utm"].bounds
        xs += [x0, x1]; ys += [y0, y1]
    bounds = (min(xs) - pad_m, min(ys) - pad_m, max(xs) + pad_m, max(ys) + pad_m)

    red, tr = _read_window(_asset_href(item, "red", "B04"), bounds)
    nir, _ = _read_window(_asset_href(item, "nir", "B08"), bounds)
    swir, _ = _read_window(_asset_href(item, "swir16", "B11"), bounds, out_shape=red.shape)
    scl, _ = _read_window(_asset_href(item, "scl", "SCL"), bounds, out_shape=red.shape)

    red_r = red * S2_SCALE + S2_OFFSET
    nir_r = nir * S2_SCALE + S2_OFFSET
    swir_r = swir * S2_SCALE + S2_OFFSET

    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (nir_r - red_r) / (nir_r + red_r)
        ndmi = (nir_r - swir_r) / (nir_r + swir_r)

    valid = ~np.isin(scl, list(SCL_INVALID)) & (red > 0) & (nir > 0)

    results = []
    for c in corridors:
        mask = ~geometry_mask([mapping(c["poly_utm"])], out_shape=ndvi.shape,
                              transform=tr)   # True inside the corridor
        ok = mask & valid & np.isfinite(ndvi)
        n = int(ok.sum())
        results.append({
            "pair": c["pair"], "gap_m": c["gap_m"],
            "n_pixels": n,
            "ndvi_median": float(np.median(ndvi[ok])) if n else None,
            "ndvi_p25": float(np.percentile(ndvi[ok], 25)) if n else None,
            "ndvi_p75": float(np.percentile(ndvi[ok], 75)) if n else None,
            "ndmi_median": float(np.median(ndmi[ok])) if n else None,
        })
    chips = {"ndvi": ndvi, "transform": tr, "valid": valid}
    return results, chips, corridors


def verdict_for(ndvi_median):
    if ndvi_median is None:
        return "NO DATA"
    if ndvi_median >= NDVI_GREEN:
        return "GREEN barrier"
    if ndvi_median <= NDVI_CURED:
        return "CURED (fuel)"
    return "MIXED"


# ---------------------------------------------------------------------------
# STEP 4 -- run everything, decide, report
# ---------------------------------------------------------------------------

def run_gap_check(make_figure=True, verbose=True):
    corridors = build_corridors()
    if verbose:
        print("=" * 92)
        print("SATELLITE GAP CHECK -- are the 7 undecided gaps green or cured in June?")
        print("=" * 92)
        print(f"{len(corridors)} corridors "
              f"(gaps {GAP_MIN_M:.0f}-{GAP_MAX_M:.0f} m), sampled "
              f"{CORRIDOR_HALF_WIDTH_M*2:.0f} m wide, {FIELD_EDGE_MARGIN_M:.0f} m clear "
              f"of field edges")

    lons = [c["poly_ll"].centroid.x for c in corridors]
    lats = [c["poly_ll"].centroid.y for c in corridors]
    bbox = [min(lons) - 0.02, min(lats) - 0.02, max(lons) + 0.02, max(lats) + 0.02]

    scenes = find_scenes(bbox)
    per_gap = {c["pair"]: {} for c in corridors}   # pair -> year -> list of stats
    chip_store = {}                                # (year) -> (chips, corridors) best scene

    for year, items in scenes.items():
        if verbose:
            print(f"\n{year}: {len(items)} scene(s) "
                  + ", ".join(f"{it['properties']['datetime'][:10]} "
                              f"({it['properties']['eo:cloud_cover']:.0f}% cloud)"
                              for it in items))
        for k, item in enumerate(items):
            stats, chips, cors = score_scene(item, corridors)
            date = item["properties"]["datetime"][:10]
            if k == 0:
                chip_store[year] = (chips, cors, date)
            for s in stats:
                per_gap[s["pair"]].setdefault(year, []).append(dict(s, date=date))

    # ---- aggregate: median of scene-medians per gap per year, then verdicts
    summary = []
    for c in corridors:
        pair = c["pair"]
        year_medians = {}
        for year in YEARS:
            meds = [s["ndvi_median"] for s in per_gap[pair].get(year, [])
                    if s["ndvi_median"] is not None]
            year_medians[year] = float(np.median(meds)) if meds else None
        vals = [v for v in year_medians.values() if v is not None]
        overall = float(np.median(vals)) if vals else None
        summary.append({
            "pair": pair, "gap_m": round(c["gap_m"], 1),
            "ndvi_by_year": year_medians,
            "ndvi_overall": overall,
            "verdict": verdict_for(overall),
        })

    # ---- print the table
    if verbose:
        print()
        print(f"{'PAIR':<12}{'GAP':>8}" + "".join(f"{y:>9}" for y in YEARS)
              + f"{'OVERALL':>10}   VERDICT (June NDVI, median)")
        print("-" * 92)
        for s in summary:
            row = f"{s['pair']:<12}{s['gap_m']:>6.0f} m"
            for y in YEARS:
                v = s["ndvi_by_year"][y]
                row += f"{v:>9.2f}" if v is not None else f"{'--':>9}"
            ov = s["ndvi_overall"]
            row += f"{ov:>10.2f}" if ov is not None else f"{'--':>10}"
            print(row + f"   {s['verdict']}")
        print("-" * 92)
        print(f"thresholds: median NDVI >= {NDVI_GREEN} -> GREEN barrier | "
              f"<= {NDVI_CURED} -> CURED fuel | between -> MIXED")

    decision = decide(summary, verbose=verbose)

    with open(RESULTS_JSON, "w") as f:
        json.dump({"summary": summary, "decision": decision}, f, indent=1)
    if verbose:
        print(f"\nSaved raw results -> {RESULTS_JSON}")

    if make_figure and chip_store:
        make_gap_figure(chip_store, corridors, summary)

    return summary, decision


def decide(summary, verbose=True):
    """
    Turn per-gap NDVI into the adjacency decision -- PER YEAR.

    Why per year: the first run of this check revealed that neither world is
    constant. The hinge question is whether 'nte' connects to the 4-5-6-7
    chain, which happens if ANY of the three parallel nte gaps is crossable
    (paths in parallel: one open door is enough). A gap is 'crossable' in a
    given June if its median NDVI is at or below NDVI_CURED, a 'barrier' if
    at or above NDVI_GREEN.
    """
    nte_gaps = [s for s in summary if s["pair"].startswith("nte")]
    other_gaps = [s for s in summary if not s["pair"].startswith("nte")]

    per_year = {}
    for year in YEARS:
        vals = {s["pair"]: s["ndvi_by_year"].get(year) for s in nte_gaps}
        known = {p: v for p, v in vals.items() if v is not None}
        if not known:
            per_year[year] = "NO DATA"
        elif any(v <= NDVI_CURED for v in known.values()):
            per_year[year] = "CONNECTED (a hinge gap was cured -> 175 m world)"
        elif all(v >= NDVI_GREEN for v in known.values()):
            per_year[year] = "SEPARATED (all hinge gaps green -> 100 m world)"
        else:
            per_year[year] = "AMBIGUOUS (hinge gaps in the mixed NDVI band)"

    connected_years = [y for y, v in per_year.items() if v.startswith("CONNECTED")]
    separated_years = [y for y, v in per_year.items() if v.startswith("SEPARATED")]

    if connected_years and separated_years:
        world = ("SEASONAL -- the adjacency changes from year to year "
                 f"(connected in {connected_years}, separated in {separated_years})")
    elif connected_years and not separated_years:
        world = "175 m world in every observed year"
    elif separated_years and not connected_years:
        world = "100 m world in every observed year"
    else:
        world = "UNRESOLVED (ambiguous in every observed year)"

    headline = ("Guaranteed 5.5% less fire exposure under any assumption "
                "(robust schedule); up to 33% in a year whose gaps are cured "
                "(e.g. observed in " + ", ".join(map(str, connected_years)) + ")"
                if connected_years else
                "Guaranteed 5.5% less fire exposure under any assumption "
                "(robust schedule)")

    decision = {
        "per_year": per_year,
        "nte_gaps": {s["pair"]: s["verdict"] for s in nte_gaps},
        "other_gaps": {s["pair"]: s["verdict"] for s in other_gaps},
        "supported_world": world,
        "headline_number": headline,
    }
    if verbose:
        print()
        print("DECISION (per year -- one cured hinge gap is enough to connect)")
        print("-" * 92)
        for y, v in per_year.items():
            print(f"  June {y}: {v}")
        print(f"  => {world}")
        print(f"  => headline: {headline}")
        print()
        print("  Caveat we say out loud: NDVI classifies green vs cured. 'Cured' means")
        print("  dead fine fuel here because our December imagery already showed these")
        print("  gaps are vegetated margins, not roads or canals.")
    return decision


# ---------------------------------------------------------------------------
# STEP 5 -- the figure for the submission
# ---------------------------------------------------------------------------

def make_gap_figure(chip_store, corridors, summary, out_path=FIGURE_PATH):
    """One NDVI map per year (best scene), corridors outlined and labelled."""
    years = sorted(chip_store)
    fig, axes = plt.subplots(1, len(years), figsize=(7.2 * len(years), 7.6))
    if len(years) == 1:
        axes = [axes]

    verdict_by_pair = {s["pair"]: s["verdict"] for s in summary}
    for ax, year in zip(axes, years):
        chips, cors, date = chip_store[year]
        ndvi = np.where(chips["valid"], chips["ndvi"], np.nan)
        tr = chips["transform"]
        h, w = ndvi.shape
        extent = (tr.c, tr.c + tr.a * w, tr.f + tr.e * h, tr.f)
        im = ax.imshow(ndvi, cmap="RdYlGn", vmin=0.0, vmax=0.7, extent=extent)
        for c in cors:
            poly = c["poly_utm"]
            geoms = getattr(poly, "geoms", [poly])
            for g in geoms:
                xs, ys = g.exterior.xy
                ax.plot(xs, ys, color="#1a1a1a", linewidth=1.8)
            cx, cy = poly.centroid.x, poly.centroid.y
            v = verdict_by_pair.get(c["pair"], "")
            short = {"GREEN barrier": "GREEN", "CURED (fuel)": "CURED",
                     "MIXED": "MIXED", "NO DATA": "?"}.get(v, v)
            ax.annotate(f"{c['pair']}\n{short}", (cx, cy),
                        textcoords="offset points", xytext=(0, 14),
                        ha="center", fontsize=8, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                  ec="#555", alpha=0.9))
        ax.set_title(f"June {year} ({date})", fontsize=12, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])

    fig.suptitle(
        "The 7 contested gaps at harvest time -- NDVI from Sentinel-2\n"
        "green = living vegetation (fire barrier) | red/yellow = cured or bare "
        "(fire can cross)", fontsize=13, fontweight="bold")
    cbar = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
    cbar.set_label("NDVI")
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure -> {out_path}")


# ---------------------------------------------------------------------------
# BONUS EVIDENCE -- what each FIELD was doing each June (found by accident,
# kept on purpose)
# ---------------------------------------------------------------------------
#
# While validating the gap numbers against the fields themselves, the data
# showed something bigger than the validation: the fields change identity from
# year to year (crop rotation). In June 2026 fields 4-7 and 10-12 crashed from
# NDVI ~0.6 to ~0.25 in 17 days -- that is the harvest itself, visible from
# space -- while 'nte' and '9' stayed at 0.8+ (an irrigated summer crop: not
# fuel at all that year) and '13' went bare-then-green (planted in June).
#
# Consequence for the model: the fuel map (which fields are dry wheat AND
# which gaps are cured) must be read from the satellite EACH season. That is
# not a weakness -- it is the product: Hassad reads the year's actual fuel map
# and optimises for it.

FIELD_FIG_PATH = "satellite_fields.png"

# Field-year classification thresholds (three samples per June window).
FIELD_GREEN_ALL = 0.50     # never drops below -> living irrigated crop, a barrier
FIELD_LOW_ALL = 0.25       # never rises above -> bare / harvested before window
FIELD_DROP_MIN = 0.15      # start-to-end fall at least this -> harvest happened


def field_state_check(verbose=True, make_figure=True):
    """NDVI trajectory for every field's interior, each scene, each year."""
    fields = load_fields(verbose=False)
    ref_lon, ref_lat = projection_reference()
    unproject = make_unprojector(ref_lon, ref_lat)

    zones = []
    for f in fields:
        interior = f.poly_m.buffer(-20)
        if interior.is_empty:
            interior = f.poly_m.buffer(-8)
        zones.append({"pair": f.name, "gap_m": 0,
                      "poly_ll": shp_transform(lambda x, y, z=None: unproject(x, y),
                                               interior)})

    lons = [z["poly_ll"].centroid.x for z in zones]
    lats = [z["poly_ll"].centroid.y for z in zones]
    bbox = [min(lons) - 0.02, min(lats) - 0.02, max(lons) + 0.02, max(lats) + 0.02]
    scenes = find_scenes(bbox)

    names = [z["pair"] for z in zones]
    rows = []          # (date, {field: ndvi})
    for year, items in scenes.items():
        for item in items:
            stats, _, _ = score_scene(item, zones)
            rows.append((item["properties"]["datetime"][:10],
                         {s["pair"]: s["ndvi_median"] for s in stats}))
    rows.sort()

    # classify each field-year from its first and last valid samples
    states = {}
    for year in YEARS:
        ystr = str(year)
        for n in names:
            vals = [(d, by[n]) for d, by in rows
                    if d.startswith(ystr) and by[n] is not None]
            if not vals:
                states[(year, n)] = "no data"
                continue
            first, last = vals[0][1], vals[-1][1]
            lo, hi = min(v for _, v in vals), max(v for _, v in vals)
            if lo >= FIELD_GREEN_ALL:
                states[(year, n)] = "GREEN CROP (barrier, not fuel)"
            elif hi <= FIELD_LOW_ALL:
                states[(year, n)] = "bare / cut before June"
            elif first - last >= FIELD_DROP_MIN and last <= 0.30:
                states[(year, n)] = "HARVESTED during June (seen from space)"
            else:
                states[(year, n)] = "mixed / uncertain"

    if verbose:
        print()
        print("FIELD STATE BY YEAR (from the same imagery)")
        print("-" * 92)
        print("  date       " + "".join(f"{n:>6}" for n in names))
        for d, by in rows:
            print(f"  {d} " + "".join(
                f"{by[n]:>6.2f}" if by[n] is not None else f"{'--':>6}" for n in names))
        print()
        for year in YEARS:
            print(f"  {year}:")
            for n in names:
                print(f"    {n:<5} {states[(year, n)]}")

    if make_figure:
        _field_figure(rows, names, out_path=FIELD_FIG_PATH)

    return rows, states


def _field_figure(rows, names, out_path):
    """Heatmap: fields x scene dates, colored by NDVI -- rotation at a glance."""
    data = np.array([[by[n] if by[n] is not None else np.nan for _, by in rows]
                     for n in names])
    fig, ax = plt.subplots(figsize=(1.05 * len(rows) + 3, 6.2))
    im = ax.imshow(data, cmap="RdYlGn", vmin=0.0, vmax=0.9, aspect="auto")
    ax.set_yticks(range(len(names)), names)
    ax.set_xticks(range(len(rows)), [d for d, _ in rows], rotation=45, ha="right")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if np.isfinite(data[i, j]):
                ax.text(j, i, f"{data[i, j]:.2f}", ha="center", va="center",
                        fontsize=8,
                        color="#111" if 0.25 < data[i, j] < 0.75 else "#eee")
    ax.set_title("What each field was doing, June by June (NDVI from Sentinel-2)\n"
                 "green = living crop | red = bare or freshly cut stubble",
                 fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, label="NDVI", fraction=0.03)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"Saved field-state figure -> {out_path}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    summary, decision = run_gap_check()
    rows, states = field_state_check()

    # keep everything in one JSON for Team B
    with open(RESULTS_JSON, "w") as f:
        json.dump({
            "summary": summary,
            "decision": decision,
            "field_ndvi": [{"date": d, **by} for d, by in rows],
            "field_states": {f"{y}:{n}": s for (y, n), s in states.items()},
        }, f, indent=1)
    print(f"Updated {RESULTS_JSON} with field states")
