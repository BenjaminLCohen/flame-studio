# Flame Studio Mobile: the public phone viewer

A full-screen, app-style 3-D flame viewer for phones (works on desktop too). It opens straight into the best flame playing in cinematic slow motion. The only visible control is a gear icon.

## What a visitor sees
- **Black screen, the flame, nothing else.** Playback cycles **temperature → fuel concentration → reaction rate → …**, one full slow-motion pass each (10 s), with smooth streamline particles riding the true flow.
- **Look around:** tilt the phone, or drag with one finger. Pinch to zoom; double-tap to reset.
- **Tap to pause.** A card shows *how good the reconstruction is*:
  - S1: errors against the known truth;
  - Z1 / Z2: camera match and physics residuals.
  - The particles keep flowing along the frozen field while paused.
- **Gear → settings sheet** covering at most half the screen (a side panel in landscape), so the flame stays visible. Dropdowns:
  - flame; field (auto cycle or one field); playback speed; streamlines; motion (tilt / drag / auto-orbit); gap depth scale; quality (auto / 4K / battery); pause card; captions.
  - Settings are remembered on the device.
- **Install:** "Add to Home Screen" (iOS Safari / Android Chrome) installs it as a full-screen app (`manifest.webmanifest`).
- **Shareable links:** `?flame=Z2_v85&field=2&t=0.5&paused=1` (field 0 temperature, 1 fuel, 2 reaction rate, 3 camera light; `t` = 0–1 through the clip).

## Folder layout (deploy this whole folder)
| Path | Contents |
|---|---|
| `index.html` | the whole app (WebGL2 ray-marcher + particles + UI), no external libraries |
| `manifest.webmanifest`, `icon-*.png` | home-screen app |
| `vercel.json` | headers: data files cached forever, served as binary |
| `data/flames.json` | catalogue (order = what plays first), the About text, optional `base` URL for the data |
| `data/<flame>/meta.json` | shapes, times, scales |
| `data/<flame>/s<k>.bin.gz` | 144 states × (temperature, fuel, reaction rate, light) at 0.25 mm × 24 layers |
| `data/<flame>/u<k>.bin.gz` | velocity for the streamlines |
| `data/<flame>/report.json` | the pause card |
| `build_site.py` | rebuilds `data/` from the pod (not needed by visitors; Vercel can ignore it) |

**Included flames:** only the best views of Z2 and Z1 (v8.5, or v8.2 if v8.5 is missing), S1 reconstruction and S1 truth. Each is ~100 MB. The app streams it, keeps it compressed in memory and decodes only a few states at a time, so phones stay smooth.

## Deploy with Vercel
1. **Build the data (on the Mac, with the pod running):** `python3 build_site.py`.
   - It pulls the packs and writes `data/flames.json` plus the reports.
   - Delete `data/_test` before deploying.
2. **Deploy, either way:**
   - **Vercel CLI:** `npm i -g vercel`, then in this folder: `vercel` (first time: link a new project), then `vercel --prod`.
   - **Git:** push the folder to a GitHub repo, then on vercel.com → *Add New Project* → import the repo. Framework: **Other**. Build command: none. Output directory: `.`.
3. **If Vercel rejects the size** (plan limits on deployment size or file count):
   - Upload `data/` to a bucket: Cloudflare R2, Google Cloud Storage or Vercel Blob, all with public read and CORS `GET` allowed for your Vercel domain.
   - Set `"base": "https://<bucket-url>/data/"` in `data/flames.json` (keep `flames.json` itself on Vercel).
   - Only `index.html`, the manifest, icons and `flames.json` stay on Vercel.
4. **Test locally:** `python3 -m http.server 8790` in this folder, then open `http://<your-mac-ip>:8790` on the phone (same wifi).
   - Tilt control needs **https** on iOS, so test tilt on the Vercel URL.

## Updating
- **New reconstruction:** export a pack on the pod with `z8mobile.py`:
  `python3 z8mobile.py --ckpt <ckpt.pt> --obs <obs.pt> --chem <chem.json> --out /workspace/mobile/<id> --n 144`
  (for Z1, prefix with the Z1 environment, as in `/root/mobile_export.sh`).
  Then add the id to `ORDER` in `build_site.py`, re-run it, and redeploy.
- **What plays first:** the first available id in `ORDER`.

## How the flames were made (for the explainer video)
See `Write_Up/Manim_Handoff/README.md`: storyboard, narration, and every chart's data, including the server bill.
