# design/ — the design surface (content time)

```
  a person · a script · a model
              │  a few lines of design text
              ▼
        design.py  propose      compiles the text to the net difference from the current world
              │    preview      the shell admits it into a scratch root; CURRENT and PROPOSED are shown
              │    admit        the same proposal bytes go to the shell again, for the project
              ▼
        shell admit (ADMIT-0)   the certified seam: recognizes, checks the grant, admits one ordinary edit
              ▼
        the session             the authority; a new sealed file each time, the old one never touched
              ▼
        the kernel              renders it:  shell live-window --resume <session.json>
```

This folder is **content time**. Nothing here is a row of the gate, and no gate runs when it is used. The gate
certified the shell, the session and the kernel; this tool only drives them. It holds no authority of its own:
every change to a world is made by `shell admit`, and what the shell refuses stays refused.

## The five verbs

| verb | what it does | what it changes |
|---|---|---|
| `inspect` | the project's identities, the session's head, the world from above, the tile classes, the grant, what can be proposed | nothing |
| `propose` | reads design text, compiles it against the current world, keeps it as the pending proposal | the pending proposal |
| `preview` | admits the pending proposal into a scratch root, shows CURRENT against PROPOSED, the changes and the readings | a scratch folder |
| `admit` | gives the previewed proposal bytes to the shell for the project's own sessions | the project's head moves to a new session |
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

This text is the tool's own. It is not a registered language of the tree. What reaches the shell is `VRDNP1`,
ADMIT-0's proposal language, one operation per proposal, written by this tool and by nothing else here.

## What is authority and what is a view

| | |
|---|---|
| authority | the session file the shell saved and verified. Its head is the world's identity |
| the verifier | `shell admit`: the grant, the anchor, the session's own validation of the edit |
| the grant | the admitter's, set with `grant` and passed on the shell's command line. A design text cannot carry or widen it. With no cells granted, every cell operation is refused |
| a view | everything this tool computes itself: the top view, the counts, what is reachable from the camera. For a reader. Where it disagrees with the shell, the shell is right |
| a prediction | the tool refuses an opened border, a changed stair and a closed camera cell before asking the shell. `propose --no-predict` sends them to the shell, which refuses them itself |
| a preview | state in a scratch folder. Not authority: the project's sessions and its head are as they were |

## Limits

- **One operation per run of the shell.** ADMIT-0 admits one operation per proposal and one proposal per run, and
  verifies the whole session each time. A design of 60 cells took about 20 s to preview and 20 s to admit on the
  build container, one run, and a single admission cost about fifteen times more on the 60-edit session than on the
  empty one. A proposal that carries a bounded list of operations is a change to the certified program, and so a
  rung with its own registration; it is not built.
- **Cells and classes, nothing above them.** A room here is a statement that expands to cells. Once admitted there
  is no room, only cells. There are no objects, relations or constraints in the world.
- **Readings, not constraints.** "Reachable from the camera" is a flood over floor cells, computed by this tool.
  Nothing registers it and nothing holds it.
- **The top view is not the certified picture.** The kernel's frame is seen by opening the session in the window.
- **A starting session made by `new` comes from the live editor's mock** (`shell live-selftest`), with no key
  pressed. `open --session` starts from one saved in the window.
- **`undo` moves the project's pointer.** The session stepped back from stays on disk, sealed and unchanged.
- **Its checks are its own.** `python design/test_design.py` drives the tool against a real shell: ten checks, each
  with its plant. It is not a row of the gate.
