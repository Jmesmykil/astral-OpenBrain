# Handoff: Astral on the OpenHome DevKit

Updated September 5, 2026, HST. Software and release checks are recorded below;
physical and platform acceptance remain open. This is the current
operating record; the dated grant and demo documents preserve earlier claims.

## Current state

- The DevKit runs the local voice loop. The deployed source and compiled package were
  verified after the interrupted September 4 deployment was repaired.
- The approved sound pack is unchanged. Speaker volume was measured at 65 percent and
  microphone configuration at 160. Neither was adjusted during this audit.
- The OpenHome CLI is restored at a persistent location. The current ability package
  passes validation. Login, platform deployment, assignment and a spoken platform request
  remain unverified.
- The full device run finished: 4,053 held, 0 failed, 5 skipped, all 419 hostile inputs
  examined. Later library and ability changes passed their targeted device checks.
- Kernel 2.2.2 is installed and verified in both interpreters. Its exact artifact is
  hash-pinned in the ability requirements. The published release was downloaded on the
  DevKit with pip hash checking; its bytes match the installed artifact.

## Deployed repairs

The running voice code now rejects failed, empty or invalid synthesis output instead of
playing a previous answer. Playback failures have their own error result. `[said]` records
speech prepared for playback; `[spoken]` records successful, uninterrupted player
completion. Neither log marker alone proves acoustic audibility to a person.

Deployment identifies its wheel from build inputs and verifies the installed extension,
wrapper and manifest in both Python interpreters. Compiler and pip failures cannot be
hidden by a stale wheel. Restart guards also ensure that failed restart, inactive
loop and a kiosk that still owns the microphone cannot be reported as deployment success.
Library indexing and required service setup errors are no longer suppressed. All 18
changed device source/test/shim files match the checkout. The loop is active with PID
21518, started September 5 at 00:24:12 HST.

Library repairs give each file its own provenance. Reindexing replaces that file's
passages and preserves sibling outlines. A schema rebuild is constructed separately and
published atomically; failure preserves the old index. Linked-directory cycles are
visited once, and partial-read warnings persist across unchanged index runs.

The final library has 191 physical inputs, 191 indexed source rows, 35 named sources
and 412,826 passages. All source hashes and per-file passage counts match the actual
files and FTS rows. SQLite integrity passes, with no empty sources or unread warnings.

Britannica Volume 29 was unreadable and Volume 3 truncated in the local archives. Only
the device copies were replaced; the original Media archive and a verified pre-rebuild
SQLite backup are preserved. All 29 on-device volume files now match Internet Archive
SHA-1 records. Retrieval reaches both recovered volumes. Those measurements were warm
queries; a cold-cache benchmark was not performed. Plain OCR text in these volumes has
no reliable page markers, and checksum integrity does not correct OCR recognition errors.

Ability fixes reject named refusals and ambiguous route choices. A failed hub is
reported even when a fallback kernel is installed but cannot answer. The foreground
request deadline covers the bounded hub answer and offer subprocesses. Root-invoked
checks preserve temporary audit state across the user boundary, keeping production
memory, notes and timers out of the test run.

## Verification receipts

| Run | Held | Failed | Skipped | Scope |
|---|---:|---:|---:|---|
| Mac full | 4,031 | 0 | 12 | All 419 hostile inputs; updated library and ability |
| Device full | 4,053 | 0 | 5 | All 419 hostile inputs; installed native kernels and models |
| Device later changes | 316 | 0 | 3 | Library, pages, ability, deployment, shipped artifact and honesty |
| Device final license/package | 41 | 0 | 2 | Latest licensed wheel, deployment and installed artifact |
| Actual root shim | 179 answers + 8 calls | 0 | 0 | Pinned answers, telemetry and runtime contract; isolated state |

The device full run preceded the library and ability revisions, which the later targeted
run covers. The final license metadata change has its own package and root-shim receipts.

Mac skips for native mathematics, MECH reading, dictionary, Linux pipe behavior, Vosk,
Spanish voice, page-numbered books and compiled-package behavior are covered on the
DevKit. The separate flake8 7.3.0 run passed on all three ability files. The trained wake
head is intentionally retired. Device skips for Mac installation scripts and package
metadata are covered in the workspace. Removed README measurement tables are not an
active capability. The optional platform daemon and real human speech remain separate,
unverified surfaces despite software fixture passes.

The detailed per-suite counts, verbatim skip reasons, negative controls and source hashes
are in `~/AstralBrainEngine/projects/openhome/audits/2026-09-04-completion/` on the Mac,
starting with `AUDIT.md` and `TEST-COVERAGE.md`. Local receipts are not included in the
public repository because they describe the owner's device and library.

## Machines and paths

| Item | Location |
|---|---|
| DevKit | `openhome@192.168.1.23`, Raspberry Pi 4, 8 GB, Python 3.13.5 |
| Private development checkout | `~/Documents/OpenHome-Astral/hub/` on the Mac |
| Device loop | `~/astral-voice/hub-v2/` |
| Voice interpreter | `~/astral-voice/kws-venv/bin/python3` |
| User state | `~/astral-voice/state/` |
| Library and index | `~/astral-voice/library/` |
| Voice log | `~/astral-voice/astral-hub.log` |
| Full audit receipts | `~/astral-checks/codex-completion-20260904/` on the device |

The public repository contains the MIT ability and deployment scripts. The private hub
repository is required to rebuild the local loop. The compiled engine is installed in
both the voice environment and system Python, which OpenHome invokes as root.

## Develop and verify

```sh
python3 hub/tests/run.py --full
python3 hub/tests/run.py library ability voice deployment
openhome validate community/astral
```

On the device:

```sh
SSH_AUTH_SOCK= ssh openhome@192.168.1.23   'cd ~/astral-voice/hub-v2 && ~/astral-voice/kws-venv/bin/python3 tests/run.py --full'
```

Retain the exit code and complete log. The normal discovery run has a time cap for the
hostile corpus; `--full` removes it. Software fixtures and actual human speech are
separate evidence. The runner isolates mutable user state; real device data is still
needed for checks of installed models, native kernels and the library.

## Deploy the local loop

```sh
deploy/install_v2.sh openhome@192.168.1.23 --start
```

A running loop is restarted after a successful deployment even without `--start`. The
startup command stops OpenHome's kiosk first: one microphone, one owner. To return the
microphone to OpenHome, stop Astral before starting `openhome-dashboard.service`.

The rsync include list is explicit. A new data directory must be added there, then its
actual device files checked. The deploy preserves the device's measured cost profile;
it must not copy Mac measurements over it.

OpenHome owns both audio settings. The existing installation migration changes only an
untouched default `MIC_SENSITIVITY` of 30 to 160. The runtime never forces mixer levels.
Live speaker volume is 65 percent, while OpenHome has saved `SPEAKER_VOLUME=14`. The
app must reconcile that discrepancy; direct mixer or configuration overwrites are not
a substitute. Reboot persistence and the app slider still need direct verification.

## Ship the platform ability

The Mac CLI is the creator's fork of `Jmesmykil/openhome-cli`, installed from
`~/.local/share/openhome-cli`. Its validator contains the DevKit contract fix. Do not
replace that fork with an upstream update without checking that fix.

```sh
openhome login
openhome validate community/astral
openhome deploy community/astral --name Astral --category local --json
openhome assign
openhome trigger "what time is it"
```

Login must be completed locally. Keep credentials out of transcripts and retain a
sanitized deployment/assignment receipt. Device-file parity does not prove that the
platform registered hotwords or routed a spoken turn. The optional background daemon
is a separate ability category and is not proved by foreground validation.

## Release and outstanding acceptance

Follow [RELEASE.md](RELEASE.md). Use a new version for a new artifact, retain its hash and
pin the exact download. Do not overwrite the published v2.2.1 asset with a different wheel.

Remaining acceptance work includes authenticated platform routing, human wake positives and room negatives, short follow-ups, interruption
while speaking and thinking, and app/reboot audio persistence. The two empty transcriptions in
the September 4 quiet-room pass remain open until measured again.

The creator reported submitting the grant. Its proposed harness bridge and the longer
term deterministic-engine ambition remain future work. Do not present those as delivered
features of this release, and do not infer completed portfolio releases from development
status or commit counts.
