# Handoff: Astral on the OpenHome DevKit

## Current runtime verification — September 6, 2026

The DevKit runs kernel **2.2.6** in both interpreters. The full device run passed **5,111
checks, zero failures, five documented skips**, including all hostile inputs and the stress
suite. The Mac full run passed 5,002 with thirteen skips. The library index is schema 32,
577,773 passages across 191 files. These runs overlap and
must not be added together.

Three defects found in the room were reproduced, repaired and gated this day.

**Long questions lost their ending.** The whisper window was pinned at 512 encoder frames,
which is 10.24 seconds at 20 ms a frame, while the recorder was allowed to hand it MAX_SEC
plus a seed, about fifteen. Nothing compared the two numbers. A 13.4 second question came
back missing its final clause, identically from a clean recording and a noisy one, which is
what identified the window rather than the room. The window is now sized to each capture.
Measured on the device against the recording that failed: at 512 the transcript stops at
"becomes active", at 697 it runs to the end. Short commands are unchanged at 2.66 s and
3.99 s. The separate 12.2 second timeout recorded earlier is NOT explained by this and
remains open; that file is short speech padded with silence and transcribes correctly at
either setting.

**Pages laid out in columns were read straight across.** DK sets a body column beside
numbered captions and the extractor reads the page the way a printer does, so the library
held "Hawaii's Big Island lies Kilauea volcano on The huge volcanoes above the hotspot,
which the southern flank of..." — captions interleaved word by word, every word present in
an order nobody wrote. Columns are now unwound before a page is paragraphed. The guards
matter more than the unwinding: a table keeps its rows, a block with no column structure is
untouched, a column must be sustained across adjacent lines and may miss at most one, and a
caption is kept whole rather than dropped for being short. Over all 211 pages of one volume:
105 pages reordered, 595 passages to 1,163, 315 words recovered that the old floor was
dropping, and of the words that leave the passage text only 44 have lower-case in them —
every one a diagram label of one or two words, which previously survived only inside a
garbled run-on. No piece of three words or more is lost.

**Two requests in one breath were answered with silence.** "turn off the lights and close
the blinds" parsed as a device named "lights and close blinds", and "turn on the lamp and
turn off the fan" as "on lamp and turn" carrying OFF. The name guards already refused to
publish those, so no malformed MQTT target was ever sent and no half of a request was
carried out; what was missing is that the device said nothing at all. It now names both
halves and does neither.

**The local layer stopped cutting the cloud agent off mid-word.** The background daemon
preempts the cloud agent by interrupting it, which is the cost ranking made audible: the
device wins the turn when it is cheaper AND faster. Only the first half was checked. The
foreground `respond()` is allowed twelve seconds and answers a slow engine with a sentence
of its own, so the daemon could sit through the agent's whole reply and then sever it to
report that the local side had been slow. The daemon now asks `respond_now`, whose budget
is one second, and it does not interrupt at all once two seconds have passed since the turn
appeared: after that the cloud's answer is the ranked outcome. The budget is measured, not
picked — a native callback's median round trip here is 181-203 ms and a tier-0 answer
computes in under 1.4 ms. A timer coming due still interrupts, and so does the
once-a-session health sentence, because `speak()` without an interrupt does not wait its
turn on this platform and two voices at once is worse than one clean cut.

The library index is schema 31 with **574,308 passages across 191 files**. On the device,
"how do islands form", "ring of fire", "what causes earthquakes" and "volcano" now each
return a readable passage first; the first three returned woven text before this work.

**Stress testing found two real defects, both now fixed.** A new `stress` suite covers what
the hostile-sentence sweep does not: several requests at once, a card full of files nobody
curated, a failure register under flood, and input nobody would type on purpose.

It found, first, a crash. "what is 20 percent of" followed by four hundred digits raised an
`OverflowError` out of the number formatter and through the router: an integer that large
becomes infinity the moment it is divided, and both `round()` and `int()` raise on that. The
formatter is now total — it never raises, whatever it is handed — and an unsayable result is
refused out loud. That is engine code, so it required a new wheel.

It found, second, a stall that only the device could show. Fifteen thousand characters
through the front door cost the DevKit **28.5 seconds** — eight in regular expressions and
twenty more waiting out a subprocess timeout — for a sentence nobody said. The microphone
cannot produce that; the platform's ability path can. Requests are now bounded at the single
door and refused out loud: 28.5 seconds became 0.000, with ordinary questions untouched.

The suite also holds three invariants for a card people put files on: every file given to
the drop folder is still somewhere on the card afterwards, no malformed file raises while
being read, and a name already taken is never overwritten.

**Kernel 2.2.6 is published** at
[v2.2.6](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.6), 494,785 bytes,
SHA256 `e9d723d6…`. It fixes a wrong answer found by playing a question through the device's
own speaker: a follow-up completed to "what time is in london", without its "it", matched
nothing in the clock, escalated to the model tier and was answered aloud with "Time
downloaded software." The clock now accepts the dropped word. Earlier releases are
immutable and unchanged. 2.2.5 SHA256 `737a77ed…`. Its compiled extension is byte-identical in both device interpreters, the
current sources reproduce the input fingerprint `a0a5aeab…` exactly, an independent public
download matches, the DevKit resolves the exact pin under `pip download --require-hashes`,
and the package passes `openhome validate`. All three capability folders carry it. 2.2.4,
2.2.3 and 2.2.2 are unchanged and immutable.

**One folder to put things in.** A person should not have to decide whether a research paper
is a book or a document. Anything copied into the library's `drop` folder is filed onto the
right shelf when the card is next indexed — say "index the library" — and anything nothing
here can read stays exactly where it was put and is named when asked "what could you not
read". Nothing is ever deleted, and a name already on the shelf is given a number rather
than overwritten.

**No silent failure, at the root.** 160 exception handlers in the hub swallow a failure
without recording it. Most are correct; converting all of them would bury the real ones. So
`hub/mishaps.py` is now the one register everything lost reports into — the library's
unreadable files report through a dict subclass whose assignment IS the report, so no call
site has to remember — and two surfaces read it: the health line stops looking healthy while
turns are being lost, and "what went wrong" answers out loud with the reason. The count is
held as a ratchet by the integrity suite: it may fall freely and may not rise.

**A subscription is a provider too.** Requiring a metered API key to reach a model somebody
already pays for is an accounting decision dressed up as an architecture. A provider with
`"shape": "subscription"` in `routes.json` is reached by running a command that is already
signed in as the owner, with the question on standard input — no key, no metering. The
command is declared in `routes.json` rather than shipped, because the program that reaches it
is a fact about one machine. A command this machine does not have is refused by name rather
than attempted and blamed on the provider; nothing is ever passed through a shell. This is
also what a higher rung than the DevKit actually means: the Mac carries four capabilities to
the device's ten, so copying the card there would change nothing, while a subscription
command on the Mac reaches a model the Pi cannot hold.

**An answer must have the shape the question asked for.** A question about a time or a
quantity is not answered by a sentence carrying neither. Asked "what time is in london" — a
follow-up that had lost its "it" — the reader replied "Time downloaded software.", a fragment
of its own corpus. The clock now accepts the dropped word, and separately the router refuses
a reader answer whose shape does not match the question, trying the books first and then
saying it will not guess. It joins the guards already here for empty glosses and for
six-word explanations of why the sky is blue.

**The document readers no longer lose files quietly.** Ten of them — epub, xlsx, rtf,
subtitles, notebooks, mail, pdf and the document paths — returned nothing when a file could
not be opened, bypassing the very register written to stop that. A research paper copied onto
the card could fail to parse and nobody would be told. They report now, by name and with the
reason, and the silent-handler ratchet came down from 160 to 150 with them.

**A spoken answer arrives in 7.6 seconds, not 12.2.** None of the wait was the engine, which
answers in a third of a second — all of it was the capture. `SIL_PEAK` is a constant chosen
for a quiet room and it decided when speech had ENDED, so in a loud room nothing ever fell
below it: measured over 765 real captures, 20 percent ran to the fourteen-second ceiling, and
where the ambient peak read 1500 or more, 48 of 177 never saw silence at all. Ending is now
judged against the room and starting still against the constant, which is the whole safety of
it — a measured floor can only end a burst sooner, never make the device deaf to a quiet
voice, and in a quiet room the two numbers are identical. Five clean runs on the device:
captures fell from 7.7 seconds to 3.4-4.1 and the answer arrived at +7.6 where it had been
+12.2, all five transcribed correctly.

**There is now a labelled wake rate, and it cost a repair.** Every previous number came from
counting log lines in a room nobody annotated. A stimulus synthesised from chosen text is its
own ground truth, so: twelve conversational negatives and six positives gave 0 false
activations and 0 misses, and fourteen adversarial near-misses — "open a", "open and",
"opening ceremony at home", "hope and brain" — activated it 6 to 8 times across runs. That is
the recogniser, and it is the argument for the trained head scoped to V3.

Three of those fourteen made the device SPEAK, inventing a device out of the words after the
verb: "I don't have any devices set up yet, so I can't open bank account without address."
Two paths reached device control and only `control.py` asked whether the target was a thing in
a room; the registry path asks now. Re-run against the same corpus the three nonsense answers
are gone — silent, as "ignored: not a request" or "floor: not for me". A false wake that stays
quiet costs nobody anything; a false wake that talks is the one worth fixing, and unlike the
recogniser it was fixable here. Evidence in `acceptance/wake-rate-v1/`.

**The column repair covers 95.4 percent of it.** Measured across all 65 DK volumes rather than
sampled: 19,813 pages, 54,108 columnar blocks, 51,620 unwound and 2,488 declined because
unwinding would push readable prose under the passage floor. The residual is 1.96 percent of
all blocks. Three attempts to measure the damage by scanning the finished index were abandoned
and are written down in `acceptance/library-layout-v1/COVERAGE.md`, because each measured
English rather than damage — author initials and mathematical variables are indistinguishable
by shape from letter-spaced OCR debris, and a number from a detector that cannot tell them
apart is worse than no number.

**Silent handlers are down to 146** from 160, held by a ratchet that may fall and may not
rise. The last four discarded the owner's own choices: a failed settings read replaced the
voice and the speech model he picked with the defaults, so the device sounded or heard wrong
with the symptom and the cause in different places.

**Still open.** DK's most heavily designed spreads, where display lettering is set through
the body text, can still come back interleaved in a lower-ranked hit. Human wake, room, interruption
and audibility acceptance remain open, as does platform spoken-session routing and the
remaining capability and library semantic breadth. The wake-word false-activation evidence
is now measured — see the engine-side `acceptance/room-noise-v1/FINDINGS.md` — but it is log
analysis, not a labelled corpus with a person in the room. Earlier dated sections below are
historical snapshots.

## Current runtime verification — September 5, 2026, 20:02 HST

Private hub 7a88d13d71629d507cf76e7edca74f612bf62e00 is deployed. All 30 device suites passed: **4,367 checks, zero failures, five documented skips**, including all 419 hostile inputs. The run preserved 115 source hashes, 47 protected file hashes, audio levels, actual user services and the live Slate child. Registered native requests passed 3/3 before and after. The test-owned kernel was cleaned up with no running descendants. The compiled 2.2.3 artifact is unchanged.

Schema27 retains all **191 source files** and contains **417,340 passages**. A final independent census found no missing files, changed source hashes, unread inputs or chunk-count mismatches. The repairs preserve words separated by wide OCR column spacing, remove lookup request scaffolding from the topic, and distinguish exact qualified API names such as json.load and json.loads. All 71 non-gzip source chunk counts and the 17 predicates from four visually reviewed PDF pages were preserved. Seven targeted raw-word predicates and 46 installed retrieval scenarios passed.

Thirty alternating-order warm repetitions per question compared both lookup implementations against the same index. Fraction documentation remained correct and median handler time fell from 323 ms to 9.5 ms; json.load remained correct and fell from 321 ms to 7.3 ms. All 180 revised answers passed their oracles. Some previous answers were incorrect, so their latency is not presented as equivalent successful work. These are text-handler measurements; they exclude microphone, ASR, TTS and platform spoken-session latency.

The existing account is verified, and Astral is registered, installed and assigned. An in-app browser sign-in is not required. Remaining work includes human wake/follow-up speech, interruptions, audibility, platform spoken-session acceptance, broader capability scenarios and source publication. Some OCR sources still interleave columns; preserving their words does not establish the intended reading order of every page. Code and data shelves are currently empty. Original requirements remain seven verified within scope and ten open or partial.

The schema26/source rollback is retained at /home/openhome/astral-voice/platform-hardening/library27-v1/rollback. Local acceptance records include LIBRARY27-DEPLOYMENT-RECEIPT.json, FULL-DEVICE-V4-RECEIPT.json and the personal Ponytail/pre-mortem review. Source commits have not been pushed. Earlier dated snapshots below are historical and may describe issues subsequently resolved.

## Previous runtime verification — September 5, 2026, 19:03 HST

Private hub `fbd3e7d620c151a3e617b2c81394fb30b49817c2` is deployed. The full device run completed all 30 suites and all 419 hostile inputs: **4,342 held, zero failed, five explicitly skipped**, in 149 seconds. All 115 selected Python/support source hashes and 47 protected file hashes stayed unchanged during the run. Audio levels, actual user-service processes and the live Slate child stayed unchanged. Three registered native requests passed before and after; the final equation response was `x = 4` in 181 ms. This is a software/native-path observation, not an acoustic latency measurement.

The latest corrections fix decimal memory units, replace unconditional privacy claims with the actual local/platform/diagnostic boundaries, expire abandoned math requests, and make readiness/recovery follow a working kernel. Tests and stress runs now own an isolated Slate process instead of falling back to the live socket. The full run recorded its test kernel and verified cleanup with no running descendants remaining. Focused device checks passed 586/0/2 before the full run; these counts overlap and must not be added together.

The five device skips are the deploy-machine installer, the retired trained wake head, background-ability health in a layout without that package, the Mac restart command, and workspace-document checks. Mac-side deployment and document checks have separate evidence; the retired head is not the active Vosk wake detector. The compiled 2.2.3 input fingerprint is unchanged, so no new wheel was built.

Some earlier helper receipts queried inactive system units instead of the actual Astral user services. Those comparisons alone did not prove preservation. The correction records real user-service start times preceding the affected operations; the current full run explicitly checks user units, their kernel child and actual answers. Original receipts and the first rolled-back deployment attempt remain preserved in the local acceptance ledger.

The existing account works; Astral remains registered, installed and assigned. Still open: platform spoken routing, human wake/room/interruption/audibility acceptance, the remaining capability/library semantic matrix, final source publication and final handoff. Read the latest local acceptance ledger for progress after this timestamp. Earlier dated sections below are historical snapshots.

## Current account and repeat deployment — September 5, 2026, 17:50 HST

The existing account key works. Astral is registered as `jamesmykilastral`, installed on the DevKit and assigned to the existing Astral agent. The original17 installed abilities and the other7 agents were preserved. Three actual Node/Python/shim/hub requests through the registered name pass. This is not a platform spoken-turn receipt.

The companion installer now refreshes names explicitly recorded in `~/astral-voice/state/openhome-capability-names.txt`, one alphanumeric registration name per line. It preserves existing names, platform metadata and the canonical `astral`/`astral-daemon` copies. Keep this owner-state file with device configuration when migrating; do not infer managed folders by scanning arbitrary capability code. Malformed names and symlink targets fail before copying. Current Mac deployment checks:70 held,0 failed,0 skipped. Installed device:63 held,0 failed,1 skipped (the Mac-only restart group). The real refresh preserved46 owner hashes, capability contents, audio levels and service processes.

The account's committed initial release and editable release contain identical archive bytes. OpenHome renamed the uploaded Python class to match the registration name; a source hash difference alone is not evidence of a changed algorithm. Actual platform runtime selection and physical voice acceptance remain unverified. The corrected persistent CLI uses the existing API key without requiring a JWT;14 auth/name checks, typecheck and build pass. No new account, credential or inference provider was introduced.

Still open: platform spoken routing, human wake/room/interruption/audibility acceptance, the full capability/library semantic matrix, final regression and source publication. Earlier dated sections below retain historical states; use this section and the local acceptance ledger for current account status.


## Actual app control — September 5, 2026, 16:50 HST

The authenticated DevKit speaker control changed the actual mixer and saved setting from 14% to 17%; both were restored to 14%. Mic sensitivity stayed 160%, other environment content hashes and the three Astral service identities were unchanged. An intermediate pointer attempt displayed 21%; the exact original value was then selected with keys and committed by clicking the slider. No audio playback was used, so human audibility remains open.

Arrow keys alone changed the displayed value without committing to the device until a click. This observed app limitation remains open. [The hardware acceptance guide](deploy/HW_TEST.md) now matches the current wake phrases, equation support and live interruption path. Its human trials are explicitly not run.

## Installation reconciliation — September 5, 2026, 16:41 HST

All168 selected source/support files and all three Astral service definitions match. Both actual Python interpreters match the pinned2.2.3 wheel; the installed platform sync and Node boundary sources also agree. Private hub7d45259ca46535f2bd69feef47d47d1e0f629f0b adds the final deployment regression checks; runtime code remains the deployed library26 version below.

The installer now copies dependency metadata with the daemon shim. Fresh/upgrade cases previously failed; final Mac deployment checks pass51/0/0 and installed device44/0/1. The device skip is the seven Mac-side installer restart checks, which pass on the Mac. Stale staged main.py and BOUNDARY.md were reconciled. Five support/test files changed, with exact backups at /home/openhome/astral-voice/platform-hardening/install-manifest-v2. Services,46 protected hashes and14%/160% audio levels were preserved.

Existing device-key SDK access returns200 for Astral595324. Its explicit matching_capabilities list is empty; this is separate from17 globally installed/enabled abilities. Management-list access with the device key returns401 and needs its session mode. Safari is authenticated and usable outside the saved draft, whose resume remains blank. No account upload/assignment or hosted inference occurred. No new account or GPT-app sign-in is needed.

Installation agreement is verified for this snapshot. Remaining account integration, human voice/app acceptance, broader semantic coverage and final publication are still open.

## Historical deployment — September 5, 2026, 16:11 HST

Private hub879a0444d9c984072d4b10aafc923b373c0835e8 is deployed. All109 installer-selected Python files match the local source. E13 prevents the diagnostic soak from touching persistent state or hardware; E14 preserves complete subtitle text; E15 preserves PDF printed-page labels and technical code. The schema26 index retains191 physical sources and now contains412,863 passages. Four visually checked PDF pages pass17 selected live-index predicates; this is bounded semantic evidence.

Affected final Mac checks passed202/0/1, staged device library/pages221/0/0, installed isolation3/3 and postactivation native answers3/3. These runs overlap. VoicePID72284 has a capture child; bridgePID72285 is active. All46 protected hashes and speaker14%/mic160% levels were preserved. Rollback lives at /home/openhome/astral-voice/platform-hardening/library26-v1/rollback.

The earlier one-hour observer completed183/183 native answers with zero detector issues, before this library migration. It does not prove human audibility or a final-library26 acoustic soak. Existing Safari account authentication is confirmed; no new account or GPT-app login is needed. Astral ability registration/assignment remains unfinished, with its draft opening blank. Human voice/app acceptance, remaining coverage and final publication remain open. Later local commits are not yet pushed; published kernel2.2.3 bytes are unchanged.

The earlier dated snapshots below retain their historical counts and pending statements.

## Room speech and fallback commands — September 5, 2026, 15:02 HST

The running service exposed an additional failure: ordinary room speech containing
an embedded device verb passed the registry's question-only guard. A stale referent
then made the fallback control reply worse. Private hub6476322 fixes the imperative
boundary and checks original intent before device-pronoun substitution. Polite
split-particle commands and legitimate turn-it-off follow-ups are preserved.

The installed focused checks passed24/0/0. Affected Mac suites passed463/0/4 and
staged device suites477/0/2; counts overlap. Voice restarted asPID68707 with its
parec capture child. All46 protected hashes and14/160 audio levels were unchanged;
other services stayed running. A one-hour runtime observer began15:02:25 HST.
Its result remains pending and will not stand in for human acoustic acceptance.


## Account package and control boundary — September 5, 2026

The [control-socket restriction](deploy/PLATFORM-BOUNDARY.md) is deployed. The previous
root wildcard websocket exposed its API-key field to unauthenticated LAN connections.
LAN access is now refused; foreign browser origins and Host headers are rejected.
Oversized frames no longer crash the connection handler. Five live boundary checks
and three native answer checks passed; all46 protected hashes, three user services
and14/160 audio levels were unchanged. Prior key exposure needs owner rotation.

The foreground README now constructs a validated seven-file ZIP and explains separate
CLI metadata. Mock upload proves only file/argument handling. Safari's existing Astral
draft opened a blank workspace on resume; no draft was replaced or uploaded. Actual
platform, voice/app and soak acceptance remains open.


## Native deadlines — September 5, 2026, 13:36 HST

The native shim now gives answer-plus-offer one 12-second budget and reserves reply
time under the wrapper's 15-second timeout. Named routes use the same upper allowance.
Exhausted work returns an explicit timeout instead of silence. The background source
wait is corrected from six to 20 seconds; its account-side deployment is still pending.
The device's affected checks held156 with zero failures/skips. A final90-call warm
native run returned every answer correctly at181.72–201.62ms medians; ten concurrent
calls also passed. All46 protected hashes and service PIDs were unchanged. No service
restart or compiled-package rebuild was needed for this correction.

## Native startup optimization — September 5, 2026, 13:19 HST

The [owner bridge](deploy/OWNER-BRIDGE.md) is deployed and enabled. The same 90 warm
native requests retained correct answers while median latency fell from 605–616 ms
to 181–200 ms. Ten simultaneous requests also returned their own correct answers.
The new owner service passed actual socket, absent-service fallback and restart
checks; its dated PID is 52461. Voice PID 19661 and Slate PID 19580 were unchanged.
All 46 protected state/configuration/sound hashes remained unchanged.

Affected device suites held 448 checks, zero failed, one Mac-only skip. The final
Mac integration run held 152, zero failed, two device-covered skips. The installer
now carries the boundary document alongside the dependency metadata. Kernel 2.2.3
bytes are unchanged. These are scoped additions to the historical evidence below.
The timeout mismatch was addressed in the follow-up above. The account path, real
voice/app acceptance, broader coverage and sustained-operation checks remain open;
the full goal is not complete.
The creator has signed-in sessions in other browsers. Earlier Mac CLI or GPT-app
login observations do not establish absent account access or a device-work blocker.

## Native platform corrections — September 5, 2026

The [native integration corrections](deploy/PLATFORM-HARDENING.md) are applied on the
DevKit. They cover complete ability dependency metadata, safe staged platform sync,
installation into the actual native interpreter, and independent request scripts in
the node dispatcher. The final sync method passed 19 isolated cases; the dispatcher
passed eight, and four actual local WebSocket checks passed. Owner settings/state were
preserved and the voice/mathematics services were not restarted.

A 90-request warm native-path baseline returned correct answers in every case, with
605–616 ms medians; first observed equation latency was 4.73 seconds. The startup
optimization above follows that baseline. Account deployment,
physical voice/app controls and sustained operation remain open. Historical test totals
below retain their original scope; they are not the count of this new platform audit.


## Earlier deployment — September 5, 2026, 10:19 HST

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
The previously recorded baseline was pushed. Existing 2.2.2 release bytes are unchanged.

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
| DevKit | `openhome@<devkit>`, Raspberry Pi 4, 8 GB, CPython 3.13.5 / Linux aarch64 |
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
deploy/install_v2.sh openhome@<devkit> --start
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

Use the existing authorized account key through an ephemeral CLI environment for account reads. The account-specific registration already exists; do not create a duplicate or delete it to update it.

```sh
openhome validate community/astral
openhome list --json
openhome status jamesmykilastral --json
```

A new registration requires an actual ZIP and an alphanumeric account name; directory-only deploy is invalid. Preserve existing account records and use the supported in-place release update API/editor for updates. Local package validation, typed native calls, assignment read-back and physical voice are distinct acceptance surfaces. Platform voice testing must also respect the local-only inference boundary; do not start a hosted conversation merely to obtain a green result.

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

The the submission was reported by the creator. Its proposed harness bridge and longer
term deterministic-engine ambition remain future work. Separate portfolio products are
not shipped OpenHome functionality. No new the submission was made during this audit.

See [RELEASE.md](RELEASE.md) for artifact provenance and immutable release procedure.
