# Handoff: Astral on the OpenHome DevKit

Written 2026-09-04. Everything here was verified on the day it was written, and every
number came from the machine it describes. When something is not verified, it says so.

## What this is

A voice assistant that answers on the DevKit itself. You say "open brain" and ask, and the
wake word, the speech recognition, the answering and the voice all run on the Raspberry Pi 4.
Nothing is sent anywhere unless you say yes out loud.

It ships in two forms, and they share one engine:

1. **The OpenHome ability** (`community/astral/`), which runs inside OpenHome's own runtime.
   It answers the exact-answer class and hands everything else back to the agent.
2. **The local loop** (`hub/live_hub.py`), which owns the microphone itself and runs the
   whole conversation on the device.

One microphone, one owner. Never run both at once. The deploy script installs the loop as a
user service; stopping it hands the microphone back to OpenHome.

## The machines

| Name | Address | What it is |
|---|---|---|
| The DevKit | `openhome@192.168.1.23` | Raspberry Pi 4, 4 cores, 7.7 GB, Python 3.13.5 |
| The Mac | `192.168.1.4` | where you develop, and the network rung the device can ask |

The device's interpreter is `~/astral-voice/kws-venv/bin/python3`. The ability runs as root
under the system `python3`, so the compiled kernel is installed into both.

## Working on it

```
# deploy the loop and everything it needs, then restart it
deploy/install_v2.sh openhome@192.168.1.23

# the suites, on the Mac
python3 hub/tests/run.py                 # 3,910 checks, 27 suites
python3 hub/tests/run.py voice           # one suite

# the suites, on the device, which holds more because the model and kernel are live there
ssh openhome@192.168.1.23 'cd ~/astral-voice/hub-v2 && ~/astral-voice/kws-venv/bin/python3 tests/run.py'
```

Both suites run against a scratch copy of the device's state, so no check can touch the card.
Every new check is proved to fail before its fix goes in.

## Shipping the ability

The ability is validated and ready. These are your commands, because they need your key:

```
openhome login
openhome deploy community/astral --name Astral --category local --json
openhome assign
openhome trigger "what time is it"
```

`openhome validate community/astral` should say "All checks passed" before any of that.

The CLI on this Mac is your fork, `Jmesmykil/openhome-cli`, carrying your one commit that
makes the validator judge `devkit_functions.py` by the DevKit contract instead of the
capability-worker rules. OpenHome's published build rejects every valid DevKit ability,
including their own template. If `openhome` ever goes missing, rebuild it:

```
git clone --depth 20 https://github.com/Jmesmykil/openhome-cli.git
cd openhome-cli && npm install && npm run build && npm install -g .
```

## The kernel

The engine ships as a compiled wheel named by URL in `community/astral/requirements.txt`,
currently release v2.2.1 of `Jmesmykil/astral-OpenBrain`. The deploy rebuilds it on the Pi
whenever a source file is newer than the wheel, which takes about four minutes. After a
rebuild the release asset is stale, so replace it:

```
scp openhome@192.168.1.23:~/astral-voice/hub-v2/kernel/dist/astral_kernel-*.whl .
gh release upload v2.2.1 astral_kernel-*.whl -R Jmesmykil/astral-OpenBrain --clobber
```

Bump `VERSION` in `hub/build_kernel.py` and `version` in `hub/kernel/setup.py` together, and
cut a new release when the version moves.

## Volume, and who owns it

OpenHome owns both levels, by your rule. Their app's slider sets the speaker and persists it
as `SPEAKER_VOLUME` in `~/.env` on the device; their boot sets the microphone from
`MIC_SENSITIVITY` in the same file. This project never writes either at runtime.

The deploy writes `MIC_SENSITIVITY=160` into their file once, and only while it still holds
their default of 30, because the wake word was measured deaf at 30. A value you choose later
is never overwritten.

**What this means in practice:** after every boot the speaker comes up at whatever the
OpenHome app last stored, which is 14 today and nearly inaudible. Move the app's slider once
and it stays. The health line in the log names the key when the microphone is below what the
wake needs.

## The sounds

Seven cues live in `hub/data/sounds/astral/`: ready, wake, working, accept, handoff, decline,
dismiss. They are glass struck once per cue, all in A major, with one tone shape across the
set and a deliberate loudness offset each (ready is the loudest, dismiss the softest). The
tick is a water drop, 1.9 seconds apart.

The pack carries a `MASTERED.txt`, which means the device plays it as authored: no levelling
to a common loudness and no transient lift. Packs without that marker, including OpenHome's
own tunes, are still levelled at play time. Say "use the openhome sound pack" to switch.

## What is open

- **Short spoken follow-ups of two or three words** are lost more often than long ones when
  they come through the device's own speaker. Four of thirteen turns in the last voice pass
  came back as nothing usable. This has not been measured with a person speaking in a quiet
  room, which is the test that would settle it.
- **A mishearing can reach the comprehension tier**, which then asks a clarifying question
  about words nobody said. The tier is doing what it should, which is to ask rather than
  guess. The error is upstream, in the transcription, in a room with a television in it.
- **The speaker level after a reboot**, above.
- **The library's first question after the index grows** takes about fifty seconds cold.

## The traps that have cost the most time

1. **The ssh agent wedges.** Any `ssh`, `scp` or signed `git commit` to a known host that
   hangs at zero CPU is the launchd agent, not the network. Prefix with `SSH_AUTH_SOCK=`.
   The deploy script already does.
2. **The deploy copies by an include list.** A new directory under `hub/data/` is silently
   not copied until a line names it. The sound pack sat stale on the card through two
   deploys while the deploy printed success. Verify what the device resolves, not what the
   deploy says.
3. **A gate that reads a file must be run in the device's layout too.** Two gates read the
   deploy scripts from the Mac's paths and raised on the DevKit, taking the rest of the
   voice suite down with them. Copy the hub to a scratch directory shaped like the device
   and run the suite there before deploying.
4. **Check the speaker before reading a voice test.** At sink 14 the device's own stimulus
   reaches its microphone at a peak near 700 and whisper invents sentences out of it. At
   sink 65 the same stimulus arrives near 15,000.
5. **The scratchpad is not durable.** Anything installed from one, the OpenHome CLI included,
   dies with it.
6. **The Mac suite cannot see the model tier.** The Mac has no local model and no measured
   cost profile, so whole classes go silent there and pass. Run the suite on the device
   before calling anything shipped.

## Where things live

| Path | What |
|---|---|
| `community/astral/` | the MIT ability that runs inside OpenHome |
| `hub/` | the local loop and the engine sources, a separate private repository |
| `deploy/install_v2.sh` | the deploy, run from the Mac |
| `deploy/on_device.sh` | what the deploy runs on the Pi |
| `KNOWN-BUGS.md` | the ledger: every defect, with dates and numbers |
| `GRANT-APPLICATION.md` | the grant answers as submitted |
| `handout/` | the handout and the demo transcript |

On the device: the loop in `~/astral-voice/hub-v2/`, its state in `~/astral-voice/state/`,
the library and its index in `~/astral-voice/library/`, the log at
`~/astral-voice/astral-hub.log`, and test stimuli in `~/astral-checks/`.
