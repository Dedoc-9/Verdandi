// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/presentstretch.rs — PRESENT-STRETCH-0: does the 2:1 blit's cost depend on GDI's stretch mode.
//
// PRESENT-SCALE-0 (confirmed) found that on the owner's host the 1:1 destination's blit was far cheaper than the 2:1
// one under the device context's default stretch mode, 1 (BLACKONWHITE, a Boolean-AND reduction). This diagnostic
// court asks whether that cost belongs to scaling in general or to that mode, varying ONE thing at the half-size
// destination: the stretch mode, BLACKONWHITE (1, the default, now set explicitly) against COLORONCOLOR (3, drops the
// eliminated pixels) and HALFTONE (4, averages them). Every present sets the mode and the brush origin before the blit
// (a common DC resets both on every GetDC), identically in every cell; only the mode's value differs. Everything else
// is FRAME-SPLIT-0's production path, unchanged, with the envelope and the split recorded per mode.
//
// The mode changes between BLOCKS, never between samples: 12 blocks, B C H H C B B C H H C B, each opening with 5
// discarded warm-up rounds; the effective mode is read back after each change and must equal the request. The half-size
// client area is read back once and must be 960x540. Platform-agnostic over `StretchSurface`; the gate uses a mock.

use crate::latency1r::{percentiles, FrameInput, MockSurface, Surface};
use crate::mantle::{frame_digest, H, W};
use crate::present::{arm_composite, arm_composite_marked, to_blit, Arm, Marks};

pub const PHASES: [&str; 7] = ["strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit"];
pub const MODES: [i32; 3] = [1, 3, 4];
pub const MODE_NAMES: [&str; 3] = ["BLACKONWHITE", "COLORONCOLOR", "HALFTONE"];
pub const BLOCK_ORDER: [usize; 12] = [0, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0];
pub const WARM_ROUNDS_PER_BLOCK: usize = 5;
pub const DESTINATION: (u32, u32) = ((W / 2) as u32, (H / 2) as u32);

/// A surface presenting into a half-size client area whose stretch mode can be set. `set_mode` makes `mode` the mode
/// every later present sets before its blit and returns the mode a device context actually reports after setting it;
/// `client` returns the client area's size.
pub trait StretchSurface: Surface {
    fn set_mode(&mut self, mode: i32) -> i32;
    fn client(&mut self) -> (u32, u32);
}

struct StretchMarks<'a, S: StretchSurface> {
    s: &'a mut S,
    t: [i64; 5],
    n: usize,
}

impl<'a, S: StretchSurface> Marks for StretchMarks<'a, S> {
    fn mark(&mut self) {
        if self.n < 5 {
            self.t[self.n] = self.s.ticks();
        }
        self.n += 1;
    }
}

pub struct ModeCells {
    pub effective: i32,
    pub env_render: Vec<u64>,
    pub env_present: Vec<u64>,
    pub split_render: Vec<u64>,
    pub split_present: Vec<u64>,
    pub phases: Vec<Vec<u64>>,
}

pub struct Stretch {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub client: (u32, u32),
    pub modes: Vec<ModeCells>,
}

pub fn court<S: StretchSurface>(s: &mut S, inputs: &[FrameInput], per_cell: usize) -> Result<Stretch, String> {
    if inputs.is_empty() || per_cell == 0 || per_cell % 4 != 0 {
        return Err("PRESENTSTRETCH-EMPTY: no sealed frames, or samples per cell not a positive multiple of 4".to_string());
    }
    // 1. witnesses first — outside every clock
    struct NoMarks;
    impl Marks for NoMarks {
        fn mark(&mut self) {}
    }
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let (fr, comp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fr) != f.witness {
            return Err(format!("PRESENTSTRETCH-WITNESS: the production frame {} is not the sealed witness", i));
        }
        let (mfr, mcomp) = arm_composite_marked(&f.scene, Arm::Production, &mut NoMarks);
        if mfr != fr || mcomp != comp {
            return Err(format!("PRESENTSTRETCH-MIRROR: the marked path differs from arm_composite on frame {}", i));
        }
        expected.push(comp);
    }
    let client = s.client();
    if client != DESTINATION {
        return Err(format!("PRESENTSTRETCH-GEOMETRY: the client area is {}x{}, not the half-size {}x{}; no number is taken",
                           client.0, client.1, DESTINATION.0, DESTINATION.1));
    }
    // 2. the refresh (context only)
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
    // 3. the blocks
    let mut modes: Vec<ModeCells> = (0..MODES.len()).map(|_| ModeCells {
        effective: 0, env_render: Vec::new(), env_present: Vec::new(), split_render: Vec::new(),
        split_present: Vec::new(), phases: vec![Vec::new(); PHASES.len()] }).collect();
    let rounds_per_block = per_cell / 4;
    let mut round_global = 0usize;
    for (b, &mi) in BLOCK_ORDER.iter().enumerate() {
        let effective = s.set_mode(MODES[mi]);
        if effective != MODES[mi] {
            return Err(format!("PRESENTSTRETCH-MODE: block {} asked for stretch mode {} ({}) and the device context reports {}; no number is taken",
                               b + 1, MODES[mi], MODE_NAMES[mi], effective));
        }
        modes[mi].effective = effective;
        for r in 0..(WARM_ROUNDS_PER_BLOCK + rounds_per_block) {
            let record = r >= WARM_ROUNDS_PER_BLOCK;
            let k = round_global % inputs.len();
            round_global += 1;
            let order: [bool; 2] = if r % 2 == 0 { [false, true] } else { [true, false] };
            for &instrumented in order.iter() {
                if !s.pump() {
                    return Err(format!("PRESENTSTRETCH-CLOSED: the window closed before the court finished (block {} of 12); no partial record", b + 1));
                }
                s.flush(); // the locked phase origin
                let t0 = s.ticks();
                let (comp, marks) = if instrumented {
                    let mut m = StretchMarks { s: &mut *s, t: [0; 5], n: 0 };
                    let (_fr, comp) = arm_composite_marked(&inputs[k].scene, Arm::Production, &mut m);
                    if m.n != 5 {
                        return Err("PRESENTSTRETCH-MARKS: the marked path did not mark exactly five render phases".to_string());
                    }
                    (comp, Some(m.t))
                } else {
                    let (_fr, comp) = arm_composite(&inputs[k].scene, Arm::Production);
                    (comp, None)
                };
                let bgr = to_blit(&comp);
                let t_bgr = if marks.is_some() { s.ticks() } else { 0 };
                let (t1, t2) = match s.present(&bgr) {
                    Some(t) => t,
                    None => return Err("PRESENTSTRETCH-NO-PRESENT: the blit or the composition barrier failed".to_string()),
                };
                if comp != expected[k] {
                    return Err(format!("PRESENTSTRETCH-DRIFT: a composite of frame {} drifted from its verified bytes", k));
                }
                if record {
                    let mc = &mut modes[mi];
                    match marks {
                        Some(t) => {
                            mc.split_render.push(us(t1 - t0));
                            mc.split_present.push(us(t2 - t1));
                            let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];
                            for p in 0..PHASES.len() {
                                mc.phases[p].push(us(bounds[p + 1] - bounds[p]));
                            }
                        }
                        None => {
                            mc.env_render.push(us(t1 - t0));
                            mc.env_present.push(us(t2 - t1));
                        }
                    }
                }
            }
        }
        s.progress((b + 1) * rounds_per_block * 2, per_cell * MODES.len() * 2);
    }
    Ok(Stretch { refresh_us, frames: inputs.len(), per_cell, client, modes })
}

fn pct_json(xs: &[u64]) -> String {
    let (p50, p95, p99, max) = percentiles(xs);
    format!("{{\"p50\":{},\"p95\":{},\"p99\":{},\"max\":{}}}", p50, p95, p99, max)
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

pub fn raw_record(host: &str, surface: &str, st: &Stretch, unix_seconds: u64) -> String {
    let mut ms = Vec::new();
    for (i, mc) in st.modes.iter().enumerate() {
        let phases: Vec<String> = PHASES.iter().enumerate()
            .map(|(p, name)| format!("\"{}\":{}", name, pct_json(&mc.phases[p]))).collect();
        ms.push(format!(
            "\"{}\":{{\"requested\":{},\"effective\":{},\"envelope\":{{\"render_us\":{},\"present_us\":{},\"samples\":{}}},\"split\":{{\"phases_us\":{{{}}},\"render_us\":{},\"present_us\":{},\"samples\":{}}}}}",
            MODE_NAMES[i], MODES[i], mc.effective, pct_json(&mc.env_render), pct_json(&mc.env_present), mc.env_render.len(),
            phases.join(","), pct_json(&mc.split_render), pct_json(&mc.split_present), mc.split_render.len()));
    }
    let data = format!(
        "{{\"modes\":{{{}}},\"default_mode\":\"BLACKONWHITE\",\"destination\":[{},{}],\"client\":[{},{}],\"source\":[{},{}],\"phases\":[{}],\"block_order\":\"BCHHCBBCHHCB\",\"warm_rounds_per_block\":{},\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"production_threads\":{},\"phase_origin\":\"locked\"}}",
        ms.join(","), DESTINATION.0, DESTINATION.1, st.client.0, st.client.1, W, H,
        PHASES.iter().map(|p| format!("\"{}\"", p)).collect::<Vec<_>>().join(","),
        WARM_ROUNDS_PER_BLOCK, st.refresh_us, st.frames, st.per_cell, crate::fast::PROD_THREADS);
    let prov = format!(
        "{{\"tool\":\"shell/presentstretch.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"PRESENT-STRETCH-0\",\"chain_hash\":\"PASTE_PRESENTSTRETCH0_HASH\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("the shell's production frame (envelope and split) presented into the half-size {}x{} client area under stretch modes BLACKONWHITE, COLORONCOLOR and HALFTONE over the sealed reference session on host {}, locked phase origin, {} samples per cell over {} frames",
                        DESTINATION.0, DESTINATION.1, host, st.per_cell, st.frames);
    format!(
        "{{\"name\":\"verdandi-presentstretch\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"the blit and the whole frame per stretch mode; the attribution is the reader's; NOT input-to-photon\"}}",
        prov, esc(&scope), esc(host), data)
}

pub fn summary(st: &Stretch) -> Vec<String> {
    let mut out = vec![format!("presentstretch refresh_us {} frames {} per_cell {} client {}x{}", st.refresh_us, st.frames, st.per_cell, st.client.0, st.client.1)];
    for (i, mc) in st.modes.iter().enumerate() {
        let (e50, _, e99, _) = percentiles(&mc.env_render);
        let (b50, _, b99, _) = percentiles(&mc.phases[6]);
        let non_blit: u64 = (0..6).map(|p| percentiles(&mc.phases[p]).0).sum();
        out.push(format!("presentstretch {} effective {} envelope_p50={} envelope_p99={} blit_p50={} blit_p99={} non_blit_p50_sum={}",
                         MODE_NAMES[i], mc.effective, e50, e99, b50, b99, non_blit));
    }
    out
}

/// The gate's surface: latency1r's deterministic mock with a settable mode. `refuse_mode` is a plant: the device context
/// reports the default mode whatever is asked, which the court must refuse.
pub struct MockStretch {
    pub inner: MockSurface,
    pub refuse_mode: bool,
}

impl Surface for MockStretch {
    fn ticks(&mut self) -> i64 {
        self.inner.ticks()
    }
    fn freq(&self) -> i64 {
        self.inner.freq()
    }
    fn present(&mut self, bgr: &[u8]) -> Option<(i64, i64)> {
        self.inner.present(bgr)
    }
    fn flush(&mut self) {
        self.inner.flush()
    }
    fn pump(&mut self) -> bool {
        self.inner.pump()
    }
}

impl StretchSurface for MockStretch {
    fn set_mode(&mut self, mode: i32) -> i32 {
        if self.refuse_mode { 1 } else { mode }
    }
    fn client(&mut self) -> (u32, u32) {
        DESTINATION
    }
}
