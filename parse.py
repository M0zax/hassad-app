"""
STAGE 1 -- Parse & validate the KML of wheat fields.

What this module does:
  1. Reads the KML file exported from Google Earth.
  2. Extracts (name, polygon) for every placemark that actually has a <Polygon>.
  3. Projects the lon/lat degrees into local METERS so we can do real geometry
     (areas in hectares, distances in metres) instead of degree-math.
  4. Computes each field's area (ha) and centroid.
  5. Filters out the far-away outlier fields so we study one contiguous cluster.

Written for the FIRST Global Challenge 2026 "Harvest-Sequencing Optimizer".
Kept deliberately simple and heavily commented -- this is a student prototype.
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from shapely.geometry import Polygon

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# The KML file our team traced in Google Earth.
KML_FILE = "nte (1).kml"

# Name of the field we treat as the "anchor" of the study area. Every other
# field must have its centroid within STUDY_RADIUS_KM of this field's centroid,
# otherwise we drop it as an outlier (our team accidentally traced two fields
# ~17-24 km away, which are not part of the same fire-spread neighbourhood).
ANCHOR_FIELD = "nte"

# Radius of the study area, in kilometres, measured from ANCHOR_FIELD's centroid.
# Fields further than this are excluded (and reported) -- fire cannot realistically
# spread between fields tens of kilometres apart, so they'd pollute the model.
STUDY_RADIUS_KM = 6.0

# KML uses an XML namespace; ElementTree needs it spelled out to find tags.
KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


# ---------------------------------------------------------------------------
# THE FIELD RECORD
# ---------------------------------------------------------------------------

@dataclass
class Field:
    """One wheat field: its name, its shape, and the numbers we derived from it."""

    name: str            # e.g. "nte", "5", "13"
    poly_m: Polygon      # shape in local METRES (use this for all geometry)
    poly_ll: Polygon     # shape in raw lon/lat degrees (kept for reference/debug)
    area_ha: float       # area in hectares (1 ha = 10,000 m^2)
    cx: float            # centroid x, metres
    cy: float            # centroid y, metres

    def __repr__(self):
        return f"Field({self.name!r}, {self.area_ha:.1f} ha)"


# ---------------------------------------------------------------------------
# PROJECTION: degrees -> metres
# ---------------------------------------------------------------------------
#
# Latitude/longitude are ANGLES, so you cannot measure area or distance with them
# directly (1 degree of longitude is ~93 km at the equator but ~0 km at the pole).
# We use a "local equirectangular" projection: pick a reference point in the middle
# of our farmland, then treat the small patch of Earth around it as flat.
#
# Over a study area only a few km wide this is accurate to well under 1%, which is
# far better than the accuracy of hand-tracing polygons in Google Earth.
#
# The two formulas below are the standard WGS84 approximations for how many metres
# one degree of latitude / longitude is worth at a given latitude.

def metres_per_degree(lat_deg):
    """Return (metres per degree of latitude, metres per degree of longitude)."""
    lat = math.radians(lat_deg)
    m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat) + 1.175 * math.cos(4 * lat)
    m_per_deg_lon = 111412.84 * math.cos(lat) - 93.5 * math.cos(3 * lat)
    return m_per_deg_lat, m_per_deg_lon


def make_projector(ref_lon, ref_lat):
    """
    Build a function that converts (lon, lat) degrees -> (x, y) metres,
    with the origin (0, 0) placed at the reference point.
    """
    m_lat, m_lon = metres_per_degree(ref_lat)

    def project(lon, lat):
        x = (lon - ref_lon) * m_lon
        y = (lat - ref_lat) * m_lat
        return (x, y)

    return project


def make_unprojector(ref_lon, ref_lat):
    """
    The exact inverse of make_projector: (x, y) metres -> (lon, lat) degrees.

    Needed whenever we compute something in metres (e.g. the midpoint of the gap
    between two fields) but want to hand a human a coordinate they can paste into
    Google Earth.
    """
    m_lat, m_lon = metres_per_degree(ref_lat)

    def unproject(x, y):
        return (ref_lon + x / m_lon, ref_lat + y / m_lat)

    return unproject


def projection_reference(kml_path=KML_FILE):
    """
    The reference point load_fields() uses for its projection: the mean centroid
    of every polygon in the KML.

    Exposed as its own function so other modules can rebuild the SAME projection
    (and therefore the same inverse) instead of guessing at it.
    """
    raw_polys, _ = read_placemarks(kml_path)
    ref_lon = sum(p.centroid.x for _, p in raw_polys) / len(raw_polys)
    ref_lat = sum(p.centroid.y for _, p in raw_polys) / len(raw_polys)
    return ref_lon, ref_lat


# ---------------------------------------------------------------------------
# KML READING
# ---------------------------------------------------------------------------

def _ring_coords(ring_elem):
    """
    Turn a KML <LinearRing> element into a list of (lon, lat) tuples.

    KML coordinate text looks like:  "35.88,33.73,0 35.87,33.73,0 ..."
    i.e. lon,lat,altitude triples separated by whitespace. We ignore altitude.
    """
    text = ring_elem.find(".//kml:coordinates", KML_NS).text
    points = []
    for triple in text.split():
        lon, lat, *_ = triple.split(",")
        points.append((float(lon), float(lat)))
    return points


def read_placemarks(kml_path):
    """
    Read every <Placemark> that contains a <Polygon>.

    Returns a list of (name, shapely Polygon in lon/lat) and a list of the
    names we skipped because they had no polygon at all.

    DATA ISSUE HANDLED HERE: one placemark ("Untitled measurement") was traced
    as a <LineString> (a measuring tape, not a field), so it has no <Polygon>
    and must be skipped.
    """
    tree = ET.parse(kml_path)
    root = tree.getroot()

    polygons = []      # list of (name, Polygon in degrees)
    skipped = []       # names of placemarks with no polygon

    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        name_elem = pm.find("kml:name", KML_NS)
        # .strip() matters: one field is literally named "nte3 " with a trailing space.
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else "(unnamed)"

        poly_elem = pm.find(".//kml:Polygon", KML_NS)
        if poly_elem is None:
            skipped.append(name)
            continue

        outer_elem = poly_elem.find(".//kml:outerBoundaryIs/kml:LinearRing", KML_NS)
        if outer_elem is None:
            skipped.append(name)
            continue

        shell = _ring_coords(outer_elem)
        # Holes are unlikely in hand-traced fields, but support them anyway.
        holes = [
            _ring_coords(r)
            for r in poly_elem.findall(".//kml:innerBoundaryIs/kml:LinearRing", KML_NS)
        ]

        polygons.append((name, Polygon(shell, holes)))

    return polygons, skipped


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT FOR STAGE 1
# ---------------------------------------------------------------------------

def load_fields(kml_path=KML_FILE, verbose=True):
    """
    Do the whole of Stage 1 and return the list of Field objects inside the
    study area, sorted by name.

    Steps: read KML -> project to metres -> compute area/centroid -> drop outliers.
    """
    raw_polys, skipped = read_placemarks(kml_path)

    if verbose:
        print("=" * 74)
        print("STAGE 1 -- PARSE & VALIDATE")
        print("=" * 74)
        print(f"KML file            : {kml_path}")
        print(f"Placemarks with a polygon : {len(raw_polys)}")
        for name in skipped:
            print(f"  SKIPPED (no <Polygon> in this placemark): {name!r}")

    # --- pick a projection reference point: the average of all polygon centroids.
    # Using the middle of the data keeps distortion as small as possible.
    # (Same formula as projection_reference(), kept in step with it.)
    ref_lon = sum(p.centroid.x for _, p in raw_polys) / len(raw_polys)
    ref_lat = sum(p.centroid.y for _, p in raw_polys) / len(raw_polys)
    project = make_projector(ref_lon, ref_lat)

    if verbose:
        print(f"Projection reference: lon {ref_lon:.5f}, lat {ref_lat:.5f} "
              f"(local equirectangular, units = metres)")

    # --- build Field objects in projected metres
    all_fields = []
    for name, poly_ll in raw_polys:
        poly_m = Polygon(
            [project(lon, lat) for lon, lat in poly_ll.exterior.coords],
            [[project(lon, lat) for lon, lat in ring.coords] for ring in poly_ll.interiors],
        )
        # buffer(0) is the classic shapely trick to repair self-intersecting
        # ("bow-tie") polygons that hand-tracing sometimes produces.
        if not poly_m.is_valid:
            poly_m = poly_m.buffer(0)
            if verbose:
                print(f"  NOTE: repaired self-intersecting polygon for field {name!r}")

        c = poly_m.centroid
        all_fields.append(
            Field(
                name=name,
                poly_m=poly_m,
                poly_ll=poly_ll,
                area_ha=poly_m.area / 10_000.0,   # m^2 -> hectares
                cx=c.x,
                cy=c.y,
            )
        )

    # --- filter to the study area (drop the far-away outliers)
    anchor = next((f for f in all_fields if f.name == ANCHOR_FIELD), None)
    if anchor is None:
        raise ValueError(f"Anchor field {ANCHOR_FIELD!r} not found in the KML.")

    kept, dropped = [], []
    for f in all_fields:
        dist_km = math.hypot(f.cx - anchor.cx, f.cy - anchor.cy) / 1000.0
        if dist_km <= STUDY_RADIUS_KM:
            kept.append(f)
        else:
            dropped.append((f, dist_km))

    if verbose:
        print()
        print(f"Study area filter: centroid within {STUDY_RADIUS_KM:.1f} km "
              f"of field {ANCHOR_FIELD!r}")
        if dropped:
            for f, d in sorted(dropped, key=lambda t: -t[1]):
                print(f"  EXCLUDED {f.name!r}: centroid is {d:.1f} km away "
                      f"(> {STUDY_RADIUS_KM:.0f} km) -- too far to share a fire "
                      f"with the main cluster")
        else:
            print("  (nothing excluded)")

    kept.sort(key=lambda f: _name_sort_key(f.name))

    if verbose:
        print_field_table(kept)

    return kept


def _name_sort_key(name):
    """Sort '4','5','13' numerically but keep text names like 'nte' first."""
    return (0, 0, name) if not name.isdigit() else (1, int(name), "")


def print_field_table(fields):
    """Pretty-print the Stage 1 results table."""
    print()
    print(f"{'FIELD':<8}{'AREA (ha)':>12}{'CENTROID X (m)':>17}{'CENTROID Y (m)':>17}"
          f"{'PERIMETER (m)':>16}")
    print("-" * 70)
    for f in fields:
        print(f"{f.name:<8}{f.area_ha:>12.2f}{f.cx:>17.1f}{f.cy:>17.1f}"
              f"{f.poly_m.exterior.length:>16.0f}")
    print("-" * 70)
    total = sum(f.area_ha for f in fields)
    print(f"{'TOTAL':<8}{total:>12.2f}   ({len(fields)} fields in the study area)")


# ---------------------------------------------------------------------------
# SELF-TEST: run `python parse.py` to check Stage 1 on its own.
# ---------------------------------------------------------------------------

# Areas the team measured by hand in Google Earth, used as a sanity check.
# If our computed numbers drift far from these, the projection or parsing is wrong.
SANITY_TARGETS_HA = {"nte": 25.3, "13": 45.9, "5": 4.5}
SANITY_TOLERANCE = 0.10   # allow 10% difference from the hand-measured value

if __name__ == "__main__":
    fields = load_fields()

    print()
    print("SANITY CHECK against hand-measured areas:")
    by_name = {f.name: f for f in fields}
    all_ok = True
    for name, target in SANITY_TARGETS_HA.items():
        got = by_name[name].area_ha
        err = abs(got - target) / target
        ok = err <= SANITY_TOLERANCE
        all_ok = all_ok and ok
        print(f"  {name:<5} expected {target:>6.1f} ha   got {got:>6.1f} ha   "
              f"diff {err * 100:>4.1f}%   {'OK' if ok else 'FAIL'}")
    print("  ==> " + ("ALL SANITY CHECKS PASSED" if all_ok else "MISMATCH -- STOP AND DEBUG"))
    