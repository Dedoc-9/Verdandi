# Research findings — outside sources set against what the repository does

Targeted reading of primary sources, done on 2026-10-09 during the documentation audit (`REPOSITORY-TRUTH.md`). Each
finding names the established concept and where it comes from, and what Verðandi already has. It then gives the kind
of gap, what the source does and does not establish, a finite experiment, and whether the finding merits a separate
decision. Nothing here is implemented, registered or ruled. No novelty is claimed: where nothing matching was found,
the finding says that it was not identified in the sources examined. Two small experiments were run for this file,
and their outputs are given.

## R-1 · Translation validation

- **Source.** A. Pnueli, M. Siegel, E. Singerman, "Translation validation", TACAS 1998, LNCS 1384, pp. 151–166
  ([doi:10.1007/bfb0054170](https://doi.org/10.1007/bfb0054170)). Also Pnueli, Shtrichman and Siegel, ICALP 1998
  ([page](https://www.wisdom.weizmann.ac.il/~verify/publications/1998/pss98.html)). Instead of proving a compiler
  correct once, *each individual translation is followed by a validation phase*, and the validation is fully
  automatic.
- **Here.** `graybox/check.py` is a translation validator for the level converter: it reads the source again with its
  own reader and holds W and C to it, run by run. It does not prove `level.py` correct. DESIGN-IR/DIFF-0 is something
  else: a differential comparison of the shell's compiler with the gate's reference, plus the owner's literal targets
  (HERMENEUTICS-0).
- **Gap.** Documentation only: neither practice was named. The source also shows the limit. A validator is only as
  independent as its reader. One author wrote both of `check.py`'s reader and `level.py`, so a shared misreading
  passes both (the class GHOSTS G29 records for the compiler).
- **Experiment.** Plant the same misreading of one `GRAYBOX 0` statement in both readers and confirm `check.py`
  passes. That would demonstrate the shared-author limit.
- **A decision?** No.

## R-2 · Noninterference is a property of pairs of runs

- **Source.** M. R. Clarkson and F. B. Schneider, "Hyperproperties", Cornell CIS technical report, 2009
  ([pdf](https://ecommons.cornell.edu/bitstream/1813/11660/4/hyperproperties-tr.pdf)); the journal version is in the
  Journal of Computer Security, 2010. *Hyperproperties … are sets of trace properties*, able to express secure
  information flow, *that trace properties cannot.* Noninterference is not a property of individual traces.
- **Here.** Several invariants are of this kind and are already tested with two runs:
  - the tick is never authority (`simtick-equivalence`: the same commands at other ticks give the same head);
  - batching is not meaning (`sessionwalk-batch-invariance`);
  - observers change nothing ("replay stays byte-identical with observers active", `PROGRAM.md`);
  - FULL×2 (two gate runs).

  The graybox's `render-readonly` is weaker. It compares one state before and after frames are drawn: a single run.

  Since 2026-10-10, at the owner's request, the graybox has two-run checks of its simulation's own state.
  `fx-noninterference` steps a twin with the view's feedback swapped beside the original, from states the game
  reaches, and compares every following tick. That is the lockstep form tested from reachable states, after
  Hriţcu et al., "Testing Noninterference, Quickly" (ICFP 2013; [arXiv:1409.0393](https://arxiv.org/abs/1409.0393)).
  `snapshot-resume` and `resume-realm` compare a run with its own resumption. The renderer's paired replay below is
  still open.
- **Gap.** Documentation, plus one possible check. The two-run framing explains why a one-run test cannot witness
  these properties. A stronger graybox check would replay the recorded route twice, once drawing between ticks and
  once not, and compare the hash of every tick.
- **Experiment.** That paired replay, with a renderer planted to write `s.yaw` mid-route. The paired check must catch
  it, and the one-state check should catch it only if the write happens to survive.
- **A decision?** Yes, if the graybox's checks are extended. The sprint rule allows it only when a defect blocks.

## R-3 · Equivalent mutants

- **Source.** Y. Jia and M. Harman, "An Analysis and Survey of the Development of Mutation Testing", CREST technical
  report TR-09-06, King's College London
  ([pdf](https://uio.no/studier/emner/matnat/ifi/nedlagte-emner/INF4290/v11/undervisningsmateriale/MuttestSurvey.pdf)).
  An equivalent mutant is *syntactically different but functionally equivalent to the original program*, and
  detecting one automatically is impossible *because program equivalence is undecidable.*
- **Here.** Already practised. Equivalents are recorded by class and never "fixed" (DEVNOTES lessons 48–49; RUNGS).
- **What the source adds.** A fixture can make a mutant equivalent *in that state*. FPS-VISUAL-0's first plant of a
  state write wrote a value the state already held, because the shot had hit. The DESIGN-EVENT-0 memo plant bit only
  on a parent with a paint and no cell edit after it.
- **Gap.** None in practice. Documentation: a mutant's survival is a fact about the fixture as much as about the
  check.
- **A decision?** No.

## R-4 · The envelope's canonical JSON is not RFC 8785

- **Source.** A. Rundgren, B. Jordan, S. Erdtman, "JSON Canonicalization Scheme (JCS)", RFC 8785, June 2020
  ([rfc8785](https://www.rfc-editor.org/rfc/rfc8785)). JCS:
  - orders member names by their **UTF-16 code units**;
  - emits no whitespace;
  - serialises numbers as ECMAScript does (IEEE-754 doubles);
  - requires I-JSON input.
- **Here.** `verify/envelope.py:canonical` sorts keys by **code point**, as Python's `sort_keys` and Rust's `BTreeMap`
  both do. It allows integers only and uses the saved form's string spelling. The two writers agree with each other
  (`records-twins`).
- **Experiment, run.** On the object `{"｡":1, "\U0001F600":2, "a":3}`:

  ```
  envelope: {"a":3,"｡":1,"\U0001f600":2}
  RFC 8785: {"a":3,"\U0001f600":2,"｡":1}
  same bytes: False
  ```
- **Gap.** Documentation. An outside verifier that assumes JCS computes a different `chain_hash` for any record with
  a key outside the Basic Multilingual Plane. No record has one today. `graybox/level.py:canon` is further still from
  JCS: it writes Python float reprs and allows `NaN`, which is not JSON.
- **A decision?** Only if a format is made public (`BINARY-SDK.md` §12).

## R-5 · FULL×2 is not a reproducible build

- **Sources.**
  - reproducible-builds.org: *A build is reproducible if given the same source code, build environment and build
    instructions, any party can recreate bit-by-bit identical copies of all specified artifacts*
    ([definition](https://reproducible-builds.org/docs/definition/)).
  - The rustc book: `--edition` defaults to `2015`
    ([command-line arguments](https://doc.rust-lang.org/beta/rustc/command-line-arguments.html)).
- **Here.** FULL×2 compares the gate's printed output twice on one tree. It does not compare binaries. The toolchain
  is unpinned: no rustc version, no edition flag, bare `-O`. A rustc version appears only inside some host records.
- **Experiment, run in the build container.** `rustc 1.95.0` built `kernel/main.rs` twice into two paths, and the two
  binaries were byte-identical (sha256 `2387aabd52c6…`). One machine, one compiler: that is not a cross-machine
  result.
- **Gap.** Documentation: FULL×2 establishes repeatable *results*, not reproducible *artifacts*. Implementation, if
  wanted: the gate could print `rustc -V`. That changes the gate's output, so it is a decision.
- **A decision?** Yes, if build provenance ever matters.

## R-6 · Floating point across platforms

- **Sources.**
  - G. Fiedler, "Floating Point Determinism"
    ([gafferongames.com](https://gafferongames.com/post/floating_point_determinism)): the answer is *"yes, if…"*. It
    holds with the same binary, compiler, instruction set and settings. Transcendental functions and fused
    multiply-add are named as sources of divergence.
  - ECMA-262 leaves `Math.sin`, `Math.cos` and the others as implementation-approximated. A proposal to require
    one-ulp accuracy is unsettled ([tc39/ecma262#903](https://github.com/tc39/ecma262/pull/903)).
- **Here.** The certified tree's rules are integers (only `simtick.rs` is fenced for floats). `graybox/web/sim.js`
  uses JS doubles and `Math.sin`, `Math.cos`, `Math.hypot` and `Math.atan2`, and its docs claim replay in one build
  in one page only, which these sources support. The same final replay hash was seen once in Chromium, node and the
  host's Firefox. That is consistent with determinism and does not establish it. What an equal hash covers within
  one page is now checked: the self-test's `hash-coverage`, `fx-noninterference`, `snapshot-resume` and
  `resume-realm` (`graybox/README.md`).
- **Gap.** None in the claims. Implementation, if lockstep play is ever wanted: integer or fixed-point movement, as
  the declared arena text proposes.
- **Experiment.** Run the self-test's replay under several engines and CPUs and compare every tick's hash, not only
  the last.
- **A first measurement, with one engine (2026-10-10).** Two more sources:
  - Factorio's "heavy mode" saves and loads the game every tick to find state that is not saved
    ([Factorio wiki, Desynchronization](https://wiki.factorio.com/Desynchronization)).
  - An open JavaScript physics engine reports `Math.sin` and `Math.cos` hashing differently between two V8 versions
    (node 20 and Chrome 149) and a simulation diverging between them. Its proposed fix is sin and cos built from exactly
    specified operations ([perplexdotgg/bounce#8](https://codeberg.org/perplexdotgg/bounce/issues/8), 2026-08-03).

  The self-test now plays each run in a worker whose `Math.sin`, `Math.cos` or `Math.hypot` is off by its last bit
  at every call: a counterfactual engine, made without a second browser. In the build container, in Chromium and again
  under node, the tactical walk's state parted from the page's at tick 1172 of 1787. It ended 2.8 × 10⁻¹⁴ m away, with
  the final hash different and no cell, footing or hit changed; the fight did not part at all. MEASURED, this engine,
  these runs. The step's displacement changed in its last bit on about a third of the ticks (590 of 1787, under node).
  Added to a position near 50 m it was almost always rounded away, but once a rounding went the other way the bits
  stayed apart. So the game's behaviour held while its bits did not, and a bitwise replay across engines would fail
  on one such rounding. That argues for the gap's remedy, exact arithmetic in movement, over a looser comparison: a
  difference that persists can later meet a threshold (a cell edge, a collision's halving), which these runs did not
  show and do not exclude.
- **On the owner's machine (2026-10-10).** The self-test ran in the browser `serve.py` opened there; the output does
  not name it. It passed 27 / 27 and 24 / 24, and every check's line matched the container's, down to the replays'
  last hashes `91350c39A` and `ce819a52A`. Four of the eight MEASURED lines differed:

  | map | counterfactual | build container (Chromium) | the owner's machine |
  |---|---|---|---|
  | tactical | `Math.cos` | parted at tick 1174, 2.8 × 10⁻¹⁴ m | parted at tick 1077, 7.1 × 10⁻¹⁵ m |
  | tactical | all three | parted at tick 1172, 2.8 × 10⁻¹⁴ m | never parted |
  | witness | `Math.sin` | never parted | parted at tick 377, 1.4 × 10⁻¹⁴ m |
  | witness | all three | parted at tick 377, 1.4 × 10⁻¹⁴ m | never parted |

  The other four lines were the same on both. What follows, from the code:
  - Each line's ticks are a function of two things only. One is the bits the engine's `Math` returns at the arguments
    the run passes. The other is operations whose results the language fixes exactly: +, −, ×, ÷, `%`, comparisons,
    `Math.floor`, `Math.min`, `Math.max`, `Math.abs` and the DataView bit flip.
  - If the two engines' `sin`, `cos`, `hypot` and `atan2` had returned the same bits at every one of those arguments,
    all eight lines would be the same. (The walk's recorded inputs come from a bot that calls `atan2` and `hypot`.)
  - They are not the same. So on at least one argument, one of these functions returned different bits on the two
    machines. Which one is not established.
  - Yet the unperturbed replays ended with equal hashes.

  So an equal final hash across two browsers is weaker evidence than it looked. A difference in `Math` was present,
  and rounding absorbed it, in these runs. OBSERVED once, on two maps; the inference rests on the step calling no
  other function whose result the language leaves to the engine.
- **A trace, in the build container (2026-10-11).** By the owner's ruling, a small experiment apart from the self-test
  (`graybox/trace.py`). It logs every call of the four functions with its arguments' and result's bits, every tick's
  input and every tick's snapshot, and compares two traces argument by argument. Node 22.22 (V8 12.4) against Chromium
  141 (V8 14.1). The node trace ran the same worker file under node, in a harness of the build container's that is not
  committed:

  | map | `Math.sin` | `Math.cos` | `hypot`, `atan2` | inputs and states |
  |---|---|---|---|---|
  | tactical | different on 5 of 745 arguments | different on 2 of 745 | the same on every common argument | the same at every tick of both runs |
  | witness | different on 3 of 670 | different on 7 of 670 | the same on every common argument | the same at every tick of both runs |

  Every difference was one ulp. MEASURED, these two engines, these runs. The first differing call came while the walk
  was being recorded, and rounding absorbed every difference before it reached an input or a state. This is the same
  kind of difference the owner's run implied, now with its function and argument named. The same trace from the
  owner's browser, compared with the container's, would name the function behind his four lines.
- **The trace from the owner's machine (2026-10-11).** Firefox 157 on his machine, against the container's Chromium 141,
  on the tactical map, compared by `trace.py compare`:

  | function | arguments both runs passed | results that differ |
  |---|---|---|
  | `Math.hypot` | 3,523 | 943, each by one ulp (for one: 1.0 in Firefox, 1.0000000000000002 in Chromium) |
  | `Math.sin` | 745 | 1, by one ulp, at 2.8529933382462254 (bits `4006d2ee2bdbc988`) |
  | `Math.cos` | 745 | none |
  | `Math.atan2` | all | none |

  The first differing call was the 2,386th, while the walk was being recorded, and it was a result, not an argument:
  `hypot(0.14834045293008993, -0.9889363528683207)`, 1.0 in Firefox and 0.9999999999999999 in Chromium. Every input
  and every state was the same at every tick of both runs. OBSERVED once, one run in each engine, these two engines.
  - What it shows. Between these two engines `hypot` differs at about a quarter of the arguments these runs pass,
    where V8 against V8 showed none, and `sin` at one; every difference is one ulp, and rounding absorbed all of them
    before they reached an input or a state.
  - What it does not show. Why four of his MEASURED lines differed on 2026-10-10. Those ran in the browser `serve.py`
    opened, which the output did not name; that this trace explains them is an inference, and R-6's cross-machine
    finding stays what it was: observed once.
  - A remedy, for the owner to decide (not done). `Math.sqrt` and the four operations are exactly specified, so
    `Math.sqrt(a * a + b * b)` in place of `Math.hypot(a, b)` would make those calls the same bits in every engine at
    the magnitudes the game uses; `sin`, `cos` and `atan2` would need forms built from exactly specified operations
    (as perplexdotgg/bounce#8 proposes). Either changes the simulation's numbers, and so the recorded replays' hashes.
- **The remedy, by the owner's ruling (2026-10-11).** *"Investigate and implement the deterministic math layer now."*
  He ruled out the naive form: *"Simply replacing `hypot` with `sqrt(a*a+b*b)` is not sufficient: `sqrt` may itself be
  platform-dependent at the bit level, and the naive expression has different overflow and underflow behavior."* On
  `sqrt` the sources disagree: a 2017 proposal to the specification ([tc39/ecma262#903](https://github.com/tc39/ecma262/pull/903))
  says *"Math.sqrt is defined to have correct rounding"*, while a survey of the specification
  ([uhyo, zenn.dev](https://zenn.dev/uhyo/articles/javascript-math-accuracy?locale=en)) lists `sqrt` among the
  implementation-approximated functions. Rules 1 therefore use none of them: fdlibm's sine, cosine and atan2 built from
  the four operations, and square roots by an integer square root in BigInt, correctly rounded, with hypot's squares
  summed exactly (no intermediate overflow or underflow). Measured in the build container: the five functions give the
  same bits under node 22, in Chromium 141 and in CPython over 20,000 arguments each; on the same inputs, node and
  Chromium reach the same state at every tick of three runs under rules 1, and call no engine function. Under rules 0
  they still differ in `sin` and `cos`. Firefox: NOT MEASURED until the owner's run (ROADMAP, DET-MATH-0).
- **Firefox 157, on the owner's machine (2026-10-11).** Its self-test passed `rules-arithmetic`: SpiderMonkey's
  results for the rules' five functions on 20,000 arguments are CPython's, bit for bit. Its own `Math` against the
  rules' on those arguments: `sin` different on 70 of 4,000, `cos` 62, `hypot` 693, `atan2` and `sqrt` none (V8 14.1's,
  in the container: 123, 108, 1,023, 0, 0). Its trace's digests of every tick's state under rules 1 equal the
  container's Chromium 141 and node 22 on the same inputs; under rules 0 the stress run's do not. OBSERVED once, across
  two machines, at the level of a digest. The owner's ruling keeps cross-browser equivalence NOT ESTABLISHED until a
  field-level comparison of Firefox and Chromium on one machine; the run meant for it played Firefox twice.
- **Firefox 157 against Edge 155, on one machine (2026-10-11).** The owner's machine, the tactical map, both browsers
  playing the runs his Firefox had recorded, each trace accepted from the engine family `--browser` named:

  | function, rules 0 | arguments both runs passed | results that differ |
  |---|---|---|
  | `Math.sin` | 4,307 | 103 |
  | `Math.cos` | 4,307 | 98 |
  | `Math.hypot` | 4,084 | 1,414 |
  | `Math.atan2`, `Math.sqrt` | not called (the runs were given, so no bot ran) | |

  Each difference shown was one ulp. The first differing call was the 1,424th, at the walk's tick 475, in a result:
  `hypot(0.14834045293008993, -0.9889363528683207)`, 1.0 in Firefox and 0.9999999999999999 in Edge, the argument
  and the split the container's Chromium 141 had shown. Under rules 0 the walk's and the fight's states were still the
  same at every tick, and the stress run's parted at tick 490, in `x`, by one ulp. Under rules 1 neither engine called
  its `Math`, and every snapshot of the three runs was the same bytes at every tick. MEASURED once, one machine, these
  two engines.
  - What it shows. The machine is the same, so the rules-0 differences are the engines'. A third of `hypot`'s results
    differ between these two, and still rounding absorbed every difference on the walk and the fight; only the stress
    run, which slides along walls, kept one. So an equal state on most runs is weak evidence that two engines agree,
    which is why the rules' arithmetic is held result by result (`rules-arithmetic`, `rules_ref.py`) and not by runs
    alone. Rules 1 removed every such difference on these runs.
  - What it does not show. The witness level, another machine's Firefox, JavaScriptCore, or other builds of either
    engine; that either engine has no defect in the operations rules 1 use.
- **The Python walk in both, the same machine (2026-10-11).** Firefox 157 and Edge 155 played the walk `bot_ref.py`
  made (1,787 ticks). Under rules 0 `Math.cos` differed on 1 of 678 common arguments and `Math.hypot` on 255 of 677, and
  every state was still the same; under rules 1 every state was the same, and the Python tick's. OBSERVED once.

## R-7 · A browser's clock

- **Sources.** The HR-Time resolution as MDN gives it
  ([mirror](https://docs.w3cub.com/dom/performance/now)): 5 µs in cross-origin-isolated contexts, 100 µs otherwise.
  Firefox's history is 20 µs, then 2 ms (59), then 1 ms (60).
- **Measured here.** On the host, Firefox 157 stepped 1 ms without isolation. With the COOP/COEP headers 0178 added,
  the page reported 0.0200 ms. Headless Chromium in the container reported 0.0050 ms.
- **Gap.** Closed by 0178 (isolation, batches and the printed step). Documentation: a timing smaller than the printed
  step is not a measurement.
- **A decision?** No.

## R-8 · A WebGL renderer string is not the hardware

- **Sources.**
  - Firefox's renderer sanitizer tests
    ([TestSanitizeRenderer.cpp](https://searchfox.org/firefox-main/source/dom/canvas/gtest/TestSanitizeRenderer.cpp))
    map a Radeon RX 5700, an RX 460, an RX Vega, a Radeon Pro 5300M and the Renoir and Rembrandt APUs all to
    *"Radeon R9 200 Series, or similar"*.
  - MDN, [WEBGL_debug_renderer_info](https://developer.mozilla.org/en-US/docs/Web/API/WEBGL_debug_renderer_info).
- **Here.** The 0179 and 0180 host records named the GPU from that string. Corrected in this pass: the string
  establishes an AMD GPU through ANGLE on Direct3D 11, and the model is not established.
- **Gap.** Documentation, corrected.
- **A decision?** No.

## R-9 · Pointer Lock 2.0

- **Source.** W3C, Pointer Lock 2.0, Working Draft of 25 February 2026
  ([TR](https://www.w3.org/TR/pointerlock-2/)):
  - `requestPointerLock()` returns a `Promise`.
  - It rejects, firing `pointerlockerror`, when the document is unfocused, or when there is no transient activation
    and the page has not released a lock itself.
  - `unadjustedMovement: true` asks for movement without the platform's acceleration.
- **Here.** 0178 asks from either the overlay or the view, and shows a rejection.
- **What the source adds.** The graybox does not ask for `unadjustedMovement`, so the operating system's pointer
  acceleration shapes the look. That bears on feel, which no record claims. The draft is under active development.
- **Experiment.** Request the lock with and without `unadjustedMovement`, then compare the yaw produced by one
  recorded physical sweep.
- **A decision?** Yes, as an input-feel choice.

## R-10 · What Git's status cannot see

- **Source.** [git-update-index](https://git-scm.com/docs/git-update-index.html). With assume-unchanged, *the user
  promises not to change the file*, and Git will *omit any checking and assume it has not changed*. With skip-worktree,
  Git treats the file as unchanged. `git ls-files -v` shows the bits.
- **Here.** GHOSTS G36. The direct Git-state check the owner asked for uses `git ls-files -v` and `--untracked-files=all`.
- **Gap.** None; the source supports the ruling.
- **A decision?** No.

## R-11 · The aliasing model and G1

- **Sources.**
  - R. Jung, H.-H. Dang, J. Kang, D. Dreyer, "Stacked Borrows: An Aliasing Model for Rust", POPL 2020
    ([page](https://plv.mpi-sws.org/rustbelt/stacked-borrows/)).
  - "Tree Borrows", PLDI 2025 ([pdf](https://iris-project.org/pdfs/2025-pldi-treeborrows.pdf)).

  Both are operational aliasing models: a program that breaks one has undefined behaviour.
- **Here.** `kernel/fast.rs` shares a framebuffer across scoped threads through a raw pointer (G1, graded SOUND?).
  BEARING-FAST-0 took G1's remedy instead: disjoint row bands through `split_at_mut`, with no `unsafe`.
- **Gap.** Implementation, unverified. The facing emit has never been run under an aliasing checker. Byte identity
  shows its output on the corpus, for this compiler; it does not show the absence of undefined behaviour.
- **Experiment.** Run the threaded emit on a small frame under Miri, with both models.
- **A decision?** Yes. It touches a pinned file only if the code changes; running the check changes nothing.

## R-12 · Records and supply-chain attestations

- **Source.** SLSA and in-toto ([slsa.dev, 2023](https://slsa.dev/blog/2023/05/in-toto-and-slsa)). in-toto
  statements carry predicates such as SLSA provenance, which records how an artifact was built. Source and test
  claims are other predicates.
- **Here.** RECORD-0 records carry provenance, a claim class, a validity scope and forbidden interpretations. That is
  more epistemic structure than a provenance predicate, but there are no signatures. G16 and G20 already say a seal
  is a hash, not authorship.
- **Gap.** None for the claims made. Authenticity is absent by design and stated so.
- **A decision?** Only if records are to be trusted by a third party.

## R-13 · AGENTS.md

- **Source.** [agents.md](https://agents.md/): a plain-Markdown file at the root of a repository that briefs coding
  agents. In a tree of them, *the closest AGENTS.md to the edited file wins*, and the user's own instructions override
  it.
- **Here.** `AGENTS.md` was added at the root in this pass. It points at the documents and states the rules that
  reading them alone could miss.
- **A decision?** No.

## R-14 · Referring to the objects of a scene, for a language model

Read on 2026-10-11, after the owner tried STUDIO-0 and asked how to name an object to the director.

- **Sources.**
  - "Chat-Scene: Bridging 3D Scene and Large Language Models with Object Identifiers", NeurIPS 2024
    ([pdf](https://proceedings.neurips.cc/paper_files/paper/2024/file/cebbd24f1e50bcb63d015611fe0fe767-Paper-Conference.pdf)).
    Each object of a scene gets an identifier token (`<OBJ013>`); a question names objects by it and the model answers
    by naming identifiers, instead of describing objects in words, which is cumbersome and ambiguous.
  - "SceneCraft: An LLM Agent for Synthesizing 3D Scene as Blender Code", 2024
    ([arXiv 2403.01248](https://arxiv.org/html/2403.01248v1)). A scene is a graph of assets and relations (proximity,
    alignment, parallelism); each relation becomes a scoring function and a solver places the assets; a vision model
    reviews a render against the request and the script is revised. Reported: a constraint passing score of 88.9
    against 5.6 for the baseline.
  - "ScanEdit: Hierarchically-Guided Functional 3D Scan Editing", 2025 ([arXiv 2504.15049](https://arxiv.org/html/2504.15049v1)).
    A hierarchical scene graph (on top of, facing, against a wall); a model proposes placements and their relations,
    which become losses (support, against a wall, collision) that an optimiser enforces.
- **Here.** STUDIO-0 sends the selected piece's id and its statement, nothing in metres, and one piece at most. The
  scene's pieces are axis-aligned boxes in metres (`x` east, `z` south, `y` up), and the director checks every
  candidate's scope. The art language can say a canopy's height, corners, depth, ribs and lights, and nothing that
  joins two pieces.
- **Gap.** Interface. A designer cannot name a second piece, and a model is not told where anything is.
- **What the sources do not establish.** That identifiers make a model's edits right: they make its references
  unambiguous. That a render can replace geometry: SceneCraft uses both.
- **Experiment.** STUDIO-1 (the owner's ruling): tags and pins, the pieces' bounds and measured relations in the
  request, and a probe that reports, for each candidate, which tagged pieces it changed.
- **A decision?** Made: his ruling of 2026-10-11 (`docs/ROADMAP.md`, STUDIO-1).

## Not searched, so not claimed

- **The graybox's decoration bound:** decoration must stand above the highest eye a player can reach, so no
  decoration lies between an eye and a target.
- **The use of defect-directed plants to check a level converter.**

Neither was compared with the literature. They are not described here as new.
