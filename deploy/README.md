# Device deployment

Run `deploy/install_v2.sh openhome@<devkit> --start` from the private development
checkout to install and start the local loop. A running loop is restarted after a
successful deployment even when `--start` is omitted. The public repository does not
include the private `hub/` sources required by that script.

The deploy copies the hub through an explicit rsync include list, then runs
`on_device.sh`. New shipped directories must be included and their device hashes
verified. It preserves the device's measured cost profile and the owner's library and
state. It verifies the compiled wheel against current build inputs and verifies both
installed interpreters; a failed build or kernel install stops before restart.

The local loop and OpenHome's kiosk must not both own the microphone. `--start` stops the
kiosk before starting Astral. OpenHome owns the speaker and microphone levels. The loop
never adjusts them; the installer only changes OpenHome's untouched default microphone
setting from 30 (deaf to the wake phrase on the DevKit's microphone board) to 160, and
leaves any value somebody chose alone.

`devkit-config.json` is a historical device-side configuration example. The current
ability package also has its platform metadata in `community/astral/config.json`.
Editing a device file does not prove that the platform registered hotwords or assigned
an ability. Use the authenticated OpenHome CLI and retain the returned platform receipt.

The old `build_followup_pr.sh` workflow is retired. It reset a checkout and bundled engine
source, which does not match the current private-engine/compiled-dependency boundary.
It now exits without modifying a checkout. Do not follow the old instructions in the
historical `followup-pr-body.md`.

See [KNOWN-BUGS.md](../KNOWN-BUGS.md) for the current state and [RELEASE.md](../RELEASE.md) for packaging.
