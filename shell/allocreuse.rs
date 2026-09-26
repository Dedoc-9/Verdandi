// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/allocreuse.rs — ALLOC-REUSE-0: how much of the frame is buffer allocation.
//
// FRAME-SPLIT-0 (confirmed) attributes each allocation to the phase it happens in: the index frame's 2 MB to `frame`,
// the pixels' 6 MB to `emit`, the BGR blit buffer's 6 MB to `bgr` (and the strips vector to `strips`). This diagnostic
// court varies ONE thing — the buffers' lifetime: FRESH (allocated every frame, the production path, `arm_composite` /
// `arm_composite_marked` + `to_blit`) against REUSED (allocated once and overwritten, `arm_composite_reuse_marked` +
// `to_blit_into`), the same calls in the same order otherwise. Everything else is FRAME-SPLIT-0's apparatus: the
// production window (half size, the default stretch mode), the sealed session, the GDI present, the locked phase
// origin. Per variant an uninstrumented envelope and an instrumented split are recorded, four cells interleaved ABBA
// after 10 warm-up rounds. Witnesses first: the reuse variant's composite and blit bytes must equal the fresh path's
// for every sealed frame before any clock, and every composite is checked after its sample. The gate uses a mock.

use crate::latency1r::{percentiles, FrameInput, Surface};
use crate::mantle::frame_digest;
use crate::present::{arm_composite, arm_composite_marked, arm_composite_reuse_marked, to_blit, to_blit_into, Arm, Marks, ReuseBufs};

pub const PHASES: [&str; 7] = ["strips", "frame", "floor_swizzle", "emit", "hud", "bgr", "blit"];
pub const VARIANTS: [&str; 2] = ["fresh", "reused"];
pub const WARM_ROUNDS: usize = 10;

struct AllocMarks<'a> {
    s: &'a mut dyn Surface,
    t: [i64; 5],
    n: usize,
}

impl<'a> Marks for AllocMarks<'a> {
    fn mark(&mut self) {
        if self.n < 5 {
            self.t[self.n] = self.s.ticks();
        }
        self.n += 1;
    }
}

pub struct VariantCells {
    pub env_render: Vec<u64>,
    pub env_present: Vec<u64>,
    pub split_render: Vec<u64>,
    pub split_present: Vec<u64>,
    pub phases: Vec<Vec<u64>>,
}

pub struct Alloc {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub variants: Vec<VariantCells>,
}

pub fn court(s: &mut dyn Surface, inputs: &[FrameInput], per_cell: usize) -> Result<Alloc, String> {
    if inputs.is_empty() || per_cell == 0 {
        return Err("ALLOCREUSE-EMPTY: no sealed frames or no samples requested".to_string());
    }
    struct NoMarks;
    impl Marks for NoMarks {
        fn mark(&mut self) {}
    }
    // 1. witnesses first — outside every clock: fresh reproduces the sealed witness; reused reproduces fresh, byte for byte
    let mut bufs = ReuseBufs::new();
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    let mut expected_bgr: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let (fr, comp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fr) != f.witness {
            return Err(format!("ALLOCREUSE-WITNESS: the production frame {} is not the sealed witness", i));
        }
        let (mfr, mcomp) = arm_composite_marked(&f.scene, Arm::Production, &mut NoMarks);
        if mfr != fr || mcomp != comp {
            return Err(format!("ALLOCREUSE-MIRROR: the marked path differs from arm_composite on frame {}", i));
        }
        arm_composite_reuse_marked(&f.scene, &mut bufs, &mut NoMarks);
        let bgr = to_blit(&comp);
        to_blit_into(&bufs.pixels, &mut bufs.bgr);
        if bufs.frame != fr || bufs.pixels != comp || bufs.bgr != bgr {
            return Err(format!("ALLOCREUSE-REUSE: the reused buffers differ from the fresh path on frame {}", i));
        }
        expected.push(comp);
        expected_bgr.push(bgr);
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
    // 3. the court: cells 0..4 = (fresh, reused) x (envelope, split); ABBA; warm rounds discarded
    let mut variants: Vec<VariantCells> = (0..2).map(|_| VariantCells {
        env_render: Vec::new(), env_present: Vec::new(), split_render: Vec::new(), split_present: Vec::new(),
        phases: vec![Vec::new(); PHASES.len()] }).collect();
    let total_rounds = WARM_ROUNDS + per_cell;
    for round in 0..total_rounds {
        let k = round % inputs.len();
        let record = round >= WARM_ROUNDS;
        let order: [usize; 4] = if round % 2 == 0 { [0, 1, 2, 3] } else { [3, 2, 1, 0] };
        for &c in order.iter() {
            if !s.pump() {
                return Err(format!("ALLOCREUSE-CLOSED: the window closed before the court finished (round {} of {}); no partial record",
                                   round + 1, total_rounds));
            }
            let (v, instrumented) = (c / 2, c % 2 == 1);
            s.flush(); // the locked phase origin
            let t0 = s.ticks();
            let mut marks_t: Option<[i64; 5]> = None;
            let mut t_bgr = 0i64;
            let presented = if v == 0 {
                // FRESH — the production path, buffers allocated inside their phases
                let comp = if instrumented {
                    let mut m = AllocMarks { s: &mut *s, t: [0; 5], n: 0 };
                    let (_fr, comp) = arm_composite_marked(&inputs[k].scene, Arm::Production, &mut m);
                    if m.n != 5 {
                        return Err("ALLOCREUSE-MARKS: the marked path did not mark exactly five render phases".to_string());
                    }
                    marks_t = Some(m.t);
                    comp
                } else {
                    arm_composite(&inputs[k].scene, Arm::Production).1
                };
                let bgr = to_blit(&comp);
                if instrumented {
                    t_bgr = s.ticks();
                }
                let t = s.present(&bgr);
                if comp != expected[k] || bgr != expected_bgr[k] {
                    return Err(format!("ALLOCREUSE-DRIFT: a fresh composite of frame {} drifted from its verified bytes", k));
                }
                t
            } else {
                // REUSED — the same calls into buffers allocated once
                if instrumented {
                    let mut m = AllocMarks { s: &mut *s, t: [0; 5], n: 0 };
                    arm_composite_reuse_marked(&inputs[k].scene, &mut bufs, &mut m);
                    if m.n != 5 {
                        return Err("ALLOCREUSE-MARKS: the reuse path did not mark exactly five render phases".to_string());
                    }
                    marks_t = Some(m.t);
                } else {
                    arm_composite_reuse_marked(&inputs[k].scene, &mut bufs, &mut NoMarks);
                }
                to_blit_into(&bufs.pixels, &mut bufs.bgr);
                if instrumented {
                    t_bgr = s.ticks();
                }
                let t = s.present(&bufs.bgr);
                if bufs.pixels != expected[k] || bufs.bgr != expected_bgr[k] {
                    return Err(format!("ALLOCREUSE-DRIFT: a reused composite of frame {} drifted from its verified bytes", k));
                }
                t
            };
            let (t1, t2) = match presented {
                Some(t) => t,
                None => return Err("ALLOCREUSE-NO-PRESENT: the blit or the composition barrier failed".to_string()),
            };
            if record {
                let vc = &mut variants[v];
                match marks_t {
                    Some(t) => {
                        vc.split_render.push(us(t1 - t0));
                        vc.split_present.push(us(t2 - t1));
                        let bounds = [t0, t[0], t[1], t[2], t[3], t[4], t_bgr, t1];
                        for p in 0..PHASES.len() {
                            vc.phases[p].push(us(bounds[p + 1] - bounds[p]));
                        }
                    }
                    None => {
                        vc.env_render.push(us(t1 - t0));
                        vc.env_present.push(us(t2 - t1));
                    }
                }
            }
        }
        if record {
            s.progress((round + 1 - WARM_ROUNDS) * 4, per_cell * 4);
        }
    }
    Ok(Alloc { refresh_us, frames: inputs.len(), per_cell, variants })
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

pub fn raw_record(host: &str, surface: &str, al: &Alloc, unix_seconds: u64) -> String {
    let mut vs = Vec::new();
    for (i, vc) in al.variants.iter().enumerate() {
        let phases: Vec<String> = PHASES.iter().enumerate()
            .map(|(p, name)| format!("\"{}\":{}", name, pct_json(&vc.phases[p]))).collect();
        vs.push(format!(
            "\"{}\":{{\"envelope\":{{\"render_us\":{},\"present_us\":{},\"samples\":{}}},\"split\":{{\"phases_us\":{{{}}},\"render_us\":{},\"present_us\":{},\"samples\":{}}}}}",
            VARIANTS[i], pct_json(&vc.env_render), pct_json(&vc.env_present), vc.env_render.len(),
            phases.join(","), pct_json(&vc.split_render), pct_json(&vc.split_present), vc.split_render.len()));
    }
    let data = format!(
        "{{\"variants\":{{{}}},\"phases\":[{}],\"warm_rounds\":{},\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"production_threads\":{},\"phase_origin\":\"locked\"}}",
        vs.join(","), PHASES.iter().map(|p| format!("\"{}\"", p)).collect::<Vec<_>>().join(","),
        WARM_ROUNDS, al.refresh_us, al.frames, al.per_cell, crate::fast::PROD_THREADS);
    let prov = format!(
        "{{\"tool\":\"shell/allocreuse.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"ALLOC-REUSE-0\",\"chain_hash\":\"PASTE_ALLOCREUSE0_HASH\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("the shell's production frame (envelope and split) with its buffers allocated every frame (fresh) and allocated once (reused), over the sealed reference session on host {}, locked phase origin, {} samples per cell over {} frames",
                        host, al.per_cell, al.frames);
    format!(
        "{{\"name\":\"verdandi-allocreuse\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"the frame per buffer lifetime; the attribution is the reader's; NOT input-to-photon\"}}",
        prov, esc(&scope), esc(host), data)
}

pub fn summary(al: &Alloc) -> Vec<String> {
    let mut out = vec![format!("allocreuse refresh_us {} frames {} per_cell {} warm_rounds {}", al.refresh_us, al.frames, al.per_cell, WARM_ROUNDS)];
    for (i, vc) in al.variants.iter().enumerate() {
        let (e50, _, e99, _) = percentiles(&vc.env_render);
        let parts: Vec<String> = PHASES.iter().enumerate()
            .map(|(p, name)| { let (a, _, b, _) = percentiles(&vc.phases[p]); format!("{}={}/{}", name, a, b) }).collect();
        out.push(format!("allocreuse {} envelope_p50={} envelope_p99={} {}", VARIANTS[i], e50, e99, parts.join(" ")));
    }
    out
}
