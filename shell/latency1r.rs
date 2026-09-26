// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/latency1r.rs — LATENCY-1R: render-start -> composited, the production render against the single-thread
// reference, in the same sealed window session.
//
// LATENCY-0's instrument (and so LATENCY-1, which reuses it unchanged) times blit -> composited over frames that
// `playback::frames` rendered BEFORE the window opened, so the renderer is outside its clock. This court puts the
// render inside the clock: per sample, the arm's renderer runs on a pre-parsed sealed scene, the composite is
// converted and blitted, and the sample ends when the composition barrier returns. Two arms render the identical
// certified frame — Production (fast::render, T=8) and SingleThread (the LOCKED fast::emit) — and the render phase
// relative to composition is a declared variable with two regimes:
//
//     locked   the render starts immediately after a composition (a loop that renders right after it presents)
//     uniform  the render starts at a seeded pseudo-random offset, uniform in [0, refresh), after a composition
//
// The court is platform-agnostic: it runs against a `Surface` (a clock, a present, a composition barrier, a message
// pump). The Windows window is one Surface (appended to win32.rs, after LATENCY-0's untouched instrument, host-only);
// `MockSurface` is another, a deterministic clock the gate drives through `shell latency1r-selftest`, so everything
// here except the Win32 calls is exercised on every gate run. Witnesses come first: no clock starts until both arms
// have rendered every sealed frame to the sealed frame witness and to byte-identical composites.

use crate::mantle::{frame_digest, Scene};
use crate::present::{arm_composite, to_blit, Arm};

/// The preregistered phase seed (LATENCY-1R): the uniform regime's offsets are reproducible run to run.
pub const PHASE_SEED: u64 = 0x5EED_1A7E_0000_0001;
pub const PHASES: [&str; 2] = ["locked", "uniform"];
pub const ARMS: [Arm; 2] = [Arm::Production, Arm::SingleThread];

/// What the court needs from a window. `present` blits one frame and blocks on the composition barrier, returning
/// (frame-ready, composited) ticks exactly as LATENCY-0's present does: frame-ready is read right after the blit
/// call returns, composited right after the barrier returns.
pub trait Surface {
    fn ticks(&mut self) -> i64;
    fn freq(&self) -> i64;
    fn present(&mut self, bgr: &[u8]) -> Option<(i64, i64)>;
    fn flush(&mut self);
    fn pump(&mut self) -> bool;
}

/// One sealed move to render: its scene (parsed outside every clock) and its sealed frame witness.
pub struct FrameInput {
    pub scene: Scene,
    pub witness: String,
}

pub struct Cell {
    pub phase: usize,
    pub arm: Arm,
    pub render_us: Vec<u64>,
    pub present_us: Vec<u64>,
    pub total_us: Vec<u64>,
}

pub struct Court {
    pub refresh_us: u64,
    pub frames: usize,
    pub per_cell: usize,
    pub cells: Vec<Cell>,
}

fn splitmix(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut z = *state;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// Nearest-rank percentiles, the same definition as LATENCY-0's (`win32.rs percentiles`).
pub fn percentiles(xs: &[u64]) -> (u64, u64, u64, u64) {
    let mut xs = xs.to_vec();
    xs.sort_unstable();
    let n = xs.len();
    let at = |p: f64| xs[(((n as f64) * p).ceil() as usize).saturating_sub(1).min(n - 1)];
    (at(0.50), at(0.95), at(0.99), xs[n - 1])
}

pub fn arm_name(arm: Arm) -> &'static str {
    match arm {
        Arm::Production => "production",
        Arm::SingleThread => "single_thread",
    }
}

/// The court. Witnesses first, then the refresh (LATENCY-0's estimate: the median of eight idle barrier intervals),
/// then `per_cell` rounds; each round renders the round's sealed frame once in each of the four cells
/// (locked/uniform x production/single_thread), in ABBA order (reversed on odd rounds) so drift and cache warmth
/// cancel between arms. Every sample starts from a composition. After each sample (outside its interval) the
/// composite is compared byte-for-byte to its pre-verified bytes. Any refusal returns Err and no record is written.
pub fn court(s: &mut dyn Surface, inputs: &[FrameInput], per_cell: usize) -> Result<Court, String> {
    if inputs.is_empty() || per_cell == 0 {
        return Err("LATENCY1R-EMPTY: no sealed frames or no samples requested".to_string());
    }
    // 1. witnesses first — outside every clock
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let (fp, cp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fp) != f.witness {
            return Err(format!("LATENCY1R-WITNESS: the production arm's frame {} is not the sealed witness", i));
        }
        let (fs, cs) = arm_composite(&f.scene, Arm::SingleThread);
        if frame_digest(&fs) != f.witness {
            return Err(format!("LATENCY1R-WITNESS: the single-thread arm's frame {} is not the sealed witness", i));
        }
        if cp != cs {
            return Err(format!("LATENCY1R-WITNESS: the two arms' composites differ on frame {}", i));
        }
        expected.push(cp);
    }
    // 2. the refresh period — the median of eight idle composition intervals, LATENCY-0's estimate
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
    if refresh_us == 0 {
        return Err("LATENCY1R-NO-REFRESH: the composition barrier did not block".to_string());
    }
    // 3. the interleaved court
    let mut cells: Vec<Cell> = Vec::with_capacity(4);
    for c in 0..4 {
        cells.push(Cell { phase: c / 2, arm: ARMS[c % 2], render_us: Vec::with_capacity(per_cell),
                          present_us: Vec::with_capacity(per_cell), total_us: Vec::with_capacity(per_cell) });
    }
    let mut rng = PHASE_SEED;
    for round in 0..per_cell {
        let k = round % inputs.len();
        let order: [usize; 4] = if round % 2 == 0 { [0, 1, 2, 3] } else { [3, 2, 1, 0] };
        for &c in order.iter() {
            if !s.pump() {
                return Err("LATENCY1R-CLOSED: the window closed before the court finished; no partial record".to_string());
            }
            let (phase, arm) = (cells[c].phase, cells[c].arm);
            s.flush(); // the phase origin: every sample starts from a composition
            if phase == 1 {
                let offset_us = splitmix(&mut rng) % refresh_us;
                let wait = (offset_us as u128 * freq / 1_000_000) as i64;
                let target = s.ticks() + wait;
                while s.ticks() < target {}
            }
            let t0 = s.ticks();
            let (_frame, comp) = arm_composite(&inputs[k].scene, arm);
            let bgr = to_blit(&comp);
            let (t1, t2) = match s.present(&bgr) {
                Some(t) => t,
                None => return Err("LATENCY1R-NO-PRESENT: the blit or the composition barrier failed".to_string()),
            };
            if comp != expected[k] {
                return Err(format!("LATENCY1R-DRIFT: a composite of frame {} drifted from its verified bytes", k));
            }
            cells[c].render_us.push(us(t1 - t0));
            cells[c].present_us.push(us(t2 - t1));
            cells[c].total_us.push(us(t2 - t0));
        }
    }
    Ok(Court { refresh_us, frames: inputs.len(), per_cell, cells })
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
            '\n' => out.push_str("\\n"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// The raw record the court's numbers go into. Sealing (the chain hash and the preregistration citation) is Python's
/// (`verify/latency1r.py`), so the envelope keeps one implementation. `data` holds numbers only — no verdict key.
pub fn raw_record(host: &str, surface: &str, c: &Court, unix_seconds: u64) -> String {
    let mut phases = Vec::new();
    for (p, pname) in PHASES.iter().enumerate() {
        let mut arms = Vec::new();
        for cell in c.cells.iter().filter(|x| x.phase == p) {
            arms.push(format!("\"{}\":{{\"render_us\":{},\"present_us\":{},\"total_us\":{},\"samples\":{}}}",
                              arm_name(cell.arm), pct_json(&cell.render_us), pct_json(&cell.present_us),
                              pct_json(&cell.total_us), cell.total_us.len()));
        }
        phases.push(format!("\"{}\":{{{}}}", pname, arms.join(",")));
    }
    let data = format!(
        "{{\"cells\":{{{}}},\"refresh_period_us\":{},\"sequence_frames\":{},\"samples_per_cell\":{},\"production_threads\":{},\"phase_seed\":\"0x{:016X}\"}}",
        phases.join(","), c.refresh_us, c.frames, c.per_cell, crate::fast::PROD_THREADS, PHASE_SEED);
    let prov = format!(
        "{{\"tool\":\"shell/latency1r.rs court over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"LATENCY-1R\",\"chain_hash\":\"PASTE_LATENCY1R_HASH\"}},\"unix_seconds\":{}}}",
        surface, esc(host), unix_seconds);
    let scope = format!("render-start -> composited of the production render (T={}) and the single-thread reference over the sealed reference session on host {}, locked and uniform phase, {} samples per cell over {} frames",
                        crate::fast::PROD_THREADS, host, c.per_cell, c.frames);
    format!(
        "{{\"name\":\"verdandi-latency1r\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"render-start -> composited, production vs single-thread reference, per phase regime; NOT input-to-photon; never compared to LATENCY-0/LATENCY-1 or any emit p99\"}}",
        prov, esc(&scope), esc(host), data)
}

/// Human-readable lines (stdout) for the host operator and the gate.
pub fn summary(c: &Court) -> Vec<String> {
    let mut out = vec![format!("latency1r refresh_us {} frames {} per_cell {}", c.refresh_us, c.frames, c.per_cell)];
    for cell in &c.cells {
        let (r50, _, r99, _) = percentiles(&cell.render_us);
        let (p50, _, p99, _) = percentiles(&cell.present_us);
        let (t50, _, t99, tmax) = percentiles(&cell.total_us);
        out.push(format!("latency1r cell {} {} n={} render_p50={} render_p99={} present_p50={} present_p99={} total_p50={} total_p99={} total_max={}",
                         PHASES[cell.phase], arm_name(cell.arm), cell.total_us.len(), r50, r99, p50, p99, t50, t99, tmax));
    }
    out
}

/// A deterministic stand-in for the window so the gate drives the SAME court headless: a microsecond clock that
/// advances `step` per read, a composition every `period` µs (the barrier jumps to the next one), a present that
/// always lands, and a pump that reports the window closed after `close_after` pumps (a plant), if set.
pub struct MockSurface {
    pub t: i64,
    pub period: i64,
    pub step: i64,
    pub pumps: usize,
    pub close_after: Option<usize>,
}

impl MockSurface {
    pub fn new(period: i64, step: i64, close_after: Option<usize>) -> MockSurface {
        MockSurface { t: 0, period, step, pumps: 0, close_after }
    }
}

impl Surface for MockSurface {
    fn ticks(&mut self) -> i64 {
        self.t += self.step;
        self.t
    }
    fn freq(&self) -> i64 {
        1_000_000
    }
    fn present(&mut self, _bgr: &[u8]) -> Option<(i64, i64)> {
        let ready = self.ticks();
        self.flush();
        let composited = self.ticks();
        Some((ready, composited))
    }
    fn flush(&mut self) {
        self.t = (self.t / self.period + 1) * self.period;
    }
    fn pump(&mut self) -> bool {
        self.pumps += 1;
        match self.close_after {
            Some(k) => self.pumps <= k,
            None => true,
        }
    }
}
