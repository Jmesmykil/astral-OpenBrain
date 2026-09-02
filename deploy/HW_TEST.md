# Hardware acceptance: current Astral installation

Updated September 6, 2026. This is a pending acceptance procedure, not a record of completed
human tests.

**Run `deploy/acceptance.py` rather than working through this by hand.** It prints each
sentence to say, watches the loop's own log for what it made of it, and asks the one
question the log cannot answer — what happened in the room — then writes a receipt. This
document is the context around that; the harness is the procedure.

The user service runs live_hub.py, which includes wake interruption and follow-ups. Wake
phrases are **open brain** and **open home**; both route into Astral, and while the local
loop owns the microphone neither reaches OpenHome's own agent. Whisper is base.en-q5_1 with
an audio context sized to each capture (a floor of 512, grown for long questions) — it is no
longer fixed at 512, which used to cut anything past 10.24 seconds. Input is the Google
Voice HAT.

Do not redeploy, start a second microphone consumer, or switch to duplex.py as test setup.
The kiosk is inactive; keep one microphone owner. Switching to OpenHome platform voice is a
separate coordinated step and is R04, still unproven.

## Verified starting point

Kernel **2.2.6** in both interpreters, matching the published release byte for byte. Library
index **schema 32**, 191 physical sources, **577,773 passages**. Device full suite 5,111
held, zero failed, five skipped; Mac 5,002 held, zero failed. None of that establishes human
audibility, which is the whole point of this pass.

Audio levels belong to the owner and to OpenHome's app, not to this procedure. Read them,
record them, and do not set them: `pactl get-sink-volume @DEFAULT_SINK@` and
`get-source-volume`. **A pass run at a low speaker level proves nothing about audibility** —
raise it in the app first if that is what is being judged.

## What has already been driven without a person

A self-echo pass is kept in the private acceptance records: the device speaks the stimulus
through its own speaker and its own microphone hears it. That already exercised the
acoustic path end to end and found two defects — a library answer read aloud as
interleaved OCR, and a follow-up that escalated to the model tier and was answered with an
invented sentence. What it cannot do is recognise a person's voice or hear the room, so
R07's positive half and R10 still need a person. Its pass criterion asked whether the
device spoke, not whether it was right, so read its notes before quoting its score.

## Read-only preflight

On the computer you deploy from (your ssh configuration and agent choose the key):

~~~sh
ssh -o BatchMode=yes -o ConnectTimeout=8 openhome@<devkit>
~~~

Then on the DevKit:

~~~sh
systemctl --user is-active astral-hub.service astral-ability.service astral-slate.service
systemctl --user is-active openhome-dashboard.service
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl get-volume @DEFAULT_AUDIO_SOURCE@
~~~

The three Astral services should be active and the kiosk inactive. The second command therefore normally exits nonzero. Record whatever the speaker and microphone read; the owner sets them, not this pass. If state differs, investigate the actual owner/process before starting another loop.

Use bounded recording/log tools only for identified test turns. Retain prompt, trial time, captured signal, ASR, route, response and actual audible outcome. Mark empty, missed and incorrect trials explicitly. A log event without human ground truth is neither a proved success nor a proved false wake.

## Controlled short and long requests

Have a person speak these through the HAT at the agreed position. Repeat matched short/long pairs in a quiet room and the chosen representative room condition. Keep all attempts in the denominator.

| Trial | Say | Independent acceptance target |
|---|---|---|
| A01 | Open brain, what time is it? | Wake detected; current local time spoken. |
| A02 | And in London? | During the follow-up window, complete the prior time request for London. |
| A03 | Open brain, twenty percent of eighty. | Numerical result 16. |
| A04 | Open brain, please calculate twenty percent of eighty for me. | Same result as A03, with longer wording captured. |
| A05 | Open brain, convert ten pounds to kilograms. | Approximately 4.5359 kilograms; no unit reversal. |
| A06 | Open brain, how do you say hello in French? | A French translation, not a generic time-of-day greeting. |
| A07 | Open brain, hello, what time is it? | The time request wins over the greeting prefix. |
| A08 | Open brain, solve two x plus three equals eleven for x. | x=4. This equation is supported. |

Replay the two previously empty quiet-room captures using their original recorded stimulus identities too. These examples do not erase those failures. Distinguish missing captured signal from empty ASR and routing rejection.

For matched negatives, have a person deliberately read the designated non-addressed room statements, including the embedded-command regression phrase retained in the audit. Observe the agreed ambient interval with human labels. Do not deliberately issue a real command and label its execution a false positive.

Record wake detection, false activation, missed/empty capture, exact-answer success and end-of-speech to first-audible-response latency separately. Report counts and distributions; do not combine native typed and acoustic latencies.

## Timers and mutable capabilities

Inspect existing owner timers, notes and settings first. Use an identifiable test timer only when it can be distinguished from owner timers. Exercise create, query, expiry and cancellation of that test item. Do not use global cancel/delete against unknown owner state.

Test historical cancel-versus-stop routing in isolation when no safe owner-free timer is available. Installed regressions prove software routing, not human acoustic cancellation. Temporary notes/settings scenarios also need named test items and restoration checks.

## Human interruption

Use the running live_hub service. While it speaks an agreed sufficiently long answer, say the wake phrase and a different short request. Verify actual playback stops, the new request is captured and its answer is correct. Measure interruption-to-stop latency and retain prior/new context evidence.

Repeat during listening/thinking and with a false interruption. The latter must not corrupt context or abandon a valid answer. Do not substitute duplex.py fixtures or log lines for measured human interruption.

## Actual app controls and account path

Use the existing signed-in OpenHome account. Under OpenHome DevKit → Microphone & devices, inspect the selected HAT, pro-audio profile and speaker control. Preserve microphone sensitivity, interruption toggles, account abilities and other settings. Check a small reversible speaker change against both wpctl and persisted SPEAKER_VOLUME, then restore its starting value. Human audibility is separate.

The account needs its Astral agent, and device-key SDK access must work. An agent's explicit SDK matching_capabilities list is separate from the globally installed/enabled abilities; do not replace one list with the other.

The native shim answers through root Python and the owner bridge. Direct/local-WebSocket requests prove that native path only. To prove account routing, retain registration/upload and assignment receipts, coordinate one microphone owner, and correlate spoken platform input with the intended capability ID and device execution. No new account or GPT-app sign-in is needed.

Do not start a hosted model merely to produce a green check when local-only operation is required. Stored hosted-agent settings do not prove local inference.

## Completion record

Every trial needs an observed outcome: passed, failed, skipped with a reason, or not run. Preserve prior failures and repairs. Record final source/index/package identities, services and restored state.

[Known limitations](../KNOWN-BUGS.md) retain current status. Human wake, short-capture, interruption and audible app/platform acceptance remain open until actual evidence is collected.
