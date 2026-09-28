// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/livesession.rs — LIVE-SESSION-0: the live session made durable and recoverable, without a second authority.
//
// LIVE-INPUT-0's loop runs unchanged over a playback::LiveSession. This module adds what makes the session outlive the
// run, and nothing else:
//
//   the journal   build/sessions/<run_id>/journal.vsj (VERDANDI_SESSIONS overrides the root): append-only, one text
//                 record per line, "R <length> <sha256> <payload>", a header record and then one record per appended
//                 event, each flushed to the disk before it is counted as journaled. A torn final record is dropped on
//                 load; any other bad record refuses.
//   the seal      on Esc (or a closed window) the session is written in the workshop's session-walk format to a
//                 temporary file, flushed, and moved over build/sessions/<run_id>/session.json atomically
//                 (MoveFileEx with MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH on Windows; a rename and a
//                 directory flush elsewhere). Its live block names the run, the renderer identity, the lineage, the
//                 journal, how the session ended and the keyboard-focus observation; its seal is the sha256 of the
//                 file's bytes before the seal. The saved file is then read back from the disk and verified — the
//                 seal, then a replay to every witness, camera, content and head of the live session — and only then
//                 is the run counted as saved (exit 0). A seal that cannot be written or does not verify refuses.
//   the loader    --resume reads a saved session or a crashed run's journal and goes: integrity (the seal or the
//                 records, the base files' W and M, the chain's own fold, the lineage), the renderer identity, the
//                 replay, the witnesses, the classification — LOAD, LOAD with a different renderer, TAMPERED, or
//                 DIFFERENT-RENDERER. An identity mismatch alone never means corruption, and a divergence no renderer
//                 can explain (an edit's content, a move's camera) is TAMPERED under any identity. The continuation is
//                 sealed as a new file whose log begins with the parent's events; the parent is never modified.
//
// The session stays the authority: its W and M change only by the replay of appended events (playback.rs), and the
// saved file is what the workshop's sessionwalk verifies. No clock is taken. The focus observation is recorded, never
// read by a rule.

use std::cell::RefCell;
use std::fs;
use std::io::Write;
use std::rc::Rc;

use crate::formats::{facing_letter, parse_camera, Camera};
use crate::liveinput::{Keys, ScriptedKeys};
use crate::mantle::{hex, sha256};
use crate::playback::{chain_heads, content_of, parse_view, EventSink, JsonView, LiveEvent, LiveSession};
use crate::presentexact::ExactSurface;
use crate::refusallog::{esc, V};

pub const LOG: &str = "LIVE-SESSION-0";
pub const ENV: &str = "VERDANDI_SESSIONS";
pub const DEFAULT_ROOT: &str = "build/sessions";
pub const JOURNAL: &str = "journal.vsj";
pub const SESSION: &str = "session.json";
pub const JOURNAL_MAGIC: &str = "VRDNLJ1";
pub const SEAL_KEY: &str = "\n \"seal\": \"";
pub const CRASH_AFTER: u64 = 5; // the crash plant tears the record of the event after the fifth

/// The rendering sources the shell was built from, in a fixed order: the renderer identity's inputs.
const RENDER_SOURCES: [(&str, &[u8]); 5] = [
    ("kernel/mantle.rs", include_bytes!("../kernel/mantle.rs")),
    ("kernel/formats.rs", include_bytes!("../kernel/formats.rs")),
    ("kernel/fast.rs", include_bytes!("../kernel/fast.rs")),
    ("kernel/hud.rs", include_bytes!("../kernel/hud.rs")),
    ("shell/present.rs", include_bytes!("present.rs")),
];

/// The renderer identity: the sha256 of "<path> <sha256 of the source>\n" for each rendering source in order, each
/// source's line endings taken as the repository stores them (LF), so a CRLF checkout names the same renderer.
pub fn renderer_id() -> String {
    let mut s = String::new();
    for (name, bytes) in RENDER_SOURCES.iter() {
        let lf: Vec<u8> = normalize(bytes);
        s.push_str(&format!("{} {}\n", name, hex(&sha256(&lf))));
    }
    hex(&sha256(s.as_bytes()))
}

fn normalize(b: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(b.len());
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'\r' && i + 1 < b.len() && b[i + 1] == b'\n' {
            i += 1;
            continue;
        }
        out.push(b[i]);
        i += 1;
    }
    out
}

fn cam_token(c: Camera) -> String {
    format!("{},{},{}", c.x, c.z, facing_letter(c.facing))
}

/// The sessions root: $VERDANDI_SESSIONS, else build/sessions under the working directory.
pub fn root() -> String {
    std::env::var(ENV).ok().filter(|v| !v.is_empty()).unwrap_or_else(|| DEFAULT_ROOT.to_string())
}

// ------------------------------------------------------------------ refusals
/// A LIVE-SESSION-0 refusal as data, logged where it is emitted.
pub struct Refusal {
    pub attribution: &'static str,
    pub context: Vec<(&'static str, V)>,
    pub message: String,
}

fn refusal(attribution: &'static str, context: Vec<(&'static str, V)>, message: String) -> Refusal {
    Refusal { attribution, context, message }
}

fn refuse_run(r: Refusal, surface: &'static str) -> i32 {
    let reason = crate::refusallog::code_of(&r.message);
    let ev = crate::refusallog::Event { operation: "livesession", surface, reason, attribution: r.attribution, context: r.context };
    crate::refusallog::refuse(&ev, &format!("SHELL-{}", r.message));
    crate::runledger::end(2);
    2
}

// ------------------------------------------------------------------ the base and the lineage
#[derive(Clone)]
pub struct Base {
    pub level: String,
    pub tiles: String,
    pub w: String,
    pub m: String,
    pub content: String,
    pub camera: Camera,
}

#[derive(Clone)]
pub struct Lineage {
    pub parent_head: String,
    pub parent_events: usize,
    pub source: &'static str, // "session" | "journal"
    pub parent_sha256: String,
    pub torn: usize,
}

fn base_json(b: &Base) -> String {
    format!("{{\"level\":{},\"tiles\":{},\"W\":{},\"M\":{},\"content\":{},\"camera\":{}}}",
            esc(&b.level), esc(&b.tiles), esc(&b.w), esc(&b.m), esc(&b.content), esc(&cam_token(b.camera)))
}

fn lineage_json(l: &Option<Lineage>) -> String {
    match l {
        None => "null".to_string(),
        Some(l) => format!("{{\"parent_head\":{},\"parent_events\":{},\"source\":{},\"parent_sha256\":{},\"torn\":{}}}",
                           esc(&l.parent_head), l.parent_events, esc(l.source), esc(&l.parent_sha256), l.torn),
    }
}

// ------------------------------------------------------------------ the journal
/// One journal record: the payload's length and sha256, then the payload, on one line.
pub fn record_line(payload: &str) -> String {
    format!("R {} {} {}\n", payload.len(), hex(&sha256(payload.as_bytes())), payload)
}

fn event_payload(k: usize, ev: &LiveEvent) -> String {
    let (kind, pk) = if ev.tag == b'M' { ("move", "command") } else { ("edit", "spec") };
    format!("{{\"k\":{},\"kind\":\"{}\",\"{}\":{},\"camera\":{},\"witness\":{},\"content\":{},\"head\":{}}}",
            k, kind, pk, esc(&ev.param), esc(&cam_token(ev.camera)), esc(&ev.witness), esc(&ev.content), esc(&ev.head))
}

/// The append-only journal. A record is counted only after its bytes were flushed to the disk.
pub struct Journal {
    file: fs::File,
    pub path: String,
    pub records: u64,
    pub events: u64,
    pub broken: Option<String>,
    crash: bool,
    surface: &'static str,
}

impl Journal {
    fn open(path: &str, crash: bool, surface: &'static str) -> Result<Journal, String> {
        let file = fs::OpenOptions::new().create_new(true).append(true).open(path).map_err(|e| format!("{}: {}", path, e))?;
        Ok(Journal { file, path: path.to_string(), records: 0, events: 0, broken: None, crash, surface })
    }

    /// Append one record and flush it; only then count it.
    fn put(&mut self, payload: &str) -> Result<(), String> {
        let line = record_line(payload);
        self.file.write_all(line.as_bytes()).map_err(|e| e.to_string())?;
        self.file.sync_data().map_err(|e| e.to_string())?;
        self.records += 1;
        Ok(())
    }

    fn put_event(&mut self, k: usize, ev: &LiveEvent) {
        if self.broken.is_some() {
            return;
        }
        if self.crash && self.events == CRASH_AFTER {
            // PLANT crash: the next record is torn half-way and the process dies before sealing (no ledger line)
            let line = record_line(&event_payload(k, ev));
            let _ = self.file.write_all(&line.as_bytes()[..line.len() / 2]);
            let _ = self.file.sync_data();
            eprintln!("SHELL-LIVESESSION-PLANT-CRASH: the process dies after {} journaled events ({})", self.events, self.path);
            std::process::exit(70);
        }
        match self.put(&event_payload(k, ev)) {
            Ok(()) => self.events += 1,
            Err(m) => {
                // the journal failed: said once, logged once; the session goes on in memory, and only a verified seal
                // can make it durable
                println!("[livesession] JOURNAL FAILED at event {}: {} — the session goes on in memory; only the seal can save it", k, m);
                crate::refusallog::record(&crate::refusallog::Event {
                    operation: "livesession", surface: self.surface, reason: "LIVESESSION-JOURNAL-UNWRITTEN".to_string(),
                    attribution: "session.journal", context: vec![("event", V::N(k as u64))] });
                self.broken = Some(m);
            }
        }
    }
}

struct JournalSink(Rc<RefCell<Journal>>);

impl EventSink for JournalSink {
    fn appended(&mut self, index: usize, ev: &LiveEvent) {
        self.0.borrow_mut().put_event(index, ev);
    }
}

// ------------------------------------------------------------------ reading a journal
struct JournalRead {
    header: JsonView,
    events: Vec<JsonView>,
    torn: usize,
}

fn read_journal(bytes: &[u8]) -> Result<JournalRead, Refusal> {
    let corrupt = |n: usize, why: &str| refusal("session.load", vec![("record", V::N(n as u64))],
                                                format!("LIVESESSION-JOURNAL-CORRUPT: record {} {}", n, why));
    let mut lines: Vec<&[u8]> = Vec::new();
    let mut start = 0;
    for (i, b) in bytes.iter().enumerate() {
        if *b == b'\n' {
            lines.push(&bytes[start..=i]);
            start = i + 1;
        }
    }
    if start < bytes.len() {
        lines.push(&bytes[start..]);
    }
    let mut payloads: Vec<&[u8]> = Vec::new();
    let mut torn = 0;
    for (n, ln) in lines.iter().enumerate() {
        let last = n + 1 == lines.len();
        let parsed = parse_record(ln);
        match parsed {
            Some(p) => payloads.push(p),
            None if last => torn = 1,
            None => return Err(corrupt(n, "is not a complete record whose length and checksum agree")),
        }
    }
    if payloads.is_empty() {
        return Err(corrupt(0, "is missing: the journal has no header"));
    }
    let header = parse_view(payloads[0]).map_err(|m| corrupt(0, &m))?;
    if header.get("journal").s() != JOURNAL_MAGIC {
        return Err(corrupt(0, "is not a LIVE-SESSION-0 journal header"));
    }
    let mut events = Vec::new();
    for (i, p) in payloads[1..].iter().enumerate() {
        let v = parse_view(p).map_err(|m| corrupt(i + 1, &m))?;
        if v.get("k").num() != Some(i as i64) {
            return Err(corrupt(i + 1, "is out of sequence"));
        }
        events.push(v);
    }
    Ok(JournalRead { header, events, torn })
}

/// One record line -> its payload, if its length and sha256 agree and the line is complete.
fn parse_record(ln: &[u8]) -> Option<&[u8]> {
    let body = ln.strip_suffix(b"\n")?;
    let s = std::str::from_utf8(body).ok()?;
    let mut parts = s.splitn(4, ' ');
    if parts.next()? != "R" {
        return None;
    }
    let len: usize = parts.next()?.parse().ok()?;
    let sum = parts.next()?;
    let payload = parts.next()?;
    if payload.len() != len || hex(&sha256(payload.as_bytes())) != sum {
        return None;
    }
    let off = body.len() - payload.len();
    Some(&body[off..])
}

// ------------------------------------------------------------------ the seal
/// The seal of a saved file's text: the sha256 of every byte before the seal line's key.
pub fn seal_of(prefix: &[u8]) -> String {
    hex(&sha256(prefix))
}

/// Check a saved file's seal; return the bytes it covers.
fn check_seal(bytes: &[u8]) -> Result<(), Refusal> {
    let text = std::str::from_utf8(bytes).map_err(|_| refusal("session.load", vec![], "LIVESESSION-CORRUPT: the saved session is not UTF-8".to_string()))?;
    let i = text.rfind(SEAL_KEY).ok_or_else(|| refusal("session.load", vec![], "LIVESESSION-CORRUPT: the saved session has no seal".to_string()))?;
    let prefix = &bytes[..i + 1];
    let rest = &text[i + SEAL_KEY.len()..];
    let got = rest.split('"').next().unwrap_or("");
    if got != seal_of(prefix) || rest[got.len()..] != *"\"\n}\n" {
        return Err(refusal("session.load", vec![], "LIVESESSION-CORRUPT: the saved session's seal does not match its bytes".to_string()));
    }
    Ok(())
}

fn event_item(ev: &LiveEvent) -> String {
    if ev.tag == b'M' {
        format!("{{\"kind\": \"move\", \"command\": {}, \"camera\": {}, \"witness\": {}}}", esc(&ev.param), esc(&cam_token(ev.camera)), esc(&ev.witness))
    } else {
        format!("{{\"kind\": \"edit\", \"spec\": {}, \"witness\": {}}}", esc(&ev.param), esc(&ev.witness))
    }
}

/// The saved session's text, in the workshop's session-walk format with the live block, then the seal.
fn saved_text(s: &LiveSession, base: &Base, live: &str) -> String {
    let log = s.log();
    let moves = log.iter().filter(|e| e.tag == b'M').count();
    let items: Vec<String> = log.iter().map(|e| format!("   {}", event_item(e))).collect();
    let prefix = format!(
        "{{\n \"name\": \"verdandi-session-walk\",\n \"data\": {{\n  \"magic\": \"VRDNSW1\",\n  \"base\": {},\n  \"log\": [{}{}{}],\n  \"head\": {},\n  \"final_camera\": {},\n  \"final_content\": {},\n  \"moves\": {},\n  \"edits\": {}\n }},\n \"live\": {},\n",
        base_json(base), if items.is_empty() { "" } else { "\n" }, items.join(",\n"), if items.is_empty() { "" } else { "\n  " },
        esc(s.head()), esc(&cam_token(s.camera())), esc(s.content()), moves, log.len() - moves, live);
    format!("{} \"seal\": \"{}\"\n}}\n", prefix, seal_of(prefix.as_bytes()))
}

#[cfg(target_os = "windows")]
mod replace {
    #[link(name = "kernel32")]
    extern "system" {
        fn MoveFileExW(existing: *const u16, new: *const u16, flags: u32) -> i32;
    }
    const MOVEFILE_REPLACE_EXISTING: u32 = 0x1;
    const MOVEFILE_WRITE_THROUGH: u32 = 0x8;

    /// Move the flushed temporary file over the destination in one step, written through to the disk.
    pub fn atomic_replace(tmp: &str, dst: &str) -> Result<(), String> {
        let t: Vec<u16> = tmp.encode_utf16().chain(Some(0)).collect();
        let d: Vec<u16> = dst.encode_utf16().chain(Some(0)).collect();
        let ok = unsafe { MoveFileExW(t.as_ptr(), d.as_ptr(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) };
        if ok != 0 { Ok(()) } else { Err(format!("MoveFileExW: {}", std::io::Error::last_os_error())) }
    }
}

#[cfg(not(target_os = "windows"))]
mod replace {
    /// Rename the flushed temporary file over the destination, then flush the directory that holds it.
    pub fn atomic_replace(tmp: &str, dst: &str) -> Result<(), String> {
        std::fs::rename(tmp, dst).map_err(|e| format!("rename: {}", e))?;
        let dir = std::path::Path::new(dst).parent().map(|p| p.to_path_buf()).unwrap_or_else(|| std::path::PathBuf::from("."));
        std::fs::File::open(&dir).and_then(|d| d.sync_all()).map_err(|e| format!("directory flush: {}", e))
    }
}

/// Write the saved session: the temporary file, flushed, then moved over the destination atomically.
fn write_saved(dst: &str, text: &str, plant: &str) -> Result<(), String> {
    if plant == "seal-unwritable" {
        return Err("PLANT seal-unwritable: the file system refused the temporary file".to_string());
    }
    let tmp = format!("{}.tmp", dst);
    {
        let mut f = fs::OpenOptions::new().create_new(true).write(true).open(&tmp).map_err(|e| format!("{}: {}", tmp, e))?;
        f.write_all(text.as_bytes()).map_err(|e| e.to_string())?;
        f.sync_all().map_err(|e| e.to_string())?;
    }
    replace::atomic_replace(&tmp, dst)?;
    if plant == "seal-flip" {
        // PLANT seal-flip: one byte of the saved file changes between its write and its verification
        let mut b = fs::read(dst).map_err(|e| e.to_string())?;
        if let Some(i) = text.find("\"witness\": \"").map(|i| i + 12) {
            b[i] = if b[i] == b'0' { b'1' } else { b'0' };
        }
        fs::write(dst, b).map_err(|e| e.to_string())?;
    }
    Ok(())
}

// ------------------------------------------------------------------ loading and classifying
/// A loaded, replayed and classified session, at its final state.
pub struct Loaded {
    pub session: LiveSession,
    pub base: Base,
    pub lineage: Lineage,
    pub classification: &'static str, // "LOAD" | "LOAD-DIFFERENT-RENDERER"
    pub parent_renderer: String,
}

struct SavedEvent {
    tag: u8,
    param: String,
    camera: String,
    witness: String,
}

fn read_base(v: &JsonView, level: &str, tiles: &str) -> Result<(Base, Vec<u8>, Vec<u8>), Refusal> {
    let camera = parse_camera(&v.get("camera").s())
        .map_err(|crate::mantle::Refusal(m)| refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: the base camera: {}", m)))?;
    let lv = fs::read(level).map_err(|e| refusal("session.load", vec![("level", V::S(level.to_string()))], format!("LIVESESSION-BASE: {}: {}", level, e)))?;
    let tl = fs::read(tiles).map_err(|e| refusal("session.load", vec![("tiles", V::S(tiles.to_string()))], format!("LIVESESSION-BASE: {}: {}", tiles, e)))?;
    let base = Base { level: level.to_string(), tiles: tiles.to_string(), w: v.get("W").s(), m: v.get("M").s(), content: v.get("content").s(), camera };
    if hex(&sha256(&lv)) != base.w || hex(&sha256(&tl)) != base.m || content_of(&lv, &tl) != base.content {
        return Err(refusal("session.load", vec![("level", V::S(base.level.clone()))],
                           "LIVESESSION-BASE: the base files are not the W and M the session was made over".to_string()));
    }
    Ok((base, lv, tl))
}

/// Load a saved session (or a crashed run's journal): integrity, identity, replay, witnesses, classification.
pub fn load(path: &str) -> Result<Loaded, Refusal> {
    let bytes = fs::read(path).map_err(|e| refusal("session.load", vec![("path", V::S(path.to_string()))], format!("LIVESESSION-UNREADABLE: {}: {}", path, e)))?;
    let file_sha = hex(&sha256(&bytes));
    let is_journal = bytes.starts_with(b"R ");
    // 1. integrity: the seal or the records, the base, the chain's own fold, the lineage
    let (base, lv, tl, events, stored_head, stored_final, parent_renderer, torn, heads_given) = if is_journal {
        let j = read_journal(&bytes)?;
        let h = &j.header;
        let (base, lv, tl) = read_base(&h.get("base"), &h.get("base").get("level").s(), &h.get("base").get("tiles").s())?;
        let mut evs = Vec::new();
        let mut heads = Vec::new();
        for e in &j.events {
            evs.push(saved_event(e)?);
            heads.push(e.get("head").s());
        }
        let last = heads.last().cloned();
        (base, lv, tl, evs, last, None, h.get("renderer").s(), j.torn, Some(heads))
    } else {
        check_seal(&bytes)?;
        let root = parse_view(&bytes).map_err(|m| refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: {}", m)))?;
        let d = root.get("data");
        if root.get("name").s() != "verdandi-session-walk" || d.get("magic").s() != "VRDNSW1" {
            return Err(refusal("session.load", vec![], "LIVESESSION-CORRUPT: not a session-walk".to_string()));
        }
        let (base, lv, tl) = read_base(&d.get("base"), &d.get("base").get("level").s(), &d.get("base").get("tiles").s())?;
        let mut evs = Vec::new();
        for e in d.get("log").arr() {
            evs.push(saved_event(&e)?);
        }
        let fin = (d.get("final_camera").s(), d.get("final_content").s());
        (base, lv, tl, evs, Some(d.get("head").s()), Some(fin), root.get("live").get("renderer").s(), 0, None)
    };
    let pairs: Vec<(u8, String)> = events.iter().map(|e| (e.tag, e.witness.clone())).collect();
    let heads = chain_heads(&base.content, base.camera, &pairs);
    let folded = heads.last().cloned().unwrap_or_default();
    if let Some(h) = &stored_head {
        if *h != folded {
            return Err(refusal("session.load", vec![], "LIVESESSION-CORRUPT: the stored head is not the fold of the stored witnesses".to_string()));
        }
    }
    if let Some(hs) = &heads_given {
        if hs.iter().zip(heads[1..].iter()).any(|(a, b)| a != b) {
            return Err(refusal("session.load", vec![], "LIVESESSION-JOURNAL-CORRUPT: a record's head is not the fold of the witnesses before it".to_string()));
        }
    }
    if !is_journal {
        let root = parse_view(&bytes).map_err(|m| refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: {}", m)))?;
        let l = root.get("live").get("lineage");
        if !l.is_null() {
            let n = l.get("parent_events").num().unwrap_or(-1);
            if n < 0 || n as usize > events.len() || heads[n as usize] != l.get("parent_head").s() {
                return Err(refusal("session.load", vec![], "LIVESESSION-LINEAGE: the named parent head is not on this session's own chain".to_string()));
            }
        }
    }
    // 2. the renderer identity
    let same = parent_renderer == renderer_id();
    // 3. the replay, 4. the witnesses
    let mut s = LiveSession::new(lv, tl, base.camera).map_err(|m| refusal("session.load", vec![], format!("LIVESESSION-BASE: {}", m)))?;
    for (k, e) in events.iter().enumerate() {
        let (frame, camera_ok, witness_ok) = if e.tag == b'M' {
            match s.push_move(e.param.as_bytes()[0]) {
                Ok(ev) => (true, cam_token(ev.camera) == e.camera, ev.witness == e.witness),
                Err(_) => (false, false, false),
            }
        } else {
            match (cell_of(&e.param), tile_of(&e.param)) {
                (Some((x, z, to)), _) => match s.push_edit_cell(x, z, to) {
                    Ok(ev) => (false, true, ev.witness == e.witness),
                    Err(_) => (false, false, false),
                },
                // LIVE-AUTHOR-0: a tile edit replays as a cell edit does, through the session
                (None, Some((class, rgb))) => match s.push_edit_tile(class, rgb) {
                    Ok(ev) => (false, true, ev.witness == e.witness),
                    Err(_) => (false, false, false),
                },
                (None, None) => return Err(refusal("session.load", vec![("event", V::N(k as u64))],
                                                   format!("LIVESESSION-UNSUPPORTED: event {} is {:?}, neither a cell nor a tile edit", k, e.param))),
            }
        };
        if !(camera_ok && witness_ok) {
            // 5. classify: only a frame witness can be the renderer's; a camera or a content is not
            let renderable = frame && camera_ok;
            let (code, why) = if renderable && !same {
                ("LIVESESSION-DIFFERENT-RENDERER", "a frame witness does not reproduce under a different renderer")
            } else if renderable {
                ("LIVESESSION-TAMPERED", "a frame witness does not reproduce under the same renderer")
            } else {
                ("LIVESESSION-TAMPERED", "a witness no renderer can explain (a camera or a content) does not reproduce")
            };
            return Err(refusal("session.replay", vec![("event", V::N(k as u64)), ("same_renderer", V::N(same as u64))],
                               format!("{}: event {}: {}", code, k, why)));
        }
    }
    if let Some((cam, content)) = &stored_final {
        if cam_token(s.camera()) != *cam || s.content() != content {
            return Err(refusal("session.replay", vec![], "LIVESESSION-TAMPERED: the stored final camera or content is not the replay's".to_string()));
        }
    }
    let lineage = Lineage { parent_head: s.head().to_string(), parent_events: events.len(), source: if is_journal { "journal" } else { "session" },
                            parent_sha256: file_sha, torn };
    Ok(Loaded { session: s, base, lineage, classification: if same { "LOAD" } else { "LOAD-DIFFERENT-RENDERER" }, parent_renderer })
}

fn saved_event(e: &JsonView) -> Result<SavedEvent, Refusal> {
    let (tag, param) = match e.get("kind").s().as_str() {
        "move" => (b'M', e.get("command").s()),
        "edit" => (b'E', e.get("spec").s()),
        k => return Err(refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: event kind {:?}", k))),
    };
    if tag == b'M' && !matches!(param.as_str(), "L" | "R" | "F" | "B" | "Q" | "E") {
        return Err(refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: move {:?}", param)));
    }
    Ok(SavedEvent { tag, param, camera: e.get("camera").s(), witness: e.get("witness").s() })
}

fn tile_of(spec: &str) -> Option<(u8, [u8; 3])> {
    let rest = spec.strip_prefix("tile:")?;
    let p: Vec<&str> = rest.split(',').collect();
    if p.len() != 4 {
        return None;
    }
    let class = crate::playback::TILE_CLASSES.iter().position(|c| *c == p[0])? as u8;
    Some((class, [p[1].parse().ok()?, p[2].parse().ok()?, p[3].parse().ok()?]))
}

fn cell_of(spec: &str) -> Option<(i64, i64, u8)> {
    let rest = spec.strip_prefix("cell:")?;
    let p: Vec<&str> = rest.split(',').collect();
    if p.len() != 3 || p[2].len() != 1 {
        return None;
    }
    Some((p[0].parse().ok()?, p[1].parse().ok()?, p[2].as_bytes()[0]))
}

// ------------------------------------------------------------------ the run
/// The keyboard-focus observation of a surface, as a JSON object. Recorded, never ruled on.
pub trait Focus {
    fn focus(&self) -> String;
}

impl<S> Focus for ScriptedKeys<S> {
    fn focus(&self) -> String {
        "{\"source\":\"mock\"}".to_string()
    }
}

/// What a run starts from, as its command line gave it.
pub struct Plan {
    pub level: String,
    pub tiles: String,
    pub cam0: Camera,
    pub resume: Option<String>,
    pub plant: String,
    pub surface: &'static str,
}

/// A run made ready: the ledger begun, the session (new or loaded), the journal open with every event so far.
pub struct Prepared {
    session: LiveSession,
    base: Base,
    lineage: Option<Lineage>,
    resumed: Option<(&'static str, String)>,
    journal: Rc<RefCell<Journal>>,
    dir: String,
    plant: String,
    surface: &'static str,
}

/// Begin the run: the ledger, the session, the journal. A refusal ends the ledger and gives the exit code.
pub fn prepare(plan: Plan) -> Result<Prepared, i32> {
    crate::runledger::begin("livesession", plan.surface); // RUN-LEDGER-0: the live-session run begins
    let surface = plan.surface;
    let (session, base, lineage, resumed) = match &plan.resume {
        Some(p) => match load(p) {
            Ok(l) => {
                println!("[livesession] resumed {} ({}): {} events, head {}{}", p, l.classification, l.lineage.parent_events, &l.lineage.parent_head[..12],
                         if l.lineage.torn > 0 { " — a torn final journal record was dropped" } else { "" });
                (l.session, l.base, Some(l.lineage), Some((l.classification, l.parent_renderer)))
            }
            Err(r) => return Err(refuse_run(r, surface)),
        },
        None => {
            let lv = fs::read(&plan.level);
            let tl = fs::read(&plan.tiles);
            let (lv, tl) = match (lv, tl) {
                (Ok(a), Ok(b)) => (a, b),
                _ => return Err(refuse_run(refusal("session.load", vec![], format!("LIVESESSION-BASE: {} or {} cannot be read", plan.level, plan.tiles)), surface)),
            };
            let base = Base { level: plan.level.clone(), tiles: plan.tiles.clone(), w: hex(&sha256(&lv)), m: hex(&sha256(&tl)),
                              content: content_of(&lv, &tl), camera: plan.cam0 };
            match LiveSession::new(lv, tl, plan.cam0) {
                Ok(s) => (s, base, None, None),
                Err(m) => return Err(refuse_run(refusal("session.load", vec![], format!("LIVESESSION-CAMERA: {}", m)), surface)),
            }
        }
    };
    let dir = std::path::Path::new(&root()).join(crate::refusallog::run_id()).to_string_lossy().to_string();
    let jpath = std::path::Path::new(&dir).join(JOURNAL).to_string_lossy().to_string();
    let opened = fs::create_dir_all(&dir).map_err(|e| e.to_string()).and_then(|_| Journal::open(&jpath, plan.plant == "crash", surface));
    let mut journal = match opened {
        Ok(j) => j,
        Err(m) => return Err(refuse_run(refusal("session.journal", vec![], format!("LIVESESSION-JOURNAL-UNWRITTEN: {}", m)), surface)),
    };
    let header = format!("{{\"journal\":\"{}\",\"run_id\":{},\"base\":{},\"renderer\":{},\"lineage\":{}}}",
                         JOURNAL_MAGIC, esc(crate::refusallog::run_id()), base_json(&base), esc(&renderer_id()), lineage_json(&lineage));
    let mut wrote = journal.put(&header);
    for (k, ev) in session.log().iter().enumerate() {
        if wrote.is_ok() {
            wrote = journal.put(&event_payload(k, ev));
            if wrote.is_ok() {
                journal.events += 1;
            }
        }
    }
    if let Err(m) = wrote {
        return Err(refuse_run(refusal("session.journal", vec![], format!("LIVESESSION-JOURNAL-UNWRITTEN: {}", m)), surface));
    }
    let journal = Rc::new(RefCell::new(journal));
    let session = session.with_sink(Box::new(JournalSink(journal.clone())));
    Ok(Prepared { session, base, lineage, resumed, journal, dir, plant: plan.plant, surface })
}

/// The run: LIVE-INPUT-0's loop, then the seal, then the saved file's verification. Returns the exit code.
pub fn go<S: ExactSurface + Keys + Focus>(s: &mut S, p: Prepared) -> i32 {
    go_with(s, p, crate::liveinput::bind).0
}

/// The same run under a given binding (LIVE-AUTHOR-0's live editor); also hands back the loop's counts for the gate.
pub fn go_with<S: ExactSurface + Keys + Focus>(s: &mut S, p: Prepared, binding: fn(u32) -> crate::liveinput::Action) -> (i32, Option<crate::liveinput::Live>) {
    let Prepared { mut session, base, lineage, resumed, journal, dir, plant, surface } = p;
    let live = match crate::liveinput::run_with(s, &mut session, surface, binding) {
        Ok(l) => l,
        Err(r) => {
            // the loop's refusal is LIVE-INPUT-0's (logged as its operation); the journal keeps what was flushed
            let (ev, m) = r.into_event(surface);
            crate::refusallog::refuse(&ev, &format!("SHELL-LIVEINPUT: {}", m));
            crate::runledger::end(2);
            return (2, None);
        }
    };
    for ln in crate::liveinput::summary(&live, &session) {
        println!("{}", ln);
    }
    let (jrecords, jevents, jbroken, jpath) = {
        let j = journal.borrow();
        (j.records, j.events, j.broken.clone(), j.path.clone())
    };
    let jsha = fs::read(&jpath).map(|b| hex(&sha256(&b))).unwrap_or_default();
    let resumed_json = match &resumed {
        None => "null".to_string(),
        Some((c, r)) => format!("{{\"classification\":{},\"parent_renderer\":{}}}", esc(c), esc(r)),
    };
    let live_json = format!(
        "{{\"log\":\"{}\",\"run_id\":{},\"renderer\":{},\"lineage\":{},\"resumed\":{},\"journal\":{{\"file\":\"{}\",\"records\":{},\"events\":{},\"complete\":{},\"sha256\":{}}},\"ended\":{},\"focus\":{}}}",
        LOG, esc(crate::refusallog::run_id()), esc(&renderer_id()), lineage_json(&lineage), resumed_json, JOURNAL, jrecords, jevents,
        jbroken.is_none() && jevents as usize == session.log().len(), esc(&jsha), esc(live.ended), s.focus());
    let text = if plant == "seal-stale" {
        // PLANT seal-stale: a sealed, self-consistent file that is not this live session (its base alone)
        match (fs::read(&base.level), fs::read(&base.tiles)) {
            (Ok(lv), Ok(tl)) => match LiveSession::new(lv, tl, base.camera) {
                Ok(fresh) => saved_text(&fresh, &base, &live_json),
                Err(_) => saved_text(&session, &base, &live_json),
            },
            _ => saved_text(&session, &base, &live_json),
        }
    } else {
        saved_text(&session, &base, &live_json)
    };
    let dst = std::path::Path::new(&dir).join(SESSION).to_string_lossy().to_string();
    if let Err(m) = write_saved(&dst, &text, &plant) {
        return (refuse_run(refusal("session.seal", vec![("path", V::S(dst.clone()))], format!("LIVESESSION-SEAL-UNWRITTEN: {}", m)), surface), None);
    }
    // the saved artifact, read back from the disk, must verify before the run counts as saved
    let verified = fs::read(&dst).map_err(|e| e.to_string()).and_then(|b| {
        if b != text.as_bytes() {
            return Err("the bytes read back are not the bytes written".to_string());
        }
        let l = load(&dst).map_err(|r| r.message)?;
        let (a, b2) = (l.session.log(), session.log());
        if l.session.head() != session.head() || cam_token(l.session.camera()) != cam_token(session.camera()) || l.session.content() != session.content()
            || a.len() != b2.len() || a.iter().zip(b2.iter()).any(|(x, y)| x.witness != y.witness || x.param != y.param) {
            return Err("the replay of the saved file does not reach the live session's state".to_string());
        }
        Ok(())
    });
    if let Err(m) = verified {
        return (refuse_run(refusal("session.seal", vec![("path", V::S(dst.clone()))], format!("LIVESESSION-SEAL-UNVERIFIED: {}", m)), surface), None);
    }
    if let Some(m) = jbroken {
        println!("[livesession] the journal failed during the run ({}); the saved session is complete and verified", m);
    }
    println!("[livesession] saved and verified: {} — {} events, head {}", dst, session.log().len(), session.head());
    crate::runledger::end(0);
    (0, Some(live))
}
