// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/director/conform.rs — DIRECTOR-0's second implementation, held to the shared conformance vectors.
//
//     rustc -O art/director/conform.rs -o art/build/conform
//     art/build/conform art/director/vectors.json
//
// std-only Rust. It reads vectors.json with its own JSON reader, implements the canonical form (VERDANDI-CANON 0),
// the intent's validation, the head, the material digest, the address patterns and check_scope from their written
// rules (art/director/intent.py and scope.py describe them), and compares what it computes with every expected
// output: the verdict object field by field AND its canonical bytes, byte for byte. It never runs or imports the
// Python reference. The same author wrote both, so agreement shows the rules are written down completely enough
// to be implemented twice, not that either is right: the vectors are the contract.

use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs;

// ------------------------------------------------------------------------------------------------ sha-256
fn sha256(data: &[u8]) -> String {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
        0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
        0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
        0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ];
    let mut h: [u32; 8] = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    let mut msg = data.to_vec();
    let bits = (data.len() as u64).wrapping_mul(8);
    msg.push(0x80);
    while msg.len() % 64 != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bits.to_be_bytes());
    for chunk in msg.chunks(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([chunk[4 * i], chunk[4 * i + 1], chunk[4 * i + 2], chunk[4 * i + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }
        let mut a = h;
        for i in 0..64 {
            let s1 = a[4].rotate_right(6) ^ a[4].rotate_right(11) ^ a[4].rotate_right(25);
            let ch = (a[4] & a[5]) ^ (!a[4] & a[6]);
            let t1 = a[7].wrapping_add(s1).wrapping_add(ch).wrapping_add(K[i]).wrapping_add(w[i]);
            let s0 = a[0].rotate_right(2) ^ a[0].rotate_right(13) ^ a[0].rotate_right(22);
            let maj = (a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]);
            let t2 = s0.wrapping_add(maj);
            a = [t1.wrapping_add(t2), a[0], a[1], a[2], a[3].wrapping_add(t1), a[4], a[5], a[6]];
        }
        for i in 0..8 {
            h[i] = h[i].wrapping_add(a[i]);
        }
    }
    h.iter().map(|x| format!("{:08x}", x)).collect()
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len() / 2).map(|i| u8::from_str_radix(&s[2 * i..2 * i + 2], 16).unwrap()).collect()
}

// ------------------------------------------------------------------------------------------------ JSON values
#[derive(Clone, Debug)]
enum V {
    Null,
    Bool(bool),
    Num(f64),
    Str(String),
    Arr(Vec<V>),
    Obj(Vec<(String, V)>),
}

impl PartialEq for V {
    // value equality as the protocol uses it: numbers by value, objects as maps (member order does not matter)
    fn eq(&self, o: &V) -> bool {
        match (self, o) {
            (V::Null, V::Null) => true,
            (V::Bool(a), V::Bool(b)) => a == b,
            (V::Num(a), V::Num(b)) => a == b,
            (V::Str(a), V::Str(b)) => a == b,
            (V::Arr(a), V::Arr(b)) => a.len() == b.len() && a.iter().zip(b).all(|(x, y)| x == y),
            (V::Obj(a), V::Obj(b)) => a.len() == b.len() && a.iter().all(|(k, v)| b.iter().any(|(k2, v2)| k == k2 && v == v2)),
            _ => false,
        }
    }
}

impl V {
    fn get(&self, k: &str) -> Option<&V> {
        match self {
            V::Obj(m) => m.iter().rev().find(|(kk, _)| kk == k).map(|(_, v)| v),
            _ => None,
        }
    }
    fn g(&self, k: &str) -> &V {
        self.get(k).unwrap_or_else(|| panic!("no member {}", k))
    }
    fn s(&self) -> &str {
        match self {
            V::Str(s) => s,
            _ => panic!("not a string: {:?}", self),
        }
    }
    fn n(&self) -> f64 {
        match self {
            V::Num(n) => *n,
            _ => panic!("not a number: {:?}", self),
        }
    }
    fn a(&self) -> &Vec<V> {
        match self {
            V::Arr(a) => a,
            _ => panic!("not an array: {:?}", self),
        }
    }
    fn o(&self) -> &Vec<(String, V)> {
        match self {
            V::Obj(o) => o,
            _ => panic!("not an object: {:?}", self),
        }
    }
    fn b(&self) -> bool {
        match self {
            V::Bool(b) => *b,
            _ => panic!("not a boolean"),
        }
    }
    fn keys(&self) -> Vec<String> {
        self.o().iter().map(|(k, _)| k.clone()).collect()
    }
}

fn st(s: &str) -> V {
    V::Str(s.to_string())
}

fn strs(v: &[String]) -> V {
    V::Arr(v.iter().map(|s| st(s)).collect())
}

// ------------------------------------------------------------------------------------------------ JSON reader
struct P<'a> {
    b: &'a [u8],
    i: usize,
    strict: bool, // the canonical reader: numbers, null, bad and duplicate keys are refusals
}

type R<T> = Result<T, &'static str>;

impl<'a> P<'a> {
    fn ws(&mut self) {
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\t' | b'\n' | b'\r') {
            self.i += 1;
        }
    }
    fn value(&mut self) -> R<V> {
        self.ws();
        if self.i >= self.b.len() {
            return Err("INTENT-NOT-JSON");
        }
        match self.b[self.i] {
            b'{' => self.object(),
            b'[' => self.array(),
            b'"' => Ok(V::Str(self.string()?)),
            b't' => self.lit("true", V::Bool(true)),
            b'f' => self.lit("false", V::Bool(false)),
            b'n' => {
                let v = self.lit("null", V::Null)?;
                if self.strict {
                    return Err("INTENT-NULL");
                }
                Ok(v)
            }
            b'-' | b'0'..=b'9' => {
                let n = self.number()?;
                if self.strict {
                    return Err("INTENT-NUMBER");
                }
                Ok(n)
            }
            _ => Err("INTENT-NOT-JSON"),
        }
    }
    fn lit(&mut self, w: &str, v: V) -> R<V> {
        if self.b[self.i..].starts_with(w.as_bytes()) {
            self.i += w.len();
            Ok(v)
        } else {
            Err("INTENT-NOT-JSON")
        }
    }
    fn number(&mut self) -> R<V> {
        let s = self.i;
        if self.b[self.i] == b'-' {
            self.i += 1;
        }
        let digits = |p: &mut P| {
            let s = p.i;
            while p.i < p.b.len() && p.b[p.i].is_ascii_digit() {
                p.i += 1;
            }
            p.i > s
        };
        if !digits(self) {
            return Err("INTENT-NOT-JSON");
        }
        if self.i < self.b.len() && self.b[self.i] == b'.' {
            self.i += 1;
            if !digits(self) {
                return Err("INTENT-NOT-JSON");
            }
        }
        if self.i < self.b.len() && (self.b[self.i] == b'e' || self.b[self.i] == b'E') {
            self.i += 1;
            if self.i < self.b.len() && (self.b[self.i] == b'+' || self.b[self.i] == b'-') {
                self.i += 1;
            }
            if !digits(self) {
                return Err("INTENT-NOT-JSON");
            }
        }
        let t = std::str::from_utf8(&self.b[s..self.i]).unwrap();
        t.parse::<f64>().map(V::Num).map_err(|_| "INTENT-NOT-JSON")
    }
    fn hex4(&mut self) -> R<u32> {
        if self.i + 4 > self.b.len() {
            return Err("INTENT-NOT-JSON");
        }
        let t = std::str::from_utf8(&self.b[self.i..self.i + 4]).map_err(|_| "INTENT-NOT-JSON")?;
        let v = u32::from_str_radix(t, 16).map_err(|_| "INTENT-NOT-JSON")?;
        self.i += 4;
        Ok(v)
    }
    fn string(&mut self) -> R<String> {
        self.i += 1;
        let mut out = String::new();
        let mut raw: Vec<u8> = Vec::new();
        loop {
            if self.i >= self.b.len() {
                return Err("INTENT-NOT-JSON");
            }
            let c = self.b[self.i];
            if c == b'"' {
                self.i += 1;
                break;
            }
            if c < 0x20 {
                return Err("INTENT-NOT-JSON");
            }
            if c == b'\\' {
                if !raw.is_empty() {
                    out.push_str(std::str::from_utf8(&raw).map_err(|_| "INTENT-NOT-JSON")?);
                    raw.clear();
                }
                self.i += 1;
                if self.i >= self.b.len() {
                    return Err("INTENT-NOT-JSON");
                }
                let e = self.b[self.i];
                self.i += 1;
                match e {
                    b'"' => out.push('"'),
                    b'\\' => out.push('\\'),
                    b'/' => out.push('/'),
                    b'b' => out.push('\u{8}'),
                    b'f' => out.push('\u{c}'),
                    b'n' => out.push('\n'),
                    b'r' => out.push('\r'),
                    b't' => out.push('\t'),
                    b'u' => {
                        let u = self.hex4()?;
                        if (0xD800..0xDC00).contains(&u) {
                            if self.b[self.i..].starts_with(b"\\u") {
                                let save = self.i;
                                self.i += 2;
                                let l = self.hex4()?;
                                if (0xDC00..0xE000).contains(&l) {
                                    out.push(char::from_u32(0x10000 + ((u - 0xD800) << 10) + (l - 0xDC00)).unwrap());
                                    continue;
                                }
                                self.i = save;
                            }
                            return Err("INTENT-STRING");
                        }
                        if (0xDC00..0xE000).contains(&u) {
                            return Err("INTENT-STRING");
                        }
                        out.push(char::from_u32(u).unwrap());
                    }
                    _ => return Err("INTENT-NOT-JSON"),
                }
                continue;
            }
            raw.push(c);
            self.i += 1;
        }
        if !raw.is_empty() {
            out.push_str(std::str::from_utf8(&raw).map_err(|_| "INTENT-NOT-JSON")?);
        }
        Ok(out)
    }
    fn array(&mut self) -> R<V> {
        self.i += 1;
        let mut out = Vec::new();
        self.ws();
        if self.i < self.b.len() && self.b[self.i] == b']' {
            self.i += 1;
            return Ok(V::Arr(out));
        }
        loop {
            out.push(self.value()?);
            self.ws();
            if self.i >= self.b.len() {
                return Err("INTENT-NOT-JSON");
            }
            match self.b[self.i] {
                b',' => self.i += 1,
                b']' => {
                    self.i += 1;
                    return Ok(V::Arr(out));
                }
                _ => return Err("INTENT-NOT-JSON"),
            }
        }
    }
    fn object(&mut self) -> R<V> {
        self.i += 1;
        let mut out: Vec<(String, V)> = Vec::new();
        self.ws();
        if self.i < self.b.len() && self.b[self.i] == b'}' {
            self.i += 1;
            return Ok(V::Obj(out));
        }
        loop {
            self.ws();
            if self.i >= self.b.len() || self.b[self.i] != b'"' {
                return Err("INTENT-NOT-JSON");
            }
            let k = self.string()?;
            self.ws();
            if self.i >= self.b.len() || self.b[self.i] != b':' {
                return Err("INTENT-NOT-JSON");
            }
            self.i += 1;
            let v = self.value()?;
            out.push((k, v));
            self.ws();
            if self.i >= self.b.len() {
                return Err("INTENT-NOT-JSON");
            }
            match self.b[self.i] {
                b',' => self.i += 1,
                b'}' => {
                    self.i += 1;
                    break;
                }
                _ => return Err("INTENT-NOT-JSON"),
            }
        }
        if self.strict {
            let mut seen = BTreeSet::new();
            for (k, _) in &out {
                if !key_ok(k) {
                    return Err("INTENT-KEY");
                }
                if !seen.insert(k.clone()) {
                    return Err("INTENT-DUPLICATE-KEY");
                }
            }
        }
        Ok(V::Obj(out))
    }
}

fn parse_any(b: &[u8]) -> V {
    let mut p = P { b, i: 0, strict: false };
    let v = p.value().expect("vectors.json is JSON");
    v
}

fn key_ok(k: &str) -> bool {
    let b = k.as_bytes();
    !b.is_empty() && b[0].is_ascii_lowercase() && b.iter().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || *c == b'_')
}

// ------------------------------------------------------------------------------------------------ the canonical form
fn esc(s: &str, out: &mut String) -> R<()> {
    out.push('"');
    for ch in s.chars() {
        let o = ch as u32;
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{8}' => out.push_str("\\b"),
            '\t' => out.push_str("\\t"),
            '\n' => out.push_str("\\n"),
            '\u{c}' => out.push_str("\\f"),
            '\r' => out.push_str("\\r"),
            _ if o < 0x20 || o == 0x7f => out.push_str(&format!("\\u{:04x}", o)),
            _ if o <= 0x7e => out.push(ch),
            _ if o <= 0xffff => out.push_str(&format!("\\u{:04x}", o)),
            _ => {
                let v = o - 0x10000;
                out.push_str(&format!("\\u{:04x}\\u{:04x}", 0xD800 + (v >> 10), 0xDC00 + (v & 0x3ff)));
            }
        }
    }
    out.push('"');
    Ok(())
}

fn dumps(v: &V) -> R<Vec<u8>> {
    fn w(v: &V, out: &mut String) -> R<()> {
        match v {
            V::Bool(true) => out.push_str("true"),
            V::Bool(false) => out.push_str("false"),
            V::Str(s) => esc(s, out)?,
            V::Arr(a) => {
                out.push('[');
                for (i, e) in a.iter().enumerate() {
                    if i > 0 {
                        out.push(',');
                    }
                    w(e, out)?;
                }
                out.push(']');
            }
            V::Obj(m) => {
                for (k, _) in m {
                    if !key_ok(k) {
                        return Err("INTENT-KEY");
                    }
                }
                let mut keys: Vec<&(String, V)> = m.iter().collect();
                keys.sort_by(|a, b| a.0.as_bytes().cmp(b.0.as_bytes()));
                out.push('{');
                for (i, (k, e)) in keys.iter().map(|p| (&p.0, &p.1)).enumerate() {
                    if i > 0 {
                        out.push(',');
                    }
                    esc(k, out)?;
                    out.push(':');
                    w(e, out)?;
                }
                out.push('}');
            }
            V::Null => return Err("INTENT-NULL"),
            V::Num(_) => return Err("INTENT-TYPE"),
        }
        Ok(())
    }
    let mut s = String::new();
    w(v, &mut s)?;
    Ok(s.into_bytes())
}

fn loads(b: &[u8]) -> R<V> {
    if b.iter().any(|c| *c > 0x7f) {
        return Err("INTENT-BYTES");
    }
    let mut p = P { b, i: 0, strict: true };
    let v = p.value()?;
    p.ws();
    if p.i != b.len() {
        return Err("INTENT-NOT-JSON");
    }
    if dumps(&v)? != b {
        return Err("INTENT-NONCANONICAL");
    }
    Ok(v)
}

fn is_hex64(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn validate(d: &V) -> R<()> {
    let m = match d {
        V::Obj(m) => m,
        _ => return Err("INTENT-FIELD"),
    };
    let _ = m;
    if d.get("format") != Some(&st("VERDANDI-INTENT")) {
        return Err("INTENT-FORMAT");
    }
    if d.get("version") != Some(&st("0")) {
        return Err("INTENT-VERSION");
    }
    let req: BTreeSet<&str> = ["format", "version", "brief", "prompt", "candidate", "rationale", "base", "scope", "revision", "layout"].iter().cloned().collect();
    let have: BTreeSet<String> = d.keys().into_iter().collect();
    if have.len() != req.len() || !req.iter().all(|k| have.contains(*k)) {
        return Err("INTENT-FIELD");
    }
    for k in ["brief", "prompt", "candidate", "rationale"] {
        match d.g(k) {
            V::Str(s) if !s.trim().is_empty() => {}
            _ => return Err("INTENT-FIELD"),
        }
    }
    let b = d.g("base");
    match b {
        V::Obj(bm) => {
            let bk: BTreeSet<&str> = bm.iter().map(|(k, _)| k.as_str()).collect();
            let want: BTreeSet<&str> = ["art_sha256", "world_sha256", "exporter_sha256"].iter().cloned().collect();
            if bk != want || bm.len() != 3 {
                return Err("INTENT-FIELD");
            }
            for (_, v) in bm {
                match v {
                    V::Str(s) if is_hex64(s) => {}
                    _ => return Err("INTENT-FIELD"),
                }
            }
        }
        _ => return Err("INTENT-FIELD"),
    }
    match d.g("scope") {
        V::Arr(a) if !a.is_empty() && a.iter().all(|p| matches!(p, V::Str(s) if !s.is_empty())) => {}
        _ => return Err("INTENT-FIELD"),
    }
    let (rev, lay) = match (d.g("revision"), d.g("layout")) {
        (V::Arr(r), V::Arr(l)) if !(r.is_empty() && l.is_empty()) => (r, l),
        _ => return Err("INTENT-FIELD"),
    };
    for ln in lay {
        match ln {
            V::Str(s) if !s.trim().is_empty() && !s.contains('\n') && !s.trim_start().starts_with('#')
                && ["open", "close", "room", "entrance", "paint"].contains(&s.split_whitespace().next().unwrap_or("")) => {}
            _ => return Err("INTENT-LAYOUT"),
        }
    }
    for ln in rev {
        match ln {
            V::Str(s) if (s.starts_with("= ") || s.starts_with("+ ") || s.starts_with("- ")) && !s.contains('\n') && !s.contains('#') => {}
            _ => return Err("INTENT-REVISION"),
        }
    }
    Ok(())
}

fn head(parts: &V) -> String {
    let o = V::Obj(["art_sha256", "exporter_sha256", "world_sha256"].iter().map(|k| (k.to_string(), parts.g(k).clone())).collect());
    sha256(&dumps(&o).unwrap())
}

// ------------------------------------------------------------------------------------------------ materials, patterns
fn rgb(v: &V) -> String {
    v.a().iter().map(|x| format!("{}", x.n() as i64)).collect::<Vec<_>>().join(",")
}

fn material_record(m: &V) -> V {
    let mut o = vec![
        ("base".to_string(), V::Str(rgb(m.g("base")))),
        ("roughness".to_string(), V::Str(format!("{:.4}", m.g("roughness").n()))),
        ("metallic".to_string(), V::Str(format!("{:.4}", m.g("metallic").n()))),
        ("emissive".to_string(), V::Str(rgb(m.g("emissive")))),
        ("emissive_strength".to_string(), V::Str(format!("{:.4}", m.g("emissive_strength").n()))),
    ];
    if let Some(p) = m.get("parent") {
        o.push(("parent".to_string(), p.clone()));
    }
    V::Obj(o)
}

fn material_digest(m: &V) -> String {
    sha256(&dumps(&material_record(m)).unwrap())
}

const NAMESPACES: [&str; 8] = ["play", "surface", "material", "env", "asset", "view", "layout", "region"];

fn matches(pattern: &str, address: &str) -> bool {
    let ps: Vec<&str> = pattern.split('/').collect();
    let xs: Vec<&str> = address.split('/').collect();
    if (ps[0] == "*" || ps[0] == "**") && NAMESPACES.contains(&xs[0]) {
        return false;
    }
    fn m(ps: &[&str], xs: &[&str], i: usize, j: usize) -> bool {
        if i == ps.len() {
            return j == xs.len();
        }
        if ps[i] == "**" {
            return (j..=xs.len()).any(|k| m(ps, xs, i + 1, k));
        }
        if j == xs.len() {
            return false;
        }
        (ps[i] == "*" || ps[i] == xs[j]) && m(ps, xs, i + 1, j + 1)
    }
    m(&ps, &xs, 0, 0)
}

// ------------------------------------------------------------------------------------------------ check_scope
struct Piece {
    address: String,
    material: String,
    play: Option<String>,
    shape: V,
    light: Option<V>,
}

fn without(v: &V, drop: &[&str]) -> V {
    V::Obj(v.o().iter().filter(|(k, _)| !drop.contains(&k.as_str())).cloned().collect())
}

fn pieces(scene: &V) -> BTreeMap<String, Piece> {
    let mut out = BTreeMap::new();
    if let Some(V::Arr(cs)) = scene.get("collision") {
        for b in cs {
            let id = b.g("id").s().to_string();
            let kind = b.g("kind").s().to_string();
            out.insert(format!("play/{}", id), Piece {
                address: format!("play/{}/{}", kind, id),
                material: b.g("material").s().to_string(),
                play: Some(kind.clone()),
                shape: V::Obj(vec![("kind".into(), b.g("kind").clone()), ("cells".into(), b.g("cells").clone()), ("box".into(), b.g("box").clone())]),
                light: None,
            });
        }
    }
    let region_of = |r: &str| if r == "*" { "city".to_string() } else { r.to_string() };
    if let Some(V::Arr(vs)) = scene.get("visuals") {
        for v in vs {
            let id = v.g("id").s().to_string();
            let (kind, place) = id.split_once(':').unwrap();
            out.insert(id.clone(), Piece {
                address: format!("{}/{}/{}", region_of(v.g("region").s()), kind, place),
                material: v.g("material").s().to_string(),
                play: None,
                shape: without(v, &["id", "by", "material"]),
                light: None,
            });
        }
    }
    if let Some(V::Arr(ls)) = scene.get("lights") {
        for l in ls {
            let id = l.g("id").s().to_string();
            if !out.contains_key(&id) {
                let (kind, place) = id.split_once(':').unwrap();
                out.insert(id.clone(), Piece {
                    address: format!("{}/{}/{}", region_of(l.g("region").s()), kind, place),
                    material: String::new(),
                    play: None,
                    shape: V::Obj(vec![]),
                    light: None,
                });
            }
            out.get_mut(&id).unwrap().light = Some(without(l, &["id", "by"]));
        }
    }
    out
}

fn light_view(p: &Piece, mats: &V) -> Option<V> {
    let l = p.light.as_ref()?;
    if let Some(m) = mats.get(&p.material) {
        let col = l.get("color").cloned().unwrap_or(V::Arr(vec![]));
        let cd = l.get("candela").map(|c| c.n()).unwrap_or(-1.0);
        if col == *m.g("emissive") && cd == m.g("emissive_strength").n() {
            return Some(without(l, &["color", "candela"]));
        }
    }
    Some(l.clone())
}

fn changed_materials(base: &V, cand: &V) -> (BTreeSet<String>, BTreeSet<&'static str>) {
    let mut codes = BTreeSet::new();
    for mats in [base, cand] {
        for (_n, m) in mats.o() {
            if let Some(p) = m.get("parent") {
                if mats.get(p.s()).is_none() {
                    codes.insert("GRAPH-DANGLING");
                }
            }
        }
        for (name, _m) in mats.o() {
            let mut seen = BTreeSet::new();
            let mut at = Some(name.clone());
            while let Some(a) = at.clone() {
                let m = match mats.get(&a) {
                    Some(m) => m,
                    None => break,
                };
                if !seen.insert(a.clone()) {
                    codes.insert("GRAPH-CYCLE");
                    break;
                }
                at = m.get("parent").map(|p| p.s().to_string());
            }
        }
    }
    let names: BTreeSet<String> = base.keys().into_iter().chain(cand.keys()).collect();
    let direct: BTreeSet<String> = names.into_iter().filter(|n| match (base.get(n), cand.get(n)) {
        (Some(a), Some(b)) => material_digest(a) != material_digest(b),
        _ => true,
    }).collect();
    if codes.contains("GRAPH-CYCLE") {
        return (direct, codes);
    }
    let mut out = direct;
    loop {
        let mut grew = false;
        for (n, m) in cand.o() {
            if !out.contains(n) {
                if let Some(p) = m.get("parent") {
                    if out.contains(p.s()) {
                        out.insert(n.clone());
                        grew = true;
                    }
                }
            }
        }
        if !grew {
            break;
        }
    }
    (out, codes)
}

fn check_scope(it: &V, base: &V, cand: &V, current: &V, checks: &V) -> V {
    let mut codes: BTreeSet<&str> = BTreeSet::new();
    let patterns: Vec<String> = it.g("scope").a().iter().map(|p| p.s().to_string()).collect();
    let empty = V::Obj(vec![]);
    let regions = base.get("regions").unwrap_or(&empty);
    for p in &patterns {
        let segs: Vec<&str> = p.split('/').collect();
        if segs.iter().any(|s| s.is_empty()) {
            codes.insert("SCOPE-PATTERN");
        } else if segs[0] == "play" {
            codes.insert("SCOPE-RESERVED-GRANT");
        } else if segs[0] == "layout" && (segs.len() != 2 || regions.get(segs[1]).is_none()) {
            codes.insert("SCOPE-PATTERN");
        } else if segs[0] == "surface" && segs.len() != 2 {
            codes.insert("SCOPE-PATTERN");
        }
    }
    let mut cells: Vec<String> = Vec::new();
    let (bt, ct) = (base.g("tops").a(), cand.g("tops").a());
    if base.g("grid") != cand.g("grid") || base.g("spawns") != cand.g("spawns") || bt.len() != ct.len() {
        codes.insert("SCOPE-PLAY");
    } else {
        let w = base.g("grid").g("w").n() as usize;
        let mut zx: Vec<(usize, usize)> = (0..bt.len()).filter(|k| bt[*k] != ct[*k]).map(|k| (k / w, k % w)).collect();
        zx.sort();
        cells = zx.iter().map(|(z, x)| format!("{},{}", x, z)).collect();
    }
    let grants: Vec<Vec<i64>> = patterns.iter().filter(|p| p.starts_with("layout/")).filter_map(|p| {
        let segs: Vec<&str> = p.split('/').collect();
        if segs.len() >= 2 { regions.get(segs[1]).map(|r| r.a().iter().map(|x| x.n() as i64).collect()) } else { None }
    }).collect();
    let in_r = |c: &str, r: &[i64]| {
        let (x, z) = c.split_once(',').unwrap();
        let (x, z): (i64, i64) = (x.parse().unwrap(), z.parse().unwrap());
        r[0] <= x && x <= r[2] && r[1] <= z && z <= r[3]
    };
    let inside = |c: &str| grants.iter().any(|r| in_r(c, r));
    if !cells.is_empty() && !cells.iter().all(|c| inside(c)) {
        codes.insert("SCOPE-LAYOUT");
    }
    let (bm, cm) = (base.get("materials").unwrap_or(&empty), cand.get("materials").unwrap_or(&empty));
    let (mchanged, gcodes) = changed_materials(bm, cm);
    codes.extend(gcodes);
    let (p0, p1) = (pieces(base), pieces(cand));
    for (pp, mats) in [(&p0, bm), (&p1, cm)] {
        if pp.values().any(|p| !p.material.is_empty() && mats.get(&p.material).is_none()) {
            codes.insert("GRAPH-DANGLING");
        }
    }
    let mut realized: BTreeSet<String> = BTreeSet::new();
    let mut affected: BTreeSet<String> = BTreeSet::new();
    let mut play_shape: BTreeSet<String> = BTreeSet::new();
    let mut play_look: BTreeMap<String, String> = BTreeMap::new();
    let keys: BTreeSet<&String> = p0.keys().chain(p1.keys()).collect();
    for key in keys {
        let (a, b) = (p0.get(key), p1.get(key));
        let differs = match (a, b) {
            (Some(a), Some(b)) => a.shape != b.shape || a.material != b.material || light_view(a, bm) != light_view(b, cm),
            _ => true,
        };
        if differs {
            let shape_changed = match (a, b) {
                (Some(a), Some(b)) => a.shape != b.shape,
                _ => true,
            };
            for p in [a, b].iter().flatten() {
                realized.insert(p.address.clone());
                if let Some(k) = &p.play {
                    if shape_changed {
                        play_shape.insert(p.address.clone());
                    } else {
                        play_look.insert(p.address.clone(), k.clone());
                    }
                }
            }
        } else if let Some(b) = b {
            if mchanged.contains(&b.material) {
                affected.insert(b.address.clone());
                if let Some(k) = &b.play {
                    play_look.insert(b.address.clone(), k.clone());
                }
            }
        }
    }
    for n in &mchanged {
        realized.insert(format!("material/{}", n));
    }
    let env = |s: &V| {
        let mut m: Vec<(String, V)> = s.get("environment").map(|e| e.o().clone()).unwrap_or_default();
        m.retain(|(k, _)| k != "title");
        m.push(("title".into(), s.get("title").cloned().unwrap_or(st(""))));
        V::Obj(m)
    };
    let (e0, e1) = (env(base), env(cand));
    let ek: BTreeSet<String> = e0.keys().into_iter().chain(e1.keys()).collect();
    for k in ek {
        if e0.get(&k) != e1.get(&k) {
            realized.insert(format!("env/{}", k));
        }
    }
    for (fam, ns) in [("views", "view"), ("assets", "asset"), ("regions", "region")] {
        let (x0, x1) = (base.get(fam).unwrap_or(&empty), cand.get(fam).unwrap_or(&empty));
        let fk: BTreeSet<String> = x0.keys().into_iter().chain(x1.keys()).collect();
        for k in fk {
            if x0.get(&k) != x1.get(&k) {
                realized.insert(format!("{}/{}", ns, k));
            }
        }
    }
    if !play_shape.is_empty() && cells.is_empty() {
        codes.insert("SCOPE-PLAY");
    }
    let surfaces: BTreeSet<String> = patterns.iter().filter(|p| p.starts_with("surface/")).map(|p| p["surface/".len()..].to_string()).collect();
    let plain: Vec<&String> = patterns.iter().filter(|p| !p.starts_with("layout/") && !p.starts_with("surface/")).collect();
    let mut used: BTreeSet<String> = BTreeSet::new();
    let mut unclaimed: Vec<String> = Vec::new();
    let all: BTreeSet<String> = realized.union(&affected).cloned().collect();
    for addr in &all {
        let ok = if play_shape.contains(addr) {
            let ok = !cells.is_empty() && !grants.is_empty() && cells.iter().all(|c| inside(c));
            if ok {
                for p in &patterns {
                    if p.starts_with("layout/") {
                        let segs: Vec<&str> = p.split('/').collect();
                        if let Some(r) = regions.get(segs[1]) {
                            let r: Vec<i64> = r.a().iter().map(|x| x.n() as i64).collect();
                            if cells.iter().any(|c| in_r(c, &r)) {
                                used.insert(p.clone());
                            }
                        } else if cells.iter().any(|c| inside(c)) {
                            used.insert(p.clone());
                        }
                    }
                }
            }
            ok
        } else if let Some(k) = play_look.get(addr) {
            if surfaces.contains(k) {
                used.insert(format!("surface/{}", k));
                true
            } else {
                false
            }
        } else {
            let hit: Vec<&String> = plain.iter().filter(|p| matches(p, addr)).cloned().collect();
            for h in &hit {
                used.insert((*h).clone());
            }
            !hit.is_empty()
        };
        if !ok {
            unclaimed.push(addr.clone());
        }
    }
    for p in &patterns {
        if p.starts_with("layout/") && !cells.is_empty() {
            let segs: Vec<&str> = p.split('/').collect();
            if let Some(r) = regions.get(segs[1]) {
                let r: Vec<i64> = r.a().iter().map(|x| x.n() as i64).collect();
                if cells.iter().any(|c| in_r(c, &r)) {
                    used.insert(p.clone());
                }
            }
        }
    }
    let pset: BTreeSet<String> = patterns.iter().cloned().collect();
    let phantom: Vec<String> = pset.difference(&used).cloned().collect();
    if !unclaimed.is_empty() {
        codes.insert("SCOPE-LEAK");
    }
    let mut failed: Vec<String> = checks.a().iter().filter(|c| !c.g("ok").b()).map(|c| c.g("name").s().to_string()).collect();
    failed.sort();
    if !failed.is_empty() {
        codes.insert("CHECK-FAILED");
    }
    let written = head(it.g("base"));
    let checked = head(current);
    if written != checked {
        codes.insert("HEAD-MOVED");
    }
    let refusing = ["SCOPE-RESERVED-GRANT", "SCOPE-PATTERN", "SCOPE-LAYOUT", "SCOPE-PLAY", "GRAPH-CYCLE", "GRAPH-DANGLING", "CHECK-FAILED"];
    let verdict = if codes.iter().any(|c| refusing.contains(c)) { "REFUSED" } else if codes.contains("SCOPE-LEAK") { "LEAKAGE" } else { "CLEAN" };
    let mut declared = patterns.clone();
    declared.sort();
    let sorted = |s: &BTreeSet<String>| s.iter().cloned().collect::<Vec<_>>();
    V::Obj(vec![
        ("protocol".into(), st("DIRECTOR-0")),
        ("version".into(), st("0")),
        ("verdict".into(), st(verdict)),
        ("codes".into(), V::Arr(codes.iter().map(|c| st(c)).collect())),
        ("intent_sha256".into(), st(&sha256(&dumps(it).unwrap()))),
        ("written_against".into(), st(&written)),
        ("checked_against".into(), st(&checked)),
        ("re_evaluated".into(), V::Bool(written != checked)),
        ("declared".into(), strs(&declared)),
        ("realized".into(), strs(&sorted(&realized))),
        ("affected".into(), strs(&sorted(&affected))),
        ("unclaimed".into(), strs(&unclaimed)),
        ("phantom".into(), strs(&phantom)),
        ("cells_changed".into(), strs(&cells)),
        ("materials_changed".into(), strs(&sorted(&mchanged))),
        ("failed_checks".into(), strs(&failed)),
    ])
}

// ------------------------------------------------------------------------------------------------ the runner
fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| "art/director/vectors.json".to_string());
    let text = fs::read(&path).expect("read the vectors");
    let vv = parse_any(&text);
    let (mut n, mut bad) = (0usize, Vec::<String>::new());
    let mut judge = |name: String, ok: bool| {
        n += 1;
        if !ok {
            bad.push(name);
        }
    };
    for c in vv.g("dumps").a() {
        let e = c.g("expect");
        let ok = match dumps(c.g("value")) {
            Ok(b) => e.g("ok").b() && hex(&b) == e.g("hex").s() && sha256(&b) == e.g("sha256").s(),
            Err(code) => !e.g("ok").b() && code == e.g("code").s(),
        };
        judge(format!("dumps: {}", c.g("name").s()), ok);
    }
    for c in vv.g("loads").a() {
        let e = c.g("expect");
        let ok = match loads(&unhex(c.g("hex").s())) {
            Ok(v) => e.g("ok").b() && v == *e.g("value"),
            Err(code) => !e.g("ok").b() && code == e.g("code").s(),
        };
        judge(format!("loads: {}", c.g("name").s()), ok);
    }
    for c in vv.g("intents").a() {
        let e = c.g("expect");
        let b = unhex(c.g("hex").s());
        let ok = match loads(&b).and_then(|d| validate(&d)) {
            Ok(()) => e.g("ok").b() && sha256(&b) == e.g("sha256").s(),
            Err(code) => !e.g("ok").b() && code == e.g("code").s(),
        };
        judge(format!("intent: {}", c.g("name").s()), ok);
    }
    for c in vv.g("heads").a() {
        judge("head".into(), head(c.g("parts")) == c.g("expect").s());
    }
    for c in vv.g("materials").a() {
        let e = c.g("expect");
        let rec = dumps(&material_record(c.g("material"))).unwrap();
        judge("material".into(), hex(&rec) == e.g("record_hex").s() && material_digest(c.g("material")) == e.g("digest").s());
    }
    for c in vv.g("patterns").a() {
        judge(format!("pattern {} ~ {}", c.g("pattern").s(), c.g("address").s()), matches(c.g("pattern").s(), c.g("address").s()) == c.g("expect").b());
    }
    for c in vv.g("scope").a() {
        let v = check_scope(c.g("intent"), c.g("base"), c.g("candidate"), c.g("current"), c.g("checks"));
        let b = dumps(&v).unwrap();
        let e = c.g("expect");
        let same_obj = v == *e.g("verdict");
        let same_bytes = hex(&b) == e.g("hex").s() && sha256(&b) == e.g("sha256").s();
        if !(same_obj && same_bytes) {
            eprintln!("  {}: got {}", c.g("name").s(), String::from_utf8_lossy(&b));
        }
        judge(format!("scope: {} ({})", c.g("name").s(), v.g("verdict").s()), same_obj && same_bytes);
    }
    for b in &bad {
        println!("FAIL vector: {}", b);
    }
    println!("CONFORMANCE {} / {} reproduced by the second implementation (Rust, std only; verdicts and canonical bytes)", n - bad.len(), n);
    std::process::exit(if bad.is_empty() { 0 } else { 1 });
}
