# Astral for OpenHome — v2

**One line:** the DevKit answers most of what people ask it without the network, in
milliseconds, and asks permission before it uses anything that costs money.

v1 was an ability: a deterministic layer that caught "what time is it" before it became a
cloud round-trip. It was approved and merged into `dev` as PR #361 on 2026-08-31.

v2 is the rest of that idea. Same hardware, same platform, no network.

---

## What it does now

**It answers 22 classes of question on the device.** The time, arithmetic, unit
conversions with both spellings, exact fractions checked against a proven kernel,
chemistry, physics, statistics, the moon, definitions with every sense, 682 written-down
facts across 20 fields, and 314,128 indexed passages from the books, encyclopedias and
documentation on its own SD card — searched in single-digit milliseconds.

**It knows what it cannot do, and says so.** Every refusal is a sentence with a reason:
*"That needed the reader, and this machine doesn't have it."* There is a test suite whose
only job is to prove nothing ever fails silently — it reads the reasons out of the source
and fails the build if any path can go quiet.

**It climbs a ladder, with consent at every rung.** Mechanical here → a small model here →
a machine in the house over the LAN → a named cloud provider. Each rung is offered *by
name* — "the Mac, or Claude?" — because "the cloud" is not something a person can choose
between. Nothing leaves the device without a spoken yes. The cloud ships switched off, and
a provider with no key is never offered at all, because offering a route that cannot
answer turns a refusal into a broken promise.

**It holds a conversation.** After it answers, the floor stays open — no wake word for the
follow-up — and it only takes sentences addressed to it, so a conversation happening
nearby is not answered. It takes notes in a meeting and reads them back. It quizzes you
from decks on the card. It flips coins, rolls dice, tells riddles, and knows what to say
when you tell it you are tired.

## What it costs, measured on the DevKit

| | |
|---|---|
| Wake word | vosk phrase recogniser, 2 phrases + everything-else; the room is never transcribed |
| Table answers | 40–1,400 µs |
| 314,128 passages | indexed in ~3 minutes; looked up in 1–58 ms |
| Mechanical comprehension (MECH) | 1.5 s, no model, no network |
| Whole demo, 53 questions | 7.6 s end to end, median 2 ms |
| Silence between the thinking tone and the answer | 0.00 s |
| Checks passing | 3,250 on a Mac, ~3,290 on the DevKit |

## How it ships to you

Three files, MIT, exactly as your Local Ability docs describe: `devkit_functions.py`,
`requirements.txt`, `README.md`. The shim is 343 lines and readable — it finds the hub,
falls back to a compiled kernel, and if neither is present it says *why* rather than
failing quietly.

The engine itself ships the way any Python dependency does: a wheel named in
`requirements.txt`. That boundary is deliberate and documented in `BOUNDARY.md`. Nothing
proprietary is hidden inside the MIT file, and nothing in the MIT file needs the engine to
be readable to be reviewed.

## What I want

Three things, in order of what would help most:

1. **Tell me which conversation this is** — grant, sponsored integration, or a role. What
   is here is more than an ability, and it is built on your hardware and your platform.
2. **A paid integration.** A defined scope, milestone-based, to make this a supported path
   on the DevKit rather than one developer's card.
3. **Register the trigger words on agent 595324** so the ability can be installed the
   ordinary way, and tell me whether you want the wake phrase to stay "open home".

## Open, and honest about it

- The phone rung of the ladder is not finished. It is switched off, and never offered.
- The cloud rung needs one line in a key file before any provider is offered by name.
- Answers are in English. It *hears* about a hundred languages and says so; answering in
  another language would mean translating its own sentences with a 1B model that
  demonstrably invents, so it says which it is doing instead of guessing.
- Britannica is scanned text. Some passages carry OCR damage, and it reads what is there.

Everything above can be reproduced on the hardware in about ten minutes:
`deploy/install_v2.sh openhome@<address> --start`, then `python3 demo.py --speak`.
