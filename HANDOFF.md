# Handoff: Astral on the OpenHome DevKit

## Current deployment — September 5, 2026, 10:19 HST

The reconnected DevKit runs private hub `63fa1668ef345b21a17ac7c8de3f04ce78f7c6bc`
and kernel **2.2.3**. All 106 deployable Python files match the checkout. Both system
Python and the voice environment match the verified wheel. The latest guarded deployment
finished successfully; the voice service started at 10:13:19 HST (PID 19661), the shared
mathematics service is active, and the kiosk is inactive so it does not compete for the
microphone. These process identifiers are a dated observation, not permanent configuration.

The personal Ponytail/pre-mortem pass reproduced and repaired 22 findings across library
integrity, OCR, timer/settings/notes persistence, speech publication, isolated staging,
shared-kernel routing, test isolation and the root-to-owner audio-session boundary.
The wheel carries the compiled timer repair; the other runtime features require the
companion hub deployment. The wheel alone is not the complete voice assistant.

| Verification | Held | Failed | Skipped | Revision and scope |
|---|---:|---:|---:|---|
| Final Mac full | 4,119 | 0 | 12 | `63fa166`; all 29 suites and 419 hostile inputs |
| Device full | 4,142 | 0 | 6 | `cca08bb`; all 29 suites and 419 hostile inputs |
| Device state changes | 4,102 | 0 | 5 | `2938674`; 28 suites, excluding the prior hostile sweep |
| Device final audio change | 604 | 0 | 4 | `63fa166`; seven relevant suites |

These runs overlap and must not be added as unique tests. The full device run preceded
the final state/audio changes, which have separate device regressions. A later eight-call
check through the actual installed root shim proved saved zero values, the real 14% master
report, preserved separate notebooks and owner-written isolated state. An earlier root
check covered 139 pinned answers, 40 intended silences and ten runtime calls. Compiled
parity covers 181 corpus entries. None of these typed calls proves human audibility.

The public [2.2.3 release](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.3)
is published and hash-pinned in `community/astral/requirements.txt`. An unauthenticated
public download and the DevKit's exact `pip download --require-hashes` dependency both
match the installed artifact. The package validates with the persistent creator-fork CLI.
Both repositories are pushed. Existing 2.2.2 release bytes are unchanged.

Schema 25 independently matches all 191 physical/source files and 412,826 passages,
including each file's hash and FTS count. All 29 encyclopedia archives match their source
checksums. No empty, unread or orphan source rows were found. Actual-device passage-count
median fell from 986 ms to 0.63 ms; this is a count operation, not overall answer latency.
Four search queries retained identical results: first queries after verified zero index-file
cache residency took 68–296 ms; warm medians were 6.8–28.6 ms, broadly unchanged.
Repeated shared mathematics requests avoid new child processes: observed warm repeats
were 2.8–3.6 ms, while the first equation request still took 4.1 seconds.

All nine approved sound-pack files and all seven selected cues match. Production settings,
notes-state and timer-state hashes remained unchanged through deployment and isolated
verification. Your power cycle restored OpenHome's saved speaker 14% and microphone 160%,
matching live PipeWire levels. This audit changed neither level.

Still open: authenticated platform deployment/assignment and spoken routing; human wake
positives and room negatives; short follow-ups, including the two empty quiet-room captures;
interruption while thinking/speaking; app-slider behavior and audibility. The Mac was locked
at the latest UI check, and CLI authentication was false. The retired trained wake head is
not part of the active Vosk phrase recognizer. Hash integrity does not establish library-wide
OCR accuracy, recognition of every diagram, or page labels in plain OCR archives.

Detailed, dated receipts and every skip reason:
`~/AstralBrainEngine/projects/openhome/audits/2026-09-05-ponytail-premortem/`.

## Machines and ownership

| Item | Location |
|---|---|
| DevKit | `openhome@192.168.1.23`, Raspberry Pi 4, 8 GB, CPython 3.13.5 / Linux aarch64 |
| Private development | `~/Documents/OpenHome-Astral/hub/` on the Mac |
| Device loop | `~/astral-voice/hub-v2/` |
| Voice interpreter | `~/astral-voice/kws-venv/bin/python3` |
| Owner state | `~/astral-voice/state/` |
| Library and index | `~/astral-voice/library/` |
| Selected sound pack | `~/astral-voice/sounds/packs/astral/` |
| Voice log | `~/astral-voice/astral-hub.log` |
| Device audit/rollback files | `~/astral-checks/codex-ponytail-20260905/` |

The public integration and readable ability shim are MIT. The private hub and proprietary
compiled engine are separate; the public repository alone cannot rebuild them. The wheel
contains no private Python, Cython or C source. No optional cloud route was enabled.
The preserved Pi ranking profile covers 30 classes measured on September 3; Mac data did
not replace it. Optional external routes require the owner's explicit choice.

## Develop and deploy

```sh
python3 hub/tests/run.py --full
openhome validate community/astral
deploy/install_v2.sh openhome@192.168.1.23 --start
```

Use the established Python environment with the required test dependencies. Preserve full
logs and exit codes. `--full` removes the hostile-corpus discovery cap. Tests redirect
mutable state with `ASTRAL_STATE`; they do not prove the physical room. The final Mac's
native-kernel, reader, dictionary, Linux pipe, Vosk, Spanish voice, page-book, lint and
compiled-package skips have device coverage. The trained wake head is intentionally
retired, and the removed README measurement table is absent. Device skips for the Mac
installer and package/doc files are covered in the workspace. Optional daemon software
checks do not prove platform assignment.

The installer fails on build, index, package-verification or service-start errors. It
verifies the exact extension, wrapper and manifest in both interpreters and restarts the
running loop. Keep the explicit rsync include list current for new directories. Preserve
the device's measured profile and verify installed files after deployment.

Astral and OpenHome's kiosk must not own the microphone simultaneously. To return the
microphone to OpenHome, stop Astral before starting `openhome-dashboard.service`.
OpenHome owns saved master speaker and microphone levels. The installer migration only
changes an untouched default microphone value of 30; subsequent owner choices are
preserved. Approved mastered sounds play as authored.

## Platform and human acceptance

The persistent CLI is the creator's fork, installed under `~/.local/share/openhome-cli`,
with its validator fix. An advertised upstream update has not been substituted for it.

```sh
openhome login
openhome validate community/astral
openhome deploy community/astral --name Astral --category local --json
openhome assign
openhome trigger "what time is it"
```

Authentication requires the owner. Keep credentials out of transcripts and retain sanitized
platform receipts. A local validator, copied DevKit files and typed shim calls do not prove
platform registration, assignment or a spoken platform turn.

With the owner present, record real wake positives and matched overheard negatives, short
and long requests, time→London/date follow-ups, timer cancellation, and interruption while
thinking and speaking. Check the actual microphone capture, transcript, routing, completed
playback and what the owner heard. Measure interruption latency. Use OpenHome's app for
its speaker slider and verify its live/saved effect without silently choosing a new level.
The power-cycle restoration of saved 14/160 is already proved. Player exit zero and the
`[spoken]` marker prove uninterrupted player completion, not acoustic audibility.

## History and completed-work boundaries

The exact September 4 OPEN HOME session is
`f1455099-d3d1-4c6a-aa44-ebd66ce5c6e0`. The local reference index retains all 128 creator
messages and distinguishes development, delivered artifacts and future work. The dated
[known-bug ledger](KNOWN-BUGS.md) preserves previous observations; its historical readiness
claims do not replace current acceptance. Earlier completion-audit receipts remain under
`~/AstralBrainEngine/projects/openhome/audits/2026-09-04-completion/`.

The grant submission was reported by the creator. Its proposed harness bridge and longer
term deterministic-engine ambition remain future work. Separate portfolio products are
not shipped OpenHome functionality. No new grant submission was made during this audit.

See [RELEASE.md](RELEASE.md) for artifact provenance and immutable release procedure.
