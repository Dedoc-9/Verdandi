"""Crafted misplaced-bucket vectors (reported under G2). Each proves the SPECIFIC placement rejection path, and its
defect-removed counterpart validates cleanly (so the rejection is not an unrelated framing/digest/rebuild failure)."""
from oracle import canonicality as C
from fixtures.malformed import buckets as B
from .harness import Cases, reject


def run():
    c = Cases()

    for cand in ("A", "B"):
        # (1) misplaced depth: a well-framed bucket beneath the ROOT (depth 1) -> BUCKET_MISPLACED, specifically
        def misplaced(cand=cand):
            buf = B.misplaced_depth(cand)
            reject(lambda: C.reconstruct(buf, cand), code="BUCKET_MISPLACED")
        c.ok("G2 misplaced bucket (depth 1) -> BUCKET_MISPLACED [%s]" % cand, misplaced)

        # defect-removed counterpart: a correctly placed full-collision bucket (depth 52) validates cleanly
        def placed_ok(cand=cand):
            st, buf, kh_coll, _kh_bad = B.colliding_tree(cand)
            if C.reconstruct(buf, cand, keyhasher=kh_coll) != st:
                raise AssertionError("correctly-placed bucket did not validate")
        c.ok("G2 correctly-placed full-collision bucket validates [%s]" % cand, placed_ok)

        # (2) non-colliding members: the SAME well-framed depth-52 bucket, validated under a key-hash where its two
        # members do NOT fully collide -> BUCKET_NOT_COLLIDING, reached BEFORE the generic rebuild-compare
        def noncolliding(cand=cand):
            st, buf, _kh_coll, kh_bad = B.colliding_tree(cand)
            e = reject(lambda: C.reconstruct(buf, cand, keyhasher=kh_bad), code="BUCKET_NOT_COLLIDING")
            if e.code == "CANONICALITY":
                raise AssertionError("rejected by generic rebuild-compare, not the specific bucket reason")
        c.ok("G2 bucket members not fully colliding -> BUCKET_NOT_COLLIDING [%s]" % cand, noncolliding)

    return c.done()
