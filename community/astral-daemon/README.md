# OpenBrain Daemon

The local answer layer without a trigger word. This is a background daemon: it starts
with the call, runs for the whole of it, and reads the live transcript rather than
waiting for the platform to match a phrase.

Every turn is offered to the DevKit engine first. When the device has an exact answer it
interrupts and speaks it. When the device has nothing, which is most turns, the daemon
does nothing at all and OpenHome's normal routing handles the turn exactly as it would
have. The failure mode of the filter is silence.

It also speaks local timers when they come due, because a timer set on the device has to
be announced by something still alive when it fires, and a foreground ability is a
subprocess that exited long ago.

**Requires a connected DevKit.** It calls `respond_now`, `due_alerts` and `heard` in
`devkit_functions.py`, which reaches the compiled `astral-kernel` named in
`requirements.txt` and the local hub when one is installed.

## The race, and when it declines to win

The agent and this daemon see the same turn at the same moment. The daemon polls the
transcript, asks the device, and calls `send_interrupt_signal()` before speaking. A
device answer costs a subprocess and a table lookup; a model answer costs a round trip
and speech synthesis, so the daemon usually arrives first.

When it does not, it stays out of the way. This path asks `respond_now`, whose budget is
one second, and it will not interrupt once its deadline has passed. The case for
preempting the cloud is that the local answer is both cheaper and faster; the moment it
stops being faster, the cloud's turn is the right answer. A sentence severed mid-word is
a real cost paid by the person in the room and it is never worth a fraction of a second.

Two things interrupt unconditionally: a timer coming due, because an alert that waits
for a gap can be minutes late, and a once-a-session health sentence after three failed
device calls in a row.

## Relationship to the OpenBrain ability

`OpenBrain` is the foreground ability: the platform matches a trigger word, hands over
the transcript, and the ability answers and hands the turn back. This daemon is the
same engine on the same device with no trigger word and no turn handover. They share one
`devkit_functions.py`, so there is one engine on the device, not two. Running both is
supported; running either alone is fine.

## Validation note

`openhome validate` reports `resume_normal_flow() must be called`. That rule is correct
for a foreground ability, which holds the turn and must return it. A background daemon
never takes the turn: it interrupts and speaks, and releasing a turn it never held would
be wrong. Foreground validation does not establish a daemon, and this category has its
own voice-race acceptance requirements.

## License

These integration files are MIT. `astral-kernel` is a separately licensed compiled
dependency, named in `requirements.txt` and pinned by SHA-256.
