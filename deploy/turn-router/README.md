# Paired voice routing

This source bundle matches the V9 browser, native dispatcher and loopback bridge installed on the DevKit on September 12. The hub owns microphone admission and local ranking; the browser plays selected agent turns and opens no microphone. Verified AEC voice interruption is armed in the development configuration, but physical speech preservation still fails during some overlapping turns. Both microphone sources are currently paused; see ../../HANDOFF.md.

The installation and rollback receipts are in the Astral Engine project's acceptance/protocol-20260912 directory. The device backup is /home/openhome/astral-voice/platform-hardening/single-router-20260912/rollback-v9-20260912-155348. Acoustic acceptance is still pending.

install_v2.sh checks this exact browser/bridge pair before any local or device write, preserves device routing choices while refreshing the Mac address, and keeps the paired browser running when restarting the hub. A fresh device needs the coordinated browser/Node installation first; the hub-only installer refuses an incompatible pair.

Keep protocol.json synchronized with a verified browser build. check_installed.py checks the turn router, native dispatcher and App source hashes, actual served assets, and authenticated local registration. It never prints credentials or starts services. Preserve the existing Node socket boundary.

The native dispatcher is `../astral_capability.cjs`. On paired installs it declines autonomous `respond_now`, `due_alerts` and `heard` calls for the installed Astral aliases before executing any shim. The hub owns those jobs. Foreground ability calls and unrelated abilities remain available. Changing an Astral capability's installed name requires updating and testing the alias set; same-named functions on other abilities are not suppressed.

Native results carry local request/turn identity and return only to the requesting, still-current agent socket. This metadata never reaches the cloud. Work already explicitly dispatched may finish after an interruption; its result cannot enter a later conversation, and already-performed side effects are not rolled back.

Install the dispatcher and browser as one stopped-service transaction, or install/restart the dispatcher before starting the new browser. A new browser with the old dispatcher cannot correlate results. Backend capability synchronization touches the shim cache and cannot overwrite this persistent dispatcher. An old hub without the paired router must still use one speech owner at a time; simultaneous independent hub/daemon operation is unsupported.
