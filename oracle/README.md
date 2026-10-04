<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `oracle/` — frozen evidence from Urðr

Nothing in this folder is computed here. Every file is carried from `Dedoc-9/Urdr` at the tag
`urdr-oracle-1` (commit `4c8c2451d942ff320a11501b59fbbf2737ec42ce`), except the two BEARING-0 carried from the tag
`urdr-oracle-2` (commit `ad6d55fea165c13841d8305bec38b7f93e8f0f77`), and the studio consumes it read-only:
the kernel is compared against it, the workshop measures consequences relative to it, no code path writes it.
A new oracle is a new file with a new name and a new tag behind it, never an edit to this one.

## Blueprint

This folder is the one place the studio does not decide anything. Its design is a direction: evidence flows out of
it and nothing flows in.

```text
    Dedoc-9/Urdr @ urdr-oracle-1 ──► urdr-oracle-1.json · levels/ · tiles/ · witnesses.json · game/
    Dedoc-9/Urdr @ urdr-oracle-2 ──► urdr-oracle-2.json · bearing_octant.txt
                                          │ read, hashed, compared against
                                          ▼
                              kernel/ (reproduces the witnesses)   verify/ (pins every byte carried)
```

| Invariant | Mechanism | Row |
|---|---|---|
| Every carried byte is the tag's | each file's sha256 pinned; the game layer by manifest and git blob id | `oracle-frozen`, `oracle2-frozen`, `game-frozen` |
| What the records state can be recomputed | every digest of `urdr-oracle-2` rebuilt from the record and the octant alone | `oracle2-identity` |
| The third hash is checked and not minted | Urðr's own `statecanon`, run in place | `oracle-d0` |
| The game layer still passes its own tests here | Urðr's suites run in place, with a plant | `game-suites`, `game-plant` |
| Nothing at run time depends on the game layer | a source fence over the kernel, the workshop and the shell | `game-not-runtime` |

| File | Origin in Urðr | sha256 |
|---|---|---|
| `urdr-oracle-1.json` | `studio/attest/studio-oracle-1.json` at the tag, verbatim | `470d3ab2b1e3ac5a13cefa028b6362fa938fb0dc7a6ad447ced8b01438ec32c9` |
| `levels/witness.lvl` `corridor.lvl` `room.lvl` `landmark.lvl` `neighbour.lvl` | `gamegen.generate(seed, depth)` at the tag, with the depth's `vista.lut` table and `mantle` band maps (`VRDNLVL1`; W = the file's sha256; Urðr's `level_digest` beside each in `witnesses.json`) | in `witnesses.json` |
| `tiles/identity.tiles` `oriented.tiles` | `mantle.identity_tiles()` and the oriented synthetic set (`VRDNTIL1`; M = the file's sha256; Urðr's `tiles_digest` beside each) | in `witnesses.json` |
| `game/` | Urðr's game layer (GAME-0): the seventeen discrete vertical slices, their corpora, suites, briefs, D24/D25 and the two physics modules `kinema` needs, verbatim at the same paths — see [`game/README.md`](game/README.md) | each in `game/MANIFEST.json`, with its git blob id (the manifest pinned by `game-frozen`) |
| `urdr-oracle-2.json` | `studio/attest/studio-oracle-2.json` at the tag `urdr-oracle-2` (commit `ad6d55fea165c13841d8305bec38b7f93e8f0f77`), verbatim — BEARING-0: the bearing camera's contract (the registered vocabulary, the law, URDRBRG1's identity, the anchor witness, the 26 corpus cases with every witness, the kernel input format), extending `urdr-oracle-1.json` by its sha256 | `61d51062917bce7b25fb76c7fbbdc30d42bb3c98a7f044c4a863329d73e2d8c5` |
| `bearing_octant.txt` | `tools/terrain/bearing_octant.txt` at `urdr-oracle-2`, verbatim: the octant of the registered headings, 45,001 lines `p q`; compiled into the kernel by `kernel/vocab.rs` and refused there if it does not match this pin (the record's `octant_sha256`) | `f70b2fc20ba8ea8fde7f802ae0f1180ae003d2de5acb963524ca58421405a82c` |
| `witnesses.json` | the corpus: six scenes (the four of Urðr's corpus, the witness view, and the neighbour seed `0xABCDF` whose level keeps the witness camera on floor) × two tile sets, each with its frame digest and pixel sha computed live by the tag's Python modules | — |

What the record fixes: the view (seed `0xABCDE`, depth 1, the player at (34, 28) facing W), `D_0`, the
URDRFB1 frame digest, the identity picture's pixel sha256, the oriented picture and its tile digest, the
identity laws, the camera constants, the index layout, the corpus goldens, the kernel input format and the
Python that witnessed it. Of the three hashes, two are reproduced natively by the kernel (the frame digest
and the pixel sha); `D_0` is Urðr's composed CORE identity and is evidence: since ORACLE-D0 it is recomputed at
gate time by Urðr's own `statecanon`, in place under `game/` (row `oracle-d0`), and the studio still does not mint it.

Since BEARING-0 a second tag stands beside the first. `urdr-oracle-2` freezes Urðr's bearing camera (VIEW-YAW-0): a
heading is an integer id in [0, 360000) naming one primitive Pythagorean triple, and at the four cardinals it is the
frame and the picture `urdr-oracle-1` already fixes. Its two files are carried verbatim, and `urdr-oracle-1`'s carry is
untouched. Every digest the record states is recomputed by the gate from the record and the octant alone (row
`oracle2-identity`), and the reference bearing kernel reproduces its 104 witnesses (row `bearing-oracle`).

## Dev notes

- **Semantics are earned upstream.** When the studio needed a camera that turns, the turning camera was built and
  certified in Urðr first (VIEW-YAW-0) and frozen as `urdr-oracle-2`, because nothing here could hold a renderer to
  account outside the four cardinals. Anything that decides the world's cells or tiles takes that route.
- **Bytes, not meanings.** A carried file is pinned by its hash. On the owner's host `urdr-oracle-1.json` once stood
  with Windows line endings (checked out before the repository fixed its line-ending rule): 2,980 bytes against
  2,890, the same content line for line. A row that parsed it passed; the first row that hashed it refused. The row
  was kept strict and the file was checked out again.
- **These files keep Urðr's form.** The JSON here is written the way Urðr wrote it: one record ends without a final
  line feed, and two write characters above U+007F as `\u` escapes. They are read by Python alone. They are not
  the studio's saved form, they are never rewritten to fit it, and READER-COURT-0's registration says so.

## Ghosts

- The oracle is evidence of what Urðr computed, at two commits. It does not show that Urðr is right: a defect
  frozen at the tag is reproduced here bit for bit, on purpose.
- The corpus is small: six scenes and two tile sets for the facing camera, 26 cases for the bearing camera. The
  kernels are held to it and to the gate's adversarial cameras. Nothing is claimed about a level no court has seen.
- `D_0` is recomputed by Urðr's code and compared. The studio still has no implementation of it, so a change in
  how the oracle's state identity is composed would be seen and could not be explained from here.
