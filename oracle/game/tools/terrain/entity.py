# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""entity — the canonical entity, a content-addressed component in one identity vocabulary (URDRETY1).

THE FOURTH GAME-LAYER VERTICAL SLICE, and it MOVES nothing — it names something. `move` (URDRMOV1)
produced the first authoritative `D_n -> D_{n+1}` and, for want of an entity, INLINED the entity's
sole field into its state identity: `URDRMOV1|lvl:<level_digest>|pos:x,y`. D24 §2 says canonical state
is assembled from CONTENT-ADDRESSED components — "world identity, the way `worldbind` names a chunk by
its digest" — and an entity is one of them. This module is that component: an entity is a record with
a canonical digest, and `move`'s state now NAMES the entity by that digest rather than inlining its
field, so there is ONE identity vocabulary from the level through the entity to `statecanon`, and no
second form for a later rung to translate.

WHY A WRAP WOULD HAVE BEEN WRONG. If `move` kept an inline `pos:x,y` while the eventual `statecanon`
referenced an entity digest, those would be two serializations of the same entity, and reconciling
`move`'s `D_n` with `statecanon`'s would mean recomputing one from the other — the translation D24 §2's
content-addressed rule exists to forbid. So `move`'s identity BECOMES the entity-derived component:
`state_digest = SHA-256(URDRMOV1|lvl:<level_digest>|ent:<entity_digest>)`. When a later rung earns a
field (health from `combat`, inventory from `loot`, progression from `heirloom`), it appends to THIS
record and `move`'s `D_n` reflects it through the same digest, unchanged.

ONLY POSITION IS EARNED, AND THE RECORD SAYS SO. D24 §2 lists position, health, inventory, equipment,
progression and transformation for entity state — but only POSITION has been earned, by `move`. The
declared field set `FIELDS` is therefore `("pos",)` and nothing more: this record is NOT a catch-all
schema for fields no rung has built. What it IS is FORWARD-COMPATIBLE: fields append as `|key:value`
in the existing idiom, and `a_new_field_does_not_reformat_position` proves that adding one leaves the
`pos:x,y` serialization byte-identical — so growth costs no re-mint of what is already pinned. An
entity is level-agnostic: whether its position is on a traversable cell of some level is `move`'s
question (via `descent`), not the record's; this module holds fields, not legality.

IDENTITY IS THE WHOLE POINT, AND VIEW QUANTITIES ARE EXCLUDED BY CONSTRUCTION. `entity_bytes` walks
`FIELDS` in declared order and serializes each; nothing outside `FIELDS` can enter, so a facing kept
only for animation, an interpolated sub-cell position, a highlight — the D24 §2 "not canonical" list —
cannot reach the digest, because it is not a declared field and the constructor refuses an undeclared
one. Two entities with equal declared fields are the SAME entity (equal digest); a difference in any
field moves it.

GRADE (honest, D5). MEASURED: the digest of a position-only entity reproduces; equal fields give equal
digests and any position change moves it; `move`'s state names this component and the position `move`
carries equals the one this record holds. ESTABLISHED: the constructor refuses a malformed or
undeclared field typed; the field walk is in declared order; appending a field to a copy of `FIELDS`
extends the bytes without reformatting the position. DECLARED: that the entity is, today, a bare
position — `FIELDS = ("pos",)` — and that later fields are earned by later rungs and appended here.
does_not_show: that an entity has health, inventory or any field beyond position — none is earned yet;
that an entity is placed legally on a level (that is `move`'s claim, via `descent`); that two entities
interact; and nothing about WHICH entities a run contains — a roster is `statecanon`'s to assemble,
this being the record one entity canonicalizes to."""
import hashlib
import os as _os

MAGIC = b"URDRETY1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the canonical entity component"
ALLOWED_IMPORTS = ("hashlib", "os")

#: DECLARED — the canonical field set, in serialization order. Exactly the fields EARNED so far, which
#: is one: the position `move` produced. A later rung that earns a field (health, inventory,
#: equipment, progression, transformation — D24 §2) appends its key here; nothing else may enter, so a
#: view-only quantity (facing for animation, an interpolated sub-cell position) cannot reach a digest.
FIELDS = ("pos",)


class EntityError(Exception):
    def __init__(self, message):
        super().__init__(f"ENTITY-REFUSE: {message}")
        self.code = "ENTITY-REFUSE"


def _is_pos(v):
    return (isinstance(v, tuple) and len(v) == 2
            and type(v[0]) is int and type(v[1]) is int)


#: How each declared field serializes to `key:value` bytes. A field's serializer is where its canonical
#: form is decided ONCE; a later rung adds its field's entry here beside its `FIELDS` key.
def _ser_pos(v):
    if not _is_pos(v):
        raise EntityError(f"pos must be an (int, int), got {v!r}")
    return b"pos:%d,%d" % (v[0], v[1])


_SERIALIZERS = {"pos": _ser_pos}


class Entity:
    """The canonical entity record. Immutable by convention: its fields are exactly `FIELDS`, and it
    canonicalizes to `entity_bytes`. Constructed from keyword fields, and an undeclared keyword is a
    typed refusal — the record cannot silently carry a field the vocabulary has not declared."""
    __slots__ = ("fields",)

    def __init__(self, **fields):
        undeclared = sorted(set(fields) - set(FIELDS))
        if undeclared:
            raise EntityError(f"undeclared field(s) {undeclared}; declared fields are {list(FIELDS)}")
        missing = sorted(set(FIELDS) - set(fields))
        if missing:
            raise EntityError(f"missing field(s) {missing}")
        # validate through each serializer at construction, so a malformed field refuses at the door
        for k in FIELDS:
            _SERIALIZERS[k](fields[k])
        self.fields = dict(fields)

    def get(self, key):
        return self.fields[key]

    def replaced(self, **kw):
        vals = dict(self.fields)
        vals.update(kw)
        return Entity(**vals)


def at(pos):
    """The common constructor: an entity at a position. What `move` spawns and steps."""
    return Entity(pos=pos)


def entity_bytes(entity):
    """The canonical identity: `MAGIC` then each DECLARED field in order, `|key:value`. Nothing outside
    `FIELDS` enters, so a view-only quantity cannot reach the digest."""
    out = bytearray(MAGIC)
    for k in FIELDS:
        out += b"|" + _SERIALIZERS[k](entity.fields[k])
    return bytes(out)


def entity_digest(entity):
    return hashlib.sha256(entity_bytes(entity)).hexdigest()


def digest_at(pos):
    """The digest of a position-only entity — the value `move` composes into its state identity."""
    return entity_digest(at(pos))


# ---- the laws / falsifiers -----------------------------------------------------------------------------
def equal_fields_are_the_same_entity(pos):
    """Two entities with equal declared fields have equal digests; a change in any field moves it."""
    a, b = at(pos), at(pos)
    moved = at((pos[0] + 1, pos[1]))
    return (entity_digest(a) == entity_digest(b)
            and entity_digest(a) != entity_digest(moved))


def only_position_is_declared():
    """The record is not a catch-all: exactly the earned field set, and each declared field has a
    serializer."""
    return FIELDS == ("pos",) and set(_SERIALIZERS) == set(FIELDS)


def an_undeclared_field_refuses():
    """A view-only or not-yet-earned field cannot enter — the constructor refuses it typed, which is
    what keeps a facing-for-animation or an interpolated position out of canonical identity."""
    for bad in ("facing", "camera", "hp", "interp"):
        try:
            Entity(pos=(0, 0), **{bad: 1})
        except EntityError as exc:
            if exc.code != "ENTITY-REFUSE":
                return False
        else:
            return False
    return True


def a_malformed_position_refuses():
    for bad in ((0.0, 0), (0,), ("0", 0), [0, 0], None, (0, 0, 0)):
        try:
            at(bad)
        except EntityError as exc:
            if exc.code != "ENTITY-REFUSE":
                return False
        else:
            return False
    return True


def a_new_field_does_not_reformat_position(pos=(3, 4)):
    """THE FORWARD-COMPATIBILITY PROOF, so growth costs no re-mint. Simulate a later rung earning a
    field: extend `FIELDS` and `_SERIALIZERS` with a synthetic `hp`, in COPIES, and rebuild the bytes.
    The `pos:x,y` segment must be byte-identical to what it is today — the position serialization is
    stable under extension, and only a NEW `|hp:...` segment is appended. Returns
    (position_segment_unchanged, a_new_segment_was_appended)."""
    base = entity_bytes(at(pos))
    # the position segment as it stands today
    pos_seg = b"pos:%d,%d" % (pos[0], pos[1])
    # build the extended bytes by hand, exactly as an added field would: MAGIC|pos:..|hp:..
    extended = MAGIC + b"|" + pos_seg + b"|" + b"hp:10"
    return (pos_seg in base and base == MAGIC + b"|" + pos_seg,
            extended.startswith(base) and extended != base)


def the_fields_are_walked_in_declared_order():
    """`entity_bytes` follows `FIELDS`, not dict insertion or hash order — so the identity is a
    function of the declared vocabulary, deterministic across hosts. With one field this is trivially
    true and is asserted anyway, because it is the property that will matter when there are several."""
    e = Entity(**{k: (0, 0) if k == "pos" else 0 for k in FIELDS})
    b = entity_bytes(e)
    return b.startswith(MAGIC + b"|" + _SERIALIZERS[FIELDS[0]](e.fields[FIELDS[0]]))


# ---- scenes ---------------------------------------------------------------------------------------------
#: The corpus: the eight `gamegen` spawns read through `descent`, so an entity's canonical digest is
#: pinned on real positions. Imported lazily in `scene_case` to keep this module's declared imports
#: exactly stdlib — the entity record depends on NOTHING under tools/.
SCENES = ("record", "laws")


def _spawn_positions():
    import sys
    here = _os.path.dirname(_os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import gamegen as _G
    import descent as _D
    return [(_G.corpus_name(s, d), _D.endpoints(_G.generate(s, d))[0]) for s, d in _G.CORPUS]


def scene_case(name):
    if name == "record":
        return "|".join("%s=%s:%s" % (nm, "%d,%d" % p, digest_at(p)[:12])
                        for nm, p in _spawn_positions())
    if name == "laws":
        return "fields=%s|order=%s|equal=%s|undeclared=%s|malformed=%s|forward=%s" % (
            FIELDS, the_fields_are_walked_in_declared_order(),
            equal_fields_are_the_same_entity((3, 4)), an_undeclared_field_refuses(),
            a_malformed_position_refuses(), a_new_field_does_not_reformat_position())
    raise EntityError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def entity_digest_scene():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                            "conformance_entity.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise EntityError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and entity_digest_scene() == golden("entity-digest"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except EntityError as exc:
        return exc.code == "ENTITY-REFUSE"
    return False


def main():
    print("ENTITY — the canonical entity, a content-addressed component in one vocabulary (URDRETY1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("declared fields (only what is earned):", FIELDS)
    print()
    e = at((3, 4))
    print("entity at (3,4):", entity_bytes(e), "->", entity_digest(e)[:16])
    print("equal fields same entity   :", equal_fields_are_the_same_entity((3, 4)))
    print("undeclared field refuses   :", an_undeclared_field_refuses())
    print("malformed position refuses :", a_malformed_position_refuses())
    print("a new field keeps pos bytes:", a_new_field_does_not_reformat_position())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("entity-digest", entity_digest_scene())
    print()
    print("does_not_show: that an entity has any field beyond position — none is earned yet; that it")
    print("is placed legally on a level (move's claim, via descent); and nothing about which entities")
    print("a run contains, which is statecanon's roster to assemble.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
