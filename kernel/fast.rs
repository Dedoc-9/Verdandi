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
// This file now holds the optimization STAIRCASE, each tread proven byte-identical to the frozen emit:
//   * `emit`          — GAUNTLET-1c: the row-major floor DDA (the accepted fast path). Per floor row the perspective
//                       divide is done a bounded number of times and the per-column texel steps by a recurrence:
//                       O(rows) divides where the collapse did O(pixels). Ceiling + wall are the exact transcription.
//   * `emit_collapse` — GAUNTLET-1b: the floor divide-collapse (2 divides per floor pixel), a verbatim copy kept as
//                       the SAME-APPARATUS performance BASELINE the DDA is measured against — never the oracle.
// Correctness is mandatory and gate-enforced for BOTH (each byte-identical to frozen); speed is a second, separate
// court measured off-gate on a host. `mantle.rs` is untouched.

use crate::mantle::{
    texel, u_axis_is_z, Scene, Strip, BANDS, CY, DOWN0, EYE_Y, FLOOR0, FOCAL, H, Q, T, U_SIGN, W, WALL0,
};

/// GAUNTLET-1c — the accepted fast path: the frozen ceiling + wall (an exact transcription) in a column-major pass,
/// then the floor in a ROW-MAJOR pass that replaces the per-pixel perspective divide with a per-row DDA.
///
/// Why row-major: at a fixed floor row `r`, `kk = 2(r-CY)+1` is constant, and (from `direction`) exactly one floor
/// axis is constant across columns while the other's numerator `D(c)` steps by `+/- 2*EYE_Y` per column. The frozen
/// (collapse) texel for the varying axis is `(e + D(c).div_euclid(kk)) & (T-1)`; tracking `(q, rem) =
/// (D.div_euclid(kk), D.rem_euclid(kk))` and advancing `D` by its constant step needs at most one correction — O(1)
/// per column, ~5 divides per ROW instead of 2 per floor pixel. Validated exact over the recurrence (2.07M points)
/// and the facing/assignment mapping (3.93M texels), and — decisively — proven byte-identical to the frozen emit by
/// `gauntlet1-equiv`. `buf` is read, never written, so the frame (and `frame_digest`) cannot move.
pub fn emit(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8]) {
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
