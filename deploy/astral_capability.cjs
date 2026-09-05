// Native DevKit execution with confined source paths and one script per request.
const fs = require("node:fs");
const path = require("node:path");
const { randomUUID } = require("node:crypto");
const { spawn } = require("node:child_process");

module.exports = function handleCapability(ws, payload) {
  const { capability_name, function_name, args = [] } = payload || {};
  let script;
  let finished = false;
  function finish(success, output, error) {
    if (finished) return;
    finished = true;
    if (script) {
      try { fs.unlinkSync(script); } catch (err) {
        if (err.code !== "ENOENT") console.error("Could not remove capability request file:", err.message);
      }
    }
    ws.send(JSON.stringify({type: "devkit-capability-result", data: {
      capability_name: capability_name || null,
      function_name: function_name || null,
      args, success, output: output || null, error: error || null,
    }}));
  }
  try {
    if (typeof capability_name !== "string" || !/^[A-Za-z0-9_-]+$/.test(capability_name) ||
        typeof function_name !== "string" || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(function_name) ||
        !Array.isArray(args) || !args.every(x => ["string", "number", "boolean"].includes(typeof x))) {
      throw new Error("Invalid capability name, function name or arguments");
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
