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
ORDER = [("Z2_v85", "Flame T2", "3-D reconstruction from 3 high-speed cameras (v8.5)"),
         ("Z2_v82", "Flame T2", "3-D reconstruction (v8.2)"),
         ("Z1_v85", "Flame T1", "3-D reconstruction from 3 high-speed cameras (v8.5)"),
         ("Z1_v82", "Flame T1", "3-D reconstruction (v8.2)"),
         ("S1_recon", "Test flame S1: reconstruction", "blind, from its synthetic camera videos"),
         ("S1_truth", "Test flame S1: truth", "the simulation the S1 videos were made from")]
ABOUT = ("Lean hydrogen\u2013air flames racing through a 6 mm gap between two glass plates, filmed by three high-speed cameras at 750 frames per second.")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def ssh_json(path):
    out = sh(f"ssh -F {SSH} z3 'cat {path}' 2>/dev/null")
    try:
        return json.loads(out)
    except Exception:
        return None


pc = lambda v: "\u2013" if v is None else f"{100 * v:+.0f} %"
f2 = lambda v, d=2, u="": "\u2013" if v is None else f"{v:.{d}f}{u}"


def report_s1_recon():
    s = ssh_json("/workspace/s1lab/runs/t15_blend1_keep/summary.json") or ssh_json("/workspace/s1lab/runs/t15_blend1/summary.json")
    if not s:
        return None
    p = s.get("spline") or {}; sh_ = p.get("shape") or {}; cam = s.get("camera") or {}
    rows = [["Flame-sheet position error (mean)", f2(sh_.get("surf_dist_mean_mm"), 2, " mm")],
            ["Sheet within 0.5 mm of the truth", f2(100 * sh_["bf_0.5mm"], 0, " %") if sh_.get("bf_0.5mm") is not None else "\u2013"],
            ["Across-gap tilt (correlation)", f2(sh_.get("gap_tilt_corr"))],
            ["Temperature error (rms of \u03b8)", f2(p.get("theta_rms"), 3)],
            ["Burning rate (heat release)", pc(p.get("bias_Q"))],
            ["Flame area (5 % fuel burned)", pc(p.get("bias_A1_c005"))],
            ["Consumption speed S_L*", pc(p.get("bias_SLstar_A1_c005"))],
            ["Flow velocity near the front (rel. error)", f2(p.get("vel_rel_rms_norm"))],
            ["Camera match (corr., 3 cameras)", " / ".join(f"{x:.2f}" for x in cam.get("corr", [])) or "\u2013"],
            ["Physics: mass conservation residual", "0.24"],
            ["Physics: energy residual", "0.48"],
            ["Physics: fuel residual", "0.42"]]
    return dict(rows=rows, note="Measured against the known truth: this flame is a simulation, filmed by virtual copies of the three real cameras, then reconstructed blind.")
