// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/savedform.rs — READER-COURT-0: the reader of the saved form.
//
// Everything the tree saves and reads back is written in one bounded language: what the tree's registered writers
// are permitted to emit, and nothing wider. This file is its one Rust reader, shared by path (the shell, and the
// workshop's sessionwalk, session and edit). It is not a general JSON reader.
//
//   a DOCUMENT   one object followed by exactly one LF; nothing before the object, nothing after the LF
//   a PAYLOAD    one object and nothing else (a journal record's)
//   a value      an object, an array, a string, an integer, true, false or null
//   between tokens   spaces (0x20) and LFs (0x0A) only
//   an object    its names are strings and no name occurs twice; it may be empty
//   depth        objects and arrays nest at most SEVEN deep: the count is of those open at once, the root object
//                the first; a string, an integer, true, false or null opens no level
//   an integer   "0", or an optional "-" and a digit 1-9 followed by digits, within signed 64 bits: no leading zero,
//                no minus zero, no fraction, no exponent
//   a string     well-formed UTF-8, raw from U+0020 up except the quote and the backslash; \" \\ \b \f \n \r \t;
//                \u00XX in lower-case hex for the other characters below U+0020 and for nothing else
//
// The verdict on any bytes is a typed value, or a code and a byte offset. The offset is the first byte at which the
// input stops being the beginning of any document (or payload) of the language, or the input's length if it ended
// where one could still continue: it belongs to the language and the bytes, and this reader only computes it.
//
//   READER-TRUNCATED   the input ended
//   READER-TRAILING    the object is complete and this byte may not follow it
//   READER-DEPTH       this bracket or brace would open an eighth level
//   READER-DUPLICATE   this closing quote completes a name the object already has
//   READER-STRING      inside a string: a control character, an escape that is not the language's, ill-formed UTF-8
//   READER-NUMBER      inside an integer, or a digit or one of . e E + - directly after one
//   READER-STRUCTURE   any other byte that cannot come next
//
// This file owns reading the language and its one string spelling, and nothing else. It opens no file and starts
// nothing, and it knows nothing of the window, the tools that include it, what a document means, or who reads it.
// It reads with a stack it keeps itself, so no input can exhaust the machine's.
#![allow(dead_code)]

use std::collections::BTreeMap;

/// The deepest nesting of objects and arrays the language holds, the root object counted as the first.
pub const DEPTH_MAX: usize = 7;

pub const TRUNCATED: &str = "READER-TRUNCATED";
pub const TRAILING: &str = "READER-TRAILING";
pub const DEPTH: &str = "READER-DEPTH";
pub const DUPLICATE: &str = "READER-DUPLICATE";
pub const STRING: &str = "READER-STRING";
pub const NUMBER: &str = "READER-NUMBER";
pub const STRUCTURE: &str = "READER-STRUCTURE";

/// A typed value of the language. A member's position in an object carries no meaning.
#[derive(Clone, Debug, PartialEq)]
pub enum Json {
    Null,
    Bool(bool),
    Num(i64),
    Str(String),
    Arr(Vec<Json>),
    Obj(BTreeMap<String, Json>),
}

impl Json {
    /// The member of that name, or null for a missing member or a value that is not an object.
    pub fn get(&self, k: &str) -> &Json {
        match self {
            Json::Obj(m) => m.get(k).unwrap_or(&Json::Null),
            _ => &Json::Null,
        }
    }
    /// The text of a string, or the empty text.
    pub fn s(&self) -> &str {
        match self {
            Json::Str(s) => s,
            _ => "",
        }
    }
    pub fn str(&self) -> &str {
        self.s()
    }
    /// The integer, or -1 for a value that is not one.
    pub fn n(&self) -> i64 {
        match self {
            Json::Num(n) => *n,
            _ => -1,
        }
    }
    pub fn num(&self) -> i64 {
        self.n()
    }
    pub fn boolean(&self) -> bool {
        matches!(self, Json::Bool(true))
    }
    /// The items of an array, or none.
    pub fn arr(&self) -> &[Json] {
        match self {
            Json::Arr(a) => a,
            _ => &[],
        }
    }
}

/// Why bytes are not of the language: what was being read, and where they stopped being a beginning of it.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Refused {
    pub code: &'static str,
    pub offset: usize,
}

impl Refused {
    /// "CODE offset", the one line every reader gives.
    pub fn line(&self) -> String {
        format!("{} {}", self.code, self.offset)
    }
}

fn at(b: &[u8], code: &'static str, i: usize) -> Refused {
    if i >= b.len() {
        Refused { code: TRUNCATED, offset: b.len() }
    } else {
        Refused { code, offset: i }
    }
}

/// The first byte at or after i that is neither a space nor an LF.
fn gap(b: &[u8], mut i: usize) -> usize {
    while i < b.len() && (b[i] == 0x20 || b[i] == 0x0a) {
        i += 1;
    }
    i
}

/// A string whose opening quote is at `open`: its text and the index after its closing quote.
fn string(b: &[u8], open: usize) -> Result<(String, usize), Refused> {
    let n = b.len();
    let mut out: Vec<u8> = Vec::new();
    let mut j = open + 1;
    loop {
        if j >= n {
            return Err(at(b, TRUNCATED, n));
        }
        let c = b[j];
        match c {
            b'"' => {
                // every byte pushed was checked, so this conversion cannot fail; if it ever did, it is the string's fault
                return String::from_utf8(out).map(|s| (s, j + 1)).map_err(|_| Refused { code: STRING, offset: open });
            }
            b'\\' => {
                if j + 1 >= n {
                    return Err(at(b, TRUNCATED, n));
                }
                let short = match b[j + 1] {
                    b'"' => Some(b'"'),
                    b'\\' => Some(b'\\'),
                    b'b' => Some(0x08),
                    b'f' => Some(0x0c),
                    b'n' => Some(0x0a),
                    b'r' => Some(0x0d),
                    b't' => Some(0x09),
                    _ => None,
                };
                if let Some(x) = short {
                    out.push(x);
                    j += 2;
                    continue;
                }
                if b[j + 1] != b'u' {
                    return Err(Refused { code: STRING, offset: j + 1 });
                }
                // \u00XX: two zeros, then 0 or 1, then one lower-case hex digit
                let want: [&[u8]; 4] = [b"0", b"0", b"01", b"0123456789abcdef"];
                for (k, w) in want.iter().enumerate() {
                    let p = j + 2 + k;
                    if p >= n {
                        return Err(at(b, TRUNCATED, n));
                    }
                    if !w.contains(&b[p]) {
                        return Err(Refused { code: STRING, offset: p });
                    }
                }
                let low = b[j + 5];
                let v = (b[j + 4] - b'0') * 16 + if low <= b'9' { low - b'0' } else { low - b'a' + 10 };
                if matches!(v, 0x08 | 0x09 | 0x0a | 0x0c | 0x0d) {
                    // these five have a two-character escape, and a character has one spelling
                    return Err(Refused { code: STRING, offset: j + 5 });
                }
                out.push(v);
                j += 6;
            }
            0x00..=0x1f => return Err(Refused { code: STRING, offset: j }),
            0x20..=0x7f => {
                out.push(c);
                j += 1;
            }
            _ => {
                // a lead byte, and the range each byte after it must lie in: no overlong form, no surrogate,
                // nothing past U+10FFFF
                const C: (u8, u8) = (0x80, 0xbf);
                let need: &[(u8, u8)] = match c {
                    0xc2..=0xdf => &[C],
                    0xe0 => &[(0xa0, 0xbf), C],
                    0xed => &[(0x80, 0x9f), C],
                    0xe1..=0xec | 0xee..=0xef => &[C, C],
                    0xf0 => &[(0x90, 0xbf), C, C],
                    0xf1..=0xf3 => &[C, C, C],
                    0xf4 => &[(0x80, 0x8f), C, C],
                    _ => return Err(Refused { code: STRING, offset: j }),
                };
                for (k, (lo, hi)) in need.iter().enumerate() {
                    let p = j + 1 + k;
                    if p >= n {
                        return Err(at(b, TRUNCATED, n));
                    }
                    if b[p] < *lo || b[p] > *hi {
                        return Err(Refused { code: STRING, offset: p });
                    }
                }
                out.extend_from_slice(&b[j..j + 1 + need.len()]);
                j += 1 + need.len();
            }
        }
    }
}

/// An integer starting at i (a minus or a digit): its value and the index after it.
fn integer(b: &[u8], i: usize) -> Result<(i64, usize), Refused> {
    let n = b.len();
    let mut j = i;
    let neg = b[j] == b'-';
    if neg {
        j += 1;
        if j >= n {
            return Err(at(b, TRUNCATED, n));
        }
        if !(b'1'..=b'9').contains(&b[j]) {
            return Err(Refused { code: NUMBER, offset: j }); // "-0" and "-x" are not integers of the language
        }
    }
    let mut v: u128 = 0;
    if b[j] == b'0' {
        j += 1;
    } else {
        let limit: u128 = if neg { 1u128 << 63 } else { (1u128 << 63) - 1 };
        while j < n && b[j].is_ascii_digit() {
            v = v * 10 + u128::from(b[j] - b'0');
            if v > limit {
                return Err(Refused { code: NUMBER, offset: j }); // the digit that takes it out of range
            }
            j += 1;
        }
    }
    if j < n && (b[j].is_ascii_digit() || matches!(b[j], b'.' | b'e' | b'E' | b'+' | b'-')) {
        return Err(Refused { code: NUMBER, offset: j });
    }
    let value = if neg { (-(v as i128)) as i64 } else { v as i64 };
    Ok((value, j))
}

/// The rest of a literal whose first byte, at i, is already known: the index after it.
fn literal(b: &[u8], i: usize, word: &[u8]) -> Result<usize, Refused> {
    for k in 1..word.len() {
        if i + k >= b.len() {
            return Err(at(b, TRUNCATED, b.len()));
        }
        if b[i + k] != word[k] {
            return Err(Refused { code: STRUCTURE, offset: i + k });
        }
    }
    Ok(i + word.len())
}

/// A name and its colon, starting at i: the name and the index of its value. `held` is the object so far.
fn name(b: &[u8], i: usize, held: &BTreeMap<String, Json>) -> Result<(String, usize), Refused> {
    if i >= b.len() || b[i] != b'"' {
        return Err(at(b, STRUCTURE, i));
    }
    let (text, after) = string(b, i)?;
    if held.contains_key(&text) {
        return Err(Refused { code: DUPLICATE, offset: after - 1 });
    }
    let colon = gap(b, after);
    if colon >= b.len() || b[colon] != b':' {
        return Err(at(b, STRUCTURE, colon));
    }
    Ok((text, gap(b, colon + 1)))
}

/// An object or an array that is open, and what it holds so far.
enum Open {
    Obj(BTreeMap<String, Json>, String), // the members so far, and the name whose value is being read
    Arr(Vec<Json>),
}

/// One object starting at byte 0: the object and the index after it.
fn root(b: &[u8]) -> Result<(Json, usize), Refused> {
    let n = b.len();
    if n == 0 || b[0] != b'{' {
        return Err(at(b, STRUCTURE, 0));
    }
    let mut open: Vec<Open> = Vec::new();
    let mut i = 0;
    loop {
        // a value begins at i
        if i >= n {
            return Err(at(b, TRUNCATED, n));
        }
        let mut done = match b[i] {
            b'{' => {
                if open.len() >= DEPTH_MAX {
                    return Err(Refused { code: DEPTH, offset: i });
                }
                i = gap(b, i + 1);
                if i < n && b[i] == b'}' {
                    i += 1;
                    Json::Obj(BTreeMap::new())
                } else {
                    let held = BTreeMap::new();
                    let (first, value_at) = name(b, i, &held)?;
                    open.push(Open::Obj(held, first));
                    i = value_at;
                    continue;
                }
            }
            b'[' => {
                if open.len() >= DEPTH_MAX {
                    return Err(Refused { code: DEPTH, offset: i });
                }
                i = gap(b, i + 1);
                if i < n && b[i] == b']' {
                    i += 1;
                    Json::Arr(Vec::new())
                } else {
                    open.push(Open::Arr(Vec::new()));
                    continue;
                }
            }
            b'"' => {
                let (text, after) = string(b, i)?;
                i = after;
                Json::Str(text)
            }
            b'-' | b'0'..=b'9' => {
                let (value, after) = integer(b, i)?;
                i = after;
                Json::Num(value)
            }
            b't' => {
                i = literal(b, i, b"true")?;
                Json::Bool(true)
            }
            b'f' => {
                i = literal(b, i, b"false")?;
                Json::Bool(false)
            }
            b'n' => {
                i = literal(b, i, b"null")?;
                Json::Null
            }
            _ => return Err(Refused { code: STRUCTURE, offset: i }),
        };
        // a value ended before i: it goes into what is open, which may close in turn
        loop {
            match open.pop() {
                None => return Ok((done, i)),
                Some(Open::Obj(mut held, key)) => {
                    held.insert(key, done);
                    i = gap(b, i);
                    if i >= n {
                        return Err(at(b, TRUNCATED, n));
                    }
                    if b[i] == b',' {
                        let (next, value_at) = name(b, gap(b, i + 1), &held)?;
                        open.push(Open::Obj(held, next));
                        i = value_at;
                        break;
                    }
                    if b[i] != b'}' {
                        return Err(Refused { code: STRUCTURE, offset: i });
                    }
                    i += 1;
                    done = Json::Obj(held);
                }
                Some(Open::Arr(mut items)) => {
                    items.push(done);
                    i = gap(b, i);
                    if i >= n {
                        return Err(at(b, TRUNCATED, n));
                    }
                    if b[i] == b',' {
                        open.push(Open::Arr(items));
                        i = gap(b, i + 1);
                        break;
                    }
                    if b[i] != b']' {
                        return Err(Refused { code: STRUCTURE, offset: i });
                    }
                    i += 1;
                    done = Json::Arr(items);
                }
            }
        }
    }
}

/// Read a document: one object, then exactly one LF.
pub fn read_document(b: &[u8]) -> Result<Json, Refused> {
    let (value, i) = root(b)?;
    if i >= b.len() {
        return Err(at(b, TRUNCATED, b.len()));
    }
    if b[i] != 0x0a {
        return Err(Refused { code: TRAILING, offset: i });
    }
    if i + 1 != b.len() {
        return Err(Refused { code: TRAILING, offset: i + 1 });
    }
    Ok(value)
}

/// Read a payload: one object and nothing else.
pub fn read_payload(b: &[u8]) -> Result<Json, Refused> {
    let (value, i) = root(b)?;
    if i != b.len() {
        return Err(Refused { code: TRAILING, offset: i });
    }
    Ok(value)
}

/// The writers' check: these bytes are a document of the language, or the writer writes nothing.
pub fn check_document(b: &[u8]) -> Result<(), Refused> {
    read_document(b).map(|_| ())
}

/// The writers' check for a payload.
pub fn check_payload(b: &[u8]) -> Result<(), Refused> {
    read_payload(b).map(|_| ())
}

/// The one spelling of a string, quotes included: so every string has one byte form.
pub fn spell(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}
