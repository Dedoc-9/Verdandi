<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `oracle/game/` — Urðr's game layer, carried as frozen evidence (GAME-0)

Nothing in this folder except this README and `MANIFEST.json` is Verðandi's. Every other file is carried verbatim from
`Dedoc-9/Urdr` at the tag `urdr-oracle-1` (commit `4c8c2451d942ff320a11501b59fbbf2737ec42ce`) — the **same tag** the
rest of `oracle/` cites — at the **same path** it has in Urðr. No new oracle is minted and no charter clause moves:
these are CORE and VIEW semantics that were earned in Urðr and frozen there, which is the one route the charter
allows CORE semantics to reach this repository by.

## What is here

The runtime closure of Urðr's seventeen discrete game-layer vertical slices, found by relocating them and running
their own mains and suites until nothing was missing:

| Folder | Holds |
|---|---|
| `tools/terrain/` | the seventeen slices — `gamegen`, `descent`, `move`, `entity`, `rngstream`, `descend`, `loot`, `combat`, `heirloom`, `actionlog`, `savegame`, `enact`, `rerun`, `statecanon`, `kinema`, `chorus`, `cue` — and each one's frozen `conformance_<slice>.txt` corpus |
| `tools/physics/` | `field.py` and `rational.py` only: `kinema` reads the frozen Q32.32 radix from `field.ONE`, and `field` imports `rational` |
| `tests/` | each slice's red-first suite, 411 tests in all |
| `docs/` | each slice's brief and the game-layer roadmap, as Urðr wrote them |
| `spec/` | `D24` (the game boundary) and `D25` (the kinema view membrane) |

Three members are in the closure for a reason the import graph alone does not show: `enact` reads the source of
`combat.py` and `heirloom.py` as its derivations register, and `test_cue`'s one-way audit names `chorus` among the
observers it checks. `MANIFEST.json` records these reasons beside the file list.

## How it is held frozen

`MANIFEST.json` lists every file with its size, its sha256 and its **git blob id** — the id `git ls-tree -r
urdr-oracle-1` prints for that path in Urðr — so anyone holding Urðr can check every file without trusting this
repository. `.gitattributes` marks the folder `-text`, so git never rewrites a line ending in it. Four gate rows
hold the rest:

- `game-frozen` — every file's bytes, sha256 and git blob, recomputed from disk, equal the manifest; the tree holds
  nothing the manifest does not list; the manifest's own digest is pinned in `verify/verify.py`; the origin is the
  oracle's tag and commit; and every import is a closure module or one of nine pinned stdlib names.
- `game-suites` — Urðr's own 411 tests pass in place under `PYTHONHASHSEED=0`, and all seventeen slices' witnesses
  exit 0 and print their `does_not_show` boundary.
- `game-plant` — one hex digit of a frozen golden, flipped in a scratch copy, is refused by the byte check **and**
  reddens Urðr's own suite. Both checks can fail.
- `game-not-runtime` — no `kernel/`, `workshop/` or `shell/` code reaches into this folder.

To run the suites yourself, from this folder:

    python -m unittest discover -s tests -p "test_*.py"

## What it is not

It is not a runtime dependency. The kernel, the workshop and the shell do not read it; only the gate does. A
Verðandi-native placement of any of these slices would be a separate rung that reproduces these corpora byte for
byte, the way `KERNEL-0` reproduced the frozen renderer. It is not a claim that the game layer is fast, complete or
fun: each slice's `does_not_show` says what that slice does not establish, and those statements still apply here.
A change to any file in this folder would be a new oracle with a new name, never an edit to this one.
