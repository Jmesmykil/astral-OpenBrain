# Native control socket boundary

The DevKit's Node control service (`openhome_node_server.service`, `index.js`) serves a
WebSocket on port 3030 for the kiosk and local diagnostics. This patch confines it to
those callers:

- It listens on 127.0.0.1 only, so nothing off the device can connect.
- It accepts a connection only from a loopback peer, with a `Host` of
  `127.0.0.1:<port>` or `localhost:<port>`.
- A browser must send the kiosk's exact `Origin`, `http://127.0.0.1:3000` or
  `http://localhost:3000`. Non-browser clients on the device send no `Origin` and are
  accepted; a `null`, malformed or unrelated `Origin` is refused before anything is sent.
- Frames are limited to 64 KiB; a larger frame closes the connection with 1009.
- Each connection gets an error handler, so a socket error is logged instead of
  restarting Node.

Local processes remain trusted: this is not authentication of local processes. The kiosk
connects to `localhost:3030` from `127.0.0.1:3000` and keeps working unchanged.

## Apply

Copy `astral_ws_boundary.cjs` beside the platform's `index.js`, then:

```sh
python3 patch_devkit_boundary.py <index.js>            # dry run: prints what would change
python3 patch_devkit_boundary.py <index.js> --apply
```

The patcher admits only the two reviewed revisions of `index.js`, identified by SHA-256,
and refuses any other: a new upstream version needs inspection first, so re-check after
platform updates. It verifies that the helper beside `index.js` is byte-identical to the
shipped one, checks the result with `node --check`, keeps a backup and changes only the
WebSocket construction and the connection error handler. Restart only
`openhome_node_server.service`.

Helper SHA-256:
`6f3b3d839a8eadb15c653b708069b155a08c2c82fd3b49545ab988ccdec5bf3b`.
Patched `index.js` SHA-256 on the reviewed platform version:
`388e67a7f65bbeeb416bd317bbe86e2fd3c4d67f6eecf255c4a49050bcebbce7`.

## Verify

```sh
NODE_PATH=<platform node_modules> node test_ws_boundary.cjs <patched index.js>
```

The harness runs the platform's own connection handler behind the boundary, with a
harmless snapshot and hardware actions disabled. It expects the kiosk origins and a local
client without `Origin` to be accepted; foreign origins and a misleading `Host` to get
401 and no snapshot; a non-loopback peer to be refused; and an oversized frame to close
with 1009. Fourteen cases pass.

On the device afterwards: a connection to port 3030 from another machine is refused
(ECONNREFUSED), and a foreign `Origin` or `Host` from the device itself gets 401. An
oversized frame closes only its own connection: the client reconnects, and the Node
service keeps its PID and restart count.

## Restore

The patcher's backup, `index.js.before-astral-boundary-<first 16 hex of the old hash>`,
holds the exact prior bytes. To restore, stop only the Node control service, copy the
backup over `index.js` and start the service again; the voice loop and the mathematics
service can keep running. Restoring puts back the original listener, which accepts
connections on every interface, so prefer re-applying the boundary once the cause of the
restore is fixed.
