// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/readercourt.rs — READER-COURT-0: the court command over the saved form's reader (kernel/savedform.rs).
//
// The reader is a library; this is how the gate asks it questions without going through a session, a record or a
// window. Four commands, none of which writes anything but the file it is told to:
//
//   shell form-verdict (--document | --payload) FILE
//       one line: "A <sha256 of the typed value's canonical JSON>" or "R <CODE> <offset>"
//   shell form-court (--document | --payload) FILE --out OUT
//       the exhaustive single-byte court, in process: every substitution of every byte by each of the 255 other
//       values, every deletion of one byte, every insertion of each of the 256 values at each of the length + 1
//       places, in that order; one verdict line per mutant written to OUT
//   shell form-splice --manifest MANIFEST
//       each line of MANIFEST is "document|payload <TAB> FILE <TAB> SCRIPT <TAB> OUT"; each line of SCRIPT is
//       "<offset> <bytes removed> <hex inserted or ->", one splice of FILE; the same line of OUT is the verdict on
//       FILE with that splice applied: the registered boundary mutations of real files, without writing each mutant
//       to the disk
//   shell form-spell --in FILE --out OUT
//       each line of FILE is the hex of a UTF-8 text; the same line of OUT is the hex of its one spelling
//
// A verdict is data, so every command ends 0 when it could do its work, whatever the verdicts were; a file it cannot
// read or a line it cannot parse ends 2 with a coded line. Nothing here reads a clock or takes a different path for
// a mutant than for a real file: each mutant is given to the same two functions a loader calls.

use crate::mantle::{hex, sha256};
use crate::savedform::{self, Json};

/// RECORD-0's canonical JSON of a typed value: names in byte order, no whitespace, the one spelling. Two accepted
/// inputs hold the same typed value exactly when these bytes are equal.
pub fn canonical(v: &Json, out: &mut String) {
    match v {
        Json::Null => out.push_str("null"),
        Json::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Json::Num(n) => out.push_str(&n.to_string()),
        Json::Str(s) => out.push_str(&savedform::spell(s)),
        Json::Arr(a) => {
            out.push('[');
            for (i, x) in a.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                canonical(x, out);
            }
            out.push(']');
        }
        Json::Obj(m) => {
            out.push('{');
            for (i, (k, x)) in m.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push_str(&savedform::spell(k));
                out.push(':');
                canonical(x, out);
            }
            out.push('}');
        }
    }
}

/// The verdict line on some bytes, as a document or as a payload.
pub fn verdict(b: &[u8], payload: bool) -> String {
    let read = if payload { savedform::read_payload(b) } else { savedform::read_document(b) };
    match read {
        Ok(v) => {
            let mut text = String::new();
            canonical(&v, &mut text);
            format!("A {}", hex(&sha256(text.as_bytes())))
        }
        Err(r) => format!("R {}", r.line()),
    }
}

fn refuse(code: &str, detail: &str) -> i32 {
    eprintln!("SHELL-FORM-{}: {}", code, detail);
    2
}

fn unhex(s: &str) -> Option<Vec<u8>> {
    let b = s.as_bytes();
    if b.len() % 2 != 0 {
        return None;
    }
    let d = |c: u8| match c {
        b'0'..=b'9' => Some(c - b'0'),
        b'a'..=b'f' => Some(c - b'a' + 10),
        _ => None,
    };
    let mut out = Vec::with_capacity(b.len() / 2);
    for p in b.chunks(2) {
        out.push(d(p[0])? * 16 + d(p[1])?);
    }
    Some(out)
}

/// The exhaustive single-byte court over one input: a verdict line per mutant, in the registered order.
pub fn court(base: &[u8], payload: bool) -> Vec<String> {
    let n = base.len();
    let mut lines = Vec::with_capacity(n * 512 + 256);
    let mut m = base.to_vec();
    for p in 0..n {
        let keep = m[p];
        for v in 0..=255u8 {
            if v != keep {
                m[p] = v;
                lines.push(verdict(&m, payload));
            }
        }
        m[p] = keep;
    }
    for p in 0..n {
        let mut d = Vec::with_capacity(n - 1);
        d.extend_from_slice(&base[..p]);
        d.extend_from_slice(&base[p + 1..]);
        lines.push(verdict(&d, payload));
    }
    for p in 0..=n {
        let mut w = Vec::with_capacity(n + 1);
        w.extend_from_slice(&base[..p]);
        w.push(0);
        w.extend_from_slice(&base[p..]);
        for v in 0..=255u8 {
            w[p] = v;
            lines.push(verdict(&w, payload));
        }
    }
    lines
}

fn write_lines(out: &str, lines: &[String]) -> Result<String, String> {
    let mut text = lines.join("\n");
    text.push('\n');
    std::fs::write(out, text.as_bytes()).map_err(|e| format!("{}: {}", out, e))?;
    Ok(hex(&sha256(text.as_bytes())))
}

pub fn run(args: &[String]) -> i32 {
    let cmd = args[1].as_str();
    let a = &args[2..];
    let opt = |flag: &str| -> Option<String> { a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned()) };
    let known: &[&str] = match cmd {
        "form-verdict" => &["--document", "--payload"],
        "form-court" => &["--document", "--payload", "--out"],
        "form-splice" => &["--manifest"],
        _ => &["--in", "--out"],
    };
    if a.len() % 2 != 0 || a.chunks(2).any(|p| !known.contains(&p[0].as_str())) {
        return refuse("USAGE", "an option this command does not take, or an option without its value");
    }
    if cmd == "form-spell" {
        let (Some(inp), Some(out)) = (opt("--in"), opt("--out")) else { return refuse("USAGE", "form-spell --in FILE --out OUT") };
        let text = match std::fs::read_to_string(&inp) {
            Ok(t) => t,
            Err(e) => return refuse("CANNOT-READ", &format!("{}: {}", inp, e)),
        };
        let mut lines = Vec::new();
        for (k, ln) in text.lines().enumerate() {
            let Some(s) = unhex(ln).and_then(|b| String::from_utf8(b).ok()) else {
                return refuse("LINE", &format!("line {} is not the hex of a UTF-8 text", k + 1));
            };
            lines.push(hex(savedform::spell(&s).as_bytes()));
        }
        return match write_lines(&out, &lines) {
            Ok(sum) => {
                println!("spelled {} texts sha256 {}", lines.len(), sum);
                0
            }
            Err(m) => refuse("CANNOT-WRITE", &m),
        };
    }
    if cmd == "form-splice" {
        let Some(manifest) = opt("--manifest") else { return refuse("USAGE", "form-splice --manifest MANIFEST") };
        let listing = match std::fs::read_to_string(&manifest) {
            Ok(t) => t,
            Err(e) => return refuse("CANNOT-READ", &format!("{}: {}", manifest, e)),
        };
        let (mut files, mut mutants) = (0usize, 0usize);
        for (row, entry) in listing.lines().enumerate() {
            let f: Vec<&str> = entry.split('\t').collect();
            if f.len() != 4 || (f[0] != "document" && f[0] != "payload") {
                return refuse("LINE", &format!("manifest line {} is not \"document|payload <TAB> FILE <TAB> SCRIPT <TAB> OUT\"", row + 1));
            }
            let payload = f[0] == "payload";
            let base = match std::fs::read(f[1]) {
                Ok(b) => b,
                Err(e) => return refuse("CANNOT-READ", &format!("{}: {}", f[1], e)),
            };
            let script = match std::fs::read_to_string(f[2]) {
                Ok(t) => t,
                Err(e) => return refuse("CANNOT-READ", &format!("{}: {}", f[2], e)),
            };
            let mut lines = Vec::new();
            for (k, ln) in script.lines().enumerate() {
                let mut it = ln.split(' ');
                let parsed = (|| {
                    let at: usize = it.next()?.parse().ok()?;
                    let cut: usize = it.next()?.parse().ok()?;
                    let ins = match it.next()? {
                        "-" => Vec::new(),
                        h => unhex(h)?,
                    };
                    if it.next().is_some() || at > base.len() || cut > base.len() - at {
                        return None;
                    }
                    Some((at, cut, ins))
                })();
                let Some((at, cut, ins)) = parsed else {
                    return refuse("LINE", &format!("{} line {} is not \"<offset> <removed> <hex or ->\" inside the file", f[2], k + 1));
                };
                let mut m = Vec::with_capacity(base.len() - cut + ins.len());
                m.extend_from_slice(&base[..at]);
                m.extend_from_slice(&ins);
                m.extend_from_slice(&base[at + cut..]);
                lines.push(verdict(&m, payload));
            }
            if let Err(m) = write_lines(f[3], &lines) {
                return refuse("CANNOT-WRITE", &m);
            }
            files += 1;
            mutants += lines.len();
        }
        println!("spliced {} files {} mutants", files, mutants);
        return 0;
    }
    let (file, payload) = match (opt("--document"), opt("--payload")) {
        (Some(f), None) => (f, false),
        (None, Some(f)) => (f, true),
        _ => return refuse("USAGE", "exactly one of --document FILE and --payload FILE"),
    };
    let base = match std::fs::read(&file) {
        Ok(b) => b,
        Err(e) => return refuse("CANNOT-READ", &format!("{}: {}", file, e)),
    };
    match cmd {
        "form-verdict" => {
            println!("{}", verdict(&base, payload));
            0
        }
        _ => {
            let Some(out) = opt("--out") else { return refuse("USAGE", "form-court needs --out OUT") };
            let lines = court(&base, payload);
            match write_lines(&out, &lines) {
                Ok(sum) => {
                    println!("court {} bytes {} mutants sha256 {}", base.len(), lines.len(), sum);
                    0
                }
                Err(m) => refuse("CANNOT-WRITE", &m),
            }
        }
    }
}
