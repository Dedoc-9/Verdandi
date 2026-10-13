<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The studio: a director summoned into the running plaza (STUDIO-0, STUDIO-1)

By the owner's direction of 2026-10-11: *"the LLM edits design intent; Verðandi compiles that intent into a live
world; the designer remains in control."* And by his ruling on how a model is reached: *"a pluggable model adapter,
with a persistent local director service behind it"*, starting with *"a CLI adapter so the first implementation
remains standard-library-only"*; *"the model proposes changes—it never directly mutates the live world. Verðandi owns
validation, compilation, preview, and admission."*

```text
 the page (art/web/play.js)          play.py                    art/studio.py, the gateway          a provider (a command)
 E target, R pin           ──POST──►  token, host  ──────────►  tags bound to objects
 Enter summons, @1 @2 …    ──POST──►  token, host  ──────────►  context from the head  ──stdin──►  the model, or a script
                                                                 limits, cancel, time    ◄─stdout─  ≤ 3 candidates (JSON)
                                                                 the response, read whole
                                                                 each candidate an intent ──► art/director.py: checks, scope
 [ Show ] swaps the scene  ◄──/live── candidates as sources  ◄── those not refused, compiled
 [ Admit ] [ Reject ] [ Undo ] ─────►  the director's ledger: evaluate, admit / refuse; the brief written
```

## Using it

```
python art/play.py plaza-night --director art/providers/scripted.json
python art/play.py plaza-night --director art/providers/claude_code.json
python art/play.py plaza-night --director art/providers/anthropic.json
```

The first needs no model: `art/providers/scripted.py` answers a selected canopy with three fixed variations (the three
of the owner's sketch: *Monolithic*, *Lit underside*, *Deeper canopy*) and anything else with nothing. It reads a
prompt only for the word *magenta*: it understands nothing, and is there so that the studio can be tried and tested.

The second asks a Claude model through Claude Code's command line (`claude -p`), on the login Claude Code already has:
no key is set for it. By the owner's ruling of 2026-10-11 it is the first real provider, for his own development
setup, *"not a substitute for a properly authorized provider integration in a product offered to other users"*. Its
settings, both optional, are in the environment: `VERDANDI_DIRECTOR_MODEL` (as `claude --model` takes it, an alias
such as `sonnet` or a full name; Claude Code's default if not set) and `VERDANDI_CLAUDE` (the executable, if `claude`
on the PATH is not it; on Windows `claude.exe`, since a `.cmd` or `.ps1` shim runs only under a shell and is refused).

The third asks a Claude model through the Anthropic Messages API, with a key from the Claude Console. The key is in
the environment, never in a file: `ANTHROPIC_API_KEY`. The model is the configuration's (`art/providers/anthropic.json`
passes `--model claude-opus-5-5`, the model his Claude Code CLI answered as, so the two providers differ in the adapter
alone; B1, 2026-10-12); `VERDANDI_DIRECTOR_MODEL` overrides it, and `VERDANDI_DIRECTOR_API` names another endpoint. The
answer is constrained by structured outputs (`output_config.format`, a JSON schema; the JSON is the answer's text), not
by a forced tool choice, which every current model refuses with 400; the schema sent is the gateway's with what
structured outputs do not support moved into its descriptions, and the gateway still enforces every limit. A refusal
or an answer cut at its token limit is said and not read.

The two model providers tell their models the same thing (`art/providers/director_prompt.py`: one system text, and the
request rendered as text), and differ only in how the model is reached.

```
python art/studio.py probe art/providers/claude_code.json
python art/studio.py probe art/providers/claude_code.json --references
python art/studio.py report
```

`probe` is the owner's smoke test, *"that the model was actually invoked—not just that a provider configuration was
loaded"*: it asks about the same canopy with two different prompts, through the gateway as the page asks, records both
requests (marked as the probe's), admits nothing, and says SHOWN only if the provider reported a model and tokens for
each and no two prompts were answered with the same revision lines. The scripted provider is NOT SHOWN, by design.
`probe --references` is STUDIO-1's measure, the owner's acceptance criterion put to a model (*"the model consistently
identifies the intended objects, receives their actual geometry, and proposes edits the existing compiler can
express"*): the north canopy the target `@1`, the west and south canopies pinned `@2` and `@3`, four prompts that each
name what to change (*make @1 match @2*; *make @1 twice as deep; keep @2 and @3 exactly as they are*; *give @2 a warm
glow along its edge, and leave @1 and @3 alone*; *make @1 look like it connects to @2, without changing @2*), each asked
twice (`--runs N`); for every candidate, which tags it changed and how many untagged objects, against what the prompt
meant, and its verdict. Each request costs a model call. `report` reads every recorded request of the brief and gives, by provider configuration, what the owner asked to
compare: the requests answered, invalid outputs, timeouts and provider errors, the provider's time (median and
longest), the candidates' verdicts, the edits admitted from the page, the tokens, and the cost where a provider reports
one, per admitted edit.

In the page: what is under the crosshair is named in the corner, by its address (`plaza/canopy/19,10-28,11`) and its
tag if it has one. **E** makes it the target; **R** pins it as a reference, or unpins it, up to four (the game's reset
is **Backspace** here). play.py gives each a tag, `@1`, `@2`, …, which names that object, and keeps it across restarts; each
tagged object is framed and labelled on screen (the target amber, a pin dashed blue), and the panel lists them with
their addresses, sizes and statements' lines. **Enter** opens the director's panel, and the game goes on. Type the
change, naming objects by their tags (*make @1 match @2*); **Ctrl+Enter** asks. The candidates come back with their
verdicts and what each touches (*@1 changed · @2 unchanged · no other object changed*). **Show** draws one in place:
the scene changes, the game, the player and the camera do not. **Original** draws the brief. **Admit** writes it
through the director's ledger, **Reject** records a refusal, and **Undo** admits the last admission's exact inverse.
**Cancel** stops a request, and **Esc** goes back to the world. Without a target, the prompt is for the whole world.

## The references (STUDIO-1)

By the owner's ruling of 2026-10-11: *"Bind references to a scene revision and object identity, not just a reusable
tag. If an edit invalidates a reference, report it rather than silently redirecting it."*

- **An object** (`art/studio_refs.py`) is a box of the scene's dressing with its parts: an id that extends another by
  `:something` is a part of it (a canopy's ribs, downlights and edge fixtures, a tower's cornice), and a light belongs
  to the object whose id it shares. An object's identity is its id, which holds its cells: a canopy given new corners
  is a new object.
- **A tag** is made the first time an object is selected or pinned, and names that object, by its id; it is never
  given to another. B1 (docs/STUDIO-CONTRACT.md §9): the tags are kept in `art/ledger/<brief>.tags.json`, written whole
  and flushed, so a restart keeps them; the counter only grows, so a tag is never reused; a tag whose object is gone
  stays, listed apart. The panel shows every tag as a chip, and a click puts it into the prompt; a prompt naming a tag
  that is not the target or a pin is refused with what that tag names and how to pin it. A probe keeps no tags file. Selecting or pinning it again binds it again to the scene and head of
  that moment. Its status, in the panel and in `/live`, is read against the scene served: *ok*, *changed* (the same
  object, another shape or look than when it was bound), or *gone* (no object of its id).
- **A request** carries the target and the pins (below). A prompt that names a tag that is neither, or a tag whose
  object is not in the scene at the head, is refused before anything is asked (`STUDIO-REFERENCE`).
- **What each candidate touches** is the gateway's own account, from the director's verdict (what it realized and
  what a changed material affected): each tag changed or unchanged, the untagged objects of the head it changed, and
  the objects it made that the head has not.

## A provider's configuration

```json
{"provider": "cli", "argv": ["{python}", "art/providers/scripted.py"], "model": "scripted-1", "timeout_s": 30, "max_output_bytes": 65536}
```

`argv` is a list of arguments, run from the repository's root without a shell; `{python}` is the Python that runs
play.py. `model` names what answers, for the record. `timeout_s` (1–600) and `max_output_bytes` (1 KiB – 4 MiB) are
limits; past either, the command is killed. A configuration that is not exactly this is refused whole
(`STUDIO-CONFIG`), and play.py serves the world without a director.

## The request (on the provider's standard input)

`VERDANDI-STUDIO-REQUEST 1`, one JSON document (version 1 since STUDIO-1: `target`, `references`, `relations`, `mentions`
and `coordinates` in place of version 0's `selection`):

| field | |
|---|---|
| `id` | the request's id; the response must name it |
| `brief`, `head`, `base` | the brief, and the head the request was made at (the director's head and its three parts) |
| `prompt` | the designer's words, 1–2,000 characters |
| `target` | null, or the target's reference (as in `references`) |
| `references` | the target and the pins, each: its tag and role, whether the prompt mentions it, its id, address, kind, region and material; the brief's statement that made it (line, text, key), how many objects that statement makes, and what a revision of it can change; the address patterns it falls under (`plaza/canopy/*`, `material/concrete_slab`); its geometry (bounds, centre and size in metres, underside and top, long axis, orientation, its boxes and parts and lights, and the direction its lights point where the scene records one); the nearest wall of the play geometry (which, on which side, how far in plan and in space, its top); and its binding (the scene and head it was bound at, and whether it has changed since) |
| `relations` | for every two references: the gap between their boxes, whether they touch, their overlap in plan, the direction and distance from one centre to the other, the differences of their undersides and tops, whether they share a kind, a material, a statement, each marked *measured*; and, where the first records a facing, whether it faces the second, marked *inferred* (a half-space test on centres, not a line of sight, not a connection) |
| `mentions` | the tags the prompt names |
| `coordinates` | metres; x east, z south, y up; yaw 0 north; the cell's size and the walls' height; a box's six numbers |
| `camera` | where the designer stands and looks: x, y, z (metres), yaw and pitch (degrees) |
| `statements` | the brief: every statement's line, text and key |
| `revision_syntax`, `language` | how a revision is written, and the art file's statements as `art/README.md` describes them |
| `respond` | the response's format, the id again, at most 3 candidates, and the JSON Schema they follow |

## The response (on its standard output)

`VERDANDI-STUDIO-RESPONSE 0`: `{"format", "version": "0", "id", "provider": {"name", "model"[, "usage"]}, "candidates": [...]}`,
at most three candidates, each with exactly these fields (`python art/studio.py schema` prints the schema, which a
provider that supports constrained output should constrain its model to):

| field | |
|---|---|
| `title` | a few words, at most 80 characters |
| `rationale` | what the change means, at most 1,200 characters |
| `revision` | 1–16 lines: `= <statement>` replaces the statement with the same key, `+ <statement>` adds one, `- <key>` removes one |
| `scope` | 1–12 address patterns: everything outside them must stay as it is |
| `preserve` | what it means to keep, in words, at most 12 (recorded, and shown; the scope check is what holds it) |

`usage`, if a provider gives it, is exactly `{"input_tokens", "output_tokens", "cost_usd", "cost_basis"}`: two counts,
a cost in dollars or `null`, and a few words saying where the cost comes from (Claude Code's own client-side estimate;
the API's token counts with no cost, since prices are not a provider's to know). It is recorded, never charged against
anything here.

An exit status other than 0 is a failure; the last line of the provider's standard error is shown. An empty list of
candidates is an answer: *the director proposed nothing*.

## What the gateway does with it

The response is read whole or refused whole. Each candidate becomes a `VERDANDI-INTENT` (art/director/intent.py):
the gateway gives it its letter (A, B, C), the base it was asked at and the designer's prompt; the provider gives the
rest. The director evaluates each at the current head (the art checks, and the scope check). A candidate it refuses is
shown with the reason and never drawn; one it finds CLEAN or LEAKAGE is compiled and served as a source the page can
switch to. Only a CLEAN candidate is admitted from the page, and only after it is evaluated again at the head as the
files stand and that head is the one it was drawn at.

| code | when |
|---|---|
| `STUDIO-CONFIG` | the configuration is not exactly as above |
| `STUDIO-NO-PROVIDER` | no director is configured |
| `STUDIO-PROMPT`, `STUDIO-SELECTION` | an empty or too long prompt; a piece the head's scene does not hold |
| `STUDIO-REFERENCE`, `STUDIO-PINS` | a prompt naming a tag that is not the target or a pin; a tagged object not in the scene at the head; the target pinned; an unpin of what is not pinned; a fifth pin |
| `STUDIO-PROVIDER-START` | the command cannot be started |
| `STUDIO-TIMEOUT`, `STUDIO-RESPONSE-SIZE` | past its time; past its output limit (killed) |
| `STUDIO-CANCELLED`, `STUDIO-SUPERSEDED` | cancelled by the designer; a newer request asked (killed, its result discarded) |
| `STUDIO-PROVIDER-EXIT` | it exited with an error (its last line of standard error shown) |
| `STUDIO-RESPONSE-JSON`, `-FORMAT`, `-ID`, `-FIELD`, `-CANDIDATES`, `-REVISION`, `-SCOPE` | the response is not JSON, not this format, for another request, or a field breaks its rule |
| `INTENT-*`, the director's verdicts | a candidate that is not an intent, or that the director refuses (`INTENT-APPLY`, `CHECK-FAILED`, …) or finds leaking (`LEAKAGE`) |
| `STUDIO-STALE`, `STUDIO-NOT-ADMISSIBLE`, `STUDIO-DECIDED`, `STUDIO-NO-CANDIDATE` | at admission: the head moved since it was drawn; not CLEAN; already decided; no such candidate |
| `STUDIO-DIRECTOR-REFUSED` | the director itself refused the admission, refusal or undo (its own reason shown) |
| `STUDIO-NOTHING-TO-UNDO`, `STUDIO-NOT-UNDOABLE` | no admission left to undo (an undo is never itself undone; undo again walks further back); one that changed the layout, or whose inverse is not CLEAN |

## What is kept

Every request, under `art/build/studio/BRIEF/ID/` (never committed): `request.json`, `response.raw`, and each
candidate's intent (`A.intent`, …); and one line a request, admission, rejection or undo in
`art/build/studio/BRIEF/requests.jsonl`: the head, the configuration and the model it names, the prompt, the
target's address and every tag's object, the sha256 of the request and the response, and, as the owner asked (*"Record the provider, model, exit
status, schema-validation result and latency, without logging secrets"*), the provider and model the response names,
the exit status, whether the response was valid, the provider's time in milliseconds, the usage it reported, each
candidate's verdict and what it touched, and the outcome (a probe's requests are marked `"origin": "probe"`). Nothing a provider is given
or gives holds a credential, and none is recorded. play.py also prints one line a request (`STUDIO  ID  provider
(model)  time  tokens  A CLEAN; B LEAKAGE …`, or its refusal). A recorded candidate is played again without
the provider: `python art/play.py BRIEF --intent art/build/studio/BRIEF/ID/A.intent`. Admissions, rejections and undos
are in the brief's ledger (`art/ledger/BRIEF.ledger`), as `art/director.py` writes it.

## Its boundary

A provider is a command with an argument list, never a shell line; the request reaches it on its standard input, never
in its arguments. It is limited in time and in output, and killed when cancelled or superseded, with everything it
started: it runs in a process group of its own (POSIX), or is ended with `taskkill /T` (Windows), so that a model's own
command line cannot outlive a cancellation. play.py, stopping, does the same to a request running.

`claude_code.py` runs `claude` from an empty temporary folder with `--tools ""`, `--disallowedTools "mcp__*"`,
`--strict-mcp-config`, `--safe-mode`, `--no-session-persistence` and `--permission-mode dontAsk`, its own system text
(`--system-prompt-file`), the gateway's schema (`--json-schema`) and `--output-format stream-json`, so that the
session's first event, which lists the tools it offers, is read before its answer. If it offers any tool but
`StructuredOutput` (the means by which it holds its answer to the schema), claude is stopped and nothing it said is
used. Measured in the build container (Claude Code 2.1.296): `--tools ""` alone left a connected MCP server's 22 tools
offered; with `--disallowedTools "mcp__*"` the session offered `StructuredOutput` alone. The gateway reads its answer
again, whole, as it reads every provider's: the CLI's own enforcement of the schema is not relied on.

A provider's keys are in its environment; nothing of it reaches the browser but the candidates' text and their
verdicts, and the name, model and usage its response gives. The page's requests to play.py carry a token the page is
served with, in a header that a page of another origin cannot send without a preflight play.py never answers, and
every request, a GET too, must name 127.0.0.1 or localhost as its host: a page of another site that rebinds its own name
to 127.0.0.1 (DNS rebinding) is answered 403, so it reads neither the page's token nor the world, the prompts or the
queue. Nothing is admitted without the designer, and nothing reaches the
world but what the director judged.

## Crash safety, and what a supervisor reads (B1)

Every admission is written so that a process killed at any point leaves the brief and its ledger at the parent or
the child, never between: `art/director.py`'s docstring says how, and `python art/director.py crashtest` kills an
admission at each of its writes and recovers it (14 cases). Every director command, and play.py's start, recovers
first. One writer at a time: every writer of a tree's ledgers, briefs, tags and maps holds the tree's content lock
(`art/build/content.lock`; a thread lock in a process and the system's lock between processes, which the system releases
when its holder dies); an admission holds it from before its first write to after its last and reads the head again
under it, so a second admission drawn at the same head is refused (HEAD-MOVED) instead of writing over the first; and
recovery takes the same lock, so while an admission is alive a recovery refuses (LEDGER-BUSY) and changes nothing.
`python art/director.py racetest` (32 cases) puts a second admission and another process's recovery at each of an
admission's writes, and keeps the plants that break it. Briefs share the graybox's maps, so a layout admitted in one
world would change every world that plays its map: a layout change is refused while another brief plays the map
(SHARED-MAP), an art change admitted as before, until each world keeps a map of its own. play.py answers `GET /healthz` (`ready`, `version`, `page`, `page_age_s`, `bye_age_s`, `pid`), takes the page's
heartbeat on `POST /studio/alive` (every 5 s) and its goodbye on `POST /studio/bye` (a `pagehide` beacon whose body is
the token, since a beacon cannot set a header), and stops on `POST /studio/shutdown`, SIGTERM or Ctrl+Break; it exits
0 stopped, 70 when its port is taken (bound exclusively on Windows), 75 when recovery refuses.

## The desktop studio (B1)

```
python art\studio_app.py shortcut --director art\providers\claude_code.json    once: a desktop icon, "Verdandi Studio"
```

The icon starts `pythonw art\studio_app.py`, the supervisor: it joins a job object of its own (so play.py, the
provider and the browser end with it), starts play.py on a free port without a console, opens Edge in application mode
with a profile of its own, and stops everything when the window is closed (the page's goodbye, not followed within 3 s
by its speaking again, as a reload does), when the page has not spoken for three minutes and no request is running (a
silent page is not a closed window: Edge's sleeping tabs freeze a background page's timers; while a provider works,
the studio waits for it, then stops), or when play.py ends. A second click opens another window on the same studio. Errors are shown in a dialog and kept in
`%LOCALAPPDATA%\VerdandiStudio\state\logs\`. `shortcut` keeps the shell's non-secret variables for the icon
(`VERDANDI_CLAUDE`, `VERDANDI_DIRECTOR_MODEL`, `VERDANDI_DIRECTOR_API`); a key never: for the API provider,
`ANTHROPIC_API_KEY` must be a user environment variable. Claude Code's native install
(`%USERPROFILE%\.local\bin\claude.exe`) is found without any. `python art/studio_app.py selftest` holds the lifecycle
with a stand-in browser (10 cases; 11 on Windows, where a live job's process list is read as well).

## What is not shown

The quality of what a model proposes: the checks hold a candidate to the rules of the art and to its declared scope,
not to taste. The live Anthropic API: `anthropic_messages.py` is held only to a local server that answers as the API's
documentation describes. `claude_code.py` has been run against the real CLI in the build container (Linux) and on the
owner's Windows machine (`claude.exe` from Claude Code's own installer, his Claude plan, 2026-10-12), its probes SHOWN
in both; a `.cmd` or `.ps1` shim is refused, not measured beyond the self-test's. That a model
identifies the intended objects in general: the references' probe is four prompts about three canopies, a few runs,
one model. A tag on a light or a play piece (E and R pick the dressing's boxes; a light goes with its object). Tags
shared between two pages at once. The structured-outputs request against the live API (no key here). An image of the view (the next slice, by his sequence) and
pieces that connect two objects (after it). A scope pattern that names one object with its parts: the director's
grammar has none, so a model told only an object's exact address declares a scope that leaves its ribs and lights
out (`SCOPE-LEAK`); the request now says so. Changes to the layout (the look only; a layout change is the design
tool's). A long-running worker: each request starts the provider's command afresh, which the owner allowed for the
first version. A latency in general: the scripted provider answers in well under a second, and Claude Code's CLI took
9–17 s a request in the build container's probes, which says nothing of another machine, model or prompt.
