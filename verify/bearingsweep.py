# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""bearingsweep.py — BEARING-FAST-0's sweep on a named host (off-gate, sealed).

    python verify/bearingsweep.py --host NAME [--tread ca] [--procs N]

Every walkable cell of the five corpus levels at every whole degree (heading id 1000*d, d = 0..359) — 622,440
frames — rendered by the reference and by the production candidate, compared byte for byte (index frame and picture)
in the kernel's court (`--bearing-court --treads T --no-digest`). The tile sets alternate identity, oriented in list
order. The tread defaults to the production candidate of the sealed speed court (kernel/attest/bearingfast-<host>.json);
the list is cut into small chunks run by N processes at once, for wall-clock only, with progress printed as chunks
finish. Writes kernel/attest/bearingsweep-<host>.json, citing the BEARING-FAST-0 registration: the counts, the list's
digest and the first differing cameras if any. It is long: about an hour on a 16-thread host.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
import envelope  # noqa: E402

LEVELS = ("corridor", "landmark", "neighbour", "room", "witness")
CHUNK = 2000


def walkable(level: str) -> list:
    with open(os.path.join(ROOT, "oracle", "levels", level + ".lvl"), "rb") as fh:
        b = fh.read()
    w, h = int.from_bytes(b[8:12], "little"), int.from_bytes(b[12:16], "little")
    cells = b[16:16 + w * h]
    return [(x, z) for z in range(h) for x in range(w) if cells[z * w + x] != ord("#")]


def sweep_list() -> list:
    lines = []
    for level in LEVELS:
        for (x, z) in walkable(level):
            for d in range(360):
                tiles = "identity" if len(lines) % 2 == 0 else "oriented"
                lines.append(f"oracle/levels/{level}.lvl oracle/tiles/{tiles}.tiles {x} {z} {1000 * d}")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--tread", default=None, help="the tread to sweep (default: the sealed speed court's production candidate)")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    tread = a.tread
    court_path = os.path.join(ROOT, "kernel", "attest", f"bearingfast-{a.host}.json")
    court_hash = None
    if tread is None:
        if not os.path.exists(court_path):
            print("REFUSE: no sealed speed court (kernel/attest/bearingfast-%s.json) to name the production candidate; "
                  "run verify/bearingfast.py --host %s first, or pass --tread" % (a.host, a.host))
            return 2
        court = envelope.read(court_path)
        tread, court_hash = court["data"]["production_tread"], court["chain_hash"]
    if tread not in ("a", "b", "ca", "cb"):
        print(f"REFUSE: no fast tread named {tread!r} (the production candidate may be the reference itself)")
        return 2
    rustc = shutil.which("rustc")
    if rustc is None:
        print("REFUSE: rustc not found")
        return 2
    build = os.path.join(ROOT, "verify", "build")
    os.makedirs(build, exist_ok=True)
    exe = os.path.join(build, "kernel-bearingsweep" + (".exe" if os.name == "nt" else ""))
    print("[bearingsweep] compiling kernel/main.rs with -O ...", flush=True)
    cp = subprocess.run([rustc, "-O", os.path.join(ROOT, "kernel", "main.rs"), "-o", exe], capture_output=True, text=True)
    if cp.returncode != 0:
        print("REFUSE: rustc failed\n" + cp.stderr)
        return 2
    lines = sweep_list()
    digest = hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()
    chunks = [lines[i:i + CHUNK] for i in range(0, len(lines), CHUNK)]
    print(f"[bearingsweep] {len(lines):,} frames, tread {tread} against the reference, {len(chunks)} chunks on "
          f"{a.procs} processes", flush=True)

    def one(i):
        path = os.path.join(build, f"sweep-{i}.txt")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(chunks[i]) + "\n")
        c = subprocess.run([exe, "--bearing-court", path, "--treads", tread, "--no-digest"], cwd=ROOT,
                           capture_output=True, text=True)
        os.remove(path)
        if c.returncode != 0:
            raise RuntimeError(f"chunk {i} exited {c.returncode}: {c.stderr.strip()[-300:]}")
        eq, diffs = 0, []
        for ln in c.stdout.splitlines():
            f = ln.split()
            if f[-1] == "1":
                eq += 1
            else:
                diffs.append(chunks[i][int(f[1])])
        if eq + len(diffs) != len(chunks[i]):
            raise RuntimeError(f"chunk {i} reported {eq + len(diffs)} of {len(chunks[i])} cameras")
        return i, eq, diffs

    t0 = time.time()
    equal, differing, done = 0, [], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.procs) as pool:
        for i, eq, diffs in pool.map(one, range(len(chunks))):
            equal += eq
            differing.extend(diffs)
            done += 1
            el = time.time() - t0
            print(f"[bearingsweep] chunk {done}/{len(chunks)}  equal {equal:,}  differing {len(differing)}  "
                  f"{el / 60:.1f} min, about {el / done * (len(chunks) - done) / 60:.0f} min left", flush=True)
    elapsed = int(time.time() - t0)
    per_level = {lv: len(walkable(lv)) * 360 for lv in LEVELS}
    data = {
        "frames": len(lines), "equal": equal, "differing": len(differing), "first_differing": differing[:20],
        "tread": tread, "list_sha256": digest, "frames_per_level": per_level, "headings": "1000*d, d = 0..359",
        "tiles": "alternating identity, oriented in list order", "procs": a.procs, "elapsed_s": elapsed,
    }
    with open(os.path.join(ROOT, "verify", "preregister.json"), encoding="utf-8") as fh:
        reg = json.load(fh)["entries"]["BEARING-FAST-0"]["chain_hash"]
    prov = {
        "tool": "kernel/main.rs --bearing-court --treads T --no-digest (chunks across processes) + verify/bearingsweep.py",
        "flags": ["-O"], "rustc": subprocess.run([rustc, "--version"], capture_output=True, text=True).stdout.strip(),
        "host": a.host, "python": platform.python_version(), "os": platform.system(), "machine": platform.machine(),
        "preregistered": {"rung": "BEARING-FAST-0", "chain_hash": reg},
    }
    if court_hash:
        prov["production_from"] = {"record": f"kernel/attest/bearingfast-{a.host}.json", "chain_hash": court_hash}
    reading = (f"BEARING-FAST-0's sweep on host {a.host}: every walkable cell of the five corpus levels at every whole "
               f"degree, {len(lines):,} frames, tread {tread} against the reference byte for byte (index frame and "
               f"picture): {equal:,} equal, {len(differing)} differing"
               + (" — the production candidate IS the reference at every one." if not differing else
                  f" — the first: {differing[0]}; the tread is NOT the reference there.")
               + f" Wall-clock {elapsed // 60} min on {a.procs} processes, informational only.")
    rec = envelope.seal(
        "verdandi-bearingsweep", 1, "measured", prov,
        {"certifies": f"byte-identity of tread {tread} to the reference at every walkable cell of the five corpus levels "
                      f"at every whole degree, on host {a.host}", "host": a.host},
        ["agreement between whole degrees or off the five corpus levels beyond the exact arithmetic the gate bounds",
         "any speed: the wall-clock is the sweep's own, not a renderer number",
         "any present, window or input path"],
        data, reading)
    out = os.path.join(ROOT, "kernel", "attest", f"bearingsweep-{a.host}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    envelope.write(out, rec)
    print("[bearingsweep] " + reading)
    print(f"[bearingsweep] -> {os.path.relpath(out, ROOT)}  (cites BEARING-FAST-0 {reg[:8]})")
    return 0 if not differing else 1


if __name__ == "__main__":
    sys.exit(main())
