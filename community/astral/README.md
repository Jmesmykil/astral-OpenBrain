# Astral — OpenHome Ability
![Community](https://img.shields.io/badge/OpenHome-Community-orange?style=flat-square)
![Local](https://img.shields.io/badge/Category-Local-green?style=flat-square)

## What this is

Astral answers the exact-answer class on the device, without the LLM: time, date, math, money, unit conversions, DevKit telemetry, and simple device control over MQTT. You ask in plain language, the device computes the answer with pattern-and-table code, and the agent speaks it. When a request is not an exact-answer question, Astral speaks nothing and the agent takes the turn.

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

**Device control (MQTT).** It understands the command, not just on and off. It extracts action, device, attribute, and value from plain speech, so "turn on the kitchen light", "dim the bedroom light to 30", "set the thermostat to 72", and "lock the front door" all parse, and it publishes to `home/<device>/...` with no LLM. It remembers the last device, so a follow-up like "turn it off" resolves. Universal by topic, so it works before you set up a device registry; without an MQTT broker it says so plainly instead of failing silently.

## Suggested trigger words

Set these in the OpenHome dashboard. Pick the ones you want.

`what time`, `what's the time`, `what's the date`, `what day is it`, `calculate`, `what's`, `how much is`, `percent of`, `square root of`, `convert`, `how many`, `tip on`, `tax on`, `split`, `turn on`, `turn off`, `switch`, `toggle`, `dim`, `set`, `lock`, `unlock`, `open`, `close`, `device temperature`, `uptime`, `disk usage`, `memory usage`

## How it works

**Cloud side (`main.py`).** On a trigger word it takes the transcript and sends it straight to the device with `send_devkit_capability_action(function_name="respond", args=[transcript])`. No LLM routing. It speaks the device's `spoken_response`, or nothing if the device returns an empty one, then calls `resume_normal_flow()`.

**Device side (`devkit_functions.py`).** One self-contained file. `respond` runs the transcript through the inlined engine (time and date, then math, money, and conversions) and emits a structured result:

```json
{ "success": true, "spoken_response": "It's 3:10 pm.", "data": { ... }, "error": null }
```

An empty `spoken_response` means no exact answer, so the agent takes the turn.

## Speech to text is an option

This ability version uses the agent's speech-to-text, so the transcript comes from the cloud. For a fully local path, wake and speech-to-text also run on the device (whisper base.en, quantized), so the exact-answer class answers with no cloud trip at all. That local path is proven on the DevKit with the network off. It becomes native once the agent can hand the turn to a hardware ability before the LLM, which the platform is moving toward.

Both paths use the same engine. Local speech-to-text is the default when it is available; a small cloud speech-to-text is the fallback for consistency. These are options, and they get better as the tech does.

## Requirements

- An OpenHome DevKit running the device-side bridge.
- Python standard library only. No API keys, no external services.

## Setup

1. Add Astral to your agent from the OpenHome dashboard.
2. Set trigger words in the dashboard (suggestions above).
3. Power on the DevKit, connect it to your agent, and say a trigger word.

## Files

- `main.py` — the cloud-side capability. Deterministic dispatch, no LLM.
- `devkit_functions.py` — the device side. One self-contained file: the time/date and math/money/conversion engine is inlined, so it needs no siblings.
- `requirements.txt` — standard library only.

## Extending it

Add a reader to `devkit_functions.py` that calls `_emit_success` / `_emit_error`, then register it in `FUNCTION_REGISTRY`. New phrasings that route through `respond` go in the inlined `mech_handle` (time/date) or `calc_handle` (math/money/conversions) sections.
