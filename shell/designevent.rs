// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/designevent.rs — DESIGN-EVENT-0: a design admitted as one batch.
//
// `shell design --session S --proposal P` reads the bytes of P, recognizes them as a batch or refuses them, checks the
// batch against this shell, the saved session S and the grant its command line was given, and admits it by ONE
// admission as N ordinary edit events of S's log, sealed as a new session file by LIVE-SESSION-0's journal and seal.
// S is never modified. Either all N are appended, in memory, before anything is written, or the batch is refused and
// nothing exists. Windowless. Nothing here spawns a process, opens a connection or reads the gate.
//
//   the language   VRDNP2, frozen by the registration, beside VRDNP1 (shell/admit.rs, unchanged): 6 + N lines, each
//                  ended by one LF, nothing before the first and nothing after the last —
//                      VRDNP2
//                      renderer=<64 of 0-9a-f>
//                      bearing=<64 of 0-9a-f>
//                      parent=<64 of 0-9a-f>
//                      proposal=<64 of 0-9a-f>
//                      operations=<N>                       "0" or a digit 1-9 and at most three more; 1..4096
//                      open <x>,<z> | close <x>,<z> | paint <class> <colour>          N of these
//                  A coord, a class and a colour are VRDNP1's. A batch is 322 to 74,059 bytes.
//   canonical      a batch denotes a NET CHANGE SET: a set of targets, each with the one value it is to have. So a
//                  target occurs once, and the set has one spelling: the cell operations first, in row-major order (z,
//                  then x, strictly ascending), then the paints in the order of the tile classes, strictly. Each typed
//                  batch has exactly one byte sequence: `emit_batch` writes it and `recognize_batch` accepts nothing
//                  else. The shell reorders, nets and rewrites nothing: canonicalising is the compiler's.
//   the checks     in the registered order, the first that applies: ADMIT-IO, ADMIT-SIZE, ADMIT-PARSE, ADMIT-RANGE,
//                  ADMIT-ORDER (not strictly after the operation before), ADMIT-PREVIEW (--previewed: not the previewed
//                  bytes), ADMIT-PROGRAM, the session loader's own refusals, ADMIT-SESSION, ADMIT-ANCHOR,
//                  ADMIT-DUPLICATE, then each operation in order — ADMIT-CAPABILITY, ADMIT-AUTHORITY, naming its line —
//                  and last ADMIT-PREVIEW (--previewed: not the previewed head).
//   the events     each operation is the edit a key would make, appended by the session's own push — its validation,
//                  its replay, its fold. There is no second fold and no new kind of event: the head after a batch is
//                  the head of N ordinary edits because it is N ordinary edits.
//   the preview    `--dry-run` is this same run, ended after every check has passed and all N are applied in memory:
//                  it prints the binding (language, parent, digest, head, count) and writes nothing.

use std::io::Read;

use crate::admit::{Grant, Op, Unrecognized, COLOUR_MAX, COORD_MAX};
use crate::livesession::{bearing_id, hex64, renderer_id};
use crate::mantle::{hex, sha256};
use crate::playback::{Admit, TILE_CLASSES};
use crate::refusallog::V;

pub const LANGUAGE: &str = "VRDNP2";
pub const MAX_OPERATIONS: usize = 4096;
pub const MIN_BATCH_BYTES: usize = 322;
pub const MAX_BATCH_BYTES: usize = 74_059;

/// A recognized batch: the typed form of exactly one byte sequence.
#[derive(Clone, PartialEq, Debug)]
pub struct Batch {
    pub renderer: String,
    pub bearing: String,
    pub parent: String,
    pub id: String,
    pub ops: Vec<Op>,
}

/// A decimal in canonical form: "0", or a digit 1-9 followed by at most `more` digits.
fn decimal(d: &[u8], more: usize) -> Option<u64> {
    if d.is_empty() || d.len() > more + 1 || !d.iter().all(|c| c.is_ascii_digit()) || (d[0] == b'0' && d.len() > 1) {
        return None;
    }
    Some(d.iter().fold(0u64, |v, c| v * 10 + (*c - b'0') as u64))
}

/// A place or a count as an envelope writes it: a canonical decimal in 1..4096.
pub fn count_text(s: &str) -> Option<u32> {
    decimal(s.as_bytes(), 3).filter(|n| (1..=MAX_OPERATIONS as u64).contains(n)).map(|n| n as u32)
}

/// Where an operation stands in the one order: cells in row-major order, then the classes.
fn rank(op: &Op) -> (u8, u32, u32) {
    match *op {
        Op::Open(x, z) | Op::Close(x, z) => (0, z, x),
        Op::Paint(c, _) => (1, c as u32, 0),
    }
}

/// The recognizer of VRDNP2: the only reader of a batch's bytes. The whole byte sequence is recognized before any
/// integer's domain is looked at, and every domain before the order.
pub fn recognize_batch(b: &[u8]) -> Result<Batch, Unrecognized> {
    if b.len() > MAX_BATCH_BYTES {
        return Err(Unrecognized { code: "ADMIT-SIZE", line: 0, expected: "at most 74059 bytes" });
    }
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
    const FIRST: &str = "the batch language's name, then LF";
    if at(1, FIRST)? != LANGUAGE.as_bytes() {
        return Err(parse(1, FIRST));
    }
    const HEX: [(&[u8], &str); 4] = [
        (b"renderer=", "renderer= and 64 characters of 0-9a-f, then LF"),
        (b"bearing=", "bearing= and 64 characters of 0-9a-f, then LF"),
        (b"parent=", "parent= and 64 characters of 0-9a-f, then LF"),
        (b"proposal=", "proposal= and 64 characters of 0-9a-f, then LF"),
    ];
    let mut ids: Vec<String> = Vec::with_capacity(4);
    for (n, (key, expected)) in HEX.iter().enumerate() {
        let s = at(n + 2, expected)?.strip_prefix(*key).and_then(|r| std::str::from_utf8(r).ok()).filter(|s| hex64(s));
        match s {
            Some(s) => ids.push(s.to_string()),
            None => return Err(parse(n + 2, expected)),
        }
    }
    const COUNT: &str = "operations= and a decimal of at most four digits with no leading zero, then LF";
    let n = at(6, COUNT)?.strip_prefix(b"operations=").and_then(|d| decimal(d, 3)).ok_or(parse(6, COUNT))? as usize;
    let mut range: Option<Unrecognized> = None;
    if n == 0 || n > MAX_OPERATIONS {
        range = Some(Unrecognized { code: "ADMIT-RANGE", line: 6, expected: "a count in 1..4096" });
    }
    const OPERATION: &str = "open X,Z or close X,Z or paint CLASS COLOUR, then LF";
    let mut ops: Vec<Op> = Vec::with_capacity(n.min(MAX_OPERATIONS));
    for k in 7..7 + n {
        let ln = at(k, OPERATION)?;
        let cell = |rest: &[u8]| -> Option<(u64, u64)> {
            let mut parts = rest.split(|c| *c == b',');
            match (parts.next().and_then(|d| decimal(d, 4)), parts.next().and_then(|d| decimal(d, 4)), parts.next()) {
                (Some(x), Some(z), None) => Some((x, z)),
                _ => None,
            }
        };
        let op = if let Some(rest) = ln.strip_prefix(b"open ") {
            let (x, z) = cell(rest).ok_or(parse(k, OPERATION))?;
            if (x > COORD_MAX || z > COORD_MAX) && range.is_none() {
                range = Some(Unrecognized { code: "ADMIT-RANGE", line: k, expected: "each coordinate in 0..65535" });
            }
            Op::Open(x as u32, z as u32)
        } else if let Some(rest) = ln.strip_prefix(b"close ") {
            let (x, z) = cell(rest).ok_or(parse(k, OPERATION))?;
            if (x > COORD_MAX || z > COORD_MAX) && range.is_none() {
                range = Some(Unrecognized { code: "ADMIT-RANGE", line: k, expected: "each coordinate in 0..65535" });
            }
            Op::Close(x as u32, z as u32)
        } else if let Some(rest) = ln.strip_prefix(b"paint ") {
            let mut parts = rest.split(|c| *c == b' ');
            let class = parts.next().and_then(|t| TILE_CLASSES.iter().position(|c| c.as_bytes() == t));
            let colour = parts.next().and_then(|d| decimal(d, 7));
            match (class, colour, parts.next()) {
                (Some(c), Some(v), None) => {
                    if v > COLOUR_MAX && range.is_none() {
                        range = Some(Unrecognized { code: "ADMIT-RANGE", line: k, expected: "a colour in 0..16777215" });
                    }
                    Op::Paint(c as u8, v as u32)
                }
                _ => return Err(parse(k, OPERATION)),
            }
        } else {
            return Err(parse(k, OPERATION));
        };
        ops.push(op);
    }
    if lines.len() > 6 + n || start != b.len() {
        return Err(parse(7 + n, "nothing after the last operation's LF"));
    }
    if let Some(r) = range {
        return Err(r);
    }
    for i in 1..ops.len() {
        if rank(&ops[i - 1]) >= rank(&ops[i]) {
            return Err(Unrecognized { code: "ADMIT-ORDER", line: 7 + i,
                                      expected: "an operation strictly after the one before it: cells in row-major order, then the classes" });
        }
    }
    let id = ids.pop().unwrap_or_default();
    let parent = ids.pop().unwrap_or_default();
    let bearing = ids.pop().unwrap_or_default();
    let renderer = ids.pop().unwrap_or_default();
    Ok(Batch { renderer, bearing, parent, id, ops })
}

/// One operation's line, without its LF.
fn op_line(op: &Op) -> String {
    match *op {
        Op::Open(x, z) => format!("open {},{}", x, z),
        Op::Close(x, z) => format!("close {},{}", x, z),
        Op::Paint(c, v) => format!("paint {} {}", TILE_CLASSES[c as usize], v),
    }
}

/// The one byte sequence of a typed batch (its operations as they stand: the writer does not sort).
pub fn emit_batch(p: &Batch) -> Vec<u8> {
    let mut s = format!("{}\nrenderer={}\nbearing={}\nparent={}\nproposal={}\noperations={}\n", LANGUAGE, p.renderer, p.bearing, p.parent, p.id, p.ops.len());
    for op in &p.ops {
        s.push_str(&op_line(op));
        s.push('\n');
    }
    s.into_bytes()
}

/// The verdict on some bytes, as the court writes it: "R <code> <line>" or "A <typed fields>".
fn verdict(b: &[u8]) -> (String, bool, bool) {
    match recognize_batch(b) {
        Err(u) => (format!("R {} {}", u.code, u.line), false, false),
        Ok(p) => {
            let ops: Vec<String> = p.ops.iter().map(op_line).collect();
            (format!("A {} {} {} {} {}", p.renderer, p.bearing, p.parent, p.id, ops.join(";")), true, emit_batch(&p) != b)
        }
    }
}

/// The court in process: every single-byte substitution, deletion and insertion of `base`, in one fixed order. Each
/// mutant is refused, or is a batch whose emission is the mutant byte for byte. Returns the counts and the sha256 of the
/// verdicts, one per line, for the gate's oracle to reproduce.
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
            if own_ok && !own_bad { "recognized" } else { "NOT-A-BATCH" }, base.len(), if own_ok { String::new() } else { format!(": {}", own) },
            n, refused, recognized, respelled, hex(&sha256(all.as_bytes())))
}

// ------------------------------------------------------------------ the run
fn refuse(code: &'static str, attribution: &'static str, context: Vec<(&'static str, V)>, detail: String) -> i32 {
    let ev = crate::refusallog::Event { operation: "design", surface: "none", reason: code.to_string(), attribution, context };
    crate::refusallog::refuse(&ev, &format!("SHELL-{}: {}", code, detail));
    crate::runledger::end(2);
    2
}

/// At most `MAX_BATCH_BYTES + 1` bytes of the file: enough to tell a batch from a file that is too long.
fn read_capped(path: &str) -> std::io::Result<Vec<u8>> {
    let mut buf = Vec::with_capacity(4096);
    std::fs::File::open(path)?.take(MAX_BATCH_BYTES as u64 + 1).read_to_end(&mut buf)?;
    Ok(buf)
}

/// What the run is asked to do besides admitting: nothing, a dry run, or an admission bound to a preview.
pub struct Mode {
    pub dry_run: bool,
    pub previewed: Option<(String, String)>, // the previewed digest and the previewed head
    pub plant: String,
}

/// The admission of a batch: its bytes, the checks in their registered order, then all N edits applied in memory by
/// the session's own push and sealed as one new session. Returns the exit code (0 admitted and saved, or previewed;
/// 2 refused).
pub fn run(session: &str, proposal: &str, grant: &Grant, mode: &Mode) -> i32 {
    crate::runledger::begin("design", "none");
    let plant = mode.plant.as_str();
    let payload = match read_capped(proposal) {
        Ok(b) => b,
        Err(e) => return refuse("ADMIT-IO", "proposal.read", vec![("path", V::S(proposal.to_string()))], format!("{}: {}", proposal, e)),
    };
    crate::livesession::die(plant, "die-received");
    let digest = hex(&sha256(&payload));
    let size = payload.len();
    let p = match recognize_batch(&payload) {
        Ok(p) => p,
        Err(u) => {
            let detail = if u.code == "ADMIT-SIZE" {
                format!("the batch is more than {} bytes", MAX_BATCH_BYTES)
            } else {
                format!("line {}: expected {}", u.line, u.expected)
            };
            return refuse(u.code, "proposal.recognize", vec![("line", V::N(u.line as u64)), ("expected", V::S(u.expected.to_string()))], detail);
        }
    };
    crate::livesession::die(plant, "die-recognized");
    println!("[design] recognized: batch {} digest {} ({} operations, {} bytes)", &p.id[..12], &digest[..12], p.ops.len(), size);
    if let Some((d, _)) = &mode.previewed {
        if *d != digest {
            return refuse("ADMIT-PREVIEW", "proposal.preview", vec![("previewed", V::S(d.clone())), ("digest", V::S(digest.clone()))],
                          format!("these bytes have digest {} and the preview was of digest {}: not the batch that was previewed", digest, d));
        }
    }
    let (renderer, bearing) = (renderer_id(), bearing_id());
    if p.renderer != renderer || p.bearing != bearing {
        let which = if p.renderer != renderer { "renderer" } else { "bearing" };
        return refuse("ADMIT-PROGRAM", "proposal.anchor", vec![("identity", V::S(which.to_string()))],
                      format!("the batch's {} identity is not this shell's (renderer {}, bearing {})", which, renderer, bearing));
    }
    let mut l = match crate::livesession::load(session) {
        Ok(l) => l,
        Err(r) => return crate::livesession::refuse_run(r, "none"),
    };
    if l.lineage.source != "session" {
        return refuse("ADMIT-SESSION", "proposal.anchor", vec![("path", V::S(session.to_string()))],
                      format!("{} is a journal, not a saved session: a batch is admitted to a sealed session only", session));
    }
    let head = l.session.head().to_string();
    if p.parent != head {
        return refuse("ADMIT-ANCHOR", "proposal.anchor", vec![("parent", V::S(p.parent.clone())), ("head", V::S(head.clone()))],
                      format!("the batch was made against head {} and the session's head is {} — stale; there is no rebase", p.parent, head));
    }
    if l.session.log().iter().any(|e| e.admit.as_ref().map_or(false, |a| a.proposal == p.id)) {
        return refuse("ADMIT-DUPLICATE", "proposal.identity", vec![("proposal", V::S(p.id.clone()))],
                      format!("proposal {} is already in this session's admitted history", p.id));
    }
    if plant == "memo" {
        // PLANT (design-selftest only): from here on, in this process, the memo reuses a digest of edited bytes; see playback::MEMO_PLANT
        crate::playback::MEMO_PLANT.store(true, std::sync::atomic::Ordering::Relaxed);
    }
    // the authority: every operation in order, each checked against the grant and then made by the session's own push
    // on the session as loaded, in memory. The first refusal ends the run, and nothing has been written.
    let count = p.ops.len() as u32;
    for (i, op) in p.ops.iter().enumerate() {
        let line = 7 + i;
        if let Err(why) = grant.permits(*op) {
            return refuse("ADMIT-CAPABILITY", "proposal.grant", vec![("line", V::N(line as u64)), ("grant", V::S(grant.line()))],
                          format!("line {}: {} (grant: {})", line, why, grant.line()));
        }
        let content = l.session.content().to_string();
        l.session.batch_place_next(Admit { language: LANGUAGE.to_string(), proposal: p.id.clone(), digest: digest.clone(), renderer: renderer.clone(),
                                           bearing: bearing.clone(), parent: String::new(), head: String::new(), grant: grant.line() },
                                   i as u32 + 1, count);
        let pushed = match *op {
            Op::Open(x, z) => l.session.push_edit_cell(x as i64, z as i64, b'.').map(|ev| ev.param.clone()).map_err(|(code, m)| format!("{}: {}", code, m)),
            Op::Close(x, z) => l.session.push_edit_cell(x as i64, z as i64, b'#').map(|ev| ev.param.clone()).map_err(|(code, m)| format!("{}: {}", code, m)),
            Op::Paint(c, v) => l.session.push_edit_tile(c, [(v >> 16) as u8, (v >> 8) as u8, v as u8]).map(|ev| ev.param.clone()),
        };
        let spec = match pushed {
            Ok(spec) => spec,
            Err(m) => return refuse("ADMIT-AUTHORITY", "proposal.authority", vec![("line", V::N(line as u64))],
                                    format!("line {}: the session refuses the edit — {}", line, m)),
        };
        if l.session.content() == content {
            return refuse("ADMIT-AUTHORITY", "proposal.authority", vec![("line", V::N(line as u64)), ("edit", V::S(spec.clone()))],
                          format!("line {}: {} leaves W and M as they are: nothing to change", line, spec));
        }
    }
    let reached = l.session.head().to_string();
    if let Some((_, h)) = &mode.previewed {
        if *h != reached {
            return refuse("ADMIT-PREVIEW", "proposal.preview", vec![("previewed", V::S(h.clone())), ("head", V::S(reached.clone()))],
                          format!("the batch reaches head {} and the preview reached {}: not the admission that was previewed", reached, h));
        }
    }
    crate::livesession::die(plant, "die-verified");
    if mode.dry_run {
        // the preview: every check has passed and all N are applied in memory; nothing is written
        println!("[design] preview {} parent={} digest={} head={} operations={}", LANGUAGE, head, digest, reached, count);
        crate::runledger::end(0);
        return 0;
    }
    println!("[design] admitted {} parent={} digest={} head={} operations={} ({})", LANGUAGE, head, digest, reached, count, grant.line());
    crate::livesession::seal_batch(l, plant.to_string(), "none")
}

/// `shell design-selftest --memo S`: the memo against the computation with no memo, over every edit of S.
pub fn memo(session: &str, plant: bool) -> i32 {
    crate::runledger::begin("design", "none");
    match crate::livesession::memo_check(session, plant) {
        Ok((edits, differ)) => {
            // the comparison is reported as data: how many edits were replayed and how many differ. It refuses nothing
            println!("memo edits {} differing {}", edits, differ);
            crate::runledger::end(0);
            0
        }
        Err(r) => crate::livesession::refuse_run(r, "none"),
    }
}
