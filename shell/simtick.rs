// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/simtick.rs — SIM-TICK-0: the mouse-look rules as integer law. Pure.
//
//   raw input -> tick command -> SESSION-WALK -> authority
//
// This module is the first arrow and the laws the others lean on, and nothing else. It reads no mouse, no key, no
// clock and no window: a time is an integer the caller hands it, and every function is a function of its arguments.
//
//   THE TICK. 64 Hz, exactly 15,625 us. An input stamped t microseconds after the run began belongs to tick t div 15625.
//   ONE COMMAND PER TICK. A tick's mouse reports are accumulated — a checked sum of signed horizontal counts — and
//   applied once, as one look; then the tick's key presses and sensitivity actions, in arrival order. A tick whose
//   counts sum to zero makes no look; an empty tick makes no command. The sum alone decides: how the counts were split
//   into reports, and when inside the tick they arrived, cannot matter.
//   THE LOOK. delta = counts x multiplier x step, integers end to end: the multiplier a whole number 1..64 (starting
//   at 1), the step 88 ids (coarse) or 1 id (fine), starting coarse — the two in force when the tick began. A
//   sensitivity action is applied in arrival order with the keys, so it takes effect from the next tick.
//   THE HEADING. k' = (k + delta) mod 360000, into [0, 360000).
//   THE NEAREST CARDINAL. ((k + 45000) div 90000) mod 4: N, E, S, W, each owning 90,000 ids, the tie at an exact
//   45-degree boundary going clockwise. An anchor is a heading that is exactly a cardinal.
//   THE BINDING under ticks is LIVE-AUTHOR-0's with A and D rebound to the strafes (Q and E): W, A, S and D step
//   toward the nearest cardinal's four directions and never change the heading.
//
// Nothing here is a float, a static, a file, a thread or unsafe; the gate's fence reads this file for them.

pub const TICK_HZ: u64 = 64;
pub const TICK_US: u64 = 15_625; // 1,000,000 / 64, exactly
pub const YAW_MOD: i64 = 360_000;
pub const QUARTER: i64 = 90_000;
pub const HALF_SECTOR: i64 = 45_000;
pub const STEP_COARSE: i64 = 88;
pub const STEP_FINE: i64 = 1;
pub const MULT_MIN: i64 = 1;
pub const MULT_MAX: i64 = 64;
pub const COUNTS_MAX: i64 = 2_147_483_647; // 2^31 - 1: one report, and one tick's sum
pub const DELTA_MAX: i64 = COUNTS_MAX * MULT_MAX * STEP_COARSE; // below 2^44

/// The tick an input stamped `us` microseconds after the run began belongs to.
pub fn tick_of(us: u64) -> u64 {
    us / TICK_US
}

/// The heading after a look: (k + delta) mod 360000, into [0, 360000).
pub fn turn(k: i64, delta: i64) -> i64 {
    (k + delta).rem_euclid(YAW_MOD)
}

/// The nearest cardinal of a heading: 0 N, 1 E, 2 S, 3 W; the tie at 45 degrees goes clockwise.
pub fn cardinal(k: i64) -> u8 {
    (((k + HALF_SECTOR) / QUARTER) % 4) as u8
}

/// The cardinal a heading is exactly, if it is one of the four anchors.
pub fn anchor(k: i64) -> Option<u8> {
    if k % QUARTER == 0 { Some((k / QUARTER) as u8) } else { None }
}

/// The sensitivity: a whole-number multiplier and a step in heading ids.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Sens {
    pub multiplier: i64,
    pub step: i64,
}

/// The sensitivity a run starts with: multiplier 1, the coarse step.
pub const START: Sens = Sens { multiplier: MULT_MIN, step: STEP_COARSE };

impl Sens {
    pub fn valid(&self) -> bool {
        (MULT_MIN..=MULT_MAX).contains(&self.multiplier) && (self.step == STEP_COARSE || self.step == STEP_FINE)
    }
    /// The multiplier one higher, or None at 64.
    pub fn up(self) -> Option<Sens> {
        if self.multiplier < MULT_MAX { Some(Sens { multiplier: self.multiplier + 1, step: self.step }) } else { None }
    }
    /// The multiplier one lower, or None at 1.
    pub fn down(self) -> Option<Sens> {
        if self.multiplier > MULT_MIN { Some(Sens { multiplier: self.multiplier - 1, step: self.step }) } else { None }
    }
    /// Coarse to fine, fine to coarse.
    pub fn toggled(self) -> Sens {
        Sens { multiplier: self.multiplier, step: if self.step == STEP_COARSE { STEP_FINE } else { STEP_COARSE } }
    }
}

/// A look's delta: counts x multiplier x step, or None when the counts leave +-(2^31 - 1) or the sensitivity is not
/// a registered one. Checked arithmetic; the largest delta is below 2^44.
pub fn delta(counts: i64, s: Sens) -> Option<i64> {
    if !(-COUNTS_MAX..=COUNTS_MAX).contains(&counts) || !s.valid() {
        return None;
    }
    counts.checked_mul(s.multiplier)?.checked_mul(s.step)
}

/// The tick binding's one difference from LIVE-AUTHOR-0's: A is Q's key and D is E's (the strafes). Every other key
/// is itself. The caller binds the result as LIVE-AUTHOR-0 does.
pub fn rebind(vk: u32) -> u32 {
    match vk {
        0x41 => 0x51, // A: strafe to the cardinal 90 degrees left
        0x44 => 0x45, // D: strafe to the cardinal 90 degrees right
        other => other,
    }
}

/// One raw input: a mouse report (signed horizontal counts), a key press (a virtual-key code), or a sensitivity action.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Input {
    Mouse(i64),
    Key(u32),
    MultUp,
    MultDown,
    StepToggle,
}

/// One tick's command: the tick, its reports' sum (and whether the sum left the bound, in which case the look is
/// refused), and its other inputs in arrival order.
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Command {
    pub tick: u64,
    pub counts: i64,
    pub over: bool,
    pub acts: Vec<Input>,
}

/// The accumulator: the inputs of the tick being gathered. `feed` hands back the finished command of the tick before
/// when an input begins a later one; `close` ends the run.
pub struct Accumulator {
    tick: u64,
    sum: i128,
    acts: Vec<Input>,
    open: bool,
}

impl Accumulator {
    pub fn new() -> Accumulator {
        Accumulator { tick: 0, sum: 0, acts: Vec::new(), open: false }
    }

    /// One input at its tick. A tick earlier than the one being gathered, or a report outside +-(2^31 - 1), refuses.
    pub fn feed(&mut self, tick: u64, input: Input) -> Result<Option<Command>, String> {
        if self.open && tick < self.tick {
            return Err(format!("SIMTICK-ORDER: an input for tick {} after tick {} was begun", tick, self.tick));
        }
        if let Input::Mouse(c) = input {
            if !(-COUNTS_MAX..=COUNTS_MAX).contains(&c) {
                return Err(format!("SIMTICK-REPORT: a mouse report of {} counts is outside +-{}", c, COUNTS_MAX));
            }
        }
        let done = if self.open && tick > self.tick { self.close() } else { None };
        if !self.open {
            self.tick = tick;
            self.open = true;
        }
        match input {
            Input::Mouse(c) => self.sum += c as i128, // each report is below 2^31: an i128 holds any run's sum
            other => self.acts.push(other),
        }
        Ok(done)
    }

    /// End the tick being gathered: its command, or None if it made none (no look and no other input).
    pub fn close(&mut self) -> Option<Command> {
        if !self.open {
            return None;
        }
        self.open = false;
        let sum = std::mem::replace(&mut self.sum, 0);
        let acts = std::mem::replace(&mut self.acts, Vec::new());
        let over = sum > COUNTS_MAX as i128 || sum < -(COUNTS_MAX as i128);
        let counts = if over { 0 } else { sum as i64 };
        if counts == 0 && !over && acts.is_empty() {
            return None;
        }
        Some(Command { tick: self.tick, counts, over, acts })
    }
}

/// A script of raw inputs: comma-separated `T:WHAT`, T the time in whole microseconds since the run began (never
/// decreasing), WHAT a mouse report (`m+N` or `m-N`), a sensitivity action (`mult+`, `mult-`, `step`) or a key name
/// (resolved by `key`).
pub fn parse_script(s: &str, key: fn(&str) -> Option<u32>) -> Result<Vec<(u64, Input)>, String> {
    let mut out: Vec<(u64, Input)> = Vec::new();
    for tok in s.split(',').map(|t| t.trim()).filter(|t| !t.is_empty()) {
        let (t, what) = match tok.split_once(':') {
            Some(p) => p,
            None => return Err(format!("script token {:?} is not T:WHAT", tok)),
        };
        let canonical = !t.is_empty() && t.bytes().all(|c| c.is_ascii_digit()) && (t == "0" || !t.starts_with('0'));
        let us: u64 = match (canonical, t.parse()) {
            (true, Ok(v)) => v,
            _ => return Err(format!("script time {:?} is not whole microseconds", t)),
        };
        if let Some(&(last, _)) = out.last() {
            if us < last {
                return Err(format!("script time {} is earlier than the input before it ({})", us, last));
            }
        }
        let input = match what {
            "mult+" => Input::MultUp,
            "mult-" => Input::MultDown,
            "step" => Input::StepToggle,
            w if w.starts_with("m+") || w.starts_with("m-") => {
                let digits = &w[2..];
                let ok = !digits.is_empty() && digits.bytes().all(|c| c.is_ascii_digit()) && digits.len() <= 10;
                let n: i64 = match (ok, digits.parse()) {
                    (true, Ok(v)) => v,
                    _ => return Err(format!("mouse report {:?} is not m+N or m-N", w)),
                };
                if n > COUNTS_MAX {
                    return Err(format!("mouse report {:?} is outside +-{}", w, COUNTS_MAX));
                }
                Input::Mouse(if w.as_bytes()[1] == b'-' { -n } else { n })
            }
            name => match key(name) {
                Some(vk) => Input::Key(vk),
                None => return Err(format!("script input {:?} is neither a mouse report, a sensitivity action nor a key", name)),
            },
        };
        out.push((us, input));
    }
    Ok(out)
}

/// One saved event as the tick form sees it: whether it is a look, its delta, and the tick and inputs saved beside it.
pub struct Timed {
    pub look: bool,
    pub delta: i64,
    pub tick: Option<u64>,
    pub input: Option<(i64, i64, i64)>,
}

/// The tick form of a saved log, checked: a look's delta is non-zero and inside the bound; inputs sit only beside a
/// timed look and multiply to its delta; the ticks never decrease; a timed look is the first event of its tick; and
/// the session's tick block (the rate, the count, the final sensitivity), which must be present exactly when the
/// session ran on ticks, covers every tick.
pub fn check_form(events: &[Timed], ticks: Option<(i64, i64, i64, i64)>) -> Result<(), String> {
    let mut last: Option<u64> = None;
    for (k, e) in events.iter().enumerate() {
        if e.look && (e.delta == 0 || e.delta > DELTA_MAX || e.delta < -DELTA_MAX) {
            return Err(format!("event {}: a look of {} ids is zero or outside the bound", k, e.delta));
        }
        match (e.look, e.tick, e.input) {
            (false, _, Some(_)) => return Err(format!("event {}: inputs beside an event that is not a look", k)),
            (true, None, Some(_)) => return Err(format!("event {}: a look with inputs and no tick", k)),
            (true, Some(_), None) => return Err(format!("event {}: a timed look without its inputs", k)),
            (true, Some(_), Some((counts, multiplier, step))) => {
                if counts == 0 || delta(counts, Sens { multiplier, step }) != Some(e.delta) {
                    return Err(format!("event {}: the delta {} is not counts {} x multiplier {} x step {}", k, e.delta, counts, multiplier, step));
                }
            }
            _ => {}
        }
        if let Some(t) = e.tick {
            match last {
                Some(l) if t < l => return Err(format!("event {}: tick {} after tick {} — a tick ran backwards", k, t, l)),
                Some(l) if t == l && e.look => return Err(format!("event {}: a look that is not the first event of tick {}", k, t)),
                _ => {}
            }
            last = Some(t);
        }
    }
    match (ticks, last) {
        (None, Some(_)) => Err("an event carries a tick but the session has no tick block".to_string()),
        (None, None) => Ok(()),
        (Some((hz, count, multiplier, step)), _) => {
            if hz != TICK_HZ as i64 || count < 0 || !(Sens { multiplier, step }).valid() {
                return Err(format!("the tick block (hz {}, count {}, multiplier {}, step {}) is not a registered one", hz, count, multiplier, step));
            }
            match last {
                Some(l) if l as i128 >= count as i128 => Err(format!("tick {} is not below the session's tick count {}", l, count)),
                _ => Ok(()),
            }
        }
    }
}

/// The laws, as lines the gate compares with its own derivation. `sha` hashes bytes to hex; nothing here hashes.
pub fn law_lines(sha: fn(&[u8]) -> String) -> Vec<String> {
    let letter = |c: u8| ['N', 'E', 'S', 'W'][c as usize];
    let mut out = Vec::new();
    out.push(format!("tick {} {}", TICK_HZ, TICK_US));
    let times: [u64; 9] = [0, 1, 15_624, 15_625, 15_626, 31_249, 31_250, 999_999, 1_000_000];
    out.push(format!("tick_of {}", times.iter().map(|t| format!("{}={}", t, tick_of(*t))).collect::<Vec<_>>().join(" ")));
    let mut letters = Vec::with_capacity(YAW_MOD as usize);
    let mut owns = [0u64; 4];
    let mut quarter = 0u64;
    for k in 0..YAW_MOD {
        let c = cardinal(k);
        letters.push(letter(c) as u8);
        owns[c as usize] += 1;
        if cardinal(turn(k, QUARTER)) == (c + 1) % 4 && cardinal(turn(k, -QUARTER)) == (c + 3) % 4 {
            quarter += 1;
        }
    }
    out.push(format!("cardinal_digest {}", sha(&letters)));
    out.push(format!("cardinal_owns N={} E={} S={} W={}", owns[0], owns[1], owns[2], owns[3]));
    let edges: [i64; 10] = [0, 44_999, 45_000, 134_999, 135_000, 224_999, 225_000, 314_999, 315_000, 359_999];
    out.push(format!("boundaries {}", edges.iter().map(|k| format!("{}={}", k, letter(cardinal(*k)))).collect::<Vec<_>>().join(" ")));
    out.push(format!("quarter_law {}", quarter));
    let anchors: [i64; 8] = [0, 1, 89_999, 90_000, 180_000, 270_000, 270_001, 359_999];
    out.push(format!("anchors {}", anchors.iter().map(|k| format!("{}={}", k, anchor(*k).map(letter).unwrap_or('-'))).collect::<Vec<_>>().join(" ")));
    let ks: [i64; 11] = [0, 1, 44_999, 45_000, 89_999, 90_000, 179_999, 180_000, 269_999, 270_000, 359_999];
    let ds: [i64; 10] = [0, 1, 87, 88, 89_999, 90_000, 359_999, 360_000, 360_001, DELTA_MAX];
    let mut grid = String::new();
    for k in ks.iter() {
        for d in ds.iter() {
            for sign in [1i64, -1] {
                grid.push_str(&format!("{},{}={};", k, sign * d, turn(*k, sign * d)));
            }
        }
    }
    out.push(format!("turn_digest {}", sha(grid.as_bytes())));
    out.push(format!("turn {}", [(0i64, -1i64), (359_999, 1), (0, 360_000), (0, -360_000), (44_968, 88), (88, -176)].iter()
        .map(|(k, d)| format!("{}{:+}={}", k, d, turn(*k, *d))).collect::<Vec<_>>().join(" ")));
    let cs: [i64; 8] = [1, -1, 2, 511, -511, 65_536, COUNTS_MAX, -COUNTS_MAX];
    let mut grid = String::new();
    for c in cs.iter() {
        for m in [1i64, 2, 63, 64] {
            for s in [STEP_FINE, STEP_COARSE] {
                grid.push_str(&format!("{},{},{}={};", c, m, s, delta(*c, Sens { multiplier: m, step: s }).map(|d| d.to_string()).unwrap_or_else(|| "refused".to_string())));
            }
        }
    }
    out.push(format!("delta_digest {}", sha(grid.as_bytes())));
    let show = |c: i64, m: i64, s: i64| format!("{},{},{}={}", c, m, s, delta(c, Sens { multiplier: m, step: s }).map(|d| d.to_string()).unwrap_or_else(|| "refused".to_string()));
    out.push(format!("delta {}", [show(1, 1, 88), show(-3, 2, 88), show(32, 1, 1), show(COUNTS_MAX, 64, 88), show(COUNTS_MAX + 1, 1, 1), show(-COUNTS_MAX - 1, 1, 1),
                                 show(1, 0, 88), show(1, 65, 88), show(1, 1, 87), show(1, 1, 2)].join(" ")));
    let s = |x: Option<Sens>| x.map(|v| format!("{},{}", v.multiplier, v.step)).unwrap_or_else(|| "refused".to_string());
    out.push(format!("sens start={} up(1)={} up(64)={} down(1)={} down(64)={} toggle(coarse)={} toggle(fine)={}",
                     s(Some(START)), s(START.up()), s(Sens { multiplier: MULT_MAX, step: STEP_COARSE }.up()), s(START.down()),
                     s(Sens { multiplier: MULT_MAX, step: STEP_COARSE }.down()), s(Some(START.toggled())), s(Some(START.toggled().toggled()))));
    out.push(format!("rebind {}", [0x41u32, 0x44, 0x57, 0x53, 0x51, 0x45, 0x25, 0x27, 0x20].iter().map(|v| format!("{:02X}={:02X}", v, rebind(*v))).collect::<Vec<_>>().join(" ")));
    out
}
