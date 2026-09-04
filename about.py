"""
The "About Hassad" page: everything a judge, a mentor, a farmer or a
journalist could ask, in one place -- including the questions our MIT mentor
actually asked, with our answers.

Rendered inside app.py when the URL has ?page=about or the About button is
pressed. Text is English (the audience is the competition); a short Arabic
summary sits at the top when the app is in Arabic.
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
    "gif": "harvest_comparison.gif",
    "sens": "sensitivity_thresholds.png",
}


def _img(key, caption):
    path = FIG[key]
    if os.path.exists(path):
        st.image(path, caption=caption, use_container_width=True)


def render(lang="en"):
    if lang == "ar":
        st.markdown("""
### ما هو «حصاد»؟
«حصاد» يخبر مزارعي القمح في سهل البقاع بأي ترتيب يحصدون حقولهم المتجاورة، بحيث لا تجد
النار أبداً كتلة كبيرة متصلة من القمح الجاف لتحرقها. الحقل المحصود يصبح حاجزاً للنار.
البرنامج يحسب الترتيب الأمثل رياضياً من بين كل الاحتمالات (أكثر من 39 مليون ترتيب
لأحد عشر حقلاً) في أجزاء من الثانية، ويقرأ حالة الحقول والفجوات بينها من صور الأقمار
الصناعية المجانية كل موسم. لا يحتاج أي أجهزة، وكلفته على المزارع صفر. الصفحة التالية
بالإنجليزية تشرح كل التفاصيل والأسئلة الشائعة.
""")
        st.divider()

    st.markdown("""
# About Hassad حصاد

**Hassad tells a wheat cooperative the order in which to harvest neighbouring
fields so that a fire can never find a large connected block of standing dry
wheat.** A harvested field is stubble — a firebreak. The order of the harvest
decides how big the largest block of fuel is on every day of the season, and
that order can be chosen. Hassad chooses the provably best one, in
milliseconds, at zero cost to the farmer.

*FIRST Global Challenge 2026 "Igniting Innovation" · Team Lebanon · Prevent
category · Phase 2 semifinalist.*

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

| | fire exposure (ha·days) | vs. "largest field first" |
| --- | --- | --- |
| Largest field first (what farmers do) | 1093 | — |
| Greedy (our Phase 1) | 854 | −22% |
| **Exact optimum (Phase 2)** | **730** | **−33%** |

Under the wet-year rule (gaps green, fields separated) the gain is 6%. A
*robust* order that never hurts under either rule gives a guaranteed 5.5%.

**Per fire event:** on a random day of the season a fire would find a 46 ha
burnable block under the usual order versus 30 ha under the plan — **15 ha
(about &#36;13,000 of crop) less exposed per fire**, at an assumed
{y} t/ha × &#36;{p}/t. Expected saving per season = that × the chance of a fire,
which nobody has measured; the app's *Numbers* section has a slider for it.

## Evidence

""".format(y=WHEAT_YIELD_T_PER_HA, p=f"{WHEAT_PRICE_USD_PER_T:.0f}"))

    _img("map", "The study area and the fire-adjacency graph (red = fields within 175 m).")
    st.markdown("""
**The gaps are seasonal.** We measured every contested gap between fields in
Sentinel-2 imagery across three harvest seasons. In June 2025 the gap between
field *nte* and field 4 was cured dry vegetation (NDVI 0.17 — a fuel bridge);
in 2024 and 2026 the same gaps stayed green (barriers). So Hassad does not
assume a fuel map: it reads each year's real one from orbit.
""")
    _img("gaps", "NDVI of the seven contested gaps at harvest time, three summers.")
    st.markdown("""
**The harvest is visible from space.** The same imagery caught the June 2026
harvest as an NDVI collapse (0.6 → 0.25 in 17 days) on fields 4–7 and 10–12 —
while two of our "wheat" fields carried an irrigated summer crop that year and
acted as firebreaks. Fields rotate; the app treats which fields are fuel as a
yearly input.
""")
    _img("fields", "What each field was doing, June by June, from Sentinel-2.")
    st.markdown("""
**Fires happen when wheat is standing.** NASA's FIRMS archive holds 1,821
thermal-anomaly detections in the Bekaa since 2012, 550 of them within 10 km
of our fields; June–July carry 1.7× their calendar share. (Detections are
thermal anomalies, a lower bound: they include deliberate stubble burns and
miss fires under ~0.1 ha.)
""")
    _img("firms", "Thirteen years of NASA fire detections in the Bekaa: when and where.")
    st.markdown("""
**The fire service agrees.** The Chief of Civil Defence in Jdita told the team
(26 July 2026) that most fires ignite just before harvest, when machinery
blades strike hidden rocks in tinder-dry wheat, and that fire trucks cannot
reach remote farmland in time — so firebreaks between fields are the
defence that works.
""")
    _img("frame", "Day 5 of the season: largest-field-first (left), greedy (middle), exact optimum (right).")

    st.markdown("""
## Questions our MIT mentor asked — and our answers

**Have real farmers tested it?** Not yet — a usability session with a Bekaa
cooperative manager is scheduled, with a written 20-minute script (five tasks
in Arabic, three questions). The app was tested on a real Android phone on
2 September 2026: tapping fields, planning, re-planning, WhatsApp sharing and
surviving a refresh all work.

**Is it cost-efficient — do farmers actually benefit?** The farmer's cost is
&#36;0: no sensors, no subscription, a different order for work they already do.
The benefit is measured, not promised: 5.5% less fire exposure guaranteed
under any assumption, up to 33% in cured-gap years, and about 15 ha (~&#36;13,000)
less crop exposed per fire event on our 141 ha study area.

**Why not focus on Arabic?** We did, on his advice: the whole app runs in
Arabic with one tap — every screen, the generated reasons, the WhatsApp
message and the printable calendar, right-to-left. A native-speaker
naturalness pass is the remaining step.

**Can farmers choose their own fields?** Yes — tap to pick among the
pre-traced fields, or draw any farm with the pencil tool and get a plan for
fields Hassad has never seen.

**Does it work for other crops?** Any crop that is fuel while standing dry
and whose harvest removes that fuel:
""")
    st.table({"crop": list(CROP_NOTES), "in the model": list(CROP_NOTES.values())})
    st.markdown("""
Our own imagery proved the barrier case: irrigated fields are firebreaks, not
fuel. In a mixed farm, simply don't select the green fields.

**How much have you saved?** Nothing yet — no one has harvested with Hassad.
What we can state exactly is how much less crop a fire would find on a random
day (the table above). Money saved per season needs an ignition probability;
we show that as an explicit slider rather than bury it in a headline.

## Questions judges ask

**How do you know the order is optimal?** The fire objective decomposes over
sets of completed fields, so a subset dynamic program (Held-Karp) finds the
exact minimum. We verified it by brute force: all 5,040 orders of a 7-field
sub-problem, scored by an independent day-by-day simulator, match the
solver's answer to the last decimal. The check runs every time the code does.

**What if the farmer doesn't follow the plan?** Mark any field as cut — in
any order, for any reason — and the remaining season is re-solved from the
machine's position in milliseconds. Cut fields become firebreaks in the graph.

**Why not sensors or drones like other teams?** They detect fires after
ignition; Hassad prevents large ones before it, and costs nothing per hectare.
The two are complementary: their sensors find the spark, our order makes sure
it finds nothing big to burn.

**Does it scale?** Any cooperative anywhere: free satellite data plus field
boundaries (traced or drawn) is all it needs. Scaling is distribution, not
manufacturing. The exact solver handles up to ~20 fields; larger villages use
a heuristic calibrated against it.

**What are the limits?** One harvester per plan; a field counts as fuel until
fully cut (conservative); fire spreads only between adjacent standing fields —
no wind direction or ignition probability yet; the two gap rules come from
three summers of imagery at one site; the economics use assumed yield and
price until sourced. All of this is stated in the code and the README.

## The team, the plan after Incheon

FIRST Global Team Lebanon. After the competition: a farmer usability test
(September), partnerships with Civil Defence (active), LARI Tal Amara and
Bekaa cooperatives (in progress), a pilot harvest with one cooperative in
May–July 2027 with GPS logging on the combine and before/after satellite
verification, then scaling across the Bekaa and Akkar plains. Free for
farmers; institutional partners carry operating costs.

## Try it

- **Plan** — the main page: tap fields, or draw your own, and press *Make my plan*.
- `?lang=ar` opens in Arabic · `?mode=draw` opens in drawing mode · `?judge=1`
  opens on a finished plan with the *Numbers* section expanded.
""")
    _img("sens", "Why we hedge: the benefit depends on the gap rule, so a robust order stays positive in every world.")
