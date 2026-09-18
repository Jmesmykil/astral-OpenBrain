# OpenHome audio runtime

This package captures the seven audio configuration files used on the development
DevKit on September 12, 2026. It complements the paired browser/Node deployment;
it does not install the hub, models or browser.

Run as openhome on the supported VoiceHAT device, using Python 3:

    python3 install-audio-runtime.py plan
    python3 install-audio-runtime.py verify
    python3 install-audio-runtime.py apply
    python3 install-audio-runtime.py rollback <backup-directory>

Plan exits 3 when changes are needed. Verify exits nonzero for a failed contract.
Apply refuses to run without the VoiceHAT, the WebRTC echo-cancellation plugin, active
RTKit and polkit, the openhome user, non-interactive sudo, a writable backup root and the
hub unit, or while a room test holds its lock (`--room-lock`, default
`~/astral-voice/platform-hardening/.acoustic-calibration.lock`). A hostname or
PipeWire/WirePlumber version other than those in ORIGIN.txt is reported as a warning.

The first apply records this device's saved (`~/.env`) and live speaker and microphone
levels in `installed-levels.json` in the backup root. Later applies and rollbacks refuse
to run if the saved levels have changed since, verify compares the live levels with the
record, and after a full audio-stack restart the levels are returned to it. Remove that
file to record the current levels at the next apply. Microphones and Chromium stay
muted. The prior global sink mute value is restored, including on errors.
Use --backup-root or --report-dir before the subcommand to override their locations.

Apply backs up existing targets with their actual bytes/mode/uid/gid. Rollback changes
only targets written by that transaction and refuses conflicting current bytes.
The default backup directory is ~/astral-voice/platform-hardening/audio-runtime-backups.
Keep it. An abrupt crash between a file write and its metadata update can require
manual reconciliation from that backup; crash-atomic recovery is not claimed.

Current settings: native echo cancellation with a speaker-monitor reference,
960/48000 block timing, HAT headroom 1024, preserved channel timing with
node.link-group cleared, and no Chromium stream property restoration.
RTKit authorization is scoped to user openhome and retains its RR20 limit/watchdog.
Noise/transient suppression use their defaults.

Validation of the captured configuration: 23 unit checks passed on Mac and Pi. On the
live device a no-op apply changed nothing and restarted nothing. A fixture differing by one harmless hub
drop-in comment applied, restarted the hub, and rolled back. All original bytes
and metadata were checked afterward; all 38 runtime checks passed. This exercises
the hub restart level. Other levels and error paths have controlled unit evidence,
not equivalent fresh-device or reboot proof. The level record and the version warnings
came later and are covered by the 26 unit checks only, not by a device run.

    python3 -m unittest -v test_audio_runtime.py

Physical interruption still sometimes loses the next question through echo
cancellation. The audio configuration is a verified development state, not acoustic
release acceptance. See [the known limitations](../../KNOWN-BUGS.md).

