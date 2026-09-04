# Spoken script: Brady / OpenHome, 30 minutes, 2026-09-04

Read this out loud once before the call. Everything stated as a number below was measured
on the DevKit or the Mac and is in KNOWN-BUGS.md with its date. yours to say, so don't read the bracket.

---

## 1. What is on the device today (open with this, 4 minutes)

"Thanks for the time. I'll start with what's running on the DevKit right now, because
the rest of the call makes more sense after it.

The whole loop is on the Pi 4 with the XMOS HAT, and nothing leaves it. The wake phrase
is a Vosk grammar, two phrases and an everything-else bucket, so the room is never
transcribed. Speech-to-text is whisper base.en, q5_1. The voice is piper. Above those
there's a compiled answer kernel, `astral_kernel` 2.2.0, built aarch64 on the device,
which is a Julia mathematics kernel running as a service, and a small model, Llama 3.2 1B
Instruct at Q4_K_M, served by llama-server on port 8791. That's the whole stack, and there
is no network in the answer path.

The levels it hits: the mechanical class, meaning time, date, arithmetic, unit conversion
and 'what can you do', answers in one to eleven milliseconds, median, on the device. The
library class, passages out of the books and encyclopedias and the curated facts, is
sub-second warm. Comprehension in its own words is seconds. One honest number: after a
cold reboot, the first library question took forty seconds once. That's the index warming
off the card, and I'm fixing it with a warm-up at boot.

On the card: three books, two documentation sets across sixty-six files, a reference shelf
of Britannica, world history and physical science, about three hundred thousand passages,
six hundred and eighty-two curated facts, and twenty-eight local abilities.

Two more numbers matter more to me than the features. Three thousand six hundred and
thirty-six checks held on the DevKit across twenty-six suites, zero failed; three thousand six hundred and thirty on the Mac, zero failed. And every new gate I write, I prove red
before I trust it green, because if a check has never failed, I don't know that it checks
anything.

Yesterday I ran the scripted voice demo under scrutiny: twelve questions asked and
answered by voice, twelve of twelve as scripted, two hundred and sixteen to two hundred
and seventy-two seconds, and it left the settings, the hooks and the notes as it
found them."

---

## 2. The mechanics: how it actually works (7 minutes)

"The loop is: wake, burst-record, transcribe, route, speak. It runs half-duplex, because
this HAT has no hardware echo cancellation. After every sound it makes, it flushes the
microphone and holds a refractory window so it can't answer its own voice.

**Router and tiers.** One place decides run, ask, or stay silent. It names the command
class a phrase needs, asks a fits table what this host may do with that class, and returns
something the loop can act on without a second opinion. Tier 0 is pattern and table code,
microseconds. Tier 1 is a native kernel or an indexed corpus on the card. Tier 2 is
comprehension. Every class carries a measured cost profile for the machine it's on,
written by a script that runs the shipped engine over the corpus on the card.

**Budgets advise the router, and I learned that the hard way.** The budgets file holds a
ceiling per tier per host. The library index grew from two hundred and thirty-one thousand
passages to three hundred and nine thousand, the measured 95th percentile crossed the
ceiling by two hundred and fifty-eight microseconds, and the device correctly and
completely switched its own library off. Every book question answered with nothing. A
ceiling that kills a capability at a margin of three hundredths of a percent is a number I
chose wrongly, and the capability itself was fine. Storage classes carry their own budgets
now, because a file write is not a table lookup. And a class measured slow here goes to a
second lane, 'I'll look that up while we talk', with the answer landing in a pause rather
than over a sentence.

**The kernel as a shim.** Your contributing rules are MIT, readable and security-scanned,
and a local ability is three files with `devkit_functions.py` named that.
So the ability is a thin MIT shim, three hundred and forty-three lines: it finds the hub,
falls back to the compiled kernel, and if neither is there it says why rather than failing
in silence. My engine ships the way any Python dependency ships, as a wheel named in
`requirements.txt`. Nothing proprietary hides inside the MIT file, and nothing in the MIT
file needs my engine to be readable in review. That seam is documented in BOUNDARY.md,
because I'd rather have it on the table than smuggle a blob into a PR.

**The mathematics kernel.** It's Julia with an Ada/SPARK oracle behind a C ABI. It takes
about forty-three seconds to come up on this board and milliseconds after that, so one
process owns it and both callers talk to it over a Unix socket. Before that the ability
paid the start on every turn and then offered to send the question away, which is a
local-first device giving up exact mathematics it can do, because of a process boundary.
Exact arithmetic is computed twice, Python's fractions and the SPARK oracle, and they must
agree before a word is spoken. If they disagree it stays quiet, and it never guesses.

**Memory and consent.** Nothing is written until somebody says 'remember me'. It's a
property graph on the card, with a clock reading on every row. 'Forget me' deletes the
whole file rather than the rows. Notes mode is separate and announces itself. Conversation
context lives in process memory, times out, and is never written down.

**The loudness model.** Measured as RMS at the device, the wake chime was sixteen thousand
eight hundred, the tick five thousand seven hundred, the ready tune three thousand one
hundred, a spread of five to one, which is why no setting could ever make it consistent.
Every file and every sentence is levelled to one target now before its relative and the
chime lift apply, under one master that only a person moves.

**The ear.** Yesterday I found the microphone running two full seconds behind the room.
`parec` with no stated latency inherits pipewire-pulse's default record fragment, and
that's two seconds, so every wake phrase, every interruption and every flush was acting on
a room that no longer existed. At fifty milliseconds, with the pipe widened so a flush
really empties, the same sound is heard six hundred and sixty milliseconds after its player
launches. Barge-in is echo-gated on top: a wake matched while the device speaks counts only
if the last eight-tenths of a second at the microphone is above a measured threshold, and
its own echo sits below it. A false barge is harmless, since it resumes the sentence from
before the cut.

**Test discipline.** Twenty-six suites named for what they prove, run against a scratch
copy of the device's state so a check can never touch the card. One suite's only job is to
prove nothing fails silently: it reads the refusal reasons out of the source and fails the
build if any path can go quiet."

---

## 3. Where it goes next (4 minutes)

"The ladder is four rungs: mechanical here, a model here, a machine in the house, then a
named cloud provider. It exists in code today, with consent by name, 'the Mac, or
Claude?', because 'the cloud' is not something a person can choose between. Only the
local rungs are live. The cloud hand-off is designed and not connected, and that's
deliberate: I'll add the optional cloud when the ranking reaches a level that needs it.
Today no class is in that position, so the device doesn't make the offer. A route that
can't answer is worse than no route.

The near list: a trained wake model from real recordings, so I can put a measured
false-wake rate on a room with a television, which today I can only estimate. Sound packs
already ship, your house set is the default, and any folder dropped in is a pack.
Languages: it hears about a hundred and says which it heard, rather than translating its
own sentences with a 1B model that demonstrably invents. And a second household, a DevKit
running a month in a home that isn't mine. That's the test I can't run alone."

---

## 4. The bridge: this is the small end of something bigger (5 minutes)

"I want to be straight about where this came from, because it explains why the device is
built the way it is. The DevKit work is the smallest node of a local-first system I've
been building.
I've been at this for about three years on my own, teaching myself as I went. What pulled me in was wanting machines that answer without a subscription and without a data centre, and finding out that nobody had built the mechanical half properly.

Underneath it there's an orchestration engine I run locally: prime directives that gate
what any process may do, product isolation so two projects can never be conflated into one
build path, and a coordination bus where a process claims the work before it touches
anything. The rule that matters here is the same one the device follows, evidence or
silence. A claim without a receipt isn't done.

Beside it there's a deterministic comprehension engine. Its law is that a reading becomes a
belief rather than a fact: revisable, carrying its inferential provenance and a condition
that would overturn it, and only a gate promotes anything to actual. It stores a sentence
one of two ways: as 'this document states…' with no subject bound, which by design can
never be promoted, or as a typed reading with a real subject, predicate and object, which
can. Measured on the live ledger, ninety-nine point nine percent of a seventy-gigabyte
library landed in the first lane. That is the engine telling the truth about what it did
not understand, and the remedy is a re-read with comprehension on, which put seventeen and
a half percent into the typed lane on one documentation set. It abstains rather than
guesses, and I've spent real time on why, one probe at a time.

It has the same shape the device does: a Julia lane for exact mathematics, an Ada/SPARK
lane where float behaviour is proved rather than asserted, with thirty-five open
verification conditions closed by running the prover per subprogram instead of whole-unit,
and Rust libraries behind one C ABI. Slate on the DevKit is that same Julia lane shrunk to
fit a Pi.

Then there's the model side. I've trained adapters, and a from-scratch pretrain is running
for the component that may only propose and never answer.
My own model work is real and small. Two fine-tuned models of mine already run, a role-tuned four-billion model from July and a behaviour-tuned point-eight-billion model from August, and a from-scratch transformer I call the subconscious is thirty-four thousand steps into pretraining on my own corpus, on the Mac mini. The inference side is my own server in Rust with candle on the CPU and an MLX lane on the GPU. That's where the comprehension tier goes: a small model I trained, on hardware I own.
Everything you've heard runs on hardware I already owned: a sixteen gigabyte M4 Mac mini that panics when its swap fills, a second Linux box with twenty-three gigabytes of RAM, an RTX 2060 with six gigabytes that can't hold a training run, an RX 580, and the DevKit. The mini is the bottleneck. Over the last one to three years I've spent about ten thousand dollars on this in total, all out of pocket, most of it renting compute I'd rather own.

Those aren't finished, and I'm not claiming they are. The DevKit product is what happens
when that discipline is aimed at one small board, and there, measured, today, it works."

---

## 5. The ask (4 minutes)

"I'm not here to ask for fifty thousand dollars. I'm here to show you what each amount does, because I'm going to keep building this either way. I'm a student with no income, and right now every hour of compute comes out of my pocket and every test runs on one Pi.

The advancement is what you heard. A device that answers most of what a household asks on its own hardware, in milliseconds, with no model call and nothing sent anywhere, and that tells you when it can't. That runs today. Each level buys more of it.

There are five milestones. One, the mechanical assistant finished: every exact-answer class complete, the suite kept at zero failures, the wheel published, the ability installable from your catalogue, the runbook and the bug ledger current. That's my time. Two, the ladder live: a machine in the house as the LAN rung and named cloud providers as the last rung, each offered by name and consented to by voice, measured end to end. Three, the library at full size: the encyclopedias I already own on the card, sixty-five more volumes are converted and waiting today, with the index built on a real machine and shipped built, so an offline device answers from an encyclopedia in under a second. Four, measured in other homes: two more DevKits in homes that aren't mine for a month each, every failure read from the logs and fixed. Five, the comprehension tier: my own inference and transformer work applied to the one tier that still uses a stock model, so the device can hold a conversation the way it holds a fact.

One purchase changes what I can do, and I want to name it plainly. A Minisforum MS-S1 MAX with 128 gigabytes of unified memory, or a Mac Studio at the same level. It's thirty-eight hundred dollars on sale today, forty-seven fifty at list. The memory is the point: 128 gigabytes the GPU can use holds a seventy-billion-parameter model quantised, so I can train and run the comprehension tier at home. The same box builds the library index in minutes instead of hours on the Pi, runs as the LAN rung, and stops me renting compute for a product whose whole argument is that a household shouldn't have to rent.

So the ladder. At fifty thousand, all five milestones, the machine, the hardware for testing, the training compute and frontier model access for the comprehension tier, and part-time help with packaging and review so milestone one lands in weeks instead of months. At ten thousand, milestones one, two and three in full and the machine: a fully mechanical assistant, installable, with the ladder live and the library at full size. At thirty-eight hundred to forty-seven fifty, the machine, and with it milestones one and three. At five hundred to two thousand, one more DevKit and test hardware, and milestone one on my own time. At nothing, I keep building it on the Pi, slower.

Three things I want out of this conversation, in order. First, tell me which conversation this is: grant, sponsored integration, or both. What's here is more than an ability and it's built on your hardware and your platform. Second, a paid milestone-based integration, so this is a supported path on the DevKit rather than one developer's card. Third, register the trigger words on agent 595324, and tell me whether you want the wake phrase to stay 'open home'."

---

## 6. Likely questions, and short answers

| Brady asks | Say |
|---|---|
| "What does OpenHome get out of it?" | Every turn answered on the device is a turn that costs the platform nothing, and works when the network doesn't. |
| "Why is the engine closed?" | The engine is a dependency, and none of it is hidden. The ability is MIT and readable; the engine is a wheel in `requirements.txt`, which your own local-ability docs describe as the way to bring code onto the DevKit. |
| "Can we review it, then?" | You review the shim, and that's the whole surface touching your platform. If you need more, tell me what and we'll scope it. |
| "How do we install it?" | The wheel needs a home, PyPI or a release asset. It's part of milestone one, a day's work once we agree where it lives. |
| "Does it need a platform change?" | Not to work. The Skill and the DevKit ability both run through the existing ability system. The one change is small, and only for the fully-local path: let a hardware ability answer and stop before the model call. |
| "Is it accurate?" | It refuses rather than guesses, and it can say why. Ask it the capital of Mongolia on the call, then ask why that didn't work. |
| "What about false wakes?" | With a video playing near it yesterday it woke a handful of times, each dismissed; the chime goes quiet after three in a row. I won't put a rate on it until I've trained on real recordings, and that's on the roadmap, not in the ask. |
| "Can it be interrupted?" | Yes, echo-gated so its own voice can't trigger it. The limit: a person has to be louder than the speaker by a clear margin. Proper echo cancellation on this HAT needs graph work I haven't shipped. |
| "Other languages?" | It hears about a hundred and says which one it heard. It answers in English, because translating its own sentences with a 1B model that invents names would be worse than saying so. |
| "What's still broken?" | KNOWN-BUGS.md, and it's dated: the cold-boot warm-up, the phone rung being off, echo cancellation, and Britannica's OCR damage, which it reads as it finds it. |
| "How long did this take?" | About three years of research on my own, the engine since spring, and the OpenHome work over the last month. |
| "Who else is on it?" | Me. At the full amount I'd bring in part-time help for packaging and review so milestone one lands in weeks. |
| "Could we build it ourselves?" | Then I'd rather be the reference implementation and contribute upstream. That's why v1 is already merged. |

---

## 7. Thirty minutes

| Elapsed | Minutes | What |
|---|---|---|
| 0:00 | 2 | Hello, and the one line: it answers most of what people ask it without the network, and asks before it uses anything that costs money. |
| 0:02 | 4 | **Section 1**: what's on the device, and the numbers. |
| 0:06 | 3 | **Live**: "open brain, run the demo". Let it run; don't talk over it. |
| 0:09 | 7 | **Section 2**: the mechanics. If you're behind, cut the loudness model first, the memory graph second. |
| 0:16 | 3 | **Live**: the capital of Mongolia, then "why didn't that work". Then `python3 demo.py --lanes` on screen. |
| 0:19 | 3 | **Section 3**: expansion and the roadmap. |
| 0:22 | 3 | **Section 4**: the bridge. If behind, compress to three things: the engine, the comprehension lane, the training bottleneck. |
| 0:25 | 3 | **Section 5**: the ask, and the three things you want. |
| 0:28 | 2 | Questions, and the close: next step in writing, with a date. |

**If you lose time**, protect three things: the demo running, "why didn't that work", and
the ask.

**Do not claim**: a LAN or cloud hand-off happening on the call, since no class needs it
today; say so. A false-wake rate in a room with a television. Any suite count not in
KNOWN-BUGS.md with a date.
