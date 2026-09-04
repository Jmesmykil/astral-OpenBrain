# Spoken script — Brady / OpenHome, 30 minutes, 2026-09-04

Read this out loud once before the call. Everything stated as a number below was measured
on the DevKit or the Mac and is in KNOWN-BUGS.md with its date. Anything in `[YOU: …]` is
yours to say — do not read the bracket.

---

## 1. What is on the device today (open with this — 4 minutes)

"Thanks for the time. Let me start with what's running on the DevKit right now, because
the rest of the call makes more sense after it.

The whole loop is on the Pi 4 with the XMOS HAT, and nothing leaves it. The wake phrase
is a Vosk grammar — two phrases and an everything-else bucket, so the room is never
transcribed. Speech-to-text is whisper base.en, q5_1. The voice is piper. Above those
there's a compiled answer kernel — `astral_kernel` 2.2.0, built aarch64 on the device — a
Julia mathematics kernel running as a service, and a small model, Llama 3.2 1B Instruct at
Q4_K_M, served by llama-server on port 8791. That's the whole stack. No network in the
answer path.

The levels it hits: the mechanical class — time, date, arithmetic, unit conversion, 'what
can you do' — answers in one to eleven milliseconds, median, on the device. The library
class, passages out of the books and encyclopedias and the curated facts, is sub-second
warm. Comprehension in its own words is seconds. One honest number: after a cold reboot,
the first library question took forty seconds once. That's the index warming off the card,
and I'm fixing it with a warm-up at boot.

On the card: three books, two documentation sets across sixty-six files, a reference shelf
— Britannica, world history, physical science, about three hundred thousand passages — six
hundred and eighty-two curated facts, and twenty-eight local abilities.

Two more numbers that matter more to me than the features. Three thousand six hundred and
thirty-six checks held on the DevKit across twenty-six suites, zero failed; three thousand
six hundred and thirteen on the Mac, zero failed. And every new gate I write, I prove red
before I trust it green — if a check has never failed, I don't know that it checks
anything.

Yesterday I ran the scripted voice demo under scrutiny: twelve questions asked and
answered by voice, twelve of twelve as scripted, two hundred and sixteen to two hundred
and seventy-two seconds, and it left the settings, the hooks and the notes exactly as it
found them."

---

## 2. The mechanics — how it actually works (7 minutes)

"The loop is: wake, burst-record, transcribe, route, speak. Half-duplex, because this HAT
has no hardware echo cancellation — after every sound it makes, it flushes the microphone
and holds a refractory window so it can't answer its own voice.

**Router and tiers.** One place decides run, ask, or stay silent. It names the command
class a phrase needs, asks a fits table what this host may do with that class, and returns
something the loop can act on without a second opinion. Tier 0 is pattern and table code,
microseconds. Tier 1 is a native kernel or an indexed corpus on the card. Tier 2 is
comprehension. Every class carries a measured cost profile for the machine it's on,
written by a script that runs the real engine over the real corpus.

**Budgets inform, they don't block — learned the hard way.** The budgets file holds a
ceiling per tier per host. The library index grew from two hundred and thirty-one thousand
passages to three hundred and nine thousand, the measured 95th percentile crossed the
ceiling by two hundred and fifty-eight microseconds, and the device correctly and
completely switched its own library off. Every book question answered with nothing. A
ceiling that kills a capability at a margin of three hundredths of a percent is a number
chosen wrongly, not a capability that failed. Storage classes carry their own budgets now,
because a file write is not a table lookup. And a class measured slow here goes to a second
lane — 'I'll look that up while we talk' — with the answer landing in a pause rather than
over a sentence.

**The kernel as a shim.** Your contributing rules are MIT, readable and security-scanned,
and a local ability is exactly three files with `devkit_functions.py` named exactly that.
So the ability is a thin MIT shim, three hundred and forty-three lines: it finds the hub,
falls back to the compiled kernel, and if neither is there it says why rather than failing
quietly. My engine ships the way any Python dependency ships, a wheel named in
`requirements.txt`. Nothing proprietary hides inside the MIT file, and nothing in the MIT
file needs my engine to be readable in review. That seam is documented in BOUNDARY.md —
I'd rather have it on the table than smuggle a blob into a PR.

**The mathematics kernel.** Julia with an Ada/SPARK oracle behind a C ABI. It takes about
forty-three seconds to come up on this board and milliseconds after that, so one process
owns it and both callers talk to it over a Unix socket. Before that the ability paid the
start on every turn and then honestly offered to send the question away — a local-first
device giving up exact mathematics it can do, because of a process boundary. Exact
arithmetic is computed twice, Python's fractions and the SPARK oracle, and they must agree
before a word is spoken. A disagreement is a silence, never a guess.

**Memory and consent.** Nothing is written until somebody says 'remember me'. It's a
property graph on the card, with a clock reading on every row. 'Forget me' deletes the
file, not the rows. Notes mode is separate and announces itself. Conversation context lives
in process memory, times out, and is never written down.

**The loudness model.** Measured as RMS at the device, the wake chime was sixteen thousand
eight hundred, the tick five thousand seven hundred, the ready tune three thousand one
hundred — five to one, which is why no setting could ever make it consistent. Every file
and every sentence is levelled to one target now before its relative and the chime lift
apply, under one master that only a person moves.

**The ear.** Yesterday I found the microphone running two full seconds behind the room.
`parec` with no stated latency inherits pipewire-pulse's default record fragment, and
that's two seconds — so every wake phrase, every interruption and every flush was acting on
a room that no longer existed. At fifty milliseconds, with the pipe widened so a flush
really empties, the same sound is heard six hundred and sixty milliseconds after its player
launches. Barge-in is echo-gated on top: a wake matched while the device speaks counts only
if the last eight-tenths of a second at the microphone is above a measured threshold, and
its own echo sits below it. A false barge is harmless — it resumes the sentence from just
before the cut.

**Test discipline.** Twenty-six suites named for what they prove, run against a scratch
copy of the device's state so a check can never touch the card. One suite's only job is to
prove nothing fails silently — it reads the refusal reasons out of the source and fails the
build if any path can go quiet."

---

## 3. Where it goes next (4 minutes)

"The ladder is four rungs: mechanical here, a model here, a machine in the house, then a
named cloud provider. It exists in code today, with consent by name — 'the Mac, or
Claude?' — because 'the cloud' is not something a person can choose between. Only the
local rungs are live. The cloud hand-off is designed and not connected, and that's
deliberate: I'll add the optional cloud when the ranking reaches a level that needs it.
Today no class is in that position, so the device doesn't make the offer. A route that
can't answer is worse than no route.

The near list: a trained wake model from real recordings, so a false-wake number in a room
with a television is a measurement instead of an estimate. Sound packs already ship — your
house set is the default, and any folder dropped in is a pack. Languages: it hears about a
hundred and says which it heard, rather than translating its own sentences with a 1B model
that demonstrably invents. And a second household, a DevKit running a month in a home that
isn't mine. That's the test I can't run alone."

---

## 4. The bridge — this is the small end of something bigger (5 minutes)

"I want to be straight about where this came from, because it explains why the device is
built the way it is. The DevKit work is the smallest node of a local-first system I've
been building.
[YOU: one line on when you started and what pulled you into it — your history, not the repo's.]

Underneath it there's an orchestration engine I run locally: prime directives that gate
what any process may do, product isolation so two projects can never be conflated into one
build path, and a coordination bus where a process claims the work before it touches
anything. The rule that matters here is the same one the device follows — evidence or
silence. A claim without a receipt isn't done.

Beside it there's a deterministic comprehension engine. Its law is that a reading becomes a
belief, not a fact: revisable, carrying its inferential provenance and a condition that
would overturn it, and only a gate promotes anything to actual. It stores a sentence one of
two ways — as 'this document states…' with no subject bound, which by design can never be
promoted, or as a typed reading with a real subject, predicate and object, which can.
Measured on the live ledger, ninety-nine point nine percent of a seventy-gigabyte library
landed in the first lane. That's not a bug: it's the engine telling the truth about what it
did not understand, and the remedy is a re-read with comprehension on — seventeen and a
half percent typed on one documentation set. It abstains rather than guesses, and I've
spent real time on why, one probe at a time.

It has the same shape the device does: a Julia lane for exact mathematics, an Ada/SPARK
lane where float behaviour is proved rather than asserted — thirty-five open verification
conditions closed by running the prover per subprogram instead of whole-unit — and Rust
libraries behind one C ABI. Slate on the DevKit is that same Julia lane shrunk to fit a Pi.

Then the model side. I've trained adapters, and a from-scratch pretrain is running for the
component that may only propose and never answer.
[YOU: two sentences on what your custom transformer and inference work actually does —
architecture, objective, what it's for — in your own words.]
[YOU: name the machines you own, what each is doing today, and which is the bottleneck.]

The point isn't that those are finished. It's that the DevKit product is what happens when
that discipline is aimed at one small board — and there, measured, today, it works."

---

## 5. The ask (4 minutes)

"So: the fifty-thousand-dollar developer grant, and what it buys.

Five milestones. One, the trained wake word from real recordings, with a false-wake rate
measured in a room with a television — recording sessions, training compute, my time. Two,
the ladder live: a class that genuinely needs the LAN or a named cloud rung, offered and
consented to by voice, measured end to end — LAN machine time, provider credits, my time.
Three, installable: the wheel published, the ability in your catalogue, trigger words
registered. Four, a second household, running a month, log read weekly. Five,
documentation and hand-over, with your review feedback folded in.

Most of that is time — this is one developer's work, and the hardware is a small part of
the cost, with one exception I want to name plainly. The largest single piece of equipment
I need is a machine that can do the training and inference work locally. That lane is the
bottleneck in everything I've described: the wake model, the comprehension work, the
component that proposes. Local-first has to mean the training is local too, or I'm renting
the thing my whole product argument says you shouldn't have to rent.
[YOU: name the machine you want and roughly what it costs — GPU, memory, and why that tier.]

The rest funds continuing the research: the reading lane, the abstention work, and the
proof lanes that keep the answers honest.

Three things I want out of this conversation, in order. First, tell me which conversation
this is — grant, sponsored integration, or a role. What's here is more than an ability and
it's built on your hardware and your platform. Second, a paid milestone-based integration,
so this is a supported path on the DevKit rather than one developer's card. Third,
register the trigger words on agent 595324, and tell me whether you want the wake phrase
to stay 'open home'."

---

## 6. Likely questions, and short answers

| Brady asks | Say |
|---|---|
| "What does OpenHome get out of it?" | Every turn answered on the device is a turn that costs the platform nothing, and works when the network doesn't. |
| "Why is the engine closed?" | It isn't hidden — it's a dependency. The ability is MIT and readable; the engine is a wheel in `requirements.txt`, which your own local-ability docs describe as the way to bring code onto the DevKit. |
| "Can we review it, then?" | You review the shim — that's the whole surface touching your platform. If you need more, tell me what and we'll scope it. |
| "How do we install it?" | The wheel needs a home, PyPI or a release asset. Milestone three, a day's work once we agree where it lives. |
| "Does it need a platform change?" | Not to work — the Skill and the DevKit ability both run through the existing ability system. The one change is small, and only for the fully-local path: let a hardware ability answer and stop before the model call. |
| "Is it accurate?" | It refuses rather than guesses, and it can say why. Ask it the capital of Mongolia on the call, then ask why that didn't work. |
| "What about false wakes?" | With a video playing near it yesterday it woke a handful of times, each dismissed; the chime goes quiet after three in a row. I won't put a rate on it until I've trained on real recordings — milestone one. |
| "Can it be interrupted?" | Yes, echo-gated so its own voice can't trigger it. The limit: a person has to be clearly louder than the speaker. Proper echo cancellation on this HAT needs graph work I haven't shipped. |
| "Other languages?" | It hears about a hundred and says which one it heard. It answers in English, because translating its own sentences with a 1B model that invents names would be worse than saying so. |
| "What's still broken?" | KNOWN-BUGS.md, and it's dated: the cold-boot warm-up, the phone rung being off, echo cancellation, and Britannica's OCR damage — it reads what's there. |
| "How long did this take?" | [YOU: your real timeline, in one sentence.] |
| "Who else is on it?" | Just me. [YOU: say whether you'd bring anyone in on a funded scope.] |
| "What if we build it ourselves?" | Then I'd rather be the reference implementation and contribute upstream. That's why v1 is already merged. |

---

## 7. Thirty minutes

| Elapsed | Minutes | What |
|---|---|---|
| 0:00 | 2 | Hello, and the one line: it answers most of what people ask it without the network, and asks before it uses anything that costs money. |
| 0:02 | 4 | **Section 1** — what's on the device, and the numbers. |
| 0:06 | 3 | **Live**: "open brain, run the demo". Let it run; don't talk over it. |
| 0:09 | 7 | **Section 2** — the mechanics. If you're behind, cut the loudness model first, the memory graph second. |
| 0:16 | 3 | **Live**: the capital of Mongolia, then "why didn't that work". Then `python3 demo.py --lanes` on screen. |
| 0:19 | 3 | **Section 3** — expansion and the roadmap. |
| 0:22 | 3 | **Section 4** — the bridge. If behind, compress to three things: the engine, the comprehension lane, the training bottleneck. |
| 0:25 | 3 | **Section 5** — the ask, and the three things you want. |
| 0:28 | 2 | Questions, and the close: next step in writing, with a date. |

**If you lose time**, protect three things: the demo running, "why didn't that work", and
the ask.

**Do not claim**: a LAN or cloud hand-off happening on the call — no class needs it today,
say so. A false-wake rate in a room with a television. Any suite count not in
KNOWN-BUGS.md with a date.
