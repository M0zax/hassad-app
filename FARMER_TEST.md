# Hassad — farmer test kit

One session with one real farmer or cooperative manager, 20 minutes, on
**their** phone. Write down what happens, honestly. Even one session,
reported truthfully, is worth more to judges than any feature.

## Before the visit

1. **Give them a link they can open.** Two ways:
   - *Same-room:* run `streamlit run app.py` on the laptop, turn on the
     laptop's hotspot (or join the same Wi-Fi), and give them
     `http://<laptop-IP>:8501` (find the IP with `ipconfig`). Works today.
   - *Anywhere:* free hosting on Streamlit Community Cloud — push the folder
     to a GitHub repository, sign in at share.streamlit.io, "New app", pick
     the repo and `app.py`. `requirements.txt` is already in the folder. You
     get a public URL that works from any phone, forever.
2. Open the app once yourself on the phone you'll use, so the map tiles are
   cached and nothing loads slowly in front of them.
3. Bring the printed calendar (the "Print" button) as a prop.

## The five tasks (say them in Arabic; switch the app to عربي first)

Do not explain the app. Say the task, then watch. Note every hesitation.

| # | Say to the farmer | What you watch for |
| --- | --- | --- |
| 1 | "هذه حقول قرية في البقاع. اختر ثلاثة حقول كأنها حقولك." (Pick three fields as if they were yours.) | Do they understand tapping the map? Do they tap the number badge or the field? |
| 2 | "اطلب الخطة." (Ask for the plan.) | Do they find the one big button without help? |
| 3 | "ما الذي يجب أن تحصده اليوم، ولماذا؟" (What should you cut today, and why?) | Do they read the field number and the "fire block" line? Does the reason make sense to them — ask them to say it back in their own words. |
| 4 | "لنفترض أنك حصدت حقلاً آخر اليوم بدل هذا. عدّل الخطة." (Suppose you cut a different field today. Fix the plan.) | Do they discover tapping a field → "Mark cut"? How long does it take? |
| 5 | "أرسل الخطة إلى مجموعة الواتساب." (Send the plan to the WhatsApp group.) | Does the WhatsApp button do what they expect? |

## The three questions afterwards

1. "لو كانت هذه حقولك فعلاً، هل كنت ستتبع هذا الترتيب؟ لماذا / لماذا لا؟"
   *(If these were really your fields, would you follow this order? Why / why not?)* — this is the honest verdict on the whole idea.
2. "ما الذي كان مربكاً أو غير واضح؟" *(What was confusing or unclear?)*
3. "كيف تقرر ترتيب الحصاد اليوم؟" *(How do you decide the harvest order today?)* — their current method is the baseline we compare against.

## Write it up (half a page)

Name/role (with permission), date, phone model, which tasks succeeded
without help, time to complete task 4, their exact words for question 1,
and the top two confusions. Send it to Team B the same day — it goes into
the Impact answer as *"tested with a Bekaa farmer on [date]"*.

## Also worth asking, if there's time

- How many fields does their cooperative harvest, and with how many machines?
- Do they know of a field that burned in the last five years? (A case study
  for Phase 3.)
- Would the cooperative let us follow one harvest next June with a GPS
  logger on the combine? (The 2027 pilot.)
