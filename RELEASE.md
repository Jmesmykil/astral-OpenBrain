# Kernel release procedure

[Release 2.2.8](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.8) is the
current release and is what the DevKit runs.

| Artifact property | Verified value |
|---|---|
| File | `astral_kernel-2.2.8-cp313-cp313-linux_aarch64.whl` |
| Size | 504756 bytes |
| SHA256 | `99f716d2dcf1ae22cfd983f4e7c4b95347313347b184ba3d6c82250d8849eaa7` |
| Engine source fingerprint | `c682edb882ca058e359e6e0c08838ad9ed7fc427db014594079666933d422bcf` |
| Installed on device | 2.2.8 in both interpreters, verified by the deploy |
| Target | CPython 3.13 / Linux aarch64 |
| Engine metadata license | Proprietary |

Verified after publication: an anonymous unauthenticated download matches the digest above,
the device's installed `build.json` carries the same engine source fingerprint as the build
inputs, and `openhome validate community/astral-devkit` passes.

`community/astral/requirements.txt` pins this release by SHA-256.

## Preserve immutable versions

Three releases carry a published wheel. Never clobber an existing asset: one version must
continue to identify the same bytes.

| Release | Size | SHA256 |
|---|---|---|
| [2.2.8](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.8) | 504756 | `99f716d2dcf1ae22cfd983f4e7c4b95347313347b184ba3d6c82250d8849eaa7` |
| [2.2.7](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.7) | 494779 | `a1107b5bc78d62e24325dbb5f0bb7818dd96c66b70f6a12f739308ebe8289081` |
| [2.2.6](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.6) | 494785 | `c636265d3289bfc2706b376ef784ad85c0c32243e58b30cf87c4b613c3549d8e` |

2.2.8 answers tomorrow's and yesterday's date, sets a reminder given with no am or pm for the next
time the clock reads it, and says how far the Moon and the Sun are.

2.2.6 fixed a wrong answer found by playing a question through the device's own speaker.
Asked "and in london" as a follow-up to a turn that was itself misheard, the completion
produced "what time is in london", without its "it", which matched nothing in the clock,
escalated to the model tier and was answered out loud with "Time downloaded software."
The clock now accepts the dropped word; sentences that merely contain "time" still do not
match.

Tags `v2.2.5`, `v2.2.4`, `v2.2.3`, `v2.2.2`, `v2.2.1` and `v2.2.0` exist in git, and no
wheel was ever published for any of them; their asset URLs return 404. Sizes and digests
for those builds were recorded locally during development and cannot be reproduced by a
reader, so they are not listed here. A digest nobody can check against a file nobody can
fetch is worse than no digest at all.

## Build, publish and verify

Change `VERSION` in private `build_kernel.py`, then run its source generator. Generated
`kernel/setup.py`, wrapper and manifest derive from that source. Build on the target;
`install_kernel.py` accepts only a wheel whose manifest, wrapper, version and extension
match the current inputs and interpreter. Install and verify the exact artifact in system
Python and the voice environment. Any compiler, install or verification error is a failure.

Retain source revision, input fingerprint, filename, byte size, SHA256, interpreter and
architecture, ZIP-member/license inspection, installed-byte comparisons and all relevant
test logs with skips named. Later hub changes may reuse a not-yet-published artifact only
when its compiled input identity remains exact; new artifact bytes require a new version.

Publish the verified wheel under a new version, download the public asset independently,
and compare its hash. Pin the immutable URL with `#sha256=` in
`community/astral/requirements.txt`; verify that exact dependency using pip hash checking
on the target and validate the exact ability package. Deploy/assign through an authenticated
OpenHome session and retain its own receipt. Public source or green local tests cannot
substitute for platform routing and human acoustic acceptance.
