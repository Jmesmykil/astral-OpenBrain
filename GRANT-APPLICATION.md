# OpenHome Developer Grant: application answers

Fields 1 to 8 are yours (name, email, phone, referrer, location, GitHub, Discord, address).
Fields 9 to 18 below were audited on 2026-09-04 against the form's own prompts, the grant
announcement, and the five milestone stages OpenHome lists; see GRANT-AUDIT.md. Every number
was measured on the DevKit or the Mac on the date given.

---

## 9. Project Title

Astral for OpenHome: a voice assistant that answers on the device, with nothing sent anywhere

## 10. Project Description

Astral is a local voice assistant for the OpenHome DevKit. You say "open brain" and ask, and it answers from the device itself: the time and date, arithmetic and unit conversions, definitions, chemistry and physics, 682 curated facts, timers and reminders, notes, and questions against a full-text library of 397,706 passages indexed from books and reference works on the SD card. Answers arrive in milliseconds. It holds a conversation across turns without repeating the wake word, it asks before anything leaves the house, and when it cannot answer it says why instead of going quiet. The wake word, speech recognition, reasoning and voice all run on the Raspberry Pi 4 inside the DevKit, so the speaker keeps working when the network does not.

Version 1 shipped as an OpenHome ability and was merged into OpenHome's dev branch as PR #361 on 2026-08-31. It answers exact questions before they become a cloud round trip. Version 2, running on the DevKit today, is the full local loop with a consent ladder above it: deterministic answers first, then a small model on the Pi, then a machine in the house over the LAN, then a named cloud provider, and no step up without a spoken yes. The grant would turn this from one developer's card into a supported path on the DevKit: hardened, documented, installable from the OpenHome catalogue, and measured in homes other than mine.

## 11. Rationale

Related work. Cloud assistants send nearly every utterance to a data centre, including the ones a table lookup could answer. That costs money per turn, fails without a network, and exposes household speech. Home Assistant's Assist covers local device control with fixed intents. Open Voice OS, the successor to Mycroft, and Rhasspy run skills locally on a Raspberry Pi and are the closest relatives of this project. On-device wake words (openWakeWord, Porcupine) and on-device speech recognition (whisper.cpp) are mature. Offline reference readers exist (Kiwix) but are not voice-first. None of these answer open questions from a large full-text library on the device itself, hold a conversation locally, and make every escalation to a bigger machine or a cloud provider a spoken, named consent.

Where Astral fits and what is new. Astral is an OpenHome ability plus a local loop that takes the turn before the cloud does, which the OpenHome platform already allows. It contributes four things. A ranked router over deterministic tables (time, math, money, units, definitions, facts) that answers in milliseconds with no model call. A full-text library of 397,706 passages on an SD card, searched with SQLite FTS5 in under a second. A consent ladder that offers each rung by name and moves only on a spoken yes. And a product rule against silent failures, held by a test suite that reads every refusal reason out of the source, so the device always says why it did not answer.

Relevance and impact. For OpenHome, every turn answered locally is a turn that costs the platform nothing and works offline, and the consent ladder is a model for how a voice device should handle escalation to the cloud. For the field, the project is evidence that a useful assistant can be built with no model in the path for most of what people ask, and that a Raspberry Pi can carry an encyclopedia.

## 12. Methodology

Build. Everything that runs inside OpenHome's runtime is MIT and readable: the ability (main.py, devkit_functions.py, background.py) and the deploy scripts, in the public repository at https://github.com/Jmesmykil/astral-OpenBrain. The engine ships as a compiled Python wheel named in requirements.txt, the way OpenHome's local ability documentation describes, and the seam between the two is one documented function (community/astral/BOUNDARY.md). The local loop installs with one script and runs as a user service beside OpenHome's own, and the device stays fully usable from the OpenHome app.

Test. The product carries 3,868 automated checks in 27 suites, run on my Mac and on the DevKit itself against a scratch copy of the device's state, so no check can touch the card. Every new check is proved to fail before its fix goes in. Beyond the suite I test by asking the device everything: one adversarial review found 57 candidate defects, of which 24 were verified and 13 reproduced on the device and fixed the same day, each with a check that holds it. Latency, loudness at the device's own microphone and the demo's length are measured and dated in the repository, and a bug ledger (KNOWN-BUGS.md) lists what is still open.

Plan against OpenHome's milestones. Dev Kit tier: I have a DevKit and ship on it. Community development: the repository is public, I am active in the Discord, and I will post an update at each milestone. Completed demo: the demo runs by voice today ("open brain, run the demo"), and a transcript with timings is in the repository. Live integration: version 1 is merged (PR #361), and version 2 will go through the same review. Critical selected feature: local-first answering with the consent ladder, proposed under question 16 with a six-month timeline.

## 13. Experience

Relevant experience. I built Astral alone on the DevKit over the past month, from the wake phrase to the library indexer to the deploy script, and shipped version 1 as an ability that OpenHome reviewed and merged. Before that I wrote openhome-cli, a public TypeScript command line tool that deploys, validates and scaffolds OpenHome abilities, and I maintain a public repository of open-source abilities for OpenHome agents. This is my third OpenHome project, and the first two are in use.

The engines underneath are mine as well. The Astral Brain Engine is a model-agnostic orchestration layer with a delegation hierarchy, persistent memory, budgets and a task board (607 commits), and it coordinated the work on this project. Astral MECH, in the Strata repository, is a language comprehension engine written in Julia with Ada SPARK proofs and Rust lanes: no model weights, a typed role graph for every sentence, memory that keeps its sources, byte-identical output for the same input, and an honest refusal when it cannot read something (436 commits). Slate, its mathematics lane, runs on the DevKit today as the kernel service. I also do systems work on constrained hardware: Q OS, a windowed desktop for the Nintendo Switch (in development, repository public), a hardware-in-the-loop firmware workbench, and a Game Boy emulator.

Confidence. High, because most of the proposal already runs on the hardware: the local loop, the library, the router and the test suite are in place, and the remaining work is hardening, packaging, measurement in other homes, and the comprehension tier. The risks I see are the quality of the comprehension tier on a one-billion-parameter model, which milestone 5 addresses, and my own time as a student, which the budget addresses. I work independently, and I measure before I claim.

## 14. Technologies Used

Raspberry Pi 4 (OpenHome DevKit) with its microphone array and speaker. The vosk phrase recogniser for the wake phrase. whisper.cpp (base.en, quantised) for speech recognition. piper for the voice. llama.cpp with Llama 3.2 1B Instruct for paraphrase and summary. A Cython-compiled deterministic kernel for the table answers and a Julia mathematics kernel as a service. SQLite FTS5 for the library. PipeWire for audio, systemd user services, Python 3.13. On the platform side, the OpenHome SDK and its local-ability contract, with the OpenHome app for volume and pairing. AWS credits, if awarded, would fund the training and evaluation runs in milestone 5.

## 15. Team

Jamesmykil Weber, sole developer: architecture, kernel, router, library, audio, deployment and tests. Author of openhome-cli and the OpenHome abilities repository. Version 1 of Astral merged into OpenHome as PR #361. Independent developer and student, Oahu, Hawaii. GitHub: https://github.com/Jmesmykil

## 16. Elaborate on the details of your project

Expected impact. A DevKit that answers locally makes every household turn cheaper for OpenHome and private for the person, and it keeps working without a network. The library on the card means a device can answer what an encyclopedia says with no connection at all. The consent ladder is a reusable pattern for the field: escalation to a bigger machine or a cloud provider becomes a choice made by name, out loud. In settings where speech should not leave the room, such as clinics, classrooms and homes with children, a local-first device is the difference between usable and not.

Why I am excited. I wanted a speaker that would not go quiet when the network did and would not send my kitchen to a server to tell me the time. It works now on a Pi, it is a pleasure to use, and I want other people to have it: ask a follow-up without the wake word, ask for a riddle or a quiz, have it read a page from a book on the card, and hear it say why when it cannot help.

Ethics and security. Nothing leaves the device without a spoken yes, and cloud routes ship switched off. The wake word is a constrained phrase recogniser that never transcribes the room. Memory of the person is opt-in and erased with two words. Note-taking starts only on request and announces itself. The device says when it does not know rather than guessing, and every refusal reason is tested. The library indexes the owner's own books on the owner's card. What ships is the indexer and an openly licensed starter shelf, never anyone's copyrighted volumes. The ability that runs inside OpenHome is MIT and reviewable, and the seam to the compiled engine is documented.

Milestones and timeline, six months from award.
1. Month 1. The mechanical assistant finished and installable from the OpenHome catalogue: every exact-answer class complete, the suite kept at zero failures, the kernel wheel published, the runbook and bug ledger current. This is the live integration milestone.
2. Months 2 to 3. The consent ladder live end to end, with a machine in the house as the LAN rung and named cloud providers as the last rung, each consented to by voice and measured.
3. Months 2 to 3. The reference shelf at full size, openly licensed, with the index built on a real machine and shipped built, so any device answers from an encyclopedia offline in under a second.
4. Months 4 to 5. Measured in two homes that are not mine for a month each, with false wakes, loudness and every failure read from the logs and fixed, and a project update in the Discord at each milestone.
5. Months 4 to 6. The comprehension tier: my own inference and transformer work applied to the one tier that still uses a stock model, trained and evaluated on the machine, so the device holds a conversation the way it holds a fact. This is the critical selected feature.

Budget. The one thing I cannot buy on my own timeline is a machine that can hold a training run and serve as the in-house rung. Today the training lane is a 16 GB Mac mini and a 6 GB RTX 2060.

Proposed use of funds at $50,000:
- Workstation with 128 GB of unified memory (Minisforum MS-S1 MAX, $3,799 on the maker's store today and $4,749 at list, or a Mac Studio at the same level). It holds a 70-billion-parameter model quantised, builds the library index in minutes instead of hours, and serves as the in-house rung: $4,749
- Two more DevKits with speakers and microphones for the home measurements, and travel: $1,100
- Frontier model access and evaluation compute beyond AWS credits: $1,500
- Part-time help with packaging and review, so milestone 1 lands in weeks rather than months: $6,000
- Developer time, six months: $32,000
- Contingency: $4,651

At $10,000: the workstation at $3,799, test hardware $600, evaluation $600 and $5,001 of developer time, which delivers milestones 1 to 3 in full. At a smaller award: one more DevKit and test hardware, and milestone 1 on my own time.

## 17. What is the project you are most proud of?

The harness and the engines under it, because this device is the first piece of that work to ship through someone else's review. The Astral Brain Engine is the orchestration layer I run everything through: model-agnostic, with a delegation hierarchy, persistent memory, budgets and a coordination bus, and it carried this project from the wake word to the merged pull request. Under it sit two engines written in languages I chose for proof rather than convenience. Astral MECH, in the Strata repository, is a language comprehension engine in Julia with Ada SPARK proofs and Rust lanes: no model weights, no sampling, a typed role graph for every sentence, memory that keeps its sources, and an honest refusal when it cannot read something. Slate is its mathematics lane, and it is the kernel service answering arithmetic on the DevKit today.

Links. This project: https://github.com/Jmesmykil/astral-OpenBrain, with the handout and demo transcript at https://github.com/Jmesmykil/astral-OpenBrain/tree/main/handout. openhome-cli: https://github.com/Jmesmykil/openhome-cli. Open-source abilities for OpenHome: https://github.com/Jmesmykil/abilities. Q OS (in development): https://github.com/Jmesmykil/QNX. The Astral Brain Engine, Strata and Slate are private and available on request.

## 18. Anything else we should know?

How I heard about the program. From Brady at OpenHome. I am in the OpenHome Discord and in touch with the developer relations team there, and I gave Brady a thirty-minute demo on 2026-09-04.

Affiliation. Independent developer and student. No organisation or company is behind the project.

Previous projects in AI and related fields. The Astral Brain Engine (orchestration), Astral MECH and Slate (language comprehension and mathematics engines), all private and available on request. openhome-cli and the OpenHome abilities repository, both public and in use.

Presentations and publications. The demo call with OpenHome on 2026-09-04. The handout with the demo timeline and measurements is in the repository (handout/OpenBrain-Handout.pdf). No publications yet.

References. None claimed. Brady at OpenHome has seen the working demo.

Reproducibility. Everything claimed here can be reproduced on the hardware in about ten minutes with the deploy script, and the demo runs by voice. Everything so far was built on hardware I already own, about $10,000 of it out of pocket over the last three years. Contact: mykiljames253@gmail.com, +1 253 392 9204.
