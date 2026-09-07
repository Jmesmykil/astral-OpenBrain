# Astral V2 — capabilities and mechanics

A voice assistant that runs entirely on the OpenHome DevKit. It hears, thinks and answers
locally. Nothing leaves the house unless the owner says yes.

Kernel `astral-kernel 2.2.7` · library index schema 33 · 5,269 checks passing, 0 failed,
0 skipped.

---

## The loop

| | |
|---|---|
| **Wake** | Vosk phrase recogniser on "open brain" or "open home". Near misses count — "open brian" wakes it. |
| **Hearing** | whisper.cpp `base.en-q5_1`, on device. The capture window sizes itself to the question, so a long sentence keeps its ending. |
| **Answering** | Compiled Cython kernel. Tier-0 answers resolve in microseconds without entering Python. |
| **Speaking** | Piper TTS. A thinking tick runs until the words actually start, so silence never lands where somebody is waiting. |
| **Open floor** | After an answer the floor stays open for a few seconds, so follow-ups need no wake word. Overheard room speech is ignored rather than answered. |

## Ranking and deferral

| | |
|---|---|
| **Measured, not assumed** | Every command class is timed on the machine it runs on and written to a cost profile. The routing table is measurements, not intentions. |
| **Offers by name** | Work too heavy for the Pi is never silently escalated. It asks: "I'd need the Mac for that. Want me to send it there?" |
| **Rungs** | Local model → Mac → phone → cloud. A rung is offered only when its own measured profile says the work fits there. |
| **Cloud ships off** | Disabled by default. A provider without a key is never offered — offering a route that cannot answer turns a refusal into a wrong promise. |

## The card as a research shelf

| | |
|---|---|
| **Drop and go** | Books, PDFs, EPUBs, papers, notes and code on the SD card are indexed and searchable. 577,773 passages across 191 files on this card. |
| **Read by page** | "Read me page 42 of the python handbook", then "the next page". Chapters and contents pages as well. |
| **Misheard titles** | A title mangled by the microphone still finds the book — "moderate" reaches *Modern C++* — but a book that is not on the card is refused, never substituted. |
| **Honest about gaps** | A source with no page breaks says so and offers search instead. Anything it fails to read is recorded and can be asked about out loud. |

## Conversation and memory

| | |
|---|---|
| **Follow-ups** | "What time is it" → "and in London". "20 percent of 80" → "and thirty percent". The frame carries, the subject swaps. |
| **Another one** | After a joke or a fact, "another one" asks again. |
| **Recall** | "What did we talk about" returns the subjects. The boot greeting reads from the same store. |
| **Commands stay commands** | A follow-up that is really a new request — "and turn off the lights" — is carried out rather than folded into the previous question. |

## Also on board

| | |
|---|---|
| **Timers and alarms** | Set, ask, cancel. Due alerts interrupt and speak. |
| **Device control** | MQTT out. Compound commands — "turn off the lights and close the blinds" — name both halves or do neither. |
| **Maths** | Arithmetic and units in the kernel. Calculus, algebra and physics through a resident Slate kernel with a proven exact-arithmetic oracle behind it. |
| **Reference** | Dictionary, 682 facts, encyclopedias, flashcard decks, notes and jokes, all local. |
| **Languages** | Reports honestly what it can hear against what it can speak, per voice on the card. |

---

## Two notes for OpenHome

Both reproduced against the published CLI `0.1.42`.

**`assign` reports success without taking effect.**

```
$ openhome assign --agent <id> --capabilities <id> --json
{"ok":true,"agent_id":"...","assigned":["8854"],"count":1,"message":"Updated with 1 ability(s)."}

$ openhome status <ability> --json
"personality_ids": []
```

Empty before the call and after it.

**`validate` approves code the upload path rejects.**

```
$ openhome validate ./ability
All checks passed. Ability is ready to deploy!

$ openhome deploy ...
Deploy failed: Forbidden use of 'getattr' (background.py, Line: 279)
```

`getattr` does not appear anywhere in the published package, so the rule is enforced
server-side only and is discovered at the last step. Reproduced with a minimal ability
whose only notable content is one `getattr` call.
