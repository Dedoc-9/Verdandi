// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/hud.rs — HUD-0: the overlay is a frame.
//
// The kernel draws the HUD into the picture it already made, so the shell blits ONE buffer and the gate pins
// the overlay like any other pixels. Geometry only in this rung (no glyph, no font, no asset): a reticle at the
// horizon, a strip-band bar along the bottom (per column: the depth band as height, the light family as
// shade — read off the strips), a facing plate (four squares, the current facing lit) and a minimap of the
// level's cells with the camera's cell marked and a tick on its facing side. Every mark is a function of
// kernel state — the strips, the camera, the cells — and of nothing the shell knows.
//
// THE LAWS THIS FILE IS HELD TO (../verify/verify.py):
//   the HUD moves no index      — the URDRFB1 frame digest is the same with and without the overlay
//   the HUD stays in its region — outside `region()` the composite equals the viewport picture, byte for byte
//   the HUD reads state         — the overlay bytes change with the camera and the level, and not with the tiles
//   the overlay is pinned       — three witnesses per scene: viewport sha, overlay sha, composite sha
//
// Constants are DECLARED (the layout, the shades); their values are pinned by the rows, not argued.

use super::mantle::{face_light, Scene, Strip, CY, H, W};

// ---- layout (pixels) --------------------------------------------------------------------------------------
pub const RETICLE_ARM: usize = 9; // half-length of each arm
pub const RETICLE_GAP: usize = 3; // half-gap at the centre
pub const BAR_ROWS: usize = 40; // the strip-band bar: the bottom BAR_ROWS rows
pub const PLATE_MARGIN: usize = 16;
pub const FACING_SQUARE: usize = 12;
pub const FACING_PLATE: usize = 48;
pub const CELL_PX: usize = 4; // minimap: one level cell
pub const MAP_BORDER: usize = 4;

// ---- shades (RGB) -----------------------------------------------------------------------------------------
pub const BLACK: [u8; 3] = [0, 0, 0];
pub const WHITE: [u8; 3] = [255, 255, 255];
pub const PLATE: [u8; 3] = [24, 24, 24];
pub const DIM: [u8; 3] = [72, 72, 72];
// the bar's shade per light family: 240 * LIGHT_PERMILLE / 1000 for (1000, 828, 607, 429)
pub const BAR_SHADE: [[u8; 3]; 4] = [[240, 240, 240], [199, 199, 199], [146, 146, 146], [103, 103, 103]];
pub const MAP_ROCK: [u8; 3] = [40, 40, 40];
pub const MAP_FLOOR: [u8; 3] = [160, 160, 160];
pub const MAP_UP: [u8; 3] = [80, 160, 220];
pub const MAP_DOWN: [u8; 3] = [220, 140, 60];
pub const MAP_EYE: [u8; 3] = [255, 255, 255];
pub const MAP_TICK: [u8; 3] = [255, 0, 0];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rect {
    pub x0: usize,
    pub y0: usize,
    pub x1: usize, // exclusive
    pub y1: usize, // exclusive
}

impl Rect {
    pub fn contains(&self, x: usize, y: usize) -> bool {
        x >= self.x0 && x < self.x1 && y >= self.y0 && y < self.y1
    }
}

/// The declared region: the union of four rectangles. The overlay may write only inside it.
pub fn region(scene: &Scene) -> [Rect; 4] {
    let cx = W / 2;
    let cy = CY as usize;
    let reticle = Rect { x0: cx - RETICLE_ARM - 1, y0: cy - RETICLE_ARM - 1, x1: cx + RETICLE_ARM + 2, y1: cy + RETICLE_ARM + 2 };
    let bar = Rect { x0: 0, y0: H - BAR_ROWS, x1: W, y1: H };
    let facing = Rect { x0: PLATE_MARGIN, y0: PLATE_MARGIN, x1: PLATE_MARGIN + FACING_PLATE, y1: PLATE_MARGIN + FACING_PLATE };
    let map_w = scene.w * CELL_PX + 2 * MAP_BORDER;
    let map_h = scene.rows * CELL_PX + 2 * MAP_BORDER;
    let map = Rect { x0: W - PLATE_MARGIN - map_w, y0: PLATE_MARGIN, x1: W - PLATE_MARGIN, y1: PLATE_MARGIN + map_h };
    [reticle, bar, facing, map]
}

pub fn in_region(rects: &[Rect; 4], x: usize, y: usize) -> bool {
    rects.iter().any(|r| r.contains(x, y))
}

#[inline]
fn put(out: &mut [u8], x: usize, y: usize, rgb: [u8; 3]) {
    let o = (y * W + x) * 3;
    out[o..o + 3].copy_from_slice(&rgb);
}

fn fill(out: &mut [u8], r: Rect, rgb: [u8; 3]) {
    for y in r.y0..r.y1 {
        for x in r.x0..r.x1 {
            put(out, x, y, rgb);
        }
    }
}

/// Draw the overlay into `out` (the W*H*3 picture), reading the strips and the scene. Pure; no allocation
/// beyond the stack; writes only inside `region(scene)`.
pub fn overlay(scene: &Scene, strips: &[Strip], out: &mut [u8]) {
    let [reticle, bar, facing, map] = region(scene);

    // reticle: a black 3-px cross under a white 1-px cross, a gap at the centre
    let cx = W / 2;
    let cy = CY as usize;
    for d in RETICLE_GAP..=RETICLE_ARM {
        for t in 0..3usize {
            let k = t as isize - 1;
            put(out, cx + d, (cy as isize + k) as usize, BLACK);
            put(out, cx - d, (cy as isize + k) as usize, BLACK);
            put(out, (cx as isize + k) as usize, cy + d, BLACK);
            put(out, (cx as isize + k) as usize, cy - d, BLACK);
        }
    }
    for d in RETICLE_GAP..=RETICLE_ARM {
        put(out, cx + d, cy, WHITE);
        put(out, cx - d, cy, WHITE);
        put(out, cx, cy + d, WHITE);
        put(out, cx, cy - d, WHITE);
    }
    let _ = reticle;

    // strip-band bar: black, then per column (band + 1) px from the bottom in the light family's shade
    fill(out, bar, BLACK);
    for (c, s) in strips.iter().enumerate().take(W) {
        let h = (s.band.max(0).min(BAR_ROWS as i64 - 1) + 1) as usize;
        let shade = BAR_SHADE[face_light(s.face)];
        for y in (H - h)..H {
            put(out, c, y, shade);
        }
    }

    // facing plate: four squares N E S W, the current one white, the others dim
    fill(out, facing, PLATE);
    let sq = FACING_SQUARE;
    let (fx0, fy0) = (facing.x0, facing.y0);
    let mid = (FACING_PLATE - sq) / 2;
    let squares = [
        Rect { x0: fx0 + mid, y0: fy0 + 2, x1: fx0 + mid + sq, y1: fy0 + 2 + sq },                          // N
        Rect { x0: fx0 + FACING_PLATE - 2 - sq, y0: fy0 + mid, x1: fx0 + FACING_PLATE - 2, y1: fy0 + mid + sq }, // E
        Rect { x0: fx0 + mid, y0: fy0 + FACING_PLATE - 2 - sq, x1: fx0 + mid + sq, y1: fy0 + FACING_PLATE - 2 }, // S
        Rect { x0: fx0 + 2, y0: fy0 + mid, x1: fx0 + 2 + sq, y1: fy0 + mid + sq },                          // W
    ];
    for (i, r) in squares.iter().enumerate() {
        fill(out, *r, if i as u8 == scene.facing { WHITE } else { DIM });
    }

    // minimap: a black border, the cells, the eye's cell white with a red tick on its facing side
    fill(out, map, BLACK);
    for z in 0..scene.rows {
        for x in 0..scene.w {
            let c = scene.cells[z * scene.w + x];
            let rgb = match c {
                b'#' => MAP_ROCK,
                b'<' => MAP_UP,
                b'>' => MAP_DOWN,
                _ => MAP_FLOOR,
            };
            let r = Rect {
                x0: map.x0 + MAP_BORDER + x * CELL_PX,
                y0: map.y0 + MAP_BORDER + z * CELL_PX,
                x1: map.x0 + MAP_BORDER + (x + 1) * CELL_PX,
                y1: map.y0 + MAP_BORDER + (z + 1) * CELL_PX,
            };
            fill(out, r, rgb);
        }
    }
    let ex = scene.pos_x as usize;
    let ez = scene.pos_z as usize;
    let eye = Rect {
        x0: map.x0 + MAP_BORDER + ex * CELL_PX,
        y0: map.y0 + MAP_BORDER + ez * CELL_PX,
        x1: map.x0 + MAP_BORDER + (ex + 1) * CELL_PX,
        y1: map.y0 + MAP_BORDER + (ez + 1) * CELL_PX,
    };
    fill(out, eye, MAP_EYE);
    let tick = match scene.facing {
        0 => Rect { x0: eye.x0, y0: eye.y0, x1: eye.x1, y1: eye.y0 + 1 },         // N: top edge
        1 => Rect { x0: eye.x1 - 1, y0: eye.y0, x1: eye.x1, y1: eye.y1 },         // E: right edge
        2 => Rect { x0: eye.x0, y0: eye.y1 - 1, x1: eye.x1, y1: eye.y1 },         // S: bottom edge
        _ => Rect { x0: eye.x0, y0: eye.y0, x1: eye.x0 + 1, y1: eye.y1 },         // W: left edge
    };
    fill(out, tick, MAP_TICK);
}

/// The overlay's own bytes: the overlay drawn onto a black canvas, then the region's pixels in raster order —
/// the HUD's identity, independent of the viewport underneath (a reticle's unpainted neighbours are black
/// here, not the wall behind them).
pub fn overlay_bytes(scene: &Scene, strips: &[Strip]) -> Vec<u8> {
    let mut canvas = vec![0u8; W * H * 3];
    overlay(scene, strips, &mut canvas);
    let rects = region(scene);
    let mut out = Vec::new();
    for y in 0..H {
        for x in 0..W {
            if in_region(&rects, x, y) {
                let o = (y * W + x) * 3;
                out.extend_from_slice(&canvas[o..o + 3]);
            }
        }
    }
    out
}

/// (inside, outside): pixels that differ between viewport and composite inside the region, and outside it.
/// The region law is `outside == 0`; a non-vacuous overlay has `inside > 0`.
pub fn region_audit(scene: &Scene, viewport: &[u8], composite: &[u8]) -> (usize, usize) {
    let rects = region(scene);
    let (mut inside, mut outside) = (0usize, 0usize);
    for y in 0..H {
        for x in 0..W {
            let o = (y * W + x) * 3;
            if viewport[o..o + 3] != composite[o..o + 3] {
                if in_region(&rects, x, y) {
                    inside += 1;
                } else {
                    outside += 1;
                }
            }
        }
    }
    (inside, outside)
}
