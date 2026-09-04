# Releasing the kernel wheel

The ability's `requirements.txt` names `astral-kernel>=2.1.0`. OpenHome's installer runs pip
on the DevKit, so the wheel has to be somewhere pip can fetch it. The current build is
`hub/kernel/dist/astral_kernel-2.2.0-cp313-cp313-linux_aarch64.whl` (built on the DevKit,
CPython 3.13, aarch64, 401 KB). Two ways to host it; both are the owner's decision:

1. **PyPI** (simplest for OpenHome): `python3 -m twine upload hub/kernel/dist/*.whl` with your
   PyPI account. The name `astral-kernel` must be free or yours.
2. **A GitHub release asset**: attach the wheel to a release and point requirements.txt at it:
   `astral-kernel @ https://github.com/<you>/<repo>/releases/download/v2.2.0/astral_kernel-2.2.0-cp313-cp313-linux_aarch64.whl`

Until one of these is done, the ability installs only on a device that already has the hub.
