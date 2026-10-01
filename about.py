"""
The "About Hassad" page: everything a judge, a mentor, a farmer or a
journalist could ask, in one place -- including the questions our MIT mentor
actually asked, with our answers.

Rendered by app.py when the URL has ?page=about or the About link is pressed:
render_ar_summary() inside st.container(key="about") when the app is in Arabic,
then render_en() inside st.container(key="about_en"), which the skin keeps
left-to-right on the Arabic page. Text is English (the audience is the
competition). Dollar signs are written as &#36; because Streamlit's markdown
treats $...$ as maths.
"""

import os

import streamlit as st

from app_logic import CROP_NOTES, WHEAT_YIELD_T_PER_HA, WHEAT_PRICE_USD_PER_T

FIG = {
    "map": "map_adjacency.png",
    "gaps": "satellite_gaps.png",
    "fields": "satellite_fields.png",
    "firms": "firms_bekaa.png",
    "frame": "frame_day05.png",
    "sens": "sensitivity_thresholds.png",
}


def _img(key, n, caption):
    path = FIG[key]
    if os.path.exists(path):
        st.image(path, caption=f"Figure {n} — {caption}", width="stretch")


def render_ar_summary():
    """The Arabic summary above the English body (shown when the app is in Arabic)."""
    st.markdown("""
<div class="ar-summary" lang="ar" dir="rtl">
<h3>ما هو «حصاد»؟</h3>
<p>«حصاد» يقول لمزارعي القمح في البقاع بأي ترتيب يحصدون حقولهم المتجاورة، حتى تبقى
كتل القمح الجاف المتصلة التي قد تصلها النار أصغر ما يمكن: الحقل المحصود يصير حاجزاً
للنار. يجد البرنامج أفضل ترتيب بين أكثر من 39 مليون ترتيب لأحد عشر حقلاً، في أجزاء من
الثانية ومن دون أن يجرّبها واحداً واحداً. وقسنا الفجوات بين الحقول في صور الأقمار
الصناعية المجانية لثلاثة أشهر حزيران سابقة. لا جهاز ولا رسوم. بقية هذه الصفحة
بالإنجليزية للجنة التحكيم.</p>
</div>
""", unsafe_allow_html=True)
    st.divider()


def render(lang="en"):
    """Both parts in one call (the name older scripts import)."""
    if lang == "ar":
        render_ar_summary()
    render_en()


def render_en():
    """The English body. The page title is drawn by app.py above the Try-it buttons."""
    st.markdown("""
**Hassad tells a wheat cooperative the order in which to harvest neighbouring
fields so that the connected blocks of standing dry wheat a fire could reach
stay as small as possible on every day of the season.** A harvested field is
stubble with little left to burn — a firebreak. The order of the harvest
decides how big the largest block of fuel is on every day, and that order can
be chosen. Hassad finds the best one for our model, exactly, in milliseconds.
No device, no fee.

<p><em>FIRST Global Challenge 2026 "Igniting Innovation" · Team Lebanon · Prevent
category · Phase 3 finalist.</em></p>

## How it works, in four steps

1. **Fields.** Eleven real wheat fields (141 ha) near Jdita in the Bekaa
   Valley, traced from satellite imagery — or any farm a farmer draws on the
   map.
2. **Fire graph.** Two fields are "connected" if fire can cross the gap
   between them. Our satellite check found that this changes year to year
   (see *Evidence*), so the app carries both cases.
3. **Season simulation.** One harvester, 8 ha/day. Each day we measure the
   largest connected block of still-standing wheat. Summed over the season,
   that is the *fire exposure* score.
4. **The best order.** A dynamic program searches every possible harvest
   order (39,916,800 for 11 fields) exactly, and re-plans from any state when
   real life diverges from the plan.

## The numbers

If every gap between the fields can carry fire (the 175 m rule):

| | fire exposure (ha·days) | vs. "largest field first" |
| --- | --- | --- |
| Largest field first (our comparison) | 1093 | — |
| Greedy (our Phase 1) | 854 | −22% |
| **Exact optimum (Phase 2)** | **730** | **−33%** |

If the gaps stay green (the 100 m rule), the best order for that case gives
6% less. The order above would then be 10% worse than largest field first,
which is why the app carries both rules and says which one it is using. A
compromise order our model found gains 5.5% under both rules, but not under
every mix of dry and green gaps, so we never call any order guaranteed.

**Per fire event** (if every gap can carry fire): on a random day of the
season a fire would find a 46 ha burnable block with largest field first
versus 30 ha under the plan — **15 ha
(about &#36;13,000 of crop) less exposed per fire**, at an assumed
{y} t/ha × &#36;{p}/t. Expected saving per season = that × the chance of a fire,
which nobody has measured; the app's *Numbers* section has a slider for it.

## Evidence

""".format(y=WHEAT_YIELD_T_PER_HA, p=f"{WHEAT_PRICE_USD_PER_T:.0f}"), unsafe_allow_html=True)

    _img("map", 1, "The study area and the fire-adjacency graph (fields within 175 m are connected).")
    st.markdown("""
**The gaps change from year to year.** We measured every contested gap
between fields in Sentinel-2 imagery in three Junes. In June 2025 the gap
between field 3 and field 4 had low greenness (NDVI 0.17), dry enough to carry
fire, and four other gaps were borderline. In June 2024 the gaps around
field 3 were green, but the gap between field 9 and field 10 read as dry;
June 2026 was unclear. So the app carries both gap rules. We measured these
three past Junes by hand; checking the gaps automatically before each harvest
is a next step.
""")
    _img("gaps", 2, "NDVI of the seven contested gaps at harvest time, three summers.")
    st.markdown("""
**The harvest is visible from space.** The same imagery caught the June 2026
harvest: on fields 4–7 the greenness fell from 0.55–0.67 on 8 June to
0.22–0.24 on 3 July, while fields 3 and 9 stayed green (0.77–0.91), an
irrigated summer crop that year that acted as a firebreak. Fields rotate; the app treats which fields are fuel as a
yearly input.
""")
    _img("fields", 3, "What each field was doing, June by June, from Sentinel-2.")
    st.markdown("""
**Fires are common in the harvest months.** NASA's FIRMS archive holds 1,821
thermal-anomaly detections in the Bekaa since 2012, 550 of them within 10 km
of our fields; June–July carry 1.7× their calendar share. August to October
are high too, so the record alone does not single out the harvest. (Detections are
thermal anomalies, a lower bound: they include deliberate stubble burns and
miss fires under ~0.1 ha.)
""")
    _img("firms", 4, "NASA fire detections (thermal anomalies) in the Bekaa since 2012: when and where.")
    st.markdown("""
**What the fire service told us.** A Civil Defence chief in the Bekaa told
the team (26 July 2026) that most fires ignite just before harvest, when
machinery blades strike hidden rocks in tinder-dry wheat, and that fire trucks
cannot reach remote farmland in time. That is why Hassad works before a fire
starts.
""")
    _img("frame", 5, "Day 5 of the season: largest-field-first (left), greedy (middle), exact optimum (right).")

    st.markdown("""
## Questions our MIT mentor asked — and our answers

**Have real farmers tested it?** Not yet — a usability session with a Bekaa
farmer is planned, with a written 20-minute script (five tasks
in Arabic, three questions). The app was tested on a real Android phone on
2 September 2026: tapping fields, planning, re-planning, WhatsApp sharing and
surviving a refresh all work.

**Is it cost-efficient — do farmers actually benefit?** No device and no fee:
a different order for work they already do, with some extra driving (about
3.7 km over the season). The benefit is computed by our model, not yet
measured in a real harvest: 33% less fire exposure if every gap between the
fields can carry fire, 6% if the gaps stay green, and about 15 ha (~&#36;13,000
at assumed prices) less crop exposed per fire event on our 141 ha study area. The section
*Cost and benefit, in numbers* below sets it out line by line.

**Why not focus on Arabic?** We did, on his advice: the whole app runs in
Arabic with one tap — every screen, the generated reasons, the WhatsApp
message and the printable calendar, right-to-left. A native-speaker
naturalness pass is the remaining step.

**Can farmers choose their own fields?** Yes — tap to pick among the
pre-traced fields, or draw any farm with the pencil tool and get a plan for
fields Hassad has never seen.

**Does it work for other crops?** Any crop that is fuel while standing dry
and whose harvest removes that fuel:
""", unsafe_allow_html=True)
    st.table({"crop": list(CROP_NOTES), "in the model": list(CROP_NOTES.values())})
    st.markdown("""
Our own imagery proved the barrier case: irrigated fields are firebreaks, not
fuel. In a mixed farm, simply don't select the green fields.

**How much have you saved?** Nothing yet — no one has harvested with Hassad.
What we can state exactly is how much less crop a fire would find on a random
day (the table above). Money saved per season needs an ignition probability;
we show that as an explicit slider rather than bury it in a headline.

## Cost and benefit, in numbers

Every figure below is computed by the app from the 11 study fields (141 ha,
24-day season, the 175 m rule — every gap can carry fire — unless stated) and appears in the Numbers
section under every plan. Yield and price are assumptions until Team A
sources Bekaa figures.

| | value |
| --- | --- |
| For the farmer | No device, no fee; the same harvest in a different order, with about 3.7 km more driving over the season |
| Cost to run the service | hosting on Streamlit Community Cloud (free tier); Sentinel-2 and NASA FIRMS data (free); tracing a village's fields once (hours, not money); no hardware |
| Crop value at stake | ≈ &#36;123,500 per season (3.5 t/ha × &#36;250/t = &#36;875/ha, assumed) |
| Largest block a fire finds on a random day, largest field first | 46 ha |
| … with Hassad's order | 30 ha |
| Less crop exposed per fire event | 15.1 ha ≈ &#36;13,200, about &#36;94 of crop per hectare in the plan |
| Season fire exposure, every gap can carry fire (ha·days) | 1093 largest field first → 854 greedy → 730 Hassad (−33%) |
| Season fire exposure, gaps stay green | 589 → 553 with the best order for that case (−6%) |
| Compromise order, under both rules (not under every mix of gaps) | −5.5% |
| Expected saving per season = chance of a fire × &#36;13,200 | 5%: ≈ &#36;660 · 10%: ≈ &#36;1,300 · 25%: ≈ &#36;3,300 · 50%: ≈ &#36;6,600 |
| Driving over the season | 19.5 km largest field first → 23.2 km fire-only order (+3.7 km); the fire + driving setting: 21.9 km at −33.0% |
| Time | a plan in under a second; re-planning after a cut, one tap |

**Why the benefit is larger than it looks.** The farmer needs no device and
pays no fee, and the software does not cost more as the number of farms grows,
so every hectare planned adds about &#36;94
of crop protected per fire event; a cooperative of 1,000 ha is the same
software and the same free data. Three things would make the figure firmer or
bigger, in this order:

1. **Measure the ignition chance.** The expected-saving line is the only one
   that depends on an assumption. NASA's FIRMS record for the Bekaa (13 years,
   550 detections within 10 km of the fields) is enough to estimate how often a
   fire reaches a given block of fields in June, which turns the slider into a
   number.
2. **Use the fire + driving setting by default** once the balanced order is
   validated with the cooperative: it recovers most of the extra driving
   (23.2 → 21.9 km) at almost no fire cost (−33.2% → −33.0%).
3. **Check the gaps by satellite before each harvest.** The gain is 33% if
   every gap can carry fire and 6% if the gaps stay green. We measured three
   past Junes by hand; making the check automatic, before the harvest starts,
   is a next step. Until then the app says which rule it uses, and the larger
   figure is always given with its condition.

## Questions judges ask

**How do you know the order is optimal?** The fire objective decomposes over
sets of completed fields, so a subset dynamic program (Held-Karp) finds the
exact minimum for our model, without trying the orders one by one. A check
runs every time the code does: all 5,040 orders of a smaller 7-field problem,
scored by an independent day-by-day simulator, match the solver's answer to
the last decimal.

**What if the farmer doesn't follow the plan?** Mark any field as cut — in
any order, for any reason — and the remaining season is re-solved from the
machine's position in milliseconds. Cut fields become firebreaks in the graph.

**Why not sensors or drones?** They detect fires after ignition; Hassad
shrinks what a fire could reach before it starts, with no device and no fee.
The two work together: sensors find the spark, Hassad shrinks what it can
burn.

**Does it scale?** Any cooperative anywhere: free satellite data plus field
boundaries (traced or drawn) is all it needs. Scaling is distribution, not
manufacturing. The exact solver handles up to 20 fields at a time (16 with
the fire + driving setting); a method for larger villages is future work.

**What are the limits?** One harvester per plan; a field counts as fuel until
fully cut (conservative); fire spreads only between adjacent standing fields —
no wind direction or ignition probability yet; the two gap rules come from
three summers of imagery at one site; the economics use assumed yield and
price until sourced. All of this is stated in the code and the README.

## The team, the plan after Incheon

FIRST Global Team Lebanon. Next steps: a farmer usability test (planned);
meetings with Civil Defence (interviewed in July 2026), LARI Tal Amara and
Bekaa cooperatives; a pilot harvest with one cooperative in May–July 2027
with GPS logging on the combine and before/after satellite checks; then the
Bekaa and Akkar plains. Free for farmers; who covers the running costs is
still to be agreed.
""", unsafe_allow_html=True)
    _img("sens", 6, "How the benefit depends on how far fire can jump (made with our Phase 1 method): large when every gap can carry fire, small when the gaps stay green.")
