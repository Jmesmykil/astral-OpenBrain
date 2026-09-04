# Astral for OpenHome: v2

**One line:** the DevKit answers most of what people ask it without the network, in
milliseconds, and asks permission before it uses anything that costs money.

v1 was an ability: a deterministic layer that caught "what time is it" before it became a
cloud round-trip. It was approved and merged into `dev` as PR #361 on 2026-08-31.

v2 is the rest of that idea, on the same hardware and the same platform, with no network.

---

## What it does now

**It answers 28 classes of question on the DevKit, and says how many, because the number
is computed from its own cost table for the host it is on.** The time, arithmetic, unit
conversions with both spellings, exact fractions checked against a proven kernel,
chemistry, physics, statistics, the moon, definitions with every sense, 682 written-down
facts across 20 fields, and 308,952 indexed passages from the books, encyclopedias and
documentation on its own SD card, searched in single-digit milliseconds.

**It was tested by asking it everything.** Three sweeps ran overnight: 2,534 spoken
phrasings across 115 capability areas, 13,408 library questions built from the index
itself, and 932 conversation sequences of 3,088 turns. Those runs found 568 silent
failures, a watermark being read aloud on 21,439 passages, two encyclopedia volumes
silently discarded, five confidently wrong answers, and a budget that had switched the whole
library off by a margin of 258 microseconds. All of that is fixed, each with a check that
holds it. What remains is written down in KNOWN-BUGS.md, with numbers.

**It knows what it cannot do, and says so.** Every refusal is a sentence with a reason:
"That needed the reader, and this machine doesn't have it." There is a test suite whose
only job is to prove nothing ever fails silently: it reads the reasons out of the source
and fails the build if any path can go quiet.

**It climbs a ladder, with consent at every rung.** The local rungs are live today; the LAN and cloud rungs are designed and switched off, because no measured class needs them yet. Mechanical here → a small model here →
a machine in the house over the LAN → a named cloud provider. Each rung is offered BY
NAME, "the Mac, or Claude?", because "the cloud" is not something a person can choose
between. Nothing leaves the device without a spoken yes. The cloud ships switched off, and
a provider with no key is never offered at all, because offering a route that cannot
answer turns a refusal into a broken promise.

**It holds a conversation.** After it answers, the floor stays open, with no wake word for the
follow-up, and it only takes sentences addressed to it, so a conversation happening
nearby is not answered. It takes notes in a meeting and reads them back. It quizzes you
from decks on the card. It flips coins, rolls dice, tells riddles, and knows what to say
when you tell it you are tired.

## What it costs, measured on the DevKit

| | |
|---|---|
| Wake word | vosk phrase recogniser, 2 phrases + everything-else; the room is never transcribed |
| Table answers, router end to end | the time 0.4 ms, arithmetic 1.4 ms, what-can-you-do 2.9 ms (median, DevKit) |
| 308,952 passages, 34 sources, 126 files | indexed in ~3 minutes; looked up in 1-58 ms |
| Mechanical comprehension (MECH) | 1.5 s, no model, no network |
| Spoken demo, 12 questions | 392 words, 2 min 28 s of speech at 159 words a minute; answers median 11 ms |
| The thinking tick | runs until the first word; cannot start after the answer chime (checked) |
| Checks passing | 3,630 on a Mac; 3,636 on the DevKit, all 26 suites, 2026-09-03 (KNOWN-BUGS.md has the per-suite record) |

## How it ships to you

Three files, MIT, exactly as your Local Ability docs describe: `devkit_functions.py`,
`requirements.txt`, `README.md`. The shim is 343 lines and readable: it finds the hub,
falls back to a compiled kernel, and if neither is present it says WHY rather than
failing quietly.

The engine itself ships the way any Python dependency does: a wheel named in
`requirements.txt`. That boundary is deliberate and documented in `BOUNDARY.md`. Nothing
proprietary is hidden inside the MIT file, and nothing in the MIT file needs the engine to
be readable to be reviewed.

## What I want

Three things, in order of what would help most:

1. **Tell me which conversation this is**: grant, sponsored integration, or a role. What
   is here is more than an ability, and it is built on your hardware and your platform.
2. **A paid integration.** A defined scope, milestone-based, to make this a supported path
   on the DevKit rather than one developer's card.
3. **Register the trigger words on agent 595324** so the ability can be installed the
   ordinary way, and tell me whether you want the wake phrase to stay "open home".

## Open, and honest about it

- The phone rung of the ladder is not finished. It is switched off, and never offered.
- The cloud rung needs one line in a key file before any provider is offered by name.
- Answers are in English. It HEARS about a hundred languages and says so; answering in
  another language would mean translating its own sentences with a 1B model that
  demonstrably invents, so it says which it is doing instead of guessing.
- Britannica is scanned text. Some passages carry OCR damage, and it reads what is there.

Everything above can be reproduced on the hardware in about ten minutes:
`deploy/install_v2.sh openhome@<address> --start`, then say **"open brain, run the demo"**,
and the loop runs it in its own voice. `python3 demo.py` on its own is the silent check of every
line; it leaves no timer, note or setting behind.
