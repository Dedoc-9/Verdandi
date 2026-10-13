<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Verðandi Studio — the architecture decision and the development plan (STUDIO-APP-0, declared)

**Status.** A plan, by the owner's direction of 2026-10-12, amended the same day after three reviews he brought were
checked against primary sources (§13); nothing here is built, nothing enters the certified gate, and no pinned
source, oracle file or registered entry is touched by it. Research was done first (its sources are
cited where they bear weight), the architecture was decided second, and this document was written third. The
inventory it stands on was read from the source at HEAD `58917b7` (2026-10-12), with `path:line` references; the
web sources were read on 2026-10-12 and are marked VERIFIED (a primary source, cited) or INFERRED (an inference from
one). **The interfaces and the change transaction are frozen in [`STUDIO-CONTRACT.md`](STUDIO-CONTRACT.md)** (the
same day, after a second review); where the two differ, the contract governs, and this plan keeps the research and
the reasons.

**His direction, in his words.** *"The next objective should be a runnable Verðandi Studio, not another narrowly
scoped rung."* *"The shift is from proving individual capabilities to building an executable application that can
continually improve without losing its ability to launch, edit, and play the world."* Two requirements, *"related,
but they should not be conflated"*: progressive development and recursive self-improvement, the second requiring
*"an explicit update and rollback mechanism, not just a prompt that edits source files."* The crucial decision:
*"Keep the studio that is running separate from the studio being built."* *"The model must not be able to overwrite
the running executable or promote its own changes without the update supervisor's approval."* *"Packaging is a
deployment step; replacing the current rendering architecture is a separate decision."* *"The existing 251-row gate
remains a regression signal, not the definition of the product."* On scope: *"a rung would be a waste on only a
simple feature like that... it should be in a rung batched with other updates"*; *"prioritize larger rungs and
adding/batching many features per rung when possible."* On method: *"be liberal with custom theorem mixing and be
pioneering. consider ACCT as one of many potential candidates. when faced with design forks consider producing both
when both are useful and robust; prioritize those traits with elegance."* And the operators he named for hardening a
theorem — relational (`<`, `>`, `<=`, `>=`) for boundaries and ordering, boolean (`and`, `or`, `not`) for composing
predicates, identity (`is`, `===`) for *the same thing* against equality for *an equal thing*, and nullish
assignment (`??=`) for *assign only if unset* — are used below as the vocabulary of the protocol's clauses.

**His product reference.** A screenshot of Unreal Editor (a park with a pavilion, café tables and umbrellas,
trees; the viewport in Play-in-Editor; an Outliner of 836 actors with a search box; a Details panel with the
selected actor's transform; a Content Drawer and Output Log). The studio's workspace below is drawn toward that
shape — a viewport that plays, an outliner, a details pane, a log — without copying the engine.

---

## 1. Current state, read from the source

| area | state | evidence |
|---|---|---|
| The live plaza: a std-lib `http.server` on 127.0.0.1 serving a WebGL 2 page and the graybox simulation, recompiling edited files in a fresh process, swapping scenes in place without touching the game | **implemented** | `art/play.py` (1,418 lines); files served at `80-84, 481-509`; watcher and `--emit` child at `303-372`; COOP/COEP and `no-store` headers at `473-479` |
| The director gateway: a provider command with no shell, the request on stdin, time and output limits, the whole process tree killed on cancel; the response read whole; candidates evaluated, drawn, admitted, rejected, undone through the ledger; every request recorded | **implemented** | `art/studio.py:171-247, 266-315, 596-605, 708-782`; `STUDIO SELFTEST 51/51` |
| References: tags on objects, pins, geometry and relations measured from the scene, each candidate's touches | **implemented**, tags **in memory only** (lost when play.py stops) | `art/studio.py:22-25, 346-350`; `art/studio_refs.py`; `art/STUDIO.md` "What is not shown" |
| Providers: a scripted stand-in; Claude Code's CLI (tools off, no session, schema, a session offering tools refused); the Anthropic Messages API | CLI **implemented and measured** on Linux and on the owner's Windows machine; API **broken on every current model** (see §2.5) | `art/providers/claude_code.py:81-87, 122-161`; `art/providers/anthropic_messages.py:53` sends `tool_choice: {"type": "tool"}` |
| The content transaction kernel: canonical intents, head = sha256 of three parts, scope verdicts CLEAN / LEAKAGE / REFUSED over declared vs realized addresses, early cutoff by content digest, a hash-chained append-only ledger, replay-defined verification, a std-only Rust second implementation of 62 vectors | **implemented** (DIRECTOR-0) | `art/director/intent.py:122-148, 163-166`; `art/director/scope.py:23-47, 252-255`; `art/director/ledger.py:4-10, 55-69`; `art/director.py:306-340, 388-456`; `art/director/conform.rs` |
| Crash-safe writes of the authoritative content files | **missing**: the brief is written with a plain `open(ws.art, "wb")` and the ledger appended with `open(path, "ab")`, no flush, no fsync, no rename | `art/director.py:331`; `art/director/ledger.py:50`; contrast `shell/livesession.rs:303-313, 517-562` (fsync per record; temp, `sync_all`, `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`) and `design/design.py:94-100` (`os.replace`) |
| A durable, recoverable session with death-point courts | **implemented in the shell** (LIVE-SESSION-0, ADMIT-0): a journal flushed per record, a torn tail dropped, a write-through seal, a loader that classifies; `admit-crash` kills the run at eight points and checks what is left loads to the parent's or the child's head | `shell/livesession.rs:4-47`; `verify/verify.py` rows `admit-crash`, `livesession-recover`, `livesession-classify` |
| A window the studio could live in | **not a candidate**: `shell/win32.rs` is a borderless 1920×1080 GDI presenter with raw mouse input, compiled only with `--cfg shell_window`, an instrument of the kernel's framebuffer; the plaza is a browser page needing WebGL 2 with `EXT_color_buffer_float`, pointer lock and `crypto.subtle` | `shell/win32.rs:1574-1581`; `shell/main.rs:117-119`; `art/web/scene_render.js:420-423`; `art/web/play.js:41-62, 391` |
| Launch and lifecycle | **missing**: launch is a shell command; the browser is whatever `webbrowser.open` picks; the port is ephemeral unless `--port`; the only stop is Ctrl+C (no signal handler, no stop endpoint, no PID file); `--root` is not forwarded to the `--emit` child | `art/play.py:593, 601-610, 225-226` vs `574-577` |
| Installer, shortcut, version file, updater, supervisor, packaging | **none** (searched by name and content: no `.msi`, `.msix`, `.iss`, `setup.py`, `pyproject`, `.bat`, `.ps1`, `Cargo.toml`, `VERSION`) | the inventory of 2026-10-12 |
| Build system | bare `rustc -O`, no Cargo, no crates; Python standard library only; the gate stops growing; 58 pinned sources; `oracle/` frozen | `docs/CORE.md` §2; `AGENTS.md:46-68`; `README.md:17-32, 63-64` |
| `graybox/serve.py` | hosts `graybox/web/*` and maps, writes nothing, watches nothing; **must not host the studio** (the owner's ruling, BOUNDARIES row) | `graybox/serve.py:4-18`; `docs/BOUNDARIES.md:36` |
| Self-tests the studio can reuse as its contract, off the gate | `STUDIO SELFTEST 51/51` (26 s), `LIVE SELFTEST 13/13` (7 s), `ART CHECKS PASSED` (33 rows, 4 s), `DIRECTOR SELFTEST PASSED` (10 s), `CONFORMANCE 62/62`, `DESIGN TOOL PASSED 17` (15 s); the graybox page's 30/30 and 27/27 need a browser; the gate's 251 rows run on the owner's host | re-run 2026-10-12 |
| Uncommitted changes | none at HEAD `58917b7`; the owner's admissions #24–#27 of 2026-10-12 were discarded by his `git checkout` | `git status` |

**Uncertain.** Whether the owner accepts any packaging-time tool outside the repository (an installer builder, a
Microsoft-authored loader DLL): no ruling exists. Whether his machine's Edge is intact: assumed, not asked.

---

## 2. Research findings (what the sources establish)

### 2.1 Windows delivery

- **Microsoft Edge in application mode.** `--app=URL`, `--user-data-dir`, `--window-size`, `--window-position`,
  `--window-name`, `--no-first-run`, `--no-default-browser-check` are defined Chromium switches (VERIFIED:
  [chrome_switches.cc](https://chromium.googlesource.com/chromium/src/+/HEAD/chrome/common/chrome_switches.cc)).
  Chromium's process singleton is "named according to the user data directory, so we can be sure that no more than
  one copy of the application can be running at once with a given data directory" (VERIFIED:
  [process_singleton.h](https://chromium.googlesource.com/chromium/src/+/main/chrome/browser/process_singleton.h)):
  a **private `--user-data-dir` is what gives the studio a browser process of its own** instead of a window of the
  user's running Edge (INFERRED). Microsoft documents only kiosk mode, which runs InPrivate and blocks F12 (VERIFIED:
  [kiosk mode](https://learn.microsoft.com/deployedge/microsoft-edge-configure-kiosk-mode)); `--kiosk` is the wrong
  flag for a tool whose designer needs DevTools. Edge is end-user-removable **only in the EEA** (VERIFIED: Windows
  Insider blog, 2023-11-16; Windows blog, 2025-06-02), and "Microsoft Edge can be uninstalled without causing a
  problem for WebView2" (VERIFIED: [WebView2 end-user FAQ](https://learn.microsoft.com/en-nz/Microsoft-edge/webview2/concepts/end-user-faq)).
  Not established by any source: whether `msedge.exe` with a private profile exits when its last `--app` window
  closes (Edge's startup boost is the suspect), and whether pointer lock works in `--app` windows (parity with the
  browser is INFERRED). Both are the first experiment (§8).
- **WebView2.** The runtime is part of Windows 11 and on "the vast majority" of Windows 10; embedding is a plain DLL
  export (`CreateCoreWebView2EnvironmentWithOptions` in `WebView2Loader.dll`) plus COM interfaces under an STA
  (VERIFIED: [distribution](https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution),
  [webview2-idl](https://learn.microsoft.com/zh-cn/microsoft-edge/webview2/reference/win32/webview2-idl)). Pointer
  lock works in HWND hosting, is broken in visual hosting, and has an open "Blocking" jitter bug with sporadic
  `movementX/Y` jumps that the same demo in Edge does not show (VERIFIED:
  [#4968](https://github.com/MicrosoftEdge/WebView2Feedback/issues/4968),
  [#4084](https://github.com/MicrosoftEdge/WebView2Feedback/issues/4084)). Feasible from std-only Rust with
  hand-written vtables, about a thousand lines (INFERRED). pywebview needs `pythonnet` and .NET (VERIFIED:
  [pywebview](https://pywebview.flowrl.com/guide/installation.html)); Tauri needs a crate graph and MSVC and its
  updater "must be signed" (VERIFIED: [Tauri v2](https://v2.tauri.app/start/prerequisites/),
  [updater](https://v2.tauri.app/plugin/updater/)); Electron ships Chromium and Node. Each of the three violates the
  charter's std-only rule in shipped code.
- **Python.** The python.org embeddable package is "(almost) fully isolated from the user's system" through a `._pth`
  file, ships no pip or Tcl/Tk, and is meant to be launched by "a batch file or generated shortcut" or "a specialized
  executable as a launcher" (VERIFIED: [Using Python on Windows §4.4](https://docs.python.org/3/using/windows.html)).
  PyInstaller one-file unpacks to `%TEMP%\_MEIxxxxxx` each run and warns against administrator privileges; Nuitka
  warns its default builds "might be recognized by some AV vendors as malware" (VERIFIED: their manuals). With no
  third-party package to collect, neither adds anything a small launcher does not.
- **Installation and signing.** Per-user installation is Microsoft's recommendation (VERIFIED:
  [Application Registration](https://learn.microsoft.com/windows/win32/shell/app-registration)); Inno Setup's
  `PrivilegesRequired=lowest` with `{autopf}` installs under `%LOCALAPPDATA%\Programs` without UAC (VERIFIED:
  [Inno](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm)); MSIX packages "must be signed"
  (VERIFIED: [MSIX overview](https://learn.microsoft.com/en-us/windows/msix/overview)). A desktop shortcut needs no
  tool: `WScript.Shell.CreateShortcut` is inbox COM from PowerShell (VERIFIED: Microsoft's scripting reference).
  EV certificates no longer bypass SmartScreen (2024); Azure Artifact Signing is about $9.99/month and builds
  reputation over releases; unsigned binaries get "Windows protected your PC" (VERIFIED:
  [code signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)).
- **Clean-machine testing.** Windows Sandbox: Pro/Enterprise/Education only, pristine and disposable, vGPU on by
  default (VERIFIED: [overview](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-overview)).
  Its image derives from the host, so Edge and WebView2 are present; their absence must be simulated.

### 2.2 Supervision and atomic promotion

- **Job objects.** "If the job has specified the JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE flag, closing the last job object
  handle terminates all associated processes"; children join the job by default; "once a process is associated with
  a job, the association cannot be broken"; nested jobs since Windows 8 (VERIFIED:
  [Job Objects](https://learn.microsoft.com/nl-nl/windows/win32/procthread/job-objects),
  [Nested Jobs](https://learn.microsoft.com/en-ie/Windows/Win32/procthread/nested-jobs)). Terminating a process
  "does not terminate any child processes" (VERIFIED: [Terminating a Process](https://learn.microsoft.com/en-ie/Windows/Win32/procthread/terminating-a-process)),
  which is why the gateway's `taskkill /T` is a best-effort walk, not a guarantee. The race-free sequence is create
  job, set limits, `CreateProcess(CREATE_SUSPENDED)`, assign, resume (VERIFIED: The Old New Thing). Python's
  `subprocess` can send `CTRL_BREAK_EVENT` to a `CREATE_NEW_PROCESS_GROUP` child (VERIFIED: [subprocess docs](https://docs.python.org/3/library/subprocess.html)).
- **Atomic replacement.** CPython's `os.replace` on Windows is `MoveFileExW(src, dst, MOVEFILE_REPLACE_EXISTING)` —
  no write-through (VERIFIED: the CPython commit). `MOVEFILE_WRITE_THROUGH` means "the function does not return
  until the file is actually moved on the disk" (VERIFIED: [MoveFileExA](https://learn.microsoft.com/pl-pl/windows/desktop/api/WinBase/nf-winbase-movefileexa)).
  `ReplaceFile` has three documented partial-failure states and its write-through flag "is not supported"
  (VERIFIED: [ReplaceFileW](https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-replacefilew)).
  Transactional NTFS is deprecated (VERIFIED: [Alternatives to TxF](https://learn.microsoft.com/sv-se/windows/win32/FileIO/deprecation-of-txf)).
  Microsoft states nowhere that an NTFS rename is crash-atomic; Java, CPython and Chromium rely on it (gap, carried
  as an axiom in §5). Windows has no directory fsync; the journal is pre-created so appends extend an existing
  entry (INFERRED from ALICE).
- **A running executable** cannot be overwritten or deleted while it has "outstanding image sections", but can be
  renamed aside (VERIFIED: [WDK rename processing](https://learn.microsoft.com/en-sg/WINDOWS-HARDWARE/DRIVERS/ifs/rename-and-hard-link-processing));
  a directory cannot be renamed while any file in it is open or any process has its working directory inside it
  (VERIFIED: [Velopack](https://docs.velopack.io/packaging/operating-systems/windows)); Chrome sets the working
  directory to the exe's directory on relaunch for that reason (VERIFIED: `upgrade_util_win.cc`).
- **The proven shapes.** Android A/B marks the slot unbootable, switches, then `markBootSuccessful` only after
  verification (VERIFIED: [AOSP](https://source.android.com/docs/core/ota/ab)); ChromeOS counts `remaining_attempts`
  down to 6 and falls back (VERIFIED); NixOS repoints a profile symlink "atomic on Unix" and `--rollback` repoints it
  back (VERIFIED: [Nix profiles](https://nix.dev/manual/nix/2.34/package-management/profiles)); OSTree stages under
  a directory named after the boot id and fsyncs files and directories before swapping (VERIFIED); systemd keeps the
  tries counter in the entry's *filename* and blesses by rename after `boot-complete.target` (VERIFIED:
  [AUTOMATIC_BOOT_ASSESSMENT](https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT)); Squirrel and Velopack keep `app-x.y.z`
  sibling directories behind a stable stub (VERIFIED); the Chromium updater keeps versioned instances, qualifies a
  new one only by running it against a qualification app, and recovers an interrupted activation from a flushed
  "swapping" bit (VERIFIED: [design doc](https://chromium.googlesource.com/chromium/src.git/+/HEAD/docs/updater/design_doc.md));
  Firefox's CVE-2015-2720 came from running the updater out of a user-writable staging directory (VERIFIED:
  Bugzilla 1127481). ARIES: the log is forced before the data it describes, and redo is idempotent by LSN
  (VERIFIED: Mohan et al. 1992). ALICE: "An fsync() on a file does not guarantee that the file's directory entry is
  also persisted", and write-then-rename alone "only fixes a small minority (3)" of 60 found vulnerabilities
  (VERIFIED: [ALICE, OSDI '14](https://pages.cs.wisc.edu/~remzi/Classes/739/Fall2016/Papers/alice-osdi14.pdf)).

### 2.3 Editors

Godot, Blender, Unreal and Unity agree on four things (all VERIFIED from their documentation; sources in the research
notes): the only authoritative state is text (or self-describing versioned binary) under version control, and the
derived cache (`.godot/`, `Library/`, `Intermediate/`, `Saved/`) is disposable; undo and crash recovery share one
transaction stream (Godot's do/undo pairs, Unreal's `FScopedTransaction` and its Recovery Hub that replays
transactions after a crash, Unity's deltas, Blender's memfile snapshots); backups are written beside the source,
never over it, and even "safe save by rename" fails on Windows when antivirus or debuggers hold locks (Godot
#40366), so renames must retry on sharing violations; a newer file is refused by an older editor rather than
reinterpreted (Unreal's package versions; Blender's minimum-reader version). The only shipped in-editor agent, Unity
Assistant, has an Ask mode that changes nothing, a Plan mode that changes nothing "until approved", and an Agent mode
gated by permissions (VERIFIED). Blender's extension rule — sending data to a third party is "an explicit user
action" — applies to sending a rendered view to a model. Verðandi already has the text-authority shape (the brief,
the ledger, gitignored `art/build/`), the transaction stream (intents and their inverses), and the proposal-until-
admitted boundary; what it lacks is the persisted tag vocabulary and the crash-safe write.

### 2.4 Theory a change transaction can be composed from

Each clause of the protocol in §5 has a formal parent. Atomicity and recovery: Haerder & Reuter 1983, ARIES 1992,
FSCQ's Crash Hoare Logic (recovery is idempotent because "its crash condition implies its precondition", SOSP 2015),
Yggdrasil's crash refinement (OSDI 2016). Footprints: the separation-logic frame rule, `{p} c {q} ⊢ {p ∗ r} c {q ∗ r}`
when `c` modifies no variable free in `r` (Reynolds 2002; O'Hearn 2019). Noninterference: Goguen–Meseguer 1982, and
Rushby's intransitive form (1992) with its unwinding conditions, which is the one that admits a sanctioned flow
`candidate ⇝ gate ⇝ admitted` while forbidding `candidate ⇝ admitted`; seL4's information-flow proof (Murray et al.
2013) shows the cost of nondeterminism at the observation boundary. Build theory: Mokhov, Mitchell and Peyton Jones,
"Build Systems à la Carte" (ICFP 2018): correctness, minimality, early cutoff, verifying against constructive traces,
and the finding that deep constructive traces cannot do early cutoff and produce "Frankenbuilds" for nondeterministic
tasks; Nix: "a store object can never be changed after it has been built" (Dolstra 2004), and *same inputs ⇒ same
path* is a theorem about naming but an assumption about contents. Incremental computation: Adapton (PLDI 2014)
recomputes only along inconsistent recorded dependencies. Authority: object capabilities ("an object can affect the
world outside itself only by sending messages to objects it holds references to", Miller 2006; "Capability Myths
Demolished", 2003). Bootstrapping: Thompson 1984 and Wheeler's diverse double-compiling (2005), which needs an
independent trusted path and a deterministic parent. Fault containment: Gray 1985 (fail-fast modules, process
pairs), Candea & Fox 2003 (crash-only software), Erlang's supervision trees (bounded restart intensity; a failed
supervisor is terminated by its own supervisor). Append-only logs: RFC 6962's consistency proofs, git's object
model. No fetched publication composes all of these; the composition in §5 is this plan's, and its evidence will be
a death-point harness, not a proof. Full citations: the research notes of 2026-10-12 (`docs/RESEARCH-FINDINGS.md`,
R-15).

### 2.5 The director's providers (all VERIFIED on 2026-10-12 from platform.claude.com and code.claude.com)

- **Forced tool choice is refused by every current model**: "`any` and `tool` return a 400 error" on Opus 5.5,
  Sonnet 5.5, Fable 5.1 and Mythos 5.1; the page says to use "`auto` with strict tool use … or structured outputs"
  ([implement tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)).
  `art/providers/anthropic_messages.py:53` sends `tool_choice: {"type": "tool"}`. The self-test could not see this:
  it holds the adapter to a local mock. **The adapter must move to `output_config.format = {"type": "json_schema",
  "schema": …}`**, no beta header ([structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)).
  The schema rules there — `additionalProperties: false` required, no recursion, no `minimum`/`maximum`, no
  `minLength`/`maxLength`, `minItems` only 0 or 1, at most 24 optional parameters — are compatible with the gateway's
  schema as long as its limits stay client-side, which they are (`art/studio.py:78-79, 266-315`). Failure signals:
  `stop_reason: "refusal"` (billed) and `"max_tokens"`; "Changing the `output_config.format` parameter will invalidate
  any prompt cache for that conversation thread."
- **Prompt caching**: 512-token minimum on the 5.x models; writes 1.25× (5-minute) or 2× (1-hour); reads 0.05× on
  Opus 5.5 and Sonnet 5.5; four breakpoints; prefixes in the order tools, system, messages
  ([prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)). The art-language reference
  and the statement list (6–10k tokens, re-sent on every request today) are the cacheable prefix.
- **Images**: `⌈width/28⌉ × ⌈height/28⌉` visual tokens; the high-resolution tier (Claude 4.7 and later) allows a 2576 px
  long edge and 4,784 tokens; a 1920×1080 still is 2,691 tokens, a 1280×720 still 1,196; "Claude's coordinate and
  localization outputs are approximate" ([vision](https://platform.claude.com/docs/en/build-with-claude/vision)).
- **Claude Code's CLI**: `claude -p` single-message mode "does not support direct image attachments"; an image goes in
  through `--input-format stream-json` as a base64 content block. `--permission-prompts none`, `--max-turns`,
  `--max-budget-usd` (a client-side estimate that "can pass the cap") exist and are not yet passed; `--bare` never
  reads OAuth and needs `ANTHROPIC_API_KEY`. Policy: "Unless previously approved, Anthropic does not allow third
  party developers to offer claude.ai login or rate limits for their products" ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)):
  the shippable path is an API key; the CLI on the owner's plan is his own development path, as he ruled.
- **Images and 3D editing, in the literature**: LayoutVLM's ablation (CVPR 2025) shows an image raises the
  collision-free rate (67.2 → 81.8) and the overall score but not position or rotation accuracy, and that removing
  the labels and coordinate marks burned into the image is the largest loss; SceneCraft's render-and-review loop lifts
  its constraint score from 26.1 to 88.9; 3D vision-language models hallucinate relations on opposite-direction
  questions more than half the time (2025). The design that follows: **structured first, the image as a critic** —
  the model proposes in the statement language against measured geometry; a still with the tags burned in is used to
  rank candidates or to list violated constraints by tag, each verified against the scene before anything acts on it.

---

## 3. The architecture comparison

Criteria (each 0–3; a higher score is better for the studio): reliability on a clean Windows machine; creative
iteration speed; graphics capability (WebGL 2, `EXT_color_buffer_float`, pointer lock); input behaviour for a
first-person world; process isolation and lifetime control; self-update safety; development cost; portability;
debugging; and the risk of rewriting working components (3 = no rewrite).

| option | reliable | iteration | graphics | input | isolation | self-update | cost | portable | debug | no rewrite | **sum** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A. The page in Edge `--app` with a private profile, under a std-only Rust stub that owns a job object and the active-version pointer, and a std-lib Python supervisor; the python.org embeddable interpreter** | 2 | 3 | 3 | 3 | 2 | 3 | 3 | 2 | 3 | 3 | **27** |
| B. The page in WebView2, hosted from std-only Rust by raw COM | 2 | 3 | 3 | 1 | 3 | 3 | 1 | 1 | 2 | 3 | 22 |
| C. Tauri, Electron or pywebview | 2 | 3 | 3 | 1–3 | 3 | 2 | 2 | 2 | 2 | 3 | 22–24, **and each violates the std-only rule in shipped code** |
| D. A native renderer and editor (the kernel's framebuffer in `win32.rs`, or a GPU renderer written for it) | 1 | 1 | 1 | 2 | 3 | 2 | 0 | 1 | 1 | 0 | 12 |
| E. PyInstaller or Nuitka one-file wrapping `play.py` | 1 | 2 | 3 | 3 | 1 | 1 | 2 | 1 | 1 | 3 | 18 |

A wins on the charter's terms (nothing third-party is shipped; the shell layer stays "replaceable"), on input (the
browser's own pointer-lock path, which WebView2's open jitter bug argues against for an FPS-style world), and on the
rewrite criterion (nothing of the renderer, the simulation, the exporter or the director changes). Its weakness is
lifetime control — a browser PID and nothing more — which the stub's job object and a page heartbeat repair (§4).
B loses on input and cost but is the right **fallback engine** when Edge and Chrome are both absent (the EEA case);
it is built only if the launcher's logs show that branch firing (§8, kill criterion). C would be the fastest path in
a repository without the charter; here each is a shipped dependency the owner has not allowed, and Tauri's mandatory
signed updater duplicates §5 with a design this plan cannot verify. D is the rewrite his ruling forbids. E solves
nothing A does not and adds temp-directory unpacking and antivirus false positives.

**Design forks resolved by producing both, where both are robust.** The shell: A now, with Chrome by the same
mechanism, and B's probe kept as a bounded experiment. The installation: a portable layout with a shortcut made by
inbox COM (no tool), *and* an Inno Setup script kept beside it for a per-user installer, used only if the owner
rules that a packaging-time tool is acceptable. The providers: the API with structured outputs for shipping, the CLI
on his plan for development, the same prompt for both (already so). The journal: the promotion journal and the
content ledger share one canonical form and one chain rule (DIRECTOR-0's), two files, two validators.

---

## 4. The recommended architecture

```text
 VerdandiStudio.exe   the stub: std-only Rust, raw Win32 FFI (as shell/win32.rs), outside every version directory
   │  owns   a job object (KILL_ON_JOB_CLOSE | DIE_ON_UNHANDLED_EXCEPTION); the active pointer; the promotion journal's tail
   │  reads  studio\promotions.log and studio\active.json, and decides by the contract's §7 (the pointer a cache of the journal)
   │  never  executes code from staging; never replaced by a transaction it is part of (replaced by rename-aside, §5.6)
   ▼
 versions\<hash>\python\pythonw.exe  versions\<hash>\repo\art\studio_app.py      the supervisor: std-lib Python, one per generation
   │  starts  art\play.py --port N --root <projects\...> --director <config>   (in the job; cwd outside versions\)
   │  opens   msedge.exe --app=http://127.0.0.1:N/ --user-data-dir=<state\edge> …  (or chrome.exe; later WebView2)
   │  watches the browser PID and the page's heartbeat; stops the server with /studio/shutdown, then CTRL_BREAK, then the job
   │  runs    a candidate's lifecycle up to `promote` (the Try in a fresh job); the stub activates, blesses or rolls back
   ▼
 art\play.py ──► art\studio.py (the gateway) ──► a provider command (claude.exe | python anthropic_messages.py | scripted)
   │                 │                              in its own process group, inside the job, no tools, stdin only
   │                 └──► art\director.py: evaluate, admit, refuse, undo; the content ledger
   └──► the page (WebGL 2): the world, the outliner, the details pane, the director's panel, the candidate strip
```

**Directories and ownership** (per user, under `%LOCALAPPDATA%\VerdandiStudio\` by default; one tree, four kinds of
thing, each with one writer):

| path | holds | written by | survives |
|---|---|---|---|
| `bin\VerdandiStudio.exe` | the stub | the installer, or a stub transaction (§5.6) | everything |
| `runtime\python-3.x\` | the embeddable interpreter | a runtime transaction (rare) | version promotions |
| `versions\<content-hash>\` | one immutable generation: the repository tree it was built from, its built binaries (`shell`, `conform`), its manifest (sources' sha256s, the build's rustc version, the tests' results) | the supervisor's staging, then never | until garbage-collected (never the active or the previous blessed one) |
| `studio\active.json`, `studio\promotions.log` | the pointer and the journal | the stub (the pointer and the activation records), the active supervisor (the lifecycle records and `promote`) | everything; the journal is the authority, the pointer a cache checked against it (the contract, §5) |
| `projects\<name>\art\{briefs,ledger}\`, `projects\<name>\tags.json`, `projects\<name>\build\studio\` | the user's worlds: the authoritative text, the content ledger, the tags, the records | the director (through `--root`), the gateway | every promotion and rollback (clause C) |
| `state\edge\`, `state\logs\`, `state\diagnostics\` | the private browser profile; logs; a diagnostics bundle | the browser; the supervisor | disposable |

**Trust boundaries.** The model sees a request on stdin and answers on stdout; it holds no handle to any file above
(the ocap reading of clause A). The gateway reads the answer whole or refuses it whole. The director judges content
candidates; the supervisor judges source candidates; **only a person admits**, by a POST the page sends with its
token to the running supervisor — never by anything a provider wrote. The stub alone moves the pointer and writes the
commit; the active supervisor writes the lifecycle up to `promote`, and nothing while a promotion is open (the
contract, §2 and §5); a candidate's processes live in a job of their own and die with it. The 58 pinned sources, `oracle/`, `verify/`, the charter block, `graybox/serve.py` and the stub's
own source are **never-grantable** footprints for a source candidate, as `play/…` is never grantable for a content
candidate (`art/director/scope.py:32-35`); a change to them is the owner's, through his gate, by his push.

**What stays as it is.** The renderer, the simulation (`sim.js`, rules 1, the input contract), the exporter, the art
checks, DIRECTOR-0's canonical form, scope protocol and ledger, the gateway's request and response formats, and the
gate. The desktop layer wraps `play.py`; it does not fork it.

---

## 5. The theorems, and the one this plan builds to

### 5.1 The candidates

Each is scored for usefulness (does it decide something the implementation would otherwise guess), robustness (does
it hold under the failure model the sources establish) and elegance (how few new mechanisms it needs, given what the
tree has), 0–3 each.

| id | candidate | from | useful | robust | elegant | note |
|---|---|---|---|---|---|---|
| T1 | **ACCT**, Admitted-Change Containment (the owner's text): `Failed(C) ⇒ (S', D') = (Sₙ, Dₙ)`; `A(C) ⇒ Valid(Sₙ₊₁) ∧ Dₙ₊₁ ≡ Dₙ ∧ Oₙ₊₁ = Oₙ` | ACID, noninterference, incremental computation, immutable artifacts | 3 | 2 | 2 | the right statement; its proof needs the axioms T4–T6 supply, and it says nothing about who may switch |
| T2 | **Generation pointer**: the active application is a pointer to an immutable generation; promotion is one atomic rename; rollback is a pointer move; blessing comes after a health check by the *previous* generation | Nix, OSTree, systemd, Android A/B, the Chromium updater | 3 | 3 | 3 | nothing is ever edited in place; the existing shell seal is this rename |
| T3 | **Frozen input**: the model's output is a content-addressed *input* artifact; every derived step is deterministic in it; early cutoff by content identity | Build Systems à la Carte, Nix, seL4's lesson, DIRECTOR-0's own ruling ("early cutoff must depend on content identity") | 3 | 3 | 3 | already the gateway's practice (`<L>.intent`, `request_sha256`, `response_sha256`) |
| T4 | **Intransitive admission**: `candidate ⇝ gate ⇝ admitted`, never `candidate ⇝ admitted`; the candidate holds no capability to the pointer, the ledger writer or the stub | Rushby 1992, Miller 2006 | 3 | 3 | 2 | the process layer of "the model proposes; Verðandi admits" |
| T5 | **Supervisor independence**: no transaction replaces the supervisor that runs it; a new supervisor is qualified by the old; the stub is replaced out of band and bounded restarts fall back to the previous blessed generation | Thompson, Wheeler's DDC, Erlang, the Chromium updater, Firefox's CVE | 3 | 3 | 2 | the owner's own caveat: "if the update supervisor itself can be replaced by the candidate it supervises, the protocol loses its independent enforcement point" |
| T6 | **Crash refinement with explicit persistence axioms**: the recovered state after any crash is one of an enumerated set; the axioms (write-through rename, per-record fsync, a pre-created journal) are stated and tested at death points | ARIES, FSCQ, Yggdrasil, ALICE; the shell's journal and `admit-crash` | 3 | 3 | 3 | the harness exists in the gate for the shell; the studio needs the same off the gate |
| T7 | **Semantic preservation of user data**: `Dₙ₊₁ ≡ Dₙ` means the ledger replays to the same files (`director.py verify`); a migration is a logged event with a minimum-reader version, and an older generation refuses a newer ledger rather than reinterpreting it | Unreal's package versions, Blender's compatibility rule, DIRECTOR-0's replay | 3 | 3 | 3 | the oracle for ≡ already exists |
| T8 | **Liveness of the last admitted world**: when a request, a provider or a candidate fails, the world served stays the last admitted one and stays playable | STUDIO-0's acceptance test ("keep the world playable when the model is unavailable") | 2 | 3 | 3 | measured 10/10; generalized to generations |
| T9 | **Footprint as frame**: a change declares its modifies-set; what it realizes outside the closure of that set is a leak; namespaces outside any grant are reserved | the separation-logic frame rule; `check_scope`'s declared/realized/affected/unclaimed | 3 | 3 | 3 | built for content; the source analogue is file globs |

ACCT is kept as the *statement*; it is one of nine, and the eight others are what make it provable and testable. The
synthesis below is the mix.

### 5.2 VCT-0: the Verðandi Change Transaction (the synthesis, with its operators)

One protocol, two domains (a world's content; the studio's source), two validators, one ledger discipline. Let `G`
be a generation (an immutable directory named by its content hash), `A` the active generation, `P` the previous
blessed one, `J` the promotion journal, `D` the projects, `C` a candidate with declared footprint `F(C)`, and `B_C`
its **basis**: the record of everything its validation depended on — the base generation's hash, the source
revision, the manifest digest, the validators' own sources' hashes, the toolchain's identity (rustc's and Python's
version strings), the configuration's digest. `B_now` is the same record computed at promotion time.

**The operators, defined once.** `is` is identity: the same bytes, by sha256 — never a head that looks equal. `==` is
equality of bytes. `≡` is equivalence of user data under one named procedure: the content ledger of a project
replays to the files it holds (`director.py verify`), at the reader's version. `<` is the journal's order (`seq`), and
nothing else. `??=` assigns only when the left side is **missing**; an **invalid** left side is a different state
with its own rule (below), never silently reassigned.

```text
Built(C)          := G(C) exists and its manifest's hashes are those of its files                              (T3)
Checked(C, B_C)   := every validator of C's domain passed inside C's own job against G(C), with basis B_C       (T1, T9)
Leak(C)           := realized(C) \ cl(F(C)) != ∅   or   F(C) ∩ RESERVED != ∅                                     (T9)
Fresh(C, B_now)   := B_C is B_now, or every member of B_now that differs is outside C's recorded dependencies   (T3)
Admitted(C, B_C)  := a person said so through the supervisor, shown the diff, footprint, tests, basis, identity (T4)
Integrity(G)      := G's manifest digest verifies and every file G names hashes as the manifest says            (T2)
Healthy(G)        := G's supervisor answered /healthz with version is G.hash within T, and the page spoke once  (T2)
Recoverable(P)    := P exists, Integrity(P), and J holds its blessed (or installed) record                       (T5)
Promote(C)        := Built(C) and Checked(C, B_C) and not Leak(C) and Fresh(C, B_now) and Admitted(C, B_C)
                     and Integrity(G(C)) and Recoverable(A)
Failed(C)         := not Promote(C)
```

Three claims, kept apart because their obligations differ (a reviewer's correction of 2026-10-12, adopted):

1. **Isolation.** `Failed(C) ⇒ A' is A ∧ D' == D ∧ (∀ o ∉ cl(F(C))) o' == o`, and `J` only grew. A candidate that
   was not promoted changed nothing a person relies on.
2. **Promotion correctness.** The active reference never names a generation that did not complete validation and
   admission: `A' is G(C) ⇒ Promote(C)`, and after it `P' is A`, `D' ≡ D`, `(∀ o ∉ cl(F(C))) o' == o`, and the tries
   counter is set. `tries = 3` is a policy, not a clause; the clause is that a counter exists and is decremented by
   rename before each launch.
3. **Recovery correctness.** After a crash at any enumerated point, recovery is `Recover(J, P, F)`, the decision
   table of the contract's §7: the journal, the pointer and the files read together, the first rule that holds
   applied, its writes made record-before-pointer, until it runs a generation or stops in SAFE for a person. The
   commit point is the durable `blessed` record: before it, a promotion continues its trial only while the candidate
   verifies, its evidence is intact and a try remains (`boot` records count them), and otherwise rolls back to the
   committed generation; after it, nothing undoes it. The pointer is a cache: `P ??= target` when it is missing,
   rebuilt and recorded when unreadable or behind, and **never followed** when it names what the journal did not set
   (SAFE). Held by `python art/studio_txn.py check`: 41,568 crash states, 195,376 crashes inside recovery, 0 failures
   (MEASURED in the container; the contract, §8).

**Three levels of consistency, claimed separately.** *Process-kill consistency*: recovery works after the
application is terminated at each enumerated point — this is what the harness measures. *OS-crash consistency*:
recovery works across an operating-system crash — claimed only under the platform axioms below, and measured, if
at all, by a VM reset. *Power-loss durability*: acknowledged writes survive loss of power — depends on the disk and
the driver and is **not claimed**; the axioms say what it would need.

**The axioms** (what the parents require; each a hypothesis the implementation must state, not a fact a harness
establishes): A1, a `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH` over an existing file
leaves either the old or the new file at that name (Microsoft documents "does not return until the file is actually
moved on the disk" and nowhere "atomic"); A2, `os.fsync` persists a record's bytes (on Windows it is `_commit`, which
"forces the operating system to write the file associated with fd to disk" and says nothing of the directory
entry — so A3); A3, the journal and the pointer's directory pre-exist, so an append and a rename extend entries that
are already durable; A4, the stub's binary is altered by no candidate (its source is reserved; it is installed, never
staged); A5, the validators and their inputs are independent of the candidate and cannot be changed by it after
validation (the basis `B_C` records them; the capability boundary below enforces it); A6, the person who admits is the
designer, and nothing admits for them. Outside the failure model: a disk that lies about flushing, an administrator
or malicious code at the user's own integrity level, a corrupt installer.

**Two notes on the operators.** `??=` also names the tag rule the studio already has: `tag(object) ??= next()`,
assigned at first touch and never reassigned, and the owner's friction with it (2026-10-12) is answered by showing
the tags (§7, B1), not by changing the rule. And `≡` for a project carries `min_reader`: a generation whose reader is
older refuses the project (`reader.version < min_reader`), never reinterprets it (§6, T7).

**What VCT-0 does not claim.** That a candidate is good, or beautiful, or that the suites catch every defect; that
the model's proposal is reproducible (it is frozen, not reproduced); anything the axioms exclude.

**The capability boundary (what a candidate cannot obtain, not merely which process it is).** Process separation is
not isolation: on one Windows account, a candidate's process could write `studio\active.json` as well as the
supervisor can. The boundary this plan adopts is Windows' Mandatory Integrity Control: "a principal with a low
integrity level cannot write to an object with a medium integrity level, even if that object's DACL allows write
access", objects are created `NO_WRITE_UP` by default, and "objects that lack an integrity label are treated as
medium" (VERIFIED: [Mandatory Integrity Control](https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control)).
A low-integrity process is made by `DuplicateTokenEx`, `SetTokenInformation(TokenIntegrityLevel, S-1-16-4096)` and
`CreateProcessAsUser`, may write only under `%USERPROFILE%\AppData\LocalLow` or a folder labelled low
(`icacls … /setintegritylevel Low`, or `SetNamedSecurityInfoW` with `S:(ML;;NW;;;LW)`) (VERIFIED, an archived
Vista-era article still describing the mechanism: [Designing applications to run at a low integrity level](https://learn.microsoft.com/en-us/previous-versions/dotnet/articles/bb625960(v=msdn.10));
Chromium's sandbox sets the same token level). So: a candidate's staging, build, suites and *Try* run **at low
integrity** in their job, writing only to a low-labelled scratch (`state\low\`) and their own staging directory;
`bin\`, `studio\`, `versions\` (once staged), `projects\` and `runtime\` are medium and cannot be written by them even
by mistake; *Try* plays a scratch copy of a project. Trust transfers at **Admit**: the promoted generation runs at
medium as the active studio, because the designer admitted it and `P` stays recoverable. What this does not stop: an
administrator, or malicious code that already runs at medium — for those the hash-chained journal is evidence, not
prevention (RFC 6962's limit). Whether the suites run under low integrity is experiment 4 of §8; if they cannot, the
boundary is tamper-evidence alone and the plan says so.

**How it is held.** Mutants of the supervisor (a pointer written before the journal; a candidate allowed to append
the journal; the old supervisor replaced by the candidate; a health check that trusts the candidate's own word; a
generation activated whose manifest does not match; a stale basis accepted; a low-integrity write to `studio\`
that succeeds) must each be refused by the death-point harness or the self-test; the harness enumerates the crash
points as `admit-crash` does for the shell. These are off the gate.

---

## 6. The recursive update, as a transaction

The ten steps the owner asked for, as the supervisor runs them. The journal `studio\promotions.log` has DIRECTOR-0's
form (one canonical document a line, `seq`, `prev` the sha256 of the line before; `art/director/ledger.py`'s rule
with its own `KINDS`) and the shell's discipline (each record flushed and fsynced before it counts; a torn last
record dropped on load, any other fault refuses).

| step | record | what happens | who | on crash here |
|---|---|---|---|---|
| 1. Capture | — | `head(A)` is read: the active generation's hash and the projects' ledger heads | supervisor | nothing to recover |
| 2. Propose | `PROPOSED {request_sha256, response_sha256, footprint, basis}` | the model answers a `VERDANDI-STUDIO-SOURCE-REQUEST` (the repository's file list with hashes, the footprint grammar, the self-tests' names, the tree's AGENTS.md rules) with a bounded patch: at most N files, each named, unified diffs, a rationale, a declared footprint of file globs, and the tests it expects to pass; read whole or refused whole, as `read_response` reads content; the raw response is frozen under `studio\candidates\<id>\` | gateway | the record is the only trace; nothing else exists |
| 3. Stage | `STAGED {id, gen_hash}` | the active generation's tree is copied to `versions\<tmp-run-id>\`, the patch applied; the footprint check: every changed path ∈ `cl(F)`, `F ∩ RESERVED = ∅` (`SOURCE-LEAK`, `SOURCE-RESERVED`); the tree's content hash is computed and the directory renamed to `versions\<hash>\` (a rename, so a crash leaves a tmp directory that the next start garbage-collects) | supervisor | tmp directory removed at next start |
| 4. Build | `BUILT {hash, rustc, binaries}` | `rustc -O` for what the tree builds (`shell/main.rs`, `art/director/conform.rs`) in the candidate's job, with a timeout; no rustc ⇒ `SOURCE-NO-RUSTC`, refused (the design tool refuses `DESIGN-NO-SHELL` likewise) | supervisor | the generation directory is complete or not; its manifest says which |
| 5. Check | `CHECKED {hash, basis, suites: {name: result, seconds}}` | the off-gate suites run inside the candidate's own job, at low integrity, against the staged tree, with scratch roots, timeouts and output limits; the basis (the validators' own hashes, the toolchain, the configuration) is recorded with the results, and a result is reused for another candidate only when its whole basis `is` the same (a verifying trace, never a bare generation hash); a candidate touching a pinned source, `oracle/` or `verify/` is marked `OWNER-GATE`: the owner runs the gate, the supervisor never does | supervisor | re-run; results are idempotent |
| 6. Launch and health | `LAUNCHED {hash, port}` → `HEALTHY {hash, ms}` or `DEAD {hash, exit, tail}` | the candidate's own supervisor is started from `versions\<hash>\` in a fresh job, cwd outside it, on a second port; it must answer `/healthz` with `{"version": hash, "ready": true}` within T seconds; the page can open it in a second window ("try the candidate"); the candidate cannot see the pointer or the journal | the *old* supervisor | the job dies with the supervisor; `DEAD` is appended at next start if `LAUNCHED` has no end |
| 7. Review | — | the page shows: the diff, the footprint and what the check realized, the suites' results and times, the generation's hash and the manifest, the launch's health, and the model's rationale; Admit and Reject buttons; nothing else is enabled while a candidate is unreviewed | the designer | nothing moves |
| 8. Promote | `promote {gen, from, basis, tries}` → `activate {gen}` → pointer rename | only on Admit, and only while `Fresh(C, B_now)` (a basis that moved in a dependency the candidate recorded is `SOURCE-STALE`: validate again or discard): the supervisor appends `promote` (the admission) and exits; the stub closes the old job and, by the contract's R9, checks `Integrity(G(C))` (the manifest and every file it names re-hashed now, no unnamed file, the time measured and reported), the evidence and `Integrity(A)`, appends `activate`, then writes the pointer `{gen, seq}` by a temporary file, a flush and `MoveFileExW(MOVEFILE_REPLACE_EXISTING \| MOVEFILE_WRITE_THROUGH)`; a failed check appends `aborted` instead | supervisor, then stub | `activate` durable and the pointer behind ⇒ the pointer is moved on (R8); neither ⇒ the checks again (R9, R10) |
| 9. Trial and commit | `boot {gen, left}` …, then `blessed {gen}` or `rollback {from, to, reason}` | before each launch on trial the stub appends `boot` (the tries are the count of these records); the candidate must answer the stub's `GET /healthz` with its own hash and `ready` within T seconds and report that the page spoke (a `/studio/alive` POST with its token); then the stub appends `blessed` — **the commit point**; a dead or silent candidate is killed with its job, and the next decision boots it again or, with no try left or a failed check, appends `rollback` and moves the pointer back | stub | before `blessed`: the trial goes on or rolls back (R11, R12); after it: committed, never undone |
| 10. Recover | `recovered {reason}` when anything was repaired | every start, and every exit of a generation, is `Recover(J, P, F)` (the contract's §7): a torn tail set aside and truncated; a pointer missing, unreadable or behind rebuilt; a pointer naming what the journal never set, a damaged middle line, or no committed generation that verifies ⇒ SAFE, and a person chooses; tmp directories and generations other than the committed one, the one committed before it and an open candidate are garbage-collected; the first page shows what was done | stub | idempotent; 0 failures over the check's crash states |

The record names are the contract's (`docs/STUDIO-CONTRACT.md` §5). This table's first version had `PROMOTE_BEGIN`,
`PROMOTE_END`, a bless written by the new generation's own supervisor, the tries in the pointer's filename, and a
recovery to "the last `PROMOTE_END`", which could restart an uncommitted generation as if it were committed; the
second review of 2026-10-12 found the ambiguity, and the contract removes it.

**Atomicity.** One durable append commits a promotion (`blessed`); the pointer's renames are cache updates; no file of
a generation is ever rewritten. **Durability.** The journal is forced before the pointer; the pointer is moved
write-through; a generation's files are
fsynced before `STAGED` (OSTree's rule). **Provenance.** Every candidate carries its request and response hashes, its
base, its patch, its footprint, its suites, its build inputs (sources' sha256, rustc's version) and its hash;
`versions\<hash>\manifest.json` is the artifact's identity, and the stub refuses to activate a generation whose
manifest does not reproduce its hash. **Recovery.** The stub's replay is the only path; it never runs code from
`studio\candidates\` or a tmp directory (Firefox's lesson).

**Binaries against data.** Rolling the studio back moves `A` to `P` and leaves `projects\` alone (clause C). A
project written by a newer generation carries `min_reader`; an older generation refuses it with the version named,
and the designer rolls forward or keeps a copy. A migration of a project is a content transaction of its own,
admitted through the content ledger with an `inverse`, never performed silently by a studio promotion.

**The supervisor and the stub.** A candidate that changes `art/studio_app.py` is a normal generation: the old
supervisor launches and qualifies it, so the supervisor is never replaced by a transaction it runs (T5). The stub's
source is reserved; a new stub is installed by a separate *stub transaction*: the new `VerdandiStudio.exe` is placed
beside the old, the old is renamed aside (a running executable can be renamed, not overwritten), the new one is
started with the same pointer, and the old is deleted at the next start if the new one blessed itself by reading the
pointer and launching `A`; otherwise the renamed-aside stub is moved back by the installer's repair path. Until that
transaction exists, the stub changes only through the installer: a documented limit, not a hidden one.

**Git.** The supervisor promotes a working tree, not a branch. Committing an admitted source change to the repository
remains the owner's act: the generation's `manifest.json` names the patch, and a `git am` of it is one command; the
supervisor never commits and never pushes (`AGENTS.md`).

---

## 7. The development plan: five batches

Dependency order: **B1 → B2 → {B3, B4} → B5**; B3 and B4 are independent of each other and both need B1's launcher
and B2's transaction for their own candidates to be tried the studio way. Priorities: MUST for the first release,
SHOULD for the second, LATER after that.

```text
   B1 STUDIO-APP-0  launch · supervise · hardened content path · tags shown
          │
   B2 STUDIO-APP-1  the self-change transaction (VCT-0 for source)
        ┌─┴──────────────┐
   B3 STUDIO-2          B4 ART-2
   workspace, image,    vocabulary, connecting pieces,
   caching, projects    scope for an object with its parts
        └─┬──────────────┘
   B5 RELEASE-0  installer, clean-machine tests, diagnostics, signing decision, runtime transaction
```

### B1 · STUDIO-APP-0 — a desktop icon starts the studio, and the content path is crash-safe (MUST)

**User-visible outcome.** Double-click a desktop icon: a window opens with the plaza playing; the director works as
today; close the window and everything stops; the tags a designer made are there after a restart; the Anthropic
provider works with a Console key; the studio survives a crash mid-admission with the brief and ledger intact.

**Status (2026-10-12): the first part built, off the gate.** Done and measured in the container: the content path's
crash safety (step 2: `art/director/durable.py`; an admission's redo-or-undo folder and recovery at every start;
`python art/director.py crashtest`, 14 cases, each a real process killed at a write and recovered to the parent or
the child); the tags persisted and shown (step 3, the contract's §9; chips that put a tag into the prompt; a refusal
that says what a tag names and how to pin it); the API provider on structured outputs with `claude-opus-5-5` from its
configuration (step 4; a forced tool choice now refused by the self-test's mock as by the API); the request record's
basis (the validators' and the configuration's sha256s); play.py's `/healthz`, `/studio/alive`, `/studio/shutdown`,
signals, exit codes, `--root` forwarded to the `--emit` child, and its port bound exclusively on Windows (step 1);
the page's heartbeat; the five probes of §8 under `tools/probe/`. **The second part, after probes 1 and 2 on his
machine** (both HELD; Edge outlived its window by more than 20 s, twice, which the plan foresaw): the supervisor
`art/studio_app.py` (step 6: a job it joins so that everything it starts ends with it; play.py without a console; Edge in
application mode with its own profile; stopping on the page's goodbye beacon, a three-minute silence, or play.py's end;
a second start opening another window; a dialog and a log for errors; `selftest`, 7 cases with a stand-in browser) and
the shortcut (step 8: `python art\studio_app.py shortcut`, a `.lnk` made with the inbox WScript.Shell). **Moved to
B2's first step**: the stub (step 7) and the per-user layout of generations, since the checkout is B1's one generation
and the reviewed scope says *"The studio does not need its self-updater to update itself in B1. That is B2."*; the
stub's Rust also cannot be compiled for Windows in the build container. Held back: the CLI's extra flags (step 5: the
CLI works on his machine as it is, and a flag his version refuses would stop it).

**Accepted on his machine (2026-10-12).** In his words: *"I ran it from the desktop icon and it worked as built.
congratulations. movement worked and the requested changes held after closing and reopening the program, as well as the
@1 @2 and @3 tags."* His supervisor log showed `processes left in the job at exit: 256`, a misreading of the job's
process list (fix 6 below), not 256 processes. **Known limitation, deferred:** a tag names its object by its id, and
an object's id carries its cells (`canopy:19,10-28,11`), so an admission that moves or resizes a tagged object leaves
its tag "gone" (kept, listed apart, refusing a request that names it) rather than following the object.

**Hardened (2026-10-13), fixes 1 and 8 of the review of that day** (the ghosts searched for, then each checked
against the source): *one writer at a time* — every writer of a tree's ledgers, briefs, tags and maps holds the tree's
content lock (`art/director/durable.py`), an admission from before its first write to after its last, reading the
head again under it (the fence), and recovery takes the same lock and refuses while a live writer holds it; *every
request by this server's name* — play.py answers a GET, as it answers a POST, only to 127.0.0.1 or localhost by name,
so a rebinding page reads nothing. Two more defects of the same kind found while building it: `Workspace.export`
swaps the module-global maps folder (two exports at once read each other's maps), and the gateway's `quiet()` swaps
the process's one standard output (two at once left it redirected). `python art/director.py racetest`, 32 cases, each
case's plant caught. Next, in the order he approved: the queue's torn tail cut (3), a crash never paying twice (4), the
job's process list read right (6), silence never stopping a busy studio (7), and the shared map refused (2). On his
machine the race court passed 32 of 32 (the lock measured on Windows); his own admissions in the working brief then
showed that the studio's self-tests played in it, so they now play in `art/fixtures/selftest/` (`selftest_tree`).

**Components.** New: `shell/studio_stub.rs` (the stub; std-only, raw FFI, built by hand like `win32.rs`, never by the
gate), `art/studio_app.py` (the supervisor), `art/studio_launch.md` (the contract); changed: `art/play.py`
(`/healthz`, `/studio/shutdown` POST, `--port`, `--root` forwarded to the `--emit` child, a signal handler),
`art/director.py` and `art/director/ledger.py` (write-through writes), `art/studio.py` (persisted tags; the panel's
tag conveniences), `art/providers/anthropic_messages.py` (structured outputs), `art/providers/claude_code.py`
(`--permission-prompts none`, `--max-turns`, `--max-budget-usd`, `--permission-mode` explicit), `art/web/play.js`
and `play.html` (the heartbeat; tags in the prompt box; click a tag to insert it; a refusal names the likely tag),
`art/STUDIO.md`, `docs/BOUNDARIES.md`, `AGENTS.md`.

**Prerequisites.** None but the two experiments in §8 (Edge's exit on last window; the job object from Python).

**Steps.**
1. `play.py`: `GET /healthz` → `{"version", "ready", "brief", "head"}`; `POST /studio/shutdown` (token) → stop the
   studio, the watcher and the server; `signal.SIGINT`/`SIGBREAK` handled; `--port` fixed by the supervisor; `--root`
   forwarded to `--emit`; exit codes documented (0 stopped, 70 could not serve, 75 refused to start).
2. Crash-safe content writes: one function `art/director/durable.py` — write a temp file beside the target, flush,
   `os.fsync`, then `MoveFileExW(... REPLACE_EXISTING | WRITE_THROUGH)` through `ctypes` on Windows and
   `os.replace` plus a directory fsync elsewhere, with a retry on sharing violations (Godot's finding); the ledger
   appends with flush and fsync and the file is pre-created at genesis; a torn last line is reported as
   `LEDGER-TORN` with the repair named (truncate to the last whole line, which the chain then verifies), never
   repaired silently. Used by `cmd_admit`, `cmd_refuse`, `cmd_rebase`, the studio's records.
3. Tags persisted, by the contract's §9 (a counter that only grows; a gone object's tag kept apart and refused when
   named; a new project from `@1`): `projects\<brief>\tags.json` (DIRECTOR-0 canonical form, written durably), loaded at start,
   bound to the scene hash as today; the panel's prompt box shows the active tags; clicking a tag inserts it; a
   `STUDIO-REFERENCE` refusal names the tag most likely meant (the nearest by kind and distance); the owner's
   numbering friction is answered by display, the rule `tag ??= next()` unchanged.
4. The API provider: `output_config.format` with the gateway's schema; `stop_reason` `refusal` and `max_tokens`
   mapped to `STUDIO-PROVIDER-EXIT` with the reason; the mock in the self-test answers the new shape and refuses
   the old (`tool_choice: tool` → 400, as the real API does); prompt caching breakpoints on the system text (the
   art reference, 1 h) and the statement list (5 min), the varying part last; `usage` reports cache reads.
5. The CLI provider: the flags above; `--bare` as an opt-in when `ANTHROPIC_API_KEY` is set (the shippable path);
   `cache_read_input_tokens` recorded. The gateway's request record gains the sha256 of the director's and the
   scope's sources and of the provider's configuration file (the envelope's two gaps, the contract's §3); the model
   is the configuration's field, its default the owner's ruling.
6. The supervisor: find Edge (App Paths in the registry via `winreg`, then the two conventional paths), else Chrome,
   else refuse with `STUDIO-NO-BROWSER` and the WebView2 note; start `play.py` on a free fixed port with
   `--root projects\<name>`; launch `msedge.exe --app=… --user-data-dir=state\edge --window-size=… --no-first-run
   --no-default-browser-check`; wait on the browser PID and on the page's heartbeat (`navigator.sendBeacon('/bye')`
   on `pagehide`, a `/studio/alive` every 5 s); stop in order: `/studio/shutdown`, `CTRL_BREAK_EVENT`, then the job.
7. The stub: create the job (`KILL_ON_JOB_CLOSE | DIE_ON_UNHANDLED_EXCEPTION`), decide by the contract's R0–R8, R14
   and R15 (the journal, the pointer, the generation's manifest; SAFE shows its reason and launches nothing), held to
   vectors emitted by `art/studio_txn.py`; launch the supervisor suspended-assign-resume, wait; on exit, if the supervisor asked for
   a restart (exit 86), loop; write `state\logs\stub.log`. Under 400 lines; raw FFI as `win32.rs` does it.
8. Layout and shortcut: `tools\layout.py` makes the per-user tree from a checkout and the embeddable interpreter's
   zip (downloaded by the owner, its sha256 recorded); `tools\shortcut.ps1` makes the desktop `.lnk` with inbox
   COM; the Inno script `tools\studio.iss` written beside them and used only on his ruling.
9. Self-tests: `python art/studio_app.py selftest` (the supervisor without a browser: health, shutdown order, the
   heartbeat timeout, the job's kill, the browser lookup with planted registry values, a dead server, a dead
   browser); the director's death-point harness `python art/director.py crashtest` (kill at each of the write
   points: temp written, fsynced, renamed, ledger appended, ledger fsynced; the brief and ledger load to the parent
   or the child, never between); the studio self-test grown with the tags' persistence and the API's new shape;
   mutants of each.

**Acceptance.** On the owner's machine: the icon starts the studio; `tasklist` shows one `VerdandiStudio.exe`, one
`pythonw.exe`, one private `msedge.exe` tree; closing the window ends all three within 5 s; killing `pythonw.exe`
closes the window and the stub reports it; the tags survive a restart; a prompt through the API provider with a
Console key returns candidates; `crashtest` passes at every death point on Windows; the self-tests above pass; the
gate unchanged, 251 rows.

**Failure and adversarial cases.** Edge absent (refused, said); the port taken (another chosen); a second icon click
(single instance: `CreateMutexW` → the first window is raised); the page closed but Edge's process lingering (the
heartbeat timeout ends it); the browser profile locked by another instance; a sharing violation on the brief's
rename (retried, then refused with the holder's name if `RestartManager` gives it); a torn ledger; a provider that
hangs (the existing timeout); `--root` pointing outside `projects\` (refused).

**Tests to add or reuse.** `art/studio_app.py selftest`; `art/director.py crashtest`; `art/studio.py selftest`
(grown); `art/play.py --selftest`; the browser harness of the container (not committed); mutants. **Deliverables.**
The files above, the portable layout, the shortcut, `art/studio_launch.md`. **Risks and open questions.** Edge's
exit behaviour (§8); the owner's ruling on Inno Setup; Windows Home machines without Sandbox for testing. **Out of
scope.** Source candidates (B2); an installer with uninstall (B5); WebView2.

**Completion.** The acceptance list above met on his machine and recorded in `docs/ROADMAP.md`; the batch's
patches applied and pushed by him.

### B2 · STUDIO-APP-1 — the studio proposes, builds, tests and offers a change to itself (MUST)

**User-visible outcome.** In the panel: "improve the studio: …". The model's patch comes back as a candidate with its
diff, footprint, test results and a *Try* button that opens the candidate in a second window; *Admit* promotes it
and the studio restarts into it; *Reject* discards it; a candidate that crashes on launch is rolled back
automatically and the designer sees why; the previous version is one click away.

**Components.** New: `art/studio_source.py` (the source domain: request format, patch reader, footprint check,
staging, build, suites, manifest), `art/studio_promote.py` (the journal, the pointer, bless and rollback, the
replay), `art/STUDIO-SOURCE.md`; changed: `art/studio.py` (a second gateway domain), `art/providers/*` (the source
request rendered for the model), `art/web/play.*` (the candidate view: diff, footprint, tests, Try/Admit/Reject;
the "previous version" control), the stub (the contract's R9–R13; restart on exit 86), `art/studio_app.py`.

**Prerequisites.** B1. **Steps.** The ten steps of §6, in this order of implementation: the journal and the pointer
with their replay and death-point harness first (nothing else is trustworthy without them); then staging and the
footprint check with `RESERVED`; then the basis record and its comparison (`Fresh`), with the three cases a reviewer
named — a candidate on the current basis promotes; a validator or toolchain change after validation refuses or
revalidates; an unrelated change reuses the recorded result only because the basis says the dependency is
unchanged; then build and suites in a low-integrity job; then launch and health; then the page; then the model's
request format last, so that every stage is tested with hand-written candidates before any model writes one. **Acceptance.** The product list in §9, items 6–9, on his machine: a prompt yields a built candidate; Try opens
it; Admit promotes and restarts; Reject leaves A; a candidate planted to crash after `ready` is rolled back to `P`
with `rollback` in the journal; a power loss simulated at each death point (the harness kills the supervisor) leaves
the stub able to start `A` or `P`. **Adversarial.** A patch touching a reserved path (`SOURCE-RESERVED`); a patch
whose realized changes exceed its footprint (`SOURCE-LEAK`); a candidate that edits `studio\active.json` (it cannot:
no capability; the harness plants the attempt and checks the pointer is unchanged); a candidate that answers
`/healthz` with another hash (not blessed); a candidate that passes the suites and hangs on launch (timeout,
`DEAD`); two promotions raced (the second refused `STUDIO-STALE` by identity of base); rustc absent. **Tests.**
`art/studio_promote.py crashtest` (the death points of §6); `art/studio_source.py selftest` (hand-written
candidates: clean, leaking, reserved, failing a suite, dead on launch); mutants (§5.2's list); the browser harness.
**Risks.** Build time on the owner's machine (the shell builds in seconds; the suites take ~70 s in the container);
the model proposing patches that do not apply (refused, counted; the request format carries the files' exact text
so the diff can be exact). **Out of scope.** Replacing the stub (documented limit); committing to git (the owner's).
**Completion.** The acceptance met, the harness green at every death point on Windows, recorded.

### B3 · STUDIO-2 — the workspace: outliner, details, comparison, the image as critic, projects (SHOULD)

**User-visible outcome.** The page becomes a studio: an **outliner** listing the scene's objects by region and kind
with a search box (the Unreal reference), where clicking selects (E) or pins (R) and tagged objects are marked; a
**details pane** for the object under the crosshair or selected — its statement, its measured geometry (bounds, size,
underside, top), its nearest wall, what a revision can change; a **candidate strip** showing the brief and each
candidate as stills from the designer's camera with the tags burned in and the touches beneath, switchable in place;
**save and open a project** (a name under `projects\`, its provenance: the generation that wrote it, the heads);
**the image as a critic**: after candidates are drawn, an optional second request sends the same still of each
candidate (1280×720, tags burned in) and asks the model to rank them and list violated constraints by tag, each
constraint checked against the scene before it is shown; prompt caching measured.

**Components.** `art/web/play.js`, `play.html`, `scene_render.js` (a still with marks, `?critic=1`), `art/play.py`
(stills on demand, project open/save endpoints), `art/studio.py` (the critic request, `VERDANDI-STUDIO-CRITIC 0`),
`art/providers/*` (image content blocks: the API's `image` source; the CLI's `--input-format stream-json`),
`art/studio_refs.py` (the outliner's listing), `art/STUDIO.md`. **Prerequisites.** B1; B2 for trying the batch's own
candidates. **Steps.** Outliner and details first (no model involved; measured data only); the strip and stills;
projects; the critic last, with its egress rule: the first still sent in a session asks the designer once (Blender's
rule). **Acceptance.** The owner can find an object by name, select it from the list, read its geometry, compare
three candidates side by side, save a project, reopen it in a fresh start with its tags and heads, and ask the critic
for a ranking that names only tags that exist and constraints that the scene confirms; `probe --references` and a
new `probe --critic` measure, with and without the image, whether the chosen candidate changes (the literature says
the image helps ranking, not coordinates; the probe will say whether it does here). **Adversarial.** A critic naming
a tag that does not exist (refused); a constraint the scene contradicts (shown as "not confirmed"); an image larger
than the tier (downsized before sending, never refused by the API); `--json-schema` with stream-json input in one
process (tested; if unsupported, the CLI critic uses `--output-format json` and the gateway's own reading).
**Tests.** The page harness; `studio.py selftest` grown; a still-with-marks row in `play.py --selftest`. **Risks.** The
page's software-GPU harness cannot screenshot (known); stills come from `?still` mode. **Out of scope.** New art
statements (B4). **Completion.** Acceptance met and measured on his machine.

### B4 · ART-2 — the vocabulary: what "connect" and "match" can mean, and a scope for an object with its parts (SHOULD)

**User-visible outcome.** The director can propose what the reference image shows and the plaza cannot say today:
**columns and piers** under a canopy (bearing into the floor's rock or a wall face, never on walkable cells); **beams
and hangers** joining two canopies or a canopy to a wall ("make @1 look like it connects to @2" becomes a real
piece); **railings and balustrades** along raised edges; **pavilion roofs** (a canopy with a pitched or stepped
profile); **props and foliage** as `asset` meshes placed by statements (café tables, umbrellas, trees from `cc0` or
`own` sources, each with its licence); and a **material library** with named families. And one grammar change in
the director: a scope pattern for **one object with its parts** (`plaza/canopy/19,10-28,11/**`), so that "change
only @1" is a verdict the director enforces, not a report the studio shows.

**Components.** `art/dress.py` (the statements and their exporter), `art/check.py` (plants for each: a column where a
player can be, a beam under the reach ceiling, a railing off its edge, a prop with no licence), `art/README.md` (the
language table), `art/director/scope.py` and `conform.rs` with new vectors (DIRECTOR-1: the parts grammar, a
`min_reader` field; the 62 vectors kept, new ones added; both implementations), `art/providers/director_prompt.py`,
`art/web/scene_render.js` (meshes beyond the cube: a small glTF-free format the exporter writes, or instanced
boxes for the first props), `art/briefs/plaza-night.art` (a revision admitted through the ledger, never by hand).
**Prerequisites.** B1; B2 to try its own candidates; B3's outliner makes the new pieces findable. **Steps.** The scope
grammar and vectors first (it is the smallest and it changes the director's verdicts); then columns and beams (the
"connect" family) with their checks; then railings and roofs; then assets and props with the licence rule; then the
material families; the prompt's language section regenerated from the README. **Acceptance.** Each new statement has
a plant the checks refuse and a probe prompt a model answers CLEAN; "make @1 look like it connects to @2" yields a
beam or hanger between them that the scene confirms touches both (`gap_m == 0` on the measured relation, by the
boxes); `probe --references` holds at the same rate as before; the second implementation reproduces every vector;
his look at the stills. **Adversarial.** A column on a walkable cell (refused by the existing check); a beam that
leaks into a pin's address (`SCOPE-LEAK` under the new grammar); an asset without a licence (refused); a mesh that
carries collision (refused by "the art carries no collision"). **Risks.** The renderer's mesh path is new work;
assets' sources and licences are the owner's to choose. **Out of scope.** Layout changes (the design tool's);
Unreal. **Completion.** The language table grown, every plant refused, the vectors reproduced in both
implementations, the probe measured, recorded.

### B5 · RELEASE-0 — install, uninstall, clean-machine proof, diagnostics, the runtime transaction, the signing decision (SHOULD → LATER)

**User-visible outcome.** An installer (or a portable zip with a shortcut script) that a second machine can run; an
uninstaller that leaves `projects\` and asks about it; a "diagnostics bundle" button (logs, the journal, the
pointer, the manifests, versions, never a key); the embeddable interpreter updated by its own transaction; a
repeatable release script that produces the layout, its manifests and the installer from a tag; a decision on
signing recorded with its cost.

**Components.** `tools\release.py`, `tools\studio.iss` (used on his ruling), `tools\sandbox.wsb` and
`tools\sandbox_test.ps1` (install in Windows Sandbox from a clean image, run the acceptance list headlessly:
start, health, a scripted edit, shutdown; simulate Edge's absence by renaming paths), the stub's rename-aside
transaction (§6), the runtime transaction (`runtime\python-3.y\` staged, a generation's manifest naming its runtime,
the pointer switching both), `docs/STUDIO-APP.md` (this document, kept current). **Prerequisites.** B1, B2.
**Acceptance.** A clean Sandbox: install, start from the icon, play, one edit through the scripted provider, close,
uninstall, `projects\` intact; the same on his machine; a signed or unsigned decision recorded with SmartScreen's
behaviour measured. **Risks.** Sandbox needs Pro; the owner's Windows edition is private — if Home, a Hyper-V VM from
his own ISO. **Out of scope.** Store distribution; MSIX.

### The backlog, classified

| class | item | batch |
|---|---|---|
| MUST | `/healthz`, `/studio/shutdown`, fixed port, `--root` forwarded, signal handling | B1 |
| MUST | write-through writes in the director; the ledger pre-created and fsynced; `crashtest` | B1 |
| MUST | the API provider on structured outputs; the CLI's missing flags; cache breakpoints | B1 |
| MUST | tags persisted; tags shown in the prompt box; click to insert; a refusal names the likely tag | B1 |
| MUST | the stub (job object, pointer, restart), the supervisor (browser lookup, heartbeat, stop order), the layout and shortcut | B1 |
| MUST | the journal and pointer with replay and death points; staging with footprint and `RESERVED`; build and suites in a job; launch and health; Try/Admit/Reject; bless and rollback | B2 |
| SHOULD | outliner, details pane, candidate strip with stills, projects | B3 |
| SHOULD | the critic with the still and its egress rule; cache measured | B3 |
| SHOULD | the parts grammar in the scope protocol (DIRECTOR-1) with vectors in both implementations | B4 |
| SHOULD | columns, beams and hangers, railings, roofs; the connect family's checks | B4 |
| SHOULD | installer or portable release script; Sandbox test; diagnostics bundle | B5 |
| LATER | assets and props with licences; material families; a mesh path in the renderer | B4 |
| LATER | the stub transaction; the runtime transaction; signing | B5 |
| LATER | WebView2 as the fallback engine (only if the lookup's logs show Edge and Chrome absent) | after B5 |
| LATER | the plaza's game checked against the Python tick from a recorded human session | separate |

---

## 8. The first vertical slice, and the prototype that can falsify the architecture

**The prototype (one or two days, before B1 is committed to).** Five experiments with pass/fail criteria, on the
owner's machine, scratch scripts under `tools\probe\`, off the gate, each ending in one verdict line (the contract's
§11 fixes their output form; by his ruling a failed kill criterion revises the architecture, and the probes never
become a gate):

1. `msedge.exe --app=http://127.0.0.1:PORT/ --user-data-dir=%TEMP%\vs-edge --no-first-run` against a running
   `play.py --port PORT`: pointer lock works (E, R, WASD, the mouse); closing the window ends the `msedge.exe`
   tree within 5 s **or** does not (then the heartbeat is mandatory, and the supervisor kills the tree; the
   architecture still stands). *Kill criterion:* pointer lock does not engage in `--app` mode → WebView2 moves from
   LATER to B1 and the plan is revised.
2. A 60-line `ctypes` script: create a job with `KILL_ON_JOB_CLOSE`, start `python play.py` suspended, assign, resume,
   start a provider through it, close the handle: every process is gone. *Kill criterion:* assignment fails under
   his shell's own job (nested jobs should allow it on Windows 8+); then the stub must `CREATE_BREAKAWAY_FROM_JOB`.
3. A 40-line pointer-swap script with `MoveFileExW(... WRITE_THROUGH)` killed by a second process at random points
   over 200 runs: the pointer always reads as the old or the new file. This measures process-kill consistency only.
   *Kill criterion:* none for correctness any longer — the pointer is a cache, and an unreadable one is rebuilt by
   the contract's R7; a torn read is recorded against axiom A1.
4. The suites at low integrity: a 50-line `ctypes` script makes a low-integrity token and runs `python art/check.py`
   and `python art/studio.py selftest` with `TMP` set to a folder labelled Low; then tries to write
   `studio\active.json` from inside: the suites pass, the write is refused. *Kill criterion:* a suite cannot run at
   low integrity (a registry or profile write it needs) → the capability boundary of §5.2 is downgraded to
   tamper-evidence, written as such, and the Try window runs at medium against a scratch copy.
5. The journal replay (accepted by his ruling of 2026-10-12, *"Define the recovery state machine and oracle before
   writing the harness"* — defined: the contract's §5–§7, and `art/studio_txn.py`): a writer makes the contract's
   records with flush and `_commit`, and the pointer by write-through rename, and is killed by `TerminateProcess` at
   random over 200 runs; after each, `python art/studio_txn.py recover` reads the directory, and its decision is
   compared with the contract for the records the writer had acknowledged, or one more. *Kill criterion:* any SAFE,
   any chain fault, or any decision not the contract's → the record form is revised before B2's promotion code, and
   B1's stub keeps the rules without a transaction.

**The slice (B1 in full).** Its files, its acceptance and its tests are in §7. Its demonstrable outcome: *the icon on
his desktop opens the plaza; he tags two canopies, matches one to the other through Claude, admits it, closes the
window; everything stops; he opens it again and the tags are there.*

---

## 9. Product-centred acceptance for the first end-to-end release

| the user can… | batch | measured by |
|---|---|---|
| 1. launch the studio from a desktop icon without a terminal | B1 | the icon; `tasklist`; the stub's log |
| 2. open and play the plaza | B1 | the page; the game's ticks |
| 3. ask the model to modify the world and compare candidates in the viewport | B1 (today's panel), B3 (the strip) | `STUDIO SELFTEST`; the browser harness |
| 4. keep the simulation state during a visual edit (a new map is a new game, as documented) | B1 | STUDIO-0's test, re-run |
| 5. save and reopen a project with its provenance | B3 | the project's manifest and heads |
| 6. request a studio code change and receive a separately built candidate | B2 | the journal's `STAGED`, `BUILT`, `CHECKED` |
| 7. launch and test the candidate without replacing the working studio | B2 | `LAUNCHED`, `HEALTHY`; two windows |
| 8. admit and promote, or reject and continue with the old version | B2 | `promote`, `activate`, `blessed`; the pointer |
| 9. recover the previous working version after a crash or an interrupted promotion | B2 | experiment 5; `crashtest`; `rollback` |

The release is not complete because a packaged executable opens; it is complete when the nine rows are measured on
the owner's machine and recorded.

---

## 10. Risk register

| risk | impact | mitigation | kill criterion |
|---|---|---|---|
| Edge `--app` keeps a background process after the last window, or pointer lock fails in it | the window's lifetime is wrong; or the world cannot be played | the heartbeat and the job; WebView2 as the fallback engine | §8.1 |
| NTFS rename under write-through is not crash-atomic on some disk or driver | a torn pointer after power loss | none needed for correctness: the pointer is a cache, rebuilt by the contract's R7; what remains load-bearing is the journal's flushed append (A2, A3) | §8.5 |
| A candidate holds a file open in the active directory so a rename fails (antivirus, a debugger) | promotion refused | cwd outside versions; retry; name the holder; never force | repeated refusals on his machine → the versions directory moves under `state\` with exclusions documented |
| The model's patches rarely apply, or the suites rarely pass | B2 is a toy | the request carries exact file text; the footprint bounds the patch; counts are recorded and reported by `report` | fewer than half of a month's candidates apply → the source domain is reduced to statement-level edits of `art/` only |
| Build time on the owner's machine | review waits minutes | the shell builds in seconds; the suites run in parallel jobs; results cached by generation hash (T3) | a candidate cycle above 5 minutes → the suites are tiered (fast first, full on Admit) |
| The API provider's schema rules drift (as `tool_choice` did) | the provider breaks silently | the self-test's mock mirrors the documented rules; `probe` is run after any provider change; the CLI stays as the second path | — |
| The charter's std-only rule against a packaging-time tool | no installer | the portable layout and the inbox-COM shortcut need no tool; the Inno script waits for his ruling | — |
| Sending stills to a model (egress) | a privacy surprise | the per-session opt-in; the still is the renderer's, never a screen capture | — |
| The suites or Python cannot run at low integrity (a write outside the low-labelled scratch) | the capability boundary is weaker than §5.2 claims | experiment 4 first; the boundary downgraded in writing, not quietly | §8.4 |
| A stale basis is accepted (a validator or the toolchain changed after validation) | an old verdict authorizes a different candidate | the basis is recorded at PROPOSED and compared at PROMOTE; `SOURCE-STALE` revalidates or discards; a mutant that skips the comparison must fail | — |
| Self-improvement promotes a generation that breaks the gate's trees | the owner's repository diverges from the certified program | reserved footprints; `OWNER-GATE` marking; the supervisor never commits | — |
| Scope creep into a plugin framework or a general engine | the product stalls | the backlog's classes; one protocol, domain validators, no plugin API | — |

---

## 11. Immediate next actions, in order

**The working rule from here** (the review he brought on 2026-10-12, put as *"agree?"*; agreed): *"No new
architecture proposal, theorem, verification rung, or candidate-design patch unless implementation exposes a
concrete defect that the current contract cannot handle."* B1 is *"one end-to-end desktop application milestone"*,
done when he can open Verðandi from a desktop icon, walk the plaza, select an object and see its stable tag, ask the
director to change it, see the candidate in the renderer, reject a bad edit without damaging the world, and restart
without losing the saved intent and history.

1. On his machine, the five probes of §8 (`tools\probe\`), alongside B1 rather than before all of it: 1 and 2 decide
   the supervisor's and the stub's shape; 3, 4 and 5 bear on B2.
2. B1's second part, after probes 1 and 2: the supervisor, the stub, the layout and the shortcut; the acceptance on
   his machine; `probe` run on the API provider with his Console key.
3. B2's journal and pointer with their death-point harness, before any other part of B2.
4. His rulings: recorded in the contract's §1, the default model among them (Opus 5.5, configurable).

---

## 12. What this plan does not show

That the architecture works: it is decided from documentation and the repository, and §8's prototype is where it is
first measured. That VCT-0 is a theorem: it is three claims with named parents and an explicit axiom list, held by a
harness for process-kill consistency, not proved, and not measured for an operating-system crash or a power loss.
That the capability boundary holds beyond what Mandatory Integrity Control documents: an administrator, or code
already at the user's integrity level, is outside it. Anything about the quality of what a model proposes for source
or for art. The behaviour of Edge, WebView2 or Windows Sandbox beyond what the cited pages say. Whether the owner
accepts a packaging-time tool. Nothing here enters the certified gate; the gate stays at 251 rows. The contract
([`STUDIO-CONTRACT.md`](STUDIO-CONTRACT.md)) says what its reference measured and what that does not show (§8).

Sources: the research notes and report of 2026-10-12 (`docs/RESEARCH-FINDINGS.md`, R-15, lists the primary pages);
the repository at HEAD `58917b7`.

---

## 13. The review of 2026-10-12, verified before agreement

The owner brought three reviews of this plan and asked that their claims be searched before anything was agreed
(*"websearch this before agreement"*). Each claim that bears weight was checked against a primary page the same
day; the table says what was found and what the plan now does.

| the reviewers' claim | found | the plan |
|---|---|---|
| "Fable 5.1 is cheaper but weaker" (first review) | **wrong on price**: Fable 5.1 is the most expensive of the four, $10 / $50 per million tokens; Sonnet 5.5 $2 / $10, Opus 5.5 $4 / $20, Haiku 5.5 $0.10 / $0.50 (VERIFIED: [pricing](https://platform.claude.com/docs/en/about-claude/pricing)); on relative strength no benchmark was read | the default model stays the owner's ruling; the prices are in §11 |
| `tool_choice: tool` → `output_config.format` "should be validated against the exact model and API" (second review) | **validated**: "`any` and `tool` return a 400 error" on Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1 ([implement tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)); `output_config.format` with `type: "json_schema"` is the Messages API's parameter ([API reference](https://platform.claude.com/docs/en/api/messages), [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)); the CLI's `--json-schema` already worked on his machine with Opus 5.5 | B1 step 4 stands; the self-test's mock will refuse the old shape as the API does |
| `_commit` is not evidence that directory entries or a later rename are durable (second review) | **right**: `os.fsync` on Windows is `_commit` ([os](https://docs.python.org/3/library/os.html)), which "forces the operating system to write the file associated with fd to disk" and says nothing of the directory ([_commit](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/commit)) | axioms A2 and A3 in §5.2; three consistency levels claimed separately |
| "NTFS rename with `MOVEFILE_WRITE_THROUGH` is crash-atomic" is too strong (second review) | **right**: no Microsoft page says "atomic" (§2.2) | axiom A1, a hypothesis; the harness measures process-kill consistency only |
| Separate failure isolation, promotion correctness and recovery correctness (second review) | a structural point, not a factual one | adopted: §5.2's three claims |
| "Process separation is not capability isolation" (second review) | **right**, and answerable: Mandatory Integrity Control's `NO_WRITE_UP` default, "a principal with a low integrity level cannot write to an object with a medium integrity level, even if that object's DACL allows write access" (VERIFIED: [MIC](https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control)); a low-integrity process by `SetTokenInformation(TokenIntegrityLevel)` and `CreateProcessAsUser` (VERIFIED, an archived article) | adopted: candidates validate and Try at low integrity; experiment 4; the limit written (administrators, medium-level code) |
| `??=` must not keep a corrupt pointer; missing and invalid differ (second review) | a semantic point | adopted: `??=` for missing only; invalid recovers from the journal, recorded |
| A generation hash is not a complete cache key (second and third reviews) | **right**, by Build Systems à la Carte's verifying traces (§2.4) | adopted: the basis record `B_C`; a suite result reused only on an identical basis; both reuse and invalidation tested |
| Checkpoint freshness: bind a candidate to its base generation, source revision, validators, toolchain and configuration; three outcomes — fresh, stale but reusable, stale and invalidated (the third review's refinement) | consistent with T3 and `STUDIO-STALE` | adopted as `Fresh(C, B_now)` and `SOURCE-STALE` |
| Verify the manifest and content before launch, at "microseconds per launch" (third review) | the cost claim is **unsupported**: hashing a generation is proportional to its size and the disk | adopted: `Integrity(G)` before activation and recovery, its time measured and reported |
| `tries = 3` as a theorem clause (third review) | a policy | adopted as policy: the clause is that a counter exists and is decremented by rename |
| A flipped verdict is a changed decision boundary, not automatically a regression (second review) | a semantic point | adopted for the verdict-drift probe: old verdicts and their inputs kept; flips classified, not failed |
| A rendered view can reveal private project content; disclose what leaves the machine and to whom (second review) | agrees with Blender's rule (§2.3) | adopted for B3's critic: per-session consent naming the provider and what is sent |

The rulings the reviews recommended (a packaging-time tool as an optional path; tags persisted and shown; the
default model configurable; session-scoped consent for stills; the three probes accepted off the gate) are
recommendations until the owner rules; §11 asks him.

**The second review (the same day).** Brought with his host run of 0209 (251 rows / 0 fail, pushed
`2517a27..f99c494`): rulings on §11's items and the journal-replay court; a correction that *"five states are not
yet a complete recovery specification"* (*"journal state and runtime state are separate dimensions"*; *"Do not let
the journal alone determine recovery"*; *"At which durable operation does promotion become committed?"*); and the
request for *"a short Studio Architecture Contract that freezes these interfaces and transaction semantics before
B1"*. Each repository contract the review named was looked up (the contract, §10: all exist; BOT-REF-0 is a
deterministic bot, not a model; HERMENEUTICS-0 is not a source fence; environmental independence is a deferred
audit, not a finding). The current models and prices were checked again. Done: the contract — the commit point at
`blessed`, the tries in the journal, the stub the only writer of the commit, `Recover(J, P, F)` as a sixteen-rule
table — and its reference, `art/studio_txn.py`, checked exhaustively in the container.
