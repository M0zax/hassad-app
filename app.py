"""
HASSAD -- the farmer-facing app.   Run with:   streamlit run app.py

Built for a cooperative manager on an Android phone in June sunlight: one
column, 56 px buttons, one job per screen, no engineering words, in Arabic
or English (toggle at the top; every string lives in i18n.py).

  FIELDS  "Tap your fields"    the Bekaa demo fields: tap to add / remove,
          "Draw your fields"   OR draw your own farm with the pencil tool --
                               any farm, anywhere -- then "Make my plan"
  TODAY   the hero card        which field to cut now, how long, one trust
                               line ("Fire block now 76 ha, after 71 ha");
                               "Field 5 is cut" re-plans the rest; tap a
                               field on the map to mark it cut / not cut;
                               Undo; WhatsApp and Print; the whole order.

Everything judges want (percentages, charts, tables, the model switches, the
value-at-stake economics) lives in ONE collapsed section, "Numbers", at the
bottom -- opened only by /?judge=1 -- so it never crowds the farmer's screen.

Demo-field plans mirror into the URL (?f=...&cut=...&lang=..) so a refresh
or a forwarded link restores them with no backend. All the thinking is in
app_logic.py (tested separately); this file is layout.
"""

import urllib.parse

import folium
from folium.plugins import Draw
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import app_logic as logic
from i18n import STRINGS

# Status colours. Every colour is paired with a glyph (check mark, rank number,
# yellow ring), so the map still reads for red-green colour blindness.
C_STANDING, C_DONE, C_TODAY, C_OTHER = "#D64B2A", "#2F7D46", "#F2B705", "#9E9E9E"

st.set_page_config(page_title="Hassad حصاد", page_icon="🌾", layout="centered",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------

ss = st.session_state
qp = st.query_params
ss.setdefault("lang", "ar" if qp.get("lang") == "ar" else "en")
# "demo" (traced Bekaa fields) | "custom" (a farm the farmer draws).
# /?mode=draw opens straight in drawing mode -- handy for the stage demo.
ss.setdefault("mode", "custom" if qp.get("mode") == "draw" else "demo")
ss.setdefault("custom_fields", [])
ss.setdefault("selected", set(logic.field_names()) if ss.mode == "demo" else set())
ss.setdefault("plan", None)
ss.setdefault("harvested", [])
ss.setdefault("screen", "fields")        # "fields" | "today"
ss.setdefault("focus", None)
ss.setdefault("undo", None)
ss.setdefault("last_click", None)
ss.setdefault("flash", None)
ss.setdefault("dry_year", True)          # judge-only model switches
ss.setdefault("balanced", False)
ss.setdefault("machine_at", None)

T = STRINGS[ss.lang]
RTL = ss.lang == "ar"
DRY_RULE, WET_RULE = list(logic.GAP_RULES)


def current_fields():
    return ss.custom_fields if ss.mode == "custom" else list(logic.all_fields())


def gap_rule():
    return DRY_RULE if ss.dry_year else WET_RULE


def sync_url():
    """Mirror demo-field plans into the address bar (drawn farms can't be
    encoded in a URL -- the app says so on screen)."""
    qp["lang"] = ss.lang
    if ss.mode == "demo" and ss.plan is not None:
        qp["f"] = ",".join(sorted(ss.selected))
        if ss.harvested:
            qp["cut"] = ",".join(ss.harvested)
        elif "cut" in qp:
            del qp["cut"]
    else:
        for k in ("f", "cut"):
            if k in qp:
                del qp[k]


def rebuild_plan():
    base = logic.plan(sorted(ss.selected), gap_rule(), ss.balanced,
                      fields=current_fields(), lang=ss.lang)
    cut = [c for c in ss.harvested if c in base["G"].nodes]
    ss.harvested = cut
    if cut:
        pos = ss.machine_at if (ss.balanced and ss.machine_at in cut) else cut[-1]
        ss.plan = logic.replan(base, cut, position=pos, lang=ss.lang)
    else:
        ss.plan = base
    sync_url()


def make_plan():
    ss.harvested, ss.undo, ss.focus, ss.last_click = [], None, None, None
    rebuild_plan()
    ss.screen = "today"


def set_cut(field, cut):
    ss.undo = list(ss.harvested)
    if cut and field not in ss.harvested:
        ss.harvested.append(field)
    if not cut and field in ss.harvested:
        ss.harvested.remove(field)
    rebuild_plan()
    ss.focus, ss.last_click, ss.flash = None, None, T["updated"]


def undo():
    if ss.undo is not None:
        ss.harvested, ss.undo = list(ss.undo), None
        rebuild_plan()
        ss.flash = T["updated"]


def reset_all():
    ss.plan, ss.harvested, ss.undo, ss.focus, ss.last_click = None, [], None, None, None
    ss.screen = "fields"
    sync_url()


# ---- restore from the URL (refresh, forwarded link) or the demo shortcuts
judge = "judge" in qp or "auto" in qp
if ss.plan is None:
    if "f" in qp and qp["f"]:
        ss.mode = "demo"
        ss.selected = {f for f in qp["f"].split(",") if f in logic.field_names()} or ss.selected
        ss.harvested = [c for c in qp.get("cut", "").split(",") if c in ss.selected]
        rebuild_plan()
        ss.screen = "today"
    elif judge:
        ss.mode = "demo"
        make_plan()

# ---------------------------------------------------------------------------
# STYLE (+ right-to-left when Arabic)
# ---------------------------------------------------------------------------

st.markdown(f"""
<style>
  header[data-testid="stHeader"] {{ display: none; }}
  .block-container {{ max-width: 480px; padding: 0.6rem 0.8rem 6rem;
                      direction: {'rtl' if RTL else 'ltr'};
                      text-align: {'right' if RTL else 'left'}; }}
  h1.hassad {{ font-size: 2.2rem; font-weight: 900; margin: 0; letter-spacing: -0.02em; }}
  p.tagline {{ font-size: 1.05rem; color: #5b554c; margin: 0 0 0.6rem; }}
  .step {{ font-size: 1.35rem; font-weight: 900; margin: 0.6rem 0 0.2rem; }}
  .hint {{ color: #5b554c; font-size: 1rem; margin-bottom: 0.4rem; }}
  div.stButton > button, div.stLinkButton > a, div.stDownloadButton > button {{
      min-height: 56px; font-size: 1.15rem; font-weight: 800; border-radius: 14px;
      transition: none; }}
  div.stLinkButton > a {{ display: flex; align-items: center; justify-content: center; }}
  .hero {{ background: #FFF6DC; border: 3px solid {C_TODAY}; border-radius: 18px;
           padding: 1rem 1.2rem 1.1rem; margin: 0.5rem 0 0.7rem; }}
  .hero .lbl {{ font-size: 0.85rem; font-weight: 800; letter-spacing: 0.14em;
                text-transform: uppercase; color: #8a6d1c; }}
  .hero .big {{ font-size: 3rem; font-weight: 900; line-height: 1.1; margin: 0.1rem 0; }}
  .hero .sub {{ font-size: 1.1rem; color: #3f3a33; }}
  .hero .trust {{ font-size: 1.05rem; margin-top: 0.5rem; color: #111; }}
  .focus {{ border: 2px solid #ccc; border-radius: 14px; padding: 0.8rem 1rem 0.2rem;
            margin: 0.6rem 0; }}
  .focus .name {{ font-size: 1.5rem; font-weight: 900; }}
  .focus .state {{ color: #5b554c; }}
  .order {{ font-size: 1.15rem; line-height: 1.95; }}
  .order .line {{ padding: 0 0.4rem; }}
  .order .cut {{ color: {C_DONE}; font-weight: 700; }}
  .order .now {{ background: #FFF6DC; border-radius: 8px; font-weight: 900; }}
  .done {{ background: #E8F3EA; border: 3px solid {C_DONE}; border-radius: 18px;
           padding: 1.2rem; text-align: center; font-size: 1.6rem; font-weight: 900; }}
  .econ {{ background: #F4F1EA; border-radius: 14px; padding: 0.8rem 1rem; margin: 0.4rem 0; }}
  .econ .big {{ font-size: 1.6rem; font-weight: 900; }}
  .econ .note {{ color: #5b554c; font-size: 0.85rem; }}
</style>
""", unsafe_allow_html=True)

if ss.flash:
    st.toast(ss.flash)
    ss.flash = None

# ---------------------------------------------------------------------------
# HEADER + LANGUAGE
# ---------------------------------------------------------------------------

ss.setdefault("page", "about" if qp.get("page") == "about" else "plan")

h1, h2 = st.columns([3, 1.3])
h1.markdown(f'<h1 class="hassad">🌾 {T["title"]}</h1>'
            f'<p class="tagline">{T["tagline"]}</p>', unsafe_allow_html=True)
other = "ar" if ss.lang == "en" else "en"
if h2.button(STRINGS[other]["lang_name"], use_container_width=True, key="lang_btn"):
    ss.lang = other
    if ss.plan is not None:
        ss.plan = logic.relabel(ss.plan, ss.lang)
    sync_url()
    st.rerun()

# ---- the About / FAQ page (everything anyone could ask, incl. the mentor's questions)
if ss.page == "about":
    if st.button(T["back_plan"], type="primary", use_container_width=True, key="back_top"):
        ss.page = "plan"
        if "page" in qp:
            del qp["page"]
        st.rerun()
    import about
    about.render(ss.lang)
    if st.button(T["back_plan"], use_container_width=True, key="back_bottom"):
        ss.page = "plan"
        if "page" in qp:
            del qp["page"]
        st.rerun()
    st.stop()

if st.button(T["about"], use_container_width=True, key="about_btn"):
    ss.page = "about"
    qp["page"] = "about"
    st.rerun()

# ---------------------------------------------------------------------------
# THE MAP -- one component, recoloured per state, zoom preserved between taps
# ---------------------------------------------------------------------------

plan = ss.plan
fields = current_fields()
order = plan["order"] if (plan and ss.screen == "today") else []
today = order[0] if order else None
rank = {f: i + 1 for i, f in enumerate(order)}


def build_map(drawing=False):
    base = fields or list(logic.all_fields())
    lat0 = sum(f.poly_ll.centroid.y for f in base) / len(base)
    lon0 = sum(f.poly_ll.centroid.x for f in base) / len(base)
    # scrollWheelZoom off: on a laptop, scrolling the page must not zoom the
    # map; on a phone, pinch still zooms and drag still pans.
    m = folium.Map(location=[lat0, lon0], zoom_start=14, tiles=None,
                   zoom_control=drawing, control_scale=False, scrollWheelZoom=False)
    if fields:
        # Frame the selected fields so they are tappable; if one outlier would
        # shrink the cluster to specks, centre on the cluster instead.
        sel = [f for f in fields if f.name in ss.selected] or fields
        lats = [lat for f in sel for lon, lat in f.poly_ll.exterior.coords]
        lons = [lon for f in sel for lon, lat in f.poly_ll.exterior.coords]
        span_km = max((max(lats) - min(lats)) * 111, (max(lons) - min(lons)) * 92)
        if span_km <= 3.0:
            m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(20, 20))
        else:
            cys = sorted(f.poly_ll.centroid.y for f in sel)
            cxs = sorted(f.poly_ll.centroid.x for f in sel)
            m.location = [cys[len(cys) // 2], cxs[len(cxs) // 2]]
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
              "MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery", control=False).add_to(m)
    if drawing:
        Draw(export=False, position="topleft",
             draw_options={"polyline": False, "circle": False, "marker": False,
                           "circlemarker": False, "rectangle": True,
                           "polygon": {"allowIntersection": False, "showArea": True}},
             edit_options={"edit": True, "remove": True}).add_to(m)
    fg = folium.FeatureGroup(name="fields")
    for f in fields:
        pts = [(lat, lon) for lon, lat in f.poly_ll.exterior.coords]
        mine = f.name in ss.selected
        cut = f.name in ss.harvested
        if not mine:
            fill, edge, w, badge, bg = C_OTHER, "#ffffff", 1.5, f.name, "#9E9E9E"
        elif cut:
            fill, edge, w, badge, bg = C_DONE, "#1f5a30", 2, f"{f.name} ✓", C_DONE
        elif f.name == today:
            fill, edge, w, badge, bg = C_STANDING, C_TODAY, 6, f"{f.name} · 1", "#111"
        elif f.name in rank:
            fill, edge, w, badge, bg = C_STANDING, "#222", 1.5, f"{f.name} · {rank[f.name]}", "#111"
        else:
            fill, edge, w, badge, bg = C_STANDING, "#222", 1.5, f.name, "#111"
        folium.Polygon(locations=pts, color=edge, weight=w, fill=True,
                       fill_color=fill, fill_opacity=0.2 if not mine else 0.6).add_to(fg)
        c = f.poly_ll.centroid
        folium.Marker([c.y, c.x], icon=folium.DivIcon(
            html=f"<div style='pointer-events:none;font:900 15px Arial;color:#fff;"
                 f"background:{bg};border-radius:14px;padding:5px 9px;white-space:nowrap;"
                 f"border:2px solid #fff'>{badge}</div>",
            icon_anchor=(18, 14))).add_to(fg)
    return m, fg


def tapped_field(out):
    """Resolve a map tap to a field name, once per tap (streamlit-folium
    re-reports the same click on every rerun, so we dedupe)."""
    click = out.get("last_object_clicked") if out else None
    if click and click != ss.last_click:
        ss.last_click = click
        return logic.field_at(click["lat"], click["lng"], tolerance_m=60, fields=fields)
    return None


# ===========================================================================
# SCREEN A -- YOUR FIELDS (demo fields to tap, or draw your own farm)
# ===========================================================================

if ss.screen == "fields":
    mode = st.pills("mode", [T["mode_demo"], T["mode_draw"]],
                    default=T["mode_demo"] if ss.mode == "demo" else T["mode_draw"],
                    label_visibility="collapsed")
    new_mode = "custom" if mode == T["mode_draw"] else "demo"
    if new_mode != ss.mode:
        ss.mode, ss.plan, ss.harvested, ss.last_click = new_mode, None, [], None
        if new_mode == "demo":
            ss.custom_fields, ss.selected = [], set(logic.field_names())
        else:
            ss.selected = set()
        st.rerun()

    if ss.mode == "demo":
        st.markdown(f'<div class="step">{T["fields_title"]}</div>', unsafe_allow_html=True)
        m, fg = build_map()
        out = st_folium(m, key="hassad_map", feature_group_to_add=fg, height=380,
                        use_container_width=True, returned_objects=["last_object_clicked"])
        name = tapped_field(out)
        if name:
            ss.selected ^= {name}
            st.rerun()
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown(f'<div class="step">{T["n_fields"].format(n=len(ss.selected))}</div>',
                    unsafe_allow_html=True)
        if c2.button(T["all"], use_container_width=True):
            ss.selected = set(logic.field_names()); st.rerun()
        if c3.button(T["none"], use_container_width=True):
            ss.selected = set(); st.rerun()
        ready = bool(ss.selected)

    else:
        st.markdown(f'<div class="step">{T["draw_title"]}</div>'
                    f'<div class="hint">{T["draw_hint"]}</div>', unsafe_allow_html=True)
        m, fg = build_map(drawing=True)
        # An empty layer group can blank the map component -- only pass one
        # when there is something in it.
        out = st_folium(m, key="hassad_draw", height=420, use_container_width=True,
                        feature_group_to_add=fg if len(fg._children) else None,
                        returned_objects=["all_drawings"])
        drawings = (out or {}).get("all_drawings") or []
        drawn = logic.custom_fields_from_geojson(drawings)
        if drawn:
            st.markdown(f'<div class="step">{T["n_fields"].format(n=len(drawn))}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="hint">{T["drawn_none"]}</div>', unsafe_allow_html=True)
        ready = bool(drawn)

    if st.button(T["make_plan"], type="primary", use_container_width=True, disabled=not ready):
        if ss.mode == "custom":
            ss.custom_fields = drawn
            ss.selected = set(f.name for f in drawn)
        make_plan()
        st.rerun()
    if not ready:
        st.markdown(f'<div class="hint">{T["pick_first"]}</div>', unsafe_allow_html=True)

# ===========================================================================
# SCREEN B -- TODAY
# ===========================================================================

else:
    m, fg = build_map()
    out = st_folium(m, key="hassad_map", feature_group_to_add=fg, height=380,
                    use_container_width=True, returned_objects=["last_object_clicked"])
    name = tapped_field(out)
    if name and name in ss.selected:
        ss.focus = name
        st.rerun()
    st.markdown(f'<div class="hint">{T["tap_hint"]}</div>', unsafe_allow_html=True)
    if ss.mode == "custom":
        st.markdown(f'<div class="hint">{T["custom_refresh_note"]}</div>',
                    unsafe_allow_html=True)

    # ---- fix-the-plan card (a field was tapped)
    if ss.focus:
        is_cut = ss.focus in ss.harvested
        st.markdown(
            f'<div class="focus"><span class="name">{T["field"].format(n=ss.focus)}</span>'
            f' &nbsp;<span class="state">{T["state_cut"] if is_cut else T["state_standing"]}'
            f'</span></div>', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        if b1.button(T["not_cut"] if is_cut else T["mark_cut"], type="primary",
                     use_container_width=True, key="focus_action"):
            set_cut(ss.focus, not is_cut)
            st.rerun()
        if b2.button(T["cancel"], use_container_width=True, key="focus_cancel"):
            ss.focus = None
            st.rerun()

    # ---- hero card / done card
    if plan.get("done") or not order:
        st.markdown(f'<div class="done">✓ {T["all_cut"]}</div>', unsafe_allow_html=True)
        if st.button(T["new_season"], type="primary", use_container_width=True):
            reset_all()
            st.rerun()
    else:
        row = plan["rows"][0]
        d = row["Days"]
        st.markdown(f"""
<div class="hero">
  <div class="lbl">{T["cut_now"]}</div>
  <div class="big">{T["field"].format(n=today)}</div>
  <div class="sub">{T["size"].format(ha=row["Hectares"], d=d, days=T["day"] if d == 1 else T["days"])}</div>
  <div class="trust">{T["trust"].format(before=round(row["Largest block before (ha)"]), after=round(row["Largest block after (ha)"]))}</div>
</div>""", unsafe_allow_html=True)
        if st.button(T["is_cut"].format(n=today), type="primary", use_container_width=True):
            set_cut(today, True)
            st.rerun()
        if len(order) > 1:
            st.markdown(f'<div class="hint">{T["next"].format(n=order[1])}</div>',
                        unsafe_allow_html=True)

    if ss.undo is not None:
        if st.button(T["undo"], use_container_width=True):
            undo()
            st.rerun()

    # ---- the whole order, large type, no arrows
    st.markdown(f'<div class="step">{T["whole_order"]}</div>', unsafe_allow_html=True)
    lines = [f'<div class="line cut">✓ {T["field"].format(n=h)}</div>' for h in ss.harvested]
    for i, r in enumerate(plan["rows"]):
        cls = "line now" if i == 0 else "line"
        lines.append(f'<div class="{cls}">{T["day_line"].format(d=r["Day"], n=r["Field"])}</div>')
    st.markdown('<div class="order">' + "".join(lines) + "</div>", unsafe_allow_html=True)

    # ---- share
    wa = logic.whatsapp_text(plan["rows"], harvested=ss.harvested, lang=ss.lang)
    st.link_button(T["send_wa"], "https://wa.me/?text=" + urllib.parse.quote(wa),
                   use_container_width=True)
    st.download_button(T["print"], logic.calendar_html(plan["rows"], lang=ss.lang),
                       file_name="hassad_plan.html", mime="text/html",
                       use_container_width=True, on_click="ignore")
    if st.button(T["my_fields"], use_container_width=True):
        ss.screen, ss.focus, ss.last_click = "fields", None, None
        st.rerun()

    # ---- NUMBERS: everything for engineers and judges, last, collapsed
    with st.expander(T["numbers"], expanded=judge):
        e = logic.economics(plan)
        st.markdown(
            f'<div class="econ"><div class="big">{T["econ_title"]}</div>'
            f'<div>{T["econ_line"].format(ha=f"{e["total_ha"]:.0f}", usd=f"{e["value_usd"]:,.0f}")}</div>'
            f'<div><b>{T["econ_cost"]}</b></div>'
            f'<div class="note">{T["econ_note"].format(y=e["yield_t_per_ha"], p=f"{e["price_usd_per_t"]:.0f}")}</div></div>',
            unsafe_allow_html=True)
        if not plan.get("done") and e["delta_ha_per_event"] > 0:
            st.markdown(
                f'<div class="econ"><div class="big">{T["econ_event_title"]}</div>'
                f'<div>{T["econ_event_line"].format(plan=f"{e["mean_block_plan_ha"]:.0f}", naive=f"{e["mean_block_naive_ha"]:.0f}")}</div>'
                f'<div><b>{T["econ_event_saving"].format(ha=f"{e["delta_ha_per_event"]:.1f}", usd=f"{e["delta_usd_per_event"]:,.0f}")}</b></div></div>',
                unsafe_allow_html=True)
            chance = st.slider(T["econ_chance"], 0, 50, 10, step=5, format="%d%%")
            st.markdown(
                f'<div class="econ"><div class="big">'
                f'{T["econ_expected"].format(usd=f"{logic.expected_saving_usd(e, chance):,.0f}")}</div>'
                f'<div class="note">{T["econ_expected_note"]}</div></div>',
                unsafe_allow_html=True)
        if not plan.get("done"):
            opt, naive = plan["optimal"], plan["naive"]
            k1, k2, k3 = st.columns(3)
            k1.metric("Fire exposure vs 'largest field first'", f"−{plan['pct_vs_naive']:.0f}%")
            k2.metric("Season", f"{opt.season_days} days")
            k3.metric("Driving", f"{opt.travel_cost_km:.1f} km")
            curve = pd.DataFrame({
                "day": [x.day for x in opt.days],
                "Hassad (optimal)": [x.cumulative_risk for x in opt.days],
                "largest field first": [x.cumulative_risk for x in naive.days],
                "greedy": [x.cumulative_risk for x in plan["greedy"].days],
            }).set_index("day")
            st.line_chart(curve, height=200)
            st.caption("Cumulative fire exposure in hectare-days (largest connected block of "
                       "standing wheat, summed daily). Lower is safer.")
            cols = ["Day", "Field", "Hectares", "Largest block after (ha)", "Why this field now"]
            st.dataframe(pd.DataFrame(plan["rows"], columns=cols), hide_index=True,
                         use_container_width=True)
            st.download_button("Schedule (CSV)", logic.schedule_csv(plan["rows"]),
                               file_name="hassad_schedule.csv", mime="text/csv",
                               on_click="ignore")

        st.markdown("**Model switches** (judges only — the farmer never sees these)")
        rule = st.pills("Gap rule", ["Dry year 175 m", "Wet year 100 m"],
                        default="Dry year 175 m" if ss.dry_year else "Wet year 100 m")
        bal = st.toggle("Also less driving", value=ss.balanced)
        mach = ss.machine_at
        if bal and ss.harvested:
            mach = st.selectbox("Machine is at", ss.harvested,
                                index=ss.harvested.index(ss.machine_at)
                                if ss.machine_at in ss.harvested else len(ss.harvested) - 1)
        new_dry = (rule != "Wet year 100 m")
        if (new_dry, bool(bal), mach) != (ss.dry_year, ss.balanced, ss.machine_at):
            ss.dry_year, ss.balanced, ss.machine_at = new_dry, bool(bal), mach
            rebuild_plan()
            st.rerun()

        st.caption(f"Exact optimum over every possible order of {len(plan['G'].nodes)} fields "
                   f"(gap rule {plan['threshold']:.0f} m; "
                   f"{'fire + driving' if plan['balanced'] else 'fire only'}). Solver verified "
                   "against brute-force enumeration; gap conditions measured from Sentinel-2 "
                   "imagery. Hassad حصاد · FIRST Global Challenge 2026 · Team Lebanon.")
