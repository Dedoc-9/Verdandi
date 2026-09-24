// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// workshop/input.rs — INPUT-0: input → a typed command → a new camera; the command log replays headless.
//
// Moving around the world is the projection's job, not the authority's: WORKSHOP-0b proved the camera is
// carried through a world edit untouched, and a view mutation is not an edit. So a "walk" — an initial camera
// and an ordered log of typed movement commands — is replayed against a FIXED level to reproduce the whole
// camera trajectory and the frame at every step, and it never touches W or M. The shell cannot smuggle a
// camera into the studio, because the walk replays without the shell.
//
// The commands (one letter each), pure and validated against the level:
//     L turn left      R turn right          (facing rotates; the cell does not move)
//     F forward        B back                (step along the facing; blocked by rock = a no-op, still logged)
//     Q strafe left    E strafe right        (step perpendicular; blocked by rock = a no-op)
// A move is valid iff the target cell is in the level and not `#` (rock); the kernel refuses a camera on rock,
// so a blocked step stays put — walking into a wall does not move you, deterministically.
//
// Each step's witness is the kernel's URDRFB1 frame digest for (level, camera, tiles), chained:
//     head = sha256( … sha256( sha256(MAGIC ‖ frame0) ‖ frame1 ) … ‖ frameN )
// so a walk is a hash-chained file like a session, and `verify` replays it and catches a tampered command
// (the trajectory, hence the frame digests, hence the head, all move). NOT here: the shell's key/mouse capture
// (WM_KEYDOWN → a command) is INPUT-0b, cfg-gated to Windows in the shell and run on the host; this file is the
// headless command → camera → frame discipline the gate exercises.
//
// A .walk file (line-oriented; `;` comments):
//     ; verdandi camera walk — VWLK1
//     level oracle/levels/witness.lvl
//     tiles oracle/tiles/identity.tiles
//     camera 34 28 W
//     commands LFFRF
//     head <hex>            (written by `input write`; checked by `input verify`)
//
//     rustc -O workshop/input.rs -o build/input
//     input replay --level L --tiles T --camera x,z,F --commands LFFRF   # print the trajectory + head
//     input write  --walk W.walk                                         # (re)compute and store the head
//     input verify --walk W.walk                                         # replay; catch a tampered command

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;

use std::env;
use std::fs;
use std::process::exit;

use formats::{compose, facing_letter, parse_camera, parse_level, parse_tiles, Camera, Level};
use mantle::{hex, parse_scene, picture, sha256, Refusal};

const MAGIC: &[u8] = b"VWLK1";

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("INPUT-{}: {}", code, detail);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path, e)))
}

// forward vector by facing (N=0 E=1 S=2 W=3), matching the kernel's `direction`.
fn forward(facing: u8) -> (i64, i64) {
    match facing {
        0 => (0, -1),
        1 => (1, 0),
        2 => (0, 1),
        _ => (-1, 0),
    }
}

fn traversable(level: &Level, x: i64, z: i64) -> bool {
    x >= 0 && z >= 0 && (x as usize) < level.w && (z as usize) < level.rows && level.cells[z as usize * level.w + x as usize] != b'#'
}

/// Apply one command to a camera against the level. A blocked step is a no-op (returns the same camera). An
/// unknown command is refused typed.
fn step(level: &Level, cam: Camera, cmd: u8) -> Result<Camera, String> {
    let mut c = cam;
    match cmd {
        b'L' => c.facing = (c.facing + 3) % 4,
        b'R' => c.facing = (c.facing + 1) % 4,
        b'F' | b'B' | b'Q' | b'E' => {
            let dir = match cmd {
                b'F' => forward(c.facing),
                b'B' => {
                    let (dx, dz) = forward(c.facing);
                    (-dx, -dz)
                }
                b'Q' => forward((c.facing + 3) % 4),
                _ => forward((c.facing + 1) % 4),
            };
            let (nx, nz) = (c.x + dir.0, c.z + dir.1);
            if traversable(level, nx, nz) {
                c.x = nx;
                c.z = nz;
            }
            // else: blocked, a no-op (walking into a wall does not move you)
        }
        other => return Err(format!("unknown command {:?}", other as char)),
    }
    Ok(c)
}

/// The kernel's URDRFB1 frame digest for this camera over the level and tiles (geometry only — appearance
/// would add M, but a walk witnesses the geometry the camera sees).
fn frame_digest(level_bytes: &[u8], tiles_bytes: &[u8], level: &Level, cam: Camera) -> String {
    let _ = level;
    let tiles = parse_tiles(tiles_bytes).unwrap_or_else(|Refusal(m)| refuse("INVALID-TILES", &m));
    let lvl = parse_level(level_bytes).unwrap_or_else(|Refusal(m)| refuse("INVALID-LEVEL", &m));
    let scene = parse_scene(&compose(&lvl, cam, &tiles)).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
    picture(&scene).frame_digest()
}

struct Walk {
    final_cam: Camera,
    head: String,
    steps: usize,
    blocked: usize,
}

/// Replay a command string from an initial camera, chaining each step's frame digest into the head.
fn replay(level_bytes: &[u8], tiles_bytes: &[u8], cam0: Camera, commands: &str) -> Walk {
    let level = parse_level(level_bytes).unwrap_or_else(|Refusal(m)| refuse("INVALID-LEVEL", &m));
    if !traversable(&level, cam0.x, cam0.z) {
        refuse("INVALID-CAMERA", "the initial camera stands on rock or off the level");
    }
    let mut cam = cam0;
    // genesis over the initial frame
    let f0 = frame_digest(level_bytes, tiles_bytes, &level, cam);
    let mut acc = {
        let mut buf = Vec::new();
        buf.extend_from_slice(MAGIC);
        buf.extend_from_slice(f0.as_bytes());
        sha256(&buf)
    };
    let mut blocked = 0usize;
    let mut steps = 0usize;
    for &b in commands.as_bytes() {
        if b == b' ' || b == b'\t' || b == b'\n' || b == b'\r' {
            continue;
        }
        let before = (cam.x, cam.z);
        cam = step(&level, cam, b).unwrap_or_else(|m| refuse("INVALID-COMMAND", &m));
        if matches!(b, b'F' | b'B' | b'Q' | b'E') && (cam.x, cam.z) == before {
            blocked += 1;
        }
        let f = frame_digest(level_bytes, tiles_bytes, &level, cam);
        let mut buf = Vec::with_capacity(32 + f.len());
        buf.extend_from_slice(&acc);
        buf.extend_from_slice(f.as_bytes());
        acc = sha256(&buf);
        steps += 1;
    }
    Walk { final_cam: cam, head: hex(&acc), steps, blocked }
}

// ------------------------------------------------------------------ the .walk file
struct WalkFile {
    level: String,
    tiles: String,
    camera: Camera,
    commands: String,
    head: Option<String>,
}

fn parse_walk(text: &str) -> Result<WalkFile, String> {
    let (mut level, mut tiles, mut camera, mut commands, mut head) = (None, None, None, None, None);
    for raw in text.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with(';') {
            continue;
        }
        let mut it = line.split_whitespace();
        match it.next() {
            Some("level") => level = Some(it.next().ok_or("level needs a path")?.to_string()),
            Some("tiles") => tiles = Some(it.next().ok_or("tiles needs a path")?.to_string()),
            Some("camera") => {
                let x = it.next().ok_or("camera x")?;
                let z = it.next().ok_or("camera z")?;
                let f = it.next().ok_or("camera facing")?;
                camera = Some(parse_camera(&format!("{},{},{}", x, z, f)).map_err(|Refusal(m)| m)?);
            }
            Some("commands") => commands = Some(it.next().unwrap_or("").to_string()),
            Some("head") => head = Some(it.next().ok_or("head needs a value")?.to_string()),
            Some(other) => return Err(format!("unknown directive {:?}", other)),
            None => {}
        }
    }
    Ok(WalkFile {
        level: level.ok_or("no level")?,
        tiles: tiles.ok_or("no tiles")?,
        camera: camera.ok_or("no camera")?,
        commands: commands.unwrap_or_default(),
        head,
    })
}

fn write_walk(path: &str, wf: &WalkFile, head: &str) {
    let text = format!(
        "; verdandi camera walk — VWLK1\nlevel {}\ntiles {}\ncamera {} {} {}\ncommands {}\nhead {}\n",
        wf.level, wf.tiles, wf.camera.x, wf.camera.z, facing_letter(wf.camera.facing), wf.commands, head
    );
    fs::write(path, text.as_bytes()).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", path, e)));
}

fn main() {
    let argv: Vec<String> = env::args().collect();
    if argv.len() < 2 {
        refuse("USAGE", "input replay … | input write --walk W | input verify --walk W");
    }
    let mut level = None;
    let mut tiles = None;
    let mut camera = None;
    let mut commands = None;
    let mut walk = None;
    let mut i = 2;
    while i < argv.len() {
        let v = || argv.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", argv[i])));
        match argv[i].as_str() {
            "--level" => level = Some(v()),
            "--tiles" => tiles = Some(v()),
            "--camera" => camera = Some(v()),
            "--commands" => commands = Some(v()),
            "--walk" => walk = Some(v()),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    match argv[1].as_str() {
        "replay" => {
            let (lp, tp, cp, cmd) = (
                level.unwrap_or_else(|| refuse("USAGE", "replay needs --level")),
                tiles.unwrap_or_else(|| refuse("USAGE", "replay needs --tiles")),
                camera.unwrap_or_else(|| refuse("USAGE", "replay needs --camera")),
                commands.unwrap_or_default(),
            );
            let cam0 = parse_camera(&cp).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));
            let w = replay(&read(&lp), &read(&tp), cam0, &cmd);
            println!("final camera {} {} {}", w.final_cam.x, w.final_cam.z, facing_letter(w.final_cam.facing));
            println!("steps {} blocked {}", w.steps, w.blocked);
            println!("head {}", w.head);
        }
        "write" | "verify" => {
            let wp = walk.unwrap_or_else(|| refuse("USAGE", "needs --walk"));
            let wf = parse_walk(&String::from_utf8(read(&wp)).unwrap_or_else(|_| refuse("INVALID-WALK", "not UTF-8"))).unwrap_or_else(|m| refuse("INVALID-WALK", &m));
            let w = replay(&read(&wf.level), &read(&wf.tiles), wf.camera, &wf.commands);
            if argv[1] == "write" {
                write_walk(&wp, &wf, &w.head);
                println!("WALK write head {} final {} {} {} ({} steps)", &w.head[..12], w.final_cam.x, w.final_cam.z, facing_letter(w.final_cam.facing), w.steps);
            } else {
                match wf.head {
                    Some(h) if h == w.head => {
                        println!("WALK verify OK head {} final {} {} {} ({} steps, {} blocked)", &w.head[..12], w.final_cam.x, w.final_cam.z, facing_letter(w.final_cam.facing), w.steps, w.blocked);
                    }
                    Some(h) => refuse("CHAIN-BROKEN", &format!("replay head {} != the walk's stored head {} — a command was tampered", &w.head[..12], &h[..12.min(h.len())])),
                    None => refuse("NO-HEAD", "the walk has no stored head; run `input write` first"),
                }
            }
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
