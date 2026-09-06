"""
The privacy page (?page=privacy): who runs Hassad, what the app does and does
not collect, which outside services are involved, how to reach us. Plain
language in English and Arabic. Rendered by app.py inside
st.container(key="about") (Arabic, right-to-left) or st.container(key="about_en").

Keep this page honest: the app has no accounts, stores nothing on our side,
and the only data that leaves the phone goes to the hosting, map-tile and
font providers named below.
"""

import streamlit as st

OWNER = "RoboGeex Academy"
SITE = "robogeex.com"
UPDATED = "6 September 2026"
UPDATED_AR = "6 أيلول 2026"        # the Levantine month name

EN = f"""
<p><em>Last updated {UPDATED}</em></p>

## Who runs Hassad

Hassad is built by FIRST Global Team Lebanon at **{OWNER}**, Lebanon, as an
entry to the FIRST Global Challenge 2026. {OWNER} is responsible for this
website and for how it handles your data. Website: {SITE}.

## What we collect

**Nothing that identifies you.** Hassad has no accounts, asks for no name,
phone number or e-mail, and never asks your phone for its location.

- **Fields you tap or draw** are processed in the app's memory for your
  session only. They are not saved on our side. Close the page and they are
  gone.
- **The WhatsApp message and the printed calendar** are created in your
  browser. Sending the message is done by WhatsApp on your phone; we never
  see it.
- **The share link** for the demo fields (the address of the page after you
  make a plan) contains only field numbers, nothing about you.

## Services this site relies on

When the page loads, these providers receive the technical details any web
request carries (your IP address, browser type, time of the request), under
their own privacy policies:

- **Hosting:** Streamlit Community Cloud (Snowflake Inc.) serves the app and
  keeps standard server logs to operate the service.
- **Map imagery:** Esri World Imagery tiles are loaded from Esri's servers
  as you move the map.
- **Fonts:** Fraunces, Amiri and IBM Plex are loaded from Google Fonts.

We do not add analytics, advertising or tracking of any kind.

## Cookies

The hosting platform sets the technical cookies it needs to keep your
session alive while the page is open. We set no cookies of our own.

## Your choices

There is nothing to delete on our side, because nothing is kept. If you
prefer not to send the demo share link to anyone, simply do not copy the
address. Questions about this page or the project: {OWNER}, {SITE}.

## Changes

If this page changes, the date at the top changes with it.

<p><em>© 2026 {OWNER}. Hassad — FIRST Global Team Lebanon.</em></p>
"""

AR = f"""
<div lang="ar" dir="rtl">
<p><em>آخر تحديث: {UPDATED_AR}</em></p>

<h2>من يقف وراء «حصاد»</h2>
<p>«حصاد» من تطوير فريق لبنان في FIRST Global داخل <b>أكاديمية {OWNER}</b> في لبنان،
مشاركةً في تحدي FIRST Global لعام 2026. أكاديمية {OWNER} هي الجهة المسؤولة عن هذا
الموقع وعن طريقة تعامله مع بياناتك. الموقع: {SITE}.</p>

<h2>ما الذي نجمعه</h2>
<p><b>لا شيء يدلّ عليك.</b> لا حسابات في «حصاد»، ولا يطلب اسماً ولا رقم هاتف ولا
بريداً إلكترونياً، ولا يطلب من هاتفك تحديد موقعك أبداً.</p>
<ul>
<li><b>الحقول التي تضغط عليها أو ترسمها</b> تُعالَج في ذاكرة التطبيق خلال جلستك فقط،
ولا تُحفظ عندنا. أغلق الصفحة تختفِ.</li>
<li><b>رسالة واتساب والتقويم المطبوع</b> يُنشآن في متصفحك. إرسال الرسالة يتم عبر
واتساب على هاتفك، ولا نراها نحن أبداً.</li>
<li><b>رابط المشاركة</b> للحقول الجاهزة (عنوان الصفحة بعد تجهيز الخطة) لا يحمل سوى
أرقام الحقول، ولا شيء عنك.</li>
</ul>

<h2>الخدمات التي يعتمد عليها الموقع</h2>
<p>عند فتح الصفحة تصل إلى هذه الجهات التفاصيل التقنية التي يحملها أي طلب على
الإنترنت (عنوان IP، نوع المتصفح، وقت الطلب)، وفق سياسات الخصوصية الخاصة بها:</p>
<ul>
<li><b>الاستضافة:</b> Streamlit Community Cloud (شركة Snowflake) تشغّل التطبيق وتحتفظ
بسجلات الخادم المعتادة لتشغيل الخدمة.</li>
<li><b>صور الخريطة:</b> بلاطات Esri World Imagery تُحمَّل من خوادم Esri كلما حرّكت الخريطة.</li>
<li><b>الخطوط:</b> خطوط Fraunces وAmiri وIBM Plex تُحمَّل من Google Fonts.</li>
</ul>
<p>لا نضيف أي أدوات تحليل أو إعلانات أو تتبّع من أي نوع.</p>

<h2>ملفات تعريف الارتباط (الكوكيز)</h2>
<p>تضع منصة الاستضافة ملفات التعريف التقنية التي تحتاجها لإبقاء جلستك فعّالة ما دامت
الصفحة مفتوحة. ولا نضع نحن أي ملفات من عندنا.</p>

<h2>خياراتك</h2>
<p>لا يوجد ما يُحذف عندنا، لأننا لا نحتفظ بشيء. وإن كنت لا تريد إرسال رابط المشاركة
لأحد، فلا تنسخ العنوان. للأسئلة عن هذه الصفحة أو عن المشروع: أكاديمية {OWNER}،
{SITE}.</p>

<h2>التغييرات</h2>
<p>إذا تغيّرت هذه الصفحة، يتغيّر معها التاريخ في أعلاها.</p>

<p><em>© 2026 {OWNER}. حصاد — فريق لبنان في FIRST Global.</em></p>
</div>
"""


def render(lang="en"):
    st.markdown(AR if lang == "ar" else EN, unsafe_allow_html=True)
