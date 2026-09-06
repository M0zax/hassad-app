"""
Hassad -- the "Almanac" skin for Streamlit 1.63 (design/mockup-final.html is
the reference sheet). Two style blocks: BASE for both languages, RTL added
only when the app is in Arabic. Nothing here touches behaviour.

Selectors: Streamlit-owned data-testids and button[kind] attributes as they
exist in the 1.63 frontend bundle; `.st-key-*` hooks need the matching
key= in app.py (containers keyed row_* never stack on a phone).
"""

import streamlit as st

# Map colours (folium cannot see page CSS) -- the same tokens as :root below.
PAPER, DEEP, INK, MUTED, RULE = "#F7F1E3", "#EFE5CF", "#22190F", "#6B5A44", "#8C7656"
STRAW, STUBBLE, GOLD, FIRE = "#E2C46B", "#B8A785", "#AD780C", "#B3261E"

FONTS_IMPORT = ("@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500..700"
                "&family=Amiri:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600;700"
                "&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');")

BASE_CSS = FONTS_IMPORT + """
:root{--paper:#F7F1E3;--deep:#EFE5CF;--ink:#22190F;--muted:#6B5A44;--rule:#8C7656;--hair:#D9CCB0;
 --straw:#E2C46B;--stubble:#B8A785;--gold:#AD780C;--fire:#B3261E;
 --sans:"IBM Plex Sans","IBM Plex Sans Arabic","Segoe UI",Roboto,system-ui,sans-serif;
 --sans-ar:"IBM Plex Sans Arabic","IBM Plex Sans","Noto Sans Arabic",sans-serif;
 --serif:"Fraunces",Georgia,"Times New Roman",serif;--serif-ar:"Amiri","Noto Naskh Arabic",serif;}

/* ---- page chrome -------------------------------------------------------- */
header[data-testid="stHeader"],[data-testid="stStatusWidget"],[data-testid="stToolbar"],
[data-testid="stHeaderActionElements"]{display:none!important;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--paper);}
.stApp{color:var(--ink);font-family:var(--sans);-webkit-tap-highlight-color:transparent;}
.block-container,[data-testid="stMainBlockContainer"]{max-width:480px!important;padding:12px 16px 96px!important;text-align:start;}
[data-testid="stVerticalBlock"]{gap:10px!important;}
/* Streamlit pulls every markdown block up by 1rem to cancel its own trailing <p>
   margin; the rules below manage margins themselves, so blocks keep their real height */
[data-testid="stMarkdownContainer"]{color:var(--ink);font-family:var(--sans);margin-bottom:0!important;}
[data-testid="stMarkdownContainer"] p{font-size:17px;line-height:1.4;margin:0 0 10px;}
[data-testid="stMarkdownContainer"] p:last-child{margin-bottom:0;}
[data-testid="stMarkdownContainer"] strong,[data-testid="stMarkdownContainer"] b{font-weight:600;}
[data-testid="stMarkdownContainer"] a{color:var(--ink);text-decoration:underline;text-underline-offset:4px;text-decoration-color:var(--rule);}
[data-testid="stMarkdownContainer"] hr{border:0;border-top:1px solid var(--hair);margin:20px 0;}
[data-testid="stMarkdownContainer"] ol,[data-testid="stMarkdownContainer"] ul{padding-inline-start:1.4rem;padding-left:0;list-style-position:outside;margin:0 0 10px;}
[data-testid="stMarkdownContainer"] li{font-size:17px;line-height:1.4;margin-bottom:4px;}
bdi{unicode-bidi:isolate;}
::selection{background:var(--straw);color:var(--ink);}
/* labels inside buttons, segments and expander summaries are markdown paragraphs:
   they take the control's face, size and colour, not the running-text rules */
.stButton [data-testid="stMarkdownContainer"],.stLinkButton [data-testid="stMarkdownContainer"],
.stDownloadButton [data-testid="stMarkdownContainer"],[data-testid="stButtonGroup"] [data-testid="stMarkdownContainer"],
[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],
.stButton [data-testid="stMarkdownContainer"] p,.stLinkButton [data-testid="stMarkdownContainer"] p,
.stDownloadButton [data-testid="stMarkdownContainer"] p,[data-testid="stButtonGroup"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p{
 color:inherit!important;font-size:inherit!important;font-family:inherit!important;line-height:inherit!important;margin:0!important;}
[data-testid="stElementContainer"]{text-align:start;}
.stButton button,.stLinkButton a,.stDownloadButton button,[data-testid="stButtonGroup"] button,
.hero,.focus,.done,[data-testid="stExpanderDetails"],[data-testid="stToast"]{transition:none!important;animation:none!important;}

/* ---- wordmark, tagline, overlines, headings ----------------------------- */
[data-testid="stMarkdownContainer"] h1.hassad{font-family:var(--serif);font-variation-settings:"opsz" 96;font-weight:600;
 font-size:38px;line-height:1.05;letter-spacing:-.005em;margin:0!important;padding:4px 0 0!important;white-space:nowrap;color:var(--ink);}
[data-testid="stMarkdownContainer"] h1.hassad a.home,[data-testid="stMarkdownContainer"] h1.hassad a.home:hover{color:inherit!important;text-decoration:none!important;}
[data-testid="stMarkdownContainer"] h1.hassad .wm2{font-family:var(--serif-ar);font-weight:700;font-size:.8em;color:var(--muted);margin-inline-start:6px;letter-spacing:0;}
[data-testid="stMarkdownContainer"] h1.hassad.compact{font-size:26px;padding-top:8px!important;}
[data-testid="stMarkdownContainer"] p.tagline{font-size:16px;line-height:1.4;color:var(--muted);margin:0 0 4px;}
.hdr-rule{border:0;border-top:1px solid var(--hair);margin:0 0 2px;height:0;}
.over{display:block;font-family:var(--sans);font-size:12.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0;}
.step{margin:14px 0 6px;}
[data-testid="stMarkdownContainer"] .step h2,[data-testid="stMarkdownContainer"] h2.step{font-family:var(--serif);font-variation-settings:"opsz" 48;font-weight:600;
 font-size:24px;line-height:1.2;margin:0!important;padding:0!important;color:var(--ink);}
[data-testid="stMarkdownContainer"] .hint,[data-testid="stMarkdownContainer"] .note{font-family:var(--sans);color:var(--muted);font-size:15px;line-height:1.45;margin:4px 0 6px;}
[data-testid="stMarkdownContainer"] .count{font-size:19px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--ink);margin:0;line-height:1.2;white-space:nowrap;}
[data-testid="stMarkdownContainer"] .count .ha{display:block;font-size:15px;font-weight:400;color:var(--muted);margin-top:2px;}
.rule{border:0;border-top:1px solid var(--hair);margin:14px 0;height:0;}

/* ---- buttons: rectangular, 56 px, one primary per screen ---------------- */
.stButton button,.stLinkButton a,.stDownloadButton button{font-family:var(--sans);font-weight:600;line-height:1.25;
 border-radius:4px!important;box-shadow:none!important;font-variant-numeric:tabular-nums;letter-spacing:0;}
.stButton button p,.stLinkButton a p,.stDownloadButton button p{font-weight:inherit;font-size:inherit;line-height:inherit;}
.stLinkButton a{display:flex;align-items:center;justify-content:center;text-decoration:none!important;}
.stButton button[kind="primary"]{min-height:56px;padding:0 16px;font-size:18px;background:var(--ink)!important;color:var(--paper)!important;border:2px solid var(--ink)!important;}
.stButton button[kind="primary"]:hover{background:#3A2E1F!important;border-color:#3A2E1F!important;color:var(--paper)!important;}
.stButton button[kind="primary"]:disabled,.stButton button[kind="primary"]:disabled:hover{background:var(--stubble)!important;border-color:var(--stubble)!important;color:var(--muted)!important;opacity:1!important;cursor:default;}
.stButton button[kind="secondary"],.stLinkButton a[kind="secondary"],.stDownloadButton button[kind="secondary"]{min-height:56px;padding:0 14px;font-size:18px;
 background:var(--paper)!important;color:var(--ink)!important;border:2px solid var(--rule)!important;}
.stButton button[kind="secondary"]:hover,.stLinkButton a[kind="secondary"]:hover,.stDownloadButton button[kind="secondary"]:hover{background:var(--deep)!important;color:var(--ink)!important;border-color:var(--rule)!important;}
.stButton button[kind="secondary"]:active,.stLinkButton a[kind="secondary"]:active,.stDownloadButton button[kind="secondary"]:active{background:var(--deep)!important;}
.stButton button[kind="tertiary"],.stDownloadButton button[kind="tertiary"],.stLinkButton a[kind="tertiary"]{min-height:44px;padding:0 6px!important;width:auto;
 background:transparent!important;border:0!important;color:var(--ink)!important;font-weight:500;font-size:16px;
 text-decoration:underline!important;text-decoration-color:var(--rule)!important;text-decoration-thickness:1px;text-underline-offset:5px;}
.stButton button[kind="tertiary"]:hover,.stDownloadButton button[kind="tertiary"]:hover{color:var(--ink)!important;background:transparent!important;}
.stButton button[kind="tertiary"] p{font-weight:500;}
[class*="st-key-small"] .stButton button{min-height:44px!important;padding:0 8px!important;font-size:16px;white-space:nowrap;}
/* two-up rows (share, try-it): Streamlit's label container cuts a long label with an
   ellipsis; here it shrinks a little on a narrow phone and then wraps instead */
.st-key-row_share .stButton button,.st-key-row_share .stLinkButton a,.st-key-row_share .stDownloadButton button,
[class*="st-key-row_try"] .stButton button{padding:0 8px!important;font-size:16.5px;}
@media (max-width:400px){
 .st-key-row_share .stButton button,.st-key-row_share .stLinkButton a,.st-key-row_share .stDownloadButton button,
 [class*="st-key-row_try"] .stButton button{font-size:16px;}
}
.st-key-row_share [data-testid="stMarkdownContainer"],[class*="st-key-row_try"] [data-testid="stMarkdownContainer"],
.st-key-row_share [data-testid="stMarkdownContainer"] p,[class*="st-key-row_try"] [data-testid="stMarkdownContainer"] p{
 white-space:normal!important;overflow:visible!important;text-overflow:clip!important;text-align:center;}
.stButton button:focus-visible,.stLinkButton a:focus-visible,.stDownloadButton button:focus-visible,
[data-testid="stButtonGroup"] button:focus-visible,[data-testid="stExpander"] summary:focus-visible{outline:2px solid var(--gold)!important;outline-offset:2px;box-shadow:none!important;}

/* ---- rows that never stack on a phone (containers keyed row_*) ---------- */
@media (max-width:640px){
 [class*="st-key-row_"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:8px;}
 [class*="st-key-row_"] [data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important;width:auto!important;}
 .st-key-row_count [data-testid="stColumn"]:first-child{flex:1.6 1 0!important;}
}
/* ---- header: wordmark on the leading edge, two text links on the trailing edge.
   The keyed class is on the stVerticalBlock; its row is > stLayoutWrapper > stHorizontalBlock.
   When both do not fit on one line (the full wordmark on a phone) the links wrap onto
   their own line, still at the trailing edge; the compact wordmark shares the line. */
.st-key-row_hdr>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]{align-items:center;flex-wrap:wrap!important;gap:0 12px!important;}
.st-key-row_hdr>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]:first-child{flex:1 1 auto!important;min-width:0!important;width:auto!important;}
.st-key-row_hdr>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]:last-child{flex:0 0 auto!important;width:auto!important;min-width:0!important;margin-inline-start:auto;}
.st-key-row_hdrbtn>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]{justify-content:flex-end;gap:8px!important;flex-wrap:nowrap!important;}
.st-key-row_hdrbtn [data-testid="stColumn"]{flex:0 0 auto!important;width:auto!important;min-width:0!important;}
.st-key-row_hdrbtn .stButton button{white-space:nowrap;}
.st-key-row_count .stButton{display:flex;justify-content:flex-end;}

/* ---- mode switch: st.segmented_control ----------------------------------
   1.63 marks each cell button[data-variant="segmented_control"] and the chosen one
   [data-selected="true"] (there is no kind= attribute on these buttons). */
[data-testid="stButtonGroup"]{width:100%;}
[data-testid="stButtonGroup"]:has(button[data-variant="segmented_control"]) [role="radiogroup"],[data-testid="stButtonGroup"]:has(button[data-variant="segmented_control"]) [role="group"]{flex-wrap:nowrap!important;gap:0!important;width:100%;}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"]{
 flex:1 1 0!important;min-width:0;min-height:48px;padding:0 12px!important;font:600 16px/1.3 var(--sans);border:2px solid var(--ink)!important;
 border-radius:0!important;margin:0!important;margin-inline-end:-2px!important;box-shadow:none!important;background:var(--paper)!important;color:var(--ink)!important;}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"]:first-child{border-start-start-radius:4px!important;border-end-start-radius:4px!important;}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"]:last-child{border-start-end-radius:4px!important;border-end-end-radius:4px!important;margin-inline-end:0!important;}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected="true"],
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected="true"]:hover{background:var(--ink)!important;color:var(--paper)!important;}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"]:not([data-selected="true"]):hover{background:var(--paper)!important;color:var(--ink)!important;}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"]:not([data-selected="true"]):active{background:var(--deep)!important;}
[data-testid="stButtonGroup"] button p{font-weight:600;white-space:nowrap;}
/* field chips (st.pills, multi-select): rectangular, one per field, pressed = chosen */
[data-testid="stButtonGroup"]:has(button[data-variant="pills"]) [role="group"],[data-testid="stButtonGroup"]:has(button[data-variant="pills"]) [role="radiogroup"]{flex-wrap:wrap;gap:8px!important;width:100%;}
[data-testid="stButtonGroup"] button[data-variant="pills"]{min-height:44px;padding:0 12px!important;font:600 15px/1.2 var(--sans);border-radius:4px!important;border:1px solid var(--rule)!important;
 background:var(--paper)!important;color:var(--ink)!important;margin:0!important;box-shadow:none!important;font-variant-numeric:tabular-nums;}
[data-testid="stButtonGroup"] button[data-variant="pills"][data-selected="true"],[data-testid="stButtonGroup"] button[data-variant="pills"][data-selected="true"]:hover{background:var(--ink)!important;color:var(--paper)!important;border-color:var(--ink)!important;}
[data-testid="stButtonGroup"] button[data-variant="pills"]:not([data-selected="true"]):hover{background:var(--deep)!important;color:var(--ink)!important;}
[data-testid="stButtonGroup"] button[data-variant="pills"] p{font-weight:600;white-space:nowrap;}
@media (max-width:400px){[data-testid="stButtonGroup"] button[data-variant="segmented_control"]{padding:0 8px!important;font-size:15px;}}

/* ---- expander ----------------------------------------------------------- */
[data-testid="stExpander"]{margin:0;}
[data-testid="stExpander"] details{border:0!important;border-bottom:1px solid var(--hair)!important;border-radius:0!important;box-shadow:none!important;background:transparent;}
[data-testid="stExpander"] summary{min-height:48px;padding:0 4px!important;background:transparent!important;color:var(--ink)!important;font:500 16px/1.3 var(--sans);}
[data-testid="stExpander"] summary p{font-weight:500;font-size:16px;}
[data-testid="stExpander"] summary svg{color:var(--rule);}
[data-testid="stExpander"] summary:hover{color:var(--ink)!important;}
[data-testid="stExpander"] details[open]{background:var(--deep);}
[data-testid="stExpanderDetails"]{padding:4px 12px 12px!important;background:var(--deep);}
[data-testid="stExpanderDetails"] p,[data-testid="stExpanderDetails"] li{font-size:15.5px;line-height:1.45;}

/* ---- the invisible viewport reporter (viewport/index.html): out of the flow --- */
[data-testid="stElementContainer"]:has(iframe[title$="hassad_viewport"]){position:absolute;height:0!important;min-height:0!important;width:0;overflow:hidden;margin:0!important;}
/* ---- map frame ---------------------------------------------------------- */
.st-key-map_frame [data-testid="stCustomComponentV1"],.st-key-map_frame iframe{border:1px solid var(--rule)!important;border-radius:3px!important;display:block;}

/* ---- hero: the one toned panel ------------------------------------------ */
.hero{background:var(--deep);border-inline-start:5px solid var(--gold);padding:12px 16px;margin:2px 0 0;color:var(--ink);}
.hero .lbl{font-family:var(--sans);font-size:12.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}
.hero .big{font-family:var(--serif);font-variation-settings:"opsz" 96;font-weight:600;font-size:46px;line-height:1.05;margin:2px 0 4px;}
.hero .sub{font-family:var(--sans);font-size:18px;font-variant-numeric:tabular-nums;}
.hero .trust{margin-top:8px;padding-top:8px;border-top:1px solid var(--hair);font-family:var(--sans);font-size:15.5px;line-height:1.45;}
.hero .trust b{font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap;}
.hero .trust .fire{color:var(--fire);}
.hero .arr{display:inline-block;direction:ltr;unicode-bidi:isolate;}
.hero bdi,table.order bdi,.focus bdi,.stat bdi{unicode-bidi:isolate;direction:ltr;display:inline-block;}
.hero .big bdi{display:inline;}
[data-testid="stMarkdownContainer"] .hint.next{font-weight:500;color:var(--ink);margin:2px 0 4px;}

/* ---- order ledger ------------------------------------------------------- */
[data-testid="stMarkdownContainer"] table.order{width:100%;border-collapse:collapse;border:0;margin:0 0 14px;font-size:18px;font-variant-numeric:tabular-nums;table-layout:fixed;}
[data-testid="stMarkdownContainer"] table.order td{padding:8px;border:0;border-bottom:1px solid var(--hair);text-align:start;font-family:var(--sans);font-size:18px;line-height:1.3;color:var(--ink);background:transparent;vertical-align:middle;}
[data-testid="stMarkdownContainer"] table.order td.d{width:36%;color:var(--muted);white-space:nowrap;}
[data-testid="stMarkdownContainer"] table.order td.ha{width:26%;color:var(--muted);font-size:15.5px;white-space:nowrap;text-align:end;}
[data-testid="stMarkdownContainer"] table.order tr.now td{font-weight:600;color:var(--ink);background:var(--deep);}
[data-testid="stMarkdownContainer"] table.order tr.now td:first-child{border-inline-start:5px solid var(--gold);}
[data-testid="stMarkdownContainer"] table.order tr.cut td{color:var(--muted);}
[data-testid="stMarkdownContainer"] table.order tr.cut td.d{color:var(--rule);font-weight:600;}

/* ---- focus / done ------------------------------------------------------- */
.focus{border:2px solid var(--rule);border-radius:4px;padding:10px 14px;margin:8px 0 4px;display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;}
.focus .name{font-family:var(--sans);font-size:22px;font-weight:600;color:var(--ink);}
.focus .state{font-family:var(--sans);color:var(--muted);font-size:16px;}
.done{background:var(--deep);border-inline-start:5px solid var(--ink);padding:16px;margin:8px 0 6px;font-family:var(--serif);font-weight:600;font-size:26px;line-height:1.2;text-align:center;color:var(--ink);}

/* ---- judges: stats, econ, captions, widgets ----------------------------- */
.stats{display:flex;flex-wrap:wrap;margin:0 0 12px;}
.stat{flex:1 1 0;min-width:96px;padding:0 12px;border-inline-start:1px solid var(--hair);}
.stat:first-child{padding-inline-start:0;border-inline-start:0;}
.stat .l{font:400 14px/20px var(--sans);color:var(--muted);}
.stat .v{font:600 28px/34px var(--sans);font-variant-numeric:tabular-nums;color:var(--ink);margin-top:4px;white-space:nowrap;}
.stat .v.fire{color:var(--fire);}
.stat .u{font:400 15px/20px var(--sans);color:var(--muted);margin-inline-start:4px;}
.econ{padding:10px 0;border-top:1px solid var(--hair);}
.econ:first-of-type{border-top:0;padding-top:0;}
.econ .t{font:600 17px/1.4 var(--sans);color:var(--ink);}
.econ .line{font:400 17px/1.4 var(--sans);color:var(--ink);}
.econ b{font-weight:600;font-variant-numeric:tabular-nums;}
.econ .note{font:400 14px/1.4 var(--sans);color:var(--muted);margin-top:4px;}
[data-testid="stCaptionContainer"] p,[data-testid="stCaptionContainer"]{font:400 14px/20px var(--sans);color:var(--muted)!important;}
[data-testid="stCaptionContainer"]{margin-bottom:0!important;}  /* same -1rem pull as the markdown block */
[data-testid="stWidgetLabel"] p{font:600 15px/22px var(--sans);color:var(--muted);}
[data-testid="stSliderThumbValue"]{font:600 15px/1 var(--sans)!important;color:var(--ink)!important;font-variant-numeric:tabular-nums;}
[data-testid="stSliderTickBar"]{font:400 14px/20px var(--sans);color:var(--muted);}
[data-testid="stSlider"]>div:not([data-testid="stWidgetLabel"]),[data-testid="stDataFrame"],[data-testid="stVegaLiteChart"],[data-testid="stElementToolbar"]{direction:ltr;}
[data-testid="stSelectbox"] [data-baseweb="select"]>div{background:var(--paper)!important;border-radius:4px!important;box-shadow:none!important;}
[data-testid="stDataFrame"]{border-radius:4px;}

/* ---- toast -------------------------------------------------------------- */
[data-testid="stToast"]{background:var(--deep)!important;border:1px solid var(--rule)!important;border-radius:4px!important;box-shadow:none!important;padding:12px 16px!important;color:var(--ink)!important;}
[data-testid="stToast"] svg{display:none;}
[data-testid="stToastText"] p,[data-testid="stToast"] [data-testid="stMarkdownContainer"] p{font:500 16px/22px var(--sans);color:var(--ink);margin:0;}

/* ---- footer: one muted line and the privacy link, on every screen --------- */
.st-key-footer{margin-top:32px;padding-top:12px;border-top:1px solid var(--hair);}
.st-key-footer [data-testid="stMarkdownContainer"] p.foot{font:400 13.5px/1.4 var(--sans);color:var(--muted);margin:0;}
.st-key-footer .stButton{display:flex;justify-content:flex-end;}
.st-key-footer .stButton button{min-height:36px!important;font-size:14px!important;}
@media (max-width:640px){
 .st-key-footer>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;align-items:center;}
 .st-key-footer [data-testid="stColumn"]{min-width:0!important;}
 .st-key-footer [data-testid="stColumn"]:first-child{flex:1 1 0!important;}
 .st-key-footer [data-testid="stColumn"]:last-child{flex:0 0 auto!important;width:auto!important;}
}
/* ---- About page --------------------------------------------------------- */
.st-key-about [data-testid="stMarkdownContainer"] h2,.st-key-about_en [data-testid="stMarkdownContainer"] h2{font-family:var(--serif);font-variation-settings:"opsz" 48;font-weight:600;font-size:24px;line-height:1.2;color:var(--ink);padding:0!important;margin:24px 0 8px!important;}
.st-key-about [data-testid="stMarkdownContainer"] h3,.st-key-about_en [data-testid="stMarkdownContainer"] h3{font-family:var(--sans);font-weight:600;font-size:19px;line-height:1.3;color:var(--ink);padding:0!important;margin:18px 0 4px!important;}
.st-key-about [data-testid="stMarkdownContainer"] p,.st-key-about [data-testid="stMarkdownContainer"] li{font-size:17px;line-height:1.5;}
.st-key-about_en [data-testid="stMarkdownContainer"] p,.st-key-about_en [data-testid="stMarkdownContainer"] li{font-size:16.5px;line-height:1.5;}
.st-key-about_en [data-testid="stMarkdownContainer"] em{font-style:normal;font-size:15px;color:var(--muted);}
.st-key-about [data-testid="stMarkdownContainer"] em{font-style:normal;font-size:15px;color:var(--muted);}  /* italic Arabic is not a thing */
.st-key-about [data-testid="stMarkdownContainer"] table,.st-key-about [data-testid="stTableStyledTable"],.st-key-about_en [data-testid="stMarkdownContainer"] table,.st-key-about_en [data-testid="stTableStyledTable"]{width:100%;border-collapse:collapse;border:0!important;margin:10px 0 20px;}
.st-key-about [data-testid="stMarkdownContainer"] th,.st-key-about [data-testid="stTableStyledTable"] th,.st-key-about_en [data-testid="stMarkdownContainer"] th,.st-key-about_en [data-testid="stTableStyledTable"] th{font:600 14px/20px var(--sans);color:var(--muted);text-align:start;padding:8px 12px 8px 0;border:0!important;border-bottom:1px solid var(--rule)!important;background:transparent!important;}
.st-key-about [data-testid="stMarkdownContainer"] td,.st-key-about [data-testid="stTableStyledTable"] td,.st-key-about_en [data-testid="stMarkdownContainer"] td,.st-key-about_en [data-testid="stTableStyledTable"] td{font:400 15.5px/1.4 var(--sans);font-variant-numeric:tabular-nums;color:var(--ink);padding:8px 12px 8px 0;border:0!important;border-bottom:1px solid var(--hair)!important;background:transparent!important;vertical-align:top;}
.st-key-about_en [data-testid="stMarkdownContainer"] td:not(:first-child){text-align:end;}
.st-key-about [data-testid="stTable"],.st-key-about_en [data-testid="stTable"]{border:0!important;}
.st-key-about [data-testid="stImageContainer"] img,.st-key-about_en [data-testid="stImageContainer"] img{border:1px solid var(--hair);border-radius:0;}
.st-key-about [data-testid="stImageCaption"],.st-key-about_en [data-testid="stImageCaption"]{text-align:start!important;font:400 14px/20px var(--sans);color:var(--muted)!important;padding:6px 0 0;margin-bottom:20px;}

/* ---- tablet: one wider column ------------------------------------------- */
@media (min-width:640px) and (max-width:959px){
 .block-container,[data-testid="stMainBlockContainer"]{max-width:680px!important;padding:16px 24px 96px!important;}
}

/* ---- laptop and tablet-landscape: two panes ------------------------------
   The phone DOM order is untouched; the main vertical block becomes a grid whose
   first column holds the map (sticky, viewport-tall) and whose second column holds
   everything else in reading order. The header and tagline span both columns.
   In Arabic the grid mirrors itself: map on the right, panel on the left.
   The About page (no map) is one wider column. Browsers without :has() keep the
   single column. */
@media (min-width:960px){
 .block-container,[data-testid="stMainBlockContainer"]{max-width:1200px!important;padding:16px 32px 96px!important;}
 .block-container:has(.st-key-about_en),[data-testid="stMainBlockContainer"]:has(.st-key-about_en){max-width:820px!important;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame){
  display:grid!important;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:0 40px!important;align-items:start;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>*{grid-column:2;min-width:0;margin-bottom:10px;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stElementContainer"]:has(style){display:none;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stLayoutWrapper"]:has(>.st-key-row_hdr){grid-column:1/-1;grid-row:1;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stElementContainer"]:has(p.tagline),
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stElementContainer"]:has(hr.hdr-rule){grid-column:1/-1;grid-row:2;margin-bottom:14px;}
 /* the wrapper fills the map's grid area; the map block sticks inside it, so it can
    never slide past the area into the Numbers or footer rows while scrolling */
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stLayoutWrapper"]:has(>.st-key-map_frame){
  grid-column:1;grid-row:3/span 80;align-self:stretch;margin-bottom:0;overflow:visible;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stLayoutWrapper"]>.st-key-map_frame{position:sticky;top:16px;flex:0 0 auto!important;height:auto!important;}
 /* judges' Numbers: the whole width, below both panes (the map's area ends above it) */
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stLayoutWrapper"]:has(>.st-key-numbers){grid-column:1/-1;grid-row:90;margin-top:16px;}
 [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]:has(.st-key-map_frame)>[data-testid="stLayoutWrapper"]:has(>.st-key-footer){grid-column:1/-1;grid-row:95;}
 .block-container:has(.st-key-about_en) .st-key-footer,.block-container:has(.st-key-about) .st-key-footer{max-width:none;}
 .st-key-numbers .econ,.st-key-numbers .stats,.st-key-numbers [data-testid="stMarkdownContainer"] .hint,.st-key-numbers [data-testid="stSlider"]{max-width:720px;}
 .st-key-numbers [data-testid="stButtonGroup"]{max-width:720px;}
 [data-testid="stMarkdownContainer"] h1.hassad{font-size:44px;}
 [data-testid="stMarkdownContainer"] h1.hassad.compact{font-size:30px;}
 .hero .big{font-size:52px;}
 [data-testid="stMarkdownContainer"] table.order td{font-size:19px;}
 [data-testid="stMarkdownContainer"] .step h2{font-size:26px;}
}
@media print{.stButton,.stLinkButton,.stDownloadButton,[data-testid="stButtonGroup"],.st-key-map_frame{display:none!important;}.block-container{max-width:none!important;padding:0!important;}}
"""

RTL_CSS = """
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMainBlockContainer"],[data-testid="stToast"],
[data-testid="stExpander"],[data-testid="stButtonGroup"],.block-container{direction:rtl;}
.block-container{text-align:start;}
.stApp *:not(bdi):not(.arr){letter-spacing:0!important;text-transform:none!important;}
.stApp,[data-testid="stMarkdownContainer"],[data-testid="stCaptionContainer"],
.stButton button,.stLinkButton a,.stDownloadButton button,[data-testid="stButtonGroup"] button,
[data-testid="stExpander"] summary,[data-testid="stWidgetLabel"],[data-testid="stToast"],[data-testid="stToastText"] p,
.hero .lbl,.hero .sub,.hero .trust,.focus .name,.focus .state,.econ,.stat,.over,
[data-testid="stMarkdownContainer"] .hint,[data-testid="stMarkdownContainer"] .note,[data-testid="stMarkdownContainer"] .count,
[data-testid="stMarkdownContainer"] table.order td,[data-testid="stMarkdownContainer"] p.tagline{font-family:var(--sans-ar)!important;}
.stApp{line-height:1.5;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{line-height:1.5;}
[data-testid="stMarkdownContainer"] h1.hassad{font-family:var(--serif-ar)!important;font-weight:700;font-size:42px;line-height:1.15;font-variation-settings:normal;padding-top:0!important;}
[data-testid="stMarkdownContainer"] h1.hassad.compact{font-size:32px;}
[data-testid="stMarkdownContainer"] h1.hassad .wm2{font-family:var(--serif)!important;font-weight:600;font-size:.62em;font-variation-settings:"opsz" 96;}
[data-testid="stMarkdownContainer"] .step h2,.done,.st-key-about [data-testid="stMarkdownContainer"] h2{font-family:var(--serif-ar)!important;font-weight:700;font-size:27px;line-height:1.3;font-variation-settings:normal;}
.done{font-size:28px;}
.hero .big{font-family:var(--serif-ar)!important;font-weight:700;font-size:48px;line-height:1.2;font-variation-settings:normal;}
.hero .big bdi{font-family:var(--sans-ar)!important;font-weight:700;font-size:.88em;}
.over,.hero .lbl{font-size:15px;}
[data-testid="stMarkdownContainer"] *,.hero *,.focus *,[data-testid="stMarkdownContainer"] table.order td{text-align:start;}
[data-testid="stMarkdownContainer"] table.order td.ha{text-align:end;}
[data-testid="stMarkdownContainer"] ol,[data-testid="stMarkdownContainer"] ul,[data-testid="stExpanderDetails"] ol{padding-inline-start:1.5rem;padding-left:0;}
[data-testid="stMarkdownContainer"] table th,[data-testid="stMarkdownContainer"] table td,[data-testid="stTable"] th,[data-testid="stTable"] td{text-align:start;}
[data-testid="stSlider"] [data-testid="stWidgetLabel"]{direction:rtl;text-align:right;width:100%;}
[data-testid="stToast"],[data-testid="stToast"] *{text-align:right;}
[data-testid="stExpander"] summary{direction:rtl;text-align:right;}
[data-testid="stButtonGroup"] button p{font-size:15.5px;}
[class*="st-key-small"] .stButton button{font-size:15px;}
.st-key-about_en,.st-key-judge_en{direction:ltr;text-align:left;}
.st-key-about [data-testid="stMarkdownContainer"] h2{font-family:var(--serif-ar)!important;font-weight:700;font-size:26px;line-height:1.3;}
.st-key-about_en *,.st-key-judge_en *{text-align:left;}
.st-key-about_en [data-testid="stMarkdownContainer"] ol,.st-key-about_en [data-testid="stMarkdownContainer"] ul{padding-inline-start:1.5rem;}
.st-key-about_en [data-testid="stMarkdownContainer"] td:not(:first-child){text-align:end;}
/* the judge island is LTR for the chart, grid and CSV; its Arabic caption and button label read right-to-left */
.st-key-judge_en [data-testid="stCaptionContainer"],.st-key-judge_en [data-testid="stCaptionContainer"] *,
.st-key-judge_en .stDownloadButton,.st-key-judge_en .stDownloadButton *{direction:rtl;text-align:right;}
@media (min-width:960px){[data-testid="stMarkdownContainer"] h1.hassad{font-size:48px;}[data-testid="stMarkdownContainer"] h1.hassad.compact{font-size:34px;}.hero .big{font-size:54px;}}
"""

# The printable calendar (a standalone HTML file the farmer downloads): the
# same paper, ink and type as the app, tuned for an A4 sheet on a noticeboard.
CALENDAR_CSS = f"""
 body{{font-family:'IBM Plex Sans','IBM Plex Sans Arabic','Segoe UI',Tahoma,sans-serif;
      background:{PAPER};color:{INK};margin:16mm 14mm}}
 h1{{font-family:Fraunces,Amiri,Georgia,serif;font-weight:600;font-size:30px;margin:0 0 4px}}
 .sub{{color:{MUTED};margin:0 0 14px;font-size:15px}}
 table{{border-collapse:collapse;width:100%;font-size:15px}}
 th{{text-align:start;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:{MUTED};
     border-bottom:2px solid {INK};padding:6px}}
 td{{padding:9px 6px;border-bottom:1px solid {RULE};vertical-align:top}}
 td.d{{font-weight:600;white-space:nowrap;color:{MUTED}}}
 td.f{{font-family:Fraunces,Amiri,Georgia,serif;font-weight:600;font-size:22px;color:{INK}}}
 td.why{{color:{MUTED}}}
 tr:first-child td{{background:{DEEP}}}
 [dir=rtl] th{{letter-spacing:0;text-transform:none}}  /* tracking pulls joined Arabic letters apart */
 @media print{{body{{margin:12mm;background:#fff}}}}
"""

# Inside the folium iframe: attribution, draw toolbar, zoom bar.
MAP_HEAD = ("<style>@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@600&display=swap');"
            ".leaflet-control-attribution{font:11px 'IBM Plex Sans',Arial,sans-serif;background:rgba(34,25,15,.55);"
            f"color:{PAPER};padding:2px 5px}}.leaflet-control-attribution a,.leaflet-attribution-flag{{display:none!important}}"
            f".leaflet-draw-toolbar a,.leaflet-bar a{{width:44px;height:44px;line-height:44px;border:1px solid {RULE};"
            f"border-radius:4px;background-color:{PAPER};color:{INK}}}"
            "</style>")


def inject(rtl):
    """Emit the base block, then the Arabic block when the app is in Arabic."""
    st.markdown("<style>" + BASE_CSS + "</style>", unsafe_allow_html=True)
    if rtl:
        st.markdown("<style>" + RTL_CSS + "</style>", unsafe_allow_html=True)
