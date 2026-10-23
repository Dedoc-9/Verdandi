"""p1-oracle: a test-only, standalone decoder/oracle for the P-1 byte-encoding contract (ENCODING-TABLE-P1.md rev 20).

OFF-GATE / SCRATCH. Not part of the Verdandi gate; P-1 remains OPEN. See AUTHORIZATION.md.

The oracle derives its rules from the written P-1 grammar. Its only semantic dependency is the frozen ECS
(oracle/frozen/ecs.py, sha256 3d568d22...), used for Tier-3 replay (ecs._apply_ops) and the conformance identity
(ecs.digest). It never imports a production candidate implementation.
"""
