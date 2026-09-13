// Native DevKit execution with confined source paths and one script per request.
const fs = require("node:fs");
const path = require("node:path");
const { randomUUID } = require("node:crypto");
const { spawn } = require("node:child_process");

// On a paired install (the turn router lives beside this dispatcher) the Astral daemon
// must not act through the native path: the local hub owns alerts, the corpus and the
// kernel. These autonomous functions are declined for these aliases only; foreground
// respond/route_answer/health/telemetry/device_control and every other ability keep
// their behavior. The router file is checked per request, so losing its token or
// removing the router later takes effect without a restart.
const PAIRED_MARKER = "astral_turn_router.cjs";
const AUTONOMOUS_FUNCTIONS = new Set(["respond_now", "due_alerts", "heard"]);
const DAEMON_ALIASES = new Set(["openbrain", "openbraindaemon",
                                "astral", "astral-daemon", "jamesmykilastral"]);
// The exact nested shape the daemon's health checks read as "healthy, nothing to say".
const QUIET_OUTPUT = JSON.stringify({success: true, spoken_response: "", data: {}, error: null});
const ID_PATTERN = /^[A-Za-z0-9_-]{1,128}$/;

module.exports = function handleCapability(ws, payload) {
  const { capability_name, function_name, args = [], _astral } = payload || {};
  let script;
  let finished = false;
  let correlation = null;
  function finish(success, output, error) {
    if (finished) return;
    finished = true;
    if (script) {
      try { fs.unlinkSync(script); } catch (err) {
        if (err.code !== "ENOENT") console.error("Could not remove capability request file:", err.message);
      }
    }
    const result = {type: "devkit-capability-result", data: {
      capability_name: capability_name || null,
      function_name: function_name || null,
      args, success, output: output || null, error: error || null,
    }};
    if (correlation) result._astral = correlation;
    // The child's close handler may outlive the page that asked: never throw at a dead socket.
    if (!ws || (ws.readyState !== undefined && ws.readyState !== 1)) {
      console.error("Local socket closed before the capability result could be delivered");
      return;
    }
    try { ws.send(JSON.stringify(result)); }
    catch (err) { console.error("Could not deliver capability result:", err.message); }
  }
  try {
    if (typeof capability_name !== "string" || !/^[A-Za-z0-9_-]+$/.test(capability_name) ||
        typeof function_name !== "string" || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(function_name) ||
        !Array.isArray(args) || !args.every(x => ["string", "number", "boolean"].includes(typeof x))) {
      throw new Error("Invalid capability name, function name or arguments");
    }
    // Local-only correlation from the App. Absent means a legacy standalone request;
    // present means both browser-generated ids must be well formed, or nothing runs.
    if (_astral !== undefined) {
      if (!_astral || typeof _astral !== "object" || Array.isArray(_astral) ||
          typeof _astral.request_id !== "string" || !ID_PATTERN.test(_astral.request_id) ||
          typeof _astral.turn_id !== "string" || !ID_PATTERN.test(_astral.turn_id)) {
        throw new Error("Invalid request correlation");
      }
      correlation = {request_id: _astral.request_id, turn_id: _astral.turn_id};
    }
    if (AUTONOMOUS_FUNCTIONS.has(function_name) && DAEMON_ALIASES.has(capability_name) &&
        fs.existsSync(path.join(__dirname, PAIRED_MARKER))) {
      console.error("Declined autonomous native call on paired install:", capability_name, function_name);
      finish(true, QUIET_OUTPUT, null);
      return;
    }
    const root = path.resolve(__dirname, "..");
    const caps = fs.realpathSync(process.env.LOCAL_CAPABILITIES_DIR || path.join(root, "local_capabilities"));
    const source = fs.realpathSync(path.join(caps, capability_name, "devkit_functions.py"));
    const relative = path.relative(caps, source);
    if (relative === ".." || relative.startsWith(".." + path.sep) || path.isAbsolute(relative)) {
      throw new Error("Capability script is outside the configured capability directory");
    }
    if (!fs.statSync(source).isFile()) throw new Error("Capability script must be a regular file");
    // Keep the platform root on Python's import path, as before, but never let a
    // concurrent request overwrite the script another child is about to read.
    const target = path.join(root, ".astral-call-" + randomUUID() + ".py");
    fs.copyFileSync(source, target, fs.constants.COPYFILE_EXCL);
    script = target;
    const child = spawn("sudo", ["python3", script, function_name, ...args.map(String)], {
      stdio: ["ignore", "pipe", "pipe"], timeout: 15000,
    });
    let stdout = "", stderr = "";
    child.stdout.on("data", chunk => { stdout += chunk.toString(); });
    child.stderr.on("data", chunk => { stderr += chunk.toString(); });
    child.on("close", (code, signal) => finish(code === 0, stdout.trim(),
      code === 0 ? null : stderr.trim() || `Exited with ${signal || code}`));
    child.on("error", err => finish(false, null, err.message));
  } catch (err) {
    finish(false, null, err.message);
  }
};
