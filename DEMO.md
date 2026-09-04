# The demo

Two ways to run it. Both use the same script, and the script is a program, every line in
it goes through the live router on the live card, and the run fails loudly if any line
answers with nothing. Nothing here is a promise that hasn't already happened.

```
python3 demo.py                 run it silently, print what every line answers, with timings
python3 demo.py --speak         say it out loud on the device: both sides, real chimes
python3 demo.py --lanes         the ladder, and what is ready on each rung
python3 demo.py --section books one part
python3 demo.py --json out.json the whole transcript
```

**Run `python3 demo.py` before the meeting.** It writes nothing to the card, no timer, no
note, settings put back. If it prints `56 lines, 56 as scripted`, the
demo will work. If it doesn't, it names the line that broke and you have not been
surprised in front of anybody.

---

## The five minutes, if you only have five

Say the wake word, **"open brain"**, before each one. After it answers, the floor stays
open for a few seconds, so follow-ups need no wake word.

**1. It knows what it is** (10 seconds)

> *what can you do*
> "28 things, all on this device with nothing sent anywhere: your books, 682 facts,
> arithmetic and timers. Try 'what do the books say about entropy'. Say 'list everything'
> if you want all of them."
>
> (28 on the DevKit. The number is computed from the cost table for whichever machine it is
> on, a Mac says a different one, which is the point: it counts what it can do.)

**2. The instant class, no model, no network** (20 seconds)

> *what is twenty percent of eighty*, "20 percent of 80 is 16." (about a millisecond and a half,
> router end to end, measured on the DevKit)
> *what is one third plus one sixth*, "One third plus one sixth is one half." (exact, from
> a proven kernel, not floating point)
> *how many kilometres in twelve miles*, "12 miles is 19.31 kilometres."

These never touch a model: the time answers in under half a millisecond, arithmetic in
about a millisecond and a half, end to end.

**3. The card** (60 seconds). This is the one that lands.

> *how many books do you have*
> "3 books on the card: Modern C++ For Absolute Beginners, The Ultimate Python Handbook,
> The Lamp At Low Tide. There's also 2 sets of documentation in 66 files and 29 reference
> works in 57 volumes, 397,706 passages in all."
>
> *what do the books say about entropy*, a passage, with the book it came from.
> *tell me more about that*, it follows the subject.

Then pull the network cable out and do it again.

**4. It is worth talking to** (60 seconds)

> *tell me something interesting*, one of 682, and it never repeats.
> *another one* · *tell me a physics fact* · *tell me more about that*
> *flip a coin* · *roll two dice* · *tell me a riddle* → *I give up*
> *open the pod bay doors*, "I'm afraid I can't do that. Mostly because there aren't any,
> and I don't have hands."

**5. The ladder, and consent** (60 seconds), the argument of the whole product.

> *what is the capital of Mongolia*
> "I couldn't work that one out, and I won't guess."
> *why didn't that work*
> "It went to the part of me that works things out, and that came back with nothing it
> was sure of. I would rather say nothing than invent an answer."
>
> That is the consent argument as it stands today: it refuses rather than guesses, and it
> can say why. An offer BY NAME, "I could ask the Mac. Want that?", is made only when a
> class does not fit on this machine and does fit on another, and with today's cost
> profiles no class is in that position, so the device does not make the offer. The lane is
> live and reachable (`python3 demo.py --lanes` shows it); what it lacks is a question that
> needs it. KNOWN-BUGS.md has this under the premortem.

`python3 demo.py --lanes` prints the same ladder as a table, including what is *not*
ready, the phone rung is switched off and is never offered.

**To light the cloud rung before the meeting** (two edits on the device, no code):

```bash
# 1. switch a provider on
nano ~/astral-voice/hub-v2/data/routes.json      # "anthropic": {"enabled": true, ...}
# 2. give it a key, readable only by you
printf '{"anthropic":"sk-..."}' > ~/astral-voice/state/keys.json
chmod 600 ~/astral-voice/state/keys.json
python3 demo.py --lanes                          # it now says: cloud: Claude, yes
```

Any of the six providers in routes.json works the same way. Claude, ChatGPT, Gemini,
Groq, Mistral, OpenRouter, plus OpenHome's own agent, and each is offered by its own name. A provider switched on
with no key is deliberately *not* offered: a route that cannot answer is worse than no
route.

**6. It never goes quiet** (20 seconds)

> *why didn't that work*, it tells you, from the live decision, not an apology.
> *what did you say*, it repeats.

---

## What to say about the numbers

- **3,593 checks on a Mac and 3,636 on the DevKit, all 26 suites, 2026-09-03.** The suites are named after
  what they prove, not the files they touch.
- **The thinking tick runs until the first word** and can no longer start after the answer
  chime; a silent second while somebody waits is the thing that makes a device feel broken.
- **397,706 passages**, indexed in about three minutes, looked up in 1 to 58 ms.
- **1.5 s** for mechanical comprehension of a question it has never seen, no model.
- One evening of real use produced four bugs, all now permanent checks. That is the process,
  and it is worth saying out loud.

## If something goes wrong on the day

- Nothing answers → `systemctl --user status astral-hub` on the device; `--user`, not root.
- It answers but sounds quiet → *turn the chimes up*, out loud. It is a setting now.
- A line in the script fails → run `python3 demo.py --section <name>` to see that part.
- If you switch the Mac rung on to show it, it is offered but unreachable → start the listener on the Mac:
  `python3 hub/lan.py serve`.
