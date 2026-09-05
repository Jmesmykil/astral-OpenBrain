# Astral for OpenHome

Astral provides answers and conversation on an OpenHome DevKit. Its deterministic engine
handles time, arithmetic, conversions, grades, chemistry, physics and statistics. The
local hub adds the library on the SD card, definitions, notes, timers, memory, conversation
and optional local-model assistance.

The current completion audit is in progress. Read [HANDOFF.md](HANDOFF.md) for deployment
state, evidence and the remaining checks. Automated passes do not establish wake-word
reliability, audible playback, human interruption or successful platform assignment.

## Two current ways to use it

| Mode | Who handles speech | Where answers run | Status |
|---|---|---|---|
| Local loop | Vosk wake recognition, whisper.cpp transcription and Piper speech on the DevKit | Local hub, compiled/table engines, native mathematics and optional local model | Running on the development DevKit; acoustic acceptance remains open |
| OpenHome local ability | OpenHome's own speech and agent runtime | The DevKit shim asks the local hub, then the compiled kernel | Package validates; account login, platform deployment and assignment remain open |

The local loop and OpenHome's kiosk share one microphone. Run one at a time. In OpenHome
mode, speech handling belongs to the platform; device-side computation does not make
that whole path offline.

The local route order is mechanical computation, a local model when offered and accepted,
a named machine on the LAN, then an explicitly enabled cloud route. The cloud route is disabled in the current local
configuration; a Mac endpoint is configured on the LAN and the phone endpoint is unset. A named refusal or an ambiguous choice must
never authorize a transfer. The harness bridge described in the grant application is
future work; this release does not provide general access to project files or execute
harness tasks by voice.

## Development and package boundary

`community/astral/` is the readable MIT integration. `devkit_functions.py` delegates
answering to the hub or `astral-kernel`, reads device telemetry and publishes supported
MQTT commands. The compiled engine is separately licensed and proprietary. Its public
contract has two functions: `answer(text, now=None)` and `command(text, last_device=None)`.
See [BOUNDARY.md](community/astral/BOUNDARY.md).

The hub sources are maintained in a separate private repository at `hub/` in the
development checkout. They are not included in this public repository. A public clone
alone does not contain everything needed to rebuild the local loop.

`community/astral-skill/` retains the earlier cloud-side, source-inlined integration. It is
historical and is not the current compiled DevKit release. The former source-bundling
follow-up script is retired; it must not be used to publish the private hub.

## Device and library

The development device is a Raspberry Pi 4 with 8 GB RAM, Python 3.13 and a 128 GB card.
The wake phrases are “open brain” and “open home”; these are triggers, while the product
name remains Astral. The rejected trained wake classifier is not the active detector.

Library shelves hold reference material, documentation, code, datasets and books. The
current audit counted 191 physical inputs and 35 named sources. File count, source count,
passage count and readable coverage are different measurements. The audit found damaged
Britannica inputs and index-update defects; recovery and current counts are recorded in
[HANDOFF.md](HANDOFF.md). Scanned images alone do not establish searchable coverage.

The approved Astral sound pack is played as authored. Its `MASTERED.txt` marker bypasses
playback levelling. OpenHome owns the speaker and microphone settings; the runtime does
not force either level.

## Work on the current release

From the private development checkout:

```sh
python3 hub/tests/run.py --full
python3 hub/tests/run.py library ability voice
openhome validate community/astral
deploy/install_v2.sh openhome@192.168.1.23 --start
```

`--full` examines every hostile-input case without the normal discovery time cap. The
runner separates held, failed and skipped checks. Tests that use fake speech channels
are software checks, not proof that a person can interrupt or be heard in the room.

Deployment verifies a wheel against its build inputs and verifies the installed bytes
in both the system interpreter and the voice environment. A compiler, pip or kernel
verification failure stops deployment before the loop is restarted. See
[RELEASE.md](RELEASE.md) for the release artifact contract.

## Project records

- [HANDOFF.md](HANDOFF.md): current operating instructions and completion status.
- [KNOWN-BUGS.md](KNOWN-BUGS.md): current open issues followed by the dated historical ledger.
- [GRANT-APPLICATION.md](GRANT-APPLICATION.md): the September 4 application text; its counts and proposed bridge are historical claims, not a current release receipt.
- [handout/](handout/): the dated demonstration and presentation materials.
- [REVIEW-2026-09-01.md](REVIEW-2026-09-01.md): the earlier upstream review.

The creator reported submitting the grant application. This repository does not contain
an independently verified submission receipt. The harness, Slate mathematics, Astral
MECH and Q OS have distinct product identities; the grant does not make their proposed
future integration part of the completed OpenHome release.
