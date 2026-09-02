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

Say the wake word ("hey mycroft" until the custom model lands), then the phrase. Tick
each line only if the sound and the words were both right.

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
| integral of x squared | handoff cue, "I would need the Mac for that. Want me to send it there?"; say "no": "Okay." | ask, declined |
| integral of x squared, then "yes" | handoff cue, the ask, then accept and the Mac's answer, or the decline tone and "I couldn't reach the Mac right now." | ask, LAN |
| the weather is nice today | nothing at all | silent |
| tell me a joke | handoff cue and the ask (conversation is not on the device yet) | ask |

## Measure while it runs

`ssh` in and run `python3 measure_costs.py` inside `~/astral-voice/hub-v2` while the loop
is listening. That profile, not the idle one, is the fits table the device ships with.
Copy `data/costs/pi4-8g-arm64.json` back into the workspace.

## After

`systemctl --user stop astral-hub && systemctl --user start openhome-dashboard` puts the
kiosk back. The log is `~/astral-voice/astral-hub.log`; every turn writes a `[route]` and
a `[rank]` line.
