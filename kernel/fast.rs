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
/// textured work, with `black_box` anchoring the work so the optimizer cannot elide the very thing being timed:
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
                acc = acc.wrapping_add(k as u64);
                let (mut rr, mut gg, mut bb) = (0u8, 0u8, 0u8);
                if MODE >= LOOKUP {
                    let (t0, t1, t2) = (tile[k], tile[k + 1], tile[k + 2]);
                    acc = acc.wrapping_add(t0 as u64 ^ ((t1 as u64) << 8) ^ ((t2 as u64) << 16));
                    if MODE >= FULL {
                        rr = m[t0 as usize];
                        gg = m[t1 as usize];
                        bb = m[t2 as usize];
                        acc = acc.wrapping_add(rr as u64 ^ ((gg as u64) << 8) ^ ((bb as u64) << 16));
                    }
                }
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
                        acc = acc.wrapping_add(k as u64);
                        let (mut rr, mut gg, mut bb) = (0u8, 0u8, 0u8);
                        if MODE >= LOOKUP {
                            let (t0, t1, t2) = (tile[k], tile[k + 1], tile[k + 2]);
                            acc = acc.wrapping_add(t0 as u64 ^ ((t1 as u64) << 8) ^ ((t2 as u64) << 16));
                            if MODE >= FULL {
                                rr = m[t0 as usize];
                                gg = m[t1 as usize];
                                bb = m[t2 as usize];
                                acc = acc.wrapping_add(rr as u64 ^ ((gg as u64) << 8) ^ ((bb as u64) << 16));
                            }
                        }
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
