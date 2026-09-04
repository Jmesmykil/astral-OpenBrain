# OpenHome Developer Grant: application answers

Fields 1 to 8 are yours (name, email, phone, referrer, location, GitHub, Discord, address).
Referrer: put Brady's name if he sent you the form. Fields 9 to 18 below are drafted from
SUBMISSION.md, DEMO.md and KNOWN-BUGS.md, and every number in them was measured on the DevKit.

---

## 9. Project Title

Astral for OpenHome: a DevKit that answers without the network

## 10. Project Description

Astral is a local voice layer for the OpenHome DevKit. It answers most of what people ask a kitchen speaker right on the device. The time, arithmetic, unit conversions, chemistry and physics, definitions, 682 written-down facts, and questions against 397,706 indexed passages from the books and encyclopedias on the SD card. Answers come back in milliseconds and nothing is sent anywhere. The wake word, the speech-to-text, the reasoning and the voice all run on the Raspberry Pi 4.

Version 1 shipped as an OpenHome ability and was merged into dev as PR #361 on 2026-08-31. It catches "what time is it" before it becomes a cloud round trip. Version 2 is the rest of that idea: a full local loop on the same hardware with a ladder of consent above it. Mechanical answers come first. Then a small model on the Pi, then a machine in the house over the LAN, then a named cloud provider, and nothing leaves the device without a spoken yes. I want the grant to turn this from one developer's card into a supported path on the DevKit: hardened, documented and installable the ordinary way.

## 11. Rationale

Voice assistants today send nearly every sentence to a data centre, including the ones a table lookup could answer. That costs money per turn, it fails without a network, and it leaks the household's speech. The DevKit is the right hardware to prove the alternative. It has a microphone array and a speaker on a Pi 4, and the platform already lets a local ability take a turn before the cloud does.

Related work: on-device wake words (openWakeWord, Porcupine) and on-device speech-to-text (whisper.cpp) are mature. On-device answering is not. Home Assistant's local intents cover device control, and nobody covers "what do the books say about entropy" locally on a Pi. Astral contributes a ranked router over deterministic tables and a 400k-passage full-text library on a card. It adds a consent ladder that offers each rung by name, and a product rule against silent failures that a test suite holds by reading every refusal reason out of the source. For OpenHome the value is direct. Every turn answered locally is a turn that costs the platform nothing.

## 12. Methodology

Build: everything ships as an MIT shim plus a compiled kernel wheel, the way OpenHome's local ability docs describe it, and BOUNDARY.md documents the line. The local loop deploys with one script (deploy/install_v2.sh) and runs as a user service beside OpenHome's own.

Test: the product carries 3,630 checks in 26 suites on my Mac and 3,636 on the DevKit. They run against a scratch copy of the device's state, so a check can never touch the card. Every new check is proved to fail before its fix goes in. Beyond the suite I test it by asking it everything. One adversarial review day found 57 defects. I verified 24, reproduced 13 on the device, and fixed those the same day, each with a check that holds it. Latencies, loudness at the device's own microphone and the demo's length in words and seconds are in the documents with the dates they were taken.

Milestones for the grant (details under question 16): the mechanical assistant finished and installable from the OpenHome catalogue. The consent ladder live with a machine in the house and named cloud providers. The reference library at full size with its index built on a real machine and shipped built. The device measured in other people's homes. And the model work that makes the comprehension tier good enough to trust.

## 13. Experience

I built Astral alone on the DevKit over the last month, from the wake phrase to the library indexer to the deploy script, and I shipped v1 as an ability that OpenHome reviewed and merged. Before that I wrote openhome-cli, a public TypeScript command line tool that deploys, validates and scaffolds OpenHome abilities, and I keep a public repository of open-source abilities for OpenHome agents. So this is my third OpenHome project and the first two are in use.

The rest of my work is the same idea at a larger scale, and most of it is further along than this device. The Astral Brain Engine is my harness. It's a model-agnostic orchestration layer with a delegation hierarchy, persistent memory, budgets and a task board, at 607 commits, and it routed the work on this project. Strata is Astral MECH, a language comprehension engine I wrote in Julia with Ada SPARK proofs and Rust lanes. No model weights and no sampling. It reads a sentence into a typed role graph, keeps what you tell it with the source attached, gives byte-identical output for the same input, and says so when it can't read something. It's at 436 commits and ships as a signed macOS app. Slate is its math lane and it runs on the DevKit today as the kernel service.

Around the engine sits an ecosystem I built. Q OS is a windowed desktop for the Nintendo Switch that replaces the home menu, and it's verified on hardware and public. Void IDE is a native macOS editor in Swift and Void CLI is a Rust terminal, and both speak to the engine. Astral Workspace and the Swift packages under it. The ASCII glyph-grid render kernel, with hosts for Unity 6, Blender and Tessera, which turns 3D models into sprite sheets with no image model in the path. sCAN, a crypto research desktop with a Rust gateway and PostgreSQL, at 179 commits. SlimeShot, a Unity game that's close to done, and MoBA, a server-authoritative online game that's close to mechanically done at 579 commits. soloDOLO, an animated series in production. SourceBound, a 2D RPG that teaches coding. Filament, a hardware-in-the-loop firmware workbench. EMULive, a living Game Boy emulator. The pattern across all of it is local first, with the cloud as a choice and never the default.

My stack for this project is whisper.cpp, piper, vosk, llama.cpp, SQLite FTS5 and Cython, and I measure before I claim. I'm confident in delivering because most of it already runs on the hardware today. The grant funds the machine, the test hardware, the compute and the time.

## 14. Technologies Used

Raspberry Pi 4 (OpenHome DevKit). The vosk phrase recogniser for the wake word. whisper.cpp base.en, quantised, for speech-to-text. piper for the voice. llama.cpp with Llama 3.2 1B Instruct for paraphrase and summary. A Cython-compiled deterministic kernel for the table answers and a Julia math kernel as a service. SQLite FTS5 for the 397,706-passage library. PipeWire for audio, systemd user services, Python 3.13. On the platform side, the OpenHome SDK and its local-ability contract.

## 15. Team

Jamesmykil Weber, sole developer: architecture, kernel, router, library, audio, deploy, tests. GitHub: https://github.com/Jmesmykil

## 16. Elaborate on the details of your project

Expected impact. A DevKit that answers locally makes every household turn cheaper for OpenHome and private for the person. The library on the card means a device with no network can still answer what the encyclopedia says. The consent ladder means the cloud is a choice made by name.

Why I'm excited. I wanted a speaker that wouldn't go quiet when the network did, and wouldn't send my kitchen to a server to tell me the time. It works now, on a Pi, and I want other people to have it.

Ethics. Nothing leaves the device without a spoken yes. The cloud ships switched off. Memory of the person is opt-in and erased with two words. Note-taking only starts when asked for, and it announces itself. The room is never transcribed for the wake word.

What the money buys. The advancement here is a mechanical assistant. It answers most of a household's questions on its own hardware, in milliseconds, with no model call and nothing sent anywhere, and it says so when it can't. That's what I have running today, and each level below buys more of it.

Milestones, with what each delivers and what it costs:
1. The mechanical assistant, finished. Every exact-answer class complete (time, date, math, money, units, definitions, facts, the library, timers, notes, memory), the no-silent-failure suite kept at zero failures, the kernel wheel published, the ability installable from the OpenHome catalogue, the runbook and the bug ledger current. Cost: my time.
2. The ladder, live. A machine in the house as the LAN rung and named cloud providers as the last rung, each offered by name and consented to by voice, measured end to end. Cost: the machine below, provider credits, my time.
3. The library at full size. The rest of the encyclopedias I own on the card (65 DK volumes went on today, 397,706 passages indexed), with the index built on a real machine and shipped built, so an offline device answers from an encyclopedia in under a second. Cost: the machine below, my time.
4. Measured in other homes. Two more DevKits in homes that aren't mine for a month each, with false wakes, loudness and every failure read from the logs and fixed. Cost: two DevKits, speakers and microphones for testing, travel, my time.
5. The comprehension tier. My own inference and transformer work applied to the one tier that still uses a stock model, trained and evaluated on the machine, so the device can hold a conversation the way it holds a fact. Cost: training compute, frontier model access for evaluation, my time.

Hardware, by level. I'm upfront about my limits because they're the reason I'm asking. Today the training lane is a 16 GB Mac mini and a 6 GB RTX 2060 that can't hold a training run. There are levels, and each one buys real speed. At $2,000 to $5,000, a GPU with real memory plus RAM for my second machine. That alone moves training and the library index off the mini and onto a card that can hold them. At $3,800 to $4,750, a Minisforum MS-S1 MAX with 128 GB of unified memory (AMD Ryzen AI Max+ 395, Radeon 8060S graphics, 2 TB SSD, dual 10 GbE), $3,799 on the maker's store today and $4,749 at list, or a Mac Studio at the same level. 128 GB the GPU can use holds a 70-billion-parameter model quantised, so I can train and run the comprehension tier at home. The same machine builds the library index in minutes instead of hours on the Pi and serves as the LAN rung. The full build is a board with two full-lane PCIe slots, two cards at 32 to 48 GB of VRAM each, and the RAM to match. That's the machine that trains the comprehension tier and serves the LAN rung at once. I'm a student with no income, so hardware is the one thing I can't buy on my own timeline, and it's the single purchase that changes what I can do.

What each level delivers:
$50,000: all five milestones, the machine, the hardware for testing, the training compute and frontier model access for milestone 5, and part-time help with packaging and review so milestone 1 lands in weeks rather than months.
$10,000: milestones 1, 2 and 3 in full and the machine. A fully mechanical assistant, installable, with the ladder live and the library at full size.
$2,000 to $5,000: a GPU and RAM for my second machine, or the MS-S1 MAX at $3,799, and with it milestones 1 and 3.
$500 to $2,000: one more DevKit and test hardware, and milestone 1 on my own time.
Nothing: I keep building it on the Pi, out of pocket and slower, with no second device and no machine.

## 17. What is the project you are most proud of?

The harness and the engines under it. The Astral Brain Engine is the orchestration layer I run everything through. It's model-agnostic, with a delegation hierarchy, persistent memory, budgets and a coordination bus, and it carried this project from the wake word to the merged pull request. Under it sit two engines I wrote in languages I chose for proof, not convenience. Astral MECH, in the Strata repository, is a language comprehension engine in Julia with Ada SPARK proofs and Rust lanes. No model weights, no sampling. A typed role graph for every sentence, memory that keeps its sources, and an honest refusal when it can't read something. Slate is its mathematics lane, and it's the kernel service answering arithmetic on the DevKit today.

Around them is an ecosystem of applications. Q OS, a windowed desktop for the Nintendo Switch verified on hardware. Void IDE and Void CLI. Astral Workspace. The ASCII render kernel and its Unity and Blender hosts. sCAN. Two games, SlimeShot close to done and MoBA close to mechanically done. And soloDOLO, an animated series. This device is the small end of that work, and it's the first piece of it to ship through someone else's review.

Public work you can open now: https://github.com/Jmesmykil/astral-OpenBrain (this project), https://github.com/Jmesmykil/openhome-cli, https://github.com/Jmesmykil/abilities, https://github.com/Jmesmykil/QNX (Q OS). The rest is private and available on request.

## 18. Anything else we should know?

Everything claimed here can be reproduced on the hardware in about ten minutes with the deploy script, and the demo runs by voice: "open brain, run the demo". The bug ledger, KNOWN-BUGS.md, lists what is still open with numbers and dates. I heard about the program from Brady at OpenHome. I'm in the OpenHome Discord and in touch with your developer relations team there, and I spoke with Brady on 2026-09-04. You can reach me at mykiljames253@gmail.com or +1 253 392 9204.

Affiliation: independent developer and student, no institution. Everything so far was built on hardware I already owned: a 16 GB M4 Mac mini, a second Linux box with 23 GB of RAM, an RTX 2060 with 6 GB, an RX 580, and the DevKit. I've spent about $10,000 on this work over the last one to three years, all out of pocket. Previous projects: openhome-cli and the abilities repository, both public and in use with OpenHome. Q OS, public. The Astral Brain Engine, Strata (Astral MECH), Slate, Void IDE, Void CLI, Astral Workspace, the ASCII kernel and its hosts, Tessera, sCAN, SlimeShot, MoBA, soloDOLO, SourceBound, Filament and EMULive, private and available on request.
