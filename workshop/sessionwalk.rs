// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// workshop/sessionwalk.rs — SESSION-WALK: one interleaved sealed chain of edits AND moves.
//
// WORKSHOP-1 sealed a log of EDITS; INPUT-0 sealed a log of MOVES. Fusing them is the studio's real loop —
// move around while authoring — but the two cannot be two independent chains: a move's traversability and its
// frame are decided against the CURRENT world, so an edit that opens a cell changes what a later move sees. If
// the two chains were independent and edits were deferred, batching would change the trajectory: the same
// events would mean different things. So a session-walk is ONE append-only log, and every event is evaluated
// in log order against the authority produced by all preceding events:
//
//     EDIT(open 28,27) ; MOVE(F)   -> the move steps through the opened cell   (28,28 -> 28,27)
//     MOVE(F) ; EDIT(open 28,27)   -> the move is blocked by rock, then the edit opens it (28,28 stays)
//
// The head is a single left fold, so it is checkpoint/replay-equivalent: a scheduler may verify events in any
// batching it likes, but the sealed head is a function of the event ORDER alone, not of when verification runs.
// walk_head and edit_head are then DERIVED PROJECTIONS of this one chain, never independent authorities.
//
//   content(W,M) = sha256( sha256(W) ‖ sha256(M) )          (the authority state, as in WORKSHOP-1)
//   head0        = sha256( MAGIC ‖ content(base) ‖ "@" ‖ "x,z,F" )
//   move  i:  witness = the kernel URDRFB1 frame digest at the new camera over the CURRENT (W,M)
//   edit  i:  witness = content(W',M') after applying the edit
//   head        = sha256( head ‖ ":" ‖ tag ‖ ":" ‖ witness )     tag = "M" (move) | "E" (edit)
//
// SIM-TICK-0: the camera gains a heading, an id in [0, 360000) (millidegrees clockwise from north, the carried
// vocabulary of urdr-oracle-2). It starts at the base facing's anchor; a quarter turn turns it with the facing; a LOOK —
// one more event kind — turns it by an integer delta. The facing is always the heading's nearest cardinal,
// ((k + 45000) div 90000) mod 4, so a step, a strafe and an edit mean what they meant, taken toward that cardinal.
//
//   look  i:  witness = the frame digest at the new heading over the CURRENT (W,M)
//             head    = sha256( head ‖ ":K:" ‖ token ‖ ":" ‖ witness )   — the camera token is folded with the witness,
//                       because one index frame can be shared by neighbouring headings
//
// At one of the four anchor headings a frame is the facing kernel's, as before, and the token keeps its letter; at any
// other it is the bearing REFERENCE kernel's (kernel/bearing.rs) and the token carries the id. This verifier renders
// with the reference only: the production tread the shell renders live with is not here. An event may carry the tick a
// tick run applied it at, and a timed look its inputs (counts, multiplier, step); `verify` checks their form — the delta
// is counts x multiplier x step, ticks never decrease, a timed look is the first event of its tick — and never folds
// them: a tick is when, not what.
//
// SIM-TICK-0a: a tick session also records its sensitivity changes, each as one event of kind sensitivity carrying the
// configuration after it (the multiplier and the step). It is configuration, not a world event: it has no witness and
// folds nothing, so the head after it is the head before it. `verify` replays the configuration from multiplier 1,
// step 88: each sensitivity event must be exactly one legal transition and carry a tick, a timed look's inputs must
// carry the configuration in force, and the tick block the configuration at the end.
//
// A move never changes W or M (the camera is projection-owned, WORKSHOP-0b); an edit never moves the camera.
// `verify` replays from the base, re-derives every witness and the head, and catches a tampered event. Timing
// is NOT here: the 144Hz/batch scheduler is a LATENCY-0 hypothesis; this file is headless and clock-free.
//
//     rustc -O workshop/sessionwalk.rs -o build/sessionwalk
//     sessionwalk new   --level L --tiles T --camera x,z,F --out S.json
//     sessionwalk move  --session S.json --command F
//     sessionwalk edit  --session S.json --edit cell:28,27,.
//     sessionwalk look  --session S.json --delta D     # SIM-TICK-0: turn the heading by D ids (untimed)
//     sessionwalk replay --session S.json     # recompute head/trajectory from the base (monolithic)
//     sessionwalk verify --session S.json     # replay, check the stored head and every witness

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;
// SIM-TICK-0: the carried vocabulary and the bearing reference kernel (never the fast path)
#[allow(dead_code)]
#[path = "../kernel/vocab.rs"]
mod vocab;
#[allow(dead_code)]
#[path = "../kernel/bearing.rs"]
mod bearing;

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::process::exit;

use formats::{compose, facing_letter, level_bytes, parse_camera, parse_level, parse_tiles, tiles_bytes, Camera, Level, Tiles, ALPHABET};
use mantle::{hex, parse_scene, picture, sha256, Refusal};

const MAGIC: &[u8] = b"VRDNSW1";

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("SESSIONWALK-{}: {}", code, detail);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path, e)))
}

// ------------------------------------------------------------------ a small JSON value (self-contained I/O)
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

fn obj(pairs: Vec<(&str, Json)>) -> Json {
    Json::Obj(pairs.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
}

fn esc(s: &str) -> String {
    let mut o = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' => o.push_str("\\n"),
            '\r' => o.push_str("\\r"),
            '\t' => o.push_str("\\t"),
            c if (c as u32) < 0x20 => o.push_str(&format!("\\u{:04x}", c as u32)),
            c => o.push(c),
        }
    }
    o.push('"');
    o
}

fn write_json(v: &Json, indent: usize, out: &mut String) {
    let pad = " ".repeat(indent);
    match v {
        Json::Null => out.push_str("null"),
        Json::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Json::Num(n) => out.push_str(&n.to_string()),
        Json::Str(s) => out.push_str(&esc(s)),
        Json::Arr(a) => {
            if a.is_empty() {
                out.push_str("[]");
                return;
            }
            out.push_str("[\n");
            for (i, x) in a.iter().enumerate() {
                out.push_str(&pad);
                out.push(' ');
                write_json(x, indent + 1, out);
                out.push_str(if i + 1 < a.len() { ",\n" } else { "\n" });
            }
            out.push_str(&pad);
            out.push(']');
        }
        Json::Obj(m) => {
            out.push_str("{\n");
            for (i, (k, x)) in m.iter().enumerate() {
                out.push_str(&pad);
                out.push(' ');
                out.push_str(&esc(k));
                out.push_str(": ");
                write_json(x, indent + 1, out);
                out.push_str(if i + 1 < m.len() { ",\n" } else { "\n" });
            }
            out.push_str(&pad);
            out.push('}');
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

// ------------------------------------------------------------------ authority, edits, chain (as in WORKSHOP-1)
struct Authority {
    level: Level,
    tiles: Tiles,
}

impl Authority {
    fn w_hex(&self) -> String {
        hex(&sha256(&level_bytes(&self.level)))
    }
    fn m_hex(&self) -> String {
        hex(&sha256(&tiles_bytes(&self.tiles)))
    }
    /// content = sha256( sha256(W) ‖ sha256(M) ) — the authority state, hex.
    fn content_hex(&self) -> String {
        let mut buf = Vec::with_capacity(64);
        buf.extend_from_slice(&sha256(&level_bytes(&self.level)));
        buf.extend_from_slice(&sha256(&tiles_bytes(&self.tiles)));
        hex(&sha256(&buf))
    }
}

#[derive(Clone)]
enum Edit {
    Cell { x: usize, z: usize, to: u8 },
    Tile { class: String, rgb: [u8; 3] },
}

fn parse_edit(spec: &str) -> Result<Edit, String> {
    let (kind, rest) = spec.split_once(':').ok_or("edit has no kind (cell:… | tile:…)")?;
    match kind {
        "cell" => {
            let p: Vec<&str> = rest.split(',').collect();
            if p.len() != 3 {
                return Err("cell:X,Z,C".into());
            }
            let x = p[0].trim().parse().map_err(|_| "cell X")?;
            let z = p[1].trim().parse().map_err(|_| "cell Z")?;
            let c = p[2].trim().as_bytes();
            if c.len() != 1 || !ALPHABET.contains(&c[0]) {
                return Err(format!("cell value {:?} not in #.<>", p[2]));
            }
            Ok(Edit::Cell { x, z, to: c[0] })
        }
        "tile" => {
            let p: Vec<&str> = rest.split(',').collect();
            if p.len() != 4 {
                return Err("tile:CLASS,R,G,B".into());
            }
            let class = p[0].trim().to_string();
            if !matches!(class.as_str(), "wall0" | "wall1" | "wall2" | "wall3" | "floor") {
                return Err(format!("tile class {:?} not wall0..wall3 or floor", class));
            }
            let mut rgb = [0u8; 3];
            for (i, q) in p[1..].iter().enumerate() {
                rgb[i] = q.trim().parse().map_err(|_| "tile channel")?;
            }
            Ok(Edit::Tile { class, rgb })
        }
        other => Err(format!("edit kind {:?} not cell or tile", other)),
    }
}

fn edit_spec(e: &Edit) -> String {
    match e {
        Edit::Cell { x, z, to } => format!("cell:{},{},{}", x, z, *to as char),
        Edit::Tile { class, rgb } => format!("tile:{},{},{},{}", class, rgb[0], rgb[1], rgb[2]),
    }
}

/// Apply one edit to an authority, validating first. Pure: no camera, no clock, no I/O (as in WORKSHOP-1).
fn apply(auth: &mut Authority, e: &Edit) -> Result<(), String> {
    match e {
        Edit::Cell { x, z, to } => {
            let (w, rows) = (auth.level.w, auth.level.rows);
            if *x >= w || *z >= rows {
                return Err(format!("cell ({}, {}) outside the {}x{} level", x, z, w, rows));
            }
            let border = *x == 0 || *z == 0 || *x == w - 1 || *z == rows - 1;
            if border && *to != b'#' {
                return Err(format!("cell ({}, {}) is on the border, which must stay rock", x, z));
            }
            auth.level.cells[z * w + x] = *to;
            Ok(())
        }
        Edit::Tile { class, rgb } => {
            let tile: &mut Vec<u8> = match class.as_str() {
                "floor" => &mut auth.tiles.floor,
                "wall0" => &mut auth.tiles.walls[0],
                "wall1" => &mut auth.tiles.walls[1],
                "wall2" => &mut auth.tiles.walls[2],
                "wall3" => &mut auth.tiles.walls[3],
                other => return Err(format!("tile class {:?}", other)),
            };
            for px in tile.chunks_exact_mut(3) {
                px.copy_from_slice(rgb);
            }
            Ok(())
        }
    }
}

// ------------------------------------------------------------------ movement (as in INPUT-0)
fn forward(facing: u8) -> (i64, i64) {
    match facing {
        0 => (0, -1),
        1 => (1, 0),
        2 => (0, 1),
        _ => (-1, 0),
    }
}

fn traversable(level: &Level, x: i64, z: i64) -> bool {
    x >= 0 && z >= 0 && (x as usize) < level.w && (z as usize) < level.rows && level.cells[z as usize * level.w + x as usize] != b'#'
}

/// One move against the CURRENT level. A blocked step is a no-op (walking into a wall does not move you).
fn step(level: &Level, cam: Camera, cmd: u8) -> Result<Camera, String> {
    let mut c = cam;
    match cmd {
        b'L' => c.facing = (c.facing + 3) % 4,
        b'R' => c.facing = (c.facing + 1) % 4,
        b'F' | b'B' | b'Q' | b'E' => {
            let dir = match cmd {
                b'F' => forward(c.facing),
                b'B' => {
                    let (dx, dz) = forward(c.facing);
                    (-dx, -dz)
                }
                b'Q' => forward((c.facing + 3) % 4),
                _ => forward((c.facing + 1) % 4),
            };
            let (nx, nz) = (c.x + dir.0, c.z + dir.1);
            if traversable(level, nx, nz) {
                c.x = nx;
                c.z = nz;
            }
        }
        other => return Err(format!("unknown command {:?}", other as char)),
    }
    Ok(c)
}

/// The kernel URDRFB1 frame digest at a camera over the current authority.
fn frame_digest(auth: &Authority, cam: Camera) -> String {
    let scene = parse_scene(&compose(&auth.level, cam, &auth.tiles)).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    picture(&scene).frame_digest()
}

// ------------------------------------------------------------------ the heading (SIM-TICK-0)
const YAW_MOD: i64 = 360_000;
const QUARTER: i64 = 90_000;
const TICK_HZ: i64 = 64;
const STEP_COARSE: i64 = 88;
const STEP_FINE: i64 = 1;
const MULT_MAX: i64 = 64;
const COUNTS_MAX: i64 = 2_147_483_647;
const DELTA_MAX: i64 = COUNTS_MAX * MULT_MAX * STEP_COARSE;

/// The heading after a turn of `delta` ids.
fn turn(k: i64, delta: i64) -> i64 {
    (k + delta).rem_euclid(YAW_MOD)
}

/// The nearest cardinal of a heading: 0 N, 1 E, 2 S, 3 W; the tie at 45 degrees goes clockwise.
fn cardinal(k: i64) -> u8 {
    (((k + QUARTER / 2) / QUARTER) % 4) as u8
}

fn is_anchor(k: i64) -> bool {
    k % QUARTER == 0
}

/// The camera token: the letter at an anchor heading, the id anywhere else.
fn token(cam: Camera, yaw: i64) -> String {
    if is_anchor(yaw) {
        format!("{},{},{}", cam.x, cam.z, facing_letter(cam.facing))
    } else {
        format!("{},{},{}", cam.x, cam.z, yaw)
    }
}

/// The frame digest at a camera and heading: the facing kernel's at an anchor, the bearing reference kernel's elsewhere.
fn frame_at(auth: &Authority, voc: &mut Option<vocab::Vocab>, cam: Camera, yaw: i64) -> String {
    if is_anchor(yaw) {
        return frame_digest(auth, cam);
    }
    if voc.is_none() {
        *voc = Some(vocab::load().unwrap_or_else(|Refusal(m)| refuse("VOCABULARY", &m)));
    }
    let triple = voc.as_ref().unwrap().triple(yaw).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    let data = vocab::compose(&auth.level, vocab::BearingCamera { x: cam.x, z: cam.z, k: yaw }, triple, &auth.tiles);
    let scene = bearing::parse_scene(&data).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    let mut strips: Vec<bearing::Strip> = Vec::with_capacity(bearing::W);
    let mut frame = vec![0u8; bearing::W * bearing::H];
    scene.strips(&mut strips);
    scene.frame(&strips, &mut frame);
    bearing::frame_digest(&frame)
}

/// The tick stamp an event may carry: the tick a tick run applied it at, and a timed look's inputs.
#[derive(Clone, Copy, Default)]
struct Stamp {
    tick: Option<u64>,
    input: Option<(i64, i64, i64)>,
}

/// The tick form of a log: a look's delta non-zero and inside the bound; inputs only beside a timed look, multiplying
/// to its delta; ticks never decreasing; a timed look the first event of its tick; the tick block present exactly when
/// the session ran on ticks, and covering every tick.
fn check_form(log: &[Event], stamps: &[Stamp], ticks: Option<(i64, i64, i64, i64)>) -> Result<(), String> {
    let mut last: Option<u64> = None;
    // SIM-TICK-0a: the configuration in force, replayed from the start
    let mut config: (i64, i64) = (1, STEP_COARSE);
    for (k, (ev, st)) in log.iter().zip(stamps.iter()).enumerate() {
        if let Event::Sens(m, s) = ev {
            let valid = (1..=MULT_MAX).contains(m) && (*s == STEP_COARSE || *s == STEP_FINE);
            let one_step = (*s == config.1 && (*m == config.0 + 1 || *m == config.0 - 1)) || (*m == config.0 && *s != config.1);
            if st.tick.is_none() {
                return Err(format!("event {}: a sensitivity event with no tick", k));
            }
            if !valid || !one_step {
                return Err(format!("event {}: the sensitivity {},{} is not one legal transition from {},{}", k, m, s, config.0, config.1));
            }
            config = (*m, *s);
        }
        if let (Event::Look(_), Some((_, m, s))) = (ev, st.input) {
            if (m, s) != config {
                return Err(format!("event {}: a look's inputs carry the sensitivity {},{} and {},{} is in force", k, m, s, config.0, config.1));
            }
        }
        let look = match ev {
            Event::Look(d) => {
                if *d == 0 || *d > DELTA_MAX || *d < -DELTA_MAX {
                    return Err(format!("event {}: a look of {} ids is zero or outside the bound", k, d));
                }
                Some(*d)
            }
            _ => None,
        };
        match (look, st.tick, st.input) {
            (None, _, Some(_)) => return Err(format!("event {}: inputs beside an event that is not a look", k)),
            (Some(_), None, Some(_)) => return Err(format!("event {}: a look with inputs and no tick", k)),
            (Some(_), Some(_), None) => return Err(format!("event {}: a timed look without its inputs", k)),
            (Some(d), Some(_), Some((c, m, s))) => {
                let ok = c != 0 && (-COUNTS_MAX..=COUNTS_MAX).contains(&c) && (1..=MULT_MAX).contains(&m) && (s == STEP_COARSE || s == STEP_FINE);
                if !ok || c.checked_mul(m).and_then(|v| v.checked_mul(s)) != Some(d) {
                    return Err(format!("event {}: the delta {} is not counts {} x multiplier {} x step {}", k, d, c, m, s));
                }
            }
            _ => {}
        }
        if let Some(t) = st.tick {
            match last {
                Some(l) if t < l => return Err(format!("event {}: tick {} after tick {} — a tick ran backwards", k, t, l)),
                Some(l) if t == l && look.is_some() => return Err(format!("event {}: a look that is not the first event of tick {}", k, t)),
                _ => {}
            }
            last = Some(t);
        }
    }
    match (ticks, last) {
        (None, Some(_)) => Err("an event carries a tick but the session has no tick block".to_string()),
        (None, None) => Ok(()),
        (Some((hz, count, m, s)), _) => {
            if hz != TICK_HZ || count < 0 || !(1..=MULT_MAX).contains(&m) || !(s == STEP_COARSE || s == STEP_FINE) {
                return Err(format!("the tick block (hz {}, count {}, multiplier {}, step {}) is not a registered one", hz, count, m, s));
            }
            if (m, s) != config {
                return Err(format!("the tick block's sensitivity {},{} is not the configuration at the end of the log ({},{})", m, s, config.0, config.1));
            }
            match last {
                Some(l) if l as i128 >= count as i128 => Err(format!("tick {} is not below the session's tick count {}", l, count)),
                _ => Ok(()),
            }
        }
    }
}

// ------------------------------------------------------------------ the head (one interleaved left fold)
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

// ------------------------------------------------------------------ events and replay
#[derive(Clone)]
enum Event {
    Move(u8),
    Edit(Edit),
    Look(i64), // SIM-TICK-0: the heading turned by an integer delta
    Sens(i64, i64), // SIM-TICK-0a: the sensitivity after a change (multiplier, step) — configuration, not a world event
}

struct Replay {
    head: String,
    cam: Camera,
    yaw: i64,
    final_content: String,
    moves: usize,
    edits: usize,
    looks: usize,
    settings: usize,
    // per-event witnesses, in log order (for `verify` to check against the stored file)
    witnesses: Vec<(char, String)>, // ('M'|'E'|'K', witness hex; 'S' with no witness)
    tokens: Vec<String>,            // the camera token after each event
}

fn load_auth(level_path: &str, tiles_path: &str) -> Authority {
    let level = parse_level(&read(level_path)).unwrap_or_else(|Refusal(m)| refuse("INVALID-LEVEL", &m));
    let tiles = parse_tiles(&read(tiles_path)).unwrap_or_else(|Refusal(m)| refuse("INVALID-TILES", &m));
    Authority { level, tiles }
}

/// Replay the log from the base authority, folding one interleaved head. Every event is evaluated against the
/// authority produced by all preceding events.
fn replay(level_path: &str, tiles_path: &str, cam0: Camera, log: &[Event]) -> Replay {
    let mut auth = load_auth(level_path, tiles_path);
    if !traversable(&auth.level, cam0.x, cam0.z) {
        refuse("INVALID-CAMERA", "the initial camera stands on rock or off the level");
    }
    let base_content = auth.content_hex();
    let mut head = genesis(&base_content, cam0);
    let mut cam = cam0;
    let mut yaw = cam0.facing as i64 * QUARTER;
    let mut voc: Option<vocab::Vocab> = None;
    let (mut moves, mut edits, mut looks, mut settings) = (0usize, 0usize, 0usize, 0usize);
    let mut witnesses = Vec::new();
    let mut tokens = Vec::new();
    for ev in log {
        match ev {
            Event::Move(c) => {
                let before = cam.facing;
                cam = step(&auth.level, cam, *c).unwrap_or_else(|m| refuse("INVALID-COMMAND", &m));
                yaw = turn(yaw, QUARTER * ((cam.facing + 4 - before) % 4) as i64); // a quarter turn turns the heading
                let w = frame_at(&auth, &mut voc, cam, yaw);
                head = fold(&head, b'M', &w);
                witnesses.push(('M', w));
                moves += 1;
            }
            Event::Edit(e) => {
                apply(&mut auth, e).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
                let w = auth.content_hex();
                head = fold(&head, b'E', &w);
                witnesses.push(('E', w));
                edits += 1;
            }
            Event::Look(d) => {
                if *d == 0 || *d > DELTA_MAX || *d < -DELTA_MAX {
                    refuse("INVALID-LOOK", &format!("a look of {} ids is zero or outside the bound", d));
                }
                yaw = turn(yaw, *d);
                cam.facing = cardinal(yaw);
                let w = frame_at(&auth, &mut voc, cam, yaw);
                // a look folds the camera token with the witness
                head = fold(&head, b'K', &format!("{}:{}", token(cam, yaw), w));
                witnesses.push(('K', w));
                looks += 1;
            }
            Event::Sens(_, _) => {
                // SIM-TICK-0a: configuration, not a world event — no witness, nothing folded, nothing moved
                witnesses.push(('S', String::new()));
                settings += 1;
            }
        }
        tokens.push(token(cam, yaw));
    }
    Replay { head, cam, yaw, final_content: auth.content_hex(), moves, edits, looks, settings, witnesses, tokens }
}

// ------------------------------------------------------------------ the session-walk file
struct SessionWalk {
    level: String,
    tiles: String,
    base_w: String,
    base_m: String,
    base_content: String,
    cam0: Camera,
    log: Vec<Event>,
    head: String,
    // SIM-TICK-0: the tick stamp beside each event, and the session's tick block (hz, count, multiplier, step)
    stamps: Vec<Stamp>,
    ticks: Option<(i64, i64, i64, i64)>,
}

fn parse_camera_token(s: &str) -> Camera {
    parse_camera(s).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m))
}

fn event_json(ev: &Event, wit: &(char, String), tok: &str, st: &Stamp) -> Json {
    let mut pairs = match ev {
        Event::Move(c) => vec![
            ("kind", Json::Str("move".into())),
            ("command", Json::Str((*c as char).to_string())),
            ("camera", Json::Str(tok.to_string())),
            ("witness", Json::Str(wit.1.clone())),
        ],
        Event::Edit(e) => vec![
            ("kind", Json::Str("edit".into())),
            ("spec", Json::Str(edit_spec(e))),
            ("witness", Json::Str(wit.1.clone())),
        ],
        Event::Look(d) => vec![
            ("kind", Json::Str("look".into())),
            ("delta", Json::Num(*d)),
            ("camera", Json::Str(tok.to_string())),
            ("witness", Json::Str(wit.1.clone())),
        ],
        Event::Sens(m, s) => vec![
            ("kind", Json::Str("sensitivity".into())),
            ("multiplier", Json::Num(*m)),
            ("step", Json::Num(*s)),
        ],
    };
    // the tick stamp, kept as it was read (an untimed event has none)
    if let Some(t) = st.tick {
        pairs.push(("tick", Json::Num(t as i64)));
    }
    if let Some((c, m, s)) = st.input {
        pairs.push(("input", obj(vec![("counts", Json::Num(c)), ("multiplier", Json::Num(m)), ("step", Json::Num(s))])));
    }
    obj(pairs)
}

fn write_sessionwalk(path: &str, sw: &SessionWalk) {
    let r = replay(&sw.level, &sw.tiles, sw.cam0, &sw.log);
    let mut items = Vec::new();
    for (k, ev) in sw.log.iter().enumerate() {
        items.push(event_json(ev, &r.witnesses[k], &r.tokens[k], &sw.stamps[k]));
    }
    let mut data = vec![
        ("magic", Json::Str(String::from_utf8_lossy(MAGIC).into())),
        ("base", obj(vec![
            ("level", Json::Str(sw.level.clone())),
            ("tiles", Json::Str(sw.tiles.clone())),
            ("W", Json::Str(sw.base_w.clone())),
            ("M", Json::Str(sw.base_m.clone())),
            ("content", Json::Str(sw.base_content.clone())),
            ("camera", Json::Str(format!("{},{},{}", sw.cam0.x, sw.cam0.z, facing_letter(sw.cam0.facing)))),
        ])),
        ("log", Json::Arr(items)),
        ("head", Json::Str(r.head.clone())),
        ("final_camera", Json::Str(token(r.cam, r.yaw))),
        ("final_content", Json::Str(r.final_content.clone())),
        ("moves", Json::Num(r.moves as i64)),
        ("edits", Json::Num(r.edits as i64)),
    ];
    // SIM-TICK-0: the looks are counted only when there are some, and the tick block is kept only if the session has
    // one, so a walk with neither is written as it always was
    if r.looks > 0 {
        data.push(("looks", Json::Num(r.looks as i64)));
    }
    if r.settings > 0 {
        data.push(("sensitivity_changes", Json::Num(r.settings as i64)));
    }
    if let Some((hz, count, m, s)) = sw.ticks {
        data.push(("ticks", obj(vec![("hz", Json::Num(hz)), ("count", Json::Num(count)), ("multiplier", Json::Num(m)), ("step", Json::Num(s))])));
    }
    let root = obj(vec![("name", Json::Str("verdandi-session-walk".into())), ("data", obj(data))]);
    let mut out = String::new();
    write_json(&root, 0, &mut out);
    out.push('\n');
    fs::write(path, out.as_bytes()).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", path, e)));
}

fn num(j: &Json) -> Option<i64> {
    match j {
        Json::Num(n) => Some(*n),
        _ => None,
    }
}

fn is_null(j: &Json) -> bool {
    matches!(j, Json::Null)
}

/// Returns the session, each event's stored (tag, witness), each event's stored camera token ("" for an edit) and the
/// stored final camera.
fn load_sessionwalk(path: &str) -> (SessionWalk, Vec<(char, String)>, Vec<String>, String) {
    let root = parse_json(&read(path)).unwrap_or_else(|m| refuse("INVALID-SESSION", &m));
    if root.get("name").s() != "verdandi-session-walk" {
        refuse("INVALID-SESSION", "not a verdandi-session-walk");
    }
    let d = root.get("data");
    let base = d.get("base");
    let cam0 = parse_camera_token(base.get("camera").s());
    let mut log = Vec::new();
    let mut stored = Vec::new();
    let mut cameras = Vec::new();
    let mut stamps = Vec::new();
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
                let e = parse_edit(item.get("spec").s()).unwrap_or_else(|m| refuse("INVALID-SESSION", &m));
                log.push(Event::Edit(e));
                stored.push(('E', item.get("witness").s().to_string()));
            }
            "look" => {
                let dl = num(item.get("delta")).unwrap_or_else(|| refuse("INVALID-SESSION", "a look without an integer delta"));
                log.push(Event::Look(dl));
                stored.push(('K', item.get("witness").s().to_string()));
            }
            "sensitivity" => {
                match (num(item.get("multiplier")), num(item.get("step"))) {
                    (Some(m), Some(s)) => log.push(Event::Sens(m, s)),
                    _ => refuse("INVALID-SESSION", "a sensitivity event without its multiplier and step"),
                }
                stored.push(('S', item.get("witness").s().to_string()));
            }
            other => refuse("INVALID-SESSION", &format!("event kind {:?}", other)),
        }
        cameras.push(item.get("camera").s().to_string());
        let tick = match (is_null(item.get("tick")), num(item.get("tick"))) {
            (true, _) => None,
            (false, Some(t)) if t >= 0 => Some(t as u64),
            _ => refuse("INVALID-SESSION", "an event's tick is not a whole number"),
        };
        let i = item.get("input");
        let input = if is_null(i) {
            None
        } else {
            match (num(i.get("counts")), num(i.get("multiplier")), num(i.get("step"))) {
                (Some(c), Some(m), Some(s)) => Some((c, m, s)),
                _ => refuse("INVALID-SESSION", "a look's inputs are not counts, multiplier and step"),
            }
        };
        stamps.push(Stamp { tick, input });
    }
    let t = d.get("ticks");
    let ticks = if is_null(t) {
        None
    } else {
        let n = |k: &str| num(t.get(k)).unwrap_or(-1);
        Some((n("hz"), n("count"), n("multiplier"), n("step")))
    };
    if let Err(m) = check_form(&log, &stamps, ticks) {
        refuse("TICK-FORM", &m);
    }
    let sw = SessionWalk {
        level: base.get("level").s().to_string(),
        tiles: base.get("tiles").s().to_string(),
        base_w: base.get("W").s().to_string(),
        base_m: base.get("M").s().to_string(),
        base_content: base.get("content").s().to_string(),
        cam0,
        log,
        head: d.get("head").s().to_string(),
        stamps,
        ticks,
    };
    (sw, stored, cameras, d.get("final_camera").s().to_string())
}

// ------------------------------------------------------------------ CLI
fn arg(argv: &[String], flag: &str) -> Option<String> {
    argv.iter().position(|a| a == flag).and_then(|i| argv.get(i + 1).cloned())
}

fn main() {
    let argv: Vec<String> = env::args().collect();
    if argv.len() < 2 {
        refuse("USAGE", "sessionwalk new|move|edit|replay|verify …");
    }
    match argv[1].as_str() {
        "new" => {
            let level = arg(&argv, "--level").unwrap_or_else(|| refuse("USAGE", "new needs --level"));
            let tiles = arg(&argv, "--tiles").unwrap_or_else(|| refuse("USAGE", "new needs --tiles"));
            let cam0 = parse_camera_token(&arg(&argv, "--camera").unwrap_or_else(|| refuse("USAGE", "new needs --camera")));
            let out = arg(&argv, "--out").unwrap_or_else(|| refuse("USAGE", "new needs --out"));
            let auth = load_auth(&level, &tiles);
            if !traversable(&auth.level, cam0.x, cam0.z) {
                refuse("INVALID-CAMERA", "the initial camera stands on rock or off the level");
            }
            let sw = SessionWalk {
                level: level.clone(),
                tiles: tiles.clone(),
                base_w: auth.w_hex(),
                base_m: auth.m_hex(),
                base_content: auth.content_hex(),
                cam0,
                log: Vec::new(),
                head: genesis(&auth.content_hex(), cam0),
                stamps: Vec::new(),
                ticks: None,
            };
            write_sessionwalk(&out, &sw);
            println!("SESSIONWALK new head {} base {},{},{}", &sw.head[..12], cam0.x, cam0.z, facing_letter(cam0.facing));
        }
        "move" | "edit" | "look" => {
            let path = arg(&argv, "--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let (mut sw, _st, _cams, _fc) = load_sessionwalk(&path);
            sw.stamps.push(Stamp::default()); // the workshop appends outside time: no tick
            if argv[1] == "look" {
                // SIM-TICK-0: an untimed look of D ids (canonical decimal, an optional leading minus)
                let dl = arg(&argv, "--delta").unwrap_or_else(|| refuse("USAGE", "look needs --delta"));
                let digits = dl.strip_prefix('-').unwrap_or(&dl);
                let canonical = !digits.is_empty() && digits.bytes().all(|c| c.is_ascii_digit()) && !digits.starts_with('0') && digits.len() <= 15;
                let v: i64 = match (canonical, dl.parse()) {
                    (true, Ok(v)) => v,
                    _ => refuse("INVALID-LOOK", "the delta is a non-zero whole number of heading ids, in canonical decimal"),
                };
                if v > DELTA_MAX || v < -DELTA_MAX {
                    refuse("INVALID-LOOK", &format!("a look of {} ids is outside the bound", v));
                }
                sw.log.push(Event::Look(v));
            } else if argv[1] == "move" {
                let c = arg(&argv, "--command").unwrap_or_else(|| refuse("USAGE", "move needs --command"));
                let cb = c.as_bytes();
                if cb.len() != 1 || !matches!(cb[0], b'L' | b'R' | b'F' | b'B' | b'Q' | b'E') {
                    refuse("INVALID-COMMAND", "command is one of L R F B Q E");
                }
                sw.log.push(Event::Move(cb[0]));
            } else {
                let spec = arg(&argv, "--edit").unwrap_or_else(|| refuse("USAGE", "edit needs --edit"));
                let e = parse_edit(&spec).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
                // validate the edit applies against the CURRENT authority (all prior edits applied) before appending
                let mut auth = load_auth(&sw.level, &sw.tiles);
                for ev in &sw.log {
                    if let Event::Edit(pe) = ev {
                        apply(&mut auth, pe).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
                    }
                }
                if let Err(m) = apply(&mut auth, &e) {
                    refuse("INVALID-EDIT", &m);
                }
                sw.log.push(Event::Edit(e));
            }
            write_sessionwalk(&path, &sw);
            let r = replay(&sw.level, &sw.tiles, sw.cam0, &sw.log);
            println!("SESSIONWALK {} head {} — moves {} edits {}{} (final {})", argv[1], &r.head[..12], r.moves, r.edits,
                     if r.looks > 0 { format!(" looks {}", r.looks) } else { String::new() }, token(r.cam, r.yaw));
        }
        "replay" => {
            let path = arg(&argv, "--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let (sw, _st, _cams, _fc) = load_sessionwalk(&path);
            let r = replay(&sw.level, &sw.tiles, sw.cam0, &sw.log);
            println!("final camera {}", token(r.cam, r.yaw).replace(',', " "));
            println!("final content {}", r.final_content);
            println!("committed moves {} edits {}{}", r.moves, r.edits, if r.looks > 0 { format!(" looks {}", r.looks) } else { String::new() });
            println!("head {}", r.head);
        }
        "verify" => {
            let path = arg(&argv, "--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let (sw, stored, cameras, final_cam) = load_sessionwalk(&path);
            let r = replay(&sw.level, &sw.tiles, sw.cam0, &sw.log);
            // every per-event witness must match, then the head, then the reported final camera
            if stored.len() != r.witnesses.len() {
                refuse("CHAIN-BROKEN", "the log length changed under replay");
            }
            for (k, (want, got)) in stored.iter().zip(r.witnesses.iter()).enumerate() {
                if want.0 != got.0 || want.1 != got.1 {
                    refuse("CHAIN-BROKEN", &format!("event {} witness diverged on replay — an event was tampered", k));
                }
            }
            // SIM-TICK-0: a stored camera token must be the replay's — a look's heading is what its token says
            for (k, (want, got)) in cameras.iter().zip(r.tokens.iter()).enumerate() {
                if !want.is_empty() && want != got {
                    refuse("CHAIN-BROKEN", &format!("event {}: stored camera {} != replay {}", k, want, got));
                }
            }
            if r.head != sw.head {
                refuse("CHAIN-BROKEN", &format!("replay head {} != the stored head {} — the log was tampered", &r.head[..12], &sw.head[..12.min(sw.head.len())]));
            }
            let want_cam = token(r.cam, r.yaw);
            if !final_cam.is_empty() && final_cam != want_cam {
                refuse("CHAIN-BROKEN", &format!("stored final camera {} != replay {}", final_cam, want_cam));
            }
            println!("SESSIONWALK verify OK head {} — moves {} edits {}{} (final {})", &r.head[..12], r.moves, r.edits,
                     if r.looks > 0 { format!(" looks {}", r.looks) } else { String::new() }, want_cam);
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
