// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/vocab.rs — THE BEARING VOCABULARY (BEARING-0): the registered rational directions of urdr-oracle-2,
// carried, never chosen, and the bearing camera C = (cell_x, cell_z, heading id) composed into the scene.
//
// A heading is an integer id k with 0 <= k < 360000 — millidegrees clockwise from north — and the id is the
// authority: it names one primitive Pythagorean triple (A, B, C), A^2 + B^2 = C^2, forward (A/C, B/C) in the
// level's (x, z) axes (z grows south), screen-right (-B/C, A/C). The triples are the oracle's DATA: the octant
// k = 0..45000 as 45,001 lines "p q" in ../oracle/bearing_octant.txt (carried verbatim from Urðr at the tag
// urdr-oracle-2), compiled in and checked against the sha256 the oracle record pins BEFORE any triple is read —
// a file that does not match refuses, and nothing here regenerates it. The rest of the circle follows by exact
// symmetry (the record's `expansion`): r <= 45000 gives (2pq, -(q^2 - p^2), p^2 + q^2) from pair r; 45000 < r <
// 90000 gives (q^2 - p^2, -2pq, p^2 + q^2) from pair 90000 - r; reduced by the gcd; then each quarter turn
// (A, B) -> (-B, A). The largest hypotenuse is 8,404,122,277 (about 2^33), so i64 holds every triple.
//
// An id is read from text only in its canonical decimal form (no sign, no leading zero, no whitespace) and only
// inside [0, 360000): anything else refuses, never normalized. Every function here is pure and refuses typed;
// nothing here renders, opens a window, reads a clock or touches a file at run time.

use super::formats::{Level, Tiles};
use super::mantle::{hex, sha256, Refusal};

pub const YAW_MOD: i64 = 360_000;
pub const QUARTER: i64 = YAW_MOD / 4;
pub const OCTANT: i64 = QUARTER / 2;
/// The octant file's sha256, as urdr-oracle-2.json's `vocabulary.octant_sha256` pins it.
pub const OCTANT_SHA256: &str = "f70b2fc20ba8ea8fde7f802ae0f1180ae003d2de5acb963524ca58421405a82c";
/// The carried file, compiled in.
pub const OCTANT_FILE: &[u8] = include_bytes!("../oracle/bearing_octant.txt");
pub const MAGIC_BRG: &[u8] = b"URDRBRG1";

fn no(msg: String) -> Refusal {
    Refusal(format!("BEARING-REFUSE: {}", msg))
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

/// The registered vocabulary: the octant's pairs, read from the carried bytes after their pin is checked.
pub struct Vocab {
    pairs: Vec<(i64, i64)>,
}

/// The carried octant, checked against its pin first, then parsed and checked canonical (0 <= p < q, gcd 1,
/// exactly OCTANT + 1 lines, id 0 is (0, 1)). Fail-closed: any difference refuses.
pub fn load() -> Result<Vocab, Refusal> {
    load_bytes(OCTANT_FILE)
}

pub fn load_bytes(data: &[u8]) -> Result<Vocab, Refusal> {
    let got = hex(&sha256(data));
    if got != OCTANT_SHA256 {
        return Err(no(format!("the octant's sha256 {} is not the pinned {} — refused, never regenerated", &got[..16], &OCTANT_SHA256[..16])));
    }
    let text = std::str::from_utf8(data).map_err(|_| no("the octant is not text".to_string()))?;
    let mut pairs = Vec::with_capacity((OCTANT + 1) as usize);
    for ln in text.split('\n') {
        if ln.is_empty() {
            continue;
        }
        let mut it = ln.split(' ');
        let (p, q) = match (it.next(), it.next(), it.next()) {
            (Some(p), Some(q), None) => (p, q),
            _ => return Err(no(format!("octant line {} is not 'p q'", pairs.len()))),
        };
        let p: i64 = p.parse().map_err(|_| no(format!("octant line {}: p", pairs.len())))?;
        let q: i64 = q.parse().map_err(|_| no(format!("octant line {}: q", pairs.len())))?;
        if !(0 <= p && p < q && gcd(p, q) == 1) {
            return Err(no(format!("octant line {} is not a canonical pair", pairs.len())));
        }
        pairs.push((p, q));
    }
    if pairs.len() != (OCTANT + 1) as usize || pairs[0] != (0, 1) {
        return Err(no(format!("the octant has {} pairs, or id 0 is not (0, 1)", pairs.len())));
    }
    Ok(Vocab { pairs })
}

/// An id from text: canonical decimal only, inside [0, 360000).
pub fn parse_id(s: &str) -> Result<i64, Refusal> {
    let ok = !s.is_empty() && s.bytes().all(|c| c.is_ascii_digit()) && (s == "0" || !s.starts_with('0')) && s.len() <= 6;
    if !ok {
        return Err(no(format!("heading {:?} is not an id in canonical decimal — refused, never normalized", s)));
    }
    let k: i64 = s.parse().map_err(|_| no(format!("heading {:?}", s)))?;
    check_id(k)?;
    Ok(k)
}

pub fn check_id(k: i64) -> Result<(), Refusal> {
    if !(0 <= k && k < YAW_MOD) {
        return Err(no(format!("heading {} outside [0, {}) — refused, never normalized", k, YAW_MOD)));
    }
    Ok(())
}

impl Vocab {
    /// The id's triple (A, B, C), by the record's expansion.
    pub fn triple(&self, k: i64) -> Result<(i64, i64, i64), Refusal> {
        check_id(k)?;
        let (turns, r) = (k / QUARTER, k % QUARTER);
        let (mut a, mut b, c);
        if r <= OCTANT {
            let (p, q) = self.pairs[r as usize];
            a = 2 * p * q;
            b = -(q * q - p * p);
            c = p * p + q * q;
        } else {
            let (p, q) = self.pairs[(QUARTER - r) as usize];
            a = q * q - p * p;
            b = -2 * p * q;
            c = p * p + q * q;
        }
        let g = gcd(gcd(a, b), c);
        a /= g;
        b /= g;
        let c = c / g;
        for _ in 0..turns {
            let t = a;
            a = -b;
            b = t;
        }
        Ok((a, b, c))
    }

    /// The vocabulary's identity, as the record's `table_digest_rule` states it: sha256 of
    /// "URDRBRG1|table|" followed by "A,B,C;" for every id 0..359999 in order.
    pub fn table_digest(&self) -> String {
        let mut ser: Vec<u8> = Vec::with_capacity(16 + 360_000 * 28);
        ser.extend_from_slice(MAGIC_BRG);
        ser.extend_from_slice(b"|table|");
        for k in 0..YAW_MOD {
            let (a, b, c) = self.triple(k).expect("an id inside the range");
            ser.extend_from_slice(format!("{},{},{};", a, b, c).as_bytes());
        }
        hex(&sha256(&ser))
    }
}

/// The bearing camera: a cell and a heading id. The id is authoritative; its triple is the vocabulary's.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct BearingCamera {
    pub x: i64,
    pub z: i64,
    pub k: i64,
}

/// "x,z,K" with K a heading id in canonical decimal.
pub fn parse_at(s: &str) -> Result<BearingCamera, Refusal> {
    let parts: Vec<&str> = s.split(',').collect();
    if parts.len() != 3 {
        return Err(no(format!("bearing camera {:?} is not x,z,K", s)));
    }
    let x: i64 = parts[0].trim().parse().map_err(|_| no(format!("camera x {:?}", parts[0])))?;
    let z: i64 = parts[1].trim().parse().map_err(|_| no(format!("camera z {:?}", parts[1])))?;
    let k = parse_id(parts[2])?;
    Ok(BearingCamera { x, z, k })
}

/// The bearing kernel's input, composed: W + C + M -> URDRBRGI bytes, the format urdr-oracle-2's
/// `kernel_input` fixes. The eye must stand on a traversable cell of THIS level (checked by the bearing
/// kernel's own parser when the bytes are read).
pub fn compose(level: &Level, cam: BearingCamera, triple: (i64, i64, i64), tiles: &Tiles) -> Vec<u8> {
    let mut out = Vec::with_capacity(8 + 8 + level.cells.len() + 36 + 768 + 2 * 32 * 256 + 5 * 196_608);
    out.extend_from_slice(b"URDRBRGI");
    out.extend_from_slice(&(level.w as u32).to_le_bytes());
    out.extend_from_slice(&(level.rows as u32).to_le_bytes());
    out.extend_from_slice(&level.cells);
    out.extend_from_slice(&(cam.x as i32).to_le_bytes());
    out.extend_from_slice(&(cam.z as i32).to_le_bytes());
    out.extend_from_slice(&triple.0.to_le_bytes());
    out.extend_from_slice(&triple.1.to_le_bytes());
    out.extend_from_slice(&triple.2.to_le_bytes());
    out.extend_from_slice(&level.depth.to_le_bytes());
    out.extend_from_slice(&level.table);
    out.extend_from_slice(&level.wall_map);
    out.extend_from_slice(&level.floor_map);
    for w in &tiles.walls {
        out.extend_from_slice(w);
    }
    out.extend_from_slice(&tiles.floor);
    out
}
