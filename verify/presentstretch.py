# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""presentstretch.py — PRESENT-STRETCH-0: does the 2:1 blit's cost depend on GDI's stretch mode (off-gate, host).

    python verify/presentstretch.py --host NAME [--session workshop/attest/sessionwalk-demo.json] [--per-cell 300] [--confirm]

PRESENT-SCALE-0 (confirmed) found the half-size blit far dearer than the 1:1 one on the owner's host under the
default stretch mode, BLACKONWHITE. This diagnostic court varies ONE thing at the half-size destination: the stretch
mode — BLACKONWHITE (1, the default, set explicitly), COLORONCOLOR (3) and HALFTONE (4) — set with the brush origin
before every blit, identically; blocks B C H H C B B C H H C B, 5 warm-up rounds each, the effective mode read back
and required to equal the request, the 960x540 client area read back. Everything else is FRAME-SPLIT-0's path.

The preregistered reading, on p50s, for each of COLORONCOLOR and HALFTONE against BLACKONWHITE: VOID (for the whole
court) if any mode's |instrumentation tax| >= 100 permille of its envelope; CONFOUNDED if that mode's non-blit phases
moved >= 50 permille of BLACKONWHITE's; otherwise |blit delta| >= 100 permille of BLACKONWHITE's blit reads MODE
MATERIAL (cheaper or dearer), less reads MODE IMMATERIAL. A diagnostic: no seat, no winner, and no mode is adopted —
each mode draws different pixels, so choosing one is a separate court. Writes shell/attest/presentstretch-<host>.json.
"""
from __future__ import annotations

import argparse
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envelope  # noqa: E402
from diagcommon import Refuse, host_run, registry, write_record  # noqa: E402

DEFAULT_SESSION = "workshop/attest/sessionwalk-demo.json"
PHASES = ("strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit")
NON_BLIT = PHASES[:-1]
MODES = {"BLACKONWHITE": 1, "COLORONCOLOR": 3, "HALFTONE": 4}
PCT = ("p50", "p95", "p99", "max")
BLOCK_ORDER = "BCHHCBBCHHCB"
WARM_ROUNDS_PER_BLOCK = 5
VOID_TAX_PERMILLE = 100
CONFOUND_PERMILLE = 50
MATERIAL_PERMILLE = 100


def _pct(x) -> bool:
    return isinstance(x, dict) and all(isinstance(x.get(k), int) for k in PCT)


def check_raw(raw: dict) -> dict:
    if raw.get("name") != "verdandi-presentstretch":
        raise Refuse("not a verdandi-presentstretch record")
    d = raw.get("data", {})
    if tuple(d.get("phases", ())) != PHASES or d.get("source") != [1920, 1080]:
        raise Refuse("the phases or the source size are not the registered ones")
    if d.get("destination") != [960, 540] or d.get("client") != [960, 540]:
        raise Refuse("the client area is not the half-size 960x540")
    if (d.get("production_threads"), d.get("warm_rounds_per_block"), d.get("block_order"), d.get("phase_origin"), d.get("default_mode")) != \
            (8, WARM_ROUNDS_PER_BLOCK, BLOCK_ORDER, "locked", "BLACKONWHITE"):
        raise Refuse("production T, warm-up, block order, phase origin or default mode is not the registered one")
    n = d.get("samples_per_cell")
    if not isinstance(n, int) or n <= 0 or n % 4:
        raise Refuse("samples per cell is not a positive multiple of 4")
    for name, mode in MODES.items():
        md = d.get("modes", {}).get(name, {})
        if md.get("requested") != mode or md.get("effective") != mode:
            raise Refuse(f"{name}: the device context did not report the requested mode {mode}")
        env, spl = md.get("envelope", {}), md.get("split", {})
        if env.get("samples") != n or spl.get("samples") != n:
            raise Refuse(f"{name}: a cell is missing or partial")
        if not (_pct(env.get("render_us")) and _pct(env.get("present_us")) and _pct(spl.get("render_us")) and _pct(spl.get("present_us"))):
            raise Refuse(f"{name}: intervals are not integer p50/p95/p99/max")
        if tuple(spl.get("phases_us", {}).keys()) != PHASES or not all(_pct(v) for v in spl["phases_us"].values()):
            raise Refuse(f"{name}: the split's phases are missing or not integer percentiles")
    return d


def derive(md: dict) -> dict:
    env, spl, ph = md["envelope"]["render_us"], md["split"]["render_us"], md["split"]["phases_us"]
    tax = spl["p50"] - env["p50"]
    return {"envelope_p50_us": env["p50"], "envelope_p99_us": env["p99"],
            "blit_p50_us": ph["blit"]["p50"], "blit_p99_us": ph["blit"]["p99"],
            "non_blit_p50_sum_us": sum(ph[p]["p50"] for p in NON_BLIT),
            "tax_p50_us": tax, "abs_tax_p50_permille_of_envelope": (abs(tax) * 1000) // env["p50"] if env["p50"] > 0 else 0}


def attribute(dv: dict) -> tuple[str, dict]:
    """The preregistered attribution -> (label, per-mode readings and deltas)."""
    base = dv["BLACKONWHITE"]
    if max(v["abs_tax_p50_permille_of_envelope"] for v in dv.values()) >= VOID_TAX_PERMILLE:
        return "VOID", {}
    out = {}
    for name in ("COLORONCOLOR", "HALFTONE"):
        m = dv[name]
        dN = m["non_blit_p50_sum_us"] - base["non_blit_p50_sum_us"]
        dB = m["blit_p50_us"] - base["blit_p50_us"]
        nperm = (abs(dN) * 1000) // base["non_blit_p50_sum_us"] if base["non_blit_p50_sum_us"] > 0 else 0
        bperm = (abs(dB) * 1000) // base["blit_p50_us"] if base["blit_p50_us"] > 0 else 0
        if nperm >= CONFOUND_PERMILLE:
            reading = "CONFOUNDED"
        elif bperm >= MATERIAL_PERMILLE:
            reading = "MODE MATERIAL (cheaper)" if dB < 0 else "MODE MATERIAL (dearer)"
        else:
            reading = "MODE IMMATERIAL"
        out[name] = {"reading": reading, "blit_delta_p50_us": dB, "blit_delta_permille_of_default": bperm,
                     "non_blit_delta_p50_us": dN, "non_blit_delta_permille_of_default": nperm,
                     "envelope_delta_p50_us": m["envelope_p50_us"] - base["envelope_p50_us"]}
    return "; ".join(f"{k}: {v['reading']}" for k, v in out.items()), out


def seal_presentstretch(raw: dict, reg: dict, host: str, session: dict, build: dict,
                        confirm_of: dict | None = None) -> tuple[dict, str]:
    d = check_raw(raw)
    dv = {name: derive(d["modes"][name]) for name in MODES}
    label, per_mode = attribute(dv)
    data = dict(d)
    data["derived"] = {"modes": dv, "against_default": {k: {kk: vv for kk, vv in v.items() if kk != "reading"} for k, v in per_mode.items()}}
    data["rule_permille"] = {"void_tax": VOID_TAX_PERMILLE, "confounded": CONFOUND_PERMILLE, "material": MATERIAL_PERMILLE}
    prov = {"tool": "shell presentstretch-window (shell/presentstretch.rs court over the half-size stretch-mode GDI surface "
                    "appended to shell/win32.rs) + verify/presentstretch.py",
            "surface": raw.get("provenance", {}).get("tool", ""), "host": host, "session": session, "build": build,
            "raw_unix_seconds": raw.get("provenance", {}).get("unix_seconds"),
            "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
            "preregistered": {"rung": "PRESENT-STRETCH-0", "chain_hash": reg["PRESENT-STRETCH-0"]["chain_hash"]}}
    blits = ", ".join(f"{k} {v['blit_p50_us']}/{v['blit_p99_us']}" for k, v in dv.items())
    reading = (f"PRESENT-STRETCH-0 on host {host} ({d['samples_per_cell']} samples per cell, blocks {BLOCK_ORDER}, half-size "
               f"960x540). Blit p50/p99 us: {blits}. Against BLACKONWHITE: {label}. A diagnostic: no seat, no winner, no mode "
               f"adopted — each mode draws different pixels; not input-to-photon.")
    name = "verdandi-presentstretch"
    if confirm_of is not None:
        name = "verdandi-presentstretch-confirm"
        prov["confirms"] = confirm_of
        same = confirm_of.get("original_label") == label
        reading = (f"CONFIRMATION run — does NOT replace the sealed PRESENT-STRETCH-0 record (chain {confirm_of['chain_hash'][:8]}). "
                   f"The reading {'REPRODUCED' if same else 'did NOT reproduce'}: original {confirm_of.get('original_label')}; "
                   f"this run {label}. ") + reading
    rec = envelope.seal(
        name, 1, "measured", prov,
        {"certifies": f"the shell's production frame presented into the half-size 960x540 client area under stretch modes "
                      f"BLACKONWHITE, COLORONCOLOR and HALFTONE on host {host}, envelope and split per mode, locked phase "
                      f"origin, {d['samples_per_cell']} samples per cell over {d['sequence_frames']} frames"
                      + (" (a confirmation run)" if confirm_of is not None else ""),
         "host": host},
        ["a seat, a winner or an adopted mode: each mode draws different pixels, so choosing one is a separate court",
         "that any mode's pixels on the glass are certified (the modes' semantics are GDI's, recorded, not verified)",
         "a statement about GDI or Windows in general: this host, this apparatus and workload only",
         "input-to-photon latency, or a comparison with any emit p99",
         "any other host, destination size, DPI setting or phase origin"],
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
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    try:
        if a.per_cell <= 0 or a.per_cell % 4:
            raise Refuse("--per-cell must be a positive multiple of 4 (four blocks per mode)")
        raw, session, build = host_run("PRESENT-STRETCH-0", "presentstretch", a.host, a.session, a.per_cell, 4)
        reg = registry()
        name, confirm_of = f"presentstretch-{a.host}.json", None
        if a.confirm:
            canon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shell", "attest", name)
            if not os.path.exists(canon):
                raise Refuse(f"nothing to confirm — no sealed shell/attest/{name}; run without --confirm first")
            orig = envelope.read(canon)
            lab, _ = attribute(orig["data"]["derived"]["modes"])
            confirm_of = {"of": f"shell/attest/{name}", "chain_hash": orig["chain_hash"], "original_label": lab}
            name = f"presentstretch-confirm-{a.host}.json"
        rec, label = seal_presentstretch(raw, reg, a.host, session, build, confirm_of)
    except Refuse as e:
        print(f"REFUSE: {e}")
        return 2
    out = write_record(name, rec)
    print(f"[presentstretch] {label}")
    print(f"[presentstretch] -> {os.path.relpath(out)}  (cites PRESENT-STRETCH-0 {reg['PRESENT-STRETCH-0']['chain_hash'][:8]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
