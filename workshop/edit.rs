// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// workshop/edit.rs — WORKSHOP-0: an edit is a new authority, and the witnesses say what it moved.
//
// The authority is split three ways and every record keeps them apart:
//
//     W  the level  (cells, depth, the depth's table and band maps)   W = sha256 of the level file
//     M  the tiles  (the material set)                                 M = sha256 of the tiles file
//     C  the camera (pos, facing) — CARRIED through an edit untouched: a view mutation is not an edit
//
// An edit goes  old authority ──validate──▶ new authority ──kernel──▶ witnesses ──diff──▶ consequence,
// and the consequence is measured, never estimated: three witnesses before and after — the exact strips
// (geometry at the kernel's own grain: voxel, face, tn/td, top, bot, band per column), the URDRFB1 frame
// digest (geometry at the index grain) and the pixel sha (appearance) — the columns whose strip or index
// changed, the pixels that differ. The old authority is never mutated: the new level and tiles are written
// as files beside the record (the world survives the app), and the record is what a verifier re-derives —
// `check` recomputes every hash from the files and refuses, typed, when the record's projection is stale
// under a moved authority (STALE-PROJECTION), when a projection moved with no authority behind it
// (PROJECTION-WITHOUT-AUTHORITY), when the camera moved (CAMERA-MOVED), or when an edit could not play
// (INVALID-EDIT: a cell outside the level or the alphabet, a camera left in rock, an opened border).
//
// WORKSHOP-0b — THE TRUTH TABLE, POPULATED. The consequence is classified by an exhaustive match over
// (W moved, M moved, strips moved, frame moved, pixels moved) into a recorded SIGNATURE: identity,
// outside-view (the authority moved and nothing on screen did — 1,308 of the 1,379 single-cell edits of the
// witness level under its camera; the normal case in a workshop, never a fault), geometry, material,
// geometry+material, sub-index (strips and pixels moved, the index frame did not — possible in principle,
// unseen in the census). Only the arms the kernel makes impossible are refused (CONSEQUENCE-IMPOSSIBLE).
// The laws are one-directional, with the camera carried: pixels moved => strips moved or index moved or
// M moved; frame moved => strips moved. `columns_unexplained` — columns whose pixels moved with no strip,
// no index and no material behind them — is a field whose law is zero. A biconditional
// (authority moved <=> projection moved) was proposed and measured false (`edit census`).
//
//     rustc -O workshop/edit.rs -o build/edit
//     edit record --level L.lvl --tiles T.tiles --camera x,z,F --edit SPEC --out-dir DIR --name NAME
//         SPEC:  cell:X,Z,C      one cell to C in '#.<>'
//                tile:CLASS,R,G,B   one material recoloured flat; CLASS = wall0..wall3 (light family) | floor
//                level:PATH.lvl  another authority entirely (the seed edit: a frozen level from the oracle)
//                none            the identity edit
//         writes DIR/NAME.before.lvl .before.tiles .after.lvl .after.tiles and DIR/NAME.record.json
//     edit check --record DIR/NAME.record.json
//         prints `CHECK OK ...` (exit 0) or `WORKSHOP-REFUSE: CODE detail` (exit 2)
//     edit census --level L.lvl --tiles T.tiles --camera x,z,F --out FILE.json
//         off-gate instrument: every single-cell flip of the level (rock <-> floor; stairs to floor) under
//         the carried camera, each classified; the signature counts, three examples per signature, the
//         unexplained-column total (law: 0), the base witnesses. No clock, so the record is reproducible.
//
// This file calls the kernel; it never draws, never opens a window, never reads a clock. std-only.

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::exit;

use formats::{compose, facing_letter, level_bytes, parse_camera, parse_level, parse_tiles, tiles_bytes, Camera, Level, Tiles, ALPHABET};
use mantle::{hex, parse_scene, picture, sha256, Picture, Refusal, Strip, H, W};

// ------------------------------------------------------------------ typed refusal
fn refuse(code: &str, detail: &str) -> ! {
    println!("WORKSHOP-REFUSE: {} {}", code, detail);
    exit(2)
}

fn read(path: &Path) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path.display(), e)))
}

fn write(path: &Path, bytes: &[u8]) {
    fs::write(path, bytes).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", path.display(), e)))
}

// ------------------------------------------------------------------ a minimal JSON (enough for a record)
#[derive(Clone, Debug, PartialEq)]
enum Json {
    Null,
    Bool(bool),
    Num(i64),
    Str(String),
    Arr(Vec<Json>),
    Obj(BTreeMap<String, Json>),
}

impl Json {
    fn get(&self, key: &str) -> &Json {
        match self {
            Json::Obj(m) => m.get(key).unwrap_or(&Json::Null),
            _ => &Json::Null,
        }
    }
    fn str(&self) -> &str {
        match self {
            Json::Str(s) => s,
            _ => "",
        }
    }
    fn num(&self) -> i64 {
        match self {
            Json::Num(n) => *n,
            _ => -1,
        }
    }
    fn boolean(&self) -> bool {
        matches!(self, Json::Bool(true))
    }
    fn arr(&self) -> &[Json] {
        match self {
            Json::Arr(a) => a,
            _ => &[],
        }
    }
}

fn json_escape(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn json_write(v: &Json, indent: usize, out: &mut String) {
    let pad = " ".repeat(indent);
    match v {
        Json::Null => out.push_str("null"),
        Json::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Json::Num(n) => out.push_str(&n.to_string()),
        Json::Str(s) => out.push_str(&json_escape(s)),
        Json::Arr(a) => {
            out.push('[');
            for (i, x) in a.iter().enumerate() {
                if i > 0 {
                    out.push_str(", ");
                }
                json_write(x, indent, out);
            }
            out.push(']');
        }
        Json::Obj(m) => {
            out.push_str("{\n");
            let n = m.len();
            for (i, (k, x)) in m.iter().enumerate() {
                out.push_str(&pad);
                out.push(' ');
                out.push_str(&json_escape(k));
                out.push_str(": ");
                json_write(x, indent + 1, out);
                out.push_str(if i + 1 < n { ",\n" } else { "\n" });
            }
            out.push_str(&pad);
            out.push('}');
        }
    }
}

struct Parser<'a> {
    s: &'a [u8],
    p: usize,
}

impl<'a> Parser<'a> {
    fn ws(&mut self) {
        while self.p < self.s.len() && matches!(self.s[self.p], b' ' | b'\n' | b'\r' | b'\t') {
            self.p += 1;
        }
    }
    fn expect(&mut self, c: u8) -> Result<(), String> {
        self.ws();
        if self.p < self.s.len() && self.s[self.p] == c {
            self.p += 1;
            Ok(())
        } else {
            Err(format!("expected '{}' at byte {}", c as char, self.p))
        }
    }
    fn value(&mut self) -> Result<Json, String> {
        self.ws();
        if self.p >= self.s.len() {
            return Err("unexpected end".to_string());
        }
        match self.s[self.p] {
            b'{' => {
                self.p += 1;
                let mut m = BTreeMap::new();
                self.ws();
                if self.p < self.s.len() && self.s[self.p] == b'}' {
                    self.p += 1;
                    return Ok(Json::Obj(m));
                }
                loop {
                    self.ws();
                    let k = match self.value()? {
                        Json::Str(k) => k,
                        _ => return Err("object key is not a string".to_string()),
                    };
                    self.expect(b':')?;
                    let v = self.value()?;
                    m.insert(k, v);
                    self.ws();
                    if self.p < self.s.len() && self.s[self.p] == b',' {
                        self.p += 1;
                        continue;
                    }
                    self.expect(b'}')?;
                    return Ok(Json::Obj(m));
                }
            }
            b'[' => {
                self.p += 1;
                let mut a = Vec::new();
                self.ws();
                if self.p < self.s.len() && self.s[self.p] == b']' {
                    self.p += 1;
                    return Ok(Json::Arr(a));
                }
                loop {
                    a.push(self.value()?);
                    self.ws();
                    if self.p < self.s.len() && self.s[self.p] == b',' {
                        self.p += 1;
                        continue;
                    }
                    self.expect(b']')?;
                    return Ok(Json::Arr(a));
                }
            }
            b'"' => {
                self.p += 1;
                let mut out = String::new();
                loop {
                    if self.p >= self.s.len() {
                        return Err("unterminated string".to_string());
                    }
                    let c = self.s[self.p];
                    self.p += 1;
                    match c {
                        b'"' => return Ok(Json::Str(out)),
                        b'\\' => {
                            if self.p >= self.s.len() {
                                return Err("bad escape".to_string());
                            }
                            let e = self.s[self.p];
                            self.p += 1;
                            match e {
                                b'"' => out.push('"'),
                                b'\\' => out.push('\\'),
                                b'/' => out.push('/'),
                                b'n' => out.push('\n'),
                                b'r' => out.push('\r'),
                                b't' => out.push('\t'),
                                b'u' => {
                                    if self.p + 4 > self.s.len() {
                                        return Err("bad \\u escape".to_string());
                                    }
                                    let h = std::str::from_utf8(&self.s[self.p..self.p + 4]).map_err(|_| "bad \\u escape")?;
                                    let cp = u32::from_str_radix(h, 16).map_err(|_| "bad \\u escape")?;
                                    out.push(char::from_u32(cp).unwrap_or('\u{fffd}'));
                                    self.p += 4;
                                }
                                _ => return Err("bad escape".to_string()),
                            }
                        }
                        _ => {
                            // copy one UTF-8 scalar
                            let start = self.p - 1;
                            let len = match c {
                                0x00..=0x7f => 1,
                                0xc0..=0xdf => 2,
                                0xe0..=0xef => 3,
                                _ => 4,
                            };
                            let end = (start + len).min(self.s.len());
                            out.push_str(std::str::from_utf8(&self.s[start..end]).map_err(|_| "bad utf-8")?);
                            self.p = end;
                        }
                    }
                }
            }
            b't' if self.s[self.p..].starts_with(b"true") => {
                self.p += 4;
                Ok(Json::Bool(true))
            }
            b'f' if self.s[self.p..].starts_with(b"false") => {
                self.p += 5;
                Ok(Json::Bool(false))
            }
            b'n' if self.s[self.p..].starts_with(b"null") => {
                self.p += 4;
                Ok(Json::Null)
            }
            b'-' | b'0'..=b'9' => {
                let start = self.p;
                self.p += 1;
                while self.p < self.s.len() && self.s[self.p].is_ascii_digit() {
                    self.p += 1;
                }
                let t = std::str::from_utf8(&self.s[start..self.p]).map_err(|_| "bad number")?;
                t.parse::<i64>().map(Json::Num).map_err(|_| format!("bad number {:?}", t))
            }
            c => Err(format!("unexpected byte '{}' at {}", c as char, self.p)),
        }
    }
}

fn json_parse(s: &[u8]) -> Result<Json, String> {
    let mut p = Parser { s, p: 0 };
    let v = p.value()?;
    p.ws();
    if p.p != s.len() {
        return Err("trailing bytes after the document".to_string());
    }
    Ok(v)
}

/// Canonical JSON — the Rust twin of verify/envelope.py::canonical: keys by code point (BTreeMap's byte
/// order is code-point order for UTF-8), no whitespace, integers only, the same escapes.
fn json_canonical(v: &Json, out: &mut String) {
    match v {
        Json::Null => out.push_str("null"),
        Json::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Json::Num(n) => out.push_str(&n.to_string()),
        Json::Str(s) => out.push_str(&json_escape(s)),
        Json::Arr(a) => {
            out.push('[');
            for (i, x) in a.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                json_canonical(x, out);
            }
            out.push(']');
        }
        Json::Obj(m) => {
            out.push('{');
            for (i, (k, x)) in m.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push_str(&json_escape(k));
                out.push(':');
                json_canonical(x, out);
            }
            out.push('}');
        }
    }
}

// ------------------------------------------------------------------ RECORD-0: the envelope (twin of verify/envelope.py)
const CLAIM_CLASSES: [&str; 4] = ["measured", "established", "declared", "predicted"];
const REQUIRED: [&str; 7] = ["name", "version", "claim_class", "provenance", "validity_scope", "forbidden_interpretations", "data"];
const VERDICT_KEYS: [&str; 17] = [
    "verdict", "valid", "passed", "healthy", "anomaly", "correct", "legal", "safe", "approved", "score_is_good",
    "ok", "pass", "fail", "failed", "status", "within", "over",
];

fn envelope_chain_hash(rec: &Json) -> String {
    let mut m = BTreeMap::new();
    for k in REQUIRED {
        m.insert(k.to_string(), rec.get(k).clone());
    }
    let mut text = String::new();
    json_canonical(&Json::Obj(m), &mut text);
    hex(&sha256(text.as_bytes()))
}

fn envelope_scan(node: &Json, path: &str) -> Result<(), String> {
    match node {
        Json::Obj(m) => {
            for (k, v) in m {
                if VERDICT_KEYS.contains(&k.to_lowercase().as_str()) {
                    return Err(format!("verdict_field:{}.{}", path, k));
                }
                envelope_scan(v, &format!("{}.{}", path, k))?;
            }
        }
        Json::Arr(a) => {
            for (i, v) in a.iter().enumerate() {
                envelope_scan(v, &format!("{}[{}]", path, i))?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn envelope_validate(rec: &Json) -> Result<(), String> {
    for k in REQUIRED {
        let v = rec.get(k);
        let empty = matches!(v, Json::Null) || v.str() == "" && matches!(v, Json::Str(_)) || v.arr().is_empty() && matches!(v, Json::Arr(_))
            || matches!(v, Json::Obj(m) if m.is_empty());
        if empty {
            return Err(format!("missing_or_empty:{}", k));
        }
    }
    if !CLAIM_CLASSES.contains(&rec.get("claim_class").str()) {
        return Err(format!("claim_class:{}", rec.get("claim_class").str()));
    }
    if rec.get("validity_scope").get("certifies").str().is_empty() {
        return Err("validity_scope.certifies required".to_string());
    }
    let fi = rec.get("forbidden_interpretations").arr();
    if fi.is_empty() || fi.iter().any(|x| x.str().is_empty()) {
        return Err("forbidden_interpretations must be a non-empty list of strings".to_string());
    }
    if !matches!(rec.get("version"), Json::Num(_)) {
        return Err("version must be an integer".to_string());
    }
    envelope_scan(rec.get("data"), "data")?;
    if rec.get("chain_hash").str() != envelope_chain_hash(rec) {
        return Err("chain_hash does not match the required fields".to_string());
    }
    Ok(())
}

/// Build a sealed record; refuses (typed) if the envelope's own rules are broken.
fn envelope_seal(name: &str, version: i64, claim_class: &str, provenance: Json, validity_scope: Json, forbidden: Vec<&str>, data: Json, reading: &str) -> Json {
    let mut rec = obj(vec![
        ("name", Json::Str(name.to_string())),
        ("version", Json::Num(version)),
        ("claim_class", Json::Str(claim_class.to_string())),
        ("provenance", provenance),
        ("validity_scope", validity_scope),
        ("forbidden_interpretations", Json::Arr(forbidden.into_iter().map(|s| Json::Str(s.to_string())).collect())),
        ("data", data),
        ("reading", Json::Str(reading.to_string())),
    ]);
    let h = envelope_chain_hash(&rec);
    if let Json::Obj(m) = &mut rec {
        m.insert("chain_hash".to_string(), Json::Str(h));
    }
    envelope_validate(&rec).unwrap_or_else(|m| refuse("ENVELOPE", &m));
    rec
}

fn obj(pairs: Vec<(&str, Json)>) -> Json {
    Json::Obj(pairs.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
}

// ------------------------------------------------------------------ the edit
#[derive(Clone, Debug, PartialEq)]
enum Edit {
    None,
    Cell { x: usize, z: usize, to: u8 },
    Tile { class: String, rgb: [u8; 3] },
    Level { path: String },
}

fn parse_edit(spec: &str) -> Result<Edit, String> {
    if spec == "none" {
        return Ok(Edit::None);
    }
    let (kind, rest) = spec.split_once(':').ok_or_else(|| format!("edit {:?} has no kind", spec))?;
    match kind {
        "cell" => {
            let parts: Vec<&str> = rest.split(',').collect();
            if parts.len() != 3 {
                return Err("cell edit is cell:X,Z,C".to_string());
            }
            let x = parts[0].trim().parse::<usize>().map_err(|_| "cell X")?;
            let z = parts[1].trim().parse::<usize>().map_err(|_| "cell Z")?;
            let c = parts[2].trim().as_bytes();
            if c.len() != 1 || !ALPHABET.contains(&c[0]) {
                return Err(format!("cell value {:?} is not one of # . < >", parts[2]));
            }
            Ok(Edit::Cell { x, z, to: c[0] })
        }
        "tile" => {
            let parts: Vec<&str> = rest.split(',').collect();
            if parts.len() != 4 {
                return Err("tile edit is tile:CLASS,R,G,B".to_string());
            }
            let class = parts[0].trim().to_string();
            if !matches!(class.as_str(), "wall0" | "wall1" | "wall2" | "wall3" | "floor") {
                return Err(format!("tile class {:?} is not wall0..wall3 or floor", class));
            }
            let mut rgb = [0u8; 3];
            for (i, p) in parts[1..].iter().enumerate() {
                rgb[i] = p.trim().parse::<u8>().map_err(|_| format!("tile channel {:?}", p))?;
            }
            Ok(Edit::Tile { class, rgb })
        }
        "level" => Ok(Edit::Level { path: rest.to_string() }),
        other => Err(format!("edit kind {:?} is not cell, tile, level or none", other)),
    }
}

fn edit_json(e: &Edit) -> Json {
    match e {
        Edit::None => obj(vec![("kind", Json::Str("none".into()))]),
        Edit::Cell { x, z, to } => obj(vec![
            ("kind", Json::Str("cell".into())),
            ("x", Json::Num(*x as i64)),
            ("z", Json::Num(*z as i64)),
            ("to", Json::Str((*to as char).to_string())),
        ]),
        Edit::Tile { class, rgb } => obj(vec![
            ("kind", Json::Str("tile".into())),
            ("class", Json::Str(class.clone())),
            ("rgb", Json::Arr(rgb.iter().map(|c| Json::Num(*c as i64)).collect())),
        ]),
        Edit::Level { path } => obj(vec![("kind", Json::Str("level".into())), ("level", Json::Str(path.clone()))]),
    }
}

fn edit_from_json(v: &Json, record_dir: &Path) -> Result<Edit, String> {
    match v.get("kind").str() {
        "none" => Ok(Edit::None),
        "cell" => {
            let to = v.get("to").str().as_bytes();
            if to.len() != 1 || !ALPHABET.contains(&to[0]) {
                return Err("cell edit's target value".to_string());
            }
            let (x, z) = (v.get("x").num(), v.get("z").num());
            if x < 0 || z < 0 {
                return Err("cell edit's coordinates".to_string());
            }
            Ok(Edit::Cell { x: x as usize, z: z as usize, to: to[0] })
        }
        "tile" => {
            let a = v.get("rgb").arr();
            if a.len() != 3 || a.iter().any(|c| c.num() < 0 || c.num() > 255) {
                return Err("tile edit's rgb".to_string());
            }
            Ok(Edit::Tile { class: v.get("class").str().to_string(), rgb: [a[0].num() as u8, a[1].num() as u8, a[2].num() as u8] })
        }
        "level" => Ok(Edit::Level { path: record_dir.join(v.get("level").str()).to_string_lossy().into_owned() }),
        other => Err(format!("edit kind {:?}", other)),
    }
}

/// Apply an edit to (level, tiles): a NEW level and tiles, the old ones untouched. Validates before it
/// returns: the cell in range and in the alphabet, the border still rock, the carried camera still on a
/// traversable cell of the new level, the tile class known. Err = INVALID-EDIT detail.
fn apply(level: &Level, tiles: &Tiles, camera: Camera, edit: &Edit) -> Result<(Level, Tiles), String> {
    let mut new_level = Level {
        w: level.w,
        rows: level.rows,
        cells: level.cells.clone(),
        depth: level.depth,
        table: level.table.clone(),
        wall_map: level.wall_map.clone(),
        floor_map: level.floor_map.clone(),
    };
    let mut new_tiles = Tiles { walls: tiles.walls.clone(), floor: tiles.floor.clone() };
    match edit {
        Edit::None => {}
        Edit::Cell { x, z, to } => {
            if *x >= level.w || *z >= level.rows {
                return Err(format!("cell ({}, {}) is outside the {}x{} level", x, z, level.w, level.rows));
            }
            let border = *x == 0 || *z == 0 || *x == level.w - 1 || *z == level.rows - 1;
            if border && *to != b'#' {
                return Err(format!("cell ({}, {}) is on the border, which must stay rock", x, z));
            }
            new_level.cells[z * level.w + x] = *to;
        }
        Edit::Tile { class, rgb } => {
            let tile: &mut Vec<u8> = match class.as_str() {
                "floor" => &mut new_tiles.floor,
                "wall0" => &mut new_tiles.walls[0],
                "wall1" => &mut new_tiles.walls[1],
                "wall2" => &mut new_tiles.walls[2],
                "wall3" => &mut new_tiles.walls[3],
                other => return Err(format!("tile class {:?}", other)),
            };
            for px in tile.chunks_exact_mut(3) {
                px.copy_from_slice(rgb);
            }
        }
        Edit::Level { path } => {
            let bytes = fs::read(path).map_err(|e| format!("cannot read level {}: {}", path, e))?;
            let l = parse_level(&bytes).map_err(|Refusal(m)| format!("level {}: {}", path, m))?;
            new_level = l;
        }
    }
    // the carried camera must still play on the new authority
    let (cx, cz) = (camera.x, camera.z);
    if cx < 0 || cz < 0 || cx as usize >= new_level.w || cz as usize >= new_level.rows {
        return Err(format!("the carried camera ({}, {}) is outside the new level", cx, cz));
    }
    if new_level.cells[cz as usize * new_level.w + cx as usize] == b'#' {
        return Err(format!("the carried camera ({}, {}) would stand in rock on the new authority", cx, cz));
    }
    Ok((new_level, new_tiles))
}

// ------------------------------------------------------------------ the witnesses and the consequence
struct Side {
    w: String,
    m: String,
    strips: String,
    frame: String,
    pixels: String,
    pic: Picture,
}

/// The exact strips as bytes, column by column: voxel, face, tn, td, top, bot, band — the geometry the
/// kernel selected, before any rounding to an index. Its sha256 is the third witness.
fn strips_bytes(strips: &[Strip]) -> Vec<u8> {
    let mut out = Vec::with_capacity(strips.len() * 57);
    for s in strips {
        for v in [s.vox_x, s.vox_z, s.tn, s.td, s.top, s.bot, s.band] {
            out.extend_from_slice(&v.to_le_bytes());
        }
        out.push(s.face);
    }
    out
}

fn strip_differs(a: &Strip, b: &Strip) -> bool {
    (a.vox_x, a.vox_z, a.face, a.tn, a.td, a.top, a.bot, a.band) != (b.vox_x, b.vox_z, b.face, b.tn, b.td, b.top, b.bot, b.band)
}

fn witness(level: &Level, tiles: &Tiles, camera: Camera) -> Result<Side, String> {
    let lb = level_bytes(level);
    let tb = tiles_bytes(tiles);
    let scene_bytes = compose(level, camera, tiles);
    let scene = parse_scene(&scene_bytes).map_err(|Refusal(m)| m)?;
    let pic = picture(&scene);
    let strips = hex(&sha256(&strips_bytes(&pic.strips)));
    Ok(Side { w: hex(&sha256(&lb)), m: hex(&sha256(&tb)), strips, frame: pic.frame_digest(), pixels: pic.pixel_sha256(), pic })
}

struct Consequence {
    w_moved: bool,
    m_moved: bool,
    strips_moved: bool,
    frame_moved: bool,
    pixels_moved: bool,
    strips_changed: usize,   // columns whose exact strip differs
    index_changed: usize,    // columns whose index column differs
    columns_changed: usize,  // columns with any pixel differing
    columns_unexplained: usize, // pixel moved, no strip, no index, no material behind it — law: 0
    pixels_changed: usize,
    pixels_permille: i64,
    signature: &'static str,
}

/// The exhaustive classification. Arms the kernel makes impossible return Err (the caller refuses).
fn classify(w: bool, m: bool, strips: bool, frame: bool, pixels: bool) -> Result<&'static str, String> {
    match (w || m, strips, frame, pixels) {
        (false, false, false, false) => Ok("identity"),
        (false, _, _, _) => Err("the authority did not move and a witness did (with the camera carried, the kernel is a function of the authority)".to_string()),
        (true, false, true, _) => Err("the frame digest moved with no strip moved (the index frame is a function of the strips)".to_string()),
        (true, false, false, false) => Ok("outside-view"),
        (true, false, false, true) => {
            if m {
                Ok("material")
            } else {
                Err("pixels moved with no strip, no index and no material moved".to_string())
            }
        }
        (true, true, true, true) => Ok(if m { "geometry+material" } else { "geometry" }),
        (true, true, false, true) => Ok(if m { "sub-index+material" } else { "sub-index" }),
        (true, true, _, false) => Ok("sub-pixel"),
    }
}

fn consequence(before: &Side, after: &Side) -> Result<Consequence, String> {
    let (mut strips_changed, mut index_changed, mut columns_changed, mut columns_unexplained) = (0usize, 0usize, 0usize, 0usize);
    let mut pixels_changed = 0usize;
    let m_moved = before.m != after.m;
    for c in 0..W {
        let s_ch = strip_differs(&before.pic.strips[c], &after.pic.strips[c]);
        let mut i_ch = false;
        for r in 0..H {
            if before.pic.frame[r * W + c] != after.pic.frame[r * W + c] {
                i_ch = true;
                break;
            }
        }
        let mut p_ch = false;
        for r in 0..H {
            let o = (r * W + c) * 3;
            if before.pic.pixels[o..o + 3] != after.pic.pixels[o..o + 3] {
                p_ch = true;
                pixels_changed += 1;
            }
        }
        if s_ch {
            strips_changed += 1;
        }
        if i_ch {
            index_changed += 1;
        }
        if p_ch {
            columns_changed += 1;
            if !s_ch && !i_ch && !m_moved {
                columns_unexplained += 1;
            }
        }
    }
    let (w_moved, strips_moved, frame_moved, pixels_moved) =
        (before.w != after.w, before.strips != after.strips, before.frame != after.frame, before.pixels != after.pixels);
    if strips_moved != (strips_changed > 0) || frame_moved != (index_changed > 0) || pixels_moved != (columns_changed > 0) {
        return Err("a digest moved without a column moving, or the reverse".to_string());
    }
    let signature = classify(w_moved, m_moved, strips_moved, frame_moved, pixels_moved)?;
    if columns_unexplained != 0 {
        return Err(format!("{} columns changed pixels with no strip, no index and no material behind them", columns_unexplained));
    }
    Ok(Consequence {
        w_moved,
        m_moved,
        strips_moved,
        frame_moved,
        pixels_moved,
        strips_changed,
        index_changed,
        columns_changed,
        columns_unexplained,
        pixels_changed,
        pixels_permille: (pixels_changed as i64 * 1000) / (W * H) as i64,
        signature,
    })
}

fn side_json(s: &Side, level_file: &str, tiles_file: &str, camera: Camera) -> Json {
    obj(vec![
        ("level", Json::Str(level_file.to_string())),
        ("W", Json::Str(s.w.clone())),
        ("tiles", Json::Str(tiles_file.to_string())),
        ("M", Json::Str(s.m.clone())),
        ("camera", Json::Arr(vec![Json::Num(camera.x), Json::Num(camera.z), Json::Str(facing_letter(camera.facing).to_string())])),
        ("strips", Json::Str(s.strips.clone())),
        ("frame", Json::Str(s.frame.clone())),
        ("pixels", Json::Str(s.pixels.clone())),
    ])
}

fn consequence_json(c: &Consequence) -> Json {
    obj(vec![
        ("w_moved", Json::Bool(c.w_moved)),
        ("m_moved", Json::Bool(c.m_moved)),
        ("camera_carried", Json::Bool(true)),
        ("strips_moved", Json::Bool(c.strips_moved)),
        ("frame_moved", Json::Bool(c.frame_moved)),
        ("pixels_moved", Json::Bool(c.pixels_moved)),
        ("signature", Json::Str(c.signature.to_string())),
        ("strips_changed", Json::Num(c.strips_changed as i64)),
        ("index_changed", Json::Num(c.index_changed as i64)),
        ("columns_changed", Json::Num(c.columns_changed as i64)),
        ("columns_unexplained", Json::Num(c.columns_unexplained as i64)),
        ("pixels_changed", Json::Num(c.pixels_changed as i64)),
        ("pixels_permille", Json::Num(c.pixels_permille)),
    ])
}

fn consequence_line(c: &Consequence) -> String {
    format!(
        "{} — W {} M {} camera carried strips {} frame {} pixels {} strips_changed {} index_changed {} columns_changed {} unexplained {} pixels_changed {} ({} permille)",
        c.signature,
        if c.w_moved { "moved" } else { "unmoved" },
        if c.m_moved { "moved" } else { "unmoved" },
        if c.strips_moved { "moved" } else { "unmoved" },
        if c.frame_moved { "moved" } else { "unmoved" },
        if c.pixels_moved { "moved" } else { "unmoved" },
        c.strips_changed,
        c.index_changed,
        c.columns_changed,
        c.columns_unexplained,
        c.pixels_changed,
        c.pixels_permille
    )
}

fn camera_from_json(v: &Json) -> Result<Camera, String> {
    let a = v.arr();
    if a.len() != 3 {
        return Err("camera is not [x, z, F]".to_string());
    }
    parse_camera(&format!("{},{},{}", a[0].num(), a[1].num(), a[2].str())).map_err(|Refusal(m)| m)
}

// ------------------------------------------------------------------ the view cone (a theorem, held by the census)
/// Every ray the kernel casts has |forward| = 2*FOCAL = 1920 and |sideways| <= 1919, and the floor point lies on
/// the ray; so a cell that any ray or floor cast can touch lies in the cone: forward of the eye, and no farther
/// sideways than forward, plus one cell for its own extent. Facing N: z <= cz, |x-cx| <= cz-z+1; E: x >= cx,
/// |z-cz| <= x-cx+1; S: z >= cz, |x-cx| <= z-cz+1; W: x <= cx, |z-cz| <= cx-x+1. Conservative: a cell inside the
/// cone may still be occluded. The census records, per signature, how many edits lie inside and outside it; the
/// law is that no geometry edit lies outside.
fn in_cone(x: i64, z: i64, cam: Camera) -> bool {
    let (dx, dz) = (x - cam.x, z - cam.z);
    match cam.facing {
        0 => dz <= 0 && dx.abs() <= -dz + 1,
        1 => dx >= 0 && dz.abs() <= dx + 1,
        2 => dz >= 0 && dx.abs() <= dz + 1,
        _ => dx <= 0 && dz.abs() <= -dx + 1,
    }
}

// ------------------------------------------------------------------ record
fn cmd_record(args: &[String]) {
    let mut level_path: Option<String> = None;
    let mut tiles_path: Option<String> = None;
    let mut camera: Option<String> = None;
    let mut spec: Option<String> = None;
    let mut out_dir: Option<String> = None;
    let mut name = String::from("edit");
    let mut i = 0;
    while i < args.len() {
        let val = |i: usize| args.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", args[i])));
        match args[i].as_str() {
            "--level" => level_path = Some(val(i)),
            "--tiles" => tiles_path = Some(val(i)),
            "--camera" => camera = Some(val(i)),
            "--edit" => spec = Some(val(i)),
            "--out-dir" => out_dir = Some(val(i)),
            "--name" => name = val(i),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    let (level_path, tiles_path, camera, spec, out_dir) = match (level_path, tiles_path, camera, spec, out_dir) {
        (Some(a), Some(b), Some(c), Some(d), Some(e)) => (a, b, c, d, e),
        _ => refuse("USAGE", "record needs --level --tiles --camera --edit --out-dir"),
    };
    let level_bytes_in = read(Path::new(&level_path));
    let tiles_bytes_in = read(Path::new(&tiles_path));
    let level = parse_level(&level_bytes_in).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let tiles = parse_tiles(&tiles_bytes_in).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let cam = parse_camera(&camera).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    let edit = parse_edit(&spec).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));

    let before = witness(&level, &tiles, cam).unwrap_or_else(|m| refuse("INVALID-AUTHORITY", &m));
    let (new_level, new_tiles) = apply(&level, &tiles, cam, &edit).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
    let after = witness(&new_level, &new_tiles, cam).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
    let cons = consequence(&before, &after).unwrap_or_else(|m| refuse("CONSEQUENCE-IMPOSSIBLE", &m));

    let dir = PathBuf::from(&out_dir);
    fs::create_dir_all(&dir).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", dir.display(), e)));
    let files = [
        (format!("{}.before.lvl", name), level_bytes_in.clone()),
        (format!("{}.before.tiles", name), tiles_bytes_in.clone()),
        (format!("{}.after.lvl", name), level_bytes(&new_level)),
        (format!("{}.after.tiles", name), tiles_bytes(&new_tiles)),
    ];
    for (f, b) in &files {
        write(&dir.join(f), b);
    }
    // a level edit names its source relative to the record: copy it beside the record too
    let edit_rec = match &edit {
        Edit::Level { path } => {
            let f = format!("{}.edit.lvl", name);
            write(&dir.join(&f), &read(Path::new(path)));
            Edit::Level { path: f }
        }
        e => e.clone(),
    };
    // a computed explanation for an out-of-view cell edit: outside the cone, or inside it and occluded
    let mut cons_json = consequence_json(&cons);
    if let (Edit::Cell { x, z, .. }, "outside-view") = (&edit, cons.signature) {
        let why = if in_cone(*x as i64, *z as i64, cam) { "inside the view cone, occluded" } else { "outside the view cone" };
        if let Json::Obj(m) = &mut cons_json {
            m.insert("explanation".to_string(), Json::Str(why.to_string()));
        }
    }
    let scope = format!("one edit ({}) of the authority W {}… M {}… under the camera ({}, {}, {}), as recorded in these files", spec, &before.w[..12], &before.m[..12], cam.x, cam.z, facing_letter(cam.facing));
    let record = envelope_seal(
        "verdandi-edit-record",
        3,
        "measured",
        obj(vec![
            ("tool", Json::Str("workshop/edit.rs record".into())),
            ("before_level", Json::Str(files[0].0.clone())),
            ("before_tiles", Json::Str(files[1].0.clone())),
            ("after_level", Json::Str(files[2].0.clone())),
            ("after_tiles", Json::Str(files[3].0.clone())),
        ]),
        obj(vec![
            ("certifies", Json::Str(scope)),
            ("camera", Json::Arr(vec![Json::Num(cam.x), Json::Num(cam.z), Json::Str(facing_letter(cam.facing).to_string())])),
        ]),
        vec![
            "that the edit is good, wanted, or intended — the record measures what moved, never why",
            "a consequence under any other camera (a view mutation is not an edit and is refused here)",
            "any wall-clock: `record` is off the frame path",
            "that an outside-view edit is a fault: it is the normal case (see workshop/attest/census-witness.json)",
        ],
        obj(vec![
            ("before", side_json(&before, &files[0].0, &files[1].0, cam)),
            ("edit", edit_json(&edit_rec)),
            ("after", side_json(&after, &files[2].0, &files[3].0, cam)),
            ("consequence", cons_json),
        ]),
        "W = sha256 of the level file, M = sha256 of the tiles file, the camera carried; strips = sha256 of the exact strips (geometry at the kernel's grain), frame = URDRFB1 digest (geometry at the index grain), pixels = sha256 of the RGB picture (appearance); signature = the exhaustive classification of what moved; strips_changed / index_changed / columns_changed = columns whose exact strip / index column / pixels differ; columns_unexplained = pixel moved with no strip, index or material behind it (law: 0); explanation (outside-view cell edits) = the cone test; every value re-derived by `edit check`",
    );
    let mut text = String::new();
    json_write(&record, 0, &mut text);
    text.push('\n');
    let rec_path = dir.join(format!("{}.record.json", name));
    write(&rec_path, text.as_bytes());
    println!("RECORD {}", rec_path.display());
    println!("before W {} M {} strips {} frame {} pixels {}", &before.w[..12], &before.m[..12], &before.strips[..12], &before.frame[..12], &before.pixels[..12]);
    println!("after  W {} M {} strips {} frame {} pixels {}", &after.w[..12], &after.m[..12], &after.strips[..12], &after.frame[..12], &after.pixels[..12]);
    println!("CONSEQUENCE {}", consequence_line(&cons));
}

// ------------------------------------------------------------------ check
fn cmd_check(args: &[String]) {
    let mut record_path: Option<String> = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--record" => record_path = args.get(i + 1).cloned(),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    let record_path = PathBuf::from(record_path.unwrap_or_else(|| refuse("USAGE", "check needs --record")));
    let dir = record_path.parent().map(Path::to_path_buf).unwrap_or_else(|| PathBuf::from("."));
    let rec = json_parse(&read(&record_path)).unwrap_or_else(|m| refuse("INVALID-RECORD", &m));
    // 0. the envelope: required fields, a claim class, a scope, forbidden readings, no verdict inside data,
    //    the chain hash over the required fields
    envelope_validate(&rec).unwrap_or_else(|m| refuse("ENVELOPE", &m));
    if rec.get("name").str() != "verdandi-edit-record" || rec.get("version").num() != 3 {
        refuse("INVALID-RECORD", "not a verdandi-edit-record version 3");
    }
    let d = rec.get("data");
    let (b, a, e) = (d.get("before"), d.get("after"), d.get("edit"));

    // 1. the before side re-derives from its files
    let level = parse_level(&read(&dir.join(b.get("level").str()))).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let tiles = parse_tiles(&read(&dir.join(b.get("tiles").str()))).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let cam_b = camera_from_json(b.get("camera")).unwrap_or_else(|m| refuse("INVALID-RECORD", &m));
    let before = witness(&level, &tiles, cam_b).unwrap_or_else(|m| refuse("INVALID-AUTHORITY", &m));
    if before.w != b.get("W").str() || before.m != b.get("M").str() {
        refuse("BEFORE-MISMATCH", "the record's before authority is not what its files hash to");
    }
    if before.strips != b.get("strips").str() || before.frame != b.get("frame").str() || before.pixels != b.get("pixels").str() {
        refuse("BEFORE-MISMATCH", "the record's before witnesses are not what the kernel computes from its files");
    }

    // 2. the camera is carried, or this is not an edit record. The camera is projection-owned: while it is
    //    fixed, every consequence below is attributable to the authority; once it moved, attribution is
    //    impossible and the case is reported as its own — with or without an authority change beside it.
    let cam_a = camera_from_json(a.get("camera")).unwrap_or_else(|m| refuse("INVALID-RECORD", &m));
    if cam_a != cam_b {
        let moved = format!("({}, {}, {}) -> ({}, {}, {})", cam_b.x, cam_b.z, facing_letter(cam_b.facing), cam_a.x, cam_a.z, facing_letter(cam_a.facing));
        let authority_claimed_moved = a.get("W").str() != b.get("W").str() || a.get("M").str() != b.get("M").str();
        if authority_claimed_moved {
            refuse("CAMERA-MOVED", &format!("{}: the record carries a changed camera beside a new authority; the camera must be carried untouched", moved));
        }
        refuse("CAMERA-MOVED", &format!("{}: the projection-owned camera changed with no edit; a view mutation is not an edit (INPUT-0 records it)", moved));
    }

    // 3. the edit re-applies and validates
    let edit = edit_from_json(e, &dir).unwrap_or_else(|m| refuse("INVALID-RECORD", &m));
    let (new_level, new_tiles) = apply(&level, &tiles, cam_b, &edit).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
    let after = witness(&new_level, &new_tiles, cam_b).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));

    // 4. the after files ARE the new authority the edit produces
    let after_level_file = read(&dir.join(a.get("level").str()));
    let after_tiles_file = read(&dir.join(a.get("tiles").str()));
    if hex(&sha256(&after_level_file)) != after.w || hex(&sha256(&after_tiles_file)) != after.m {
        refuse("AUTHORITY-MISMATCH", "the after files are not the authority the recorded edit produces");
    }
    if a.get("W").str() != after.w || a.get("M").str() != after.m {
        refuse("AUTHORITY-MISMATCH", "the record's after W/M are not what the edit produces");
    }

    // 5. the projection as CLAIMED by the record, against what the kernel re-derives: stale under a moved
    //    authority, moved with no authority behind it, or plainly wrong. (On re-derived values the arm
    //    "authority unmoved, projection moved" cannot occur — the kernel is a function of the authority
    //    and the carried camera — so it is a claim check, and the honest arm "authority moved, projection
    //    unmoved" is the outside-view signature, never a refusal.)
    let authority_moved = after.w != before.w || after.m != before.m;
    let claimed = (a.get("strips").str().to_string(), a.get("frame").str().to_string(), a.get("pixels").str().to_string());
    let derived = (after.strips.clone(), after.frame.clone(), after.pixels.clone());
    let old = (before.strips.clone(), before.frame.clone(), before.pixels.clone());
    if claimed != derived {
        if authority_moved && claimed == old {
            refuse("STALE-PROJECTION", "the authority moved and the record still shows the old strips, frame and picture");
        }
        if !authority_moved {
            refuse("PROJECTION-WITHOUT-AUTHORITY", "the record's projection moved while W, M and the camera did not");
        }
        refuse("PROJECTION-MISMATCH", "the record's after witnesses are not what the kernel computes from the new authority");
    }

    // 6. the consequence re-derives, signature included; an impossible arm is refused as such
    let cons = consequence(&before, &after).unwrap_or_else(|m| refuse("CONSEQUENCE-IMPOSSIBLE", &m));
    let c = d.get("consequence");
    let same = c.get("w_moved").boolean() == cons.w_moved
        && c.get("m_moved").boolean() == cons.m_moved
        && c.get("camera_carried").boolean()
        && c.get("strips_moved").boolean() == cons.strips_moved
        && c.get("frame_moved").boolean() == cons.frame_moved
        && c.get("pixels_moved").boolean() == cons.pixels_moved
        && c.get("signature").str() == cons.signature
        && c.get("strips_changed").num() == cons.strips_changed as i64
        && c.get("index_changed").num() == cons.index_changed as i64
        && c.get("columns_changed").num() == cons.columns_changed as i64
        && c.get("columns_unexplained").num() == cons.columns_unexplained as i64
        && c.get("pixels_changed").num() == cons.pixels_changed as i64
        && c.get("pixels_permille").num() == cons.pixels_permille;
    if !same {
        refuse("CONSEQUENCE-MISMATCH", &format!("re-derived: {}", consequence_line(&cons)));
    }
    if let (Edit::Cell { x, z, .. }, "outside-view") = (&edit, cons.signature) {
        let why = if in_cone(*x as i64, *z as i64, cam_b) { "inside the view cone, occluded" } else { "outside the view cone" };
        if c.get("explanation").str() != why {
            refuse("CONSEQUENCE-MISMATCH", &format!("explanation re-derived: {}", why));
        }
    }
    println!("CHECK OK {}", consequence_line(&cons));
}

// ------------------------------------------------------------------ census (off-gate instrument)
fn cmd_census(args: &[String]) {
    let mut level_path: Option<String> = None;
    let mut tiles_path: Option<String> = None;
    let mut camera: Option<String> = None;
    let mut out: Option<String> = None;
    let mut i = 0;
    while i < args.len() {
        let val = |i: usize| args.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", args[i])));
        match args[i].as_str() {
            "--level" => level_path = Some(val(i)),
            "--tiles" => tiles_path = Some(val(i)),
            "--camera" => camera = Some(val(i)),
            "--out" => out = Some(val(i)),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    let (level_path, tiles_path, camera, out) = match (level_path, tiles_path, camera, out) {
        (Some(a), Some(b), Some(c), Some(d)) => (a, b, c, d),
        _ => refuse("USAGE", "census needs --level --tiles --camera --out"),
    };
    let level_bytes_in = read(Path::new(&level_path));
    let tiles_bytes_in = read(Path::new(&tiles_path));
    let level = parse_level(&level_bytes_in).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let tiles = parse_tiles(&tiles_bytes_in).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let cam = parse_camera(&camera).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    let before = witness(&level, &tiles, cam).unwrap_or_else(|m| refuse("INVALID-AUTHORITY", &m));

    let mut counts: BTreeMap<String, i64> = BTreeMap::new();
    let mut cone_in: BTreeMap<String, i64> = BTreeMap::new();
    let mut cone_out: BTreeMap<String, i64> = BTreeMap::new();
    let mut examples: BTreeMap<String, Vec<Json>> = BTreeMap::new();
    let (mut tested, mut skipped, mut unexplained_total, mut impossible) = (0i64, 0i64, 0i64, 0i64);
    for z in 1..level.rows - 1 {
        for x in 1..level.w - 1 {
            if (x as i64, z as i64) == (cam.x, cam.z) {
                skipped += 1;
                continue;
            }
            let old = level.cells[z * level.w + x];
            let to = if old == b'#' { b'.' } else { b'#' };
            let edit = Edit::Cell { x, z, to };
            let (nl, nt) = match apply(&level, &tiles, cam, &edit) {
                Ok(v) => v,
                Err(_) => {
                    skipped += 1;
                    continue;
                }
            };
            let after = match witness(&nl, &nt, cam) {
                Ok(v) => v,
                Err(_) => {
                    skipped += 1;
                    continue;
                }
            };
            tested += 1;
            match consequence(&before, &after) {
                Ok(c) => {
                    *counts.entry(c.signature.to_string()).or_insert(0) += 1;
                    let bucket = if in_cone(x as i64, z as i64, cam) { &mut cone_in } else { &mut cone_out };
                    *bucket.entry(c.signature.to_string()).or_insert(0) += 1;
                    unexplained_total += c.columns_unexplained as i64;
                    let ex = examples.entry(c.signature.to_string()).or_default();
                    if ex.len() < 3 {
                        ex.push(obj(vec![
                            ("x", Json::Num(x as i64)),
                            ("z", Json::Num(z as i64)),
                            ("from", Json::Str((old as char).to_string())),
                            ("to", Json::Str((to as char).to_string())),
                            ("strips_changed", Json::Num(c.strips_changed as i64)),
                            ("index_changed", Json::Num(c.index_changed as i64)),
                            ("columns_changed", Json::Num(c.columns_changed as i64)),
                            ("pixels_changed", Json::Num(c.pixels_changed as i64)),
                        ]));
                    }
                }
                Err(_) => impossible += 1,
            }
        }
    }
    let level_name = Path::new(&level_path).file_name().map(|f| f.to_string_lossy().into_owned()).unwrap_or_default();
    let tiles_name = Path::new(&tiles_path).file_name().map(|f| f.to_string_lossy().into_owned()).unwrap_or_default();
    let geometry_outside_cone: i64 = cone_out.iter().filter(|(k, _)| k.as_str() != "outside-view" && k.as_str() != "identity").map(|(_, v)| *v).sum();
    let record = envelope_seal(
        "verdandi-edit-census",
        2,
        "measured",
        obj(vec![
            ("tool", Json::Str("workshop/edit.rs census".into())),
            ("level", Json::Str(level_name.clone())),
            ("W", Json::Str(before.w.clone())),
            ("tiles", Json::Str(tiles_name.clone())),
            ("M", Json::Str(before.m.clone())),
            ("camera", Json::Arr(vec![Json::Num(cam.x), Json::Num(cam.z), Json::Str(facing_letter(cam.facing).to_string())])),
            ("base", obj(vec![("strips", Json::Str(before.strips.clone())), ("frame", Json::Str(before.frame.clone())), ("pixels", Json::Str(before.pixels.clone()))])),
        ]),
        obj(vec![
            ("certifies", Json::Str(format!("the consequence signature of every single-cell flip (rock -> floor, anything else -> rock; the border and the camera's cell excepted) of {} (W {}…) under the camera ({}, {}, {}) with {} (M {}…)", level_name, &before.w[..12], cam.x, cam.z, facing_letter(cam.facing), tiles_name, &before.m[..12]))),
            ("edit_family", Json::Str("single-cell flips".into())),
        ]),
        vec![
            "any other level, camera or tile set",
            "that a signature unseen here (sub-index, sub-pixel) cannot occur",
            "a wall-clock (none is inside; the record reproduces byte for byte)",
            "that an outside-view edit is a fault",
        ],
        obj(vec![
            ("tested", Json::Num(tested)),
            ("skipped", Json::Num(skipped)),
            ("impossible", Json::Num(impossible)),
            ("unexplained_columns_total", Json::Num(unexplained_total)),
            ("signatures", Json::Obj(counts.iter().map(|(k, v)| (k.clone(), Json::Num(*v))).collect())),
            ("cone", obj(vec![
                ("inside", Json::Obj(cone_in.iter().map(|(k, v)| (k.clone(), Json::Num(*v))).collect())),
                ("outside", Json::Obj(cone_out.iter().map(|(k, v)| (k.clone(), Json::Num(*v))).collect())),
                ("geometry_outside_cone", Json::Num(geometry_outside_cone)),
            ])),
            ("examples", Json::Obj(examples.into_iter().map(|(k, v)| (k, Json::Arr(v))).collect())),
        ]),
        "the truth table populated: how many single-cell edits of this level under this camera move which witnesses; outside-view = the authority moved and no strip, index or pixel did; the cone = the theorem that a cell any ray can touch lies forward of the eye and no farther sideways than forward (+1 cell): inside/outside count each signature on either side, and geometry_outside_cone is 0 by law; a biconditional authority-moved <=> projection-moved would refuse every outside-view edit; the one-directional laws hold (unexplained_columns_total 0, impossible 0)",
    );
    let mut text = String::new();
    json_write(&record, 0, &mut text);
    text.push('\n');
    write(Path::new(&out), text.as_bytes());
    println!("CENSUS {} tested {} skipped {} impossible {} unexplained {} geometry_outside_cone {}", out, tested, skipped, impossible, unexplained_total, geometry_outside_cone);
    for (k, v) in &counts {
        println!("  {:6}  {}", v, k);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        refuse("USAGE", "edit record ... | edit check --record R.json | edit census ...");
    }
    match args[1].as_str() {
        "record" => cmd_record(&args[2..]),
        "check" => cmd_check(&args[2..]),
        "census" => cmd_census(&args[2..]),
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
