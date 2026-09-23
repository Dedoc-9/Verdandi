<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `workshop/` — the design loop

Contract: an authored edit in, a new authority out, and beside it a consequence record that says exactly what
the edit moved. The authority is split three ways and the record keeps them apart: **W** the level (its
cells, its depth, the depth's table and maps), **M** the material set (the tiles), **C** the camera — carried
through an edit untouched, because a view mutation is not an edit. The consequence is measured, not
estimated: the two witnesses before and after, the columns whose strip changed, the pixels that differ.

The workshop validates before it projects (an edit that cannot play is refused with a reason and the old
authority stands), creates new authority as files (the world survives the app), and holds no renderer
state: it calls the kernel; it never draws.

Lands at WORKSHOP-0 with two planted falsifiers: a stale projection under a changed authority must redden,
and a projection that moved without an authority change must be detected, never accepted.
