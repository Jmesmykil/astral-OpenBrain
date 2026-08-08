# Astral

A deterministic layer for OpenHome. It answers the exact-answer class instantly, without the LLM: time, date, math, money, unit conversions, and device telemetry. Everything else passes to the agent.

## Why

OpenHome sends every request to the cloud, even ones with a single right answer like "what time is it" or "what's 20 percent of 80." Those never needed a model. Astral catches that class and answers it directly.

OpenHome already ships `date-and-time` as an official base capability. Astral is that generalized: the whole exact-answer class as one capability.

## Three ways to run it

1. **Cloud-side Skill (works today, no platform change).** The engine is inlined in one `main.py`, like `date-and-time`. The agent transcribes, a trigger word routes to Astral, it computes the answer and speaks it, no LLM. Works for any agent, no DevKit. → `community/astral-skill/`
2. **Local DevKit ability.** The compute runs on the device through OpenHome's `devkit-capability` path, plus telemetry: temperature, uptime, disk, memory. → `community/astral/`
3. **Fully local, no cloud.** Wake and speech-to-text run on the DevKit too, so the exact-answer class answers with no network at all. Proven with the network off. Going native here wants one small platform change: a gate so a hardware ability can answer before the LLM.

## Does it need an OpenHome OS change?

No, not to work. The cloud-side Skill and the DevKit ability run today through the existing ability system and answer without the LLM, the same way the official `date-and-time` base does. The one platform change is only for version 3, the fully-local no-cloud path, and it is small: let a hardware ability return an answer and stop before the LLM call.

## Measured on the DevKit

Raspberry Pi 4 Model B, 4 cores, 7.7 GB RAM, Python 3.13.5.

| Part | Number |
|---|---|
| Wake word, always-on (openWakeWord, hey_mycroft) | 5.5% of 4 cores at rest, 210 MB RAM |
| Speech-to-text burst (whisper base.en-q5_1, audio-ctx 512, 4 threads) | ~2.5 to 3.3s per command, all 4 cores briefly |
| Answer: time and date | 27 microseconds |
| Answer: math and conversions | 427 microseconds |
| Text-to-speech (piper lessac-medium) | ~2s per reply |
| Disk | whisper 57 MB, wake 496 KB, piper 61 MB |

The answer itself is microseconds. On the fully-local path the latency is speech-to-text and text-to-speech, not the compute. The cloud-side Skill adds only those microseconds on top of the agent's own speech handling.

## Layout

```
community/astral-skill/   cloud-side Skill (the uploadable ability, engine inlined in main.py)
  main.py                 the capability: deterministic dispatch, no LLM
community/astral/         Local DevKit ability (device compute + telemetry + MQTT)
  main.py                 the capability
  devkit_functions.py     one self-contained device file (engine inlined)
RELEASE.md                the full release write-up
SUBMISSION.md             the short pitch to OpenHome
KNOWN-BUGS.md             honest limitations
assets/                   cover image
```

## The engine

`mechanical.py` and `calc.py` are pattern and table based. No model, no network. They return nothing when it is not an exact-answer question, so the agent takes the turn. That is how it stays out of the way instead of blocking.

## Test the engine (no device needed)

```bash
python3 community/astral/devkit_functions.py respond "what time is it"
python3 community/astral/devkit_functions.py respond "convert ten pounds to kilograms"
python3 community/astral/devkit_functions.py respond "eighteen percent tip on forty five dollars"
```
