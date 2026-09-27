// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/presentexact.rs — PRESENT-EXACT-0: which GDI call presents the certified picture 1:1, and proof that it does.
//
// PRESENTATION-CHOICE-0 (declared) fixed what the shell shows: the certified 1920x1080 composite, pixel for pixel, in a
// borderless window covering the 1920x1080 screen at (0,0). This court implements that target with two GDI calls, the
// call the only variable: StretchDIBits at 1:1 (destination = source) and SetDIBitsToDevice (no stretch path at all).
// Frames render through the adopted render-loop entry, `present::LoopRenderer`.
//
//   Witnesses first, outside every clock: the geometry is verified (client 1920x1080 at screen (0,0), the screen's
//   logical and physical size both 1920x1080). Then for every sealed frame and each call: the window is cleared to
//   white and the clear is read back (the readback must see it), the call presents the frame, and the COMPOSED SCREEN
//   under the window is read back and must equal the certified blit bytes, byte for byte. Clearing first means a call
//   that wrote nothing cannot pass on the previous call's pixels.
//
//   Then the court: the envelope render-start -> frame-ready (LoopRenderer render + blit + the call) for each call,
//   interleaved ABBA after 10 warm-up rounds, N samples per cell (default 1000), with the call interval (call start ->
//   frame-ready) and frame-ready -> composited beside. After the court the last frame is read back again under each
//   call. The rule is the sealer's; this file records and never reads it. The gate drives it over a mock surface.

use crate::latency1r::{percentiles, FrameInput, Surface};
use crate::mantle::{frame_digest, H, W};
use crate::present::{arm_composite, to_blit, Arm, LoopRenderer};
use crate::refusallog::V;

pub const CALLS: [&str; 2] = ["stretchdibits", "setdibitstodevice"];
pub const WARM_ROUNDS: usize = 10;
pub const DEFAULT_PER_CELL: usize = 1000;
pub const TAIL: usize = 12;

/// A surface that can switch the present call, clear its client area, read back the composed screen under it, and
/// report its geometry.
pub trait ExactSurface: Surface {
    /// 0 = StretchDIBits at 1:1, 1 = SetDIBitsToDevice.
    fn set_call(&mut self, call: usize);
    /// Fill the client area with white through a path that is neither call (so a no-op call cannot pass).
    fn clear(&mut self) -> bool;
    /// The composed screen under the client area, as 24-bit BGR top-down, W*H*3 bytes.
    fn readback(&mut self) -> Option<Vec<u8>>;
    /// (client w, client h, client origin x, y on the screen, screen logical w, h, screen physical w, h)
    fn geometry(&mut self) -> [i32; 8];
    /// REFUSAL-WHY-0: what lies above the window over a differing box, for a refusal's message. Explanatory only: it is
    /// called after a verdict is decided and never changes one. The default names nothing.
    fn attribute(&mut self, _bbox: [usize; 4]) -> String {
        String::new()
    }
}

pub struct Readback {
    pub frames: usize,
    pub checks: usize,
    pub bytes_compared: u64,
    pub mismatched_bytes: u64,
}

fn mismatches(a: &[u8], b: &[u8]) -> u64 {
    if a.len() != b.len() {
        return a.len().max(b.len()) as u64;
    }
    a.iter().zip(b.iter()).filter(|(x, y)| x != y).count() as u64
}

/// Where a read-back differs from what was expected, pixel by pixel: how many pixels, their bounding box, and the first
/// one's bytes (read, then wanted), so a refusal says whether it is a strip (a taskbar), a small box (a cursor), the
/// whole frame shifted by a little (a colour transform) or nothing at all (a readback that sees nothing).
pub fn describe(v: &[u8], want: &dyn Fn(usize) -> u8) -> String {
    if v.len() != W * H * 3 {
        return format!("the readback holds {} bytes, not {}", v.len(), W * H * 3);
    }
    let (mut n, mut x0, mut y0, mut x1, mut y1) = (0u64, W, H, 0usize, 0usize);
    let mut first: Option<(usize, usize, [u8; 3], [u8; 3])> = None;
    for p in 0..W * H {
        let i = p * 3;
        let got = [v[i], v[i + 1], v[i + 2]];
        let exp = [want(i), want(i + 1), want(i + 2)];
        if got != exp {
            let (x, y) = (p % W, p / W);
            n += 1;
            x0 = x0.min(x);
            y0 = y0.min(y);
            x1 = x1.max(x);
            y1 = y1.max(y);
            if first.is_none() {
                first = Some((x, y, got, exp));
            }
        }
    }
    match first {
        None => "0 pixels differ".to_string(),
        Some((x, y, g, e)) => format!("{} of {} pixels differ, box ({},{})-({},{}), first at ({},{}) read BGR {:?} want {:?}",
                                      n, W * H, x0, y0, x1, y1, x, y, g, e),
    }
}

/// The bounding box (x0, y0, x1, y1) of the pixels that differ from what was expected, if any do.
pub fn diff_bbox(v: &[u8], want: &dyn Fn(usize) -> u8) -> Option<[usize; 4]> {
    if v.len() != W * H * 3 {
        return Some([0, 0, W - 1, H - 1]);
    }
    let (mut x0, mut y0, mut x1, mut y1, mut any) = (W, H, 0usize, 0usize, false);
    for p in 0..W * H {
        let i = p * 3;
        if v[i] != want(i) || v[i + 1] != want(i + 1) || v[i + 2] != want(i + 2) {
            let (x, y) = (p % W, p / W);
            x0 = x0.min(x);
            y0 = y0.min(y);
            x1 = x1.max(x);
            y1 = y1.max(y);
            any = true;
        }
    }
    if any { Some([x0, y0, x1, y1]) } else { None }
}

/// REFUSAL-LOG-0: a court refusal as data — where on the path it came from (the attribution), a few facts (the context)
/// and its console message, unchanged. The court builds it and returns it; it writes nothing and prints nothing. Where
/// the refusal is emitted (the selftest in main.rs, the host window in win32.rs) it is logged through
/// `refusallog::refuse` and its message printed exactly as before.
pub struct Refused {
    pub attribution: &'static str,
    pub context: Vec<(&'static str, V)>,
    pub message: String,
}

fn refused(attribution: &'static str, context: Vec<(&'static str, V)>, message: String) -> Refused {
    Refused { attribution, context, message }
}

impl Refused {
    /// The log event and the message, for the caller that emits the refusal on `surface` ("mock" or "gdi").
    pub fn into_event(self, surface: &'static str) -> (crate::refusallog::Event, String) {
        let reason = crate::refusallog::code_of(&self.message);
        (crate::refusallog::Event { operation: "presentexact.court", surface, reason, attribution: self.attribution, context: self.context },
         self.message)
    }
}

fn at(what: &str, call: usize) -> Vec<(&'static str, V)> {
    vec![("what", V::S(what.to_string())), ("call", V::S(CALLS[call].to_string()))]
}

fn boxed(mut ctx: Vec<(&'static str, V)>, b: Option<[usize; 4]>) -> Vec<(&'static str, V)> {
    if let Some(b) = b {
        ctx.push(("box", V::S(format!("{},{},{},{}", b[0], b[1], b[2], b[3]))));
    }
    ctx
}

/// REFUSAL-WHY-0: a refusal's attribution suffix — decided afterwards, appended only.
fn why<S: ExactSurface>(s: &mut S, v: &[u8], want: &dyn Fn(usize) -> u8) -> String {
    match diff_bbox(v, want).map(|b| s.attribute(b)) {
        Some(w) if !w.is_empty() => format!("; {}", w),
        _ => String::new(),
    }
}

/// Clear, present `bgr` under `call`, read back; Err(reason) on any failure or mismatch.
fn witness_one<S: ExactSurface>(s: &mut S, call: usize, bgr: &[u8], rb: &mut Readback, what: &str) -> Result<(), Refused> {
    if !s.clear() {
        return Err(refused("surface.clear", at(what, call),
                           format!("PRESENTEXACT-READBACK: the window could not be cleared before {} under {}", what, CALLS[call])));
    }
    s.flush();
    s.flush();
    match s.readback() {
        Some(v) if v.len() == bgr.len() && v.iter().all(|&b| b == 0xFF) => {}
        Some(v) => {
            let who = why(s, &v, &|_| 0xFF);
            return Err(refused("clear.readback", boxed(at(what, call), diff_bbox(&v, &|_| 0xFF)),
                               format!("PRESENTEXACT-READBACK-STALE: the window cleared to white before {} under {} did not read back as white ({}{}); the readback does not see the window exactly",
                                       what, CALLS[call], describe(&v, &|_| 0xFF), who)));
        }
        None => return Err(refused("surface.readback", at(what, call), "PRESENTEXACT-READBACK: the screen could not be read back".to_string())),
    }
    s.set_call(call);
    if s.present(bgr).is_none() {
        return Err(refused("surface.present", at(what, call), format!("PRESENTEXACT-NO-PRESENT: {} failed on {}", CALLS[call], what)));
    }
    s.flush();
    let v = match s.readback() {
        Some(v) => v,
        None => return Err(refused("surface.readback", at(what, call), "PRESENTEXACT-READBACK: the screen could not be read back".to_string())),
    };
    let bad = mismatches(&v, bgr);
    rb.checks += 1;
    rb.bytes_compared += bgr.len() as u64;
    rb.mismatched_bytes += bad;
    if bad != 0 {
        let who = why(s, &v, &|i| bgr[i]);
        let mut ctx = at(what, call);
        ctx.push(("differing_bytes", V::N(bad)));
        return Err(refused("present.readback", boxed(ctx, diff_bbox(&v, &|i| bgr[i])),
                           format!("PRESENTEXACT-READBACK: the composed screen differs from the certified picture on {} under {} ({} of {} bytes; {}{})",
                                   what, CALLS[call], bad, bgr.len(), describe(&v, &|i| bgr[i]), who)));
    }
    Ok(())
}

pub struct Exact {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub geometry: [i32; 8],
    pub readback: Readback,
    pub render: [Vec<u64>; 2],
    pub call: [Vec<u64>; 2],
    pub present: [Vec<u64>; 2],
    pub renders: u64,
}

pub fn court<S: ExactSurface>(s: &mut S, inputs: &[FrameInput], per_cell: usize) -> Result<Exact, Refused> {
    if inputs.is_empty() || per_cell == 0 {
        return Err(refused("court.input", vec![("frames", V::N(inputs.len() as u64)), ("per_cell", V::N(per_cell as u64))],
                           "PRESENTEXACT-EMPTY: no sealed frames or no samples requested".to_string()));
    }
    // 1. the geometry: the whole certified frame, 1:1, at the screen's origin, on a 1920x1080 screen at 100%
    let _ = s.pump();
    let g = s.geometry();
    let want = [W as i32, H as i32, 0, 0, W as i32, H as i32, W as i32, H as i32];
    if g != want {
        return Err(refused("window.geometry", vec![("stage", V::S("before the witnesses".to_string())), ("geometry", V::S(format!("{:?}", g)))],
                           format!("PRESENTEXACT-GEOMETRY: client {}x{} at ({},{}), screen logical {}x{} physical {}x{}; the target is {}x{} at (0,0) on a {}x{} screen",
                                   g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], W, H, W, H)));
    }
    // 2. witnesses first — outside every clock: the fresh reference reproduces the sealed witness; the loop renderer
    //    reproduces the fresh bytes; each call's presented frame reads back from the composed screen byte for byte
    let mut lr = LoopRenderer::new();
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    let mut expected_bgr: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    let mut rb = Readback { frames: inputs.len(), checks: 0, bytes_compared: 0, mismatched_bytes: 0 };
    for (i, f) in inputs.iter().enumerate() {
        let (fr, comp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fr) != f.witness {
            return Err(refused("render.witness", vec![("frame", V::N(i as u64))],
                               format!("PRESENTEXACT-WITNESS: the production frame {} is not the sealed witness", i)));
        }
        let bgr = to_blit(&comp);
        lr.render(&f.scene);
        if lr.composite() != &comp[..] || lr.blit() != &bgr[..] {
            return Err(refused("render.loop", vec![("frame", V::N(i as u64))],
                               format!("PRESENTEXACT-REUSE: the loop renderer differs from the fresh path on frame {}", i)));
        }
        for call in 0..2 {
            if !s.pump() {
                return Err(refused("window.close", vec![("stage", V::S("witnesses".to_string())), ("frame", V::N(i as u64))],
                                   "PRESENTEXACT-CLOSED: the window closed during the witnesses; no record".to_string()));
            }
            witness_one(s, call, &bgr, &mut rb, &format!("sealed frame {}", i))?;
        }
        expected.push(comp);
        expected_bgr.push(bgr);
    }
    // 3. the refresh (context only)
    let freq = s.freq().max(1) as u128;
    let us = |d: i64| -> u64 { (d.max(0) as u128 * 1_000_000 / freq) as u64 };
    let mut idle: Vec<u64> = Vec::with_capacity(8);
    for _ in 0..8 {
        let a = s.ticks();
        s.flush();
        let b = s.ticks();
        idle.push(us(b - a));
    }
    idle.sort_unstable();
    let refresh_us = idle[idle.len() / 2];
    // 4. the court: the two calls ABBA across rounds; warm rounds discarded; only the call differs
    let mut render: [Vec<u64>; 2] = [Vec::with_capacity(per_cell), Vec::with_capacity(per_cell)];
    let mut callv: [Vec<u64>; 2] = [Vec::with_capacity(per_cell), Vec::with_capacity(per_cell)];
    let mut present: [Vec<u64>; 2] = [Vec::with_capacity(per_cell), Vec::with_capacity(per_cell)];
    let total_rounds = WARM_ROUNDS + per_cell;
    for round in 0..total_rounds {
        let k = round % inputs.len();
        let record = round >= WARM_ROUNDS;
        let order: [usize; 2] = if round % 2 == 0 { [0, 1] } else { [1, 0] };
        for &c in order.iter() {
            if !s.pump() {
                return Err(refused("window.close", vec![("stage", V::S("rounds".to_string())), ("round", V::N(round as u64 + 1))],
                                   format!("PRESENTEXACT-CLOSED: the window closed before the court finished (round {} of {}); no partial record",
                                           round + 1, total_rounds)));
            }
            s.set_call(c);
            s.flush(); // the locked phase origin
            let t0 = s.ticks();
            lr.render(&inputs[k].scene);
            let bgr = lr.blit();
            let tc = s.ticks();
            let presented = s.present(bgr);
            let (t1, t2) = match presented {
                Some(t) => t,
                None => return Err(refused("surface.present", vec![("stage", V::S("rounds".to_string())), ("call", V::S(CALLS[c].to_string()))],
                                           format!("PRESENTEXACT-NO-PRESENT: {} or the composition barrier failed", CALLS[c]))),
            };
            if lr.composite() != &expected[k][..] || lr.bgr() != &expected_bgr[k][..] {
                return Err(refused("render.drift", vec![("frame", V::N(k as u64)), ("call", V::S(CALLS[c].to_string()))],
                                   format!("PRESENTEXACT-DRIFT: a composite of frame {} drifted from its verified bytes", k)));
            }
            if record {
                render[c].push(us(t1 - t0));
                callv[c].push(us(t1 - tc));
                present[c].push(us(t2 - t1));
            }
        }
        if record {
            s.progress((round + 1 - WARM_ROUNDS) * 2, per_cell * 2);
        }
    }
    // 5. after the court: the last frame reads back again under each call
    let last = (total_rounds - 1) % inputs.len();
    for call in 0..2 {
        if !s.pump() {
            return Err(refused("window.close", vec![("stage", V::S("closing".to_string()))],
                               "PRESENTEXACT-CLOSED: the window closed during the closing readback; no record".to_string()));
        }
        witness_one(s, call, &expected_bgr[last], &mut rb, "the last frame after the court")?;
    }
    let g2 = s.geometry();
    if g2 != want {
        return Err(refused("window.geometry", vec![("stage", V::S("after the court".to_string())), ("geometry", V::S(format!("{:?}", g2)))],
                           "PRESENTEXACT-GEOMETRY: the geometry changed during the court".to_string()));
    }
    Ok(Exact { refresh_us, frames: inputs.len(), per_cell, geometry: g, readback: rb, render, call: callv, present, renders: lr.renders() })
}

fn pct_json(xs: &[u64]) -> String {
    let (p50, p95, p99, max) = percentiles(xs);
    format!("{{\"p50\":{},\"p95\":{},\"p99\":{},\"max\":{}}}", p50, p95, p99, max)
}

/// The TAIL largest samples, largest first (p99 at N = 1000 is the 11th largest, nearest rank).
pub fn tail(xs: &[u64]) -> Vec<u64> {
    let mut v = xs.to_vec();
    v.sort_unstable_by(|a, b| b.cmp(a));
    v.truncate(TAIL);
    v
}

fn esc(s: &str) -> String {
    let mut out = String::from("\"");
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

pub fn raw_record(host: &str, surface: &str, e: &Exact, unix_seconds: u64) -> String {
    let mut cs = Vec::new();
    for c in 0..2 {
        let t: Vec<String> = tail(&e.render[c]).iter().map(|x| x.to_string()).collect();
        cs.push(format!(
            "\"{}\":{{\"envelope\":{{\"render_us\":{},\"call_us\":{},\"present_us\":{},\"samples\":{}}},\"tail_render_us\":[{}]}}",
            CALLS[c], pct_json(&e.render[c]), pct_json(&e.call[c]), pct_json(&e.present[c]), e.render[c].len(), t.join(",")));
    }
    let g = e.geometry;
    let data = format!(
        "{{\"calls\":{{{}}},\"geometry\":{{\"client\":[{},{}],\"origin\":[{},{}],\"screen_logical\":[{},{}],\"screen_physical\":[{},{}],\"source\":[{},{}]}},\"readback\":{{\"frames\":{},\"checks\":{},\"bytes_compared\":{},\"mismatched_bytes\":{},\"method\":\"clear to white, read the clear back, present, read the composed screen back\"}},\"block_order\":\"ABBA\",\"warm_rounds\":{},\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"production_threads\":{},\"phase_origin\":\"locked\",\"render_entry\":\"LoopRenderer\",\"loop_renders\":{}}}",
        cs.join(","), g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], W, H, e.readback.frames, e.readback.checks,
        e.readback.bytes_compared, e.readback.mismatched_bytes, WARM_ROUNDS, e.refresh_us, e.frames, e.per_cell,
        crate::fast::PROD_THREADS, e.renders);
    let prov = format!(
        "{{\"tool\":\"shell/presentexact.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"PRESENT-EXACT-0\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("the certified composite presented 1:1 by StretchDIBits and by SetDIBitsToDevice in a borderless {}x{} window at the screen's origin on host {}, the composed screen read back, uninstrumented envelopes interleaved ABBA, locked phase origin, {} samples per cell over {} frames",
                        W, H, host, e.per_cell, e.frames);
    format!(
        "{{\"name\":\"verdandi-presentexact\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"the envelope per present call, and the composed screen read back; the rule is the sealer's; NOT input-to-photon\"}}",
        prov, esc(&scope), esc(host), data)
}

pub fn summary(e: &Exact) -> Vec<String> {
    let mut out = vec![format!("presentexact refresh_us {} frames {} per_cell {} warm_rounds {} readback_checks {} mismatched_bytes {}",
                               e.refresh_us, e.frames, e.per_cell, WARM_ROUNDS, e.readback.checks, e.readback.mismatched_bytes)];
    for c in 0..2 {
        let (r50, r95, r99, rmax) = percentiles(&e.render[c]);
        let (c50, _, c99, _) = percentiles(&e.call[c]);
        let (p50, _, p99, _) = percentiles(&e.present[c]);
        out.push(format!("presentexact {} envelope_p50={} envelope_p95={} envelope_p99={} envelope_max={} call_p50={} call_p99={} composited_p50={} composited_p99={}",
                         CALLS[c], r50, r95, r99, rmax, c50, c99, p50, p99));
    }
    out
}

/// The gate's surface: LATENCY-1R's mock clock, with a screen that holds exactly what was last presented.
/// Plants: "geometry" (a title bar's worth of client missing), "readback" (one byte changed on the way back under
/// StretchDIBits), "noop" (SetDIBitsToDevice writes nothing), "stale" (the clear writes nothing; REFUSAL-WHY-0's
/// witness that the STALE refusal carries its attribution).
pub struct MockExact {
    pub inner: crate::latency1r::MockSurface,
    pub call: usize,
    pub screen: Vec<u8>,
    pub plant: String,
}

impl MockExact {
    pub fn new(inner: crate::latency1r::MockSurface, plant: &str) -> MockExact {
        MockExact { inner, call: 0, screen: vec![0u8; W * H * 3], plant: plant.to_string() }
    }
}

impl Surface for MockExact {
    fn ticks(&mut self) -> i64 {
        self.inner.ticks()
    }
    fn freq(&self) -> i64 {
        self.inner.freq()
    }
    fn present(&mut self, bgr: &[u8]) -> Option<(i64, i64)> {
        if !(self.plant == "noop" && self.call == 1) {
            self.screen.copy_from_slice(bgr);
        }
        self.inner.present(bgr)
    }
    fn flush(&mut self) {
        self.inner.flush()
    }
    fn pump(&mut self) -> bool {
        self.inner.pump()
    }
}

impl ExactSurface for MockExact {
    fn set_call(&mut self, call: usize) {
        self.call = call;
    }
    fn clear(&mut self) -> bool {
        if self.plant != "stale" {
            self.screen.fill(0xFF);
        }
        true
    }
    fn readback(&mut self) -> Option<Vec<u8>> {
        let mut v = self.screen.clone();
        if self.plant == "readback" && self.call == 0 && v[..] != vec![0xFFu8; v.len()][..] {
            v[12_345] ^= 1;
        }
        Some(v)
    }
    fn geometry(&mut self) -> [i32; 8] {
        if self.plant == "geometry" {
            [W as i32, H as i32 - 39, 0, 39, W as i32, H as i32, W as i32, H as i32]
        } else {
            [W as i32, H as i32, 0, 0, W as i32, H as i32, W as i32, H as i32]
        }
    }
    fn attribute(&mut self, b: [usize; 4]) -> String {
        format!("attribution: the mock screen has no windows; nothing lies above ({},{})-({},{})", b[0], b[1], b[2], b[3])
    }
}
