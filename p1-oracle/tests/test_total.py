"""0261 (G-7): aggregate-byte limit MAX_TOTAL (reported under G6). MAX_TOTAL counts the sum of the unique node
encodings (not the container header), tallied incrementally. Tests the parser boundary, the builder honouring the same
limit (0261 fix: serialize_state now checks MAX_TOTAL for builder/parser symmetry), the combined-exceeds case,
truncation-near-limit kept distinct from a resource reject, and the production constant kept separate from the reduced
test limit. Both candidates."""
from oracle import decoder as d
from oracle import canonicality as C
from .harness import Cases, reject

ST = {"entities": {"e1": {"hp": 1, "name": "orc", "pos": 5}, "e2": {"k": -7}}, "alloc": 3, "rng": {"seed": 0, "counter": 0}}


def run():
    c = Cases()
    for cand in ("A", "B"):
        _rh, coll = C.build_state(ST, cand)
        total = sum(len(e) for e in coll.values())              # what MAX_TOTAL counts
        sizes = sorted(len(e) for e in coll.values())
        buf = C.serialize_state(ST, cand)                       # production limits

        c.ok("G6 MAX_TOTAL parser at-limit accepts [%s]" % cand,
             lambda cand=cand, buf=buf, total=total: C.parse_collection(buf, cand, d.Limits(max_total=total)))
        c.ok("G6 MAX_TOTAL parser one-under -> MAX_TOTAL [%s]" % cand,
             lambda cand=cand, buf=buf, total=total: reject(lambda: C.parse_collection(buf, cand, d.Limits(max_total=total - 1)), code="MAX_TOTAL"))
        c.ok("G6 MAX_TOTAL combined-exceeds (legal singles) -> MAX_TOTAL [%s]" % cand,
             lambda cand=cand, buf=buf, sizes=sizes: reject(lambda: C.parse_collection(buf, cand, d.Limits(max_total=sizes[-1] + 1)), code="MAX_TOTAL"))

        c.ok("G6 MAX_TOTAL builder at-limit accepts [%s]" % cand,
             lambda cand=cand, total=total: C.serialize_state(ST, cand, limits=d.Limits(max_total=total)))
        c.ok("G6 MAX_TOTAL builder one-under -> MAX_TOTAL (0261 fix) [%s]" % cand,
             lambda cand=cand, total=total: reject(lambda: C.serialize_state(ST, cand, limits=d.Limits(max_total=total - 1)), code="MAX_TOTAL"))

        def symmetry(cand=cand, total=total):
            lim = d.Limits(max_total=total)
            out = C.serialize_state(ST, cand, limits=lim)        # builder accepts at the limit
            C.parse_collection(out, cand, lim)                   # parser accepts the builder's output at the same limit
            reject(lambda: C.serialize_state(ST, cand, limits=d.Limits(max_total=total - 1)), code="MAX_TOTAL")
        c.ok("G6 MAX_TOTAL builder/parser symmetry at reduced limit [%s]" % cand, symmetry)

        def truncation(cand=cand, buf=buf):
            reject(lambda: C.parse_collection(buf[:-5], cand, d.PROD_LIMITS), code="TRUNCATED")
        c.ok("G6 truncation near limit -> TRUNCATED, not MAX_TOTAL [%s]" % cand, truncation)

    def prod_constant():
        if d.MAX_TOTAL != 2 ** 40:
            raise AssertionError("production MAX_TOTAL != 2**40")
    c.ok("G6 production MAX_TOTAL == 2**40 (separate from reduced test limits)", prod_constant)
    return c.done()
