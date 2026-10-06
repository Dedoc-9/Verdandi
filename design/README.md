# design/ — the design surface (content time)

```
  a person · a script · a model
              │  a few lines of design text
              ▼
        design.py  propose      compiles the text to its net difference, written as ONE batch (VRDNP2)
              │    preview      the shell's dry run of that batch: every check, the replay, nothing written
              │    admit        the same bytes go to the shell, bound to the preview
              ▼
        shell design            the certified seam (DESIGN-EVENT-0): recognizes the batch, checks the grant
              │                 at every operation, appends them as ordinary edits, or refuses the whole
              ▼
        the session             the authority; one new sealed file for one design, the old one never touched
              ▼
        the kernel              renders it:  shell live-window --resume <session.json>
```

This folder is **content time**. Nothing here is a row of the gate, and no gate runs when it is used. The gate
certified the shell, the session and the kernel; this tool only drives them. It holds no authority of its own:
every change to a world is made by `shell design`, and what the shell refuses stays refused.

## The five verbs

| verb | what it does | what it changes |
|---|---|---|
| `inspect` | the project's identities, the session's head, the world from above, the tile classes, the grant, what can be proposed | nothing |
| `propose` | reads design text, compiles it against the current world, writes the batch | the pending batch |
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

Statements apply in order to a working copy. What is proposed is the **net difference** from the current world: one
operation per cell or class that ends up different. At most 64 statements and 4,096 operations. `x` runs across,
`z` runs down, both from 0.

This text is the tool's own. It is not a registered language of the tree. What reaches the shell is one batch in
`VRDNP2`, DESIGN-EVENT-0's language: a net change set in one fixed order, cells in row-major order and then the
classes, each target once. Two texts with the same net difference compile to the same operations, and compiling a
set that is already in order gives it back unchanged. A design that changes nothing proposes no batch: the language
has none of no operations. The shell rewrites nothing: it recognizes the batch or refuses it.

## What is authority and what is a view

| | |
|---|---|
| authority | the session file the shell saved and verified. Its head is the world's identity |
| the verifier | `shell design`: the batch's form, the anchor, the grant and the session's own validation at every operation |
| the grant | the admitter's, set with `grant` and passed on the shell's command line. A design text cannot carry or widen it. With no cells granted, every cell operation is refused |
| a view | everything this tool computes itself: the top view, the counts, what is reachable from the camera. For a reader. Where it disagrees with the shell, the shell is right |
| a prediction | the tool refuses an opened border, a changed stair and a closed camera cell before asking the shell. `propose --no-predict` sends them to the shell, which refuses them itself |
| a preview | the shell's dry run: the same checks and the same replay as the admission, with nothing written. It names the head the batch would give. Not authority: no session exists for it |
| the binding | `admit` hands the shell the previewed digest and head. The shell refuses unless the bytes have that digest and reach that head |

## Limits

- **An admission still replays the whole session.** One design is one run of the shell, and that run loads and
  verifies the session it is admitted to, then verifies the file it wrote. The cost of an admission grows with the
  session's history. Nothing skips replay.
- **The compiler is not certified.** The shell holds the batch's form and admits what the grant and the session
  allow. Whether the batch is the design you meant is this tool's arithmetic, and the preview is how you check it.
- **Cells and classes, nothing above them.** A room here is a statement that expands to cells. Once admitted there
  is no room, only cells. There are no objects, relations or constraints in the world.
- **Readings, not constraints.** "Reachable from the camera" is a flood over floor cells, computed by this tool.
  Nothing registers it and nothing holds it.
- **The top view is not the certified picture.** The kernel's frame is seen by opening the session in the window.
- **A starting session made by `new` comes from the live editor's mock** (`shell live-selftest`), with no key
  pressed. `open --session` starts from one saved in the window.
- **`undo` moves the project's pointer.** The session stepped back from stays on disk, sealed and unchanged.
- **Its checks are its own.** `python design/test_design.py` drives the tool against a real shell: twelve checks,
  each with its plant. It is not a row of the gate.
