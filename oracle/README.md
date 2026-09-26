<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `oracle/` — frozen evidence from Urðr

Nothing in this folder is computed here. Every file is carried from `Dedoc-9/Urdr` at the tag
`urdr-oracle-1` (commit `4c8c2451d942ff320a11501b59fbbf2737ec42ce`), and the studio consumes it read-only:
the kernel is compared against it, the workshop measures consequences relative to it, no code path writes it.
A new oracle is a new file with a new name and a new tag behind it, never an edit to this one.

| File | Origin in Urðr | sha256 |
|---|---|---|
| `urdr-oracle-1.json` | `studio/attest/studio-oracle-1.json` at the tag, verbatim | `470d3ab2b1e3ac5a13cefa028b6362fa938fb0dc7a6ad447ced8b01438ec32c9` |
| `levels/witness.lvl` `corridor.lvl` `room.lvl` `landmark.lvl` `neighbour.lvl` | `gamegen.generate(seed, depth)` at the tag, with the depth's `vista.lut` table and `mantle` band maps (`VRDNLVL1`; W = the file's sha256; Urðr's `level_digest` beside each in `witnesses.json`) | in `witnesses.json` |
| `tiles/identity.tiles` `oriented.tiles` | `mantle.identity_tiles()` and the oriented synthetic set (`VRDNTIL1`; M = the file's sha256; Urðr's `tiles_digest` beside each) | in `witnesses.json` |
| `game/` | Urðr's game layer (GAME-0): the seventeen discrete vertical slices, their corpora, suites, briefs, D24/D25 and the two physics modules `kinema` needs, verbatim at the same paths — see [`game/README.md`](game/README.md) | each in `game/MANIFEST.json`, with its git blob id (the manifest pinned by `game-frozen`) |
| `witnesses.json` | the corpus: six scenes (the four of Urðr's corpus, the witness view, and the neighbour seed `0xABCDF` whose level keeps the witness camera on floor) × two tile sets, each with its frame digest and pixel sha computed live by the tag's Python modules | — |

What the record fixes: the view (seed `0xABCDE`, depth 1, the player at (34, 28) facing W), `D_0`, the
URDRFB1 frame digest, the identity picture's pixel sha256, the oriented picture and its tile digest, the
identity laws, the camera constants, the index layout, the corpus goldens, the kernel input format and the
Python that witnessed it. Of the three hashes, two are reproduced natively by the kernel (the frame digest
and the pixel sha); `D_0` is Urðr's composed CORE identity and is evidence only.
