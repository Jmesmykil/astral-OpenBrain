#!/usr/bin/env python3
"""Speak through Vox where the hub expects Piper.

The hub's _render_speech runs `PIPER --model <voice> --output_file <wav>` with the text on
stdin, then validates the wave frame by frame and publishes it atomically. This presents
that exact surface and renders through vox_core's word path instead, so swapping the voice
is a path change in live_hub.py and nothing else.

What it does NOT do is pretend. vox_say refuses any word outside its inventory, and this
refuses the whole utterance rather than speaking a partial one: half a sentence in a new
voice is worse than the failure the hub already knows how to handle. --model is accepted
and ignored, because the Vox voice is the lexicon, not a model file.

    echo "mahmee bahdee" | vox_piper_shim.py --model ignored --output_file out.wav
"""
import argparse, os, struct, subprocess, sys, tempfile, wave

RATE = 44100                      # what lex.say(word, 44100.0) renders at
GAP_MS = 60                       # silence between words, so the judge sees word edges


def render(word, vox_say, lexicon_dir):
    """One word as f32 samples, or None if this inventory cannot build it."""
    with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as t:
        raw = t.name
    try:
        env = dict(os.environ, VOX_LEXICON_DIR=lexicon_dir)
        r = subprocess.run([vox_say, word, raw], capture_output=True, text=True, env=env)
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
    for w in words:
        s = render(w.strip(".,!?;:").lower(), a.vox_say, a.lexicon)
        if s is None:
            missing.append(w)
            continue
        out.extend(s); out.extend(gap)
    if missing:
        # WHOLE utterance to Piper, never a mix. Vox's inventory is 1008 CVCV words, so most
        # real sentences contain at least one word it cannot build; refusing them was correct
        # while this was a demonstration and is useless as a voice. Per WORD would be worse
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
