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
  host's Firefox. That is consistent with determinism and does not establish it.
- **Gap.** None in the claims. Implementation, if lockstep play is ever wanted: integer or fixed-point movement, as
  the declared arena text proposes.
- **Experiment.** Run the self-test's replay under several engines and CPUs and compare every tick's hash, not only
  the last.
- **A decision?** Yes, before any networked play.

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

## Not searched, so not claimed

- **The graybox's decoration bound:** decoration must stand above the highest eye a player can reach, so no
  decoration lies between an eye and a target.
- **The use of defect-directed plants to check a level converter.**

Neither was compared with the literature. They are not described here as new.
