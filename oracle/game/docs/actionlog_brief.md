<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: actionlog-order -->
# `actionlog` — design brief (URDRACT1, the authoritative recoverable action history)

**Built**: 2026-09-18, one rung after `heirloom`, on the boundary measured from `rngstream`. It is the
**tenth game-layer vertical slice**, the first **sequence/order** rung (where `combat` and `heirloom` were
pure per-input arithmetic), and the first **consumer** — not a stdlib leaf — since `loot`. D24 §2:
"authoritative action history — the ordered inputs replay consumes".

## 0. What it is

An immutable, recoverable, order-committing log of opaque action tokens:

    empty() -> ()
    append(log, action) -> log'          # immutable, order-sensitive; one rngstream.advance
    entries(log) -> (bytes, ...)          # RECOVERABLE — the capability the stream lacks
    count(log) -> int
    digest(log) -> hex                    # order-committing, via rngstream's fold from LOG_ROOT

## 1. Why it is not redundant with `rngstream`

The stream already commits to the ordered action history (its chain `R_{n+1} = SHA(…|R_n|action)` diverges
under reordering), but it **discards the actions**: the transition is one-way, so `R_n` cannot be read back
into the sequence that produced it. `replay` (rung 10) will need to re-consume the actions and the stream
cannot give them back. So this rung owns the one thing the stream lacks: **recoverability**. `rngstream`
owns ordered state *transition*; `actionlog` owns recoverable ordered *history*.

## 2. Order is composed, not reinvented

The log's order-committing identity **is** `rngstream`'s fold, from a declared, seed-independent,
domain-separated root:

    LOG_ROOT = Stream(0, SHA("URDRACT1|root"))
    digest(log) = rngstream.stream_digest(rngstream.apply(LOG_ROOT, entries(log)))

There is **no second hash chain**: `append` is exactly one `rngstream.advance` (`each_append_is_one_advance`),
and the ordering functions build no `hashlib` chain of their own (the only `hashlib.sha256` is the root
constant, read off the module's AST). The ordering **authority** stays `rngstream`'s; `actionlog` adds the
recoverable entries and the count.

## 3. One vocabulary

Tokens are canonicalized by exactly `rngstream`'s rule (`str → utf-8`, `bytes` pass through, else refuse), so
a `str` token and its utf-8 `bytes` are the **same action** and never split the log's identity. This is not
merely a copied rule: the stream-agreement law **gate-enforces** the match, because a divergent
canonicalization would fail to reproduce the run's stream.

## 4. The stream-agreement law is the external ruler

Folding the logged actions through `rngstream.apply(root(seed), entries(log))` **reproduces** run `seed`'s
stream, and a reordered log **diverges** it. The point is that a reorder is caught by the **stream** — an
authority this module does not own — so `actionlog` cannot certify its own ordering merely by agreeing with
its own digest. **Not claimed** (your refinement): that the log is the unique mathematical *preimage* of an
arbitrary stream state. The stream's transition is one-way; the log is a recoverable **source sequence** that
reproduces a stream, which is weaker and true.

## 5. The tokens stay opaque

No canonical action vocabulary has been earned: `move`'s `N/S/E/W` commands do not advance the stream, `loot`
folds `b"loot:" + S`, and there is no unified typed command type. So the log records **opaque tokens** and
commits to their order; interpreting a token as a move, a loot or a descend is a later rung's
(`statecanon`/`replay`), and this module imports neither `move` nor `entity` — importing them to make the log
"look game-specific" would invent structure the measurement did not earn. It imports `rngstream` (+ stdlib),
import-depth 1 — a genuine consumer, superseding the roadmap's predicted `transition`/`entity` dependencies.

## 6. The reorder witness, explicit

Because this is the first sequence-history rung: `[A,B]` and `[B,A]` produce **different** committed states
(`a_reorder_changes_the_committed_state`), while the `str`/`bytes` equivalence produces the **same** state
(`str_and_bytes_are_the_same_action`). The `laws` scene pins both witnesses.

## 7. Grade

**MEASURED**: over the corpus `entries` recover the exact appended order; a reorder of two distinct actions
changes the digest while a `str`/`bytes` equivalence does not; folding the entries through a run seed
reproduces that run's stream and a reordered log diverges it; each `append` is exactly one `rngstream.advance`.
**ESTABLISHED**: `append` is immutable and order-sensitive; the empty log has a canonical identity; the
ordering builds no second hash chain; a malformed action or a malformed log refuses typed `ACTIONLOG-REFUSE`;
`rngstream` imports no `actionlog`. **DECLARED**: that tokens are opaque and canonicalized by `rngstream`'s
rule, and that a typed command vocabulary, the "replay consumes only this" claim, disk persistence,
entity/snapshot binding and bounded/compacted history are later rungs'.

## does_not_show

That the log is replay's sole input (replay is unbuilt); that it survives a process (persistence is
`persist`'s, rung 9); what a token means (opaque, no typed vocabulary earned); that it is a unique preimage of
a stream state (only that it reproduces one); and nothing about `rngstream`'s own law, which stands on its own
frozen vectors and imports no `actionlog`.

## Falsifier

`actionlog-order` (order is composed not duplicated and certified by an authority this module does not own:
the digest is `rngstream.apply` from a declared root, `append` is one `rngstream.advance`, `[A,B]` and `[B,A]`
commit to different states while `str`/`bytes` commit to the same, and folding the log through a run seed
reproduces that run's stream while a reordered log diverges it — recomputed against `rngstream` directly),
with `actionlog:scenes` (the two scenes and the top digest reproduce, an unpinned name refuses) and
`actionlog-isolation` (a consumer of `rngstream` plus stdlib only, no `move`/`entity`, no second hash chain,
typed `ACTIONLOG-REFUSE`) alongside; `tests/test_actionlog.py`.
