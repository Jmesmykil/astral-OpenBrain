#!/usr/bin/env python3
"""Astral — the DevKit half of the ability. A shim, deliberately.

WHAT THIS FILE IS

Everything the platform needs and nothing it does not. It takes a transcript from
`main.py`, asks the Astral engine for an exact answer, and prints one line of JSON. It
also reads this device's own telemetry and publishes MQTT for device control, because
those are I/O and I/O belongs on this side of the line.

WHAT THIS FILE IS NOT

It is not the engine. The engine is `astral-kernel`, a separate package named in
`requirements.txt`, which the platform installs on the DevKit — "Packages listed in
requirements.txt are installed for devkit_functions.py on the OpenHome DevKit". That
package is compiled and is not MIT; this file is, like everything else in this
repository, and there is nothing in it worth hiding.

The seam between the two is one function and one contract:

    astral_kernel.answer(text, now=None) -> str | None

A string in. A spoken answer out, or None. None means the engine has no exact answer for
this turn and the agent should take it — which is the whole cooperative bargain of this
ability: it answers what it can answer exactly, instantly, on the device, and it is
silent about everything else.

WHERE AN ANSWER COMES FROM, IN ORDER

  1. the local hub, if this device has one installed — the same engine plus everything
     on the card: the dictionary, the books, the maths kernel, the owner's own shelves
  2. the astral-kernel package
  3. neither — and then it SAYS SO. A device that cannot answer must never be a device
     that quietly says nothing: that is indistinguishable from a broken one.

    python3 devkit_functions.py respond what is twenty percent of eighty
    python3 devkit_functions.py health
"""
import json
import os
import shutil
import subprocess
import sys

# The account that owns the hub. The node server runs this file as `sudo python3 …`, so
# HOME is /root here — measured on the device, not assumed — and every path below is
# written out in full rather than expanded from a "~" that means the wrong thing.
DEVICE_HOME = os.environ.get("ASTRAL_HOME") or "/home/openhome"
HUB = os.path.join(DEVICE_HOME, "astral-voice/hub-v2")
HUB_USER = "openhome"
HUB_PYTHON = os.path.join(DEVICE_HOME, "astral-voice/kws-venv/bin/python3")
BRIDGE = os.path.join(HUB, "ability_bridge.py")
CONTEXT = "/tmp/astral_ctx.json"


# ── the one line of JSON this file exists to print ───────────────────────────────────
def _emit_success(spoken, data=None):
    print(json.dumps({"success": True, "spoken_response": spoken,
                      "data": data or {}, "error": None}))


def _emit_error(code, message):
    print(json.dumps({"success": False, "spoken_response": "", "data": {},
                      "error": {"code": code, "message": message}}))


def _emit_none():
    """No exact answer. An empty spoken_response tells main.py to defer to the agent."""
    print(json.dumps({"success": True, "spoken_response": "", "data": {}, "error": None}))


# ── where answers come from ──────────────────────────────────────────────────────────
def kernel():
    """The Astral engine, if the package is installed here."""
    try:
        import astral_kernel
    except ImportError:
        return None
    return astral_kernel


def hub(*args, timeout=10):
    """Ask the local hub, if this device has one. Returns its dict, or None.

    Crosses back to the account that owns the hub. This file runs as root, and as root
    every path the hub resolves from a home directory lands in /root, where none of its
    data is — measured on the device: the same questions answer as the owner and answer
    nothing as root.
    """
    if not os.path.exists(BRIDGE):
        return None
    python = HUB_PYTHON if os.path.exists(HUB_PYTHON) else "python3"
    cmd = ["sudo", "-n", "-u", HUB_USER, "-H", python, BRIDGE] + [str(a) for a in args]
    if os.geteuid() != 0:
        cmd = cmd[5:]                        # already that user: no sudo needed
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = json.loads((r.stdout or "").strip().splitlines()[-1])
        return out if isinstance(out, dict) and out.get("ok") else None
    except subprocess.TimeoutExpired:
        # Slow is not the same as impossible, and the caller must be able to tell them
        # apart: a cold mathematics kernel is tens of seconds in a fresh process.
        return {"ok": True, "kind": "timeout"}
    except Exception:                        # noqa: BLE001 — the caller is a voice
        return None


def why_nothing_works():
    """The sentence to say when neither the hub nor the kernel is here.

    Said out loud on purpose. The alternative — printing an empty answer — is silence,
    and silence from this ability means "the agent should take it", which would leave a
    broken install looking exactly like a working one for the rest of its life.
    """
    return ("The Astral engine is not installed on this device. "
            "Install the astral-kernel package, or the local hub, and ask me again.")


# ── the functions the platform calls ─────────────────────────────────────────────────
def respond(*words):
    """A transcript in, an exact answer out — or nothing, and the agent takes the turn."""
    q = " ".join(str(w) for w in words).strip()
    if not q:
        _emit_none()
        return

    # 1. the hub: the same engine plus everything on the card
    out = hub("answer", "--agent", q)
    if out and out.get("kind") == "timeout":
        out = hub("offer", "--agent", q, timeout=8)
    if out and out.get("kind") == "answer" and out.get("say"):
        _emit_success(out["say"], {"query": q, "from": "hub", "class": out.get("class")})
        return
    if out and out.get("kind") == "ask" and out.get("say"):
        _emit_success(out["say"], {"query": q, "from": "hub", "offer": True,
                                   "routes": out.get("routes") or [],
                                   "class": out.get("class")})
        return

    # 2. the kernel package
    engine = kernel()
    if engine is not None:
        said = engine.answer(q)
        if said:
            _emit_success(said, {"query": q, "from": "kernel"})
            return
        commanded = _device_command(q)
        if commanded:
            _emit_success(commanded, {"query": q, "from": "kernel"})
            return
        _emit_none()                         # no exact answer: the agent's turn
        return

    # 3. neither, and it says so rather than going quiet
    if out is None:
        _emit_success(why_nothing_works(), {"query": q, "from": "nothing"})
        return
    _emit_none()


def _device_command(q):
    """Device control: the engine understands it, this file publishes it.

    The split is deliberate. Understanding "dim the bedroom light to thirty" is engine
    work; putting a byte on an MQTT topic is device work, and device work belongs in the
    file that runs on the device.
    """
    engine = kernel()
    if engine is None or not hasattr(engine, "command"):
        return None
    cmd = engine.command(q, _last_device())
    if not cmd or not cmd.get("topic"):
        return None
    _remember_device(cmd.get("device"))
    ok = _publish(cmd["topic"], cmd.get("payload", ""))
    if ok is None:
        return "MQTT isn't set up on this device yet."
    return cmd.get("spoken") if ok else "I couldn't reach the {}.".format(cmd.get("device"))


def _last_device():
    try:
        with open(CONTEXT) as f:
            return json.load(f).get("device")
    except Exception:                        # noqa: BLE001
        return None


def _remember_device(device):
    if not device:
        return
    try:
        with open(CONTEXT, "w") as f:
            json.dump({"device": device}, f)
    except OSError:
        pass


def _publish(topic, payload):
    """True sent, False failed, None no broker tools installed."""
    try:
        r = subprocess.run(["mosquitto_pub", "-t", topic, "-m", str(payload)],
                           capture_output=True, timeout=4)
        return r.returncode == 0
    except FileNotFoundError:
        return None
    except Exception:                        # noqa: BLE001
        return False


def device_control(action="", device="", *_):
    said = _device_command("turn {} the {}".format(action, device)) if device else None
    if said:
        _emit_success(said, {"action": action, "device": device})
    else:
        _emit_error("device_failed", "Could not command the device.")


def due_alerts(*_):
    """Timers and reminders that have come due, for the background daemon to speak."""
    out = hub("alerts")
    if out is None:
        _emit_success("", {"count": 0, "hub": False})
        return
    _emit_success(out.get("say") or "", {"count": out.get("count", 0), "hub": True})


def route_answer(route="", *words):
    """Send a question where the user just said to send it, and say what came back.

    A named cloud provider is not a place this device sends anything: on the OpenHome
    path the agent IS that route, so choosing it means this ability stays quiet and the
    agent takes the turn. main.py handles that; if it ever reaches here it is answered
    honestly rather than pretended at.
    """
    q = " ".join(str(w) for w in words).strip()
    if not route or not q:
        _emit_error("no_route", "A route and a question are both required.")
        return
    if route.startswith("cloud"):
        _emit_none()
        return
    out = hub("route", route, q, timeout=25)
    if out is None:
        _emit_error("no_hub", "This device has no local hub to route through.")
        return
    if out.get("kind") == "answer" and out.get("say"):
        _emit_success(out["say"], {"query": q, "route": route})
        return
    where = "the Mac" if route == "mac" else "your {}".format(route)
    _emit_success("I couldn't reach {} right now.".format(where),
                  {"query": q, "route": route, "unreachable": True})


# ── this device, about itself ────────────────────────────────────────────────────────
def get_temperature(*_):
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            c = int(f.read().strip()) / 1000
        _emit_success("The DevKit is at {:.0f} degrees Celsius.".format(c),
                      {"celsius": round(c, 1)})
    except Exception as e:                   # noqa: BLE001
        _emit_error("temp_unavailable", str(e))


def get_uptime(*_):
    try:
        with open("/proc/uptime") as f:
            s = float(f.read().split()[0])
        h, m = int(s // 3600), int((s % 3600) // 60)
        _emit_success("Up {} hours and {} minutes.".format(h, m) if h
                      else "Up {} minutes.".format(m), {"seconds": int(s)})
    except Exception as e:                   # noqa: BLE001
        _emit_error("uptime_unavailable", str(e))


def get_disk(*_):
    try:
        total, used, free = shutil.disk_usage("/")
        _emit_success("Disk is {} percent used, with {} gigabytes free.".format(
            round(used / total * 100), free // 10**9),
            {"used_percent": round(used / total * 100), "free_gb": free // 10**9})
    except Exception as e:                   # noqa: BLE001
        _emit_error("disk_unavailable", str(e))


def get_memory(*_):
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, v = line.partition(":")
                if k in ("MemTotal", "MemAvailable"):
                    info[k] = int(v.split()[0])
        used = round((1 - info["MemAvailable"] / info["MemTotal"]) * 100)
        _emit_success("Memory is {} percent used.".format(used), {"used_percent": used})
    except Exception as e:                   # noqa: BLE001
        _emit_error("memory_unavailable", str(e))


def health(*_):
    """What this ability can reach, for anybody wondering why it is quiet."""
    engine = kernel()
    have_hub = os.path.exists(BRIDGE)
    parts = ["kernel " + engine.__version__ if engine else "no kernel package",
             "local hub installed" if have_hub else "no local hub"]
    _emit_success("Astral: " + ", ".join(parts) + ".",
                  {"kernel": bool(engine), "hub": have_hub,
                   "version": getattr(engine, "__version__", None)})


FUNCTION_REGISTRY = {
    "respond": respond,
    "device_control": device_control,
    "due_alerts": due_alerts,
    "route_answer": route_answer,
    "get_temperature": get_temperature,
    "get_uptime": get_uptime,
    "get_disk": get_disk,
    "get_memory": get_memory,
    "health": health,
}


def main():
    if len(sys.argv) < 2:
        _emit_error("no_function", "No function name given.")
        return
    name, args = sys.argv[1], sys.argv[2:]
    func = FUNCTION_REGISTRY.get(name)
    if func is None:
        respond(name, *args)                 # anything unrecognised is a question
        return
    try:
        func(*args)
    except TypeError:
        respond(*args)
    except Exception as e:                   # noqa: BLE001 — never a traceback into a voice
        _emit_error("unexpected", str(e))


if __name__ == "__main__":
    main()
