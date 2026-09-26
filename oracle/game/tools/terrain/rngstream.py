# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""rngstream — the canonical RNG stream, the first STATEFUL canonical component (URDRRNG1).

THE FIFTH GAME-LAYER VERTICAL SLICE, and the first whose STATE ADVANCES. `gamegen` generates a level
from a seed by STATELESS content-addressed draws (`SHA-256(MAGIC|seed|depth|tag|i)` — "there is no RNG
object"); `descent` witnesses a topology property; `move` steps an entity; `entity` names it. None of
them holds a stream: canonical randomness that is CONSUMED, so that advancing it is itself a change to
canonical state. D24 §2 lists exactly that field — "RNG state: the deterministic stream, advanced only
by canonical actions" — and this module is it.

STATEFUL, WHERE `gamegen` IS STATELESS, AND THAT IS THE POINT. `gamegen`'s draw depends only on its
own preimage and on nothing that happened before it, so generation is order-independent and reproduces
anywhere. The RNG STREAM is the opposite by design: `R_{n+1}` depends on `R_n` AND on the action, so
the stream COMMITS to the ordered action history (D24 §2's "authoritative action history — the ordered
inputs replay consumes"). That commitment is what makes a run's randomness replayable and auditable:
the same seed and the same actions reproduce the same stream, and a different action sequence diverges.
Advancing IS a canonical state change, so the stream's identity participates in the canonical state
digest — the reason a stateless draw could not have carried this field.

ONE STREAM, ROOTED AT THE RUN'S SEED — NOT A SECOND SEED. §2 says "the deterministic stream"
(singular) and lists `seed` as "the run's generative root". So the stream roots at the SAME `seed`
`gamegen` already uses, through a DOMAIN-SEPARATED root so it cannot be confused with a `gamegen`
derivation of that seed:

    R_0 = SHA-256( b"rngstream/v1" | b"|s:" | seed )

The domain tag is part of the LAW, not an incident of the implementation: drop it and `R_0` collapses
toward a rootless hash. `SEED_MAX`/`SEED_BITS` mirror `gamegen`'s domain and a law pins them equal, so
the "same seed" claim is single-sourced rather than a copied constant.

THE STREAM STATE CARRIES AN EXPLICIT SEQUENCE COORDINATE `(n, R_n)`, NOT MERELY `R_n`. Two runs that
happen to hold the same stream value after different numbers of actions must NOT be able to masquerade
as the same canonical state, so `n` is bound into the identity:

    I_n = SHA-256( URDRRNG1|n:<n>|r:<R_n as hex> )

ADVANCE IS AN ACTION; A READ NEVER ADVANCES — BY CONSTRUCTION. `Stream` is immutable: `advance` returns
a NEW `Stream`, and every read (`stream_bytes`, `stream_digest`, `peek`) takes a `Stream` and returns a
VALUE. So a read cannot advance the stream because it has no handle that could — the same structural
firewall `entity` used to keep view fields out of the digest, and `move` used to keep a view quantity
out of the state. The preimages are tag-separated — `adv` for the advance chain, `draw` for `peek` —
so a consumer's draw label can never collide with the advance that threads the stream.

VERIFICATION-ONLY SYNTHETIC ACTION. `advance(stream, action)` takes ANY canonical action token; this
module declares NO gameplay action vocabulary of its own (that is `move`'s `DIRECTIONS`, and `loot`'s /
`combat`'s draws to come). Its corpus exercises the advance law with clearly-synthetic tokens (`v0`,
`v1`, …) whose ONLY purpose is to make the stream law non-vacuously testable now, so `loot` (rung 5)
can be the first REAL consumer without this rung having to invent gameplay.

MOVE IS NOT CONTAMINATED. `move` consumes no randomness today, and this rung does not change that:
`move` neither imports this module nor carries a stream, so a move action CANNOT advance the stream. A
boundary law measures it — a reference assembly of `(level, entity, stream)` stepped by `move` leaves
the stream a fixed point while the entity moves — as a COMPATIBILITY invariant for the current `move`
contract, not a universal claim that movement can never consume randomness; a later rung that changes
that revises the boundary explicitly rather than moving `move` underneath this one.

GRADE (honest, D5). MEASURED: over a corpus of seeds and a fixed synthetic action sequence, the root,
the advance chain, every prefix state and the top digest reproduce, across a hash-seed sweep of fresh
interpreters; identical (seed, actions) reproduce the whole stream trace; a different action sequence
diverges; a reference `move` assembly leaves the stream fixed while the entity moves. ESTABLISHED: the
constructor and the domain refuse malformed seeds, actions and bounds typed; a read leaves `(n, R_n)`
unchanged; incremental and batch advancement agree at every prefix; the same `R` at different `n` has a
different identity; the root is domain-separated from a `gamegen` derivation of the same seed. DECLARED:
that the URDRRNG1 serialization is v1 and is FROZEN — the golden vectors are its representation lock,
and a format change mints v2 rather than editing v1. does_not_show: WHICH real canonical actions
advance the stream (the synthetic action is verification-only; `move` advances nothing, and `loot` is
the first real consumer); independent sub-stream domains for decoupling subsystem draw order (a
counter-based `derive(R_n, domain)`, `loot`/`combat`'s to earn, not built here); statistical quality
of the draws beyond determinism; and the assembly of the full `D_n` snapshot, which is `statecanon`'s."""
import hashlib
import os as _os

MAGIC = b"URDRRNG1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the canonical RNG stream"
ALLOWED_IMPORTS = ("hashlib", "os")

#: The DOMAIN-SEPARATED root tag — part of the law. The `/v1` is the FROZEN serialization version:
#: a representation change mints `rngstream/v2` rather than editing v1's bytes.
DOMAIN = b"rngstream/v1"

#: The seed domain MIRRORS `gamegen`'s (the stream roots at the run's `gamegen` seed). Held here as a
#: local constant so the record depends on nothing under tools/ at load; `seed_domain_matches_gamegen`
#: pins it equal to `gamegen`'s by lazy import, so a drift reddens rather than diverging silently.
SEED_BITS = 64
SEED_MAX = (1 << SEED_BITS) - 1


class RngError(Exception):
    def __init__(self, message):
        super().__init__(f"RNG-REFUSE: {message}")
        self.code = "RNG-REFUSE"


def _is_seed(v):
    return type(v) is int and 0 <= v <= SEED_MAX          # bool is a subclass of int — excluded


def _canon_action(action):
    """A canonical action token as bytes. A `str` is UTF-8; `bytes` pass through; anything else is a
    typed refusal — the stream cannot fold a token it cannot serialize deterministically."""
    if isinstance(action, bytes):
        return action
    if isinstance(action, str):
        return action.encode("utf-8")
    raise RngError(f"action must be str or bytes, got {action!r}")


class Stream:
    """The canonical RNG stream state: a sequence coordinate `n` and a 32-byte digest `r`. Immutable by
    construction — `advance` returns a NEW `Stream`, and there is no mutator — which is what makes a
    read structurally unable to advance it. Equality and hashing are over `(n, r)`."""
    __slots__ = ("n", "r")

    def __init__(self, n, r):
        if not (type(n) is int and n >= 0):
            raise RngError(f"n must be a non-negative int, got {n!r}")
        if not (isinstance(r, bytes) and len(r) == 32):
            raise RngError(f"r must be 32 bytes, got {r!r}")
        self.n = n
        self.r = r

    def __eq__(self, other):
        return isinstance(other, Stream) and self.n == other.n and self.r == other.r

    def __hash__(self):
        return hash((self.n, self.r))

    def __repr__(self):
        return "Stream(n=%d, r=%s...)" % (self.n, self.r.hex()[:12])


def root(seed):
    """`R_0` from the run's seed, DOMAIN-SEPARATED so it cannot be a `gamegen` derivation of that seed."""
    if not _is_seed(seed):
        raise RngError(f"seed must be an int in 0..{SEED_MAX}, got {seed!r}")
    r0 = hashlib.sha256(DOMAIN + b"|s:%d" % seed).digest()
    return Stream(0, r0)


def advance(stream, action):
    """THE ADVANCE LAW: `R_{n+1} = SHA-256(DOMAIN|adv|R_n|action)`, `n -> n+1`. A pure function of
    `(stream, action)` — the same pair yields the same successor on any host. `R_n` is fixed-length, so
    the boundary between it and the action bytes is unambiguous."""
    if not isinstance(stream, Stream):
        raise RngError(f"stream must be a Stream, got {stream!r}")
    a = _canon_action(action)
    r = hashlib.sha256(DOMAIN + b"|adv|" + stream.r + b"|" + a).digest()
    return Stream(stream.n + 1, r)


def apply(stream, actions):
    """Fold an action sequence, returning the final `Stream`. Pure."""
    for a in actions:
        stream = advance(stream, a)
    return stream


def trace(stream, actions):
    """The prefix states: `[R_0, R_1, ..., R_k]` — the stream at every index, so an indexing error is
    localizable rather than visible only in the final digest."""
    out = [stream]
    for a in actions:
        stream = advance(stream, a)
        out.append(stream)
    return out


def peek(stream, label, bound):
    """A READ: a value in `0..bound-1` derived from `R_n` under a `draw`-tagged preimage, WITHOUT
    advancing. Returns an int; the `Stream` is untouched (it is immutable, and this returns no stream).
    The primitive a consumer (`loot`) will read before it decides to advance."""
    if not isinstance(stream, Stream):
        raise RngError(f"stream must be a Stream, got {stream!r}")
    if not (type(bound) is int and bound >= 1):
        raise RngError(f"bound must be an int >= 1, got {bound!r}")
    lab = _canon_action(label)
    d = hashlib.sha256(DOMAIN + b"|draw|" + stream.r + b"|" + lab).digest()
    return int.from_bytes(d[:8], "big") % bound


# ---- identity, in the frozen v1 serialization ----------------------------------------------------------
def stream_bytes(stream):
    """The canonical identity bytes — FROZEN v1: `URDRRNG1|n:<n>|r:<R_n hex>`. `n` participates, so the
    same `R` at a different `n` is a different canonical state."""
    return b"%s|n:%d|r:%s" % (MAGIC, stream.n, stream.r.hex().encode())


def stream_digest(stream):
    """`I_n` — the stream's canonical identity, the value composed into the run's `D_n` (the way `move`
    composes `entity.entity_digest`)."""
    return hashlib.sha256(stream_bytes(stream)).hexdigest()


def digest_after(seed, actions):
    """The identity of the stream reached from `seed` by `actions` — the convenience a later rung uses
    to fold the RNG component into canonical state identity."""
    return stream_digest(apply(root(seed), actions))


# ---- the laws / falsifiers -----------------------------------------------------------------------------
def _rootless(seed):
    """A root WITHOUT the domain tag — what `R_0` would be if the separation were dropped. Used only to
    prove the tag is load-bearing."""
    return hashlib.sha256(b"s:%d" % seed).digest()


def the_root_is_domain_separated(seed):
    """`R_0` is not a rootless hash of the seed, and not a `gamegen` derivation of the same seed — so
    the stream's namespace cannot be confused with generation's. `gamegen` is imported LAZILY so this
    module's declared substrate stays stdlib."""
    r0 = root(seed).r
    if r0 == _rootless(seed):
        return False
    import sys
    here = _os.path.dirname(_os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import gamegen as _G
    # a real, PUBLIC gamegen derivation of the same seed; different preimage, so different bytes
    return r0.hex() != _G.digest_of(seed, 1)


def an_advance_changes_the_state(seed, action="v0"):
    """A canonical action advances the coordinate AND the value AND the identity."""
    s0 = root(seed)
    s1 = advance(s0, action)
    return (s1.n == s0.n + 1 and s1.r != s0.r
            and stream_digest(s1) != stream_digest(s0))


def a_read_does_not_advance(seed, action="v0"):
    """READS LEAVE `(n, R_n)` UNCHANGED — the D24 §2 clause "advanced only by canonical actions" made
    structural: `stream_bytes`, `stream_digest` and `peek` return values and never a stream, and
    `Stream` is immutable, so none can advance it. Call each and require the state identical."""
    s = advance(root(seed), action)
    before = (s.n, s.r)
    _ = stream_bytes(s)
    _ = stream_digest(s)
    _ = peek(s, "probe", 100)
    _ = peek(s, "other", 6)
    return (s.n, s.r) == before


def identical_actions_give_the_identical_stream(seed, actions):
    """Determinism: the same `(seed, actions)` reproduces the whole trace, digest for digest."""
    t1 = [stream_digest(s) for s in trace(root(seed), actions)]
    t2 = [stream_digest(s) for s in trace(root(seed), actions)]
    return t1 == t2


def different_actions_diverge(seed):
    """The stream COMMITS to the action: a different action from the same state gives a different
    stream, so replay depends on WHICH actions, not only how many."""
    s0 = root(seed)
    return advance(s0, "v0").r != advance(s0, "v1").r


def composition_matches_every_prefix(seed, actions):
    """Incremental and batch advancement agree AT EVERY PREFIX, not only at the end: `apply(root,
    actions[:k])` equals `trace(root, actions)[k]` for every `k`. Regrouping the SAME sequence — never
    a claim that reordered actions commute."""
    tr = trace(root(seed), actions)
    for k in range(len(actions) + 1):
        if apply(root(seed), actions[:k]) != tr[k]:
            return False
    return True


def the_index_is_bound_into_identity(seed, actions=("v0", "v1")):
    """`(n, R_n)`, not merely `R_n`: the SAME digest value at a different `n` is a different canonical
    identity — so two runs holding the same value after different action counts cannot masquerade as
    the same state."""
    s = apply(root(seed), actions)
    same_r_other_n = Stream(s.n + 1, s.r)
    return stream_digest(same_r_other_n) != stream_digest(s)


def move_leaves_the_stream_a_fixed_point(seed, gseed=0, gdepth=1):
    """BOUNDARY INVARIANT for the current `move` contract: a reference assembly `(level, entity,
    stream)` stepped by `move` leaves the stream a FIXED POINT while the entity moves. `move` is not
    edited and does not import this module — structural decoupling — so a move action cannot advance
    the stream; this MEASURES that, it does not make it a universal law. Returns (stream_fixed,
    entity_moved, move_is_decoupled). `gamegen`/`move` are imported LAZILY."""
    import sys
    here = _os.path.dirname(_os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import gamegen as _G
    import move as _M
    lvl = _G.generate(gseed, gdepth)
    pos = _M.spawn(lvl)
    s = root(seed)                       # the RNG component of the reference D_n
    moved = False
    for c in sorted(_M.DIRECTIONS):
        outcome, nxt = _M.step(lvl, pos, c)   # move updates (level, entity); the stream is not passed
        if outcome == _M.MOVED and nxt != pos:
            moved = True
        pos = nxt
    decoupled = "rngstream" not in _M.ALLOWED_IMPORTS
    return (s == root(seed), moved, decoupled)


def seed_domain_matches_gamegen():
    """The stream roots at `gamegen`'s seed, so the domain is SINGLE-SOURCED, not a copied constant:
    `SEED_MAX`/`SEED_BITS` equal `gamegen`'s. Lazy import keeps the record's substrate stdlib."""
    import sys
    here = _os.path.dirname(_os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import gamegen as _G
    return SEED_MAX == _G.SEED_MAX and SEED_BITS == _G.SEED_BITS


def refuse_is_total():
    """(seeds, actions, bounds, streams): every malformed seed, action, bound and stream refuses typed,
    never a clamp or a silent default."""
    s_ref = 0
    for bad in (-1, SEED_MAX + 1, 1.0, "0", None, True):
        try:
            root(bad)
        except RngError as exc:
            s_ref += exc.code == "RNG-REFUSE"
    a_ref = 0
    s0 = root(0)
    for bad in (0, None, ("v",), 1.0):
        try:
            advance(s0, bad)
        except RngError as exc:
            a_ref += exc.code == "RNG-REFUSE"
    b_ref = 0
    for bad in (0, -1, 1.0, None):
        try:
            peek(s0, "x", bad)
        except RngError as exc:
            b_ref += exc.code == "RNG-REFUSE"
    st_ref = 0
    for bad in ((0, b"short"), (-1, b"\x00" * 32), (1.0, b"\x00" * 32)):
        try:
            Stream(*bad)
        except RngError as exc:
            st_ref += exc.code == "RNG-REFUSE"
    return s_ref == 6, a_ref == 4, b_ref == 4, st_ref == 3


# ---- scenes --------------------------------------------------------------------------------------------
#: The corpus of seeds — the SAME values `gamegen` roots at (0, 1, 12345, 0xDEADBEEF, SEED_MAX), so the
#: "one seed, two domains" claim is visible, plus 7. And ONE fixed synthetic action sequence, whose
#: tokens are clearly VERIFICATION tokens (`v0`..`v3`) and not a gameplay vocabulary.
SEEDS = (0, 1, 12345, 0xDEADBEEF, 7, SEED_MAX)
ACTIONS = ("v0", "v1", "v0", "v2", "v1", "v3")

SCENES = ("root", "trace", "laws")


def corpus_name(seed):
    return "rng-%d" % seed


def scene_case(name):
    if name == "root":
        # R_0 and I_0 for each corpus seed — the domain-separated root, pinned per seed
        return "|".join("%s=%s:%s" % (corpus_name(s), root(s).r.hex()[:12], stream_digest(root(s)))
                        for s in SEEDS)
    if name == "trace":
        # the full prefix trace (n, I_n) for a fixed seed and the synthetic action sequence — the
        # golden replay/prefix vector, and the representation lock for advance
        rows = []
        for s in trace(root(SEEDS[3]), ACTIONS):
            rows.append("n%d=%s" % (s.n, stream_digest(s)))
        return "seed=%d|acts=%s|" % (SEEDS[3], ",".join(ACTIONS)) + "|".join(rows)
    if name == "laws":
        return ("root_sep=%s|advance=%s|read_inv=%s|det=%s|diverge=%s|compose=%s|index=%s|"
                "move=%s|seeddom=%s|refuse=%s") % (
            tuple(the_root_is_domain_separated(s) for s in SEEDS),
            tuple(an_advance_changes_the_state(s) for s in SEEDS),
            tuple(a_read_does_not_advance(s) for s in SEEDS),
            tuple(identical_actions_give_the_identical_stream(s, ACTIONS) for s in SEEDS),
            different_actions_diverge(SEEDS[0]),
            tuple(composition_matches_every_prefix(s, ACTIONS) for s in SEEDS),
            the_index_is_bound_into_identity(SEEDS[0]),
            move_leaves_the_stream_a_fixed_point(SEEDS[0]),
            seed_domain_matches_gamegen(), refuse_is_total())
    raise RngError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def rngstream_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                            "conformance_rngstream.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise RngError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and rngstream_digest() == golden("rngstream"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except RngError as exc:
        return exc.code == "RNG-REFUSE"
    return False


def main():
    print("RNGSTREAM — the canonical RNG stream, the first stateful canonical component (URDRRNG1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("root domain: %r  (v1 FROZEN)" % DOMAIN)
    print()
    s = root(0xDEADBEEF)
    print("R_0 for seed 0xDEADBEEF:", s.r.hex()[:16], " I_0", stream_digest(s)[:16])
    cur = s
    for a in ACTIONS:
        cur = advance(cur, a)
        print("  advance %-3s -> n=%d  I_n=%s" % (a, cur.n, stream_digest(cur)[:16]))
    print()
    print("root domain-separated :", tuple(the_root_is_domain_separated(x) for x in SEEDS))
    print("advance changes state :", tuple(an_advance_changes_the_state(x) for x in SEEDS))
    print("read does not advance :", tuple(a_read_does_not_advance(x) for x in SEEDS))
    print("composition == prefix :", tuple(composition_matches_every_prefix(x, ACTIONS) for x in SEEDS))
    print("index bound in identity:", the_index_is_bound_into_identity(SEEDS[0]))
    print("move leaves stream fix :", move_leaves_the_stream_a_fixed_point(SEEDS[0]))
    print("seed domain == gamegen :", seed_domain_matches_gamegen())
    print("refuse total           :", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("rngstream", rngstream_digest())
    print()
    print("does_not_show: WHICH real actions advance the stream (verification action only; move")
    print("advances nothing; loot is the first real consumer); sub-stream domains for subsystem")
    print("draw-order decoupling (loot/combat's to earn); statistical quality beyond determinism;")
    print("and the full D_n snapshot, which is statecanon's to assemble.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
