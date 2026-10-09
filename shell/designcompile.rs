// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/designcompile.rs — DESIGN-IR/DIFF-0: a design compiled to its change set.
//
// `shell design-compile --session S --design D` reads the bytes of D and the saved session S and writes, to standard
// output and nowhere else, the one canonical batch for the net difference between S's world and the world D's
// statements describe; or it refuses, with a code and the design's line, and writes nothing there. It admits nothing:
// the batch goes to `shell design`, which takes a batch and never a design. Windowless. Nothing here spawns a process,
// opens a connection, reads a clock or writes a file.
//
//   the source language   VERDANDI-DESIGN 0, pinned at the byte by the registration. At most 16,384 bytes. The lines
//                         are the bytes between LFs; a CR directly before an LF is not part of the line; bytes after
//                         the last LF are a last line. Line 1, with spaces and tabs at either end dropped, is the
//                         version. In a later line what follows the first '#' is a comment and may hold any byte; with
//                         the comment and the blanks at either end dropped, a line is empty or one statement — words
//                         of printable ASCII separated by spaces or tabs:
//                             open CELL | open CELL CELL | close CELL | close CELL CELL | room CELL CELL
//                             entrance CELL | paint CLASS R,G,B
//                         A CELL is X,Z, decimals with no leading zero and at most five digits, inside the level. Two
//                         cells are a rectangle's corners in either order. A room is at least three cells each way.
//                         At least one statement and at most 64.
//   the meaning           the statements are applied in order to a copy of the parent's world: open writes floor to
//                         its rectangle, close rock, room rock to the rim and floor to the inside, entrance floor to
//                         its cell, paint one colour to a class; a later statement writes over an earlier one. What
//                         results is the design's target. The change set is the net difference between the parent's
//                         world and the target, in the batch language's own order: cells row-major, then the classes.
//   the refusal boundary  COMPILE-IO; COMPILE-SIZE (bytes); the loader's own; COMPILE-SESSION; then the lines in order
//                         — COMPILE-PARSE, COMPILE-RANGE, COMPILE-SIZE (a 65th statement), each at its line; then the
//                         statements in order, each cell as it is written — COMPILE-BORDER (floor written to a border
//                         cell), COMPILE-STAIR (a stair written to), at the statement's line; then COMPILE-CAMERA (the
//                         target leaves the camera's cell closed); COMPILE-SIZE (more than 4,096 operations);
//                         COMPILE-EMPTY (nothing changes). Part of a design is never emitted, a statement is never
//                         skipped and a rectangle is never clipped.
//   the id                the lower-case hexadecimal SHA-256 of the design's bytes exactly as they were read.
//   the selftest          `design-compile-selftest` is the same run with one planted defect, or the court in process:
//                         the verdict on every single-byte substitution, deletion and insertion of a design. The first
//                         eleven plants are DESIGN-IR/DIFF-0's; the three after them are HERMENEUTICS-0's (named in
//                         HERMENEUTICS-0a), each planted alike in the gate's reference, so that a byte comparison of
//                         the two programs cannot see it.

use std::io::{Read, Write};

use crate::admit::Op;
use crate::designevent::{emit_batch, Batch, MAX_OPERATIONS};
use crate::livesession::{bearing_id, renderer_id};
use crate::mantle::{hex, sha256};
use crate::playback::{LiveSession, TILE_CLASSES};
use crate::refusallog::V;

pub const VERSION: &[u8] = b"VERDANDI-DESIGN 0";
pub const MAX_DESIGN_BYTES: usize = 16_384;
pub const MAX_STATEMENTS: usize = 64;

/// The plants `design-compile-selftest` takes. `design-compile` takes none. DESIGN-IR/DIFF-0's eleven, then
/// HERMENEUTICS-0's three (HERMENEUTICS-0a).
pub const PLANTS: [&str; 14] = ["entrance-dropped", "order-reversed", "rect-short", "paint-next-class", "first-wins", "net-stale",
                                "stair-skipped", "border-clipped", "camera-buried", "id-stripped", "net-short",
                                "rim-keeps-openings", "corners-one-order", "writes-as-operations"];

#[derive(Clone, Copy, PartialEq)]
enum Verb {
    Open,
    Close,
    Room,
    Entrance,
}

enum Statement {
    // `low_first`: the rectangle's first corner, as written, is its low corner on both axes
    Cells { verb: Verb, x0: usize, z0: usize, x1: usize, z1: usize, line: usize, low_first: bool },
    Paint { class: usize, rgb: [u8; 3] },
}

/// A refusal of the compiler: its registered code and the design's line it names (0 where it names none).
pub struct Refused {
    pub code: &'static str,
    pub line: usize,
}

/// A world as the compiler reads it: the level's cells, each class's one colour where it wholly has one, and the
/// camera's cell.
pub struct World {
    w: usize,
    rows: usize,
    cells: Vec<u8>,
    tiles: [Option<[u8; 3]>; 5],
    cam: (usize, usize),
}

/// The session's world, read through the session's own read-only views. The level's size is found by asking for
/// cells until there is none: the session answers `None` outside the level.
fn world_of(s: &LiveSession) -> World {
    let (mut w, mut rows) = (0usize, 0usize);
    while s.cell(w as i64, 0).is_some() {
        w += 1;
    }
    while s.cell(0, rows as i64).is_some() {
        rows += 1;
    }
    let mut cells = Vec::with_capacity(w * rows);
    for z in 0..rows {
        for x in 0..w {
            cells.push(s.cell(x as i64, z as i64).unwrap_or(b'#'));
        }
    }
    let mut tiles = [None; 5];
    for (c, t) in tiles.iter_mut().enumerate() {
        *t = s.tile_rgb(c as u8);
    }
    let cam = s.camera();
    World { w, rows, cells, tiles, cam: (cam.x.max(0) as usize, cam.z.max(0) as usize) }
}

/// The lines of a design: the bytes between LFs, a CR directly before an LF dropped; bytes after the last LF are a
/// last line, and a design that ends in LF has no line after it.
fn lines_of(d: &[u8]) -> Vec<&[u8]> {
    let mut out = Vec::new();
    let mut start = 0;
    for (i, &c) in d.iter().enumerate() {
        if c == b'\n' {
            let ln = &d[start..i];
            out.push(if ln.last() == Some(&b'\r') { &ln[..ln.len() - 1] } else { ln });
            start = i + 1;
        }
    }
    if start < d.len() {
        out.push(&d[start..]);
    }
    out
}

/// A byte string with the spaces and tabs at either end dropped.
fn trim(b: &[u8]) -> &[u8] {
    let blank = |c: &u8| *c == b' ' || *c == b'\t';
    let a = b.iter().position(|c| !blank(c)).unwrap_or(b.len());
    let z = b.iter().rposition(|c| !blank(c)).map_or(a, |i| i + 1);
    &b[a..z]
}

/// A decimal in canonical form: "0", or a digit 1-9 followed by at most `more` digits.
fn decimal(d: &[u8], more: usize) -> Option<u32> {
    if d.is_empty() || d.len() > more + 1 || !d.iter().all(|c| c.is_ascii_digit()) || (d[0] == b'0' && d.len() > 1) {
        return None;
    }
    Some(d.iter().fold(0u32, |n, c| n * 10 + (c - b'0') as u32))
}

/// A cell word: X,Z, each a canonical decimal of at most five digits.
fn cell_word(tok: &[u8]) -> Option<(u32, u32)> {
    let comma = tok.iter().position(|c| *c == b',')?;
    Some((decimal(&tok[..comma], 4)?, decimal(&tok[comma + 1..], 4)?))
}

/// A colour word: R,G,B, each a canonical decimal of at most three digits, at most 255.
fn colour_word(tok: &[u8]) -> Option<[u8; 3]> {
    let parts: Vec<&[u8]> = tok.split(|c| *c == b',').collect();
    if parts.len() != 3 {
        return None;
    }
    let mut rgb = [0u8; 3];
    for (k, p) in parts.iter().enumerate() {
        let v = decimal(p, 2)?;
        if v > 255 {
            return None;
        }
        rgb[k] = v as u8;
    }
    Some(rgb)
}

/// The design's statements, typed, or the first line that is not the language.
fn statements(design: &[u8], w: usize, rows: usize) -> Result<Vec<Statement>, Refused> {
    if design.len() > MAX_DESIGN_BYTES {
        return Err(Refused { code: "COMPILE-SIZE", line: 0 });
    }
    let lines = lines_of(design);
    if lines.is_empty() || trim(lines[0]) != VERSION {
        return Err(Refused { code: "COMPILE-PARSE", line: 1 });
    }
    let mut out = Vec::new();
    for (k, raw) in lines.iter().enumerate().skip(1) {
        let n = k + 1;
        let parse = Refused { code: "COMPILE-PARSE", line: n };
        let code = match raw.iter().position(|c| *c == b'#') {
            Some(i) => &raw[..i],
            None => raw,
        };
        let ln = trim(code);
        if ln.is_empty() {
            continue;
        }
        if ln.iter().any(|c| !(*c == b' ' || *c == b'\t' || (33..=126).contains(c))) {
            return Err(parse);
        }
        let t: Vec<&[u8]> = ln.split(|c| *c == b' ' || *c == b'\t').filter(|x| !x.is_empty()).collect();
        let point = |tok: &[u8]| -> Result<(usize, usize), Refused> {
            let (x, z) = cell_word(tok).ok_or(Refused { code: "COMPILE-PARSE", line: n })?;
            if x as usize >= w || z as usize >= rows {
                return Err(Refused { code: "COMPILE-RANGE", line: n });
            }
            Ok((x as usize, z as usize))
        };
        let verb = match t[0] {
            b"open" => Some(Verb::Open),
            b"close" => Some(Verb::Close),
            b"room" => Some(Verb::Room),
            b"entrance" => Some(Verb::Entrance),
            _ => None,
        };
        match verb {
            Some(Verb::Entrance) => {
                if t.len() != 2 {
                    return Err(parse);
                }
                let (x, z) = point(t[1])?;
                out.push(Statement::Cells { verb: Verb::Entrance, x0: x, z0: z, x1: x, z1: z, line: n, low_first: true });
            }
            Some(v) => {
                if !(t.len() == 2 || t.len() == 3) || (v == Verb::Room && t.len() != 3) {
                    return Err(parse);
                }
                let a = point(t[1])?;
                let b = if t.len() == 3 { point(t[2])? } else { a };
                let (x0, x1, z0, z1) = (a.0.min(b.0), a.0.max(b.0), a.1.min(b.1), a.1.max(b.1));
                if v == Verb::Room && (x1 - x0 < 2 || z1 - z0 < 2) {
                    return Err(Refused { code: "COMPILE-RANGE", line: n });
                }
                out.push(Statement::Cells { verb: v, x0, z0, x1, z1, line: n, low_first: a.0 <= b.0 && a.1 <= b.1 });
            }
            None if t[0] == b"paint" => {
                let class = if t.len() == 3 { TILE_CLASSES.iter().position(|c| c.as_bytes() == t[1]) } else { None };
                let rgb = if t.len() == 3 { colour_word(t[2]) } else { None };
                match (class, rgb) {
                    (Some(class), Some(rgb)) => out.push(Statement::Paint { class, rgb }),
                    _ => return Err(parse),
                }
            }
            None => return Err(parse),
        }
        if out.len() > MAX_STATEMENTS {
            return Err(Refused { code: "COMPILE-SIZE", line: n });
        }
    }
    if out.is_empty() {
        return Err(Refused { code: "COMPILE-PARSE", line: lines.len() });
    }
    Ok(out)
}

/// The world the statements describe: each applied in order to a copy of the parent's. A PLANT (design-compile-selftest
/// only) changes one thing here.
fn target(stmts: &[Statement], world: &World, plant: &str) -> Result<(Vec<u8>, [Option<[u8; 3]>; 5]), Refused> {
    let (w, rows) = (world.w, world.rows);
    let mut cells = world.cells.clone();
    let mut tiles = world.tiles;
    let mut written = vec![false; cells.len()];
    let order: Vec<&Statement> = if plant == "order-reversed" { stmts.iter().rev().collect() } else { stmts.iter().collect() };
    for s in order {
        match *s {
            Statement::Paint { class, rgb } => {
                let c = if plant == "paint-next-class" { (class + 1) % 5 } else { class };
                tiles[c] = Some(rgb);
            }
            Statement::Cells { verb, x0, z0, x1, z1, line, low_first } => {
                if plant == "entrance-dropped" && verb == Verb::Entrance {
                    continue;
                }
                // PLANT corners-one-order: a rectangle read from its first corner to its second, so that one written
                // with a high corner first names no cell
                if plant == "corners-one-order" && !low_first {
                    continue;
                }
                let xe = if plant == "rect-short" && x1 > x0 { x1 - 1 } else { x1 };
                for z in z0..=z1 {
                    for x in x0..=xe {
                        let i = z * w + x;
                        let rim = verb == Verb::Room && (x == x0 || x == x1 || z == z0 || z == z1);
                        // PLANT rim-keeps-openings: a rim cell that is floor stays floor
                        let keep = plant == "rim-keeps-openings" && rim && cells[i] == b'.';
                        let to = if verb == Verb::Close || (rim && !keep) { b'#' } else { b'.' };
                        if (x == 0 || z == 0 || x == w - 1 || z == rows - 1) && to != b'#' {
                            if plant == "border-clipped" {
                                continue;
                            }
                            return Err(Refused { code: "COMPILE-BORDER", line });
                        }
                        if cells[i] == b'<' || cells[i] == b'>' {
                            if plant == "stair-skipped" {
                                continue;
                            }
                            return Err(Refused { code: "COMPILE-STAIR", line });
                        }
                        if plant == "first-wins" && written[i] {
                            continue;
                        }
                        written[i] = true;
                        cells[i] = to;
                    }
                }
            }
        }
    }
    Ok((cells, tiles))
}

/// The design's change set against the parent's world, in the batch language's one order, or the refusal.
fn compile(design: &[u8], world: &World, base: Option<&World>, plant: &str) -> Result<Vec<Op>, Refused> {
    let stmts = statements(design, world.w, world.rows)?;
    let (cells, tiles) = target(&stmts, world, plant)?;
    // PLANT net-stale: the net is taken against the base world and not the parent's
    let against = match base {
        Some(b) if plant == "net-stale" => b,
        _ => world,
    };
    // PLANT writes-as-operations: every cell a statement names and every class painted is written as an operation,
    // whether it changes or not
    let writes = plant == "writes-as-operations";
    let named = |i: usize| -> bool {
        let (x, z) = (i % world.w, i / world.w);
        stmts.iter().any(|s| match *s {
            Statement::Cells { x0, z0, x1, z1, .. } => x0 <= x && x <= x1 && z0 <= z && z <= z1,
            Statement::Paint { .. } => false,
        })
    };
    let painted = |c: usize| -> bool { stmts.iter().any(|s| matches!(*s, Statement::Paint { class, .. } if class == c)) };
    let mut ops = Vec::new();
    for (i, &c) in cells.iter().enumerate() {
        if c != against.cells[i] || (writes && named(i)) {
            let (x, z) = ((i % world.w) as u32, (i / world.w) as u32);
            ops.push(if c == b'#' { Op::Close(x, z) } else { Op::Open(x, z) });
        }
    }
    for c in 0..5 {
        if tiles[c] != against.tiles[c] || (writes && painted(c)) {
            if let Some(rgb) = tiles[c] {
                ops.push(Op::Paint(c as u8, rgb[0] as u32 * 65536 + rgb[1] as u32 * 256 + rgb[2] as u32));
            }
        }
    }
    let cam = cells[world.cam.1 * world.w + world.cam.0];
    if plant != "camera-buried" && !(cam == b'.' || cam == b'<' || cam == b'>') {
        return Err(Refused { code: "COMPILE-CAMERA", line: 0 });
    }
    if plant == "net-short" {
        // PLANT: the net leaves out its last operation
        ops.pop();
    }
    if ops.len() > MAX_OPERATIONS {
        return Err(Refused { code: "COMPILE-SIZE", line: 0 });
    }
    if ops.is_empty() {
        return Err(Refused { code: "COMPILE-EMPTY", line: 0 });
    }
    Ok(ops)
}

/// The design's id: the SHA-256 of its bytes exactly as they were read.
fn design_id(design: &[u8], plant: &str) -> String {
    if plant == "id-stripped" {
        // PLANT: the id of the design with its comments and blanks removed
        let mut stripped = Vec::new();
        for raw in lines_of(design) {
            let code = match raw.iter().position(|c| *c == b'#') {
                Some(i) => &raw[..i],
                None => raw,
            };
            stripped.extend_from_slice(trim(code));
            stripped.push(b'\n');
        }
        return hex(&sha256(&stripped));
    }
    hex(&sha256(design))
}

/// The batch's bytes for a compiled change set: this shell's two identities, the parent's head, the design's id.
fn batch_of(design: &[u8], head: &str, ops: Vec<Op>, plant: &str) -> Vec<u8> {
    emit_batch(&Batch { renderer: renderer_id(), bearing: bearing_id(), parent: head.to_string(), id: design_id(design, plant), ops })
}

fn refuse(code: &'static str, attribution: &'static str, context: Vec<(&'static str, V)>, detail: String) -> i32 {
    let ev = crate::refusallog::Event { operation: "design-compile", surface: "none", reason: code.to_string(), attribution, context };
    crate::refusallog::refuse(&ev, &format!("SHELL-{}: {}", code, detail));
    crate::runledger::end(2);
    2
}

/// What a refusal says of itself, after its code.
fn detail_of(r: &Refused) -> String {
    let what = match r.code {
        "COMPILE-PARSE" => "the line is not the design language",
        "COMPILE-RANGE" => "a cell outside the level, or a room smaller than three cells each way",
        "COMPILE-BORDER" => "the statement writes floor to a cell on the level's border, which stays rock",
        "COMPILE-STAIR" => "the statement writes to a stair cell, which the batch language cannot say",
        "COMPILE-CAMERA" => "the design leaves the camera's cell closed",
        "COMPILE-EMPTY" => "the design changes nothing: the world is already so, and a batch says at least one operation",
        _ if r.line > 0 => "a statement after the 64th",
        _ => "the design is over a bound of the language",
    };
    if r.line > 0 { format!("line {}: {}", r.line, what) } else { what.to_string() }
}

/// At most `MAX_DESIGN_BYTES + 1` bytes of the file: enough to tell a design from a file that is too long.
fn read_design(path: &str) -> std::io::Result<Vec<u8>> {
    let mut buf = Vec::with_capacity(1024);
    std::fs::File::open(path)?.take(MAX_DESIGN_BYTES as u64 + 1).read_to_end(&mut buf)?;
    Ok(buf)
}

/// `shell design-compile` (plant "") and the planted runs of its selftest.
pub fn run(session: &str, design: &str, plant: &str) -> i32 {
    crate::runledger::begin("design-compile", "none");
    let text = match read_design(design) {
        Ok(b) => b,
        Err(e) => return refuse("COMPILE-IO", "design.read", vec![("path", V::S(design.to_string()))], format!("{}: {}", design, e)),
    };
    if text.len() > MAX_DESIGN_BYTES {
        return refuse("COMPILE-SIZE", "design.size", vec![("line", V::N(0))], format!("the design is more than {} bytes", MAX_DESIGN_BYTES));
    }
    let l = match crate::livesession::load(session) {
        Ok(l) => l,
        Err(r) => return crate::livesession::refuse_run(r, "none"),
    };
    if l.lineage.source != "session" {
        return refuse("COMPILE-SESSION", "design.anchor", vec![("path", V::S(session.to_string()))],
                      format!("{} is a journal, not a saved session: a design is compiled against a sealed session only", session));
    }
    let world = world_of(&l.session);
    let base = if plant == "net-stale" { l.session.rebased().ok().map(|b| world_of(&b)) } else { None };
    match compile(&text, &world, base.as_ref(), plant) {
        Err(r) => {
            let detail = detail_of(&r);
            refuse(r.code, "design.compile", vec![("line", V::N(r.line as u64))], detail)
        }
        Ok(ops) => {
            let out = batch_of(&text, l.session.head(), ops, plant);
            let mut stdout = std::io::stdout();
            let wrote = stdout.write_all(&out).and_then(|_| stdout.flush());
            let code = if wrote.is_ok() { 0 } else { 1 };
            crate::runledger::end(code);
            code
        }
    }
}

/// The court in process: the verdict on every single-byte insertion, substitution and deletion of a design, against
/// one session's world — a refusal with its code and line, or the digest of the batch the mutant compiles to. One
/// line a mutant, in a fixed order: at each position the 256 insertions, then the 255 substitutions, then the deletion.
pub fn court(session: &str, design: &str) -> i32 {
    crate::runledger::begin("design-compile", "none");
    let text = match read_design(design) {
        Ok(b) => b,
        Err(e) => return refuse("COMPILE-IO", "design.read", vec![("path", V::S(design.to_string()))], format!("{}: {}", design, e)),
    };
    let l = match crate::livesession::load(session) {
        Ok(l) => l,
        Err(r) => return crate::livesession::refuse_run(r, "none"),
    };
    let world = world_of(&l.session);
    let head = l.session.head().to_string();
    let verdict = |m: &[u8]| -> String {
        match compile(m, &world, None, "") {
            Err(r) => format!("R {} {}", r.code, r.line),
            Ok(ops) => format!("B {}", hex(&sha256(&batch_of(m, &head, ops, "")))),
        }
    };
    let mut out = String::new();
    let n = text.len();
    for i in 0..=n {
        for b in 0..=255u8 {
            let mut m = Vec::with_capacity(n + 1);
            m.extend_from_slice(&text[..i]);
            m.push(b);
            m.extend_from_slice(&text[i..]);
            out.push_str(&verdict(&m));
            out.push('\n');
        }
        if i < n {
            for b in 0..=255u8 {
                if b != text[i] {
                    let mut m = text.clone();
                    m[i] = b;
                    out.push_str(&verdict(&m));
                    out.push('\n');
                }
            }
            let mut m = Vec::with_capacity(n - 1);
            m.extend_from_slice(&text[..i]);
            m.extend_from_slice(&text[i + 1..]);
            out.push_str(&verdict(&m));
            out.push('\n');
        }
    }
    print!("{}", out);
    crate::runledger::end(0);
    0
}
