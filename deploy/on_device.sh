#!/bin/bash
# What happens ON the DevKit after a sync. Run there, never here.
#
# This used to be a single-quoted string inside install_v2.sh, which meant every `$(...)`
# and `~` in it was one quoting mistake away from being evaluated on the Mac instead —
# and once was: the Mac tried to run the device's Python and the install reported a
# missing profile it had never looked for. A file has one meaning in one place.
set -e
cd ~/astral-voice/hub-v2
PY=~/astral-voice/kws-venv/bin/python3
if [ -f data/lan.token ]; then chmod 600 data/lan.token; fi

$PY sounds.py make >/dev/null

# Books and decks live on the card where they can be dropped in, not inside the hub.
mkdir -p ~/astral-voice/books ~/astral-voice/decks
for b in data/books/*.txt data/books/*.md; do [ -e "$b" ] && cp -n "$b" ~/astral-voice/books/ || true; done
for d in data/decks/*.txt; do [ -e "$d" ] && cp -n "$d" ~/astral-voice/decks/ || true; done
$PY books.py index >/dev/null

# The library: the owner's own shelves on the card. The shelves are made here so there is
# somewhere obvious to drop things, and the starter glossary is copied in with cp -n so a
# deploy can never overwrite what the owner has put there. Indexing is incremental: only
# what is new or changed is read.
for shelf in reference docs code data; do mkdir -p ~/astral-voice/library/$shelf; done
for f in data/library/reference/*.tsv data/library/reference/*.md; do
  [ -e "$f" ] && cp -n "$f" ~/astral-voice/library/reference/ || true
done
# The documentation for the Python that is actually on this device, written from its own
# docstrings. No network, about a second, and it makes "in Python, how do I read a file"
# answerable on a device that has never been online. Only when it is not already there.
[ -d ~/astral-voice/library/docs/python ] || $PY -c 'import library; print(library.generate_python_docs())' >/dev/null 2>&1 || true
$PY library.py index

# Refresh the ability OpenHome itself routes to. Their path — their wake word, their
# speech-to-text, their hotword match — dispatches devkit_functions.py through the node
# server, and that copy is a HAND-PLACED file: nothing here syncs it, so it sat at the
# 17 August build while the engine moved on. It was still answering "solve 2x + 3 = 11
# for x" with "3 times 11 is 33" three weeks after that was fixed everywhere else.
# Local config.json and README.md are legacy manual metadata: native platform sync
# only installs the shim and requirements. Account routing is managed by OpenHome.
# Preserve those extra files; refresh both active execution inputs together.
# The kernel: built here, installed into the interpreter the PLATFORM uses. That is
# system python3 running as root, not this venv — the node server runs the ability as
# `sudo python3 devkit_functions.py`, and a kernel installed anywhere else is a kernel
# the ability cannot see. Measured: with it in the venv only, `health` reported "no
# kernel package" while the wheel sat two directories away.
# This helper validates a build-input fingerprint and the wheel contents, installs the
# same artifact into both interpreters, then verifies the installed bytes. Any build,
# pip or verification failure exits nonzero; set -e stops the deploy before restart.
$PY install_kernel.py

# The microphone level is OpenHome's: their node server sets it at boot from MIC_SENSITIVITY
# in ~/.env, and their app has no slider for it. Their default, 30, was measured deaf for the
# wake ("open brain" at peak 112). The value the wake needs is written ONCE into their
# configuration, only while it still holds their default, so a number they or the owner
# choose later is never overwritten; the loop itself never touches the mixer. The speaker is
# the app's slider (SPEAKER_VOLUME), and nothing here writes it.
ENVF=~/.env
if [ -f "$ENVF" ]; then
  MICNOW=$(grep '^MIC_SENSITIVITY=' "$ENVF" | tail -1 | cut -d= -f2)
  case "${MICNOW:-none}" in
    none) echo "MIC_SENSITIVITY=160" >> "$ENVF"; echo "mic:        MIC_SENSITIVITY=160 added to OpenHome's ~/.env (their boot sets it)";;
    30|30.0|30.00) sed -i 's/^MIC_SENSITIVITY=.*/MIC_SENSITIVITY=160/' "$ENVF"; echo "mic:        MIC_SENSITIVITY 30 -> 160 in OpenHome's ~/.env (their boot sets it)";;
    *) echo "mic:        MIC_SENSITIVITY=$MICNOW in OpenHome's ~/.env, left as chosen";;
  esac
fi
CAPS=~/openhome_devkit/local_capabilities
SHIPPED=~/astral-voice/hub-v2/shipped
# Check the complete input before changing either installed file. A partial sync
# must fail before it can mix a new shim with old dependency metadata.
for f in devkit_functions.py requirements.txt; do
  [ -s "$SHIPPED/$f" ] || { echo "ability: missing or empty $SHIPPED/$f" >&2; exit 1; }
done
# Account registration names can differ from the public package name. This owner
# list survives hub syncs and contains one verified alphanumeric name per line.
# Account sync installs the named folder; an upgrade must refresh that folder too.
REGISTRATIONS=~/astral-voice/state/openhome-capability-names.txt
# Legacy folders are refreshed only while they still exist. Naming one here
# unconditionally recreated it on every deploy long after its registration was
# deleted, leaving a shim installed for an ability the account no longer has.
TARGETS=()
for legacy in astral-daemon astral; do
  if [ -d "$CAPS/$legacy" ]; then TARGETS+=("$legacy"); fi
done
[ ! -L "$CAPS" ] || { echo "ability: capability root is a symlink" >&2; exit 1; }
[ ! -L "$REGISTRATIONS" ] || { echo "ability: registration list is a symlink" >&2; exit 1; }
if [ -e "$REGISTRATIONS" ]; then
  [ -f "$REGISTRATIONS" ] || { echo "ability: registration list is not a file" >&2; exit 1; }
  while IFS= read -r name || [ -n "$name" ]; do
    [ -n "$name" ] || continue
    [[ "$name" =~ ^[A-Za-z][A-Za-z0-9]*$ ]] || {
      echo "ability: invalid registration name" >&2; exit 1;
    }
    # A repeated name does not need another copy.
    seen=0
    for target in "${TARGETS[@]}"; do [ "$target" != "$name" ] || seen=1; done
    [ "$seen" = 1 ] || TARGETS+=("$name")
  done < "$REGISTRATIONS"
fi
# An empty target list would install nothing and say it succeeded. With legacy
# folders now conditional, that is reachable whenever the registration list is
# missing, so it fails here instead of leaving a device with no shim.
[ "${#TARGETS[@]}" -gt 0 ] || {
  echo "ability: no capability targets; $REGISTRATIONS names none and no legacy folder exists" >&2
  exit 1
}

# Check every target before changing the first. Never follow an alias or entrypoint
# symlink into owner files. Existing config/README/platform metadata stay untouched.
for name in "${TARGETS[@]}"; do
  target="$CAPS/$name"
  if [ -L "$target" ] || { [ -e "$target" ] && [ ! -d "$target" ]; }; then
    echo "ability: invalid target $name" >&2; exit 1
  fi
  for f in devkit_functions.py requirements.txt; do
    [ ! -L "$target/$f" ] || { echo "ability: symlink entrypoint in $name" >&2; exit 1; }
  done
done
for name in "${TARGETS[@]}"; do
  mkdir -p "$CAPS/$name"
  cp "$SHIPPED/devkit_functions.py" "$SHIPPED/requirements.txt" "$CAPS/$name/"
  echo "ability:    shim and requirements refreshed in local_capabilities/$name"
done

mkdir -p ~/astral-voice/state ~/.config/systemd/user
# Native ability calls already arrive as independent processes. Preload the router
# as its owner, then fork a bounded child per request. No microphone or TCP port is
# owned here; an absent socket leaves the existing owner CLI path available.
cat > ~/.config/systemd/user/astral-ability.service <<UNIT
[Unit]
Description=Astral owner bridge for native ability requests

[Service]
WorkingDirectory=%h/astral-voice/hub-v2
Environment=PATH=%h/opt/julia/bin:%h/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=%h/astral-voice/kws-venv/bin/python3 ability_server.py
UMask=0077
Restart=on-failure
RestartSec=3
TimeoutStopSec=5
StandardOutput=append:%h/astral-voice/astral-ability.log
StandardError=append:%h/astral-voice/astral-ability.log

[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/astral-hub.service <<UNIT
[Unit]
Description=Astral local loop (version two): wake, local STT, ranked local answers, local TTS
After=pipewire.service

[Service]
WorkingDirectory=%h/astral-voice/hub-v2
Environment=PATH=%h/opt/julia/bin:%h/.cargo/bin:/usr/local/bin:/usr/bin:/bin
Environment=LD_LIBRARY_PATH=%h/astral-voice/whisper.cpp/build/bin
ExecStart=%h/astral-voice/kws-venv/bin/python3 live_hub.py
Restart=always
RestartSec=3
StandardOutput=append:%h/astral-voice/astral-hub.log
StandardError=append:%h/astral-voice/astral-hub.log

[Install]
WantedBy=default.target
UNIT
# The model, kept in memory, when there is one and a server to run it. Loading 800 MB off
# the card is most of what a rewrite costs — 60 seconds end to end, of which reading and
# writing were barely half. Optional in both directions: no server and the summariser
# still works through a subprocess, slowly and correctly.
MODEL=$(ls -S ~/astral-voice/models/*.gguf 2>/dev/null | tail -1)
if [ -x ~/astral-voice/llama.cpp/build/bin/llama-server ] && [ -n "$MODEL" ]; then
cat > ~/.config/systemd/user/astral-model.service <<UNIT
[Unit]
Description=Astral local model, resident (one load, many answers)

[Service]
ExecStart=%h/astral-voice/llama.cpp/build/bin/llama-server -m $MODEL --host 127.0.0.1 --port 8791 -t 3 -c 2048 --no-webui
Restart=always
RestartSec=10
Nice=5
StandardOutput=append:%h/astral-voice/astral-model.log
StandardError=append:%h/astral-voice/astral-model.log

[Install]
WantedBy=default.target
UNIT
fi

# One kernel for the whole machine. Slate costs 43 seconds to start and milliseconds to
# answer, so the process that owns it must outlive any one question — and the OpenHome
# ability is a fresh process per turn, which is why exact mathematics was being offered
# away to the cloud on a device that can do it. This service owns it; both callers ask
# the socket. Started only when the kernel binary is actually here.
if [ -x ~/slate-trim/slate-kernel-full ] || [ -x ~/slate-trim/slate-kernel ]; then
cat > ~/.config/systemd/user/astral-slate.service <<UNIT
[Unit]
Description=Astral Slate kernel, resident and shared (one warm kernel, one socket)

[Service]
WorkingDirectory=%h/astral-voice/hub-v2
Environment=PATH=%h/opt/julia/bin:%h/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=%h/astral-voice/kws-venv/bin/python3 slate_server.py
Restart=always
RestartSec=5
StandardOutput=append:%h/astral-voice/astral-slate.log
StandardError=append:%h/astral-voice/astral-slate.log

[Install]
WantedBy=default.target
UNIT
fi

systemctl --user daemon-reload

# Measure this machine. Without a profile every class above the table layer is refused,
# and the table layer answers alone — which is survivable but is not the product. This is
# also the only way the fits table can be true: measured here, or somebody else's numbers.
HOST=$($PY -c 'import costs; print(costs.host_id())')
PROFILE="data/costs/$HOST.json"
# Measure when the machine's answer to "what do I have" has changed, not only when there
# is no profile at all. Copying the decks onto the card and leaving a stale profile in
# place is how the quiz ended up refused on a device that had the decks sitting there.
HAVE_NOW=$($PY -c 'import measure_costs; print(",".join(measure_costs.available_here()))')
HAVE_THEN=$($PY - "$PROFILE" <<'PYEOF' 2>/dev/null || true
import json, sys
try:
    print(",".join(json.load(open(sys.argv[1]))["available"]))
except Exception:
    print("")
PYEOF
)
if [ "$HAVE_NOW" != "$HAVE_THEN" ]; then
  echo "what this machine has changed since the last measurement: measuring, about a minute"
  echo "  was: ${HAVE_THEN:-nothing measured}"
  echo "  now: $HAVE_NOW"
  $PY measure_costs.py --runs 40
fi

echo "host:       $HOST"
if [ -s "$PROFILE" ]; then
  $PY - "$PROFILE" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"profile:    {len(d['commands'])} classes measured at {d['measured_at'][:19]}")
print(f"available:  {', '.join(d['available'])}")
PYEOF
else
  echo "profile:    MISSING — the table layer answers, everything above it stays silent"
fi
if [ -f ~/.config/systemd/user/astral-slate.service ]; then
  systemctl --user enable astral-slate.service
  systemctl --user restart astral-slate.service
fi
if [ -f ~/.config/systemd/user/astral-model.service ]; then
  systemctl --user enable astral-model.service
  systemctl --user restart astral-model.service
fi
# Restart even when voice capture is stopped: this service preloads the deployed
# routing code and must never keep the preceding deployment in memory.
systemctl --user enable astral-ability.service
systemctl --user restart astral-ability.service
$PY ability_server.py --check
echo "kiosk:      $(systemctl --user is-active openhome-dashboard.service || true)"
echo "model:      $(systemctl --user is-active astral-model.service 2>/dev/null || echo absent)$([ -n "$(ls ~/astral-voice/models/*.gguf 2>/dev/null)" ] && echo " ($(basename $(ls -S ~/astral-voice/models/*.gguf | tail -1)))")"
echo "slate:      $(systemctl --user is-active astral-slate.service 2>/dev/null || echo absent)"
echo "astral-hub: $(systemctl --user is-active astral-hub.service || true)"
echo "oracle:     $(ls ~/slate/ada/slate_exact/lib/libslate_exact_c.so 2>/dev/null || echo absent)"
echo "wake:       $($PY -c 'import wake_phrase as w; print(", ".join(w.WAKE_PHRASES) + " (phrase recogniser)" if w.available() else "hey mycroft (no phrase model on this machine)")')"
echo "sounds:     $(ls ~/astral-voice/sounds 2>/dev/null | wc -l | tr -d ' ') files"
echo "kernel:     $(sudo python3 -c 'import astral_kernel; print("astral-kernel " + astral_kernel.__version__ + " (compiled, system python)")' 2>/dev/null || echo 'not installed — the ability will use the hub, or say it has no engine')"
echo "library:    $($PY -c 'import library; s=library.sources(); print(f"{len(s)} sources: " + ", ".join(sorted({x[0] for x in s})) if s else "empty — drop files in ~/astral-voice/library")')"
echo "python:     $($PY -V)"
