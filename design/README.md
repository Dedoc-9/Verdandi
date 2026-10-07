# design/ — the design surface (content time)

```
  a person · a script · a model
              │  a few lines of design text
              ▼
        design.py  propose      hands the text's bytes to the shell's compiler and keeps the batch it writes
              │    preview      the shell's dry run of that batch: every check, the replay, nothing written
              │    admit        the same bytes go to the shell, bound to the preview
              ▼
        shell design-compile    the certified compiler (DESIGN-IR/DIFF-0): the text and a session give the one
              │                 batch (VRDNP2) for the net difference, or a refusal with its code and the line
              ▼
        shell design            the certified admission (DESIGN-EVENT-0): recognizes the batch, checks the grant
              │                 at every operation, appends them as ordinary edits, or refuses the whole
              ▼
        the session             the authority; one new sealed file for one design, the old one never touched
              ▼
        the kernel              renders it:  shell live-window --resume <session.json>
```

This folder is **content time**. Nothing here is a row of the gate, and no gate runs when it is used. The gate
certified the shell, the session and the kernel; this tool only drives them. It holds no authority of its own and
computes no change set: the batch is written by `shell design-compile`, every change to a world is made by
`shell design`, and what either refuses stays refused. Nothing under `verify/` reads this folder.

## The five verbs

| verb | what it does | what it changes |
|---|---|---|
| `inspect` | the project's identities, the session's head, the world from above, the tile classes, the grant, what can be proposed | nothing |
| `propose` | reads design text, hands its bytes to the shell's compiler against the current session, keeps the batch and the text | the pending batch; the text, kept under its id |
| `preview` | asks the shell for a dry run of the batch; shows CURRENT against PROPOSED, the changes and the readings | nothing but the note of what was previewed |
| `admit` | gives the previewed bytes to the shell, bound to the preview | the project's head moves to one new session |
| `undo` | the project stands at the session before | the project's pointer; no file is deleted |

`new` or `open` starts a project, `grant` sets what may be admitted, `reject` drops a proposal, `status` says where
things stand. Every command takes `--project DIR`; without it the project is `design/work/`.

```
python design/design.py new
python design/design.py grant --cells 1,1,20,12 --classes floor
python design/design.py inspect
python design/design.py propose my-room.txt
python design/design.py preview
python design/design.py admit
```

## The design text

```
VERDANDI-DESIGN 0
# a room with two entrances
room 6,3 16,10
entrance 6,6
entrance 11,10
paint floor 60,70,90
```

| statement | meaning |
|---|---|
| `open x0,z0 x1,z1` | every cell of the rectangle becomes floor (one corner alone is one cell) |
| `close x0,z0 x1,z1` | every cell of the rectangle becomes rock |
| `room x0,z0 x1,z1` | the rectangle's rim becomes rock and its inside floor |
| `entrance x,z` | one cell becomes floor |
| `paint CLASS R,G,B` | a tile class (`wall0` `wall1` `wall2` `wall3` `floor`) takes one colour |

Statements apply in order, a later one writing over an earlier one. What is proposed is the **net difference**
from the current world: one operation per cell or class that ends up different. At most 16,384 bytes, 64 statements
and 4,096 operations. `x` runs across, `z` runs down, both from 0.

The text is `VERDANDI-DESIGN 0`, the source language DESIGN-IR/DIFF-0 registered, pinned at the byte: lines end in
LF (a CR directly before it is dropped), words are separated by spaces or tabs, and a comment runs from `#` to the
end of its line. Three things it will not say, each refused by the compiler with the line: floor written to a cell
on the level's border (`COMPILE-BORDER`), anything written to a stair (`COMPILE-STAIR`), and a design that leaves
the camera's cell closed (`COMPILE-CAMERA`). A design that changes nothing is refused too (`COMPILE-EMPTY`): a
batch says at least one operation.

What the compiler writes is one batch in `VRDNP2`, DESIGN-EVENT-0's language: a net change set in one fixed order,
cells in row-major order and then the classes, each target once. Two texts with the same net difference compile to
the same operations. They are still two designs: **the batch's id is the SHA-256 of the text's bytes exactly as
they were given**, so a comment or a CR LF makes another id. The tool keeps each proposed text under its id in
`designs/`. The id is a commitment and not a copy: only the kept bytes say what was designed.

One consequence is the session's own rule: a session refuses an id already in its history
(`ADMIT-DUPLICATE`), so the same design bytes are admitted at most once in a history. A design to be admitted
again differs in a byte; a comment is enough.

## What is authority and what is a view

| | |
|---|---|
| authority | the session file the shell saved and verified. Its head is the world's identity |
| the compiler | `shell design-compile`: the one production compiler, held on every gate to an independent reference byte for byte, and to the design's target by content |
| the verifier | `shell design`: the batch's form, the anchor, the grant and the session's own validation at every operation |
| the grant | the admitter's, set with `grant` and passed on the shell's command line. A design text cannot carry or widen it. With no cells granted, every cell operation is refused |
| a view | everything this tool computes itself: the top view, the counts, what is reachable from the camera. For a reader. Where it disagrees with the shell, the shell is right |
| the tool's own check | that the batch it was handed names the digest of the bytes it gave and the head it gave them against, and that a pending batch is still those bytes when it is previewed |
| a preview | the shell's dry run: the same checks and the same replay as the admission, with nothing written. It names the head the batch would give. Not authority: no session exists for it |
| the binding | `admit` hands the shell the previewed digest and head. The shell refuses unless the bytes have that digest and reach that head |

## Limits

- **An admission still replays the whole session.** One design is one run of the shell, and that run loads and
  verifies the session it is admitted to, then verifies the file it wrote. The cost of an admission grows with the
  session's history. Nothing skips replay.
- **The compiler is certified; what you meant is not.** The gate holds that the batch is the text's net
  difference, on the designs its court compiles. Whether the text says what you meant by a room is yours to check,
  and the preview is how. The camera's and the stair's rules are the design language's: a batch from any other
  editor is not held to them.
- **Cells and classes, nothing above them.** A room here is a statement that expands to cells. Once admitted there
  is no room, only cells. There are no objects, relations or constraints in the world.
- **Readings, not constraints.** "Reachable from the camera" is a flood over floor cells, computed by this tool.
  Nothing registers it and nothing holds it.
- **The top view is not the certified picture.** The kernel's frame is seen by opening the session in the window.
- **A starting session made by `new` comes from the live editor's mock** (`shell live-selftest`), with no key
  pressed. `open --session` starts from one saved in the window.
- **`undo` moves the project's pointer.** The session stepped back from stays on disk, sealed and unchanged.
- **Its checks are its own.** `python design/test_design.py` drives the tool against a real shell: seventeen
  checks. Thirteen drive it as a program. One holds it as a client of the shell's compiler (DESIGN-IR/CLIENT-FENCE-0:
  the pending batch is byte for byte what the compiler writes; with a stand-in compiler the tool proposes what the
  stand-in wrote; an admit is bound to its preview; the source holds no line of the batch language to write), and
  four are plants — changed copies of the tool that compute their own difference, rewrite the compiler's result,
  never call it, or admit without the binding — each of which has to fail that check. None is a row of the gate.
