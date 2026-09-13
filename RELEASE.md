# Kernel release procedure

[Release 2.2.7](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.7) is the
current release and is what the DevKit runs.

| Artifact property | Verified value |
|---|---|
| File | `astral_kernel-2.2.7-cp313-cp313-linux_aarch64.whl` |
| Size | 494779 bytes |
| SHA256 | `a1107b5bc78d62e24325dbb5f0bb7818dd96c66b70f6a12f739308ebe8289081` |
| Engine source fingerprint | `2293f7c7478a58f4b72d8bb009a7765f2e692675f2d5b3bd7dd2e0be51508c16` |
| Installed on device | 2.2.7 in both interpreters; compiled extension `f429691b3b1fbdb4d3ebb157fcc41c0e`, identical in both |
| Target | CPython 3.13 / Linux aarch64 |
| Engine metadata license | Proprietary |

Verified after publication: an anonymous unauthenticated download matches the digest above,
the device's installed `build.json` carries the same engine source fingerprint as the build
inputs, and `openhome validate community/astral-devkit` passes.

`community/astral/requirements.txt` pins this release by SHA-256.

## Preserve immutable versions

Existing [2.2.6](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.6) remains
unchanged: 494785 bytes, SHA256 `c636265d3289bfc2706b376ef784ad85c0c32243e58b30cf87c4b613c3549d8e`. It fixed a wrong
answer found by playing a question through the device's own speaker. Asked "and in london"
as a follow-up to a turn that was itself misheard, the completion produced "what time is in
london", without its "it", which matched nothing in the clock, escalated to the model tier
and was answered out loud with "Time downloaded software." The clock now accepts the dropped
word; sentences that merely contain "time" still do not match.

Existing [2.2.5](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.5)
remains unchanged: 494782 bytes, SHA256
`737a77edd61de604b6c0abdee067e07994c791d2ef459fad2058324e5c7886c6`.

Existing [2.2.4](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.4)
remains unchanged: 492916 bytes, SHA256
`04b35dbc1da8c419d631876d27c839140453ff9d5182f40e3dbcae5a46a7558a`.

Existing [2.2.3](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.3)
remains unchanged: 474035 bytes, SHA256
`68378bef23dc3d53387689130bba192cd9f4293107d7f86a10a605ce6e32ff8f`. Its asset size was
rechecked after publishing 2.2.4.

Existing [2.2.2](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.2) remains
unchanged: 460607 bytes, SHA256
`2c7ca3dc0b466a26f2279bf1a5ff14c06ff344f2643fcae9e00e247f0b0fd33e`.
Its asset digest, size and update timestamp were rechecked after publishing 2.2.3. Never
clobber an existing asset: one version must continue to identify the same bytes.

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
