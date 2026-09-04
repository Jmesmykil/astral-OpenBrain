# Notes from the call with Bradyn, OpenHome, 2026-09-04

What was said, grouped, and what I'm doing about it.

## Hardware

The DevKit's audio cable connections need reseating from time to time, and a LAN cable
is the stable way to work over a terminal. I asked for hardware buttons: tap to mute, and
an emergency off switch, so the person in the room has physical control. OpenHome is
waiting on new DevKit parts and wants more meetups and workshops, including a screen or
mini display prototype for a richer interface.

What I'm doing: the cable note goes in KNOWN-BUGS.md next to the deaf-start findings, and
tap-to-mute and emergency off go on the roadmap as things the local loop should honour.

## Languages and the development experience

Python is easy, and I'd rather write C and more specific languages where they fit. I want
broader language support and more flexibility in how abilities are built.

## The mechanical assistant and local compute

What runs on the DevKit is a deterministic mechanical assistant in the Eliza tradition,
with a large lexicon and CPU-only compute. The Astral engine outside it joins local and
cloud compute under a governance-style harness that manages the logic flow and the task
boards. I'm porting the Hermes harness behaviour into my own compatible system so people
with DIY harness styles can use it too.

## Why I'm building it

A fluent communication engine that accumulates local conversation, recognises voices and
translates, because my household is bilingual. Siri still does some things better than a
model, and that is the bar for the mechanical layer. I'm a coding student with limited
resources, and I'm looking for guidance and collaboration.

## The stack and latency

Long term I want to own the whole stack, custom transformers and inference pipelines with
no cloud in the path. The pain today is network and cloud delay and juggling several
compute layers on site, so I build to keep speech-to-text, text-to-speech and inference
local.

## Security and memory

I work on the device over SSH because the platform's file system access is limited and I
care about security. Memory is a lexicon, heat maps, neural points, and encyclopedias on
the SD card for fast retrieval. The chimes for thinking, accepted and denied are the
device's way of saying what state it is in.

## The CLI and the community

Bradyn recommends the new CLI tools for faster development and easier submission of
abilities. The Hermes and OpenClaw bridge integration supports people with custom
harnesses, and OpenHome is interested in the Astral engine running locally with OpenHome
for experiments. My harness is designed for universal compatibility through clean-room
reverse engineering.

What I'm doing: the ability now carries a config.json for the CLI, the kernel wheel is
released so requirements.txt installs it, my CLI's validator is fixed so the DevKit
contract file is judged by the right rules, and the deploy and trigger registration go
through the CLI next.

## Julia and Ada

Julia and Ada SPARK are the languages behind the computational engines and the fail-safe
parts. Family members who build their own technology and AI projects are part of why I
do this.

## Follow-up

OpenHome will share transcripts and summaries; the two threads to explore are DIY harness
bridging and using the CLI tools for everything that ships.
