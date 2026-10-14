<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The studio: a director summoned into the running plaza (STUDIO-0, STUDIO-1, STUDIO-2, STUDIO-3)

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

In the page (since STUDIO-3 the page opens in the editor; **P** plays, and in play what follows is what is under the
crosshair; in the editor it is what is selected): what is under the crosshair is named in the corner, by its address
(`plaza/canopy/19,10-28,11`) and its tag if it has one. **E** makes it the target; **R** pins it as a reference, or unpins it, up to four (the game's reset
is **Backspace** here). play.py gives each a tag, `@1`, `@2`, …, which names that object, and keeps it across restarts; each
tagged object is framed and labelled on screen (the target amber, a pin dashed blue), and the panel lists them with
their addresses, sizes and statements' lines. **Enter** opens the director's panel, and the game goes on. Type the
change, naming objects by their tags (*make @1 match @2*); **Ctrl+Enter** asks. The candidates come back with their
verdicts and what each touches (*@1 changed · @2 unchanged · no other object changed*). **Show** draws one in place:
the scene changes, the game, the player and the camera do not. **Original** draws the brief. **Admit** writes it
through the director's ledger, **Reject** records a refusal, and **Undo** admits the last admission's exact inverse.
**Cancel** stops a request, and **Esc** goes back to the world. Without a target, the prompt is for the whole world.

## The shell (STUDIO-3, 0230)

By the owner's plan of 2026-10-14 (Sprint 1, *"Core studio shell"*: *"Launch Verðandi, enter the world, select an
object, inspect it, and play"*), the page is a studio around the play surface, after his mockup: a menu bar (File, Edit,
View, World, Tools, Build, Play, Validate, Help; on its right **Local Build**, **Play (1080p)** and **Validate**), a bar
naming the scene (the world), the layer and the selection, with what play.py says (connected, the world, the ledger's
revision, the source drawn and its scene, the rules), a navigator (World, Create, Content, Review), the viewport, an
inspector with the world's layers and settings, and a dock of the asset browser, the candidates and the ledger.

Nothing in the shell is the world. It reads what play.py serves and asks play.py to act, through the routes the studio
already had and three new ones: GET `/object.json` (what a picked box's object is, read from the scene and lineage of the
source drawn: its address, kind, region, boxes, materials, the mesh the scene names, whether it collides, the statement
that made it and how many objects that statement makes, its nearest wall; a box of the play geometry is the map's and
says so; nothing is bound and no tag is made), GET `/validate.json` (the art checks' rows as they were run when the
source was compiled, and its latest refusal if it was refused; read back, not run again) and POST `/studio/build`
(every source compiled again now, as the watcher does on an edit, with the page's token; what fails leaves the scene
before it drawn).

**The editor.** The page opens in it: a free camera (right-drag looks, the right button held with W A S D flies, Q and E
down and up, the wheel moves forward), the cursor naming what it is over, a click selecting it. The pick is the view's
arithmetic: the ray through the cursor's pixel and the nearest box it enters of the layers shown, the dressing, the
play geometry, the movers and the standing targets. The selection is drawn as its box, projected in blue on a canvas over
the picture; **F** frames it. **P** (or Tab, or the tool strip's last button) plays: the mouse is captured and the game's
keys apply, as before; **Esc** comes back to the editor at the player's eye. The game waits while it is not played.
**Play (1080p)** plays at 1920 × 1080, the window filled, the picture 16:9. **E** and **R** make the selection the
director's target or pin it; in play they take what is under the crosshair, as before. A box of the play geometry, a
mover or a target can be inspected, not tagged: it is the map's.

**The viewport.** The tool strip: select (Q) and measure (T: two clicks, the distance between the points the rays hit,
in plan and in rise); move, rotate and scale are drawn and not built, and say why (nothing in the editor moves the
world). The pills: Perspective (and Top and Side, telephoto cameras: the renderer draws in perspective only, and they say
so), Lit (the renderer's picture, with the dressing's wireframe or the play geometry drawn over it), Show (the grid of
cells, the regions, the spawns and targets, the tags, the statistics). The statistics are what the page measures and no
more: frames a second, the frame's time, the time to issue it (the GPU's is not measured), the draw calls the renderer
made (counted), its triangles, boxes and lights, and the canvas's size; video memory is *n/a*, since WebGL does not
report it.

**The panels.** The inspector: Transform (the boxes' centre and size, read-only; nothing is rotated), Static Mesh (the
asset the scene names, its source and licence), Materials (each with a flat swatch, a key and not the renderer's
picture), Collision, LOD, Physics, Gameplay Tags (the studio's tag) and Custom Properties (the statement, its key, what
it makes and can change, the nearest wall, the lights). Layers: each shown or hidden (the renderer is given the scene
without it; the game is not touched) and locked or not (never picked); the bar's Layer limits a click to one. World
Settings: the environment, the grid, the player's constants, the spawns, the regions, the views, the source. The asset
browser: the scene's own pieces by folder (the dressing by kind, the play geometry by kind, the movers, the spawns and
targets, the lights, the materials, the regions, the views, and the views saved in the page, each with the art
statement it would be), each drawn as a thumbnail by a second renderer from a camera framed on it: the scene as it
stands, from there. The candidates: the request's, each drawn the same way from the target's frame, with its verdict
(*Ready* when CLEAN and undecided), its rung, and Show, Admit and Reject, which do what the director's drawer does (an
admission brings its still, as ADMISSION-0 requires). The ledger: `/history.json`, newest first, ADMITTED, CANDIDATE,
REJECTED, REFUSED, REBASED. The director's panel is a drawer over the inspector (Enter). A footer keeps the roadmap
in view: Sprint 1, the shell; then Mark & Shape, the candidate loop, a world-generation slice, the dynamic world,
scale.

What is not built says so, with why: Geometry (the layout changes through the design tool), Voxel Tools (the world is
cells and boxes), Decals (no statement), Audio (the studio cannot make it yet), AI (none), Prefabs (one statement makes
one object), Procedural (a later slice), Templates (a world is a duplicate of one), Compare (with Mark & Shape). Stills
(`?view`, `?cam`, `?still`) are the picture alone, as before.

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

`VERDANDI-STUDIO-RESPONSE 0`: `{"format", "version": "0", "id", "provider": {"name", "model"[, "usage"][, "stop_reason"]}, "candidates": [...][, "outcome": {...}]}`,
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

An exit status other than 0 is a failure; the last line of the provider's standard error is shown.

**Every request ends in a disposition (0220).** His first queued prompt, to add a figure, came back *"the director
proposed nothing"*, with no reason: the art file says canopies, towers, neon, lamps, puddles, materials, the sky and
the air, and nothing of people, vehicles or props, and the studio could not say so. Now the request publishes
`capabilities`: what the studio can make (`look.material`, `dressing.canopy`, ...) and, by name, the closed list of
what it cannot make yet (`entity.person`, `entity.vehicle`, `motion.path`, `motion.surface`, `mechanism.door`,
`physics.dynamic`, `audio`, ...). The response may carry `outcome`, the model's account when it proposes nothing:
`{"kind": none | unsupported | ambiguous | declined, "unmet": [names from that list], "questions": [...], "reason":
content | rights | safety | other, "note": "..."}`. The gateway decides, the host's observations first:

| disposition | when | decided by |
|---|---|---|
| `REALIZED` | one to three candidates came back (each then has its verdict: CLEAN, LEAKAGE, REFUSED) | the studio |
| `DECLINED` | the provider's API reported a refusal (`stop_reason` refusal, which the adapter passes on) | the studio |
| `UNSUPPORTED` | no candidates, and the outcome names what is needed from the list of what the studio cannot make | the provider (its account) |
| `AMBIGUOUS` | no candidates, and one to three questions for the designer, shown as text and never carried out | the provider |
| `DECLINED` | no candidates, and the provider declines with a reason from the closed list | the provider |
| `FAILED` | the provider could not be run or read (`STUDIO-*`), or it answered nothing and gave no reason (`STUDIO-EMPTY-WITHOUT-REASON`) | the studio |

An outcome that names a capability the studio has, or one the request never listed, refuses the response
(`STUDIO-RESPONSE-OUTCOME`). `INFEASIBLE` and `PROJECTED` are reserved for a repair stage that is not built. No
disposition but `REALIZED` evaluates, draws or writes anything: the brief and its ledger stay byte for byte as they
were. The scripted provider gives `UNSUPPORTED` when a word of the prompt is in its small list (a person, a vehicle, a
door, ...): word matching, not understanding. Whether Claude Code's CLI passes the API's stop reason on is not
measured; if it does not, a refusal on that path reads as `FAILED` or as the model's own account.

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
| `STUDIO-NO-STILL`, `STUDIO-STILL-FLAGGED` | at admission (ADMISSION-0, 0222): no still taken of the candidate as drawn; a still the detectors flag, admitted only with "Admit despite" |
| `STUDIO-DIRECTOR-REFUSED` | the director itself refused the admission, refusal or undo (its own reason shown) |
| `STUDIO-NOTHING-TO-UNDO`, `STUDIO-NOT-UNDOABLE` | no admission left to undo (an undo is never itself undone; undo again walks further back); one that changed the layout, or whose inverse is not CLEAN |

## The record and the still (ADMISSION-0, 0222)

Each candidate's card shows what the studio computed of it: its rung and why (from what changed, never from the
model's words), what an admission needs, and, folded, what was not checked. **Admit** draws the candidate if another
source is shown, waits two frames, takes the canvas as a PNG (a copy at most 960 pixels wide) and gives it to play.py
(`POST /studio/still`, the studio's token, the PNG as the body), which keeps it and reads its detectors (QUALITY-0) from
the bytes. With no flag the candidate is admitted with that still; with a flag nothing is admitted, the flag is shown,
and **Admit despite** appears beside it (recorded in the ledger). The still goes into the world's ledger folder by its
sha256 and `verify` reads it again. Undo needs no still: it is checked to be the exact inverse of the admission it
undoes. The detectors flag a still drawn white or black; they prove nothing about a picture, and the designer judges it.

## What is kept

Each line of `requests.jsonl` now carries its disposition and `prev`, the sha256 of the line before it:
`python art/studio.py records [--brief B] [--root DIR]` reads the record back, says whether the chain is whole (a line
taken out of the middle is found; lines cut from the end are not, without the last line's hash kept elsewhere), counts
the dispositions, and lists what was asked for and is not made yet, the studio's backlog (telemetry, never a gate).

Every request, under `art/build/studio/BRIEF/ID/` (never committed; in the studio's worlds, under the world's own
folder): `request.json`, `response.raw`, and each
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
admission at each of its writes and recovers it (15 cases since 0222, which added the point after an admission's still is kept). Every director command, and play.py's start, recovers
first. One writer at a time: every writer of a tree's ledgers, briefs, tags and maps holds the tree's content lock
(`art/build/content.lock`; a thread lock in a process and the system's lock between processes, which the system releases
when its holder dies); an admission holds it from before its first write to after its last and reads the head again
under it, so a second admission drawn at the same head is refused (HEAD-MOVED) instead of writing over the first; and
recovery takes the same lock, so while an admission is alive a recovery refuses (LEDGER-BUSY) and changes nothing.
`python art/director.py racetest` (32 cases) puts a second admission and another process's recovery at each of an
admission's writes, and keeps the plants that break it. Briefs share the graybox's maps, so a layout admitted in one
world would change every world that plays its map: a layout change is refused while another brief plays the map
(SHARED-MAP), an art change admitted as before. That holds in one tree; in the studio's worlds (STUDIO-2, below) each
world keeps a copy of the maps of its own. play.py answers `GET /healthz` (`ready`, `version`, `page`, `page_age_s`, `bye_age_s`, `pid`), takes the page's
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
with a stand-in browser (11 cases; 12 on Windows, where a live job's process list is read as well).

## The worlds and the queue (STUDIO-2)

The milestone, in the owner's words: *"Build a desktop-launched application that can open two saved worlds, switch
between them, queue an edit for either world, and review the resulting candidate without interrupting play."* Where
the worlds live is his choice of 2026-10-13: *"Per-user folder (Recommended)"*.

**Where.** `%LOCALAPPDATA%\VerdandiStudio\worlds\NAME\` (elsewhere `~/.local/share/verdandi-studio/worlds/NAME/`),
or `--worlds DIR`. Each world is a tree of its own: its brief (`art/briefs/NAME.art`), its ledger and tags
(`art/ledger/`), its own copy of the graybox's maps (`graybox/maps/`), its requests' records (`art/build/studio/`) and
its content lock (`art/build/content.lock`). One world's admission therefore writes no file of another, by
construction, and two worlds never share a map. The desktop studio serves this folder; `--root DIR` (one tree, the
self-tests') and the checkout itself are served as before.

**The first start.** When the folder holds no world it is made from the checkout: every brief there (today
`plaza-night` and `harbor-day`) is copied whole, with its ledger and tags if it has them and the checkout's maps, into a
folder made aside; its ledger is replayed in the copy, and only if it verifies is the folder put in place, by one
rename. A brief whose ledger does not verify is not copied, and why is said and recorded. `SEEDED.json` records what was
copied, by sha256. The checkout is read, never written (but for its own recovery, as any start there does); after the
first start it is a template, and the studio's worlds change only through their own ledgers.

**In the page.** The panel (**Enter**) names the world played and lists the others: choosing one loads its page.
**Duplicate as** makes a new world from this one (its brief, its title marked as a copy, a ledger of its own and, in the
worlds folder, its own copy of the maps) and opens it. The **Queue** section queues the prompt for any world, with a
provider (`art/providers/*.json`) and a model (or the configuration's own), and with that world's present target and
pins: the task runs in the background, and the page, and every world, plays on. A request asked with **Ctrl+Enter** is
the page's own, as before; a queued one is not tied to the window.

**The queue** (`art/studio_queue.py`). A task belongs to a world: it records the world, the references and the camera
it was queued with, the head when it was queued and when it ran, the provider's configuration and the model. Tasks run
in the order they were queued, at most two at once (`--jobs N`) and at most one per world, so that a world's requests
meet the head the one before left. A task is *queued*, *running*, then *ready* (its candidates recorded), *failed* or
*cancelled*; *interrupted* if the studio stopped while it ran and nothing of its answer was recorded; *reviewed* once
decided. The panel lists every task with its state, its world and prompt, its model, and the tokens or cost its
provider reported, with **Cancel**, **Review**, **Set aside** and **Queue again** as the state allows; a toast says when
one is ready or failed, in whatever world's page is open. **Review** opens the task's world (another world's page loads,
with `&review=ID`) and draws the task's recorded candidates again at the head as it is now, each evaluated again, never
trusted: a candidate made against an older head says so (`HEAD-MOVED` in its codes) and is admitted, as every
candidate is, only at the head it is drawn at. Nothing in the queue admits; the person does, through the gateway.

**Kept across restarts.** The queue is one file, `queue.jsonl` in the worlds folder, one event a line, each appended
under the queue's lock and flushed. Two rules from the ghost search (fixes 3 and 4 of 2026-10-13): a torn last line is
set aside (`queue.jsonl.torn.N`) and cut from the file, durably, before anything is appended, so the next event never
merges into it; and a task that was running when the studio stopped is *ready* if its world's records hold its answer
(nothing is asked, or paid for, again), *interrupted* otherwise, and can be queued again.

`python art/studio_queue.py selftest` (13 cases) seeds a worlds folder, refuses a brief whose ledger does not verify,
queues for one world from another's page and reviews and admits there (the other world's ledger unchanged), duplicates
a world, runs two worlds at once with one request per world, cancels and queues again, compiles two worlds' scenes at
once (and keeps the plant without the export lock), and keeps fixes 3 and 4 with their plants. The studio app's
self-test starts the supervisor without `--root` on a worlds folder.

## The first window (0220)

By his direction of 2026-10-13, *"when i click the desktop icon a window should open asking what part of the studio
should open first; different abstractions can be added as be design"*: the icon's window opens on `start.html`, which
lists the worlds, each read back as the window opens (its ledger replayed to its files, under its content lock: VERIFIED
says the files are the bytes the ledger records, not that the world is right; whether the head is anchored outside the
world folder is said, and it is not yet), and the studio's views, one manifest each in `art/web/views/`:

| view | level | what |
|---|---|---|
| Play and direct | make | the world first-person with the director's panel |
| Queue prompts | make | the same, with the queue open |
| Compose | make | not built: a top-down blockout; says why |
| History | one level deeper | the ledger and the request record read back, read-only, with the head and the last line's hash to copy elsewhere |
| Mechanisms | one level deeper | not built: arrives with the first physics slice; says why |
| Evidence | one level deeper | not built: the self-tests' results; says why |

A view is added by adding a manifest (`id`, `title`, `summary`, `level`, `order`, `open`, `needs_world`,
`capability` inspect or propose, `status` ready or not built, `why`); one that is not well formed, or that opens a page
outside the studio, is listed as unavailable with why, never left out. The window and the read-only views are served
with a second token, good for the window's heartbeat and goodbye and nothing else: they cannot ask, admit, reject,
undo or queue. *Next time, skip this window* is a preference of the window's own browser profile, never part of a
world. `python art/studio_queue.py selftest` holds the launcher (the token, a broken manifest, a world changed outside
its ledger not verified) and `python art/studio_app.py selftest` the window opening on it.

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
STUDIO-2: switching worlds in a browser on a real GPU (in the build container's headless Chromium, on SwiftShader, a
page with a live WebGL context took 40 to more than 90 s to give way to the next, the server having answered in about a
millisecond; the browser run gave the context back first, and passed its ten flows); whether a provider started by the
desktop studio opens a console window (it is started with `CREATE_NO_WINDOW`; not seen on Windows yet); a studio that
dies between asking a provider and recording that the task started finds the task still queued at its next start,
and asks again (the first answer, if one came, is in the world's records, but not the task's).
