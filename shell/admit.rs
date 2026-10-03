// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/admit.rs — ADMIT-0: the admission seam.
//
// The gate certifies the machine; ADMIT admits the world's changes. `shell admit --session S --proposal P` reads the
// bytes of P, recognizes them or refuses them, checks the recognized proposal against this shell, the saved session S
// and the grant its command line was given, and admits it as one ordinary edit event of S's log, sealed as a new
// session file by LIVE-SESSION-0's journal and seal. S is never modified. Windowless. One operation per proposal and
// one proposal per run. Nothing here spawns a process, opens a connection or reads the gate.
//
//   the language   VRDNP1, frozen by the registration: exactly eight lines, each ended by one LF, nothing before the
//                  first and nothing after the last —
//                      VRDNP1
//                      renderer=<64 of 0-9a-f>
//                      bearing=<64 of 0-9a-f>
//                      parent=<64 of 0-9a-f>
//                      proposal=<64 of 0-9a-f>
//                      op=open | op=close | op=paint
//                      target=<x>,<z>            (open, close)     target=<wall0|wall1|wall2|wall3|floor>   (paint)
//                      value=0                   (open, close)     value=<colour>                           (paint)
//                  A coord is "0" or a digit 1-9 and at most four more digits, in 0..65535; a colour is "0" or a digit
//                  1-9 and at most seven more, in 0..16777215, read as R*65536 + G*256 + B. No other byte is legal. A
//                  proposal is 327 to 337 bytes and each typed proposal has exactly one byte sequence: `emit` writes
//                  it, and `recognize` accepts nothing else. The digest is the sha256 of the exact bytes.
//   one recognizer `recognize` is the only function that reads a proposal's bytes. The workshop and the sealer never
//                  see the language: they verify the saved session.
//   the checks     in the registered order, the first that applies: ADMIT-IO, ADMIT-SIZE, ADMIT-PARSE (the first line
//                  that is not the language, and what was expected there), ADMIT-RANGE, ADMIT-PROGRAM (the renderer or
//                  the bearing identity is not this shell's), the session loader's own refusals, ADMIT-SESSION (S is a
//                  journal), ADMIT-ANCHOR (the parent is not S's head; both heads are named; there is no rebase),
//                  ADMIT-DUPLICATE (the proposal id is already in S's admitted history), ADMIT-CAPABILITY (outside
//                  the grant), ADMIT-AUTHORITY (the session's own validation of the edit, or nothing to change).
//   the grant      the admitter's, from the command line: the operation kinds, an inclusive rectangle of cells for open
//                  and close, a set of tile classes for paint. What is not granted is refused; with no grant
//                  everything is. A proposal cannot carry one.
//   the event      the edit a key would make (cell:x,z,. / cell:x,z,# / tile:CLASS,R,G,B), appended by the session's own
//                  push — its validation, its replay, its fold — on the session as loaded, in memory, before anything
//                  is written. A refused admission therefore leaves no run directory, no journal and no file.
//
// The envelope (playback::Admit) is written beside the event by shell/livesession.rs.

use std::io::Read;

use crate::livesession::{bearing_id, hex64, renderer_id};
use crate::mantle::{hex, sha256};
use crate::playback::{Admit, TILE_CLASSES};
use crate::refusallog::V;

pub const LANGUAGE: &str = "VRDNP1";
pub const MIN_BYTES: usize = 327;
pub const MAX_BYTES: usize = 337;
pub const COORD_MAX: u64 = 65_535;
pub const COLOUR_MAX: u64 = 16_777_215;
const OPS: [&str; 3] = ["open", "close", "paint"];

/// The one operation of a proposal.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Op {
    Open(u32, u32),
    Close(u32, u32),
    Paint(u8, u32),
}

/// A recognized proposal: the typed form of exactly one byte sequence.
#[derive(Clone, PartialEq, Debug)]
pub struct Proposal {
    pub renderer: String,
    pub bearing: String,
    pub parent: String,
    pub id: String,
    pub op: Op,
}

/// Why bytes are not a proposal: the refusal, the line (1-8, or 9 for what follows the eighth) and what was expected.
#[derive(Clone, PartialEq, Debug)]
pub struct Unrecognized {
    pub code: &'static str,
    pub line: usize,
    pub expected: &'static str,
}

/// A decimal in canonical form: "0", or a digit 1-9 followed by at most `more` digits.
fn canonical(d: &[u8], more: usize) -> Option<u64> {
    if d.is_empty() || d.len() > more + 1 || !d.iter().all(|c| c.is_ascii_digit()) || (d[0] == b'0' && d.len() > 1) {
        return None;
    }
    Some(d.iter().fold(0u64, |v, c| v * 10 + (*c - b'0') as u64))
}

fn hex_line<'a>(line: &'a [u8], key: &[u8]) -> Option<&'a str> {
    let rest = line.strip_prefix(key)?;
    let s = std::str::from_utf8(rest).ok()?;
    if hex64(s) { Some(s) } else { None }
}

/// The recognizer of VRDNP1: the only reader of a proposal's bytes. The whole byte sequence is recognized before any
/// integer's domain is looked at, so a parse refusal on a later line comes before a range refusal on an earlier one.
pub fn recognize(b: &[u8]) -> Result<Proposal, Unrecognized> {
    if b.len() > MAX_BYTES {
        return Err(Unrecognized { code: "ADMIT-SIZE", line: 0, expected: "at most 337 bytes" });
    }
    // the lines: a line is the bytes before one LF; bytes after the last LF are not a line
    let mut lines: Vec<&[u8]> = Vec::new();
    let mut start = 0;
    for (i, c) in b.iter().enumerate() {
        if *c == b'\n' {
            lines.push(&b[start..i]);
            start = i + 1;
        }
    }
    let parse = |line: usize, expected: &'static str| Unrecognized { code: "ADMIT-PARSE", line, expected };
    let at = |k: usize, expected: &'static str| -> Result<&[u8], Unrecognized> { lines.get(k - 1).copied().ok_or(parse(k, expected)) };
    const HEX: [(&[u8], &str); 4] = [
        (b"renderer=", "renderer= and 64 characters of 0-9a-f, then LF"),
        (b"bearing=", "bearing= and 64 characters of 0-9a-f, then LF"),
        (b"parent=", "parent= and 64 characters of 0-9a-f, then LF"),
        (b"proposal=", "proposal= and 64 characters of 0-9a-f, then LF"),
    ];
    if at(1, "VRDNP1, then LF")? != LANGUAGE.as_bytes() {
        return Err(parse(1, "VRDNP1, then LF"));
    }
    let mut ids: Vec<String> = Vec::with_capacity(4);
    for (n, (key, expected)) in HEX.iter().enumerate() {
        match hex_line(at(n + 2, expected)?, key) {
            Some(s) => ids.push(s.to_string()),
            None => return Err(parse(n + 2, expected)),
        }
    }
    const OP: &str = "op=open, op=close or op=paint, then LF";
    let op = match at(6, OP)? {
        b"op=open" => 0,
        b"op=close" => 1,
        b"op=paint" => 2,
        _ => return Err(parse(6, OP)),
    };
    let mut range: Option<Unrecognized> = None;
    let typed = if op < 2 {
        const TARGET: &str = "target= and x,z, each a decimal of at most five digits with no leading zero, then LF";
        const VALUE: &str = "value=0, then LF";
        let t = at(7, TARGET)?.strip_prefix(b"target=").ok_or(parse(7, TARGET))?;
        let mut parts = t.split(|c| *c == b',');
        let (x, z) = match (parts.next().and_then(|d| canonical(d, 4)), parts.next().and_then(|d| canonical(d, 4)), parts.next()) {
            (Some(x), Some(z), None) => (x, z),
            _ => return Err(parse(7, TARGET)),
        };
        if at(8, VALUE)? != b"value=0" {
            return Err(parse(8, VALUE));
        }
        if x > COORD_MAX || z > COORD_MAX {
            range = Some(Unrecognized { code: "ADMIT-RANGE", line: 7, expected: "each coordinate in 0..65535" });
        }
        if op == 0 { Op::Open(x as u32, z as u32) } else { Op::Close(x as u32, z as u32) }
    } else {
        const TARGET: &str = "target= and one of wall0, wall1, wall2, wall3, floor, then LF";
        const VALUE: &str = "value= and a decimal of at most eight digits with no leading zero, then LF";
        let t = at(7, TARGET)?.strip_prefix(b"target=").ok_or(parse(7, TARGET))?;
        let class = TILE_CLASSES.iter().position(|c| c.as_bytes() == t).ok_or(parse(7, TARGET))?;
        let v = at(8, VALUE)?.strip_prefix(b"value=").and_then(|d| canonical(d, 7)).ok_or(parse(8, VALUE))?;
        if v > COLOUR_MAX {
            range = Some(Unrecognized { code: "ADMIT-RANGE", line: 8, expected: "a colour in 0..16777215" });
        }
        Op::Paint(class as u8, v as u32)
    };
    if lines.len() > 8 || start != b.len() {
        return Err(parse(9, "nothing after the eighth line's LF"));
    }
    if let Some(r) = range {
        return Err(r);
    }
    let id = ids.pop().unwrap_or_default();
    let parent = ids.pop().unwrap_or_default();
    let bearing = ids.pop().unwrap_or_default();
    let renderer = ids.pop().unwrap_or_default();
    Ok(Proposal { renderer, bearing, parent, id, op: typed })
}

/// The one byte sequence of a typed proposal.
pub fn emit(p: &Proposal) -> Vec<u8> {
    let (op, target, value) = match p.op {
        Op::Open(x, z) => ("open", format!("{},{}", x, z), 0),
        Op::Close(x, z) => ("close", format!("{},{}", x, z), 0),
        Op::Paint(c, v) => ("paint", TILE_CLASSES[c as usize].to_string(), v),
    };
    format!("{}\nrenderer={}\nbearing={}\nparent={}\nproposal={}\nop={}\ntarget={}\nvalue={}\n", LANGUAGE, p.renderer, p.bearing, p.parent, p.id,
            op, target, value).into_bytes()
}

/// The typed fields of a proposal on one line (the reader court's verdict for a recognized input).
fn fields(p: &Proposal) -> String {
    let (op, a, b) = match p.op {
        Op::Open(x, z) => ("open", x, z),
        Op::Close(x, z) => ("close", x, z),
        Op::Paint(c, v) => ("paint", c as u32, v),
    };
    format!("{} {} {} {} {} {} {}", p.renderer, p.bearing, p.parent, p.id, op, a, b)
}

/// The verdict on some bytes, as the reader court writes it: "R <code> <line>" or "A <typed fields>".
fn verdict(b: &[u8]) -> (String, bool, bool) {
    match recognize(b) {
        Err(u) => (format!("R {} {}", u.code, u.line), false, false),
        Ok(p) => (format!("A {}", fields(&p)), true, emit(&p) != b),
    }
}

/// The reader court, in process: every single-byte substitution, deletion and insertion of `base`, in one fixed order.
/// Each mutant is refused, or is a proposal whose emission is the mutant byte for byte. Returns the counts and the
/// sha256 of the verdicts, one per line, for the gate's oracle to reproduce.
pub fn neighbourhood(base: &[u8]) -> String {
    let (mut n, mut refused, mut recognized, mut respelled) = (0u64, 0u64, 0u64, 0u64);
    let mut all = String::new();
    let mut take = |m: &[u8]| {
        let (v, ok, bad) = verdict(m);
        n += 1;
        if ok { recognized += 1 } else { refused += 1 }
        if bad {
            respelled += 1;
        }
        all.push_str(&v);
        all.push('\n');
    };
    let mut m = base.to_vec();
    for i in 0..base.len() {
        for v in 0..=255u8 {
            if v != base[i] {
                m[i] = v;
                take(&m);
            }
        }
        m[i] = base[i];
    }
    for i in 0..base.len() {
        let mut d = base.to_vec();
        d.remove(i);
        take(&d);
    }
    for i in 0..=base.len() {
        let mut d = base.to_vec();
        d.insert(i, 0);
        for v in 0..=255u8 {
            d[i] = v;
            take(&d);
        }
    }
    let (own, own_ok, own_bad) = verdict(base);
    format!("neighbourhood base {} ({} bytes{}) mutants {} refused {} recognized {} respelled {} verdicts {}",
            if own_ok && !own_bad { "recognized" } else { "NOT-A-PROPOSAL" }, base.len(), if own_ok { String::new() } else { format!(": {}", own) },
            n, refused, recognized, respelled, hex(&sha256(all.as_bytes())))
}

// ------------------------------------------------------------------ the grant
/// What the admitter allows this run to admit.
#[derive(Clone, PartialEq, Debug)]
pub struct Grant {
    pub ops: [bool; 3],
    pub cells: Option<(u64, u64, u64, u64)>,
    pub classes: [bool; 5],
}

/// The grant, from the command line's --allow, --cells and --classes. Each is a comma list in canonical form with no
/// item twice; a missing one grants nothing of its kind.
pub fn grant_of(allow: Option<&str>, cells: Option<&str>, classes: Option<&str>) -> Result<Grant, String> {
    let mut g = Grant { ops: [false; 3], cells: None, classes: [false; 5] };
    if let Some(a) = allow {
        for item in a.split(',') {
            let k = OPS.iter().position(|o| *o == item).ok_or(format!("--allow: {:?} is not one of open, close, paint", item))?;
            if g.ops[k] {
                return Err(format!("--allow names {} twice", item));
            }
            g.ops[k] = true;
        }
    }
    if let Some(c) = cells {
        let v: Vec<Option<u64>> = c.split(',').map(|d| canonical(d.as_bytes(), 4).filter(|n| *n <= COORD_MAX)).collect();
        match v.as_slice() {
            [Some(x0), Some(z0), Some(x1), Some(z1)] if x0 <= x1 && z0 <= z1 => g.cells = Some((*x0, *z0, *x1, *z1)),
            _ => return Err("--cells is x0,z0,x1,z1: four decimals in 0..65535 with x0 <= x1 and z0 <= z1".to_string()),
        }
    }
    if let Some(c) = classes {
        for item in c.split(',') {
            let k = TILE_CLASSES.iter().position(|o| *o == item).ok_or(format!("--classes: {:?} is not a tile class", item))?;
            if g.classes[k] {
                return Err(format!("--classes names {} twice", item));
            }
            g.classes[k] = true;
        }
    }
    Ok(g)
}

impl Grant {
    /// The grant's one line, as the envelope records it.
    pub fn line(&self) -> String {
        let list = |names: &[&str], on: &[bool]| {
            let v: Vec<&str> = names.iter().zip(on.iter()).filter(|(_, b)| **b).map(|(n, _)| *n).collect();
            if v.is_empty() { "-".to_string() } else { v.join(",") }
        };
        format!("allow={} cells={} classes={}", list(&OPS, &self.ops),
                self.cells.map_or("-".to_string(), |(a, b, c, d)| format!("{},{},{},{}", a, b, c, d)), list(&TILE_CLASSES, &self.classes))
    }

    /// Whether the grant covers the operation; if not, what it lacks.
    pub fn permits(&self, op: Op) -> Result<(), String> {
        match op {
            Op::Open(x, z) | Op::Close(x, z) => {
                let (k, name) = if matches!(op, Op::Open(..)) { (0, "open") } else { (1, "close") };
                if !self.ops[k] {
                    return Err(format!("the grant does not allow {}", name));
                }
                match self.cells {
                    Some((x0, z0, x1, z1)) if (x0..=x1).contains(&(x as u64)) && (z0..=z1).contains(&(z as u64)) => Ok(()),
                    Some(_) => Err(format!("cell ({}, {}) is outside the granted rectangle", x, z)),
                    None => Err("the grant names no cells".to_string()),
                }
            }
            Op::Paint(c, _) => {
                if !self.ops[2] {
                    return Err("the grant does not allow paint".to_string());
                }
                if self.classes[c as usize] { Ok(()) } else { Err(format!("the grant does not name the class {}", TILE_CLASSES[c as usize])) }
            }
        }
    }
}

/// Whether text has the alphabet and the length of a grant's line (the loader's check of an envelope's grant).
pub fn grant_text(s: &str) -> bool {
    !s.is_empty() && s.len() <= 96 && s.bytes().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || matches!(c, b'=' | b',' | b'-' | b' '))
}

// ------------------------------------------------------------------ the run
fn refuse(code: &'static str, attribution: &'static str, context: Vec<(&'static str, V)>, detail: String) -> i32 {
    let ev = crate::refusallog::Event { operation: "admit", surface: "none", reason: code.to_string(), attribution, context };
    crate::refusallog::refuse(&ev, &format!("SHELL-{}: {}", code, detail));
    crate::runledger::end(2);
    2
}

/// At most `MAX_BYTES + 1` bytes of the proposal file: enough to tell a proposal from a file that is too long.
fn read_bounded(path: &str) -> std::io::Result<Vec<u8>> {
    let mut buf = Vec::with_capacity(MAX_BYTES + 1);
    std::fs::File::open(path)?.take(MAX_BYTES as u64 + 1).read_to_end(&mut buf)?;
    Ok(buf)
}

/// The admission: the proposal's bytes, the checks in their registered order, then the admitted edit sealed as a new
/// session. Returns the exit code (0 admitted and saved, 2 refused). `plant` names a death point (admit-selftest only).
pub fn run(session: &str, proposal: &str, grant: &Grant, plant: &str) -> i32 {
    crate::runledger::begin("admit", "none");
    let bytes = match read_bounded(proposal) {
        Ok(b) => b,
        Err(e) => return refuse("ADMIT-IO", "proposal.read", vec![("path", V::S(proposal.to_string()))], format!("{}: {}", proposal, e)),
    };
    crate::livesession::die(plant, "die-received");
    let p = match recognize(&bytes) {
        Ok(p) => p,
        Err(u) => {
            let detail = if u.code == "ADMIT-SIZE" {
                format!("the proposal is more than {} bytes", MAX_BYTES)
            } else {
                format!("line {}: expected {}", u.line, u.expected)
            };
            return refuse(u.code, "proposal.recognize", vec![("line", V::N(u.line as u64)), ("expected", V::S(u.expected.to_string()))], detail);
        }
    };
    let digest = hex(&sha256(&bytes));
    crate::livesession::die(plant, "die-recognized");
    println!("[admit] recognized: proposal {} digest {} ({} bytes)", &p.id[..12], &digest[..12], bytes.len());
    let (renderer, bearing) = (renderer_id(), bearing_id());
    if p.renderer != renderer || p.bearing != bearing {
        let which = if p.renderer != renderer { "renderer" } else { "bearing" };
        return refuse("ADMIT-PROGRAM", "proposal.anchor", vec![("identity", V::S(which.to_string()))],
                      format!("the proposal's {} identity is not this shell's (renderer {}, bearing {})", which, renderer, bearing));
    }
    let mut l = match crate::livesession::load(session) {
        Ok(l) => l,
        Err(r) => return crate::livesession::refuse_run(r, "none"),
    };
    if l.lineage.source != "session" {
        return refuse("ADMIT-SESSION", "proposal.anchor", vec![("path", V::S(session.to_string()))],
                      format!("{} is a journal, not a saved session: a proposal is admitted to a sealed session only", session));
    }
    let head = l.session.head().to_string();
    if p.parent != head {
        return refuse("ADMIT-ANCHOR", "proposal.anchor", vec![("parent", V::S(p.parent.clone())), ("head", V::S(head.clone()))],
                      format!("the proposal was made against head {} and the session's head is {} — stale; there is no rebase", p.parent, head));
    }
    if l.session.log().iter().any(|e| e.admit.as_ref().map_or(false, |a| a.proposal == p.id)) {
        return refuse("ADMIT-DUPLICATE", "proposal.identity", vec![("proposal", V::S(p.id.clone()))],
                      format!("proposal {} is already in this session's admitted history", p.id));
    }
    if let Err(why) = grant.permits(p.op) {
        return refuse("ADMIT-CAPABILITY", "proposal.grant", vec![("grant", V::S(grant.line()))], format!("{} (grant: {})", why, grant.line()));
    }
    // the authority: the session's own validation and replay of the edit, on the session as loaded, in memory
    let content = l.session.content().to_string();
    l.session.admit_next(Admit { language: LANGUAGE.to_string(), proposal: p.id.clone(), digest: digest.clone(), renderer, bearing,
                                 parent: String::new(), head: String::new(), grant: grant.line() });
    let pushed = match p.op {
        Op::Open(x, z) => l.session.push_edit_cell(x as i64, z as i64, b'.').map(|ev| ev.param.clone()).map_err(|(code, m)| format!("{}: {}", code, m)),
        Op::Close(x, z) => l.session.push_edit_cell(x as i64, z as i64, b'#').map(|ev| ev.param.clone()).map_err(|(code, m)| format!("{}: {}", code, m)),
        Op::Paint(c, v) => l.session.push_edit_tile(c, [(v >> 16) as u8, (v >> 8) as u8, v as u8]).map(|ev| ev.param.clone()),
    };
    let spec = match pushed {
        Ok(spec) => spec,
        Err(m) => return refuse("ADMIT-AUTHORITY", "proposal.authority", vec![], format!("the session refuses the edit — {}", m)),
    };
    if l.session.content() == content {
        return refuse("ADMIT-AUTHORITY", "proposal.authority", vec![("edit", V::S(spec.clone()))],
                      format!("{} leaves W and M as they are: nothing to change", spec));
    }
    crate::livesession::die(plant, "die-verified");
    println!("[admit] admitted: {} — head {} -> {} ({})", spec, &head[..12], &l.session.head()[..12], grant.line());
    crate::livesession::go_admitted(l, plant.to_string(), "none")
}

/// `shell admit-anchor`: lines 1 to 4 of a proposal anchored to a saved session, on standard output. It reads only.
pub fn anchor(session: &str) -> i32 {
    crate::runledger::begin("admit", "none");
    let l = match crate::livesession::load(session) {
        Ok(l) => l,
        Err(r) => return crate::livesession::refuse_run(r, "none"),
    };
    if l.lineage.source != "session" {
        return refuse("ADMIT-SESSION", "proposal.anchor", vec![("path", V::S(session.to_string()))],
                      format!("{} is a journal, not a saved session: a proposal is admitted to a sealed session only", session));
    }
    print!("{}\nrenderer={}\nbearing={}\nparent={}\n", LANGUAGE, renderer_id(), bearing_id(), l.session.head());
    crate::runledger::end(0);
    0
}
