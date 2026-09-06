"""
Every string the app shows, in English and Arabic.

Rules for editing (Team C): keep sentences short, verbs on buttons, numbers
as separate tokens ({n}, {ha}) so the same line works right-to-left. Arabic
is Modern Standard with plain, everyday words -- the kind a farmer reads on a
sign or a WhatsApp message, not a legal form. Western digits in both
languages.
"""

STRINGS = {
    "en": {
        "lang_name": "English",
        "about": "About Hassad",
        "back_plan": "Back to the plan",
        "title": "Hassad",
        "tagline": "Cut your fields in the safest order.",
        "mode_demo": "Bekaa demo fields",
        "mode_draw": "Draw my own fields",
        "fields_title": "Tap your fields",
        "draw_title": "Draw your fields",
        "draw_hint": "Use the pencil tool on the map to outline each field, then press “Make my plan”.",
        "drawn_none": "No fields drawn yet.",
        "n_fields": "{n} fields",
        "all": "All",
        "none": "None",
        "make_plan": "Make my plan",
        "pick_first": "Tap 1 field first",
        "cut_now": "Cut now",
        "field": "Field {n}",
        "size": "{ha} ha · {d} {days}",
        "day": "day",
        "days": "days",
        "trust": "Fire block now {before} ha, after {after} ha",
        "is_cut": "Field {n} is cut",
        "next": "Next: Field {n}",
        "undo": "Undo",
        "tap_hint": "Tap a field to change it.",
        "state_cut": "cut",
        "state_standing": "standing",
        "mark_cut": "Mark cut",
        "not_cut": "Not cut",
        "cancel": "Cancel",
        "whole_order": "Whole order",
        "day_range": "Day {d}",
        "days_range": "Days {d}",
        "cut_label": "cut",
        "day_line": "Day {d} · Field {n}",
        "send_wa": "Send on WhatsApp",
        "print": "Print",
        "my_fields": "My fields",
        "all_cut": "All fields cut",
        "new_season": "New season",
        "numbers": "Numbers",
        "updated": "Plan updated",
        "econ_title": "Value at stake",
        "econ_line": "{ha} ha of wheat ≈ ${usd} this season",
        "econ_cost": "Hassad's cost to the farmer: $0",
        "econ_note": "Estimate: {y} t/ha × ${p}/t — assumptions until sourced.",
        "econ_event_title": "If a fire reaches your fields on a random day",
        "econ_event_line": "Burnable block: {plan} ha with this plan, instead of {naive} ha the usual way",
        "econ_event_saving": "{ha} ha (≈ ${usd}) less crop exposed per fire",
        "econ_chance": "Chance a fire reaches these fields this season",
        "econ_expected": "Expected saving this season: ≈ ${usd}",
        "econ_expected_note": "= chance × value no longer exposed. Nobody has measured the ignition chance yet, so the slider keeps that assumption visible.",
        "custom_refresh_note": "Drawn fields live only on this screen — send or print the plan before closing.",
        # Numbers section (judges)
        "m_exposure": "Fire exposure vs “largest field first”",
        "m_season": "Season",
        "m_driving": "Driving",
        "unit_days": "days",
        "s_hassad": "Hassad (optimal)",
        "s_naive": "largest field first",
        "s_greedy": "greedy",
        "chart_caption": "Cumulative fire exposure in hectare-days (largest connected block of standing wheat, summed daily). Lower is safer.",
        "col_day": "Day",
        "col_field": "Field",
        "col_ha": "Hectares",
        "col_block_after": "Largest block left (ha)",
        "col_why": "Why this field now",
        "csv": "Schedule (CSV)",
        "model_switches": "Model switches — judges only; the farmer never sees these",
        "gap_rule": "Gap rule",
        "gap_dry": "Dry year 175 m",
        "gap_wet": "Wet year 100 m",
        "objective": "Objective",
        "obj_fire": "Fire only",
        "obj_driving": "Fire + driving",
        "machine_at": "Machine is at",
        "footer": "Exact optimum over every possible order of {n} fields (gap rule {m} m; {mode}). Solver verified against brute-force enumeration; gap conditions measured from Sentinel-2 imagery. Hassad · FIRST Global Challenge 2026 · Team Lebanon.",
        "fire_only": "fire only",
        "fire_driving": "fire + driving",
        # --- added to complete the redesign (was missing)
        "about_title": "About Hassad",
        "try_it": "Try it",
        "try_plan": "Open the plan",
        "try_draw": "Draw my own fields",
        "try_judge": "Judges' view",
        "guide_title": "How to draw a field",
        "what_title": "What does this mean?",
        "step1": "Step 1",
        "demo_note": "11 real wheat fields near Jdita, traced from satellite imagery and checked to about 5 m² — a complete plan in one tap.",
        "demo_more": "What are these fields?",
        "draw_first": "Draw 1 field first",
        "cut_help": "Tap any field on the map to mark it cut, or put it back.",
        "ha": "ha",
        "unit_km": "km",
        "m_exposure_v": "−{pct}%",
        "draw_guide": "How to draw a field",
        "criteria_short": "How Hassad decides",
    },
    "ar": {
        "lang_name": "العربية",
        "about": "عن «حصاد»",
        "back_plan": "العودة إلى الخطة",
        "title": "حصاد",
        "tagline": "احصد حقولك بالترتيب الأكثر أماناً.",
        "mode_demo": "حقول جاهزة من البقاع",
        "mode_draw": "ارسم حقولي",
        "fields_title": "اختر حقولك على الخريطة",
        "draw_title": "ارسم حقولك",
        "draw_hint": "ارسم حدود كل حقل بأداة المضلّع على الخريطة، ثم اضغط «جهّز خطتي».",
        "drawn_none": "لم ترسم أي حقل بعد.",
        "n_fields": "عدد الحقول: {n}",
        "all": "الكل",
        "none": "إلغاء الكل",
        "make_plan": "جهّز خطتي",
        "pick_first": "اختر حقلاً واحداً على الأقل.",
        "cut_now": "احصد الآن",
        "field": "حقل {n}",
        "size": "{ha} هكتار · {d} {days}",
        "day": "يوم",
        "days": "أيام",
        "trust": "أكبر كتلة قابلة للاحتراق: {before} هكتار الآن، وتصبح {after} هكتار بعد حصاده",
        "is_cut": "حصدتُ حقل {n}",
        "next": "بعده: حقل {n}",
        "undo": "تراجع",
        "tap_hint": "اضغط على أي حقل لتعديل حالته.",
        "state_cut": "محصود",
        "state_standing": "لم يُحصد بعد",
        "mark_cut": "حصدتُه",
        "not_cut": "لم أحصده بعد",
        "cancel": "إلغاء",
        "whole_order": "الترتيب الكامل",
        "day_range": "اليوم {d}",
        "days_range": "الأيام {d}",
        "cut_label": "محصود",
        "day_line": "اليوم {d} · حقل {n}",
        "send_wa": "أرسل على واتساب",
        "print": "اطبع الخطة",
        "my_fields": "حقولي",
        "all_cut": "تم حصاد كل الحقول",
        "new_season": "موسم جديد",
        "numbers": "الأرقام",
        "updated": "تم تحديث الخطة",
        "econ_title": "القيمة المعرّضة للخطر",
        "econ_line": "{ha} هكتار قمح ≈ {usd} دولار هذا الموسم",
        "econ_cost": "كلفة «حصاد» على المزارع: 0 دولار",
        "econ_note": "تقدير: {y} طن/هكتار × {p} دولار/طن — أرقام مبدئية حتى توثيقها.",
        "econ_event_title": "إذا وصلت النار إلى حقولك في يوم عشوائي",
        "econ_event_line": "الكتلة القابلة للاحتراق: {plan} هكتار بهذه الخطة، بدل {naive} هكتار بالطريقة المعتادة",
        "econ_event_saving": "في كل حريق: {ha} هكتار أقل من المحصول المعرّض للنار (≈ {usd} دولار)",
        "econ_chance": "احتمال وصول حريق إلى هذه الحقول هذا الموسم",
        "econ_expected": "التوفير المتوقع هذا الموسم: ≈ {usd} دولار",
        "econ_expected_note": "= الاحتمال × قيمة المحصول الذي لم يعد معرّضاً للنار. لم يقس أحد احتمال الاشتعال بعد، لذلك نُبقي هذا الافتراض ظاهراً في الشريط أعلاه بدل إخفائه.",
        "custom_refresh_note": "الحقول المرسومة تبقى على هذه الشاشة فقط — أرسل الخطة أو اطبعها قبل الإغلاق.",
        # Numbers section (judges)
        "m_exposure": "التعرّض للحريق مقارنةً بـ«الحقل الأكبر أولاً»",
        "m_season": "الموسم",
        "m_driving": "المسافة",
        "unit_days": "يوم",
        "s_hassad": "حصاد (الأمثل)",
        "s_naive": "الحقل الأكبر أولاً",
        "s_greedy": "الجشع",
        "chart_caption": "التعرّض التراكمي للحريق بالهكتار·يوم (أكبر كتلة متصلة من القمح القائم، مجموعةً يومياً). الأقل أكثر أماناً.",
        "col_day": "اليوم",
        "col_field": "الحقل",
        "col_ha": "هكتار",
        "col_block_after": "أكبر كتلة متبقية (هكتار)",
        "col_why": "لماذا هذا الحقل الآن",
        "csv": "الجدول (CSV)",
        "model_switches": "إعدادات النموذج — للحكام فقط؛ لا يراها المزارع",
        "gap_rule": "قاعدة الفجوات",
        "gap_dry": "سنة جافة 175 م",
        "gap_wet": "سنة رطبة 100 م",
        "objective": "الهدف",
        "obj_fire": "النار فقط",
        "obj_driving": "النار + القيادة",
        "machine_at": "الحصّادة عند",
        "footer": "الترتيب الأمثل بالضبط من بين كل الترتيبات الممكنة لـ{n} حقول (قاعدة الفجوات {m} م؛ {mode}). تم التحقق من الحل بالمقارنة مع التعداد الكامل؛ حالة الفجوات مقيسة من صور سنتينل-2. حصاد · FIRST Global Challenge 2026 · فريق لبنان.",
        "fire_only": "النار فقط",
        "fire_driving": "النار + القيادة",
        # --- added to complete the redesign (was missing)
        "about_title": "عن «حصاد»",
        "try_it": "جرّب بنفسك",
        "try_plan": "افتح الخطة",
        "try_draw": "ارسم حقولي",
        "try_judge": "عرض لجنة التحكيم",
        "guide_title": "كيف أرسم حقلاً",
        "what_title": "ماذا يعني هذا؟",
        "step1": "الخطوة 1",
        "demo_note": "11 حقل قمح حقيقي قرب جديتا، رُسمت من صور الأقمار الصناعية ودُقّقت إلى نحو 5 م² — خطة كاملة بضغطة واحدة.",
        "demo_more": "ما هذه الحقول؟",
        "draw_first": "ارسم حقلاً واحداً أولاً",
        "cut_help": "اضغط أي حقل على الخريطة لتحدّده محصوداً أو تعيده كما كان.",
        "ha": "هكتار",
        "unit_km": "كم",
        "m_exposure_v": "−{pct}٪",
        "draw_guide": "كيف أرسم حقلاً",
        "criteria_short": "كيف يقرّر «حصاد»",
    },
}

LANGS = ["en", "ar"]

# The tracing name of one field leaked from the data file; farmers see a number.
FIELD_LABELS = {"nte": "3"}


def label(name):
    """Display name for a field id (the data keeps 'nte'; the screen shows '3')."""
    return FIELD_LABELS.get(str(name), str(name))


def days_word(n, lang):
    """"1 day" / "3 days" -- Arabic uses the dual/plural a farmer would say."""
    s = STRINGS[lang]
    try:
        n = int(n)
    except (TypeError, ValueError):
        return f'{n} {s["days"]}'
    if lang == "ar":
        if n == 1:
            return "يوم واحد"
        if n == 2:
            return "يومان"
        if 3 <= n <= 10:
            return f"{n} أيام"
        return f"{n} يوماً"
    return f'{n} {s["day"] if n == 1 else s["days"]}'


# ---------------------------------------------------------------------------
# LONGER CONTENT -- the explanations that live inside expanders.
# Written as small HTML blocks because app.py renders them with
# st.markdown(..., unsafe_allow_html=True) inside st.expander.
# ---------------------------------------------------------------------------

CONTENT = {
    # "How to draw a field" -- the expander above the drawing map.
    "draw_guide": {
        "en": """<ol>
<li>Zoom the map to your farm. Pinch on a phone; use + and − on a laptop.</li>
<li>Tap the polygon tool — the shape icon at the top-left corner of the map.</li>
<li>Tap each corner of the field, going around its edge. Tap the first corner again to close the shape. For a rectangular field the square tool is quicker.</li>
<li>Made a mistake? The edit tool moves corners; the bin deletes a shape.</li>
<li>One shape per field. A field split by a road or a canal is two fields.</li>
<li>Press "Make my plan".</li>
</ol>
<p>Good to know:</p>
<ul>
<li>Fields are numbered 1, 2, 3 in the order you draw them. That number is what the plan, the WhatsApp message and the printed calendar use.</li>
<li>Very small shapes — under 0.05 ha, about 20 by 25 metres — are treated as a mis-tap and ignored.</li>
<li>Your drawings live only in this session. Close the page and they are gone, so send the plan on WhatsApp or print it before you leave. The Bekaa demo fields can be shared by link; drawn fields cannot.</li>
</ul>""",
        "ar": """<ol>
<li>كبّر الخريطة حتى تصل إلى أرضك. بإصبعين على الهاتف، أو بزرّي + و− على الحاسوب.</li>
<li>اضغط أداة الرسم — رمز المضلّع في أعلى الخريطة على اليمين.</li>
<li>اضغط على زوايا الحقل واحدة تلو الأخرى وأنت تدور حول حدوده، ثم اضغط على الزاوية الأولى مرة ثانية لإغلاق الشكل. للحقل المستطيل تكفي أداة المربّع.</li>
<li>أخطأت؟ أداة التعديل تحرّك الزوايا، وأداة الحذف تمسح الشكل كلّه.</li>
<li>شكل واحد لكل حقل. الحقل الذي يقطعه طريق أو قناة هو حقلان.</li>
<li>اضغط «جهّز خطتي».</li>
</ol>
<p>مهم أن تعرف:</p>
<ul>
<li>تُرقَّم الحقول 1، 2، 3 بترتيب رسمها، وبهذا الرقم تظهر في الخطة وفي رسالة واتساب وفي التقويم المطبوع.</li>
<li>الأشكال الصغيرة جداً — أقل من 0.05 هكتار، أي نحو 20 × 25 متراً — تُعدّ ضغطة خطأ وتُهمَل.</li>
<li>ما ترسمه يبقى في هذه الجلسة فقط. إذا أغلقت الصفحة ضاع، فأرسل الخطة عبر واتساب أو اطبعها قبل أن تخرج. الحقول الجاهزة من البقاع يمكن مشاركتها برابط، أما الحقول المرسومة فلا.</li>
</ul>""",
    },
    # "What does this mean?" -- the expander under the Cut-now card.
    "criteria_short": {
        "en": """<p><b>Dry standing wheat is fuel.</b> A cut field is short stubble — fire finds nothing to burn there, so it works as a firebreak.</p>
<p><b>Fields close together are connected.</b> If the gap between two fields is narrow enough for fire to cross, Hassad treats them as one block: fire that starts in one can reach the other.</p>
<p><b>Every day, Hassad measures the largest block.</b> For each day of the harvest it looks at the fields still standing and finds the largest connected block — the most wheat one fire could burn in one go. The aim is to keep that block as small as possible, every day, until the last field is cut.</p>
<p><b>It checks every possible order.</b> For 11 fields that is almost 40 million orders. Hassad tries them all and picks the one that keeps the blocks smallest across the whole season. This is not a guess or a rule of thumb: it is the best order there is, found in a fraction of a second. It assumes one harvester cutting about 8 hectares a day, so a bigger field simply takes more days.</p>
<p><b>What the line under "Cut now" means.</b> "Fire block now 76 ha, after 71 ha" says: today, the biggest connected stretch of standing wheat is 76 hectares. Once you cut this field, the biggest stretch left is 71 hectares. That is what you gain by cutting this field first.</p>
<p><b>When you mark a field cut.</b> Hassad treats it as a firebreak from now on — whichever field it is, whatever order you actually cut in — and works out the best order for the fields that remain, starting from where the harvester is. Undo puts it back.</p>
<p><b>The two gap rules.</b> How wide a gap fire can jump depends on what grows in it. In a dry year the grass and scrub between fields is dead by June and carries fire, so Hassad counts fields up to 175 m apart as connected. In a wet year those gaps stay green and stop fire, so only fields within 100 m count. Satellite pictures of these same fields showed both cases in the last three summers. Hassad uses the dry-year rule unless told otherwise, because a plan that is safe when the gaps burn is safe either way — and the reverse is not true.</p>""",
        "ar": """<p><b>القمح القائم الجاف وقود.</b> أما الحقل المحصود فقشّ قصير لا تجد النار فيه ما تأكله، فيصبح حاجزاً يوقفها.</p>
<p><b>الحقول المتقاربة متصلة.</b> إذا كانت الفجوة بين حقلين ضيقة بما يكفي لتعبرها النار، عدّهما «حصاد» كتلة واحدة: فالنار التي تبدأ في أحدهما تصل إلى الآخر.</p>
<p><b>كل يوم، يقيس «حصاد» أكبر كتلة.</b> في كل يوم من أيام الحصاد ينظر إلى الحقول التي ما زالت قائمة ويجد أكبر كتلة متصلة منها، أي أكبر مساحة قمح يمكن أن يحرقها حريق واحد دفعة واحدة. الهدف أن تبقى هذه الكتلة أصغر ما يمكن، كل يوم، حتى يُحصد آخر حقل.</p>
<p><b>يجرّب كل ترتيب ممكن.</b> لأحد عشر حقلاً يقارب ذلك 40 مليون ترتيب. يجرّبها «حصاد» كلها ويختار الترتيب الذي تبقى فيه الكتل أصغر على مدار الموسم كله. ليس هذا تخميناً ولا قاعدة تقريبية، بل أفضل ترتيب موجود، يجده التطبيق في أقل من ثانية. ويفترض حصّادة واحدة تقطع نحو 8 هكتارات في اليوم، فالحقل الأكبر يأخذ أياماً أكثر لا غير.</p>
<p><b>ماذا يعني السطر تحت «احصد الآن»؟</b> «أكبر كتلة قابلة للاحتراق: 76 هكتار الآن، وتصبح 71 هكتار بعد حصاده» يعني: اليوم، أكبر مساحة متصلة من القمح القائم هي 76 هكتاراً. وبعد أن تحصد هذا الحقل، تصبح أكبر مساحة متبقية 71 هكتاراً. هذا ما تكسبه بحصاد هذا الحقل أولاً.</p>
<p><b>عندما تحدّد حقلاً على أنه محصود.</b> يعامله «حصاد» من الآن فصاعداً كحاجز للنار — أيّ حقل كان، وبأيّ ترتيب حصدته فعلاً — ثم يحسب أفضل ترتيب للحقول الباقية انطلاقاً من مكان الحصّادة. وزر «تراجع» يعيد الأمر كما كان.</p>
<p><b>قاعدتا الفجوة.</b> المسافة التي تقفزها النار تتوقّف على ما ينمو بين الحقول. في السنة الجافة يكون العشب والشجيرات بين الحقول قد يبس بحلول حزيران وينقل النار، لذا يعدّ «حصاد» الحقول التي تفصلها مسافة تصل إلى 175 متراً متصلة. وفي السنة الرطبة تبقى تلك الفجوات خضراء وتوقف النار، فلا تُعدّ متصلة إلا الحقول التي تفصلها مسافة 100 متر أو أقل. وقد أظهرت صور الأقمار الصناعية لهذه الحقول نفسها الحالتين في المواسم الصيفية الثلاثة الأخيرة. يعتمد «حصاد» قاعدة السنة الجافة ما لم يُطلب غير ذلك، لأن الخطة الآمنة حين تشتعل الفجوات آمنة في الحالتين، والعكس غير صحيح.</p>""",
    },
}
