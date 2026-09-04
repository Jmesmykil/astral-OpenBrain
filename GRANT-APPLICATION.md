# OpenHome Developer Grant — application draft

Fields 1–8 are yours (name, email, phone, referrer, location, GitHub, Discord, address).
Referrer: put Brady's name if he sent you the form. Fields 9–18 below are drafted from
SUBMISSION.md, DEMO.md and KNOWN-BUGS.md — every number in them was measured on the DevKit.
Edit the voice to yours; do not add claims that are not in those three files.

---

## 9. Project Title

Astral for OpenHome — a DevKit that answers without the network

## 10. Project Description

Astral is a local-first voice layer for the OpenHome DevKit. It answers most of what people
ask a kitchen speaker — the time, arithmetic, unit conversions, chemistry and physics,
definitions, 682 written-down facts, and questions against 308,952 indexed passages from
books, encyclopedias and documentation on the device's own SD card — in milliseconds, with
nothing sent anywhere. Wake word, speech-to-text, the reasoning, and the voice all run on the
Raspberry Pi 4.

Version 1 shipped as an OpenHome ability (merged into `dev` as PR #361 on 2026-08-31): a
deterministic layer that catches "what time is it" before it becomes a cloud round-trip.
Version 2 is the rest of that idea: a full local loop on the same hardware, with a ladder of
consent above it — mechanical here, a small model here, a machine in the house over the
LAN, then a named cloud provider — where nothing leaves the device without a spoken yes.
The goal of the grant is to make that a supported path on the DevKit rather than one
developer's card: hardened, documented, and installable the ordinary way.

## 11. Rationale

Voice assistants today send nearly every sentence to a data centre, even the ones a table
lookup could answer. That costs money per turn, fails without a network, and leaks the
household's speech. The DevKit is exactly the hardware to prove the alternative: a Pi 4 with
a microphone array and a speaker, and a platform that already lets a local ability take a
turn before the cloud does.

Related work: on-device wake words (openWakeWord, Porcupine) and on-device STT (whisper.cpp)
are mature; on-device answering is not. Home Assistant's local intents cover device control;
nobody covers "what do the books say about entropy" locally on a Pi. Astral's contributions:
a ranked router over deterministic tables, a 300k-passage full-text library on a card, a
consent ladder that offers each rung by name, and a product law — no silent failures — held
by a test suite that reads every refusal reason out of the source. It matters to OpenHome
directly: every turn answered locally is a turn that costs the platform nothing.

## 12. Methodology

Build: everything ships as MIT shim + a compiled kernel wheel, exactly as OpenHome's local
ability docs describe (BOUNDARY.md documents the line). The local loop deploys with one
script (`deploy/install_v2.sh`) and runs as a user service beside OpenHome's own.

Test: the product carries 3,587 checks in 26 suites, run against a scratch copy of the
device's state so a check can never touch the card. Beyond the suite, it is tested by asking
it everything: an adversarial pass with five auditors and independent reproduction found 57
defects in one day, 13 verified on the device and fixed the same day, each with a check that
holds it. Measurements — latencies, loudness at the device's own microphone, the demo's
length in words and seconds — are in the documents, with dates.

Milestones for the grant (see 16): a trained wake model from real recordings; the LAN and
cloud rungs offered by name with a class that genuinely needs them; the ability installable
from the OpenHome catalogue; and a second DevKit in a second household as the real test.

## 13. Experience

I built Astral alone on the DevKit over the last month, from the wake phrase to the
library indexer to the deploy script, and shipped v1 as an ability that OpenHome reviewed
and merged. I work with a local-first stack — whisper.cpp, piper, vosk, llama.cpp, SQLite
FTS5, Cython — and I measure before I claim: the documents in the repository carry the
numbers and the dates they were taken. I am confident in implementing this because most of
it already runs on the hardware today; the grant funds the hardening, the second device, and
the time.

## 14. Technologies Used

Raspberry Pi 4 (OpenHome DevKit) · vosk phrase recogniser for the wake word · whisper.cpp
(base.en, quantised) for speech-to-text · piper for the voice · llama.cpp with Llama 3.2 1B
Instruct for paraphrase and summary · a Cython-compiled deterministic kernel for the table
answers · SQLite FTS5 for the 308,952-passage library · PipeWire for audio · systemd user
services · Python 3.13. The OpenHome SDK and its local-ability contract for the platform
side.

## 15. Team

[Your name] — sole developer: architecture, kernel, router, library, audio, deploy, tests.
GitHub: [your URL]. (Add collaborators only if they will actually work on the grant.)

## 16. Elaborate on the details of your project

**Impact.** A DevKit that answers locally makes every household turn cheaper for OpenHome
and private for the person. The library on the card means a device with no network can
still answer what the encyclopedia says; the consent ladder means the cloud is a choice,
made by name, not a default.

**Motivation.** I wanted a speaker that would not go quiet when the network did, and would
not send my kitchen to a server to tell me the time.

**Ethics.** Nothing leaves the device without a spoken yes; the cloud ships switched off;
memory of the person is opt-in and erased with two words; note-taking only starts when
asked for and announces itself; the room is never transcribed for the wake word.

**What the money buys — milestones and use of funds (proposed, adjust to the award):**

| Milestone | What is delivered | Use of funds |
|---|---|---|
| 1. Wake word | a trained "open brain" model from real recordings, false-wake rate measured in a room with a television | recording sessions, compute for training, my time |
| 2. The ladder, live | a class that genuinely needs the LAN or a named cloud rung, offered and consented to by voice, measured end to end | LAN machine time, cloud credits for the named providers, my time |
| 3. Installable | the kernel wheel published, the ability installable from the OpenHome catalogue, trigger words registered | packaging, code review turnaround, my time |
| 4. A second household | a second DevKit running for a month in a home that is not mine, with its log read weekly | a DevKit and speaker, travel, my time |
| 5. Documentation and hand-over | the runbook, the bug ledger and the measurements kept current; code review feedback folded in | my time |

Most of the grant is time: this is one developer's work, and the hardware and credits are a
small part of the cost.

## 17. What is the project you are most proud of?

This one — specifically the day it was tested adversarially. Five auditors were sent to break
it and told to reproduce or kill every finding; 13 survived, and each was fixed the same day
with a check that will fail if it ever comes back. The device's own final speech file that
evening, transcribed by its own whisper, says: "that was twelve questions in three minutes
and fifty seconds, all of them answered here on this card with nothing sent anywhere."

## 18. Anything else we should know?

Everything claimed here can be reproduced on the hardware in about ten minutes with the
deploy script, and the demo runs by voice: "open brain, run the demo". The bug ledger,
KNOWN-BUGS.md, lists what is still open with numbers and dates, including what I could not
fix without a second person's voice. I have a call booked with Brady on 2026-09-04.
