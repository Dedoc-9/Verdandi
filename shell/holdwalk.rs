// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/holdwalk.rs — HOLD-WALK-0: which held keys walk the live editor.
//
// The live editor binds a fresh press exactly as LIVE-AUTHOR-0 does. An auto-repeated press (the key already down) of a
// key in this held set is bound as that key's move, so holding W walks and holding A or D looks around, one ordinary
// move event per admitted repeat. The loop admits at most one repeat per composition and counts the rest as coalesced;
// a repeat of any other key (Q, E, Space, 1-5, Esc) is ignored, so holding an edit key edits once. The input is
// continuous; the world is not: every admitted repeat is one cell step or one quarter turn in the same SESSION-WALK
// log a pressed walk makes. Nothing here holds a key state or reads a clock: the key code alone decides.

use crate::liveinput::{VK_DOWN, VK_LEFT, VK_RIGHT, VK_UP};

/// The held set: W, A, S, D and the four arrows — the steps and the quarter turns.
pub const HELD: [u32; 8] = [0x57, 0x41, 0x53, 0x44, VK_UP, VK_LEFT, VK_DOWN, VK_RIGHT];

/// Whether an auto-repeat of this key walks. Pure.
pub fn held(vk: u32) -> bool {
    HELD.contains(&vk)
}
