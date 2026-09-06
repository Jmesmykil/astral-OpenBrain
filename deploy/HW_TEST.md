# Hardware acceptance: current Astral installation

Updated September 5, 2026. This is a pending acceptance procedure, not a record of completed human tests.

The current user service runs live_hub.py, which already includes wake interruption and follow-ups. Its latest startup reports **open brain** and **open home**, local whisper-base.en-q5_1 with audio context 512, and the Google Voice HAT input. Use **open brain** for this run. The product remains OpenHome/Astral; a wake phrase is not a product rename.

Do not redeploy, start a second microphone consumer, or switch to duplex.py as test setup. Installation agreement has already been verified. The kiosk is inactive; keep one microphone owner. Switching to OpenHome platform voice is a separate coordinated step after account ability registration.

## Verified starting point

The source/support comparison matches 168 files and three Astral service definitions. Both Python interpreters match kernel 2.2.3. Schema 26 retains 191 physical sources and 412,863 passages. These facts do not establish human audibility.

The actual app speaker slider was exercised and restored to 14%; microphone sensitivity remains 160%. Pointer changes reached both the physical mixer and saved SPEAKER_VOLUME. In the observed Safari control, arrow keys changed the display without committing to the device; clicking the focused slider committed the selected value. Re-read the mixer and saved setting rather than trusting the displayed number.

The completed one-hour native WebSocket observer returned 183/183 correct answers before library 26 activation. It bypassed acoustic capture, recognition and audible speech. Do not count it as the human voice pass.

## Read-only preflight

On the Mac:

~~~sh
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8 openhome@<devkit>
~~~

Then on the DevKit:

~~~sh
systemctl --user is-active astral-hub.service astral-ability.service astral-slate.service
systemctl --user is-active openhome-dashboard.service
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl get-volume @DEFAULT_AUDIO_SOURCE@
~~~

The three Astral services should be active and the kiosk inactive. The second command therefore normally exits nonzero. Speaker and microphone should read 0.14 and 1.60. If state differs, investigate the actual owner/process before starting another loop.

Use bounded recording/log tools only for identified test turns. Retain prompt, trial time, captured signal, ASR, route, response and actual audible outcome. Mark empty, missed and incorrect trials explicitly. A log event without human ground truth is neither a proved success nor a proved false wake.

## Controlled short and long requests

Have the creator speak these through the HAT at the agreed position. Repeat matched short/long pairs in a quiet room and the chosen representative room condition. Keep all attempts in the denominator.

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

For matched negatives, have the creator deliberately read the designated non-addressed room statements, including the embedded-command regression phrase retained in the audit. Observe the agreed ambient interval with human labels. Do not deliberately issue a real command and label its execution a false positive.

Record wake detection, false activation, missed/empty capture, exact-answer success and end-of-speech to first-audible-response latency separately. Report counts and distributions; do not combine native typed and acoustic latencies.

## Timers and mutable capabilities

Inspect existing owner timers, notes and settings first. Use an identifiable test timer only when it can be distinguished from owner timers. Exercise create, query, expiry and cancellation of that test item. Do not use global cancel/delete against unknown owner state.

Test historical cancel-versus-stop routing in isolation when no safe owner-free timer is available. Installed regressions prove software routing, not human acoustic cancellation. Temporary notes/settings scenarios also need named test items and restoration checks.

## Human interruption

Use the running live_hub service. While it speaks an agreed sufficiently long answer, say the wake phrase and a different short request. Verify actual playback stops, the new request is captured and its answer is correct. Measure interruption-to-stop latency and retain prior/new context evidence.

Repeat during listening/thinking and with a false interruption. The latter must not corrupt context or abandon a valid answer. Do not substitute duplex.py fixtures or log lines for measured human interruption.

## Actual app controls and account path

Use the existing signed-in OpenHome account. Under OpenHome DevKit → Microphone & devices, inspect the selected HAT, pro-audio profile and speaker control. Preserve microphone sensitivity, interruption toggles, account abilities and other settings. Check a small reversible speaker change against both wpctl and persisted SPEAKER_VOLUME, then restore its starting value. Human audibility is separate.

Astral agent 595324 exists and device-key SDK access works. Its explicit SDK matching_capabilities list is empty, separately from 17 globally installed/enabled abilities. Do not replace one list with the other. The saved Astral draft is unfinished and its resume currently renders blank.

The native shim answers through root Python and the owner bridge. Direct/local-WebSocket requests prove that native path only. To prove account routing, retain registration/upload and assignment receipts, coordinate one microphone owner, and correlate spoken platform input with the intended capability ID and device execution. No new account or GPT-app sign-in is needed.

Do not start a hosted model merely to produce a green check when local-only operation is required. Stored hosted-agent settings do not prove local inference.

## Completion record

Every trial needs an observed outcome: passed, failed, skipped with a reason, or not run. Preserve prior failures and repairs. Record final source/index/package identities, services and restored state.

[HANDOFF](../HANDOFF.md) and [known limitations](../KNOWN-BUGS.md) retain current status. Human wake, short-capture, interruption and audible app/platform acceptance remain open until actual evidence is collected.
