// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/refusallog.rs — REFUSAL-LOG-0: every refusal on the present path leaves one line in an unsealed, append-only log.
//
// A console line says that a refusal happened, once, to whoever was watching. This log keeps it: one JSON line per
// refusal event, appended and never rewritten, so a refusal that recurs across runs can be counted instead of being
// recalled from transcripts. It is an observation about execution, never evidence and never authority: it is not
// sealed, not chained, not committed, read by no rule, and nothing on the present path reads it back. Writing it can
// never change a refusal: a failed append is said on the console and the refusal goes on exactly as before.
//
// The admitted operations (REFUSAL-LOG-0's scope): the PRESENT-EXACT-0 court (`presentexact::court`, whose refusals
// are data and are logged where they are emitted, by the headless selftest and by the host window), and the locked
// presenter (`shell show` / `shell show-playback`), whose refusals and whose every differing screen readback are
// logged. One record per refusal event; one record per differing readback.
//
// Where: $VERDANDI_REFUSAL_LOG if set, else build/refusals.log relative to the working directory (the repository root
// in every documented command). The gate points the variable at its own scratch file, so its planted refusals never
// reach the owner's log. The log is gitignored (*.log).
//
// A record (one line, keys in this order; integers and strings only; no interpretation):
//   {"log":"REFUSAL-LOG-0","refusal_id":"<run_id>/<seq>","run_id":…,"seq":…,"unix_ms":…,"operation":…,"surface":…,
//    "reason_code":…,"attribution":…,"context":{…},"context_digest":"<sha256 of the context object's JSON>"}

use crate::mantle::{hex, sha256};
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

pub const ENV: &str = "VERDANDI_REFUSAL_LOG";
pub const DEFAULT_PATH: &str = "build/refusals.log";
pub const LOG: &str = "REFUSAL-LOG-0";

/// A context value: an integer or a string (RECORD-0's rule, kept here though the log is not a record).
pub enum V {
    N(u64),
    S(String),
}

/// One refusal event on an admitted operation: what refused (the operation and the surface it ran on), the refusal's
/// stable code (the reason), where on the path it came from (the attribution), and a few facts (the context).
pub struct Event {
    pub operation: &'static str,
    pub surface: &'static str,
    pub reason: String,
    pub attribution: &'static str,
    pub context: Vec<(&'static str, V)>,
}

static SEQ: AtomicU64 = AtomicU64::new(0);
static RUN: OnceLock<String> = OnceLock::new();

pub(crate) fn unix_ms() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_millis() as u64).unwrap_or(0)
}

/// This process's run identity: its start in unix milliseconds and its process id, in hex.
pub fn run_id() -> &'static str {
    RUN.get_or_init(|| format!("{:x}-{:x}", unix_ms(), std::process::id()))
}

/// How many refusal records this run has emitted (appended or attempted): RUN-LEDGER-0's join count.
pub fn emitted() -> u64 {
    SEQ.load(Ordering::SeqCst)
}

/// The stable code at the head of a console refusal message ("PRESENTEXACT-READBACK: …" -> "PRESENTEXACT-READBACK").
pub fn code_of(message: &str) -> String {
    let head: String = message.chars().take_while(|c| c.is_ascii_uppercase() || c.is_ascii_digit() || *c == '-').collect();
    if !head.is_empty() && message[head.len()..].starts_with(':') { head } else { "UNCODED".to_string() }
}

/// JSON string escaping as Python's json.dumps(ensure_ascii=False) does it, so the digest can be recomputed there.
pub(crate) fn esc(s: &str) -> String {
    let mut out = String::from("\"");
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn context_json(ctx: &[(&'static str, V)]) -> String {
    let parts: Vec<String> = ctx
        .iter()
        .map(|(k, v)| format!("{}:{}", esc(k), match v { V::N(n) => n.to_string(), V::S(s) => esc(s) }))
        .collect();
    format!("{{{}}}", parts.join(","))
}

/// The one line an event appends (no trailing newline).
pub fn line(ev: &Event, seq: u64, ms: u64) -> String {
    let ctx = context_json(&ev.context);
    let run = run_id();
    format!("{{\"log\":{},\"refusal_id\":{},\"run_id\":{},\"seq\":{},\"unix_ms\":{},\"operation\":{},\"surface\":{},\"reason_code\":{},\"attribution\":{},\"context\":{},\"context_digest\":{}}}",
            esc(LOG), esc(&format!("{}/{}", run, seq)), esc(run), seq, ms, esc(ev.operation), esc(ev.surface), esc(&ev.reason),
            esc(ev.attribution), ctx, esc(&hex(&sha256(ctx.as_bytes()))))
}

fn path() -> String {
    std::env::var(ENV).ok().filter(|p| !p.is_empty()).unwrap_or_else(|| DEFAULT_PATH.to_string())
}

/// Record one refusal event: exactly one line appended, never a rewrite. A failed append is said on the console and
/// changes nothing else.
pub fn record(ev: &Event) {
    let seq = SEQ.fetch_add(1, Ordering::SeqCst);
    let text = format!("{}\n", line(ev, seq, unix_ms()));
    let p = path();
    let res = (|| -> std::io::Result<()> {
        if let Some(dir) = std::path::Path::new(&p).parent() {
            if !dir.as_os_str().is_empty() {
                std::fs::create_dir_all(dir)?;
            }
        }
        let mut f = std::fs::OpenOptions::new().create(true).append(true).open(&p)?;
        f.write_all(text.as_bytes())
    })();
    if let Err(e) = res {
        eprintln!("SHELL-REFUSAL-LOG-UNWRITTEN: {}: {} (the refusal below stands as it would without the log)", p, e);
    }
}

/// The refusal primitive: record the event, then print its console line exactly as the refusal printed it before. The
/// caller then cleans up and exits as it did; a refusal cannot print without leaving its line.
pub fn refuse(ev: &Event, console: &str) {
    record(ev);
    eprintln!("{}", console);
}
