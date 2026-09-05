# OpenHome Developer Grant: application answers

Fields 1 to 8 are yours (name, email, phone, referrer, location, GitHub, Discord, address).
Fields 9 to 18 below are version 3, 2026-09-04: the bridge to the AI tools on your own
computer as the critical selected feature, the local assistant as phase 1 already delivered,
and the deterministic engine as the road beyond. The strategy is in GRANT-STRATEGY.md and the
audit of version 2 in GRANT-AUDIT.md. Every number was measured on the DevKit or the Mac on
the date given.

---

## 9. Project Title

Astral for OpenHome: talk to the AI tools on your own computer, privately and with your consent

## 10. Project Description

Astral is a local voice assistant for the OpenHome DevKit, and it already runs. You say "open brain" and it answers on the device: the time, arithmetic and conversions, definitions, 682 curated facts, timers and notes, and questions against a library of 397,706 passages from books on the SD card. It holds a conversation without repeating the wake word, asks before anything leaves the house, and says why when it cannot help. Version 1 shipped as an OpenHome ability and was merged into OpenHome's dev branch as PR #361 on 2026-08-31. Version 2, the full local loop, runs on the DevKit today.

The grant funds the next step: a bridge from the DevKit to the AI tools on your own computer. Developers now run harnesses, the programs that drive a model to read and change project files, run commands and report back, and each one has its own keyboard-bound interface. The bridge gives all of them one voice. You ask the speaker what is failing in the build, hand a task to the harness, hear it ask you a question, confirm out loud before anything is changed, and ask it afterwards what it did. The protocol is open, so any harness can adopt it, and every action passes through the device's consent and audit rules on the local network. Beyond the grant, my own deterministic engine is meant to take over the model tier, but the bridge is built to deliver its value with whatever model the harness uses.

## 11. Rationale

Related work. Cloud assistants answer from a data centre and cannot touch your files. Home Assistant's Assist covers device control with fixed intents. Open Voice OS and Rhasspy run skills locally on a Raspberry Pi and are the closest relatives of the device itself. Offline reference readers such as Kiwix are not voice-first. The voice modes of assistant products let you talk to a model but not to the software on your machine. Agent harnesses such as Claude Code, OpenAI's Codex CLI and Aider do real work inside a project, and bridges in the style of OpenClaw and Hermes connect chat clients to them, but all of them are typed, tied to one interface, and run with whatever access the terminal happens to have. None of these give you a private, on-premises voice device that connects to any harness through one open protocol and asks your spoken consent for each action.

Where Astral fits and what is new. The device already has a ladder of routes: deterministic answers on the Pi, then a small local model, then a machine in the house over the local network, then named cloud providers, each offered by name and taken only on a spoken yes. Today's loop already reaches the Mac over that network rung through a one-line JSON protocol with a shared token. The bridge is the next rung of the same ladder, not a new direction. It contributes four things. An open protocol for pairing a voice device with a harness and scoping it to named projects. A consent model in which every action that changes a file or runs a program is confirmed by voice. An audit log the device can read back. And a reference adapter for an open-source harness, so the design is reproducible without my engine.

Relevance and impact. For OpenHome, the DevKit becomes the reference device for talking to your computer, with one open protocol that every harness author can support and a consent pattern other abilities can reuse. For the field, it is evidence that a voice device can be given real access to a computer safely, by putting the consent into the conversation instead of into a settings page.

## 12. Methodology

Build. The bridge is a small specification: pair, scope, ask, propose, confirm, run, report, stop and audit, each one line of JSON on the local network with a shared token, the way the existing network rung works (lan.py, port 8790). The device side goes into the local loop and into the ability that runs inside OpenHome, both MIT and public at https://github.com/Jmesmykil/astral-OpenBrain, with the seam to the compiled engine documented in community/astral/BOUNDARY.md. The harness side is an adapter of about a hundred lines. I will ship two: one for my own harness, the Astral Brain Engine, which the bridge was designed against, and one for an open-source coding harness, so anyone can reproduce the demo with public software.

Test. The product carries 3,884 automated checks in 27 suites on my Mac, and the same suite runs on the DevKit against a scratch copy of its state, so no check can touch the card. Every new check is proved to fail before its fix goes in, and every refusal reason the device can give is read out of the source and tested, so no failure is silent. The bridge gets suites of its own: no action without a scope, no change without a confirmation, a replayed session for every exchange in this application, and an audit that always matches what ran. Beyond the suite I use the device in my own work, and one adversarial review found 57 candidate defects, of which 24 were verified and 13 reproduced on the device and fixed the same day.

Plan against OpenHome's stages. Dev Kit tier: I have a DevKit and ship on it. Community development: the repository is public, I am in the OpenHome Discord, and I will post an update at each phase. Completed demo: the local assistant runs by voice today, with a transcript in the repository, and the bridge demo follows the same way. Live integration: version 1 is merged as PR #361, and the bridge goes through the same review. Critical selected feature: the bridge.

## 13. Experience

Relevant experience. I built Astral alone on the DevKit over the past month, from the wake phrase to the library indexer to the deploy script, and shipped version 1 as an ability that OpenHome reviewed and merged. Before that I wrote openhome-cli, a public TypeScript command line tool that deploys, validates and scaffolds OpenHome abilities, and I maintain a public repository of open-source abilities for OpenHome agents. This is my third OpenHome project, and the first two are in use.

I have also built the thing the bridge connects to. The Astral Brain Engine is my harness: a model-agnostic orchestration layer with a delegation hierarchy, persistent memory, budgets and a task board (607 commits), and it coordinated the work on this project. Under it, Astral MECH, in the Strata repository, is a language comprehension engine written in Julia with Ada SPARK proofs and Rust lanes: no model weights, a typed role graph for every sentence, memory that keeps its sources, and an honest refusal when it cannot read something (436 commits). Slate, its mathematics lane, runs on the DevKit today as the kernel service. I also do systems work on constrained hardware: Q OS, a windowed desktop for the Nintendo Switch (in development, repository public), a hardware-in-the-loop firmware workbench, and a Game Boy emulator.

Confidence. High for the bridge, because the network rung, the consent ladder, the audit discipline and the test suite already exist, and the first harness it connects to is mine. I am honest about the longer road. A deterministic engine that does what a model does is ambitious, and I am not certain it will fully succeed. The bridge does not depend on it. It is model-agnostic and delivers its value to OpenHome with whatever model the harness runs.

## 14. Technologies Used

Raspberry Pi 4 (OpenHome DevKit) with its microphone array and speaker. The vosk phrase recogniser for the wake phrase. whisper.cpp (base.en, quantised) for speech recognition. piper for the voice. llama.cpp with Llama 3.2 1B Instruct for paraphrase and summary. A Cython-compiled deterministic kernel for the table answers and a Julia mathematics kernel as a service. SQLite FTS5 for the library. PipeWire for audio, systemd user services, Python 3.13. For the bridge, one line of JSON per message over the local network with a shared token, per-project scopes, an audit log in SQLite, and adapters in Python on the harness side. On the platform side, the OpenHome SDK and its local-ability contract, with the OpenHome app for volume and pairing. AWS credits, if awarded, would fund evaluation runs.

## 15. Team

Jamesmykil Weber, sole developer: architecture, kernel, router, library, audio, deployment, tests, and the bridge protocol and adapters. Author of openhome-cli and the OpenHome abilities repository. Version 1 of Astral merged into OpenHome as PR #361. Independent developer and student, Oahu, Hawaii. GitHub: https://github.com/Jmesmykil

## 16. Elaborate on the details of your project

What it is like to use. You are at the kitchen counter and the build is running on the computer in the other room.
"Open brain, what's failing in the build?" "Two tests in the payments module. Both expect a rounding rule that changed on Tuesday."
"Ask the harness to fix it and tell me when it's done." "It wants to change two files in payments. Say yes to allow that." "Yes." A minute later: "Done. Both tests pass. Nothing else was touched."
"What did you change?" "A rounding helper and its test. I can read you the change or leave it for the morning."
And in the other direction, the harness asking you: "The harness has a question. Should it keep the old rule for invoices before Tuesday?" "Keep it." "Told it. It's working."
Each exchange is short and goes both ways, and the device asks before anything changes.

Expected impact. For OpenHome, the DevKit becomes the reference device for talking to your computer, with one open protocol any harness author can support and a consent pattern other abilities can copy. For developers, the tools they already run gain a hands-free front end that never leaves the house. For the field, it is a working answer to how a voice device can be given real access to a computer without giving up control.

Why I am excited. I built the local assistant because I wanted a speaker that would not go quiet when the network did. I want the bridge because I already spend my days talking to a harness through a keyboard, and the first time the speaker answered from the books on the card with nothing sent anywhere, the room changed. I want developers to have that for the tools they work in.

Ethics and security. The bridge starts from the rules the device already keeps. Nothing leaves the local network, and cloud providers are offered only by name and taken only on a spoken yes. A harness is paired once, from the device, with a token, and given scopes by project, so it never sees more than it was told. Every action that changes a file or runs a program is proposed in plain words and confirmed by voice before it happens. Everything that ran is written to an audit the device reads back on request, and "open brain, stop everything" halts the harness. The device says when it does not know or cannot do something rather than guessing, and every refusal reason is tested. The ability and the bridge protocol are MIT and reviewable. The engine underneath is my product and ships compiled, with the seam between the two documented.

Three phases. Phase 1 is delivered: the local assistant, merged as PR #361, version 2 running on the DevKit, 3,884 checks. Phase 2 is the grant: the bridge protocol, the device side in the loop and in the ability, adapters for my harness and for one open-source harness, the consent and audit suites, a demo with a transcript, and the code review into OpenHome. Phase 3 is beyond the grant and is my own venture: a deterministic engine taking over the model tier, so the harness can do most of its work without a model in the loop. The workstation below serves both phases, as the machine in the house for the bridge and as the training lane for the engine.

Budget. A workstation that can hold a training run and serve as the machine in the house (a Minisforum MS-S1 MAX with 128 GB of unified memory, $3,799 on the maker's store today, or a Mac Studio at that level). Test hardware, including two more DevKits for measuring the bridge in homes that are not mine. My time for the two phases the grant covers. At a smaller award, the bridge and one adapter still ship, on my own time. AWS credits would fund evaluation runs.

## 17. What is the project you are most proud of?

The harness and the engines under it, because the bridge is how they reach a voice. The Astral Brain Engine is the orchestration layer I run everything through: model-agnostic, with a delegation hierarchy, persistent memory, budgets and a coordination bus, and it carried this project from the wake word to the merged pull request. Under it sit two engines written in languages I chose for proof rather than convenience. Astral MECH, in the Strata repository, is a language comprehension engine in Julia with Ada SPARK proofs and Rust lanes: no model weights, no sampling, a typed role graph for every sentence, memory that keeps its sources, and an honest refusal when it cannot read something. Slate is its mathematics lane, and it is the kernel service answering arithmetic on the DevKit today. This device is the first piece of that work to ship through someone else's review.

Links. This project: https://github.com/Jmesmykil/astral-OpenBrain, with the handout and demo transcript at https://github.com/Jmesmykil/astral-OpenBrain/tree/main/handout. openhome-cli: https://github.com/Jmesmykil/openhome-cli. Open-source abilities for OpenHome: https://github.com/Jmesmykil/abilities. Q OS (in development): https://github.com/Jmesmykil/QNX. The Astral Brain Engine, Strata and Slate are private and available on request.

## 18. Anything else we should know?

How I heard about the program. From Brady at OpenHome. I am in the OpenHome Discord and in touch with the developer relations team there, and I gave Brady a thirty-minute demo on 2026-09-04.

Affiliation. Independent developer and student. No organisation or company is behind the project.

Previous projects in AI and related fields. The Astral Brain Engine (orchestration), Astral MECH and Slate (language comprehension and mathematics engines), all private and available on request. openhome-cli and the OpenHome abilities repository, both public and in use.

Presentations and publications. The demo call with OpenHome on 2026-09-04. The handout with the demo timeline and measurements is in the repository (handout/OpenBrain-Handout.pdf). No publications yet.

References. None claimed. Brady at OpenHome has seen the working demo.

Reproducibility. Everything claimed here can be reproduced on the hardware in about ten minutes with the deploy script, and the demo runs by voice. Everything so far was built on hardware I already own, about $10,000 of it out of pocket over the last three years. Contact: mykiljames253@gmail.com, +1 253 392 9204.
