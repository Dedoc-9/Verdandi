// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/main.rs — the kernel's command line: a scene in, two witnesses out; the bench off-gate.
//
//     rustc -O kernel/main.rs -o build/kernel
//     kernel scene.bin                                           # URDRMNTI bytes
//     kernel --level L.lvl --tiles T.tiles --camera 34,28,W      # composed from the studio's files
//     kernel ... --bench 200 --warm 20                           # off-gate: p50/p95/p99/max us per phase
//     kernel ... --write-scene out.bin                           # the composed URDRMNTI bytes, for a record
//
// Prints `frame <sha256>`, `pixels <sha256>`, `selfcheck OK|DIVERGED` (the picture computed twice), and
// with --bench the per-phase percentiles and the host line. Renderer time only: no window, no present, no
// input — never an input-to-photon number.

#[allow(dead_code)]
#[path = "mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "formats.rs"]
mod formats;

use std::env;
use std::fs;
use std::process::exit;
use std::time::Instant;

use mantle::{frame_digest, hex, parse_scene, picture, sha256, Refusal, Strip, H, W};

fn refuse(msg: &str) -> ! {
    eprintln!("KERNEL-REFUSE: {}", msg);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse(&format!("cannot read {}: {}", path, e)))
}

fn percentiles(mut xs: Vec<u128>) -> (u128, u128, u128, u128) {
    xs.sort_unstable();
    let n = xs.len();
    let at = |p: f64| xs[(((n as f64) * p).ceil() as usize).saturating_sub(1).min(n - 1)];
    (at(0.50), at(0.95), at(0.99), xs[n - 1])
}

fn host_line() -> String {
    let mut cpu = String::from("unknown");
    if let Ok(txt) = fs::read_to_string("/proc/cpuinfo") {
        for ln in txt.lines() {
            if ln.starts_with("model name") {
                if let Some(v) = ln.split(':').nth(1) {
                    cpu = v.trim().to_string();
                    break;
                }
            }
        }
    } else if let Ok(v) = env::var("PROCESSOR_IDENTIFIER") {
        cpu = v;
    }
    format!("host os={} arch={} cpu=\"{}\"", env::consts::OS, env::consts::ARCH, cpu)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let usage = "usage: kernel <scene.bin> | --level L --tiles T --camera x,z,F  [--bench N] [--warm M] [--write-scene OUT]";
    let mut scene_path: Option<String> = None;
    let (mut level, mut tiles, mut camera): (Option<String>, Option<String>, Option<String>) = (None, None, None);
    let mut bench = 0usize;
    let mut warm = 10usize;
    let mut write_scene: Option<String> = None;
    let mut i = 1;
    while i < args.len() {
        let next = |i: usize| -> String {
            args.get(i + 1).cloned().unwrap_or_else(|| refuse(&format!("{} needs a value", args[i])))
        };
        match args[i].as_str() {
            "--level" => { level = Some(next(i)); i += 2; }
            "--tiles" => { tiles = Some(next(i)); i += 2; }
            "--camera" => { camera = Some(next(i)); i += 2; }
            "--bench" => { bench = next(i).parse().unwrap_or_else(|_| refuse("--bench needs a count")); i += 2; }
            "--warm" => { warm = next(i).parse().unwrap_or_else(|_| refuse("--warm needs a count")); i += 2; }
            "--write-scene" => { write_scene = Some(next(i)); i += 2; }
            a if a.starts_with("--") => refuse(&format!("unknown argument {}", a)),
            _ => { scene_path = Some(args[i].clone()); i += 1; }
        }
    }
    let data: Vec<u8> = match (scene_path, level, tiles, camera) {
        (Some(p), None, None, None) => read(&p),
        (None, Some(l), Some(t), Some(c)) => {
            let lvl = formats::parse_level(&read(&l)).unwrap_or_else(|Refusal(m)| refuse(&m));
            let til = formats::parse_tiles(&read(&t)).unwrap_or_else(|Refusal(m)| refuse(&m));
            let cam = formats::parse_camera(&c).unwrap_or_else(|Refusal(m)| refuse(&m));
            formats::compose(&lvl, cam, &til)
        }
        _ => refuse(usage),
    };
    if let Some(out) = &write_scene {
        fs::write(out, &data).unwrap_or_else(|e| refuse(&format!("cannot write {}: {}", out, e)));
    }
    let scene = parse_scene(&data).unwrap_or_else(|Refusal(m)| refuse(&m));

    // the witnesses, twice (determinism is the selfcheck)
    let first = picture(&scene);
    let fd = first.frame_digest();
    let ps = first.pixel_sha256();
    let second = picture(&scene);
    let same = second.frame_digest() == fd && second.pixel_sha256() == ps;
    println!("frame {}", fd);
    println!("pixels {}", ps);
    println!("selfcheck {}", if same { "OK" } else { "DIVERGED" });

    if bench > 0 {
        // warm-up excluded; each sample is one full frame: traversal+strip+floor (frame) then the texel pass (pixels)
        let mut strips: Vec<Strip> = Vec::with_capacity(W);
        let mut buf = vec![0u8; W * H];
        let mut rgb = vec![0u8; W * H * 3];
        let mut t_frame: Vec<u128> = Vec::with_capacity(bench);
        let mut t_pix: Vec<u128> = Vec::with_capacity(bench);
        let mut t_tot: Vec<u128> = Vec::with_capacity(bench);
        for k in 0..(warm + bench) {
            let t0 = Instant::now();
            scene.strips(&mut strips);
            scene.frame(&strips, &mut buf);
            let t1 = Instant::now();
            scene.emit(&strips, &buf, &mut rgb);
            let t2 = Instant::now();
            if k >= warm {
                t_frame.push((t1 - t0).as_micros());
                t_pix.push((t2 - t1).as_micros());
                t_tot.push((t2 - t0).as_micros());
            }
        }
        // the bench rendered the same thing it witnessed
        let same_after = frame_digest(&buf) == fd && hex(&sha256(&rgb)) == ps;
        let (a, b, c, d) = percentiles(t_frame);
        println!("bench_frame_us p50={} p95={} p99={} max={}", a, b, c, d);
        let (a, b, c, d) = percentiles(t_pix);
        println!("bench_pixels_us p50={} p95={} p99={} max={}", a, b, c, d);
        let (a, b, c, d) = percentiles(t_tot);
        println!("bench_total_us p50={} p95={} p99={} max={}", a, b, c, d);
        println!("bench_samples {} warmup {} same_witnesses {}", bench, warm, if same_after { "OK" } else { "DIVERGED" });
        println!("{}", host_line());
    }
    if !same {
        exit(1);
    }
}
