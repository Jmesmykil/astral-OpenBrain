// Native DevKit execution with confined source paths and one script per request.
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { randomUUID } = require("node:crypto");
const { spawn } = require("node:child_process");

// On a paired install (the turn router lives beside this dispatcher) the Astral daemon
// must not act through the native path: the local hub owns alerts, the corpus and the
// kernel. These autonomous functions are declined for Astral's own capability names only;
// foreground respond/route_answer/health/telemetry/device_control and every other ability
// keep their behavior. The router file and the name list are read per request, so pairing,
// unpairing or registering another name takes effect without a restart.
const PAIRED_MARKER = "astral_turn_router.cjs";
const AUTONOMOUS_FUNCTIONS = new Set(["respond_now", "due_alerts", "heard"]);
// The package's own folder names. An account registers the ability under names of its
// own, and those are listed on the device, one per line, in the file on_device.sh reads
// to refresh each registered folder; they are read from there, never written here.
const PACKAGE_NAMES = ["astral", "astral-daemon"];
const REGISTRATIONS = path.join("astral-voice", "state", "openhome-capability-names.txt");
const REGISTRATION_NAME = /^[A-Za-z][A-Za-z0-9]*$/;
const REGISTRATIONS_MAX_BYTES = 65536;
// The exact nested shape the daemon's health checks read as "healthy, nothing to say".
const QUIET_OUTPUT = JSON.stringify({success: true, spoken_response: "", data: {}, error: null});
const ID_PATTERN = /^[A-Za-z0-9_-]{1,128}$/;

// Where Astral's state lives: ASTRAL_HOME when set, else the running user's home when the
// install is there, else the stock DevKit user's. The platform runs this as root, whose
// own home holds nothing of Astral's.
function astralHome() {
  if (process.env.ASTRAL_HOME) return process.env.ASTRAL_HOME;
  const home = os.homedir();
  return fs.existsSync(path.join(home, "astral-voice")) ? home : "/home/openhome";
}

// The package names plus every registration name the device lists. A missing list leaves
// the package names; a link, a non-regular file, an oversized file or a malformed line
// adds nothing, the same names on_device.sh would refuse to install.
function astralNames() {
  const names = new Set(PACKAGE_NAMES);
  let fd;
  try {
    fd = fs.openSync(path.join(astralHome(), REGISTRATIONS),
                     fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    const info = fs.fstatSync(fd);
    if (!info.isFile() || info.size > REGISTRATIONS_MAX_BYTES) throw new Error("not a small regular file");
    for (const name of fs.readFileSync(fd, "utf8").split("\n")) {
      if (REGISTRATION_NAME.test(name)) names.add(name);
    }
  } catch (err) {
    if (err.code !== "ENOENT") console.error("Ignoring the capability name list:", err.code || err.message);
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
  return names;
}

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
    if (AUTONOMOUS_FUNCTIONS.has(function_name) && fs.existsSync(path.join(__dirname, PAIRED_MARKER)) &&
        astralNames().has(capability_name)) {
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
