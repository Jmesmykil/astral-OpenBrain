# Kernel release procedure

[Release 2.2.5](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.5) is published.
It fixes a crash a stress run found: "what is 20 percent of" followed by four hundred digits
raised an OverflowError out of the number formatter and through the router, because an
integer that large becomes infinity the moment it is divided and both `round()` and `int()`
raise on that. The formatter is now total and an unsayable result is refused out loud.

| Artifact property | Verified value |
|---|---|
| File | `astral_kernel-2.2.5-cp313-cp313-linux_aarch64.whl` |
| Size | 494782 bytes |
| SHA256 | `737a77edd61de604b6c0abdee067e07994c791d2ef459fad2058324e5c7886c6` |
| Generated input | `a0a5aeab72225a4d7ed9191d6e1db67c83f6a04317942dc357e002c5988d0275` |
| Compiled extension | `fb3575861f4edb541d17e965301c5642935883d3a120f158c43024ac1dc9d01a`, byte-identical in both device interpreters |
| Verified companion hub | device full suite 5,106 held, zero failed, five skipped |
| Target | CPython 3.13 / Linux aarch64 |
| Engine metadata license | Proprietary |

Verified after publication: an independent unauthenticated public download matches, the
DevKit resolves the exact pinned dependency under `pip download --require-hashes` and gets
those same bytes, and the updated package passes `openhome validate community/astral`.

## Preserve immutable versions

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
