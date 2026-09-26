# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""presentscale.py — PRESENT-SCALE-0: how much of the blit is the 2:1 destination scaling (off-gate, host).

    python verify/presentscale.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--per-cell 300] [--confirm]

FRAME-SPLIT-0 (confirmed) found the blit — StretchDIBits of the 1920x1080 composite into the half-size client area —
the largest phase of the shell's frame, without a seat. This diagnostic court varies ONE thing, the destination
geometry as a client-area size: half (960x540) against full (1920x1080, 1:1). Everything else is FRAME-SPLIT-0's
production path, unchanged, with its envelope and split recorded per geometry so a geometry that silently changed
the rest of the path is caught. Blocks H F F H H F F H, 5 warm-up rounds after every resize, the client rectangle read
back and required to equal the request. It is a diagnostic court: there is no seat and no winner, only attribution.

The preregistered reading, on p50s:
  * VOID if either geometry's |instrumentation tax| >= 100 permille of its envelope (as FRAME-SPLIT-0);
  * CONFOUNDED if the six non-blit phases (strips .. bgr, summed) moved by >= 50 permille of their half-size sum —
    the geometry changed more than the blit, and nothing is attributed to scaling;
  * otherwise the blit delta dB = blit(full) - blit(half): |dB| >= 100 permille of blit(half) reads SCALING MATERIAL
    (the sign says whether the full-size, unscaled destination was cheaper or dearer), else SCALING IMMATERIAL.
p99s, the envelopes and frame-ready -> composited are reported beside, never folded in. The logical and physical
screen sizes and the device context's stretch mode are recorded, never varied. Writes
shell/attest/presentscale-<host>.json citing PRESENT-SCALE-0. Not input-to-photon; never compared to an emit p99.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402

DEFAULT_SESSION = "workshop/attest/sessionwalk-demo.json"
PHASES = ("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit")
NON_BLIT = PHASES[:-1]
GEOMS = {"half": [960, 540], "full": [1920, 1080]}
PCT = ("p50", "p95", "p99", "max")
PROD_THREADS = 8
WARM_ROUNDS_PER_BLOCK = 5
BLOCK_ORDER = "HFFHHFFH"
VOID_TAX_PERMILLE = 100
CONFOUND_PERMILLE = 50
MATERIAL_PERMILLE = 100


class Refuse(Exception):
    pass


def registry() -> dict:
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        return json.load(fh)["entries"]


def _pct(x) -> bool:
    return isinstance(x, dict) and all(isinstance(x.get(k), int) for k in PCT)


def check_raw(raw: dict) -> dict:
    if raw.get("name") != "verdandi-presentscale":
        raise Refuse("not a verdandi-presentscale record")
    d = raw.get("data", {})
    if tuple(d.get("phases", ())) != PHASES or d.get("source") != [1920, 1080]:
        raise Refuse("the phases or the source size are not the registered ones")
    if (d.get("production_threads"), d.get("warm_rounds_per_block"), d.get("block_order"), d.get("phase_origin")) != \
            (PROD_THREADS, WARM_ROUNDS_PER_BLOCK, BLOCK_ORDER, "locked"):
        raise Refuse("production T, warm-up, block order or phase origin is not the registered one")
    n = d.get("samples_per_cell")
    if not isinstance(n, int) or n <= 0 or n % 4:
        raise Refuse("samples per cell is not a positive multiple of 4")
    for g, dest in GEOMS.items():
        gd = d.get("geometries", {}).get(g, {})
        if gd.get("destination") != dest or gd.get("client") != dest:
            raise Refuse(f"{g}: the client area is not the requested {dest[0]}x{dest[1]} — not the registered geometry")
        env, spl = gd.get("envelope", {}), gd.get("split", {})
        if env.get("samples") != n or spl.get("samples") != n:
            raise Refuse(f"{g}: a cell is missing or partial")
        if not (_pct(env.get("render_us")) and _pct(env.get("present_us")) and _pct(spl.get("render_us")) and _pct(spl.get("present_us"))):
            raise Refuse(f"{g}: intervals are not integer p50/p95/p99/max")
        if tuple(spl.get("phases_us", {}).keys()) != PHASES or not all(_pct(v) for v in spl["phases_us"].values()):
            raise Refuse(f"{g}: the split's phases are missing or not integer percentiles")
    return d


def derive(gd: dict) -> dict:
    env, spl, ph = gd["envelope"]["render_us"], gd["split"]["render_us"], gd["split"]["phases_us"]
    tax = spl["p50"] - env["p50"]
    return {"envelope_p50_us": env["p50"], "envelope_p99_us": env["p99"],
            "blit_p50_us": ph["blit"]["p50"], "blit_p99_us": ph["blit"]["p99"],
            "non_blit_p50_sum_us": sum(ph[p]["p50"] for p in NON_BLIT),
            "tax_p50_us": tax, "abs_tax_p50_permille_of_envelope": (abs(tax) * 1000) // env["p50"] if env["p50"] > 0 else 0,
            "present_p50_us": gd["envelope"]["present_us"]["p50"], "present_p99_us": gd["envelope"]["present_us"]["p99"]}


def attribute(h: dict, f: dict) -> tuple[str, dict]:
    """The preregistered attribution, on p50s -> (label, the deltas)."""
    dB = f["blit_p50_us"] - h["blit_p50_us"]
    dN = f["non_blit_p50_sum_us"] - h["non_blit_p50_sum_us"]
    deltas = {"blit_delta_p50_us": dB, "blit_delta_p99_us": f["blit_p99_us"] - h["blit_p99_us"],
              "blit_delta_permille_of_half": (abs(dB) * 1000) // h["blit_p50_us"] if h["blit_p50_us"] > 0 else 0,
              "non_blit_delta_p50_us": dN,
              "non_blit_delta_permille_of_half": (abs(dN) * 1000) // h["non_blit_p50_sum_us"] if h["non_blit_p50_sum_us"] > 0 else 0,
              "envelope_delta_p50_us": f["envelope_p50_us"] - h["envelope_p50_us"],
              "present_delta_p50_us": f["present_p50_us"] - h["present_p50_us"]}
    if max(h["abs_tax_p50_permille_of_envelope"], f["abs_tax_p50_permille_of_envelope"]) >= VOID_TAX_PERMILLE:
        return "VOID", deltas
    if deltas["non_blit_delta_permille_of_half"] >= CONFOUND_PERMILLE:
        return "CONFOUNDED", deltas
    if deltas["blit_delta_permille_of_half"] >= MATERIAL_PERMILLE:
        return ("SCALING MATERIAL (the full-size destination is cheaper)" if dB < 0
                else "SCALING MATERIAL (the full-size destination is dearer)"), deltas
    return "SCALING IMMATERIAL", deltas


def seal_presentscale(raw: dict, reg: dict, host: str, session: dict, build: dict,
                      confirm_of: dict | None = None) -> tuple[dict, str]:
    d = check_raw(raw)
    h, f = derive(d["geometries"]["half"]), derive(d["geometries"]["full"])
    label, deltas = attribute(h, f)
    data = dict(d)
    data["derived"] = {"half": h, "full": f, "deltas": deltas}
    data["rule_permille"] = {"void_tax": VOID_TAX_PERMILLE, "confounded": CONFOUND_PERMILLE, "material": MATERIAL_PERMILLE}
    prov = {
        "tool": "shell presentscale-window (shell/presentscale.rs court over the settable-client GDI surface appended to "
                "shell/win32.rs) + verify/presentscale.py",
        "surface": raw.get("provenance", {}).get("tool", ""),
        "host": host, "session": session, "build": build,
        "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
        "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "preregistered": {"rung": "PRESENT-SCALE-0", "chain_hash": reg["PRESENT-SCALE-0"]["chain_hash"]},
    }
    scr = d["screen"]
    dpi_note = ("" if scr["logical"] == scr["desktop"] else
                f" The logical screen ({scr['logical'][0]}x{scr['logical'][1]}) differs from the physical desktop "
                f"({scr['desktop'][0]}x{scr['desktop'][1]}): the compositor scales this DPI-unaware window again on the "
                f"way to the glass, in both geometries alike.")
    reading = (f"PRESENT-SCALE-0 on host {host} ({d['samples_per_cell']} samples per cell, blocks {BLOCK_ORDER}, stretch "
               f"mode {d['stretch_mode']}). Blit p50/p99: half {h['blit_p50_us']}/{h['blit_p99_us']} us, full "
               f"{f['blit_p50_us']}/{f['blit_p99_us']} us (delta {deltas['blit_delta_p50_us']} us at p50, "
               f"{deltas['blit_delta_permille_of_half']} permille of the half-size blit). Non-blit phases moved "
               f"{deltas['non_blit_delta_p50_us']} us ({deltas['non_blit_delta_permille_of_half']} permille); envelopes "
               f"{h['envelope_p50_us']} -> {f['envelope_p50_us']} us; frame-ready -> composited {h['present_p50_us']} -> "
               f"{f['present_p50_us']} us. Reading: {label}." + dpi_note +
               " A diagnostic: it attributes, it does not seat or promote a change; not input-to-photon.")
    name = "verdandi-presentscale"
    if confirm_of is not None:
        name = "verdandi-presentscale-confirm"
        prov["confirms"] = confirm_of
        same = confirm_of.get("original_label") == label
        reading = (f"CONFIRMATION run — does NOT replace the sealed PRESENT-SCALE-0 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"The reading {'REPRODUCED' if same else 'did NOT reproduce'}: original {confirm_of.get('original_label')}, "
                   f"this run {label}. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the shell's production frame presented into a half-size (960x540) and a full-size (1920x1080) "
                      f"client area on host {host}, envelope and split per geometry, locked phase origin, "
                      f"{d['samples_per_cell']} samples per cell over {d['sequence_frames']} frames"
                      + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["a seat, a winner or a promoted change: this court attributes the blit's cost to destination scaling or not, nothing more",
         "that the full-size window is what the shell should use (it changes what the window shows and how much screen it takes)",
         "a claim about any present path other than StretchDIBits into a GDI window (PRESENT-1's flip model is not measured here)",
         "that the pixels reaching the glass are certified in either geometry (the stretch mode and any DPI scaling are recorded, not verified)",
         "input-to-photon latency, or a comparison with any emit p99",
         "any other host, panel, DPI setting, window position or phase origin; absolute us are host-specific"],
        data, reading)
    return rec, label


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--session", default=DEFAULT_SESSION)
    ap.add_argument("--per-cell", type=int, default=300)
    ap.add_argument("--confirm", action="store_true",
                    help="a reproducibility run: seal a SEPARATE presentscale-confirm-<host>.json citing the sealed record")
    a = ap.parse_args()
    run = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        if os.name != "nt":
            raise Refuse("PRESENT-SCALE-0 is Windows-only (the instrument is the GDI/DWM window)")
        if a.per_cell <= 0 or a.per_cell % 4:
            raise Refuse("--per-cell must be a positive multiple of 4 (four blocks per geometry)")
        reg = registry()
        if "PRESENT-SCALE-0" not in reg:
            raise Refuse("PRESENT-SCALE-0 is not preregistered — no number before the method")
        rustc = shutil.which("rustc")
        if rustc is None:
            raise Refuse("rustc not found")
        build_dir = os.path.join(ROOT, "verify", "build")
        os.makedirs(build_dir, exist_ok=True)
        exe = os.path.join(build_dir, "shell-presentscale.exe")
        flags = ["-O", "--cfg", "shell_window"]
        cp = subprocess.run([rustc] + flags + [os.path.join(ROOT, "shell", "main.rs"), "-o", exe], **run)
        if cp.returncode != 0:
            raise Refuse("rustc failed:\n" + cp.stderr)
        build = {"rustc": subprocess.run([rustc, "--version"], **run).stdout.strip(), "flags": flags}
        srec = envelope.read(os.path.join(ROOT, a.session))
        session = {"path": a.session, "chain_hash": srec["chain_hash"], "head": srec["data"]["head"]}
        cp = subprocess.run([exe, "presentscale-selftest", "--session", a.session, "--per-cell", "4"], cwd=ROOT, **run)
        if cp.returncode != 0 or "presentscale court OK" not in cp.stdout:
            raise Refuse("the headless court did not reproduce the sealed witnesses — no number is taken\n" + cp.stdout + cp.stderr)
        raw_path = os.path.join(build_dir, f"presentscale-raw-{a.host}.json")
        if os.path.exists(raw_path):
            os.remove(raw_path)
        sys.stdout.flush()
        rc = subprocess.run([exe, "presentscale-window", "--session", a.session, "--per-cell", str(a.per_cell),
                             "--host", a.host, "--out", raw_path], cwd=ROOT).returncode
        if rc != 0 or not os.path.exists(raw_path):
            raise Refuse("the window court refused or wrote nothing (its reason is printed above)")
        with open(raw_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        os.remove(raw_path)
        confirm_of = None
        name = f"presentscale-{a.host}.json"
        if a.confirm:
            canon = os.path.join(ROOT, "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            lab, _ = attribute(orig["data"]["derived"]["half"], orig["data"]["derived"]["full"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"], "original_label": lab}
            name = f"presentscale-confirm-{a.host}.json"
        rec, label = seal_presentscale(raw, reg, a.host, session, build, confirm_of)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out_dir = os.path.join(ROOT, "shell", "attest")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name)
    envelope.write(out, rec)
    dv = rec["data"]["derived"]
    print(f"[presentscale] {label} — blit p50 half {dv['half']['blit_p50_us']} us, full {dv['full']['blit_p50_us']} us "
          f"({dv['deltas']['blit_delta_permille_of_half']} permille); non-blit moved {dv['deltas']['non_blit_delta_permille_of_half']} permille")
    print(f"[presentscale] -> {os.path.relpath(out, ROOT)}  (cites PRESENT-SCALE-0 {reg['PRESENT-SCALE-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
