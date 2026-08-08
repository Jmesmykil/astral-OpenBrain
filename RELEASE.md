# Astral

A local deterministic layer for OpenHome. It answers the simple, exact-answer questions on the device with no cloud trip, and hands everything else to the agent.

## The idea

Every request on the DevKit goes to the cloud right now. "What time is it." "What's 20 percent of 80." "Convert 10 pounds to kilograms." Those have one right answer. They do not need a model, and they do not need the network.

Astral catches that class first. It wakes on the device, transcribes on the device, and answers on the device. The LLM never gets touched for it. Only the hard stuff goes to the agent.

This is not an LLM replacement. The LLM still does the real thinking. Astral is the fast layer in front that stops the round-trip for questions with one answer. A local reflex before the brain has to wake up.

## How it works

```
you speak
  -> wake word            (on device)
  -> speech to text        (on device)
  -> Astral checks: is this an exact-answer question?
        yes -> answer on the device, speak it, stop     (no cloud)
        no  -> hand the turn to the agent                (normal cloud flow)
```

The one piece OpenHome needs to add is the gate. When Astral has the answer, it speaks and stops instead of waking the LLM. That is the whole core change, a boolean on the turn. Everything else is a normal ability package.

## What it answers today

Time and date. Math. Money, including tips, tax, and splitting a bill. Unit conversions across weight, length, volume, and temperature. Device status: temperature, uptime, disk, memory.

Run on a Pi 4 DevKit with the network off:

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

All of it is plain pattern-and-table code. No model, no `eval`, microseconds per answer. When a phrase is not something it can answer for certain, it returns nothing and the agent takes the turn. It stays out of the way.

## Speech to text

Local by default, since the goal is no cloud. On the DevKit that is whisper base.en, quantized, running during the short listen window. It can fall back to a small cloud STT for consistency when a device needs it. Both are options at release, and they get better as the tech does.

## What is proven, and what OpenHome needs to add

Proven on the DevKit with the network off: wake, local speech to text, and the deterministic answers, end to end. The same answer handlers also run through OpenHome's own `devkit-capability` path, so they already fit the ability system.

Needs OpenHome: the gate before the LLM callout, so the local layer can answer and stop. That is the one ask. It lines up with the primitives work the team is already considering and with passing information cleanly to and from the main flow.

## The package

`community/astral/`, in the OpenHome ability format:

- `main.py` — the cloud-side capability. Deterministic dispatch, no LLM routing.
- `devkit_functions.py` — the device side. One self-contained file: the time/date and math/money/conversion engine is inlined, so it needs no siblings and can't break on deploy.
- `README.md` — trigger words, setup, and how it works.
- `requirements.txt` — Python standard library only.

OpenHome manages the platform `config.json` at runtime, so the ability ships without one. Trigger words go in the dashboard.

## Try it

Astral ships as a community ability, the same route as the others:

1. Fork `openhome-dev/abilities` and branch off `dev`.
2. Add the folder as `community/astral/`.
3. Set trigger words in the OpenHome dashboard and connect a DevKit.
4. Open a PR against `dev`.

The ability answers the exact-answer class on the device through the ability system. The fully local path, wake and speech-to-text on the device too, is proven with the network off and goes native as the agent gains the ability to run a hardware ability before the LLM. That piece is moving now.

## Later

A heavier local layer using datasets and a mechanical transformer on the device, for comprehension past the exact-answer class. Separate track, bigger swing. The release above does not depend on it, and it does not inherit its hardware needs.
