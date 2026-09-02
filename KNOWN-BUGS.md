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
