# Releasing the kernel wheel

The ability's `requirements.txt` installs `astral-kernel` from a GitHub release by URL. OpenHome's installer runs pip
on the DevKit, so the wheel has to be somewhere pip can fetch it. The current build is
`astral_kernel-2.2.1-cp313-cp313-linux_aarch64.whl` (built on the DevKit, CPython 3.13, aarch64,
460 KB), published as release v2.2.1 of Jmesmykil/astral-OpenBrain; the deploy rebuilds it on the
device whenever a source file is newer than the wheel, and the release asset is replaced after each
rebuild. Two ways to host it; both are the owner's decision:

1. **PyPI** (simplest for OpenHome): `python3 -m twine upload hub/kernel/dist/*.whl` with your
   PyPI account. The name `astral-kernel` must be free or yours.
2. **A GitHub release asset**: attach the wheel to a release and point requirements.txt at it:
   `astral-kernel @ https://github.com/Jmesmykil/astral-OpenBrain/releases/download/v2.2.1/astral_kernel-2.2.1-cp313-cp313-linux_aarch64.whl`
   (this is what requirements.txt says today)

Until one of these is done, the ability installs only on a device that already has the hub.
