#!/usr/bin/env python3
"""The human acceptance pass, guided and written down.

    deploy/acceptance.py                     the whole pass
    deploy/acceptance.py --only wake         one section
    deploy/acceptance.py --host openhome@<devkit>

WHY THIS EXISTS

Everything else about this device can be proved by a machine, and 5,106 checks do. What
cannot is whether a person in a room is heard, answered audibly, and able to interrupt.
That has been the last open requirement for weeks, and the reason it stayed open is that
doing it properly is tedious: you have to say a fixed thing, watch what the loop actually
did, and write down what you heard — and the third part is the one that gets skipped.

So this asks. It prints the sentence to say, watches the device's own log for what the loop
made of it, and then asks the one question the log cannot answer: what happened in the room.
Both halves go into a receipt. A log line without human ground truth is not proof of a
success or of a false wake, which is exactly the trap HW_TEST.md warns about.

WHAT IT WILL NOT DO

It does not touch the device beyond reading the log. It does not deploy, restart, retune or
play anything. Every trial counts, including the ones you fluff — a denominator that quietly
drops bad takes is how a device gets a reputation it has not earned.
"""
import argparse
import json
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

LOG = "~/astral-voice/astral-hub.log"
SSH = ["ssh", "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8"]

MARK = re.compile(r"\[(wake|burst|heard|route|said|spoken|floor[^\]]*|barge|ignored[^\]]*)\]")


class Watcher:
    """Everything the loop printed, with the moment it printed it."""

    def __init__(self, host, key):
        self.lines, self.stop = [], threading.Event()
        cmd = SSH + (["-i", key] if key else []) + [host, f"tail -n0 -F {LOG}"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            if self.stop.is_set():
                return
            self.lines.append((time.time(), line.rstrip("\n")))

    def since(self, when):
        return [l for t, l in self.lines if t >= when and MARK.search(l)]

    def close(self):
        self.stop.set()
        self.proc.terminate()


TRIALS = [
    ("wake", 'Say: "open brain"  — then WAIT. Do not ask anything.',
     "Did it chime or otherwise acknowledge you?",
     "R07 — it wakes for you when you use the phrase."),
    ("wake", 'Say: "open brain, what time is it"',
     "Did you hear a correct time, clearly?",
     "R07/R10 — wake plus a short answer, audible."),
    ("wake", 'Stay SILENT for twenty seconds. Say nothing at all.',
     "Did it stay quiet the whole time? (n = it woke or spoke on its own)",
     "R07 — it does not wake on an empty room."),
    ("room", 'Talk to someone, or to yourself, WITHOUT the wake phrase. About twenty seconds.',
     "Did it stay out of it? (n = it woke, answered or interrupted)",
     "R07 — it ignores room speech that was not addressed to it."),
    ("short", 'Say: "open brain, what is twenty percent of eighty"',
     "Did you hear 16, clearly?",
     "R08 — a short request, heard and answered."),
    ("follow", 'Say: "open brain, what time is it in tokyo"  then, WITHOUT the wake phrase, say: "and in london"',
     "Did it answer London too, without you saying the wake phrase again?",
     "R08 — a bare follow-up on the open floor."),
    ("long", 'Say, in ONE breath: "open brain, what do the books say about volcanoes and how islands form over a hotspot"',
     "Did it answer, and did the answer use the WHOLE question rather than trailing off?",
     "R08 — a long question keeps its ending (the whisper window fix)."),
    ("interrupt", 'Say: "open brain, tell me about volcanoes"  — then, while it is still talking, say "open brain" over the top of it.',
     "Did it stop talking promptly when you cut in?",
     "R09 — interruption works in the room, not just in a test."),
    ("audible", 'Say: "open brain, what is on the card"',
     "Was every word of that clearly audible from where you normally sit?",
     "R10 — audibility at your real listening position and volume."),
]


def ask(question):
    while True:
        got = input(f"    {question} [y/n/s=skip] ").strip().lower()
        if got in ("y", "n", "s"):
            return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="openhome@<devkit>")
    ap.add_argument("--key", default=str(Path.home() / ".ssh/id_ed25519"))
    ap.add_argument("--only", default=None, help="one section: wake room short follow long interrupt audible")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    trials = [t for t in TRIALS if args.only is None or t[0] == args.only]
    print(__doc__.strip().splitlines()[0])
    print(f"\n{len(trials)} trials, about a minute each. Every one counts, including the ones")
    print("you fluff — say so with n and it goes in the receipt as a miss.\n")
    print("Watching the device log. Ctrl-C stops and still writes what you have done.\n")

    watch = Watcher(args.host, args.key)
    time.sleep(1.5)
    done = []
    try:
        for i, (section, instruction, question, why) in enumerate(trials, 1):
            print(f"\n─── {i}/{len(trials)}  [{section}]  {why}")
            print(f"    {instruction}")
            # The window opens BEFORE you speak and closes when you say you are done. A
            # fixed lookback would drag the previous trial's wake and answer into this one,
            # and a receipt that attributes one trial's events to another is worse than no
            # receipt: it looks like evidence.
            started = time.time()
            input("    press ENTER when you have finished speaking… ")
            time.sleep(0.8)
            saw = watch.since(started)
            heard = [l for l in saw if "[heard]" in l or "[burst]" in l]
            spoke = [l for l in saw if "[said]" in l or "[spoken]" in l]
            print(f"    the loop recorded: {len(saw)} events, "
                  f"{len(heard)} capture(s), {len(spoke)} spoken")
            for l in saw[-4:]:
                print(f"      {l[:110]}")
            verdict = ask(question)
            done.append({"n": i, "section": section, "instruction": instruction,
                         "question": question, "requirement": why,
                         "human": {"y": "pass", "n": "fail", "s": "skipped"}[verdict],
                         "log": saw, "at": datetime.now(timezone.utc).isoformat()})
    except KeyboardInterrupt:
        print("\n  stopped early — writing what you did.")
    finally:
        watch.close()

    passed = sum(1 for d in done if d["human"] == "pass")
    failed = sum(1 for d in done if d["human"] == "fail")
    skipped = sum(1 for d in done if d["human"] == "skipped")
    where = Path(args.out or f"acceptance-{datetime.now().strftime('%Y%m%d-%H%M')}.json")
    where.write_text(json.dumps(
        {"at": datetime.now(timezone.utc).isoformat(), "host": args.host,
         "passed": passed, "failed": failed, "skipped": skipped,
         "attempted": len(done), "trials": done}, indent=1) + "\n", encoding="utf-8")

    print(f"\n{'═' * 60}")
    print(f"  {passed} held, {failed} failed, {skipped} skipped, of {len(done)} attempted")
    for d in done:
        mark = {"pass": "ok  ", "fail": "FAIL", "skipped": "skip"}[d["human"]]
        print(f"  {mark}  [{d['section']}] {d['requirement']}")
    print(f"{'═' * 60}")
    print(f"  receipt: {where}")
    if failed:
        print("  A failure here is worth more than a green suite. It is the only kind of")
        print("  evidence this product has never had.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
