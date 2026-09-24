// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// workshop/session.rs — WORKSHOP-1: the log is the history, undo is replay, the session is a hash-chained file.
//
// A session is a base authority (a level + tiles) and an ordered log of edits — cell edits (walls and ground)
// and tile edits (textures), the two things the frozen oracle certifies. It is event-sourced (Fowler): the
// current world is not stored mutably; it is REBUILT by replaying the log from the base, so `undo to n` is a
// deterministic replay of the first n edits, never a localised mutation. `apply` is pure (cells, tiles — no
// clock, no I/O, no camera), which is what makes replay deterministic.
//
// Each entry carries two digests, the claim/full split (from the owner's provenance_runtime):
//     content = sha256( W ‖ M )                    the authority STATE after this edit (the claim)
//     full    = sha256( parent.full ‖ content )    the state bound to its whole history (a hash chain)
// so the head digest is the session's integrity in one hash: tampering any entry cascades and moves the head
// (`session verify` replays and catches it). A single-writer hash chain is the right structure here — records
// are ordered from one author and verifiers replay from the base; a Merkle tree only earns its keep for
// O(log n) sampling proofs a session does not need.
//
// THREE STATES (from live_world_kernel): an entry is COMMITTED (in the log), IRREVERSIBLE (something committed
// depends on it — any entry before the head), and the session is DURABLE iff it replays to its head. `propose`
// validates an edit against the head and writes NOTHING (the speculative scratchpad; the committed world stays
// oblivious); `commit` appends it with its digests; a failed propose leaves the log and head unchanged.
//
// BOUNDARY (from the audit-log literature): a hash chain catches tampering UNDER REPLAY; it does not prove
// timing, prove non-membership, or stop someone rewriting entries AND their hashes together — for that the
// committed session is additionally SEALED under RECORD-0's envelope (`verify/seal_session.py`) and anchored by
// git history. NOT in this rung: the skybox (new VIEW semantics) and physics (new CORE semantics) — see the
// ledger's open clause; the studio authors only what Urðr certifies.
//
//     rustc -O workshop/session.rs -o build/session
//     session new    --level B.lvl --tiles B.tiles --out S.json
//     session propose --session S.json --level B.lvl --tiles B.tiles --edit cell:30,25,#   (validate; no write)
//     session commit  --session S.json --level B.lvl --tiles B.tiles --edit tile:floor,96,80,64
//     session undo    --session S.json --level B.lvl --tiles B.tiles --to 1
//     session replay  --session S.json --level B.lvl --tiles B.tiles [--out-level O.lvl --out-tiles O.tiles]
//     session verify  --session S.json --level B.lvl --tiles B.tiles

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::process::exit;

use formats::{level_bytes, parse_level, parse_tiles, tiles_bytes, Level, Tiles, ALPHABET};
use mantle::{hex, sha256, Refusal};

const MAGIC: &[u8] = b"VRDNSES1";

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("SESSION-{}: {}", code, detail);
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
    fn n(&self) -> i64 {
        match self {
            Json::Num(n) => *n,
            _ => -1,
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

// ------------------------------------------------------------------ the authority, the edits, the chain
struct Authority {
    level: Level,
    tiles: Tiles,
}

impl Authority {
    fn w(&self) -> [u8; 32] {
        sha256(&level_bytes(&self.level))
    }
    fn m(&self) -> [u8; 32] {
        sha256(&tiles_bytes(&self.tiles))
    }
    /// content = sha256( W ‖ M ): the authority state after this edit (the claim digest).
    fn content(&self) -> [u8; 32] {
        let mut buf = Vec::with_capacity(64);
        buf.extend_from_slice(&self.w());
        buf.extend_from_slice(&self.m());
        sha256(&buf)
    }
}

fn genesis(base: &Authority) -> [u8; 32] {
    let mut buf = Vec::new();
    buf.extend_from_slice(MAGIC);
    buf.extend_from_slice(&base.content());
    sha256(&buf)
}

fn chain(parent_full: &[u8; 32], content: &[u8; 32]) -> [u8; 32] {
    let mut buf = Vec::with_capacity(64);
    buf.extend_from_slice(parent_full);
    buf.extend_from_slice(content);
    sha256(&buf)
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

fn edit_json(e: &Edit) -> Json {
    match e {
        Edit::Cell { x, z, to } => obj(vec![
            ("op", Json::Str("cell".into())),
            ("x", Json::Num(*x as i64)),
            ("z", Json::Num(*z as i64)),
            ("to", Json::Str((*to as char).to_string())),
        ]),
        Edit::Tile { class, rgb } => obj(vec![
            ("op", Json::Str("tile".into())),
            ("class", Json::Str(class.clone())),
            ("rgb", Json::Arr(rgb.iter().map(|c| Json::Num(*c as i64)).collect())),
        ]),
    }
}

fn edit_from_json(v: &Json) -> Result<Edit, String> {
    match v.get("op").s() {
        "cell" => {
            let to = v.get("to").s().as_bytes();
            if to.len() != 1 || !ALPHABET.contains(&to[0]) {
                return Err("cell to".into());
            }
            let (x, z) = (v.get("x").n(), v.get("z").n());
            if x < 0 || z < 0 {
                return Err("cell coords".into());
            }
            Ok(Edit::Cell { x: x as usize, z: z as usize, to: to[0] })
        }
        "tile" => {
            let a = v.get("rgb").arr();
            if a.len() != 3 || a.iter().any(|c| c.n() < 0 || c.n() > 255) {
                return Err("tile rgb".into());
            }
            Ok(Edit::Tile { class: v.get("class").s().to_string(), rgb: [a[0].n() as u8, a[1].n() as u8, a[2].n() as u8] })
        }
        other => Err(format!("op {:?}", other)),
    }
}

/// Apply one edit to an authority, validating first. Pure: no camera, no clock, no I/O.
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

// ------------------------------------------------------------------ the session
struct Session {
    base_level: String,
    base_tiles: String,
    base_w: String,
    base_m: String,
    base_full: String,
    log: Vec<Edit>,
    head: String,
}

fn load_session(path: &str) -> Session {
    let root = parse_json(&read(path)).unwrap_or_else(|m| refuse("INVALID-SESSION", &m));
    let d = root.get("data");
    if root.get("name").s() != "verdandi-session" {
        refuse("INVALID-SESSION", "not a verdandi-session");
    }
    let b = d.get("base");
    let log = d.get("log").arr().iter().map(|e| edit_from_json(e.get("edit")).unwrap_or_else(|m| refuse("INVALID-SESSION", &m))).collect();
    Session {
        base_level: b.get("level").s().to_string(),
        base_tiles: b.get("tiles").s().to_string(),
        base_w: b.get("W").s().to_string(),
        base_m: b.get("M").s().to_string(),
        base_full: b.get("full").s().to_string(),
        log,
        head: d.get("head").s().to_string(),
    }
}

struct Replay {
    auth: Authority,
    base_full: [u8; 32],
    head: [u8; 32],
    entries: Vec<([u8; 32], [u8; 32])>, // (content, full) per log entry, in order
}

/// Replay the log from the base files, recomputing every content and full digest. Refuses on an invalid edit
/// (a session should never hold one, so it is a session fault, not an ordinary refusal).
fn do_replay(base_level: &[u8], base_tiles: &[u8], log: &[Edit]) -> Replay {
    let level = parse_level(base_level).unwrap_or_else(|Refusal(m)| refuse("INVALID-BASE", &format!("level: {}", m)));
    let tiles = parse_tiles(base_tiles).unwrap_or_else(|Refusal(m)| refuse("INVALID-BASE", &format!("tiles: {}", m)));
    let mut auth = Authority { level, tiles };
    let base_full = genesis(&auth);
    let mut parent = base_full;
    let mut entries = Vec::with_capacity(log.len());
    for (i, e) in log.iter().enumerate() {
        apply(&mut auth, e).unwrap_or_else(|m| refuse("INVALID-LOG", &format!("entry {}: {}", i + 1, m)));
        let content = auth.content();
        let full = chain(&parent, &content);
        entries.push((content, full));
        parent = full;
    }
    let head = entries.last().map(|(_, f)| *f).unwrap_or(base_full);
    Replay { auth, base_full, head, entries }
}

fn base_of(session: &Session) -> (Vec<u8>, Vec<u8>) {
    let lvl = read(&session.base_level);
    let til = read(&session.base_tiles);
    if hex(&sha256(&lvl)) != session.base_w {
        refuse("BASE-MISMATCH", "the base level file does not hash to the session's base W");
    }
    if hex(&sha256(&til)) != session.base_m {
        refuse("BASE-MISMATCH", "the base tiles file does not hash to the session's base M");
    }
    (lvl, til)
}

fn session_json(session: &Session, entries: &[(String, String)]) -> Json {
    let log: Vec<Json> = session
        .log
        .iter()
        .zip(entries.iter())
        .enumerate()
        .map(|(i, (e, (content, full)))| {
            obj(vec![
                ("seq", Json::Num(i as i64 + 1)),
                ("edit", edit_json(e)),
                ("content", Json::Str(content.clone())),
                ("full", Json::Str(full.clone())),
            ])
        })
        .collect();
    obj(vec![
        ("name", Json::Str("verdandi-session".into())),
        ("version", Json::Num(1)),
        ("data", obj(vec![
            ("base", obj(vec![
                ("level", Json::Str(session.base_level.clone())),
                ("tiles", Json::Str(session.base_tiles.clone())),
                ("W", Json::Str(session.base_w.clone())),
                ("M", Json::Str(session.base_m.clone())),
                ("full", Json::Str(session.base_full.clone())),
            ])),
            ("log", Json::Arr(log)),
            ("head", Json::Str(session.head.clone())),
            ("three_state", obj(vec![
                ("committed", Json::Num(session.log.len() as i64)),
                ("irreversible", Json::Num((session.log.len() as i64 - 1).max(0))),
                ("durable", Json::Bool(true)),
            ])),
        ])),
        ("reading", Json::Str("an event-sourced session: base authority + an ordered cell/tile edit log; content = sha256(W‖M) after an edit, full = sha256(parent.full‖content) — a single-writer hash chain whose head is the session's integrity; undo to n is a deterministic replay of the first n edits; a hash chain catches tampering under replay but is additionally sealed under RECORD-0 and anchored by git".into())),
    ])
}

/// Rebuild `head` and every entry digest by replaying, then write the session file.
fn write_session(path: &str, session: &mut Session) {
    let (lvl, til) = base_of(session);
    let r = do_replay(&lvl, &til, &session.log);
    session.base_full = hex(&r.base_full);
    session.head = hex(&r.head);
    let entries: Vec<(String, String)> = r.entries.iter().map(|(c, f)| (hex(c), hex(f))).collect();
    let mut text = String::new();
    write_json(&session_json(session, &entries), 0, &mut text);
    text.push('\n');
    fs::write(path, text.as_bytes()).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", path, e)));
}

// ------------------------------------------------------------------ commands
struct Args {
    session: Option<String>,
    level: Option<String>,
    tiles: Option<String>,
    edit: Option<String>,
    out: Option<String>,
    to: Option<i64>,
    out_level: Option<String>,
    out_tiles: Option<String>,
}

fn parse_args(args: &[String]) -> Args {
    let mut a = Args { session: None, level: None, tiles: None, edit: None, out: None, to: None, out_level: None, out_tiles: None };
    let mut i = 0;
    while i < args.len() {
        let v = || args.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", args[i])));
        match args[i].as_str() {
            "--session" => a.session = Some(v()),
            "--level" => a.level = Some(v()),
            "--tiles" => a.tiles = Some(v()),
            "--edit" => a.edit = Some(v()),
            "--out" => a.out = Some(v()),
            "--to" => a.to = Some(v().parse().unwrap_or_else(|_| refuse("USAGE", "--to needs a number"))),
            "--out-level" => a.out_level = Some(v()),
            "--out-tiles" => a.out_tiles = Some(v()),
            x => refuse("USAGE", &format!("unknown argument {}", x)),
        }
        i += 2;
    }
    a
}

fn base_digests(level: &[u8], tiles: &[u8]) -> (String, String, String) {
    let auth = Authority {
        level: parse_level(level).unwrap_or_else(|Refusal(m)| refuse("INVALID-BASE", &format!("level: {}", m))),
        tiles: parse_tiles(tiles).unwrap_or_else(|Refusal(m)| refuse("INVALID-BASE", &format!("tiles: {}", m))),
    };
    (hex(&auth.w()), hex(&auth.m()), hex(&genesis(&auth)))
}

fn main() {
    let argv: Vec<String> = env::args().collect();
    if argv.len() < 2 {
        refuse("USAGE", "session new|propose|commit|undo|replay|verify …");
    }
    let a = parse_args(&argv[2..]);
    match argv[1].as_str() {
        "new" => {
            let (lp, tp, out) = (
                a.level.unwrap_or_else(|| refuse("USAGE", "new needs --level")),
                a.tiles.unwrap_or_else(|| refuse("USAGE", "new needs --tiles")),
                a.out.unwrap_or_else(|| refuse("USAGE", "new needs --out")),
            );
            let (lvl, til) = (read(&lp), read(&tp));
            let (w, m, full) = base_digests(&lvl, &til);
            let mut session = Session { base_level: lp, base_tiles: tp, base_w: w, base_m: m, base_full: full.clone(), log: vec![], head: full.clone() };
            write_session(&out, &mut session);
            println!("SESSION new head {} (empty log)", &full[..12]);
        }
        "propose" | "commit" => {
            let sp = a.session.clone().unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let spec = a.edit.unwrap_or_else(|| refuse("USAGE", "needs --edit"));
            let e = parse_edit(&spec).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
            let mut session = load_session(&sp);
            let (lvl, til) = base_of(&session);
            // replay to the head, then validate the new edit against it (the speculative scratchpad)
            let mut r = do_replay(&lvl, &til, &session.log);
            if let Err(m) = apply(&mut r.auth, &e) {
                refuse("INVALID-EDIT", &m); // propose and commit both refuse; the log is untouched either way
            }
            if argv[1] == "propose" {
                let content = r.auth.content();
                let full = chain(&r.head, &content);
                println!("SESSION propose OK would-commit content {} head {} -> {} (nothing written)", &hex(&content)[..12], &session.head[..12], &hex(&full)[..12]);
            } else {
                session.log.push(e);
                write_session(&sp, &mut session);
                let s2 = load_session(&sp);
                println!("SESSION commit head {} log {} entries", &s2.head[..12], s2.log.len());
            }
        }
        "undo" => {
            let sp = a.session.clone().unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let to = a.to.unwrap_or_else(|| refuse("USAGE", "undo needs --to N"));
            let mut session = load_session(&sp);
            if to < 0 || to as usize > session.log.len() {
                refuse("USAGE", &format!("--to {} is outside 0..{}", to, session.log.len()));
            }
            session.log.truncate(to as usize); // undo = replay the first N; write_session recomputes head
            write_session(&sp, &mut session);
            let s2 = load_session(&sp);
            println!("SESSION undo to {} head {} (replayed, not mutated)", to, &s2.head[..12]);
        }
        "replay" => {
            let sp = a.session.unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let session = load_session(&sp);
            let (lvl, til) = base_of(&session);
            let r = do_replay(&lvl, &til, &session.log);
            if hex(&r.head) != session.head {
                refuse("HEAD-MISMATCH", &format!("replay head {} != the session's stored head {}", &hex(&r.head)[..12], &session.head[..12]));
            }
            if let Some(ol) = a.out_level {
                fs::write(&ol, level_bytes(&r.auth.level)).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", ol, e)));
            }
            if let Some(ot) = a.out_tiles {
                fs::write(&ot, tiles_bytes(&r.auth.tiles)).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", ot, e)));
            }
            println!("SESSION replay head {} final W {} M {} ({} edits)", &hex(&r.head)[..12], &hex(&r.auth.w())[..12], &hex(&r.auth.m())[..12], session.log.len());
        }
        "verify" => {
            let sp = a.session.unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let session = load_session(&sp);
            let (lvl, til) = base_of(&session);
            let r = do_replay(&lvl, &til, &session.log);
            // re-parse the file to check each stored per-entry digest against the replay
            let root = parse_json(&read(&sp)).unwrap();
            let stored = root.get("data").get("log").arr();
            for (i, (content, full)) in r.entries.iter().enumerate() {
                if stored[i].get("content").s() != hex(content) || stored[i].get("full").s() != hex(full) {
                    refuse("CHAIN-BROKEN", &format!("entry {}: a stored digest does not match the replay — the log was tampered", i + 1));
                }
            }
            if hex(&r.head) != session.head {
                refuse("CHAIN-BROKEN", "the head does not match the replay");
            }
            if hex(&r.base_full) != session.base_full {
                refuse("CHAIN-BROKEN", "the base genesis does not match");
            }
            let committed = session.log.len();
            let irreversible = committed.saturating_sub(1);
            println!("SESSION verify OK head {} — committed {} irreversible {} durable yes", &session.head[..12], committed, irreversible);
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
