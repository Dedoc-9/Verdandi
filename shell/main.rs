// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/main.rs — the shell's command line.
//
//     rustc -O shell/main.rs -o build/shell                          # the headless law (what the gate builds)
//     rustc -O --cfg shell_window shell/main.rs -o build/shell       # + the window, ON WINDOWS (the host build)
//     shell witness --level L --tiles T --camera x,z,F        # headless: the composite sha and the blit witness
//     shell selfcheck --level L --tiles T --camera x,z,F      # headless: `blit_roundtrip OK|BROKEN`
//     shell run --level L --tiles T --camera x,z,F [--measure N --host NAME]   # a window (window build only)
//
// The window, the blit and the DWM composition clock live in shell/win32.rs, compiled ONLY when BOTH
// target_os = "windows" AND the `--cfg shell_window` flag are set. The gate never passes that flag, so
// win32.rs is out of every gate build on every host, and `shell witness`/`shell selfcheck` — the blit-hash
// law — are what the gate exercises, host-independently. Without the window, `run` refuses `SHELL-NO-WINDOW`
// rather than pretending to present. The owner adds `--cfg shell_window` to build the real window on the host.

#![allow(unexpected_cfgs)]

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;
#[allow(dead_code)]
#[path = "../kernel/hud.rs"]
mod hud;
#[allow(dead_code)]
#[path = "../kernel/fast.rs"]
mod fast;
#[allow(dead_code)]
#[path = "present.rs"]
mod present;
#[allow(dead_code)]
#[path = "playback.rs"]
mod playback;
#[allow(dead_code)]
#[path = "latency1r.rs"]
mod latency1r;
#[allow(dead_code)]
#[path = "framesplit.rs"]
mod framesplit;
#[allow(dead_code)]
#[path = "presentscale.rs"]
mod presentscale;
#[allow(dead_code)]
#[path = "presentstretch.rs"]
mod presentstretch;
#[allow(dead_code)]
#[path = "allocreuse.rs"]
mod allocreuse;
#[allow(dead_code)]
#[path = "allocreuse1.rs"]
mod allocreuse1;
#[allow(dead_code)]
#[path = "presentexact.rs"]
mod presentexact;

#[path = "refusallog.rs"]
mod refusallog;

#[path = "runledger.rs"]
mod runledger;

#[path = "liveloop.rs"]
mod liveloop;

#[path = "liveinput.rs"]
mod liveinput;

#[path = "livesession.rs"]
mod livesession;

#[path = "liveauthor.rs"]
mod liveauthor;

#[path = "holdwalk.rs"]
mod holdwalk;

// SIM-TICK-0: the bearing kernels (reached only through heading.rs), the tick rules, the frame at a heading, the tick run
#[allow(dead_code)]
#[path = "../kernel/vocab.rs"]
mod vocab;
#[allow(dead_code)]
#[path = "../kernel/bearing.rs"]
mod bearing;
#[allow(dead_code)]
#[path = "../kernel/bearingfast.rs"]
mod bearingfast;

#[path = "simtick.rs"]
mod simtick;

#[path = "heading.rs"]
mod heading;

#[path = "tickrun.rs"]
mod tickrun;
// MOUSE-LOOK-0: the tick source of the live loop — the ticker, the off-loop sample, the mock's mouse, focus and clock
#[path = "mouselook.rs"]
mod mouselook;
#[path = "admit.rs"]
mod admit;
// DESIGN-EVENT-0: a design admitted as one batch, its dry run and its binding
#[path = "designevent.rs"]
mod designevent;
// DESIGN-IR/DIFF-0: a design compiled to its change set, against a saved session; it admits nothing
#[path = "designcompile.rs"]
mod designcompile;
// READER-COURT-0: the saved form's one reader, shared by path with the workshop, and its court command
#[path = "../kernel/savedform.rs"]
mod savedform;
#[path = "readercourt.rs"]
mod readercourt;

#[cfg(all(target_os = "windows", shell_window))]
#[path = "win32.rs"]
mod win32;

use std::env;
use std::fs;
use std::process::exit;

use formats::{parse_camera, Camera};
use mantle::Refusal;
use present::{blit_witness, blit_roundtrip_ok, compose_frame, to_blit, Composed};

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("SHELL-{}: {}", code, detail);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path, e)))
}

#[allow(dead_code)]
struct Args {
    level: String,
    tiles: String,
    camera: Camera,
    measure: usize,
    host: String,
}

fn parse(args: &[String]) -> Args {
    let (mut level, mut tiles, mut camera) = (None, None, None);
    let mut measure = 0usize;
    let mut host = String::from("unnamed");
    let mut i = 0;
    while i < args.len() {
        let val = |i: usize| args.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", args[i])));
        match args[i].as_str() {
            "--level" => level = Some(val(i)),
            "--tiles" => tiles = Some(val(i)),
            "--camera" => camera = Some(val(i)),
            "--measure" => measure = val(i).parse().unwrap_or_else(|_| refuse("USAGE", "--measure needs a count")),
            "--host" => host = val(i),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    let (level, tiles, camera) = match (level, tiles, camera) {
        (Some(a), Some(b), Some(c)) => (a, b, c),
        _ => refuse("USAGE", "needs --level --tiles --camera"),
    };
    let cam = parse_camera(&camera).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    Args { level, tiles, camera: cam, measure, host }
}

fn composed(a: &Args) -> Composed {
    compose_frame(&read(&a.level), &read(&a.tiles), a.camera).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        refuse("USAGE", "shell witness ... | shell selfcheck ... | shell run ...");
    }
    match args[1].as_str() {
        "witness" => {
            let a = parse(&args[2..]);
            let c = composed(&a);
            let blit = to_blit(&c.composite);
            println!("frame {}", c.frame_digest);
            println!("pixels {}", c.pixels);
            println!("composite {}", c.composite_sha);
            println!("blit {}", blit_witness(&blit));
        }
        "selfcheck" => {
            let a = parse(&args[2..]);
            let c = composed(&a);
            println!("blit_roundtrip {}", if blit_roundtrip_ok(&c.composite) { "OK" } else { "BROKEN" });
        }
        "run" => {
            let a = parse(&args[2..]);
            let c = composed(&a);
            #[cfg(all(target_os = "windows", shell_window))]
            {
                win32::run(c, a.measure, &a.host, a.camera);
            }
            #[cfg(not(all(target_os = "windows", shell_window)))]
            {
                let _ = c;
                refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to present and measure");
            }
        }
        "playback" | "checkpoint" | "resume" | "playback-window" => {
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            match args[1].as_str() {
                "playback" => {
                    let batch = opt("--batch").and_then(|v| v.parse().ok()).unwrap_or(usize::MAX);
                    playback::playback(&session, &root, batch);
                }
                "checkpoint" => {
                    let at = opt("--at").and_then(|v| v.parse().ok()).unwrap_or_else(|| refuse("USAGE", "checkpoint needs --at"));
                    let out = opt("--out").unwrap_or_else(|| refuse("USAGE", "checkpoint needs --out"));
                    playback::checkpoint(&session, &root, at, &out);
                }
                "resume" => {
                    let ck = opt("--checkpoint").unwrap_or_else(|| refuse("USAGE", "resume needs --checkpoint"));
                    playback::resume(&session, &root, &ck);
                }
                _ => {
                    // playback-window (SHELL-PLAYBACK-b): play the sealed session IN the host window; with
                    // --measure N it is LATENCY-0's instrument (window build only)
                    #[cfg(all(target_os = "windows", shell_window))]
                    {
                        let measure = opt("--measure").and_then(|v| v.parse().ok()).unwrap_or(0usize);
                        let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                        let frames = playback::frames(&session, &root);
                        win32::playback_window(frames, measure, &host);
                    }
                    #[cfg(not(all(target_os = "windows", shell_window)))]
                    {
                        let _ = (&session, &root);
                        refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to play a sealed session in the window");
                    }
                }
            }
        }
        "latency1r-selftest" | "latency1r-window" => {
            // LATENCY-1R (render-start -> composited, production vs single-thread reference): ONE court, driven
            // headless through a deterministic mock surface (`latency1r-selftest`, what the gate runs) or through the
            // host window (`latency1r-window`, window build only). LATENCY-0's `playback-window` path is untouched.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let per_cell = opt("--per-cell").and_then(|v| v.parse().ok()).unwrap_or(200usize);
            let out = opt("--out");
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            if args[1] == "latency1r-selftest" {
                // plants: `--plant witness` tampers the first sealed witness (must refuse before any clock);
                // `--plant close` closes the mock window mid-court (must refuse with no record)
                let plant = opt("--plant").unwrap_or_default();
                if plant == "witness" {
                    if let Some(f) = inputs.first_mut() {
                        let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                        f.witness = format!("{}{}", flipped, &f.witness[1..]);
                    }
                }
                let close_after = if plant == "close" { Some(3) } else { None };
                let mut surf = latency1r::MockSurface::new(13_333, 1, close_after);
                match latency1r::court(&mut surf, &inputs, per_cell) {
                    Ok(c) => {
                        for ln in latency1r::summary(&c) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, latency1r::raw_record("gate-mock", "mock", &c, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("latency1r court OK");
                    }
                    Err(m) => refuse("LATENCY1R", &m),
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                    win32::latency1r_window(inputs, per_cell, &host, out);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&inputs, per_cell, &out);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the LATENCY-1R court in the window");
                }
            }
        }
        "framesplit-selftest" | "framesplit-window" => {
            // FRAME-SPLIT-0 (where render-start -> frame-ready goes): ONE court, driven headless through the mock
            // surface (`framesplit-selftest`, what the gate runs) or through the host window (`framesplit-window`).
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let per_cell = opt("--per-cell").and_then(|v| v.parse().ok()).unwrap_or(300usize);
            let out = opt("--out");
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            if args[1] == "framesplit-selftest" {
                // plants: `--plant witness` tampers the first sealed witness; `--plant close` closes the mock window
                let plant = opt("--plant").unwrap_or_default();
                if plant == "witness" {
                    if let Some(f) = inputs.first_mut() {
                        let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                        f.witness = format!("{}{}", flipped, &f.witness[1..]);
                    }
                }
                let close_after = if plant == "close" { Some(5) } else { None };
                let mut surf = latency1r::MockSurface::new(13_333, 1, close_after);
                match framesplit::court(&mut surf, &inputs, per_cell) {
                    Ok(sp) => {
                        for ln in framesplit::summary(&sp) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, framesplit::raw_record("gate-mock", "mock", &sp, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("framesplit court OK");
                    }
                    Err(m) => refuse("FRAMESPLIT", &m),
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                    win32::framesplit_window(inputs, per_cell, &host, out);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&inputs, per_cell, &out);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the FRAME-SPLIT-0 court in the window");
                }
            }
        }
        "presentscale-selftest" | "presentscale-window" => {
            // PRESENT-SCALE-0 (the blit at a half-size vs a full-size client area): ONE court, driven headless through
            // the mock surface (`presentscale-selftest`, what the gate runs) or the host window (`presentscale-window`).
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let per_cell = opt("--per-cell").and_then(|v| v.parse().ok()).unwrap_or(300usize);
            let out = opt("--out");
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            if args[1] == "presentscale-selftest" {
                // plants: `--plant witness` tampers the first sealed witness; `--plant geometry` makes the mock window
                // manager refuse the full client size; `--plant close` closes the mock window mid-court
                let plant = opt("--plant").unwrap_or_default();
                if plant == "witness" {
                    if let Some(f) = inputs.first_mut() {
                        let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                        f.witness = format!("{}{}", flipped, &f.witness[1..]);
                    }
                }
                let close_after = if plant == "close" { Some(5) } else { None };
                let mut surf = presentscale::MockGeom { inner: latency1r::MockSurface::new(13_333, 1, close_after), clamp: plant == "geometry" };
                match presentscale::court(&mut surf, &inputs, per_cell) {
                    Ok(sc) => {
                        for ln in presentscale::summary(&sc) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, presentscale::raw_record("gate-mock", "mock", &sc, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("presentscale court OK");
                    }
                    Err(m) => refuse("PRESENTSCALE", &m),
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                    win32::presentscale_window(inputs, per_cell, &host, out);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&inputs, per_cell, &out);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the PRESENT-SCALE-0 court in the window");
                }
            }
        }
        "presentstretch-selftest" | "presentstretch-window" | "allocreuse-selftest" | "allocreuse-window" => {
            // PRESENT-STRETCH-0 (the half-size blit under three stretch modes) and ALLOC-REUSE-0 (fresh vs reused
            // buffers): each ONE court, driven headless through the mock surface (`-selftest`, what the gate runs) or
            // the host window (`-window`, window build only).
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let per_cell = opt("--per-cell").and_then(|v| v.parse().ok()).unwrap_or(300usize);
            let out = opt("--out");
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            let plant = opt("--plant").unwrap_or_default();
            if plant == "witness" {
                if let Some(f) = inputs.first_mut() {
                    let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                    f.witness = format!("{}{}", flipped, &f.witness[1..]);
                }
            }
            let close_after = if plant == "close" { Some(5) } else { None };
            match args[1].as_str() {
                "presentstretch-selftest" => {
                    // plants: witness, close, and `--plant mode` (the device context ignores the requested mode)
                    let mut surf = presentstretch::MockStretch { inner: latency1r::MockSurface::new(13_333, 1, close_after), refuse_mode: plant == "mode" };
                    match presentstretch::court(&mut surf, &inputs, per_cell) {
                        Ok(st) => {
                            for ln in presentstretch::summary(&st) {
                                println!("{}", ln);
                            }
                            if let Some(o) = out {
                                fs::write(&o, presentstretch::raw_record("gate-mock", "mock", &st, 0))
                                    .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                            }
                            println!("presentstretch court OK");
                        }
                        Err(m) => refuse("PRESENTSTRETCH", &m),
                    }
                }
                "allocreuse-selftest" => {
                    let mut surf = latency1r::MockSurface::new(13_333, 1, close_after);
                    match allocreuse::court(&mut surf, &inputs, per_cell) {
                        Ok(al) => {
                            for ln in allocreuse::summary(&al) {
                                println!("{}", ln);
                            }
                            if let Some(o) = out {
                                fs::write(&o, allocreuse::raw_record("gate-mock", "mock", &al, 0))
                                    .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                            }
                            println!("allocreuse court OK");
                        }
                        Err(m) => refuse("ALLOCREUSE", &m),
                    }
                }
                _ => {
                    #[cfg(all(target_os = "windows", shell_window))]
                    {
                        let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                        if args[1] == "presentstretch-window" {
                            win32::presentstretch_window(inputs, per_cell, &host, out);
                        } else {
                            win32::allocreuse_window(inputs, per_cell, &host, out);
                        }
                    }
                    #[cfg(not(all(target_os = "windows", shell_window)))]
                    {
                        let _ = (&inputs, per_cell, &out);
                        refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run this court in the window");
                    }
                }
            }
        }
        "loop-equiv" => {
            // ALLOC-REUSE-1's correctness court (headless, no clock): one persistent-buffer loop renderer, poisoned
            // first, renders every case in three orders; every render must equal the fresh path byte for byte, the
            // corpus's goldens must reproduce, and no buffer may be replaced. Cases: a tab-separated file of
            // `label level tiles camera golden_frame golden_pixels` (a golden of `-` is none), plus a sealed session.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let mut cases: Vec<allocreuse1::EquivCase> = Vec::new();
            if let Some(path) = opt("--cases") {
                let text = String::from_utf8(read(&path)).unwrap_or_else(|_| refuse("USAGE", "the cases file is not UTF-8"));
                for ln in text.lines().filter(|l| !l.trim().is_empty()) {
                    let f: Vec<&str> = ln.split('\t').collect();
                    if f.len() != 6 {
                        refuse("USAGE", &format!("a case line needs 6 tab-separated fields: {}", ln));
                    }
                    let cam = parse_camera(f[3]).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
                    let scene = present::scene_of(&read(f[1]), &read(f[2]), cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m));
                    let g = |x: &str| if x == "-" { None } else { Some(x.to_string()) };
                    cases.push(allocreuse1::EquivCase { label: f[0].to_string(), scene, golden_frame: g(f[4]), golden_pixels: g(f[5]) });
                }
            }
            if let Some(session) = opt("--session") {
                let root = opt("--root").unwrap_or_default();
                for (i, (lv, tl, cam, w)) in playback::frame_inputs(&session, &root).into_iter().enumerate() {
                    let scene = present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m));
                    cases.push(allocreuse1::EquivCase { label: format!("session:{}", i), scene, golden_frame: Some(w), golden_pixels: None });
                }
            }
            let plant = opt("--plant").unwrap_or_default();
            match allocreuse1::loop_equiv(&cases, &plant) {
                Ok(r) => {
                    for ln in &r.lines {
                        println!("{}", ln);
                    }
                    println!("loop-equiv OK cases {} goldens {} orders 3 renders {} buffers persistent", r.cases, r.goldens, r.renders);
                }
                Err(m) => refuse("LOOP", &m),
            }
        }
        "allocreuse1-selftest" | "allocreuse1-window" => {
            // ALLOC-REUSE-1's performance court: the fresh reference and the persistent-buffer render-loop entry,
            // driven headless through the mock surface (`-selftest`, what the gate runs) or the host window
            // (`-window`, window build only). Plants (selftest): witness, close, persist.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let per_cell = opt("--per-cell").and_then(|v| v.parse().ok()).unwrap_or(allocreuse1::DEFAULT_PER_CELL);
            let out = opt("--out");
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            let plant = opt("--plant").unwrap_or_default();
            if plant == "witness" {
                if let Some(f) = inputs.first_mut() {
                    let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                    f.witness = format!("{}{}", flipped, &f.witness[1..]);
                }
            }
            let close_after = if plant == "close" { Some(5) } else { None };
            if args[1] == "allocreuse1-selftest" {
                let mut surf = latency1r::MockSurface::new(13_333, 1, close_after);
                match allocreuse1::court(&mut surf, &inputs, per_cell, plant == "persist") {
                    Ok(ad) => {
                        for ln in allocreuse1::summary(&ad) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, allocreuse1::raw_record("gate-mock", "mock", &ad, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("allocreuse1 court OK");
                    }
                    Err(m) => refuse("ALLOCREUSE1", &m),
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                    win32::allocreuse1_window(inputs, per_cell, &host, out);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&inputs, per_cell, &out);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the ALLOC-REUSE-1 court in the window");
                }
            }
        }
        "show" => {
            // PRESENT-EXACT-0 LOCK: the certified frame 1:1 in the borderless window, SetDIBitsToDevice, the composed
            // screen read back (window build only). Exit 0 if every readback was exact, 3 if any differed.
            let a = parse(&args[2..]);
            let c = composed(&a);
            #[cfg(all(target_os = "windows", shell_window))]
            {
                win32::show(vec![c], "SHOW");
            }
            #[cfg(not(all(target_os = "windows", shell_window)))]
            {
                let _ = c;
                refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to show the certified picture");
            }
        }
        "show-playback" => {
            // PRESENT-EXACT-0 LOCK: a sealed session's frames, each certified and shown 1:1 as above
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let frames = playback::frames(&session, &root);
            #[cfg(all(target_os = "windows", shell_window))]
            {
                win32::show(frames, "SHOW-PLAYBACK");
            }
            #[cfg(not(all(target_os = "windows", shell_window)))]
            {
                let _ = frames;
                refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to show the sealed session");
            }
        }
        "presentexact-probe" => {
            // A diagnostic for PRESENT-EXACT-0's readback (window build only): no clock, no court, no record.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let out = opt("--out");
            let inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            #[cfg(all(target_os = "windows", shell_window))]
            {
                win32::presentexact_probe(inputs, out);
            }
            #[cfg(not(all(target_os = "windows", shell_window)))]
            {
                let _ = (&inputs, &out);
                refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the probe");
            }
        }
        "presentexact-selftest" | "presentexact-window" => {
            // PRESENT-EXACT-0: the certified composite presented 1:1 by StretchDIBits and by SetDIBitsToDevice, the
            // composed screen read back before and after the court; headless through the mock (`-selftest`, what the
            // gate runs) or in the borderless host window (`-window`, window build only). Plants (selftest): witness,
            // close, geometry, readback, noop.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let per_cell = opt("--per-cell").and_then(|v| v.parse().ok()).unwrap_or(presentexact::DEFAULT_PER_CELL);
            let out = opt("--out");
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            let plant = opt("--plant").unwrap_or_default();
            if plant == "witness" {
                if let Some(f) = inputs.first_mut() {
                    let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                    f.witness = format!("{}{}", flipped, &f.witness[1..]);
                }
            }
            let close_after = if plant == "close" { Some(12) } else { None };
            if args[1] == "presentexact-selftest" {
                let mut surf = presentexact::MockExact::new(latency1r::MockSurface::new(13_333, 1, close_after), &plant);
                runledger::begin("presentexact.court", "mock"); // RUN-LEDGER-0: the court run begins
                match presentexact::court(&mut surf, &inputs, per_cell) {
                    Ok(ex) => {
                        runledger::end(0);
                        for ln in presentexact::summary(&ex) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, presentexact::raw_record("gate-mock", "mock", &ex, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("presentexact court OK");
                    }
                    Err(r) => {
                        // REFUSAL-LOG-0: the court's refusal is logged where it is emitted, then printed as before
                        let (ev, m) = r.into_event("mock");
                        refusallog::refuse(&ev, &format!("SHELL-PRESENTEXACT: {}", m));
                        runledger::end(2);
                        exit(2)
                    }
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                    win32::presentexact_window(inputs, per_cell, &host, out);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&inputs, per_cell, &out);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the PRESENT-EXACT-0 court in the window");
                }
            }
        }
        "liveloop-selftest" | "liveloop-window" => {
            // LIVE-LOOP-0: the sealed session walked live — every composition rendered through the LoopRenderer from
            // the current step and presented by SetDIBitsToDevice; headless through the mock (`-selftest`, what the
            // gate runs) or in the borderless host window (`-window`, window build only). Plants (selftest): witness,
            // close, geometry, noop. `--per-cell` is accepted and ignored (the host flow passes it to every court).
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let root = opt("--root").unwrap_or_default();
            let out = opt("--out");
            let before = mantle::hex(&mantle::sha256(&read(&session)));
            let mut inputs: Vec<latency1r::FrameInput> = playback::frame_inputs(&session, &root)
                .into_iter()
                .map(|(lv, tl, cam, w)| latency1r::FrameInput {
                    scene: present::scene_of(&lv, &tl, cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m)),
                    witness: w,
                })
                .collect();
            let plant = opt("--plant").unwrap_or_default();
            if plant == "witness" {
                if let Some(f) = inputs.first_mut() {
                    let flipped = if f.witness.starts_with('0') { "1" } else { "0" };
                    f.witness = format!("{}{}", flipped, &f.witness[1..]);
                }
            }
            let close_after = if plant == "close" { Some(60) } else { None };
            if args[1] == "liveloop-selftest" {
                let mut surf = presentexact::MockExact::new(latency1r::MockSurface::new(13_333, 1, close_after), &plant);
                runledger::begin("liveloop", "mock"); // RUN-LEDGER-0: the live-loop run begins
                match liveloop::run(&mut surf, &inputs, "mock") {
                    Ok(live) => {
                        runledger::end(0);
                        let after = mantle::hex(&mantle::sha256(&read(&session)));
                        for ln in liveloop::summary(&live) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, liveloop::raw_record("gate-mock", "mock", &live, &session, &before, &after, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("liveloop court OK");
                    }
                    Err(r) => {
                        // REFUSAL-LOG-0: the loop's refusal is logged where it is emitted, then printed
                        let (ev, m) = r.into_event("mock");
                        refusallog::refuse(&ev, &format!("SHELL-LIVELOOP: {}", m));
                        runledger::end(2);
                        exit(2)
                    }
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let host = opt("--host").unwrap_or_else(|| "unnamed".to_string());
                    win32::liveloop_window(inputs, &host, out, &session, &before);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&inputs, &out, &before);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run LIVE-LOOP-0 in the window");
                }
            }
        }
        "liveinput-selftest" | "liveinput-window" => {
            // LIVE-INPUT-0: key presses become typed events in an in-memory session-walk whose replay the loop renders
            // live — through the mock with a key script (`-selftest`, what the gate runs) or in the borderless host
            // window with the keyboard (`-window`, window build only). The base defaults to the frozen witness level and
            // identity tiles at 28,28,N. Nothing is saved: the session lives in memory. Plants (selftest): geometry, noop.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let level = opt("--level").unwrap_or_else(|| "oracle/levels/witness.lvl".to_string());
            let tiles = opt("--tiles").unwrap_or_else(|| "oracle/tiles/identity.tiles".to_string());
            let cam0 = parse_camera(&opt("--camera").unwrap_or_else(|| "28,28,N".to_string())).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
            let mut session = playback::LiveSession::new(read(&level), read(&tiles), cam0).unwrap_or_else(|m| refuse("INVALID-SESSION", &m));
            if args[1] == "liveinput-selftest" {
                let script = liveinput::parse_script(&opt("--keys").unwrap_or_default()).unwrap_or_else(|m| refuse("USAGE", &m));
                let plant = opt("--plant").unwrap_or_default();
                let out = opt("--out");
                let mock = presentexact::MockExact::new(latency1r::MockSurface::new(13_333, 1, None), &plant);
                let mut surf = liveinput::ScriptedKeys::new(mock, script, liveinput::MOCK_EVERY);
                runledger::begin("liveinput", "mock"); // RUN-LEDGER-0: the live-input run begins
                match liveinput::run(&mut surf, &mut session, "mock") {
                    Ok(live) => {
                        runledger::end(0);
                        for ln in liveinput::summary(&live, &session) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, liveinput::raw_json(&live, &session, &level, &tiles))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("liveinput court OK");
                    }
                    Err(r) => {
                        // REFUSAL-LOG-0: the loop's refusal is logged where it is emitted, then printed
                        let (ev, m) = r.into_event("mock");
                        refusallog::refuse(&ev, &format!("SHELL-LIVEINPUT: {}", m));
                        runledger::end(2);
                        exit(2)
                    }
                }
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    win32::liveinput_window(session);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = &mut session;
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run LIVE-INPUT-0 in the window");
                }
            }
        }
        "livesession-selftest" | "livesession-window" => {
            // LIVE-SESSION-0: LIVE-INPUT-0's live session, journaled as it runs and sealed on Esc into
            // build/sessions/<run_id>/session.json, which is read back and verified before the run counts as saved;
            // --resume continues a saved session (or a crashed run's journal) into a new file with lineage. Through the
            // mock with a key script (`-selftest`, what the gate runs) or in the borderless host window (`-window`,
            // window build only). Plants (selftest): geometry, noop (the surface's); crash, seal-unwritable, seal-flip,
            // seal-stale.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let level = opt("--level").unwrap_or_else(|| "oracle/levels/witness.lvl".to_string());
            let tiles = opt("--tiles").unwrap_or_else(|| "oracle/tiles/identity.tiles".to_string());
            let cam0 = parse_camera(&opt("--camera").unwrap_or_else(|| "28,28,N".to_string())).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
            let resume = opt("--resume");
            if args[1] == "livesession-selftest" {
                let script = liveinput::parse_script(&opt("--keys").unwrap_or_default()).unwrap_or_else(|m| refuse("USAGE", &m));
                let plant = opt("--plant").unwrap_or_default();
                let plan = livesession::Plan { level, tiles, cam0, resume, plant: plant.clone(), surface: "mock" };
                let prepared = livesession::prepare(plan).unwrap_or_else(|code| exit(code));
                let mock = presentexact::MockExact::new(latency1r::MockSurface::new(13_333, 1, None), &plant);
                let mut surf = liveinput::ScriptedKeys::new(mock, script, liveinput::MOCK_EVERY);
                let code = livesession::go(&mut surf, prepared);
                if code == 0 {
                    println!("livesession court OK");
                }
                exit(code)
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let plan = livesession::Plan { level, tiles, cam0, resume, plant: String::new(), surface: "gdi" };
                    win32::livesession_window(plan);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&level, &tiles, &cam0, &resume);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run LIVE-SESSION-0 in the window");
                }
            }
        }
        "live-selftest" | "live-window" => {
            // LIVE-AUTHOR-0: the live editor — LIVE-SESSION-0's durable loop (journal, seal, verification, --resume) under
            // the authoring binding (LIVE-INPUT-0's keys, plus 1-5 for the tile classes). Through the mock with a key
            // script (`-selftest`, what the gate runs; --out writes the loop's counts, views and pixels for the gate) or
            // in the borderless host window (`-window`, window build only). Plants (selftest): the surface's.
            // HOLD-WALK-0: under HOLD-WALK-0's held set (a held W/A/S/D or arrow walks, at most one admitted repeat per
            // composition, the rest coalesced); the selftest's script may group presses with `/` (drained together).
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let level = opt("--level").unwrap_or_else(|| "oracle/levels/witness.lvl".to_string());
            let tiles = opt("--tiles").unwrap_or_else(|| "oracle/tiles/identity.tiles".to_string());
            let cam0 = parse_camera(&opt("--camera").unwrap_or_else(|| "28,28,N".to_string())).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
            let resume = opt("--resume");
            if args[1] == "live-selftest" {
                let script = liveinput::parse_groups(&opt("--keys").unwrap_or_default()).unwrap_or_else(|m| refuse("USAGE", &m));
                let plant = opt("--plant").unwrap_or_default();
                let out = opt("--out");
                let plan = livesession::Plan { level: level.clone(), tiles: tiles.clone(), cam0, resume, plant: plant.clone(), surface: "mock" };
                let prepared = livesession::prepare(plan).unwrap_or_else(|code| exit(code));
                let mock = presentexact::MockExact::new(latency1r::MockSurface::new(13_333, 1, None), &plant);
                let mut surf = liveinput::ScriptedKeys::grouped(mock, script, liveinput::MOCK_EVERY);
                let (code, live) = livesession::go_with(&mut surf, prepared, liveauthor::bind, Some(holdwalk::held));
                if let (Some(o), Some(l)) = (out, live.as_ref()) {
                    fs::write(&o, liveinput::raw_json_counts(l, &level, &tiles)).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                }
                if code == 0 {
                    println!("live court OK");
                }
                exit(code)
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let plan = livesession::Plan { level, tiles, cam0, resume, plant: String::new(), surface: "gdi" };
                    win32::live_window(plan);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&level, &tiles, &cam0, &resume);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the live editor in the window");
                }
            }
        }
        "look-selftest" | "look-window" => {
            // MOUSE-LOOK-0: the live editor with the mouse — the same loop, session, journal and seal as live-window,
            // with a tick source switched on: every key press and horizontal mouse count the loop drains is stamped
            // with the tick of the clock (64 Hz), a tick's command is applied once by the tick run, and at a free
            // heading the loop presents the session's own picture. Through the mock (`-selftest`, what the gate runs: a
            // scripted mouse, keyboard and focus — `T:m+N`, `T:KEY`, `T:KEY+`, `T:blur`, `T:focus`, T in microseconds —
            // and a clock that is the composition count times 13,333 us; --out writes the counts for the gate) or in
            // the borderless host window with the real mouse (`-window`, window build only). Plants (selftest): the
            // surface's and LIVE-SESSION-0's.
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let level = opt("--level").unwrap_or_else(|| "oracle/levels/witness.lvl".to_string());
            let tiles = opt("--tiles").unwrap_or_else(|| "oracle/tiles/identity.tiles".to_string());
            let cam0 = parse_camera(&opt("--camera").unwrap_or_else(|| "28,28,N".to_string())).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
            let resume = opt("--resume");
            if args[1] == "look-selftest" {
                let script = mouselook::parse_script(&opt("--script").unwrap_or_default()).unwrap_or_else(|m| refuse("USAGE", &m));
                let plant = opt("--plant").unwrap_or_default();
                let out = opt("--out");
                let plan = livesession::Plan { level, tiles, cam0, resume, plant: plant.clone(), surface: "mock" };
                let prepared = livesession::prepare(plan).unwrap_or_else(|code| exit(code));
                let mock = presentexact::MockExact::new(latency1r::MockSurface::new(13_333, 1, None), &plant);
                let mut surf = mouselook::ScriptedLook::new(mock, script);
                let (code, raw) = livesession::go_look(&mut surf, prepared);
                if let (Some(o), Some(r)) = (out, raw.as_ref()) {
                    fs::write(&o, r).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                }
                if code == 0 {
                    println!("look court OK");
                }
                exit(code)
            } else {
                #[cfg(all(target_os = "windows", shell_window))]
                {
                    let plan = livesession::Plan { level, tiles, cam0, resume, plant: String::new(), surface: "gdi" };
                    win32::look_window(plan);
                }
                #[cfg(not(all(target_os = "windows", shell_window)))]
                {
                    let _ = (&level, &tiles, &cam0, &resume);
                    refuse("NO-WINDOW", "this build has no window (built without --cfg shell_window, or not on Windows); rebuild with `rustc --cfg shell_window` on the host to run the live editor with the mouse in the window");
                }
            }
        }
        "simtick-law" => {
            // SIM-TICK-0: the laws as lines — the tick, the nearest cardinal of every id, the quarter-turn law, the
            // turn's wrap, the delta, the sensitivity, the rebinding — for the gate to compare with its own derivation.
            for ln in simtick::law_lines(|b| mantle::hex(&mantle::sha256(b))) {
                println!("{}", ln);
            }
        }
        "simtick-selftest" => {
            // SIM-TICK-0: the tick run, windowless — a script of raw inputs with their times (`T:m+N`, `T:KEY`, `T:mult+`,
            // `T:mult-`, `T:step`; T in microseconds; SIM-TICK-0a: `T:KEY+` an auto-repeated press, and PGUP, PGDN and
            // TAB the sensitivity's control keys) through the accumulator, one command per tick, into the live
            // session; journaled as it runs and sealed (certified by the reference, written, read back, verified) into
            // build/sessions/<run_id>/session.json; --resume continues a saved session or a crashed run's journal.
            // No surface, no loop, no clock. --out writes the trace and the counts for the gate. Plants: crash,
            // seal-unwritable, seal-flip, seal-stale (LIVE-SESSION-0's).
            let a = &args[2..];
            let opt = |flag: &str| -> Option<String> {
                a.iter().position(|x| x == flag).and_then(|i| a.get(i + 1).cloned())
            };
            let level = opt("--level").unwrap_or_else(|| "oracle/levels/witness.lvl".to_string());
            let tiles = opt("--tiles").unwrap_or_else(|| "oracle/tiles/identity.tiles".to_string());
            let cam0 = parse_camera(&opt("--camera").unwrap_or_else(|| "28,28,N".to_string())).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
            let script = simtick::parse_script(&opt("--script").unwrap_or_default(), tickrun::key_named).unwrap_or_else(|m| refuse("USAGE", &m));
            let out = opt("--out");
            let plan = livesession::Plan { level, tiles, cam0, resume: opt("--resume"), plant: opt("--plant").unwrap_or_default(), surface: "none" };
            let prepared = livesession::prepare(plan).unwrap_or_else(|code| exit(code));
            let (code, raw) = livesession::go_ticks(prepared, &script);
            if let (Some(o), Some(r)) = (out, raw.as_ref()) {
                fs::write(&o, r).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
            }
            if code == 0 {
                println!("simtick court OK");
            }
            exit(code)
        }
        "form-verdict" | "form-court" | "form-splice" | "form-spell" => {
            // READER-COURT-0: the court command over the saved form's reader (kernel/savedform.rs). `form-verdict
            // (--document | --payload) FILE` prints the verdict on a file; `form-court ... --out OUT` gives every
            // single-byte mutant of it to the reader, in process; `form-splice --manifest M` gives it each file of M
            // with one splice applied, per line of that file's script; `form-spell --in F --out OUT` spells each
            // text of F. A verdict is data: the command ends 0 whatever the verdicts were.
            exit(readercourt::run(&args))
        }
        "design-compile" | "design-compile-selftest" => {
            // DESIGN-IR/DIFF-0: the compiler of the design language, windowless. `design-compile --session S --design
            // D` reads the design text D (VERDANDI-DESIGN 0) and the saved session S and writes to standard output the
            // one canonical batch for the net difference between S's world and the world D describes, and nothing
            // else; or it refuses, with a code and the design's line, and writes nothing there. It admits nothing and
            // writes no batch file, journal or session: the batch goes to `design`, which takes a batch and never a
            // design. `design-compile-selftest` is the same run with `--plant` naming one planted defect, or the court
            // in process: `--neighbourhood D` gives every single-byte mutant of D to the compiler against S.
            let selftest = args[1] == "design-compile-selftest";
            let a = &args[2..];
            let known: &[&str] = if selftest { &["--session", "--design", "--plant", "--neighbourhood"] } else { &["--session", "--design"] };
            if a.len() % 2 != 0 || a.chunks(2).any(|c| !known.contains(&c[0].as_str()))
                || known.iter().any(|k| a.chunks(2).filter(|c| c[0] == *k).count() > 1) {
                refuse("USAGE", &format!("{} takes each of {} at most once, each with a value", args[1], known.join(", ")));
            }
            let opt = |flag: &str| -> Option<String> { a.chunks(2).find(|c| c[0] == flag).map(|c| c[1].clone()) };
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            if let Some(d) = opt("--neighbourhood") {
                exit(designcompile::court(&session, &d))
            }
            let design = opt("--design").unwrap_or_else(|| refuse("USAGE", "needs --design"));
            let plant = opt("--plant").unwrap_or_default();
            if selftest && !designcompile::PLANTS.contains(&plant.as_str()) {
                refuse("USAGE", &format!("--plant is one of {}", designcompile::PLANTS.join(", ")));
            }
            exit(designcompile::run(&session, &design, &plant))
        }
        "design" | "design-selftest" => {
            // DESIGN-EVENT-0: a batch admitted by one admission, windowless. `design --session S --proposal P [--allow
            // ...] [--cells ...] [--classes ...] [--dry-run] [--previewed DIGEST,HEAD]` recognizes P (the batch
            // language) or refuses it, checks it against this shell, S and the grant, and admits its N operations as N
            // ordinary edit events sealed into one new session; S is never modified. `--dry-run` runs the same checks
            // and the same replay in memory, prints the binding and writes nothing; `--previewed` refuses unless the
            // bytes have that digest and the batch reaches that head. `design-selftest` is the same run with a plant
            // naming a death point (die-received, die-recognized, die-verified, die-opened, die-torn-K,
            // die-appended-K, die-written, die-replaced) or `memo`; or the court in process over every single-byte
            // mutant of a batch; or the memo against the computation with no memo, over a saved session.
            let selftest = args[1] == "design-selftest";
            let mut a: Vec<String> = args[2..].to_vec();
            let dry_run = match a.iter().position(|x| x == "--dry-run") {
                Some(i) => {
                    a.remove(i);
                    true
                }
                None => false,
            };
            let known: &[&str] = if selftest {
                &["--session", "--proposal", "--allow", "--cells", "--classes", "--previewed", "--plant", "--neighbourhood", "--memo"]
            } else {
                &["--session", "--proposal", "--allow", "--cells", "--classes", "--previewed"]
            };
            if a.len() % 2 != 0 || a.chunks(2).any(|c| !known.contains(&c[0].as_str()))
                || known.iter().any(|k| a.chunks(2).filter(|c| c[0] == *k).count() > 1) {
                refuse("USAGE", &format!("{} takes each of {} at most once, each with a value, and --dry-run at most once", args[1], known.join(", ")));
            }
            let opt = |flag: &str| -> Option<String> { a.chunks(2).find(|c| c[0] == flag).map(|c| c[1].clone()) };
            if let Some(p) = opt("--neighbourhood") {
                println!("{}", designevent::neighbourhood(&read(&p)));
                exit(0)
            }
            let plant = opt("--plant").unwrap_or_default();
            if let Some(s) = opt("--memo") {
                exit(designevent::memo(&s, plant == "memo"))
            }
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            let proposal = opt("--proposal").unwrap_or_else(|| refuse("USAGE", "needs --proposal"));
            let grant = admit::grant_of(opt("--allow").as_deref(), opt("--cells").as_deref(), opt("--classes").as_deref())
                .unwrap_or_else(|m| refuse("USAGE", &m));
            let previewed = opt("--previewed").map(|v| {
                let mut it = v.split(',');
                match (it.next(), it.next(), it.next()) {
                    (Some(d), Some(h), None) if livesession::hex64(d) && livesession::hex64(h) => (d.to_string(), h.to_string()),
                    _ => refuse("USAGE", "--previewed is DIGEST,HEAD: two values of 64 characters of 0-9a-f"),
                }
            });
            if dry_run && previewed.is_some() {
                refuse("USAGE", "--dry-run is the preview; --previewed belongs to the admission that follows it");
            }
            exit(designevent::run(&session, &proposal, &grant, &designevent::Mode { dry_run, previewed, plant }))
        }
        "admit" | "admit-selftest" | "admit-anchor" => {
            // ADMIT-0: the admission seam, windowless. `admit --session S --proposal P [--allow open,close,paint]
            // [--cells x0,z0,x1,z1] [--classes wall0,...]` recognizes P (VRDNP1) or refuses it, checks it against this
            // shell, the saved session S and the grant, and admits it as one edit event sealed into
            // build/sessions/<run_id>/session.json; S is never modified. `admit-anchor --session S` prints lines 1 to
            // 4 of a proposal anchored to S and reads only. `admit-selftest` is the same run with `--plant` naming a
            // death point (die-received, die-recognized, die-verified, die-opened, die-torn, die-appended,
            // die-written, die-replaced), or the reader court in process: `--neighbourhood P` gives every single-byte
            // mutant of P to the recognizer.
            let a = &args[2..];
            let known: &[&str] = match args[1].as_str() {
                "admit" => &["--session", "--proposal", "--allow", "--cells", "--classes"],
                "admit-anchor" => &["--session"],
                _ => &["--session", "--proposal", "--allow", "--cells", "--classes", "--plant", "--neighbourhood"],
            };
            if a.len() % 2 != 0 || a.chunks(2).any(|c| !known.contains(&c[0].as_str()))
                || known.iter().any(|k| a.chunks(2).filter(|c| c[0] == *k).count() > 1) {
                refuse("USAGE", &format!("{} takes each of {} at most once, each with a value", args[1], known.join(", ")));
            }
            let opt = |flag: &str| -> Option<String> { a.chunks(2).find(|c| c[0] == flag).map(|c| c[1].clone()) };
            if let Some(p) = opt("--neighbourhood") {
                println!("{}", admit::neighbourhood(&read(&p)));
                exit(0)
            }
            let session = opt("--session").unwrap_or_else(|| refuse("USAGE", "needs --session"));
            if args[1] == "admit-anchor" {
                exit(admit::anchor(&session))
            }
            let proposal = opt("--proposal").unwrap_or_else(|| refuse("USAGE", "needs --proposal"));
            let grant = admit::grant_of(opt("--allow").as_deref(), opt("--cells").as_deref(), opt("--classes").as_deref())
                .unwrap_or_else(|m| refuse("USAGE", &m));
            exit(admit::run(&session, &proposal, &grant, &opt("--plant").unwrap_or_default()))
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
