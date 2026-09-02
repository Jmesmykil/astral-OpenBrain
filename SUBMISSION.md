# Astral for OpenHome

Status: accepted. PR #361 was approved and merged into `dev` on 2026-08-31. Follow-ups from the review are staged as a second PR (`deploy/README.md`).

## What it is

Astral answers the simple questions on the device, with no cloud trip.

Right now the DevKit sends every request to the cloud for speech-to-text and an LLM turn. That includes "what time is it," "what's 20 percent of 80," and "convert 10 pounds to kilograms." Those questions have one right answer. They never needed a model, and they never needed the network.

Astral is a fast deterministic layer that sits in front of the agent. It catches that class of request, wakes on the device, transcribes on the device, and answers on the device. The LLM never gets touched for it. Only the hard stuff hands off to the agent. So this is not an LLM replacement. The LLM still does the real thinking. Astral stops the round-trip for questions with one exact answer.

It is opt-in. Not installed, the agent works the way it does today. Installed, the user gets instant local answers for the everyday stuff and the cloud agent for everything else.

## What we proved

We built the full local path and ran it on real hardware, a Raspberry Pi 4 with the Google Voice HAT, with the network off:

- Wake on the device (openWakeWord).
- Speech-to-text on the device (whisper base.en, quantized).
- A deterministic engine that answers with plain pattern-and-table code, no model:

```
what time is it                    -> It's 2:37 pm.
what is the date                    -> Today is Friday, August 7, 2026.
what is twenty percent of eighty    -> 20 percent of 80 is 16.
convert ten pounds to kilograms     -> 10 pounds is 4.54 kilograms.
how many cups are in two liters     -> 2 liters is 8.45 cups.
eighteen percent tip on forty five dollars
                                    -> A tip of 18 percent on 45 dollars is 8.1 dollars, for a total of 53.1.
seventy fahrenheit to celsius       -> 70 degrees Fahrenheit is 21.11 degrees Celsius.
what is the square root of 155       -> The square root of 155 is 12.45.
tell me a joke                       -> (nothing; the agent takes it)
```

The same engine also runs through OpenHome's own `devkit-capability` path, so the handlers already fit your ability system.

## The one change on your side

The deterministic layer needs a gate before the LLM callout. If the layer already has the answer, speak it and stop. That is the boolean the core change turns on. Everything else ships as a normal ability package. This is the small modification. It matches what you raised about better primitives and passing information to and from the main flow.

## Speech-to-text is an option, not a lock-in

Local STT is the default, since the goal is no cloud trip. It can fall back to a small cloud STT for consistency when a device needs it. These are options at release, and they get better as the tech does.

## What's in the package

`community/astral/`, in the OpenHome ability format:

- `main.py` — the cloud-side capability. Deterministic dispatch, no LLM routing.
- `devkit_functions.py` — the device side. One self-contained file: the engine is inlined, so it needs no siblings. Pattern and table based, no `eval`.
- `README.md` — trigger words, setup, and how it works.
- `requirements.txt` — Python standard library only.

## Why you'd want it

The simple class answers on the device, so it is faster than a cloud turn and it works with the network down. Every catch is one less cloud inference. It is a layer in front of the agent, not a fork of the runtime, so it carries no maintenance on your side.
