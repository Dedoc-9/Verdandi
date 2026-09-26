# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""cue — the one-way input membrane: a raw window/device event becomes a typed `enact` token (URDRCUE1).

THE SEVENTEENTH GAME-LAYER VERTICAL SLICE, WINDOW-1 of the observer-composition arc, and the INPUT-SIDE
mirror of `chorus`. `chorus` (URDRCHO1) is the one-way DISPLAY membrane — an authoritative transition flows
out to disposable observers and never back to `D_n`. `cue` is the one-way INPUT membrane — a raw external
event flows IN and becomes a typed action token, and the identity of the window that originated it flows
NOWHERE. Its one invariant, carried from the WINDOW-1 measurement pass: FOCUS IDENTITY IS NON-AUTHORITATIVE;
THE CANONICAL ACTION STREAM IS DETERMINED BY THE INPUT, NOT BY WHICH WINDOW ORIGINATED IT.

THE DIRECTION IS ONE-WAY, AND IT IS THE WHOLE POINT:

    raw window/device event -> bind() -> typed enact token | refusal -> enact -> D_{n+1}

never `token authority -> window`. The membrane owns BINDING, not gameplay interpretation. `bind(event)` is a
PURE function of the raw event and the binding table; it reads no `level`/`pos`/`stream`/`D_n`, its signature
cannot receive canonical state (sealed observer), and it computes no transition and no identity. It imports
`enact` for its CODEC ONLY (`encode`/`decode`/`kind_of`) so the tree keeps ONE token vocabulary — WINDOW-1
turns a raw event into a token, `enact` turns a token into a transition — and it never reaches `enact.dispatch`
or `enact.apply`, nor imports `move`/`descend`/`loot`/`statecanon`/`rerun`/`savegame`/`lockstep`.
`the_membrane_is_one_way` reads this module's OWN full AST (function-local imports included) and refuses any
authority import or any `.dispatch`/`.apply`/`.d_n`/`.step` reach, with a positive control.

FOCUS IS A ROUTING LABEL, NOT AN AUTHORITY. A raw `Event(focus, key)` names the window that received the
event and the raw device key. `bind` consumes ONLY `key`; `focus` reaches neither the token nor any canonical
value. The certified statement is precise — FOCUS IDENTITY ALONE is non-authoritative: hold the BINDING TABLE
and the RAW KEY SEQUENCE fixed and vary ONLY which focus/window receives each event, and the emitted token
stream is byte-identical (`focus_identity_is_non_authoritative`), so the canonical replay is byte-identical
too. That is distinct from CONFIGURATION behaviour: a DIFFERENT binding table may legitimately yield different
tokens for the same key (`a_different_binding_table_changes_the_tokens`) — which is not focus authority, and
which also proves the map is real (a binding that always refused would satisfy the focus differential
vacuously).

THE BINDING TABLE IS DATA. `DEFAULT_BINDINGS` is a frozen tuple of `(raw key, (enact KIND, payload))` pairs
read by `bind` through a plain `dict`; swap the table and the behaviour swaps with no code change. It reads no
canonical state — its values are `enact` kinds and literal payloads. The token VOCABULARY is `enact`'s and is
single-sourced there: `bind` delegates to `enact.encode`, so a MOVE carries a `move.DIRECTIONS` command and
DESCEND/LOOT carry none, and a malformed payload is `enact`'s refusal, not this module's.

OWNERSHIP IS A THREE-TIER LADDER, PROVED AS A DIFFERENTIAL. An unbound or malformed EVENT is THIS module's
typed refusal, `CUE-REFUSE` ("I cannot bind this event"). A bound-but-malformed PAYLOAD surfaces `enact`'s
`ENACT-REFUSE` ("I cannot form this token") — the vocabulary stays `enact`'s even at bind time. A
syntactically valid token whose GAMEPLAY legality is false (a DESCEND off the down-stairs) passes WINDOW-1
cleanly and is refused DOWNSTREAM by the authority (`DESCEND-REFUSE`, surfaced through `enact.dispatch`) — and
that third tier is the GATE's to prove, because this module must not (and does not) reach `enact.dispatch`.
So `cue` never becomes a gameplay validator: it emits tokens; it adjudicates none.

THIS RUNG IS SINGLE-PEER AND STOPS SHORT ON PURPOSE. It owns exactly `event -> token | refusal` and the
focus-independence differential. It introduces NO input loop or runtime, NO stateful/timed input (no chords,
key-repeat, hold-timing or modifiers-as-state — those need a time coordinate the game layer has not earned,
the same one `enact` refused to mint), NO focus arbitration (which window is focused is a GIVEN label, never
decided here — the authority `chorus` already refused), and it minted no raw-event history channel.

GRADE (honest, D5). MEASURED: `bind` is pure in the raw event and ignores `focus`; focus identity alone is
non-authoritative (same bindings + same keys + rerouted focus -> byte-identical token stream, with the two
routes genuinely different and each focus used); a different binding table changes the tokens (the map is
real, and configuration is not focus authority); the binding table is data; an unbound or malformed event
refuses `CUE-REFUSE` while a malformed payload surfaces `ENACT-REFUSE`. ESTABLISHED: the membrane is one-way —
read off the full AST it imports exactly its declared substrate (`enact` for its codec only, no authority
module, function-local included), reaches no `.dispatch`/`.apply`/`.d_n`/`.step`, and synthetic authority
reaches are rejected as the positive control; no CORE module imports `cue`. DECLARED: the token vocabulary is
`enact`'s; `focus` is a routing label; the binding table is the declared default; single peer. does_not_show:
the DOWNSTREAM gameplay-legality refusal and the canonical-replay half of the focus differential across a real
`enact`/`savegame`/`rerun` core (the gate's, not the module's); stateful/timed input, chords, key-repeat,
modifiers; focus arbitration / any window-manager authority; a raw-event history channel; OS-native input,
gamepads, and any wall-clock or frame budget (all deferred or rejected)."""
import ast
import collections
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import enact as _EN                                                     # noqa: E402  (the token CODEC ONLY)

MAGIC = b"URDRCUE1"

LAYER = "VIEW"
D24_ANSWER = "produces a typed action from a raw window/device event — the one-way input membrane (bind; focus identity is non-authoritative)"
ALLOWED_IMPORTS = ("ast", "collections", "hashlib", "os", "enact")

#: A raw window/device event. `focus` is the window/observer that received it — a ROUTING LABEL, disposable
#: and non-authoritative. `key` is the raw device key. `bind` consumes ONLY `key`; `focus` reaches nothing.
Event = collections.namedtuple("Event", ("focus", "key"))

#: The FROZEN binding table, as DATA: raw key -> (enact KIND, payload). It reads no canonical state; a MOVE
#: carries a `move.DIRECTIONS` command, DESCEND/LOOT carry none. The token VOCABULARY is `enact`'s — `bind`
#: delegates to `enact.encode` and mints none of its own.
DEFAULT_BINDINGS = (
    ("Up",    (_EN.MOVE, "N")),
    ("Down",  (_EN.MOVE, "S")),
    ("Right", (_EN.MOVE, "E")),
    ("Left",  (_EN.MOVE, "W")),
    (">",     (_EN.DESCEND, None)),
    ("g",     (_EN.LOOT, None)),
)

#: Read off THIS module's full AST by `the_membrane_is_one_way`. `enact` is PERMITTED (its pure codec), but
#: its AUTHORITY attrs are forbidden; the transition/identity modules are forbidden in ANY scope. `descend`
#: (the depth transition) is forbidden and is a different name from the `DESCEND` kind it never routes.
_FORBIDDEN_MODULES = frozenset({"move", "descend", "loot", "statecanon", "rerun", "savegame", "lockstep"})
_FORBIDDEN_ATTRS = frozenset({"step", "dispatch", "apply", "d_n", "d_n_preimage"})


class CueError(Exception):
    def __init__(self, message):
        super().__init__(f"CUE-REFUSE: {message}")
        self.code = "CUE-REFUSE"


# ---- the membrane: a raw event -> a typed enact token ---------------------------------------------------
def _is_event(e):
    return isinstance(e, Event)


def bind(event, bindings=DEFAULT_BINDINGS):
    """Map ONE raw event to a typed `enact` token. PURE in the event and the binding table — it reads no
    `level`/`pos`/`stream`/`D_n`, and its signature CANNOT receive canonical state (sealed observer). `focus`
    is a routing label consumed by NOTHING here. An event with no binding is THIS module's typed refusal,
    `CUE-REFUSE`; a bound-but-malformed payload surfaces `enact`'s `ENACT-REFUSE` (the vocabulary stays
    `enact`'s); gameplay legality remains the authority's question, downstream of this membrane."""
    if not _is_event(event):
        raise CueError(f"an event must be an Event(focus, key), got {type(event).__name__}")
    table = dict(bindings)
    if event.key not in table:
        raise CueError(f"no binding for key {event.key!r}")
    kind, payload = table[event.key]
    return _EN.encode(kind, payload)              # ENACT-REFUSE surfaces here on a malformed payload


def bind_stream(events, bindings=DEFAULT_BINDINGS):
    """Bind a sequence of raw events to the tuple of tokens they emit — the canonical action stream WINDOW-1
    hands to `enact`."""
    if not isinstance(events, (tuple, list)):
        raise CueError("events must be a sequence of Event")
    return tuple(bind(e, bindings) for e in events)


def route(keys, focuses):
    """Deliver each raw key to a named focus — the ONLY thing `focus` does is label who received the event.
    Returns the event stream; requires one focus per key."""
    if not (isinstance(keys, (tuple, list)) and isinstance(focuses, (tuple, list))):
        raise CueError("route needs a key sequence and a focus sequence")
    if len(keys) != len(focuses):
        raise CueError("route needs exactly one focus per key")
    return tuple(Event(f, k) for f, k in zip(focuses, keys))


# ---- corpus ---------------------------------------------------------------------------------------------
SCENES = ("binding", "focus")
#: A raw key sequence and two genuinely different focus routings of it. Each route uses BOTH windows and the
#: two routes differ at every position — the focus reroute is non-vacuous.
_KEYS = ("Up", "Down", "Right", "Left", "g", "Up")
_FOCUS_A = ("wA", "wB", "wA", "wB", "wA", "wB")
_FOCUS_B = ("wB", "wA", "wB", "wA", "wB", "wA")


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def bind_ignores_focus(key):
    """`bind` consumes only the raw key: the SAME key through two different focuses yields the SAME token."""
    return bind(Event("wA", key)) == bind(Event("wB", key))


def focus_identity_is_non_authoritative(keys=_KEYS, fa=_FOCUS_A, fb=_FOCUS_B, bindings=DEFAULT_BINDINGS):
    """THE CENTRAL FALSIFIER (token half). Hold the BINDING TABLE and the RAW KEY SEQUENCE fixed and vary
    ONLY which focus/window receives each event: the emitted token stream is byte-identical. Non-vacuity: the
    two routes genuinely differ and each route uses more than one focus. Returns
    (tokens_identical, routes_differ, both_routes_use_multiple_focuses)."""
    tokens_a = bind_stream(route(keys, fa), bindings)
    tokens_b = bind_stream(route(keys, fb), bindings)
    routes_differ = tuple(fa) != tuple(fb)
    both_used = len(set(fa)) >= 2 and len(set(fb)) >= 2
    return tokens_a == tokens_b, routes_differ, both_used


def a_different_binding_table_changes_the_tokens(key="Up"):
    """NON-VACUITY of the map, and CONFIGURATION IS NOT FOCUS AUTHORITY. The SAME key under a DIFFERENT
    binding table yields a DIFFERENT but still-valid typed token. This proves `bind` is a real map (not a
    constant / always-refuse), and that a token change can come from CONFIGURATION — which is legitimate and
    distinct from focus identity, the thing that must NEVER move a token. Returns
    (tokens_differ, both_are_moves, directions_differ)."""
    t1 = bind(Event("w", key), (("Up", (_EN.MOVE, "N")),))
    t2 = bind(Event("w", key), (("Up", (_EN.MOVE, "S")),))
    k1, d1 = _EN.decode(t1)
    k2, d2 = _EN.decode(t2)
    return t1 != t2, (k1 == _EN.MOVE and k2 == _EN.MOVE), (d1 != d2)


def an_unbound_event_is_our_refusal(key="\x00-no-such-key"):
    """A key with no binding is THIS module's refusal, typed `CUE-REFUSE` — 'I cannot bind this event.'"""
    try:
        bind(Event("wA", key))
    except CueError as exc:
        return exc.code == "CUE-REFUSE"
    return False


def a_malformed_event_is_our_refusal():
    """A non-Event surfaces `CUE-REFUSE` — the membrane owns the SHAPE of its input. A bare 2-tuple is NOT an
    `Event` and is refused, so the shape is a real gate, not a duck-typed coincidence."""
    verdicts = []
    for bad in (("wA", "Up"), 42, None, "Up", ("wA", "Up", "extra")):
        try:
            bind(bad)
            verdicts.append(False)
        except CueError as exc:
            verdicts.append(exc.code == "CUE-REFUSE")
    return all(verdicts)


def a_bad_payload_surfaces_enacts_refusal():
    """The token VOCABULARY stays `enact`'s: a binding that names a MALFORMED payload (a bad direction) is not
    THIS module's fault — `bind` delegates to `enact.encode`, which refuses `ENACT-REFUSE`. WINDOW-1 owns 'I
    cannot bind this event'; `enact` owns 'I cannot form this token.'"""
    try:
        bind(Event("w", "Q"), (("Q", (_EN.MOVE, "NOPE")),))
    except _EN.EnactError as exc:
        return exc.code == "ENACT-REFUSE"
    except CueError:
        return False                                  # a payload fault must NOT be miscounted as ours
    return False


def the_binding_table_is_data(bindings=DEFAULT_BINDINGS):
    """The binding table is DATA, not code: a tuple of `(str key, (kind, payload))` pairs, read by `bind`
    through `dict()`. It reads no canonical state — every value is an `enact` kind and a literal payload."""
    if not isinstance(bindings, tuple):
        return False
    for entry in bindings:
        if not (isinstance(entry, tuple) and len(entry) == 2):
            return False
        key, kp = entry
        if not (isinstance(key, str) and isinstance(kp, tuple) and len(kp) == 2):
            return False
        kind, _payload = kp
        if kind not in _EN.KINDS:
            return False
    return True


def refuse_is_total():
    """(malformed event, unbound key) each surface a typed `CUE-REFUSE`; a malformed PAYLOAD instead surfaces
    `enact`'s `ENACT-REFUSE`. The ownership ladder is crisp at bind time: shape/binding is ours, vocabulary is
    `enact`'s (and gameplay legality is the authority's, downstream — the gate's to show)."""
    return (a_malformed_event_is_our_refusal()
            and an_unbound_event_is_our_refusal()
            and a_bad_payload_surfaces_enacts_refusal())


# ---- stateless stream composition -----------------------------------------------------------------------
def _distributes(make_binder, e1, e2):
    """Does `make_binder` distribute over concatenation? `make_binder` is a FACTORY, so each of the three
    passes (E1++E2, E1, E2) gets a FRESH binder — a stateless binder distributes, a binder that carries
    state ACROSS the batch boundary does not (its whole-stream E2 portion sees an E1 predecessor its fresh
    E2 pass never does)."""
    bw = make_binder()
    whole = tuple(bw(e) for e in list(e1) + list(e2))          # one binder across the whole stream
    bl = make_binder()
    left = tuple(bl(e) for e in e1)                            # a fresh binder for E1 alone
    br = make_binder()
    right = tuple(br(e) for e in e2)                           # a fresh binder for E2 alone
    return whole == left + right


def _stateful_binder():
    """THE POSITIVE CONTROL — a synthetic binder that FOLDS THE PREVIOUS EVENT into its output, the exact
    statefulness this law forbids. It remembers the last key, so a stream's first event depends on what
    preceded it; concatenation therefore fails for it, and the gate REDs on this shape rather than trusting
    the current implementation to satisfy its own definition."""
    prev = [None]

    def b(event):
        tok = bind(event)
        if prev[0] is not None:
            tok = tok + prev[0].encode("ascii", "replace")     # output depends on history -> NOT stateless
        prev[0] = event.key
        return tok
    return b


def stream_composition_is_stateless(e1=None, e2=None):
    """STATELESS STREAM COMPOSITION. On any stream whose constituent bindings SUCCEED, binding is a
    HOMOMORPHISM over concatenation — `bind_stream(E1 ++ E2) == bind_stream(E1) ++ bind_stream(E2)` — the
    empty stream maps to the empty token stream, duplicates duplicate, and REFUSAL IS ATOMIC at the batch
    boundary (any unbound/malformed event refuses the WHOLE batch `CUE-REFUSE`, with no partial result). The
    law is NOT total over the raw-event domain: it is a homomorphism only where the bindings succeed, and
    refusal is atomic. Positive control: a synthetic STATEFUL binder that folds the previous event breaks
    concatenation, so this is a live tripwire — the day chords/repeat/hold/modifier state enters the membrane,
    concatenation ceases to hold and the gate forces that new state/time coordinate to be acknowledged rather
    than drifting in silently. Returns (homomorphism, empty_identity, duplicates_duplicate, refusal_atomic,
    real_bind_is_stateless, stateful_control_breaks)."""
    if e1 is None:
        e1 = route(("Up", "g"), ("wA", "wB"))
    if e2 is None:
        e2 = route(("Right", "Down", "g"), ("wB", "wA", "wA"))
    homomorphism = bind_stream(list(e1) + list(e2)) == bind_stream(e1) + bind_stream(e2)
    empty_identity = bind_stream(()) == () and bind_stream([]) == ()
    duplicates = bind_stream(list(e1) + list(e1)) == bind_stream(e1) + bind_stream(e1)
    refusal_atomic = False
    try:
        bind_stream((Event("wA", "Up"), Event("wA", "\x00-no-such-key"), Event("wA", "g")))
    except CueError as exc:
        refusal_atomic = exc.code == "CUE-REFUSE"
    real_stateless = _distributes(lambda: bind, e1, e2)
    control_breaks = not _distributes(_stateful_binder, e1, e2)
    return (homomorphism, empty_identity, duplicates, refusal_atomic, real_stateless, control_breaks)


# ---- the one-way membrane guard (full AST, direction-aware) ---------------------------------------------
def _import_top(tree):
    top = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return top


def _source_is_one_way(src):
    """A source is a one-way INPUT membrane iff it imports only its declared substrate, imports NO transition/
    identity authority module (any scope), and reaches NO authority attr — in particular no `.dispatch`/
    `.apply` (it may HOLD `enact`'s codec but must never route a token through it) and no `.d_n`/`.step`."""
    tree = ast.parse(src)
    top = _import_top(tree)
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    return (top <= set(ALLOWED_IMPORTS)
            and not (top & _FORBIDDEN_MODULES)
            and not (attrs & _FORBIDDEN_ATTRS))


def the_membrane_is_one_way():
    """STRUCTURAL, read off this module's OWN full AST — direction-aware and function-local-aware. It imports
    exactly `ALLOWED_IMPORTS` (`enact` among them, for its CODEC ONLY), imports none of the transition/identity
    authorities in ANY scope, and reaches no `.dispatch`/`.apply` (never routes a token) nor `.d_n`/`.step`.
    Positive controls: synthetic sources that reach `enact.dispatch`, `enact.apply`, nest a `statecanon` or
    `rerun` import, or reach a bare `.d_n`/`.dispatch` are each REJECTED, while the read-only codec path
    (`enact.encode`/`enact.decode`) is accepted."""
    with open(_os.path.join(_HERE, "cue.py"), encoding="utf-8") as fh:
        own = fh.read()
    clean = _source_is_one_way(own)
    bad = (
        "import enact as _E\ndef f(s, t):\n    return _E.dispatch(s, t)\n",              # routes a token
        "import enact as _E\ndef g(s, t):\n    return _E.apply(s, t)\n",                 # folds a stream
        "import enact\ndef h(t):\n    import statecanon as _S\n    return _S.d_n(*t)\n",  # ingests D_n
        "import enact\ndef j(r):\n    import rerun as _R\n    return _R.verdict(r)\n",    # reaches replay
        "import enact\ndef k(l, p, c):\n    import move as _M\n    return _M.step(l, p, c)\n",  # a transition
        "x = y.dispatch(1, 2)\n",
        "z = w.d_n(1)\n",
    )
    bites = all(not _source_is_one_way(b) for b in bad)
    allows = _source_is_one_way(
        "import enact\ndef h(key):\n    k, p = enact.decode(enact.encode('LOOT'))\n    return k\n")
    return clean and bites and allows


# ---- scenes ---------------------------------------------------------------------------------------------
def _binding_row():
    parts = []
    for key, (kind, payload) in DEFAULT_BINDINGS:
        tok = bind(Event("_", key))
        k, p = _EN.decode(tok)
        parts.append("%s->%s(%s,%s)" % (key, tok.hex(), k, p))
    return "|".join(parts)


def scene_case(name):
    if name == "binding":
        return ("map=%s||data=%s|configdiff=%s|unbound=%s|malformed=%s|badpayload=%s|compose=%s"
                % (_binding_row(),
                   the_binding_table_is_data(),
                   a_different_binding_table_changes_the_tokens(),
                   an_unbound_event_is_our_refusal(),
                   a_malformed_event_is_our_refusal(),
                   a_bad_payload_surfaces_enacts_refusal(),
                   stream_composition_is_stateless()))
    if name == "focus":
        return ("ignore=%s|focus=%s|oneway=%s|refuse=%s"
                % (tuple(bind_ignores_focus(k) for k, _v in DEFAULT_BINDINGS),
                   focus_identity_is_non_authoritative(),
                   the_membrane_is_one_way(),
                   refuse_is_total()))
    raise CueError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def cue_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_cue.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise CueError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and cue_digest() == golden("cue"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except CueError as exc:
        return exc.code == "CUE-REFUSE"
    return False


def main():
    print("CUE — the one-way input membrane: a raw window/device event becomes a typed enact token (URDRCUE1)")
    print("layer %s: %s" % (LAYER, D24_ANSWER))
    print("WINDOW-1 of the observer-composition arc; the input-side mirror of chorus.")
    print()
    print("The binding table (raw key -> typed enact token):")
    for key, (kind, payload) in DEFAULT_BINDINGS:
        tok = bind(Event("_", key))
        print("  %-6s -> %-4s  %s" % (key, tok.hex(), "%s %s" % (kind, payload if payload is not None else "")))
    print()
    ti, rd, bu = focus_identity_is_non_authoritative()
    print("bind ignores focus (per key)        :", tuple(bind_ignores_focus(k) for k, _v in DEFAULT_BINDINGS))
    print("focus identity non-authoritative    :", (ti, rd, bu), "(tokens identical, routes differ, both used)")
    print("a different table changes the tokens :", a_different_binding_table_changes_the_tokens())
    print("the binding table is data           :", the_binding_table_is_data())
    print("an unbound event is our refusal     :", an_unbound_event_is_our_refusal())
    print("a malformed event is our refusal    :", a_malformed_event_is_our_refusal())
    print("a bad payload is enact's refusal    :", a_bad_payload_surfaces_enacts_refusal())
    print("the membrane is one-way             :", the_membrane_is_one_way())
    print("refuse is total                     :", refuse_is_total())
    print("stateless stream composition        :", stream_composition_is_stateless(),
          "(homo, empty, dup, atomic, real-stateless, control-breaks)")
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("cue", cue_digest())
    print()
    print("does_not_show: the downstream gameplay-legality refusal and the canonical-replay half of the focus")
    print("differential across a real core (the gate's); stateful/timed input, chords, repeat, modifiers;")
    print("focus arbitration; a raw-event history channel; OS input, gamepads, wall-clock (deferred/rejected).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
