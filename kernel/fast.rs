// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/fast.rs — GAUNTLET-1: a SIBLING of the frozen emit, never `mantle.rs`.
//
// GAUNTLET-0 selected `emit` as the sole optimization target (emit at 695 permille of the instrumented render on
// host DANIELDILLBERG). GAUNTLET-1a seeded this file as an EXACT TRANSCRIPTION of `mantle::Scene::emit` so the
// differential equivalence court (`gauntlet1-equiv`) and the region measure existed and were proven before any
// candidate technique was inspected. The frozen `mantle.rs` is the correctness oracle; a candidate is guilty until
// its bytes agree with it, and the harness compares candidate -> frozen, never the reverse.
//
// This file holds the optimization STAIRCASE, each tread proven byte-identical to the frozen emit. LOCALITY-0
// LOCKED the blocked floor-tile layout as the accepted single-thread emit, so the promotion chain is now:
//   * `emit`          — LOCALITY-0 LOCKED (the accepted fast path): the GAUNTLET-1c row-major floor DDA with the
//                       floor tile fetched from the 8x8 BLOCKED execution format (`blocked_floor`, swizzled ONCE at
//                       scene load). Monomorphized to blocked — the floor index is `floor_blocked` (pure shift/mask,
//                       no runtime layout branch), the buffer is the pre-swizzled `floor`, never `scene.floor`.
//   * `emit_linear`   — GAUNTLET-1c ARCHIVED: the same row-major DDA fetching the floor from the canonical
//                       row-major `scene.floor` (the pre-LOCK linear layout). Retained VERBATIM as an immutable
//                       reference witness on the archive shelf — the fixed byte-identical target the historical
//                       courts (fast-bench, the probe/structure, the LINEAR anchor and DDA baseline) still measure.
//   * `emit_collapse` — GAUNTLET-1b: the floor divide-collapse (2 divides per floor pixel), a verbatim copy kept as
//                       the SAME-APPARATUS performance BASELINE the DDA was measured against — never the oracle.
// Correctness is mandatory and gate-enforced for ALL THREE (each byte-identical to frozen); speed is a second,
// separate court measured off-gate on a host. `mantle.rs` is untouched, and `emit`/`emit_linear`/`emit_collapse`
// call no probe (the RE-BREAKDOWN-1 fence).

use crate::mantle::{
    texel, u_axis_is_z, Scene, Strip, BANDS, CY, DOWN0, EYE_Y, FLOOR0, FOCAL, H, Q, T, U_SIGN, W, WALL0,
};

const TZ: usize = T as usize; // 256, the tile edge

/// The LOCKED floor-tile execution format (LOCALITY-0, blocked 8x8): the single definition of where texel (tj, ti)
/// lives in the cache-blocked layout — 8x8 blocks in row-major block order, texels row-major within a block. The
/// production `emit` fetches through it and `blocked_floor` fills through it, so the hot path and the scene-load
/// swizzle share ONE index (a divergence is impossible without a red gate). The court's
/// `locality::swizzle_index::<BLOCKED>` delegates here, so BLOCKED has exactly one definition repo-wide.
#[inline(always)]
fn floor_blocked(tj: i64, ti: i64) -> usize {
    let (tj, ti) = (tj as usize, ti as usize);
    (((tj >> 3) * (TZ >> 3)) + (ti >> 3)) * 64 + (tj & 7) * 8 + (ti & 7)
}

/// Ingest the canonical row-major floor tile and re-lay it into the LOCKED blocked execution format, ONCE (at
/// scene load, not per frame): the texel at (tj, ti) moves to `floor_blocked(tj, ti)`. A pure permutation — the
/// execution FORMAT — holding the same CONTENT as the input. `emit` reads the result; `scene.floor` is never
/// touched in the hot path again.
pub fn blocked_floor(floor: &[u8]) -> Vec<u8> {
    let mut out = vec![0u8; TZ * TZ * 3];
    for tj in 0..TZ {
        for ti in 0..TZ {
            let src = (tj * TZ + ti) * 3;
            let dst = floor_blocked(tj as i64, ti as i64) * 3;
            out[dst..dst + 3].copy_from_slice(&floor[src..src + 3]);
        }
    }
    out
}

/// LOCALITY-0 LOCKED — the accepted single-thread fast path: the GAUNTLET-1c row-major floor DDA with the floor
/// tile fetched from the 8x8 BLOCKED execution format (`blocked_floor`, built once at scene load). Blocked won the
/// LOCALITY-0 court byte-identical AND faster than the linear-fetch DDA (it carries the lower index-arithmetic tax
/// of the two layouts), so it is monomorphized here as production: the floor index is `floor_blocked` (pure
/// shift/mask, no runtime layout branch), and `floor` is the pre-swizzled buffer — `scene.floor` is never read in
/// the hot path. Ceiling + wall are the exact frozen transcription in a column-major pass.
///
/// Why row-major: at a fixed floor row `r`, `kk = 2(r-CY)+1` is constant, and (from `direction`) exactly one floor
/// axis is constant across columns while the other's numerator `D(c)` steps by `+/- 2*EYE_Y` per column. The frozen
/// (collapse) texel for the varying axis is `(e + D(c).div_euclid(kk)) & (T-1)`; tracking `(q, rem) =
/// (D.div_euclid(kk), D.rem_euclid(kk))` and advancing `D` by its constant step needs at most one correction — O(1)
/// per column, ~5 divides per ROW instead of 2 per floor pixel. Byte-identical to the frozen emit (`gauntlet1-equiv`,
/// `locality0-lock`); `buf` is read, never written, so the frame (and `frame_digest`) cannot move. The archived
/// linear-fetch form (the LOCALITY-0 reference witness and the historical courts' target) is `emit_linear`.
pub fn emit(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8], floor: &[u8]) {
    let ex = scene.pos_x * Q + EYE_Y;
    let ez = scene.pos_z * Q + EYE_Y;
    let table = &scene.table;
    // Pass 1 (column-major): ceiling + wall, exactly as the frozen emit (no floor here). Also find the highest
    // horizon (min bot) so the floor pass starts at the first row any column has floor.
    let mut min_bot = H as i64 - 1;
    for c in 0..W {
        let s = &strips[c];
        let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
        let mut along = if u_axis_is_z(s.face) { ez * td + tn * dz } else { ex * td + tn * dx };
        if U_SIGN[s.face as usize] < 0 {
            along = -along;
        }
        let u_d = Q * td;
        let u_n = along.rem_euclid(u_d);
        let ti = texel(u_n, u_d);
        let v_base = Q * td - EYE_Y * td - (2 * CY - 1) * tn;
        let v_den = Q * td;
        let top = s.top as usize;
        let bot = s.bot as usize;
        if s.bot < min_bot {
            min_bot = s.bot;
        }
        for r in 0..top {
            let idx = buf[r * W + c] as usize;
            let o = (r * W + c) * 3;
            out[o..o + 3].copy_from_slice(&table[idx * 3..idx * 3 + 3]);
        }
        for r in top..=bot {
            let idx = buf[r * W + c];
            let o = (r * W + c) * 3;
            if idx < WALL0 {
                let i = idx as usize;
                out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                continue;
            }
            let light = ((idx - WALL0) / (BANDS as u8)) as usize;
            let band = ((idx - WALL0) % (BANDS as u8)) as usize;
            let tj = texel(v_base + 2 * r as i64 * tn, v_den);
            let k = ((tj * T + ti) * 3) as usize;
            let tile = &scene.walls[light];
            let m = &scene.wall_map[band * 256..band * 256 + 256];
            out[o] = m[tile[k] as usize];
            out[o + 1] = m[tile[k + 1] as usize];
            out[o + 2] = m[tile[k + 2] as usize];
        }
    }
    // Pass 2 (row-major): the floor DDA. Per facing, one floor coordinate is constant across the row and the other
    // varies; `d0` / `d_const` are the varying axis's starting numerator (before *EYE_Y-less framing — see below)
    // and the constant axis's per-column direction component. The floor region of a column is exactly the pixels
    // whose frame index is in [FLOOR0, WALL0): floor bands (< DOWN0) take the texel, stair bands (>= DOWN0) a table
    // copy — the frozen floor loop's two cases. Ceiling/wall indices (< FLOOR0 or >= WALL0) are Pass 1's; skip them.
    let (varying_is_x, delta_pos, d0, d_const): (bool, bool, i64, i64) = match scene.facing {
        0 => (true, true, EYE_Y * (1 - W as i64), -2 * FOCAL),   // N: X varies (+2/col), Z constant (dz = -2*FOCAL)
        1 => (false, true, EYE_Y * (1 - W as i64), 2 * FOCAL),   // E: Z varies (+2/col), X constant (dx =  2*FOCAL)
        2 => (true, false, EYE_Y * (W as i64 - 1), 2 * FOCAL),   // S: X varies (-2/col), Z constant (dz =  2*FOCAL)
        _ => (false, false, EYE_Y * (W as i64 - 1), -2 * FOCAL), // W: Z varies (-2/col), X constant (dx = -2*FOCAL)
    };
    let e_const = if varying_is_x { ez } else { ex }; // constant axis is Z for N,S; X for E,W
    let e_vary = if varying_is_x { ex } else { ez }; // varying axis is X for N,S; Z for E,W
    let dconst_eye = d_const * EYE_Y;
    let step = 2 * EYE_Y; // D(c) steps by 2*EYE_Y per column (a = 2c+1-W steps by 2; D = EYE_Y * (+/-a))
    for r in ((min_bot + 1) as usize)..H {
        let kk = 2 * (r as i64 - CY) + 1;
        let cconst = (e_const + dconst_eye.div_euclid(kk)) & (T - 1);
        let a_step = step.div_euclid(kk);
        let b_step = step.rem_euclid(kk);
        let mut q = d0.div_euclid(kk);
        let mut rem = d0.rem_euclid(kk);
        let row = r * W;
        for c in 0..W {
            let idx = buf[row + c];
            if idx >= FLOOR0 && idx < WALL0 {
                let o = (row + c) * 3;
                if idx < DOWN0 {
                    let vary = (e_vary + q) & (T - 1);
                    let (tj, ti_f) = if varying_is_x { (cconst, vary) } else { (vary, cconst) };
                    let kf = floor_blocked(tj, ti_f) * 3;
                    let band = (idx - FLOOR0) as usize;
                    let m = &scene.floor_map[band * 256..band * 256 + 256];
                    out[o] = m[floor[kf] as usize];
                    out[o + 1] = m[floor[kf + 1] as usize];
                    out[o + 2] = m[floor[kf + 2] as usize];
                } else {
                    // a down/up stair band in the floor region: a table copy, as the frozen floor loop does
                    let i = idx as usize;
                    out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                }
            }
            // advance the DDA every column (q is a pure function of c and kk, valid whether or not we wrote)
            if delta_pos {
                q += a_step;
                rem += b_step;
                if rem >= kk {
                    rem -= kk;
                    q += 1;
                }
            } else {
                q -= a_step;
                rem -= b_step;
                if rem < 0 {
                    rem += kk;
                    q -= 1;
                }
            }
        }
    }
}

/// GAUNTLET-1c ARCHIVED — the row-major floor DDA fetching the floor from the canonical row-major `scene.floor`
/// (the pre-LOCK LINEAR layout). This is the accepted fast path's predecessor: LOCALITY-0 LOCKED the blocked-layout
/// form (`emit`), and this linear-fetch form is retained VERBATIM on the archive shelf beside `emit_collapse` as an
/// immutable REFERENCE WITNESS. It stays byte-identical to the frozen emit (`locality0-lock`), so the historical
/// courts that measured the linear DDA keep a fixed target and the LOCK's blocked win stays reproducible against it:
/// the GAUNTLET-1c fast-bench times it as "the DDA", RE-BREAKDOWN-1's ablation and structure courts verify against
/// it, and LOCALITY-0's LINEAR anchor and DDA baseline are it. Not the production path (that is `emit`, blocked);
/// never promoted, never edited for speed. `buf` is read, never written.
pub fn emit_linear(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8]) {
    let ex = scene.pos_x * Q + EYE_Y;
    let ez = scene.pos_z * Q + EYE_Y;
    let table = &scene.table;
    let mut min_bot = H as i64 - 1;
    for c in 0..W {
        let s = &strips[c];
        let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
        let mut along = if u_axis_is_z(s.face) { ez * td + tn * dz } else { ex * td + tn * dx };
        if U_SIGN[s.face as usize] < 0 {
            along = -along;
        }
        let u_d = Q * td;
        let u_n = along.rem_euclid(u_d);
        let ti = texel(u_n, u_d);
        let v_base = Q * td - EYE_Y * td - (2 * CY - 1) * tn;
        let v_den = Q * td;
        let top = s.top as usize;
        let bot = s.bot as usize;
        if s.bot < min_bot {
            min_bot = s.bot;
        }
        for r in 0..top {
            let idx = buf[r * W + c] as usize;
            let o = (r * W + c) * 3;
            out[o..o + 3].copy_from_slice(&table[idx * 3..idx * 3 + 3]);
        }
        for r in top..=bot {
            let idx = buf[r * W + c];
            let o = (r * W + c) * 3;
            if idx < WALL0 {
                let i = idx as usize;
                out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                continue;
            }
            let light = ((idx - WALL0) / (BANDS as u8)) as usize;
            let band = ((idx - WALL0) % (BANDS as u8)) as usize;
            let tj = texel(v_base + 2 * r as i64 * tn, v_den);
            let k = ((tj * T + ti) * 3) as usize;
            let tile = &scene.walls[light];
            let m = &scene.wall_map[band * 256..band * 256 + 256];
            out[o] = m[tile[k] as usize];
            out[o + 1] = m[tile[k + 1] as usize];
            out[o + 2] = m[tile[k + 2] as usize];
        }
    }
    let (varying_is_x, delta_pos, d0, d_const): (bool, bool, i64, i64) = match scene.facing {
        0 => (true, true, EYE_Y * (1 - W as i64), -2 * FOCAL),
        1 => (false, true, EYE_Y * (1 - W as i64), 2 * FOCAL),
        2 => (true, false, EYE_Y * (W as i64 - 1), 2 * FOCAL),
        _ => (false, false, EYE_Y * (W as i64 - 1), -2 * FOCAL),
    };
    let e_const = if varying_is_x { ez } else { ex };
    let e_vary = if varying_is_x { ex } else { ez };
    let dconst_eye = d_const * EYE_Y;
    let step = 2 * EYE_Y;
    let tile = &scene.floor;
    for r in ((min_bot + 1) as usize)..H {
        let kk = 2 * (r as i64 - CY) + 1;
        let cconst = (e_const + dconst_eye.div_euclid(kk)) & (T - 1);
        let a_step = step.div_euclid(kk);
        let b_step = step.rem_euclid(kk);
        let mut q = d0.div_euclid(kk);
        let mut rem = d0.rem_euclid(kk);
        let row = r * W;
        for c in 0..W {
            let idx = buf[row + c];
            if idx >= FLOOR0 && idx < WALL0 {
                let o = (row + c) * 3;
                if idx < DOWN0 {
                    let vary = (e_vary + q) & (T - 1);
                    let (tj, ti_f) = if varying_is_x { (cconst, vary) } else { (vary, cconst) };
                    let k = ((tj * T + ti_f) * 3) as usize;
                    let band = (idx - FLOOR0) as usize;
                    let m = &scene.floor_map[band * 256..band * 256 + 256];
                    out[o] = m[tile[k] as usize];
                    out[o + 1] = m[tile[k + 1] as usize];
                    out[o + 2] = m[tile[k + 2] as usize];
                } else {
                    let i = idx as usize;
                    out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                }
            }
            if delta_pos {
                q += a_step;
                rem += b_step;
                if rem >= kk {
                    rem -= kk;
                    q += 1;
                }
            } else {
                q -= a_step;
                rem -= b_step;
                if rem < 0 {
                    rem += kk;
                    q -= 1;
                }
            }
        }
    }
}

/// GAUNTLET-1b — the floor divide-collapse, kept VERBATIM as the same-apparatus performance BASELINE the DDA is
/// measured against (it is not the oracle; `mantle.rs` is). Ceiling and wall are the exact transcription; the floor
/// does one `div_euclid` per coordinate (2 divides per floor pixel) instead of the frozen four. Proven byte-identical
/// to the frozen emit by `gauntlet1b-reduction`, so the baseline stays pinned to the oracle and cannot silently drift.
pub fn emit_collapse(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8]) {
    let ex = scene.pos_x * Q + EYE_Y;
    let ez = scene.pos_z * Q + EYE_Y;
    let table = &scene.table;
    for c in 0..W {
        let s = &strips[c];
        let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
        let mut along = if u_axis_is_z(s.face) { ez * td + tn * dz } else { ex * td + tn * dx };
        if U_SIGN[s.face as usize] < 0 {
            along = -along;
        }
        let u_d = Q * td;
        let u_n = along.rem_euclid(u_d);
        let ti = texel(u_n, u_d);
        let v_base = Q * td - EYE_Y * td - (2 * CY - 1) * tn;
        let v_den = Q * td;
        let top = s.top as usize;
        let bot = s.bot as usize;
        for r in 0..top {
            let idx = buf[r * W + c] as usize;
            let o = (r * W + c) * 3;
            out[o..o + 3].copy_from_slice(&table[idx * 3..idx * 3 + 3]);
        }
        for r in top..=bot {
            let idx = buf[r * W + c];
            let o = (r * W + c) * 3;
            if idx < WALL0 {
                let i = idx as usize;
                out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                continue;
            }
            let light = ((idx - WALL0) / (BANDS as u8)) as usize;
            let band = ((idx - WALL0) % (BANDS as u8)) as usize;
            let tj = texel(v_base + 2 * r as i64 * tn, v_den);
            let k = ((tj * T + ti) * 3) as usize;
            let tile = &scene.walls[light];
            let m = &scene.wall_map[band * 256..band * 256 + 256];
            out[o] = m[tile[k] as usize];
            out[o + 1] = m[tile[k + 1] as usize];
            out[o + 2] = m[tile[k + 2] as usize];
        }
        // the GAUNTLET-1b collapse: (e + (d*EYE_Y).div_euclid(kk)) & (T-1), the d*EYE_Y hoisted per column
        let dz_eye = dz * EYE_Y;
        let dx_eye = dx * EYE_Y;
        for r in (bot + 1)..H {
            let idx = buf[r * W + c];
            let o = (r * W + c) * 3;
            if idx < FLOOR0 || idx >= DOWN0 {
                let i = idx as usize;
                out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                continue;
            }
            let kk = 2 * (r as i64 - CY) + 1;
            let tj = (ez + dz_eye.div_euclid(kk)) & (T - 1);
            let ti_f = (ex + dx_eye.div_euclid(kk)) & (T - 1);
            let k = ((tj * T + ti_f) * 3) as usize;
            let band = (idx - FLOOR0) as usize;
            let m = &scene.floor_map[band * 256..band * 256 + 256];
            let tile = &scene.floor;
            out[o] = m[tile[k] as usize];
            out[o + 1] = m[tile[k + 1] as usize];
            out[o + 2] = m[tile[k + 2] as usize];
        }
    }
}

/// The GAUNTLET-1a region measure, DETERMINISTIC (so the gate computes it byte-identically, no host timing):
/// count the pixels that take each of emit's three branches, mirroring the frozen branch logic exactly (region
/// by top/bot, then the idx test). The per-source divide cost is read off the source mechanism: ceiling/table = 0;
/// a textured wall pixel = 1 (one `texel`); a textured FLOOR pixel = 4 in the FROZEN emit (two `texel`, each a
/// `rem_euclid` + a `div_euclid`) and 2 in the GAUNTLET-1b collapse (one `div_euclid` per coordinate). Returns
/// (wall_textured_px, floor_textured_px, table_px); `main.rs --fast` reads the frozen baseline (wall + 4*floor) and
/// the collapse (wall + 2*floor) off these counts. GAUNTLET-1c's DDA is per-ROW, not per-pixel — see `floor_rows`.
pub fn region_divides(strips: &[Strip], buf: &[u8]) -> (usize, usize, usize) {
    let (mut wall_tex, mut floor_tex, mut table_px) = (0usize, 0usize, 0usize);
    for c in 0..W {
        let s = &strips[c];
        let top = s.top as usize;
        let bot = s.bot as usize;
        table_px += top; // ceiling rows are always a table copy
        for r in top..=bot {
            let idx = buf[r * W + c];
            if idx < WALL0 {
                table_px += 1;
            } else {
                wall_tex += 1;
            }
        }
        for r in (bot + 1)..H {
            let idx = buf[r * W + c];
            if idx < FLOOR0 || idx >= DOWN0 {
                table_px += 1;
            } else {
                floor_tex += 1;
            }
        }
    }
    (wall_tex, floor_tex, table_px)
}

/// The number of rows the GAUNTLET-1c floor DDA processes: `H - 1 - min_c(bot)`, i.e. the count of image rows that
/// contain at least one floor-region pixel (the floor region of every column is contiguous down to `H`, so their
/// union is the contiguous band `[min_bot+1, H)`). The DDA does a bounded number of divides PER such row (the two
/// step constants, the constant-axis texel, and the row's starting `(q, rem)` — 5 `div_euclid`/`rem_euclid` ops),
/// so its floor divide-work is `5 * floor_rows`, against the collapse's `2 * floor_textured_px`.
pub fn floor_rows(strips: &[Strip]) -> usize {
    let mut min_bot = H as i64 - 1;
    for s in strips.iter().take(W) {
        if s.bot < min_bot {
            min_bot = s.bot;
        }
    }
    (H as i64 - 1 - min_bot).max(0) as usize
}

/// RE-BREAKDOWN-1 — Court A: the DETERMINISTIC structural attribution (gate-computed, wall-clock-free). What work
/// exists in `emit`, read off the frozen frame: divide-work (wall 1/px + floor DDA 5/row), the tile/map memory reads
/// (3 texels + 3 map indirections per textured pixel), the tile working-set cardinality (distinct texel addresses),
/// the floor's adjacent-column texel-stride locality (the fraction within a 64-byte cache line — where the DDA's
/// near-horizon stride is benign or pathological), and a coverage proof that every framebuffer pixel is written
/// exactly once. Names candidates; it is a proxy for time, not time (Court B is the wall-clock).
pub struct Structure {
    pub wall_tex: usize,
    pub floor_tex: usize,
    pub divides: usize,       // wall_tex (1/px) + 5 * floor_rows (the DDA's per-row divides)
    pub tile_reads: usize,    // 3 per textured pixel (the big tile texture fetches)
    pub map_reads: usize,     // 3 per textured pixel (the 256-byte band-map indirections)
    pub ws_floor: usize,      // distinct floor texel addresses k (the floor working set)
    pub ws_wall: usize,       // distinct wall texel addresses k (the wall working set)
    pub floor_adj: usize,     // adjacent same-row floor texel pairs sampled
    pub floor_local: usize,   // of those, |Δk| <= 64 (within a cache line)
    pub writes: usize,        // total framebuffer pixels written (coverage sum)
    pub writes_once: bool,    // every framebuffer pixel written exactly once
}

pub fn structure(scene: &Scene, strips: &[Strip], buf: &[u8]) -> Structure {
    use std::collections::HashSet;
    let ex = scene.pos_x * Q + EYE_Y;
    let ez = scene.pos_z * Q + EYE_Y;
    let (mut wall_tex, mut floor_tex) = (0usize, 0usize);
    let mut ws_wall: HashSet<usize> = HashSet::new();
    let mut ws_floor: HashSet<usize> = HashSet::new();
    let (mut floor_adj, mut floor_local) = (0usize, 0usize);
    let mut cover = vec![0u8; W * H];
    // wall texel addresses (column-major, mirroring emit's wall pass)
    for c in 0..W {
        let s = &strips[c];
        let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
        let mut along = if u_axis_is_z(s.face) { ez * td + tn * dz } else { ex * td + tn * dx };
        if U_SIGN[s.face as usize] < 0 {
            along = -along;
        }
        let u_d = Q * td;
        let ti = texel(along.rem_euclid(u_d), u_d);
        let v_base = Q * td - EYE_Y * td - (2 * CY - 1) * tn;
        let v_den = Q * td;
        let top = s.top as usize;
        let bot = s.bot as usize;
        for r in 0..top {
            cover[r * W + c] += 1;
        }
        for r in top..=bot {
            cover[r * W + c] += 1;
            let idx = buf[r * W + c];
            if idx >= WALL0 {
                wall_tex += 1;
                let tj = texel(v_base + 2 * r as i64 * tn, v_den);
                ws_wall.insert(((tj * T + ti) * 3) as usize);
            }
        }
    }
    // floor texel addresses (row-major, mirroring the DDA; the collapse formula gives the same k, off the hot path)
    for r_us in 0..H {
        let r = r_us as i64;
        let kk = 2 * (r - CY) + 1;
        let mut prev: Option<(usize, usize)> = None; // (column, k) of the previous floor pixel in this row
        for c in 0..W {
            let s = &strips[c];
            if r_us <= s.bot as usize {
                continue; // wall/ceiling region — Pass 1's, already covered above
            }
            cover[r_us * W + c] += 1;
            let idx = buf[r_us * W + c];
            if idx < FLOOR0 || idx >= DOWN0 {
                prev = None;
                continue; // stair band: a table copy, not a floor texel
            }
            floor_tex += 1;
            let tj = (ez + (s.dz * EYE_Y).div_euclid(kk)) & (T - 1);
            let ti_f = (ex + (s.dx * EYE_Y).div_euclid(kk)) & (T - 1);
            let k = ((tj * T + ti_f) * 3) as usize;
            ws_floor.insert(k);
            if let Some((pc, pk)) = prev {
                if pc + 1 == c {
                    floor_adj += 1;
                    if (k as i64 - pk as i64).abs() <= 64 {
                        floor_local += 1;
                    }
                }
            }
            prev = Some((c, k));
        }
    }
    let writes: usize = cover.iter().map(|&v| v as usize).sum();
    let writes_once = cover.iter().all(|&v| v == 1);
    Structure {
        wall_tex,
        floor_tex,
        divides: wall_tex + 5 * floor_rows(strips),
        tile_reads: 3 * (wall_tex + floor_tex),
        map_reads: 3 * (wall_tex + floor_tex),
        ws_floor: ws_floor.len(),
        ws_wall: ws_wall.len(),
        floor_adj,
        floor_local,
        writes,
        writes_once,
    }
}

/// RE-BREAKDOWN-1 — Court B: the fenced ablation-probe apparatus. NOT a renderer: `probe` is measurement scaffold,
/// isolated from the promotion chain (the production `emit` never calls it; a gate row asserts so). `emit_probe`
/// is a faithful copy of the DDA `emit`, `const MODE`-gated so each build does a nested SUBSET of the per-pixel
/// textured work, with ONE `black_box`-fed anchor per pixel in every mode (RE-BREAKDOWN-1b: constant tax that
/// cancels in the increments — see `anchor_of`) so the optimizer cannot elide the very thing being timed:
///   ADDR    — classify + coordinate/DDA arithmetic, then a CONSTANT store (no memory fetch)
///   LOOKUP  — ADDR + the tile texel fetches (the big-texture memory reads), CONSTANT store
///   FULL    — LOOKUP + the band-map indirection/assembly, CONSTANT store (the negative control's work)
///   VERIFY  — FULL's work + the REAL store: byte-identical to `emit` (gate-proven), so the probe path is
///             demonstrably the intended subset of the certified path, auditable rather than asserted.
/// The host deltas (LOOKUP−ADDR, FULL−LOOKUP) are INCREMENTAL wall-clock attribution under controlled ablation —
/// not pure hardware-resource costs (cache/branch/scheduling make the subtraction non-additive).
pub mod probe {
    use super::*;
    use std::hint::black_box;

    pub const ADDR: u8 = 0;
    pub const LOOKUP: u8 = 1;
    pub const FULL: u8 = 2;
    pub const VERIFY: u8 = 3;

    /// RE-BREAKDOWN-1b: every mode produces THREE bytes and folds them with the IDENTICAL combine, so the anchor's
    /// arithmetic tax is constant across modes and cancels exactly in the increments; only the memory work being
    /// measured differs. ADDR folds three bytes of the address `k` (forces the coordinate arithmetic, no fetch);
    /// LOOKUP folds the three tile texel bytes (forces the tile-texture read); FULL/VERIFY fold the three band-map
    /// results `m[tile[k]]` (forces the map indirection, and returns them as the pixel `rr,gg,bb`). Thus
    /// LOOKUP−ADDR is the tile fetch alone and FULL−LOOKUP the map indirection alone — the combine cancels. The 1a
    /// probe accumulated 1/2/3 values by depth, so its tax grew with the mode and contaminated the deltas; this does not.
    #[inline(always)]
    fn anchor_of<const MODE: u8>(tile: &[u8], m: &[u8], k: usize, rr: &mut u8, gg: &mut u8, bb: &mut u8) -> u64 {
        let (b0, b1, b2): (u8, u8, u8) = if MODE == ADDR {
            (k as u8, (k >> 8) as u8, (k >> 16) as u8)
        } else {
            let (t0, t1, t2) = (tile[k], tile[k + 1], tile[k + 2]);
            if MODE == LOOKUP {
                (t0, t1, t2)
            } else {
                *rr = m[t0 as usize];
                *gg = m[t1 as usize];
                *bb = m[t2 as usize];
                (*rr, *gg, *bb)
            }
        };
        b0 as u64 ^ ((b1 as u64) << 8) ^ ((b2 as u64) << 16)
    }

    pub fn emit_probe<const MODE: u8>(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8]) {
        let ex = scene.pos_x * Q + EYE_Y;
        let ez = scene.pos_z * Q + EYE_Y;
        let table = &scene.table;
        let mut acc: u64 = 0;
        let mut min_bot = H as i64 - 1;
        for c in 0..W {
            let s = &strips[c];
            let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
            let mut along = if u_axis_is_z(s.face) { ez * td + tn * dz } else { ex * td + tn * dx };
            if U_SIGN[s.face as usize] < 0 {
                along = -along;
            }
            let u_d = Q * td;
            let ti = texel(along.rem_euclid(u_d), u_d);
            let v_base = Q * td - EYE_Y * td - (2 * CY - 1) * tn;
            let v_den = Q * td;
            let top = s.top as usize;
            let bot = s.bot as usize;
            if s.bot < min_bot {
                min_bot = s.bot;
            }
            for r in 0..top {
                // a ceiling table copy: identical in every mode (cancels in the deltas), so it is never gated
                let idx = buf[r * W + c] as usize;
                let o = (r * W + c) * 3;
                out[o..o + 3].copy_from_slice(&table[idx * 3..idx * 3 + 3]);
            }
            for r in top..=bot {
                let idx = buf[r * W + c];
                let o = (r * W + c) * 3;
                if idx < WALL0 {
                    out[o..o + 3].copy_from_slice(&table[idx as usize * 3..idx as usize * 3 + 3]);
                    continue;
                }
                let light = ((idx - WALL0) / (BANDS as u8)) as usize;
                let band = ((idx - WALL0) % (BANDS as u8)) as usize;
                let tj = texel(v_base + 2 * r as i64 * tn, v_den);
                let k = ((tj * T + ti) * 3) as usize;
                let tile = &scene.walls[light];
                let m = &scene.wall_map[band * 256..band * 256 + 256];
                let (mut rr, mut gg, mut bb) = (0u8, 0u8, 0u8);
                let anchor = anchor_of::<MODE>(tile, m, k, &mut rr, &mut gg, &mut bb);
                acc = acc.wrapping_add(anchor);
                if MODE == VERIFY {
                    out[o] = rr;
                    out[o + 1] = gg;
                    out[o + 2] = bb;
                } else {
                    out[o] = 0;
                    out[o + 1] = 0;
                    out[o + 2] = 0;
                }
            }
        }
        // Pass 2: the floor DDA, mode-gated exactly as the wall pass
        let (varying_is_x, delta_pos, d0, d_const): (bool, bool, i64, i64) = match scene.facing {
            0 => (true, true, EYE_Y * (1 - W as i64), -2 * FOCAL),
            1 => (false, true, EYE_Y * (1 - W as i64), 2 * FOCAL),
            2 => (true, false, EYE_Y * (W as i64 - 1), 2 * FOCAL),
            _ => (false, false, EYE_Y * (W as i64 - 1), -2 * FOCAL),
        };
        let e_const = if varying_is_x { ez } else { ex };
        let e_vary = if varying_is_x { ex } else { ez };
        let dconst_eye = d_const * EYE_Y;
        let step = 2 * EYE_Y;
        let tile = &scene.floor;
        for r in ((min_bot + 1) as usize)..H {
            let kk = 2 * (r as i64 - CY) + 1;
            let cconst = (e_const + dconst_eye.div_euclid(kk)) & (T - 1);
            let a_step = step.div_euclid(kk);
            let b_step = step.rem_euclid(kk);
            let mut q = d0.div_euclid(kk);
            let mut rem = d0.rem_euclid(kk);
            let row = r * W;
            for c in 0..W {
                let idx = buf[row + c];
                if idx >= FLOOR0 && idx < WALL0 {
                    let o = (row + c) * 3;
                    if idx < DOWN0 {
                        let vary = (e_vary + q) & (T - 1);
                        let (tj, ti_f) = if varying_is_x { (cconst, vary) } else { (vary, cconst) };
                        let k = ((tj * T + ti_f) * 3) as usize;
                        let band = (idx - FLOOR0) as usize;
                        let m = &scene.floor_map[band * 256..band * 256 + 256];
                        let (mut rr, mut gg, mut bb) = (0u8, 0u8, 0u8);
                        let anchor = anchor_of::<MODE>(tile, m, k, &mut rr, &mut gg, &mut bb);
                        acc = acc.wrapping_add(anchor);
                        if MODE == VERIFY {
                            out[o] = rr;
                            out[o + 1] = gg;
                            out[o + 2] = bb;
                        } else {
                            out[o] = 0;
                            out[o + 1] = 0;
                            out[o + 2] = 0;
                        }
                    } else {
                        // a down/up stair band: a table copy, identical in every mode
                        let i = idx as usize;
                        out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                    }
                }
                if delta_pos {
                    q += a_step;
                    rem += b_step;
                    if rem >= kk {
                        rem -= kk;
                        q += 1;
                    }
                } else {
                    q -= a_step;
                    rem -= b_step;
                    if rem < 0 {
                        rem += kk;
                        q -= 1;
                    }
                }
            }
        }
        black_box(acc); // anchor the ablated work so the optimizer cannot elide what we are timing
    }
}

/// LOCALITY-0 — the floor-tile execution-format court. The frozen `mantle.rs` and the accepted DDA `fast::emit`
/// stay untouched; this is a fast-path apparatus that fetches the FLOOR tile from a re-laid-out copy (the execution
/// FORMAT) holding the same texel values (the CONTENT provenance). Two layouts compete, each a lossless bijection
/// proven byte-identical to the frozen emit: BLOCKED (8×8 cache blocks, cheap shift/mask index) and MORTON (Z-order
/// space-filling curve, portable scalar bit-interleave). LINEAR is the identity (reproduces `fast::emit`), the
/// apparatus anchor. Per the Epistemic-Invariance theorem, the variants are hot-swapped at the binary boundary and
/// timed process-isolated; here we provide the byte-identical renderer, the bijection, and the per-band instruments.
pub mod locality {
    use super::*;
    use std::hint::black_box;

    pub const LINEAR: u8 = 0;
    pub const BLOCKED: u8 = 1;
    pub const MORTON: u8 = 2;
    pub const FULL: u8 = 0; // MODE: the real fetch + store (byte-identical)
    pub const ADDR: u8 = 1; // MODE: the floor index math only, anchored — the arithmetic tax X
    // TZ (the tile edge) is the production `super::TZ`; the court's BLOCKED index delegates to `super::floor_blocked`.

    #[inline(always)]
    fn spread8(v: usize) -> usize {
        // Part1By1 (8-bit): insert a zero between each low bit, for the Morton interleave
        let mut v = v & 0xFF;
        v = (v | (v << 4)) & 0x0F0F;
        v = (v | (v << 2)) & 0x3333;
        v = (v | (v << 1)) & 0x5555;
        v
    }

    /// The tile texel index (0..T*T) for coordinate (tj, ti) under LAYOUT. LINEAR is the frozen row-major order
    /// (identity); BLOCKED is 8×8 cache blocks (shifts + masks); MORTON is the Z-order curve (scalar interleave,
    /// portable so byte-identity holds on any host). All three are bijections on [0, T*T) (row: locality0-bijection).
    #[inline(always)]
    pub fn swizzle_index<const LAYOUT: u8>(tj: i64, ti: i64) -> usize {
        if LAYOUT == BLOCKED {
            // the LOCKED blocked layout has ONE definition repo-wide: the production `super::floor_blocked`, so the
            // court apparatus and the promoted `emit` can never disagree on where a blocked texel lives.
            super::floor_blocked(tj, ti)
        } else if LAYOUT == MORTON {
            let (tj, ti) = (tj as usize, ti as usize);
            spread8(ti) | (spread8(tj) << 1)
        } else {
            let (tj, ti) = (tj as usize, ti as usize);
            tj * TZ + ti
        }
    }

    /// A LAYOUT copy of the canonical row-major floor tile: the texel at (tj, ti) moves to swizzle_index(tj, ti). A
    /// pure permutation — the execution FORMAT — holding the same CONTENT as the input. LINEAR returns a copy.
    pub fn swizzle_tile<const LAYOUT: u8>(tile: &[u8]) -> Vec<u8> {
        let mut out = vec![0u8; TZ * TZ * 3];
        for tj in 0..TZ {
            for ti in 0..TZ {
                let src = (tj * TZ + ti) * 3;
                let dst = swizzle_index::<LAYOUT>(tj as i64, ti as i64) * 3;
                out[dst..dst + 3].copy_from_slice(&tile[src..src + 3]);
            }
        }
        out
    }

    /// The inverse permutation: reconstruct the canonical tile from a LAYOUT-swizzled one. The witness
    /// `unswizzle_tile(swizzle_tile(t)) == t` proves the format transform is lossless (row: locality0-bijection).
    pub fn unswizzle_tile<const LAYOUT: u8>(sw: &[u8]) -> Vec<u8> {
        let mut out = vec![0u8; TZ * TZ * 3];
        for tj in 0..TZ {
            for ti in 0..TZ {
                let dst = (tj * TZ + ti) * 3;
                let src = swizzle_index::<LAYOUT>(tj as i64, ti as i64) * 3;
                out[dst..dst + 3].copy_from_slice(&sw[src..src + 3]);
            }
        }
        out
    }

    /// facing -> (varying_is_x, delta_pos, d0, d_const), the GAUNTLET-1c floor DDA parameters (shared).
    #[inline(always)]
    fn dda_params(facing: u8) -> (bool, bool, i64, i64) {
        match facing {
            0 => (true, true, EYE_Y * (1 - W as i64), -2 * FOCAL),
            1 => (false, true, EYE_Y * (1 - W as i64), 2 * FOCAL),
            2 => (true, false, EYE_Y * (W as i64 - 1), 2 * FOCAL),
            _ => (false, false, EYE_Y * (W as i64 - 1), -2 * FOCAL),
        }
    }

    /// The GAUNTLET-1c DDA emit with the FLOOR tile fetched from `floor_buf` at `swizzle_index::<LAYOUT>` — the
    /// LOCALITY-0 candidate renderer. LAYOUT=LINEAR + floor_buf=scene.floor reproduces `fast::emit` byte-for-byte
    /// (the apparatus anchor). Ceiling and wall are the frozen transcription (not swizzled). Byte-identity is proven
    /// by locality0-equiv; `buf` is read-only so the frame cannot move.
    pub fn emit_swizzled<const LAYOUT: u8>(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8], floor_buf: &[u8]) {
        let ex = scene.pos_x * Q + EYE_Y;
        let ez = scene.pos_z * Q + EYE_Y;
        let table = &scene.table;
        let mut min_bot = H as i64 - 1;
        for c in 0..W {
            let s = &strips[c];
            let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
            let mut along = if u_axis_is_z(s.face) { ez * td + tn * dz } else { ex * td + tn * dx };
            if U_SIGN[s.face as usize] < 0 {
                along = -along;
            }
            let u_d = Q * td;
            let ti = texel(along.rem_euclid(u_d), u_d);
            let v_base = Q * td - EYE_Y * td - (2 * CY - 1) * tn;
            let v_den = Q * td;
            let top = s.top as usize;
            let bot = s.bot as usize;
            if s.bot < min_bot {
                min_bot = s.bot;
            }
            for r in 0..top {
                let idx = buf[r * W + c] as usize;
                let o = (r * W + c) * 3;
                out[o..o + 3].copy_from_slice(&table[idx * 3..idx * 3 + 3]);
            }
            for r in top..=bot {
                let idx = buf[r * W + c];
                let o = (r * W + c) * 3;
                if idx < WALL0 {
                    out[o..o + 3].copy_from_slice(&table[idx as usize * 3..idx as usize * 3 + 3]);
                    continue;
                }
                let light = ((idx - WALL0) / (BANDS as u8)) as usize;
                let band = ((idx - WALL0) % (BANDS as u8)) as usize;
                let tj = texel(v_base + 2 * r as i64 * tn, v_den);
                let k = ((tj * T + ti) * 3) as usize;
                let tile = &scene.walls[light];
                let m = &scene.wall_map[band * 256..band * 256 + 256];
                out[o] = m[tile[k] as usize];
                out[o + 1] = m[tile[k + 1] as usize];
                out[o + 2] = m[tile[k + 2] as usize];
            }
        }
        let (varying_is_x, delta_pos, d0, d_const) = dda_params(scene.facing);
        let e_const = if varying_is_x { ez } else { ex };
        let e_vary = if varying_is_x { ex } else { ez };
        let dconst_eye = d_const * EYE_Y;
        let step = 2 * EYE_Y;
        for r in ((min_bot + 1) as usize)..H {
            let kk = 2 * (r as i64 - CY) + 1;
            let cconst = (e_const + dconst_eye.div_euclid(kk)) & (T - 1);
            let a_step = step.div_euclid(kk);
            let b_step = step.rem_euclid(kk);
            let mut q = d0.div_euclid(kk);
            let mut rem = d0.rem_euclid(kk);
            let row = r * W;
            for c in 0..W {
                let idx = buf[row + c];
                if idx >= FLOOR0 && idx < WALL0 {
                    let o = (row + c) * 3;
                    if idx < DOWN0 {
                        let vary = (e_vary + q) & (T - 1);
                        let (tj, ti_f) = if varying_is_x { (cconst, vary) } else { (vary, cconst) };
                        let kf = swizzle_index::<LAYOUT>(tj, ti_f) * 3;
                        let band = (idx - FLOOR0) as usize;
                        let m = &scene.floor_map[band * 256..band * 256 + 256];
                        out[o] = m[floor_buf[kf] as usize];
                        out[o + 1] = m[floor_buf[kf + 1] as usize];
                        out[o + 2] = m[floor_buf[kf + 2] as usize];
                    } else {
                        let i = idx as usize;
                        out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                    }
                }
                if delta_pos {
                    q += a_step;
                    rem += b_step;
                    if rem >= kk {
                        rem -= kk;
                        q += 1;
                    }
                } else {
                    q -= a_step;
                    rem -= b_step;
                    if rem < 0 {
                        rem += kk;
                        q -= 1;
                    }
                }
            }
        }
    }

    /// The floor-only band instrument: the DDA floor pass over rows [r_lo, r_hi) ONLY, for per-band host timing (the
    /// mid-field shear question). MODE=FULL does the real swizzled fetch + store; MODE=ADDR does the floor index math
    /// only, one constant anchor per pixel (RE-BREAKDOWN-1b discipline) + a constant store — so ADDR(variant) −
    /// ADDR(LINEAR) is the index-arithmetic tax X on that band. Not a renderer: a timing probe (a differing pixel is
    /// expected). Ceiling/wall are never touched here, so the band delta is the floor's alone.
    pub fn floor_bench<const LAYOUT: u8, const MODE: u8>(
        scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8], floor_buf: &[u8], r_lo: usize, r_hi: usize,
    ) {
        let ex = scene.pos_x * Q + EYE_Y;
        let ez = scene.pos_z * Q + EYE_Y;
        let mut min_bot = H as i64 - 1;
        for s in strips.iter().take(W) {
            if s.bot < min_bot {
                min_bot = s.bot;
            }
        }
        let (varying_is_x, delta_pos, d0, d_const) = dda_params(scene.facing);
        let e_const = if varying_is_x { ez } else { ex };
        let e_vary = if varying_is_x { ex } else { ez };
        let dconst_eye = d_const * EYE_Y;
        let step = 2 * EYE_Y;
        let lo = r_lo.max((min_bot + 1) as usize);
        let hi = r_hi.min(H);
        let mut acc: u64 = 0;
        for r in lo..hi {
            let kk = 2 * (r as i64 - CY) + 1;
            let cconst = (e_const + dconst_eye.div_euclid(kk)) & (T - 1);
            let a_step = step.div_euclid(kk);
            let b_step = step.rem_euclid(kk);
            let mut q = d0.div_euclid(kk);
            let mut rem = d0.rem_euclid(kk);
            let row = r * W;
            for c in 0..W {
                let idx = buf[row + c];
                if idx >= FLOOR0 && idx < DOWN0 {
                    let o = (row + c) * 3;
                    let vary = (e_vary + q) & (T - 1);
                    let (tj, ti_f) = if varying_is_x { (cconst, vary) } else { (vary, cconst) };
                    let kf = swizzle_index::<LAYOUT>(tj, ti_f) * 3;
                    if MODE == FULL {
                        let band = (idx - FLOOR0) as usize;
                        let m = &scene.floor_map[band * 256..band * 256 + 256];
                        out[o] = m[floor_buf[kf] as usize];
                        out[o + 1] = m[floor_buf[kf + 1] as usize];
                        out[o + 2] = m[floor_buf[kf + 2] as usize];
                    } else {
                        acc = acc.wrapping_add(kf as u64);
                        out[o] = 0;
                    }
                }
                if delta_pos {
                    q += a_step;
                    rem += b_step;
                    if rem >= kk {
                        rem -= kk;
                        q += 1;
                    }
                } else {
                    q -= a_step;
                    rem -= b_step;
                    if rem < 0 {
                        rem += kk;
                        q -= 1;
                    }
                }
            }
        }
        if MODE != FULL {
            black_box(acc);
        }
    }

    /// The three floor row-bands [near, mid, far] of the horizon, as (r_lo, r_hi) pairs: near = just below the
    /// horizon (small kk, huge DDA stride — near-random tile access), far = the bottom rows (large kk, tight
    /// stride), mid = the sheared middle where a block layout may cross boundaries while a Z-curve holds.
    pub fn floor_bands(strips: &[Strip]) -> [(usize, usize); 3] {
        let mut min_bot = H as i64 - 1;
        for s in strips.iter().take(W) {
            if s.bot < min_bot {
                min_bot = s.bot;
            }
        }
        let lo = (min_bot + 1) as usize;
        let span = H.saturating_sub(lo);
        let t1 = lo + span / 3;
        let t2 = lo + 2 * span / 3;
        [(lo, t1), (t1, t2), (t2, H)]
    }

    /// DETERMINISTIC per-band locality for LAYOUT: for each of the three bands, over adjacent-column floor texels,
    /// count how many land within a 64-byte cache line of each other IN THE SWIZZLED BUFFER (|Δ index|*3 <= 64).
    /// This is the structural shear story — where blocked locality collapses (near/mid, stride crosses blocks) vs
    /// where the Z-curve holds — gate-computed, wall-clock-free. Returns [(adjacent_pairs, within_line); 3].
    pub fn band_locality<const LAYOUT: u8>(scene: &Scene, strips: &[Strip], buf: &[u8]) -> [(usize, usize); 3] {
        let ex = scene.pos_x * Q + EYE_Y;
        let ez = scene.pos_z * Q + EYE_Y;
        let (varying_is_x, delta_pos, d0, d_const) = dda_params(scene.facing);
        let e_const = if varying_is_x { ez } else { ex };
        let e_vary = if varying_is_x { ex } else { ez };
        let dconst_eye = d_const * EYE_Y;
        let step = 2 * EYE_Y;
        let bands = floor_bands(strips);
        let mut outb = [(0usize, 0usize); 3];
        for (bi, &(lo, hi)) in bands.iter().enumerate() {
            let (mut adj, mut local) = (0usize, 0usize);
            for r in lo..hi {
                let kk = 2 * (r as i64 - CY) + 1;
                let cconst = (e_const + dconst_eye.div_euclid(kk)) & (T - 1);
                let a_step = step.div_euclid(kk);
                let b_step = step.rem_euclid(kk);
                let mut q = d0.div_euclid(kk);
                let mut rem = d0.rem_euclid(kk);
                let mut prev: Option<(usize, usize)> = None; // (column, swizzle_index)
                let row = r * W;
                for c in 0..W {
                    let idx = buf[row + c];
                    if idx >= FLOOR0 && idx < DOWN0 {
                        let vary = (e_vary + q) & (T - 1);
                        let (tj, ti_f) = if varying_is_x { (cconst, vary) } else { (vary, cconst) };
                        let ki = swizzle_index::<LAYOUT>(tj, ti_f);
                        if let Some((pc, pk)) = prev {
                            if pc + 1 == c {
                                adj += 1;
                                if (ki as i64 - pk as i64).abs() * 3 <= 64 {
                                    local += 1;
                                }
                            }
                        }
                        prev = Some((c, ki));
                    } else {
                        prev = None;
                    }
                    if delta_pos {
                        q += a_step;
                        rem += b_step;
                        if rem >= kk {
                            rem -= kk;
                            q += 1;
                        }
                    } else {
                        q -= a_step;
                        rem -= b_step;
                        if rem < 0 {
                            rem += kk;
                            q -= 1;
                        }
                    }
                }
            }
            outb[bi] = (adj, local);
        }
        outb
    }
}
