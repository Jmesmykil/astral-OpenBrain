# Kernel release procedure

[Release 2.2.3](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.3) is published.
The ability's exact requirements dependency was downloaded successfully on the DevKit with
`pip download --no-deps --require-hashes`. Its bytes and an independent unauthenticated
public download match the target-built artifact installed in both device interpreters.
The exact updated ability package passes `openhome validate community/astral`.
Platform authentication, deployment, assignment and spoken routing remain separate and open.

| Artifact property | Verified value |
|---|---|
| File | `astral_kernel-2.2.3-cp313-cp313-linux_aarch64.whl` |
| Size | 474035 bytes |
| SHA256 | `68378bef23dc3d53387689130bba192cd9f4293107d7f86a10a605ce6e32ff8f` |
| Generated input | `9fca5603fc4f9a10e240b404cab54a2166b1fba272909242ef052d3916f47cc4` |
| Build source | private hub `13969e80be21ca1badfd0eeff7a12494f4f417f6` |
| Verified companion hub | `63fa1668ef345b21a17ac7c8de3f04ce78f7c6bc`; compiled inputs unchanged |
| Release target | public `a3a50785dc8d904c07acca8b6295382c52c5b7f4` |
| Target | CPython 3.13 / Linux aarch64 |
| Engine metadata license | Proprietary |

The MIT ability shim remains readable and separate. The wheel packages the compiled
extension, public wrapper, build manifest and distribution metadata; no private Python,
Cython or C source is included. Timer persistence changes are compiled into the wheel.
Library, voice, notes/settings and shared mathematics-server repairs require the companion
hub deployment. See [HANDOFF.md](HANDOFF.md) for the exact layered tests and open acceptance.

The release receipt is under
`~/AstralBrainEngine/projects/openhome/audits/2026-09-05-ponytail-premortem/release/`.
It retains build/installed identity, publication, public-download and exact consumer receipts.

## Preserve immutable versions

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
