#!/usr/bin/env python3
"""Speak through Vox where the hub expects Piper.

The hub's _render_speech runs `PIPER --model <voice> --output_file <wav>` with the text on
stdin, then validates the wave frame by frame and publishes it atomically. This presents
that exact surface and renders through vox_core's word path instead. Pointing live_hub.py
here is the whole mechanical change.

That is not the same as having swapped the voice, and this file should not be read as
saying it is. MEASURED, against the 2050 things this hub says and the 11038 words in them:
Vox can build 0 of those words and 0 of those utterances, so every turn goes to Piper
below. A letter-to-phone layer, which the lexicon spelling ah and ee makes tempting, would
take it to 6 of 11038 - the single word `data` - and leave whole utterances at zero. The
wall is not the size of the inventory and not how good the rendering is: it is that the
lexicon builds CVCV and nothing else. A CVCV voice with unlimited vowels and consonants
still tops out near 530 of 11038 words and 1 of 2050 utterances, because the ten commonest
things this hub says are 2514 of those 11038 tokens and not one of them is CVCV - `the` is
CCV, `a` and `i` are V, `and` is VCC, `to` is CV. What would move the number is syllable
shapes, V and CV and VC and CVC, before any further CVCV units.

What it does NOT do is pretend. vox_say refuses any word outside its inventory, and this
refuses the whole utterance rather than speaking a partial one: half a sentence in a new
voice is worse than the failure the hub already knows how to handle. --model is accepted
and ignored, because the Vox voice is the lexicon, not a model file.

    echo "mahmee bahdee" | vox_piper_shim.py --model ignored --output_file out.wav
"""
import argparse, os, struct, subprocess, sys, tempfile, wave

RATE = 44100                      # what lex.say(word, 44100.0) renders at
GAP_MS = 60                       # silence between words, so the judge sees word edges


class NoVox(Exception):
    """vox_say could not be run at all, which is not the same as a word it cannot say."""


def render(word, vox_say, lexicon_dir):
    """One word as f32 samples, or None if this inventory cannot build it.

    Raises NoVox when the binary itself is missing, unexecutable or hangs. That is a
    DIFFERENT fact from "not in the inventory" and the caller says so out loud, because
    telling somebody their words are unbuildable when really they never built Vox sends
    them to fix the wrong thing. Either way the utterance still goes to Piper: somebody
    who installs this ability without building Vox gets the voice they already had, not
    a stack trace in the middle of a turn.
    """
    with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as t:
        raw = t.name
    try:
        env = dict(os.environ, VOX_LEXICON_DIR=lexicon_dir)
        try:
            r = subprocess.run([vox_say, word, raw], capture_output=True, text=True,
                               env=env, timeout=20)
        except OSError as exc:                # not there, not executable, wrong arch
            raise NoVox(f"cannot run {vox_say}: {exc}") from exc
        except subprocess.TimeoutExpired:
            # A hang is not a word this inventory cannot build, but it must not hold the
            # turn open either. Twenty seconds is far beyond the 0.34 s a word takes on
            # the DevKit, so this only fires when something is actually wrong.
            raise NoVox(f"{vox_say} did not return within 20s on {word!r}")
        if r.returncode != 0:
            return None
        with open(raw, "rb") as f:
            b = f.read()
        if not b or len(b) % 4:
            return None
        return struct.unpack(f"<{len(b)//4}f", b)
    finally:
        try: os.unlink(raw)
        except OSError: pass


def piper_whole(words, missing, a):
    """The fallback voice, for an utterance Vox cannot say. Returns the shim's exit code.

    Piper is invoked exactly as live_hub does: text on stdin, --output_file, then the same
    frame-by-frame validation the hub will repeat, so a truncated wave fails here rather
    than in the turn. If Piper is absent or fails we publish NOTHING and exit non-zero,
    which is the behaviour the hub already knows how to handle; an empty wave would be a
    silent failure wearing a success.
    """
    piper = os.path.expanduser(os.environ.get("PIPER_BIN", "~/astral-voice/tts/piper/piper"))
    model = a.model or os.environ.get("PIPER_MODEL", "")
    if not os.path.exists(piper) or not (model and os.path.exists(model)):
        print(f"not buildable by Vox ({' '.join(missing)}) and no Piper to fall back to "
              f"(bin={piper} model={model or 'unset'})", file=sys.stderr)
        return 1
    tmp = a.output_file + ".piper"
    r = subprocess.run([piper, "--model", model, "--output_file", tmp],
                       input="\n".join(words), capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        try: os.unlink(tmp)
        except OSError: pass
        print(f"Piper exited {r.returncode}: {(r.stderr or '')[-200:]}", file=sys.stderr)
        return 1
    try:
        with wave.open(tmp, "rb") as w:
            n = w.getnframes()
            if n <= 0: raise ValueError("Piper produced an empty wave")
            rem = n * w.getnchannels() * w.getsampwidth()
            while rem:
                b = w.readframes(16384)
                if not b: raise ValueError("Piper produced a truncated wave")
                rem -= len(b)
            secs, rate = n / w.getframerate(), w.getframerate()
    except Exception as e:
        try: os.unlink(tmp)
        except OSError: pass
        print(f"Piper wave rejected: {e}", file=sys.stderr)
        return 1
    os.replace(tmp, a.output_file)
    print(f"{len(words)} words via PIPER ({' '.join(missing)} not in the Vox inventory), "
          f"{secs:.2f}s at {rate} Hz -> {a.output_file}")
    return 0


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--model", default=None)      # accepted, ignored: the lexicon is the voice
    ap.add_argument("--output_file", required=True)
    ap.add_argument("--vox-say", default=os.path.expanduser("~/private-bench/crate/target/release/vox_say"))
    ap.add_argument("--lexicon", default=os.path.expanduser("~/private-bench/m0"))
    a, _ = ap.parse_known_args()

    words = sys.stdin.read().split()
    if not words:
        print("no text on stdin", file=sys.stderr); return 2

    out, missing = [], []
    gap = [0.0] * int(RATE * GAP_MS / 1000)
    try:
        for w in words:
            s = render(w.strip(".,!?;:").lower(), a.vox_say, a.lexicon)
            if s is None:
                missing.append(w)
                continue
            out.extend(s); out.extend(gap)
    except NoVox as exc:
        print(f"Vox is not usable here ({exc}); the whole utterance goes to Piper",
              file=sys.stderr)
        return piper_whole(words, ["vox_say is not runnable"], a)
    if missing:
        # WHOLE utterance to Piper, never a mix. Vox's inventory is 1008 CVCV words, and on
        # this hub's own 2050 spoken strings that is EVERY one of them: not a single utterance
        # it says is buildable. Refusing them is correct while this is a demonstration and is
        # useless as a voice, and the arithmetic is in the module docstring. Per WORD is worse
        # than either: two different voices inside one sentence is a defect a listener hears
        # immediately, and the hub has no way to say "some of this is someone else".
        return piper_whole(words, missing, a)
    if not out:
        print("nothing rendered", file=sys.stderr); return 1

    peak = max(abs(v) for v in out) or 1.0
    scale = 0.89 / peak if peak > 0.89 else 1.0   # headroom, never clip on the way to s16
    pcm = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v * scale)) * 32767)) for v in out)

    tmp = a.output_file + ".partial"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(pcm)
    os.replace(tmp, a.output_file)                # publish whole or not at all
    print(f"{len(words)} words, {len(out)/RATE:.2f}s at {RATE} Hz -> {a.output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
