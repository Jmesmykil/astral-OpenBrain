"use strict";
const assert = require("node:assert/strict");
const { once } = require("node:events");
const { WebSocket, WebSocketServer } = require("ws");
const options = require("./astral_ws_boundary.cjs");
const fs = require("node:fs");
const vm = require("node:vm");
assert.ok(process.argv[2], "Pass the actual staged platform index.js");
const source = fs.readFileSync(process.argv[2], "utf8");
const start = source.indexOf('wss.on("connection", (ws) => {');
const end = source.indexOf('console.log(`WebSocket server running', start);
assert.ok(start >= 0 && end > start);
const connectionBlock = source.slice(start, end);

(async () => {
  const server = new WebSocketServer(options(0));
  await once(server, "listening");
  const port = server.address().port;
  const results = [];
  let accepted = 0, received = 0;
  // Exercise the actual platform connection handler. Only its environment
  // snapshot and hardware actions are stubbed; error handling is not invented.
  vm.runInNewContext(connectionBlock, {
    wss: server, setInterval, clearInterval,
    console: { log() {}, error() {}, warn() {} },
    getEnvSnapshot: () => ({ test_snapshot: true }),
    handleSystemAction: () => { throw Error("unexpected hardware action"); },
    mqttController: {}, require: () => { throw Error("unexpected capability"); },
  });
  server.on("connection", ws => {
    accepted++;
    ws.on("message", () => received++);
  });
  async function probe(name, headers, allowed, oversized = false, hostname = "127.0.0.1") {
    const before = accepted;
    const result = await new Promise((resolve, reject) => {
      const ws = new WebSocket(`ws://${hostname}:${port}`, { headers, handshakeTimeout: 1500 });
      const timer = setTimeout(() => { ws.terminate(); reject(Error(name + " timed out")); }, 2500);
      ws.on("unexpected-response", (_req, res) => {
        res.resume(); clearTimeout(timer); ws.terminate(); resolve({ status: res.statusCode });
      });
      ws.on("error", error => { if (allowed) { clearTimeout(timer); reject(error); } });
      ws.once("message", data => {
        assert.deepEqual(JSON.parse(data.toString()), {test_snapshot:true});
        if (oversized) ws.send(Buffer.alloc(65537));
        else ws.close();
      });
      ws.on("close", code => { clearTimeout(timer); resolve({ code }); });
    });
    if (allowed) {
      assert.equal(accepted, before + 1, name);
      assert.equal(result.code, oversized ? 1009 : 1005, name);
    } else {
      assert.equal(result.status, 401, name);
      assert.equal(accepted, before, name + " must receive no snapshot");
    }
    results.push({ name, passed: true, ...result });
  }
  try {
    assert.equal(server.address().address, "127.0.0.1");
    await probe("local diagnostic", {}, true);
    await probe("existing kiosk origin", { Origin: "http://127.0.0.1:3000" }, true);
    await probe("localhost kiosk alias", { Origin: "http://localhost:3000" }, true);
    await probe("existing localhost websocket URL", {}, true, false, "localhost");
    for (const origin of ["https://example.invalid", "https://app.openhome.com", "null", "http://127.0.0.1:3001", "http://127.0.0.1:3000.evil.invalid", "http://127.0.0.1:3000/"]) {
      await probe("reject origin " + origin, { Origin: origin }, false);
    }
    await probe("reject rebinding host", { Host: `evil.invalid:${port}` }, false);
    await probe("reject forwarded host claim", { Host: `evil.invalid:${port}`, "X-Forwarded-Host": `localhost:${port}` }, false);
    await probe("oversized local frame", {}, true, true);
    assert.equal(received, 0);
    const verify = options(0).verifyClient;
    assert.equal(verify({ req: {socket: {remoteAddress: "192.0.2.1", localPort: port}, headers: {host: `localhost:${port}`}}}), false);
    results.push({name:"non-loopback peer rejected even with allowed Host",passed:true});
    console.log(JSON.stringify({passed:results.length,failed:0,results}, null, 2));
  } finally {
    for (const ws of server.clients) ws.terminate();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
