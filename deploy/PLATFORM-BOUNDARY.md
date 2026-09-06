# Native control socket boundary

The September 5 audit reproduced unauthenticated LAN access to the root WebSocket
on3030. Connecting returned a populated API_KEY field. Only presence booleans were
retained; the key was never printed or saved. Exposure does not prove misuse.

The deployed fix binds127.0.0.1, accepts exact kiosk origins
http://127.0.0.1:3000 and http://localhost:3000, checks Host and loopback peer,
and limits frames to64KiB. Non-browser local clients may omit Origin. Socket errors
are handled without restarting Node. The actual kiosk connects to localhost3030
and its launch script opens127.0.0.1:3000. Local processes remain trusted; this is
not local process authentication.

Copy astral_ws_boundary.cjs beside platform index.js. Run patch_devkit_boundary.py
<index.js> for a dry run, then --apply. It admits only two exact audited revisions,
verifies the helper, checks syntax, retains backups and changes only the WebSocket
construction and connection error handler. Restart only openhome_node_server.service.
Unknown upstream revisions require inspection. Revalidate after platform updates.

Run NODE_PATH=<platform node_modules> node test_ws_boundary.cjs <patched index.js>.
The harness runs the actual connection-handler code, using a harmless snapshot and
disabled hardware actions.14 cases passed on both Mac and DevKit. The original
handler fails the oversized-frame control. The patcher passed14 checks across both
admitted revisions. Counts overlap across machines and are not unique-case totals.

Live production: LAN ECONNREFUSED; foreign Origin and misleading Host401; oversized
frame closes1009; reconnection succeeds with unchanged Node PID. Three native answers
passed. All46 protected file hashes, voice/math/bridge PIDs and14/160 audio levels
were unchanged. Node PID66150/NRestarts0; platform client PID42226 at this milestone.

Final index SHA256:
388e67a7f65bbeeb416bd317bbe86e2fd3c4d67f6eecf255c4a49050bcebbce7
Helper SHA256:
6f3b3d839a8eadb15c653b708069b155a08c2c82fd3b49545ab988ccdec5bf3b

Backups index.js.before-astral-boundary-* preserve prior bytes. Restoring the original
wildcard listener reopens exposure. If recovery is needed, stop only the Node control
service while reconstructing the reviewed boundary; independent local voice/math
can continue. Do not silently restore an exposed listener.

The prior device key should be rotated through the owner's normal OpenHome account
and supported device configuration. No credential was changed. Actual kiosk/account
voice and app-slider acceptance remains open; simulated headers are protocol proof.
