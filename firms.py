"""
FIRMS EVIDENCE -- does the Bekaa actually burn in harvest weeks? (yes: proof)

NASA's FIRMS system publishes every satellite thermal-anomaly detection since
2012 (VIIRS sensor, 375 m pixels) as free per-country CSV files -- no account,
no key. This module downloads Lebanon's archive, clips it to the Bekaa and to
the area around our fields, and produces the evidence chart for the Phase 2
submission: detections spike exactly in the June-July harvest window.

WORDING RULE (from the team plan): these are "thermal anomalies", not
"confirmed wheat fires". VIIRS cannot tell a wildfire from a deliberate
stubble burn, and it misses small fires that ignite and die between overpasses.
Counts are therefore a LOWER BOUND on fire activity. We say all of this out
loud -- it makes the evidence stronger, not weaker.
"""

import io
import math
import os

import numpy as np
import pandas as pd
import requests

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from parse import load_fields, projection_reference

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp"
YEARS = range(2012, 2027)          # VIIRS record starts 2012; 2026 is partial
CACHE_DIR = "firms_cache"          # downloaded CSVs live here, ~1-3 MB each

# The Bekaa valley, generously: from Qab Elias up past Baalbek.
BEKAA_BBOX = dict(lat_min=33.45, lat_max=34.30, lon_min=35.65, lon_max=36.40)

# "Near our fields": within this many km of the study-area centre.
NEAR_RADIUS_KM = 10.0

FIGURE_PATH = "firms_bekaa.png"


# ---------------------------------------------------------------------------
# DOWNLOAD (with a local cache so re-runs are instant and offline-safe)
# ---------------------------------------------------------------------------

def fetch_year(year):
    """One year of Lebanon VIIRS detections as a DataFrame (cached on disk)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"viirs_{year}_lebanon.csv")
    if not os.path.exists(path):
        url = f"{FIRMS_BASE}/{year}/viirs-snpp_{year}_Lebanon.csv"
        r = requests.get(url, timeout=120)
        if r.status_code != 200 or not r.content.startswith(b"latitude"):
            return None                       # year not published (yet)
        with open(path, "wb") as f:
            f.write(r.content)
    df = pd.read_csv(path)
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    return df


def load_lebanon(years=YEARS, verbose=True):
    frames = []
    for y in years:
        df = fetch_year(y)
        if df is None:
            if verbose:
                print(f"  {y}: not available")
            continue
        frames.append(df)
        if verbose:
            print(f"  {y}: {len(df):5d} detections nationwide")
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------------------------

def study_centre():
    """Mean centroid of the study fields, in lon/lat."""
    fields = load_fields(verbose=False)
    ref_lon, ref_lat = projection_reference()
    # projection_reference is the mean of ALL traced polygons (incl. outliers);
    # use the kept fields' own centroids instead.
    lons = [f.poly_ll.centroid.x for f in fields]
    lats = [f.poly_ll.centroid.y for f in fields]
    return sum(lons) / len(lons), sum(lats) / len(lats)


def km_from(df, lon0, lat0):
    """Rough distance (km) from a point -- fine at this scale."""
    kx = 111.32 * math.cos(math.radians(lat0))
    ky = 110.57
    return np.hypot((df["longitude"] - lon0) * kx, (df["latitude"] - lat0) * ky)


def analyse(verbose=True):
    if verbose:
        print("=" * 88)
        print("FIRMS -- Lebanon thermal-anomaly archive (VIIRS, 375 m)")
        print("=" * 88)
    leb = load_lebanon(verbose=verbose)

    bekaa = leb[
        leb["latitude"].between(BEKAA_BBOX["lat_min"], BEKAA_BBOX["lat_max"])
        & leb["longitude"].between(BEKAA_BBOX["lon_min"], BEKAA_BBOX["lon_max"])
    ].copy()
    lon0, lat0 = study_centre()
    bekaa["km_to_fields"] = km_from(bekaa, lon0, lat0)
    near = bekaa[bekaa["km_to_fields"] <= NEAR_RADIUS_KM]

    bekaa["month"] = bekaa["acq_date"].dt.month
    bekaa["year"] = bekaa["acq_date"].dt.year

    monthly = bekaa.groupby("month").size().reindex(range(1, 13), fill_value=0)
    harvest_share = monthly.loc[6:7].sum() / max(monthly.sum(), 1) * 100
    # Two months are 2/12 = 16.7% of a calendar year; how far above that
    # "fair share" do the harvest months sit?
    harvest_multiple = harvest_share / (2 / 12 * 100)

    if verbose:
        y0, y1 = bekaa["year"].min(), bekaa["year"].max()
        print(f"\nBekaa valley: {len(bekaa):,} detections, {y0}-{y1}")
        print(f"Within {NEAR_RADIUS_KM:.0f} km of our fields: {len(near):,}")
        print("\nDETECTIONS BY MONTH (all years):")
        peak = monthly.max()
        for m, cnt in monthly.items():
            bar = "#" * int(cnt / peak * 48)
            mark = "  <-- HARVEST (standing dry wheat)" if m in (6, 7) else ""
            print(f"  {m:>2}  {cnt:>6,}  {bar}{mark}")
        print(f"\nJune+July hold {harvest_share:.0f}% of the year's Bekaa detections "
              f"(~{harvest_multiple:.1f}x their calendar share).")
        print("HONESTY NOTE: August-September are comparably active. Standing wheat")
        print("is gone by then -- much of that later activity is burning of what the")
        print("harvest leaves behind (an interpretation, not a satellite fact). Our")
        print("claim is precise: fire activity is elevated in exactly the weeks when")
        print("standing dry wheat exists and harvest ORDER can still protect it.")
        june_by_year = bekaa[bekaa['month'].isin((6, 7))].groupby('year').size()
        print("June+July detections per year (Bekaa): "
              + ", ".join(f"{y}: {c}" for y, c in june_by_year.items()))

    return bekaa, near, monthly


# ---------------------------------------------------------------------------
# THE FIGURE
# ---------------------------------------------------------------------------

def make_figure(bekaa, near, monthly, out_path=FIGURE_PATH):
    fields = load_fields(verbose=False)
    lon0, lat0 = study_centre()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.6))

    # ---- left: the seasonality bar chart
    colors = ["#c62828" if m in (6, 7) else "#c9b78a" for m in monthly.index]
    ax1.bar(monthly.index, monthly.values, color=colors, edgecolor="#6b4f14",
            linewidth=0.6)
    ax1.set_xticks(range(1, 13),
                   ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    hs = monthly.loc[6:7].sum() / max(monthly.sum(), 1) * 100
    y0, y1 = int(bekaa["year"].min()), int(bekaa["year"].max())
    ax1.set_title(f"When the Bekaa burns: detections by month, {y0}-{y1}\n"
                  f"June+July = {hs:.0f}% of the year (~{hs / (200 / 12):.1f}x "
                  f"their calendar share) -- while dry wheat is standing",
                  fontsize=12, fontweight="bold")
    ax1.set_ylabel("thermal-anomaly detections (VIIRS)")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.4)

    # ---- right: where they are, relative to our fields
    jj = bekaa[bekaa["month"].isin((6, 7))]
    ax2.scatter(jj["longitude"], jj["latitude"], s=5, color="#c62828",
                alpha=0.35, label="June-July detection")
    other = bekaa[~bekaa["month"].isin((6, 7))]
    ax2.scatter(other["longitude"], other["latitude"], s=3, color="#9e9e9e",
                alpha=0.2, label="other months")
    for f in fields:
        xs, ys = f.poly_ll.exterior.xy
        ax2.fill(xs, ys, facecolor="#e8c56a", edgecolor="#6b4f14",
                 linewidth=1.0, zorder=5)
    circle = plt.Circle((lon0, lat0), NEAR_RADIUS_KM / 105.0, fill=False,
                        color="#1e88e5", linewidth=1.6, linestyle="--", zorder=6)
    ax2.add_patch(circle)
    ax2.annotate(f"our fields\n({len(near):,} detections within "
                 f"{NEAR_RADIUS_KM:.0f} km)", (lon0, lat0),
                 textcoords="offset points", xytext=(14, 18), fontsize=10,
                 fontweight="bold", zorder=7,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#555"))
    ax2.set_xlim(BEKAA_BBOX["lon_min"], BEKAA_BBOX["lon_max"])
    ax2.set_ylim(BEKAA_BBOX["lat_min"], BEKAA_BBOX["lat_max"])
    ax2.set_aspect(1 / math.cos(math.radians(lat0)))
    ax2.set_title(f"Where: the Bekaa valley, {y0}-{y1}\nred = June-July "
                  "(harvest weeks)", fontsize=12, fontweight="bold")
    ax2.legend(loc="lower left", fontsize=9)
    ax2.set_xticks([]); ax2.set_yticks([])

    fig.suptitle("Satellite record: the Bekaa's fire season begins in the "
                 "harvest weeks -- the only weeks a harvest order can protect",
                 fontsize=13, fontweight="bold")
    note = ("Detections are thermal anomalies (VIIRS, 375 m): they include deliberate stubble burns and MISS "
            "fires smaller than ~0.1 ha, so counts are a lower bound on fire activity. Source: NASA FIRMS.")
    fig.text(0.5, 0.015, note, ha="center", fontsize=8.5, color="#555")
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"\nSaved figure -> {out_path}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    bekaa, near, monthly = analyse()
    make_figure(bekaa, near, monthly)
