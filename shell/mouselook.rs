// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/mouselook.rs — MOUSE-LOOK-0: the tick source of the live loop.
//
//   real mouse -> 64 Hz accumulator -> command -> the existing live loop
//
// The rules are SIM-TICK-0's and SIM-TICK-0a's (shell/simtick.rs), and a command is applied by the tick run's own
// function (shell/tickrun.rs): nothing here decides what an input means. This module is what the rules left out.
//
//   Look     where a tick's raw inputs and its clock come from: the microseconds since the run began, the horizontal
//            mouse counts the shell admitted since the last call, and the mouse's release. On the host these are the
//            window's (QueryPerformanceCounter, raw input, the cursor's capture); on the gate, the mock's below.
//   Ticker   one composition's work under a tick source: every input drained now is stamped with the tick of now; a tick
//            whose end the clock has passed is closed and its command applied, once; then the composition's inputs are
//            fed to the tick now open. So a look is applied once a tick, at the first composition after its tick ends.
//   sample   every 64th frame event at a free heading in the run is recomputed by the reference on a worker thread,
//            off the loop. The loop asks, each composition, whether a sample has come back different; a difference ends
//            the run refused. A sample certifies nothing: the save still recomputes every free-heading frame.
//
// CAPTURE IS SHELL STATE. Whether the window is in the foreground, and whether the cursor is hidden and confined, decide
// only whether a raw count or a key reaches `reports()` or `keys()` at all. Nothing here, and nothing in the session,
// knows that the focus changed: no look of zero, no pause event, no synthetic input. The shell owns where the mouse is
// allowed to speak; the session owns what the mouse actually said.
//
// No latency is claimed anywhere: an input is applied up to one tick and one composition after it is drained.

use std::collections::VecDeque;
use std::thread::JoinHandle;

use crate::latency1r::Surface;
use crate::liveinput::Keys;
use crate::playback::LiveSession;
use crate::presentexact::{Attribution, ExactSurface};
use crate::refusallog::V;
use crate::simtick::{self, Accumulator, Command, Input};
use crate::tickrun::{self, Run};

/// The reference recomputes one free-heading frame event in this many.
pub const SAMPLE_EVERY: u64 = 64;
/// Under a tick source the screen is read back at the first composition and at every one of this many after it.
pub const READBACK_EVERY: u64 = 75;
/// The mock's clock: one composition every this many microseconds (the 75 Hz panel's period).
pub const MOCK_PERIOD_US: u64 = 13_333;

/// Where a tick's raw inputs and its clock come from.
pub trait Look {
    /// Microseconds since the run began.
    fn now_us(&mut self) -> u64;
    /// The horizontal mouse counts that arrived since the last call, in order — only those the shell admitted.
    fn reports(&mut self) -> Vec<i64>;
    /// Release the mouse: the run is ending. Shell state; the session never hears of it.
    fn release(&mut self);
}

/// The loop's handle on a tick source: plain functions over the surface. The clockless entry points pass none.
pub struct Source<S> {
    pub now_us: fn(&mut S) -> u64,
    pub reports: fn(&mut S) -> Vec<i64>,
}

impl<S: Look> Source<S> {
    pub fn of() -> Source<S> {
        Source { now_us: S::now_us, reports: S::reports }
    }
}

/// What one composition's step did.
pub struct Step {
    pub changed: bool,
    pub ended: bool,
}

type Sample = JoinHandle<Result<(), (usize, String)>>;

/// The live loop's ticker: the accumulator, the tick being gathered, the run's counts and the samples in flight.
pub struct Ticker {
    acc: Accumulator,
    open: Option<u64>,
    pub run: Run,
    free: u64,
    pending: VecDeque<Sample>,
    /// The samples handed to the reference; the largest number of ticks the clock moved between two compositions.
    pub samples: u64,
    pub span: u64,
    last: Option<u64>,
    ended: bool,
}

fn joined(done: Sample) -> Result<(), (usize, String)> {
    match done.join() {
        Ok(r) => r,
        Err(_) => Err((0, "a sample's thread did not finish".to_string())),
    }
}

impl Ticker {
    /// A ticker for a session: its ticks continue after the session's tick count, under HOLD-WALK-0's held set.
    pub fn new(session: &LiveSession) -> Ticker {
        Ticker { acc: Accumulator::holding(Some(crate::holdwalk::held)), open: None, run: Run::begin(session), free: 0,
                 pending: VecDeque::new(), samples: 0, span: 0, last: None, ended: false }
    }

    /// Apply one closed tick's command through the tick run, then count the frame events it appended at free headings
    /// and hand every 64th of them to the reference, off the loop.
    fn apply(&mut self, session: &mut LiveSession, cmd: &Command, surface: &'static str, step: &mut Step) {
        let before = session.log().len();
        let ended = tickrun::apply(session, cmd, &mut self.run, surface);
        for k in before..session.log().len() {
            let frame = {
                let ev = &session.log()[k];
                (ev.tag == b'M' || ev.tag == b'K') && simtick::anchor(ev.yaw).is_none()
            };
            if frame {
                self.free += 1;
                if self.free % SAMPLE_EVERY == 0 {
                    if let Some(frame) = session.free_frame_at(k) {
                        self.samples += 1;
                        self.pending.push_back(std::thread::spawn(move || crate::heading::certify(&[frame], 1)));
                    }
                }
            }
        }
        step.changed = step.changed || session.log().len() > before;
        if ended {
            self.ended = true;
            self.run.ended = "escape";
            self.run.ticks = cmd.tick + 1;
            step.ended = true;
        }
    }

    /// One composition under the tick source: close the tick the clock has passed and apply its command, then stamp
    /// this composition's key presses and mouse reports with the tick of `now_us` and feed them to the tick now open.
    /// Every input a composition drains takes that composition's tick, so one tick is open at a time and a composition
    /// applies at most one command.
    pub fn step(&mut self, session: &mut LiveSession, now_us: u64, keys: Vec<(u32, bool)>, reports: Vec<i64>, surface: &'static str) -> Step {
        let mut step = Step { changed: false, ended: false };
        if self.ended {
            return step;
        }
        let tick = self.run.first_tick + simtick::tick_of(now_us);
        if let Some(before) = self.last {
            self.span = self.span.max(tick.saturating_sub(before));
        }
        self.last = Some(tick);
        if let Some(t) = self.open {
            if t < tick {
                self.open = None;
                if let Some(cmd) = self.acc.close() {
                    self.apply(session, &cmd, surface, &mut step);
                }
            }
        }
        if step.ended {
            return step;
        }
        let inputs = keys.into_iter().map(|(vk, repeat)| if repeat { Input::Repeat(vk) } else { Input::Key(vk) })
            .chain(reports.into_iter().map(Input::Mouse));
        for input in inputs {
            match self.acc.feed(tick, input) {
                Ok(_) => {
                    // the tick was closed above if the clock had passed it: feeding never hands a command back here
                    self.open = Some(tick);
                    self.run.count(input);
                    self.run.ticks = tick + 1;
                }
                Err(m) => {
                    // a report outside the bound: one record, no input; the tick's other inputs stand
                    self.run.refused += 1;
                    crate::refusallog::record(&crate::refusallog::Event {
                        operation: "livesession", surface, reason: crate::refusallog::code_of(&m), attribution: "input.report",
                        context: vec![("tick", V::N(tick))] });
                    println!("[look] tick {}: an input was refused: {}", tick, m);
                }
            }
        }
        step
    }

    /// The samples that have come back, oldest first: Ok unless one differed (its event, and what happened). A sample
    /// is only read once every sample before it has been, so the first difference reported is the earliest one.
    pub fn poll(&mut self) -> Result<(), (usize, String)> {
        while self.pending.front().map_or(false, |h| h.is_finished()) {
            if let Some(done) = self.pending.pop_front() {
                joined(done)?;
            }
        }
        Ok(())
    }

    /// The run is ending. If the window closed (no Esc), the tick still open is closed and its command applied. The
    /// session's tick count is set, and every sample in flight is waited for, oldest first.
    pub fn finish(&mut self, session: &mut LiveSession, surface: &'static str) -> Result<(), (usize, String)> {
        if !self.ended {
            self.open = None;
            if let Some(cmd) = self.acc.close() {
                let mut step = Step { changed: false, ended: false };
                self.apply(session, &cmd, surface, &mut step);
            }
            if !self.ended {
                self.run.ended = "closed";
            }
        }
        self.run.sens = session.sensitivity();
        session.set_tick_count(Some(self.run.ticks));
        while let Some(done) = self.pending.pop_front() {
            joined(done)?;
        }
        Ok(())
    }
}

/// What the loop did under the tick source, for the saved session's live block: recorded beside the focus observation,
/// outside the session's data — counts of compositions, never events and never times.
pub fn live_json(l: &crate::liveinput::Live) -> String {
    format!("{{\"rung\":\"MOUSE-LOOK-0\",\"tick_hz\":{},\"compositions\":{},\"picture\":{},\"composite\":{},\"repeated\":{},\"screen_readbacks\":{},\"screen_differed\":{},\"readback_every\":{},\"samples\":{},\"sample_every\":{},\"span\":{}}}",
            simtick::TICK_HZ, l.compositions, l.looked, l.rendered, l.repeated, l.screen_readbacks, l.screen_differed, READBACK_EVERY, l.samples,
            SAMPLE_EVERY, l.span)
}

/// The look run's output for the gate: the tick run's own output (the trace and the counts), and what the loop did —
/// its compositions, how many showed the session's picture and how many the composite, how many repeated the picture
/// before them, the readbacks (each one's composition, camera token and the sha256 of the picture handed to the call),
/// the samples. The events themselves are the saved session's; this is the gate's scratch, not a record.
pub fn raw_json(l: &crate::liveinput::Live, s: &LiveSession) -> String {
    let esc = crate::refusallog::esc;
    let tick = l.tick.as_ref().map_or("null".to_string(), |r| tickrun::raw_json(r, s));
    let read: Vec<String> = l.read.iter().map(|(c, token, sha)| format!("[{},{},{}]", c, esc(token), esc(sha))).collect();
    format!("{{\"name\":\"verdandi-look-selftest\",\"data\":{{\"tick\":{},\"loop\":{{\"compositions\":{},\"picture\":{},\"composite\":{},\"repeated\":{},\"presented\":{},\"references\":{},\"byte_checks\":{},\"screen_readbacks\":{},\"screen_differed\":{},\"samples\":{},\"span\":{},\"read\":[{}],\"sample_every\":{},\"readback_every\":{},\"period_us\":{},\"ended\":{}}}}}}}",
            tick, l.compositions, l.looked, l.rendered, l.repeated, l.presented, l.references, l.byte_checks, l.screen_readbacks, l.screen_differed,
            l.samples, l.span, read.join(","), SAMPLE_EVERY, READBACK_EVERY, MOCK_PERIOD_US, esc(l.ended))
}

// ------------------------------------------------------------------ the mock: a scripted mouse, keyboard, focus and clock
/// One scripted thing: a raw input, or the window leaving or regaining the foreground.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Item {
    Input(Input),
    Blur,
    Focus,
}

/// The mock's script: comma-separated `T:WHAT` as the tick run's script (`T:m+N`, `T:KEY`, `T:KEY+`; T in microseconds,
/// never decreasing), plus `T:blur` and `T:focus`. A window has keys and a mouse: the typed tokens `mult+`, `mult-` and
/// `step` are not inputs it can receive (PGUP, PGDN and TAB are).
pub fn parse_script(s: &str) -> Result<Vec<(u64, Item)>, String> {
    let mut out: Vec<(u64, Item)> = Vec::new();
    for tok in s.split(',').map(|t| t.trim()).filter(|t| !t.is_empty()) {
        let item = match tok.split_once(':') {
            Some((t, what)) if what == "blur" || what == "focus" => {
                let canonical = !t.is_empty() && t.bytes().all(|c| c.is_ascii_digit()) && (t == "0" || !t.starts_with('0'));
                match (canonical, t.parse::<u64>()) {
                    (true, Ok(us)) => (us, if what == "blur" { Item::Blur } else { Item::Focus }),
                    _ => return Err(format!("script time {:?} is not whole microseconds", t)),
                }
            }
            _ => match simtick::parse_script(tok, tickrun::key_named)?.pop() {
                Some((_, Input::MultUp)) | Some((_, Input::MultDown)) | Some((_, Input::StepToggle)) => {
                    return Err(format!("script input {:?}: a window receives keys and a mouse (use PGUP, PGDN, TAB)", tok))
                }
                Some((us, input)) => (us, Item::Input(input)),
                None => return Err(format!("script token {:?} is empty", tok)),
            },
        };
        if let Some(&(last, _)) = out.last() {
            if item.0 < last {
                return Err(format!("script time {} is earlier than the input before it ({})", item.0, last));
            }
        }
        out.push(item);
    }
    Ok(out)
}

/// The mock's mouse, keyboard, focus and clock over any exact surface. At each pump the clock is the pump's index times
/// MOCK_PERIOD_US, and every scripted item whose time has come is delivered: a key press, a mouse report, or the window
/// leaving or regaining the foreground. While it is out of the foreground nothing is delivered — the items due then
/// are dropped and counted, as a window without the focus receives none. When the script is spent the window closes a
/// few pumps later. MOUSE-LOOK-0a: an admitted Esc (pressed or repeated) closes the window in the pump that delivers
/// it, and nothing scripted after it arrives — as on the host, where the presenter's window procedure destroys the
/// window when Esc is pressed.
pub struct ScriptedLook<S> {
    pub inner: S,
    script: Vec<(u64, Item)>,
    next: usize,
    pumps: u64,
    now: u64,
    foreground: bool,
    keys: Vec<(u32, bool)>,
    reports: Vec<i64>,
    pub blurs: u64,
    pub dropped: u64,
    pub released: bool,
    idle: u64,
    closed: bool,
}

impl<S> ScriptedLook<S> {
    pub fn new(inner: S, script: Vec<(u64, Item)>) -> ScriptedLook<S> {
        ScriptedLook { inner, script, next: 0, pumps: 0, now: 0, foreground: true, keys: Vec::new(), reports: Vec::new(),
                       blurs: 0, dropped: 0, released: false, idle: 0, closed: false }
    }
}

impl<S: ExactSurface> Surface for ScriptedLook<S> {
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
        // the loop pumps once before its first composition (to learn the geometry): the clock starts at the next pump
        self.now = self.pumps.saturating_sub(1) * MOCK_PERIOD_US;
        let first = self.pumps == 0;
        self.pumps += 1;
        if !self.inner.pump() {
            return false;
        }
        if first {
            return true;
        }
        while !self.closed && self.next < self.script.len() && self.script[self.next].0 <= self.now {
            match self.script[self.next].1 {
                Item::Blur => {
                    self.foreground = false;
                    self.blurs += 1;
                }
                Item::Focus => self.foreground = true,
                Item::Input(_) if !self.foreground => self.dropped += 1,
                Item::Input(Input::Mouse(c)) => self.reports.push(c),
                Item::Input(Input::Key(vk)) | Item::Input(Input::Repeat(vk)) => {
                    self.keys.push((vk, matches!(self.script[self.next].1, Item::Input(Input::Repeat(_)))));
                    // the host's window is destroyed by an Esc key-down, in the pump that reads it
                    self.closed = vk == crate::liveinput::VK_ESCAPE;
                }
                Item::Input(_) => {}
            }
            self.next += 1;
        }
        if self.next >= self.script.len() {
            self.idle += 1;
        }
        !self.closed && self.idle <= 8
    }
}

impl<S: ExactSurface> ExactSurface for ScriptedLook<S> {
    fn set_call(&mut self, call: usize) {
        self.inner.set_call(call)
    }
    fn clear(&mut self) -> bool {
        self.inner.clear()
    }
    fn readback(&mut self) -> Option<Vec<u8>> {
        self.inner.readback()
    }
    fn geometry(&mut self) -> [i32; 8] {
        self.inner.geometry()
    }
    fn attribute(&mut self, b: [usize; 4]) -> Attribution {
        self.inner.attribute(b)
    }
}

impl<S> Keys for ScriptedLook<S> {
    fn keys(&mut self) -> Vec<(u32, bool)> {
        std::mem::replace(&mut self.keys, Vec::new())
    }
}

impl<S> Look for ScriptedLook<S> {
    fn now_us(&mut self) -> u64 {
        self.now
    }
    fn reports(&mut self) -> Vec<i64> {
        std::mem::replace(&mut self.reports, Vec::new())
    }
    fn release(&mut self) {
        self.released = true;
    }
}

impl<S> crate::livesession::Focus for ScriptedLook<S> {
    fn focus(&self) -> String {
        format!("{{\"source\":\"mock\",\"mouse\":{{\"blurs\":{},\"dropped\":{},\"released\":{}}}}}", self.blurs, self.dropped, self.released)
    }
}
