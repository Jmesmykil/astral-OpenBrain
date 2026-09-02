# Hardware test, version two

The DevKit at `openhome.local`, one microphone, one owner: either OpenHome's kiosk or
Astral's loop, never both. Everything below is local; the only network in play is the
LAN between the Pi and the Mac.

## Before

1. `deploy/install_v2.sh` from the workspace. It syncs the hub, makes the chimes, points
   the LAN route at this Mac, installs the `astral-hub` user service, and prints state.
2. On the Mac, the LAN server: `python3 hub/lan.py serve` (leave it running).
3. `deploy/install_v2.sh openhome@192.168.1.23 --start`. The kiosk stops, the loop
   starts, the ready tune plays.

## The turns

Say **"hey mycroft"**, then the phrase. That is the wake word: the product word has a
model that does not ship because it wakes at an empty room, and `KNOWN-BUGS.md` has the
measurements. Tick each line only if the sound and the words were both right.

| Say | Expect to hear | Path |
|---|---|---|
| what time is it | wake cue, working tick, accept chime, the time in Honolulu | tier 0 |
| twenty percent of eighty | accept, "20 percent of 80 is 16." | tier 0 |
| one third plus one sixth | accept, "One third plus one sixth is one half." | tier 0, oracle-verified |
| mass of earth | accept, "The mass of Earth is about 5.97 times ten to the 24 kilograms." | tier 0 |
| how much space is left | accept, the card's size and free space | device |
| how hot are you | accept, processor temperature | device |
| list abilities | accept, "1 local ability installed: astral." | device |
| set a timer for one minute | accept, "Timer set for 1 minute."; one minute later: accept, "Your 1 minute timer is up." | hooks |
| integral of two x d x | working tick, then the integral | algebra, on the device |
| the weather is nice today | nothing at all | silent |
| tell me a joke | accept, a joke, and a different one next time | small talk |
| what can you do | accept, the classes that fit this device, counted | meta |
| why didn't that work | accept, the real reason the last turn was silent | meta |
| define shell | accept, the first sense and how many there are | dictionary |
| sing twinkle twinkle | the tune played, the words spoken in time | songs |
| quiz me on physics | accept, the card count, then the first question; answer it, then say stop | flashcards |
| what is a lighthouse | working tick for about two seconds, then what it read | comprehension |
| derivative of x squared | working tick, then 2 x | algebra, on the device |
| solve 2x + 3 = 11 for x | nothing: it does not have a solver and will not guess | refused |
| square root of minus four | nothing | refused |

## The suite, on the device

```
ssh openhome@openhome.local
cd ~/astral-voice/hub-v2 && ~/astral-voice/kws-venv/bin/python3 tests/run.py --quiet
```

Everything the device can prove about itself, including the kernels the Mac does not
have. Then:

## Measure while it runs

`ssh` in and run `python3 measure_costs.py` inside `~/astral-voice/hub-v2` while the loop
is listening. That profile, not the idle one, is the fits table the device ships with.
Copy `data/costs/pi4-8g-arm64.json` back into the workspace.

## Through OpenHome's own routing

Their wake word, their transcription, our answers. The ability is refreshed on every
deploy at `~/openhome_devkit/local_capabilities/astral/devkit_functions.py`, and it is
answering today's engine — checked through the exact call the node server makes:

```
ssh openhome@openhome.local
cd ~/openhome_devkit/local_capabilities/astral
python3 devkit_functions.py respond what time is it
python3 devkit_functions.py respond solve 2x + 3 = 11 for x     # says nothing, correctly
```

To hear it by voice this way, the trigger words have to be registered on agent 595324 at
app.openhome.com, which is the one step an agent cannot do. Until then this mode answers
only when invoked directly, as above. Note also that a cloud sync of abilities overwrites
that directory, so re-run the deploy after one.

## The duplex loop, if you want to try it

The service runs the half-duplex loop, which finishes a sentence before it listens again.
The duplex loop hears you while it talks:

```
systemctl --user stop astral-hub
cd ~/astral-voice/hub-v2 && ~/astral-voice/kws-venv/bin/python3 duplex.py
```

Say the wake word while it is answering and it stops mid-sentence and listens. For a few
seconds after it finishes, ask the next thing without the wake word at all. Ctrl-C, then
`systemctl --user start astral-hub` to put the service back.

## After

`systemctl --user stop astral-hub && systemctl --user start openhome-dashboard` puts the
kiosk back. The log is `~/astral-voice/astral-hub.log`; every turn writes a `[route]` and
a `[rank]` line.
