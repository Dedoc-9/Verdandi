<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Verðandi — a windowed design workshop over a frozen oracle

`Verðandi` (Verdandi in ASCII, for the repository and the crate names) is the second norn: what is becoming,
beside `Urðr`, what has become. It is a deterministic 1080p game-rendering studio with a measurable
low-latency presentation path — the target stated as what can be measured, never as a claim. Its native
kernel reproduces the pixels of the certified renderer in [`Dedoc-9/Urdr`](https://github.com/Dedoc-9/Urdr)
bit for bit; its workshop turns an authored edit into a new authority and an exact consequence record; its
shell owns the window and nothing else.

**Author:** Daniel J. Dillberg · **Contact:** [bigdilly95@gmail.com](mailto:bigdilly95@gmail.com)
**License:** [AGPL-3.0-only](LICENSE)

## The charter (ratified before the first commit)

    KERNEL
      deterministic · std-only · no shell dependency · no UI toolkit · no presentation API

    WORKSHOP
      owns authored edits · validates before projection · can create new authority
      records consequences · does not become renderer state accidentally

    SHELL
      owns window / input / presentation · contains no kernel logic
      contains no authority mirror · is replaceable

    UI
      viewport + HUD = the kernel's framebuffer, digest-pinned
      editor / inspector / tool panes = shell chrome, declared off-gate

    ORACLE
      Urðr is frozen evidence (the tag urdr-oracle-1) · not a runtime dependency

The dependency rule, and its negation:

    oracle ──► kernel                    never:   kernel ──► shell
                 ▲                                kernel ──► workshop
                 │                                shell  ──► canonical authority
    workshop ────┘

    shell ──────► kernel framebuffer

## Why this repository exists (the measurement that preceded it)

Urðr grew to 1,612 files and a thirty-six-minute gate; the game/render kernel is one fortieth of that tree.
STUDIO-0 asked, before any second repository, whether a native kernel of the certified tile path could hit a
1080p frame budget on the owner's hardware: the placement (`tools/terrain/mantle_rs/mantle.rs`, std-only
Rust, vista + mantle in reduced rationals) reproduced all twenty witnesses on its first compile, and on the
owner's host it rendered the identity picture at p50 11,361 / p95 11,959 / p99 12,319 / max 12,388 µs —
within the 60 Hz budget of 16,667 µs unoptimised, over 144 and 240 Hz. Renderer time, not input-to-photon.
The decision rule fired: the studio's first row already existed. The old studio arc (`Ursprung/weltwerk`)
was measured too, and what it settled is recorded in the shell's contract: a shell that mirrors kernel logic
is a second authority.

## What each folder holds

| Folder | Contract |
|---|---|
| `oracle/` | frozen evidence from Urðr at `urdr-oracle-1`: the contract record, and (later rungs) the corpus inputs the kernel is compared against. Read-only by convention; a change here is a new oracle, named. |
| `kernel/` | the deterministic per-frame work: a scene in, an index frame and a picture out, two witnesses. std-only. |
| `workshop/` | the design loop: an edit in, a new authority out, a consequence record beside it. Validates before it projects. |
| `shell/` | the window: blit the kernel's framebuffer, pump input, time the present path. Owns no truth. |
| `verify/` | the gate: every claim above as a row that can redden; two runs byte-identical or nothing landed. |

## The sequence (each rung stands on one already measurable)

    CREATE REPO ── the charter (c3cda5a)
         │
    KERNEL-0 ──── the placement reproduces the oracle natively, against the tag
         │
    WORKSHOP-0 ── edit → new authority → witness diff, with the planted falsifiers
         │
    HUD-0 ─────── the overlay is a frame: reticle, band bar, facing plate, minimap — pinned, index-free
         │
    SHELL-0 ───── a real window (hand-rolled Win32, zero crates), frame → composited timed;
         │        the shell hashes what it blits
    MEMBRANE-0 ── the one-way law as a compile-time wall (a row whose PASS is rustc refusing a plant)
         │
    TEXT-0 ────── the level as text, content split from provenance
         │
    WORKSHOP-1 ── the log is the history, undo is replay, the session is a file
         │
    INPUT-0 ───── shell input → typed command → new camera; the command log replays headless
         │
    LATENCY-0 ─── receipt → kernel → composited, two instruments (DWM timing beside PresentMon);
         │        never input-to-photon (input transport, present wait beyond composition and the
         │        panel need capture hardware; nothing here claims them)
    GAUNTLET-1 ── the incremental floor cast: faster AND the same witnesses
         │
    GAUNTLET-2 ── columns in parallel, invariant under the thread count
         │
    MATERIAL-0 ── a picture becomes a material under a gate

`D_0`, the third hash in the oracle, is Urðr's composed CORE identity (level, entity, RNG stream, action log)
and is carried as evidence only; the studio does not recompute it and does not mint it. New VIEW semantics the
studio did not inherit (filtering, variety) may be earned by either route — in Urðr and re-frozen here as a
new oracle, or by a Verðandi-local reference pinned by rows here, as the HUD's pins are; CORE semantics have
one route only. Which, is decided when such a rung is seated.

## Running

    python verify/verify.py                                  # the gate; needs rustc for the kernel rows
    rustc -O kernel/main.rs -o verify/build/kernel           # the kernel alone
    verify/build/kernel --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles --camera 34,28,W
    verify/build/kernel ... --bench 200 --warm 20            # off-gate: renderer time on this host
    verify/build/kernel ... --hud --write-png out.ppm         # the composite with the overlay, to look at
    rustc -O workshop/edit.rs -o verify/build/edit           # the workshop
    verify/build/edit record --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles \
        --camera 34,28,W --edit cell:31,27,. --out-dir out --name cell
    verify/build/edit check --record out/cell.record.json

Landing condition: two consecutive gate runs byte-identical and `GATE PASSED`. The ledger is
[`verify/RUNGS.md`](verify/RUNGS.md).

## Discipline

Every claim is graded — MEASURED, ESTABLISHED, DECLARED — with a `does_not_show` boundary and a falsifier that
can fail. Tests assert the apparatus (the plant bites), never a hoped outcome. Two witnesses per row where
two quantities exist (geometry and appearance), never one. Wall-clock is off-gate, on a named host, with the
witnesses checked before any number is printed. `integrity ≠ truth`; `built ≠ adopted`; `declared ≠ verified`.
