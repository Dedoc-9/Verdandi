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
| [`docs/CAPABILITY-MATRIX.md`](docs/CAPABILITY-MATRIX.md) | before planning against the engine and studio specification: what exists, graded, its findings, and the agreed order (2026-10-16) |
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
| `art/` | prompted art: the art file, the exporter, the native plaza (`play.py`, a WebGL 2 renderer), the Unreal importer (an optional path), DIRECTOR-0 (scope, ledger, vectors) | `art/check.py`, `art/director.py selftest`, `conform.rs`; no row |
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
| graybox runtime or renderer (`graybox/web/`) | `python graybox/serve.py tactical --selftest`, then `witness` | `30 / 30` and `27 / 27`, exit 0 (a browser opens). The `MEASURED` lines are measurements, not checks |
| the simulation's tick (`graybox/web/sim.js`, `graybox/RULES-1.md`, `graybox/tick_ref.py`) | `python graybox/trace.py run tactical --browser msedge` (or `--expect chromium`), then `python graybox/tick_ref.py verify graybox/build/trace/tactical/chromium.json` and `python graybox/tick_ref.py selftest graybox/build/trace/tactical/chromium.json` | `TICK REFERENCE VERIFIED`, `TICK-REF SELFTEST PASSED`. A change to the tick changes `RULES-1.md`, `sim.js` and `tick_ref.py` together, or the verifier says where they part |
| the input contract (`graybox/RULES-1.md` *The input*, `admit` in `graybox/web/sim.js` and `graybox/tick_ref.py`, `graybox/web/input_cases.json`) | `python graybox/tick_ref.py cases`, then `python graybox/trace.py run tactical --cases --browser msedge` and `python graybox/tick_ref.py cases graybox/build/trace/tactical/cases/chromium.json` | `INPUT CONTRACT HELD BY PYTHON AND THE BROWSER`. A change to what is admitted changes the table, `RULES-1.md` and both validators together, and a new contract version (`INPUT`), never an edit to a case's expected outcome to fit the code |
| rules 2, movers (`graybox/RULES-2.md`, rules 2 in `graybox/web/sim.js` and `graybox/tick_ref.py`, `graybox/web/rules2_cases.json`) | `python graybox/tick_ref.py rules2`, then `python graybox/trace.py run tactical --rules2 --browser msedge` and `python graybox/tick_ref.py rules2 graybox/build/trace/tactical/rules2/chromium.json` | `RULES 2 HELD BY PYTHON AND THE ENGINE`. A change to rules 2 changes `RULES-2.md`, `sim.js` and `tick_ref.py` together, and a value worked by hand is never changed to fit the code: a case whose working was wrong is corrected with its working, and said |
| rules 3, solid walls, targets with a top, push (`graybox/RULES-3.md`, rules 3 in `graybox/web/sim.js` and `graybox/tick_ref.py`, `graybox/web/rules3_cases.json`) | `python graybox/tick_ref.py rules3`, then `python graybox/trace.py run tactical --rules3 --browser msedge` and `python graybox/tick_ref.py rules3 graybox/build/trace/tactical/rules3/chromium.json` | `RULES 3 HELD BY PYTHON AND THE ENGINE`. As rules 2: a change to rules 3 changes `RULES-3.md`, `sim.js` and `tick_ref.py` together; a value worked by hand (or a case's `expect_rules2`, what rules 2 do with it) is never changed to fit the code; rules 1 and 2 stay byte for byte, their tables held again after any change to the file they share |
| ORT-1, the origin moved between ticks (`graybox/ORT-1.md`, `graybox/web/ort.js`, `graybox/ort_ref.py`, `graybox/web/ort_cases.json`) | `python graybox/ort_ref.py`, then `python graybox/trace.py run tactical --ort --browser msedge` and `python graybox/ort_ref.py graybox/build/trace/tactical/ort/chromium.json` | `ORT-1 HELD BY PYTHON AND THE ENGINE`. The two implementations stay written apart (never one from the other); a value worked by hand is never changed to fit the code; never commit a rebase except through `commit` (the bytes, the history and the candidate checked), never let a field of the state or the world in world-space metres go undeclared in the frame tables, and never relax the exactness guard: a rebase that would round is refused |
| the bot's walk (`graybox/WALK-1.md`, `graybox/bot_ref.py`) | `python graybox/bot_ref.py make tactical`, `python graybox/bot_ref.py check graybox/build/bot/tactical-walk.json`, then `python graybox/bot_ref.py selftest graybox/build/trace/tactical/chromium.json` (a trace whose walk is the browser's own bot's) | `BOT TRACE CHECKED`, `BOT-REF SELFTEST PASSED`. A change to the bot changes `WALK-1.md`, `sim.js`'s bot and `bot_ref.py` together, and a new policy is a new version (`walk-2`), never a fix to a recorded walk |
| the simulation's rules (`graybox/web/sim.js`, its arithmetic) | `python graybox/rules_ref.py`, then the self-test above | `RULES REFERENCE PASSED`; `rules-arithmetic` and `math-fence` PASS. A change that alters a tick's numbers is a new rules version (`RULES`), never a fix to the digests |
| an art file, the exporter or the art's checks (`art/`) | `python art/check.py`, `python art/quality.py selftest` | every check and plant PASS; `ART CHECKS PASSED` (a SKIPPED line says why it skipped); `QUALITY SELFTEST 76/76`. Every verification now holds the scene's bytes exact (QUALITY-0: finite, in their one byte form, every field known and bounded, inside the native renderer's budgets) and each brief to its frozen reference in `art/references.jsonl`. A change to the exporter fails that line until a person freezes the new references (`python art/quality.py freeze NAME --note TEXT`, appended, never rewritten); never edit, regenerate or delete a reference to make the line pass, and never freeze a reference the field comparison has not been read for. A scene that grows a field needs `art/quality.py` to grow it too, or it is refused, not passed over (movers grew it in 0226, rules and targets in 0229). The art file's numbers have a grammar of their own (`art/dress.py`, `NUMBER`): never read one with `float()` or `int()` alone. A mover is play: never let an intent add, remove or move one (the scope protocol refuses it, SCOPE-PLAY), and never let a scene be played under rules other than the ones it names (every scene names rules 3 since 0229). The reach ceiling (REACH-1, `art/README.md`) is computed twice, in `art/dress.py` and in `art/check.py`, apart and with the same arithmetic: change both or neither, never with `**` or `pow` for a square root (`math.sqrt`, correctly rounded on every machine), and hold a change to it to a search of the simulation it must stay above |
| the director: the canonical form, scope, the ledger (`art/director*`) | `python art/director.py selftest`, `python art/director.py crashtest`, `python art/director.py racetest`, then `rustc -O art/director/conform.rs -o art/build/conform` and `art/build/conform art/director/vectors.json` | `DIRECTOR SELFTEST PASSED`; `DIRECTOR CRASHTEST PASSED (15 cases)`; `DIRECTOR RACETEST PASSED (32 cases)`; `CONFORMANCE 65 / 65` (`VECTORS 65 / 65` from `python art/director.py vectors`). Every evaluation carries its ADMISSION-0 record (`art/director/contract.py`: rung computed from what changed, certifies, not checked, horizon, trusted, requires) and every admission the evidence it requires (a still of the candidate with its detectors read by the host, or the admission it exactly inverts); never let a model, a provider or a page supply a rung, a record or a detector reading, never drop a name from `EXPECTED_CHECKS` to let a candidate through, and never give the command line's `--still` a picture that is not of the candidate. A change to an expected output in `vectors.json` is a new protocol version, never a fix. Every write of the brief, the ledger, the tags or a map goes through `art/director/durable.py` holding the tree's content lock (`durable.locked`, `ledger.lock_path`); an admission reads the head again under it; every command starts by recovering, and recovery refuses (LEDGER-BUSY) rather than take the lock from a live writer. Never add a writer of those folders that does not hold the lock. LEDGER-SAFE-0 (0245): an event that names the head it was checked against (an evaluation, an admission, an approval) is appended only under the lock and only while the files are the head the ledger replays to and that head is the one it was checked against (`held_head`, `append_checked`; LEDGER-UNLOGGED or HEAD-MOVED, nothing appended); a rebase is recorded only under the lock and only for files that pass the art checks an evaluation runs (REBASE-CHECKS), and replay holds a rebase's text to its parts; a `refuse`, which names no head, is appended as before. Never append an evaluate, admit or approve event by `led.append` directly, and never let a rebase record a brief its checks refuse: one event over a head the ledger does not hold leaves a ledger that replay, and so rebase, refuses for good (MEASURED, 2026-10-16). A layout change is refused while another brief plays its map (SHARED-MAP). A self-test plays in `art/fixtures/selftest/` (`selftest_tree`), never in the working brief, ledger or tags, which are the owner's world and change with his admissions. THROUGHPUT-0 (0236): `Workspace.export` goes through the memo (`memo_call`; `python art/director.py memotest`, `MEMO SELFTEST PASSED` with its four plants caught, and the same rows in `selftest`): never return a kept result without its copy, never keep one without every file it opened and every folder it listed, never key it without the text, and never read a file in the export by a means that raises no audit event (`os.path.exists` and the like) without making it open the file |
| the native plaza (`art/play.py`, `art/web/`) | `python art/check.py`, `python art/play.py --selftest`, then `python art/play.py plaza-night` (and `harbor-lift`, the world with movers) | `ART CHECKS PASSED`; `LIVE SELFTEST 24/24`; the page opens in the studio's editor (STUDIO-3: a click selects, the inspector reads `/object.json`, **P** plays, Esc returns) and plays, and an edit to the brief or an `--intent` file is drawn without a restart; a scene is played under the rules it names (`rules 3` in the page's lower line), and a change to its movers or rules starts a new game. A person judges the picture; nothing hashes it. The shell reads and never writes: its GET routes (`/object.json`, `/validate.json`) bind nothing and make no tag, and whatever it changes goes through play.py's token-held routes; never let a panel move, admit or tag anything by itself, and never show a number the page did not measure (the statistics say *n/a* for what WebGL does not report). Never deliver a new brief, or a change to a brief's sky or air, without looking at a still of it (`play.html?world=NAME&view=VIEW`) and reading its detectors (`python art/quality.py still FILE.png`): the detectors flag a still drawn white and prove nothing, and only a person judges it |
| the studio (`art/studio.py`, `art/providers/`, the studio's parts of `art/play.py` and `art/web/play.js`) | `python art/studio.py selftest`, then `python art/play.py plaza-night --director art/providers/scripted.json` (E target, R pin, Enter summons; Backspace resets the game there) | `STUDIO SELFTEST 78/78`; `python art/play.py --boundary-selftest`: `BOUNDARY SELFTEST 7/7` (HARDEN-0: every request answered, never a reset connection; a request that a page starts always ends; a silent client let go); `python art/studio.py probe art/providers/claude_code.json [--references]` asks a real model (it costs tokens; SHOWN means the model was asked and its answers followed the prompt). A tag names one object by its id and is never moved to another. A provider proposes; nothing it says reaches the world but through the gateway's reading and the director's verdict. Never admit from the gateway without the designer, never pass a prompt to a provider in its arguments or through a shell, and never let a model's command line run with tools. A refusal over HTTP is sent only after the request's body is read (`refuse` in `art/play.py`): answered first and closed, Windows resets the connection and the client loses the answer; and a request's record line is written before the request reads as ended. A director refusal reaches the page as STUDIO-DIRECTOR-REFUSED with the director's own code (`director_code`, 0245); a certificate is written whole (`durable.write`), and every art admission the ledger holds without one is given one at the start, from the ledger alone (`recover_certificates`, which never stops a start) |
| the candidate loop (`art/scene_diff.py`, HELD-0; `host_order`, `none` and the comparison record in `art/studio.py`, COMPARE-0; `/held.json` and `/studio/none` in `art/play.py`; the candidates' cards and Diff mode in `art/web/play.js`) | `python art/scene_diff.py selftest` (`--quick` fewer cases, `--pure` without the launcher; about a minute) | `SCENE-DIFF SELFTEST PASSED: 20 of 20 plants caught` and `HELD SELFTEST 8/8`. What a candidate changed and whether it is held are the host's, computed from the two scenes of the candidate's own evaluation (never the served slot, never the page): never compute M, C or P or a region's verdict in the page, never read a model's words into the order, never call a candidate held whose shape is not ok in its base (stale), and never compare the scene's numbers as doubles (they are the decimals written) |
| a building and its bays (`building` and `bay` in `art/dress.py`, FACADE-0; the scripted director's bays in `art/providers/scripted.py`) | `python art/play.py --facade-selftest` (about a minute) | `FACADE SELFTEST 8/8`. A bay is one piece, named by its place (`building:x0,z0-x1,z1:SIDE-bK-fN`); every piece of a facade stands out from its face by less than FLUSH, so that the envelope's flush rule holds it. Never give a bay a depth, an opening or a mesh here (FACADE-0 is boxes on a box), never let a bay statement name a bay its building does not have, and never let a building stand on a cell that is not rock |
| region-strict admission (`strict` in `art/scene_diff.py`, `strict_check` and the strict admission in `art/studio.py`, the director's own check in `cmd_admit`, STRICT-0) | `python art/play.py --strict-selftest` (about two minutes) | `STRICT SELFTEST 11/11`: eight rows and its three plants caught. The footprint and its verdict are the host's, from the two scenes of the candidate's own evaluation, and checked again at the admission from that admission's evaluation: never take a strict result from a card, a page or a provider, never admit a strict FAIL, never write a strict admission to the ledger without its receipt and inverse receipt, and never let a request that is not strict refuse on its accounts |
| a candidate's cost to the native renderer (`art/impact.py`, `art/impact_model.json`, IMPACT-0) | `python art/impact.py selftest` and `python art/play.py --impact-selftest` | `IMPACT SELFTEST 9/9` and `IMPACT-STUDIO SELFTEST 8/8`, each with its three plants caught. The counts are the renderer's own way of making a frame; when `scene_render.js` changes how it builds its geometry, lights or textures, change `counts` with it and measure again. Never let a verdict, the order or an admission read the impact, never show the estimate without ESTIMATE and its calibration's host and date, never edit `impact_model.json`'s coefficients by hand (they are its rows' least squares, which the self-test computes again), and never put the clock or anything but the request into the preview's seed |
| the preview in motion (`art/motion.py`, PREVIEW-0) | `python art/motion.py selftest` and `python art/play.py --preview-selftest` | `PREVIEW SELFTEST 12/12` and `PREVIEW-STUDIO SELFTEST 14/14`, each with its three plants caught. The state fingerprints are the evidence and the stills' SSIM and PSNR only a look: never let a verdict, the order or an admission read a preview, never call a capture with a still or a state missing replayed, never put the clock into the states, the seed or the archives (the meta's `made_at` is the one clock), and never carry one run's world or state into another. When `graybox/tick_ref.py` or its rules change, the fingerprints change with them: say so in `SEMANTICS` |
| the preview's camera path and its rule (`art/camera.py`, PATH-0), and legibility along it (`art/legibility.py`, LEGIBLE-0) | `python art/camera.py selftest` and `python art/legibility.py selftest` | `PATH SELFTEST 11/11` and `LEGIBLE SELFTEST 6/6`, the first with its four plants caught (FRAME-0's among them), the second its three. The rule is decided exactly (`camera.check`); floats only choose which poses to try, never whether one is clear. Never move a request's path for one candidate (check it against the candidate's scene and say so), never call a path clear that skips its segments, and never let a verdict, the order or an admission read a legibility proxy or present it as what a person perceives. A world added to `art/briefs/` needs its reference frozen by the owner before ART CHECKS pass |
| the flagship's acceptance (`art/flagship.py`, FLAGSHIP-0) and a visual baseline | `python art/play.py --flagship-selftest` | `FLAGSHIP SELFTEST 9/9`, its three plants caught. The procedure asks for evidence the studio does not require (an impact, a framed and verified preview) and stops at the first stage without it, asking nothing further; never let the studio's admission read that evidence, never write `art/visual_baselines.jsonl` except by the owner's `approve` (a person's act, like a freeze), and never treat a real provider's run as this acceptance (it is a rehearsal, OBSERVED) |
| every admission's certificate (`art/certificate.py`, CERT-0) and two edits glued or not (`art/glue.py`, GLUE-0) | `python art/certificate.py selftest` and `python art/glue.py selftest` | `CERT SELFTEST 7/7` and `GLUE SELFTEST 9/9`, each with its three plants caught. Both are exact (text, bytes, sha256), never measured. A certificate is derived from the ledger, never the ledger from it; never call an inverse exact that restores the statements but not the bytes, never make a glue verdict depend on which edit is named first, and never let the studio's admission decide by a glue verdict until the owner rules it |
| the page executed by a test (`art/page_test.py`, `art/web/page_test.html` and `page_test.js`, the channel `/studio/page-test` and the driver's routes in `art/play.py`, PAGE-0) | `python art/play.py --page-selftest` (a browser: on Windows Edge, then Chrome; elsewhere Edge, Chrome or Chromium on PATH; or `--browser EXE` or `VERDANDI_BROWSER`; headless, `--headed` shows it; about two minutes) | `PAGE SELFTEST 16/16`: the flagship's edit made through the page's own controls (Enter, the shape's tag, Strict, Ask, the card's Preview, Admit and Show, the drawer's Undo and Original), four plants through the page and the harness's two caught, and nothing of the browser left. What held each step but the opening is the host's, read from its own state (the request, the ledger, the certificate, the preview's report, the scenes it serves, the stills as PNG); the opening rests on what the page reports (its title, held against the brief's, its director, its canvas); the page reports what it showed and decides nothing. A run ends at once when its page is lost (PageLost: a step not answered, a browser that ended, its deadline passed). Never click through a control something covers (`press` hit-tests its centre first, lesson 75), never serve the driver or answer its channel unless a page test is armed on that server (`hub.page_test`; unarmed, 404 and STUDIO-ROUTE), never count a harness plant caught by any row but the admission's, never let a failed query of what is left read as nothing left, and never read a timing it prints as a measurement of the page. Without a browser the suite fails; there is no skip |
| every self-test of the art layer at once (`art/selftests.py`, THROUGHPUT-0) | `python art/selftests.py` (`--repeat 2` runs the set twice; `--jobs N`, `--only held,studio`) | `ART SELFTESTS PASSED` and its log under `art/build/selftests/`. A suite passes only on its exit status and its summary line both; never add a suite without its summary's pattern, never count a suite that printed no summary, and never let it run or read the gate: it is the art layer's check, which has no row |
| marks and shapes (`art/studio_marks.py`, MARK-0; the shapes' routes in `art/play.py`, `#name` in `art/studio.py`, the Mark & Shape parts of `art/web/play.js`) | `python art/studio_marks.py selftest` (`--pure` without the launcher) | `MARKS SELFTEST 19/19`. A shape is the designer's mark and never the world: its vertices are surface-local integers of millimetres on one face of one box, every predicate on it is exact (integers and fractions, never a float compared), and its status is the host's (ok only when its box is exactly as marked). Never move a shape to another surface or snap a changed one back without the designer, never take a check's result from the page, never let a shape that is not ok reach the director (STUDIO-SHAPE), never read a shape's numbers as doubles (the save's body is read as decimals), and never call a constraint checked that is the designer's words |
| the studio's change transaction (`art/studio_txn.py`, `docs/STUDIO-CONTRACT.md`) | `python art/studio_txn.py selftest` (about two minutes) | `STUDIO-TXN SELFTEST PASSED`: the check over every enumerated crash point with 0 failures and all 16 rules reached, every planted wrong decision caught, the contract's decision table equal to the module's. Change the table in both or neither; a decision that needs a person is SAFE, never a guess |
| the desktop studio (`art/studio_app.py`) | `python art/studio_app.py selftest`; on Windows `python art\studio_app.py shortcut --director art\providers\claude_code.json`, then the icon | `STUDIO APP SELFTEST 12/12` (13/13 on Windows); the icon opens the plaza in a window of its own, and closing it ends play.py, the provider and the browser (the job). Never let it write a key to a file; never start a second studio on one state folder (the lock opens a window on the first) |
| the studio's worlds and queue (`art/studio_queue.py`, the Hub and `seed_worlds` in `art/play.py`, the world and queue parts of `art/web/play.js`) | `python art/studio_queue.py selftest` | `STUDIO-2 SELFTEST 19/19`. Each world in the worlds folder is a tree of its own, written only through its own ledger and content lock; a seeded world is copied whole and kept only if its ledger verifies in the copy; nothing in the queue admits. Never write the checkout from the worlds' code, never let two worlds share a map file, and never append to `queue.jsonl` without the queue's lock. Every request that ends on its own ends in a disposition (REALIZED, UNSUPPORTED, AMBIGUOUS, DECLINED, FAILED): never record an empty answer without one, never let a disposition other than REALIZED evaluate or write anything, never act on a provider's questions or note (they are text), and never serve the studio's token to the launcher or a read-only view (they get the heartbeat token) |
| a patch to the program: its rung (`tools/rung.py`, RUNG-0) | `python tools/rung.py selftest`; for a patch, the classifier the pushed tree holds: `git show origin/main:tools/rung.py > rung.py` outside the checkout (in Windows PowerShell `cmd /c "git show origin/main:tools/rung.py > ..\rung.py"`: PowerShell's `>` writes UTF-16, which Python cannot read as source), then `python rung.py classify origin/main HEAD --repo .` and `python rung.py plants origin/main HEAD --repo .` | `RUNG SELFTEST 22/22`; the report's rung, each file's reason, what the rung needs and every LOOSENS line; `PLANTS HELD`, with no checker said to have stopped early (0242: R5 reads every suite as UTF-8 whatever the console, and a suite that raised is named; 0244: only an exception that ends a suite, not a traceback it logs and goes on from; before it, a Windows console's cp1252 stopped art/check.py at its first brief's number-grammar plant, and R5 compared those 22 rows only; 0245: art/check.py's rows keyed by the world they are printed under, which had made its 202 rows 56 keys, and art/studio.py's bracketed rows that name a plant read, of which R5 had read none; two rows under one key are one row that passes only if both do). The rung is computed from the trusted base's closure and the change's semantics; never write a rung into a commit message or a report as if it were the classifier's, never shorten `ROOTS` or the loosenings it looks for to lower a rung, and never run the patch's own copy to judge the patch |
| the studio's machine probes (`tools/probe/`, docs/STUDIO-CONTRACT.md §11) | on Windows, by the owner: `python tools\probe\edge_app.py`, `job_object.py`, `pointer_swap.py`, `low_integrity.py`, `journal_replay.py` | each ends `PROBE <n>-<name> VERDICT HELD`, `KILLED <criterion>` or `INCOMPLETE`; a KILLED verdict revises the architecture as its criterion says. Off the gate, and never made a gate. They print nothing of the machine but what the verdict needs |
| the state-commitment court (`tools/probe/state_commit.py`, probe 6, DSC-0) | `python tools/probe/state_commit.py`, on any machine: it uses `verify/build/session` from a gate run, or builds one with rustc | `PROBE 6-dsc VERDICT HELD`; KILLED names soundness, agreement or necessity, and a KILLED necessity means the session's content function has to become a tree commitment before anything else is built on it. DSC-0 is a reference and never an authority: nothing in the program reads its roots, receipts or proofs, and it never writes a session. Off the gate, and never made a gate |
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
