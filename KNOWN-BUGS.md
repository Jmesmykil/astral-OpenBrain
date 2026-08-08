# Astral — known bugs and limitations

Straight list of what's rough, so nobody's surprised. Split by the two paths.

## Local mode (on-device wake + whisper)

- **No echo cancellation on the HAT.** Astral's own voice can bleed into the mic. Handled with a mic flush plus a cooldown after every listen, but a loud speaker close to the mic can still trip a false wake.
- **Wake fires on any matching sound.** Someone else talking nearby can start a listen, which then comes back empty. No speaker identification yet.
- **Whisper can double or invent a phrase** on noisy or long audio. Handled by collapsing an immediate repeat back to one copy and by stopping the capture on silence, but a noisy room can still give an empty or garbled result.
- **Occasional word or number order garble** ("45 dollars" comes back as "dollars 45"). The deterministic engine is forgiving and still answers most of these.
- **Sometimes misses a clearly spoken command** and comes back empty. Mic quality plus room noise. Say it again and it usually lands.
- **Latency is about 2.5 to 3 seconds** per command. That's whisper base.en on the Pi 4.
- **Wake word is "hey mycroft" right now.** The product wake word "Open Brain" needs a custom wake model (Picovoice Porcupine with a free key, or a trained openWakeWord model). Not wired yet.

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
