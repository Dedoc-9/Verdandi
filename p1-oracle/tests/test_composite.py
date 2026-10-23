"""0262 (G-1): the oracle's composite serialization equals the independently hand-traced literal vector
(fixtures/hand_calculated/composite.py; derivation in docs/0262-COMPOSITE-DERIVATION.md), for both candidates, and
round-trips. The fixture is built from literal grammar fields + sha256 only — never the oracle's encoders — so this is
an independent cross-check of the composite path, not a self round-trip."""
from oracle import canonicality as C
from fixtures.hand_calculated import composite as HC
from .harness import Cases


def run():
    c = Cases()
    for cand in ("A", "B"):
        def eq(cand=cand):
            state, expected = HC.composite_vector(cand)
            got = C.serialize_state(state, cand)
            if got != expected:
                i = next((k for k in range(min(len(got), len(expected))) if got[k] != expected[k]), min(len(got), len(expected)))
                raise AssertionError("composite bytes differ at %d (got %d B, hand %d B)" % (i, len(got), len(expected)))
        c.ok("G1 oracle composite == hand-traced literal [%s]" % cand, eq)

        def rt(cand=cand):
            state, expected = HC.composite_vector(cand)
            if C.reconstruct(expected, cand) != state:
                raise AssertionError("hand-traced composite did not reconstruct to the state")
        c.ok("G1 hand-traced composite reconstructs [%s]" % cand, rt)

    return c.done()
