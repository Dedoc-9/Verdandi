// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/runledger.rs — RUN-LEDGER-0: one line per admitted run, refused or not — the denominator the refusal log lacks.
//
// The refusal log (REFUSAL-LOG-0) holds refusal events only, so a run that refused nothing leaves no trace in it, and
// "no refusals occurred" cannot be told from "the run was not recorded". This ledger holds the runs: one JSON line per
// admitted run, appended when the run ends, whatever its outcome — a clean run is a line with differed 0 and exit 0.
// It is an observation, never evidence and never authority: not sealed, not chained, not committed, read by no rule
// and by nothing on the present path. It is a separate file, so every line of the refusal log is still a refusal.
//
// The admitted runs are REFUSAL-LOG-0's admitted operations: a PRESENT-EXACT-0 court run (the headless selftest or the
// host window; begun just before the court function, ended with the court's outcome) and a presenter run (`shell show`
// / `shell show-playback`; begun on entry, ended at every exit). A run is a process: its run_id is the refusal log's,
// so the two files join on it.
//
// Where: $VERDANDI_RUN_LEDGER if set, else build/runs.log relative to the working directory. The gate points the
// variable at its own scratch file. The ledger is gitignored (*.log).
//
// A line (keys in this order; integers and strings only):
//   {"log":"RUN-LEDGER-0","run_id":…,"operation":…,"surface":…,"readbacks_checked":…,"differed":…,"refusals":…,
//    "exit_code":…,"unix_ms_start":…,"unix_ms_end":…}
// readbacks_checked and differed are the operation's own counts of compared screen readbacks; refusals is how many
// refusal-log records the run emitted; exit_code is the code the run ends with.

use crate::refusallog::{esc, unix_ms};
use std::io::Write;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::OnceLock;

pub const ENV: &str = "VERDANDI_RUN_LEDGER";
pub const DEFAULT_PATH: &str = "build/runs.log";
pub const LOG: &str = "RUN-LEDGER-0";

struct Begun {
    operation: &'static str,
    surface: &'static str,
    start_ms: u64,
}

static BEGUN: OnceLock<Begun> = OnceLock::new();
static CHECKED: AtomicU64 = AtomicU64::new(0);
static DIFFERED: AtomicU64 = AtomicU64::new(0);
static ENDED: AtomicBool = AtomicBool::new(false);

/// Begin this process's admitted run. The run identity is the refusal log's.
pub fn begin(operation: &'static str, surface: &'static str) {
    let _ = crate::refusallog::run_id();
    let _ = BEGUN.set(Begun { operation, surface, start_ms: unix_ms() });
}

/// One compared screen readback of the run, and whether it differed — counted where the operation counts its own.
pub fn readback(differed: bool) {
    CHECKED.fetch_add(1, Ordering::SeqCst);
    if differed {
        DIFFERED.fetch_add(1, Ordering::SeqCst);
    }
}

fn line(b: &Begun, exit_code: i32, end_ms: u64) -> String {
    format!("{{\"log\":{},\"run_id\":{},\"operation\":{},\"surface\":{},\"readbacks_checked\":{},\"differed\":{},\"refusals\":{},\"exit_code\":{},\"unix_ms_start\":{},\"unix_ms_end\":{}}}",
            esc(LOG), esc(crate::refusallog::run_id()), esc(b.operation), esc(b.surface), CHECKED.load(Ordering::SeqCst),
            DIFFERED.load(Ordering::SeqCst), crate::refusallog::emitted(), exit_code.max(0), b.start_ms, end_ms)
}

fn path() -> String {
    std::env::var(ENV).ok().filter(|p| !p.is_empty()).unwrap_or_else(|| DEFAULT_PATH.to_string())
}

/// End the run with the code it ends with: exactly one line appended, never a rewrite; the caller then exits as it did.
/// An end with no begin, or a second end, writes nothing. A failed append is said on the console and changes nothing
/// else.
pub fn end(exit_code: i32) {
    let b = match BEGUN.get() {
        Some(b) => b,
        None => return,
    };
    if ENDED.swap(true, Ordering::SeqCst) {
        return;
    }
    let text = format!("{}\n", line(b, exit_code, unix_ms()));
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
        eprintln!("SHELL-RUN-LEDGER-UNWRITTEN: {}: {} (the run ends as it would without the ledger)", p, e);
    }
}
