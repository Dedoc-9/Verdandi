<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- brief-falsifier: chorus-topology -->
# `chorus` — design brief (URDRCHO1, WINDOW-0: observer composition)

**Built**: 2026-09-20, one rung after `kinema`, on the boundary the WINDOW-0 measurement pass established. It
is the **sixteenth game-layer vertical slice**, **WINDOW-0** of the observer-composition arc, and the **second
game-layer VIEW module**.

## 0. The one invariant

> **Observer topology is disposable; canonical simulation is not.**

The entire observer collection can be created, destroyed, rearranged, delayed, duplicated, or omitted without
changing canonical simulation. `chorus` establishes the display-side half of that at the collection level; the
canonical half is proven at the gate against a real core.

## 1. What it is

    observe(transition, spec)  -> a Frame-set          (one kinema application)
    compose(transition, specs) -> Scene = ((observer_id, Frame-set), …)

A `Scene` is a tuple of per-observer Frame-sets over **one** authoritative transition, composed **purely by
repeated `kinema` application**. `transition = (level_n, pos_n, witness_n, level_m, pos_m, witness_m)`; the
witnesses (which are `Dₙ` values) enter **opaque** and are carried **verbatim**.

## 2. No N-window authority

`compose` is exactly `tuple((s.observer_id, observe(transition, s)) for s in specs)`. N is a plain list
length; **N=0 is the empty Scene**. There is no special multi-window authority, and a future window/layout
layer consumes the `Scene`/`Frame`s — **never `Dₙ`**.

## 3. The ObserverSpec is disposable

    ObserverSpec(observer_id, source_tick, samples, window)

`window` is an **opaque, inert** blob — bounds, focus, z-order, camera, zoom, layout — that WINDOW-0 consumes
nowhere (camera/layout are a later arc). Two specs differing only in `window`/`observer_id` produce
**byte-identical** Frame-sets: window state reaches neither the Frames nor any canonical value. It is carried
so the shape is right for later rungs, and proven inert so it cannot leak.

## 4. Agreement is provenance, not pixels

A pane's **provenance** is `(source_tick, witness_n, witness_m, cls)`. Panes of one transition **share** it
while their refined samples differ (different `samples`). *Same authority is not the same picture.* And
**permutation invariance is canonical-only**: reordering the collection leaves the provenance **multiset**
identical, but the ordered Scene is deliberately **not** certified equal — ordering is not an earned observer
law, and `chorus` refuses to smuggle one in.

## 5. Staleness is provenance, not reconstruction

A pane observing an older transition carries the older witnesses; a current pane the current ones. They are
distinguished by provenance, and **neither synthesises a between-state** — `kinema`'s one-transition input
boundary makes this structural (a pane is handed exactly one transition and can only interpolate within it).

## 6. Topology is a list operation

Add / remove / reorder / duplicate / omit specs and the Scene's panes and their provenance multiset follow the
spec list exactly — the Scene is a pure function of `(transition, specs)`. The **canonical** half of the
differential (mutating the observer collection, including N=0, leaves the canonical transcript byte-identical)
is the **gate's**, run against a real `enact`/`statecanon`/`rerun` core, because this module cannot and must
not reach that core.

## 7. The membrane is one-way (D25 §11, extended)

`the_membrane_is_one_way` reads this module's **own full AST** — function-local imports included — and is
direction-aware: it imports exactly `ALLOWED_IMPORTS`, imports **none** of `move`/`descend`/`loot`/`enact`/
`statecanon`/`rerun`/`savegame`/`lockstep` in any scope, and reaches no `.d_n`/`.d_n_preimage` (**no `Dₙ`
ingestion**) and no `.step`/`.dispatch`/`.apply` mutator. Positive controls: synthetic modules that nest an
`enact` import, a `statecanon` import, a `.dispatch` reach and a `.d_n` reach are each rejected, while the
read-only `kinema`/`gamegen`/`descent` path is accepted.

## 8. Inherited, not re-proved

A forged transition refuses through `kinema` (KINEMA-REFUSE via `descent.traversable`); render-cadence
independence is `panelight`'s (URDRPNL1) dt-log decoupling plus the tree's clock guards; the no-successor and
forged-pair guarantees are `kinema`'s.

## 9. Grade

**MEASURED**: `compose` is repeated `observe`; panes of one transition agree on provenance while samples
differ; the provenance multiset is permutation-invariant; add/remove/reorder/duplicate/omit follow the spec
list; the empty Scene is pure; the `window` blob is disposable. **ESTABLISHED**: a stale and a current pane
differ by provenance and neither synthesises a between-state; a forged transition refuses KINEMA-REFUSE; the
membrane is one-way (full-AST, direction-aware, no `Dₙ` ingestion, positive control). **DECLARED**: the
observer model is `kinema`'s; the `window` blob is inert this rung; permutation invariance is canonical-only;
single peer.

## does_not_show

The canonical topology differential across a real core (the gate's, not the module's); window → `enact` input
(WINDOW-1, the separate later membrane); OS-native windows, GPU composition, camera architecture, voxels,
wireframes, developer authoring, and any wall-clock or frame budget (all deferred).

## Falsifier

`chorus-topology` (add/remove/reorder/duplicate/omit follow the spec list; the provenance multiset is
permutation-invariant with ordering NOT certified; the empty Scene is pure; the `window` blob is disposable;
stale and current panes differ by provenance without a synthesised between-state; a forged transition
refuses), with `chorus:scenes` (the two scenes and the top digest reproduce, an unpinned name refuses typed
`CHORUS-REFUSE`) and `chorus-compose` (composition is repeated `kinema` application; panes of one transition
agree on provenance while samples differ; the full-AST one-way guard bites with its positive control; and the
**canonical topology differential** — mutating the observer collection, N=0 included, leaves the canonical
component identities and the `rerun` verdict byte-identical) alongside; `tests/test_chorus.py`.
