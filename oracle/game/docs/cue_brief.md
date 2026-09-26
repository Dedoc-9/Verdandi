<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: cue-focus -->
# `cue` — design brief (URDRCUE1, WINDOW-1: the input membrane)

**Built**: 2026-09-20, one rung after `chorus`, on the boundary the WINDOW-1 measurement pass established and
the user ratified. It is the **seventeenth game-layer vertical slice**, **WINDOW-1** of the
observer-composition arc, and the **input-side mirror of `chorus`**.

## 0. The one invariant

> **Focus identity is non-authoritative; the canonical action stream is determined by the input, not by which
> window originated it.**

A real external event now crosses the membrane into the certified world, while **focus, presentation and
binding context remain demonstrably non-authoritative**.

## 1. What it is

    bind(event)              -> a typed enact token | CUE-REFUSE     (one pure map)
    bind_stream(events)      -> the tuple of tokens they emit
    route(keys, focuses)     -> the event stream (focus = who received each key)

`chorus` is the one-way **display** membrane (transition → observers, never → `Dₙ`). `cue` is the one-way
**input** membrane:

    raw window/device event → bind() → typed enact token | refusal → enact → Dₙ₊₁

never `token authority → window`. The membrane owns **binding**, not gameplay interpretation.

## 2. `bind` is pure, and sealed against canonical state

`bind(event, bindings)` reads **only** the raw event and the binding table — never `level`, `pos`, `stream`,
or `Dₙ`. Its signature **cannot receive** canonical state (a sealed observer, enforced structurally, not by
comment). It mints no transition and no identity. A binding that inspected canonical state to *choose* the
token would make the window's context a canonical input — the neutral-ruler violation this rung exists to
forbid.

## 3. Focus is a routing label, not an authority

An `Event(focus, key)` names the window that received the event; `bind` consumes **only** `key`. The certified
statement is precise — **focus identity *alone* is non-authoritative**:

> hold the binding table **and** the raw key sequence fixed, and vary **only** which focus/window receives each
> event → the emitted token stream is **byte-identical**.

with the two routes genuinely different and each route using more than one focus, so the reroute is
**non-vacuous**. This is deliberately distinct from **configuration**: a *different* binding table may
legitimately change the tokens for the same key (`a_different_binding_table_changes_the_tokens`) — which is
configuration behaviour, **not** focus authority, and which also proves the map is real (an always-refuse
binding would satisfy the focus differential vacuously).

## 4. The token vocabulary is `enact`'s — one vocabulary, two responsibilities

`bind` delegates to `enact.encode`, so the tree keeps a single token vocabulary:

    cue:   raw event → token
    enact: token → state transition

The membrane therefore **does not become a second `enact`**. A MOVE carries a `move.DIRECTIONS` command,
DESCEND/LOOT carry none, and a malformed payload is **`enact`'s** refusal, not this module's.

## 5. The binding table is data

`DEFAULT_BINDINGS` is a **frozen tuple** of `(raw key, (enact KIND, payload))` pairs read by `bind` through a
plain `dict`. Swap the table and the behaviour swaps with no code change; every value is an `enact` kind and a
literal payload, so the table reads no canonical state.

## 6. Ownership is a three-tier ladder, proved as a differential

    WINDOW-1  "I cannot bind this event."                 unbound / malformed event → CUE-REFUSE
    ENACT     "I cannot form this token."                  bad payload → ENACT-REFUSE (bind time)
    AUTHORITY "I cannot perform this legal action here."   valid token, illegal state → DESCEND-REFUSE (dispatch)

The first two are the module's own laws. The **third tier** — a syntactically valid token `cue` happily emits,
refused **downstream** by the authority because its gameplay legality is false — is the **gate's**, run
against a real `enact.dispatch`, because this module must not (and does not) reach dispatch. So `cue` emits
tokens and adjudicates none; it never quietly becomes a gameplay validator.

## 7. Stateless stream composition (the input-path tripwire)

Binding a *sequence* of events is a **stateless homomorphism over concatenation**, wherever the constituent
bindings succeed:

    bind_stream(E₁ ++ E₂) == bind_stream(E₁) ++ bind_stream(E₂)

with the empty stream mapping to the empty token stream, duplicates duplicating, and **refusal atomic at the
batch boundary** (any unbound/malformed event refuses the *whole* batch `CUE-REFUSE`, no partial result). The
claim is deliberately **not** "total": it is a homomorphism only where the bindings succeed, and refusal is
atomic — the statement aligned with the measured refusal behaviour.

The **positive control** is the point, not decoration: a synthetic **stateful** binder that folds the previous
event into its output breaks concatenation, so the gate REDs on that shape rather than the implementation
merely satisfying its own definition. And this law **does not earn timed input — it forbids its silent
arrival**. The day chords/repeat/hold/modifier state enters the membrane, concatenation ceases to hold, this
falsifier reddens, and the system is forced to acknowledge that a new state/time coordinate has entered rather
than letting it drift in. `Event(focus, key)` carries no temporal field today (measured), so that coordinate
would have to be minted deliberately — the same one `enact` and `cue` both refused.

## 8. The membrane is one-way (WINDOW-0 §7, mirrored on the input side)

`the_membrane_is_one_way` reads this module's **own full AST** — function-local imports included — and is
direction-aware: it imports exactly `ALLOWED_IMPORTS` (`enact` among them, **for its codec only**), imports
**none** of `move`/`descend`/`loot`/`statecanon`/`rerun`/`savegame`/`lockstep` in any scope, and reaches no
`.dispatch`/`.apply` (**never routes a token**) nor `.d_n`/`.step`. Positive controls: synthetic sources that
reach `enact.dispatch`, `enact.apply`, nest a `statecanon`/`rerun` import, call a `move` transition, or reach
a bare `.d_n`/`.dispatch` are each rejected, while the read-only `enact.encode`/`enact.decode` path is
accepted.

## 9. Where it stops (deferred / rejected on purpose)

**Deferred**: stateful/timed input (chords, key-repeat, hold-timing, modifiers-as-state) — these need a time
coordinate the game layer has not earned, the same one `enact` refused to mint; a raw-event history channel
(redundant with `actionlog`/`rerun` until a reason to record above the token stream is earned); the
reproducible-observer-identity record (a `chorus` display-branch deferral). **Rejected**: focus arbitration /
any window-manager authority that *decides* focus (which window is focused is a **given** label, never decided
here — the authority `chorus` already refused); any canonical-state-dependent binding; an input loop/runtime;
and window identity in `Dₙ`.

## 10. Grade

**MEASURED**: `bind` is pure in the raw event and ignores `focus`; focus identity alone is non-authoritative
(same bindings + same keys + rerouted focus → byte-identical tokens, routes genuinely different, each focus
used); a different binding table changes the tokens (the map is real; configuration is not focus authority);
the binding table is data; an unbound/malformed event refuses `CUE-REFUSE` while a malformed payload surfaces
`ENACT-REFUSE`; and stream binding is a stateless homomorphism over concatenation where the bindings succeed
(empty→empty, duplicates duplicate, refusal atomic), with a stateful-binder positive control that breaks it.
**ESTABLISHED**: the membrane is one-way (full-AST, direction-aware, `enact` codec only, no
authority import in any scope, no `.dispatch`/`.apply`/`.d_n`/`.step`, positive control); no CORE module
imports `cue`. **DECLARED**: the token vocabulary is `enact`'s; `focus` is a routing label; the binding table
is the declared default; single peer.

## does_not_show

The downstream gameplay-legality refusal and the canonical-replay half of the focus differential across a real
`enact`/`savegame`/`rerun` core (the gate's, not the module's); stateful/timed input, chords, key-repeat,
modifiers; focus arbitration / any window-manager authority; a raw-event history channel; OS-native input,
gamepads, and any wall-clock or frame budget (all deferred or rejected).

## Falsifier

`cue-focus` (focus identity alone is non-authoritative — same bindings and same raw keys with the focus
rerouted yields a byte-identical token stream, the routes genuinely differ and each uses more than one focus;
`bind` ignores focus per key; the full-AST one-way guard bites its positive controls; refusal is total), with
`cue:scenes` (the two scenes and the top digest reproduce, an unpinned name refuses typed `CUE-REFUSE`) and
`cue-bind` (`bind` is a real pure map whose vocabulary is `enact`'s; the binding table is data; a different
table changes the tokens; **stateless stream composition** — `bind_stream` is a homomorphism over
concatenation where the bindings succeed, empty→empty, duplicates duplicate, refusal atomic at the batch
boundary, with a stateful-binder positive control that breaks it; and the three-tier refusal ladder — an
unbound/malformed event is `CUE-REFUSE`, a bad payload is `ENACT-REFUSE`, and against a **real**
`enact`/`savegame`/`rerun` core a valid-but-illegal token is refused downstream by the authority while a
rerouted-focus token stream replays byte-identically) alongside; `tests/test_cue.py`.
