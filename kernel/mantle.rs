// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/mantle.rs — THE KERNEL: the deterministic per-frame work of the certified tile path, placed.
//
// Ported from Urðr's tools/terrain/mantle_rs/mantle.rs at the tag urdr-oracle-1 (4c8c2451; the source's
// sha256 9e8a8f7d3a2eb175566576df74357e7a1e9b8a42df52ffdc21b0701572fa5ba9). What changed in the port is
// visibility and shape, never arithmetic: the constants, the SHA-256, the scene, the traversal, the strip
// and floor fills, the texture coordinates and the emission are the same bytes of code, made `pub` so that
// the CLI (main.rs) and the workshop can call them; the command line moved to main.rs; the scene parser
// returns a typed refusal instead of exiting, so a caller can refuse an input without dying. The rows
// kernel-oracle and kernel-corpus (../verify/verify.py) are what make this a placement: both witnesses,
// bit for bit, against the frozen oracle, on every gate run.
//
// vista's frame (one exact ray per column through the URDRVXR1 traversal, the strip and the floor as
// floors of rationals, an 8-bit URDRFB1 index frame) and mantle's picture (exact texture coordinates on
// a flat tile, the table's own per-band maps applied to the texel):
//
//     frame  <sha256>     the URDRFB1 digest of the index frame     (geometry)
//     pixels <sha256>     the sha256 of the 1920x1080 RGB picture    (appearance)
//
// EXACTNESS WITHOUT BIG INTEGERS. voxray's traversal carries t as an unreduced rational whose
// denominator grows by |d| per step (the Python is exact at any size); here the same rational is
// carried in reduced form — along axis i the crossing parameter is (k*Q - eye_i)/|d_i| with a FIXED
// denominator |d_i| <= 1920 — and every quantity vista and mantle derive from t is a floor of a
// rational, invariant under the representation. Magnitudes: numerators below 2^36 in every product,
// so i64 throughout and no overflow path exists. The comparison rule is voxray's: strict less-than
// by cross-multiplication, ties to the lower axis.
//
// The scene is INPUT, never computed here (little-endian): "URDRMNTI" | u32 w | u32 rows | w*rows cells |
// i32 pos_x | i32 pos_z | u8 facing (0 N, 1 E, 2 S, 3 W) | u32 depth | 768 table | 32*256 wall_map |
// 32*256 floor_map | 4 * 196608 wall tiles (one per light family) | 196608 floor tile.
//
// This file opens no window, reads no clock, writes no file, and cannot reach the workshop or the shell.

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
pub const MAGIC_IN: &[u8] = b"URDRMNTI";

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

// ------------------------------------------------------------------ SHA-256 (FIPS 180-4, hand-rolled)
const SHA_H0: [u32; 8] = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
];
const SHA_K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

pub fn sha256(data: &[u8]) -> [u8; 32] {
    let mut h = SHA_H0;
    let bitlen = (data.len() as u64).wrapping_mul(8);
    let mut msg = Vec::with_capacity(data.len() + 72);
    msg.extend_from_slice(data);
    msg.push(0x80);
    while msg.len() % 64 != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bitlen.to_be_bytes());
    let mut w = [0u32; 64];
    for block in msg.chunks_exact(64) {
        for i in 0..16 {
            w[i] = u32::from_be_bytes([block[4 * i], block[4 * i + 1], block[4 * i + 2], block[4 * i + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }
        let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let t1 = hh.wrapping_add(s1).wrapping_add(ch).wrapping_add(SHA_K[i]).wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }
    let mut out = [0u8; 32];
    for i in 0..8 {
        out[4 * i..4 * i + 4].copy_from_slice(&h[i].to_be_bytes());
    }
    out
}

pub fn hex(b: &[u8]) -> String {
    const D: &[u8; 16] = b"0123456789abcdef";
    let mut s = String::with_capacity(b.len() * 2);
    for &x in b {
        s.push(D[(x >> 4) as usize] as char);
        s.push(D[(x & 15) as usize] as char);
    }
    s
}
// ------------------------------------------------------------------ the scene (input, never computed)
pub struct Scene {
    pub w: usize,
    pub rows: usize,
    pub cells: Vec<u8>,
    pub pos_x: i64,
    pub pos_z: i64,
    pub facing: u8,
    pub depth: u32,
    pub table: Vec<u8>,     // 256 * 3
    pub wall_map: Vec<u8>,  // 32 * 256
    pub floor_map: Vec<u8>, // 32 * 256
    pub walls: Vec<Vec<u8>>, // 4 * TILE_BYTES
    pub floor: Vec<u8>,     // TILE_BYTES
}

/// The four impossible states of the traversal (a zero direction, MAX_STEPS exceeded, a ray that left the
/// world, a ray that started inside rock) end the process with a typed line, exactly as the placement did:
/// they are invariants of a closed level that a parsed scene cannot violate, not inputs to refuse.
pub fn refuse(msg: &str) -> ! {
    eprintln!("KERNEL-REFUSE: {}", msg);
    std::process::exit(2)
}

/// The typed refusal of a scene: the reason, never a partial scene.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Refusal(pub String);

/// URDRMNTI bytes -> Scene, or the reason the bytes are not a scene. Pure; no I/O.
pub fn parse_scene(data: &[u8]) -> Result<Scene, Refusal> {
    let mut p = 0usize;
    fn take<'a>(data: &'a [u8], p: &mut usize, n: usize) -> Result<&'a [u8], Refusal> {
        if *p + n > data.len() {
            return Err(Refusal("input truncated".to_string()));
        }
        let s = &data[*p..*p + n];
        *p += n;
        Ok(s)
    }
    if take(data, &mut p, 8)? != MAGIC_IN {
        return Err(Refusal("input magic is not URDRMNTI".to_string()));
    }
    let u32_at = |s: &[u8]| u32::from_le_bytes([s[0], s[1], s[2], s[3]]);
    let i32_at = |s: &[u8]| i32::from_le_bytes([s[0], s[1], s[2], s[3]]);
    let w = u32_at(take(data, &mut p, 4)?) as usize;
    let rows = u32_at(take(data, &mut p, 4)?) as usize;
    if w == 0 || rows == 0 || w as i64 > LATTICE || rows as i64 > LATTICE {
        return Err(Refusal("level extent outside the lattice".to_string()));
    }
    let cells = take(data, &mut p, w * rows)?.to_vec();
    let pos_x = i32_at(take(data, &mut p, 4)?) as i64;
    let pos_z = i32_at(take(data, &mut p, 4)?) as i64;
    let facing = take(data, &mut p, 1)?[0];
    if facing > 3 {
        return Err(Refusal("facing must be 0..3".to_string()));
    }
    let depth = u32_at(take(data, &mut p, 4)?);
    let table = take(data, &mut p, 768)?.to_vec();
    let wall_map = take(data, &mut p, 32 * 256)?.to_vec();
    let floor_map = take(data, &mut p, 32 * 256)?.to_vec();
    let mut walls = Vec::with_capacity(4);
    for _ in 0..4 {
        walls.push(take(data, &mut p, TILE_BYTES)?.to_vec());
    }
    let floor = take(data, &mut p, TILE_BYTES)?.to_vec();
    if p != data.len() {
        return Err(Refusal("input has trailing bytes".to_string()));
    }
    if !(pos_x >= 0 && (pos_x as usize) < w && pos_z >= 0 && (pos_z as usize) < rows)
        || cells[pos_z as usize * w + pos_x as usize] == b'#'
    {
        return Err(Refusal("the eye stands on a non-traversable cell".to_string()));
    }
    Ok(Scene { w, rows, cells, pos_x, pos_z, facing, depth, table, wall_map, floor_map, walls, floor })
}

/// The two witnesses of a scene: (frame digest, pixel sha256), with the buffers they were taken from.
pub struct Picture {
    pub strips: Vec<Strip>,
    pub frame: Vec<u8>,  // W*H index frame
    pub pixels: Vec<u8>, // W*H*3 RGB
}

impl Picture {
    pub fn frame_digest(&self) -> String {
        frame_digest(&self.frame)
    }
    pub fn pixel_sha256(&self) -> String {
        hex(&sha256(&self.pixels))
    }
}

/// Render a scene: traversal + strip + floor fill (the frame), then the texel pass (the picture).
pub fn picture(scene: &Scene) -> Picture {
    let mut strips: Vec<Strip> = Vec::with_capacity(W);
    let mut frame = vec![0u8; W * H];
    let mut pixels = vec![0u8; W * H * 3];
    scene.strips(&mut strips);
    scene.frame(&strips, &mut frame);
    scene.emit(&strips, &frame, &mut pixels);
    Picture { strips, frame, pixels }
}

// ------------------------------------------------------------------ vista: the camera and one column's strip
pub fn direction(facing: u8, column: usize) -> (i64, i64) {
    // camera-space (a, b) = (2c + 1 - W, 2 * FOCAL), carried by the facing's right/forward pair
    let a = 2 * column as i64 + 1 - W as i64;
    let b = 2 * FOCAL;
    let (fx, fz, rx, rz): (i64, i64, i64, i64) = match facing {
        0 => (0, -1, 1, 0),  // N
        1 => (1, 0, 0, 1),   // E
        2 => (0, 1, -1, 0),  // S
        _ => (-1, 0, 0, -1), // W
    };
    (rx * a + fx * b, rz * a + fz * b)
}

#[derive(Clone, Copy)]
pub struct Strip {
    pub vox_x: i64,
    pub vox_z: i64,
    pub face: u8,
    pub tn: i64,
    pub td: i64,
    pub top: i64,
    pub bot: i64,
    pub band: i64,
    pub dx: i64,
    pub dz: i64,
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
    pub fn first_hit(&self, ex: i64, ez: i64, dx: i64, dz: i64) -> Option<(i64, i64, u8, i64, i64)> {
        let n = LATTICE;
        let mut v = [ex.div_euclid(Q), EYE_Y.div_euclid(Q), ez.div_euclid(Q)];
        if v.iter().all(|&c| 0 <= c && c < n) && self.occ(v[0], v[1], v[2]) {
            return Some((v[0], v[2], 255, 0, 1)); // started inside rock: no entry face (vista refuses this)
        }
        let d = [dx, 0i64, dz];
        let mut step = [0i64; 3];
        let mut num = [0i64; 3];
        let mut den = [0i64; 3];
        let mut active = [false; 3];
        for i in [0usize, 2usize] {
            if d[i] == 0 {
                continue;
            }
            active[i] = true;
            step[i] = if d[i] > 0 { 1 } else { -1 };
            let e = if i == 0 { ex } else { ez };
            let boundary = if d[i] > 0 { (v[i] + 1) * Q } else { v[i] * Q };
            num[i] = if d[i] > 0 { boundary - e } else { e - boundary };
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
            num[axis] += Q;
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
            let (dx, dz) = direction(self.facing, c);
            let (vx, vz, face, tn, td) = match self.first_hit(ex, ez, dx, dz) {
                Some(h) => h,
                None => refuse(&format!("the ray at column {} left the world", c)),
            };
            if face == 255 {
                refuse("the ray started inside rock");
            }
            // h = h2n / h2d = 64 * td / tn; the strip is the rows whose centres lie between the wall's edges
            let h2n = FOCAL * EYE_Y * td;
            let h2d = 2 * FOCAL * tn;
            let top = CY - (2 * h2n + h2d).div_euclid(2 * h2d);
            let bot = CY + (2 * h2n - h2d).div_euclid(2 * h2d);
            let band = ((2 * FOCAL * tn).div_euclid(td * Q)).min(BANDS - 1);
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
                let wx = (ex * kk + s.dx * EYE_Y).div_euclid(kk * Q);
                let wz = (ez * kk + s.dz * EYE_Y).div_euclid(kk * Q);
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
                let kk = 2 * (r as i64 - CY) + 1;
                let den = kk * Q;
                let tj = texel((ez * kk + dz * EYE_Y).rem_euclid(den), den);
                let ti_f = texel((ex * kk + dx * EYE_Y).rem_euclid(den), den);
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
pub fn texel(num: i64, den: i64) -> i64 {
    let i = (num * T).div_euclid(den);
    if i >= T {
        T - 1
    } else if i < 0 {
        0
    } else {
        i
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
