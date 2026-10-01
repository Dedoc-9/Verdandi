// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/bearing.rs — THE REFERENCE BEARING KERNEL (BEARING-0): the frame and the picture at a registered
// rational direction, placed. It is the CORRECTNESS COURT for every faster bearing path: a production path
// earns its place by reproducing this file's two witnesses byte for byte, and this file is never modified for
// performance. No live window uses it.
//
// Ported from Urðr's tools/terrain/bearing_rs/bearing.rs at the tag urdr-oracle-2 (ad6d55fe; the source's
// sha256 aeda8e65dc56652fbfc5b67723f78800b2c2b55cb68609149b64910d8e6130be). What changed in the port is
// visibility and shape, never arithmetic: the constants, the scene, the ray, the traversal, the strip and floor
// fills, the texture coordinates and the emission are the source's text made `pub`; the scene parser returns
// a typed refusal (BEARING-REFUSE) instead of exiting; the command line moved to main.rs; SHA-256 and hex are
// mantle.rs's (the same FIPS 180-4 code the source carried). The rows bearing-oracle and bearing-anchors
// (../verify/verify.py) are what make this a placement: all 104 witnesses of urdr-oracle-2 bit for bit, and
// the four anchors equal to the facing kernel's frames and pictures.
//
// The ray at column c is D = (A*b - B*a, B*b + A*a), a = 2c + 1 - W, b = 2*FOCAL: C times the unit ray,
// integer. The hypotenuse enters exactly four expressions: the depth 2*FOCAL*C*t (strip edges), the depth band,
// the wall's row height EYE_Y + (2*CY - 2r - 1)*C*t (the v coordinate), and the floor point E + D*EYE_Y/(kk*C).
// At C = 1 every one is mantle.rs's expression. C reaches 2^33, so every quantity derived from the ray is
// carried in i128 (a product of two operands each below 2^64 cannot overflow it).
//
// The scene is INPUT, never computed here (little-endian): "URDRBRGI" | u32 w | u32 rows | w*rows cells |
// i32 pos_x | i32 pos_z | i64 A | i64 B | i64 C | u32 depth | 768 table | 32*256 wall_map | 32*256 floor_map |
// 4 * 196608 wall tiles (one per light family) | 196608 floor tile — composed by vocab.rs from the level, the
// bearing camera and the tiles.
//
// This file opens no window, reads no clock, writes no file, spawns no thread, and cannot reach the shell.

use super::mantle::{hex, sha256, Refusal};

pub const W: usize = 1920;
pub const H: usize = 1080;
pub const CY: i64 = 540;
pub const FOCAL: i64 = 960;
pub const Q: i64 = 256;
pub const EYE_Y: i64 = 128;
pub const BANDS: i64 = 32;
pub const T: i64 = 256;
pub const TILE_BYTES: usize = 256 * 256 * 3;
pub const INK: u8 = 0;
pub const SKY0: u8 = 1;
pub const SKY_BANDS: i64 = 15;
pub const FLOOR0: u8 = 16;
pub const DOWN0: u8 = 48;
pub const UP0: u8 = 80;
pub const WALL0: u8 = 112;
pub const MAX_STEPS: usize = 4096;
pub const LATTICE: i64 = 48;
pub const MAGIC_FB: &[u8] = b"URDRFB1";
pub const MAGIC_IN: &[u8] = b"URDRBRGI";

// vista.FACE_LIGHT: entered face -> light family (4 south, 1 west, 5 north, 0 east).
pub fn face_light(face: u8) -> usize {
    match face {
        4 => 0,
        1 => 1,
        5 => 2,
        0 => 3,
        _ => 0,
    }
}
// mantle.U_SIGN by face index (faces 2 and 3 are y faces, never entered by a horizontal ray).
pub const U_SIGN: [i64; 6] = [-1, 1, 0, 0, 1, -1];
// mantle.U_AXIS: the world axis u runs along — z for the x faces (0, 1), x for the z faces (4, 5).
pub fn u_axis_is_z(face: u8) -> bool {
    face == 0 || face == 1
}

// ------------------------------------------------------------------ the scene (input, never computed)
pub struct Scene {
    pub w: usize,
    pub rows: usize,
    pub cells: Vec<u8>,
    pub pos_x: i64,
    pub pos_z: i64,
    pub a: i128,
    pub b: i128,
    pub c: i128,
    pub table: Vec<u8>,     // 256 * 3
    pub wall_map: Vec<u8>,  // 32 * 256
    pub floor_map: Vec<u8>, // 32 * 256
    pub walls: Vec<Vec<u8>>, // 4 * TILE_BYTES
    pub floor: Vec<u8>,     // TILE_BYTES
}

/// The traversal's own invariants (a zero ray, MAX_STEPS, a ray leaving the world) cannot fail on a scene the
/// parser admitted; if one does, the kernel stops loudly, as the source did.
pub fn refuse(msg: &str) -> ! {
    eprintln!("BEARING-REFUSE: {}", msg);
    std::process::exit(2)
}

/// The scene from its URDRBRGI bytes (urdr-oracle-2's `kernel_input`), refusing typed: the magic, the lattice,
/// a direction that is not a Pythagorean triple with C >= 1, trailing bytes, an eye on a non-traversable cell.
pub fn parse_scene(data: &[u8]) -> Result<Scene, Refusal> {
    let no = |m: &str| Refusal(format!("BEARING-REFUSE: {}", m));
    let mut p = 0usize;
    let take = |p: &mut usize, n: usize| -> Result<&[u8], Refusal> {
        if *p + n > data.len() {
            return Err(Refusal("BEARING-REFUSE: input truncated".to_string()));
        }
        let s = &data[*p..*p + n];
        *p += n;
        Ok(s)
    };
    if take(&mut p, 8)? != MAGIC_IN {
        return Err(no("input magic is not URDRBRGI"));
    }
    let u32_at = |s: &[u8]| u32::from_le_bytes([s[0], s[1], s[2], s[3]]);
    let i32_at = |s: &[u8]| i32::from_le_bytes([s[0], s[1], s[2], s[3]]);
    let w = u32_at(take(&mut p, 4)?) as usize;
    let rows = u32_at(take(&mut p, 4)?) as usize;
    if w == 0 || rows == 0 || w as i64 > LATTICE || rows as i64 > LATTICE {
        return Err(no("level extent outside the lattice"));
    }
    let cells = take(&mut p, w * rows)?.to_vec();
    let pos_x = i32_at(take(&mut p, 4)?) as i64;
    let pos_z = i32_at(take(&mut p, 4)?) as i64;
    let i64_at = |s: &[u8]| i64::from_le_bytes([s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]]);
    let a = i64_at(take(&mut p, 8)?) as i128;
    let b = i64_at(take(&mut p, 8)?) as i128;
    let c = i64_at(take(&mut p, 8)?) as i128;
    if c < 1 || a * a + b * b != c * c {
        return Err(no("the direction is not a Pythagorean triple with C >= 1"));
    }
    let _depth = u32_at(take(&mut p, 4)?);
    let table = take(&mut p, 768)?.to_vec();
    let wall_map = take(&mut p, 32 * 256)?.to_vec();
    let floor_map = take(&mut p, 32 * 256)?.to_vec();
    let mut walls = Vec::with_capacity(4);
    for _ in 0..4 {
        walls.push(take(&mut p, TILE_BYTES)?.to_vec());
    }
    let floor = take(&mut p, TILE_BYTES)?.to_vec();
    if p != data.len() {
        return Err(no("input has trailing bytes"));
    }
    if !(pos_x >= 0 && (pos_x as usize) < w && pos_z >= 0 && (pos_z as usize) < rows)
        || cells[pos_z as usize * w + pos_x as usize] == b'#'
    {
        return Err(no("the eye stands on a non-traversable cell"));
    }
    Ok(Scene { w, rows, cells, pos_x, pos_z, a, b, c, table, wall_map, floor_map, walls, floor })
}
// ------------------------------------------------------------------ vista: the camera and one column's strip
pub fn direction(a_: i128, b_: i128, column: usize) -> (i128, i128) {
    // D = (A*b - B*a, B*b + A*a): camera-space (a, b) carried by the triple's right (-B, A) and forward (A, B)
    let a = 2 * column as i128 + 1 - W as i128;
    let b = 2 * FOCAL as i128;
    (a_ * b - b_ * a, b_ * b + a_ * a)
}

#[derive(Clone, Copy)]
pub struct Strip {
    pub vox_x: i64,
    pub vox_z: i64,
    pub face: u8,
    pub tn: i128,
    pub td: i128,
    pub top: i64,
    pub bot: i64,
    pub band: i64,
    pub dx: i128,
    pub dz: i128,
}

impl Scene {
    pub fn occ(&self, x: i64, y: i64, z: i64) -> bool {
        // vista._occupancy: y == 0 and (z >= rows or cells[z][x] == '#'); x beyond the row reads as not rock
        if y != 0 {
            return false;
        }
        if z >= self.rows as i64 {
            return true;
        }
        if x < 0 || x >= self.w as i64 || z < 0 {
            return false;
        }
        self.cells[z as usize * self.w + x as usize] == b'#'
    }

    /// voxray.first_hit for a horizontal ray (dx, 0, dz) from the eye, opaque origin, lattice LATTICE,
    /// cell Q: (voxel, entered face, t = tn/td) — t in reduced form (see the header). None = left the world.
    pub fn first_hit(&self, ex: i64, ez: i64, dx: i128, dz: i128) -> Option<(i64, i64, u8, i128, i128)> {
        let n = LATTICE;
        let mut v = [ex.div_euclid(Q), EYE_Y.div_euclid(Q), ez.div_euclid(Q)];
        if v.iter().all(|&c| 0 <= c && c < n) && self.occ(v[0], v[1], v[2]) {
            return Some((v[0], v[2], 255, 0, 1)); // started inside rock: no entry face (vista refuses this)
        }
        let d = [dx, 0i128, dz];
        let mut step = [0i64; 3];
        let mut num = [0i128; 3];
        let mut den = [0i128; 3];
        let mut active = [false; 3];
        for i in [0usize, 2usize] {
            if d[i] == 0 {
                continue;
            }
            active[i] = true;
            step[i] = if d[i] > 0 { 1 } else { -1 };
            let e = if i == 0 { ex } else { ez };
            let boundary = if d[i] > 0 { (v[i] + 1) * Q } else { v[i] * Q };
            num[i] = (if d[i] > 0 { boundary - e } else { e - boundary }) as i128;
            den[i] = d[i].abs();
        }
        if !active[0] && !active[2] {
            refuse("a direction with no non-zero component");
        }
        for _ in 0..MAX_STEPS {
            // the axis with the smaller t, strict less-than by cross-multiplication, ties to the lower axis
            let axis = if active[0] && active[2] {
                if num[2] * den[0] < num[0] * den[2] { 2 } else { 0 }
            } else if active[0] {
                0
            } else {
                2
            };
            let t = (num[axis], den[axis]);
            v[axis] += step[axis];
            num[axis] += Q as i128;
            if 0 <= v[axis] && v[axis] < n {
                if v.iter().all(|&c| 0 <= c && c < n) && self.occ(v[0], v[1], v[2]) {
                    let face: u8 = match (axis, step[axis]) {
                        (0, 1) => 1,
                        (0, -1) => 0,
                        (2, 1) => 5,
                        _ => 4,
                    };
                    return Some((v[0], v[2], face, t.0, t.1));
                }
            } else if (v[axis] < 0) == (step[axis] < 0) {
                return None;
            }
        }
        refuse("traversal exceeded MAX_STEPS")
    }

    pub fn strips(&self, out: &mut Vec<Strip>) {
        out.clear();
        let ex = self.pos_x * Q + EYE_Y;
        let ez = self.pos_z * Q + EYE_Y;
        for c in 0..W {
            let (dx, dz) = direction(self.a, self.b, c);
            let (vx, vz, face, tn, td) = match self.first_hit(ex, ez, dx, dz) {
                Some(h) => h,
                None => refuse(&format!("the ray at column {} left the world", c)),
            };
            if face == 255 {
                refuse("the ray started inside rock");
            }
            // h = h2n / h2d = 64 * td / (C * tn); the strip is the rows whose centres lie between the wall's edges
            let (focal, eye_y, q) = (FOCAL as i128, EYE_Y as i128, Q as i128);
            let h2n = focal * eye_y * td;
            let h2d = 2 * focal * self.c * tn;
            let top = CY - (2 * h2n + h2d).div_euclid(2 * h2d) as i64;
            let bot = CY + (2 * h2n - h2d).div_euclid(2 * h2d) as i64;
            let band = ((2 * focal * self.c * tn).div_euclid(td * q)).min(BANDS as i128 - 1) as i64;
            out.push(Strip {
                vox_x: vx,
                vox_z: vz,
                face,
                tn,
                td,
                top: top.max(0),
                bot: bot.min(H as i64 - 1),
                band,
                dx,
                dz,
            });
        }
    }

    /// vista.frame: the URDRFB1 index frame, row-major, into `buf` (W*H bytes).
    pub fn frame(&self, strips: &[Strip], buf: &mut [u8]) {
        let ex = self.pos_x * Q + EYE_Y;
        let ez = self.pos_z * Q + EYE_Y;
        let mut prev: Option<(i64, i64, u8)> = None;
        for c in 0..W {
            let s = &strips[c];
            let key = (s.vox_x, s.vox_z, s.face);
            let widx = WALL0 + (face_light(s.face) as u8) * (BANDS as u8) + s.band as u8;
            let top = s.top as usize;
            let bot = s.bot as usize;
            for r in 0..top {
                let sb = (((CY - r as i64) * SKY_BANDS).div_euclid(CY)).min(SKY_BANDS - 1);
                buf[r * W + c] = SKY0 + sb as u8;
            }
            let v = if prev != Some(key) { INK } else { widx };
            for r in top..=bot {
                buf[r * W + c] = v;
            }
            if top < bot {
                buf[top * W + c] = INK;
                buf[bot * W + c] = INK;
            }
            for r in (bot + 1)..H {
                let kk = 2 * (r as i64 - CY) + 1;
                let kc = kk as i128 * self.c;
                let wx = ((ex as i128 * kc + s.dx * EYE_Y as i128).div_euclid(kc * Q as i128)) as i64;
                let wz = ((ez as i128 * kc + s.dz * EYE_Y as i128).div_euclid(kc * Q as i128)) as i64;
                let fband = ((2 * FOCAL * EYE_Y).div_euclid(kk * Q)).min(BANDS - 1) as u8;
                let cc = if wz >= 0 && (wz as usize) < self.rows && wx >= 0 && (wx as usize) < self.w {
                    self.cells[wz as usize * self.w + wx as usize]
                } else {
                    b'#'
                };
                buf[r * W + c] = match cc {
                    b'>' => DOWN0 + fband,
                    b'<' => UP0 + fband,
                    _ => FLOOR0 + fband,
                };
            }
            prev = Some(key);
        }
    }

    /// mantle._emit: the picture, RGB row-major into `out` (W*H*3 bytes). The index frame is READ.
    pub fn emit(&self, strips: &[Strip], buf: &[u8], out: &mut [u8]) {
        let ex = self.pos_x * Q + EYE_Y;
        let ez = self.pos_z * Q + EYE_Y;
        let table = &self.table;
        for c in 0..W {
            let s = &strips[c];
            let (tn, td, dx, dz) = (s.tn, s.td, s.dx, s.dz);
            // u along the face, signed per face, modulo the cell
            let (exw, ezw) = (ex as i128, ez as i128);
            let mut along = if u_axis_is_z(s.face) { ezw * td + tn * dz } else { exw * td + tn * dx };
            if U_SIGN[s.face as usize] < 0 {
                along = -along;
            }
            let u_d = Q as i128 * td;
            let u_n = along.rem_euclid(u_d);
            let ti = texel(u_n, u_d);
            let v_base = Q as i128 * td - EYE_Y as i128 * td - (2 * CY as i128 - 1) * self.c * tn;
            let v_den = Q as i128 * td;
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
                let tj = texel(v_base + 2 * r as i128 * self.c * tn, v_den);
                let k = ((tj * T + ti) * 3) as usize;
                let tile = &self.walls[light];
                let m = &self.wall_map[band * 256..band * 256 + 256];
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
                let kc = (2 * (r as i64 - CY) + 1) as i128 * self.c;
                let den = kc * Q as i128;
                let tj = texel((ezw * kc + dz * EYE_Y as i128).rem_euclid(den), den);
                let ti_f = texel((exw * kc + dx * EYE_Y as i128).rem_euclid(den), den);
                let k = ((tj * T + ti_f) * 3) as usize;
                let band = (idx - FLOOR0) as usize;
                let m = &self.floor_map[band * 256..band * 256 + 256];
                let tile = &self.floor;
                out[o] = m[tile[k] as usize];
                out[o + 1] = m[tile[k + 1] as usize];
                out[o + 2] = m[tile[k + 2] as usize];
            }
        }
    }
}

#[inline]
pub fn texel(num: i128, den: i128) -> i64 {
    let i = (num * T as i128).div_euclid(den);
    if i >= T as i128 {
        T - 1
    } else if i < 0 {
        0
    } else {
        i as i64
    }
}

pub fn frame_digest(buf: &[u8]) -> String {
    let mut ser = Vec::with_capacity(MAGIC_FB.len() + 9 + buf.len());
    ser.extend_from_slice(MAGIC_FB);
    ser.extend_from_slice(&(W as u32).to_be_bytes());
    ser.extend_from_slice(&(H as u32).to_be_bytes());
    ser.push(1u8);
    ser.extend_from_slice(buf);
    hex(&sha256(&ser))
}

/// The two witnesses' material: the strips, the index frame and the picture.
pub struct Picture {
    pub strips: Vec<Strip>,
    pub frame: Vec<u8>,
    pub pixels: Vec<u8>,
}

impl Picture {
    pub fn frame_digest(&self) -> String {
        frame_digest(&self.frame)
    }
    pub fn pixel_sha256(&self) -> String {
        hex(&sha256(&self.pixels))
    }
}

/// One frame at the scene's bearing: strips, the index frame, then the picture.
pub fn picture(scene: &Scene) -> Picture {
    let mut strips: Vec<Strip> = Vec::with_capacity(W);
    let mut frame = vec![0u8; W * H];
    let mut pixels = vec![0u8; W * H * 3];
    scene.strips(&mut strips);
    scene.frame(&strips, &mut frame);
    scene.emit(&strips, &frame, &mut pixels);
    Picture { strips, frame, pixels }
}
