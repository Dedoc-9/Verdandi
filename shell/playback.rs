// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/playback.rs — SHELL-PLAYBACK: the window shows exactly the sealed SESSION-WALK, and nothing else.
//
// A sealed session-walk (workshop/sessionwalk.rs, VRDNSW1) is the authority of a becoming: an ordered log of
// edits and moves that replays to a head. This module CONSUMES that sealed artifact — it does not reconstruct
// an ad-hoc action stream — replays it from the base authority, and for every MOVE produces the kernel's
// composite through the SHELL-0 present path (compose_frame -> to_blit), so:
//
//   sealed session  ->  replay  ->  kernel frame  ->  SHELL-0 blit/hash boundary  ->  the window
//
// The crown property: the ordered frame-digest sequence playback produces EQUALS the session's per-move
// frame-witness sequence, and playback's re-derived head equals the sealed head. If the sealed input was
// tampered/truncated/reordered, a re-derived witness or the head diverges and playback REFUSES (exit 2) — it
// never silently mints a new authority. Playback reads only; it never writes W, M or the session head, so the
// shell cannot become a second authority. Each displayed frame passes SHELL-0's `from_blit(to_blit(c)) == c`.
//
// Checkpoint/resume is folded in (SESSION-WALK's checkpoint hardening): a checkpoint captures the WHOLE
// interleaved authority (level bytes, tiles bytes, camera, head) at event k; resuming from it reproduces the
// identical frame-witness suffix and the identical head as replay from the origin — so a scheduler may split
// the run at any certified checkpoint without changing what the sealed log means. Presentation timing is NOT
// here: how fast the frames reach the glass is LATENCY-0's measurement; this file is headless and clock-free.
//
//     shell playback   --session S.json               # headless: per-move digest + blit witness + roundtrip
//     shell playback   --session S.json --batch N      # same sequence, grouped output (presentation-schedule)
//     shell checkpoint --session S.json --at K --out CK # capture the full authority at event K
//     shell resume     --session S.json --checkpoint CK # replay the suffix from the checkpoint

use std::collections::BTreeMap;
use std::fs;
use std::process::exit;

use crate::formats::{facing_letter, parse_camera, Camera};
use crate::mantle::{hex, sha256, Refusal};
use crate::present::{blit_roundtrip_ok, blit_witness, compose_frame, to_blit, Composed};

const MAGIC: &[u8] = b"VRDNSW1";
const TILE_BYTES: usize = 256 * 256 * 3;

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("SHELL-PLAYBACK-{}: {}", code, detail);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path, e)))
}

// ------------------------------------------------------------------ a small JSON reader (self-contained)
#[derive(Clone, Debug)]
enum Json {
    Null,
    Bool(bool),
    Num(i64),
    Str(String),
    Arr(Vec<Json>),
    Obj(BTreeMap<String, Json>),
}

impl Json {
    fn get(&self, k: &str) -> &Json {
        match self {
            Json::Obj(m) => m.get(k).unwrap_or(&Json::Null),
            _ => &Json::Null,
        }
    }
    fn s(&self) -> &str {
        match self {
            Json::Str(s) => s,
            _ => "",
        }
    }
    fn arr(&self) -> &[Json] {
        match self {
            Json::Arr(a) => a,
            _ => &[],
        }
    }
}

struct P<'a> {
    b: &'a [u8],
    i: usize,
}

impl<'a> P<'a> {
    fn ws(&mut self) {
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\n' | b'\r' | b'\t') {
            self.i += 1;
        }
    }
    fn val(&mut self) -> Result<Json, String> {
        self.ws();
        if self.i >= self.b.len() {
            return Err("unexpected end".into());
        }
        match self.b[self.i] {
            b'{' => {
                self.i += 1;
                let mut m = BTreeMap::new();
                self.ws();
                if self.i < self.b.len() && self.b[self.i] == b'}' {
                    self.i += 1;
                    return Ok(Json::Obj(m));
                }
                loop {
                    self.ws();
                    let k = match self.val()? {
                        Json::Str(s) => s,
                        _ => return Err("key not a string".into()),
                    };
                    self.ws();
                    if self.i >= self.b.len() || self.b[self.i] != b':' {
                        return Err("expected ':'".into());
                    }
                    self.i += 1;
                    let v = self.val()?;
                    m.insert(k, v);
                    self.ws();
                    if self.i < self.b.len() && self.b[self.i] == b',' {
                        self.i += 1;
                        continue;
                    }
                    self.ws();
                    if self.i >= self.b.len() || self.b[self.i] != b'}' {
                        return Err("expected '}'".into());
                    }
                    self.i += 1;
                    return Ok(Json::Obj(m));
                }
            }
            b'[' => {
                self.i += 1;
                let mut a = Vec::new();
                self.ws();
                if self.i < self.b.len() && self.b[self.i] == b']' {
                    self.i += 1;
                    return Ok(Json::Arr(a));
                }
                loop {
                    a.push(self.val()?);
                    self.ws();
                    if self.i < self.b.len() && self.b[self.i] == b',' {
                        self.i += 1;
                        continue;
                    }
                    self.ws();
                    if self.i >= self.b.len() || self.b[self.i] != b']' {
                        return Err("expected ']'".into());
                    }
                    self.i += 1;
                    return Ok(Json::Arr(a));
                }
            }
            b'"' => {
                self.i += 1;
                let mut s = String::new();
                loop {
                    if self.i >= self.b.len() {
                        return Err("unterminated string".into());
                    }
                    let c = self.b[self.i];
                    self.i += 1;
                    match c {
                        b'"' => return Ok(Json::Str(s)),
                        b'\\' => {
                            let e = self.b[self.i];
                            self.i += 1;
                            match e {
                                b'"' => s.push('"'),
                                b'\\' => s.push('\\'),
                                b'/' => s.push('/'),
                                b'n' => s.push('\n'),
                                b'r' => s.push('\r'),
                                b't' => s.push('\t'),
                                b'u' => {
                                    let h = std::str::from_utf8(&self.b[self.i..self.i + 4]).map_err(|_| "bad \\u")?;
                                    let cp = u32::from_str_radix(h, 16).map_err(|_| "bad \\u")?;
                                    s.push(char::from_u32(cp).unwrap_or('\u{fffd}'));
                                    self.i += 4;
                                }
                                _ => return Err("bad escape".into()),
                            }
                        }
                        _ => {
                            let start = self.i - 1;
                            let len = match c {
                                0x00..=0x7f => 1,
                                0xc0..=0xdf => 2,
                                0xe0..=0xef => 3,
                                _ => 4,
                            };
                            let end = (start + len).min(self.b.len());
                            s.push_str(std::str::from_utf8(&self.b[start..end]).map_err(|_| "bad utf8")?);
                            self.i = end;
                        }
                    }
                }
            }
            b't' if self.b[self.i..].starts_with(b"true") => {
                self.i += 4;
                Ok(Json::Bool(true))
            }
            b'f' if self.b[self.i..].starts_with(b"false") => {
                self.i += 5;
                Ok(Json::Bool(false))
            }
            b'n' if self.b[self.i..].starts_with(b"null") => {
                self.i += 4;
                Ok(Json::Null)
            }
            b'-' | b'0'..=b'9' => {
                let start = self.i;
                self.i += 1;
                while self.i < self.b.len() && self.b[self.i].is_ascii_digit() {
                    self.i += 1;
                }
                std::str::from_utf8(&self.b[start..self.i]).unwrap().parse::<i64>().map(Json::Num).map_err(|_| "bad number".into())
            }
            c => Err(format!("unexpected byte {}", c)),
        }
    }
}

fn parse_json(b: &[u8]) -> Result<Json, String> {
    let mut p = P { b, i: 0 };
    let v = p.val()?;
    p.ws();
    Ok(v)
}

// ------------------------------------------------------------------ the chain (identical to workshop/sessionwalk.rs)
fn content_hex(level_bytes: &[u8], tiles_bytes: &[u8]) -> String {
    let mut buf = Vec::with_capacity(64);
    buf.extend_from_slice(&sha256(level_bytes));
    buf.extend_from_slice(&sha256(tiles_bytes));
    hex(&sha256(&buf))
}

fn genesis(base_content: &str, cam0: Camera) -> String {
    let token = format!("{},{},{}", cam0.x, cam0.z, facing_letter(cam0.facing));
    let mut buf = Vec::new();
    buf.extend_from_slice(MAGIC);
    buf.extend_from_slice(base_content.as_bytes());
    buf.push(b'@');
    buf.extend_from_slice(token.as_bytes());
    hex(&sha256(&buf))
}

fn fold(head: &str, tag: u8, witness: &str) -> String {
    let mut buf = Vec::with_capacity(head.len() + witness.len() + 3);
    buf.extend_from_slice(head.as_bytes());
    buf.push(b':');
    buf.push(tag);
    buf.push(b':');
    buf.extend_from_slice(witness.as_bytes());
    hex(&sha256(&buf))
}

// ------------------------------------------------------------------ byte-level authority edits + movement
fn level_wh(level_bytes: &[u8]) -> (usize, usize) {
    let w = u32::from_le_bytes([level_bytes[8], level_bytes[9], level_bytes[10], level_bytes[11]]) as usize;
    let rows = u32::from_le_bytes([level_bytes[12], level_bytes[13], level_bytes[14], level_bytes[15]]) as usize;
    (w, rows)
}

fn traversable(level_bytes: &[u8], x: i64, z: i64) -> bool {
    let (w, rows) = level_wh(level_bytes);
    x >= 0 && z >= 0 && (x as usize) < w && (z as usize) < rows && level_bytes[16 + z as usize * w + x as usize] != b'#'
}

fn forward(facing: u8) -> (i64, i64) {
    match facing {
        0 => (0, -1),
        1 => (1, 0),
        2 => (0, 1),
        _ => (-1, 0),
    }
}

fn step(level_bytes: &[u8], cam: Camera, cmd: u8) -> Camera {
    let mut c = cam;
    match cmd {
        b'L' => c.facing = (c.facing + 3) % 4,
        b'R' => c.facing = (c.facing + 1) % 4,
        _ => {
            let dir = match cmd {
                b'F' => forward(c.facing),
                b'B' => {
                    let (dx, dz) = forward(c.facing);
                    (-dx, -dz)
                }
                b'Q' => forward((c.facing + 3) % 4),
                b'E' => forward((c.facing + 1) % 4),
                other => refuse("INVALID-COMMAND", &format!("unknown move {:?}", other as char)),
            };
            let (nx, nz) = (c.x + dir.0, c.z + dir.1);
            if traversable(level_bytes, nx, nz) {
                c.x = nx;
                c.z = nz;
            }
        }
    }
    c
}

/// Apply an edit spec to raw authority bytes (byte-level, matching sessionwalk's re-serialization).
fn apply_spec(level_bytes: &mut Vec<u8>, tiles_bytes: &mut Vec<u8>, spec: &str) {
    let (kind, rest) = spec.split_once(':').unwrap_or_else(|| refuse("INVALID-SESSION", "edit spec has no kind"));
    match kind {
        "cell" => {
            let p: Vec<&str> = rest.split(',').collect();
            if p.len() != 3 {
                refuse("INVALID-SESSION", "cell:X,Z,C");
            }
            let x: usize = p[0].parse().unwrap_or_else(|_| refuse("INVALID-SESSION", "cell X"));
            let z: usize = p[1].parse().unwrap_or_else(|_| refuse("INVALID-SESSION", "cell Z"));
            let c = p[2].as_bytes();
            if c.len() != 1 {
                refuse("INVALID-SESSION", "cell C");
            }
            let (w, _rows) = level_wh(level_bytes);
            level_bytes[16 + z * w + x] = c[0];
        }
        "tile" => {
            let p: Vec<&str> = rest.split(',').collect();
            if p.len() != 4 {
                refuse("INVALID-SESSION", "tile:CLASS,R,G,B");
            }
            let idx = match p[0] {
                "wall0" => 0,
                "wall1" => 1,
                "wall2" => 2,
                "wall3" => 3,
                "floor" => 4,
                other => refuse("INVALID-SESSION", &format!("tile class {:?}", other)),
            };
            let rgb = [
                p[1].parse::<u8>().unwrap_or_else(|_| refuse("INVALID-SESSION", "tile R")),
                p[2].parse::<u8>().unwrap_or_else(|_| refuse("INVALID-SESSION", "tile G")),
                p[3].parse::<u8>().unwrap_or_else(|_| refuse("INVALID-SESSION", "tile B")),
            ];
            let off = 8 + idx * TILE_BYTES;
            let mut i = off;
            while i < off + TILE_BYTES {
                tiles_bytes[i] = rgb[0];
                tiles_bytes[i + 1] = rgb[1];
                tiles_bytes[i + 2] = rgb[2];
                i += 3;
            }
        }
        other => refuse("INVALID-SESSION", &format!("edit kind {:?}", other)),
    }
}

// ------------------------------------------------------------------ the sealed session
#[derive(Clone)]
enum Event {
    Move(u8),
    Edit(String),
}

struct Sealed {
    level_bytes: Vec<u8>,
    tiles_bytes: Vec<u8>,
    cam0: Camera,
    base_content: String,
    log: Vec<Event>,
    stored: Vec<(char, String)>, // per-event ('M'|'E', witness)
    head: String,
}

fn load_sealed(path: &str, root_prefix: &str) -> Sealed {
    let root = parse_json(&read(path)).unwrap_or_else(|m| refuse("INVALID-SESSION", &m));
    if root.get("name").s() != "verdandi-session-walk" {
        refuse("INVALID-SESSION", "not a verdandi-session-walk (playback consumes the sealed artifact, not an ad-hoc stream)");
    }
    let d = root.get("data");
    if d.get("magic").s() != "VRDNSW1" {
        refuse("INVALID-SESSION", "missing VRDNSW1 magic");
    }
    let base = d.get("base");
    let level_path = format!("{}{}", root_prefix, base.get("level").s());
    let tiles_path = format!("{}{}", root_prefix, base.get("tiles").s());
    let level_bytes = read(&level_path);
    let tiles_bytes = read(&tiles_path);
    let cam0 = parse_camera(base.get("camera").s()).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    let mut log = Vec::new();
    let mut stored = Vec::new();
    for item in d.get("log").arr() {
        match item.get("kind").s() {
            "move" => {
                let c = item.get("command").s().as_bytes();
                if c.len() != 1 {
                    refuse("INVALID-SESSION", "move command must be one letter");
                }
                log.push(Event::Move(c[0]));
                stored.push(('M', item.get("witness").s().to_string()));
            }
            "edit" => {
                log.push(Event::Edit(item.get("spec").s().to_string()));
                stored.push(('E', item.get("witness").s().to_string()));
            }
            other => refuse("INVALID-SESSION", &format!("event kind {:?}", other)),
        }
    }
    let head = d.get("head").s().to_string();
    Sealed {
        base_content: content_hex(&level_bytes, &tiles_bytes),
        level_bytes,
        tiles_bytes,
        cam0,
        log,
        stored,
        head,
    }
}

// a rendered move: the camera, the SHELL-0 composite, the blit witness and the round-trip verdict
pub struct Shown {
    pub cam: Camera,
    pub composed: Composed,
    pub blit: String,
    pub roundtrip_ok: bool,
}

pub struct Play {
    pub shown: Vec<Shown>,
    pub head: String,
    pub moves: usize,
    pub edits: usize,
    pub final_cam: Camera,
}

/// Replay the sealed session from a starting authority+camera+head, over the events in `range_from..`. Renders
/// every move through the SHELL-0 present path, folds the head, and REFUSES if a re-derived witness diverges
/// from the sealed one — playback cannot show a frame the sealed authority does not name.
fn replay_from(s: &Sealed, mut level: Vec<u8>, mut tiles: Vec<u8>, mut cam: Camera, mut head: String, from: usize) -> Play {
    let mut shown = Vec::new();
    let (mut moves, mut edits) = (0usize, 0usize);
    for k in from..s.log.len() {
        match &s.log[k] {
            Event::Move(c) => {
                cam = step(&level, cam, *c);
                let composed = compose_frame(&level, &tiles, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
                if s.stored[k].0 != 'M' || s.stored[k].1 != composed.frame_digest {
                    refuse("DIVERGED", &format!("event {} frame diverged from the sealed witness — the input was tampered", k));
                }
                head = fold(&head, b'M', &composed.frame_digest);
                let blit = to_blit(&composed.composite);
                let ok = blit_roundtrip_ok(&composed.composite);
                shown.push(Shown { cam, blit: blit_witness(&blit), roundtrip_ok: ok, composed });
                moves += 1;
            }
            Event::Edit(spec) => {
                apply_spec(&mut level, &mut tiles, spec);
                let w = content_hex(&level, &tiles);
                if s.stored[k].0 != 'E' || s.stored[k].1 != w {
                    refuse("DIVERGED", &format!("event {} content diverged from the sealed witness — the input was tampered", k));
                }
                head = fold(&head, b'E', &w);
                edits += 1;
            }
        }
    }
    Play { shown, head, moves, edits, final_cam: cam }
}

fn replay_all(s: &Sealed) -> Play {
    let head0 = genesis(&s.base_content, s.cam0);
    replay_from(s, s.level_bytes.clone(), s.tiles_bytes.clone(), s.cam0, head0, 0)
}

// ------------------------------------------------------------------ public entry points
pub fn playback(session: &str, root_prefix: &str, batch: usize) {
    let s = load_sealed(session, root_prefix);
    let p = replay_all(&s);
    if p.head != s.head {
        refuse("DIVERGED", &format!("re-derived head {} != the sealed head {} — the input was tampered", &p.head[..12], &s.head[..12.min(s.head.len())]));
    }
    let batch = batch.max(1);
    for (i, sh) in p.shown.iter().enumerate() {
        if i % batch == 0 {
            println!("--- present batch (up to {} frames) ---", batch);
        }
        println!("frame {} camera {},{},{} digest {} blit {} roundtrip {}", i, sh.cam.x, sh.cam.z, facing_letter(sh.cam.facing), sh.composed.frame_digest, sh.blit, if sh.roundtrip_ok { "OK" } else { "BROKEN" });
    }
    println!("playback head {} moves {} edits {} final {},{},{}", p.head, p.moves, p.edits, p.final_cam.x, p.final_cam.z, facing_letter(p.final_cam.facing));
}

pub fn checkpoint(session: &str, root_prefix: &str, at: usize, out: &str) {
    let s = load_sealed(session, root_prefix);
    if at > s.log.len() {
        refuse("USAGE", "--at is past the end of the log");
    }
    // replay the prefix [0..at) to reconstruct the WHOLE authority at event `at`; print the prefix move frames
    let head0 = genesis(&s.base_content, s.cam0);
    let mut level = s.level_bytes.clone();
    let mut tiles = s.tiles_bytes.clone();
    let mut cam = s.cam0;
    let mut head = head0;
    for k in 0..at {
        match &s.log[k] {
            Event::Move(c) => {
                cam = step(&level, cam, *c);
                let composed = compose_frame(&level, &tiles, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
                head = fold(&head, b'M', &composed.frame_digest);
                println!("prefix frame camera {},{},{} digest {}", cam.x, cam.z, facing_letter(cam.facing), composed.frame_digest);
            }
            Event::Edit(spec) => {
                apply_spec(&mut level, &mut tiles, spec);
                head = fold(&head, b'E', &content_hex(&level, &tiles));
            }
        }
    }
    // the checkpoint captures level bytes + tiles bytes + camera + head — the FULL interleaved authority
    fs::write(format!("{}.lvl", out), &level).unwrap_or_else(|e| refuse("CANNOT-WRITE", &e.to_string()));
    fs::write(format!("{}.tiles", out), &tiles).unwrap_or_else(|e| refuse("CANNOT-WRITE", &e.to_string()));
    let meta = format!("{{\"at\":{},\"camera\":\"{},{},{}\",\"head\":\"{}\"}}\n", at, cam.x, cam.z, facing_letter(cam.facing), head);
    fs::write(out, meta.as_bytes()).unwrap_or_else(|e| refuse("CANNOT-WRITE", &e.to_string()));
    println!("checkpoint at {} head {} camera {},{},{}", at, &head[..12], cam.x, cam.z, facing_letter(cam.facing));
}

pub fn resume(session: &str, root_prefix: &str, ck: &str) {
    let s = load_sealed(session, root_prefix);
    let meta = parse_json(&read(ck)).unwrap_or_else(|m| refuse("INVALID-CHECKPOINT", &m));
    let at = match meta.get("at") {
        Json::Num(n) => *n as usize,
        _ => refuse("INVALID-CHECKPOINT", "no at"),
    };
    let cam = parse_camera(meta.get("camera").s()).unwrap_or_else(|Refusal(m)| refuse("INVALID-CHECKPOINT", &m));
    let head = meta.get("head").s().to_string();
    let level = read(&format!("{}.lvl", ck));
    let tiles = read(&format!("{}.tiles", ck));
    let p = replay_from(&s, level, tiles, cam, head, at);
    if p.head != s.head {
        refuse("DIVERGED", &format!("resumed head {} != the sealed head {} — the checkpoint did not carry the whole authority", &p.head[..12], &s.head[..12.min(s.head.len())]));
    }
    for sh in &p.shown {
        println!("suffix frame camera {},{},{} digest {} roundtrip {}", sh.cam.x, sh.cam.z, facing_letter(sh.cam.facing), sh.composed.frame_digest, if sh.roundtrip_ok { "OK" } else { "BROKEN" });
    }
    println!("resume head {} from {} — {} suffix frames", &p.head[..12], at, p.shown.len());
}

/// The frame sequence a window would present (used by the cfg-gated host window playback).
#[allow(dead_code)]
pub fn frames(session: &str, root_prefix: &str) -> Vec<Composed> {
    let s = load_sealed(session, root_prefix);
    let p = replay_all(&s);
    if p.head != s.head {
        refuse("DIVERGED", "re-derived head != the sealed head");
    }
    p.shown.into_iter().map(|sh| sh.composed).collect()
}

/// LATENCY-1R's inputs: for every MOVE of the sealed session, the authority it renders (level + tiles after the
/// preceding edits), its camera, and its SEALED frame witness. The session is first replayed in full by the same
/// witness-checked path `frames()` uses (a tampered session refuses `DIVERGED`); nothing here is timed.
#[allow(dead_code)]
pub fn frame_inputs(session: &str, root_prefix: &str) -> Vec<(Vec<u8>, Vec<u8>, Camera, String)> {
    let s = load_sealed(session, root_prefix);
    let p = replay_all(&s);
    if p.head != s.head {
        refuse("DIVERGED", "re-derived head != the sealed head");
    }
    let (mut level, mut tiles, mut cam) = (s.level_bytes.clone(), s.tiles_bytes.clone(), s.cam0);
    let mut out = Vec::new();
    for k in 0..s.log.len() {
        match &s.log[k] {
            Event::Move(c) => {
                cam = step(&level, cam, *c);
                out.push((level.clone(), tiles.clone(), cam, s.stored[k].1.clone()));
            }
            Event::Edit(spec) => apply_spec(&mut level, &mut tiles, spec),
        }
    }
    out
}
