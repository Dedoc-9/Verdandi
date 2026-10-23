# P-1 red-hardening audit — research pass 1

> **DESIGN / research only, off-gate, P-1 remains `OPEN`.** An external-attack-class review of the rev-21 design. It
> changes **no** spec text and **no** code, implements nothing, and does **not** upgrade any implementation status.
> External material is treated as **untrusted reference data** (per the instruction boundary) — a known vulnerability
> in another format is a **prompt for a test**, not proof P-1 shares it. Every external source below was **verified by
> web search in this pass** (URLs in §Sources); the primary PDFs/RFC bodies were not all read in full. Seeded by the
> owner's RH-1…RH-5 pass; this doc adds source verification and independent refinements.
>
> **Headline:** no confirmed new normative defect; **no S-9 proposed.** The value is five falsification-test proposals
> (RH-T1…RH-T5) to run against the requirement matrix, plus three honest refinements to the seed pass. The existing
> BLOCKED items (D4-2/D8) and the G-1 provenance limit are reinforced, not resolved.

Grades: `CONFIRMED` (a demonstrated P-1 defect — none here) · `POTENTIAL` (sources justify a test; no P-1 failure
shown) · `NOT APPLICABLE` (the external case's mechanism does not arise in P-1) · `KNOWN-GAP` (already an explicit
BLOCKED/OPEN item) · `UNRESOLVED`.

## Findings

### RH-1 — resource bounds ≠ work bounds (POTENTIAL) · §0/§2/§4a/§8 · matrix R0.2/R0.4/R0.5, G6
`MAX_LEN`/`MAX_NODES`/`MAX_TOTAL` and the reduced-limit tests bound *sizes*; they do not by themselves bound *worst-case
work before rejection* or intermediate allocation. **Verified lesson — OpenSSL CVE-2026-34180:** a size must be checked
**at the point it is interpreted**, before conversion/allocation/iteration; there, an ASN.1 length > 2 GiB truncated an
integer and drove an over-reading zero-byte scan. **Refinement:** P-1 already avoids that specific pattern — `lp`
lengths are `u64` (no truncation to a machine int) and the reduced-limit tests show rejection **on the length prefix
before the body is buffered**. Residual: confirm *every* length/count/total boundary rejects before work, and that
rejected input cannot cause disproportionate processing. → **RH-T1.**

### RH-2 — canonicality across independent implementations (POTENTIAL) · §2–§4a/§8 · matrix R3.1/R4a.1, gap G-1
Two implementations can agree because they share a wrong reading. **Verified context — RFC 8949/dCBOR:** a format may
admit multiple serializations while a *protocol* imposes deterministic encoding and requires receivers to enforce it
(dCBOR: encoders MUST NOT emit duplicate keys; decoders MUST reject; keys compared by bytewise lexicographic order of
their deterministic encoding). P-1 takes the stricter stance (one accepted encoding). This **reinforces G-1**: the
0262 hand-traced composite partially addresses it, but coverage should add independently-derived expected bytes for
more shapes / a second encoder written from the prose. → **RH-T2.** No new defect.

### RH-3 — Merkle ambiguity / duplicate structure (NOT APPLICABLE as a CVE analogue; POTENTIAL as a test) · §3–§4a/§8 · R4a.2, G2/G3
**Verified — CVE-2012-2459:** Bitcoin's construction duplicates the last hash on odd levels, so `[1..6]` and
`[1..6,5,6]` yield the same root; the mutated block fails validation, and duplicate-tx rejection was the workaround
(BIP-98 proposes a non-ambiguous tree). **P-1 is structurally different:** nodes are explicitly encoded, `construct`
fixes the shape, one-slot branches carry no duplication, and duplicate child hashes within a parent are rejected
(`DUP_CHILD`, 0258). So there is **no demonstrated P-1 analogue.** The transferable lesson is to test uniqueness of the
*whole logical structure*, keeping these distinct: (a) two identical child refs in one parent → reject; (b) one child
shared across parents → lawful DAG; (c) duplicate logical keys → reject; (d) two encodings, one address →
`CONTENT_ADDRESS_COLLISION` (S-8, A-h-infeasible); (e) two representations of one state both validating → must be
impossible. → **RH-T3.**

### RH-4 — collision DoS / worst-case work (POTENTIAL, premise-limited) · §2–§4a/§8 · G2/G3/G6
**Verified — Crosby–Wallach (USENIX 2003):** adversarial inputs can push hash tables to O(n²) (all keys in one
bucket); defense is universal hashing. **Key refinement (narrows the seed pass):** the attack's premise is that the
attacker can **cheaply choose colliding keys**. P-1 routes by **SHA-256(KEY)**, so forcing key-hash collisions (or long
shared prefixes) is **infeasible without breaking A-h** — the classic hash-flooding DoS is mitigated **by the routing
itself**, not left open. The genuine residual is not collisions but **per-input validation work**: sorting bucket
members, duplicate-key checks, rebuild-and-compare, and deep/wide DAG traversal — measurable, not a collision weakness.
→ **RH-T4** (measure work; do **not** treat injected key-hash collisions as evidence SHA-256 collisions are attainable).

### RH-5 — domain separation and framing (KNOWN-GAP/reinforcement; no new defect) · §4/§8, §7 · G2/G3, G5, D4-2/D8
**Verified — RFC 6962/9162:** leaf `SHA256(0x00‖…)` vs node `SHA256(0x01‖…)` domain separation gives second-preimage
resistance; unpaired nodes are **promoted unchanged, not duplicated** (the anti-CVE-2012-2459 choice). P-1's per-node-
**type** domain tags (`skuld-<cand>-{empty,root,branch,leafent,leafcomp,bucket}-0`) are **stronger** than a 2-way
prefix, and `construct`'s one-slot branches likewise avoid duplication. **Separately — CT trust (RFC 6962/9162):** a
valid tree head does **not** prove a globally consistent history; logs can present split views, detected only by
monitoring/gossip. This **matches P-1's explicit separation** of checkpoint-digest validity / anchor identity /
reachability / trust, and **reinforces the D8 block** (non-genesis trust) and D4-2 (below-boundary anchor). No new
finding; keep those blocked. → **RH-T5.**

## Falsification-test proposals (to run against the matrix; none implemented)

- **RH-T1 (resource/work).** Every length/count/total boundary at limit−1 / limit / limit+1 without allocating the full
  payload; assert arithmetic/limit checks fire **before** conversion/allocation/iteration/recursion; truncated length
  fields, excess trailing bytes, individually-legal-but-collectively-over-`MAX_TOTAL`; parser↔builder boundary
  agreement; instrument allocation/work to bound processing-before-rejection. *Maps: R0.2/R0.4/R0.5, G6; extends the
  reduced-limit tests.*
- **RH-T2 (independent canonicality).** Independently-derived expected bytes for more small hand-enumerable states;
  valid vs malformed near-neighbours (reversed order, dup keys, alternate int forms, bad framing, missing/extra
  children, misplaced leaves); compare **accept/reject**, not just root hashes; keep the G-1 separation (a test that
  calls one constructor for both expected and actual is not independent). *Maps: R3.1/R4a.1, G-1.*
- **RH-T3 (structural uniqueness).** A table mapping cases (a)–(e) above to expected results; verify lawful cross-parent
  DAG sharing is accepted while within-parent duplication / non-canonical structure is rejected; keep the real-SHA-256
  key-hash KAT separate from the injected routing seam; **no node-address seam.** *Maps: R4a.2, G2/G3; S-8.*
- **RH-T4 (worst-case work).** State expected asymptotic work (in key bytes, node count, total bytes, bucket size);
  exercise maximally-shared DAGs, maximally-wide nodes, long shared prefixes, max buckets at reduced limits; count hash
  ops / comparisons / bytes / node visits; check shared subgraphs aren't re-validated per parent; injected collisions
  are a **mechanism** test only. *Maps: G2/G3/G6.*
- **RH-T5 (checkpoint trust).** Test digest validity / retained-chain reachability / genesis trust / non-genesis trust
  as **separate** predicates; a checkpoint whose digest recomputes but whose trust is unestablished; conflicting
  checkpoints at one claimed position → no inference of global agreement from local validity; keep effects-range-root
  (D4-2) and below-boundary anchor / non-genesis trust (D8) **blocked**. *Maps: §7, G5, D4-2/D8.*

## Disposition

| ID | Grade | Falsification probe — RUN 0263 (see [`P1-RED-HARDENING-TESTS.md`](P1-RED-HARDENING-TESTS.md)) |
|---|---|---|
| RH-1 | POTENTIAL | **RH-T1 run: 6/6 PASS** — every length/count/total rejects before work; no over-read, no crash. No defect. |
| RH-2 | POTENTIAL | **RH-T2 run: PASS** on near-neighbour accept/reject (both cands); the second independent encoder stays N.A./residual (G-1 reduced). No defect. |
| RH-3 | NOT APPLICABLE (CVE); POTENTIAL (test) | **RH-T3 run: (a)(b)(c)(e) PASS, (d) N.A.** — within-parent dup rejected, cross-parent DAG lawful, one canonical form. No defect. |
| RH-4 | POTENTIAL (premise-limited) | **RH-T4 run: OBSERVED** — work scales with element count, not depth (52-level bucket = 4 key-hash calls); shared subgraph validated once. Measurement, no defect. |
| RH-5 | KNOWN-GAP/reinforcement | **RH-T5 run: PASS + 2 BLOCKED** — predicates reported apart; no global-agreement inference; D4-2/D8 stay BLOCKED. No defect. |

**No S-9 proposed — now confirmed by execution.** The RH-T1…RH-T5 probes ran against the 0263 implementation
(`probes/redharden.py`): **21 PASS · 2 BLOCKED · 2 N.A. · 3 OBSERVED · 0 FAIL**. A FAIL would become a proposed S-9+
finding for owner adjudication — it does not silently alter rev 21. These remain research/probe dispositions, not
conformance claims; the web pass was not an independent reproduction of the gate or spec, and the probes are off the gate.

## Sources (verified this pass; untrusted reference data)
- CVE-2012-2459 / Bitcoin Merkle duplicate construction — [BIP-98](https://bitcoin.org/bip/98/), Bitcoin Core `merkle.cpp` comments, [Zebra merkle.rs](https://docs.rs/crate/zebra-chain/11.3.0/source/src/block/merkle.rs)
- RFC 8949 CBOR deterministic encoding / dCBOR — [draft-mcnally-deterministic-cbor](https://datatracker.ietf.org/doc/draft-mcnally-deterministic-cbor/)
- RFC 6962 / RFC 9162 Certificate Transparency domain separation + split-view — [rfc6962-bis draft](https://potaroo.net/ietf/all-ids/draft-ietf-trans-rfc6962-bis-26.html), [Merkle tree (Wikipedia)](https://en.wikipedia.org/wiki/Merkle_tree)
- Crosby & Wallach, "Denial of Service via Algorithmic Complexity Attacks," USENIX Security 2003 — [USENIX abstract](https://www.usenix.org/conference/12th-usenix-security-symposium/denial-service-algorithmic-complexity-attacks)
- OpenSSL CVE-2026-34180 (ASN.1 >2 GiB length truncation over-read) — [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-34180), [OpenSSL advisory](https://mirror.openssl-library.org/news/vulnerabilities-4.0/)
