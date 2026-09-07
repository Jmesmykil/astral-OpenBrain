# Astral, known bugs and limitations

## Current runtime verification — September 6, 2026

The DevKit runs kernel **2.2.6** in both interpreters. The full device run passed **5,200
checks, zero failures, zero skips**; the Mac full run passed **5,189, zero failures, zero
skips**. These runs overlap and must not be added together. `demo.py` on the device: 56
lines, 56 as scripted, median 3 ms. The library index is schema 33 — 577,773 passages
across 191 files, and 1,604 of those passages carry a page number.

There are no skipped checks left on either machine. Every skip that used to be here was a
check that had quietly stopped running, and each one hid something: the maths kernel was
on the Mac all along and the adapter only knew how to start a compiled one; the document
checks skipped AND returned, so the device was the one machine never confirming the README
names the words it wakes to; four hundred hostile sentences were capped at ninety seconds
on the machine where a crash would actually happen; and the wake-phrase checks were gated
on a recogniser that only the listener needs, so the two words this product answers to
went unchecked everywhere.

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

On the device,
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

**Reading a page cost 3.6 seconds on the card, and the device said it could not do it.**
`entries` is an FTS5 table, which indexes words and nothing else, so `WHERE name = ? AND
page = ?` was a scan of all 577,773 rows — and `cast(page as integer)` guaranteed no index
could be used even in principle. Measured on the device: working out which books have pages
took 2,239 ms, finding one page's passages 1,372 ms, the whole question 3,615 ms. A small
indexed table written beside the FTS insert, holding the page and the passage's rowid, makes
both a seek: **3,615 ms to 3.2 ms**. None of it showed on the Mac, where the same code
measures 341 microseconds against a shelf of two books. The class was also measured on no
machine at all — it was never added to `measure_costs` — so `fits("pages")` said "not
measured" everywhere and "what can you do" left page reading out, while the router, which
matches a page question before the ranking gate, was reading pages perfectly well. Only the
spoken account of the device was wrong. A check now fails if any class whose parts are
present on a machine goes unmeasured there.

**The device had been deciding what the Mac can do from a four-day-old file.** Whether to
offer "ask the Mac" is settled by `_offerable()` calling `fits(cls, that_host)`, which
reads the Mac's own measured profile *off the device's card*. Nothing refreshed it. The
copy there listed thirteen classes and did not contain `slate`, so the device was certain
the Mac could not do maths and never once offered to send any there — the cross-machine
half of the ranking was dead and silent about it. The deploy now sends this machine's own
profile every time, and still never sends the device its own: those numbers are only true
where they were measured. `demo.py --lanes` on the device now reads "yes — the Mac:
26 classes".

**The trained wake head, and why it is still not the detector.** It ships in the tree and
is not wired to anything; the Vosk phrase recogniser is what wakes the device. Its own
measured numbers are the argument: on its 0.95 threshold it wakes on 66 of 100 spoken
positives, scores an empty room at 0.55, and false-fires on about 0.0 an hour. A detector
that misses a third of the time is not an improvement on a phrase recogniser that does
not, which is why the custom wake word is V3 work rather than V2 work. These three figures
are read out of `wake/openbrain.npz` and checked against this paragraph, so they cannot
drift apart — and until today they could, because the sentence that stated them had been
removed and the check quietly passed on finding nothing to compare.

**Asked for a joke, it read out an encyclopedia entry about the brain's joke centre.**
Found while measuring latency, which is the only reason anybody said "and tell me a joke"
after "what do the books say about entropy". The follow-up was resolved to "what do the
books say about tell me a joke". The subject swap has always said only a THING may be put
into the old question's place, with the guards written out at length — and the tail
replacement sits above them and returns first, so everything after "and" went in whatever
it was. The silent half was worse than the funny half: "and turn off the lights" and "and
set a timer for five minutes" became book searches, so a command the device can carry out
was swallowed by a lookup that could only fail. What follows "and" is now tested for being
a request in its own right, on the SHAPE of a command rather than its first word, so "set
theory" and "turn signals" are still subjects.

**Where the time goes, measured from the moment the speaker falls silent.** About 5.4
seconds is fixed — end-of-speech detection and whisper — and is the same for every turn.
Everything after it is Piper rendering the whole answer before any sound leaves the
speaker: 3.5 s for "20 percent of 80 is 16", 8.7 s for a passage from the shelf, and 17.4 s
for a 150-word page. First sound is therefore 9.0 s, 14.1 s and 23.0 s. The page LOOKUP is
3 ms; the wait is speech. Nothing plays until the entire wave exists, so a long answer is
not a long answer, it is a long silence. Shortening what a page reads aloud halves it; the
real repair is to play the first sentence while the rest renders, and that is V3 work.

**A title heard through a microphone was refused for not being the title.** Spoken into the
DevKit's own speaker, "what is on page 30 of modern" came back from whisper as "page 30 of
moderate" and was answered "I don't have anything called moderate on the card" — true, and
useless to somebody holding the book. Whisper mishears a title the way it mishears a wake
word, which is why the wake phrase has carried a near-miss list from the beginning. Titles
now get the same, against whatever is on the card: accepted when a word is either close
throughout ("pithon" for "python", 0.83) or shares five opening letters and is reasonably
close ("moderate" for "modern", 0.71) — which still refuses modest, model, morning, piston,
pytorch, notebook and handle.

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

Mac free space recovered to6.35GB at15:40HST; this task deleted no unrelated project files. The source Python handbook contains malformed examples; extraction preserves original author content rather than silently correcting it.

## Historical deployment snapshot — September 5, 2026, 10:19 HST

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

## Earlier verified baseline — September 5, approximately 01:15 HST

Read [HANDOFF.md](HANDOFF.md) for current deployment and verification state. The sections
below this notice are a chronological record; their early “hey mycroft” and forced-mixer
statements are superseded. The current detector recognizes “open brain” and “open home”,
and OpenHome owns audio levels.

The interrupted deployment, stale-wave playback, ambiguous playback results, unsafe
library updates, incomplete rebuilds, route-refusal parsing, hidden hub failures and
restart error reporting have been repaired and deployed. The recovered Britannica
volumes 3 and 29 are indexed; all 29 volume files match the archive checksums. The
verified index snapshot had 191 source files, 35 named sources and 412,826 passages, with no empty
sources or persisted unread warnings. OCR quality and page-number coverage are separate
limits; recovered plain OCR volumes do not provide reliable page labels.

Still open: controlled human wake and interruption tests, the two empty captures in the
September 4 quiet pass, platform login/deployment/assignment and app/reboot audio
persistence. The measured speaker volume was 65 percent, while OpenHome's saved value was 14; the
app must reconcile that setting before reboot persistence can be claimed. Audio files
and levels were preserved during this audit. Kernel 2.2.2 is published, and its exact
requirements download was verified on the DevKit with SHA-256 checking.

Mac full: 4,031 held / 0 failed / 12 skipped. Device full: 4,053 / 0 / 5, all 419 hostile
inputs examined; later changed library/ability/package suites: 316 / 0 / 3. Final license
and installed-package checks: 41 / 0 / 2. The exact root shim separately passed 179 pinned
answers and eight device calls. Mac lint was checked separately and passed. Skip reasons
and limits are in the handoff. These software results do not close physical acceptance.

## Historical ledger

Straight list of what's rough, so nobody's surprised. Split by the two paths.

## Local mode (on-device wake + whisper)

- **No echo cancellation on the HAT.** Astral's own voice can bleed into the mic. Handled with a mic flush plus a cooldown after every listen, but a loud speaker close to the mic can still trip a false wake.
- **Wake fires on any matching sound.** Someone else talking nearby can start a listen, which then comes back empty. No speaker identification yet.
- **Whisper can double or invent a phrase** on noisy or long audio. Handled by collapsing an immediate repeat back to one copy and by stopping the capture on silence, but a noisy room can still give an empty or garbled result.
- **Occasional word or number order garble** ("45 dollars" comes back as "dollars 45"). The deterministic engine is forgiving and still answers most of these.
- **Sometimes misses a spoken command** and comes back empty. Mic quality plus room noise. Say it again and it usually lands.
- **Latency is about 2.5 to 3 seconds** per command. That's whisper base.en on the Pi 4.
- **The wake word is "hey mycroft". "Open Brain" is built but does not ship, and here is
  why.** A classifier for it is trained by `wake/train_openbrain.py` from 216
  positive clips and 450 negatives, and on paper it looked usable: about two thirds of
  held-out voices detected at a 0.2% false-fire rate. Then it was graded against ninety
  seconds of this room, recorded through this microphone at the gain the device actually
  runs at. It scores **0.999 where its threshold is 0.95**. It wakes at the room.
  That is not a hypothetical. Before the gate existed, the device woke **102 times in one
  evening, every one of them attributed to "open brain", 82 of them into a room where the
  loudest thing was 20 out of 32767**, and several of the non-silent ones transcribed the
  household's conversation rather than a command.
  The cause is the corpus, not the classifier. The 216 positives are macOS `say` voices, so
  the model learned to tell synthetic speech from synthetic noise, which is not the job.
  `wake_openbrain.load()` now refuses any model that was not graded against real room audio,
  so this cannot be switched on by forgetting. Getting the product wake word working needs
  real recorded people saying it in this house, or Picovoice Porcupine with a free key.

## Native ability mode (through the agent)

- **Speech-to-text is the agent's**, so in this mode the transcript comes from the cloud. The fully local path is the mode above.
- **Skipping the LLM depends on the platform.** The answer runs on the device, but whether the turn returns without an LLM call rides on the hardware-ability-before-LLM path.
- **Device timezone must be set** for time and date to be right. The DevKit image shipped Asia/Karachi.

## Engine

- **The deterministic set is bounded on purpose.** It answers time, date, math, money, unit conversions, and telemetry. Anything outside that defers to the agent. Not a bug, but worth stating so expectations are clear.

## Fixed during testing

- Mic capture volume reset to 20 percent by firmware, which made the mic near-silent. Now forced to a working level.
- A ready-loop after a confused capture. Now cools down after every listen.
- A self-reset when one bad capture raised an error. The listen loop now recovers and keeps going instead of crashing.
- Wrong spoken time from the device timezone being off. Now matched to local.
- A bad agent timezone silenced every answer in the cloud Skill, clock or not, because `ZoneInfo(tz)` ran before the router and the error went to the log. Found in review. Now falls back to the local clock and says so in the log.
- The platform comments out `from __future__ import annotations` on upload, which made the Skill require Python 3.10 without saying so. Found in review. No future import anywhere now; the parity test fails on 3.9 if a PEP 604 union comes back.
- The new size answers stole "schwarzschild radius of the sun". Caught by the golden suite before it shipped.

## Speech-to-text limits, measured on the device 2026-08-17

Everything else in this repo is tested on typed text. These two only show up when a
sentence is actually spoken, and neither is a code defect, they are the transcript
arriving wrong, and the engine correctly declines rather than guessing.

**Words that sound like other words.** "Escape velocity of Mars" transcribed as "is
cake velocity of Mars", so nothing matched. Fuzzy-matching the transcript would fix
this case and introduce a worse one, since the whole point is that a match is exact.
A better microphone, a real voice rather than synthesized speech, and the larger
whisper model all reduce it; nothing in this code can.

**Spoken lists of numbers get concatenated.** "Standard deviation of four six eight
ten" transcribed as "Standard deviation of 46810". A five-digit number cannot be split
back into a list without inventing the boundaries, 4 6 8 10 and 46 8 10 and 4 68 10
are all readable from it. So statistics over a spoken list is unreliable by nature.
Typed or dictated-with-pauses input works; a fast spoken list does not.

Six of eight spoken phrases answered end to end through the live ASR path on the
DevKit. The other two failed here, at the transcript, before the engine saw them.

## Device state found on 2026-08-17 while testing acoustically

None of this is code. All of it stops the device working, and none of it shows up in
any test that runs on a laptop.

**The speaker was at 0 percent.** `pactl get-sink-volume` read `0% / -inf dB`. paplay
exited 0, the amp enabled and disabled in dmesg, and nothing came out. Anyone talking
to the DevKit would have heard silence and had no way to tell why. Set to 65 percent to
run the tests; it is not known whether that survives a reboot, and the mic gain is
documented as resetting every boot, so assume this one does too.

**PipeWire exposes no microphone.** `pactl list sources short` returns one
source and it is the output monitor. The hardware is fine. ALSA shows the Google
voiceHAT capture device on card 2, so anything recording through PulseAudio or
PipeWire gets nothing while `arecord -D plughw:2,0` works normally. The voiceHAT also
exposes no mixer controls at all, so there is no software capture gain to raise.

**RETRACTED, whisper does not invent sentences from silence.** This entry previously
claimed whisper hallucinated "There's a reason so much of our personal information ends
up happening. Data brokers make billions collecting and selling data." from a silent
room. The room was not silent. A video was playing nearby and the DevKit microphone
picked it up; whisper transcribed it correctly. The same file transcribes as
"centralized company this video", which is plainly the video, and a quiet
room recorded afterwards transcribes as nothing at all. The claim was wrong and the
measurement that produced it was contaminated.

**The finding underneath it: the microphone hears the room, including whatever
media is playing in it.** An always-on device three feet from a TV or a laptop gets a
continuous stream of fluent, confident, word-perfect speech that no human in
the room said. Nothing downstream can distinguish that from a user turn, and a capture
level gate does not help, because the television is loud. This is why the wake word
matters more than it looks: it is the only thing standing between ambient media and the
agent. Astral itself is safe by construction, it declines anything that is not an
exact-answer question, but the turn still gets taken.

**The wake word is still hey_mycroft.** The product wake word is Open Brain and there
is no model for it. openWakeWord ships pretrained models only, alexa, hey_jarvis,
hey_mycroft, hey_marvin, timer, so Open Brain needs either a trained custom
openWakeWord model or Picovoice Porcupine with a free key. Testing on hey_mycroft
proves the detection path, not the keyword.

**piper shipped without the execute bit.** `~/astral-voice/tts/piper/piper` was not
executable, so text-to-speech failed with PermissionError until chmod +x.

## What is now proven acoustically, and what is not

Proven on the hardware, speaker to microphone, no human in the loop: wake detection
fires at 1.000 on a known keyword and 0.000 on both other speech and silence; 7 of 8
spoken phrases answered end to end through real capture and whisper; piper speech plays
audibly and transcribes back word for word.

Not proven: the Open Brain keyword, and the OpenHome agent routing a spoken phrase to
this capability at all, the hotwords live cloud-side, so that cannot be tested until
the capability is registered against the agent.

## The background daemon: what is designed, and what a room has to settle

`community/astral/background.py` takes turns without a trigger word by polling the live
transcript and preempting with `send_interrupt_signal()`. Its logic is tested against a
faked platform (`hub/tests/suite_daemon.py`, 27 checks: which turn it reads, what it
treats as an answer, that it interrupts before it speaks, that it never answers a turn
twice, and that a device error is silence). None of that is a hardware claim. Three
things can only be settled on the device, with a person in the room:

1. **Whether a `background_daemon` ability may call `send_devkit_capability_action` at
   all.** The docs only describe that call from a Local Ability. If a daemon may not make
   it, every call fails, the daemon reads a failed call as "not mine", and it goes silent
   permanently, the failure is invisible rather than loud, which is the wrong direction
   for a bug and the reason it is written down here.
2. **Whether it wins the race.** The agent and the daemon see the same turn together. A
   device answer costs a subprocess and a table lookup; an agent answer costs a round
   trip and speech synthesis, so the daemon should be first by a wide margin. If it is
   not, the interrupt lands mid-sentence and the user hears a stub of the agent before
   the live answer.
3. **`POLL_SECONDS = 0.25`.** The documented background-ability example sleeps 20
   seconds, which is right for an alert and useless for taking a turn. A quarter second
   is a judgement, not a measurement; what it costs on a Pi 4 running the agent has not
   been measured.

The alert half (`due_alerts`) has a smaller unknown: it soft-imports `hooks` from
`~/astral-voice/hub-v2` so there is one timer store rather than two. On a device without
the local hub installed it reports nothing, forever, silently, correct, but
indistinguishable from a broken import.

## The fits table was measured inside the loop, and not every caller is the loop

Every number in `hub/data/costs/` was measured inside a long-lived process, where the
Slate kernel is already resident. The OpenHome ability is not that: the node server runs
it as `sudo python3 devkit_functions.py …`, a fresh process per turn. Measured on the
device, the same question cost 43 seconds twice in a row through that path while the
profile said `cold_start_ms: 1644`, so the ranking believed the class fitted here, and
the honest thing it could do about a 43-second answer was offer to send the question
somewhere else, from a device that can do it.

`hub/slate_server.py` fixes the case that matters by making the kernel shared rather than
per-process (0.6 s through the same path afterwards). The general problem stands: a
profile measured in one process model does not describe another, and nothing in the
measurement records which model it was taken under. `costs.offer()` exists because of
this, it answers "who else could" without consulting the local fit, for a caller that
has already found out the hard way.

Two smaller things that follow from the same service:

- **For about forty seconds after the device boots, exact mathematics says "the maths
  kernel is still starting. Ask me again in a minute."** That is the compile, once per
  restart. It is a true sentence rather than silence, but it is still a minute of a
  product that cannot do the thing it advertises.
- **The ability runs as root and the hub does not.** Every hub path resolves from the
  home directory, so as root they resolve into `/root`: measured on the device, three
  questions that answer as the openhome account answer nothing as root, while the fits
  table still reports the data as available. The ability crosses back with `sudo -u
  openhome` for this reason, and a hub file written as root would stop being
  writable by the loop that owns it, one root-owned `smalltalk.sqlite` was created this
  way during measurement and had to be given back.

## The kernel: what is settled, and what is not

`hub/build_kernel.py` compiles the engine into `astral-kernel`, a wheel whose only
contents are a 6 MB shared object and a nine-line `__init__.py`. Verified on the device:
181 of 181 byte-contract phrases answer identically through the compiled kernel, and the
wheel contains no `.pyx` and no source.

Three things about it are not settled, and all three are visible rather than silent:

- **Distribution.** `requirements.txt` names `astral-kernel>=2.1.0`; nothing publishes it
  yet. A DevKit with the local hub does not need it; a DevKit with neither hub nor wheel
  says "the Astral engine is not installed on this device" out loud. Publishing it. PyPI,
  a release URL, a private index, is the author's decision and is not made here.
- **One wheel per interpreter and architecture.** The DevKit is CPython 3.13 on aarch64.
  A different Python or a different machine needs its own build. This is a property of
  compiled code; the loader reports it rather than failing in silence.
- **Two interpreters on one device.** The ability runs under system python as root; the
  loop and the tests run in the venv. Installing into one of them left the other with a
  kernel that had never heard of an entry point added that afternoon, and nothing
  anywhere said so. The deploy now installs into both, rebuilds a wheel older than its
  sources, and reinstalls a kernel older than its wheel, and the suite fails if the
  version it imports is not the version last built on that machine.

**What is NOT claimed.** A compiled extension is machine code, not source: there is no
Python in the wheel to read. It is not unbreakable, anything that runs can be reverse
engineered by somebody determined enough, and it is not obfuscation theatre. It is the
same protection every compiled commercial library has, arranged the way this platform's
own documentation says dependencies arrive.

## The local model: what it is for, and what it did

The second rung of the ladder is real now, llama.cpp built on the device, Llama 3.2 1B
and 3B (Q4_K_M) on the card, and everything about it is offered rather than assumed,
because everything about it is expensive or unreliable or both.

**Measured on the Pi 4, not estimated.** The 3B reads a prompt at 2.5 tokens a second and
writes at 1.3: a sixty-token answer is a minute and a half. The 1B reads at 9.8 and writes
at 3.6, and the model is loaded off the SD card every time, which is most of the wait, 60
seconds end to end for a two-sentence rewrite. The offer quotes the measured number,
loading included, because a promise of "half a minute" that takes a minute is the kind of
small lie that makes a device feel broken.

**It invents things, and it is caught doing it.** Asked to rewrite one sentence, "Turing
machines were first introduced independently by Turing and Post in 1936", the 1B answered
"Alan Turing and Stephen Cook" on one run and "Alan Turing and Alan Post" on the next.
Neither name is in the passage. So every model answer is now checked against the passage
it was given: any name or number in the answer that is not in the source is a fabrication,
and the answer is refused out loud, *"The model added something the passage doesn't say , 
Stephen, so I won't read you its version."* The mechanical summary, which is the
passage's own sentences, has already been spoken and is still true.

**It is only offered for the ONE thing it does well.** `costs.MODEL_CLASSES` holds
summarising and nothing else, and that was decided by measurement rather than taste.
Rewriting a mechanical summary works: given three sentences about Turing machines it
produced two clearer ones that said the same thing. Answering an open question does not,
even with perfect retrieval, handed a passage beginning "Smart pointers are pointers that
own the object they point to and automatically delete it", the 1B replied that the text did
not mention smart pointers; asked about the laws of physics it looped, "the study of the
laws of society will be the study of the laws of society". Several prompt shapes were
tried, on the device, and the shape was not the problem. A rung that answers badly is
worse than a rung that is not there, because somebody has to spend a minute to find out. It is never offered for arithmetic, algebra or anything with one
right answer: those have exact kernels, and a model that is merely fluent about them is
worse than silence. Before that rule existed, the ranking offered a 1B model as a way to
integrate x squared.

**What is not done:** nothing keeps the model resident, so every use pays the load. A
resident server, the shape `slate_server.py` already uses, would remove most of the
wait, at the cost of about a gigabyte held permanently.

## The reader answers some questions with the question

MECH's reader sometimes hands the question back rearranged: "what are the laws of
physics" came back as *"What about the physics and law?"*, and "turn on the kitchen light"
as *"What about the kitchen and light?"*. That is no answer, and speaking it is worse
than silence because it sounds like the device was not listening.

The router now refuses an "answer" that both asks a question and says nothing the question
did not already say, and hands the turn up the ladder instead. What that exposes is the
reader's real limit: it answers definitional questions well ("what is a lighthouse") and
open ones poorly. That is a MECH question, not a routing one, and it is still open.


## The compiled kernel disagrees with its own source on three phrases (2026-09-03)

`astral_kernel.answer()` and `engine.answer()` give different answers for three
of the 181 phrases the suite checks, all of them arithmetic said in words:

```
convert ten pounds to kilograms   engine: 10 pounds is 4.54 kilograms.
                                  kernel: 1 pounds is 0.45 kilograms.
minus four plus ten               engine: -4 plus 10 is 6.        kernel: None
fifteen plus twenty seven         engine: 15 plus 27 is 42.       kernel: None
```

**What has been ruled out.** The installed extension is byte-identical to the newest
wheel (sha256 `62cca876dd21c181`), the wheel was built at 04:20 from the current sources,
and the generated `_engine.pyx` contains calc's number-word table, four occurrences of
"fifteen", the same as `calc.py`. So this is not a stale artifact, not a stale install,
and not a missing module. Cython was also found missing for the system interpreter while
present in the venv, which is why the deploy's build had been silently skipping for some
time; that is fixed by building with the venv interpreter, and it did not cause this.

**What it affects.** The OpenHome ability path only. On the device the hub answers first
and the kernel is the fallback for when the hub is not running, so a person talking to
the DevKit never sees it. It matters for the shipped ability, and it matters because two
things that are supposed to be the same thing are not.

**Where to look next.** `build_ability.build_block()` transforms the source it splices , 
renames `engine.answer` to `astral_answer`, strips markers, and skips formatting. The
next step is to diff the spliced calc block against `calc.py` line by line, and to check
whether the compiled module's regex alternation survives the transform with its
longest-first ordering intact: "ten" answering as 1 looks like an alternation
matching a shorter branch first.

## Open, as of 2026-09-03 05:45

Measured, reproducible, and not fixed. Each one is here because it is better written down
than remembered.

**1. The wake word wakes about three times an hour in a quiet room.** MEASURED, 2026-09-03
06:00 to 06:20 on the DevKit in the owner's room with nobody speaking: 20 minutes, one
wake, 3.0 per hour. That is the number any trained model has to beat, and it is the honest
figure to quote rather than the 38% below, which mixes false wakes with a person saying
the wake word and then pausing, the log carries no timestamps, so the two cannot be
separated after the fact.

**1a. The one thing blocking a better wake word is five minutes of your voice.** The
research report and the failed attempt agree: thirty to a hundred takes on the microphone
that will actually listen are worth more than ten thousand synthetic clips, and the model
trained without them scored 0.999 against its own threshold and would have woken at
nothing. `hub/wake_takes.py` collects them, forty takes across seven conditions (close,
across the room, quiet, fast, slow, turned away, with noise), about five minutes, silent
takes measured and dropped as they happen:

    python3 wake_takes.py                    # on the device
    python3 wake_takes.py --review           # what has been recorded so far
    python3 wake_takes.py --phrase "hey astral"

Until those exist, training is the same experiment that already failed once, and the vosk
phrase recogniser at 3.0 false wakes an hour stays.

**1b. Thirty-eight percent of wakes produce no words.** Of 480 wake events in one evening's
log, 182 were followed by a burst with nothing usable in it. Some of those are a person
saying the wake word and then pausing, which is correct behaviour; the rest are false
wakes. The log carries no timestamps, so the two cannot be separated after the fact, and a
controlled quiet-room measurement is the only way to get the live number. That measurement
is the right next step before any work on a trained wake model, because it is the number a
trained model has to beat, and the last attempt at one scored 0.999 against its own
threshold and would have woken at nothing.

**2. The reader's corpus contains web-development text.** MECH answered "when did the
roman empire fall" with "Roman installed helvetica", and "whats the weather" with "Weather
is towards the side exposed to wind". Both are now routed away, history and absent
capabilities are answered before the reader sees them, but the corpus itself is a
separate product's data and still holds material like that. Anything that reaches tier two
can still produce a sentence of it.

**3. PARTLY FIXED 2026-09-03. Avicenna yes, Ada Lovelace no.** Two names answered with a gloss, "who is Avicenna" and "who is
Ada Lovelace" both returned "…is a name for a particular person, place, or thing" while
Britannica had articles on each. The cause was an optional article written `(?:a|an|the)?`
in the question pattern, which matched the first LETTER of the name: the device was
looking up "vicenna" and "da Lovelace". Both now answer from the encyclopedia. Written up
because it is the second bug of this shape tonight, the first was
`.strip(" ,.of")` eating the o from "osmosis".

**3b. Was: two names still get a gloss.** "Who is Ada Lovelace" and "who is Avicenna" answer
"…is a name for a particular person, place, or thing", because the encyclopedia passage
that mentions them does not contain the surname as a separate word for the containment
check to find. The check exists to stop a Python manual being offered as an answer about
Ada Lovelace, which it did. A better rule would score the passage rather than require a
word.

**4. Britannica has no page numbers, and cannot get them from this download.** INVESTIGATED
2026-09-03, so that nobody repeats it. Every text format in the archive was checked:

  `_hocr_searchtext.txt.gz`   the text on the card. 8.1 MB per volume, ZERO form feeds.
  `_djvu.txt`                 8 volumes have it. 8-9 MB each, ZERO form feeds.
  `_hocr.html`                11 volumes have it. `file` reports "data", corrupt.
  `_hocr_pageindex.json.gz`   969 spans per volume, and they LOOK like the answer: four
                              numbers per page, the last two being character offsets. They
                              are offsets into the hOCR HTML, not into the search text , 
                              the sixth page already ends at character 213,761 of an 8.1 MB
                              file, and rebuilding against the search text produced fifty
                              enormous "pages" per volume instead of 969. Attempted and
                              discarded.
  `_page_numbers.json`        the printed number for each of the 969 leaves, and correct , 
                              but useless without a way to split the text into leaves.

So the passages have no page to belong to, and the device says so rather than
guessing. Fixing it means fetching the volumes in a format that carries page breaks. PDF
or DjVu proper, which is a download, not a code change. The two books that ARE PDFs have
real page numbers and answer page questions correctly today.

**5. Britannica volume 29 is unreadable.** Its gzip is corrupt at the source, not
truncated, so nothing can be recovered from this copy. It is reported by name as unread
rather than silently dropped. Volume 3 was truncated and 1,236,485 words of it were
recovered.

**6. FIXED 2026-09-03.** The compiled kernel disagreed with its source on three phrases.
Cause: every module is spliced into ONE namespace to build the kernel, and `hooks`'
`_TENS`/`_ONES`, added the same night to hear "twenty five minutes", silently replaced
`calc`'s far larger number tables. The kernel read "ten pounds" as one pound and could not
parse "fifteen plus twenty seven", while `calc.handle` answered both correctly. Renamed to
`_HOOK_TENS`/`_HOOK_ONES`, and there is now a check that fails when any two spliced
modules define the same top-level name. The check was proved red against two throwaway
modules before being trusted.

One operational lesson worth keeping: DEPLOY BEFORE YOU REBUILD. The kernel was rebuilt
from the device's older copy of the sources, and the fix appeared not to work for a whole
round of investigation.

## 2026-09-03, the premortem before the meeting

An adversarial pass with five auditors, each finding reproduced or killed by a second
auditor on the device. 57 findings, 24 verified, 13 reproduced. What it changed, and
what it could not.

**The one that explains the rest.** The loop on the device had been running the 07:59
code all morning: `install_v2.sh` copies files and never restarted the service, so every
fix of the day was on the card and none of it was running. That is the shape of "you
keep claiming it's ready and I keep catching problems." The deploy now restarts a loop it
finds running. The restart branch is committed but has not yet been exercised by a real
deploy, the one run since found the loop already stopped.

**Fixed and proved on the device** (`~/astral-checks/zz_evidence.py`, 22 of 23 sentences
now answered correctly, the 23rd, "dim the bedroom lights", is an honest refusal for a
house with no hub): onboarding crashed before its microphone existed; "I'm starving"
overwrote the owner's name; any sentence with "in Spanish" switched the language for
good; "how do I stop hiccups" and "stop the bleeding" were device commands; "what is a
neural network" read out the IP address; "what sound does a cow make" was a chime
setting; "where is Paris" was a C++ page list; "who was the first person on the moon" was
fifty seconds of Python homework; passages ended mid-clause; "why didn't that work" said
"kernel had no answer"; nothing could make it louder; "the pan is on fire" got silence;
"I don't want you to take notes" started taking notes; saying no to being remembered was
ignored after giving a name; a docs-only reindex across a version change would have
deleted the whole library; a test run armed a real 8 pm alarm and set the speaker to 100%.

**Open, and not fixable before Monday without his voice.** The phrase recogniser wakes on
a television: 34 wakes in a few minutes of one evening, each a chime at the room. The
wake chime is now withheld after three false wakes in a row and returns on the next real
answer, deployed at 11:02, not yet observed against room audio, because the room went
quiet. The lasting fix is a trained wake model from his own takes (`wake_takes.py`).

**Not audited.** The auditor checking the 682 written facts for accuracy was blocked by
a content filter and never ran. The facts have not been independently checked.

**Loudness, measured 2026-09-03 at the HAT's own microphone.** There were three gain paths:
chimes through mpv with a 170% boost, speech through aplay with none, the tick at 62, all on
a sink that swung between 40% and 100% in one day. Now the sink is the master (what
"louder", "quieter" and "set the volume to sixty" move; remembered in settings and applied
at boot) and chime, tick and speech are relatives on one scale through one player. Peaks at
the microphone, relatives at 100, room floor 1,469:

| master | chime peak | speech peak |
|---|---|---|
| 50% | 5,715 | 6,451 |
| 65% | 12,471 | 14,207 |
| 80% | 14,089 | 19,404 |
| 100% | 14,905 | 26,119 |

Peak-matched chimes sounded quiet to the owner, a short transient at the same peak as a
sustained voice is heard as quieter, so chimes and the tick carry a fixed 1.5× lift that
speech never gets. Shipped at master 100, chimes 100, tick 100, speech 100. The number
that is still his to set by ear is the master.

**Later the same day, after the owner's own tests.**

- **The demo, out loud, triggered by voice.** "Open brain. Run the demo." was synthesised
  and played into the room through the device's own speaker; the loop woke on it,
  transcribed "run the demo", and ran the twelve-line spoken demo. Evidence: the device's
  final speech file, transcribed by its own whisper, *"that was twelve questions in three
  minutes and fifty seconds, all of them answered here on this card with nothing sent
  anywhere."* Three minutes fifty because the device suite was running alongside it.
- **The master volume has two owners.** OpenHome's node server sets the speaker to its own
  default every time it starts, and this loop was setting a remembered number at boot, so
  the volume changed by itself eight times in one day. Only a person moves it now, "louder",
  "quieter", "set the volume to sixty", or the app, and the loop never touches it at boot.
  Chime, tick and speech are fixed proportions of it (chimes and the tick with a 1.5× lift,
  speech at unity). Shipped at master 65, chimes 70, tick 70, speech 100.
- **OpenHome's services were stopped for nine hours.** The node server and the companion-app
  client were stopped at 03:37 while chasing a greeting bug, and the app could not see the
  device until they were started again at 12:28. Both stacks now run together and both read
  the microphone; "open home" wakes both, "open brain" wakes only this loop.
- **"We last spoke four hours ago."** Filing was made strict, a real question, really
  answered, and the greeting read the last filed subject as the last conversation. Any
  answered turn now moves the timestamp without filing anything.
- **Two stale suite files shadowed the corrected checks on the device.** Pushes had put
  `suite_kernels.py` and `suite_voice.py` in the hub root, and the runner imported them ahead
  of `tests/`. The device count reported earlier today (3,583 held, 2 failed) ran those two
  stale suites; the runner now puts `tests/` first and refuses a shadowed suite, and the full
  device run is being repeated. Mac: 3,571 checks, 0 failed.

**Later still, 2026-09-03, after "the volume is all over the place" and "find a way".**

- **The sounds were never at one level.** Measured on the device as RMS of a 16-bit sample:
  the wake chime 16,862, dismiss 13,585, accept 10,262, the tick 5,776, the ready tune 3,146,
  and speech about 4,500 while peaking at full scale, five to one between loudest and
  quietest before any setting touched them, which is why no setting could make them
  consistent. Every file and every sentence is now brought to one target level before its
  relative and the chime lift apply (proved: every chime at 6,750, sentences at 3,900 to
  4,500). Shipped at master 65, chimes 70, tick 70, speech 100; only a person moves the
  master, and OpenHome's own playback file is written with the same number.
- **The demo was resetting the settings.** Its end-of-run restore wrote back everything it
  captured at the start, over anything set while it ran. It now puts back only the chime
  and tick relatives its own lines change, and only if nobody else has touched them since.
- **The facts, audited by hand.** Two agents sent to check the 682 facts were blocked by a
  content filter on their own output, so all twenty files were read and every claim judged.
  Thirty were corrected: eight outright wrong (a glacier border credited to Norway and
  Sweden; an hourglass "weighing less"; synaesthesia at one in ten thousand; J as the only
  letter absent from element names; an octopus with two hearts stopping; a blue-whale
  artery a child could crawl through; milk "pasteurised in the 1860s"; the railway-gauge
  myth stated in history and debunked in engineering), the rest over-certain. The facts
  suite still holds at 2,123.
- **The device suite's stall, found and fixed.** It stopped after `barge`, in `daemon`: that
  suite imports the ability's background module in-process, which started a maths kernel
  of its own and waited up to three minutes for it behind orphan kernels from earlier
  killed runs. Where a kernel server exists, nothing spawns a second kernel now, and the
  daemon suite runs on the device in a third of a second.
- **The Python crashes on the Mac are not this project.** Every crash report from the
  afternoon is Homebrew Python 3.13 dying inside `pysplishsplash` (an SPH fluid library),
  launched from a Terminal shell by the SlimeShot fluid campaign running on the same
  machine. This project's checks run under Xcode's Python 3.9 and none has crashed.

**Evening, 2026-09-03.**

- **Power was cut at about 13:28; clean boot at 15:33, 37.9 °C.** The voice loop was not
  enabled to start at boot. OpenHome's services and the maths kernel came up, the loop did
  not. Enabled now; it starts with the device. OpenHome's node server sets the speaker to
  38 percent at every boot; the loop applies the owner's remembered master once, at boot,
  and never again during the run.
- **Sound packs.** OpenHome's house set is the default. The `astral` pack is real recordings
, one drop cut from a Commons recording (CC BY-SA 4.0), a struck glass from Freesound
  (CC0), attributions in `data/sounds/astral/LICENSES.txt`, copied onto the card; the
  synthesised version stays only as a fallback. Any folder dropped into `sounds/packs/` is a
  pack. Chosen by voice: "use the astral sounds".
- **Before a slow answer it says a line**, "I'll think about that", "Hold on", "I'm looking",
  "Let me think", then ticks. Summaries and code explanations count as slow whatever the
  profile measured. A background errand ticks at a third of the tick level and any speech
  stops it. Mid-conversation, a statement addressed to it is acknowledged, "Yeah", "OK",
  "I understand", at most once every six seconds, never on a wake-word turn.
- **False wakes, live.** With a video playing near the device in the afternoon it woke a
  handful of times, each dismissed with the tone; the chime-withholding after three in a
  row was never reached, so it remains deployed but unobserved. Quiet room: zero wakes in
  the twenty minutes after the 15:59 restart.
- **Mac: 3,590 checks, 0 failed.** The device count is being produced by a detached run on
  the Pi and goes here with its date when it lands.

**The DevKit count, 2026-09-03 evening.** Every suite run on the device, one at a time,
each under a five-minute cap so a stall would be named rather than waited on:

| suite | held | failed | skipped | seconds |
|---|---|---|---|---|
| answers 222 · kernels 20 · ranking 66 · classes 43 · meta 55 · study 41 · library 167 · notes 46 · conversation 50 · voice 98 · duplex 11 · barge 11 · daemon 32 · ability 30 · clouds 33 · languages 69 · settings 30 · facts 2,123 · fun 202 · memory 88 · lanes 43 · pages 28 · wake_takes 14 · shipped 22 · honesty 22 | 3,566 | 0 | 5 | 118 in all, kernels 46 |
| silence | 70 | 0 | 2 | 107 |

**3,636 held, 0 failed, 7 skipped, 26 suites.** The one that had looked like a hang all day
was `silence`: 420 hostile sentences through the router, a third of a second on a Mac with
no index and fifteen minutes on the DevKit where each can reach the library. It has a
ninety-second deadline now and says how many it covered. The earlier stalls after `barge`
were that, plus checks spawning a second maths kernel, both fixed above.

## 2026-09-03, evening, the ear was two seconds behind the room; locked in at 18:00

Found while running the demo under scrutiny (12 of 12 lines answered, 216 s, settings,
hooks, notes and memory unchanged) and chasing "interruption is not working":

- **The microphone ran two seconds late.** `parec` opened with no stated latency gets
  pipewire-pulse's default record fragment, two seconds. Measured: a sound played after a
  flush was heard 2.00 s later, whatever the pipe size or backlog. Every wake phrase,
  every interruption and every "flush" acted on the room as it was two seconds ago , 
  which is why the device kept talking after "open brain", why a flush after speaking
  could not stop it hearing its own tail as a wake ('the open floor' after "It's 5:13
  pm"), and why the burst after a barge held its own words. With `--latency-msec=50` the
  same sound is heard 0.66 s after its player is *launched* (the player's start-up), with
  or without eight seconds unread. The pipe is widened to 1 MB so a flush really empties
  it: with the 64 KB default, 7.9 s of stale audio arrived in the second after a flush.
- **Barge-in is qualified, and a false one is harmless.** A wake matched while the device
  speaks counts only if the last 0.8 s at the microphone is above 1200 RMS (its own echo
  measures 982 median, 3151 at the 90th percentile, and produced no wake match in 18 s
  through a ready recogniser). A barge that comes to nothing, nothing usable, not a
  request, the wrong language, finishes the sentence from right before the cut instead
  of losing it. Three false wakes in a row switch barging off until a real answer. The
  recogniser is reset after every uninterrupted sentence, and whatever queued on the
  microphone while the voice was being made is dropped before it plays.
- **What barge-in cannot do without echo cancellation.** With the interrupter played from
  the device's own speaker over its own speech at equal loudness, the recogniser caught
  "open brain" in the controlled trial (1.2 s after the phrase began) but not inside the
  loop, where speech plays at the trim gain (louder). A person has to be louder by a clear margin
  than the device to interrupt it. PipeWire's `module-echo-cancel` with WebRTC is
  installed on the DevKit; loaded at runtime it creates `ec_source`/`ec_sink`, but under
  the pro-audio profile the source delivered zeros, the graph needs `pw-link` work
  before it is usable. Not shipped; the path is known.
- **The owner's verdict at 18:00: "the audio is perfect, lock it in."** Sink 65 %,
  speech 100, chime 70, tick 70, parec at 50 ms, 1 MB pipe. Frozen as deployed;
  hub-v2 on the card is byte-identical to this commit.
- Suites at the lock: Mac 3,607 held, 0 failed; device voice suite under the service's
  interpreter 128 held, 0 failed (the system python has no vosk, and a wake listener
  that is not ready returns None for every frame, an earlier "no match on the echo"
  run was that, not a result).

## 2026-09-04, the morning of the meeting, the boot race, the app's slider, follow-ups

- **The microphone came up at 30 %.** The Pi rebooted at 06:05. Our unit's ExecStartPre
  sets the mic to 160 %, OpenHome's node server sets its 30 % default fifteen seconds
  after boot, and whoever runs last wins. The device heard "open brain, run the demo" at
  peak 112 and threw the burst away as too quiet. The loop now pins the mic from the
  settings at boot (`device.mic`, default 160) the way it pins the speaker, and holds
  both for as long as it runs, reading the settings fresh every five seconds so a
  "louder" said to the device is kept.
- **The speaker moved on its own: 65 → 38 → 43 → 41.** OpenHome's cloud sends
  `set_source_volume` when the speaker slider moves in their app; their client applies
  it to the default sink. The hold puts it back within five seconds and logs
  `[mixer] the speaker was moved to 41 percent by something else; back to 65`. One knob,
  and it is the owner's: change the volume by voice or in settings, not in the app.
- **The ear can come up deaf.** Half the loop starts this morning heard nothing: parec
  attached and running, one error on the input node, bytes flowing (97,966 in 3 s) and
  the recogniser running on them, and no wake ever. A momentary second capture client
  cured it every time. The loop now kicks its own stream once, three seconds after
  opening the microphone, watches for a read that waits more than four seconds or five
  seconds of dead-flat frames, and kicks again (three times at most). It logs
  `[ear] …` when it does and a `[health] mic … sink … room peak … kicks …` line every
  minute, the first live analytics the loop has had.
- **Follow-ups on the open floor were thrown away.** "And in London?" after "what time
  is it in Tokyo" was judged as chatter before context completed it; the completed form
  also doubled the preposition ("in in london") and the unit ("20 milesmiles"). The
  fragment is completed first now, and the resolver replaces the last "<preposition>
  thing" of the previous question. Heard by voice at 06:56: Tokyo, then "and in
  London" → "what time is it in london", then twelve miles, then "and in twenty miles"
  → "how many kilometers in 20 miles", all answered; chatter on the floor still
  dismissed, a follow-up after the floor closed still ignored.
- **The first library question after a cold boot costs 40 s** (the 570 MB index on the
  SD card, read for the first time); the second takes 81 ms. A boot warm-up that read
  the whole file was tried and withdrawn (too heavy while the loop starts). Open.
- **What is not there yet, said plainly:** no stress test, no profile of the ranking
  under load, no live dashboard; the `[health]` line and the demo's timing summary are
  what exists. Echo cancellation is installed but unusable under the pro-audio profile.
- Suites at this commit: Mac 3,630 held, 0 failed; device voice suite under the
  service's interpreter (kws-venv) 141 held, 0 failed.

## 2026-09-04, 08:00, the sweeps before the call: 645 utterances, 88 flows, one voice pass

Fixed and deployed before the call, each with a check proved red first: a filler word in
front of a question ("uh, define osmosis") made the router call it silent, so it went to
the dismiss tone with no words; fillers are stripped before the request test now. "Are
you recording", "is anything sent to the cloud" and their kin answered "I couldn't work
that one out"; they answer with what is true. The device reported the open floor as 8
seconds when it keeps it for 25.

Open, found the same morning and not yet fixed (no crash and no state leak in any of it;
every failure is in what it says or stays silent about):

- "I'm having chest pain", "my chest hurts", "I can't breathe" class as silent and get a
  dismissal tone. The emergency pattern fires on phrasings that ask for help, not on
  symptoms. Widen it, and gate the symptom sentences.
- After "remember me", "my name is Jordan" is dismissed at the gate although the memory
  handler was ready for it; only "call me Jordan" gets through. The gate must ask the
  memory what it can take.
- "Wake me at 6.30" sets an alarm for 6:00 and says so; the half hour is dropped without
  a word. "Remind me to call mum at five" asks when, stores nothing; a reminder that does
  store keeps "This is your reminder" and loses what it was for. "Set an alarm for seven
  am" asks "for what time?" and cannot take the answer. Nothing pending can be asked
  about ("what timers do I have").
- A bare "stop", "stop the quiz" and "how do I pick a lock" reach the device-control
  path and answer with the MQTT sentence. "Never mind", "cancel", "shut up" on the open
  floor close it in silence, with no sign it heard.
- "What time is it New York City" and "what's the time London right now" answer with the
  local time; only the fully formed "what time is it in London" is guarded.
- Arithmetic with an unparsed tail answers the wrong number with full confidence: "one
  billion divided by three" becomes one divided by three, "two plus two times three"
  becomes four, "one plus one sixth" becomes two. The parser must refuse when it did not
  consume the whole sentence.
- Once a fact has been told, "tell me about Antarctica" and "when was he born" can come
  back as a random fact. "What about 15 percent" after "20 percent of 80" resolves to "20
  percent of 15 percent" and is answered.
- "Louder", "quieter", "change the voice" classify silent at the gate while the settings
  handler would have answered; "make it louder" gets through.
- "Why didn't that work" after a reader refusal repeats the refusal instead of the
  reason; "why are you quiet" after a dismissed turn says nothing happened.
- Two questions in one breath answer one of them; non-English on a transcript gets a
  bare tone; "got it", "cool", "nice one" on the floor close it in silence.
- The ear watch's flat-frame rule is a false positive on this HAT: the microphone array
  outputs exact zeros in silence, so "flat audio for five seconds" fires in a quiet
  room and the three kicks per boot are spent in the first fifteen seconds. The
  start-up kick and the no-bytes rule are the useful parts; the flat rule should go.
- From the voice pass on the device the same hour: a turn is 10 to 13 s from the end of
  the question to the answer for the mechanical classes (burst capture until 0.8 s of
  silence, then transcription, then the voice), 18 to 23 s for a tier-2 refusal and its
  "why", 29 s for the first library question after a cold boot. Twice a heard question
  produced no route and no answer, both at the moment the loop was restarted for a
  deploy; not reproduced since. The log records the length of what was said, not the
  words; the answers had to be recovered from the speech file. Two PipeWire stacks run
  after boot (one per session), and a plain ssh shell can bind to the empty one, where
  pactl shows only auto_null; the loop binds to the right one.

## 2026-09-04, after the call

- **Hardware note from OpenHome (OpenHome):** the DevKit's audio cable connections need
  reseating from time to time. That is a candidate cause for the deaf starts and the
  suspended sink seen this week; check the cables first, then the stream.
- **The level hold never ran.** For a day `_hold_levels` raised a NameError on its first
  line (`settings` was imported inside main, not at module level) and a bare except
  swallowed it, so the device booted at mic 30 % and speaker 16 % after every reboot and
  nothing put them back. Fixed: the thread reads the settings through one function, says
  so if it fails, and the gate runs the thread body itself. Proved live: moved to 40/90, back
  to 65/160 in eight seconds with two `[mixer]` lines.
- **The library:** the 65 DK volumes went into `reference/dk/` and indexed in 116 s:
  397,706 entries from 191 sources, a 660 MB index. Two volumes had no text layer (the
  Marvel Comics encyclopedia and the Visual Encyclopedia of Dinosaurs); they need OCR. The
  first library question after the index grew took 50 s cold.
- **Shipping v2:** the kernel wheel is a GitHub release (v2.2.0) and requirements.txt
  installs it by URL; `community/astral/config.json` carries the CLI's schema
  (unique_name, matching_hotwords, category local); the validator in my fork of OpenHome's CLI applied the
  capability-worker rules to devkit_functions.py, which rejects every valid DevKit
  ability including OpenHome's own devkit-stats template, and is fixed on its main
  branch (not yet published to npm). `openhome login`, deploy, assign and the trigger
  registration on agent 595324 are the owner's commands.
- **Roadmap from the call:** tap-to-mute and an emergency off switch honoured by the
  local loop; a screen or mini display; the Hermes/OpenClaw bridge for DIY harnesses.


## 2026-09-04, midday, the sweep fixes merged and the loop shipped

Three review passes ran after the call, each in its own worktree, each defect reproduced
and gated red before its fix. Merged into the hub, whole suite 3,861 checks held, 0
failed, 11 skipped, no tracebacks. Deployed in two pushes.

- **Alarms and reminders.** "Wake me at 6.30" armed 6:00, the decimal dropped. Every
  reminder phrasing asked "When should I remind you?" and one that got through stored
  "This is your reminder." with no content. Alarms were deaf to word numbers ("seven am"
  after "For what time?" got nothing). Nothing pending could be asked about. Fixed, with
  a new `hooks` suite: 69 checks. Only two digits after the dot count as minutes, so
  "a timer for 1.5 hours" is untouched; a time with no am or pm is read as said and
  rolls to tomorrow if passed; a reminder needs a cue (at, around, by) before a clock time
  so "buy one apple" is not 1 am; the pending list is ordered by when things fire.
- **Arithmetic tails and the world clock.** "Three plus four times two" answered the
  first two numbers; "billion" was skipped as an unknown word; "one hundred and fifty plus
  two" was cut at the number's own "and"; "2 point five" raised a ValueError out of the
  engine with no answer and no reason. The whole expression is read now, with times and
  over before plus and minus, and any leftover refuses: "I couldn't read all of that as
  one calculation, so I won't answer part of it." "What is 3 less than 8" used to answer
  "3 minus 8 is -5"; it is silent now and goes to the agent. The clock finds any place it
  knows anywhere after the time word, two places give two clauses, a dangling "in"
  refuses. Answers suite 257 checks.
- **The facts hijack.** "Tell me about antarctica" was answered with a fact about the
  Pacific, and "when was he born" with one about concrete, because a field that merely
  mentioned a word counted as a field about it and names matched on any substring ("he"
  inside chemistry). `facts.filed()` is the one decider: whole words, three letters or
  more, name or alias; an unfiled subject is a miss and is said so.
- **The follow-up resolver fabricated questions.** "What about 15 percent" after "what is
  20 percent of 80" became "what is 20 percent of 15 percent" and answered 3. A follow-up
  that does not fit the open question comes back unchanged and is judged as itself.
- **A verb inside a question was a device command.** "How do I pick a lock" reached the
  registry as lock; a bare "stop" was a command with no device. A question counts as a
  command only when it also reads as an imperative, and a command names the thing it acts on.
- **A bare stop.** With the command path fixed, "stop" alone went on to the reader, which
  on the board is a model replying to the word stop. "Stop the music" was answered with the
  oldest known musical instruments, through the fallback that sends a refused question to
  the books and the facts. Now: a live quiz, timer or notes session claims its own stop;
  with nothing live, "stop", "cancel", "never mind" and "stop reading" get "Okay.", and
  "stop the quiz" with no quiz says there is none. An imperative with a thing after the
  verb no longer becomes a question about the thing. The hub is built with no local runner,
  so a capability it routes to itself speaks its own sentence for not being able and never
  the orchestrator's "[ran state.cancel]" placeholder.
- **Backchannels shut the floor.** "Got it", "cool", "nice one" and "thanks" on the open
  floor were fragments of the room and closed it; "okay thanks" was acknowledged only
  because it starts with ok. A whole sentence that is a backchannel is addressed now, gets
  a person's acknowledgement, and a second one inside the six-second throttle is heard
  without another word instead of shutting the floor.
- **The suite in a worktree.** The `facts` and `fun` suites fail in a fresh checkout with
  "no cost profile measured on mac-16g-arm64": the measured profiles are not tracked, so a
  worktree has none and every class with a cost need goes silent. Not a code defect;
  measuring the host clears it. Worth tracking a profile per host or generating one.
- **A live-state hazard.** `python3 hooks.py <phrases>` wrote three real alarms into the
  card's hooks.json during the review, because the module's own demo path does not set
  ASTRAL_STATE. Fixed the same day: the demo path uses a scratch copy unless told
  otherwise.
- **The kernel suite's fake server** printed a broken-pipe traceback in the slow case
  (the client had already given up). Quieted; it was harness noise, not the product.
- **ssh from the Mac hung again** at the public-key step: the launchd agent socket. The
  deploy script hides the agent; anything ad hoc must too (`SSH_AUTH_SOCK= ssh …`).

- **Music it cannot play.** "Turn off the music" reached the reader on the device, which
  had nothing, so the loop said it could not work that one out. The rule that says what is
  missing listed "turn up the music" and "stop the music" as whole phrases and then
  demanded a second music noun after them, so neither had ever matched either. The verbs
  are plain verbs now (turn on, off, up, down; pause; skip; mute; stop), and all of them
  get "I can't play music, there's no music service on this device" through the same
  sentence "play some jazz" always got. Meta suite 66 checks.
- **Shipped.** Kernel 2.2.1 compiled on the Pi, installed into both interpreters, and
  published as GitHub release v2.2.1; `community/astral/requirements.txt` installs it by
  URL and `openhome validate community/astral` passes. Two deploys, the second for the
  music rule. Verified by text on the device under the loop's own interpreter: stop, the
  quiz, alarms with decimals, reminders with content, the two-place clock, the whole
  expression, Antarctica from the library (554 passages in 11 sources), the follow-up
  resolver, backchannels on the floor.

Open after this pass:

- "And the date" after "what time is it" comes back unglued and is judged silent, so the
  loop plays the dismiss tone rather than reading the date.
- The flat-audio ear rule is a false positive in a quiet room (the HAT gates silence to
  exact zeros); the no-bytes rule and the start-up kick do the protecting.
- The chime pack: only one of the sounds in use is liked; the rest sound like xylophones.

## 2026-09-04, late morning, the levels are OpenHome's and the sounds are mastered

- **The owner's rule:** all volume is mastered on our side and handed to the OpenHome app
  for control; nothing OpenHome has a surface for is hardcoded here. What OpenHome
  surfaces, read from their code on the device: the app's slider sets the speaker (their
  node server runs `pactl set-sink-volume` and persists SPEAKER_VOLUME in ~/.env; in local
  mode the same slider also moves the XMOS playback control through amixer), and their
  boot sets the microphone from MIC_SENSITIVITY in the same file. The app has no slider
  for the microphone. Today that file holds SPEAKER_VOLUME=14 and MIC_SENSITIVITY=30.
- **What changed.** The loop no longer sets the speaker or the microphone at boot and the
  five-second hold is gone; the unit file no longer pins the microphone. After a reboot the
  speaker will be at OpenHome's 14 until the app's slider moves it, and chime, tick and
  speech stay fixed proportions of that. The deploy writes MIC_SENSITIVITY=160 into
  OpenHome's ~/.env once, and only while it still holds their default of 30, because the
  wake was measured deaf at 30 ("open brain, run the demo" at peak 112 on the morning of
  the meeting); a value chosen later, by them or by the owner, is never overwritten. The
  health line names that key when the microphone is below 160, so a quiet ear is loud in
  the log.
- **Measured, and not what the percent says.** Two seconds of room at mic 30, 65, 100 and
  160 percent gave RMS 117, 102, 57 and 572: below 100 the HAT's capture level barely
  moves with the setting, and pulse's reported decibels (12.25 dB at 30 percent, the same
  as at 160) do not describe it either. A software gain derived from the percent would
  have been wrong by an unknown factor, which is why the value went into OpenHome's
  configuration instead of into a formula.
- **Mastered.** The astral pack's cues were levelled at play time to one RMS with a fixed
  lift, which flattens any offsets an author sets. A MASTERED file beside a pack now means
  it is played as authored, and the play-time levelling stays for packs nobody mastered.
  The second edition of the pack, glass struck once per cue in A major with one EQ and
  matched hit loudness (wake 0.213 of full scale over its loudest 0.3 s, ready +2.5 dB,
  accept -1, handoff -2, decline -3, dismiss -7, the drip 9 dB under the old one and 1.9 s
  between drops), was approved by the owner at 10:45 ("its good", after the drop was
  mastered to the set: 6 dB under the wake strike, the same EQ, a crest to match, a clean
  loop point) and is the pack in play on the device: every cue resolves to the new file,
  mastered, no trim and no lift, checked under the loop's own interpreter.
- **The deploy did not carry the pack.** The rsync rules included `data/sounds/` and its
  wav files but not the pack's own directory, so two deploys left the card playing the
  pack from the afternoon before while the pack maker found nothing new to copy. Fixed in
  `deploy/install_v2.sh` and gated: the shipped directory, its licences and its MASTERED
  marker now travel with every deploy. Five deploys today in all; kernel 2.2.1's release
  asset was replaced after each rebuild and downloads back byte for byte.
- **Still not proven by voice since the merges:** wake to whisper to answer to speech,
  barge-in, backchannels on the floor, and the level change itself. The voice pass plays
  test phrases through the device's own speaker and needs the owner's say-so.

## 2026-09-04, afternoon, the ship sweep

The owner's goal: the project perfect, no gaps or conflicts, ready to ship. Everything the
the submission names was opened and checked (every link answers 200, every file is
tracked), and the sweep then went after what the ledger still listed as open.

- **The the submission was audited** against the form's own prompts, the submission
  announcement and the five milestone stages OpenHome lists ((removed)). The public
  repository now carries the MIT licence it had been claiming, RELEASE.md names the 2.2.1
  release, and the application's numbers, links and open-source statement match what a
  reviewer finds.
- **Bare follow-ups.** "And in London" after "what time is it" and "and the date" after it
  came back unchanged and were judged silent, so the loop played the dismiss tone at a
  person mid-conversation. A place onto a question that has no place yet, or one of the
  few nouns the device answers about by itself (date, time, day, year, month, weather,
  temperature), is completed now; "and tomorrow", "and thirty percent" and "and the other
  one" are still left alone for the router to judge.
- **The flat-audio ear rule is retired.** It fired in every quiet room because the HAT
  gates silence to exact zeros, kicked three times and gave up. The no-bytes rule and the
  start-up kick remain, and they are the two that ever caught a real deaf start.
- **What the device says is in the log now** (`[said] …` beside `[heard] …`). Until today
  the log held the question and never the answer, so a pass could not read its answers
  back, and neither could the owner.
- **Two gates from the morning raised on the DevKit.** They read the deploy scripts from
  the Mac's directory layout; on the device one script lives inside the hub and the other
  is not there at all. The voice suite stopped at check 23 on the device (3,689 held, 1
  failed, the rest never ran). They read either layout now, or skip with a reason, proved
  in a device-shaped copy before the deploy. Lesson kept: a gate that reads a file must be
  run in the layout of every host that runs the suite.
- **The device rebooted by itself at 14:58** (their node server's journal: "Setting volume
  to: 14 by default", "Setting sensitivity to: 160 by default"). The hand-off held: the
  microphone came back at 160 from OpenHome's own configuration, and the speaker at their
  14. The loop came up, kicked its ear twice during the seconds before their server applied
  the microphone level, and has answered since. What this means for the owner: after every
  boot the speaker is at whatever the OpenHome app last persisted, and today that is 14,
  which is nearly inaudible. LOCAL_MODE is not set on this device, so the app's slider sets
  the sink and persists it. One move of the slider fixes every boot after. Nothing in this
  project writes that value, by the owner's rule.
- **The first voice pass of the afternoon was invalid for that reason.** Thirteen stimuli
  through the device's own speaker at sink 14 reached the microphone at a peak of about
  700, two of them woke the loop, and whisper transcribed near-silence into sentences
  about "hospital ark" and "numerous posts of pictures", which the loop ignored as chitchat
  with nothing spoken. At sink 65 the same stimulus reaches the microphone in the
  thousands. Lesson kept: check the sink and the self-echo before reading a voice pass.
- **The second voice pass, at sink 65, worked where it was read:** "what time is it" was
  answered, and "and the date" on the open floor was completed to "what is the date" and
  answered with the day and the date, by voice, on the deployed code. The pass finished on
  the device; its full record (~/astral-checks/voice_pass-1553.txt) had not been read back
  when the device went off the network at about 16:00, so the remaining eleven turns are
  recorded there and not yet reviewed.
- **The device is off the network** as of the end of the sweep (no ping, the router
  answers). Left to do when it is back: read the pass record, deploy hub commit a83adc4
  (the greeting reads back subjects, not mishearings), rerun the whole suite on the DevKit
  for its own count, and measure the loop at rest for the README's resource table. The
  code for all of it is committed and pushed; the device runs one commit behind.
- **The second voice pass, read in full (13 turns through the device's own speaker at sink 65).**
  Answered by voice on the deployed code: "what time is it"; "and the date" on the open floor,
  completed to "what is the date"; "what is three plus four times two" (11); "set a timer for
  two minutes"; "what do I have set" ("A timer with 1 minute left"); "what can you do". Not
  transcribed ("heard nothing usable"): "and in London", "got it", "cancel the timer", "tell me
  a riddle", so the timer rang two minutes later. Two turns were contaminated by the owner
  talking in the room, and one mishearing ("stop the music" heard as "is stuff pops out of the
  wall") drew a question back from the comprehension tier instead of a refusal. Open: short
  spoken follow-ups of two or three words through the speaker are lost more often than long
  ones, and a mishearing can reach the reader. Both need a quiet-room pass with a person
  speaking, not the device.
- **The the form.** The corrected answers (the CLI is OpenHome's with one validator fix in
  a fork, the abilities repository is not the applicant's, MECH is a separate product, Slate
  is the engine's lane) are in (removed) and (removed). The browser
  extension disconnected before sections 12, 13, 15, 16, 17 and 18 could be re-entered, so
  the form draft still carries the old wording of those six until they are pasted.
- **The boot greeting reads back subjects, not mishearings.** It said "We were on volcanoes,
  or land is on, entropy" after the 14:58 reboot: a mishearing recorded as a subject was read
  out as a topic. Subjects the greeting says back are now things, not clauses (a name that
  opens with a joining word, holds a verb, or is mostly one-letter tokens is skipped, and the
  next real subject taken). Deployed at 21:07; the first greeting after it read "volcanoes,
  entropy, variables". Nothing stored was changed.
- **The device came back at 16:28 after being plugged in**, and again at 21:07 after the
  deploy: the loop up, the ear kicked at start, the microphone at 160 from OpenHome's
  configuration, the speaker at their 14. The the form holds the corrected answers in
  every section as of 21:08.
- **"Okay stop" took a summary offer as a yes.** Found by the DevKit's own suite run at
  21:10 (3,955 held, 1 failed): on the device, where the model is present, the check that
  expects "okay stop" to get "Okay." got a model summary about tides, because the summary
  offer looked for a yes word anywhere in the reply. The route offer already treated "stop"
  as a no. Acceptance is one predicate now, a yes word with no word against it, so "okay
  stop", "okay never mind", "not now" and "okay wait" never take an offer. Lesson kept: the
  Mac suite cannot see this class, because the model that would answer is absent there. A
  check that passes on the Mac and fails on the device is worth more than either alone.

## 2026-09-04, night, ready to ship

The state at the close of the day, all of it verified rather than assumed.

- **The DevKit suite is green: 3,969 checks held, 0 failed, 6 skipped**, run on the device
  under its own interpreter against the deployed code. The Mac holds 3,910; the device holds
  more because the model and kernel paths are live there and silent on the Mac.
- **The the form is a copy of the source file.** All ten answers were compared section by
  section against (removed) and every length matches to the character. It carries the harness
  bridge as the critical selected feature, the local assistant as phase 1 delivered, and the
  deterministic engine as the road beyond, with the risk stated. Submit is the owner's.
- **Corrected before it went out, on the owner's word:** the OpenHome CLI is OpenHome's, and
  what is his is one commit in his fork, the validator fix; the abilities repository is not
  his; Astral MECH is a separate product from the Astral Brain Engine, and Slate is the
  engine's mathematics lane. The application no longer points a reviewer at a file that lives
  in the private repository either.
- **The ability is ready and not yet deployed.** `openhome validate community/astral` passes.
  The CLI itself had to be rebuilt: the only copy was a global install from a session
  scratchpad, which was wiped. It is back from the owner's fork with the validator fix.
  `openhome login`, `deploy` and `assign` are his commands.
- **The kernel release matches the device.** Release v2.2.1 carries the wheel built on the
  DevKit today, and the download matches it byte for byte.
- **Measured tonight, replacing numbers from August:** the whole loop, listening and idle,
  holds one core at 13 percent and 360 MB, and the Pi sits at 959 MB of 7.9 GB with the loop,
  the resident model and the mathematics kernel all up.

Still open, and honest about it: short spoken follow-ups of two or three words are lost more
often than long ones through the device's own speaker, a mishearing can still reach the
reader, and the speaker comes up at OpenHome's stored volume after every boot until the app
slider is moved once.

## 2026-09-04, 22:00, the quiet-room voice pass and what it found

Six phrases through the device's own speaker at sink 65, in a quiet room, each with the
wake word. This is the pass the earlier note asked for.

- **Short follow-ups are not the problem; the room was.** "And in London" was heard, and
  completed to "what time is it in london" and answered by voice, which is the follow-up
  fix working through the air. The losses in the noisy pass were the room, not the length.
- **"Cancel the timer" was heard correctly and then dropped**, with the log line
  "floor: not for me", while "stop the timer" is answered. The open floor's verb list had
  no cancel. Sweeping what the device answers against what the floor hears found ten such
  sentences, including "convert ten pounds to kilograms", "calculate twelve times nine",
  "mute the music" and "wake me at seven". The gate now asks the handlers the way the
  wake-word gate already did, behind the same twelve-word limit, and the verb list carries
  the verbs the device actually answers. Social verbs are deliberately out: on the open
  floor "call mum" belongs to the person it was said to.
- **A greeting was any sentence with the word in it.** "How do you say hello in french"
  was answered "Good evening.", and so were "translate hello into spanish" and "say hello
  in spanish". A greeting is a sentence that is one now, so "hello what time is it" gets
  the time.
- **hooks answered more than it declared.** "Wake me at seven" set an alarm while
  hooks.matches() said the module took no such sentence, which is why the floor dropped it.
  A gate holds the two together for everything hooks answers.
- Still open from this pass: one stimulus in six was captured at a peak of 1,098 and
  transcribed as nothing, and a second at 8,357 also came back empty. Two empty bursts in
  six turns through the speaker, in a quiet room, is worth another look.

