# Putting Hassad online (free)

Two repositories, on purpose:

| repository | visibility | what it is |
| --- | --- | --- |
| `RoboGeex-Academy/hassad` | **private** | the team's working copy — everything, including strategy documents and submission drafts that stay private until after Incheon |
| `M0zax/hassad-app` | **public** | the curated copy Streamlit hosts — app, model, data, figures, public-facing docs only |

`python publish_public.py` copies the curated file list from this folder to
the public repository and pushes it. Run it after every change you want live;
the app redeploys within a minute.

## 1. Deploy (one time)

1. Go to https://share.streamlit.io and sign in with GitHub (M0zax).
2. **New app** → repository **`M0zax/hassad-app`**, branch **`main`**, main
   file **`app.py`**. App URL: `hassad-safeharvest` (or any free name).
3. Advanced settings → Python version **3.12**.
4. **Deploy.** The first build takes 3–5 minutes; the app then lives at
   `https://hassad-safeharvest.streamlit.app` and opens on any phone.

(Community Cloud can also host private repositories — one per account, and
only if the GitHub connection was authorised with full repository access —
which is why the public curated copy is the simpler, more reliable route.)

## 3. Check it

- `https://<your-app>.streamlit.app` — the farmer screen
- `…/?lang=ar` — Arabic · `…/?mode=draw` — draw your own fields
- `…/?judge=1` — finished plan with the Numbers section open
- `…/?page=about` — the About / questions-and-answers page

## Updating later

Work in this folder as usual and keep the private team repository current:

```bash
git add -A
```
```bash
git commit -m "describe the change"
```
```bash
git push origin main
```

Then publish the curated copy — the hosted app redeploys within a minute:

```bash
python publish_public.py "describe the change"
```

## Things to know

- **Free tier sleeps** after a few days without visitors; the first visitor
  wakes it (takes ~30 s). Open the URL yourself the morning of any demo.
- **Map tiles** come from Esri's public imagery service — no key needed.
- **No data leaves the app**: there is no database and no accounts; a
  farmer's drawn fields exist only in their browser session.
- The evidence scripts (`satellite.py`, `firms.py`) are not run on the server
  — their figures are committed as PNGs and shown on the About page.
- If a build fails on `matplotlib`/`shapely`, the fix is almost always
  selecting Python 3.12 in advanced settings and redeploying.
