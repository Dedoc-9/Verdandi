// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/formats.rs — the studio's frozen input formats and their composition into the kernel's scene.
//
// The authority is split three ways and this file keeps the split literal:
//
//     W  the level    VRDNLVL1 | u32 w | u32 rows | w*rows cells | u32 depth | 768 table | 32*256 wall_map
//                     | 32*256 floor_map            W = sha256 of the file bytes
//     M  the tiles    VRDNTIL1 | 4 * 196608 wall tiles (one per light family) | 196608 floor tile
//                                                   M = sha256 of the file bytes
//     C  the camera   (pos_x, pos_z, facing N/E/S/W) — carried beside W and M, inside neither
//
// compose() writes the URDRMNTI bytes the kernel reads (the format the oracle fixes) from those three.
// Every function here is pure and refuses typed; nothing here renders, opens a window, or minds a clock.

use super::mantle::{Refusal, LATTICE, TILE_BYTES};

pub const MAGIC_LVL: &[u8] = b"VRDNLVL1";
pub const MAGIC_TIL: &[u8] = b"VRDNTIL1";
pub const ALPHABET: &[u8] = b"#.<>";

pub struct Level {
    pub w: usize,
    pub rows: usize,
    pub cells: Vec<u8>,
    pub depth: u32,
    pub table: Vec<u8>,
    pub wall_map: Vec<u8>,
    pub floor_map: Vec<u8>,
}

pub struct Tiles {
    pub walls: Vec<Vec<u8>>,
    pub floor: Vec<u8>,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Camera {
    pub x: i64,
    pub z: i64,
    pub facing: u8, // 0 N, 1 E, 2 S, 3 W
}

fn take<'a>(data: &'a [u8], p: &mut usize, n: usize) -> Result<&'a [u8], Refusal> {
    if *p + n > data.len() {
        return Err(Refusal("input truncated".to_string()));
    }
    let s = &data[*p..*p + n];
    *p += n;
    Ok(s)
}

fn u32_at(s: &[u8]) -> u32 {
    u32::from_le_bytes([s[0], s[1], s[2], s[3]])
}

pub fn parse_level(data: &[u8]) -> Result<Level, Refusal> {
    let mut p = 0usize;
    if take(data, &mut p, 8)? != MAGIC_LVL {
        return Err(Refusal("level magic is not VRDNLVL1".to_string()));
    }
    let w = u32_at(take(data, &mut p, 4)?) as usize;
    let rows = u32_at(take(data, &mut p, 4)?) as usize;
    if w == 0 || rows == 0 || w as i64 > LATTICE || rows as i64 > LATTICE {
        return Err(Refusal("level extent outside the lattice".to_string()));
    }
    let cells = take(data, &mut p, w * rows)?.to_vec();
    if let Some(&c) = cells.iter().find(|c| !ALPHABET.contains(c)) {
        return Err(Refusal(format!("cell byte {} is not in the alphabet #.<>", c)));
    }
    let depth = u32_at(take(data, &mut p, 4)?);
    let table = take(data, &mut p, 768)?.to_vec();
    let wall_map = take(data, &mut p, 32 * 256)?.to_vec();
    let floor_map = take(data, &mut p, 32 * 256)?.to_vec();
    if p != data.len() {
        return Err(Refusal("level has trailing bytes".to_string()));
    }
    Ok(Level { w, rows, cells, depth, table, wall_map, floor_map })
}

pub fn level_bytes(l: &Level) -> Vec<u8> {
    let mut out = Vec::with_capacity(8 + 8 + l.cells.len() + 4 + 768 + 2 * 32 * 256);
    out.extend_from_slice(MAGIC_LVL);
    out.extend_from_slice(&(l.w as u32).to_le_bytes());
    out.extend_from_slice(&(l.rows as u32).to_le_bytes());
    out.extend_from_slice(&l.cells);
    out.extend_from_slice(&l.depth.to_le_bytes());
    out.extend_from_slice(&l.table);
    out.extend_from_slice(&l.wall_map);
    out.extend_from_slice(&l.floor_map);
    out
}

pub fn parse_tiles(data: &[u8]) -> Result<Tiles, Refusal> {
    let mut p = 0usize;
    if take(data, &mut p, 8)? != MAGIC_TIL {
        return Err(Refusal("tiles magic is not VRDNTIL1".to_string()));
    }
    let mut walls = Vec::with_capacity(4);
    for _ in 0..4 {
        walls.push(take(data, &mut p, TILE_BYTES)?.to_vec());
    }
    let floor = take(data, &mut p, TILE_BYTES)?.to_vec();
    if p != data.len() {
        return Err(Refusal("tiles have trailing bytes".to_string()));
    }
    Ok(Tiles { walls, floor })
}

pub fn tiles_bytes(t: &Tiles) -> Vec<u8> {
    let mut out = Vec::with_capacity(8 + 5 * TILE_BYTES);
    out.extend_from_slice(MAGIC_TIL);
    for w in &t.walls {
        out.extend_from_slice(w);
    }
    out.extend_from_slice(&t.floor);
    out
}

/// "x,z,F" with F in N E S W (also accepts 0..3).
pub fn parse_camera(s: &str) -> Result<Camera, Refusal> {
    let parts: Vec<&str> = s.split(',').collect();
    if parts.len() != 3 {
        return Err(Refusal(format!("camera {:?} is not x,z,F", s)));
    }
    let x: i64 = parts[0].trim().parse().map_err(|_| Refusal(format!("camera x {:?}", parts[0])))?;
    let z: i64 = parts[1].trim().parse().map_err(|_| Refusal(format!("camera z {:?}", parts[1])))?;
    let facing = match parts[2].trim() {
        "N" | "0" => 0,
        "E" | "1" => 1,
        "S" | "2" => 2,
        "W" | "3" => 3,
        other => return Err(Refusal(format!("camera facing {:?} is not N/E/S/W", other))),
    };
    Ok(Camera { x, z, facing })
}

pub fn facing_letter(f: u8) -> &'static str {
    match f {
        0 => "N",
        1 => "E",
        2 => "S",
        _ => "W",
    }
}

/// The kernel's input, composed: W + C + M -> URDRMNTI bytes. The camera must stand on a traversable cell
/// of THIS level (validated by the kernel's own parser when the bytes are read).
pub fn compose(level: &Level, camera: Camera, tiles: &Tiles) -> Vec<u8> {
    let mut out = Vec::with_capacity(8 + 8 + level.cells.len() + 13 + 768 + 2 * 32 * 256 + 5 * TILE_BYTES);
    out.extend_from_slice(b"URDRMNTI");
    out.extend_from_slice(&(level.w as u32).to_le_bytes());
    out.extend_from_slice(&(level.rows as u32).to_le_bytes());
    out.extend_from_slice(&level.cells);
    out.extend_from_slice(&(camera.x as i32).to_le_bytes());
    out.extend_from_slice(&(camera.z as i32).to_le_bytes());
    out.push(camera.facing);
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
