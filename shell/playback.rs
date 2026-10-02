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
            // SIM-TICK-0: a look turns the heading off the four facings playback shows
            "look" => refuse("HEADING", "the session holds a look: playback shows the four facings only; a free heading on the screen is MOUSE-LOOK-0's"),
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

// ================================================================== LIVE-INPUT-0 (appended): the live session
// A session-walk written live, in memory. Its only inputs are events appended to its log — a move command, or a cell
// edit validated as the workshop's `apply` validates one (inside the level; a border cell stays rock) — and W, M, the
// camera and the head are that log's replay by the statements `replay_from` makes: `step`, `apply_spec`, `content_hex`,
// the frame digest of `compose_frame`, `fold`. The replay is resumed one event at a time from the replay of the log
// before it (a left fold: replaying log[..n+1] is replaying log[..n] and then one event — the equivalence the
// checkpoint rows certify). Its fields are private: a caller reads the state and appends events, and cannot write W or
// M. Nothing here touches a file: saving and recovering a live session is LIVE-SESSION-0's.

/// One appended event and the state its replay reached: the tag (b'M' a move, b'E' an edit), the command letter or the
/// edit's spec, the camera after it, its witness (the frame digest for a move, the content for an edit), and the
/// content and the head after it.
pub struct LiveEvent {
    pub tag: u8,
    pub param: String,
    pub camera: Camera,
    pub witness: String,
    pub content: String,
    pub head: String,
    /// SIM-TICK-0: the heading after the event (an anchor unless a look has turned it), the tick it was applied at when
    /// a tick run appended it, and a timed look's inputs (counts, multiplier, step).
    pub yaw: i64,
    pub tick: Option<u64>,
    pub input: Option<(i64, i64, i64)>,
}

/// LIVE-INPUT-0's session: the replay of an in-memory log, appended to only by `push_move` and `push_edit_cell`.
pub struct LiveSession {
    level: Vec<u8>,
    tiles: Vec<u8>,
    cam: Camera,
    content: String,
    head: String,
    cam0: Camera,
    base_content: String,
    genesis: String,
    log: Vec<LiveEvent>,
    sink: Option<Box<dyn EventSink>>,
    // SIM-TICK-0: the heading (the facing is always its nearest cardinal), the tick stamped on events appended now, the
    // session's tick block (count, multiplier, step) once it ran on ticks, and the base bytes the log replays from
    yaw: i64,
    tick: Option<u64>,
    ticks: Option<(u64, i64, i64)>,
    base_level: Vec<u8>,
    base_tiles: Vec<u8>,
}

impl LiveSession {
    /// A new session over a base authority and an initial camera, as `sessionwalk new` makes one: the base must compose
    /// and the camera must stand on a traversable cell. The log is empty and the head is the genesis.
    pub fn new(level_bytes: Vec<u8>, tiles_bytes: Vec<u8>, cam0: Camera) -> Result<LiveSession, String> {
        crate::present::scene_of(&level_bytes, &tiles_bytes, cam0).map_err(|Refusal(m)| m)?;
        if !traversable(&level_bytes, cam0.x, cam0.z) {
            return Err("the initial camera stands on rock or off the level".to_string());
        }
        let base_content = content_hex(&level_bytes, &tiles_bytes);
        let head = genesis(&base_content, cam0);
        let (base_level, base_tiles) = (level_bytes.clone(), tiles_bytes.clone());
        Ok(LiveSession { level: level_bytes, tiles: tiles_bytes, cam: cam0, content: base_content.clone(), head: head.clone(),
                         cam0, base_content, genesis: head, log: Vec::new(), sink: None,
                         yaw: cam0.facing as i64 * crate::simtick::QUARTER, tick: None, ticks: None, base_level, base_tiles })
    }

    /// LIVE-SESSION-0: the same session, handing every event appended from now on to `sink`.
    pub fn with_sink(mut self, sink: Box<dyn EventSink>) -> LiveSession {
        self.sink = Some(sink);
        self
    }

    /// Hand the event just appended to the sink, if there is one.
    fn handed(&mut self) {
        let k = self.log.len() - 1;
        if let Some(s) = self.sink.as_mut() {
            s.appended(k, &self.log[k]);
        }
    }

    pub fn camera(&self) -> Camera {
        self.cam
    }

    pub fn cam0(&self) -> Camera {
        self.cam0
    }

    pub fn head(&self) -> &str {
        &self.head
    }

    pub fn genesis(&self) -> &str {
        &self.genesis
    }

    pub fn base_content(&self) -> &str {
        &self.base_content
    }

    /// content(W, M) of the current state.
    pub fn content(&self) -> &str {
        &self.content
    }

    /// sha256 of the current level bytes (W) and of the current tiles bytes (M).
    pub fn w_hex(&self) -> String {
        hex(&sha256(&self.level))
    }

    pub fn m_hex(&self) -> String {
        hex(&sha256(&self.tiles))
    }

    pub fn log(&self) -> &[LiveEvent] {
        &self.log
    }

    /// The kernel's scene of the current state: what a live loop renders.
    pub fn scene(&self) -> Result<crate::mantle::Scene, Refusal> {
        crate::present::scene_of(&self.level, &self.tiles, self.cam)
    }

    /// The faced cell: one step ahead of the camera, the cell a forward step targets.
    pub fn faced(&self) -> (i64, i64) {
        let (dx, dz) = forward(self.cam.facing);
        (self.cam.x + dx, self.cam.z + dz)
    }

    /// The current level's cell at (x, z), or None outside the level.
    pub fn cell(&self, x: i64, z: i64) -> Option<u8> {
        let (w, rows) = level_wh(&self.level);
        if x < 0 || z < 0 || x as usize >= w || z as usize >= rows {
            None
        } else {
            Some(self.level[16 + z as usize * w + x as usize])
        }
    }

    /// Append a move and replay it: `step` against the current level (a blocked step stays put and is still logged),
    /// the frame digest at the new camera over the current W and M, the fold.
    pub fn push_move(&mut self, cmd: u8) -> Result<&LiveEvent, String> {
        if !matches!(cmd, b'L' | b'R' | b'F' | b'B' | b'Q' | b'E') {
            return Err(format!("unknown move {:?}", cmd as char));
        }
        let cam = step(&self.level, self.cam, cmd);
        // SIM-TICK-0: a quarter turn turns the heading with the facing; the frame is the facing kernel's at an anchor
        // (as before) and the bearing kernel's at a free heading
        let yaw = turned(self.yaw, self.cam.facing, cam.facing);
        let witness = crate::heading::witness(&self.level, &self.tiles, cam, yaw)?;
        self.cam = cam;
        self.yaw = yaw;
        self.head = fold(&self.head, b'M', &witness);
        self.log.push(LiveEvent { tag: b'M', param: (cmd as char).to_string(), camera: cam, witness,
                                  content: self.content.clone(), head: self.head.clone(), yaw, tick: self.tick, input: None });
        self.handed();
        Ok(&self.log[self.log.len() - 1])
    }

    /// Append a cell edit and replay it, after validating it as the workshop's `apply` does: the cell inside the level,
    /// a border cell only ever rock, the value one of the level's alphabet. A refused edit is not appended.
    pub fn push_edit_cell(&mut self, x: i64, z: i64, to: u8) -> Result<&LiveEvent, (&'static str, String)> {
        let (w, rows) = level_wh(&self.level);
        if x < 0 || z < 0 || x as usize >= w || z as usize >= rows {
            return Err(("OUTSIDE", format!("cell ({}, {}) is outside the {}x{} level", x, z, w, rows)));
        }
        if (x == 0 || z == 0 || x as usize == w - 1 || z as usize == rows - 1) && to != b'#' {
            return Err(("BORDER", format!("cell ({}, {}) is on the border, which must stay rock", x, z)));
        }
        if !matches!(to, b'#' | b'.' | b'<' | b'>') {
            return Err(("VALUE", format!("cell value {:?} is not in #.<>", to as char)));
        }
        let spec = format!("cell:{},{},{}", x, z, to as char);
        apply_spec(&mut self.level, &mut self.tiles, &spec);
        self.content = content_hex(&self.level, &self.tiles);
        self.head = fold(&self.head, b'E', &self.content);
        self.log.push(LiveEvent { tag: b'E', param: spec, camera: self.cam, witness: self.content.clone(),
                                  content: self.content.clone(), head: self.head.clone(), yaw: self.yaw, tick: self.tick, input: None });
        self.handed();
        Ok(&self.log[self.log.len() - 1])
    }
}

// ================================================================== LIVE-SESSION-0 (appended): reading a saved live session
// The sink a LiveSession hands each appended event to (the journal lives in shell/livesession.rs), the session-walk
// parser above lent to LIVE-SESSION-0's loader as a read-only view, and the chain's own fold: the heads a saved log's
// witnesses fold to from its base, computed without rendering. Nothing here opens a file.

/// LIVE-SESSION-0: where an appended event goes once it is appended (the journal). The session hands it each event
/// after the replay advanced; a sink cannot refuse or change the event, and keeps its own account of what it did.
pub trait EventSink {
    fn appended(&mut self, index: usize, ev: &LiveEvent);
}

/// A parsed JSON value, read-only.
pub struct JsonView(Json);

impl JsonView {
    pub fn get(&self, k: &str) -> JsonView {
        JsonView(self.0.get(k).clone())
    }
    pub fn s(&self) -> String {
        self.0.s().to_string()
    }
    pub fn is_str(&self) -> bool {
        matches!(self.0, Json::Str(_))
    }
    pub fn is_null(&self) -> bool {
        matches!(self.0, Json::Null)
    }
    pub fn num(&self) -> Option<i64> {
        match &self.0 {
            Json::Num(n) => Some(*n),
            _ => None,
        }
    }
    pub fn arr(&self) -> Vec<JsonView> {
        self.0.arr().iter().map(|j| JsonView(j.clone())).collect()
    }
}

/// Parse a saved session, or one journal record's payload, into a read-only view.
pub fn parse_view(b: &[u8]) -> Result<JsonView, String> {
    parse_json(b).map(JsonView)
}

/// content(W, M) of raw level and tiles bytes, as the chain defines it.
pub fn content_of(level_bytes: &[u8], tiles_bytes: &[u8]) -> String {
    content_hex(level_bytes, tiles_bytes)
}

/// The heads a log's witnesses fold to from a base: the genesis first, then one per event (tag b'M' or b'E', witness).
/// The chain's own `genesis` and `fold`; no rendering.
pub fn chain_heads(base_content: &str, cam0: Camera, events: &[(u8, String)]) -> Vec<String> {
    let mut h = genesis(base_content, cam0);
    let mut out = vec![h.clone()];
    for (tag, w) in events {
        h = fold(&h, *tag, w);
        out.push(h.clone());
    }
    out
}

// ================================================================== LIVE-AUTHOR-0 (appended): tile edits on the live session
// A tile edit is a SESSION-WALK event like a cell edit: `apply_spec` fills the class, its witness is the new content,
// it folds into the head and is handed to the sink. The loop reads a class's current colour here and appends; it holds
// no colour of its own.

/// The tile classes, in the order of the tiles file (and of `apply_spec`).
pub const TILE_CLASSES: [&str; 5] = ["wall0", "wall1", "wall2", "wall3", "floor"];

impl LiveSession {
    /// A class's colour when its tile is one solid colour, or None (a textured tile).
    pub fn tile_rgb(&self, class: u8) -> Option<[u8; 3]> {
        if class as usize >= TILE_CLASSES.len() {
            return None;
        }
        let off = 8 + class as usize * TILE_BYTES;
        let t = self.tiles.get(off..off + TILE_BYTES)?;
        let first = [t[0], t[1], t[2]];
        if t.chunks_exact(3).all(|p| p == first) { Some(first) } else { None }
    }

    /// Append a tile edit and replay it: the class filled with one colour, the content, the fold.
    pub fn push_edit_tile(&mut self, class: u8, rgb: [u8; 3]) -> Result<&LiveEvent, String> {
        if class as usize >= TILE_CLASSES.len() {
            return Err(format!("tile class {} is not one of wall0..wall3, floor", class));
        }
        let spec = format!("tile:{},{},{},{}", TILE_CLASSES[class as usize], rgb[0], rgb[1], rgb[2]);
        apply_spec(&mut self.level, &mut self.tiles, &spec);
        self.content = content_hex(&self.level, &self.tiles);
        self.head = fold(&self.head, b'E', &self.content);
        self.log.push(LiveEvent { tag: b'E', param: spec, camera: self.cam, witness: self.content.clone(),
                                  content: self.content.clone(), head: self.head.clone(), yaw: self.yaw, tick: self.tick, input: None });
        self.handed();
        Ok(&self.log[self.log.len() - 1])
    }
}

// ================================================================== SIM-TICK-0 (appended): the heading, the look, the tick stamp
// The session's camera gains a heading: an id in [0, 360000), millidegrees clockwise from north. It starts at the base
// facing's anchor; a quarter turn turns it with the facing; a look — the one new event — turns it by an integer delta.
// The facing is always the heading's nearest cardinal, so a step, a strafe and the faced cell are what they were, taken
// toward that cardinal. A look's witness is the frame digest at the new heading; it is folded with tag K over the camera
// token and the witness together — head' = sha256(head : K : token : witness) — because one index frame can be shared
// by neighbouring headings, and the head must tell them apart. The camera token keeps its letter at an anchor and
// carries the id elsewhere. A tick run stamps the events it appends with their tick, and a timed look with its inputs;
// the stamp is recorded beside the event and never folded.

/// The camera token: "x,z,F" at an anchor heading, "x,z,K" (the id, in decimal) at any other.
pub fn token(cam: Camera, yaw: i64) -> String {
    match crate::simtick::anchor(yaw) {
        Some(_) => format!("{},{},{}", cam.x, cam.z, facing_letter(cam.facing)),
        None => format!("{},{},{}", cam.x, cam.z, yaw),
    }
}

/// What a look folds into the head after its tag: the camera token it reached, then its witness.
pub fn look_fold(token: &str, witness: &str) -> String {
    format!("{}:{}", token, witness)
}

/// The heading after a move: turned by as many quarter turns as the facing was.
fn turned(yaw: i64, before: u8, after: u8) -> i64 {
    crate::simtick::turn(yaw, crate::simtick::QUARTER * ((after + 4 - before) % 4) as i64)
}

impl LiveSession {
    /// The heading id.
    pub fn yaw(&self) -> i64 {
        self.yaw
    }

    /// The current camera's token.
    pub fn token(&self) -> String {
        token(self.cam, self.yaw)
    }

    /// Whether the heading is off the four anchors.
    pub fn free_heading(&self) -> bool {
        crate::simtick::anchor(self.yaw).is_none()
    }

    /// Stamp every event appended from now on with this tick (None: appended outside time).
    pub fn at_tick(&mut self, tick: Option<u64>) {
        self.tick = tick;
    }

    /// The session's tick block once it has run on ticks: the tick count, and the sensitivity's multiplier and step.
    pub fn ticks(&self) -> Option<(u64, i64, i64)> {
        self.ticks
    }

    pub fn set_ticks(&mut self, ticks: Option<(u64, i64, i64)>) {
        self.ticks = ticks;
    }

    /// Append a look and replay it: the heading turned by `delta` ids, the facing its nearest cardinal, the frame digest
    /// at the new heading over the current W and M, the fold. A zero delta, or one outside the bound, is not appended.
    pub fn push_look(&mut self, delta: i64, input: Option<(i64, i64, i64)>) -> Result<&LiveEvent, String> {
        if delta == 0 || delta > crate::simtick::DELTA_MAX || delta < -crate::simtick::DELTA_MAX {
            return Err(format!("a look of {} ids is zero or outside the bound", delta));
        }
        let yaw = crate::simtick::turn(self.yaw, delta);
        let cam = Camera { x: self.cam.x, z: self.cam.z, facing: crate::simtick::cardinal(yaw) };
        let witness = crate::heading::witness(&self.level, &self.tiles, cam, yaw)?;
        self.cam = cam;
        self.yaw = yaw;
        self.head = fold(&self.head, b'K', &look_fold(&token(cam, yaw), &witness));
        self.log.push(LiveEvent { tag: b'K', param: delta.to_string(), camera: cam, witness, content: self.content.clone(),
                                  head: self.head.clone(), yaw, tick: self.tick, input });
        self.handed();
        Ok(&self.log[self.log.len() - 1])
    }

    /// The log's frame events at free headings, in log order, each with the W and M it was rendered over — the frames
    /// the reference recomputes before a save. The log is replayed from the base for W and M only (no rendering), and
    /// the frames are handed over in batches of at most `batch`, so no more than a batch of states is held at once.
    /// Returns how many frames were handed over, or the first error `each` gave.
    pub fn free_frames<E>(&self, batch: usize, each: &mut dyn FnMut(&[crate::heading::FreeFrame]) -> Result<(), E>) -> Result<usize, E> {
        use std::sync::Arc;
        let (mut level, mut tiles) = (self.base_level.clone(), self.base_tiles.clone());
        let (mut la, mut ta): (Option<Arc<Vec<u8>>>, Option<Arc<Vec<u8>>>) = (None, None);
        let mut out: Vec<crate::heading::FreeFrame> = Vec::new();
        let mut n = 0;
        for (k, ev) in self.log.iter().enumerate() {
            if ev.tag == b'E' {
                apply_spec(&mut level, &mut tiles, &ev.param);
                if ev.param.starts_with("cell:") { la = None } else { ta = None }
                continue;
            }
            if crate::simtick::anchor(ev.yaw).is_some() {
                continue;
            }
            let l = la.get_or_insert_with(|| Arc::new(level.clone())).clone();
            let t = ta.get_or_insert_with(|| Arc::new(tiles.clone())).clone();
            out.push(crate::heading::FreeFrame { event: k, level: l, tiles: t, x: ev.camera.x, z: ev.camera.z, yaw: ev.yaw, witness: ev.witness.clone() });
            n += 1;
            if out.len() >= batch.max(1) {
                each(&out)?;
                out.clear();
            }
        }
        if !out.is_empty() {
            each(&out)?;
        }
        Ok(n)
    }
}
