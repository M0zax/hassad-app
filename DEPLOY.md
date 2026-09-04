# Putting Hassad online (free, ~15 minutes)

The code is already on GitHub, **private**, in the team's organisation:

    https://github.com/RoboGeex-Academy/hassad   (branch `main`)

Streamlit Community Cloud hosts Streamlit apps for free straight from GitHub,
private repositories included. The app's URL will be public even though the
code stays private. What remains needs your GitHub login in a browser, so
only you can do it.

## 1. Deploy (one time)

1. Go to https://share.streamlit.io and **sign in with GitHub** (the M0zax
   account).
2. When Streamlit asks for GitHub access, it must be granted for the
   **RoboGeex-Academy organisation**, not just your personal account — in the
   authorisation screen, click **Grant** next to RoboGeex-Academy (an org
   owner may have to approve the "Streamlit" app under the org's *Settings →
   Third-party access* if it does not appear).
3. **New app** → repository `RoboGeex-Academy/hassad`, branch `main`, main
   file `app.py`. Choose the app URL (e.g. `hassad`).
4. Advanced settings → Python version **3.12** (3.13 also works if offered).
5. **Deploy.** The first build takes 3–5 minutes; the app then lives at
   `https://hassad.streamlit.app` (or whatever name you chose) and opens on
   any phone.

## 3. Check it

- `https://<your-app>.streamlit.app` — the farmer screen
- `…/?lang=ar` — Arabic · `…/?mode=draw` — draw your own fields
- `…/?judge=1` — finished plan with the Numbers section open
- `…/?page=about` — the About / questions-and-answers page

## Updating later

Every `git push` to `main` redeploys automatically within a minute.

```bash
git add -A
```
```bash
git commit -m "describe the change"
```
```bash
git push
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
