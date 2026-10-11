<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The studio: a director summoned into the running plaza (STUDIO-0)

By the owner's direction of 2026-10-11: *"the LLM edits design intent; Verðandi compiles that intent into a live
world; the designer remains in control."* And by his ruling on how a model is reached: *"a pluggable model adapter,
with a persistent local director service behind it"*, starting with *"a CLI adapter so the first implementation
remains standard-library-only"*; *"the model proposes changes—it never directly mutates the live world. Verðandi owns
validation, compilation, preview, and admission."*

```text
 the page (art/web/play.js)          play.py                    art/studio.py, the gateway          a provider (a command)
 E selects, Enter summons  ──POST──►  token, host  ──────────►  context from the head  ──stdin──►  the model, or a script
                                                                 limits, cancel, time    ◄─stdout─  ≤ 3 candidates (JSON)
                                                                 the response, read whole
                                                                 each candidate an intent ──► art/director.py: checks, scope
 [ Show ] swaps the scene  ◄──/live── candidates as sources  ◄── those not refused, compiled
 [ Admit ] [ Reject ] [ Undo ] ─────►  the director's ledger: evaluate, admit / refuse; the brief written
```

## Using it

```
python art/play.py plaza-night --director art/providers/scripted.json
python art/play.py plaza-night --director art/providers/anthropic.json
```

The first needs no model: `art/providers/scripted.py` answers a selected canopy with three fixed variations (the three
of the owner's sketch: *Monolithic*, *Lit underside*, *Deeper canopy*) and anything else with nothing. It understands
nothing, and is there so that the studio can be tried and tested. The second asks a Claude model through the
Anthropic Messages API. Its key and model are in the environment, never in a file: `ANTHROPIC_API_KEY`,
`VERDANDI_DIRECTOR_MODEL` (required; nothing guesses a model's id), and `VERDANDI_DIRECTOR_API` if the endpoint is not
`https://api.anthropic.com/v1/messages`.

In the page: **E** selects the piece of the dressing under the crosshair (a frame marks it; a wall in front of it
hides it). **Enter** opens the director's panel, and the game goes on. Type the change; **Ctrl+Enter** asks. The
candidates come back with their verdicts. **Show** draws one in place: the scene changes, the game, the player and
the camera do not. **Original** draws the brief. **Admit** writes it through the director's ledger, **Reject** records
a refusal, and **Undo** admits the last admission's exact inverse. **Cancel** stops a request, and **Esc** goes back to
the world. Without a selection, the prompt is for the whole world.

## A provider's configuration

```json
{"provider": "cli", "argv": ["{python}", "art/providers/scripted.py"], "model": "scripted-1", "timeout_s": 30, "max_output_bytes": 65536}
```

`argv` is a list of arguments, run from the repository's root without a shell; `{python}` is the Python that runs
play.py. `model` names what answers, for the record. `timeout_s` (1–600) and `max_output_bytes` (1 KiB – 4 MiB) are
limits; past either, the command is killed. A configuration that is not exactly this is refused whole
(`STUDIO-CONFIG`), and play.py serves the world without a director.

## The request (on the provider's standard input)

`VERDANDI-STUDIO-REQUEST 0`, one JSON document:

| field | |
|---|---|
| `id` | the request's id; the response must name it |
| `brief`, `head`, `base` | the brief, and the head the request was made at (the director's head and its three parts) |
| `prompt` | the designer's words, 1–2,000 characters |
| `selection` | null, or the piece: its id, address, region, kind and material, the brief's statement that made it (line, text, key), and the address patterns it falls under (`plaza/canopy/*`, `material/concrete_slab`) |
| `camera` | where the designer stands and looks: x, y, z (metres), yaw and pitch (degrees) |
| `statements` | the brief: every statement's line, text and key |
| `revision_syntax`, `language` | how a revision is written, and the art file's statements as `art/README.md` describes them |
| `respond` | the response's format, the id again, at most 3 candidates, and the JSON Schema they follow |

## The response (on its standard output)

`VERDANDI-STUDIO-RESPONSE 0`: `{"format", "version": "0", "id", "provider": {"name", "model"}, "candidates": [...]}`,
at most three candidates, each with exactly these fields (`python art/studio.py schema` prints the schema, which a
provider that supports constrained output should constrain its model to):

| field | |
|---|---|
| `title` | a few words, at most 80 characters |
| `rationale` | what the change means, at most 1,200 characters |
| `revision` | 1–16 lines: `= <statement>` replaces the statement with the same key, `+ <statement>` adds one, `- <key>` removes one |
| `scope` | 1–12 address patterns: everything outside them must stay as it is |
| `preserve` | what it means to keep, in words, at most 12 (recorded, and shown; the scope check is what holds it) |

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
`art/build/studio/BRIEF/requests.jsonl` (the head, the provider and model, the prompt, the selection, the sha256 of
the request and the response, each candidate's verdict, the outcome). A recorded candidate is played again without
the provider: `python art/play.py BRIEF --intent art/build/studio/BRIEF/ID/A.intent`. Admissions, rejections and undos
are in the brief's ledger (`art/ledger/BRIEF.ledger`), as `art/director.py` writes it.

## Its boundary

A provider is a command with an argument list, never a shell line; the request reaches it on its standard input, never
in its arguments. It is limited in time and in output, and killed when cancelled or superseded. Its keys are in its
environment; nothing of it reaches the browser but the candidates' text and their verdicts. The page's requests to
play.py carry a token the page is served with, in a header that a page of another origin cannot send without a
preflight play.py never answers, and must name 127.0.0.1 or localhost as their host. Nothing is admitted without the
designer, and nothing reaches the world but what the director judged.

## What is not shown

The quality of what a model proposes: the checks hold a candidate to the rules of the art and to its declared scope,
not to taste. The live Anthropic API: `anthropic_messages.py` is held only to a local server that answers as the API's
documentation describes. Selecting a light or a play piece (the frame and E pick the dressing's boxes). Changes to the
layout (STUDIO-0 changes the look; a layout change is the design tool's). A long-running worker: each request starts
the provider's command afresh, which the owner allowed for the first version. A latency: the scripted provider's
candidates are drawn in well under a second in the build container, which says nothing of a model's.
