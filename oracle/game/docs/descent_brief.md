<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: descent-witness -->
# `descent` — design brief (URDRDSC1, the topology witness)

**Built**: 2026-09-15, one rung after `gamegen`, on the inputs measured from a `gamegen` level before
a line of the witness was written. It is D24 §3's topology row — *"a reachability witness per level,
and a planted wall that seals a room reddens"* — made a law.

## 0. What it is

**The stairs are connected, or they are not, and the witness is a path.** `gamegen` produces a
canonical level and says nothing about whether it can be walked; its own `does_not_show` states that
the stairs down are reachable from the stairs up *only by construction*, and construction is not a
witness. `descent` is the witness. It reads a `gamegen` level, finds the two stairs, and produces a
concrete path from one to the other — or reports that none exists.

It **consumes** `gamegen`; `gamegen` does not know it exists. The dependency runs one way, and
`gamegen` was sealed one rung earlier importing only `hashlib` and `os`.

## 1. What the witness reads — measured, not chosen

Before writing the module, eight questions were answered from the level itself:

| # | question | answer |
|---|---|---|
| 1 | the representation | `level.cells`, the 48×32 grid `gamegen` already emits — no parallel representation |
| 2 | the adjacency | orthogonal 4-neighbour; traversable iff `.`, `<` or `>`; derived each call, stored nowhere |
| 3 | the endpoints | the unique `<` and unique `>`; anything else is a typed refusal |
| 4 | the output | a concrete path (a tuple of coordinates), not `True` |
| 5 | the counterexample | a ring-sealed stairs-down room |
| 6 | the dependency | `descent` → `gamegen`, one way |
| 7 | identity separation | reachability is a path property, not a digest |
| 8 | is the grid already a graph? | yes — over 256 levels the whole floor is one connected component |

Answer 8 is why the stairs connect by construction, and is a measurement about the *generator*, not
this law. The witness checks the property anyway, because a construction that happens to hold is not
a proof that it does.

## 2. The path is verified independently of the search

`descent_path` runs a deterministic BFS — neighbours in a fixed order, parent pointers, the shortest
path reconstructed from the goal. `verify_path` then checks the result **without re-running the
search**: every step orthogonally adjacent, every cell traversable, the ends the two stairs. The
expensive half is the search and the trusted half is checking a walk — `cutpin`'s shape, a witness
you can believe by reading it. The canonical path's length and digest are pinned, so the witness
reproduces bit-for-bit, and a severed level digests a distinct, stable empty witness.

## 3. The counterexample, and why it is sharp

`seal_down` walls the one-cell margin around the stairs-down room, severing every corridor mouth
while leaving the room interior, both stairs, the border and the alphabet intact. Measured over 256
levels: connected up→down *before*, severed *after*, both endpoints present and in rooms, the grid
valid, the ring never touching another room's interior.

The sharp part is what the seal does **not** break. The sealed level still passes every one of
`gamegen`'s structural predicates — `gamegen.is_well_formed(sealed)` is `True`:

> A level can be generation-correct in every way the generator's oracle can see and still be
> untraversable.

That is why topology is a **separate law** and not a corollary of generation. The two oracles do not
collapse into each other, `gamegen-*` certifying that a level is canonical and reproducible and
`descent-*` that a property of it holds. `descent-oracles` asserts it on every run.

## 4. The input domain

The witness refuses, typed, any level without exactly one stairs-up and one stairs-down. An absent or
doubled endpoint is outside what a reachability question means, and a witness that guessed would be
answering a question it was not asked. Every `gamegen` level is in the domain; a level need not be a
`gamegen` level to be, which is exactly what admits the sealed counterexample.

## 5. Grade

**MEASURED**: over the corpus and a 128-level sweep, the stairs connect and the returned path
verifies independently; the sealed counterexample severs them while staying in the domain and
well-formed under `gamegen`; the path digests reproduce. **ESTABLISHED**: `verify_path` accepts a
walk iff it is one (a broken step, a wall step, a wrong endpoint each rejected); the domain refusals
are total; the two-oracle separation. **DECLARED**: that orthogonal 4-adjacency over `{floor, up,
down}` is the traversal model — a choice a later movement rung may widen (diagonals, doors, keys) by
minting a new law, never by editing this one.

## does_not_show

That a reachable level is worth playing. That the **whole** level is connected — the witness proves
the *stairs* connect and nothing more, even though the generator happens to produce fully-connected
levels, because proving more than the claim is how a witness starts lying. That the path is the
*shortest* (it is BFS's, but shortest-ness is not the claim). That traversal in the game will use
this adjacency — a door or a locked gate is a later law. And nothing about `gamegen`'s correctness,
which is its own rung's and which this witness deliberately cannot see.

## Falsifier

`descent-witness` (a verified path on every corpus level and across the sweep), with `descent:scenes`,
`descent-sealed` (the counterexample rejected both directions), `descent-oracles` (the two oracles do
not collapse) and `descent-domain` (endpoint refusals and forgery rejection) alongside;
`tests/test_descent.py`.
