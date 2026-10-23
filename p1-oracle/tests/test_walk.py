"""0263 direct P6 enforcement (reported under G2): the explicit ancestor-slot walk (canonicality._p6_walk) checked in
ISOLATION via check_p6_walk, so each row shows the walk BY ITSELF accepts a canonical tree or rejects an off-path one
for its specific reason (WALK_MISROUTE / BUCKET_MISPLACED / BUCKET_NOT_COLLIDING). Both candidates. Misroutes at depth 0,
at a deeper branch, and inside a component trie exercise the "every ancestor slot" requirement (not just the parent).

Attribution is reported UNPROVEN by construction: rebuild-and-compare is a COMPLETE canonicality check, so it rejects
every off-path tree too; there is no witness the walk catches that rebuild-and-compare accepts. The last row disables the
walk (_p6=False) and shows the SAME tree is still rejected (CANONICALITY) — proving the walk produces the specific
verdict, not that it is necessary.
"""
from oracle import canonicality as C
from fixtures.malformed import walk as W
from fixtures.malformed import buckets as B
from .harness import Cases, reject


def run():
    c = Cases()
    for cand in ("A", "B"):

        # --- accepting controls: the walk alone accepts canonical trees -------------------------------------------
        def accept_ent(cand=cand):
            st, buf, kh = W.accept_entities(cand)
            C.check_p6_walk(buf, cand, keyhasher=kh)                       # walk alone: no raise
            if C.reconstruct(buf, cand, keyhasher=kh) != st:
                raise AssertionError("canonical two-entity tree did not round-trip")
        c.ok("P6 walk accepts canonical two-entity tree (control) [%s]" % cand, accept_ent)

        def accept_bucket(cand=cand):
            _st, buf, kh_coll, _bad = B.colliding_tree(cand)
            C.check_p6_walk(buf, cand, keyhasher=kh_coll)                  # legit full-collision bucket at depth 52
        c.ok("P6 walk accepts correctly-placed depth-52 bucket (control) [%s]" % cand, accept_bucket)

        # --- misrouting at three depths: the walk ALONE rejects ---------------------------------------------------
        def mr_root(cand=cand):
            buf, kh = W.misroute_root(cand)
            reject(lambda: C.check_p6_walk(buf, cand, keyhasher=kh), code="WALK_MISROUTE")
        c.ok("P6 walk alone rejects leaf off-path at ROOT (depth 0) -> WALK_MISROUTE [%s]" % cand, mr_root)

        def mr_branch(cand=cand):
            buf, kh = W.misroute_branch(cand)
            reject(lambda: C.check_p6_walk(buf, cand, keyhasher=kh), code="WALK_MISROUTE")
        c.ok("P6 walk alone rejects leaf off-path at a deeper BRANCH (depth 1) -> WALK_MISROUTE [%s]" % cand, mr_branch)

        def mr_comp(cand=cand):
            buf, kh = W.misroute_comp(cand)
            reject(lambda: C.check_p6_walk(buf, cand, keyhasher=kh), code="WALK_MISROUTE")
        c.ok("P6 walk alone rejects component off-path in a component trie -> WALK_MISROUTE [%s]" % cand, mr_comp)

        # --- bucket boundary: depth 52 and full collision, the walk alone -----------------------------------------
        def bk_misplaced(cand=cand):
            buf = B.misplaced_depth(cand)
            reject(lambda: C.check_p6_walk(buf, cand), code="BUCKET_MISPLACED")
        c.ok("P6 walk alone rejects bucket off terminal depth 52 -> BUCKET_MISPLACED [%s]" % cand, bk_misplaced)

        def bk_noncoll(cand=cand):
            _st, buf, _coll, kh_bad = B.colliding_tree(cand)
            reject(lambda: C.check_p6_walk(buf, cand, keyhasher=kh_bad), code="BUCKET_NOT_COLLIDING")
        c.ok("P6 walk alone rejects bucket members not fully colliding -> BUCKET_NOT_COLLIDING [%s]" % cand, bk_noncoll)

        # --- reconstruct surfaces the walk's specific code BEFORE rebuild-compare ---------------------------------
        def recon_walk(cand=cand):
            buf, kh = W.misroute_root(cand)
            reject(lambda: C.reconstruct(buf, cand, keyhasher=kh), code="WALK_MISROUTE")
        c.ok("reconstruct() surfaces the walk's code before rebuild-compare -> WALK_MISROUTE [%s]" % cand, recon_walk)

        # --- attribution UNPROVEN: walk disabled, the tree is STILL rejected by rebuild-compare alone -------------
        def attribution(cand=cand):
            buf, kh = W.misroute_root(cand)
            e = reject(lambda: C.reconstruct(buf, cand, keyhasher=kh, _p6=False), code="CANONICALITY")
            return ("attribution UNPROVEN: rebuild-and-compare independently rejects (%s); walk gives the reason, "
                    "not a unique catch" % e.code)
        c.ok("attribution UNPROVEN: walk disabled -> still rejected by rebuild-compare (CANONICALITY) [%s]" % cand, attribution)

    return c.done()
