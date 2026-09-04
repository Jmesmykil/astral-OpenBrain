# Astral

A deterministic layer for OpenHome. It answers the exact-answer class instantly, without the model: time, date, math, money, unit conversions, grades, physics, chemistry, statistics, and device telemetry. Everything else passes to the agent.

## Why

OpenHome sends every request to the cloud, even ones with a single right answer like "what time is it" or "what's 20 percent of 80." Those never needed a model. Astral catches that class and answers it directly.

OpenHome already ships `date-and-time` as an official base capability. Astral is that generalized: the whole exact-answer class as one capability.

The class is bigger than it first looks. "What do I need on the final to get a 90", "molar mass of water", "escape velocity of Mars", "standard deviation of 4 6 8 10", "is 91 prime" are all questions with exactly one right answer and a formula that produces it. A model answers them fluently and sometimes wrongly. Astral computes them, in microseconds, offline.

## Three ways to run it

1. **Cloud-side Skill (works today, no platform change).** The engine is inlined in one `main.py`, like `date-and-time`. The agent transcribes, a trigger word routes to Astral, it computes the answer and speaks it, no model. Works for any agent, no DevKit. → `community/astral-skill/`
2. **Local DevKit ability.** The compute runs on the device through OpenHome's `devkit-capability` path, plus telemetry: temperature, uptime, disk, memory. → `community/astral/`
3. **Fully local, no cloud.** Wake and speech-to-text run on the DevKit too, so the exact-answer class answers with no network at all. Proven with the network off. Going native here wants one small platform change: a gate so a hardware ability can answer before the model.

## Does it need an OpenHome OS change?

No, not to work. The cloud-side Skill and the DevKit ability run today through the existing ability system and answer without the model, the same way the official `date-and-time` base does. The one platform change is only for version 3, the fully-local no-cloud path, and it is small: let a hardware ability return an answer and stop before the model call.

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

## Version two: what runs where, measured

Version one answered the exact-answer class on the device and stayed silent otherwise.
Version two adds tiers above that, and no tier runs anywhere until its cost has been
MEASURED on that machine. `hub/measure_costs.py` runs the shipped engine over the
corpus on the host it is run on and writes a profile; `hub/costs.py` compares it to a
budget and produces the fits table; `hub/router.py` reads the table before it runs
anything. A class that fits runs. A class that fits somewhere else on the LAN says what it
would need and asks, and a class that fits nowhere stays silent while the agent takes the
turn.

Measured on the DevKit (Pi 4, 8 GB, idle, 30 runs per phrase):

| What it does | Tier | Cost on the DevKit | From |
|---|---|---|---|
| time and date | 0 | 100 us | p95 of 200 |
| the device and its OS | 0 | 261 us | p95 of 40 |
| grades | 0 | 356 us | p95 of 320 |
| sun signs and the moon | 0 | 544 us | p95 of 40 |
| physics and the planets | 0 | 793 us | p95 of 1080 |
| statistics | 0 | 808 us | p95 of 480 |
| number tools | 0 | 808 us | p95 of 1000 |
| deciding it has no answer | 0 | 870 us | p95 of 1480 |
| chemistry | 0 | 1.0 ms | p95 of 680 |
| flashcards from the card | 0 | 1.0 ms | p95 of 40 |
| math, money, conversions | 0 | 1.3 ms | p95 of 2000 |
| timers, alarms, reminders | 0 | 2.9 ms | p95 of 40 |
| what it can and cannot do | 0 | 3.2 ms | p95 of 40 |
| small talk and jokes | 0 | 3.9 ms | p95 of 40 |
| songs, played and spoken | 0 | 640.7 ms | p95 of 40 |
| exact arithmetic, proven kernel | 1 | 16 us | - |
| passages from the books | 1 | 1.1 ms | p95 of 42 |
| every sense of a word | 1 | 26.3 ms | p95 of 42 |
| algebra and calculus | 1 | 320.1 ms | p95 of 40 |
| reading a new question | 2 | 1.8 s | max of 6 |
| open conversation | 2 | 1.8 s | max of 6 |

Every row was measured on the DevKit by `hub/measure_costs.py` and is read from
`hub/data/costs/pi4-8g-arm64.json`, the same file the router obeys. "From" says how the
figure was arrived at: a percentile where a class is cheap enough to sample hundreds of
times, the observed maximum where it is not, because a percentile over six samples is a
maximum wearing a percentile's name. Memory is only reported for a kernel that runs in
its own process; for everything sharing this one there is no per-class number to give.

**All of it runs on the DevKit, off the card.** The 128 GB card is what makes the upper
tiers possible here rather than somewhere else: the dictionary is Open English WordNet
with 135,969 lexemes and 107,519 defined senses, the comprehension core reads against
133,218 dictionary entries and 52,571 phrases from a 456 MB data set, and the books and
corpora sit beside them. There is no cloud tier and no dependency on another machine.
A LAN route to a bigger machine exists for anything the device cannot hold, and today
nothing in the table needs it. Open weights and toolchains are fetched once
onto our own drives and run from there.

The exact arithmetic is checked twice: the table layer computes with Python's own
`Fraction`, and Slate's Ada/SPARK oracle re-derives the same step through its C entry
point (`hub/kernels/spark_exact.py`, built native on the device with GNAT, 92 KB). They
must agree before a word is spoken. A disagreement is a silence, never a guess.

Chimes say what is happening without words: a cue on wake, a working tick while
speech-to-text runs, an acceptance chime when a command matches, a distinct cue when it
is about to ask about a route, and a low tone when it declines. The device's own sound
set is used where a file fits the meaning.

## Layout

```
community/astral-skill/   cloud-side Skill (the uploadable ability, engine inlined in main.py)
  main.py                 the capability: deterministic dispatch, no model
community/astral/         Local DevKit ability (device compute + telemetry + MQTT)
  main.py                 the capability
  devkit_functions.py     one self-contained device file (engine inlined)
hub/                      engine source, generator and tests (ships upstream as community/astral/hub/)
  costs.py, measure_costs.py, data/budgets.json   the fits table: measured cost per class per host
  router.py               run, ask, or stay silent, from the fits table
  kernels/spark_exact.py  the proven Ada/SPARK oracle behind its C ABI
  device.py, hooks.py     the OS surface; timers, alarms and reminders
  books.py, smalltalk.py  passages from the card; jokes and pleasantries, no repeats
  sounds.py, lan.py       the chime set; the token-authenticated LAN route
deploy/install_v2.sh      put version two on the DevKit and wire the service
deploy/HW_TEST.md         the hardware test, turn by turn
RELEASE.md                the full release write-up
REVIEW-2026-09-01.md      the upstream review, quoted, and what was done about it
SUBMISSION.md             the short pitch to OpenHome
KNOWN-BUGS.md             honest limitations
assets/                   cover image
```

Both shipped files carry an inlined copy of the engine because each has to be one
self-contained file: the node server copies a single `devkit_functions.py` to the
device, and the platform uploads a single `main.py`. They are built from one set
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

## Two modes, and which one to run

The device can listen in either of two ways, and the difference is only who does the
listening.

**Through OpenHome, their way.** Their kiosk owns the microphone, their wake word gates
the turn, their speech-to-text transcribes it, and a hotword match routes the phrase to
our ability, which answers deterministically without waking their model. This is the
mode their documentation describes, it is what PR #361 shipped, and it is better than
ours at exactly the two things we are weakest at: the wake word is theirs and maintained,
and their transcription beats whisper-base on a Pi 4. It is NOT local: their kiosk
loads `openhome-staging.algoryc.com`, so the audio leaves the house for transcription.
The one step still outstanding is registering the ability's trigger words on agent 595324
at app.openhome.com, which needs an account login.

**The local loop, ours.** Wake, speech-to-text, every tier and the voice all run on the
device or on the LAN, and nothing leaves the house. It costs the two things above: the
wake phrase is recognised, not trained, "open brain" or "open home", and transcription takes two to
three seconds. It buys the chimes, timers that survive a restart, a quiz that holds its
place across turns, barge-in, and the fits table deciding what runs where.

```
deploy/install_v2.sh openhome@openhome.local --start   # the local loop
# or, to hand the microphone back to OpenHome:
ssh openhome@openhome.local 'systemctl --user stop astral-hub; systemctl --user start openhome-dashboard'
```

One microphone, one owner: never run both. Whichever is listening, the answers come from
the same engine: `hub/build_ability.py` builds the ability from the same sources the
loop imports, and the suite proves the two agree phrase for phrase.

**Through OpenHome, the ability now answers everything the loop does.** The shipped file
stays self-contained, and on a bare DevKit it is the whole product. When the hub is
installed beside it, which the deploy does, it asks the hub for anything it cannot answer
itself: the dictionary, the books, the songs, the quiz, the reader, the exact-mathematics
kernel. Measured on the device through OpenHome's own dispatch path: "define ubiquitous"
0.9 s, "sing twinkle twinkle" 0.6 s, "integral of x squared" 0.6 s, "what is 20 percent of
24352" 0.2 s.

**And when it cannot answer, it says so and asks where to send it.** "I can't do that
here. Want me to ask the Mac, or the cloud?", a question, answered out loud, naming the
machines. A machine in the house is asked over the LAN and the answer is spoken; the cloud
means this ability stays quiet and OpenHome's own agent takes the turn it would have taken
anyway. Nothing is sent anywhere on a shrug: chatter is never offered, a bare "yes" with
two places named is not an answer, and "no" ends it. The cloud route ships switched off in
`hub/data/routes.json` for the local loop, where there is nothing behind it.

**Anything you put on the card, asked out loud.** `hub/library.py` is a set of shelves
on the SD card: `reference/` for glossaries, `docs/` for language and application
documentation, `code/` for your own projects, `data/` for datasets, `books/` for books.
Drop files in, index once, and ask: "look up eigenvector", "what do the docs say about
ownership", "in my project, what does resolve_route do", "what is in my library". Prose is
cut into paragraphs, code into its functions and classes, data into records, and every
answer names where it came from, because a passage with no source is indistinguishable
from a machine inventing one. `library.py add <path|git-url> <shelf>` links a folder (no second
copy on the card) or shallow-clones a repository; a dictionary dump in JSONL lands as a
glossary, which is how terminology for a whole field gets on there. The dictionary asks
your shelves before it answers from WordNet: measured on the device, WordNet holds 20 of
25 academic terms, and knows nothing of gradient descent, a Lagrangian, or big O notation.

**It was stress-tested with a fourteen-volume encyclopedia.** The 1911 Britannica is 41 GB
of scanned page images and 96 MB of searchable text, and the text is the part worth having,
so gzipped archives are read where they lie, and nothing is extracted onto the card.
Measured on the DevKit:

| | |
|---|---|
| files read | 126 (Britannica, World History, Physical Science, my books, the Python docs) |
| passages | **308,952** |
| full rebuild from nothing | **about 3 minutes** |
| index on the card | 544 MB |
| peak memory while building | 169 MB (measured at 231k passages) |
| answering a question | **1-58 ms** |

"What does the encyclopedia say about the steam engine" comes back in 17 ms with Watt's
1769 patent, in his own words. A book's own back-of-book index is read too, so "tell me
about smart pointers" answers *"Modern C++ indexes smart pointers on pages 248 to 251"*
before it reads anything out.

**No silent failures.** A turn that began with a wake word never ends in nothing. It ends
in an answer, a question, or a spoken refusal that says why: "that needs the dictionary,
and this device doesn't have it", "the maths kernel is still starting", "two ways of
working that out disagreed, so I won't say either". For the only two silences that are
correct (what you said was not a question, nothing usable was heard), it plays a quiet
tone that means "heard you, nothing here for me". `hub/tests/suite_silence.py` reads the reasons out
of the source and fails if any of them has no voice, so a silence added tomorrow cannot be
silent by omission. Through OpenHome the same rule holds, with their agent covering what
we decline; the background daemon says out loud when it cannot reach the device at all,
and says when it is back.

**The ladder, and where a question climbs to.** Every class walks the same four rungs, in
this order: *mechanical here* (tables, kernels and MECH, in microseconds), *a model here*
(a GGUF on the card, tens of seconds, and asked for), *the house* (the Mac or your phone
over the LAN), *the cloud* (named providers, off by default and never silent: Claude,
ChatGPT, Gemini, the OpenHome agent). Two rungs and it names both: *"I can't do that here. I
could ask the Mac, the OpenHome agent, or Claude. Which one?"* A bare "yes" takes the
nearest, never the cloud.

**The model on the device answers in its own words, and is checked.** llama.cpp is built
on the DevKit with Llama 3.2 1B and 3B on the card. Measured on a Pi 4: the 1B reads at
9.8 tokens a second and writes at 3.6, and loading it off the card is most of the 60
seconds a rewrite takes, so it is OFFERED, with the measured wait quoted, and it runs
only on a spoken yes. Every answer it gives is diffed against the passage it was given:
asked to rewrite one sentence about Turing machines, it invented "Stephen Cook" once and
"Alan Post" the next time, so any name or number it adds is now refused out loud. It is
never offered for arithmetic or algebra, because those have exact kernels, and a model
that is merely fluent about them is worse than silence.

**One kernel for the machine.** Slate takes 41 seconds to compile itself and milliseconds
to answer after that, so `hub/slate_server.py` owns one and both callers ask it over a
Unix socket. Before this the ability paid the start on every turn, 43 seconds, twice in a
row, measured, and then offered to send the question away rather than do it here.
While it is warming it says so rather than going quiet.

## The wake word

It answers to **"open brain"** and **"open home"**, recognised as phrases by a small
streaming recogniser (vosk) with the two phrases as its whole grammar, so there is no
training and the room is never transcribed. The trained model in `hub/wake/` does not
ship: graded against ninety seconds of room audio recorded here, it scored 0.999 against
its own 0.95 threshold,
which means it woke at nothing. The phrase recogniser's own weakness is the opposite one:
it wakes on a television, and after three wakes in a row that come to nothing the wake
chime is withheld until a real answer. `KNOWN-BUGS.md` has the measurements.

## Tests

One runner, `python3 hub/tests/run.py`, and twenty-six suites named for what they prove:
answers, kernels, ranking, classes, meta, study, library, notes, conversation, voice, duplex,
barge, daemon, ability, clouds, languages, settings, facts, fun, memory, lanes, pages,
wake_takes, silence, shipped, honesty. 3,593 checks on the Mac and 3,636 on the DevKit (2026-09-03), every one run against a
scratch copy of the device's state so a check can never touch the card. The byte contract is the centre of
it: 167 phrases asserted BYTE-EXACT against known-good strings, the questions Astral
must stay silent on included, so the agent keeps the turn. Byte comparisons, not
approximate ones: a changed constant, a changed rounding rule, or one subject stealing
another's phrasing all show up as a diff rather than as a plausible wrong answer.

Two more suites run behind that one. A parity suite lifts the engine out of each
shipped file and replays every phrase through it, so the DevKit ability and the cloud
Skill are proven to agree rather than assumed to. And a hardening suite tries to break
it: four thousand fuzzed utterances that must never crash or hang, every unit
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

## Sound packs

Every chime and the thinking tick come from a pack: a folder holding any of seven files
(`ready`, `wake`, `working`, `accept`, `handoff`, `decline`, `dismiss`) in wav, mp3, ogg or
flac. OpenHome's house set is the default, so the DevKit sounds as it ships. `astral` is made
on the device, glass for the chimes and a water drop for the tick. Drop your own folder into
`~/astral-voice/sounds/packs/<name>/` and it is a pack; a meaning it lacks falls back for
that one sound. Say **"use the astral sounds"**, or **"what sound packs are there"**.
Loudness is levelled when played, so record at any level.
