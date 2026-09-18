# Astral for OpenHome

Astral answers out loud on an OpenHome DevKit, on the device, without sending the
question anywhere. Ask it the time, a calculation, a unit conversion, a molar mass or an
escape velocity and it computes the answer and speaks it. Ask it anything else and, with
the local hub installed, it offers to ask something that can answer (your phone, your
computer, or the OpenHome agent) and sends nothing without a yes; without the hub it says
nothing, so the agent takes the turn.

The point is not that it is fast, though it is. The point is that a question with exactly
one right answer should be computed rather than recalled. A model asked for the escape
velocity of Mars produces a number that is usually close and occasionally invented. This
produces the number.

```
what is twenty percent of eighty   →  20 percent of 80 is 16.
molar mass of water                →  The molar mass of water (H2O) is 18.015 grams per mole.
escape velocity of mars            →  Escape velocity at Mars is 5.02 kilometers per second,
                                      11234.25 miles per hour.
turn on the kitchen light          →  Turning on the kitchen light.   (publishes home/kitchen_light/set)
```

## What it answers

Time and date. Arithmetic, percentages, tips, tax and splitting a bill. Unit conversions
across weight, length, volume, temperature, speed, area, time, energy, pressure, force,
data sizes and astronomical distance. Grades: what you need on the final, weighted
totals, percent to letter, GPA. Chemistry: molar mass for a named compound or a formula,
moles and grams, molarity, pH, the ideal gas law, and the atomic mass and number of all
118 elements. Physics: escape velocity and surface gravity for the Sun, the Moon and
every planet, weight on another world, free fall, energy, momentum, force, work, power,
Ohm's law, time dilation, Schwarzschild radius, photon energy, light travel time.
Statistics: mean, median, mode, range, variance, sample and population standard
deviation, z scores, combinations. Number tools: binary, hex and octal, logs, trig, GCD
and LCM, primes, modulo, the quadratic formula, fractions, significant figures.

It also reads DevKit telemetry and publishes supported MQTT device commands.

Two things it says out loud rather than assuming. A letter grade names the scale it used,
because a grading scale is a convention and not a fact. A standard deviation says whether
it is the sample or the population one, because those are different numbers.

## The two abilities

`community/astral` is the foreground ability: the platform matches a trigger word, hands over the transcript, and it answers and gives the turn back. `community/astral-daemon` is the background daemon: no trigger word, it sees the whole session, offers each turn to the device first and stays silent when the device has nothing. They share one shim on the device, so there is one engine there, not two.

`sh deploy/build_packages.sh` builds both into `build/`. Ability names are unique across every OpenHome account, so each shipped `config.json` carries a `CHANGE-ME` placeholder: put your own `unique_name` and `name` in an untracked `config.local.json` beside it, and the build uses them.

`community/astral-skill` is version one, a single self-contained file that answers for any agent with no device and no dependency. It is unchanged from what the community catalog accepted and needs nothing from this section.

## Installing it

Add the ability to an agent from the OpenHome dashboard. The platform installs what
`community/astral/requirements.txt` names, the same way it installs any other dependency,
and that is the compiled engine:

```
astral-kernel @ https://github.com/Jmesmykil/astral-OpenBrain/releases/download/v2.2.7/astral_kernel-2.2.7-cp313-cp313-linux_aarch64.whl#sha256=...
```

The wheel is built for CPython 3.13 on linux aarch64, which is what a DevKit runs. A
compiled wheel is specific to an interpreter and an architecture; that is a property of
compiled code, not a defect. Releases are on this repository's
[releases page](https://github.com/Jmesmykil/astral-OpenBrain/releases).

A device that already has the Astral local hub installed does not need the wheel at all.
One that has neither says so when you ask it something, rather than going quiet.

## Using it

Say a trigger phrase, then the question. The wake phrases are "open brain" and "open
home"; the product is Astral.

The ability is also directly callable, which is how to check an installation without
speaking to it:

```sh
python3 devkit_functions.py health
{"success": true, "spoken_response": "Astral: kernel 2.2.7, local hub installed.",
 "data": {"kernel": true, "hub": true, "version": "2.2.7"}, "error": null}

python3 devkit_functions.py respond "molar mass of water"
{"success": true, "spoken_response": "The molar mass of water (H2O) is 18.015 grams per mole.",
 "data": {"query": "molar mass of water", "from": "hub", "class": "chem"}, "error": null}
```

Every call returns one JSON object with `success`, `spoken_response`, `data` and `error`.
An empty `spoken_response` means Astral has no exact answer and the agent should take the
turn. `data.from` names what answered: the local hub if one is installed, otherwise the
compiled kernel.

Callable functions: `respond`, `respond_now`, `route_answer`, `device_control`,
`due_alerts`, `heard`, `health`, `get_temperature`, `get_uptime`, `get_disk`,
`get_memory`. Anything unrecognised is treated as a question.

## How it fits together

Three pieces, with a deliberate line between them.

**The ability** is `community/astral/`. It is MIT, it is readable, and it is the whole of
what runs inside OpenHome's runtime. It decides nothing about answers; it asks, then
performs the device I/O.

**The engine** is `astral-kernel`, a compiled package installed from `requirements.txt`.
Its public contract is two functions: `answer(text, now=None)` returns a spoken string or
nothing, and `command(text, last_device=None)` returns a structured device command. See
[BOUNDARY.md](community/astral/BOUNDARY.md).

**The local hub** adds the library on the SD card, definitions, notes, timers, memory,
conversation and optional local-model assistance. Its sources are maintained in a
separate private repository and are not included here, so a clone of this repository
alone cannot rebuild the local loop. The ability and the compiled engine do not need it.

`community/astral-skill/` is the earlier cloud-side integration, kept for history. It is
not the current DevKit release.

## Requirements

An OpenHome DevKit: Raspberry Pi 4, 8 GB, CPython 3.13, linux aarch64. The ability itself
is Python standard library only. No API keys and no external services.

## Working on it

From the private development checkout:

```sh
python3 hub/tests/run.py --full          # every hostile-input case, no discovery cap
python3 hub/tests/run.py library ability voice
python3 hub/tests/room_regressions/run.py
openhome validate community/astral
deploy/install_v2.sh openhome@<devkit> --start
```

The runner separates held, failed and skipped checks, because a skipped check that reads
as a pass is worse than a failure. Deployment verifies a wheel against its build inputs
and verifies the installed bytes in both interpreters; a compiler, pip or kernel
verification failure stops before the loop restarts. See [RELEASE.md](RELEASE.md).

Tests that use synthetic speech channels are software checks. They are not evidence that
a person can be heard in a room, and nothing here treats them as such.

## Status

The engine, the ability and the compiled release are in use on the development DevKit.
Acoustic acceptance is not finished: physical interruption still loses words from a new
request while playback stops, and wake-word reliability, audible playback and platform
spoken routing are not established by automated passes.

[KNOWN-BUGS.md](KNOWN-BUGS.md) carries the current acceptance state, open issues and the
dated ledger.
[V2-CAPABILITIES.md](V2-CAPABILITIES.md) describes what the device does in one page.

## Licence

The ability, and everything else in this repository, is MIT — see [LICENSE](LICENSE).
The compiled `astral-kernel` engine is separately licensed and proprietary.

## Ask your phone, or your computer

The DevKit cannot run every tier, and the machines that can are not always on its network.
The local hub therefore runs a small gateway on the device: one TLS door, self-signed and
pinned by fingerprint, advertised on the LAN over mDNS. A phone or computer connects out to
it, proves it belongs to the owner of the house, and then takes signed tasks and returns signed
answers. Nothing on the phone or computer listens; there is no VPN, no mesh and no relay. When a
question is outside what the device can answer within rank, it says which machine it would need
and asks before sending it anywhere. The owner signs in once: approve the device at home with a
six-digit code, or use a GitHub account. Google and X sign-in are built in and appear once the
house is given its own app ids for them. Nothing about the owner is built in; the first account
to sign in becomes the owner of that house.

The gateway ships with the local hub, which is not part of this repository yet, and so does
the phone app (Astral Oasis). The wire contract (canonical JSON, the signed task, card and
receipt shapes) is stable and will be published with them, so any client can join.
