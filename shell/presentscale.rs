// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/presentscale.rs — PRESENT-SCALE-0: how much of the blit is the 2:1 destination scaling.
//
// FRAME-SPLIT-0 (confirmed) timed the blit — GetDC + StretchDIBits of the 1920x1080 composite into the half-size
// client area — as the largest phase of the shell's frame (~7.1 ms p50, 427-434 permille of the envelope p99),
// without a seat. This diagnostic court varies ONE thing: the destination geometry, as a CLIENT-AREA size (never
// the outer window size), half (960x540) against full (1920x1080, 1:1 with the source). Everything else is
// FRAME-SPLIT-0's production path, unchanged: the same sealed session, the same arm_composite / marked mirror, the
// same HUD, the same BGR buffer, the same GDI present, the locked phase origin. Per geometry an uninstrumented
// envelope interleaves with the instrumented split, so the whole frame is recorded beside the blit and a geometry
// that silently changed the rest of the path is caught.
//
// The window is resized between BLOCKS, never between samples: 8 blocks in the order half, full, full, half, half,
// full, full, half, each opening with 5 discarded warm-up rounds (a resize reallocates the compositor's surface), and
// the client rectangle is read back after every resize and must equal the requested size, or the court refuses.
// Platform-agnostic over `GeomSurface`; the host's is a GDI surface appended to win32.rs, the gate's a mock.

use crate::latency1r::{percentiles, FrameInput, MockSurface, Surface};
use crate::mantle::{frame_digest, H, W};
use crate::present::{arm_composite, arm_composite_marked, to_blit, Arm, Marks};

pub const PHASES: [&str; 7] = ["strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit"];
/// The two destinations, as client-area sizes: half (the shell's window) and full (1:1 with the source).
pub const GEOMETRIES: [(u32, u32); 2] = [((W / 2) as u32, (H / 2) as u32), (W as u32, H as u32)];
pub const GEOMETRY_NAMES: [&str; 2] = ["half", "full"];
pub const BLOCK_ORDER: [usize; 8] = [0, 1, 1, 0, 0, 1, 1, 0];
pub const WARM_ROUNDS_PER_BLOCK: usize = 5;

/// A surface whose client area can be set. `set_destination` resizes the client area to (w, h), makes (w, h) the
/// blit's destination rectangle, and returns the client size the window actually has.
pub trait GeomSurface: Surface {
    fn set_destination(&mut self, w: u32, h: u32) -> Result<(u32, u32), String>;
    /// (logical screen w, h, desktop w, h, the DC's stretch mode) — recorded, never varied.
    fn environment(&mut self) -> (i32, i32, i32, i32, i32);
}

struct GeomMarks<'a, S: GeomSurface> {
    s: &'a mut S,
    t: [i64; 5],
    n: usize,
}

impl<'a, S: GeomSurface> Marks for GeomMarks<'a, S> {
    fn mark(&mut self) {
        if self.n < 5 {
            self.t[self.n] = self.s.ticks();
        }
        self.n += 1;
    }
}

pub struct GeomCells {
    pub client: (u32, u32),
    pub env_render: Vec<u64>,
    pub env_present: Vec<u64>,
    pub split_render: Vec<u64>,
    pub split_present: Vec<u64>,
    pub phases: Vec<Vec<u64>>,
}

pub struct Scale {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub geoms: Vec<GeomCells>,
    pub environment: (i32, i32, i32, i32, i32),
}

pub fn court<S: GeomSurface>(s: &mut S, inputs: &[FrameInput], per_cell: usize) -> Result<Scale, String> {
    if inputs.is_empty() || per_cell == 0 || per_cell % 4 != 0 {
        return Err("PRESENTSCALE-EMPTY: no sealed frames, or samples per cell not a positive multiple of 4".to_string());
    }
    // 1. witnesses first — outside every clock: the production envelope path reproduces every sealed witness and the
    //    marked mirror reproduces the envelope path byte for byte
    struct NoMarks;
    impl Marks for NoMarks {
        fn mark(&mut self) {}
    }
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let (fr, comp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fr) != f.witness {
            return Err(format!("PRESENTSCALE-WITNESS: the production frame {} is not the sealed witness", i));
        }
        let (mfr, mcomp) = arm_composite_marked(&f.scene, Arm::Production, &mut NoMarks);
        if mfr != fr || mcomp != comp {
            return Err(format!("PRESENTSCALE-MIRROR: the marked path differs from arm_composite on frame {}", i));
        }
        expected.push(comp);
    }
    let environment = s.environment();
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
    let mut geoms: Vec<GeomCells> = (0..2).map(|_| GeomCells {
        client: (0, 0), env_render: Vec::new(), env_present: Vec::new(), split_render: Vec::new(),
        split_present: Vec::new(), phases: vec![Vec::new(); PHASES.len()] }).collect();
    let rounds_per_block = per_cell / 4;
    let mut round_global = 0usize;
    for (b, &g) in BLOCK_ORDER.iter().enumerate() {
        let (w, h) = GEOMETRIES[g];
        let client = s.set_destination(w, h)?;
        if client != (w, h) {
            return Err(format!("PRESENTSCALE-GEOMETRY: block {} asked for a {}x{} client area and got {}x{}; no number is taken",
                               b + 1, w, h, client.0, client.1));
        }
        geoms[g].client = client;
        for r in 0..(WARM_ROUNDS_PER_BLOCK + rounds_per_block) {
            let record = r >= WARM_ROUNDS_PER_BLOCK;
            let k = round_global % inputs.len();
            round_global += 1;
            let order: [bool; 2] = if r % 2 == 0 { [false, true] } else { [true, false] }; // envelope/split, alternating
            for &instrumented in order.iter() {
                if !s.pump() {
                    return Err(format!("PRESENTSCALE-CLOSED: the window closed before the court finished (block {} of 8); no partial record", b + 1));
                }
                s.flush(); // the locked phase origin
                let t0 = s.ticks();
                let (comp, marks) = if instrumented {
                    let mut m = GeomMarks { s: &mut *s, t: [0; 5], n: 0 };
                    let (_fr, comp) = arm_composite_marked(&inputs[k].scene, Arm::Production, &mut m);
                    if m.n != 5 {
                        return Err("PRESENTSCALE-MARKS: the marked path did not mark exactly five render phases".to_string());
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
                    None => return Err("PRESENTSCALE-NO-PRESENT: the blit or the composition barrier failed".to_string()),
                };
                if comp != expected[k] {
                    return Err(format!("PRESENTSCALE-DRIFT: a composite of frame {} drifted from its verified bytes", k));
                }
                if record {
                    let gc = &mut geoms[g];
                    match marks {
                        Some(t) => {
                            gc.split_render.push(us(t1 - t0));
                            gc.split_present.push(us(t2 - t1));
                            let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];
                            for p in 0..PHASES.len() {
                                gc.phases[p].push(us(bounds[p + 1] - bounds[p]));
                            }
                        }
                        None => {
                            gc.env_render.push(us(t1 - t0));
                            gc.env_present.push(us(t2 - t1));
                        }
                    }
                }
            }
        }
        s.progress((b + 1) * rounds_per_block * 2, per_cell * 4);
    }
    Ok(Scale { refresh_us, frames: inputs.len(), per_cell, geoms, environment })
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

pub fn raw_record(host: &str, surface: &str, sc: &Scale, unix_seconds: u64) -> String {
    let mut gs = Vec::new();
    for (g, gc) in sc.geoms.iter().enumerate() {
        let phases: Vec<String> = PHASES.iter().enumerate()
            .map(|(p, name)| format!("\"{}\":{}", name, pct_json(&gc.phases[p]))).collect();
        gs.push(format!(
            "\"{}\":{{\"destination\":[{},{}],\"client\":[{},{}],\"envelope\":{{\"render_us\":{},\"present_us\":{},\"samples\":{}}},\"split\":{{\"phases_us\":{{{}}},\"render_us\":{},\"present_us\":{},\"samples\":{}}}}}",
            GEOMETRY_NAMES[g], GEOMETRIES[g].0, GEOMETRIES[g].1, gc.client.0, gc.client.1,
            pct_json(&gc.env_render), pct_json(&gc.env_present), gc.env_render.len(),
            phases.join(","), pct_json(&gc.split_render), pct_json(&gc.split_present), gc.split_render.len()));
    }
    let (lw, lh, dw, dh, sm) = sc.environment;
    let data = format!(
        "{{\"geometries\":{{{}}},\"source\":[{},{}],\"phases\":[{}],\"block_order\":\"HFFHHFFH\",\"warm_rounds_per_block\":{},\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"production_threads\":{},\"phase_origin\":\"locked\",\"screen\":{{\"logical\":[{},{}],\"desktop\":[{},{}]}},\"stretch_mode\":{}}}",
        gs.join(","), W, H, PHASES.iter().map(|p| format!("\"{}\"", p)).collect::<Vec<_>>().join(","),
        WARM_ROUNDS_PER_BLOCK, sc.refresh_us, sc.frames, sc.per_cell, crate::fast::PROD_THREADS, lw, lh, dw, dh, sm);
    let prov = format!(
        "{{\"tool\":\"shell/presentscale.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"PRESENT-SCALE-0\",\"chain_hash\":\"PASTE_PRESENTSCALE0_HASH\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("the shell's production frame (envelope and split) presented into a half-size ({}x{}) and a full-size ({}x{}) client area over the sealed reference session on host {}, locked phase origin, {} samples per cell over {} frames",
                        GEOMETRIES[0].0, GEOMETRIES[0].1, GEOMETRIES[1].0, GEOMETRIES[1].1, host, sc.per_cell, sc.frames);
    format!(
        "{{\"name\":\"verdandi-presentscale\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"the blit and the whole frame per destination geometry; the attribution is the reader's; NOT input-to-photon\"}}",
        prov, esc(&scope), esc(host), data)
}

pub fn summary(sc: &Scale) -> Vec<String> {
    let (lw, lh, dw, dh, sm) = sc.environment;
    let mut out = vec![format!("presentscale refresh_us {} frames {} per_cell {} screen_logical {}x{} screen_desktop {}x{} stretch_mode {}",
                               sc.refresh_us, sc.frames, sc.per_cell, lw, lh, dw, dh, sm)];
    for (g, gc) in sc.geoms.iter().enumerate() {
        let (e50, _, e99, _) = percentiles(&gc.env_render);
        let (b50, _, b99, _) = percentiles(&gc.phases[6]);
        let non_blit: u64 = (0..6).map(|p| percentiles(&gc.phases[p]).0).sum();
        let (pr50, _, pr99, _) = percentiles(&gc.env_present);
        out.push(format!("presentscale {} client {}x{} envelope_p50={} envelope_p99={} blit_p50={} blit_p99={} non_blit_p50_sum={} present_p50={} present_p99={}",
                         GEOMETRY_NAMES[g], gc.client.0, gc.client.1, e50, e99, b50, b99, non_blit, pr50, pr99));
    }
    out
}

/// The gate's surface: latency1r's deterministic mock, with a settable destination. `clamp` is a plant: the window
/// manager refuses the full size (the client comes back short), which the court must refuse.
pub struct MockGeom {
    pub inner: MockSurface,
    pub clamp: bool,
}

impl Surface for MockGeom {
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

impl GeomSurface for MockGeom {
    fn set_destination(&mut self, w: u32, h: u32) -> Result<(u32, u32), String> {
        if self.clamp && w == W as u32 {
            return Ok((w, h - 31));
        }
        Ok((w, h))
    }
    fn environment(&mut self) -> (i32, i32, i32, i32, i32) {
        (0, 0, 0, 0, 0)
    }
}
