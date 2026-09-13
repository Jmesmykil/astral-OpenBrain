# Astral for OpenHome

Astral provides answers and conversation on an OpenHome DevKit. Its deterministic engine
handles time, arithmetic, conversions, grades, chemistry, physics and statistics. The
local hub adds the library on the SD card, definitions, notes, timers, memory, conversation
and optional local-model assistance.

The current completion audit is in progress. Read [HANDOFF.md](HANDOFF.md) for deployment
state, evidence and the remaining checks. Automated passes do not establish wake-word
reliability, audible playback, human interruption or successful platform spoken routing.

## Current development deployment — September 12, 2026

The DevKit now runs a coordinated hub, browser and Node bridge. The hub owns the
microphone and selects each turn; the browser receives only a selected OpenHome agent
request. Local takeover retires the previous agent transport. V9 also binds native
results to their original turn/session and declines duplicate autonomous Astral callbacks
before they execute. Agent context carries
only its own bounded conversation. See [HANDOFF.md](HANDOFF.md) for the current proof
and [deploy/turn-router/README.md](deploy/turn-router/README.md) for the paired install.

The current installed hub passed 1,038 targeted device checks with zero failures or
skips after the additional room-test repairs. The earlier full frozen run passed
5,490/0/0. In the actual room the device spoke 23 → 28 → 56, and time → London worked.
All 517 mixer samples in the agent run held speaker volume at 50%.

Physical interruption remains open: playback stops, but echo cancellation sometimes
loses words from the new request. Both microphone sources and browser playback are
paused after unrelated dialogue entered the last test. Saved speaker/raw microphone
levels are 50%/160%. Personal voice enrollment remains deferred. See
[the audio configuration package](deploy/audio-runtime/README.md) and the current handoff.

The table below describes the individual components; they are coordinated by the new
pair on the development DevKit.

| Mode | Who handles speech | Where answers run | Status |
|---|---|---|---|
| Local loop | Vosk wake recognition, whisper.cpp transcription and Piper speech on the DevKit | Local hub, compiled/table engines, native mathematics and optional local model | Running on the development DevKit; acoustic acceptance remains open |
| OpenHome local ability | OpenHome agent and browser playback; selected text comes from the hub on the paired device | The DevKit shim can ask the local hub, then the compiled kernel | Enabled on the development account; native checks pass; hosted source reconciliation and spoken acceptance remain open |

The paired browser opens no microphone. Older independent loop/kiosk installations
must still run one capture owner at a time. Requests selected for OpenHome use its
remote agent service; local computation does not make that path offline.

The local route order is mechanical computation, a local model when offered and accepted,
a named machine on the LAN, then an explicitly enabled cloud route. The OpenHome agent
is enabled as a named choice on the development device; other cloud providers remain
disabled. A Mac endpoint is configured on the LAN and the phone endpoint is unset. A named refusal or an ambiguous choice must
never authorize a transfer. The harness bridge is
future work; this release does not provide general access to project files or execute
harness tasks by voice.

## Development and package boundary

`community/astral/` is the readable MIT integration. `devkit_functions.py` delegates
answering to the hub or `astral-kernel`, reads device telemetry and publishes supported
MQTT commands. The compiled engine is separately licensed and proprietary. Its public
contract has two functions: `answer(text, now=None)` and `command(text, last_device=None)`.
See [BOUNDARY.md](community/astral/BOUNDARY.md).

The hub sources are maintained in a separate private repository at `hub/` in the
development checkout. They are not included in this integration repository, which is
also currently private. PR 361 in OpenHome's abilities repository is merged; that does
not make this development repository or its hub publicly accessible.

`community/astral-skill/` retains the earlier cloud-side, source-inlined integration. It is
historical and is not the current compiled DevKit release. The former source-bundling
follow-up script is retired; it must not be used to publish the private hub.

## Device and library

The development device is a Raspberry Pi 4 with 8 GB RAM, Python 3.13 and a 128 GB card.
The wake phrases are “open brain” and “open home”; these are triggers, while the product
name remains Astral. The rejected trained wake classifier is not the active detector.

Pages laid out in columns are read in the order they were written rather than straight
across, so a caption beside a body column is its own passage instead of being woven word
by word into the text next to it. The most heavily designed spreads, where display
lettering runs through the body text, can still come back interleaved.

Anything copied into the library's `drop` folder is filed onto the right shelf the next time
the card is indexed — say "index the library" — so putting a book, a paper or a report on the
device does not require deciding which shelf it belongs to. Nothing is deleted, a name already
taken is given a number rather than overwritten, and a kind nothing here can read stays where
it was put and is named when asked "what could you not read".

Library shelves hold reference material, documentation, code, datasets and books. The
current reconnect audit found schema 33, 191 indexed sources and 577,773
passages. Source count,
passage count and readable coverage are different measurements. The audit found damaged
Britannica inputs and index-update defects; recovery and current counts are recorded in
[HANDOFF.md](HANDOFF.md). Scanned images alone do not establish searchable coverage.

The approved Astral sound pack is played as authored. Its `MASTERED.txt` marker bypasses
playback levelling. OpenHome's saved speaker and microphone settings remain authoritative;
one measured agent sequence held its mixer level; broader sentence-level consistency remains open.

## Work on the current release

From the private development checkout:

```sh
python3 hub/tests/run.py --full
python3 hub/tests/run.py library ability voice
python3 hub/tests/room_regressions/run.py
openhome validate community/astral
deploy/install_v2.sh openhome@<devkit> --start
```

`--full` examines every hostile-input case without the normal discovery time cap. The
runner separates held, failed and skipped checks. Regression and stress runs own a
temporary Slate service and clean up its processes; they never fall back to the live
math socket. The latest frozen device full run passed 5,490 checks with zero failures
and zero skips, while preserving live math availability. Tests that use fake speech
channels are software checks, not proof that a person can interrupt or be heard in the room.

Deployment verifies a wheel against its build inputs and verifies the installed bytes
in both the system interpreter and the voice environment. A compiler, pip or kernel
verification failure stops deployment before the loop is restarted. See
[RELEASE.md](RELEASE.md) for the release artifact contract.

## Project records

- [HANDOFF.md](HANDOFF.md): current operating instructions and completion status.
- [KNOWN-BUGS.md](KNOWN-BUGS.md): current open issues followed by the dated historical ledger.
- [V2-CAPABILITIES.md](V2-CAPABILITIES.md): what the device does and how, in one page.
- [REVIEW-2026-09-01.md](REVIEW-2026-09-01.md): the earlier upstream review.

The harness, Slate mathematics, Astral MECH and Q OS have distinct product identities,
and none of their proposed future integration forms part of this release.
