// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/liveauthor.rs — LIVE-AUTHOR-0: the live editor's authoring binding, and the palette.
//
// The live editor (`shell live-window`, `shell live-selftest`) is LIVE-SESSION-0's durable loop under this binding:
// LIVE-INPUT-0's keys unchanged, plus 1-5 for the tile classes wall0, wall1, wall2, wall3 and floor. A class key
// becomes one edit, tile:CLASS,R,G,B, whose colour is the palette's next entry after the class's current colour — read
// from the session's own M — or the palette's first if the class is not one of its colours. Pure: the same key over
// the same M gives the same edit. Nothing here holds a colour, a tile or a preview: the edit is appended to the
// session, which applies it, and the next frame is rendered from the resulting M.

use crate::liveinput::Action;

/// The registered palette: 8 colours, in cycling order.
pub const PALETTE: [[u8; 3]; 8] = [
    [96, 80, 64],    // umber
    [176, 176, 176], // stone
    [178, 58, 48],   // brick
    [56, 104, 168],  // slate
    [72, 136, 72],   // moss
    [200, 176, 96],  // sand
    [120, 80, 152],  // plum
    [232, 232, 224], // chalk
];

/// The live editor's binding: 1-5 are the tile classes; every other key is LIVE-INPUT-0's.
pub fn bind(vk: u32) -> Action {
    match vk {
        0x31..=0x35 => Action::Tile((vk - 0x31) as u8), // 1 wall0, 2 wall1, 3 wall2, 4 wall3, 5 floor
        _ => crate::liveinput::bind(vk),
    }
}

/// The colour a class key gives: the palette entry after the class's current colour, or the first entry when the class
/// is textured or painted outside the palette.
pub fn next_colour(current: Option<[u8; 3]>) -> [u8; 3] {
    match current.and_then(|c| PALETTE.iter().position(|p| *p == c)) {
        Some(i) => PALETTE[(i + 1) % PALETTE.len()],
        None => PALETTE[0],
    }
}
