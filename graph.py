"""
STAGE 2 -- Adjacency graph + travel-distance matrix.

Two ideas live in this file, and it is important not to confuse them:

  1. ADJACENCY (the fire model). Two fields are "adjacent" if a fire in one
     could realistically creep into the other -- i.e. their traced boundaries
     are within ADJACENCY_THRESHOLD_M of each other. This gives us a networkx
     graph whose CONNECTED COMPONENTS are blocks of fuel a single fire can eat.

  2. TRAVEL DISTANCE (the cost model). How far the harvester must drive from
     one field to the next. We approximate this as straight-line centroid-to-
     centroid distance, stored as a full matrix in kilometres.

Adjacency is about *fire*, distance is about *fuel in the tractor*. Fields can
be far apart in driving terms yet adjacent in fire terms, and vice versa.
"""

import itertools
import math

import matplotlib
matplotlib.use("Agg")          # render to file, no interactive window needed
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Two fields count as ADJACENT if their polygon boundaries come within this many
# metres of each other. It is NOT zero because our polygons were hand-traced in
# Google Earth: real neighbouring fields end up with small false gaps (a road,
# a sloppy click, a hedgerow). It also roughly matches how far a grass fire can
# throw embers / creep across a track on a windy Bekaa afternoon.
#
# WHY 175 AND NOT 100: we measured every pair of fields. The gaps come in two
# clumps -- fields that clearly touch (7-12 m) and fields that clearly don't
# (114 m and up), with NOTHING in between. A 100 m rule lands in that empty band
# and falls 14 m short of joining field 'nte' to the 4-5-6-7 chain, which shatters
# the map into 6 tiny islands. 175 m sits safely past the real neighbours and
# produces 3 components with a genuine 75.5 ha fuel block -- which is the thing
# harvest ordering can actually break up. Run print_threshold_sensitivity() to
# see this trade-off for yourself.
ADJACENCY_THRESHOLD_M = 175.0

# Output image for this stage.
ADJACENCY_MAP_PNG = "map_adjacency.png"


# ---------------------------------------------------------------------------
# BUILDING THE GRAPH
# ---------------------------------------------------------------------------

def build_adjacency_graph(fields, threshold_m=ADJACENCY_THRESHOLD_M):
    """
    Build the fire-spread graph.

    Nodes  = field names, carrying 'area_ha' and the geometry as attributes.
    Edges  = pairs of fields whose polygons are within `threshold_m`, carrying
             'gap_m' (how close they actually are).

    shapely's .distance() returns the shortest distance between two geometries
    and is exactly 0.0 when they touch or overlap, which is what we want.
    """
    G = nx.Graph()

    for f in fields:
        G.add_node(f.name, area_ha=f.area_ha, cx=f.cx, cy=f.cy, poly=f.poly_m)

    # Check every unordered pair of fields once.
    for a, b in itertools.combinations(fields, 2):
        gap_m = a.poly_m.distance(b.poly_m)
        if gap_m <= threshold_m:
            G.add_edge(a.name, b.name, gap_m=gap_m)

    return G


def distance_matrix_km(fields):
    """
    Full centroid-to-centroid straight-line distance matrix, in kilometres.

    Returns (matrix, index) where matrix[i][j] is the distance between
    fields[i] and fields[j], and index maps a field name -> its row/column.

    This is the harvester's travel cost. A real harvester follows farm tracks,
    so true driving distance is longer -- but for comparing ORDERINGS against
    each other, straight-line is a fair and simple proxy.
    """
    n = len(fields)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i][j] = math.hypot(
                fields[i].cx - fields[j].cx,
                fields[i].cy - fields[j].cy,
            ) / 1000.0
    index = {f.name: i for i, f in enumerate(fields)}
    return matrix, index


# ---------------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------------

def print_graph_report(G, fields, matrix, index):
    """Print the adjacency list, the components, and the distance matrix."""
    print("=" * 74)
    print("STAGE 2 -- ADJACENCY GRAPH")
    print("=" * 74)
    print(f"Adjacency rule: boundaries within {ADJACENCY_THRESHOLD_M:.0f} m of each other")
    print(f"Nodes: {G.number_of_nodes()}    Edges: {G.number_of_edges()}")
    print()

    print("ADJACENCY LIST (neighbour: gap in metres)")
    print("-" * 74)
    for f in fields:
        nbrs = sorted(
            G[f.name].items(), key=lambda kv: kv[1]["gap_m"]
        )
        if nbrs:
            txt = ", ".join(f"{n} ({d['gap_m']:.0f} m)" for n, d in nbrs)
        else:
            txt = "(none -- isolated, its own fire island)"
        print(f"  {f.name:<5} [{f.area_ha:>6.2f} ha] -> {txt}")
    print()

    # Connected components = the fuel blocks a single fire could burn through.
    print("CONNECTED COMPONENTS AT DAY 0 (everything still standing)")
    print("-" * 74)
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    for i, comp in enumerate(comps, 1):
        ha = sum(G.nodes[n]["area_ha"] for n in comp)
        members = ", ".join(sorted(comp, key=lambda s: (not s.isdigit(), s)))
        print(f"  Component {i}: {ha:>6.2f} ha over {len(comp)} field(s) -> {members}")
    biggest = max(sum(G.nodes[n]["area_ha"] for n in c) for c in comps)
    print(f"  ==> Largest connected standing block = {biggest:.2f} ha "
          f"(this is the day-0 fire risk)")
    print()

    print("CENTROID-TO-CENTROID DISTANCE MATRIX (km) -- harvester travel cost")
    print("-" * 74)
    names = [f.name for f in fields]
    print("      " + "".join(f"{n:>7}" for n in names))
    for f in fields:
        i = index[f.name]
        row = "".join(f"{matrix[i][index[n]]:>7.2f}" for n in names)
        print(f"{f.name:>5} {row}")
    print()


# ---------------------------------------------------------------------------
# THE MAP
# ---------------------------------------------------------------------------

def _draw_fields(ax, fields, G, label_fontsize=10, gap_labels=True):
    # --- field polygons (filled wheat-gold, dark outline)
    for f in fields:
        xs, ys = f.poly_m.exterior.xy
        ax.fill(xs, ys, facecolor="#e8c56a", edgecolor="#6b4f14",
                linewidth=1.6, alpha=0.85, zorder=2)

    # --- adjacency edges, drawn centroid to centroid
    for a, b, data in G.edges(data=True):
        xa, ya = G.nodes[a]["cx"], G.nodes[a]["cy"]
        xb, yb = G.nodes[b]["cx"], G.nodes[b]["cy"]
        ax.plot([xa, xb], [ya, yb], color="#c62828", linewidth=2.2,
                alpha=0.95, zorder=3)
        if gap_labels:
            ax.text((xa + xb) / 2, (ya + yb) / 2, f"{data['gap_m']:.0f}m",
                    fontsize=7, color="#8e0000", ha="center", va="center", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))

    # --- centroid dots + labels.
    # Labels are pushed RADIALLY OUTWARD from the middle of the group so that
    # fields packed close together don't stack their labels on top of each other.
    mx = sum(f.cx for f in fields) / len(fields)
    my = sum(f.cy for f in fields) / len(fields)
    for f in fields:
        ax.plot(f.cx, f.cy, "o", color="#1a1a1a", markersize=5, zorder=6)
        dx, dy = f.cx - mx, f.cy - my
        norm = math.hypot(dx, dy) or 1.0
        off = 26.0                      # label offset in points
        ax.annotate(
            f"{f.name}\n{f.area_ha:.1f} ha",
            (f.cx, f.cy),
            textcoords="offset points",
            xytext=(off * dx / norm, off * dy / norm),
            ha="center", va="center",
            fontsize=label_fontsize, fontweight="bold", color="#111",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#555", alpha=0.92),
            arrowprops=dict(arrowstyle="-", color="#888", lw=0.8),
            zorder=8,
        )


def plot_adjacency_map(fields, G, out_path=ADJACENCY_MAP_PNG):
    """
    Draw the field polygons with adjacency edges between their centroids.

    Two panels, because the fields are not evenly spread: field 13 sits ~4 km
    from everything else, so a single frame that fits 13 squashes the main
    cluster into an unreadable blob.
        LEFT  = whole study area (shows how isolated 13 and 11/12 really are)
        RIGHT = zoom on the dense southern cluster (where the adjacency edges are)

    This plot exists so a human can eyeball it against Google Earth and confirm
    "yes, those two fields really do touch".
    """
    fig, (ax_all, ax_zoom) = plt.subplots(1, 2, figsize=(19, 10))

    # ---------------- LEFT: everything ----------------
    _draw_fields(ax_all, fields, G, label_fontsize=9, gap_labels=False)
    _add_scale_bar(ax_all, fields, length_m=1000)
    n_iso = sum(1 for n in G.nodes if G.degree(n) == 0)
    ax_all.set_title(
        f"FULL STUDY AREA -- {len(fields)} fields, {sum(f.area_ha for f in fields):.0f} ha total\n"
        f"{G.number_of_edges()} adjacency edges, {n_iso} isolated field(s)",
        fontsize=12, fontweight="bold")

    # ---------------- RIGHT: zoom on the dense cluster ----------------
    # The "dense cluster" = every field that has at least one neighbour, plus any
    # field close to them. We just take the fields south/west of field 11 here by
    # selecting on the bounding box of the connected fields.
    connected = [f for f in fields if G.degree(f.name) > 0]
    cluster = [f for f in connected if f.cy < -2000]          # the southern group
    cluster_names = {f.name for f in cluster}
    # include nearby isolated fields so the reader can see WHY they're isolated
    for f in fields:
        if f.name in cluster_names:
            continue
        if any(math.hypot(f.cx - c.cx, f.cy - c.cy) < 1800 for c in cluster):
            cluster.append(f)
    subG = G.subgraph({f.name for f in cluster})

    _draw_fields(ax_zoom, cluster, subG, label_fontsize=11, gap_labels=True)
    _add_scale_bar(ax_zoom, cluster, length_m=500)
    ax_zoom.set_title(
        f"ZOOM: main southern cluster\n"
        f"red lines = adjacent (boundaries within {ADJACENCY_THRESHOLD_M:.0f} m); "
        f"number on the line = actual gap",
        fontsize=12, fontweight="bold")

    for ax in (ax_all, ax_zoom):
        ax.set_xlabel("metres east of projection origin")
        ax.set_ylabel("metres north of projection origin")
        ax.set_aspect("equal")      # critical: don't distort the shapes
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.margins(0.16)

    fig.suptitle("Bekaa Valley harvest-sequencing study area -- adjacency check",
                 fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    print(f"Saved adjacency map -> {out_path}")
    return out_path 


def _add_scale_bar(ax, fields, length_m=1000):
    """Draw a simple horizontal scale bar in the lower-left of the plot."""
    xs = [f.cx for f in fields]
    ys = [f.cy for f in fields]
    span = max(max(xs) - min(xs), 1.0)
    x0 = min(xs) - 0.02 * span
    y0 = min(ys) - 0.10 * span
    ax.plot([x0, x0 + length_m], [y0, y0], color="black", linewidth=3, zorder=9)
    label = f"{length_m/1000:g} km" if length_m >= 1000 else f"{length_m:.0f} m"
    ax.text(x0 + length_m / 2, y0 + 0.02 * span, label,
            ha="center", fontsize=10, fontweight="bold", zorder=9)


def print_threshold_sensitivity(fields):
    """
    Show how the graph would change at other adjacency thresholds.

    Why this matters: the whole optimizer only has something to optimise if there
    ARE big connected blocks of fuel to break up. If the threshold is so tight
    that every field is its own island, harvest ORDER can barely change the risk.
    This table lets the team justify their choice of ADJACENCY_THRESHOLD_M
    instead of picking 100 m by gut feel.
    """
    print("THRESHOLD SENSITIVITY -- how the fire graph changes with the adjacency rule")
    print("-" * 74)
    print(f"{'threshold':>10}{'edges':>8}{'components':>13}{'largest block (ha)':>21}")
    for t in (50, 100, 125, 150, 175, 200, 300, 400):
        H = build_adjacency_graph(fields, threshold_m=t)
        comps = list(nx.connected_components(H))
        biggest = max(sum(H.nodes[n]["area_ha"] for n in c) for c in comps)
        star = "  <-- current" if t == ADJACENCY_THRESHOLD_M else ""
        print(f"{t:>8} m{H.number_of_edges():>8}{len(comps):>13}{biggest:>21.2f}{star}")
    print()


# ---------------------------------------------------------------------------
# SELF-TEST: run `python graph.py` to check Stage 2 on its own.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parse import load_fields

    fields = load_fields(verbose=False)
    G = build_adjacency_graph(fields)
    matrix, index = distance_matrix_km(fields)
    print_graph_report(G, fields, matrix, index)
    print_threshold_sensitivity(fields)
    plot_adjacency_map(fields, G)
