# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""statecanon — the assembled canonical identity D_n over the four earned component identities (URDRSTC1).

THE FOURTEENTH GAME-LAYER VERTICAL SLICE, and D24 §2's ASSEMBLED-STATE rung. Every rung before it earned an
identity for ONE component of a run: `gamegen.level_digest` names the world, `entity.entity_digest` names the
entity, `rngstream.stream_digest` names the RNG state, and `actionlog.digest` names the ordered action
history. This rung earns EXACTLY ONE new authority and no more — the single canonical identity `D_n` of the
whole assembled run — by COMPOSING those four already-earned identities. It reimplements none of them, mints
no second serialization of any component, and adds no new state.

THE LAW (one content-addressed digest over the four component identities):

    D_n = SHA-256( MAGIC | lvl:<level_digest> | ent:<entity_digest> | rng:<stream_digest> | log:<actionlog digest> )

Each component enters ONLY through its own authority's identity function, under a fixed label, delimited by
the reserved `|`. Every component identity is 64 hex characters and contains no `|`, so the labelled,
fixed-width, delimiter-framed preimage is injective in the four identities: two runs that differ in any one
component have different preimages, and swapping two component values (a level passing as an entity) yields a
different preimage. `D_n` is the one and only new SHA-256 this module mints — the composition itself.

THE ACTION HISTORY IS PART OF THE IDENTITY (the ratified design choice). `D_n` includes `actionlog.digest`,
so it identifies the run AND how it arrived, not merely the current world state: two runs at the SAME
`(level, entity, stream)` reached by DIFFERENT histories have DIFFERENT `D_n`. Excluding the log would make
`D_n` the pure current-state identity; D24 §2 lists the history among the canonical state, so it is included.
The seed and the depth are NOT separate components: `gamegen.level_digest` already commits to both (its canon
bytes open `URDRGEN1|s:<seed>|d:<depth>|...`), and the seed re-enters through the RNG root, so a raw `seed`
field would be redundant and is deliberately absent.

THE AUTHORITY / VIEW BOUNDARY holds by construction at the seam this rung composes. A view-only quantity — a
facing for animation, a camera, an interpolated position — cannot enter `entity` (the record refuses any
undeclared field, `entity.FIELDS == ("pos",)`), so it can never reach `entity_digest` and therefore never
reach `D_n`. `D_n` depends on the four component IDENTITIES and on nothing else; a quantity in none of them
has no slot in the preimage.

OWNERSHIP STAYS CRISP, and none of the three neighbouring laws absorbs another. `savegame` answers "can I
restore this artifact?" — it stores the earned components INDEPENDENTLY and mints no assembled identity (its
own `is_not_the_assembled_canonical_state`). `rerun` answers "does this recovered history reproduce the
independently stored state?" — a REPRODUCED/DIVERGED verdict, not an identity. `statecanon` answers "what is
the canonical identity of this assembled state-and-history?" — a single digest. It exposes no
serialize/restore/address (savegame's) and no replay/verdict/reconstruct_origin (rerun's), imports neither
module, and re-derives nothing they own.

IT ADDS NO AUTHORITY BEYOND THE COMPOSITION. It generates levels, positions entities, folds streams and
builds logs ONLY to exercise the composition over a corpus; the identity law calls each component's own digest
function and hashes the result once. It advances no RNG of its own, and — read off the AST — the assembly
reaches all four component-identity authorities, mints exactly one `sha256`, and reaches none of the
components' raw-serialization functions, so a mutant that reproduced the same `D_n` while bypassing one
authority (inlining a component's own `sha256(preimage)`, or hard-coding a digest) reddens on the structure
even though its output matched.

SINGLE-PEER, on purpose. This is the canonical identity of ONE run's assembled state. Cross-peer union
canonicalization is `lockstep.canon`'s `(tick, peer, seq)`, which game actions do not carry (Slice A), so this
module imports no `lockstep` and manufactures no such key.

GRADE (honest, D5). MEASURED: over a corpus of runs `D_n` equals SHA-256 of the labelled preimage built
independently from the four public component-identity functions; mutating ANY one of the four components
changes `D_n`; two runs at the same `(level, entity, stream)` with different histories have different `D_n`
(the history is in the identity); `D_n` depends only on the component identities, not on object instances.
ESTABLISHED: a view-only field cannot enter `entity` and so cannot reach `D_n`; the labelled fixed-width
`|`-delimited framing is injective (a swap of two component identities changes the preimage); the assembly
COMPOSES the four earned authorities and mints exactly one SHA and reaches no component's raw serialization
(read off the AST); it absorbs no neighbour (no savegame/rerun API, imports neither), and imports exactly its
declared substrate and no `lockstep`. DECLARED: the four components are the currently-earned canonical
identities (world, entity, RNG, history), the seed/depth ride inside `level_digest`, and single-peer.
does_not_show: multi-entity rosters or health/inventory (unearned components, no slot yet); cross-peer order
independence (Slice A); whether a run is reachable or winnable (that is `move`/`descent`'s, not identity's);
and anything about observers, which stay KINEMA's."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                     # noqa: E402  (world identity)
import entity as _E                                                      # noqa: E402  (entity identity)
import rngstream as _R                                                   # noqa: E402  (RNG identity)
import actionlog as _A                                                   # noqa: E402  (action-history identity)

MAGIC = b"URDRSTC1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the assembled canonical identity D_n over the four earned component identities"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "entity", "rngstream", "actionlog")

#: the four earned component identities, in canonical preimage order
COMPONENTS = ("lvl", "ent", "rng", "log")


class StatecanonError(Exception):
    def __init__(self, message):
        super().__init__(f"STATECANON-REFUSE: {message}")
        self.code = "STATECANON-REFUSE"


# ---- the assembly: D_n composes the four earned component identities ------------------------------------
def d_n_preimage(level, entity, stream, log):
    """The injective preimage `d_n` hashes: `MAGIC` then each component's identity under a fixed label,
    delimited by the reserved `|`. Every component enters ONLY through its OWN authority's identity function
    — `gamegen.level_digest`, `entity.entity_digest`, `rngstream.stream_digest`, `actionlog.digest` — so this
    reimplements none of them. Exposed so the framing's injectivity is itself falsifiable."""
    return b"%s|lvl:%s|ent:%s|rng:%s|log:%s" % (
        MAGIC,
        _G.level_digest(level).encode(),
        _E.entity_digest(entity).encode(),
        _R.stream_digest(stream).encode(),
        _A.digest(log).encode(),
    )


def d_n(level, entity, stream, log):
    """THE ONE NEW AUTHORITY: the assembled canonical identity `D_n` of a run. It COMPOSES the four
    already-earned component identities into the labelled preimage and mints EXACTLY ONE new SHA-256 — the
    composition. It re-serializes no component and re-implements no component's identity."""
    return hashlib.sha256(d_n_preimage(level, entity, stream, log)).hexdigest()


# ---- corpus construction (the four authorities exercised over a corpus) ---------------------------------
def _state(seed, depth, pos, log_tokens, stream_tokens):
    """A corpus run's four components, each from its own authority: a level from `(seed, depth)`, an entity at
    `pos`, a stream advanced from the run root by `stream_tokens`, and a log of `log_tokens`. Log and stream
    are INDEPENDENT (the log is not the stream's preimage — a move advances no stream), exactly as `savegame`
    stores them."""
    level = _G.generate(seed, depth)
    entity = _E.at(pos)
    stream = _R.apply(_R.root(seed), stream_tokens)
    log = _A.from_actions(log_tokens)
    return level, entity, stream, log


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def d_n_is_the_composition_of_the_four_identities(seed, depth, pos, log_tokens, stream_tokens):
    """MEASURED at the output: `D_n` EQUALS SHA-256 of the labelled preimage rebuilt INDEPENDENTLY here from
    the four public component-identity functions — so the emitted `D_n` is exactly the composition of the four
    earned identities, not some other value that only happens to reproduce for this corpus."""
    level, entity, stream, log = _state(seed, depth, pos, log_tokens, stream_tokens)
    independent = hashlib.sha256(b"%s|lvl:%s|ent:%s|rng:%s|log:%s" % (
        MAGIC,
        _G.level_digest(level).encode(),
        _E.entity_digest(entity).encode(),
        _R.stream_digest(stream).encode(),
        _A.digest(log).encode())).hexdigest()
    return d_n(level, entity, stream, log) == independent


def each_component_moves_d_n(seed, depth, pos, log_tokens, stream_tokens):
    """MEASURED: mutating ANY of the four components changes `D_n` — every authority is load-bearing, none is
    vestigial. Level (a deeper depth), entity (a shifted position), stream (one more advance), log (one
    appended action) each move the identity."""
    level, entity, stream, log = _state(seed, depth, pos, log_tokens, stream_tokens)
    base = d_n(level, entity, stream, log)
    return (base != d_n(_G.generate(seed, depth + 1), entity, stream, log)          # level
            and base != d_n(level, _E.at((pos[0] + 1, pos[1])), stream, log)        # entity
            and base != d_n(level, entity, _R.advance(stream, b"x"), log)           # stream
            and base != d_n(level, entity, stream, _A.append(log, "Z")))            # log


def history_is_in_the_identity(seed, depth, pos):
    """THE RATIFIED CHOICE: `D_n` includes the action history. Two runs at the SAME `(level, entity, stream)`
    reached by DIFFERENT histories have DIFFERENT `D_n` — the identity is of the run AND how it arrived, not
    merely the current world state. (The differing tokens advance no stream, so `(level, entity, stream)` is
    held fixed while only the log differs.)"""
    level = _G.generate(seed, depth)
    entity = _E.at(pos)
    stream = _R.root(seed)
    log_a = _A.from_actions(("N", "S"))
    log_b = _A.from_actions(("E", "W"))
    return d_n(level, entity, stream, log_a) != d_n(level, entity, stream, log_b)


def d_n_depends_only_on_identity(seed, depth, pos, log_tokens, stream_tokens):
    """`D_n` depends on the component IDENTITIES, not on object instances: two independently constructed but
    identical component sets give the same `D_n`, though the objects are distinct."""
    s1 = _state(seed, depth, pos, log_tokens, stream_tokens)
    s2 = _state(seed, depth, pos, log_tokens, stream_tokens)
    return d_n(*s1) == d_n(*s2) and s1[0] is not s2[0]


def a_view_field_cannot_reach_d_n():
    """The authority / view boundary at the entity seam: a view-only quantity (facing, camera, interp) cannot
    enter `entity` — the record refuses any undeclared field — so it can never reach `entity_digest` and
    therefore never reach `D_n`."""
    for bad in ("facing", "camera", "interp"):
        try:
            _E.Entity(pos=(0, 0), **{bad: 1})
        except _E.EntityError:
            continue
        return False
    return True


def the_framing_is_injective(seed, depth, pos):
    """The labelled, fixed-width, `|`-delimited framing is injective in the four identities: each identity is
    64 hex characters and contains no `|`, and swapping two component identities (an entity passing for a
    level) yields a DIFFERENT preimage — so no aliasing collapses two distinct runs before the hash."""
    level, entity, stream, log = _state(seed, depth, pos, ("N", "loot:a"), ("loot:a",))
    pre = d_n_preimage(level, entity, stream, log)
    digs = (_G.level_digest(level), _E.entity_digest(entity),
            _R.stream_digest(stream), _A.digest(log))
    widths_ok = all(len(x) == 64 and "|" not in x for x in digs)
    swapped = b"%s|lvl:%s|ent:%s|rng:%s|log:%s" % (
        MAGIC, digs[1].encode(), digs[0].encode(), digs[2].encode(), digs[3].encode())
    return widths_ok and swapped != pre


def the_assembly_composes_the_four_authorities():
    """STRUCTURAL, read off this module's own AST — the requirement that the gate establish the implementation
    COMPOSES the four earned identities, not merely emits the expected digest. The assembly (`d_n_preimage`
    and `d_n`) must:
      * reach ALL FOUR component-identity authorities (`level_digest`, `entity_digest`, `stream_digest`, and
        actionlog's `digest`) — so a mutant that drops or bypasses one reddens;
      * mint EXACTLY ONE new `sha256` (the composition) — so a mutant that inlines a component's own
        `sha256(preimage)` to reproduce its digest (same `D_n`, bypassed authority) reddens on the second;
      * reach NONE of the components' raw-serialization functions (`canon_bytes`, `entity_bytes`,
        `stream_bytes`, `stream_of`) and advance no RNG — so re-implementing a component's identity reddens;
    and the module's declared substrate is exactly `ALLOWED_IMPORTS`, importing neither `savegame`/`rerun`
    (whose jobs it must not absorb) nor `lockstep` (Slice A)."""
    import ast
    with open(_os.path.join(_HERE, "statecanon.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    assembly = [n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name in ("d_n", "d_n_preimage")]
    if len(assembly) != 2:
        return False
    attrs = [a.attr for fn in assembly for a in ast.walk(fn) if isinstance(a, ast.Attribute)]
    identities = {"level_digest", "entity_digest", "stream_digest", "digest"}
    reaches_all = identities <= set(attrs)
    one_sha = attrs.count("sha256") == 1
    no_reimpl = not ({"canon_bytes", "entity_bytes", "stream_bytes", "stream_of"} & set(attrs))
    no_advance = "advance" not in attrs
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    imports_clean = (top == set(ALLOWED_IMPORTS)
                     and not ({"savegame", "rerun", "lockstep"} & top))
    return reaches_all and one_sha and no_reimpl and no_advance and imports_clean


def statecanon_absorbs_no_neighbor():
    """Ownership stays crisp: `statecanon` answers only "what is the canonical identity?", not "can I restore
    it?" (savegame's) or "does this history reproduce it?" (rerun's). It exposes NO savegame API
    (serialize/restore/address) and NO replay API (replay/verdict/reconstruct_origin) — none absorbs
    another."""
    mod = __import__("statecanon")
    foreign = ("serialize", "restore", "address",              # savegame's
               "replay", "verdict", "reconstruct_origin")      # rerun's
    return not any(hasattr(mod, nm) for nm in foreign)


# ---- scenes ---------------------------------------------------------------------------------------------
#: The corpus: `gamegen` seeds/depths, arbitrary positions, and INDEPENDENT log/stream token sequences (the
#: log is not the stream's preimage), each pinned by its assembled canonical identity `D_n`.
CORPUS = (
    (0, 1, (3, 4), ("N", "S"), ("loot:x",)),
    (1, 2, (0, 0), ("loot:x", "N"), ()),
    (12345, 3, (7, 2), ("loot:a", "S", "loot:b"), ("loot:a", "loot:b")),
    (0xC0FFEE, 2, (5, 6), ("E", "loot:a", "W"), ("loot:a",)),
)
SCENES = ("assembly", "laws")


def _assembly_row(seed, depth, pos, log_tokens, stream_tokens):
    level, entity, stream, log = _state(seed, depth, pos, log_tokens, stream_tokens)
    return "%d,%d,%d,%d,l%d,r%d=%s" % (
        seed, depth, pos[0], pos[1], len(log_tokens), stream.n,
        d_n(level, entity, stream, log)[:16])


def scene_case(name):
    if name == "assembly":
        return "|".join(_assembly_row(*c) for c in CORPUS)
    if name == "laws":
        base = [(s, d, p) for s, d, p, _l, _st in CORPUS]
        return ("compose=%s|moves=%s|history=%s|identity=%s|view=%s|framing=%s|structure=%s|noabsorb=%s") % (
            tuple(d_n_is_the_composition_of_the_four_identities(*c) for c in CORPUS),
            tuple(each_component_moves_d_n(*c) for c in CORPUS),
            tuple(history_is_in_the_identity(s, d, p) for s, d, p in base),
            tuple(d_n_depends_only_on_identity(*c) for c in CORPUS),
            a_view_field_cannot_reach_d_n(),
            tuple(the_framing_is_injective(s, d, p) for s, d, p in base),
            the_assembly_composes_the_four_authorities(),
            statecanon_absorbs_no_neighbor())
    raise StatecanonError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def statecanon_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_statecanon.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise StatecanonError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and statecanon_digest() == golden("statecanon"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except StatecanonError as exc:
        return exc.code == "STATECANON-REFUSE"
    return False


def main():
    print("STATECANON — the assembled canonical identity D_n over the four earned component identities (URDRSTC1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print()
    level, entity, stream, log = _state(0xC0FFEE, 2, (5, 6), ("E", "loot:a", "W"), ("loot:a",))
    print("components:")
    print("  lvl", _G.level_digest(level))
    print("  ent", _E.entity_digest(entity))
    print("  rng", _R.stream_digest(stream))
    print("  log", _A.digest(log))
    print("D_n:", d_n(level, entity, stream, log))
    print()
    print("D_n is the composition of the four :", d_n_is_the_composition_of_the_four_identities(*CORPUS[3]))
    print("each component moves D_n           :", each_component_moves_d_n(*CORPUS[3]))
    print("the history is in the identity     :", history_is_in_the_identity(0, 1, (3, 4)))
    print("D_n depends only on identity       :", d_n_depends_only_on_identity(*CORPUS[3]))
    print("a view field cannot reach D_n      :", a_view_field_cannot_reach_d_n())
    print("the framing is injective           :", the_framing_is_injective(0, 1, (3, 4)))
    print("the assembly composes the four     :", the_assembly_composes_the_four_authorities())
    print("statecanon absorbs no neighbour    :", statecanon_absorbs_no_neighbor())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("statecanon", statecanon_digest())
    print()
    print("does_not_show: multi-entity rosters or health/inventory (unearned, no slot); cross-peer order")
    print("independence (Slice A); whether a run is reachable or winnable; and observers, which stay KINEMA's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
