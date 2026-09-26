# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""rerun — the recovered action history must reproduce the independently stored state (URDRRRN1).

THE THIRTEENTH GAME-LAYER VERTICAL SLICE, and a CERTIFICATION LAYER, not a new simulation authority.
`actionlog` records the ordered history, `savegame` stores the earned canonical components, and `enact`
turns a recorded token into a canonical transition. This rung binds them: from a saved run it
reconstructs the run's ORIGIN, folds the recovered history through `enact`, and certifies that the fold
reproduces the state `savegame` stored INDEPENDENTLY. The new law is exactly that — the action history and
the independently persisted final state must AGREE when replayed from the uniquely reconstructed origin —
and nothing more.

THE ORIGIN RECONSTRUCTS FROM EARNED STATE ALONE (Slice B, closed by measurement, not by a new record).
A run's origin is `(level0, pos0, stream0)`, and every part derives from what a savegame already holds:

    seed       stored directly
    depth0     = savegame.depth - (DESCEND count in the actionlog)    # depth moves ONLY via descend, +1
    level0     = gamegen.generate(seed, depth0)
    pos0       = move.spawn(level0)                                   # the authoritative starting position
    stream0    = rngstream.root(seed)

`savegame.depth` is the CURRENT depth, not the origin depth — that was the whole of Slice B — and it is
recovered by subtracting the history's DESCEND count, because depth is a pure function of that count: MOVE
and LOOT leave depth unchanged and DESCEND is the only mover (+1), with no ascent. No origin field is added
to `savegame` and no hidden origin record is minted; the derivation reads only `seed`/`depth` (savegame)
and the DESCEND count (the actionlog, through `enact.decode`).

THE ORIGIN IS RECONSTRUCTED AND THEN VERIFIED, NEVER TRUSTED. The derived origin depth makes the final
depth agree with the stored depth BY CONSTRUCTION, so depth equality is TAUTOLOGICAL and is NOT the ruler.
The discriminating comparison is the canonical MUTABLE state — the entity POSITION and the RNG STREAM —
against the independently stored `(pos, stream)`. A run that did not start at `move.spawn`, a log that is
not this run's history, or any corruption, fails that comparison; even the "runs originate at spawn"
convention is confirmed per record rather than assumed, because a run that began elsewhere would not fold
from spawn to the stored state.

THE VERDICT, and the distinction is load-bearing. For a well-formed record whose fold completes:

    REPRODUCED   the fold's (pos, stream) equal the stored (pos, stream)
    DIVERGED     they do not — an envelope-valid record whose history does not reproduce its stored state

DIVERGED is a RETURN, not a refusal (the `move` MOVED/BLOCKED pattern): an inconsistent-but-well-formed
save is an in-domain answer, and it is precisely what proves this module performs the binding `savegame`
declines to. `savegame` stores the log and the state INDEPENDENTLY (its own `persist_is_not_replay`), so a
log inconsistent with the stored state is a valid savegame; replay is the law that catches it.

OWNERSHIP STAYS CRISP. Replay owns the RECORD+LOG pairing arithmetic and the verdict; every other fault
surfaces the authority that owns it. A malformed record is `savegame`'s `SAVEGAME-REFUSE`; a malformed
token is `enact`'s `ENACT-REFUSE`; a DESCEND that cannot dispatch mid-fold (not on the down-stairs) is
`descend`'s `DESCEND-REFUSE`, surfaced through `enact`. The one refusal replay OWNS is ORIGIN UNDERFLOW —
a log whose DESCEND count exceeds the stored depth, so no origin depth >= 1 exists — typed `RERUN-REFUSE`,
because that is a statement about the record+log pair no single authority owns.

IT ADDS NO AUTHORITY. The fold IS `enact.apply` (checked on the AST), so replay re-derives no transition
and advances no RNG of its own — the stream moves only through `loot` via `enact`, so a replayed run's
`stream.n` equals its LOOT count. Replay mints no action vocabulary and no identity mechanism; its only
`hashlib` use is the conformance machinery.

SINGLE-PEER, ON PURPOSE. This is the from-origin fold of ONE recovered history. Cross-peer union
reconciliation is a different authority: `lockstep.canon` (tools/netcode) canonicalizes a delivered union
by `(tick, peer, seq)`, and game actions carry none of those coordinates (Slice A), so replay imports no
`lockstep` and manufactures no such key. Cross-peer reconciliation, the assembled canonical `D_n`
(`statecanon`), observer invariance (KINEMA) and live capture (establishing that a log was actually
recorded from a live run) are LATER rungs'.

GRADE (honest, D5). MEASURED: over a corpus of runs, the origin reconstructs from earned state and the
fold reproduces the independently stored savegame bit-for-bit, for multi-floor runs and for a deep
single-floor run (arbitrary start depth); a corrupted, reordered or deleted history DIVERGES; an
envelope-valid record whose log does not fold to its stored state DIVERGES; the empty log replays to the
origin snapshot. ESTABLISHED: origin underflow refuses typed `RERUN-REFUSE`; a bogus DESCEND surfaces
`DESCEND-REFUSE` and a malformed token `ENACT-REFUSE` and a malformed record `SAVEGAME-REFUSE`; the fold is
`enact.apply` and replay mints no transition or RNG authority (read off the AST); the discriminator is
`(pos, stream)` while depth equality is structural. DECLARED: that a run originates at `move.spawn`, that
the verdict is REPRODUCED/DIVERGED, single-peer. does_not_show: that a savegame+log pair is the run a
player ACTUALLY played (only that the pair is INTERNALLY CONSISTENT — the log folds the reconstructed
origin to the stored state); cross-peer order independence (Slice A, unearned); the assembled canonical
`D_n` (statecanon's); and anything about observers, which stay KINEMA's."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                     # noqa: E402  (regenerate the origin level)
import move as _M                                                        # noqa: E402  (the spawn / BFS authority)
import rngstream as _R                                                   # noqa: E402  (the origin stream)
import entity as _E                                                      # noqa: E402  (compare the entity)
import actionlog as _A                                                   # noqa: E402  (recover the history)
import enact as _EN                                                      # noqa: E402  (decode + fold)
import savegame as _SV                                                   # noqa: E402  (the neutral ruler)

MAGIC = b"URDRRRN1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the from-origin replay certification of a saved run"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "move", "rngstream", "entity", "actionlog", "enact", "savegame")

REPRODUCED = "REPRODUCED"
DIVERGED = "DIVERGED"
VERDICTS = (REPRODUCED, DIVERGED)


class RerunError(Exception):
    def __init__(self, message):
        super().__init__(f"RERUN-REFUSE: {message}")
        self.code = "RERUN-REFUSE"


# ---- origin reconstruction (Slice B: from earned state alone) -------------------------------------------
def descend_count(log):
    """The number of DESCEND actions in the history — the only mover of depth. Read through `enact.decode`,
    so a malformed token surfaces `enact`'s ENACT-REFUSE rather than being miscounted here."""
    return sum(1 for t in _A.entries(log) if _EN.decode(t)[0] == _EN.DESCEND)


def reconstruct_origin(seed, depth, log):
    """The run's origin `(level0, pos0, stream0)`, derived from earned state: `depth0 = depth -
    descend_count(log)` (depth moves only via DESCEND, +1), `level0 = gamegen.generate(seed, depth0)`,
    `pos0 = move.spawn(level0)`, `stream0 = rngstream.root(seed)`. ORIGIN UNDERFLOW — the log's DESCEND
    count exceeding the stored depth, so no origin depth >= 1 exists — is replay's own typed refusal, the
    one fault that is a statement about the record+log pair rather than about any single authority."""
    nd = descend_count(log)
    depth0 = depth - nd
    if depth0 < 1:
        raise RerunError(f"the log's DESCEND count {nd} exceeds the stored depth {depth}: "
                          f"no origin depth >= 1 exists (got {depth0})")
    level0 = _G.generate(seed, depth0)
    pos0 = _M.spawn(level0)
    stream0 = _R.root(seed)
    return level0, pos0, stream0


# ---- the certification --------------------------------------------------------------------------------
def replay(record):
    """THE LAW. Restore the savegame, reconstruct the origin, fold the recovered history through `enact`,
    and certify the fold reproduces the INDEPENDENTLY stored canonical mutable state. Returns `(verdict,
    (level, pos, stream))` with verdict REPRODUCED or DIVERGED. The discriminator is `(pos, stream)`;
    depth equality is structural and is not the ruler. Malformed record / token / mid-fold dispatch and
    origin underflow surface their owning authority's typed refusal."""
    seed, depth, _level, ent, stream, log = _SV.restore(record)          # SAVEGAME-REFUSE on a bad record
    origin = reconstruct_origin(seed, depth, log)                        # RERUN-REFUSE on underflow
    (lvl, pos, strm), _infos = _EN.apply(origin, _A.entries(log))        # ENACT/MOVE/DESCEND-REFUSE surface
    reproduced = (pos == ent.get("pos") and strm == stream)             # pos + stream are the discriminators
    return (REPRODUCED if reproduced else DIVERGED), (lvl, pos, strm)


def verdict(record):
    """Just the verdict."""
    return replay(record)[0]


# ---- corpus construction (deterministic runs, via the move authority) ----------------------------------
def _spawn_origin(seed, depth):
    lvl = _G.generate(seed, depth)
    return (lvl, _M.spawn(lvl), _R.root(seed))


def _path_to_down(level):
    """A shortest N/S/E/W path from the spawn to the down-stairs, found by BFS over the `move` authority
    (fixed direction order, so it is deterministic). Used only to build reachable multi-floor test runs."""
    import collections
    up, down = _M._D.endpoints(level)
    q = collections.deque([(up, ())])
    seen = {up}
    while q:
        pos, path = q.popleft()
        if pos == down:
            return path
        for c in ("N", "S", "E", "W"):
            outcome, nxt = _M.step(level, pos, c)
            if outcome == _M.MOVED and nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + (c,)))
    return None


def build_run(seed, depth0, floors, loots):
    """A realistic dispatch-valid run from the spawn of `(seed, depth0)`: loot, walk to the down-stairs,
    descend, and repeat for `floors` floors. Returns `(tokens, final_state)`; the origin pos is the spawn
    by the `move` contract."""
    toks = []
    state = _spawn_origin(seed, depth0)
    for f in range(floors):
        for _ in range(loots):
            t = _EN.encode(_EN.LOOT)
            toks.append(t)
            state, _ = _EN.dispatch(state, t)
        if f + 1 < floors:
            path = _path_to_down(state[0])
            if path is None:                                            # pragma: no cover
                raise RerunError("no path to the down-stairs on a corpus level")
            for c in path:
                t = _EN.encode(_EN.MOVE, c)
                toks.append(t)
                state, _ = _EN.dispatch(state, t)
            t = _EN.encode(_EN.DESCEND)
            toks.append(t)
            state, _ = _EN.dispatch(state, t)
    return tuple(toks), state


def build_flat_run(seed, depth, nmoves, nloots):
    """A single-floor run (NO descend): from the spawn, interleave real MOVED steps and loots. A flat run
    always dispatches cleanly (no descend to become invalid), so tampering it yields a DIVERGED verdict
    rather than a mid-fold refusal — the clean way to exhibit the ruler."""
    toks = []
    state = _spawn_origin(seed, depth)
    made_m = made_l = 0
    while made_l < nloots or made_m < nmoves:
        if made_l < nloots:
            t = _EN.encode(_EN.LOOT); toks.append(t); state, _ = _EN.dispatch(state, t); made_l += 1
        if made_m < nmoves:
            stepped = False
            for c in ("E", "S", "W", "N"):
                if _M.step(state[0], state[1], c)[0] == _M.MOVED:
                    t = _EN.encode(_EN.MOVE, c); toks.append(t); state, _ = _EN.dispatch(state, t)
                    made_m += 1; stepped = True; break
            if not stepped:
                made_m = nmoves                                          # boxed in; stop adding moves
    return tuple(toks), state


def _saved_run(seed, depth0, floors, loots):
    """Build a run and store its END state as an independent savegame — the neutral ruler."""
    toks, (lvl, pos, strm) = build_run(seed, depth0, floors, loots)
    log = _A.from_actions(toks)
    return _SV.serialize(seed, lvl.depth, pos, strm, log), toks, (lvl, pos, strm)


def _saved_flat_run(seed, depth, nmoves, nloots):
    """A saved single-floor run (no descend) — the clean substrate for the tamper/verdict laws."""
    toks, (lvl, pos, strm) = build_flat_run(seed, depth, nmoves, nloots)
    return _SV.serialize(seed, lvl.depth, pos, strm, _A.from_actions(toks)), toks, (lvl, pos, strm)


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def a_run_reproduces_and_recovers_its_origin(seed, depth0, floors, loots):
    """A saved run REPRODUCES, and the reconstructed origin depth equals the true origin depth — the
    from-origin fold matches the independently stored state."""
    rec, toks, _final = _saved_run(seed, depth0, floors, loots)
    seed_r, depth_r, _lvl, _ent, _strm, log = _SV.restore(rec)
    depth0_r = depth_r - descend_count(log)
    v, _state = replay(rec)
    return v == REPRODUCED and depth0_r == depth0


def a_deep_single_floor_run_reproduces(seed, depth0):
    """Arbitrary start depth is not accidentally tied to depth 1: a deep run with NO descend reconstructs
    origin depth == depth0 == current depth and REPRODUCES."""
    rec, _toks, _final = _saved_run(seed, depth0, 1, 3)
    seed_r, depth_r, _lvl, _ent, _strm, log = _SV.restore(rec)
    return (verdict(rec) == REPRODUCED and descend_count(log) == 0
            and depth_r - descend_count(log) == depth0)


def _tamper_log(rec, newtoks):
    """Re-store a record with the SAME (seed, depth, pos, stream) but a different log — an envelope-valid
    record whose history no longer matches its stored state (savegame stores them independently)."""
    seed, depth, _lvl, ent, stream, _log = _SV.restore(rec)
    return _SV.serialize(seed, depth, ent.get("pos"), stream, _A.from_actions(newtoks))


def a_corrupted_history_diverges(seed, depth0):
    """Flipping a recorded MOVE direction makes the fold miss the stored state — DIVERGED (on a flat run,
    where no later descend can turn the corruption into a mid-fold refusal)."""
    rec, toks, _final = _saved_flat_run(seed, depth0, 4, 3)
    bad = list(toks)
    for i, t in enumerate(bad):
        if t[:1] == b"M":
            cur = _EN.decode(t)[1]
            bad[i] = _EN.encode(_EN.MOVE, {"E": "W", "W": "E", "N": "S", "S": "N"}[cur])
            break
    return verdict(_tamper_log(rec, bad)) == DIVERGED


def a_reordered_history_diverges(seed, depth0):
    """Swapping a LOOT with a following MOVE changes the committed state — DIVERGED (loot's source is the
    position, so order is load-bearing)."""
    rec, toks, _final = _saved_flat_run(seed, depth0, 4, 3)
    ro = list(toks)
    for i in range(len(ro) - 1):
        if ro[i][:1] == b"L" and ro[i + 1][:1] == b"M":
            ro[i], ro[i + 1] = ro[i + 1], ro[i]
            break
    return verdict(_tamper_log(rec, ro)) == DIVERGED


def a_deleted_action_diverges(seed, depth0):
    """Dropping an action makes the fold miss the stored state — DIVERGED."""
    rec, toks, _final = _saved_flat_run(seed, depth0, 4, 3)
    return verdict(_tamper_log(rec, list(toks)[1:])) == DIVERGED


def an_inconsistent_pair_diverges(seed, depth0):
    """THE BINDING REPLAY OWNS: an envelope-valid savegame whose stored (pos, stream) came from the real
    run but whose LOG is a different (shorter) history REPRODUCES to a different state — DIVERGED. This is
    the check `savegame` declines to make (it stores log and state independently)."""
    rec, toks, _final = _saved_flat_run(seed, depth0, 4, 3)
    return verdict(_tamper_log(rec, list(toks)[:-1])) == DIVERGED


def origin_underflow_refuses(seed, depth0):
    """A log whose DESCEND count exceeds the stored depth has no origin depth >= 1 — replay's OWN typed
    refusal RERUN-REFUSE."""
    rec, _toks, _final = _saved_run(seed, depth0, 1, 1)
    seed_r, depth_r, _lvl, ent, stream, _log = _SV.restore(rec)
    many = _A.from_actions(tuple(_EN.encode(_EN.DESCEND) for _ in range(depth_r)))  # count >= depth
    bad = _SV.serialize(seed_r, depth_r, ent.get("pos"), stream, many)
    try:
        replay(bad)
    except RerunError as exc:
        return exc.code == "RERUN-REFUSE"
    return False


def a_bogus_descend_surfaces_the_authority(seed, depth0):
    """A DESCEND recorded where the entity is not on the down-stairs cannot dispatch mid-fold and surfaces
    `descend`'s DESCEND-REFUSE — the authority that owns state legality, not replay."""
    rec, _toks, _final = _saved_run(seed, depth0, 1, 1)
    seed_r, depth_r, _lvl, ent, stream, _log = _SV.restore(rec)
    # a LOOT (keeps the entity at the spawn/up-stairs) then a DESCEND from there -> not the down-stairs
    bad = _SV.serialize(seed_r, depth_r + 1, ent.get("pos"), stream,
                        _A.from_actions((_EN.encode(_EN.LOOT), _EN.encode(_EN.DESCEND))))
    try:
        replay(bad)
    except _EN._DE.DescendError as exc:
        return exc.code == "DESCEND-REFUSE"
    except (RerunError, _EN.EnactError, _SV.SavegameError):
        return False
    return False


def a_malformed_record_is_savegames_refusal():
    """A malformed record surfaces `savegame`'s SAVEGAME-REFUSE, not a replay code."""
    for bad in (None, 0, b"short", b"X" * 400):
        try:
            replay(bad)
        except _SV.SavegameError as exc:
            if exc.code != "SAVEGAME-REFUSE":
                return False
        except Exception:
            return False
    return True


def a_malformed_token_is_enacts_refusal(seed, depth0):
    """A malformed token in the log surfaces `enact`'s ENACT-REFUSE, not a replay code."""
    rec, _toks, _final = _saved_run(seed, depth0, 1, 1)
    seed_r, depth_r, _lvl, ent, stream, _log = _SV.restore(rec)
    bad = _SV.serialize(seed_r, depth_r, ent.get("pos"), stream, _A.from_actions((b"ZZ",)))
    try:
        replay(bad)
    except _EN.EnactError as exc:
        return exc.code == "ENACT-REFUSE"
    except (RerunError, _SV.SavegameError):
        return False
    return False


def the_empty_log_replays_to_the_origin(seed, depth0):
    """The empty log REPRODUCES and its final state IS the origin snapshot — meaningful, not a vacuous
    success: a savegame of the origin (spawn, root, empty log) round-trips through replay as REPRODUCED,
    and its state equals the reconstructed origin."""
    origin = _spawn_origin(seed, depth0)
    rec = _SV.serialize(seed, depth0, origin[1], origin[2], _A.empty())
    v, (lvl, pos, strm) = replay(rec)
    return (v == REPRODUCED and pos == origin[1] and strm == origin[2]
            and _G.level_digest(lvl) == _G.level_digest(origin[0]))


def the_discriminator_is_pos_and_stream(seed, depth0):
    """THE USER'S CONSTRAINT, made a falsifier: because origin depth is derived from the stored depth, the
    fold's depth ALWAYS equals the stored depth — so depth equality is TAUTOLOGICAL and cannot be the
    ruler. On a corrupted history the verdict is DIVERGED, yet the folded depth still equals the stored
    depth; the divergence is carried by `(pos, stream)`. Returns (depth_is_tautological, verdict_diverged,
    discriminated_by_pos_or_stream)."""
    rec, toks, _final = _saved_flat_run(seed, depth0, 4, 3)
    bad = list(toks)
    for i, t in enumerate(bad):
        if t[:1] == b"M":
            cur = _EN.decode(t)[1]
            bad[i] = _EN.encode(_EN.MOVE, {"E": "W", "W": "E", "N": "S", "S": "N"}[cur])
            break
    tampered = _tamper_log(rec, bad)
    _s, stored_depth, _l, ent, stream, log = _SV.restore(tampered)
    v, (lvl, pos, strm) = replay(tampered)
    depth_taut = (lvl.depth == stored_depth)                            # always true by construction
    discriminated = (pos != ent.get("pos")) or (strm != stream)
    return depth_taut, v == DIVERGED, discriminated


def only_loot_advances_across_a_replay(seed, depth0):
    """The RNG distinction survives replay: the replayed stream's index equals the run's LOOT count, so
    replay advances no RNG of its own."""
    rec, toks, _final = _saved_run(seed, depth0, 2, 2)
    _v, (_lvl, _pos, strm) = replay(rec)
    loots = sum(1 for t in toks if _EN.decode(t)[0] == _EN.LOOT)
    return strm.n == loots


def the_fold_adds_no_authority():
    """STRUCTURAL, read off this module's own AST: `replay` folds through `enact.apply` and reaches no
    transition constructor or RNG advance of its own — no `hashlib` inside `replay`, and the fold is
    `enact`'s. The declared substrate is exactly `ALLOWED_IMPORTS` and imports no `lockstep` (single-peer;
    cross-peer `(tick, peer, seq)` is unearned — Slice A)."""
    import ast
    with open(_os.path.join(_HERE, "rerun.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "replay"), None)
    if fn is None:
        return False
    attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    folds = "apply" in attrs                                            # enact.apply
    no_mint = "sha256" not in attrs and "advance" not in attrs
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    return (folds and no_mint and top == set(ALLOWED_IMPORTS) and "lockstep" not in top)


def refuse_is_total(seed=0, depth0=1):
    """(underflow, malformed_record, malformed_token): each surfaces its owning authority's typed code."""
    return (origin_underflow_refuses(seed, depth0),
            a_malformed_record_is_savegames_refusal(),
            a_malformed_token_is_enacts_refusal(seed, depth0))


# ---- scenes ---------------------------------------------------------------------------------------------
#: The corpus: gamegen seeds at assorted origin depths, each a run of several floors — pinned by the
#: reconstructed origin depth and the replay verdict + the final (pos, stream) identity.
CORPUS = ((0, 1, 3, 2), (1, 2, 2, 2), (12345, 3, 3, 1), (0xC0FFEE, 2, 3, 2), (7, 5, 1, 3))
SCENES = ("reconstruction", "laws")


def _run_row(seed, depth0, floors, loots):
    rec, toks, (lvl, pos, strm) = _saved_run(seed, depth0, floors, loots)
    seed_r, depth_r, _l, _e, _s, log = _SV.restore(rec)
    v, (_lvl, rpos, rstrm) = replay(rec)
    return "%d,%d,f%d=d0:%d|%s|%d,%d|%s" % (
        seed, depth0, floors, depth_r - descend_count(log), v, rpos[0], rpos[1],
        _R.stream_digest(rstrm)[:12])


def scene_case(name):
    if name == "reconstruction":
        return "|".join(_run_row(*c) for c in CORPUS)
    if name == "laws":
        base = [(s, d) for s, d, _f, _l in CORPUS]
        return ("repro=%s|deep=%s|corrupt=%s|reorder=%s|delete=%s|inconsistent=%s|underflow=%s|bogus=%s|"
                "badrec=%s|badtok=%s|empty=%s|discrim=%s|rng=%s|noauth=%s|refuse=%s") % (
            tuple(a_run_reproduces_and_recovers_its_origin(s, d, f, l) for s, d, f, l in CORPUS),
            tuple(a_deep_single_floor_run_reproduces(s, d) for s, d in base),
            tuple(a_corrupted_history_diverges(s, d) for s, d in base),
            tuple(a_reordered_history_diverges(s, d) for s, d in base),
            tuple(a_deleted_action_diverges(s, d) for s, d in base),
            tuple(an_inconsistent_pair_diverges(s, d) for s, d in base),
            tuple(origin_underflow_refuses(s, d) for s, d in base),
            tuple(a_bogus_descend_surfaces_the_authority(s, d) for s, d in base),
            a_malformed_record_is_savegames_refusal(),
            tuple(a_malformed_token_is_enacts_refusal(s, d) for s, d in base),
            tuple(the_empty_log_replays_to_the_origin(s, d) for s, d in base),
            tuple(the_discriminator_is_pos_and_stream(s, d) for s, d in base),
            tuple(only_loot_advances_across_a_replay(s, d) for s, d in base),
            the_fold_adds_no_authority(),
            tuple(refuse_is_total(s, d) for s, d in base))
    raise RerunError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def rerun_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_rerun.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise RerunError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and rerun_digest() == golden("rerun"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except RerunError as exc:
        return exc.code == "RERUN-REFUSE"
    return False


def main():
    print("REPLAY — the recovered action history must reproduce the independently stored state (URDRRRN1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print()
    rec, toks, (lvl, pos, strm) = _saved_run(0xC0FFEE, 2, 3, 2)
    seed_r, depth_r, _l, _e, _s, log = _SV.restore(rec)
    print("run: %d tokens, %d DESCENDs, stored depth %d" % (len(toks), descend_count(log), depth_r))
    print("reconstructed origin depth:", depth_r - descend_count(log), "(= %d - %d)" % (depth_r, descend_count(log)))
    v, (l2, p2, s2) = replay(rec)
    print("replay verdict:", v, " final pos", p2, " stream.n", s2.n)
    print()
    print("run reproduces + recovers origin :", a_run_reproduces_and_recovers_its_origin(0xC0FFEE, 2, 3, 2))
    print("deep single-floor reproduces     :", a_deep_single_floor_run_reproduces(7, 5))
    print("corrupted history diverges       :", a_corrupted_history_diverges(0, 1))
    print("inconsistent pair diverges       :", an_inconsistent_pair_diverges(0, 1))
    print("origin underflow refuses         :", origin_underflow_refuses(0, 1))
    print("bogus descend -> DESCEND-REFUSE  :", a_bogus_descend_surfaces_the_authority(0, 1))
    print("empty log replays to origin      :", the_empty_log_replays_to_the_origin(0, 1))
    print("discriminator is pos+stream      :", the_discriminator_is_pos_and_stream(0, 1))
    print("only loot advances across replay :", only_loot_advances_across_a_replay(0, 1))
    print("the fold adds no authority       :", the_fold_adds_no_authority())
    print("refuse total                     :", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("rerun", rerun_digest())
    print()
    print("does_not_show: that a savegame+log pair is the run a player ACTUALLY played (only that the pair")
    print("is internally consistent); cross-peer order independence (Slice A); the assembled D_n")
    print("(statecanon's); and anything about observers, which stay KINEMA's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
