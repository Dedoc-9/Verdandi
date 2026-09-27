// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/allocreuse1.rs — ALLOC-REUSE-1: the adoption court for the render-loop entry.
//
// ALLOC-REUSE-0 (confirmed) attributed a material part of the modelled render loop's frame to allocating its buffers
// every frame. The shipped shell has no such loop: `run` renders once and `playback-window` pre-renders frames that
// must own their buffers. So what this court can adopt is an ENTRY CONTRACT, not a change to a shipped window: the
// persistent-buffer `present::LoopRenderer` as the production entry for any loop that renders once per presented
// frame. The fresh path (`arm_composite` + `to_blit`) is the frozen reference throughout.
//
//   `loop_equiv` (the gate's correctness court, no clock): one LoopRenderer, its byte buffers first poisoned, renders
//   every case — the certified corpus with its goldens, the adversarial cameras, the sealed session's frames — in
//   three orders (forward, reverse, zigzag), so every render starts from another scene's leftovers. Each render's
//   index frame, viewport, composite and blit must equal the fresh reference byte for byte, the corpus's frame digest
//   and pixel sha must equal the goldens, and no buffer may be replaced (address and capacity unchanged).
//
//   `court` (the host's performance court): witnesses first, then the uninstrumented envelope render-start ->
//   frame-ready for FRESH and REUSED interleaved ABBA after 10 warm-up rounds, N samples per cell (default 1000),
//   every composite and blit compared after its composition and the reuse buffers checked persistent after every
//   sample. The rule (p99) is the sealer's; this file records and never reads it. The gate drives it over a mock.

use crate::fast;
use crate::hud;
use crate::latency1r::{percentiles, FrameInput, Surface};
use crate::mantle::{frame_digest, hex, sha256, Scene};
use crate::present::{arm_composite, to_blit, Arm, LoopRenderer};

pub const VARIANTS: [&str; 2] = ["fresh", "reused"];
pub const WARM_ROUNDS: usize = 10;
pub const DEFAULT_PER_CELL: usize = 1000;
pub const TAIL: usize = 12;
pub const POISON: u8 = 0xA5;

/// Fill the renderer's byte buffers with a poison byte, so a render that leaves any byte unwritten is caught.
pub fn poison(lr: &mut LoopRenderer) {
    lr.b.frame.fill(POISON);
    lr.b.pixels.fill(POISON);
    lr.b.bgr.fill(POISON);
}

/// The three render orders over n cases: forward, reverse and zigzag (0, n-1, 1, n-2, ...).
pub fn orderings(n: usize) -> Vec<Vec<usize>> {
    let fwd: Vec<usize> = (0..n).collect();
    let rev: Vec<usize> = (0..n).rev().collect();
    let mut zig = Vec::with_capacity(n);
    let (mut lo, mut hi) = (0usize, n);
    while lo < hi {
        zig.push(lo);
        lo += 1;
        if lo < hi {
            hi -= 1;
            zig.push(hi);
        }
    }
    vec![fwd, rev, zig]
}

pub struct EquivCase {
    pub label: String,
    pub scene: Scene,
    pub golden_frame: Option<String>,
    pub golden_pixels: Option<String>,
}

pub struct EquivReport {
    pub cases: usize,
    pub goldens: usize,
    pub renders: u64,
    pub lines: Vec<String>,
}

/// The fresh reference for one scene: `fast::render` (the production render) then the HUD, then `to_blit`.
fn fresh_reference(scene: &Scene) -> (Vec<u8>, Vec<u8>, Vec<u8>, Vec<u8>) {
    let (strips, frame, viewport) = fast::render(scene);
    let mut composite = viewport.clone();
    hud::overlay(scene, &strips, &mut composite);
    let blit = to_blit(&composite);
    (frame, viewport, composite, blit)
}

/// The correctness court (no clock). `plant`: "stale" skips the pixel pass on every other render of the second order
/// (a renderer that leaves the previous scene's pixels), "realloc" replaces the BGR buffer in the third order.
pub fn loop_equiv(cases: &[EquivCase], plant: &str) -> Result<EquivReport, String> {
    if cases.is_empty() {
        return Err("LOOP-EMPTY: no cases".to_string());
    }
    let mut lr = LoopRenderer::new();
    poison(&mut lr);
    let id0 = lr.identity();
    let mut lines = Vec::new();
    let mut goldens = 0usize;
    for (oi, order) in orderings(cases.len()).iter().enumerate() {
        for (p, &i) in order.iter().enumerate() {
            let c = &cases[i];
            let (frame, viewport, composite, blit) = fresh_reference(&c.scene);
            if oi == 0 {
                // the forward order checks the viewport between the two halves, and the certified identities
                lr.viewport(&c.scene);
                if lr.index_frame() != &frame[..] || lr.composite() != &viewport[..] {
                    return Err(format!("LOOP-EQUIV: the loop's index frame or viewport differs from the fresh path on {}", c.label));
                }
                let fd = frame_digest(lr.index_frame());
                let px = hex(&sha256(lr.composite()));
                if let Some(g) = &c.golden_frame {
                    if frame_digest(&frame) != *g {
                        return Err(format!("LOOP-REFERENCE: the fresh reference's frame digest is not the golden on {}", c.label));
                    }
                    if fd != *g {
                        return Err(format!("LOOP-GOLDEN: the loop's frame digest is not the golden on {}", c.label));
                    }
                    goldens += 1;
                }
                if let Some(g) = &c.golden_pixels {
                    if hex(&sha256(&viewport)) != *g {
                        return Err(format!("LOOP-REFERENCE: the fresh reference's pixel sha is not the golden on {}", c.label));
                    }
                    if px != *g {
                        return Err(format!("LOOP-GOLDEN: the loop's pixel sha is not the golden on {}", c.label));
                    }
                }
                lines.push(format!("case {} frame {} pixels {}", c.label, fd, px));
                lr.overlay(&c.scene);
            } else if plant == "stale" && oi == 1 && p % 2 == 1 {
                // PLANT: the strips, the frame and the HUD, but no pixel pass — the previous scene's pixels survive
                c.scene.strips(&mut lr.b.strips);
                c.scene.frame(&lr.b.strips, &mut lr.b.frame);
                hud::overlay(&c.scene, &lr.b.strips, &mut lr.b.pixels);
            } else {
                lr.render(&c.scene);
            }
            lr.blit();
            if lr.index_frame() != &frame[..] || lr.composite() != &composite[..] || lr.bgr() != &blit[..] {
                return Err(format!("LOOP-EQUIV: the loop's frame, composite or blit differs from the fresh path on {} (order {}, position {})",
                                   c.label, oi, p));
            }
            if plant == "realloc" && oi == 2 {
                lr.b.bgr = vec![0u8; lr.b.bgr.len()];
            }
            if lr.identity() != id0 {
                return Err(format!("LOOP-PERSIST: a persistent buffer was replaced (order {}, position {})", oi, p));
            }
        }
    }
    Ok(EquivReport { cases: cases.len(), goldens, renders: lr.renders(), lines })
}

pub struct Adopt {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub render: [Vec<u64>; 2],
    pub present: [Vec<u64>; 2],
    pub renders: u64,
}

/// The performance court. `plant_persist` replaces a reuse buffer after the first recorded sample (the gate's plant).
pub fn court(s: &mut dyn Surface, inputs: &[FrameInput], per_cell: usize, plant_persist: bool) -> Result<Adopt, String> {
    if inputs.is_empty() || per_cell == 0 {
        return Err("ALLOCREUSE1-EMPTY: no sealed frames or no samples requested".to_string());
    }
    // 1. witnesses first — outside every clock: fresh reproduces the sealed witness; the loop (poisoned first)
    //    reproduces fresh's index frame, composite and blit byte for byte, with its buffers never replaced
    let mut lr = LoopRenderer::new();
    poison(&mut lr);
    let id0 = lr.identity();
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    let mut expected_bgr: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let (fr, comp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fr) != f.witness {
            return Err(format!("ALLOCREUSE1-WITNESS: the production frame {} is not the sealed witness", i));
        }
        let bgr = to_blit(&comp);
        lr.render(&f.scene);
        lr.blit();
        if lr.index_frame() != &fr[..] || lr.composite() != &comp[..] || lr.bgr() != &bgr[..] {
            return Err(format!("ALLOCREUSE1-REUSE: the loop renderer differs from the fresh path on frame {}", i));
        }
        if lr.identity() != id0 {
            return Err(format!("ALLOCREUSE1-PERSIST: a persistent buffer was replaced on frame {}", i));
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
    // 3. the court: two uninstrumented cells, FRESH (0) and REUSED (1), ABBA across rounds; warm rounds discarded
    let mut render: [Vec<u64>; 2] = [Vec::with_capacity(per_cell), Vec::with_capacity(per_cell)];
    let mut present: [Vec<u64>; 2] = [Vec::with_capacity(per_cell), Vec::with_capacity(per_cell)];
    let total_rounds = WARM_ROUNDS + per_cell;
    for round in 0..total_rounds {
        let k = round % inputs.len();
        let record = round >= WARM_ROUNDS;
        let order: [usize; 2] = if round % 2 == 0 { [0, 1] } else { [1, 0] };
        for &v in order.iter() {
            if !s.pump() {
                return Err(format!("ALLOCREUSE1-CLOSED: the window closed before the court finished (round {} of {}); no partial record",
                                   round + 1, total_rounds));
            }
            s.flush(); // the locked phase origin
            let t0 = s.ticks();
            let presented = if v == 0 {
                // FRESH — the frozen reference path, its buffers allocated every frame
                let comp = arm_composite(&inputs[k].scene, Arm::Production).1;
                let bgr = to_blit(&comp);
                let t = s.present(&bgr);
                if comp != expected[k] || bgr != expected_bgr[k] {
                    return Err(format!("ALLOCREUSE1-DRIFT: a fresh composite of frame {} drifted from its verified bytes", k));
                }
                t
            } else {
                // REUSED — the render-loop entry, its buffers allocated once
                lr.render(&inputs[k].scene);
                let t = s.present(lr.blit());
                if lr.composite() != &expected[k][..] || lr.bgr() != &expected_bgr[k][..] {
                    return Err(format!("ALLOCREUSE1-DRIFT: a reused composite of frame {} drifted from its verified bytes", k));
                }
                if plant_persist && record {
                    lr.b.bgr = vec![0u8; lr.b.bgr.len()];
                }
                if lr.identity() != id0 {
                    return Err(format!("ALLOCREUSE1-PERSIST: a persistent buffer was replaced (round {})", round + 1));
                }
                t
            };
            let (t1, t2) = match presented {
                Some(t) => t,
                None => return Err("ALLOCREUSE1-NO-PRESENT: the blit or the composition barrier failed".to_string()),
            };
            if record {
                render[v].push(us(t1 - t0));
                present[v].push(us(t2 - t1));
            }
        }
        if record {
            s.progress((round + 1 - WARM_ROUNDS) * 2, per_cell * 2);
        }
    }
    Ok(Adopt { refresh_us, frames: inputs.len(), per_cell, render, present, renders: lr.renders() })
}

fn pct_json(xs: &[u64]) -> String {
    let (p50, p95, p99, max) = percentiles(xs);
    format!("{{\"p50\":{},\"p95\":{},\"p99\":{},\"max\":{}}}", p50, p95, p99, max)
}

/// The TAIL largest samples, largest first: the p99 at N = 1000 is the 11th largest (nearest rank), so the samples
/// around it are shown.
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

pub fn raw_record(host: &str, surface: &str, a: &Adopt, unix_seconds: u64) -> String {
    let mut vs = Vec::new();
    for v in 0..2 {
        let t: Vec<String> = tail(&a.render[v]).iter().map(|x| x.to_string()).collect();
        vs.push(format!(
            "\"{}\":{{\"envelope\":{{\"render_us\":{},\"present_us\":{},\"samples\":{}}},\"tail_render_us\":[{}]}}",
            VARIANTS[v], pct_json(&a.render[v]), pct_json(&a.present[v]), a.render[v].len(), t.join(",")));
    }
    let data = format!(
        "{{\"variants\":{{{}}},\"block_order\":\"ABBA\",\"warm_rounds\":{},\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"production_threads\":{},\"phase_origin\":\"locked\",\"persistent_buffers\":4,\"reuse_renders\":{}}}",
        vs.join(","), WARM_ROUNDS, a.refresh_us, a.frames, a.per_cell, fast::PROD_THREADS, a.renders);
    let prov = format!(
        "{{\"tool\":\"shell/allocreuse1.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"ALLOC-REUSE-1\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("the fresh production path and the persistent-buffer render-loop entry, uninstrumented envelopes interleaved ABBA over the sealed reference session on host {}, locked phase origin, {} samples per cell over {} frames",
                        host, a.per_cell, a.frames);
    format!(
        "{{\"name\":\"verdandi-allocreuse1\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"the envelope per buffer lifetime; the rule is the sealer's; NOT input-to-photon\"}}",
        prov, esc(&scope), esc(host), data)
}

pub fn summary(a: &Adopt) -> Vec<String> {
    let mut out = vec![format!("allocreuse1 refresh_us {} frames {} per_cell {} warm_rounds {}", a.refresh_us, a.frames, a.per_cell, WARM_ROUNDS)];
    for v in 0..2 {
        let (r50, r95, r99, rmax) = percentiles(&a.render[v]);
        let (p50, _, p99, _) = percentiles(&a.present[v]);
        out.push(format!("allocreuse1 {} envelope_p50={} envelope_p95={} envelope_p99={} envelope_max={} composited_p50={} composited_p99={}",
                         VARIANTS[v], r50, r95, r99, rmax, p50, p99));
    }
    out
}
