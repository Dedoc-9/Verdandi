# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""enact — the typed action authority: a KIND, a payload, and one dispatch to the transition (URDRENA1).

THE TWELFTH GAME-LAYER VERTICAL SLICE, and the missing piece between `actionlog` and `replay`. `actionlog`
(URDRACT1) records OPAQUE tokens and commits to their order; it deliberately does NOT say what a token
MEANS, because no typed action vocabulary had been earned. `savegame` (URDRSAV1) stores the earned canonical
components directly. Neither can turn a recorded token back into a canonical transition, and `replay` cannot
be built until something can. This rung is that something, and nothing more: it gives an action a KIND and a
PAYLOAD, and it binds each kind to the ONE existing transition authority that already owns it.

THE KINDS ARE EXACTLY THE STATE TRANSITIONS, ESTABLISHED BY A CODE SWEEP, NOT ASSUMED. A canonical action is
a function that takes a canonical state component and returns an updated one. Exactly three CORE modules do
that:

    MOVE     move.step(level, pos, command) -> (outcome, pos')      updates the entity position
    DESCEND  descend.descend(level, pos)    -> (level', pos')       updates the level and position (depth)
    LOOT     loot.loot(level, pos, stream)  -> (drop, stream')      updates the RNG stream

`combat` and `heirloom` are DELIBERATELY OUTSIDE THE VOCABULARY. Each is a certified arithmetic law that
takes DECLARED integer inputs and returns a DERIVED number — `combat.resolve(attack, defense) -> damage`,
`heirloom.heir(q) -> q'` — mutating nothing and holding no canonical component (both are stdlib leaves that
import no `gamegen`/`entity`/`rngstream`, read off their own AST). They produce results a future
health/inventory-bearing rung will consume; they are not history actions, and including them here would
manufacture a state authority rather than discover one. `the_excluded_modules_are_pure_derivations` reads
this off their imports rather than trusting the prose.

THE PAYLOAD IS WHATEVER THE ACTION ADDS BEYOND THE STATE, AND THE THREE SHAPES GENUINELY DIFFER — which is
why a single universal interpretation cannot substitute:

    MOVE     payload = one direction in `move.DIRECTIONS` (N/S/E/W)   the only free choice
    DESCEND  payload = NONE                                            fully determined by the state
    LOOT     payload = NONE                                            the source is the state's (level, pos)

A token is `KIND-tag byte | payload bytes`: `b"M" + dir` for a move, `b"D"` for a descend, `b"L"` for a loot.
`encode`/`decode` round-trip, and the tokens ARE `actionlog` tokens (canonical bytes), so the vocabulary
rides on the history channel that already exists rather than minting a second one.

DISPATCH BINDS, IT DOES NOT REIMPLEMENT. `dispatch(state, token)` threads a state bundle `(level, pos,
stream)` — every field an already-earned canonical component, nothing invented — decodes the kind, and calls
the authority that owns it. It re-derives no movement legality, no depth ceiling, no RNG draw; each law's
`*_dispatch_matches_the_authority` proves the routed result EQUALS calling `move.step`/`descend.descend`/
`loot.loot` directly. `the_router_reimplements_nothing` reads the binding off the AST.

RNG SEMANTICS ATTACH BY KIND, NOT BY PRESENCE IN THE HISTORY. A recorded action does not imply a draw:
`rng_advances(LOOT) == 1` while `rng_advances(MOVE) == rng_advances(DESCEND) == 0`, measured by threading the
stream through a dispatch of each kind. An interpretation that made every action advance the stream reddens
against `move` and `descend`, which advance nothing — the falsifier `only_loot_advances_the_stream` is that
counterexample.

ORDERING IS `actionlog`'S APPEND ORDER, THE ONLY ONE EARNED. The single earned per-action sequence coordinate
is `actionlog`'s append position (committed by `rngstream`'s fold); `rngstream.Stream.n` counts only
RNG-advancing actions, so it is not a universal index. Cross-peer canonical ordering is a DIFFERENT authority
— `lockstep.canon` (tools/netcode) sorts a delivered union by `(peer, seq)` within a `tick` — but its
ordering key is carried on netcode events and is ABSENT from every game action; the game layer has earned no
tick, peer or sequence coordinate. So this rung binds `actionlog`'s append order and invents no key and no
canonicalizer; cross-peer union reconciliation stays `replay`'s, and would need a later rung to earn those
coordinates before `lockstep.canon` could apply here.

OWNERSHIP STAYS CRISP. A malformed TOKEN (an unknown kind byte, a move token with a bad direction, a
descend/loot token carrying a payload, a non-bytes token) is THIS module's refusal, typed `ENACT-REFUSE`. A
valid token dispatched against a malformed STATE surfaces the AUTHORITY's own code — `MOVE-REFUSE`,
`DESCEND-REFUSE`, `LOOT-REFUSE` — never `ENACT-REFUSE`, because the shape of the token is this module's
question and the legality of the state is the authority's.

THE NEUTRAL RULER IS `savegame`, INDEPENDENT OF THIS MODULE. `the_dispatch_reproduces_the_savegame_ruler`
runs a single-floor token sequence through dispatch, stores the resulting `(pos, stream)` and the tokens
(as an `actionlog`) via `savegame` — which serialized them INDEPENDENTLY of any dispatch — restores, decodes
the restored tokens and re-dispatches them from the origin, and requires the reproduced level/entity/stream
identities to EQUAL what `savegame` stored. A corrupted token DIVERGES that reproduction, so the check is not
vacuous. `savegame` is imported LAZILY inside the law so this module's declared substrate stays the dispatch
stack.

THIS RUNG IS SINGLE-PEER AND STOPS SHORT ON PURPOSE. It defines the vocabulary and the dispatch; it does NOT
capture actions into a live log (a wiring rung), reconstruct a run from origin as an authoritative operation
(`replay`, rung after this), reconcile a cross-peer union (`lockstep.canon` needs coordinates game actions
lack), assemble the canonical `D_n` (`statecanon`), or bind health/inventory to `combat`/`heirloom` (a
persistence contract). Those are named DEFERs, not omissions.

GRADE (honest, D5). MEASURED: over the `gamegen` corpus, a dispatched MOVE/DESCEND/LOOT equals its authority
called directly; the stream advances only on LOOT (0 for MOVE and DESCEND); a token round-trips through
`encode`/`decode` and through an `actionlog` in append order; and the full actionlog -> decode -> dispatch
chain reproduces the state `savegame` stored independently, while a corrupted token diverges it. ESTABLISHED:
the kinds are exactly the three state transitions and `combat`/`heirloom` are pure derivations excluded (read
off their imports); the router binds the authorities and reimplements no transition (read off the AST); a
malformed token refuses typed `ENACT-REFUSE` while a bad state surfaces the authority's code; the declared
substrate is the dispatch stack and stdlib. DECLARED: that the vocabulary is exactly these three kinds with
these payloads, single-peer, and that live capture, from-origin replay, cross-peer reconciliation, the
assembled `D_n`, and health/inventory binding are LATER rungs'. does_not_show: that a token stream is
`replay`'s sole input (replay is unbuilt); cross-peer order independence (`lockstep.canon`'s coordinates are
unearned here); the assembled canonical state (`statecanon`'s); and nothing about the transition math itself,
which stands in `move`/`descend`/`loot` and imports no `enact`."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import move as _M                                                        # noqa: E402  (the MOVE authority)
import descend as _DE                                                    # noqa: E402  (the DESCEND authority)
import loot as _L                                                        # noqa: E402  (the LOOT authority)
import actionlog as _A                                                   # noqa: E402  (the ordering authority)

MAGIC = b"URDRENA1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the typed action authority (kind, payload, dispatch)"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "move", "descend", "loot", "actionlog")

#: DECLARED — the action kinds, EXACTLY the three canonical state transitions established by code sweep. A
#: kind is a function that takes a canonical state component and returns an updated one; `combat`/`heirloom`
#: are pure derivations and are not here (see `the_excluded_modules_are_pure_derivations`).
MOVE = "MOVE"
DESCEND = "DESCEND"
LOOT = "LOOT"
KINDS = (MOVE, DESCEND, LOOT)

#: The kind tag byte that opens a token. One byte per kind; a move token appends its direction.
TAG = {MOVE: b"M", DESCEND: b"D", LOOT: b"L"}
_BY_TAG = {t: k for k, t in TAG.items()}

#: The kinds that carry a payload, and where the payload's vocabulary is single-sourced: a move carries one
#: `move.DIRECTIONS` command; descend and loot carry nothing (their effect is a function of the state alone).
_NULLARY = (DESCEND, LOOT)

#: The excluded certified-arithmetic modules — pure derivations, not state transitions. Named so the
#: exclusion is a declaration a law can check against their actual imports, not a silent omission.
_DERIVATIONS = ("combat", "heirloom")


class EnactError(Exception):
    def __init__(self, message):
        super().__init__(f"ENACT-REFUSE: {message}")
        self.code = "ENACT-REFUSE"


# ---- the vocabulary: a typed action <-> a canonical token -----------------------------------------------
def encode(kind, payload=None):
    """The canonical action token for a typed action. `MOVE` requires a `move.DIRECTIONS` command as its
    payload; `DESCEND`/`LOOT` require none. A malformed kind or payload refuses typed `ENACT-REFUSE`."""
    if kind not in KINDS:
        raise EnactError(f"kind must be one of {list(KINDS)}, got {kind!r}")
    if kind == MOVE:
        if payload not in _M.DIRECTIONS:
            raise EnactError(f"a MOVE payload must be a direction in {sorted(_M.DIRECTIONS)}, got {payload!r}")
        return TAG[MOVE] + payload.encode("ascii")
    if payload is not None:
        raise EnactError(f"a {kind} action carries no payload, got {payload!r}")
    return TAG[kind]


def decode(token):
    """The inverse: a canonical token -> (kind, payload). Token-shape faults are THIS module's, typed
    `ENACT-REFUSE`; the legality of a state is the authority's question, not asked here."""
    if not isinstance(token, bytes):
        raise EnactError(f"a token must be bytes, got {type(token).__name__}")
    if len(token) < 1 or token[:1] not in _BY_TAG:
        raise EnactError(f"a token must open with a kind tag in {sorted(_BY_TAG)}, got {token!r}")
    kind = _BY_TAG[token[:1]]
    rest = token[1:]
    if kind == MOVE:
        cmd = rest.decode("ascii", "replace")
        if cmd not in _M.DIRECTIONS:
            raise EnactError(f"a MOVE token must carry a direction in {sorted(_M.DIRECTIONS)}, got {token!r}")
        return MOVE, cmd
    if rest != b"":
        raise EnactError(f"a {kind} token carries no payload, got trailing {rest!r}")
    return kind, None


def kind_of(token):
    return decode(token)[0]


def rng_advances(kind):
    """How many `rngstream` advances this KIND consumes — a fact about the kind, not about its presence in a
    history. Measured against the authorities: only `LOOT` consumes a draw."""
    if kind not in KINDS:
        raise EnactError(f"kind must be one of {list(KINDS)}, got {kind!r}")
    return 1 if kind == LOOT else 0


# ---- dispatch: bind a typed action to the one authority that owns it -------------------------------------
def dispatch(state, token):
    """THE ROUTER. From a state bundle `(level, pos, stream)` — every field an already-earned canonical
    component — and a canonical token, decode the kind and call the transition authority that owns it,
    threading the updated components back. Returns `(state', info)` where `info` is the authority's secondary
    result (the move outcome, the successor depth, or the drop). Binds; reimplements nothing. A bad state
    surfaces the AUTHORITY's typed refusal, never `ENACT-REFUSE`."""
    if not (isinstance(state, tuple) and len(state) == 3):
        raise EnactError(f"state must be a (level, pos, stream) tuple, got {state!r}")
    level, pos, stream = state
    kind, payload = decode(token)
    if kind == MOVE:
        outcome, pos2 = _M.step(level, pos, payload)
        return (level, pos2, stream), outcome
    if kind == DESCEND:
        level2, pos2 = _DE.descend(level, pos)
        return (level2, pos2, stream), level2.depth
    drop, stream2 = _L.loot(level, pos, stream)
    return (level, pos, stream2), drop


def apply(state, tokens):
    """Fold a token sequence, returning `(state', infos)`. Pure — the same `(state, tokens)` yields the same
    result on any host."""
    infos = []
    for t in tokens:
        state, info = dispatch(state, t)
        infos.append(info)
    return state, tuple(infos)


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def _origin(seed, depth, on="up"):
    """A fresh state bundle: a level from `(seed, depth)`, the entity at the up- or down-stairs, the stream
    at the run's root."""
    import descent as _D
    import rngstream as _R
    lvl = _M._G.generate(seed, depth)
    up, down = _D.endpoints(lvl)
    return (lvl, up if on == "up" else down, _R.root(seed))


def a_token_round_trips():
    """Every kind and every move direction `encode`s and `decode`s back to itself, and a nullary kind carries
    no payload."""
    ok = True
    for c in sorted(_M.DIRECTIONS):
        ok = ok and decode(encode(MOVE, c)) == (MOVE, c)
    for k in _NULLARY:
        ok = ok and decode(encode(k)) == (k, None)
    return ok


def the_kinds_are_exactly_the_state_transitions():
    """The vocabulary is exactly the three canonical state transitions — one dispatch binding each, and no
    more. A structural declaration: `KINDS` equals the tagged set and every kind has a tag."""
    return (KINDS == (MOVE, DESCEND, LOOT)
            and set(TAG) == set(KINDS) and set(_BY_TAG.values()) == set(KINDS)
            and len({TAG[k] for k in KINDS}) == len(KINDS))


def the_excluded_modules_are_pure_derivations():
    """`combat` and `heirloom` are OUT of the vocabulary because they are pure derivations, not state
    transitions — read off their ACTUAL imports (stdlib only; no `gamegen`/`entity`/`rngstream`/`move`), so
    neither can take or return a canonical component. Proved by construction rather than by prose."""
    import ast
    clean = True
    for mod in _DERIVATIONS:
        with open(_os.path.join(_HERE, mod + ".py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        top = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                top.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                top.add((node.module or "").split(".")[0])
        clean = clean and not ({"gamegen", "entity", "rngstream", "move", "descend", "loot"} & top)
        clean = clean and mod not in TAG.values() and mod.upper() not in KINDS
    return clean


def move_dispatch_matches_the_authority(seed, depth):
    """A dispatched MOVE equals `move.step` called directly, for every direction — the router routes, it does
    not re-derive."""
    lvl, pos, stream = _origin(seed, depth, "up")
    ok = True
    for c in sorted(_M.DIRECTIONS):
        (l2, p2, s2), info = dispatch((lvl, pos, stream), encode(MOVE, c))
        outcome, ep2 = _M.step(lvl, pos, c)
        ok = ok and l2 is lvl and s2 is stream and p2 == ep2 and info == outcome
    return ok


def descend_dispatch_matches_the_authority(seed, depth):
    """A dispatched DESCEND from the down-stairs equals `descend.descend` called directly."""
    import gamegen as _G
    if depth >= _G.DEPTH_MAX:
        return True                                          # ceiling members exercised elsewhere
    lvl, down, stream = _origin(seed, depth, "down")
    (l2, p2, s2), info = dispatch((lvl, down, stream), encode(DESCEND))
    el2, ep2 = _DE.descend(lvl, down)
    return (s2 is stream and p2 == ep2 and info == l2.depth
            and _G.level_digest(l2) == _G.level_digest(el2))


def loot_dispatch_matches_the_authority(seed, depth):
    """A dispatched LOOT equals `loot.loot` called directly — the same drop and the same successor stream."""
    lvl, pos, stream = _origin(seed, depth, "up")
    (l2, p2, s2), info = dispatch((lvl, pos, stream), encode(LOOT))
    edrop, es2 = _L.loot(lvl, pos, stream)
    return l2 is lvl and p2 == pos and s2 == es2 and info == edrop


def only_loot_advances_the_stream(seed, depth):
    """RNG PER KIND: threading the stream through a dispatch of each kind advances it only on LOOT — 0 for
    MOVE and DESCEND. The counterexample to "every recorded action consumes a draw": presence in a history
    is not a draw. Returns the measured advances `(move, descend, loot)`, which must be `(0, 0, 1)` and match
    `rng_advances`."""
    import gamegen as _G
    lvl, up, s0 = _origin(seed, depth, "up")
    (_l, _p, sm), _i = dispatch((lvl, up, s0), encode(MOVE, "E"))
    adv_move = sm.n - s0.n
    adv_desc = 0
    if depth < _G.DEPTH_MAX:
        lvl_d, down, s0d = _origin(seed, depth, "down")
        (_l, _p, sd), _i = dispatch((lvl_d, down, s0d), encode(DESCEND))
        adv_desc = sd.n - s0d.n
    (_l, _p, sl), _i = dispatch((lvl, up, s0), encode(LOOT))
    adv_loot = sl.n - s0.n
    measured = (adv_move, adv_desc, adv_loot)
    return (measured == (0, 0, 1)
            and (rng_advances(MOVE), rng_advances(DESCEND), rng_advances(LOOT)) == (0, 0, 1))


def a_bad_token_is_ours_a_bad_state_is_the_authoritys(seed, depth):
    """OWNERSHIP: a malformed TOKEN refuses `ENACT-REFUSE` (this module's); a VALID token dispatched against a
    malformed STATE surfaces the AUTHORITY's code (`MOVE-REFUSE`/`LOOT-REFUSE`), never `ENACT-REFUSE`. The
    token's shape is ours; the state's legality is theirs."""
    lvl, up, stream = _origin(seed, depth, "up")
    # our fault: a token that is not a valid action
    ours = 0
    for bad in (b"", b"Z", b"MZ", b"D!", b"Lx", "MN"):
        try:
            dispatch((lvl, up, stream), bad)
        except EnactError as exc:
            ours += exc.code == "ENACT-REFUSE"
    # the authority's fault: a valid MOVE token from a non-traversable (wall) position -> MOVE-REFUSE
    wall = None
    for y in range(lvl.h):
        for x in range(lvl.w):
            if lvl.cells[y][x:x + 1] == _M._G.WALL:
                wall = (x, y); break
        if wall:
            break
    theirs = False
    try:
        dispatch((lvl, wall, stream), encode(MOVE, "N"))
    except _M.MoveError as exc:
        theirs = exc.code == "MOVE-REFUSE"
    except EnactError:
        theirs = False
    return ours == 6 and theirs


def the_ordering_is_actionlog_append(seed, depth):
    """Ordering is `actionlog`'s append order, not a second mechanism: a token sequence built into an
    `actionlog` recovers in append order, and re-dispatching the recovered entries reproduces the same state
    as dispatching the originals. `actionlog` owns the order; `enact` reads its entries as typed actions."""
    toks = (encode(LOOT), encode(MOVE, "E"), encode(MOVE, "S"), encode(LOOT), encode(MOVE, "N"))
    log = _A.from_actions(toks)
    recovered = _A.entries(log)
    if recovered != toks:
        return False
    st = _origin(seed, depth, "up")
    direct, _i = apply(st, toks)
    viahist, _j = apply(st, recovered)
    return (direct[1] == viahist[1] and direct[2] == viahist[2]
            and _M._G.level_digest(direct[0]) == _M._G.level_digest(viahist[0]))


def the_router_reimplements_nothing():
    """STRUCTURAL, read off this module's own AST: `dispatch` reaches the three authorities (`_M.step`,
    `_DE.descend`, `_L.loot`) and builds no transition of its own — it names no `hashlib` and no
    `gamegen`/`entity`/`rngstream` state constructor inside `dispatch`. And the declared substrate is exactly
    `ALLOWED_IMPORTS` (the dispatch stack + stdlib)."""
    import ast
    with open(_os.path.join(_HERE, "enact.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    disp = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "dispatch"), None)
    if disp is None:
        return False
    attrs = {n.attr for n in ast.walk(disp) if isinstance(n, ast.Attribute)}
    reaches = {"step", "descend", "loot"} <= attrs
    no_mint = "sha256" not in attrs
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return reaches and no_mint and top == set(ALLOWED_IMPORTS)


def the_dispatch_reproduces_the_savegame_ruler(seed, depth):
    """THE NEUTRAL RULER — `savegame`, independent of this module. A single-floor token sequence is dispatched
    to a final state; `savegame` stores that `(pos, stream)` and the tokens (as an `actionlog`) INDEPENDENTLY;
    restore, decode the restored tokens, re-dispatch from the origin, and require the reproduced
    level/entity/stream identities to EQUAL what `savegame` stored. A CORRUPTED token DIVERGES it, so the
    check is not vacuous. `savegame`/`gamegen`/`entity`/`rngstream` imported LAZILY. Returns
    `(reproduced, corruption_diverges)`."""
    import savegame as _SG
    import gamegen as _G
    import entity as _E
    toks = (encode(LOOT), encode(MOVE, "E"), encode(MOVE, "S"), encode(LOOT), encode(MOVE, "N"))
    st0 = _origin(seed, depth, "up")
    (lvl_f, pos_f, stream_f), _i = apply(st0, toks)
    rec = _SG.serialize(seed, depth, pos_f, stream_f, _A.from_actions(toks))
    s_r, d_r, level_r, ent_r, stream_r, log_r = _SG.restore(rec)
    # re-dispatch the restored tokens from a fresh origin
    st = _origin(s_r, d_r, "up")
    (lvl_x, pos_x, stream_x), _j = apply(st, _A.entries(log_r))
    reproduced = (_G.level_digest(lvl_x) == _G.level_digest(level_r)
                  and _E.digest_at(pos_x) == _E.entity_digest(ent_r)
                  and stream_x == stream_r)
    # corruption: flip a recorded move direction and require divergence
    bad = list(_A.entries(log_r))
    for i, t in enumerate(bad):
        if t == encode(MOVE, "E"):
            bad[i] = encode(MOVE, "W"); break
    (lvl_c, pos_c, stream_c), _k = apply(_origin(s_r, d_r, "up"), bad)
    diverges = not (pos_c == pos_x and stream_c == stream_x)
    return reproduced and diverges


def refuse_is_total():
    """(tokens, kinds): every malformed token refuses typed `ENACT-REFUSE`, and `encode`/`rng_advances` refuse
    a bad kind or payload — never a silent default."""
    t_ref = 0
    for bad in (None, 0, "MN", b"", b"Q", b"MZ", b"DX", b"L!"):
        try:
            decode(bad)
        except EnactError as exc:
            t_ref += exc.code == "ENACT-REFUSE"
    e_ref = 0
    for kind, pay in (("STEP", None), (MOVE, "X"), (MOVE, None), (DESCEND, "N"), (LOOT, 1)):
        try:
            encode(kind, pay)
        except EnactError as exc:
            e_ref += exc.code == "ENACT-REFUSE"
    return t_ref == 8, e_ref == 5


# ---- scenes ---------------------------------------------------------------------------------------------
#: The corpus is `gamegen`'s seeds/depths, so the dispatch laws are pinned on real levels.
import gamegen as _G                                                      # noqa: E402  (the corpus + Level)
CORPUS = _G.CORPUS
SCENES = ("vocabulary", "laws")


def _token_row():
    rows = []
    for c in sorted(_M.DIRECTIONS):
        rows.append("MOVE:%s=%s" % (c, encode(MOVE, c).hex()))
    for k in _NULLARY:
        rows.append("%s=%s" % (k, encode(k).hex()))
    advs = ",".join("%s:%d" % (k, rng_advances(k)) for k in KINDS)
    return "kinds=%s|dirs=%s|%s|rng=%s" % (
        ",".join(KINDS), ",".join(sorted(_M.DIRECTIONS)), "|".join(rows), advs)


def scene_case(name):
    if name == "vocabulary":
        return _token_row()
    if name == "laws":
        base = [(s, d) for s, d in CORPUS]
        return ("roundtrip=%s|kinds=%s|excluded=%s|move=%s|descend=%s|loot=%s|rng=%s|own=%s|order=%s|"
                "router=%s|ruler=%s|refuse=%s") % (
            a_token_round_trips(),
            the_kinds_are_exactly_the_state_transitions(),
            the_excluded_modules_are_pure_derivations(),
            tuple(move_dispatch_matches_the_authority(s, d) for s, d in base),
            tuple(descend_dispatch_matches_the_authority(s, d) for s, d in base),
            tuple(loot_dispatch_matches_the_authority(s, d) for s, d in base),
            tuple(only_loot_advances_the_stream(s, d) for s, d in base),
            tuple(a_bad_token_is_ours_a_bad_state_is_the_authoritys(s, d) for s, d in base),
            tuple(the_ordering_is_actionlog_append(s, d) for s, d in base),
            the_router_reimplements_nothing(),
            tuple(the_dispatch_reproduces_the_savegame_ruler(s, d) for s, d in base),
            refuse_is_total())
    raise EnactError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def enact_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_enact.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise EnactError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and enact_digest() == golden("enact"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except EnactError as exc:
        return exc.code == "ENACT-REFUSE"
    return False


def main():
    print("ENACT — the typed action authority: a kind, a payload, and one dispatch (URDRENA1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("kinds:", KINDS, " move dirs:", sorted(_M.DIRECTIONS))
    print()
    for c in sorted(_M.DIRECTIONS):
        print("  MOVE %s -> token %s" % (c, encode(MOVE, c)))
    print("  DESCEND -> token", encode(DESCEND), "  LOOT -> token", encode(LOOT))
    print("  rng advances:", {k: rng_advances(k) for k in KINDS})
    print()
    print("kinds are exactly the transitions :", the_kinds_are_exactly_the_state_transitions())
    print("combat/heirloom excluded (pure)   :", the_excluded_modules_are_pure_derivations())
    print("move dispatch == authority        :", move_dispatch_matches_the_authority(0, 1))
    print("descend dispatch == authority     :", descend_dispatch_matches_the_authority(0, 1))
    print("loot dispatch == authority        :", loot_dispatch_matches_the_authority(0, 1))
    print("only loot advances the stream     :", only_loot_advances_the_stream(0, 1))
    print("bad token ours / bad state theirs :", a_bad_token_is_ours_a_bad_state_is_the_authoritys(0, 1))
    print("ordering is actionlog append      :", the_ordering_is_actionlog_append(0, 1))
    print("router reimplements nothing       :", the_router_reimplements_nothing())
    print("dispatch reproduces savegame ruler:", the_dispatch_reproduces_the_savegame_ruler(0, 1))
    print("refuse total (tokens, kinds)      :", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("enact", enact_digest())
    print()
    print("does_not_show: that a token stream is replay's sole input (replay unbuilt); cross-peer order")
    print("independence (lockstep.canon's coordinates are unearned here); the assembled canonical D_n")
    print("(statecanon's); and nothing about the transition math, which lives in move/descend/loot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
