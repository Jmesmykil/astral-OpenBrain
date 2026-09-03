# Astral — known bugs and limitations

Straight list of what's rough, so nobody's surprised. Split by the two paths.

## Local mode (on-device wake + whisper)

- **No echo cancellation on the HAT.** Astral's own voice can bleed into the mic. Handled with a mic flush plus a cooldown after every listen, but a loud speaker close to the mic can still trip a false wake.
- **Wake fires on any matching sound.** Someone else talking nearby can start a listen, which then comes back empty. No speaker identification yet.
- **Whisper can double or invent a phrase** on noisy or long audio. Handled by collapsing an immediate repeat back to one copy and by stopping the capture on silence, but a noisy room can still give an empty or garbled result.
- **Occasional word or number order garble** ("45 dollars" comes back as "dollars 45"). The deterministic engine is forgiving and still answers most of these.
- **Sometimes misses a clearly spoken command** and comes back empty. Mic quality plus room noise. Say it again and it usually lands.
- **Latency is about 2.5 to 3 seconds** per command. That's whisper base.en on the Pi 4.
- **The wake word is "hey mycroft". "Open Brain" is built but does not ship, and here is
  exactly why.** A classifier for it is trained by `wake/train_openbrain.py` from 216
  positive clips and 450 negatives, and on paper it looked usable: about two thirds of
  held-out voices detected at a 0.2% false-fire rate. Then it was graded against ninety
  seconds of this room, recorded through this microphone at the gain the device actually
  runs at. It scores **0.999 where its threshold is 0.95**. It wakes at the room.
  That is not a hypothetical. Before the gate existed, the device woke **102 times in one
  evening, every one of them attributed to "open brain", 82 of them into a room where the
  loudest thing was 20 out of 32767** — and several of the non-silent ones transcribed the
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
- The platform comments out `from __future__ import annotations` on upload, which made the Skill quietly require Python 3.10. Found in review. No future import anywhere now; the parity test fails on 3.9 if a PEP 604 union comes back.
- The new size answers stole "schwarzschild radius of the sun". Caught by the golden suite before it shipped.

## Speech-to-text limits, measured on the device 2026-08-17

Everything else in this repo is tested on typed text. These two only show up when a
sentence is actually spoken, and neither is a code defect — they are the transcript
arriving wrong, and the engine correctly declines rather than guessing.

**Words that sound like other words.** "Escape velocity of Mars" transcribed as "is
cake velocity of Mars", so nothing matched. Fuzzy-matching the transcript would fix
this case and introduce a worse one, since the whole point is that a match is exact.
A better microphone, a real voice rather than synthesized speech, and the larger
whisper model all reduce it; nothing in this code can.

**Spoken lists of numbers get concatenated.** "Standard deviation of four six eight
ten" transcribed as "Standard deviation of 46810". A five-digit number cannot be split
back into a list without inventing the boundaries — 4 6 8 10 and 46 8 10 and 4 68 10
are all readable from it. So statistics over a spoken list is unreliable by nature.
Typed or dictated-with-pauses input works; a fast spoken list does not.

Six of eight spoken phrases answered end to end through the real ASR path on the
DevKit. The other two failed here, at the transcript, before the engine saw them.

## Device state found on 2026-08-17 while testing acoustically

None of this is code. All of it stops the device working, and none of it shows up in
any test that runs on a laptop.

**The speaker was at 0 percent.** `pactl get-sink-volume` read `0% / -inf dB`. paplay
exited 0, the amp enabled and disabled in dmesg, and nothing came out. Anyone talking
to the DevKit would have heard silence and had no way to tell why. Set to 65 percent to
run the tests; it is not known whether that survives a reboot, and the mic gain is
documented as resetting every boot, so assume this one does too.

**PipeWire exposes no microphone.** `pactl list sources short` returns exactly one
source and it is the output monitor. The hardware is fine — ALSA shows the Google
voiceHAT capture device on card 2 — so anything recording through PulseAudio or
PipeWire gets nothing while `arecord -D plughw:2,0` works normally. The voiceHAT also
exposes no mixer controls at all, so there is no software capture gain to raise.

**RETRACTED — whisper does not invent sentences from silence.** This entry previously
claimed whisper hallucinated "There's a reason so much of our personal information ends
up happening. Data brokers make billions collecting and selling data." from a silent
room. The room was not silent. A video was playing nearby and the DevKit microphone
picked it up; whisper transcribed it correctly. The same file transcribes as
"centralized company this video", which is plainly the video, and a genuinely quiet
room recorded afterwards transcribes as nothing at all. The claim was wrong and the
measurement that produced it was contaminated.

**The real finding underneath it: the microphone hears the room, including whatever
media is playing in it.** An always-on device three feet from a TV or a laptop gets a
continuous stream of fluent, confident, perfectly-transcribed speech that no human in
the room said. Nothing downstream can distinguish that from a user turn, and a capture
level gate does not help, because the television is loud. This is why the wake word
matters more than it looks: it is the only thing standing between ambient media and the
agent. Astral itself is safe by construction — it declines anything that is not an
exact-answer question — but the turn still gets taken.

**The wake word is still hey_mycroft.** The product wake word is Open Brain and there
is no model for it. openWakeWord ships pretrained models only — alexa, hey_jarvis,
hey_mycroft, hey_marvin, timer — so Open Brain needs either a trained custom
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
this capability at all — the hotwords live cloud-side, so that cannot be tested until
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
   permanently — the failure is invisible rather than loud, which is the wrong direction
   for a bug and the reason it is written down here.
2. **Whether it wins the race.** The agent and the daemon see the same turn together. A
   device answer costs a subprocess and a table lookup; an agent answer costs a round
   trip and speech synthesis, so the daemon should be first by a wide margin. If it is
   not, the interrupt lands mid-sentence and the user hears a stub of the agent before
   the real answer.
3. **`POLL_SECONDS = 0.25`.** The documented background-ability example sleeps 20
   seconds, which is right for an alert and useless for taking a turn. A quarter second
   is a judgement, not a measurement; what it costs on a Pi 4 running the agent has not
   been measured.

The alert half (`due_alerts`) has a smaller unknown: it soft-imports `hooks` from
`~/astral-voice/hub-v2` so there is one timer store rather than two. On a device without
the local hub installed it reports nothing, forever, silently — correct, but
indistinguishable from a broken import.

## The fits table was measured inside the loop, and not every caller is the loop

Every number in `hub/data/costs/` was measured inside a long-lived process, where the
Slate kernel is already resident. The OpenHome ability is not that: the node server runs
it as `sudo python3 devkit_functions.py …`, a fresh process per turn. Measured on the
device, the same question cost 43 seconds twice in a row through that path while the
profile said `cold_start_ms: 1644` — so the ranking believed the class fitted here, and
the honest thing it could do about a 43-second answer was offer to send the question
somewhere else, from a device that can do it.

`hub/slate_server.py` fixes the case that matters by making the kernel shared rather than
per-process (0.6 s through the same path afterwards). The general problem stands: a
profile measured in one process model does not describe another, and nothing in the
measurement records which model it was taken under. `costs.offer()` exists because of
this — it answers "who else could" without consulting the local fit, for a caller that
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
  openhome` for exactly this reason, and a hub file written as root would stop being
  writable by the loop that owns it — one root-owned `smalltalk.sqlite` was created this
  way during measurement and had to be given back.

## The kernel: what is settled, and what is not

`hub/build_kernel.py` compiles the engine into `astral-kernel`, a wheel whose only
contents are a 6 MB shared object and a nine-line `__init__.py`. Verified on the device:
181 of 181 byte-contract phrases answer identically through the compiled kernel, and the
wheel contains no `.pyx` and no source.

Three things about it are not settled, and all three are visible rather than silent:

- **Distribution.** `requirements.txt` names `astral-kernel>=2.1.0`; nothing publishes it
  yet. A DevKit with the local hub does not need it; a DevKit with neither hub nor wheel
  says "the Astral engine is not installed on this device" out loud. Publishing it — PyPI,
  a release URL, a private index — is the author's decision and is not made here.
- **One wheel per interpreter and architecture.** The DevKit is CPython 3.13 on aarch64.
  A different Python or a different machine needs its own build. This is a property of
  compiled code; the loader reports it rather than failing quietly.
- **Two interpreters on one device.** The ability runs under system python as root; the
  loop and the tests run in the venv. Installing into one of them left the other with a
  kernel that had never heard of an entry point added that afternoon, and nothing
  anywhere said so. The deploy now installs into both, rebuilds a wheel older than its
  sources, and reinstalls a kernel older than its wheel — and the suite fails if the
  version it imports is not the version last built on that machine.

**What is NOT claimed.** A compiled extension is machine code, not source: there is no
Python in the wheel to read. It is not unbreakable — anything that runs can be reverse
engineered by somebody determined enough — and it is not obfuscation theatre. It is the
same protection every compiled commercial library has, arranged the way this platform's
own documentation says dependencies arrive.

## The local model: what it is for, and what it did

The second rung of the ladder is real now — llama.cpp built on the device, Llama 3.2 1B
and 3B (Q4_K_M) on the card — and everything about it is offered rather than assumed,
because everything about it is expensive or unreliable or both.

**Measured on the Pi 4, not estimated.** The 3B reads a prompt at 2.5 tokens a second and
writes at 1.3: a sixty-token answer is a minute and a half. The 1B reads at 9.8 and writes
at 3.6, and the model is loaded off the SD card every time, which is most of the wait — 60
seconds end to end for a two-sentence rewrite. The offer quotes the measured number,
loading included, because a promise of "half a minute" that takes a minute is the kind of
small lie that makes a device feel broken.

**It invents things, and it is caught doing it.** Asked to rewrite one sentence — "Turing
machines were first introduced independently by Turing and Post in 1936" — the 1B answered
"Alan Turing and Stephen Cook" on one run and "Alan Turing and Alan Post" on the next.
Neither name is in the passage. So every model answer is now checked against the passage
it was given: any name or number in the answer that is not in the source is a fabrication,
and the answer is refused out loud — *"The model added something the passage doesn't say —
Stephen — so I won't read you its version."* The mechanical summary, which is the
passage's own sentences, has already been spoken and is still true.

**It is only offered for the ONE thing it does well.** `costs.MODEL_CLASSES` holds
summarising and nothing else, and that was decided by measurement rather than taste.
Rewriting a mechanical summary works: given three sentences about Turing machines it
produced two clearer ones that said the same thing. Answering an open question does not,
even with perfect retrieval — handed a passage beginning "Smart pointers are pointers that
own the object they point to and automatically delete it", the 1B replied that the text did
not mention smart pointers; asked about the laws of physics it looped, "the study of the
laws of society will be the study of the laws of society". Several prompt shapes were
tried, on the device, and the shape was not the problem. A rung that answers badly is
worse than a rung that is not there, because somebody has to spend a minute to find out. It is never offered for arithmetic, algebra or anything with one
right answer: those have exact kernels, and a model that is merely fluent about them is
worse than silence. Before that rule existed, the ranking offered a 1B model as a way to
integrate x squared.

**What is not done:** nothing keeps the model resident, so every use pays the load. A
resident server — the shape `slate_server.py` already uses — would remove most of the
wait, at the cost of about a gigabyte held permanently.

## The reader answers some questions with the question

MECH's reader sometimes hands the question back rearranged: "what are the laws of
physics" came back as *"What about the physics and law?"*, and "turn on the kitchen light"
as *"What about the kitchen and light?"*. It is not an answer, and speaking it is worse
than silence because it sounds like the device was not listening.

The router now refuses an "answer" that both asks a question and says nothing the question
did not already say, and hands the turn up the ladder instead. What that exposes is the
reader's real limit: it answers definitional questions well ("what is a lighthouse") and
open ones poorly. That is a MECH question, not a routing one, and it is still open.


## The compiled kernel disagrees with its own source on three phrases (2026-09-03)

`astral_kernel.answer()` and `engine.answer()` give different answers for exactly three
of the 181 phrases the suite checks, all of them arithmetic said in words:

```
convert ten pounds to kilograms   engine: 10 pounds is 4.54 kilograms.
                                  kernel: 1 pounds is 0.45 kilograms.
minus four plus ten               engine: -4 plus 10 is 6.        kernel: None
fifteen plus twenty seven         engine: 15 plus 27 is 42.       kernel: None
```

**What has been ruled out.** The installed extension is byte-identical to the newest
wheel (sha256 `62cca876dd21c181`), the wheel was built at 04:20 from the current sources,
and the generated `_engine.pyx` contains calc's number-word table — four occurrences of
"fifteen", the same as `calc.py`. So this is not a stale artifact, not a stale install,
and not a missing module. Cython was also found missing for the system interpreter while
present in the venv, which is why the deploy's build had been silently skipping for some
time; that is fixed by building with the venv interpreter, and it did not cause this.

**What it affects.** The OpenHome ability path only. On the device the hub answers first
and the kernel is the fallback for when the hub is not running, so a person talking to
the DevKit never sees it. It matters for the shipped ability, and it matters because two
things that are supposed to be the same thing are not.

**Where to look next.** `build_ability.build_block()` transforms the source it splices —
renames `engine.answer` to `astral_answer`, strips markers, and skips formatting. The
next step is to diff the spliced calc block against `calc.py` line by line, and to check
whether the compiled module's regex alternation survives the transform with its
longest-first ordering intact: "ten" answering as 1 looks exactly like an alternation
matching a shorter branch first.

## Open, as of 2026-09-03 05:45

Measured, reproducible, and not fixed. Each one is here because it is better written down
than remembered.

**1. Thirty-eight percent of wakes produce no words.** Of 480 wake events in one evening's
log, 182 were followed by a burst with nothing usable in it. Some of those are a person
saying the wake word and then pausing, which is correct behaviour; the rest are false
wakes. The log carries no timestamps, so the two cannot be separated after the fact, and a
controlled quiet-room measurement is the only way to get the real number. That measurement
is the right next step before any work on a trained wake model, because it is the number a
trained model has to beat — and the last attempt at one scored 0.999 against its own
threshold and would have woken at nothing.

**2. The reader's corpus contains web-development text.** MECH answered "when did the
roman empire fall" with "Roman installed helvetica", and "whats the weather" with "Weather
is towards the side exposed to wind". Both are now routed away — history and absent
capabilities are answered before the reader sees them — but the corpus itself is a
separate product's data and still holds material like that. Anything that reaches tier two
can still produce a sentence of it.

**3. Two names still get a gloss.** "Who is Ada Lovelace" and "who is Avicenna" answer
"…is a name for a particular person, place, or thing", because the encyclopedia passage
that mentions them does not contain the surname as a separate word for the containment
check to find. The check exists to stop a Python manual being offered as an answer about
Ada Lovelace, which it did. A better rule would score the passage rather than require a
word.

**4. Britannica has no page numbers.** The 29 volumes arrived as gzipped scanner text with
no page breaks, so 224,021 passages carry page zero and "what is on page 412 of Britannica"
cannot be answered. It now says so plainly. Fixing it properly means re-fetching the
volumes as PDFs — a download, not a code change.

**5. Britannica volume 29 is unreadable.** Its gzip is corrupt at the source, not
truncated, so nothing can be recovered from this copy. It is reported by name as unread
rather than silently dropped. Volume 3 was truncated and 1,236,485 words of it were
recovered.

**6. The compiled kernel disagrees with its source on three phrases.** See the section
above. Ability path only.
