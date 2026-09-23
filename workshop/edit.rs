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
// and the consequence is measured, never estimated: the frame digest and the pixel sha before and after,
// the columns whose strip changed, the pixels that differ. The old authority is never mutated: the new
// level and tiles are written as files beside the record (the world survives the app), and the record is
// what a verifier re-derives — `check` recomputes every hash from the files and refuses, typed, when the
// record's projection is stale under a moved authority (STALE-PROJECTION), when a projection moved with
// no authority behind it (PROJECTION-WITHOUT-AUTHORITY), when the camera moved (CAMERA-MOVED), or when
// an edit could not play (INVALID-EDIT: a cell outside the level or the alphabet, a camera left in rock,
// an opened border).
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
use mantle::{hex, parse_scene, picture, sha256, Picture, Refusal, H, W};

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
    frame: String,
    pixels: String,
    pic: Picture,
}

fn witness(level: &Level, tiles: &Tiles, camera: Camera) -> Result<Side, String> {
    let lb = level_bytes(level);
    let tb = tiles_bytes(tiles);
    let scene_bytes = compose(level, camera, tiles);
    let scene = parse_scene(&scene_bytes).map_err(|Refusal(m)| m)?;
    let pic = picture(&scene);
    Ok(Side { w: hex(&sha256(&lb)), m: hex(&sha256(&tb)), frame: pic.frame_digest(), pixels: pic.pixel_sha256(), pic })
}

struct Consequence {
    w_moved: bool,
    m_moved: bool,
    frame_moved: bool,
    pixels_moved: bool,
    strips_changed: usize,
    columns_changed: usize,
    pixels_changed: usize,
    pixels_permille: i64,
}

fn consequence(before: &Side, after: &Side) -> Consequence {
    let mut strips_changed = 0usize;
    for c in 0..W {
        let mut differs = false;
        for r in 0..H {
            if before.pic.frame[r * W + c] != after.pic.frame[r * W + c] {
                differs = true;
                break;
            }
        }
        if differs {
            strips_changed += 1;
        }
    }
    let mut pixels_changed = 0usize;
    let mut column_touched = vec![false; W];
    for i in 0..W * H {
        if before.pic.pixels[i * 3..i * 3 + 3] != after.pic.pixels[i * 3..i * 3 + 3] {
            pixels_changed += 1;
            column_touched[i % W] = true;
        }
    }
    let columns_changed = column_touched.iter().filter(|t| **t).count();
    Consequence {
        w_moved: before.w != after.w,
        m_moved: before.m != after.m,
        frame_moved: before.frame != after.frame,
        pixels_moved: before.pixels != after.pixels,
        strips_changed,
        columns_changed,
        pixels_changed,
        pixels_permille: (pixels_changed as i64 * 1000) / (W * H) as i64,
    }
}

fn side_json(s: &Side, level_file: &str, tiles_file: &str, camera: Camera) -> Json {
    obj(vec![
        ("level", Json::Str(level_file.to_string())),
        ("W", Json::Str(s.w.clone())),
        ("tiles", Json::Str(tiles_file.to_string())),
        ("M", Json::Str(s.m.clone())),
        ("camera", Json::Arr(vec![Json::Num(camera.x), Json::Num(camera.z), Json::Str(facing_letter(camera.facing).to_string())])),
        ("frame", Json::Str(s.frame.clone())),
        ("pixels", Json::Str(s.pixels.clone())),
    ])
}

fn consequence_json(c: &Consequence) -> Json {
    obj(vec![
        ("w_moved", Json::Bool(c.w_moved)),
        ("m_moved", Json::Bool(c.m_moved)),
        ("camera_carried", Json::Bool(true)),
        ("frame_moved", Json::Bool(c.frame_moved)),
        ("pixels_moved", Json::Bool(c.pixels_moved)),
        ("strips_changed", Json::Num(c.strips_changed as i64)),
        ("columns_changed", Json::Num(c.columns_changed as i64)),
        ("pixels_changed", Json::Num(c.pixels_changed as i64)),
        ("pixels_permille", Json::Num(c.pixels_permille)),
    ])
}

fn consequence_line(c: &Consequence) -> String {
    format!(
        "W {} M {} camera carried frame {} pixels {} strips_changed {} columns_changed {} pixels_changed {} ({} permille)",
        if c.w_moved { "moved" } else { "unmoved" },
        if c.m_moved { "moved" } else { "unmoved" },
        if c.frame_moved { "moved" } else { "unmoved" },
        if c.pixels_moved { "moved" } else { "unmoved" },
        c.strips_changed,
        c.columns_changed,
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
    let cons = consequence(&before, &after);

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
    let record = obj(vec![
        ("name", Json::Str("verdandi-edit-record".into())),
        ("version", Json::Num(1)),
        ("before", side_json(&before, &files[0].0, &files[1].0, cam)),
        ("edit", edit_json(&edit_rec)),
        ("after", side_json(&after, &files[2].0, &files[3].0, cam)),
        ("consequence", consequence_json(&cons)),
        ("reading", Json::Str("W = sha256 of the level file, M = sha256 of the tiles file, the camera carried; frame = URDRFB1 digest (geometry), pixels = sha256 of the RGB picture (appearance); strips_changed = columns whose index column differs, columns_changed = columns with any pixel differing; every value re-derived by `edit check`".into())),
    ]);
    let mut text = String::new();
    json_write(&record, 0, &mut text);
    text.push('\n');
    let rec_path = dir.join(format!("{}.record.json", name));
    write(&rec_path, text.as_bytes());
    println!("RECORD {}", rec_path.display());
    println!("before W {} M {} frame {} pixels {}", &before.w[..12], &before.m[..12], &before.frame[..12], &before.pixels[..12]);
    println!("after  W {} M {} frame {} pixels {}", &after.w[..12], &after.m[..12], &after.frame[..12], &after.pixels[..12]);
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
    if rec.get("name").str() != "verdandi-edit-record" || rec.get("version").num() != 1 {
        refuse("INVALID-RECORD", "not a verdandi-edit-record version 1");
    }
    let (b, a, e) = (rec.get("before"), rec.get("after"), rec.get("edit"));

    // 1. the before side re-derives from its files
    let level = parse_level(&read(&dir.join(b.get("level").str()))).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let tiles = parse_tiles(&read(&dir.join(b.get("tiles").str()))).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let cam_b = camera_from_json(b.get("camera")).unwrap_or_else(|m| refuse("INVALID-RECORD", &m));
    let before = witness(&level, &tiles, cam_b).unwrap_or_else(|m| refuse("INVALID-AUTHORITY", &m));
    if before.w != b.get("W").str() || before.m != b.get("M").str() {
        refuse("BEFORE-MISMATCH", "the record's before authority is not what its files hash to");
    }
    if before.frame != b.get("frame").str() || before.pixels != b.get("pixels").str() {
        refuse("BEFORE-MISMATCH", "the record's before witnesses are not what the kernel computes from its files");
    }

    // 2. the camera is carried, or this is not an edit record
    let cam_a = camera_from_json(a.get("camera")).unwrap_or_else(|m| refuse("INVALID-RECORD", &m));
    if cam_a != cam_b {
        refuse("CAMERA-MOVED", &format!("({}, {}, {}) -> ({}, {}, {}): a view mutation is not an edit", cam_b.x, cam_b.z, facing_letter(cam_b.facing), cam_a.x, cam_a.z, facing_letter(cam_a.facing)));
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

    // 5. the projection: stale, moved without authority, or plainly wrong
    let authority_moved = after.w != before.w || after.m != before.m;
    let claimed = (a.get("frame").str().to_string(), a.get("pixels").str().to_string());
    if claimed != (after.frame.clone(), after.pixels.clone()) {
        if authority_moved && claimed == (before.frame.clone(), before.pixels.clone()) {
            refuse("STALE-PROJECTION", "the authority moved and the record still shows the old frame and picture");
        }
        if !authority_moved {
            refuse("PROJECTION-WITHOUT-AUTHORITY", "the record's picture moved while W, M and the camera did not");
        }
        refuse("PROJECTION-MISMATCH", "the record's after witnesses are not what the kernel computes from the new authority");
    }
    if !authority_moved && claimed != (before.frame.clone(), before.pixels.clone()) {
        refuse("PROJECTION-WITHOUT-AUTHORITY", "the picture moved with no authority behind it");
    }

    // 6. the consequence re-derives
    let cons = consequence(&before, &after);
    let c = rec.get("consequence");
    let same = c.get("w_moved").boolean() == cons.w_moved
        && c.get("m_moved").boolean() == cons.m_moved
        && c.get("camera_carried").boolean()
        && c.get("frame_moved").boolean() == cons.frame_moved
        && c.get("pixels_moved").boolean() == cons.pixels_moved
        && c.get("strips_changed").num() == cons.strips_changed as i64
        && c.get("columns_changed").num() == cons.columns_changed as i64
        && c.get("pixels_changed").num() == cons.pixels_changed as i64
        && c.get("pixels_permille").num() == cons.pixels_permille;
    if !same {
        refuse("CONSEQUENCE-MISMATCH", &format!("re-derived: {}", consequence_line(&cons)));
    }
    println!("CHECK OK {}", consequence_line(&cons));
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        refuse("USAGE", "edit record ... | edit check --record R.json");
    }
    match args[1].as_str() {
        "record" => cmd_record(&args[2..]),
        "check" => cmd_check(&args[2..]),
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
