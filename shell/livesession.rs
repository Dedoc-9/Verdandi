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
//
// SIM-TICK-0: the session may hold looks (the heading turned by an integer delta) and tick stamps. The journal and the
// saved file carry them; the loader checks the tick form before anything replays and replays a look through the
// session like a move. The seal is one function, `finish`, shared by the loop's run (go_with) and the windowless tick
// run (go_ticks). Before `finish` writes anything, every frame of the log at a free heading — rendered live, once, by
// the production tread — is recomputed by the reference kernel across threads (`certify`); one difference refuses
// LIVESESSION-UNCERTIFIED and nothing is saved. A session is saved reference-certified or it is not saved. The bearing
// kernels have their own identity (`bearing_id`), recorded beside the renderer's and consulted only for frames at free
// headings, so a walk that never looks is classified exactly as before.
//
// SIM-TICK-0a: a tick session's sensitivity changes are events of kind sensitivity in the journal and the saved file,
// carrying the configuration after them and their tick. They have no witness and fold nothing; the loader replays them
// through the session (one legal transition each), and a crashed run's configuration comes back from them.
//
// ADMIT-0: an admitted edit carries its envelope (playback::Admit) beside it, in its journal record and in its saved
// item. The loader checks an envelope's form, that it sits on an edit, that the heads it names are the chain's own
// around that event and that its proposal id occurs once, before anything replays; a continuation writes it back as it
// read it. A run can be opened from a session already loaded (`go_admitted`), so the seam checks its anchor against
// the very bytes it continues. The seal is still `finish`.

use std::cell::RefCell;
use std::fs;
use std::io::Write;
use std::rc::Rc;

use crate::formats::{facing_letter, parse_camera, Camera};
use crate::liveinput::{Keys, ScriptedKeys};
use crate::mantle::{hex, sha256};
use crate::playback::{chain_heads, content_of, look_fold, parse_view, token, Admit, EventSink, JsonView, LiveEvent, LiveSession};
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

/// SIM-TICK-0: the sources that decide a frame at a free heading, in a fixed order: the vocabulary's code and its
/// carried octant, the reference kernel and the production tread.
const BEARING_SOURCES: [(&str, &[u8]); 4] = [
    ("kernel/vocab.rs", include_bytes!("../kernel/vocab.rs")),
    ("oracle/bearing_octant.txt", include_bytes!("../oracle/bearing_octant.txt")),
    ("kernel/bearing.rs", include_bytes!("../kernel/bearing.rs")),
    ("kernel/bearingfast.rs", include_bytes!("../kernel/bearingfast.rs")),
];

/// SIM-TICK-0: the bearing renderer's identity, formed as the renderer identity is. It is consulted only for frames at
/// free headings: a session that never looks is classified by `renderer_id` alone, as before.
pub fn bearing_id() -> String {
    let mut s = String::new();
    for (name, bytes) in BEARING_SOURCES.iter() {
        s.push_str(&format!("{} {}\n", name, hex(&sha256(&normalize(bytes)))));
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

pub fn refuse_run(r: Refusal, surface: &'static str) -> i32 {
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
    // SIM-TICK-0: a look's parameter is its integer delta; the camera token carries the heading; a tick run's stamp
    // follows the head (an event appended outside time has none, and its record is what it always was)
    if ev.tag == b'S' {
        // SIM-TICK-0a: a sensitivity event carries the configuration after it; it has no witness and its head is the
        // head before it
        let (m, st) = sens_of(&ev.param);
        return format!("{{\"k\":{},\"kind\":\"sensitivity\",\"multiplier\":{},\"step\":{},\"camera\":{},\"witness\":\"\",\"content\":{},\"head\":{}{}}}",
                       k, m, st, esc(&token(ev.camera, ev.yaw)), esc(&ev.content), esc(&ev.head), stamp_json(ev, ""));
    }
    let (kind, pk, pv) = match ev.tag {
        b'M' => ("move", "command", esc(&ev.param)),
        b'K' => ("look", "delta", ev.param.clone()),
        _ => ("edit", "spec", esc(&ev.param)),
    };
    format!("{{\"k\":{},\"kind\":\"{}\",\"{}\":{},\"camera\":{},\"witness\":{},\"content\":{},\"head\":{}{}}}",
            k, kind, pk, pv, esc(&token(ev.camera, ev.yaw)), esc(&ev.witness), esc(&ev.content), esc(&ev.head), stamp_json(ev, "") + &admit_json(ev, ""))
}

/// ADMIT-0: the envelope of an admitted edit as a JSON member (with a leading comma), or nothing. Its members are in
/// one fixed order and every value is text of a narrow alphabet, so the member has one spelling per envelope.
fn admit_json(ev: &LiveEvent, sp: &str) -> String {
    match &ev.admit {
        None => String::new(),
        Some(a) => {
            let m = |k: &str, v: &str| format!("\"{}\":{}{}", k, sp, esc(v));
            format!(",{}\"admit\":{}{{{}}}", sp, sp, [m("language", &a.language), m("proposal", &a.proposal), m("digest", &a.digest),
                    m("renderer", &a.renderer), m("bearing", &a.bearing), m("parent", &a.parent), m("head", &a.head),
                    m("grant", &a.grant)].join(&format!(",{}", sp)))
        }
    }
}

/// ADMIT-0: 64 characters of 0-9 and a-f.
pub fn hex64(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

/// ADMIT-0: a death plant ends the process here, with nothing after it run (admit-selftest only).
pub fn die(plant: &str, point: &str) {
    if plant == point {
        eprintln!("SHELL-ADMIT-PLANT-DEATH: {}", point);
        std::process::exit(70);
    }
}

/// SIM-TICK-0a: a sensitivity event's parameter, "multiplier,step", as its two numbers (zeros if it is not that).
fn sens_of(param: &str) -> (i64, i64) {
    let mut it = param.split(',').map(|v| v.parse::<i64>().unwrap_or(0));
    (it.next().unwrap_or(0), it.next().unwrap_or(0))
}

/// SIM-TICK-0: the tick stamp of an event as JSON members (with a leading comma), or nothing for an untimed event.
fn stamp_json(ev: &LiveEvent, sp: &str) -> String {
    let mut s = String::new();
    if let Some(t) = ev.tick {
        s.push_str(&format!(",{}\"tick\":{}{}", sp, sp, t));
    }
    if let Some((c, m, st)) = ev.input {
        s.push_str(&format!(",{}\"input\":{}{{\"counts\":{}{},{}\"multiplier\":{}{},{}\"step\":{}{}}}", sp, sp, sp, c, sp, sp, m, sp, sp, st));
    }
    s
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
    // ADMIT-0: the death plants of an appended record (1 torn half-way, 2 after its flush); 0 on every real run
    die: u8,
}

impl Journal {
    fn open(path: &str, plant: &str, surface: &'static str) -> Result<Journal, String> {
        let file = fs::OpenOptions::new().create_new(true).append(true).open(path).map_err(|e| format!("{}: {}", path, e))?;
        let die = match plant { "die-torn" => 1, "die-appended" => 2, _ => 0 };
        Ok(Journal { file, path: path.to_string(), records: 0, events: 0, broken: None, crash: plant == "crash", surface, die })
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
        if self.die == 1 {
            // PLANT die-torn (ADMIT-0): the record is torn half-way and the process dies
            let line = record_line(&event_payload(k, ev));
            let _ = self.file.write_all(&line.as_bytes()[..line.len() / 2]);
            let _ = self.file.sync_data();
            die("die-torn", "die-torn");
        }
        match self.put(&event_payload(k, ev)) {
            Ok(()) => {
                self.events += 1;
                if self.die == 2 {
                    die("die-appended", "die-appended"); // PLANT (ADMIT-0): the record is flushed and the process dies
                }
            }
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
    // SIM-TICK-0: a look is {kind, delta, camera, witness}; a tick run's stamp follows the witness
    if ev.tag == b'M' {
        format!("{{\"kind\": \"move\", \"command\": {}, \"camera\": {}, \"witness\": {}{}}}", esc(&ev.param), esc(&token(ev.camera, ev.yaw)), esc(&ev.witness), stamp_json(ev, " "))
    } else if ev.tag == b'K' {
        format!("{{\"kind\": \"look\", \"delta\": {}, \"camera\": {}, \"witness\": {}{}}}", ev.param, esc(&token(ev.camera, ev.yaw)), esc(&ev.witness), stamp_json(ev, " "))
    } else if ev.tag == b'S' {
        // SIM-TICK-0a: a sensitivity event is {kind, multiplier, step} and its tick; it has no witness
        let (m, st) = sens_of(&ev.param);
        format!("{{\"kind\": \"sensitivity\", \"multiplier\": {}, \"step\": {}{}}}", m, st, stamp_json(ev, " "))
    } else {
        format!("{{\"kind\": \"edit\", \"spec\": {}, \"witness\": {}{}{}}}", esc(&ev.param), esc(&ev.witness), stamp_json(ev, " "), admit_json(ev, " "))
    }
}

/// The saved session's text, in the workshop's session-walk format with the live block, then the seal.
fn saved_text(s: &LiveSession, base: &Base, live: &str) -> String {
    let log = s.log();
    let moves = log.iter().filter(|e| e.tag == b'M').count();
    let looks = log.iter().filter(|e| e.tag == b'K').count();
    let settings = log.iter().filter(|e| e.tag == b'S').count();
    let items: Vec<String> = log.iter().map(|e| format!("   {}", event_item(e))).collect();
    // SIM-TICK-0: the looks are counted only when there are some, and the tick block is written only for a session that
    // ran on ticks, so a walk with neither saves the bytes it always did
    let mut more = String::new();
    if looks > 0 {
        more.push_str(&format!(",\n  \"looks\": {}", looks));
    }
    if settings > 0 {
        more.push_str(&format!(",\n  \"sensitivity_changes\": {}", settings));
    }
    if let Some((count, multiplier, step)) = s.ticks() {
        more.push_str(&format!(",\n  \"ticks\": {{\"hz\": {}, \"count\": {}, \"multiplier\": {}, \"step\": {}}}", crate::simtick::TICK_HZ, count, multiplier, step));
    }
    let prefix = format!(
        "{{\n \"name\": \"verdandi-session-walk\",\n \"data\": {{\n  \"magic\": \"VRDNSW1\",\n  \"base\": {},\n  \"log\": [{}{}{}],\n  \"head\": {},\n  \"final_camera\": {},\n  \"final_content\": {},\n  \"moves\": {},\n  \"edits\": {}{}\n }},\n \"live\": {},\n",
        base_json(base), if items.is_empty() { "" } else { "\n" }, items.join(",\n"), if items.is_empty() { "" } else { "\n  " },
        esc(s.head()), esc(&s.token()), esc(s.content()), moves, log.len() - moves - looks - settings, more, live);
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
    die(plant, "die-written"); // PLANT (ADMIT-0): the temporary file is written and flushed, not yet moved
    replace::atomic_replace(&tmp, dst)?;
    die(plant, "die-replaced"); // PLANT (ADMIT-0): the saved file is in place, not yet read back
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
    // SIM-TICK-0: the tick stamp saved beside the event, if a tick run appended it
    tick: Option<u64>,
    input: Option<(i64, i64, i64)>,
    // ADMIT-0: the envelope saved beside an admitted edit
    admit: Option<Admit>,
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
    let parent_bearing: String;
    let mut ticks: Option<(i64, i64, i64, i64)> = None;
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
        parent_bearing = h.get("bearing").s();
        // a journal has no tick block: the count follows its last timed event, and (SIM-TICK-0a) the sensitivity is
        // what its journaled sensitivity events replay to
        if let Some(t) = evs.iter().filter_map(|e| e.tick).last() {
            let (m, st) = evs.iter().filter(|e| e.tag == b'S').map(|e| sens_of(&e.param)).last()
                .unwrap_or((crate::simtick::START.multiplier, crate::simtick::START.step));
            ticks = Some((crate::simtick::TICK_HZ as i64, t as i64 + 1, m, st));
        }
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
        parent_bearing = root.get("live").get("bearing").s();
        let t = d.get("ticks");
        if !t.is_null() {
            let n = |k: &str| t.get(k).num().unwrap_or(-1);
            ticks = Some((n("hz"), n("count"), n("multiplier"), n("step")));
        }
        (base, lv, tl, evs, Some(d.get("head").s()), Some(fin), root.get("live").get("renderer").s(), 0, None)
    };
    // SIM-TICK-0: the tick form — a look's delta and inputs, the ticks' order, the tick block — before anything replays
    let timed: Vec<crate::simtick::Timed> = events.iter().map(|e| crate::simtick::Timed {
        look: e.tag == b'K', delta: if e.tag == b'K' { e.param.parse().unwrap_or(0) } else { 0 }, tick: e.tick, input: e.input,
        sens: if e.tag == b'S' { Some(sens_of(&e.param)) } else { None } }).collect();
    crate::simtick::check_form(&timed, ticks).map_err(|m| refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: the tick form: {}", m)))?;
    // SIM-TICK-0: a look folds its camera token with its witness
    let pairs: Vec<(u8, String)> = events.iter().map(|e| (e.tag, if e.tag == b'K' { look_fold(&e.camera, &e.witness) } else { e.witness.clone() })).collect();
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
    // ADMIT-0: an envelope sits on an edit, names the chain's own heads around it, and its proposal id occurs once
    let mut admitted: Vec<&str> = Vec::new();
    for (k, e) in events.iter().enumerate() {
        if let Some(a) = &e.admit {
            let bad = if e.tag != b'E' {
                Some("it is not on an edit")
            } else if a.parent != heads[k] {
                Some("its parent is not the head before the event")
            } else if a.head != heads[k + 1] {
                Some("its head is not the head after the event")
            } else if admitted.contains(&a.proposal.as_str()) {
                Some("its proposal id was already admitted")
            } else {
                None
            };
            if let Some(why) = bad {
                return Err(refusal("session.load", vec![("event", V::N(k as u64))], format!("LIVESESSION-ENVELOPE: event {}: {}", k, why)));
            }
            admitted.push(&a.proposal);
        }
    }
    // 2. the renderer identity
    let same = parent_renderer == renderer_id();
    // SIM-TICK-0: a frame at a free heading is the bearing kernels'; their identity is consulted for those frames only
    let same_bearing = parent_bearing == bearing_id();
    let mut free = false;
    // 3. the replay, 4. the witnesses
    let mut s = LiveSession::new(lv, tl, base.camera).map_err(|m| refusal("session.load", vec![], format!("LIVESESSION-BASE: {}", m)))?;
    for (k, e) in events.iter().enumerate() {
        s.at_tick(e.tick);
        let (frame, camera_ok, witness_ok) = if e.tag == b'M' {
            match s.push_move(e.param.as_bytes()[0]) {
                Ok(ev) => (true, token(ev.camera, ev.yaw) == e.camera, ev.witness == e.witness),
                Err(_) => (false, false, false),
            }
        } else if e.tag == b'K' {
            // SIM-TICK-0: a look replays through the session like a move: the heading, then the frame at it
            match s.push_look(e.param.parse().unwrap_or(0), e.input) {
                Ok(ev) => (true, token(ev.camera, ev.yaw) == e.camera, ev.witness == e.witness),
                Err(_) => (false, false, false),
            }
        } else if e.tag == b'S' {
            // SIM-TICK-0a: a sensitivity event replays through the session: one legal transition, nothing folded
            let (m, st) = sens_of(&e.param);
            match s.push_sensitivity(crate::simtick::Sens { multiplier: m, step: st }) {
                Ok(_) => (false, true, true),
                Err(_) => (false, false, false),
            }
        } else {
            // ADMIT-0: an admitted edit replays as any edit does, and takes its envelope back with it
            if let Some(a) = &e.admit {
                s.admit_next(a.clone());
            }
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
        let here = s.free_heading();
        free = free || (frame && here);
        let same = same && (!(frame && here) || same_bearing);
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
    s.at_tick(None);
    s.set_tick_count(ticks.map(|(_, count, _, _)| count as u64));
    let same = same && (!free || same_bearing);
    if let Some((cam, content)) = &stored_final {
        if s.token() != *cam || s.content() != content {
            return Err(refusal("session.replay", vec![], "LIVESESSION-TAMPERED: the stored final camera or content is not the replay's".to_string()));
        }
    }
    let lineage = Lineage { parent_head: s.head().to_string(), parent_events: events.len(), source: if is_journal { "journal" } else { "session" },
                            parent_sha256: file_sha, torn };
    Ok(Loaded { session: s, base, lineage, classification: if same { "LOAD" } else { "LOAD-DIFFERENT-RENDERER" }, parent_renderer })
}

fn saved_event(e: &JsonView) -> Result<SavedEvent, Refusal> {
    let corrupt = |m: String| refusal("session.load", vec![], format!("LIVESESSION-CORRUPT: {}", m));
    let (tag, param) = match e.get("kind").s().as_str() {
        "move" => (b'M', e.get("command").s()),
        "edit" => (b'E', e.get("spec").s()),
        // SIM-TICK-0: a look's parameter is its integer delta
        "look" => (b'K', e.get("delta").num().ok_or_else(|| corrupt("a look without an integer delta".to_string()))?.to_string()),
        // SIM-TICK-0a: a sensitivity event's parameter is the configuration after it
        "sensitivity" => match (e.get("multiplier").num(), e.get("step").num()) {
            (Some(m), Some(st)) => (b'S', format!("{},{}", m, st)),
            _ => return Err(corrupt("a sensitivity event without its multiplier and step".to_string())),
        },
        k => return Err(corrupt(format!("event kind {:?}", k))),
    };
    if tag == b'M' && !matches!(param.as_str(), "L" | "R" | "F" | "B" | "Q" | "E") {
        return Err(corrupt(format!("move {:?}", param)));
    }
    let tick = match (e.get("tick").is_null(), e.get("tick").num()) {
        (true, _) => None,
        (false, Some(t)) if t >= 0 => Some(t as u64),
        _ => return Err(corrupt("an event's tick is not a whole number".to_string())),
    };
    let i = e.get("input");
    let input = if i.is_null() {
        None
    } else {
        match (i.get("counts").num(), i.get("multiplier").num(), i.get("step").num()) {
            (Some(c), Some(m), Some(st)) => Some((c, m, st)),
            _ => return Err(corrupt("a look's inputs are not counts, multiplier and step".to_string())),
        }
    };
    // ADMIT-0: an envelope is exactly eight text members: the language, five 64-hex values around the grant's line
    let a = e.get("admit");
    let admit = if a.is_null() {
        None
    } else {
        let bad = |m: &str| refusal("session.load", vec![], format!("LIVESESSION-ENVELOPE: {}", m));
        const KEYS: [&str; 8] = ["language", "proposal", "digest", "renderer", "bearing", "parent", "head", "grant"];
        if a.members() != Some(KEYS.len()) || KEYS.iter().any(|k| !a.get(k).is_str()) {
            return Err(bad("an envelope is not its eight text members"));
        }
        let v = |k: &str| a.get(k).s();
        if v("language") != crate::admit::LANGUAGE {
            return Err(bad("an envelope's language is not VRDNP1"));
        }
        if ["proposal", "digest", "renderer", "bearing", "parent", "head"].iter().any(|k| !hex64(&v(k))) {
            return Err(bad("an envelope's id, digest, identity or head is not 64 lower-case hex"));
        }
        if !crate::admit::grant_text(&v("grant")) {
            return Err(bad("an envelope's grant is not a grant's line"));
        }
        Some(Admit { language: v("language"), proposal: v("proposal"), digest: v("digest"), renderer: v("renderer"), bearing: v("bearing"),
                     parent: v("parent"), head: v("head"), grant: v("grant") })
    };
    Ok(SavedEvent { tag, param, camera: e.get("camera").s(), witness: e.get("witness").s(), tick, input, admit })
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
    /// MOUSE-LOOK-0: the look loop's counts for the saved file's live block (None unless the run had a tick source).
    look: Option<String>,
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
    let events = session.log().len();
    open(session, base, lineage, resumed, plan.plant, surface, events)
}

/// The run's directory and journal: the header, then the session's first `opening` events as records. ADMIT-0 opens a
/// run from a session it has already loaded and checked, with the parent's events as the opening.
fn open(session: LiveSession, base: Base, lineage: Option<Lineage>, resumed: Option<(&'static str, String)>, plant: String,
        surface: &'static str, opening: usize) -> Result<Prepared, i32> {
    let dir = std::path::Path::new(&root()).join(crate::refusallog::run_id()).to_string_lossy().to_string();
    let jpath = std::path::Path::new(&dir).join(JOURNAL).to_string_lossy().to_string();
    let opened = fs::create_dir_all(&dir).map_err(|e| e.to_string()).and_then(|_| Journal::open(&jpath, &plant, surface));
    let mut journal = match opened {
        Ok(j) => j,
        Err(m) => return Err(refuse_run(refusal("session.journal", vec![], format!("LIVESESSION-JOURNAL-UNWRITTEN: {}", m)), surface)),
    };
    let header = format!("{{\"journal\":\"{}\",\"run_id\":{},\"base\":{},\"renderer\":{},\"bearing\":{},\"lineage\":{}}}",
                         JOURNAL_MAGIC, esc(crate::refusallog::run_id()), base_json(&base), esc(&renderer_id()), esc(&bearing_id()), lineage_json(&lineage));
    let mut wrote = journal.put(&header);
    for (k, ev) in session.log().iter().enumerate().take(opening) {
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
    Ok(Prepared { session, base, lineage, resumed, journal, dir, plant, surface, look: None })
}

/// ADMIT-0: the run of an admission. `l` is the saved session as loaded, with the one admitted edit already appended
/// to it in memory by the seam (the session's own validation and replay; nothing written). The journal opens with the
/// parent's events, takes the admitted event's record, and the shared seal follows.
pub fn go_admitted(l: Loaded, plant: String, surface: &'static str) -> i32 {
    let parent_events = l.lineage.parent_events;
    let p = match open(l.session, l.base, Some(l.lineage), Some((l.classification, l.parent_renderer)), plant.clone(), surface, parent_events) {
        Ok(p) => p,
        Err(code) => return code,
    };
    die(&plant, "die-opened"); // PLANT: the journal holds the parent's events and nothing else
    {
        let mut j = p.journal.borrow_mut();
        for (k, ev) in p.session.log().iter().enumerate().skip(parent_events) {
            j.put_event(k, ev);
        }
    }
    finish(p, "admission", "{\"source\":\"none\"}")
}

/// The run: LIVE-INPUT-0's loop, then the seal, then the saved file's verification. Returns the exit code.
pub fn go<S: ExactSurface + Keys + Focus>(s: &mut S, p: Prepared) -> i32 {
    go_with(s, p, crate::liveinput::bind, None).0
}

/// The same run under a given binding (LIVE-AUTHOR-0's live editor) and held set (HOLD-WALK-0's; None binds no repeat);
/// also hands back the loop's counts for the gate.
pub fn go_with<S: ExactSurface + Keys + Focus>(s: &mut S, p: Prepared, binding: fn(u32) -> crate::liveinput::Action,
                                               hold: Option<fn(u32) -> bool>) -> (i32, Option<crate::liveinput::Live>) {
    let Prepared { mut session, base, lineage, resumed, journal, dir, plant, surface, look } = p;
    let live = match crate::liveinput::run_with(s, &mut session, surface, binding, hold) {
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
    let focus = s.focus();
    // SIM-TICK-0: the seal is `finish`, shared with the tick run
    let code = finish(Prepared { session, base, lineage, resumed, journal, dir, plant, surface, look }, live.ended, &focus);
    (code, if code == 0 { Some(live) } else { None })
}

/// MOUSE-LOOK-0: the live editor with the mouse — LIVE-INPUT-0's loop under a tick source (the surface's clock and
/// mouse), the mouse released, then the same seal. Capture is shell state: the release happens before anything is
/// certified or written, whatever the loop returned, and the session never hears of it. Also hands back the run's
/// output for the gate (the trace and the counts).
pub fn go_look<S: ExactSurface + Keys + Focus + crate::mouselook::Look>(s: &mut S, p: Prepared) -> (i32, Option<String>) {
    let Prepared { mut session, base, lineage, resumed, journal, dir, plant, surface, look } = p;
    let result = crate::liveinput::run_look(s, &mut session, surface);
    s.release();
    println!("[look] the mouse is released");
    let live = match result {
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
    let observed = s.focus();
    println!("[look] the surface observed {}", observed); // MOUSE-LOOK-0a: recorded below, never ruled on
    let raw = crate::mouselook::raw_json(&live, &session);
    // the loop's counts go into the saved file's live block: what was shown, repeated, read back and sampled is recorded
    let look = look.or(Some(crate::mouselook::live_json(&live)));
    let code = finish(Prepared { session, base, lineage, resumed, journal, dir, plant, surface, look }, live.ended, &observed);
    (code, if code == 0 { Some(raw) } else { None })
}

/// SIM-TICK-0: the tick run — raw inputs with their times through the accumulator, one command per tick, into the same
/// session, journal and seal. Windowless: no surface, no loop, no present, no clock.
pub fn go_ticks(p: Prepared, script: &[(u64, crate::simtick::Input)]) -> (i32, Option<String>) {
    let Prepared { mut session, base, lineage, resumed, journal, dir, plant, surface, look } = p;
    let run = match crate::tickrun::run(&mut session, script, surface) {
        Ok(r) => r,
        Err(m) => return (refuse_run(refusal("input.tick", vec![], m), surface), None),
    };
    for ln in crate::tickrun::summary(&run, &session) {
        println!("{}", ln);
    }
    let raw = crate::tickrun::raw_json(&run, &session);
    let code = finish(Prepared { session, base, lineage, resumed, journal, dir, plant, surface, look }, run.ended, "{\"source\":\"none\"}");
    (code, if code == 0 { Some(raw) } else { None })
}

/// SIM-TICK-0: every frame of the session's log at a free heading, recomputed by the reference kernel across threads.
/// The live witness of such a frame is the production tread's; this is what makes a saved session reference-certified.
/// Returns how many frames were recomputed (none for a walk that never leaves the four facings).
pub fn certify(session: &LiveSession) -> Result<usize, Refusal> {
    let threads = crate::heading::threads();
    session.free_frames(threads * 8, &mut |batch| crate::heading::certify(batch, threads)).map_err(|(event, why)| {
        refusal("session.certify", vec![("event", V::N(event as u64))],
                format!("LIVESESSION-UNCERTIFIED: event {}: {} — the session is not saved", event, why))
    })
}

/// The seal, after a run: the reference's certification, then the saved file written, read back and verified. Returns
/// the exit code. Shared by the loop's run (go_with) and the tick run (go_ticks).
fn finish(p: Prepared, ended: &str, focus: &str) -> i32 {
    let Prepared { session, base, lineage, resumed, journal, dir, plant, surface, look } = p;
    // SIM-TICK-0: nothing is written until every free-heading frame is the reference's; a session is saved
    // reference-certified or it is not saved
    let certified = match certify(&session) {
        Ok(n) => n,
        Err(r) => return refuse_run(r, surface),
    };
    if certified > 0 {
        println!("[livesession] certified: {} free-heading frames recomputed by the reference kernel, all equal", certified);
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
        "{{\"log\":\"{}\",\"run_id\":{},\"renderer\":{},\"bearing\":{},\"lineage\":{},\"resumed\":{},\"journal\":{{\"file\":\"{}\",\"records\":{},\"events\":{},\"complete\":{},\"sha256\":{}}},\"certified\":{{\"reference\":\"kernel/bearing.rs\",\"frames\":{}}},\"ended\":{},\"focus\":{}{}}}",
        LOG, esc(crate::refusallog::run_id()), esc(&renderer_id()), esc(&bearing_id()), lineage_json(&lineage), resumed_json, JOURNAL, jrecords, jevents,
        jbroken.is_none() && jevents as usize == session.log().len(), esc(&jsha), certified, esc(ended), focus,
        look.map_or(String::new(), |l| format!(",\"look\":{}", l))); // MOUSE-LOOK-0: only a run under a tick source has it
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
        return refuse_run(refusal("session.seal", vec![("path", V::S(dst.clone()))], format!("LIVESESSION-SEAL-UNWRITTEN: {}", m)), surface);
    }
    // the saved artifact, read back from the disk, must verify before the run counts as saved
    let verified = fs::read(&dst).map_err(|e| e.to_string()).and_then(|b| {
        if b != text.as_bytes() {
            return Err("the bytes read back are not the bytes written".to_string());
        }
        let l = load(&dst).map_err(|r| r.message)?;
        let (a, b2) = (l.session.log(), session.log());
        if l.session.head() != session.head() || l.session.token() != session.token() || l.session.content() != session.content()
            || a.len() != b2.len() || a.iter().zip(b2.iter()).any(|(x, y)| x.witness != y.witness || x.param != y.param)
            || l.session.ticks() != session.ticks() || a.iter().zip(b2.iter()).any(|(x, y)| x.yaw != y.yaw || x.tick != y.tick || x.input != y.input)
            || a.iter().zip(b2.iter()).any(|(x, y)| x.admit != y.admit) {
            return Err("the replay of the saved file does not reach the live session's state".to_string());
        }
        Ok(())
    });
    if let Err(m) = verified {
        return refuse_run(refusal("session.seal", vec![("path", V::S(dst.clone()))], format!("LIVESESSION-SEAL-UNVERIFIED: {}", m)), surface);
    }
    if let Some(m) = jbroken {
        println!("[livesession] the journal failed during the run ({}); the saved session is complete and verified", m);
    }
    println!("[livesession] saved and verified: {} — {} events, head {}", dst, session.log().len(), session.head());
    crate::runledger::end(0);
    0
}
