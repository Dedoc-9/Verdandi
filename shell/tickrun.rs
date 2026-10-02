// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/tickrun.rs — SIM-TICK-0: the tick run. Raw inputs with their times -> one command per tick -> the session.
//
//   raw input (a time, a mouse report or a key or a sensitivity action)
//     -> shell/simtick.rs: the tick of its time, the accumulator, the tick's command
//     -> here: the command applied to playback::LiveSession — the look once and first, with the sensitivity in force
//        when the tick began; then the tick's other inputs in arrival order, bound as the live editor binds them with
//        A and D the strafes
//     -> the session: every event replayed, witnessed, folded, journaled (shell/livesession.rs)
//
// Windowless: there is no surface, no loop, no present and no clock here; a time is the script's integer. A refused
// input — a look whose counts leave the bound, the multiplier pushed past its ends, an edit the session refuses — is one
// refusal-log record and no event, and the run goes on. Esc ends the run; so does the end of the script. The session's
// tick block (the tick count and the sensitivity) is set when the run ends, and a resumed session's ticks follow its
// parent's.
//
// SIM-TICK-0a: the sensitivity is the session's (replayed configuration): an action that takes effect is appended as a
// sensitivity event, and the look reads the configuration from the session. PgUp, PgDn and Tab are the control keys
// (simtick::control), resolved before the editor's binding. A held key's repeat arrives already admitted, coalesced or
// ignored by the accumulator under HOLD-WALK-0's held set: a walked repeat is bound as its key's press, and the others
// are counted and traced, never events.

use crate::liveinput::{toggle, Action};
use crate::playback::LiveSession;
use crate::refusallog::V;
use crate::simtick::{self, Accumulator, Act, Command, Input, Sens};

/// What one tick run did: counts, the per-outcome trace, the tick count and sensitivity it ended with. No timing.
pub struct Run {
    pub inputs: u64,
    pub reports: u64,
    pub keys: u64,
    pub actions: u64,
    pub commands: u64,
    pub looks: u64,
    pub events: u64,
    pub moves: u64,
    pub blocked: u64,
    pub edits: u64,
    pub unbound: u64,
    pub refused: u64,
    /// SIM-TICK-0a: the sensitivity events appended; the repeats among the key presses, and how many of them walked,
    /// were coalesced or were ignored.
    pub settings: u64,
    pub repeats: u64,
    pub walked: u64,
    pub coalesced: u64,
    pub ignored: u64,
    pub first_tick: u64,
    pub ticks: u64,
    pub sens: Sens,
    pub ended: &'static str,
    pub trace: Vec<String>,
}

/// A key's name under ticks: the three control keys, else the live editor's names.
pub fn key_name(vk: u32) -> String {
    match vk {
        0x21 => "PGUP".to_string(),
        0x22 => "PGDN".to_string(),
        0x09 => "TAB".to_string(),
        other => crate::liveinput::key_name(other),
    }
}

/// A script name's key code: the inverse of `key_name`.
pub fn key_named(name: &str) -> Option<u32> {
    match name {
        "PGUP" => Some(0x21),
        "PGDN" => Some(0x22),
        "TAB" => Some(0x09),
        other => crate::liveinput::vk_named(other),
    }
}

fn refuse(run: &mut Run, surface: &'static str, tick: u64, what: &str, code: &str, attribution: &'static str, why: &str) {
    run.refused += 1;
    crate::refusallog::record(&crate::refusallog::Event {
        operation: "livesession", surface, reason: code.to_string(), attribution,
        context: vec![("tick", V::N(tick)), ("input", V::S(what.to_string()))] });
    println!("[simtick] tick {} {} -> refused {}: {}", tick, what, code, why);
    run.trace.push(format!("tick {} {} -> refused {}", tick, what, code));
}

/// SIM-TICK-0a: one sensitivity action — the session's configuration moved by one legal transition and recorded as a
/// sensitivity event, or refused at the multiplier's ends (one record, no event).
fn configure(session: &mut LiveSession, action: Input, what: &str, tick: u64, run: &mut Run, surface: &'static str) {
    let now = session.sensitivity();
    let next = match action {
        Input::MultUp => now.up(),
        Input::MultDown => now.down(),
        _ => Some(now.toggled()),
    };
    let k = session.log().len();
    match next.ok_or_else(|| format!("the multiplier stays inside {}..{}", simtick::MULT_MIN, simtick::MULT_MAX)).and_then(|n| session.push_sensitivity(n).map(|_| n)) {
        Ok(n) => {
            run.settings += 1;
            println!("[simtick] tick {} {} -> event {}: sensitivity {},{}", tick, what, k, n.multiplier, n.step);
            run.trace.push(format!("tick {} {} -> event {} sensitivity {},{}", tick, what, k, n.multiplier, n.step));
        }
        Err(m) => refuse(run, surface, tick, what, "SIMTICK-MULTIPLIER", "input.sensitivity", &m),
    }
}

/// One tick's command applied to the session. Returns whether the run ended (Esc).
fn apply(session: &mut LiveSession, cmd: &Command, run: &mut Run, surface: &'static str) -> bool {
    run.commands += 1;
    session.at_tick(Some(cmd.tick));
    // the look: once, first, with the sensitivity in force when the tick began (the session's own)
    let sens = session.sensitivity();
    if cmd.over {
        refuse(run, surface, cmd.tick, "look", "SIMTICK-COUNTS", "input.look", "the tick's counts leave +-(2^31 - 1); the look is refused, the tick's other inputs still apply");
    } else if cmd.counts != 0 {
        let what = format!("look counts={} multiplier={} step={}", cmd.counts, sens.multiplier, sens.step);
        let pushed = match simtick::delta(cmd.counts, sens) {
            Some(d) => session.push_look(d, Some((cmd.counts, sens.multiplier, sens.step))).map(|ev| (d, crate::playback::token(ev.camera, ev.yaw), ev.head.clone())),
            None => Err("the delta is outside the bound".to_string()),
        };
        match pushed {
            Ok((d, tok, head)) => {
                let k = session.log().len() - 1;
                run.events += 1;
                run.looks += 1;
                println!("[simtick] tick {} {} -> event {}: look {} -> {} head {}", cmd.tick, what, k, d, tok, &head[..12]);
                run.trace.push(format!("tick {} {} -> event {} look {} {}", cmd.tick, what, k, d, tok));
            }
            Err(m) => refuse(run, surface, cmd.tick, &what, "SIMTICK-LOOK", "input.look", &m),
        }
    }
    // then the tick's other inputs, in arrival order
    for act in cmd.acts.iter() {
        let (vk, repeat) = match *act {
            Act::MultUp => {
                configure(session, Input::MultUp, "mult+", cmd.tick, run, surface);
                continue;
            }
            Act::MultDown => {
                configure(session, Input::MultDown, "mult-", cmd.tick, run, surface);
                continue;
            }
            Act::StepToggle => {
                configure(session, Input::StepToggle, "step", cmd.tick, run, surface);
                continue;
            }
            Act::Coalesced(vk) => {
                // SIM-TICK-0a: a held key's repeat behind the tick's walked one: counted and traced, never an event
                run.coalesced += 1;
                run.trace.push(format!("tick {} key {}+ -> coalesced", cmd.tick, key_name(vk)));
                continue;
            }
            Act::Ignored(vk) => {
                // a repeat of a key that does not walk: the edit, the strafe or the setting happened once
                run.ignored += 1;
                run.trace.push(format!("tick {} key {}+ -> repeat", cmd.tick, key_name(vk)));
                continue;
            }
            Act::Key(vk) => (vk, false),
            Act::Walked(vk) => {
                run.walked += 1;
                (vk, true)
            }
        };
        let what = format!("key {}{}", key_name(vk), if repeat { "+" } else { "" });
        // SIM-TICK-0a: the control keys are resolved first; their effect, not the key, is what the session records
        if let Some(action) = simtick::control(vk) {
            configure(session, action, &what, cmd.tick, run, surface);
            continue;
        }
        let k = session.log().len(); // the index an event appended now takes in the session's log
        match crate::liveauthor::bind(simtick::rebind(vk)) {
            Action::End => {
                println!("[simtick] tick {} {} -> end", cmd.tick, what);
                run.trace.push(format!("tick {} {} -> end", cmd.tick, what));
                session.at_tick(None);
                return true;
            }
            Action::Unbound => {
                run.unbound += 1;
                println!("[simtick] tick {} {} -> unbound (ignored)", cmd.tick, what);
                run.trace.push(format!("tick {} {} -> unbound", cmd.tick, what));
            }
            Action::Move(c) => {
                let before = session.camera();
                match session.push_move(c).map(|ev| (ev.camera, crate::playback::token(ev.camera, ev.yaw), ev.head.clone())) {
                    Ok((cam, tok, head)) => {
                        let blocked = matches!(c, b'F' | b'B' | b'Q' | b'E') && cam.x == before.x && cam.z == before.z;
                        run.events += 1;
                        run.moves += 1;
                        if blocked {
                            run.blocked += 1;
                        }
                        println!("[simtick] tick {} {} -> event {}: move {} -> {}{} head {}", cmd.tick, what, k, c as char, tok,
                                 if blocked { " (blocked)" } else { "" }, &head[..12]);
                        run.trace.push(format!("tick {} {} -> event {} move {} {}", cmd.tick, what, k, c as char, tok));
                    }
                    Err(m) => refuse(run, surface, cmd.tick, &what, "SIMTICK-MOVE", "input.move", &m),
                }
            }
            Action::Toggle => {
                let faced = session.faced();
                let pushed = toggle(faced, session.cell(faced.0, faced.1)).and_then(|(x, z, to)| {
                    session.push_edit_cell(x, z, to).map(|ev| (ev.param.clone(), ev.head.clone())).map_err(|(code, m)| {
                        (match code {
                            "BORDER" => "LIVEINPUT-EDIT-BORDER",
                            "OUTSIDE" => "LIVEINPUT-EDIT-OUTSIDE",
                            _ => "LIVEINPUT-EDIT-VALUE",
                        }, m)
                    })
                });
                match pushed {
                    Ok((spec, head)) => {
                        run.events += 1;
                        run.edits += 1;
                        println!("[simtick] tick {} {} -> event {}: edit {} head {}", cmd.tick, what, k, spec, &head[..12]);
                        run.trace.push(format!("tick {} {} -> event {} edit {}", cmd.tick, what, k, spec));
                    }
                    Err((code, m)) => refuse(run, surface, cmd.tick, &what, code, "input.edit", &m),
                }
            }
            Action::Tile(class) => {
                let rgb = crate::liveauthor::next_colour(session.tile_rgb(class));
                match session.push_edit_tile(class, rgb).map(|ev| (ev.param.clone(), ev.head.clone())) {
                    Ok((spec, head)) => {
                        run.events += 1;
                        run.edits += 1;
                        println!("[simtick] tick {} {} -> event {}: edit {} head {}", cmd.tick, what, k, spec, &head[..12]);
                        run.trace.push(format!("tick {} {} -> event {} edit {}", cmd.tick, what, k, spec));
                    }
                    Err(m) => refuse(run, surface, cmd.tick, &what, "SIMTICK-EDIT", "input.edit", &m),
                }
            }
        }
    }
    session.at_tick(None);
    false
}

/// The run: every scripted input fed to the accumulator at its tick, each finished tick's command applied, until Esc or
/// the end of the script. The session's ticks continue after its parent's; its tick count is set at the end.
pub fn run(session: &mut LiveSession, script: &[(u64, Input)], surface: &'static str) -> Result<Run, String> {
    let first = session.ticks().map_or(0, |(count, _, _)| count);
    let mut run = Run { inputs: 0, reports: 0, keys: 0, actions: 0, commands: 0, looks: 0, events: 0, moves: 0, blocked: 0, edits: 0,
                        unbound: 0, refused: 0, settings: 0, repeats: 0, walked: 0, coalesced: 0, ignored: 0,
                        first_tick: first, ticks: first, sens: session.sensitivity(), ended: "script", trace: Vec::new() };
    // SIM-TICK-0a: HOLD-WALK-0's held set, with the tick as the coalescing boundary
    let mut acc = Accumulator::holding(Some(crate::holdwalk::held));
    let mut ended_at: Option<u64> = None;
    for &(us, input) in script.iter() {
        let tick = first + simtick::tick_of(us);
        if let Some(cmd) = acc.feed(tick, input)? {
            if apply(session, &cmd, &mut run, surface) {
                ended_at = Some(cmd.tick);
                break;
            }
        }
        run.inputs += 1;
        match input {
            Input::Mouse(_) => run.reports += 1,
            Input::Key(_) => run.keys += 1,
            Input::Repeat(_) => {
                run.keys += 1;
                run.repeats += 1;
            }
            _ => run.actions += 1,
        }
        run.ticks = tick + 1;
    }
    if ended_at.is_none() {
        if let Some(cmd) = acc.close() {
            if apply(session, &cmd, &mut run, surface) {
                ended_at = Some(cmd.tick);
            }
        }
    }
    if let Some(t) = ended_at {
        run.ended = "escape";
        run.ticks = t + 1;
    }
    run.sens = session.sensitivity();
    session.set_tick_count(Some(run.ticks));
    Ok(run)
}

/// The run's console summary.
pub fn summary(r: &Run, s: &LiveSession) -> Vec<String> {
    vec![
        format!("simtick inputs {} reports {} keys {} actions {} commands {} looks {} events {} moves {} blocked {} edits {} unbound {} refused {} ended {}",
                r.inputs, r.reports, r.keys, r.actions, r.commands, r.looks, r.events, r.moves, r.blocked, r.edits, r.unbound, r.refused, r.ended),
        format!("simtick sensitivity events {} repeats {} walked {} coalesced {} ignored {}", r.settings, r.repeats, r.walked, r.coalesced, r.ignored),
        format!("simtick ticks {}..{} sensitivity {},{}", r.first_tick, r.ticks, r.sens.multiplier, r.sens.step),
        format!("simtick final camera {} content {} head {}", s.token(), s.content(), s.head()),
    ]
}

fn esc(s: &str) -> String {
    crate::refusallog::esc(s)
}

/// The run's output for the gate: the trace and the counts. The events themselves are the saved session's; this is the
/// gate's scratch, not a record.
pub fn raw_json(r: &Run, s: &LiveSession) -> String {
    let trace: Vec<String> = r.trace.iter().map(|t| esc(t)).collect();
    format!("{{\"name\":\"verdandi-simtick-selftest\",\"data\":{{\"trace\":[{}],\"counts\":{{\"inputs\":{},\"reports\":{},\"keys\":{},\"actions\":{},\"commands\":{},\"looks\":{},\"events\":{},\"moves\":{},\"blocked\":{},\"edits\":{},\"unbound\":{},\"refused\":{},\"settings\":{},\"repeats\":{},\"walked\":{},\"coalesced\":{},\"ignored\":{}}},\"first_tick\":{},\"ticks\":{},\"sensitivity\":[{},{}],\"ended\":{},\"final\":{{\"camera\":{},\"content\":{},\"head\":{}}}}}}}",
            trace.join(","), r.inputs, r.reports, r.keys, r.actions, r.commands, r.looks, r.events, r.moves, r.blocked, r.edits, r.unbound, r.refused,
            r.settings, r.repeats, r.walked, r.coalesced, r.ignored,
            r.first_tick, r.ticks, r.sens.multiplier, r.sens.step, esc(r.ended), esc(&s.token()), esc(s.content()), esc(s.head()))
}
