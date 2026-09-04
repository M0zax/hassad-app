"""
STAGE 5 -- The demo animation (the deliverable for the competition video).

Produces harvest_comparison.gif: three maps side by side, all advancing through
the SAME days at the SAME time, so a viewer can see the three strategies pull
apart in real time.

    left   = (a) naive, largest field first
    middle = (b) fire-only greedy
    right  = (c) balanced greedy (fire + travel)

Colour language, kept deliberately blunt so it reads on a phone screen:

    RED field      = STANDING dry wheat -- fuel
    GREEN field    = HARVESTED -- stubble, acts as a firebreak
    YELLOW outline = the largest connected block of standing fuel RIGHT NOW.
                     This is the number the whole project is trying to shrink:
                     the worst single fire that could happen today.
    WHITE dashes   = the field the harvester is cutting today
    grey lines     = adjacency (fire could spread along these)
    RED lines      = adjacency INSIDE the highlighted block

Underneath the maps is a race chart of cumulative fire risk, so the audience
sees the three strategies diverge without having to read numbers off the maps.
"""

import matplotlib
matplotlib.use("Agg")               # write frames to file, no GUI needed
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# ---------------------------------------------------------------------------
# CONSTANTS -- animation look & feel
# ---------------------------------------------------------------------------

GIF_PATH = "harvest_comparison.gif"

FPS = 2                     # frames per second; 2 => each harvest day lasts 0.5 s
HOLD_FRAMES = 8             # extra frames frozen on the final state at the end,
                            # so the last numbers stay on screen in the video
DPI = 100                   # 100 dpi x the figsize below => ~1800 x 1000 px

COLOR_STANDING = "#d32f2f"  # red   -- dry wheat, fuel
COLOR_HARVESTED = "#43a047" # green -- stubble, firebreak
COLOR_BLOCK = "#ffd600"     # yellow-- outline of the largest standing block
COLOR_CUTTING = "#ffffff"   # white -- dashed outline of today's field

# Line colours for the cumulative-risk race chart at the bottom.
RACE_COLORS = ("#555555", "#fb8c00", "#1e88e5")


# ---------------------------------------------------------------------------
# DRAWING ONE PANEL FOR ONE DAY
# ---------------------------------------------------------------------------

def _draw_panel(ax, result, day_index, G, fields, extent):
    """
    Redraw one strategy's map for one day.

    We clear and redraw from scratch every frame. That is slightly wasteful, but
    with 11 fields it is instant, and it keeps this function easy to read --
    which matters more in a student prototype than shaving milliseconds.
    """
    ax.clear()
    state = result.days[day_index]

    # --- adjacency lines first, so polygons sit on top of them.
    # Only draw an edge if BOTH ends are still standing: once a field is cut the
    # fire path through it is dead, and showing the line would be a lie.
    for a, b in G.edges():
        if a in state.standing and b in state.standing:
            in_block = a in state.largest_block and b in state.largest_block
            ax.plot(
                [G.nodes[a]["cx"], G.nodes[b]["cx"]],
                [G.nodes[a]["cy"], G.nodes[b]["cy"]],
                color="#b71c1c" if in_block else "#9e9e9e",
                linewidth=2.6 if in_block else 1.2,
                alpha=0.95 if in_block else 0.55,
                zorder=2,
            )

    # --- the fields themselves
    for f in fields:
        xs, ys = f.poly_m.exterior.xy
        standing = f.name in state.standing
        ax.fill(
            xs, ys,
            facecolor=COLOR_STANDING if standing else COLOR_HARVESTED,
            edgecolor="#3e2723",
            linewidth=0.8,
            alpha=0.92,
            zorder=3,
        )

    # --- bold yellow outline around the largest connected standing block.
    # Drawn as a thick yellow stroke with a thin dark line on top, so it stays
    # visible against both the red fill and a pale background.
    for f in fields:
        if f.name in state.largest_block:
            xs, ys = f.poly_m.exterior.xy
            ax.plot(xs, ys, color=COLOR_BLOCK, linewidth=5.5, zorder=4,
                    solid_capstyle="round")
            ax.plot(xs, ys, color="#212121", linewidth=1.6, zorder=5)

    # --- the field being cut today: white dashed outline PLUS a marker, because
    # on a small phone screen a dashed outline alone is easy to miss.
    for f in fields:
        if f.name == state.working_on:
            xs, ys = f.poly_m.exterior.xy
            ax.plot(xs, ys, color=COLOR_CUTTING, linewidth=3.2, linestyle="--",
                    zorder=6)
            ax.plot(f.cx, f.cy, marker="X", markersize=15,
                    markerfacecolor=COLOR_CUTTING, markeredgecolor="#212121",
                    markeredgewidth=1.8, zorder=9)

    # --- field name labels
    for f in fields:
        ax.text(f.cx, f.cy, f.name, fontsize=9, fontweight="bold",
                ha="center", va="center", color="#ffffff", zorder=8,
                bbox=dict(boxstyle="round,pad=0.2", fc="#000000bb", ec="none"))

    # --- the per-panel readout
    ax.set_title(result.label, fontsize=12, fontweight="bold", pad=10)
    ax.text(
        0.5, -0.06,
        f"DAY {state.day} / {result.season_days}    cutting: {state.working_on}\n"
        f"largest standing block: {state.largest_block_ha:.1f} ha\n"
        f"cumulative fire risk: {state.cumulative_risk:.0f} ha-days",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=11, family="monospace",
        bbox=dict(boxstyle="round,pad=0.45", fc="#f5f5f5", ec="#9e9e9e"),
    )

    # Identical limits on every panel and every frame: nothing may jump around,
    # or the eye cannot compare the three strategies.
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#bdbdbd")


def _draw_race(ax, results, day_index):
    """The cumulative-risk race chart: three lines pulling apart over the season."""
    ax.clear()
    for r, color in zip(results, RACE_COLORS):
        xs = [d.day for d in r.days]
        ys = [d.cumulative_risk for d in r.days]
        # full season faint, progress so far solid -- shows where we're heading
        ax.plot(xs, ys, color=color, linewidth=1.0, alpha=0.22)
        ax.plot(xs[: day_index + 1], ys[: day_index + 1], color=color,
                linewidth=2.8, label=f"{r.label}  ({r.fire_risk_score:.0f} ha-days)")
        ax.plot(xs[day_index], ys[day_index], "o", color=color, markersize=7)

    ax.axvline(day_index + 1, color="#9e9e9e", linewidth=1.0, linestyle=":")
    ax.set_xlabel("day of season", fontsize=10)
    ax.set_ylabel("cumulative fire risk\n(ha-days)", fontsize=10)
    ax.set_title("Running total -- lower line = safer season",
                 fontsize=11, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_xlim(1, max(r.season_days for r in results))
    ax.set_ylim(0, max(r.fire_risk_score for r in results) * 1.08)


# ---------------------------------------------------------------------------
# BUILDING THE GIF
# ---------------------------------------------------------------------------

def make_animation(results, G, fields, out_path=GIF_PATH, fps=FPS,
                   hold_frames=HOLD_FRAMES):
    """
    Render the three-panel comparison GIF.

    `results` must be three SeasonResult objects (naive, fire-only, balanced),
    all simulated on the same graph so their day counts line up.
    """
    season_days = results[0].season_days
    if not all(r.season_days == season_days for r in results):
        raise ValueError("all three strategies must have the same season length")

    # --- one shared map extent, computed once, with a margin
    xs = [c for f in fields for c in f.poly_m.exterior.xy[0]]
    ys = [c for f in fields for c in f.poly_m.exterior.xy[1]]
    pad = 0.06 * max(max(xs) - min(xs), max(ys) - min(ys))
    extent = (min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad)

    # --- layout: three maps across the top, one wide race chart underneath
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(
        2, 3, height_ratios=[2.5, 1.0], hspace=0.46, wspace=0.06,
        left=0.065, right=0.985, top=0.855, bottom=0.075,
    )
    map_axes = [fig.add_subplot(gs[0, i]) for i in range(3)]
    race_ax = fig.add_subplot(gs[1, :])

    fig.suptitle(
        "Harvest-Sequencing Optimizer -- Bekaa Valley, Lebanon\n"
        "same 11 fields, same 24 days, three different harvest orders",
        fontsize=17, fontweight="bold",
    )

    # --- a single shared legend so each panel stays uncluttered
    legend_items = [
        Patch(facecolor=COLOR_STANDING, edgecolor="#3e2723", label="standing wheat (fuel)"),
        Patch(facecolor=COLOR_HARVESTED, edgecolor="#3e2723", label="harvested (firebreak)"),
        Line2D([0], [0], color=COLOR_BLOCK, lw=5, label="largest connected standing block"),
        Line2D([0], [0], color="#212121", lw=0, marker="X", markersize=11,
               markerfacecolor="#ffffff", markeredgecolor="#212121",
               label="cutting today"),
        Line2D([0], [0], color="#9e9e9e", lw=1.5, label="fire can spread (adjacent)"),
    ]
    fig.legend(handles=legend_items, loc="upper center", ncol=5,
               bbox_to_anchor=(0.5, 0.925), frameon=False, fontsize=11)

    total_frames = season_days + hold_frames

    def render(frame):
        # After the season ends, freeze on the last day for `hold_frames` frames.
        day_index = min(frame, season_days - 1)
        for ax, result in zip(map_axes, results):
            _draw_panel(ax, result, day_index, G, fields, extent)
        _draw_race(race_ax, results, day_index)
        return []

    anim = FuncAnimation(fig, render, frames=total_frames, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps), dpi=DPI)
    plt.close(fig)

    # NOTE for whoever opens the GIF and counts frames: Pillow collapses the
    # identical HOLD_FRAMES at the end into ONE frame with a longer duration.
    # So a 24-day season + 8 hold frames reports as 24 frames, the last of which
    # lasts 4.5 s. That is the freeze-frame we wanted -- nothing is missing.

    print(f"Saved animation -> {out_path}  "
          f"({total_frames} frames @ {fps} fps = {total_frames / fps:.1f} s)")
    return out_path


def save_key_frames(results, G, fields, days=(1, 5, 12, 24), prefix="frame_day"):
    """
    Save a few still PNGs of the three panels on chosen days.

    Stills are useful for the written report / poster, where a GIF is useless.
    """
    xs = [c for f in fields for c in f.poly_m.exterior.xy[0]]
    ys = [c for f in fields for c in f.poly_m.exterior.xy[1]]
    pad = 0.06 * max(max(xs) - min(xs), max(ys) - min(ys))
    extent = (min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad)

    paths = []
    for day in days:
        idx = min(day, results[0].season_days) - 1
        fig, axes = plt.subplots(1, 3, figsize=(18, 8.6))
        for ax, result in zip(axes, results):
            _draw_panel(ax, result, idx, G, fields, extent)
        fig.suptitle(f"Harvest-Sequencing Optimizer -- day {idx + 1}",
                     fontsize=16, fontweight="bold")
        # Explicit margins, not tight_layout: the readout text sits BELOW each
        # axes, and tight_layout doesn't account for it, so it gets clipped.
        fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.20,
                            wspace=0.06)
        path = f"{prefix}{idx + 1:02d}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)
        print(f"Saved still -> {path}")
    return paths


# ---------------------------------------------------------------------------
# SELF-TEST: run `python animate.py` to build just the GIF.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parse import load_fields
    from graph import build_adjacency_graph, distance_matrix_km
    from optimize import naive_largest_first, greedy_fire_only
    from exact import exact_fire_only
    from simulate import simulate_season

    fields = load_fields(verbose=False)
    G = build_adjacency_graph(fields)
    matrix, index = distance_matrix_km(fields)

    # Phase 2 line-up: the naive baseline, the Phase-1 greedy, and the exact
    # optimum from exact.py -- so the animation shows the whole journey.
    naive = simulate_season(naive_largest_first(G), G, matrix, index,
                            label="(a) naive: largest field first")
    greedy = simulate_season(greedy_fire_only(G), G, matrix, index,
                             label="(b) greedy (Phase 1)")
    _, best = exact_fire_only(G)
    optimal = simulate_season(best, G, matrix, index,
                              label="(c) exact optimum (Phase 2)")

    print("=" * 74)
    print("STAGE 5 -- BUILDING THE DEMO ANIMATION")
    print("=" * 74)
    make_animation([naive, greedy, optimal], G, fields)
    save_key_frames([naive, greedy, optimal], G, fields)
