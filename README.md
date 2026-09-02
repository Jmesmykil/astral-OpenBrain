# Astral

A deterministic layer for OpenHome. It answers the exact-answer class instantly, without the LLM: time, date, math, money, unit conversions, grades, physics, chemistry, statistics, and device telemetry. Everything else passes to the agent.

## Why

OpenHome sends every request to the cloud, even ones with a single right answer like "what time is it" or "what's 20 percent of 80." Those never needed a model. Astral catches that class and answers it directly.

OpenHome already ships `date-and-time` as an official base capability. Astral is that generalized: the whole exact-answer class as one capability.

The class is bigger than it first looks. "What do I need on the final to get a 90", "molar mass of water", "escape velocity of Mars", "standard deviation of 4 6 8 10", "is 91 prime" are all questions with exactly one right answer and a formula that produces it. A model answers them fluently and sometimes wrongly. Astral computes them, in microseconds, offline.

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
| Answer: time and date | 28 microseconds |
| Answer: grades | 74 microseconds |
| Answer: physics | 129 microseconds |
| Answer: number tools | 261 microseconds |
| Answer: statistics | 327 microseconds |
| Answer: chemistry | 357 microseconds |
| Answer: math and unit conversions | 444 microseconds |
| Deciding it has no answer, so the agent takes the turn | 262 microseconds |
| Text-to-speech (piper lessac-medium) | ~2s per reply |
| Disk | whisper 57 MB, wake 496 KB, piper 61 MB |

Measured on the device on 2026-08-17, 300 runs each, against the file as deployed.
The answer itself is microseconds. On the fully-local path the latency is speech-to-text and text-to-speech, not the compute. The cloud-side Skill adds only those microseconds on top of the agent's own speech handling.

## Layout

```
community/astral-skill/   cloud-side Skill (the uploadable ability, engine inlined in main.py)
  main.py                 the capability: deterministic dispatch, no LLM
community/astral/         Local DevKit ability (device compute + telemetry + MQTT)
  main.py                 the capability
  devkit_functions.py     one self-contained device file (engine inlined)
hub/                      engine source, generator and tests (ships upstream as community/astral/hub/)
RELEASE.md                the full release write-up
REVIEW-2026-09-01.md      the upstream review, quoted, and what was done about it
SUBMISSION.md             the short pitch to OpenHome
KNOWN-BUGS.md             honest limitations
assets/                   cover image
```

Both shipped files carry an inlined copy of the engine because each has to be one
self-contained file: the node server copies a single `devkit_functions.py` to the
device, and the platform uploads a single `main.py`. They are generated from one set
of engine sources rather than maintained by hand, so the two copies cannot drift into
answering the same question differently.

## The engine

Pattern and table code, split by subject: `mechanical.py` (time and date), `calc.py`
(arithmetic, money, ten unit dimensions), `study.py` (grades and GPA), `chem.py`
(the periodic table, molar mass by formula parse, moles, molarity, pH, ideal gas),
`sci.py` (mechanics, planet mass and size, gravity, relativity, light), `stats.py` (descriptive statistics
and counting), `mathx.py` (bases, logs, trig, primes, quadratics, fractions).
`engine.py` is the one router they all sit behind, so a phrase resolves the same way
on the device and in the cloud.

No model, no network. Every module returns nothing when the question is not its
business, so the agent takes the turn. That is how it stays out of the way instead of
blocking.

Two rules the code holds itself to. Molar masses are computed by parsing the formula
against the element table, never typed in per compound, because a hand-entered
constant is a typo waiting to be spoken with confidence. Anything resting on a
convention says which convention: a letter grade names the 90/80/70 scale, a standard
deviation says whether it is the sample or the population one.

## Tests

155 phrases are asserted BYTE-EXACT against known-good strings, the questions Astral
must stay silent on included, so the agent keeps the turn. Byte comparisons, not
approximate ones: a changed constant, a changed rounding rule, or one subject stealing
another's phrasing all show up as a diff rather than as a plausible wrong answer.

Two more suites run behind that one. A parity suite lifts the engine out of each
shipped file and replays every phrase through it, so the DevKit ability and the cloud
Skill are proven to agree rather than assumed to. And a hardening suite tries to break
it: four thousand generated utterances that must never crash or hang, every unit
round-tripped and ten of them checked against published values, statistics recomputed
against Python's own `statistics` module, factorizations multiplied back out, the
periodic table checked for all 118 elements, molar masses recomputed by hand
expansion, surface gravity and escape velocity checked against NASA's figures for
eight bodies, plus zero and negative and empty and ten-thousand-character inputs.

The point of the second and third suites is that the first one can't catch a table
typo it was written from. Checking a number a second, independent way can.

You can run any of it against the shipped file directly, no device required:

```bash
python3 community/astral/devkit_functions.py respond "molar mass of water"
python3 community/astral/devkit_functions.py respond "standard deviation of 4 6 8 10"
python3 community/astral/devkit_functions.py respond "escape velocity of mars"
```

## Test the engine (no device needed)

```bash
python3 community/astral/devkit_functions.py respond "what time is it"
python3 community/astral/devkit_functions.py respond "convert ten pounds to kilograms"
python3 community/astral/devkit_functions.py respond "eighteen percent tip on forty five dollars"
```
