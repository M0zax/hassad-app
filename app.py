"""
HASSAD -- the farmer-facing app.   Run with:   streamlit run app.py

A harvest almanac on a phone, not a dashboard (design system "Almanac",
design/mockup-final.html): warm paper, one ink, a ledger of days, one
harvest-gold accent that marks exactly one thing per screen, fire red spent
on one number only. No gradients, no pills, no logo, no emoji.

  FIELDS  "Tap your fields" / "Draw your fields"  -> one button: Make my plan
  TODAY   the hero card (which field, how long, one trust line), one primary
          action, tap a field on the map to mark it cut / not cut, Undo,
          the whole order as a ledger, WhatsApp and Print.
  NUMBERS one section at the bottom for judges (/?judge=1 only).
  ABOUT   /?page=about -- one tap from every screen, one tap back.

All strings live in i18n.py (English + Arabic, right-to-left layout).
All the thinking lives in app_logic.py (tested separately). The skin lives in
hassad_style.py. This file is layout.
"""

import urllib.parse

import altair as alt
import folium
from folium.plugins import Draw
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import app_logic as logic
import hassad_style as skin
from i18n import CONTENT, FIELD_LABELS, STRINGS, days_word, label

st.set_page_config(page_title="Hassad", page_icon="favicon.png", layout="centered",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------

ss = st.session_state
qp = st.query_params
ss.setdefault("lang", "ar" if qp.get("lang") == "ar" else "en")
ss.setdefault("mode", "custom" if qp.get("mode") == "draw" else "demo")
ss.setdefault("custom_fields", [])
ss.setdefault("selected", set(logic.field_names()) if ss.mode == "demo" else set())
ss.setdefault("plan", None)
ss.setdefault("harvested", [])
ss.setdefault("screen", "fields")
ss.setdefault("page", "about" if qp.get("page") == "about" else "plan")
ss.setdefault("focus", None)
ss.setdefault("undo", None)
ss.setdefault("last_click", None)
ss.setdefault("flash", None)
ss.setdefault("drawn_any", False)
ss.setdefault("dry_year", True)          # judge-only model switches
ss.setdefault("balanced", False)
ss.setdefault("machine_at", None)

T = STRINGS[ss.lang]
RTL = ss.lang == "ar"
OTHER = "ar" if ss.lang == "en" else "en"
DRY_RULE, WET_RULE = list(logic.GAP_RULES)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def bdi(x):
    """Numbers, ranges and Latin names stay left-to-right inside Arabic sentences."""
    return f"<bdi>{x}</bdi>"


def current_fields():
    return ss.custom_fields if ss.mode == "custom" else list(logic.all_fields())


def gap_rule():
    return DRY_RULE if ss.dry_year else WET_RULE


def sync_url():
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


# ---- navigation: every screen is one tap away, nothing needs a typed URL
def go_plan():
    ss.page = "plan"
    qp.pop("page", None)


def go_about():
    ss.page = "about"
    qp["page"] = "about"


def toggle_lang():
    ss.lang = OTHER
    if ss.plan is not None:
        ss.plan = logic.relabel(ss.plan, ss.lang)
    sync_url()


def go_draw():
    ss.page, ss.screen, ss.mode = "plan", "fields", "custom"
    ss.plan, ss.harvested, ss.undo, ss.focus, ss.last_click = None, [], None, None, None
    ss.custom_fields, ss.selected = [], set()
    ss.pop("mode_seg", None)
    qp.pop("page", None)
    qp.pop("judge", None)
    qp["mode"] = "draw"
    sync_url()


def go_judge():
    ss.page, ss.mode = "plan", "demo"
    ss.selected = set(logic.field_names())
    ss.pop("mode_seg", None)
    qp.pop("page", None)
    qp.pop("mode", None)
    qp["judge"] = "1"
    make_plan()


# ---- restore from the URL (refresh, forwarded link) or the demo shortcuts
judge = "judge" in qp or "auto" in qp
if ss.plan is None and ss.page == "plan":
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
# THE SKIN
# ---------------------------------------------------------------------------

skin.inject(RTL)

if ss.flash:
    st.toast(ss.flash)
    ss.flash = None

# ---------------------------------------------------------------------------
# HEADER: wordmark on the leading edge, two text controls on the trailing edge
# ---------------------------------------------------------------------------

on_fields = ss.page == "plan" and ss.screen == "fields"
with st.container(key="row_hdr"):
    h1, h2 = st.columns([2, 1.3], gap="small", vertical_alignment="center")
    with h1:
        if on_fields:
            html(f'<h1 class="hassad">{T["title"]} <span class="wm2" lang="{OTHER}">'
                 f'{STRINGS[OTHER]["title"]}</span></h1>')
        else:
            html(f'<h1 class="hassad compact">{T["title"]}</h1>')
    with h2:
        with st.container(key="row_hdrbtn"):
            b1, b2 = st.columns(2, gap="small")
            if b1.button(STRINGS[OTHER]["lang_name"], key="lang_btn", type="tertiary"):
                toggle_lang()
                st.rerun()
            if ss.page == "about":
                if b2.button(T["back_plan"], key="back_top", type="tertiary"):
                    go_plan()
                    st.rerun()
            else:
                if b2.button(T["about"], key="about_btn", type="tertiary"):
                    go_about()
                    st.rerun()
if on_fields:
    html(f'<p class="tagline">{T["tagline"]}</p>')
else:
    html('<hr class="hdr-rule">')

# ---------------------------------------------------------------------------
# ABOUT PAGE
# ---------------------------------------------------------------------------

if ss.page == "about":
    html(f'<div class="step"><h2>{T["about_title"]}</h2></div><span class="over">{T["try_it"]}</span>')
    with st.container(key="row_try1"):
        a, b = st.columns(2, gap="small")
        if a.button(T["try_plan"], key="try_plan", width="stretch"):
            go_plan()
            st.rerun()
        if b.button(T["try_draw"], key="try_draw", width="stretch"):
            go_draw()
            st.rerun()
    with st.container(key="row_try2"):
        a, b = st.columns(2, gap="small")
        if a.button(T["try_judge"], key="try_judge", width="stretch"):
            go_judge()
            st.rerun()
        if b.button(STRINGS[OTHER]["lang_name"], key="try_lang", width="stretch"):
            toggle_lang()
            st.rerun()
    import about
    if RTL:
        with st.container(key="about"):
            about.render_ar_summary()
    with st.container(key="about_en"):          # stays left-to-right on the Arabic page
        about.render_en()
    if st.button(T["back_plan"], key="back_bottom", type="tertiary"):
        go_plan()
        st.rerun()
    st.stop()

# ---------------------------------------------------------------------------
# THE MAP -- one component, recoloured per state, zoom preserved between taps
# ---------------------------------------------------------------------------

plan = ss.plan
fields = current_fields()
order = plan["order"] if (plan and ss.screen == "today") else []
today = order[0] if order else None
rank = {f: i + 1 for i, f in enumerate(order)}
MAP_HEAD = folium.Element(skin.MAP_HEAD)
CTRL_POS = "topright" if RTL else "topleft"


def badge(text, bg, fg, bstyle, bcol):
    return (f"<div style='pointer-events:none;direction:ltr;unicode-bidi:isolate;display:inline-block;"
            f"font:600 13px \"IBM Plex Sans\",Arial,sans-serif;color:{fg};background:{bg};"
            f"border:1px {bstyle} {bcol};border-radius:2px;padding:2px 6px;white-space:nowrap;"
            f"line-height:1.1'>{text}</div>")


def build_map(drawing=False):
    base = fields or list(logic.all_fields())
    lat0 = sum(f.poly_ll.centroid.y for f in base) / len(base)
    lon0 = sum(f.poly_ll.centroid.x for f in base) / len(base)
    m = folium.Map(location=[lat0, lon0], zoom_start=14, tiles=None,
                   zoom_control=CTRL_POS if drawing else False,
                   control_scale=False, scrollWheelZoom=False)
    m.get_root().header.add_child(MAP_HEAD)
    if fields:
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
        Draw(export=False, position=CTRL_POS,
             draw_options={"polyline": False, "circle": False, "marker": False,
                           "circlemarker": False, "rectangle": True,
                           "polygon": {"allowIntersection": False, "showArea": True}},
             edit_options={"edit": True, "remove": True}).add_to(m)
    fg = folium.FeatureGroup(name="fields")
    for f in fields:
        pts = [(lat, lon) for lon, lat in f.poly_ll.exterior.coords]
        mine, cut, is_today = f.name in ss.selected, f.name in ss.harvested, f.name == today
        name = label(f.name)
        if not mine:
            folium.Polygon(locations=pts, color=skin.PAPER, weight=1.2, dash_array="4 3", fill=True,
                           fill_color=skin.STRAW, fill_opacity=0.25).add_to(fg)
            txt = badge(name, skin.PAPER, skin.MUTED, "dashed", skin.RULE)
        elif cut:
            folium.Polygon(locations=pts, color=skin.INK, weight=1.1, dash_array="4 3", fill=True,
                           fill_color=skin.STUBBLE, fill_opacity=0.5).add_to(fg)
            txt = badge(f"{name} ✓", skin.STUBBLE, skin.INK, "solid", skin.INK)
        elif is_today:
            folium.Polygon(locations=pts, color=skin.INK, weight=2.2, fill=True,
                           fill_color=skin.GOLD, fill_opacity=0.85).add_to(fg)
            txt = badge(f"{name} · 1", skin.GOLD, skin.INK, "solid", skin.INK)
        else:
            folium.Polygon(locations=pts, color=skin.INK, weight=1.1, fill=True,
                           fill_color=skin.STRAW, fill_opacity=0.55).add_to(fg)
            r = f" · {rank[f.name]}" if f.name in rank else ""
            txt = badge(f"{name}{r}", skin.STRAW, skin.INK, "solid", skin.INK)
        p = f.poly_ll.representative_point()
        lat, lon = p.y, p.x
        if f.name == "nte":                       # hand offset: clears field 5
            lat, lon = lat - 0.00018, lon - 0.00020
        chars = len(txt.split(">")[-2].split("<")[0]) if ">" in txt else 3
        folium.Marker([lat, lon], icon=folium.DivIcon(
            html=txt, icon_anchor=(chars * 4 + 6, 9))).add_to(fg)
    return m, fg


def tapped_field(out):
    click = out.get("last_object_clicked") if out else None
    if click and click != ss.last_click:
        ss.last_click = click
        return logic.field_at(click["lat"], click["lng"], tolerance_m=150, fields=fields)
    return None


def show_map(m, fg, key, height, returned):
    with st.container(key="map_frame"):
        return st_folium(m, key=key, height=height, width="stretch",
                         feature_group_to_add=fg if len(fg._children) else None,
                         returned_objects=returned)


def step(title, over=None):
    o = f'<span class="over">{over}</span>' if over else ""
    html(f'<div class="step">{o}<h2>{title}</h2></div>')


def money(x):
    """'$120k' / '≈ $1.3k' -- no false precision on placeholder economics."""
    k = x / 1000.0
    s = f"{k:.0f}" if k >= 10 else f"{k:.1f}"
    return f"{s} ألف" if RTL else f"{s}k"


# ===========================================================================
# SCREEN A -- YOUR FIELDS
# ===========================================================================

if ss.screen == "fields":
    mode = st.segmented_control("mode", [T["mode_demo"], T["mode_draw"]],
                                default=T["mode_demo"] if ss.mode == "demo" else T["mode_draw"],
                                label_visibility="collapsed", width="stretch", key="mode_seg")
    new_mode = "custom" if mode == T["mode_draw"] else "demo"
    if new_mode != ss.mode:
        ss.mode, ss.plan, ss.harvested, ss.last_click = new_mode, None, [], None
        ss.custom_fields = []
        ss.selected = set(logic.field_names()) if new_mode == "demo" else set()
        if new_mode == "custom":
            qp["mode"] = "draw"
        else:
            qp.pop("mode", None)
        st.rerun()

    if ss.mode == "demo":
        html(f'<p class="note">{T["demo_note"]}</p>')
        if st.button(T["demo_more"], type="tertiary", key="demo_more_btn"):
            go_about()
            st.rerun()
        step(T["fields_title"], T["step1"])
        m, fg = build_map()
        out = show_map(m, fg, "hassad_map", 400, ["last_object_clicked"])
        name = tapped_field(out)
        if name:
            ss.selected ^= {name}
            st.rerun()
        with st.container(key="row_count"):
            c1, c2, c3 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
            c1.markdown(f'<div class="count">{T["n_fields"].format(n=len(ss.selected))}</div>',
                        unsafe_allow_html=True)
            with c2:
                with st.container(key="small_all"):
                    if st.button(T["all"], key="all_btn", width="stretch"):
                        ss.selected = set(logic.field_names())
                        st.rerun()
            with c3:
                with st.container(key="small_none"):
                    if st.button(T["none"], key="none_btn", width="stretch"):
                        ss.selected = set()
                        st.rerun()
        ready = bool(ss.selected)
        drawn = []
    else:
        with st.expander(T["guide_title"], expanded=not ss.drawn_any):
            html(CONTENT["draw_guide"][ss.lang])
        step(T["draw_title"], T["step1"])
        html(f'<p class="hint">{T["draw_hint"]}</p>')
        m, fg = build_map(drawing=True)
        out = show_map(m, fg, "hassad_draw", 400, ["all_drawings"])
        drawings = (out or {}).get("all_drawings") or []
        drawn = logic.custom_fields_from_geojson(drawings)
        ss.drawn_any = bool(drawn)
        if drawn:
            html(f'<div class="count">{T["n_fields"].format(n=len(drawn))}</div>')
        else:
            html(f'<p class="hint">{T["drawn_none"]}</p>')
        ready = bool(drawn)

    if st.button(T["make_plan"], type="primary", width="stretch", disabled=not ready):
        if ss.mode == "custom":
            ss.custom_fields = drawn
            ss.selected = set(f.name for f in drawn)
        make_plan()
        st.rerun()
    if not ready:
        html(f'<p class="hint">{T["pick_first"] if ss.mode == "demo" else T["draw_first"]}</p>')

# ===========================================================================
# SCREEN B -- TODAY
# ===========================================================================

else:
    m, fg = build_map()
    out = show_map(m, fg, "hassad_map", 380, ["last_object_clicked"])
    name = tapped_field(out)
    if name and name in ss.selected:
        ss.focus = name
        st.rerun()
    html(f'<p class="hint">{T["tap_hint"]}</p>')
    ha_of = {f.name: f.area_ha for f in fields}
    U = T["ha"]

    if ss.focus:
        # ---- fix-the-plan card: replaces the hero, so there is one primary on screen
        is_cut = ss.focus in ss.harvested
        html(f'<div class="focus"><span class="name">{T["field"].format(n=bdi(label(ss.focus)))}</span>'
             f'<span class="state">{T["state_cut"] if is_cut else T["state_standing"]}</span></div>')
        html(f'<p class="hint">{T["cut_help"]}</p>')
        with st.container(key="row_focus"):
            b1, b2 = st.columns(2, gap="small")
            if is_cut:
                act = b1.button(T["not_cut"], type="primary", key="focus_action", width="stretch")
            else:
                act = b1.button(T["mark_cut"], type="primary", key="focus_action", width="stretch")
            if act:
                set_cut(ss.focus, not is_cut)
                st.rerun()
            if b2.button(T["cancel"], key="focus_cancel", width="stretch"):
                ss.focus = None
                st.rerun()

    elif plan.get("done") or not order:
        html(f'<div class="done">{T["all_cut"]}</div>')
        if st.button(T["new_season"], type="primary", width="stretch"):
            reset_all()
            st.rerun()

    else:
        row = plan["rows"][0]
        before = round(row["Largest block before (ha)"])
        after = round(row["Largest block after (ha)"])
        # the template already carries the unit ("{before} ha") -- bold only the number
        trust = T["trust"].format(before=f'<b class="fire">{bdi(before)}</b>',
                                  arrow='<span class="arr">→</span>',
                                  after=f'<b>{bdi(after)}</b>')
        html(f'<div class="hero"><div class="lbl">{T["cut_now"]}</div>'
             f'<div class="big">{T["field"].format(n=bdi(label(today)))}</div>'
             f'<div class="sub">{bdi(row["Hectares"])} {U} · {days_word(row["Days"], ss.lang)}</div>'
             f'<div class="trust">{trust}</div></div>')
        with st.expander(T["what_title"]):
            html(CONTENT["criteria_short"][ss.lang])
        if st.button(T["is_cut"].format(n=label(today)), type="primary", width="stretch"):
            set_cut(today, True)
            st.rerun()
        if len(order) > 1:
            html(f'<p class="hint next">{T["next"].format(n=label(order[1]))}</p>')

    if ss.undo is not None:
        if st.button(T["undo"], key="undo_btn", width="stretch"):
            undo()
            st.rerun()

    # ---- the whole order as a ledger: day | field | hectares
    step(T["whole_order"])
    rows_html = []
    for h in ss.harvested:
        rows_html.append(f'<tr class="cut"><td class="d">✓</td>'
                         f'<td class="f">{T["field"].format(n=bdi(label(h)))}</td>'
                         f'<td class="ha">{bdi(f"{ha_of.get(h, 0):.1f}")} {U}</td></tr>')
    for i, r in enumerate(plan["rows"]):
        day = str(r["Day"])
        dcell = (T["days_range"] if "–" in day else T["day_range"]).format(d=bdi(day))
        rows_html.append(f'<tr{" class=\"now\"" if i == 0 else ""}><td class="d">{dcell}</td>'
                         f'<td class="f">{T["field"].format(n=bdi(label(r["Field"])))}</td>'
                         f'<td class="ha">{bdi(r["Hectares"])} {U}</td></tr>')
    html(f'<table class="order" role="table">{"".join(rows_html)}</table>')

    # ---- share: WhatsApp | Print, then the way back to the fields
    def _relabel(text):
        """The reason sentences come from app_logic with raw ids ('nte');
        show the same display names the rest of the screen uses."""
        for raw, shown in FIELD_LABELS.items():
            text = text.replace(f"Field {raw}", f"Field {shown}").replace(f"حقل {raw}", f"حقل {shown}")
        return text
    disp_rows = [dict(r, Field=label(r["Field"]),
                      **{"Why this field now": _relabel(r["Why this field now"])})
                 for r in plan["rows"]]
    disp_cut = [label(h) for h in ss.harvested]
    share_rows = [dict(r, Day=str(r["Day"])) for r in disp_rows]
    wa = logic.whatsapp_text(share_rows, harvested=disp_cut, lang=ss.lang)
    cal = logic.calendar_html(share_rows, lang=ss.lang)
    if RTL:
        wa = wa.replace(", ", "، ")
    cal = cal.replace("</style>", skin.FONTS_IMPORT + skin.CALENDAR_CSS + "</style>", 1)
    if ss.mode == "custom":
        html(f'<p class="hint">{T["custom_refresh_note"]}</p>')
    with st.container(key="row_share"):
        s1, s2 = st.columns(2, gap="small")
        s1.link_button(T["send_wa"], "https://wa.me/?text=" + urllib.parse.quote(wa),
                       width="stretch")
        s2.download_button(T["print"], cal, file_name="hassad_plan.html", mime="text/html",
                           width="stretch", on_click="ignore")
    if st.button(T["my_fields"], type="tertiary", key="my_fields_btn"):
        ss.screen, ss.focus, ss.last_click = "fields", None, None
        st.rerun()

    # ---- NUMBERS: for judges only (/?judge=1); the farmer never sees engineering
    if judge:
        html('<hr class="rule">')
        with st.expander(T["numbers"], expanded=True):
            e = logic.economics(plan)
            html(f'<div class="econ"><div class="t">{T["econ_title"]}</div>'
                 f'<div class="line">{T["econ_line"].format(ha=bdi(f"{e['total_ha']:.0f}"), usd="<b>" + bdi(money(e["value_usd"])) + "</b>")}</div>'
                 f'<div class="line"><b>{T["econ_cost"]}</b></div>'
                 f'<div class="note">{T["econ_note"].format(y=bdi(e["yield_t_per_ha"]), p=bdi(f"{e['price_usd_per_t']:.0f}"))}</div></div>')
            if not plan.get("done") and e["delta_ha_per_event"] > 0:
                html(f'<div class="econ"><div class="t">{T["econ_event_title"]}</div>'
                     f'<div class="line">{T["econ_event_line"].format(plan=bdi(f"{e['mean_block_plan_ha']:.0f}"), naive=bdi(f"{e['mean_block_naive_ha']:.0f}"))}</div>'
                     f'<div class="line"><b>{T["econ_event_saving"].format(ha=bdi(f"{e['delta_ha_per_event']:.1f}"), usd=bdi(money(e["delta_usd_per_event"])))}</b></div></div>')
                chance = st.slider(T["econ_chance"], 0, 50, 10, step=5, format="%d%%")
                html(f'<div class="econ"><div class="t">'
                     f'{T["econ_expected"].format(usd=bdi(money(logic.expected_saving_usd(e, chance))))}</div>'
                     f'<div class="note">{T["econ_expected_note"]}</div></div>')

            if not plan.get("done"):
                opt, naive = plan["optimal"], plan["naive"]
                html(f'<div class="stats">'
                     f'<div class="stat"><div class="l">{T["m_exposure"]}</div><div class="v fire">{bdi(T["m_exposure_v"].format(pct=f"{plan['pct_vs_naive']:.0f}"))}</div></div>'
                     f'<div class="stat"><div class="l">{T["m_season"]}</div><div class="v">{bdi(opt.season_days)}<span class="u">{T["unit_days"]}</span></div></div>'
                     f'<div class="stat"><div class="l">{T["m_driving"]}</div><div class="v">{bdi(f"{opt.travel_cost_km:.1f}")}<span class="u">{T["unit_km"]}</span></div></div>'
                     f'</div>')
                with st.container(key="judge_en"):
                    curve = pd.DataFrame({
                        "day": [x.day for x in opt.days],
                        T["s_hassad"]: [x.cumulative_risk for x in opt.days],
                        T["s_naive"]: [x.cumulative_risk for x in naive.days],
                        T["s_greedy"]: [x.cumulative_risk for x in plan["greedy"].days],
                    }).set_index("day")
                    # one line per strategy; the legend runs vertically so no label is
                    # ever cut off on a phone (st.line_chart clips a one-row legend)
                    series = [T["s_hassad"], T["s_naive"], T["s_greedy"]]
                    long = curve.reset_index().melt("day", var_name="series", value_name="exposure")
                    st.altair_chart(
                        alt.Chart(long).mark_line(strokeWidth=2.5).encode(
                            x=alt.X("day:Q", title=None),
                            y=alt.Y("exposure:Q", title=None),
                            color=alt.Color("series:N", title=None, sort=series,
                                            scale=alt.Scale(domain=series,
                                                            range=[skin.GOLD, skin.RULE, skin.STUBBLE]),
                                            legend=alt.Legend(orient="bottom", direction="vertical",
                                                              labelLimit=600, symbolType="stroke",
                                                              symbolStrokeWidth=3)),
                        ).properties(height=200),
                        width="stretch", height=330)   # 200 px plot + axis + three legend rows
                    st.caption(T["chart_caption"])
                    table = pd.DataFrame(disp_rows, columns=["Day", "Field", "Hectares",
                                                             "Largest block after (ha)", "Why this field now"])
                    table.columns = [T["col_day"], T["col_field"], T["col_ha"], T["col_block_after"], T["col_why"]]
                    st.dataframe(table, hide_index=True, width="stretch")
                    st.download_button(T["csv"], logic.schedule_csv(disp_rows),
                                       file_name="hassad_schedule.csv", mime="text/csv",
                                       type="tertiary", key="csv_btn", on_click="ignore")

            html(f'<p class="hint">{T["model_switches"]}</p>')
            rule = st.segmented_control(T["gap_rule"], [T["gap_dry"], T["gap_wet"]],
                                        default=T["gap_dry"] if ss.dry_year else T["gap_wet"],
                                        width="stretch", key="gap_seg")
            obj = st.segmented_control(T["objective"], [T["obj_fire"], T["obj_driving"]],
                                       default=T["obj_driving"] if ss.balanced else T["obj_fire"],
                                       width="stretch", key="obj_seg")
            new_dry = rule != T["gap_wet"]
            new_bal = obj == T["obj_driving"]
            mach = ss.machine_at
            if new_bal and ss.harvested:
                mach = st.selectbox(T["machine_at"], ss.harvested, format_func=label,
                                    index=ss.harvested.index(ss.machine_at)
                                    if ss.machine_at in ss.harvested else len(ss.harvested) - 1)
            if (new_dry, new_bal, mach) != (ss.dry_year, ss.balanced, ss.machine_at):
                ss.dry_year, ss.balanced, ss.machine_at = new_dry, new_bal, mach
                rebuild_plan()
                st.rerun()
            st.caption(T["footer"].format(n=len(plan["G"].nodes), m=f"{plan['threshold']:.0f}",
                                          mode=T["fire_driving"] if plan["balanced"] else T["fire_only"]))
