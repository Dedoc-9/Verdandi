<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# AGENTS.md — working in Verðandi

Verðandi is a deterministic rendering and design studio over a frozen oracle, Urðr. A gate of 251 rows holds the
program. Content is admitted without running that gate. A playable first-person graybox stands beside both. This
file is the brief for a coding agent: what to read, what never to touch, what to run, and how to write a claim. It
is plain Markdown in the [agents.md](https://agents.md/) format; a user's own instructions override it.

The rule under every other rule: **a claim is only as strong as the check that backs it.** `integrity ≠ truth`.
`declared ≠ verified`. `built ≠ adopted`. Read the code, not the prose, and that includes this file.

## 1. Where the truth is

When two sources disagree, trust them in this order:

1. **The code**, and what it does when run.
2. **The gate's rows** (`verify/verify.py`) and the **registered entries** (`verify/preregister.json`), the hashed
   methods the rows hold.
3. **The ledger**, `verify/RUNGS.md`: every rung's rows, grade, limits and falsifier, dated and append-only.
4. **The documents.**

| read | when |
|---|---|
| [`docs/CORE.md`](docs/CORE.md) | first: the modules, builds, data flow, authority, and what a change touches |
| [`docs/BINARY-SDK.md`](docs/BINARY-SDK.md) | before touching any file format, proposal language or record |
| [`docs/BOUNDARIES.md`](docs/BOUNDARIES.md) | before any graybox work: the three worlds and who writes what |
| [`docs/GHOSTS.md`](docs/GHOSTS.md) | before claiming anything: what the gate does not prove |
| [`docs/PROGRAM.md`](docs/PROGRAM.md), [`docs/ROADMAP.md`](docs/ROADMAP.md) | the why, the owner's rulings, and what is declared but not built |
| [`docs/REPOSITORY-TRUTH.md`](docs/REPOSITORY-TRUTH.md) | the last audit of documents against code, and its open findings |
| each folder's `README.md` | that folder's contract, parts, invariants and ghosts |

## 2. The map

| folder | what | held by |
|---|---|---|
| `oracle/` | frozen evidence from Urðr at two tags | `oracle-frozen`, `oracle2-*`, `game-*` — **read-only** |
| `kernel/` | std-only Rust: a scene in, an index frame and a picture out | the gate |
| `workshop/` | edits, sessions, the session verifier | the gate |
| `shell/` | presentation, the live loop and its sealed session, admission, the batch, the design compiler | the gate (the window build, `--cfg shell_window`, is off it) |
| `verify/` | the gate, the envelope, the registers, the sealers | is the gate |
| `design/` | the design tool: a client of the shell, no authority | `design/test_design.py`; no row |
| `graybox/` | the FPS slice: converter, map checks, server, browser runtime | its own checks; no row |
| `art/` | prompted art: the art file, the exporter, the Unreal importer, DIRECTOR-0 (scope, ledger, vectors) | `art/check.py`, `art/director.py selftest`, `conform.rs`; no row |
| `docs/` | the documents above | — |

## 3. Never, without the owner's word

- **Edit `oracle/`.** It is frozen evidence; a change is a new oracle, named.
- **Edit a registered entry** in `verify/preregister.json`. A correction is a new amendment entry, registered by the
  owner's ruling before what it governs is built.
- **Edit a pinned source.** Every `.rs` under `kernel/`, `shell/` and `workshop/`, and every sealer under `verify/`,
  is pinned by sha256: 58 files in `RSN_SOURCES`. A change, even to a comment, turns `reasoncourt-fence` and
  `mintwatch-fence` red until an amendment names the move and a link is added to `RSN_CHAIN`. A new file needs a
  link too.
- **Reword lines of `verify/RUNGS.md`** that `verify/reasons.json` cites; `reasoncourt-source` holds them word for
  word. Treat the ledger as append-only.
- **Edit the README's charter block** (the section "The charter (ratified before the first commit)").
- **Add a dependency.** There is no Cargo and no crate: Rust is std-only and built by bare `rustc`. Python is the
  standard library.
- **Grow the gate.** By the owner's sprint ruling (2026-10-09) the gate stops growing: no new row or rung unless a
  concrete defect blocks the work. Never change a row to make something pass.
- **Change a world by hand.** A world changes through `design/design.py` (propose, preview, then admit only after the
  owner accepts that preview), never by editing a session file, `project.json` or anything under `design/work/`.
- **Let the graybox renderer or the art decide.** They may decorate; they must not decide where walls, cover or
  anything that blocks exist. Decoration that should affect play goes into the canonical world and is checked (the
  owner's rule, `docs/BOUNDARIES.md`). In `art/` the scene's collision is C and nothing else (`art/README.md`).
- **Claim** a latency, a frame rate, input-to-photon, feel, or determinism across platforms or browsers. Software
  timings are software timings and are labelled so.
- **Commit or push.** The owner applies patches, runs the checks on his host, and pushes.

## 4. What to run, by what changed

The owner's table (2026-10-09). The full gate is a release instrument: it takes about 25 minutes in the build
container.

| what changed | run | expect |
|---|---|---|
| the compiler or authoritative semantics | the relevant engineering checks, and the gate at the checkpoint | `GATE PASSED`, then `RECONCILE  rowset 74db4c8d78625af5  251 rows / 0 fail / 0 skipped` while no row is added |
| map content (`graybox/maps/`) | `python graybox/check.py --compile` | every check and mutation PASS; `GRAYBOX MAP CHECKS PASSED` |
| graybox runtime or renderer (`graybox/web/`) | `python graybox/serve.py tactical --selftest`, then `witness` | `23 / 23` and `20 / 20`, exit 0 (a browser opens) |
| an art file, the exporter or the art's checks (`art/`) | `python art/check.py` | every check and plant PASS; `ART CHECKS PASSED` (a SKIPPED line says why it skipped) |
| the director: the canonical form, scope, the ledger (`art/director*`) | `python art/director.py selftest`, then `rustc -O art/director/conform.rs -o art/build/conform` and `art/build/conform art/director/vectors.json` | `DIRECTOR SELFTEST PASSED`; `CONFORMANCE 62 / 62`. A change to an expected output in `vectors.json` is a new protocol version, never a fix |
| a cost claim about the graybox | `python graybox/serve.py tactical --bench` | timings with the clock's step printed; a draw and readback, never a frame rate |
| the design tool | `python design/test_design.py` | 17 checks, 0 failed |
| a registered release checkpoint, or a threat to the certified contract | `python verify/verify.py`, twice, on one clean tree | the two compact outputs byte-identical |

The gate's verdict reads `GATE PASSED` whenever no row fails, **whatever the number skipped**. Without `rustc` most
rows skip, so always read the skip count. `-v` prints each row's text.

To build by hand: `rustc -O kernel/main.rs -o verify/build/kernel`, or `rustc -O shell/main.rs -o verify/build/shell`.
On Windows, `rustc -O --cfg shell_window shell/main.rs -o verify/build/shell.exe` builds the window, and the next
gate run rebuilds that path without it.

## 5. Environment

- `PYTHONHASHSEED=0` for every run.
- On Windows, set `PYTHONUTF8=1` when output is redirected; a redirected stdout uses a legacy code page.
- Line endings are LF (`.gitattributes`). Write planted files and stdin in **binary**: text mode on Windows turns LF
  into CR LF, and a design's id is the sha256 of its exact bytes.
- A stale `verify/build/` or bytecode cache can make a pass lie. Re-run clean (`python -B`, a fresh tree) before
  believing a surprising result.
- Seen in use: Python 3.11 and rustc 1.95 in the build container; Python 3.14 on the owner's Windows host, where a
  record names rustc 1.96.1. No version is pinned.

## 6. Writing a claim

- **Grade it:** MEASURED, ESTABLISHED, DECLARED, OBSERVED (seen once, outside the gate), or NOT_MEASURED. Give it a
  `does_not_show` boundary and a falsifier that can fail.
- **No scalar scorecards.** Report witnesses side by side.
- **Say where it happened.** "Run here" (the build container) and "on the host" are different claims. Never write a
  host result before the host's own output exists.
- **History is not rewritten.** A dated record stays as written. A record that was wrong is corrected in place with a
  note saying so. Current-state text is kept current.
- **Quote the owner's rulings in his words**, and paraphrase outside sources.
- **A test asserts the apparatus.** Plant the defect and require the refusal. A plant that changes nothing is an
  equivalent mutant, and it can be equivalent only in the fixture's state.

## 7. Before a push

The witness's empty status is not proof of a clean checkout (GHOSTS G36). From the repository's root:

```
git config --show-origin --get-all status.showUntrackedFiles
git status --porcelain=v2 --untracked-files=all
git ls-files -v                          # a lower-case letter or S marks a hidden flag
git rev-parse HEAD '@{u}'
```

The first two should print nothing. Every line of the third should start with `H`. The last should print one commit
twice. Predict a tree from the **pushed** history, not from a working copy: the owner's
history holds host records a build copy may not have (DEVNOTES lesson 74).

## 8. Lessons that cost something

- **Clearing the way hides what stands in it.** A test that hid the graybox's overlay could never find that the
  overlay swallowed the click (lesson 75). Click where a user clicks.
- **Hash whole numbers.** A per-face value interpolated by the GPU is not exact, and a hash of it scattered windows
  into noise (lesson 72).
- **A row about today breaks tomorrow.** Write a row about history, against what an amendment says, not about the
  present (lesson 46, G29).
- **A browser's name for its GPU is a family's name.** Firefox reports many AMD GPUs as "Radeon R9 200 Series, or
  similar".
- **A clock has a step.** Report it; a timing smaller than the step is not a measurement.
- **One author wrote both twins.** Agreement between a program and its reference shows consistency, not truth. The
  owner's literal targets are what stand against a shared mistake (G23, G29, HERMENEUTICS-0).

## 9. Privacy

Record about a host only what its own records establish. Do not write the owner's personal details, hardware or
peripherals into the repository unless he puts them there.
