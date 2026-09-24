// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// workshop/text.rs — TEXT-0: the level as text, content split from provenance.
//
// A human authors a level's TOPOLOGY as text — a `depth` directive and a grid of `#.<>` (rock, floor, up,
// down) — and it round-trips to the same `VRDNLVL1` bytes (the same W). The depth's colour table and per-band
// maps are NOT authored here: they are Urðr's derived VIEW semantics, which Verðandi carries but does not
// compute (the kernel takes them as INPUT). So `from_text` borrows the palette (table + band maps) from a
// same-depth oracle level; the text holds only what a human should edit.
//
//     to_text(&Level) -> String            depth + grid; comments (`; …`) and blank lines are authoring, ignored
//     from_text(&str, palette: &Level)     cells + depth from the text, table/maps from a same-depth Level
//
// TWO DIGESTS, the content/provenance split (as Urðr's `worldbind` row earned it):
//   W (content)      = sha256 of the reassembled VRDNLVL1 bytes — UNMOVED by a reformat (a comment, a blank
//                      line, a respaced directive), MOVED by a cell edit.
//   authoring digest = sha256 of the exact text bytes — MOVED by any text change, reformat included.
// So the record can tell an edit from a reformat: reformat moves the authoring digest and not W; an edit moves
// both. A `;` comment can never move W (comments are skipped before content is read); a cell change can
// never leave W unmoved. `#` is always a cell (rock), never a comment.
//
//     rustc -O workshop/text.rs -o build/text
//     text to-text   --level L.lvl                                  # the text form
//     text from-text --text T.wtxt --palette-from R.lvl --out O.lvl # back to bytes (R.lvl of the same depth)
//     text digests   --text T.wtxt --palette-from R.lvl             # `content <W>` and `authoring <sha>`

#[allow(dead_code)]
#[path = "../kernel/mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "../kernel/formats.rs"]
mod formats;

use std::env;
use std::fs;
use std::process::exit;

use formats::{level_bytes, parse_level, Level, ALPHABET};
use mantle::{hex, sha256, Refusal};

const MAGIC: &str = "VWTX1";

fn refuse(code: &str, detail: &str) -> ! {
    eprintln!("TEXT-{}: {}", code, detail);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse("CANNOT-READ", &format!("{}: {}", path, e)))
}

/// The canonical text of a level: a header comment, the depth directive, then the grid.
pub fn to_text(level: &Level) -> String {
    let mut out = String::new();
    out.push_str(&format!("; verdandi world text — {}\n", MAGIC));
    out.push_str(&format!("; {}x{}, depth {} (a `;` line is a comment; `depth` and the grid below are the authority)\n", level.w, level.rows, level.depth));
    out.push_str(&format!("depth {}\n", level.depth));
    out.push_str("grid\n");
    for z in 0..level.rows {
        let row = &level.cells[z * level.w..(z + 1) * level.w];
        out.push_str(std::str::from_utf8(row).unwrap_or("?"));
        out.push('\n');
    }
    out
}

/// Text + a same-depth palette source -> a Level. The cells and depth come from the text; the table and band
/// maps come from `palette` (which must be of the parsed depth). Comments (`#…`) and blank lines are ignored.
pub fn from_text(text: &str, palette: &Level) -> Result<Level, String> {
    let mut depth: Option<u32> = None;
    let mut in_grid = false;
    let mut grid: Vec<Vec<u8>> = Vec::new();
    for raw in text.lines() {
        let line = raw.strip_suffix('\r').unwrap_or(raw);
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with(';') {
            continue; // authoring: a blank line or a `;` comment, ignored for content
        }
        if !in_grid {
            let mut it = trimmed.split_whitespace();
            match it.next() {
                Some("depth") => {
                    let v = it.next().ok_or("`depth` needs a value")?;
                    depth = Some(v.parse().map_err(|_| format!("depth {:?} is not a number", v))?);
                }
                Some("grid") => {
                    in_grid = true;
                }
                Some(other) => return Err(format!("unknown directive {:?} (expected `depth` or `grid`)", other)),
                None => {}
            }
        } else {
            // a grid row: exactly the cell bytes (no trimming — a space is not a cell)
            let bytes = line.as_bytes();
            if let Some(&c) = bytes.iter().find(|c| !ALPHABET.contains(c)) {
                return Err(format!("grid byte {} is not in the alphabet #.<>", c));
            }
            grid.push(bytes.to_vec());
        }
    }
    let depth = depth.ok_or("no `depth` directive")?;
    if !in_grid || grid.is_empty() {
        return Err("no `grid`".to_string());
    }
    let w = grid[0].len();
    if w == 0 {
        return Err("the first grid row is empty".to_string());
    }
    if let Some(bad) = grid.iter().position(|r| r.len() != w) {
        return Err(format!("grid row {} has width {} but row 0 has {}", bad, grid[bad].len(), w));
    }
    let rows = grid.len();
    if depth != palette.depth {
        return Err(format!("the palette source is depth {} but the text is depth {}", palette.depth, depth));
    }
    if w != palette.w || rows != palette.rows {
        // the palette's table/maps do not depend on w/rows, but VRDNLVL1 pairs cells with them; a size mismatch
        // is allowed (the maps are size-independent), so this is not an error — recorded here for clarity.
    }
    let cells: Vec<u8> = grid.into_iter().flatten().collect();
    Ok(Level {
        w,
        rows,
        cells,
        depth,
        table: palette.table.clone(),
        wall_map: palette.wall_map.clone(),
        floor_map: palette.floor_map.clone(),
    })
}

fn content_digest(level: &Level) -> String {
    hex(&sha256(&level_bytes(level)))
}

fn authoring_digest(text: &str) -> String {
    hex(&sha256(text.as_bytes()))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        refuse("USAGE", "text to-text ... | text from-text ... | text digests ...");
    }
    let mut level_path = None;
    let mut text_path = None;
    let mut palette_path = None;
    let mut out_path = None;
    let mut i = 2;
    while i < args.len() {
        let v = || args.get(i + 1).cloned().unwrap_or_else(|| refuse("USAGE", &format!("{} needs a value", args[i])));
        match args[i].as_str() {
            "--level" => level_path = Some(v()),
            "--text" => text_path = Some(v()),
            "--palette-from" => palette_path = Some(v()),
            "--out" => out_path = Some(v()),
            a => refuse("USAGE", &format!("unknown argument {}", a)),
        }
        i += 2;
    }
    match args[1].as_str() {
        "to-text" => {
            let lp = level_path.unwrap_or_else(|| refuse("USAGE", "to-text needs --level"));
            let level = parse_level(&read(&lp)).unwrap_or_else(|Refusal(m)| refuse("INVALID-LEVEL", &m));
            print!("{}", to_text(&level));
        }
        "from-text" | "digests" => {
            let tp = text_path.unwrap_or_else(|| refuse("USAGE", "needs --text"));
            let pp = palette_path.unwrap_or_else(|| refuse("USAGE", "needs --palette-from R.lvl (a same-depth level)"));
            let text = String::from_utf8(read(&tp)).unwrap_or_else(|_| refuse("INVALID-TEXT", "not UTF-8"));
            let palette = parse_level(&read(&pp)).unwrap_or_else(|Refusal(m)| refuse("INVALID-PALETTE", &m));
            let level = from_text(&text, &palette).unwrap_or_else(|m| refuse("INVALID-TEXT", &m));
            if args[1] == "from-text" {
                let op = out_path.unwrap_or_else(|| refuse("USAGE", "from-text needs --out"));
                fs::write(&op, level_bytes(&level)).unwrap_or_else(|e| refuse("CANNOT-WRITE", &format!("{}: {}", op, e)));
                println!("content {}", content_digest(&level));
            } else {
                println!("content {}", content_digest(&level));
                println!("authoring {}", authoring_digest(&text));
            }
        }
        other => refuse("USAGE", &format!("unknown command {}", other)),
    }
}
