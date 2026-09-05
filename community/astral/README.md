# Astral. OpenHome Ability
![Community](https://img.shields.io/badge/OpenHome-Community-orange?style=flat-square)
![Local](https://img.shields.io/badge/Category-Local-green?style=flat-square)

## What this is

> Version 2.2.1, 2026-09-04: the engine wheel is installed from a GitHub release named in
> `requirements.txt`; the ability asks the local hub first when it is installed and the
> engine otherwise; `openhome validate community/astral` passes. Source and history:
> https://github.com/Jmesmykil/astral-OpenBrain.

Astral answers the exact-answer class on the device, without the LLM: time, date, math, money, unit conversions, grades, physics, chemistry, statistics, DevKit telemetry, and simple device control over MQTT. You ask in plain language, the device computes the answer with pattern-and-table code, and the agent speaks it. When a request is not an exact-answer question, Astral speaks nothing and the agent takes the turn.

There is no LLM routing and no model on the device. The answers are deterministic and take microseconds.

> Local abilities cannot be tested in the Live Editor. They run on a connected DevKit.

## What it answers

| Ask | Answer |
|-----|--------|
| "what time is it" | It's 3:10 pm. |
| "what's the date" | Today is Friday, August 7, 2026. |
| "what's twenty percent of eighty" | 20 percent of 80 is 16. |
| "convert ten pounds to kilograms" | 10 pounds is 4.54 kilograms. |
| "how many cups are in two liters" | 2 liters is 8.45 cups. |
| "eighteen percent tip on forty five dollars" | A tip of 18 percent on 45 dollars is 8.1 dollars, for a total of 53.1. |
| "seventy fahrenheit to celsius" | 70 degrees Fahrenheit is 21.11 degrees Celsius. |
| "square root of 155" | The square root of 155 is 12.45. |
| "device temperature" | The DevKit is at 64 degrees Celsius. |

Also: day of the week, addition, subtraction, multiplication, division, percentages, splitting a bill, tax, length and weight and volume and temperature conversions, uptime, disk, and memory.

## For students

The same idea, aimed at the questions that come up in a course. These are the ones a model answers fluently and sometimes wrongly, which is why they should not go to a model.

| Ask | Answer |
|-----|--------|
| "I have an 87 and the final is worth 20 percent, what do I need to get a 90" | You'd need 102 percent on the final for 90 percent, which isn't possible. A perfect final leaves you at 89.6 percent. |
| "what's my grade if I got 42 out of 50" | 42 out of 50 is 84 percent, a B on a standard 90/80/70 scale. |
| "molar mass of water" | The molar mass of water (H2O) is 18.015 grams per mole. |
| "how many moles in 36 grams of water" | 36 grams of water is 1.998 moles, at 18.015 grams per mole. |
| "escape velocity of mars" | Escape velocity at Mars is 5.03 kilometers per second, 11245.35 miles per hour. |
| "how far does something fall in 3 seconds" | In 3 seconds it falls 44.13 meters, 144.78 feet, ignoring air resistance. |
| "standard deviation of 4 6 8 10" | The sample standard deviation of 4, 6, 8, 10 is 2.58, around a mean of 7. |
| "is 91 prime" | No, 91 isn't prime. It's 7 times 13. |
| "42 in binary" | 42 in binary is 101010. |
| "solve the quadratic 1 5 6" | With a 1, b 5, c 6 the roots are -2 and -3. |

Grades: what you need on the final, weighted course totals, percent to letter, score out of total, GPA over credits. Chemistry: molar mass for any formula or a named compound, moles and grams, molarity, pH, the ideal gas law, atomic mass and number for all 118 elements. Physics: escape velocity and surface gravity for the Sun, the Moon and every planet, weight on another world, free fall, kinetic and potential energy, momentum, force, work, power, Ohm's law, time dilation, Schwarzschild radius, photon energy, light travel time. Statistics: mean, median, mode, range, variance, sample and population standard deviation, z scores, combinations and permutations. Number tools: binary, hex and octal, logs, trig, GCD and LCM, primes and prime factors, modulo, the quadratic formula, percent change, fractions, significant figures, scientific notation. Units now also cover energy, pressure, force, data sizes, and astronomical distances.

Two things it says out loud rather than assuming. Anything that depends on a grading scale names the scale, because the scale is a convention and not a fact. A standard deviation says whether it is the sample or the population one, because those are different numbers and a course grades you on which you used.

**Device control (MQTT).** It understands the command, not only on and off. It extracts action, device, attribute, and value from plain speech, so "turn on the kitchen light", "dim the bedroom light to 30", "set the thermostat to 72", and "lock the front door" all parse, and it publishes to `home/<device>/...` with no LLM. It remembers the last device, so a follow-up like "turn it off" resolves. Universal by topic, so it works before you set up a device registry; without an MQTT broker it says so plainly instead of failing silently.

## Suggested trigger words

Set these in the OpenHome dashboard. Pick the ones you want.

`what time`, `what's the time`, `what's the date`, `what day is it`, `calculate`, `what's`, `how much is`, `percent of`, `square root of`, `convert`, `how many`, `tip on`, `tax on`, `split`, `turn on`, `turn off`, `switch`, `toggle`, `dim`, `set`, `lock`, `unlock`, `open`, `close`, `device temperature`, `uptime`, `disk usage`, `memory usage`

For the student set: `what do I need`, `what letter grade`, `out of`, `weighted`, `gpa`, `molar mass`, `molecular weight`, `how many moles`, `atomic mass`, `atomic number`, `symbol for`, `molarity`, `ph of`, `escape velocity`, `surface gravity`, `how much would I weigh`, `kinetic energy`, `potential energy`, `momentum`, `schwarzschild`, `time dilation`, `mean of`, `median of`, `standard deviation`, `variance of`, `z score`, `choose`, `in binary`, `in hexadecimal`, `log of`, `log base`, `sine of`, `cosine of`, `prime`, `prime factors`, `quadratic`, `percent change`, `simplify`, `significant figures`

## How it works

**Cloud side (`main.py`).** On a trigger word it takes the transcript and sends it straight to the device with `send_devkit_capability_action(function_name="respond", args=[transcript])`. No LLM routing. It speaks the device's `spoken_response`, or nothing if the device returns an empty one, then calls `resume_normal_flow()`.

**Device side (`devkit_functions.py`).** One self-contained file. `respond` runs the transcript through the inlined engine and emits a structured result. The engine is one router with a fixed order: time and date, then grades, chemistry, physics, statistics, number tools, and plain arithmetic last. Specific before general, because the general one will match a fragment of a specific question. The result:

```json
{ "success": true, "spoken_response": "It's 3:10 pm.", "data": { ... }, "error": null }
```

An empty `spoken_response` means no exact answer, so the agent takes the turn.

**Without a trigger word (`background.py`).** Trigger words only cover the turns somebody
thought to register. The optional background daemon covers the rest: it starts with the
session, reads the live transcript with `get_full_message_history()`, offers every turn to
the same `respond` on the device, and, only when the device has an exact answer, calls
`send_interrupt_signal()` and speaks it. When the device has nothing, which is most turns,
it does nothing at all and OpenHome's normal routing handles the turn the way before.
The local layer is a filter in front of the agent, not a replacement for it, and the
failure mode of the filter is silence.

It also speaks timers and reminders when they come due (`due_alerts`), which nothing else
can do: a foreground ability is a subprocess that exited minutes ago.

Upload it as a second ability with `category=background_daemon`, containing `background.py`
alongside the same `devkit_functions.py`. Two things about it are honest unknowns until it
runs on hardware, and both fail safe: whether a non-`local` ability may call
`send_devkit_capability_action` at all (if it may not, every call returns an error, which
this reads as "not mine", and the daemon stays silent forever), and whether the daemon
every time beats the agent to the turn. See `KNOWN-BUGS.md`.

## Speech to text is an option

This ability version uses the agent's speech-to-text, so the transcript comes from the cloud. For a fully local path, wake and speech-to-text also run on the device (whisper base.en, quantized), so the exact-answer class answers with no cloud trip at all. That local path is proven on the DevKit with the network off. It becomes native once the agent can hand the turn to a hardware ability before the LLM, which the platform is moving toward.

Both paths use the same engine. Local speech-to-text is the default when it is available; a small cloud speech-to-text is the fallback for consistency. These are options, and they get better as the tech does.

## Requirements

- An OpenHome DevKit running the device-side bridge.
- The engine, `astral-kernel`, which `requirements.txt` names by URL (a wheel published as a
  GitHub release of this repository, version 2.2.1 as of 2026-09-04). OpenHome's installer
  installs it on the DevKit like any other dependency. No API keys, no external services.
- Optional: the Astral local hub beside it (`deploy/install_v2.sh` puts it there). With the
  hub present the ability answers everything the local loop answers: the dictionary, the
  books on the card, the songs, the quiz, timers, notes and the exact-mathematics kernel.
  Without it the ability answers the exact-answer class from the engine alone and says why
  when it cannot.

## Setup

1. Add Astral to your agent from the OpenHome dashboard.
2. Set trigger words in the dashboard (suggestions above).
3. Power on the DevKit, connect it to your agent, and say a trigger word.

## Files

- `main.py`, the cloud-side capability. Deterministic dispatch, no LLM.
- `devkit_functions.py`, the device side. One self-contained file: the time/date and math/money/conversion engine is inlined, so it needs no siblings.
- `background.py`, the optional background daemon. Same engine, no trigger word, plus due timers.
- `requirements.txt`, standard library only.

## Extending it

Add a reader to `devkit_functions.py` that calls `_emit_success` / `_emit_error`, then register it in `FUNCTION_REGISTRY`. New phrasings that route through `respond` go in the inlined `mech_handle` (time/date) or `calc_handle` (math/money/conversions) sections.
