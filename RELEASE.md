# Kernel release procedure

The OpenHome ability installs a compiled `astral-kernel` wheel from a GitHub release URL.
The target is CPython 3.13 on Linux aarch64, matching the development DevKit. The readable
MIT shim is separate from the proprietary compiled engine.

The verified 2.2.2 artifact is installed on the development DevKit and pinned in the
ability requirements. [Release 2.2.2](https://github.com/Jmesmykil/astral-OpenBrain/releases/tag/v2.2.2)
is published. The DevKit downloaded the exact requirements dependency using
`pip download --require-hashes`; it matches the installed artifact. Do not clobber
an existing release asset: a version must keep identifying the same bytes.

- File: `astral_kernel-2.2.2-cp313-cp313-linux_aarch64.whl`
- Size: 460607 bytes
- SHA-256: `2c7ca3dc0b466a26f2279bf1a5ff14c06ff344f2643fcae9e00e247f0b0fd33e`
- Build input fingerprint: `75f6b21f0f50560d8112043d981aab778e5d3a12b9681fa3d1c2c968c9ea3d2e`
- Metadata license: `Proprietary`; no private Python, Cython or C source is packaged.

## Pending 2.2.3 candidate

The September 5 Ponytail/pre-mortem source changes require a new kernel version.
Generated 2.2.3 inputs have fingerprint
`9fca5603fc4f9a10e240b404cab54a2166b1fba272909242ef052d3916f47cc4`.
No 2.2.3 target wheel has been built, installed or published. The DevKit was unreachable
at its last address during this pass. Keep the ability pinned to the verified 2.2.2
artifact until the target build and consumer checks below finish. See [HANDOFF.md](HANDOFF.md)
for the source-test results and remaining device/platform acceptance.

## Build and verify

In the private hub checkout, change `VERSION` in `build_kernel.py`, then run its source
generator. `kernel/setup.py`, the wrapper and build manifest are generated outputs.
Build on the target device. `install_kernel.py` accepts only a wheel whose manifest,
wrapper, distribution version and extension match the current inputs and interpreter.
It installs and verifies that exact wheel in system Python and the voice environment.
Any compiler, installation or verification error returns nonzero.

The release receipt must contain the private source revision, generated-input fingerprint,
wheel filename, byte size and SHA-256, target interpreter/architecture, installed-byte
verification results, and the relevant test results with every skip named. Inspect the ZIP
members to confirm it contains the compiled extension, public wrapper, manifest and
license/metadata without private Python or Cython source.

## Publish and validate the consumer

Publish the verified wheel as a new release on `Jmesmykil/astral-OpenBrain`. Download that
exact public asset again and compare its SHA-256 with the verified build. Set
`community/astral/requirements.txt` to the immutable version URL with a `#sha256=` fragment.
Validate the exact ability package, then deploy and assign it through an authenticated
OpenHome session. Keep the returned receipt separate from local test output.

A passing local validator proves package shape. A matching wheel proves artifact identity.
Successful platform installation, assignment and a real spoken turn require their own
receipts. The public repository alone cannot rebuild the private hub.
