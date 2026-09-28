// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/liveloop.rs — LIVE-LOOP-0: the first loop that renders every composition, live, from the current state.
//
// `show` presents frames rendered before its window opens. This loop renders each composition from the current step
// of a sealed session, through the adopted `present::LoopRenderer`, and presents it with SetDIBitsToDevice — the call
// PRESENT-EXACT-0 adopted — through the same exact surface the court witnessed. The state is the sealed session's,
// stepped at a fixed dwell (DWELL compositions per step, as show-playback), and the last step is held for HOLD
// compositions before the run ends by itself. Nothing is pre-rendered for presentation.
//
//   Witnesses first, outside the loop: the geometry is the certified frame 1:1 at (0,0); every step's fresh reference
//   composite reproduces its sealed witness, and those verified bytes are the expected bytes of that step.
//   Every composition: the window's events (Esc or close only), render the current step through the LoopRenderer,
//   compare its composite and blit bytes with the step's expected bytes (a difference refuses: the renderer drifted),
//   present, and — on the first composition of every step and every RECHECK-th composition of the hold — read the
//   composed screen back and compare it with the expected blit. A differing screen is counted and logged, never
//   hidden, and the loop goes on (as show does); it is not a refusal.
//
// No authoring input, no camera control, no clock, no flip model, no workers: the first court is the loop itself.
// The loop reads the sealed session's steps and writes nothing canonical; its caller hashes the session file before
// and after. Its refusals are data (logged where they are emitted); each differing screen readback is one record in
// the refusal log; every run is one line in the run ledger.

use crate::latency1r::FrameInput;
use crate::mantle::{frame_digest, H, W};
use crate::present::{arm_composite, to_blit, Arm, LoopRenderer};
use crate::presentexact::{describe, diff_bbox, ExactSurface};
use crate::refusallog::V;

pub const DWELL: u64 = 24;
pub const HOLD: u64 = 150;
pub const RECHECK: u64 = 75;
pub const CALL: usize = 1; // SetDIBitsToDevice, the adopted call

/// A LIVE-LOOP-0 refusal as data: where on the path it came from, a few facts, and its console message.
pub struct Refusal {
    pub attribution: &'static str,
    pub context: Vec<(&'static str, V)>,
    pub message: String,
}

impl Refusal {
    pub fn into_event(self, surface: &'static str) -> (crate::refusallog::Event, String) {
        let reason = crate::refusallog::code_of(&self.message);
        (crate::refusallog::Event { operation: "liveloop", surface, reason, attribution: self.attribution, context: self.context },
         self.message)
    }
}

fn refusal(attribution: &'static str, context: Vec<(&'static str, V)>, message: String) -> Refusal {
    Refusal { attribution, context, message }
}

/// What one run did: counts only (LIVE-LOOP-0 makes no timing claim).
pub struct Live {
    pub steps: u64,
    pub compositions: u64,
    pub rendered: u64,
    pub presented: u64,
    pub byte_checks: u64,
    pub screen_readbacks: u64,
    pub screen_differed: u64,
    pub geometry: [i32; 8],
    pub renders: u64,
}

/// Whether composition `c` reads the screen back: the first composition of every step, and every RECHECK-th
/// composition of the hold.
pub fn reads_back(c: u64, steps: u64) -> bool {
    let walk = steps * DWELL;
    if c < walk { c % DWELL == 0 } else { (c - walk + 1) % RECHECK == 0 }
}

/// The run: witnesses first, then steps x DWELL + HOLD compositions, each rendered live and presented.
pub fn run<S: ExactSurface>(s: &mut S, inputs: &[FrameInput], surface: &'static str) -> Result<Live, Refusal> {
    if inputs.is_empty() {
        return Err(refusal("court.input", vec![("steps", V::N(0))], "LIVELOOP-EMPTY: the sealed session has no steps".to_string()));
    }
    let _ = s.pump();
    let g = s.geometry();
    if g != [W as i32, H as i32, 0, 0, W as i32, H as i32, W as i32, H as i32] {
        return Err(refusal("window.geometry", vec![("geometry", V::S(format!("{:?}", g)))],
                           format!("LIVELOOP-GEOMETRY: client {}x{} at ({},{}), screen logical {}x{} physical {}x{}; the target is {}x{} at (0,0) on a {}x{} screen",
                                   g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], W, H, W, H)));
    }
    // witnesses first, outside the loop: each step's reference reproduces its sealed witness; its bytes are expected
    let mut expected: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    let mut expected_bgr: Vec<Vec<u8>> = Vec::with_capacity(inputs.len());
    for (i, f) in inputs.iter().enumerate() {
        let (fr, comp) = arm_composite(&f.scene, Arm::Production);
        if frame_digest(&fr) != f.witness {
            return Err(refusal("render.witness", vec![("step", V::N(i as u64 + 1))],
                               format!("LIVELOOP-WITNESS: step {} does not reproduce its sealed witness", i + 1)));
        }
        expected_bgr.push(to_blit(&comp));
        expected.push(comp);
    }
    s.set_call(CALL);
    let steps = inputs.len() as u64;
    let total = steps * DWELL + HOLD;
    let mut lr = LoopRenderer::new();
    let mut live = Live { steps, compositions: 0, rendered: 0, presented: 0, byte_checks: 0, screen_readbacks: 0,
                          screen_differed: 0, geometry: g, renders: 0 };
    let mut last: Option<bool> = None;
    for c in 0..total {
        if !s.pump() {
            return Err(refusal("window.close", vec![("composition", V::N(c + 1)), ("of", V::N(total))],
                               format!("LIVELOOP-CLOSED: the window closed at composition {} of {}, before the walk finished; no record",
                                       c + 1, total)));
        }
        let k = ((c / DWELL) as usize).min(inputs.len() - 1);
        lr.render(&inputs[k].scene);
        lr.blit();
        live.rendered += 1;
        if lr.composite() != &expected[k][..] || lr.bgr() != &expected_bgr[k][..] {
            return Err(refusal("render.loop", vec![("step", V::N(k as u64 + 1)), ("composition", V::N(c + 1))],
                               format!("LIVELOOP-BYTES: the loop's frame for step {} differs from its verified bytes at composition {}",
                                       k + 1, c + 1)));
        }
        live.byte_checks += 1;
        if s.present(lr.bgr()).is_none() {
            return Err(refusal("surface.present", vec![("step", V::N(k as u64 + 1)), ("composition", V::N(c + 1))],
                               format!("LIVELOOP-NO-PRESENT: SetDIBitsToDevice or the composition barrier failed at composition {}", c + 1)));
        }
        live.presented += 1;
        if reads_back(c, steps) {
            s.flush();
            let screen = s.readback();
            let exact = matches!(&screen, Some(v) if v[..] == expected_bgr[k][..]);
            live.screen_readbacks += 1;
            crate::runledger::readback(!exact);
            if !exact {
                live.screen_differed += 1;
                // a differing screen: counted above, then one record (and its covering windows), never hidden
                let want = &expected_bgr[k];
                let mut ctx = vec![("step", V::N(k as u64 + 1)), ("of", V::N(steps)), ("composition", V::N(c + 1))];
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
                        ("LIVELOOP-SCREEN-DIFFERS", "present.readback", format!("{}; {}", describe(v, &|i| want[i]), seen.text))
                    }
                    None => ("LIVELOOP-SCREEN-UNREADABLE", "surface.readback", "the screen could not be read back".to_string()),
                };
                crate::refusallog::record(&crate::refusallog::Event { operation: "liveloop", surface, reason: reason.to_string(), attribution, context: ctx });
                if last != Some(false) {
                    println!("[liveloop] step {}/{}: SCREEN DIFFERS — {}", k + 1, steps, how);
                }
            } else if last != Some(true) {
                println!("[liveloop] step {}/{}: the screen is the certified picture", k + 1, steps);
            }
            last = Some(exact);
        }
    }
    live.compositions = total;
    live.renders = lr.renders();
    Ok(live)
}

pub fn summary(l: &Live) -> Vec<String> {
    vec![format!("liveloop steps {} dwell {} hold {} compositions {} rendered {} presented {} byte_checks {} screen_readbacks {} screen_differed {}",
                 l.steps, DWELL, HOLD, l.compositions, l.rendered, l.presented, l.byte_checks, l.screen_readbacks, l.screen_differed)]
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

/// The raw record the sealer checks: counts, the geometry, the fixed call and entry, and the session file's hash
/// before and after the run. No timing.
pub fn raw_record(host: &str, surface: &str, l: &Live, session: &str, before: &str, after: &str, unix_seconds: u64) -> String {
    let g = l.geometry;
    let data = format!(
        "{{\"steps\":{},\"dwell\":{},\"hold\":{},\"recheck\":{},\"compositions\":{},\"frames_rendered\":{},\"frames_presented\":{},\"byte_checks\":{},\"screen_readbacks\":{},\"screen_differed\":{},\"geometry\":{{\"client\":[{},{}],\"origin\":[{},{}],\"screen_logical\":[{},{}],\"screen_physical\":[{},{}],\"source\":[{},{}]}},\"call\":\"setdibitstodevice\",\"render_entry\":\"LoopRenderer\",\"loop_renders\":{},\"session\":{{\"path\":{},\"sha256_before\":{},\"sha256_after\":{}}}}}",
        l.steps, DWELL, HOLD, RECHECK, l.compositions, l.rendered, l.presented, l.byte_checks, l.screen_readbacks, l.screen_differed,
        g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], W, H, l.renders, esc(session), esc(before), esc(after));
    let prov = format!("{{\"tool\":\"shell/liveloop.rs over the {} surface\",\"host\":{},\"preregistered\":{{\"rung\":\"LIVE-LOOP-0\"}},\"unix_seconds\":{}}}",
                       surface, esc(host), unix_seconds);
    format!("{{\"name\":\"verdandi-liveloop\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"the live loop's counts; no timing\"}}",
            prov, esc(&format!("the sealed session walked live on host {}: every composition rendered through the LoopRenderer and presented by SetDIBitsToDevice", host)),
            esc(host), data)
}
