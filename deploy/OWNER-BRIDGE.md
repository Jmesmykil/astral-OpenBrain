# Native owner bridge

The native platform starts a Python shim for each request. The full hub previously
started another Python interpreter and recompiled its routing expressions each time.
`ability_server.py` now preloads that router once as `openhome`. It accepts requests
on `~/astral-voice/state/ability.sock`, mode 0600, and forks a fresh bounded child for
each request. It uses the existing `ability_bridge.main` response contract.

This service owns no microphone or network listener. The voice loop and shared Slate
service retain their existing responsibilities. Installation enables and restarts
`astral-ability.service`, then waits for an actual ready response. Future source
deployments must restart this service because its parent holds imported code.

The public shim checks the socket's type, owner, permissions and Linux peer identity
before sending. If the service is absent or refuses the connection, the owner CLI
remains available. A request already sent is never replayed through that CLI after
a malformed, lost or timed-out reply. An explicit `ASTRAL_STATE` bypasses production
IPC entirely. Deadlines use system-wide `CLOCK_MONOTONIC`; Python 3.9 on macOS has a
process-relative `time.monotonic()` origin and cannot exchange those values directly.

The parent imports routing code but runs no requests. Mutable Python globals remain
fresh in each child, as with the preceding process-per-request path. Owner files and
their locks retain persistence. This preserves existing behavior; it does not add
new cross-request quiz or conversation sessions to the native interface.

## Measured on the DevKit, September 5, 2026

Same actual local WebSocket → node → sudo Python → shim workload, 30 warm requests
per class before and after. All 90 warm answers were correct in each run. First
observed requests were kept separately; neither run was a controlled cold boot.

| Request | Before p50 | After p50 | Before p95 | After p95 | After maximum |
|---|---:|---:|---:|---:|---:|
| Percent | 615.82 ms | 199.75 ms | 740.68 ms | 212.60 ms | 246.58 ms |
| Units | 613.83 ms | 199.05 ms | 647.24 ms | 231.20 ms | 235.86 ms |
| Equation | 604.74 ms | 180.99 ms | 628.37 ms | 191.10 ms | 199.77 ms |

The parent stayed at 23,536 KiB RSS, one thread and five file descriptors across
the benchmark. Ten simultaneous requests retained their distinct correct answers.
A later quiescent check after a deliberate service restart found no remaining
children, one thread and five descriptors. This is bounded resource evidence, not
a long-duration soak. Speech capture, ASR, synthesis, playback and account routing
are outside these latency measurements.

The device's affected suites held 448 checks with zero failures and one Mac-only
skip. The final Mac integration run held 152 with zero failures and two skips
(upstream lint and compiled package); the device covers both. These counts overlap.
The 46 protected state/configuration/sound hashes were unchanged through staging,
activation, benchmarks and restart. Compiled kernel 2.2.3 was not rebuilt.

## Operate and recover

```sh
systemctl --user status astral-ability.service
~/astral-voice/kws-venv/bin/python3 ~/astral-voice/hub-v2/ability_server.py --check
systemctl --user restart astral-ability.service
```

To disable this optimization, stop and disable only `astral-ability.service`; the
shim then uses the owner CLI. An actual absent-service native request returned the
correct percentage answer in 689 ms. Restart restored the socket and the next native
units answer returned correctly in 204 ms. No voice or Slate restart was needed.

Dated byte backups are under `~/astral-voice/backups/owner-bridge-v1/` and
`owner-bridge-v2/`. The first preserves the pre-change hub staging; the second also
preserves the original active native shims before activation. Each corresponding
`platform-hardening/owner-bridge-v*/before.json` records prior presence and hashes.
Restore only the intended code files from those records; never bulk-restore owner
state over changes made after the backup. Deployment receipts, all individual
trials and failure cases remain in the private acceptance directory on the Mac.

## Remaining boundaries

The timeout mismatch found in the review was corrected in a subsequent scoped
change. Answer and offer now share a 12-second budget; named routes allow 12 seconds,
leaving room below the native dispatcher's 15-second limit. Exhaustion returns an
explicit timeout sentence and starts no further fallback computation. The background
source now waits 20 seconds for the native result instead of giving up at six; that
account-side source still requires the later platform upload/assignment verification.

The final deadline regression held 156 device checks, zero failures/skips. Repeating
the identical 90 warm native requests retained every correct answer, with p50
181.72–201.62 ms and p95 189.66–212.52 ms. All ten simultaneous calls were correct and
the same 46 protected hashes and all three service PIDs remained unchanged.

Python signal handlers cannot guarantee timely interruption of a C extension that
never returns to Python. The deadline tests prove queued expiry and termination of
the tested Python worker/descendant case, not universal cancellation of arbitrary
native code. Account assignment, actual human voice/app acceptance, broader semantic
coverage and the representative soak remain open in the full execution plan.
