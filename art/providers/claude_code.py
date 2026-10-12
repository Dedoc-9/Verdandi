# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/claude_code.py — a provider for the director gateway (art/studio.py) that asks a Claude model through
# Claude Code's command-line tool in print mode (`claude -p`), on the login Claude Code already has. Standard library
# only. By the owner's ruling of 2026-10-11: "Both, CLI first"; "the CLI route is convenient for your personal
# development setup, but it is not a substitute for a properly authorized provider integration in a product offered
# to other users" (that is art/providers/anthropic_messages.py, with a Console key).
#
#   art/providers/claude_code.json   {"provider": "cli", "argv": ["{python}", "art/providers/claude_code.py"], ...}
#
# Its settings, in its environment (none is required):
#   VERDANDI_DIRECTOR_MODEL   the model, as `claude --model` takes it (an alias such as sonnet, or a full name);
#                             Claude Code's own default if not set
#   VERDANDI_CLAUDE           the claude executable, if `claude` on the PATH is not it. On Windows it must be
#                             claude.exe: a .cmd, .bat or .ps1 shim runs only under a shell, and nothing here uses one.
#                             (A .py file is run with this Python: the self-test's stand-in.)
#
# How claude is run, from an empty temporary folder (no project's settings near it), never through a shell:
#   -p INSTRUCTION                   a fixed instruction of this file's; the designer's words reach claude only on its
#                                    standard input, as director_prompt.py renders the request for every provider
#   --system-prompt-file FILE        director_prompt.py's system text (written to the temporary folder), in place of
#                                    Claude Code's own
#   --output-format stream-json --verbose
#                                    the session's first event (the model, the tools it offers) is read before anything
#                                    else; the last is the result
#   --json-schema SCHEMA             the gateway's response schema; the answer is the result's structured_output
#   --tools ""                       no built-in tool
#   --disallowedTools mcp__*         no tool of an MCP server: measured in the build container (Claude Code 2.1.296),
#                                    --tools "" left a connected server's 22 tools offered
#   --strict-mcp-config              no MCP server from any configuration file
#   --safe-mode                      no CLAUDE.md, skills, plugins or hooks; the login as usual
#   --no-session-persistence         no session saved
#   --permission-mode dontAsk        anything that would ask is denied
# The first event must offer no tool but StructuredOutput (the means by which claude holds its answer to the schema);
# if it offers any other, claude is stopped and nothing it says is used. The gateway then reads the answer again, whole,
# as it reads every provider's: the CLI's own enforcement of the schema is not relied on.
#
# The response names the model the session reported and the tokens and cost the result reported. The cost is Claude
# Code's own client-side estimate; what is billed, or counted against a plan's limits, depends on how Claude Code is
# logged in, which this file does not read. Nothing here reads, prints or records a credential.

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading

import director_prompt   # beside this file: the system text and the request as the model reads it

INSTRUCTION = ("The director's request is on standard input. Answer it only through the structured output, "
               "with at most the number of candidates it allows.")
ALLOWED_TOOLS = {"StructuredOutput"}


class Fail(Exception):
    pass


def executable():
    """The argv prefix that runs claude, or Fail."""
    exe = os.environ.get("VERDANDI_CLAUDE", "")
    if exe:
        if not os.path.isfile(exe):
            raise Fail("VERDANDI_CLAUDE names %s, which is not a file" % exe)
    else:
        exe = shutil.which("claude") or ""
        native = os.path.join(os.path.expanduser("~"), ".local", "bin", "claude.exe")
        if (not exe or exe.lower().endswith((".cmd", ".bat", ".ps1"))) and os.name == "nt" and os.path.isfile(native):
            exe = native             # where Claude Code's native installer puts it: found without VERDANDI_CLAUDE (a desktop icon has no shell's variables)
        if not exe:
            raise Fail("claude is not on the PATH: install Claude Code, or set VERDANDI_CLAUDE to its executable")
    low = exe.lower()
    if low.endswith(".py"):
        return [sys.executable, exe]
    if low.endswith((".cmd", ".bat", ".ps1")):
        raise Fail("claude resolves to %s, a script only a shell runs; set VERDANDI_CLAUDE to claude.exe "
                   "(Claude Code's native install puts it in %%USERPROFILE%%\\.local\\bin)" % exe)
    return [exe]


def argv(schema, system_file):
    a = ["-p", INSTRUCTION, "--system-prompt-file", system_file, "--output-format", "stream-json", "--verbose",
         "--json-schema", json.dumps(schema, sort_keys=True, separators=(",", ":")),
         "--tools", "", "--disallowedTools", "mcp__*", "--strict-mcp-config", "--safe-mode",
         "--no-session-persistence", "--permission-mode", "dontAsk"]
    model = os.environ.get("VERDANDI_DIRECTOR_MODEL", "")
    return a + (["--model", model] if model else [])


def ask(req):
    """(model, candidates, usage) from claude, or Fail."""
    head = executable()
    work = tempfile.mkdtemp(prefix="verdandi-claude-")
    try:
        system_file = os.path.join(work, "system.txt")
        with open(system_file, "w", encoding="utf-8") as fh:
            fh.write(director_prompt.SYSTEM)
        cmd = head + argv(req["respond"]["schema"], system_file)
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work)
        except OSError as e:
            raise Fail("claude cannot be started: %s" % e)
        err = bytearray()

        def read_err():
            while True:
                b = p.stderr.read(4096)
                if not b:
                    return
                err.extend(b)
                del err[:-4096]

        def write_in():
            try:
                p.stdin.write(director_prompt.user_text(req).encode("utf-8"))
                p.stdin.close()
            except OSError:
                pass

        for f in (read_err, write_in):
            threading.Thread(target=f, daemon=True).start()
        init, result = None, None
        for raw in p.stdout:
            try:
                ev = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                continue
            if not isinstance(ev, dict):
                continue
            if ev.get("type") == "system" and ev.get("subtype") == "init" and init is None:
                init = ev
                tools = ev.get("tools") if isinstance(ev.get("tools"), list) else ["(the tools were not listed)"]
                extra = sorted(str(t) for t in tools if t not in ALLOWED_TOOLS)
                if extra:
                    p.kill()
                    p.wait()
                    raise Fail("claude offered tools beyond its structured output (%s%s); it was stopped and nothing it "
                               "said is used" % (", ".join(extra[:6]), ", ..." if len(extra) > 6 else ""))
            elif ev.get("type") == "result":
                result = ev
        rc = p.wait()
        tail = bytes(err).decode("utf-8", "replace").strip().splitlines()[-1:]
        if init is None:
            raise Fail("claude (exit %d) began no session%s" % (rc, ": " + tail[0][:200] if tail else ""))
        if result is None:
            raise Fail("claude (exit %d) gave no result%s" % (rc, ": " + tail[0][:200] if tail else ""))
        if result.get("is_error") or result.get("subtype") != "success":
            text = " ".join(str(result.get("result") or "").split())[:200]
            raise Fail("claude's result is %s%s" % (result.get("subtype") or "an error", ": " + text if text else ""))
        so = result.get("structured_output")
        if not isinstance(so, dict) or not isinstance(so.get("candidates"), list):
            raise Fail("claude's result holds no structured output with candidates")
        u = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        n = lambda k: u.get(k) if type(u.get(k)) is int and u.get(k) >= 0 else 0
        cost = result.get("total_cost_usd")
        usage = {"input_tokens": n("input_tokens") + n("cache_creation_input_tokens") + n("cache_read_input_tokens"),
                 "output_tokens": n("output_tokens"),
                 "cost_usd": float(cost) if type(cost) in (int, float) and cost >= 0 else None,
                 "cost_basis": "Claude Code's own client-side estimate"}
        model = init.get("model") if isinstance(init.get("model"), str) and init.get("model") else "claude (model not reported)"
        return model, so["candidates"], usage
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    try:
        req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        model, cands, usage = ask(req)
    except Fail as e:
        sys.stderr.write("claude_code: %s\n" % e)
        return 2
    except (ValueError, KeyError, TypeError) as e:
        sys.stderr.write("claude_code: the request cannot be read: %s\n" % e)
        return 2
    out = {"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": req["id"],
           "provider": {"name": "claude-code", "model": model, "usage": usage}, "candidates": cands}
    sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
