# The self-tests' world

`plaza-night.art`, `tactical.design` and `tactical.layout` are the plaza's brief and its layout as they were committed
when the studio's self-tests were written (byte for byte the files of tree b1dedbf1). `art/director.py`'s
`selftest_tree(root)` lays them under a scratch root with the graybox's own maps and starts a ledger on them;
`python art/play.py --selftest`, `python art/studio.py selftest` (the studio's and the references' self-tests) and
`python art/studio_app.py selftest` play in that world.

They never read `art/briefs/`, `art/ledger/` or the maps as they stand in the checkout: those are the owner's world,
and his own admissions change them (his run of 2026-10-13 failed four of the studio's rows and stopped in the
references' self-test for that reason alone). A change to these files changes what the self-tests expect; make it
with the self-tests, never to follow the working brief.
