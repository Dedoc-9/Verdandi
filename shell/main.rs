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
                match presentexact::court(&mut surf, &inputs, per_cell) {
                    Ok(ex) => {
                        for ln in presentexact::summary(&ex) {
                            println!("{}", ln);
                        }
                        if let Some(o) = out {
                            fs::write(&o, presentexact::raw_record("gate-mock", "mock", &ex, 0))
                                .unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", o, e)));
                        }
                        println!("presentexact court OK");
                    }
                    Err(m) => refuse("PRESENTEXACT", &m),
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
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
