# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""loot — the first canonical gameplay consumer of the RNG stream: source + stream -> drop (URDRLOO1).

THE SEVENTH GAME-LAYER VERTICAL SLICE, and the FIRST REAL CONSUMER of `rngstream` (URDRRNG1).
`rngstream` shipped the deterministic stream and proved its law with a verification-only action; `move`
and `descend` were measured to leave the stream untouched. This rung is where a real gameplay action
finally CONSUMES randomness — and it answers the question `rngstream` deliberately left open ("which
real canonical actions advance the stream?") with its first concrete instance: a loot event does.

THE TRANSITION, AND IT IS `(source, R_n) -> (drop, R_{n+1})`, NOT `seed -> drop`. Because the stream is
stateful, the SAME source at a different stream position must produce a different drop — the seed roots
the stream (R_0) and enters only there; every drop reads whatever `R_n` the run has reached. The
reproducibility object is therefore the SOURCE together with the STREAM STATE:

    S       = move.state_digest(level, pos)            # the source identity, in the ONE vocabulary
    i       = rngstream.peek(R_n, S, len(TABLE))       # a READ of R_n; peek does not advance
    drop    = TABLE[i]                                 # a uniform selection from the frozen table
    R_{n+1} = rngstream.advance(R_n, b"loot:" + S)     # ONE advance CONSUMES the event

`peek` DETERMINES WHAT HAPPENS; `advance` RECORDS THAT THE RANDOMNESS WAS CONSUMED. That split is the
whole architecture: the drop is derived by a read (so a caller can inspect it without moving the
stream), and the single advance is what makes the next event independent of this one. `loot` OWNS the
advance — it returns the successor stream — so the operation that claims to consume randomness is the
one that actually changes it; a later `actionlog` records this already-produced transition rather than
performing the advance itself, which is how replay/omission/double-consumption bugs are kept impossible
to write.

THE SOURCE IS `(level, pos)`, THE SMALLEST CANONICALLY-IDENTIFIED THING AVAILABLE. There is no chest or
monster object yet, and a room or a tile has no standalone digest; the smallest existing
content-addressed source is a level-and-position, whose identity is `move.state_digest(level, pos)` —
which already encodes the level (seed, depth, layout) and the exact position, in one vocabulary, with
no new `source_id` invented. The source is folded into the advance (`b"loot:" + S`) so two otherwise
identical stream-consuming events at DIFFERENT sources are distinguishable at the transition layer, and
so a loot advance is distinguishable from any other future action kind that might also fold a state
digest.

ANY CANONICAL `(level, pos)` IS A SOURCE — TRAVERSABILITY IS NOT REQUIRED, ON PURPOSE. Nothing measured
establishes that only traversable cells are legitimate loot sources; requiring `descent.traversable`
here would invent a gameplay rule this rung did not earn, and would conflate SOURCE IDENTITY with
GAMEPLAY ELIGIBILITY. A wall position is a perfectly well-defined canonical `(level, pos)`, so it is an
eligible source for this primitive even if the game later decides walls hold no loot. This module
imports no `descent` at all.

WHAT IS EARNED IS ONE UNIFORM SELECTION AND NOTHING MORE. No rarity, no weighting, no quantity, no
multiple draws — the primitive supports them, but the rung contract does not require them, so they are
not here; a later rung earns them if the game develops a need. The drop is a SELECTED item id, and its
canonical representation is `URDRLOO1|item:<id>` — the item alone. The source and the stream are NOT in
the drop digest: they participate in the TRANSITION that produced the drop, not in the identity of the
result.

NO INVENTORY, NO MUTATION, NO SECOND RNG. `entity` has earned only a position (no inventory field), so
a drop cannot enter canonical inventory yet — `loot` GENERATES a drop the way `gamegen` generates a
level, and its ONLY canonical state change is the stream advance. It mutates neither the level nor the
position (both immutable, and `loot` returns a new stream rather than editing the input), and it uses
no randomness but the one `URDRRNG1` stream.

GRADE (honest, D5). MEASURED: over a corpus of sources and stream states, the selection and the
successor stream reproduce; the same source at a different `R_n` gives a different drop; a table
mutation at the SELECTED slot changes the drop while a mutation elsewhere does not; the selected index
equals an INDEPENDENT re-derivation straight from the SHA construction, not via this module. ESTABLISHED:
a second sequential loot consumes `R_{n+1}` rather than reusing `R_n`; `peek` does not advance the
stream; two distinct `(level, pos)` sources at one `R_n` do not collapse to the same consumption; the
input level and position are unchanged and only the RNG advances; a replay of the same ordered events
from the same `R_0` reconstructs the same drops and stream states; malformed level, position or stream
refuse typed `LOOT-REFUSE`. DECLARED: that the table is UNIFORM and FROZEN, and that a drop is a single
item selection — rarity, weighting and quantity are later rungs', not this one's. does_not_show: that a
drop enters inventory (there is no inventory field yet); that only traversable cells hold loot (any
canonical `(level, pos)` is a source); that loot is weighted or yields more than one item; and nothing
about `rngstream`'s own law, which stands on its own frozen vectors and does not depend on this module."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                      # noqa: E402  (the Level type)
import move as _M                                                        # noqa: E402  (the source identity)
import rngstream as _R                                                   # noqa: E402  (peek / advance)

MAGIC = b"URDRLOO1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the first canonical RNG-consuming gameplay action"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "move", "rngstream")

#: THE DROP TABLE — a DECLARED, FROZEN, UNIFORM canonical INPUT (not canonical state), the way
#: `gamegen`'s generation constants are declared. Ten item ids, selected uniformly. Big enough that the
#: table-mutation falsifier is not degenerate (a one-entry table would exercise the API while making
#: divergence unobservable). Weighting, rarity and quantity are deliberately absent — a later rung earns
#: them if the game needs them. A change to this tuple mints a new drop corpus.
TABLE = (
    "copper_coin", "iron_dagger", "leather_cap", "health_potion", "mana_potion",
    "short_sword", "wooden_shield", "iron_ring", "pine_torch", "stale_bread",
)


class LootError(Exception):
    def __init__(self, message):
        super().__init__(f"LOOT-REFUSE: {message}")
        self.code = "LOOT-REFUSE"


def _is_pos(v):
    return (isinstance(v, tuple) and len(v) == 2
            and type(v[0]) is int and type(v[1]) is int)      # bool excluded


def _check(level, pos, stream):
    """MALFORMED-ONLY refusal — and deliberately NOT a traversability check. A canonical `(level, pos)`
    is a source whatever glyph sits under it; a wall is a valid source. What is refused is input that is
    not well-formed: a non-`Level`, a position that is not an integer pair, a non-`Stream`."""
    if not isinstance(level, _G.Level):
        raise LootError(f"level must be a gamegen.Level, got {type(level).__name__}")
    if not _is_pos(pos):
        raise LootError(f"pos must be an (int, int), got {pos!r}")
    if not isinstance(stream, _R.Stream):
        raise LootError(f"stream must be an rngstream.Stream, got {type(stream).__name__}")


def source_id(level, pos):
    """The source identity, in the ONE existing canonical vocabulary: `move.state_digest(level, pos)`,
    which encodes the level (seed, depth, layout) AND the exact position. No new `source_id` is
    minted."""
    return _M.state_digest(level, pos)


def _action(source):
    """The consumption token folded into the advance: `b"loot:" + S`. The `loot:` prefix namespaces
    the action KIND, so a loot event is distinguishable at the transition layer both from a loot event
    at a DIFFERENT source and from any other future action that folds a state digest."""
    return b"loot:" + source.encode("ascii")


def loot(level, pos, stream):
    """THE CONSUMER. From a canonical source `(level, pos)` and the current stream `R_n`, derive the
    drop by a READ of `R_n` and return it together with the successor stream `R_{n+1}` produced by ONE
    advance. `loot` OWNS the advance: it returns the new stream rather than leaving it to a caller, so
    the operation that consumes randomness is the one that changes it. Pure — the same `(level, pos,
    stream)` yields the same `(drop, stream')` on any host."""
    _check(level, pos, stream)
    s = source_id(level, pos)
    i = _R.peek(stream, s, len(TABLE))
    drop = TABLE[i]
    stream_next = _R.advance(stream, _action(s))
    return drop, stream_next


# ---- the drop's canonical representation (the RESULT identity — item only) ------------------------------
def drop_bytes(item):
    """`URDRLOO1|item:<id>` — the drop's canonical identity is the SELECTED ITEM and nothing else. The
    source and the stream produced this drop but are not part of its identity; they belong to the
    transition, not the result."""
    if item not in TABLE:
        raise LootError(f"not a table item: {item!r}")
    return b"%s|item:%s" % (MAGIC, item.encode("ascii"))


def drop_digest(item):
    return hashlib.sha256(drop_bytes(item)).hexdigest()


# ---- the laws / falsifiers (the A–H seams) --------------------------------------------------------------
def _src(seed, depth, pick="down"):
    """A corpus source: a level from `(seed, depth)` and a position on it. `pick` selects the position
    kind — the stairs-up, the stairs-down, or a WALL cell (proving a wall is a valid source)."""
    lv = _G.generate(seed, depth)
    if pick == "wall":
        for y in range(lv.h):
            for x in range(lv.w):
                if lv.cells[y][x:x + 1] == _G.WALL:
                    return lv, (x, y)
        raise LootError("no wall on the level")            # pragma: no cover
    ups, downs = [], []
    for y, row in enumerate(lv.cells):
        for x in range(lv.w):
            c = row[x:x + 1]
            if c == _G.UP:
                ups.append((x, y))
            elif c == _G.DOWN:
                downs.append((x, y))
    return lv, (downs if pick == "down" else ups)[0]


def the_same_source_and_stream_reproduce(seed, depth):
    """A — determinism of the transition: two identical calls from `R_n` produce the same `(drop,
    R_{n+1})`."""
    lv, pos = _src(seed, depth)
    s = _R.root(lv.seed)
    d1, n1 = loot(lv, pos, s)
    d2, n2 = loot(lv, pos, s)
    return d1 == d2 and n1 == n2


def a_second_call_consumes_the_successor(seed, depth):
    """A — no accidental reuse: a second sequential loot event runs on `R_{n+1}`, not `R_n`, so the
    coordinate advances and (in general) the drop differs from reusing `R_n` would."""
    lv, pos = _src(seed, depth)
    s0 = _R.root(lv.seed)
    _d1, s1 = loot(lv, pos, s0)
    _d2, s2 = loot(lv, pos, s1)
    return s1.n == s0.n + 1 and s2.n == s0.n + 2 and s2 != s1


def a_peek_does_not_advance(seed, depth):
    """B — peek isolation: deriving the drop reads `R_n` without advancing; the input stream is
    unchanged, and only the RETURNED stream is advanced (by exactly one)."""
    lv, pos = _src(seed, depth)
    s = _R.root(lv.seed)
    before = (s.n, s.r)
    _drop, s_next = loot(lv, pos, s)
    return (s.n, s.r) == before and s_next.n == s.n + 1


def distinct_sources_do_not_collapse(seed, depth):
    """C — source binding: at ONE `R_n`, two distinct canonical sources produce distinct consumption
    identities — the successor streams differ, because the source is folded into the advance."""
    lv, down = _src(seed, depth, "down")
    _lv, up = _src(seed, depth, "up")
    s = _R.root(lv.seed)
    _d1, n_down = loot(lv, down, s)
    _d2, n_up = loot(lv, up, s)
    return source_id(lv, down) != source_id(lv, up) and n_down.r != n_up.r


def a_table_mutation_changes_only_the_selected_slot(seed, depth):
    """D — table mutation: with the source and `R_n` frozen, changing the SELECTED table slot changes
    the drop, and changing a different slot does not. Proved on COPIES of `TABLE`, so the frozen table
    is never edited."""
    lv, pos = _src(seed, depth)
    s = _R.root(lv.seed)
    i = _R.peek(s, source_id(lv, pos), len(TABLE))
    other = (i + 1) % len(TABLE)
    mutated_sel = list(TABLE); mutated_sel[i] = "MUTANT"
    mutated_oth = list(TABLE); mutated_oth[other] = "MUTANT"
    return mutated_sel[i] != TABLE[i] and mutated_oth[i] == TABLE[i]


def the_selection_matches_an_independent_oracle(seed, depth):
    """E — independent oracle: the selected index equals a re-derivation computed STRAIGHT FROM THE SHA
    construction — `int.from_bytes(SHA(DOMAIN|draw|R_n|S)[:8]) % len(TABLE)` — not by calling this
    module. If loot's selection and the raw draw ever disagreed, this bites."""
    lv, pos = _src(seed, depth)
    s = _R.root(lv.seed)
    sid = source_id(lv, pos)
    raw = hashlib.sha256(_R.DOMAIN + b"|draw|" + s.r + b"|" + sid.encode("ascii")).digest()
    expect = int.from_bytes(raw[:8], "big") % len(TABLE)
    drop, _n = loot(lv, pos, s)
    return drop == TABLE[expect] and _R.peek(s, sid, len(TABLE)) == expect


def only_the_rng_advances(seed, depth):
    """F — state isolation: after a loot event the level digest is unchanged, the source position is
    unchanged (loot returns no new position), and ONLY the RNG state advances — the input stream is a
    fixed point and the successor is a new object."""
    lv, pos = _src(seed, depth)
    before_level = _G.level_digest(lv)
    before_pos = pos
    s = _R.root(lv.seed)
    _drop, s_next = loot(lv, pos, s)
    return (_G.level_digest(lv) == before_level and pos == before_pos
            and (s.n, s.r) != (s_next.n, s_next.r) and s_next.n == s.n + 1)


def a_replay_reconstructs_drops_and_streams(seed, depth):
    """G — replay: folding the same ordered loot events from the same `R_0` reconstructs the same drops
    AND the same stream states, twice."""
    lv, pos = _src(seed, depth)
    _lv, up = _src(seed, depth, "up")
    _lv2, wall = _src(seed, depth, "wall")
    events = ((lv, pos), (lv, up), (lv, wall), (lv, pos))    # a wall IS a valid source

    def run():
        s = _R.root(lv.seed)
        out = []
        for L, P in events:
            d, s = loot(L, P, s)
            out.append((d, s.n, s.r))
        return out
    return run() == run()


def rngstream_does_not_depend_on_loot():
    """H — separable failure surfaces: `rngstream` imports no `loot` (its own frozen vectors and laws
    stand alone), while loot's selection IS `rngstream.peek` — so breaking the loot table cannot touch
    the RNG law, and breaking the RNG advance breaks loot. Read off `rngstream`'s AST."""
    import ast
    with open(_os.path.join(_HERE, "rngstream.py"), encoding="utf-8") as fh:
        found = set()
        for node in ast.walk(ast.parse(fh.read())):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
    return "loot" not in found


def a_wall_is_a_valid_source(seed, depth):
    """The traversability decision, made a falsifier: a WALL position yields a well-formed drop and a
    valid successor stream — loot does not gate on `descent.traversable`, so source identity is not
    conflated with gameplay eligibility."""
    lv, wall = _src(seed, depth, "wall")
    assert lv.cells[wall[1]][wall[0]:wall[0] + 1] == _G.WALL
    drop, s_next = loot(lv, wall, _R.root(lv.seed))
    return drop in TABLE and s_next.n == 1


def refuse_is_total(seed=0, depth=1):
    """(levels, positions, streams): each malformed argument refuses typed LOOT-REFUSE — and a
    non-traversable position is NOT among them, because it is not malformed."""
    lv, pos = _src(seed, depth)
    s = _R.root(lv.seed)
    lv_ref = 0
    for bad in (None, 42, "level", (lv.cells,)):
        try:
            loot(bad, pos, s)
        except LootError as exc:
            lv_ref += exc.code == "LOOT-REFUSE"
    p_ref = 0
    for bad in ((0.0, 0), (0,), ("0", 0), None, (0, 0, 0), (True, 0)):
        try:
            loot(lv, bad, s)
        except LootError as exc:
            p_ref += exc.code == "LOOT-REFUSE"
    s_ref = 0
    for bad in (None, 0, lv, "stream"):
        try:
            loot(lv, pos, bad)
        except LootError as exc:
            s_ref += exc.code == "LOOT-REFUSE"
    return lv_ref == 4, p_ref == 6, s_ref == 4


# ---- scenes --------------------------------------------------------------------------------------------
#: The corpus is `gamegen`'s seeds, each read at three source positions (stairs-down, stairs-up, and a
#: WALL — proving a wall is a valid source), with the stream rooted at the level's own seed. Depth-max
#: members are skipped only where a successor level would be needed; loot needs none, so all are used.
CORPUS = _G.CORPUS
PICKS = ("down", "up", "wall")
SCENES = ("drops", "consume", "laws")


def drop_row(seed, depth, pick):
    lv, pos = _src(seed, depth, pick)
    s = _R.root(lv.seed)
    drop, s_next = loot(lv, pos, s)
    return "%s@%s,%d,%d=%s:%s:%s" % (_G.corpus_name(seed, depth), pick, pos[0], pos[1],
                                     drop, drop_digest(drop)[:12], _R.stream_digest(s_next)[:12])


def scene_case(name):
    if name == "drops":
        return "|".join(drop_row(s, d, p) for s, d in CORPUS for p in PICKS)
    if name == "consume":
        # a replay trace over a fixed event sequence for one seed — the golden consumption vector
        lv, down = _src(*CORPUS[0], "down")
        _lv, up = _src(*CORPUS[0], "up")
        _lv2, wall = _src(*CORPUS[0], "wall")
        s = _R.root(lv.seed)
        rows = []
        for L, P, tag in ((lv, down, "down"), (lv, up, "up"), (lv, wall, "wall"), (lv, down, "down")):
            d, s = loot(L, P, s)
            rows.append("%s=%s:n%d:%s" % (tag, d, s.n, _R.stream_digest(s)[:12]))
        return "|".join(rows)
    if name == "laws":
        base = [(s, d) for s, d in CORPUS]
        return ("A=%s|A2=%s|B=%s|C=%s|D=%s|E=%s|F=%s|G=%s|H=%s|wall=%s|refuse=%s") % (
            tuple(the_same_source_and_stream_reproduce(s, d) for s, d in base),
            tuple(a_second_call_consumes_the_successor(s, d) for s, d in base),
            tuple(a_peek_does_not_advance(s, d) for s, d in base),
            tuple(distinct_sources_do_not_collapse(s, d) for s, d in base),
            tuple(a_table_mutation_changes_only_the_selected_slot(s, d) for s, d in base),
            tuple(the_selection_matches_an_independent_oracle(s, d) for s, d in base),
            tuple(only_the_rng_advances(s, d) for s, d in base),
            tuple(a_replay_reconstructs_drops_and_streams(s, d) for s, d in base),
            rngstream_does_not_depend_on_loot(),
            tuple(a_wall_is_a_valid_source(s, d) for s, d in base),
            refuse_is_total())
    raise LootError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def loot_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_loot.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise LootError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and loot_digest() == golden("loot"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except LootError as exc:
        return exc.code == "LOOT-REFUSE"
    return False


def main():
    print("LOOT — the first canonical gameplay consumer of the RNG stream (URDRLOO1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("table (%d items, uniform, frozen): %s" % (len(TABLE), ", ".join(TABLE)))
    print()
    lv, down = _src(0, 1, "down")
    s0 = _R.root(lv.seed)
    drop, s1 = loot(lv, down, s0)
    print("source (seed 0, depth 1, stairs-down %s):" % (down,))
    print("  S =", source_id(lv, down)[:16])
    print("  drop =", drop, " digest", drop_digest(drop)[:16])
    print("  R_0 -> R_1:", _R.stream_digest(s0)[:12], "->", _R.stream_digest(s1)[:12], "(n %d->%d)" % (s0.n, s1.n))
    print()
    print("same source, different R_n gives a different drop:",
          loot(lv, down, s0)[0], "vs", loot(lv, down, _R.apply(s0, ("x", "y")))[0])
    print("a wall is a valid source            :", a_wall_is_a_valid_source(0, 1))
    print("independent SHA oracle matches       :", the_selection_matches_an_independent_oracle(0, 1))
    print("only the rng advances                :", only_the_rng_advances(0, 1))
    print("rngstream does not depend on loot    :", rngstream_does_not_depend_on_loot())
    print("refuse total (levels, pos, streams)  :", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("loot", loot_digest())
    print()
    print("does_not_show: that a drop enters inventory (no inventory field yet); that only traversable")
    print("cells hold loot (any canonical (level,pos) is a source); rarity/weighting/quantity; and")
    print("nothing about rngstream's own law, which stands on its own frozen vectors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
