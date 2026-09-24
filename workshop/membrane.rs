// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// workshop/membrane.rs — MEMBRANE-0: the one-way law as a COMPILE-TIME wall.
//
// The charter's dependency rule forbids `shell -> canonical authority` and `kernel -> workshop`: the render
// path READS the authority and never reaches back to write it. HUD-0 proved the read is index-free at run
// time; RECORD-0 proved a record cannot smuggle a verdict; this rung proves the deeper thing with the borrow
// checker instead of a test — that you cannot edit the world while you are mid-render of it, because a live
// read-borrow of the authority makes the mutable borrow an edit needs a compile error.
//
//     Authority { level, tiles }         owns the world (the only holder of the bytes)
//     Authority::read(&self) -> Reading  the render path: an IMMUTABLE borrow, `Reading<'a>` tied to `&self`
//     Authority::edit_cell(&mut self)    the write path: needs `&mut self`
//
// While a `Reading` is alive, `&mut self` cannot be taken, so `edit_cell` cannot be called — mirrored from the
// old project's `SimExport<'a>` (a read window that forbids `tick()` while it lives). The gate exercises it as
// a ROW WHOSE PASS IS rustc's REFUSAL: compiled with `--cfg membrane_probe_illegal`, the `illegal` function
// below edits through a live `Reading` and MUST fail to borrow-check (E0502); compiled normally, `main`'s
// read-then-edit path compiles and renders the kernel's own corpus witnesses (the typestate carries identical
// semantics — the wall costs nothing).
//
// BOUNDARY (recorded, as the old project's membrane recorded its own): this stops HONEST mistakes — a render
// path that reaches back to mutate the authority — not an adversary who writes `unsafe`, a raw pointer or
// interior mutability. It is an API-hygiene wall, never a security boundary. `typestate != security`.
//
//     rustc -O workshop/membrane.rs -o build/membrane                          # the legal build (the gate)
//     rustc -O --cfg membrane_probe_illegal workshop/membrane.rs -o /dev/null  # MUST fail (the wall bites)
//     membrane witness --level L --tiles T --camera x,z,F   # the Reading path's two witnesses
//     membrane legal   --level L --tiles T --camera x,z,F --edit x,z,C   # read fully, then edit; prints OK

#![allow(unexpected_cfgs)]

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;

use std::env;
use std::fs;
use std::process::exit;

use formats::{compose, parse_camera, parse_level, parse_tiles, Camera, Level, Tiles, ALPHABET};
use mantle::{parse_scene, picture, Refusal};

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("MEMBRANE-{}: {}", code, detail);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path, e)))
}

/// The world, owned. The only holder of the level and tile bytes in this module.
pub struct Authority {
    level: Level,
    tiles: Tiles,
}

/// The render path's view of the authority: an immutable borrow, its lifetime tied to `&Authority`. While one
/// is alive the borrow checker forbids `&mut Authority`, so no edit can run.
pub struct Reading<'a> {
    level: &'a Level,
    tiles: &'a Tiles,
}

impl Authority {
    pub fn new(level: Level, tiles: Tiles) -> Self {
        Authority { level, tiles }
    }

    /// The read path. Borrows `self` immutably.
    pub fn read(&self) -> Reading<'_> {
        Reading { level: &self.level, tiles: &self.tiles }
    }

    /// The write path. Needs `&mut self`, so it cannot run while a `Reading` is alive. Minimal validation —
    /// the workshop's `edit.rs` owns the full edit vocabulary; this is only the write half of the membrane.
    pub fn edit_cell(&mut self, x: usize, z: usize, to: u8, cam: Camera) -> Result<(), String> {
        if x >= self.level.w || z >= self.level.rows {
            return Err(format!("cell ({}, {}) outside the {}x{} level", x, z, self.level.w, self.level.rows));
        }
        if !ALPHABET.contains(&to) {
            return Err(format!("cell value {} is not in the alphabet #.<>", to));
        }
        let border = x == 0 || z == 0 || x == self.level.w - 1 || z == self.level.rows - 1;
        if border && to != b'#' {
            return Err(format!("cell ({}, {}) is on the border, which must stay rock", x, z));
        }
        let mut cells = self.level.cells.clone();
        cells[z * self.level.w + x] = to;
        if cam.x < 0 || cam.z < 0 || cam.x as usize >= self.level.w || cam.z as usize >= self.level.rows
            || cells[cam.z as usize * self.level.w + cam.x as usize] == b'#'
        {
            return Err(format!("the carried camera ({}, {}) would stand in rock", cam.x, cam.z));
        }
        self.level.cells = cells;
        Ok(())
    }
}

impl<'a> Reading<'a> {
    /// The kernel's input, composed from the borrowed authority. Read-only: it takes `&self`.
    pub fn compose_bytes(&self, cam: Camera) -> Vec<u8> {
        compose(self.level, cam, self.tiles)
    }

    /// The two witnesses of rendering this reading — equal to the kernel's, since the bytes are the kernel's.
    pub fn witnesses(&self, cam: Camera) -> Result<(String, String), Refusal> {
        let scene = parse_scene(&self.compose_bytes(cam))?;
        let pic = picture(&scene);
        Ok((pic.frame_digest(), pic.pixel_sha256()))
    }
}

// THE PLANT: only compiled under `--cfg membrane_probe_illegal`. It holds a `Reading` (an immutable borrow of
// `auth`) and then calls `edit_cell` (a mutable borrow) while the reading is still used afterward — which the
// borrow checker must reject (E0502: cannot borrow `*auth` as mutable because it is also borrowed as
// immutable). The gate compiles this configuration and PASSES iff rustc REFUSES it.
#[cfg(membrane_probe_illegal)]
fn illegal(auth: &mut Authority, cam: Camera) -> Vec<u8> {
    let reading = auth.read(); // immutable borrow of *auth begins
    let _ = auth.edit_cell(1, 1, b'.', cam); // mutable borrow of *auth while `reading` is still live below
    reading.compose_bytes(cam) // `reading` used here: its borrow spans the edit above -> COMPILE ERROR
}

fn short(s: &str) -> &str {
    &s[..12.min(s.len())]
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        refuse("USAGE", "membrane witness ... | membrane legal ...");
    }
    let mut level_path = None;
    let mut tiles_path = None;
    let mut camera = None;
    let mut edit = None;
    let mut i = 2;
    while i < args.len() {
        let v = || args.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", args[i])));
        match args[i].as_str() {
            "--level" => level_path = Some(v()),
            "--tiles" => tiles_path = Some(v()),
            "--camera" => camera = Some(v()),
            "--edit" => edit = Some(v()),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    let (lp, tp, cp) = match (level_path, tiles_path, camera) {
        (Some(a), Some(b), Some(c)) => (a, b, c),
        _ => refuse("USAGE", "needs --level --tiles --camera"),
    };
    let level = parse_level(&read(&lp)).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let tiles = parse_tiles(&read(&tp)).unwrap_or_else(|Refusal(m)| refuse("INVALID-AUTHORITY", &m));
    let cam = parse_camera(&cp).unwrap_or_else(|Refusal(m)| refuse("INVALID-CAMERA", &m));

    match args[1].as_str() {
        "witness" => {
            let auth = Authority::new(level, tiles);
            let (frame, pixels) = auth.read().witnesses(cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m));
            println!("frame {}", frame);
            println!("pixels {}", pixels);
        }
        "legal" => {
            // The legal sequence the wall permits: read FULLY (the Reading is dropped when `before` is bound),
            // THEN edit (no Reading alive), then read again. This compiles; `illegal` above does not.
            let mut auth = Authority::new(level, tiles);
            let before = auth.read().witnesses(cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m));
            let spec = edit.unwrap_or_else(|| refuse("USAGE", "legal needs --edit x,z,C"));
            let parts: Vec<&str> = spec.split(',').collect();
            if parts.len() != 3 {
                refuse("USAGE", "edit is x,z,C");
            }
            let x: usize = parts[0].parse().unwrap_or_else(|_| refuse("USAGE", "edit x"));
            let z: usize = parts[1].parse().unwrap_or_else(|_| refuse("USAGE", "edit z"));
            let to = parts[2].as_bytes();
            if to.len() != 1 {
                refuse("USAGE", "edit C is one byte");
            }
            auth.edit_cell(x, z, to[0], cam).unwrap_or_else(|m| refuse("INVALID-EDIT", &m));
            let after = auth.read().witnesses(cam).unwrap_or_else(|Refusal(m)| refuse("INVALID-SCENE", &m));
            println!("legal OK before frame {} after frame {} (read, then edit, then read)", short(&before.0), short(&after.0));
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
