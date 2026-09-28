// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/liveinput.rs — LIVE-INPUT-0: a key press becomes a typed event in the live session the loop renders.
//
// LIVE-LOOP-0 rendered every composition live from a sealed session's steps. This loop renders every composition live
// from a session being written as it runs:
//
//   physical key -> typed action (bind) -> an event appended to the in-memory SESSION-WALK log (playback::LiveSession)
//   -> the log's replay: W, M, the camera, the head -> LoopRenderer -> SetDIBitsToDevice -> the screen, read back
//
// The binding is fixed and pure: Up/W forward, Down/S back, Left/A turn left, Right/D turn right, Q and E strafe, Space
// opens or closes the faced cell (the cell one step ahead of the camera: rock opens to floor, floor closes to rock, a
// stair is not toggled), Esc ends. An auto-repeated press is counted and never bound (one press, one action); any other
// key is unbound and ignored. The loop never holds a world of its own: it appends events and reads the session's state,
// and the session's W and M are private to shell/playback.rs, changed only by the replay of an appended event. An edit
// the session refuses (a border cell stays rock) or a stair is one refusal-log record and no event; the loop goes on.
//
//   Every appended event: the fresh reference of the new state is rendered once, outside the compositions; for a move
//   its frame digest must be the event's chain witness (else the loop refuses: the loop would render a state the chain
//   did not witness), and its bytes are the expected bytes from then on.
//   Every composition: the window's events and key presses, the actions, render the current state through the
//   LoopRenderer, compare its composite and blit bytes with the expected bytes (a difference refuses), present, and — on
//   the first composition after a change and every RECHECK-th composition a state is held — read the composed screen
//   back and compare. A differing screen is counted and logged, never hidden, and the loop goes on.
//
// Esc or closing the window ends the session (exit 0). No clock, no file: the log lives in memory and dies with the run
// (persistence is LIVE-SESSION-0's). Refusals are data, logged where they are emitted; every run is one ledger line.

use crate::formats::{facing_letter, Camera};
use crate::latency1r::Surface;
use crate::mantle::{frame_digest, hex, sha256, Scene, H, W};
use crate::playback::LiveSession;
use crate::present::{arm_composite, to_blit, Arm, LoopRenderer};
use crate::presentexact::{describe, diff_bbox, Attribution, ExactSurface};
use crate::refusallog::V;

pub const RECHECK: u64 = 75;
pub const CALL: usize = 1; // SetDIBitsToDevice, the adopted call
pub const MOCK_EVERY: u64 = 3; // the mock delivers one scripted press every MOCK_EVERY compositions

pub const VK_SPACE: u32 = 0x20;
pub const VK_ESCAPE: u32 = 0x1B;
pub const VK_LEFT: u32 = 0x25;
pub const VK_UP: u32 = 0x26;
pub const VK_RIGHT: u32 = 0x27;
pub const VK_DOWN: u32 = 0x28;

/// A typed action: one of INPUT-0's six moves, the faced cell's open/close, a tile class's next colour (LIVE-AUTHOR-0's
/// binding only; LIVE-INPUT-0's never makes one), the end, or nothing.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Action {
    Move(u8),
    Toggle,
    Tile(u8),
    End,
    Unbound,
}

/// LIVE-INPUT-0's binding: one physical key (a Windows virtual-key code) to one typed action. Pure.
pub fn bind(vk: u32) -> Action {
    match vk {
        VK_UP | 0x57 => Action::Move(b'F'),    // Up, W: step forward
        VK_DOWN | 0x53 => Action::Move(b'B'),  // Down, S: step back
        VK_LEFT | 0x41 => Action::Move(b'L'),  // Left, A: turn left
        VK_RIGHT | 0x44 => Action::Move(b'R'), // Right, D: turn right
        0x51 => Action::Move(b'Q'),            // Q: strafe left
        0x45 => Action::Move(b'E'),            // E: strafe right
        VK_SPACE => Action::Toggle,            // Space: open or close the faced cell
        VK_ESCAPE => Action::End,              // Esc: the session ends
        _ => Action::Unbound,
    }
}

/// The faced cell's edit: rock opens to floor, floor closes to rock, a stair is not toggled. Pure: the same faced cell
/// holding the same value gives the same edit. The session then validates it (a border cell stays rock).
pub fn toggle(faced: (i64, i64), cell: Option<u8>) -> Result<(i64, i64, u8), (&'static str, String)> {
    match cell {
        Some(b'#') => Ok((faced.0, faced.1, b'.')),
        Some(b'.') => Ok((faced.0, faced.1, b'#')),
        Some(c) => Err(("LIVEINPUT-EDIT-STAIR", format!("the faced cell ({}, {}) is {:?}, a stair: LIVE-INPUT-0 opens and closes rock and floor only",
                                                       faced.0, faced.1, c as char))),
        None => Err(("LIVEINPUT-EDIT-OUTSIDE", format!("the faced cell ({}, {}) is outside the level", faced.0, faced.1))),
    }
}

/// A key's name, for the console and the mock's scripts.
pub fn key_name(vk: u32) -> String {
    match vk {
        VK_SPACE => "SPACE".to_string(),
        VK_ESCAPE => "ESC".to_string(),
        VK_LEFT => "LEFT".to_string(),
        VK_UP => "UP".to_string(),
        VK_RIGHT => "RIGHT".to_string(),
        VK_DOWN => "DOWN".to_string(),
        0x30..=0x39 | 0x41..=0x5A => ((vk as u8) as char).to_string(),
        0x70..=0x7B => format!("F{}", vk - 0x6F),
        _ => format!("VK{:02X}", vk),
    }
}

/// A script name's virtual-key code (the inverse of `key_name` over the names it prints).
pub fn vk_named(name: &str) -> Option<u32> {
    let b = name.as_bytes();
    match name {
        "SPACE" => Some(VK_SPACE),
        "ESC" => Some(VK_ESCAPE),
        "LEFT" => Some(VK_LEFT),
        "UP" => Some(VK_UP),
        "RIGHT" => Some(VK_RIGHT),
        "DOWN" => Some(VK_DOWN),
        _ if b.len() == 1 && (b[0].is_ascii_uppercase() || b[0].is_ascii_digit()) => Some(b[0] as u32),
        _ if b.len() >= 2 && b[0] == b'F' => match name[1..].parse::<u32>() {
            Ok(n) if (1..=12).contains(&n) => Some(0x6F + n),
            _ => None,
        },
        _ => None,
    }
}

/// A mock script: comma-separated key names, each with a trailing `+` if the press is an auto-repeat.
pub fn parse_script(s: &str) -> Result<Vec<(u32, bool)>, String> {
    let mut out = Vec::new();
    for tok in s.split(',').map(|t| t.trim()).filter(|t| !t.is_empty()) {
        let (name, repeat) = match tok.strip_suffix('+') {
            Some(n) => (n, true),
            None => (tok, false),
        };
        out.push((vk_named(name).ok_or_else(|| format!("unknown key {:?}", tok))?, repeat));
    }
    Ok(out)
}

/// Where key presses come from: the window's message queue on the host, a script on the mock.
pub trait Keys {
    /// The presses that arrived since the last call, in order: (virtual-key code, auto-repeat).
    fn keys(&mut self) -> Vec<(u32, bool)>;
}

/// The mock's keyboard: one scripted press every `every` pumps (the last pump of each group of `every`), over any exact
/// surface. When the script is spent, the next due pump closes the window.
pub struct ScriptedKeys<S> {
    pub inner: S,
    script: Vec<(u32, bool)>,
    every: u64,
    pumps: u64,
    next: usize,
    pending: Vec<(u32, bool)>,
}

impl<S> ScriptedKeys<S> {
    pub fn new(inner: S, script: Vec<(u32, bool)>, every: u64) -> ScriptedKeys<S> {
        ScriptedKeys { inner, script, every: every.max(1), pumps: 0, next: 0, pending: Vec::new() }
    }
}

impl<S: ExactSurface> Surface for ScriptedKeys<S> {
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
        let p = self.pumps;
        self.pumps += 1;
        if !self.inner.pump() {
            return false;
        }
        if p % self.every == self.every - 1 {
            if self.next >= self.script.len() {
                return false;
            }
            self.pending.push(self.script[self.next]);
            self.next += 1;
        }
        true
    }
}

impl<S: ExactSurface> ExactSurface for ScriptedKeys<S> {
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

impl<S> Keys for ScriptedKeys<S> {
    fn keys(&mut self) -> Vec<(u32, bool)> {
        std::mem::take(&mut self.pending)
    }
}

/// A LIVE-INPUT-0 refusal as data: where on the path it came from, a few facts, and its console message.
pub struct Refusal {
    pub attribution: &'static str,
    pub context: Vec<(&'static str, V)>,
    pub message: String,
}

impl Refusal {
    pub fn into_event(self, surface: &'static str) -> (crate::refusallog::Event, String) {
        let reason = crate::refusallog::code_of(&self.message);
        (crate::refusallog::Event { operation: "liveinput", surface, reason, attribution: self.attribution, context: self.context },
         self.message)
    }
}

fn refusal(attribution: &'static str, context: Vec<(&'static str, V)>, message: String) -> Refusal {
    Refusal { attribution, context, message }
}

/// One key press and what became of it: `event K` (appended as event K), `refused CODE`, `unbound`, `repeat` or `end`.
pub struct Typed {
    pub key: u32,
    pub repeat: bool,
    pub composition: u64,
    pub outcome: String,
}

/// What one run did: counts, the per-key trace, and the frame digest presented for every state (the initial state
/// first, then the state after each event). No timing.
pub struct Live {
    pub keys: u64,
    pub repeats: u64,
    pub unbound: u64,
    pub events: u64,
    pub moves: u64,
    pub blocked: u64,
    pub edits: u64,
    pub refused: u64,
    pub references: u64,
    pub compositions: u64,
    pub rendered: u64,
    pub byte_checks: u64,
    pub presented: u64,
    pub screen_readbacks: u64,
    pub screen_differed: u64,
    pub renders: u64,
    pub geometry: [i32; 8],
    pub ended: &'static str,
    pub trace: Vec<Typed>,
    pub views: Vec<String>,
    /// LIVE-AUTHOR-0: the sha256 of each state's reference composite (the pixels), in the order of `views`.
    pub pixels: Vec<String>,
    /// LIVE-AUTHOR-0: for each state the loop presented, the state and the sha256 of the composite it rendered at that
    /// state's first composition — what was actually handed to the call, beside what the state's reference is.
    pub shown: Vec<(u64, String)>,
}

fn cam_token(c: Camera) -> String {
    format!("{},{},{}", c.x, c.z, facing_letter(c.facing))
}

/// The fresh reference of the session's current state, rendered once when the state changes: its scene, its composite
/// and blit bytes, and its frame digest. For a move, the digest must be the event's chain witness.
fn reference(session: &LiveSession, witness: Option<(&str, u64)>) -> Result<(Scene, Vec<u8>, Vec<u8>, String, String), Refusal> {
    let scene = session.scene().map_err(|crate::mantle::Refusal(m)| {
        refusal("render.scene", vec![("camera", V::S(cam_token(session.camera())))], format!("LIVEINPUT-SCENE: the session's state does not compose: {}", m))
    })?;
    let (fr, comp) = arm_composite(&scene, Arm::Production);
    let view = frame_digest(&fr);
    if let Some((w, k)) = witness {
        if view != w {
            return Err(refusal("render.witness", vec![("event", V::N(k))],
                               format!("LIVEINPUT-WITNESS: the reference of event {}'s state does not reproduce the event's chain witness", k)));
        }
    }
    let bgr = to_blit(&comp);
    let px = hex(&sha256(&comp));
    Ok((scene, comp, bgr, view, px))
}

/// The run: the initial state's reference, then compositions until Esc or the window closes, each one's key presses
/// turned into events first, then the current state rendered live and presented. LIVE-INPUT-0's binding.
pub fn run<S: ExactSurface + Keys>(s: &mut S, session: &mut LiveSession, surface: &'static str) -> Result<Live, Refusal> {
    run_with(s, session, surface, bind)
}

/// The same run under a given binding (LIVE-AUTHOR-0's adds the tile classes; nothing else about the loop changes).
pub fn run_with<S: ExactSurface + Keys>(s: &mut S, session: &mut LiveSession, surface: &'static str, binding: fn(u32) -> Action) -> Result<Live, Refusal> {
    let _ = s.pump();
    let g = s.geometry();
    if g != [W as i32, H as i32, 0, 0, W as i32, H as i32, W as i32, H as i32] {
        return Err(refusal("window.geometry", vec![("geometry", V::S(format!("{:?}", g)))],
                           format!("LIVEINPUT-GEOMETRY: client {}x{} at ({},{}), screen logical {}x{} physical {}x{}; the target is {}x{} at (0,0) on a {}x{} screen",
                                   g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], W, H, W, H)));
    }
    s.set_call(CALL);
    let mut live = Live { keys: 0, repeats: 0, unbound: 0, events: 0, moves: 0, blocked: 0, edits: 0, refused: 0, references: 0,
                          compositions: 0, rendered: 0, byte_checks: 0, presented: 0, screen_readbacks: 0, screen_differed: 0,
                          renders: 0, geometry: g, ended: "", trace: Vec::new(), views: Vec::new(), pixels: Vec::new(), shown: Vec::new() };
    let (mut scene, mut expected, mut expected_bgr, view, px) = reference(session, None)?;
    live.references += 1;
    live.views.push(view);
    live.pixels.push(px);
    let mut lr = LoopRenderer::new();
    let (mut fresh, mut held, mut last): (bool, u64, Option<bool>) = (true, 0, None);
    let mut c: u64 = 0;
    loop {
        let open = s.pump();
        let mut end = false;
        for (vk, repeat) in s.keys() {
            live.keys += 1;
            let name = key_name(vk);
            if repeat {
                live.repeats += 1;
                live.trace.push(Typed { key: vk, repeat, composition: c, outcome: "repeat".to_string() });
                continue;
            }
            let outcome = match binding(vk) {
                Action::End => {
                    end = true;
                    "end".to_string()
                }
                Action::Unbound => {
                    live.unbound += 1;
                    println!("[liveinput] {} -> unbound (ignored)", name);
                    "unbound".to_string()
                }
                Action::Move(cmd) => {
                    let before = session.camera();
                    let k = live.events;
                    let (cam, witness, head) = match session.push_move(cmd) {
                        Ok(ev) => (ev.camera, ev.witness.clone(), ev.head.clone()),
                        Err(m) => {
                            return Err(refusal("render.scene", vec![("event", V::N(k))], format!("LIVEINPUT-SCENE: move {} did not replay: {}", cmd as char, m)))
                        }
                    };
                    let stepped = matches!(cmd, b'F' | b'B' | b'Q' | b'E');
                    let blocked = stepped && cam.x == before.x && cam.z == before.z;
                    live.events += 1;
                    live.moves += 1;
                    if blocked {
                        live.blocked += 1;
                    }
                    let r = reference(session, Some((&witness, k)))?;
                    live.references += 1;
                    scene = r.0;
                    expected = r.1;
                    expected_bgr = r.2;
                    live.views.push(r.3);
                    live.pixels.push(r.4);
                    fresh = true;
                    println!("[liveinput] {} -> event {}: move {} -> {}{} head {}", name, k, cmd as char, cam_token(cam),
                             if blocked { " (blocked)" } else { "" }, &head[..12]);
                    format!("event {}", k)
                }
                Action::Toggle => {
                    let faced = session.faced();
                    let cell = session.cell(faced.0, faced.1);
                    let k = live.events;
                    let pushed = toggle(faced, cell).and_then(|(x, z, to)| {
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
                            live.events += 1;
                            live.edits += 1;
                            let r = reference(session, None)?;
                            live.references += 1;
                            scene = r.0;
                            expected = r.1;
                            expected_bgr = r.2;
                            live.views.push(r.3);
                            live.pixels.push(r.4);
                            fresh = true;
                            println!("[liveinput] {} -> event {}: edit {} head {}", name, k, spec, &head[..12]);
                            format!("event {}", k)
                        }
                        Err((code, m)) => {
                            // a refused edit: one record, no event; the loop goes on
                            live.refused += 1;
                            let mut ctx = vec![("x", V::S(faced.0.to_string())), ("z", V::S(faced.1.to_string())),
                                               ("camera", V::S(cam_token(session.camera())))];
                            if let Some(v) = cell {
                                ctx.push(("cell", V::S((v as char).to_string())));
                            }
                            crate::refusallog::record(&crate::refusallog::Event { operation: "liveinput", surface, reason: code.to_string(), attribution: "input.edit", context: ctx });
                            println!("[liveinput] {} -> refused {}: {}", name, code, m);
                            format!("refused {}", code)
                        }
                    }
                }
                Action::Tile(class) => {
                    // LIVE-AUTHOR-0: the class's next palette colour, read from the session's own M, appended as an
                    // edit; nothing is shown until it is appended (commit-only)
                    let k = live.events;
                    let rgb = crate::liveauthor::next_colour(session.tile_rgb(class));
                    let (spec, head) = match session.push_edit_tile(class, rgb) {
                        Ok(ev) => (ev.param.clone(), ev.head.clone()),
                        Err(m) => return Err(refusal("render.scene", vec![("event", V::N(k))], format!("LIVEINPUT-SCENE: tile edit did not replay: {}", m))),
                    };
                    live.events += 1;
                    live.edits += 1;
                    let r = reference(session, None)?;
                    live.references += 1;
                    scene = r.0;
                    expected = r.1;
                    expected_bgr = r.2;
                    live.views.push(r.3);
                    live.pixels.push(r.4);
                    fresh = true;
                    println!("[liveinput] {} -> event {}: edit {} head {}", name, k, spec, &head[..12]);
                    format!("event {}", k)
                }
            };
            live.trace.push(Typed { key: vk, repeat, composition: c, outcome });
            if end {
                break;
            }
        }
        if end {
            live.ended = "escape";
            break;
        }
        if !open {
            live.ended = "closed";
            break;
        }
        lr.render(&scene);
        lr.blit();
        live.rendered += 1;
        if lr.composite() != &expected[..] || lr.bgr() != &expected_bgr[..] {
            return Err(refusal("render.loop", vec![("state", V::N(live.events)), ("composition", V::N(c + 1))],
                               format!("LIVEINPUT-BYTES: the loop's frame for state {} differs from its reference at composition {}", live.events, c + 1)));
        }
        live.byte_checks += 1;
        if s.present(lr.bgr()).is_none() {
            return Err(refusal("surface.present", vec![("state", V::N(live.events)), ("composition", V::N(c + 1))],
                               format!("LIVEINPUT-NO-PRESENT: SetDIBitsToDevice or the composition barrier failed at composition {}", c + 1)));
        }
        live.presented += 1;
        let due = if fresh {
            live.shown.push((live.events, hex(&sha256(lr.composite()))));
            fresh = false;
            held = 0;
            true
        } else {
            held += 1;
            held % RECHECK == 0
        };
        if due {
            s.flush();
            let screen = s.readback();
            let exact = matches!(&screen, Some(v) if v[..] == expected_bgr[..]);
            live.screen_readbacks += 1;
            crate::runledger::readback(!exact);
            if !exact {
                live.screen_differed += 1;
                // a differing screen: counted above, then one record (and its covering windows), never hidden
                let want = &expected_bgr;
                let mut ctx = vec![("state", V::N(live.events)), ("composition", V::N(c + 1))];
                let (reason, attribution, how) = match &screen {
                    Some(v) => {
                        let bytes = if v.len() == want.len() { v.iter().zip(want.iter()).filter(|(a, b)| a != b).count() } else { v.len().max(want.len()) };
                        ctx.push(("differing_bytes", V::N(bytes as u64)));
                        let b = diff_bbox(v, &|i| want[i]);
                        if let Some(b) = b {
                            ctx.push(("box", V::S(format!("{},{},{},{}", b[0], b[1], b[2], b[3]))));
                        }
                        let seen = b.map(|b| s.attribute(b)).unwrap_or_default();
                        ctx.extend(seen.context);
                        ("LIVEINPUT-SCREEN-DIFFERS", "present.readback", format!("{}; {}", describe(v, &|i| want[i]), seen.text))
                    }
                    None => ("LIVEINPUT-SCREEN-UNREADABLE", "surface.readback", "the screen could not be read back".to_string()),
                };
                crate::refusallog::record(&crate::refusallog::Event { operation: "liveinput", surface, reason: reason.to_string(), attribution, context: ctx });
                if last != Some(false) {
                    println!("[liveinput] state {}: SCREEN DIFFERS — {}", live.events, how);
                }
            } else if last != Some(true) {
                println!("[liveinput] state {}: the screen is the session's picture", live.events);
            }
            last = Some(exact);
        }
        c += 1;
    }
    live.compositions = c;
    live.renders = lr.renders();
    Ok(live)
}

pub fn summary(l: &Live, s: &LiveSession) -> Vec<String> {
    vec![
        format!("liveinput keys {} repeats {} unbound {} events {} moves {} blocked {} edits {} refused {} ended {}",
                l.keys, l.repeats, l.unbound, l.events, l.moves, l.blocked, l.edits, l.refused, l.ended),
        format!("liveinput compositions {} rendered {} presented {} byte_checks {} references {} screen_readbacks {} screen_differed {}",
                l.compositions, l.rendered, l.presented, l.byte_checks, l.references, l.screen_readbacks, l.screen_differed),
        format!("liveinput final camera {} content {} head {}", cam_token(s.camera()), s.content(), s.head()),
    ]
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

/// The mock run's output for the gate (never written by the host window): the base, the per-key trace, the event log
/// with each event's witness, content and head, the frame digest presented for every state, the counts and the final
/// state. It is the gate's scratch, not a record and not a saved session.
pub fn raw_json(l: &Live, s: &LiveSession, level: &str, tiles: &str) -> String {
    let trace: Vec<String> = l.trace.iter().map(|t| {
        format!("{{\"key\":{},\"vk\":{},\"repeat\":{},\"composition\":{},\"outcome\":{}}}", esc(&key_name(t.key)), t.key, t.repeat, t.composition, esc(&t.outcome))
    }).collect();
    let events: Vec<String> = s.log().iter().map(|e| {
        let (kind, pk) = if e.tag == b'M' { ("move", "command") } else { ("edit", "spec") };
        format!("{{\"kind\":\"{}\",\"{}\":{},\"camera\":{},\"witness\":{},\"content\":{},\"head\":{}}}",
                kind, pk, esc(&e.param), esc(&cam_token(e.camera)), esc(&e.witness), esc(&e.content), esc(&e.head))
    }).collect();
    let views: Vec<String> = l.views.iter().map(|v| esc(v)).collect();
    let pixels: Vec<String> = l.pixels.iter().map(|v| esc(v)).collect();
    let g = l.geometry;
    format!(
        "{{\"name\":\"verdandi-liveinput-selftest\",\"data\":{{\"base\":{{\"level\":{},\"tiles\":{},\"camera\":{},\"content\":{},\"genesis\":{}}},\"trace\":[{}],\"events\":[{}],\"views\":[{}],\"pixels\":[{}],\"counts\":{{\"keys\":{},\"repeats\":{},\"unbound\":{},\"events\":{},\"moves\":{},\"blocked\":{},\"edits\":{},\"refused\":{},\"references\":{},\"compositions\":{},\"frames_rendered\":{},\"frames_presented\":{},\"byte_checks\":{},\"screen_readbacks\":{},\"screen_differed\":{},\"loop_renders\":{}}},\"geometry\":{{\"client\":[{},{}],\"origin\":[{},{}],\"screen_logical\":[{},{}],\"screen_physical\":[{},{}]}},\"call\":\"setdibitstodevice\",\"render_entry\":\"LoopRenderer\",\"every\":{},\"recheck\":{},\"ended\":{},\"final\":{{\"camera\":{},\"W\":{},\"M\":{},\"content\":{},\"head\":{}}}}}}}",
        esc(level), esc(tiles), esc(&cam_token(s.cam0())), esc(s.base_content()), esc(s.genesis()),
        trace.join(","), events.join(","), views.join(","), pixels.join(","),
        l.keys, l.repeats, l.unbound, l.events, l.moves, l.blocked, l.edits, l.refused, l.references, l.compositions, l.rendered,
        l.presented, l.byte_checks, l.screen_readbacks, l.screen_differed, l.renders,
        g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], MOCK_EVERY, RECHECK, esc(l.ended),
        esc(&cam_token(s.camera())), esc(&s.w_hex()), esc(&s.m_hex()), esc(s.content()), esc(s.head()))
}

/// LIVE-AUTHOR-0: the live editor's gate output — the per-key trace, each state's frame witness and pixels, and the
/// counts. The events themselves are the saved session's; this is the gate's scratch, not a record.
pub fn raw_json_counts(l: &Live, level: &str, tiles: &str) -> String {
    let trace: Vec<String> = l.trace.iter().map(|t| {
        format!("{{\"key\":{},\"vk\":{},\"repeat\":{},\"composition\":{},\"outcome\":{}}}", esc(&key_name(t.key)), t.key, t.repeat, t.composition, esc(&t.outcome))
    }).collect();
    let views: Vec<String> = l.views.iter().map(|v| esc(v)).collect();
    let pixels: Vec<String> = l.pixels.iter().map(|v| esc(v)).collect();
    let shown: Vec<String> = l.shown.iter().map(|(k, v)| format!("[{},{}]", k, esc(v))).collect();
    format!("{{\"name\":\"verdandi-live-selftest\",\"data\":{{\"level\":{},\"tiles\":{},\"trace\":[{}],\"views\":[{}],\"pixels\":[{}],\"shown\":[{}],\"counts\":{{\"keys\":{},\"repeats\":{},\"unbound\":{},\"events\":{},\"moves\":{},\"edits\":{},\"refused\":{},\"compositions\":{},\"frames_rendered\":{},\"frames_presented\":{},\"byte_checks\":{},\"screen_readbacks\":{},\"screen_differed\":{}}},\"ended\":{}}}}}",
            esc(level), esc(tiles), trace.join(","), views.join(","), pixels.join(","), shown.join(","), l.keys, l.repeats, l.unbound, l.events, l.moves, l.edits, l.refused,
            l.compositions, l.rendered, l.presented, l.byte_checks, l.screen_readbacks, l.screen_differed, esc(l.ended))
}
