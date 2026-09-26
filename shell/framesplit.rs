// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/framesplit.rs — FRAME-SPLIT-0: where the ~15 ms render-start -> frame-ready interval goes.
//
// LATENCY-1R measured the shell's render-start -> frame-ready interval (strips, frame, floor swizzle, pixel pass, HUD,
// RGB -> BGR conversion, GetDC + StretchDIBits) at 14.8-15.7 ms p50 for the production render — longer than a refresh
// — without saying how it divides. This court splits it, on the same window, the same sealed session and the same
// locked phase origin (every sample starts right after a composition), without adding a variable:
//
//     uninstrumented cells  the envelope: `arm_composite` (the path LATENCY-1R timed) + to_blit + present, one clock
//                           read at render-start and frame-ready — the accounting envelope
//     instrumented cells    the split: `arm_composite_marked` (the same statements with a mark after each phase)
//                           + to_blit + present, one clock read per phase boundary; frame-ready is the hard boundary
//
// Both arms (production T=8, single-thread reference) run both kinds of cell, interleaved ABBA. The phases of one
// instrumented sample are consecutive differences of its marks, so they sum to its total exactly; the difference
// between the instrumented total and the envelope is the instrumentation tax, measured, never assumed; and a gap is
// reported, never distributed among the phases. Witnesses first: no clock starts until every arm's envelope path
// reproduces every sealed frame witness, the marked mirror reproduces the envelope path byte for byte, and the arms
// agree. Platform-agnostic over `latency1r::Surface`; the gate drives it through the mock surface.

use crate::mantle::frame_digest;
use crate::latency1r::{arm_name, percentiles, FrameInput, Surface, ARMS};
use crate::present::{arm_composite, arm_composite_marked, to_blit, Marks};

/// The phases, in order: five inside the render (marked by `arm_composite_marked`), then the conversion and the blit.
pub const PHASES: [&str; 7] = ["strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit"];
/// Rounds run before the first recorded sample (every cell once per round), discarded.
pub const WARM_ROUNDS: usize = 10;

struct SurfaceMarks<'a> {
    s: &'a mut dyn Surface,
    t: [i64; 5],
    n: usize,
}

impl<'a> Marks for SurfaceMarks<'a> {
    fn mark(&mut self) {
        if self.n < 5 {
            self.t[self.n] = self.s.ticks();
        }
        self.n += 1;
    }
}

pub struct Cell {
    pub arm_index: usize,
    pub instrumented: bool,
    pub render_us: Vec<u64>,      // render-start -> frame-ready (the envelope, or the split's total)
    pub present_us: Vec<u64>,     // frame-ready -> composited, kept beside as the second anchor
    pub phases_us: Vec<Vec<u64>>, // instrumented only: one vector per PHASES entry
}

pub struct Split {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub cells: Vec<Cell>, // [P envelope, P split, S envelope, S split]
}

pub fn court(s: &mut dyn Surface, inputs: &[FrameInput], per_cell: usize) -> Result<Split, String> {
    if inputs.is_empty() || per_cell == 0 {
        return Err("FRAMESPLIT-EMPTY: no sealed frames or no samples requested".to_string());
    }
    // 1. witnesses first — outside every clock
    struct NoMarks;
    impl Marks for NoMarks {
        fn mark(&mut self) {}
    }
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let mut first: Option<Vec<u8>> = None;
        for &arm in ARMS.iter() {
            let (fr, comp) = arm_composite(&f.scene, arm);
            if frame_digest(&fr) != f.witness {
                return Err(format!("FRAMESPLIT-WITNESS: the {} arm's frame {} is not the sealed witness", arm_name(arm), i));
            }
            let (mfr, mcomp) = arm_composite_marked(&f.scene, arm, &mut NoMarks);
            if mfr != fr || mcomp != comp {
                return Err(format!("FRAMESPLIT-MIRROR: the marked {} path differs from arm_composite on frame {}", arm_name(arm), i));
            }
            match &first {
                None => first = Some(comp),
                Some(c) => {
                    if *c != comp {
                        return Err(format!("FRAMESPLIT-WITNESS: the arms' composites differ on frame {}", i));
                    }
                }
            }
        }
        expected.push(first.unwrap());
    }
    // 2. the refresh — LATENCY-0's estimate, the median of eight idle composition intervals (context only)
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
    // 3. the interleaved court: cells 0..4 = (production, single) x (envelope, split); ABBA; warm rounds discarded
    let mut cells: Vec<Cell> = Vec::with_capacity(4);
    for c in 0..4 {
        cells.push(Cell { arm_index: c / 2, instrumented: c % 2 == 1, render_us: Vec::with_capacity(per_cell),
                          present_us: Vec::with_capacity(per_cell),
                          phases_us: if c % 2 == 1 { vec![Vec::with_capacity(per_cell); PHASES.len()] } else { Vec::new() } });
    }
    let total_rounds = WARM_ROUNDS + per_cell;
    for round in 0..total_rounds {
        let k = round % inputs.len();
        let record = round >= WARM_ROUNDS;
        let order: [usize; 4] = if round % 2 == 0 { [0, 1, 2, 3] } else { [3, 2, 1, 0] };
        for &c in order.iter() {
            if !s.pump() {
                let taken: usize = cells.iter().map(|x| x.render_us.len()).sum();
                return Err(format!("FRAMESPLIT-CLOSED: the window closed before the court finished (round {} of {}, {} of {} samples taken); no partial record",
                                   round + 1, total_rounds, taken, per_cell * 4));
            }
            let arm = ARMS[cells[c].arm_index];
            s.flush(); // the locked phase origin: every sample starts from a composition
            let t0 = s.ticks();
            let (comp, marks) = if cells[c].instrumented {
                let mut m = SurfaceMarks { s: &mut *s, t: [0; 5], n: 0 };
                let (_fr, comp) = arm_composite_marked(&inputs[k].scene, arm, &mut m);
                if m.n != 5 {
                    return Err("FRAMESPLIT-MARKS: the marked path did not mark exactly five render phases".to_string());
                }
                (comp, Some(m.t))
            } else {
                let (_fr, comp) = arm_composite(&inputs[k].scene, arm);
                (comp, None)
            };
            let bgr = to_blit(&comp);
            let t_bgr = if marks.is_some() { s.ticks() } else { 0 };
            let (t1, t2) = match s.present(&bgr) {
                Some(t) => t,
                None => return Err("FRAMESPLIT-NO-PRESENT: the blit or the composition barrier failed".to_string()),
            };
            if comp != expected[k] {
                return Err(format!("FRAMESPLIT-DRIFT: a composite of frame {} drifted from its verified bytes", k));
            }
            if record {
                cells[c].render_us.push(us(t1 - t0));
                cells[c].present_us.push(us(t2 - t1));
                if let Some(t) = marks {
                    // consecutive differences of contiguous marks: the phases sum to t1 - t0 exactly
                    let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];
                    for p in 0..PHASES.len() {
                        cells[c].phases_us[p].push(us(bounds[p + 1] - bounds[p]));
                    }
                }
            }
        }
        if record {
            s.progress((round + 1 - WARM_ROUNDS) * 4, per_cell * 4);
        }
    }
    Ok(Split { refresh_us, frames: inputs.len(), per_cell, cells })
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

/// The raw record (numbers only; sealing and the reading are verify/framesplit.py's).
pub fn raw_record(host: &str, surface: &str, sp: &Split, unix_seconds: u64) -> String {
    let mut arms = Vec::new();
    for (ai, &arm) in ARMS.iter().enumerate() {
        let env = sp.cells.iter().find(|c| c.arm_index == ai && !c.instrumented).unwrap();
        let spl = sp.cells.iter().find(|c| c.arm_index == ai && c.instrumented).unwrap();
        let phases: Vec<String> = PHASES.iter().enumerate()
            .map(|(p, name)| format!("\"{}\":{}", name, pct_json(&spl.phases_us[p]))).collect();
        arms.push(format!(
            "\"{}\":{{\"envelope\":{{\"render_us\":{},\"present_us\":{},\"samples\":{}}},\"split\":{{\"phases_us\":{{{}}},\"render_us\":{},\"present_us\":{},\"samples\":{}}}}}",
            arm_name(arm), pct_json(&env.render_us), pct_json(&env.present_us), env.render_us.len(),
            phases.join(","), pct_json(&spl.render_us), pct_json(&spl.present_us), spl.render_us.len()));
    }
    let data = format!(
        "{{\"arms\":{{{}}},\"phases\":[{}],\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"warm_rounds\":{},\"production_threads\":{},\"phase_origin\":\"locked\"}}",
        arms.join(","), PHASES.iter().map(|p| format!("\"{}\"", p)).collect::<Vec<_>>().join(","),
        sp.refresh_us, sp.frames, sp.per_cell, WARM_ROUNDS, crate::fast::PROD_THREADS);
    let prov = format!(
        "{{\"tool\":\"shell/framesplit.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"FRAME-SPLIT-0\",\"chain_hash\":\"PASTE_FRAMESPLIT0_HASH\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("the render-start -> frame-ready interval of the shell's frame split into {} phases, production (T={}) and single-thread reference, envelope and split interleaved, locked phase origin, over the sealed reference session on host {}, {} samples per cell over {} frames",
                        PHASES.len(), crate::fast::PROD_THREADS, host, sp.per_cell, sp.frames);
    format!(
        "{{\"name\":\"verdandi-framesplit\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"per-phase split of render-start -> frame-ready with the uninstrumented envelope beside it; the seat rule is the reader's; NOT input-to-photon\"}}",
        prov, esc(&scope), esc(host), data)
}

pub fn summary(sp: &Split) -> Vec<String> {
    let mut out = vec![format!("framesplit refresh_us {} frames {} per_cell {} warm_rounds {}", sp.refresh_us, sp.frames, sp.per_cell, WARM_ROUNDS)];
    for c in &sp.cells {
        let arm = arm_name(ARMS[c.arm_index]);
        let (r50, _, r99, _) = percentiles(&c.render_us);
        if c.instrumented {
            let parts: Vec<String> = PHASES.iter().enumerate()
                .map(|(p, name)| { let (a, _, b, _) = percentiles(&c.phases_us[p]); format!("{}={}/{}", name, a, b) }).collect();
            out.push(format!("framesplit split {} n={} total_p50={} total_p99={} {}", arm, c.render_us.len(), r50, r99, parts.join(" ")));
        } else {
            out.push(format!("framesplit envelope {} n={} render_p50={} render_p99={}", arm, c.render_us.len(), r50, r99));
        }
    }
    out
}
