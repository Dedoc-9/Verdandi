// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/main.rs — the shell's command line.
//
//     rustc -O shell/main.rs -o build/shell
//     shell witness --level L --tiles T --camera x,z,F        # headless: the composite sha and the blit witness
//     shell selfcheck --level L --tiles T --camera x,z,F      # headless: `blit_roundtrip OK|BROKEN`
//     shell run --level L --tiles T --camera x,z,F [--measure N --host NAME]   # Windows only: a window; a
//                                                            # frame->composited record when --measure is given
//
// The window, the blit and the DWM composition clock live in shell/win32.rs, compiled only on Windows. On any
// other target `run` refuses `SHELL-NO-WINDOW` rather than pretending to present. `witness` and `selfcheck`
// are the blit-hash law and run anywhere: they are what the gate exercises.

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
#[path = "present.rs"]
mod present;
#[cfg(target_os = "windows")]
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

#[cfg_attr(not(target_os = "windows"), allow(dead_code))]
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
            #[cfg(target_os = "windows")]
            {
                win32::run(c, a.measure, &a.host, a.camera);
            }
            #[cfg(not(target_os = "windows"))]
            {
                let _ = c;
                refuse("NO-WINDOW", "this build has no window (compiled without target_os=windows); run it on the host to present and measure");
            }
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
