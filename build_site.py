#!/usr/bin/env python3
"""Assemble the deployable phone site: pull the mobile cinema packs from the pod, write each flame's pause-card report and the catalogue.

usage (on the Mac):  python3 build_site.py            # pulls from the pod (ssh alias z3) into ./data and writes data/flames.json
                     python3 build_site.py --no-pull  # only rewrite the reports / catalogue
Packs are made on the pod by z8mobile.py (/root/mobile_export.sh -> /workspace/mobile/<id>).
"""
import argparse, json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
SSH = os.path.expanduser("~/Desktop/3D_Flames/Phantom_Demo_09022026/_pod/ssh_config")
# preferred order: best stuff first; the first available one is the default
ORDER = [("Z2_v85", "Flame Z2", "3-D reconstruction from 3 high-speed cameras (v8.5)"),
         ("Z2_v82", "Flame Z2", "3-D reconstruction (v8.2)"),
         ("Z1_v85", "Flame Z1", "3-D reconstruction from 3 high-speed cameras (v8.5)"),
         ("Z1_v82", "Flame Z1", "3-D reconstruction (v8.2)"),
         ("S1_recon", "Test flame S1: reconstruction", "blind, from its synthetic camera videos"),
         ("S1_truth", "Test flame S1: truth", "the simulation the S1 videos were made from")]
ABOUT = ("Lean hydrogen–air flames racing through a 6 mm gap between two glass plates, filmed by three high-speed cameras at 750 frames per second. "
         "Each 3-D flame is reconstructed with SPARC: a 3-D low-Mach combustion simulation steered to the cameras' arrival times "
         "(the across-gap tilt is chosen by the camera fit), projected onto a smooth spline model of every field. Test flame S1 has a known truth, "
         "which is how the method's accuracy was measured. Tap to pause and see how good each reconstruction is. "
         "Drag or tilt the phone to look around; double-tap to reset.")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def ssh_json(path):
    out = sh(f"ssh -F {SSH} z3 'cat {path}' 2>/dev/null")
    try:
        return json.loads(out)
    except Exception:
        return None


pc = lambda v: "–" if v is None else f"{100 * v:+.0f} %"
f2 = lambda v, d=2, u="": "–" if v is None else f"{v:.{d}f}{u}"


def report_s1_recon():
    s = ssh_json("/workspace/s1lab/runs/t15_blend1_keep/summary.json") or ssh_json("/workspace/s1lab/runs/t15_blend1/summary.json")
    if not s:
        return None
    p = s.get("spline") or {}; sh_ = p.get("shape") or {}; cam = s.get("camera") or {}
    rows = [["Flame-sheet position error (mean)", f2(sh_.get("surf_dist_mean_mm"), 2, " mm")],
            ["Sheet within 0.5 mm of the truth", f2(100 * sh_["bf_0.5mm"], 0, " %") if sh_.get("bf_0.5mm") is not None else "–"],
            ["Across-gap tilt (correlation)", f2(sh_.get("gap_tilt_corr"))],
            ["Temperature error (rms of θ)", f2(p.get("theta_rms"), 3)],
            ["Burning rate (heat release)", pc(p.get("bias_Q"))],
            ["Flame area (5 % fuel burned)", pc(p.get("bias_A1_c005"))],
            ["Consumption speed S_L*", pc(p.get("bias_SLstar_A1_c005"))],
            ["Flow velocity near the front (rel. error)", f2(p.get("vel_rel_rms_norm"))],
            ["Camera match (corr., 3 cameras)", " / ".join(f"{x:.2f}" for x in cam.get("corr", [])) or "–"]]
    return dict(rows=rows, note="Measured against the known truth: this flame is a simulation, filmed by virtual copies of the three real cameras, then reconstructed blind.")


def report_s1_truth():
    return dict(rows=[["What", "direct numerical simulation"], ["Fuel", "lean H₂–air, Lewis number 0.36"], ["Grid", "0.125 × 0.125 × 0.1 mm"],
                      ["Cell", "37 mm wide, 6 mm gap"], ["Used as", "ground truth for the method study"]],
                note="Its light was rendered through the three real camera models to make the synthetic videos that S1's reconstruction saw.")


def report_z(z):
    s = None
    for name in ("v85",):
        s = ssh_json(f"/workspace/zlab/runs/{z}_{name}/summary.json") or s
    rows = []
    if s:
        cam = s.get("camera") or {}; ph = s.get("physics_cell1") or {}; st = s.get("steer") or {}
        rows += [["Camera match (corr. Nova / mini / Standalone)", " / ".join(f"{x:.2f}" for x in cam.get("corr", []) if x == x) or "–"],
                 ["Camera residual χ²/px", " / ".join(f"{x:.0f}" for x in cam.get("chi2", []) if x == x) or "–"],
                 ["Physics: mass conservation residual", f2(ph.get("cont"))], ["Physics: energy residual", f2(ph.get("energy"))], ["Physics: fuel residual", f2(ph.get("fuel"))],
                 ["Front timing vs the videos (rms)", f2(st.get("lag_rms"), 2, " frames")],
                 ["Across-gap tilt (camera choice)", f"{s.get('steering', {}).get('split-tilt', '–')} frames"]]
    return dict(rows=rows, note="A real flame has no truth. On the test flame S1, the same method puts the flame sheet within ~0.4 mm of the truth. "
                                 "Residuals: 0 = equation exactly satisfied, 1 = off by its largest term (1 mm cells).")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--no-pull", action="store_true"); a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    if not a.no_pull:
        print(sh(f"rsync -a -e 'ssh -F {SSH}' z3:/workspace/mobile/ {DATA}/ --exclude export.log 2>&1 | tail -2"))
    flames = []
    for fid, title, sub in ORDER:
        d = os.path.join(DATA, fid)
        if not os.path.exists(os.path.join(d, "meta.json")):
            continue
        if any(f["title"] == title for f in flames):                                   # one version per flame: the best available
            continue
        rep = report_s1_recon() if fid == "S1_recon" else report_s1_truth() if fid == "S1_truth" else report_z(fid[:2])
        if rep:
            json.dump(rep, open(os.path.join(d, "report.json"), "w"), indent=1)
        flames.append(dict(id=fid, title=title, subtitle=sub))
    json.dump(dict(default=flames[0]["id"] if flames else None, flames=flames, about=ABOUT), open(os.path.join(DATA, "flames.json"), "w"), indent=1)
    tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(DATA) for f in fs)
    print("catalogue:", [f["id"] for f in flames], f"| data {tot / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
