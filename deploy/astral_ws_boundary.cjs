"use strict";

// The root control socket is for the device kiosk and local diagnostics only.
// Browser Origin is checked in addition to loopback binding to reject foreign
// pages attempting to use the local service. It is not local-process identity.
const kioskOrigins = new Set([
  "http://127.0.0.1:3000",
  "http://localhost:3000",
]);

module.exports = function localControlOptions(port) {
  return {
    port,
    host: "127.0.0.1",
    maxPayload: 65536,
    verifyClient({ req }) {
      const peer = req.socket.remoteAddress;
      if (peer !== "127.0.0.1" && peer !== "::ffff:127.0.0.1") return false;
      const localPort = req.socket.localPort;
      const host = req.headers.host;
      if (host !== `127.0.0.1:${localPort}` && host !== `localhost:${localPort}`) {
        return false;
      }
      // Non-browser clients on the device have no Origin. A browser-supplied
      // null, malformed or unrelated Origin must never receive the snapshot.
      const origin = req.headers.origin;
      return origin === undefined || kioskOrigins.has(origin);
    },
  };
};
