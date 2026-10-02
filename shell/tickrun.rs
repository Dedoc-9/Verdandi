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

use crate::liveinput::{key_name, toggle, Action};
use crate::playback::LiveSession;
use crate::refusallog::V;
use crate::simtick::{self, Accumulator, Command, Input, Sens};

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
    pub first_tick: u64,
    pub ticks: u64,
    pub sens: Sens,
    pub ended: &'static str,
    pub trace: Vec<String>,
}

fn refuse(run: &mut Run, surface: &'static str, tick: u64, what: &str, code: &str, attribution: &'static str, why: &str) {
    run.refused += 1;
    crate::refusallog::record(&crate::refusallog::Event {
        operation: "livesession", surface, reason: code.to_string(), attribution,
        context: vec![("tick", V::N(tick)), ("input", V::S(what.to_string()))] });
    println!("[simtick] tick {} {} -> refused {}: {}", tick, what, code, why);
    run.trace.push(format!("tick {} {} -> refused {}", tick, what, code));
}

/// One tick's command applied to the session. Returns whether the run ended (Esc).
fn apply(session: &mut LiveSession, cmd: &Command, sens: &mut Sens, run: &mut Run, surface: &'static str) -> bool {
    run.commands += 1;
    session.at_tick(Some(cmd.tick));
    // the look: once, first, with the sensitivity in force when the tick began
    if cmd.over {
        refuse(run, surface, cmd.tick, "look", "SIMTICK-COUNTS", "input.look", "the tick's counts leave +-(2^31 - 1); the look is refused, the tick's other inputs still apply");
    } else if cmd.counts != 0 {
        let what = format!("look counts={} multiplier={} step={}", cmd.counts, sens.multiplier, sens.step);
        let pushed = match simtick::delta(cmd.counts, *sens) {
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
        match *act {
            Input::Mouse(_) => {} // a report is in the sum, never among the other inputs
            Input::MultUp | Input::MultDown => {
                let (what, next) = if *act == Input::MultUp { ("mult+", sens.up()) } else { ("mult-", sens.down()) };
                match next {
                    Some(n) => {
                        *sens = n;
                        println!("[simtick] tick {} {} -> sensitivity {},{}", cmd.tick, what, n.multiplier, n.step);
                        run.trace.push(format!("tick {} {} -> sensitivity {},{}", cmd.tick, what, n.multiplier, n.step));
                    }
                    None => refuse(run, surface, cmd.tick, what, "SIMTICK-MULTIPLIER", "input.sensitivity",
                                   &format!("the multiplier stays inside {}..{}", simtick::MULT_MIN, simtick::MULT_MAX)),
                }
            }
            Input::StepToggle => {
                *sens = sens.toggled();
                println!("[simtick] tick {} step -> sensitivity {},{}", cmd.tick, sens.multiplier, sens.step);
                run.trace.push(format!("tick {} step -> sensitivity {},{}", cmd.tick, sens.multiplier, sens.step));
            }
            Input::Key(vk) => {
                let what = format!("key {}", key_name(vk));
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
        }
    }
    session.at_tick(None);
    false
}

/// The run: every scripted input fed to the accumulator at its tick, each finished tick's command applied, until Esc or
/// the end of the script. The session's ticks continue after its parent's; its tick block is set at the end.
pub fn run(session: &mut LiveSession, script: &[(u64, Input)], surface: &'static str) -> Result<Run, String> {
    let (first, mut sens) = match session.ticks() {
        Some((count, multiplier, step)) => (count, Sens { multiplier, step }),
        None => (0, simtick::START),
    };
    let mut run = Run { inputs: 0, reports: 0, keys: 0, actions: 0, commands: 0, looks: 0, events: 0, moves: 0, blocked: 0, edits: 0,
                        unbound: 0, refused: 0, first_tick: first, ticks: first, sens, ended: "script", trace: Vec::new() };
    let mut acc = Accumulator::new();
    let mut ended_at: Option<u64> = None;
    for &(us, input) in script.iter() {
        let tick = first + simtick::tick_of(us);
        if let Some(cmd) = acc.feed(tick, input)? {
            if apply(session, &cmd, &mut sens, &mut run, surface) {
                ended_at = Some(cmd.tick);
                break;
            }
        }
        run.inputs += 1;
        match input {
            Input::Mouse(_) => run.reports += 1,
            Input::Key(_) => run.keys += 1,
            _ => run.actions += 1,
        }
        run.ticks = tick + 1;
    }
    if ended_at.is_none() {
        if let Some(cmd) = acc.close() {
            if apply(session, &cmd, &mut sens, &mut run, surface) {
                ended_at = Some(cmd.tick);
            }
        }
    }
    if let Some(t) = ended_at {
        run.ended = "escape";
        run.ticks = t + 1;
    }
    run.sens = sens;
    session.set_ticks(Some((run.ticks, sens.multiplier, sens.step)));
    Ok(run)
}

/// The run's console summary.
pub fn summary(r: &Run, s: &LiveSession) -> Vec<String> {
    vec![
        format!("simtick inputs {} reports {} keys {} actions {} commands {} looks {} events {} moves {} blocked {} edits {} unbound {} refused {} ended {}",
                r.inputs, r.reports, r.keys, r.actions, r.commands, r.looks, r.events, r.moves, r.blocked, r.edits, r.unbound, r.refused, r.ended),
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
    format!("{{\"name\":\"verdandi-simtick-selftest\",\"data\":{{\"trace\":[{}],\"counts\":{{\"inputs\":{},\"reports\":{},\"keys\":{},\"actions\":{},\"commands\":{},\"looks\":{},\"events\":{},\"moves\":{},\"blocked\":{},\"edits\":{},\"unbound\":{},\"refused\":{}}},\"first_tick\":{},\"ticks\":{},\"sensitivity\":[{},{}],\"ended\":{},\"final\":{{\"camera\":{},\"content\":{},\"head\":{}}}}}}}",
            trace.join(","), r.inputs, r.reports, r.keys, r.actions, r.commands, r.looks, r.events, r.moves, r.blocked, r.edits, r.unbound, r.refused,
            r.first_tick, r.ticks, r.sens.multiplier, r.sens.step, esc(r.ended), esc(&s.token()), esc(s.content()), esc(s.head()))
}
