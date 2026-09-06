# Kernel release procedure

[Release 2.2.4](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.4) is published.
The ability's exact requirements dependency was downloaded on the DevKit with
`pip download --no-deps --require-hashes` and its bytes match the artifact installed in both
device interpreters; an independent unauthenticated public download matches as well. The
updated ability package passes `openhome validate community/astral`. Ability deployment,
assignment and spoken platform routing remain separate and open.

| Artifact property | Verified value |
|---|---|
| File | `astral_kernel-2.2.4-cp313-cp313-linux_aarch64.whl` |
| Size | 492916 bytes |
| SHA256 | `04b35dbc1da8c419d631876d27c839140453ff9d5182f40e3dbcae5a46a7558a` |
| Generated input | `2ba075e655022dfbecf86d96d2224bb9613d58df938e38b620c26266d22c4208` |
| Compiled extension | `29c630a6da1ab01c8c2760d3635c5cf901651f95645c9e4b9abedd5a5ecd22d5`, byte-identical in both device interpreters |
| Verified companion hub | `75b9da2`; device full suite 5,023 held, zero failed, five skipped |
| Target | CPython 3.13 / Linux aarch64 |
| Engine metadata license | Proprietary |

The MIT ability shim remains readable and separate. The wheel packages the compiled
extension, public wrapper, build manifest and distribution metadata; no private Python,
Cython or C source is included. Library, voice, notes/settings and shared mathematics
repairs require the companion hub deployment, not the wheel alone. See
[HANDOFF.md](HANDOFF.md) for the layered tests and the open acceptance.

## Preserve immutable versions

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
