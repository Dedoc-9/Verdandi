// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/bearingfast.rs — BEARING-FAST-0: the bearing camera's production candidate, a SIBLING of the reference
// (kernel/bearing.rs), which stays the correctness court and is never modified. Every tread here must reproduce the
// reference's index frame and picture byte for byte; the rows bearingfast-court, -threads and -checked hold it to that.
//
// The reference spends its time in per-pixel 128-bit division: six per floor pixel (two for the cell, four for the
// texel) and one per wall pixel. The fast path keeps the reference's traversal (Scene::strips, unchanged) and
// replaces the index frame and the picture with one row-major pass in which every pixel is a few 64-bit adds:
//
//   THE EXACT WALKER. A quantity N(j) = N0 + j*s (integers) seen through floor(N*T/den) is carried as
//   M = floor(N*T/den) and e = N*T - M*den (0 <= e < den). One step adds s*T = dM*den + de: e += de, M += dM, and one
//   carry if e reaches den. M and e are set up once from N0 in 128 bits; every step after that is 64-bit.
//
//   THE FLOOR (tread A). At a floor row r, kk = 2(r - CY) + 1 and den = kk*C*Q are constant, and the floor point's
//   numerators N_x(c) = ex*kk*C + dx(c)*EYE_Y and N_z(c) = ez*kk*C + dz(c)*EYE_Y step by -2*B*EYE_Y and +2*A*EYE_Y per
//   column, because D(c) = (A*b - B*a, B*b + A*a) with a = 2c + 1 - W. With T = Q, a walker's M is the floor point in
//   texel units: the cell is M >> 8 and the texel M & 255 — exactly the reference's div_euclid(den) and
//   texel(rem_euclid(den), den). Two walkers per row, at any heading: Lode's scanline floor casting, made exact.
//   THE WALL. Down a strip, v's numerator v_base + 2r*C*tn steps by 2*C*tn per row over v_den = Q*td: one walker per
//   column, clamped to [0, T) as the reference's texel clamps. u is constant down the column (one 128-bit setup).
//   THE ORDER. The frame and the picture are written together, row by row, so both buffers are filled in address
//   order; the reference fills them column by column.
//
//   TREAD B reads the floor tile from the 8x8 blocked execution format LOCALITY-0 locked (fast::blocked_floor, built
//   once per scene), the same content re-laid; tread C runs contiguous row bands on scoped threads, each band seeding
//   its own wall walkers at its first row; the writes are disjoint, so the bytes cannot depend on the thread count.
//
// WRITTEN BOUNDS (every quantity narrowed to 64 bits; the envelope is checked per scene and per strip, and a scene
// outside it is REFUSED, never wrapped; the gate also runs this file built with overflow checks on):
//   C < 2^33 (C_BOUND; the registered table's largest hypotenuse is 8,404,122,277), |A|, |B| <= C.
//   eye: ex, ez <= 47*256 + 128 < 2^14.          |a| <= 1919, b = 1920:  |dx|, |dz| <= C*3839 < 2^45.
//   strip: tn <= 49*256 < 2^14 (TN_BOUND), td = |d_axis| < 2^45 (TD_BOUND).
//   floor row: 1 <= kk <= 1079 < 2^11, kk*C < 2^44, den = kk*C*Q < 2^52; step s = 2*|B or A|*EYE_Y < 2^41, s*T < 2^49;
//     |M| = |floor point in texel units| <= ex + |d|*EYE_Y/(kk*C) < 2^14 + 2^19; e + de < 2*den < 2^53.
//   wall column: v_den = Q*td < 2^53; step 2*C*tn < 2^48, times T < 2^56; e + de < 2*v_den < 2^54; M is the v texel
//     row, near [0, T) inside the strip and below 2^24 anywhere on screen (C*t = depth/1920 < 10).
//   The setup products (N0*T up to 2^67) are formed in i128 only, and every narrowing goes through `narrow`, which
//   is checked in every build (an `as` cast is not covered by overflow checks); each call carries its bound.

use super::bearing::{
    face_light, texel, u_axis_is_z, Scene, Strip, BANDS, CY, DOWN0, EYE_Y, FLOOR0, FOCAL, H, INK, Q, SKY0, SKY_BANDS, T,
    U_SIGN, UP0, W, WALL0,
};
use super::mantle::Refusal;
use std::convert::TryInto;

pub const C_BOUND: i128 = 1 << 33;
pub const TN_BOUND: i128 = 1 << 14;
pub const TD_BOUND: i128 = 1 << 45;
/// The production thread count for tread C (GAUNTLET-2's PROD_THREADS).
pub const PROD_THREADS: usize = 8;
const SHIFT: u32 = 8; // T = 256 = 1 << SHIFT
const MASK: i64 = T - 1;
const TU: usize = T as usize;

/// The only way from 128 to 64 bits in this file: checked in every build. The envelope makes a failure unreachable;
/// if one ever happens the fast path stops loudly instead of wrapping.
#[inline]
fn narrow(v: i128) -> i64 {
    if v < i64::MIN as i128 || v > i64::MAX as i128 {
        super::bearing::refuse("BEARING-FAST-REFUSE: a narrowed quantity left 64 bits");
    }
    v as i64
}

/// The exact walker: M = floor(N*T/den) and its remainder e, for N = N0 + j*s, stepped in 64 bits.
#[derive(Clone, Copy)]
pub struct Walker {
    pub m: i64,
    e: i64,
    dm: i64,
    de: i64,
    den: i64,
}

impl Walker {
    pub fn new(n0: i128, s: i64, den: i64) -> Walker {
        let (big, d) = (n0 * T as i128, den as i128);
        let m = big.div_euclid(d);
        let st = s * T;
        let dm = st.div_euclid(den);
        let (m, e) = (narrow(m), narrow(big - m * d)); // |m| < 2^24 (a texel coordinate); 0 <= e < den < 2^53
        Walker { m, e, dm, de: st - dm * den, den }
    }
    #[inline(always)]
    pub fn step(&mut self) {
        self.e += self.de;
        self.m += self.dm;
        if self.e >= self.den {
            self.e -= self.den;
            self.m += 1;
        }
    }
}

/// One column's constants: where the strip is, what the frame holds there, and the wall's walker parameters.
#[derive(Clone, Copy)]
pub struct Col {
    top: usize,
    bot: usize,
    widx: u8,
    edge_ink: bool,
    light: usize,
    band: usize,
    ti: usize,
    vbase: i128,
    vstep: i64,
    vden: i64,
}

/// The envelope, checked before any narrowing.
pub fn check(sc: &Scene, strips: &[Strip]) -> Result<(), Refusal> {
    if sc.c >= C_BOUND || sc.a.abs() > sc.c || sc.b.abs() > sc.c {
        return Err(Refusal("BEARING-FAST-REFUSE: the hypotenuse is outside the proven envelope (C < 2^33)".to_string()));
    }
    for (c, s) in strips.iter().enumerate() {
        if s.tn < 0 || s.tn >= TN_BOUND || s.td < 1 || s.td >= TD_BOUND {
            return Err(Refusal(format!("BEARING-FAST-REFUSE: column {} is outside the proven envelope", c)));
        }
    }
    Ok(())
}

/// The columns' constants, from the reference's strips (the frame's INK-on-a-new-face rule, the wall's u texel and
/// v walker, each the reference's expression).
pub fn columns(sc: &Scene, strips: &[Strip]) -> Vec<Col> {
    let ex = (sc.pos_x * Q + EYE_Y) as i128;
    let ez = (sc.pos_z * Q + EYE_Y) as i128;
    let mut prev: Option<(i64, i64, u8)> = None;
    let mut cols = Vec::with_capacity(W);
    for s in strips.iter() {
        let key = (s.vox_x, s.vox_z, s.face);
        let light = face_light(s.face);
        let band = s.band as usize;
        let widx = if prev != Some(key) { INK } else { WALL0 + (light as u8) * (BANDS as u8) + band as u8 };
        prev = Some(key);
        let mut along = if u_axis_is_z(s.face) { ez * s.td + s.tn * s.dz } else { ex * s.td + s.tn * s.dx };
        if U_SIGN[s.face as usize] < 0 {
            along = -along;
        }
        let u_d = Q as i128 * s.td;
        let ti = texel(along.rem_euclid(u_d), u_d) as usize;
        let vbase = Q as i128 * s.td - EYE_Y as i128 * s.td - (2 * CY as i128 - 1) * sc.c * s.tn;
        cols.push(Col {
            top: s.top as usize,
            bot: s.bot as usize,
            widx,
            edge_ink: s.top < s.bot,
            light,
            band,
            ti,
            vbase,
            vstep: narrow(2 * sc.c * s.tn),   // < 2^48: 2 * 2^33 * 2^14
            vden: narrow(Q as i128 * s.td),   // < 2^53: 2^8 * 2^45
        });
    }
    cols
}

#[inline(always)]
fn blocked(tj: usize, ti: usize) -> usize {
    (((tj >> 3) * (TU >> 3)) + (ti >> 3)) * 64 + (tj & 7) * 8 + (ti & 7)
}

/// Rows r0..r1 of the frame and the picture, into slices that begin at row r0. BLOCKED selects tread B's floor
/// fetch; `floor` is then the blocked buffer, otherwise the scene's floor tile. One pass in address order: per row,
/// the sky's colour, the floor's two walkers and its band are set up once; per pixel, the column's region decides.
pub fn rows<const BLOCKED: bool>(sc: &Scene, strips: &[Strip], cols: &[Col], floor: &[u8], r0: usize, r1: usize,
                                 buf: &mut [u8], out: &mut [u8]) {
    let table: &[u8] = &sc.table;
    let rgb = |i: u8| -> [u8; 3] { [table[i as usize * 3], table[i as usize * 3 + 1], table[i as usize * 3 + 2]] };
    let ex = (sc.pos_x * Q + EYE_Y) as i128;
    let ez = (sc.pos_z * Q + EYE_Y) as i128;
    let (dx0, dz0) = (strips[0].dx, strips[0].dz);
    let (sx, sz) = (narrow(-2 * sc.b * EYE_Y as i128), narrow(2 * sc.a * EYE_Y as i128)); // |.| < 2^41: 2 * 2^33 * 2^7
    let (cw, cr) = (sc.w as u64, sc.rows as u64);
    let cells: &[u8] = &sc.cells;
    let floor: &[u8] = &floor[..TU * TU * 3];
    // the wall walkers, seeded at each strip's first row inside this band
    let mut walls: Vec<Walker> = cols
        .iter()
        .map(|k| Walker::new(k.vbase + k.top.max(r0) as i128 * k.vstep as i128, k.vstep, k.vden))
        .collect();
    for (r, (rb, ro)) in (r0..r1).zip(buf.chunks_exact_mut(W).zip(out.chunks_exact_mut(W * 3))) {
        // the sky lies above the horizon (a strip's top is at most CY), so its band is formed only there: below it
        // the reference's expression would leave the u8 range, as the checked build showed on its first run
        let sky = if (r as i64) < CY { SKY0 + (((CY - r as i64) * SKY_BANDS).div_euclid(CY)).min(SKY_BANDS - 1) as u8 } else { INK };
        let sky_rgb = rgb(sky);
        let floor_row = r as i64 >= CY;
        let (mut fx, mut fz, fband) = if floor_row {
            let kk = 2 * (r as i64 - CY) + 1;
            let kc = kk as i128 * sc.c;
            let den = narrow(kc * Q as i128); // < 2^52: 2^11 * 2^33 * 2^8
            let fband = ((2 * FOCAL * EYE_Y).div_euclid(kk * Q)).min(BANDS - 1) as u8;
            (Walker::new(ex * kc + dx0 * EYE_Y as i128, sx, den), Walker::new(ez * kc + dz0 * EYE_Y as i128, sz, den), fband)
        } else {
            (Walker::new(0, 0, 1), Walker::new(0, 0, 1), 0)
        };
        let fmap: &[u8; 256] = sc.floor_map[fband as usize * 256..fband as usize * 256 + 256].try_into().unwrap();
        let (fl, dn, up) = (FLOOR0 + fband, DOWN0 + fband, UP0 + fband);
        let (dn_rgb, up_rgb) = (rgb(dn), rgb(up));
        for (((k, w), b), o) in cols.iter().zip(walls.iter_mut()).zip(rb.iter_mut()).zip(ro.chunks_exact_mut(3)) {
            if r < k.top {
                *b = sky;
                o.copy_from_slice(&sky_rgb);
            } else if r <= k.bot {
                let idx = if k.edge_ink && (r == k.top || r == k.bot) { INK } else { k.widx };
                *b = idx;
                if idx < WALL0 {
                    o.copy_from_slice(&rgb(idx));
                } else {
                    let t = (w.m.clamp(0, MASK) as usize * TU + k.ti) * 3;
                    let tile = &sc.walls[k.light][t..t + 3];
                    let m: &[u8; 256] = sc.wall_map[k.band * 256..k.band * 256 + 256].try_into().unwrap();
                    o[0] = m[tile[0] as usize];
                    o[1] = m[tile[1] as usize];
                    o[2] = m[tile[2] as usize];
                }
                w.step();
            } else {
                let (wx, wz) = (fx.m >> SHIFT, fz.m >> SHIFT);
                let cell = if (wz as u64) < cr && (wx as u64) < cw { cells[(wz as u64 * cw + wx as u64) as usize] } else { b'#' };
                match cell {
                    b'>' => {
                        *b = dn;
                        o.copy_from_slice(&dn_rgb);
                    }
                    b'<' => {
                        *b = up;
                        o.copy_from_slice(&up_rgb);
                    }
                    _ => {
                        *b = fl;
                        let (tj, ti) = ((fz.m & MASK) as usize, (fx.m & MASK) as usize);
                        let t = if BLOCKED { blocked(tj, ti) } else { tj * TU + ti } * 3;
                        let f = &floor[t..t + 3];
                        o[0] = fmap[f[0] as usize];
                        o[1] = fmap[f[1] as usize];
                        o[2] = fmap[f[2] as usize];
                    }
                }
            }
            if floor_row {
                fx.step();
                fz.step();
            }
        }
    }
}

/// A tread: the floor layout (A linear, B blocked) and the thread count (1 for A and B; C runs bands).
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Tread {
    pub blocked: bool,
    pub threads: usize,
}

pub const A: Tread = Tread { blocked: false, threads: 1 };
pub const B: Tread = Tread { blocked: true, threads: 1 };

/// The floor buffer a tread reads, built once per scene (B's swizzle is LOCALITY-0's, fast::blocked_floor).
pub fn prepare(sc: &Scene, tread: Tread) -> Vec<u8> {
    if tread.blocked {
        super::fast::blocked_floor(&sc.floor)
    } else {
        sc.floor.clone()
    }
}

/// The frame and the picture of one tread, into reusable buffers; the strips are the reference's.
pub fn render_into(sc: &Scene, tread: Tread, floor: &[u8], strips: &mut Vec<Strip>, buf: &mut [u8], out: &mut [u8])
                   -> Result<(), Refusal> {
    sc.strips(strips);
    check(sc, strips)?;
    let cols = columns(sc, strips);
    let n = tread.threads.max(1).min(H);
    if n == 1 {
        if tread.blocked {
            rows::<true>(sc, strips, &cols, floor, 0, H, buf, out);
        } else {
            rows::<false>(sc, strips, &cols, floor, 0, H, buf, out);
        }
        return Ok(());
    }
    // tread C: n contiguous row bands, band k = rows [k*H/n, (k+1)*H/n), disjoint slices of both buffers
    let strips: &Vec<Strip> = strips;
    std::thread::scope(|scope| {
        let (mut brest, mut orest) = (&mut buf[..], &mut out[..]);
        for k in 0..n {
            let (r0, r1) = (k * H / n, (k + 1) * H / n);
            let (bb, br) = brest.split_at_mut((r1 - r0) * W);
            let (ob, or) = orest.split_at_mut((r1 - r0) * W * 3);
            brest = br;
            orest = or;
            let cols = &cols;
            scope.spawn(move || {
                if tread.blocked {
                    rows::<true>(sc, strips, cols, floor, r0, r1, bb, ob);
                } else {
                    rows::<false>(sc, strips, cols, floor, r0, r1, bb, ob);
                }
            });
        }
    });
    Ok(())
}

/// One frame of a tread, fresh buffers: (index frame, picture).
pub fn picture(sc: &Scene, tread: Tread) -> Result<(Vec<u8>, Vec<u8>), Refusal> {
    let floor = prepare(sc, tread);
    let mut strips: Vec<Strip> = Vec::with_capacity(W);
    let mut buf = vec![0u8; W * H];
    let mut out = vec![0u8; W * H * 3];
    render_into(sc, tread, &floor, &mut strips, &mut buf, &mut out)?;
    Ok((buf, out))
}
