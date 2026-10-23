"""G1 canonical bytes: oracle encode == independently hand-calculated bytes, and decode round-trips. Both candidates."""
from oracle import decoder as d
from oracle import canonicality as C
from fixtures.hand_calculated import vectors as V
from .harness import Cases


def run():
    c = Cases()

    # VALUE vectors (hand-literal == oracle encode; and decode round-trip)
    for v, expected in V.value_vectors():
        c.ok("G1 value encode %r" % (v,),
             lambda v=v, expected=expected: _eq(d.encode_value(v), expected))
        c.ok("G1 value round-trip %r" % (v,),
             lambda v=v, expected=expected: _eq(d.decode_value(d.Reader(expected)), v))

    # KEY vectors
    for (kind, s), expected in V.key_vectors():
        c.ok("G1 key encode %s:%s" % (kind, s),
             lambda kind=kind, s=s, expected=expected: _eq(d.encode_key(kind, s), expected))

    for cand in ("A", "B"):
        # EMPTY node
        c.ok("G1 EMPTY node cand %s" % cand,
             lambda cand=cand: _eq(d.enc_empty(cand), V.empty_node(cand)))
        # LEAF_COMP node (hp=10)
        c.ok("G1 LEAF_COMP hp=10 cand %s" % cand,
             lambda cand=cand: _eq(d.enc_leaf_comp(cand, "hp", 10), V.leaf_comp(cand, "hp", 10)))
        # whole-state serializations: genesis, singleton-empty-entity, singleton-one-component
        for name, maker in (("genesis", V.genesis_serialization),
                            ("singleton-empty-entity", V.singleton_empty_entity_serialization),
                            ("singleton-one-component", V.singleton_one_component_serialization)):
            c.ok("G1 serialize %s cand %s" % (name, cand),
                 lambda maker=maker, cand=cand: _serialize_eq(maker, cand))
            c.ok("G1 reconstruct %s cand %s" % (name, cand),
                 lambda maker=maker, cand=cand: _reconstruct_eq(maker, cand))
    return c.done()


def _eq(a, b):
    if a != b:
        raise AssertionError("bytes differ:\n oracle=%r\n hand  =%r" % (a, b))


def _serialize_eq(maker, cand):
    state, expected = maker(cand)
    got = C.serialize_state(state, cand)
    _eq(got, expected)


def _reconstruct_eq(maker, cand):
    state, expected = maker(cand)
    back = C.reconstruct(expected, cand)
    if back != state:
        raise AssertionError("reconstruct != state: %r vs %r" % (back, state))
