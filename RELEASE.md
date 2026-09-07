# Kernel release procedure

[Release 2.2.6](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.6) is published.
It fixes a wrong answer found by playing a question through the device's own speaker. Asked
"and in london" as a follow-up to a turn that was itself misheard, the completion produced
"what time is in london" — without its "it" — which matched nothing in the clock, escalated
to the model tier, and was answered out loud with "Time downloaded software." The clock now
accepts the dropped word; sentences that merely contain "time" still do not match.

| Artifact property | Verified value |
|---|---|
| File | `astral_kernel-2.2.6-cp313-cp313-linux_aarch64.whl` |
| Size | 494785 bytes |
| SHA256 | `e9d723d618c58a870aa7498dfb24476df3ee414b0539d7d73e8b86de72e3bc15` |
| Generated input | `8d250cadbbb3f52226abd4990fb4bf2ce5315e6da2186a8e72e5862b882546b8` |
| Compiled extension | `8f101cec7bd0a34ea76edea7a0e592f919a9c084815857736fcb9f66ccb89d65`, byte-identical in both device interpreters |
| Verified companion hub | device full suite 5,111 held, zero failed, five skipped |
| Target | CPython 3.13 / Linux aarch64 |
| Engine metadata license | Proprietary |

Verified after publication: an independent unauthenticated public download matches, and the
updated package passes `openhome validate community/astral`.

## Preserve immutable versions

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
