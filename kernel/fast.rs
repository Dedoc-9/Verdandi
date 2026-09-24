// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/fast.rs — GAUNTLET-1: a SIBLING of the frozen emit, never `mantle.rs`.
//
// GAUNTLET-0 selected `emit` as the sole optimization target (emit at 695 permille of the instrumented render on
// host DANIELDILLBERG). GAUNTLET-1a seeds this file as an EXACT TRANSCRIPTION of `mantle::Scene::emit` — NO
// optimization — so the differential equivalence court (`gauntlet1-equiv`) and the region measure exist and are
// proven before any candidate technique is inspected. The frozen `mantle.rs` is the correctness oracle; this file
// is guilty until its bytes agree with it, and the harness compares candidate -> frozen, never the reverse.
//
// GAUNTLET-1b will replace the body below with the simplest exact optimization the measured dominant region
// justifies, and it earns acceptance only by (1) byte-identical output over the corpus + adversarial cameras and
// (2) a separately judged speed result. Correctness is mandatory; speed is a second, independent court.

use crate::mantle::{texel, u_axis_is_z, Scene, Strip, BANDS, CY, DOWN0, EYE_Y, FLOOR0, H, Q, T, U_SIGN, W, WALL0};

/// An exact transcription of `mantle::Scene::emit` as a free function (the GAUNTLET-1a seed — no optimization).
/// Every operation and its order mirror the frozen source; `mantle.rs` is not touched. `buf` is read, never
/// written, so the frame (and thus `frame_digest`) cannot move.
pub fn emit(scene: &Scene, strips: &[Strip], buf: &[u8], out: &mut [u8]) {
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
        for r in (bot + 1)..H {
            let idx = buf[r * W + c];
            let o = (r * W + c) * 3;
            if idx < FLOOR0 || idx >= DOWN0 {
                let i = idx as usize;
                out[o..o + 3].copy_from_slice(&table[i * 3..i * 3 + 3]);
                continue;
            }
            let kk = 2 * (r as i64 - CY) + 1;
            let den = kk * Q;
            let tj = texel((ez * kk + dz * EYE_Y).rem_euclid(den), den);
            let ti_f = texel((ex * kk + dx * EYE_Y).rem_euclid(den), den);
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
/// by top/bot, then the idx test), and the integer-division work each costs — read off the source cost mechanism:
/// ceiling/table = 0, a textured wall pixel = 1 (one `texel`), a textured floor pixel = 4 (two `texel`, each a
/// `rem_euclid` + a `div_euclid`). Returns (wall_textured_px, floor_textured_px, table_px), from which the
/// divide-work is wall + 4*floor. This names GAUNTLET-1b's target region without measuring a wall-clock.
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
