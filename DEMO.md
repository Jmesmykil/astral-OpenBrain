# Demonstrating it

Everything below has been spoken at the device and answered by it. Nothing here is
aspirational, and nothing needs the network.

## Before you start (two minutes)

```bash
deploy/install_v2.sh openhome@192.168.1.23 --start   # stops the kiosk: one mic, one owner
```

Then check the line it prints:

```
wake:       open brain, open home (phrase recogniser)
kernel:     astral-kernel 2.2.0 (compiled, system python)
library:    6 sources: books, docs, reference
slate:      active          # exact mathematics, warm ~40s after a restart
astral-hub: active
```

If `slate` has just restarted, give it a minute before asking for calculus — it will say
so itself if you don't ("the maths kernel is still starting").

Speaker at about 40%. The microphone is a metre from the speaker on this hardware; step
closer than that and everything below works first time.

## The five minutes that show what it is

Say each one as one sentence. **Do not wait for a chime** — the wake word and the question
belong together, which is the whole point.

**1. It is instant, and it is exact.**
> "Open brain, what is twenty percent of twenty four thousand three hundred and fifty two."

*20 percent of 24352 is 4870.4.* — a table lookup, microseconds, no model anywhere.

**2. It reads your own books.**
> "Open brain, what does the book say about list comprehensions?"

Answers from your Python handbook, with the book named.

**3. It knows the shape of them.**
> "Open brain, what is in chapter forty of modern C plus plus?"

*31 under chapter 40: Range-based Loops, Initializer Lists, Move Semantics…* — read from
the book's own table of contents, with page numbers.

**4. It tells you what it has before it reads at you.**
> "Open brain, tell me about Turing machines."

*I have 31 passages on Turing machines, in one source: Encyclopedia Of Computer Science.
Most of it is under 4.3.* Then: **"read me the first one."**

**5. It asks before it spends anything.**
> "Open brain, summarise Turing machines."

The passage's own sentences, then: *"I can put that in my own words instead — about a
minute on this device. Want that?"* Say yes and the local model answers; every word it
adds that is not in the passage is refused out loud.

**6. It stays quiet when it should.**
> "Open brain, the weather is nice today."

Nothing. Not a shrug, not a guess — a quiet tone, because that was not a question.

## If somebody asks "what happens when it can't?"

Turn on a cloud provider (`hub/data/routes.json`, plus a key in
`~/astral-voice/state/keys.json`) and ask something out of reach:

> *"I can't do that here. I could ask the Mac, the OpenHome agent, or Claude. Which one?"*

Say **"Claude"** and it goes to Claude. Say **"yes"** and it takes the nearest one — never
the cloud. Say **"no"** and nothing leaves the house. That is the product.

## Through OpenHome's own agent

Needs one thing first: the trigger words registered on agent 595324 at app.openhome.com.
After that, their wake word and their speech-to-text drive the same engine, and the same
answers come back — measured through their dispatch at 0.2 to 0.9 seconds.

## What to say about the parts that are not finished

Say them. They are more convincing than the parts that work:

- The wake word is a phrase recogniser, not a trained keyword: **zero false wakes in five
  minutes of a quiet room**, and it will wake at a television saying "open home".
- The local model is a 1B on an SD card: **a minute a go**, and it invents names, which is
  why every answer it gives is checked against the passage and refused if it drifted.
- Exact mathematics needs its kernel warm — **forty seconds after a boot**.
- The daemon that answers without a trigger word is written and tested against a faked
  platform, and has never run against the real one.
