# Where this ability ends and the engine begins

This directory is the ability. It is MIT, it is readable, and it is the whole of what
runs inside OpenHome's runtime.

The engine is not in here. It is `astral-kernel`, a separate compiled package named in
`requirements.txt`, which the platform installs on the DevKit the way it installs any
other dependency: *"Packages listed in `requirements.txt` are installed for
`devkit_functions.py` on the OpenHome DevKit."*

## The seam

One function. One contract.

```python
astral_kernel.answer(text, now=None) -> str | None
astral_kernel.command(text, last_device=None) -> dict | None
```

`answer` takes a transcript and returns a spoken answer, or `None`. `None` means the
engine has no exact answer for this turn and the agent should take it, the cooperative
bargain this ability is built on: it answers what it can answer instantly, on
the device, and it is silent about everything else.

`command` understands a spoken device command and returns *what to publish*, a topic, a
payload and a sentence to say, without publishing it. Understanding the sentence is
engine work; putting a byte on an MQTT topic is device work, and device work stays in
`devkit_functions.py`, where a reviewer can see it.

## What is in each file

| file | what it is | licence |
|---|---|---|
| `main.py` | the cloud-side capability: takes the turn, speaks, offers routes, hands back | MIT |
| `devkit_functions.py` | the device-side shim: asks the engine, prints one line of JSON, reads telemetry, publishes MQTT | MIT |
| `background.py` | the optional background daemon | MIT |
| `requirements.txt` | names the engine package | MIT |
| `astral-kernel` (a dependency) | the engine: routing, tables, guards, units, chemistry, physics | proprietary |

## Why it is arranged this way

Because the two halves have different lives. The ability is an integration with somebody
else's platform, and it should be readable by the people who maintain that platform , 
short, obvious, easy to review, easy to fix. The engine is years of somebody's work and
is licensed separately, which is how every compiled commercial library in an open-source
ecosystem is arranged.

Nothing is hidden by being smuggled: there is no binary in this package, no obfuscated
source, nothing that a security scan should object to. There is a dependency, and it is
named, and this file says what it does.

## Running without it

Three ways an answer can arrive, in this order:

1. **The local hub**, if the device has one, the same engine plus everything on the
   card: the dictionary, the books, the mathematics kernel, the owner's own shelves.
2. **The `astral-kernel` package**.
3. **Neither**, and then the ability *says so out loud*: "The Astral engine is not
   installed on this device." An empty answer would mean "the agent should take it",
   which would leave a broken install looking like a working one forever.

## Two things a reviewer will reasonably ask about

**Why does the shim shell out to `sudo`?** Only to cross back to the account that owns
the local hub, and only when that hub is installed. The platform runs this file as
`sudo python3 devkit_functions.py`, so it runs as root, and as root every path the hub
resolves from a home directory lands in `/root`, where none of its data is. Measured on
the device: the same questions answer as the owner and answer nothing as root. On a
DevKit with no hub the branch is never taken; `os.path.exists(BRIDGE)` is the first thing
it checks.

**Where does `astral-kernel` come from?** It is built with `hub/build_kernel.py` and
published by its author. It is architecture- and interpreter-specific by nature, the
DevKit is CPython 3.13 on aarch64, so the wheel is built for that target. Until it is
published somewhere the platform's installer can resolve, the honest state is: a device
with the local hub answers everything, a device with the wheel installed by hand answers
the exact-answer classes, and a device with neither says so out loud rather than
pretending. That last sentence is a feature, not an apology: silence from this ability
means "the agent should take it", and a broken install must never be able to imitate a
working one.
