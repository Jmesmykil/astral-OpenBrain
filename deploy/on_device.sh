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
$PY library.py index >/dev/null 2>&1 || true

# Refresh the ability OpenHome itself routes to. Their path — their wake word, their
# speech-to-text, their hotword match — dispatches devkit_functions.py through the node
# server, and that copy is a HAND-PLACED file: nothing here syncs it, so it sat at the
# 17 August build while the engine moved on. It was still answering "solve 2x + 3 = 11
# for x" with "3 times 11 is 33" three weeks after that was fixed everywhere else.
# config.json is the platform's and is left alone.
CAPS=~/openhome_devkit/local_capabilities
SHIPPED=~/astral-voice/hub-v2/shipped/devkit_functions.py
if [ -d "$CAPS/astral" ]; then
  cp "$SHIPPED" "$CAPS/astral/" 2>/dev/null || true
  echo "ability:    $(md5sum "$CAPS/astral/devkit_functions.py" | cut -c1-8) refreshed in local_capabilities/astral"
fi

# The background daemon is a SECOND ability upload (one category per ability), so the node
# server resolves its device calls under its own name — it reads
# local_capabilities/<capability_name>/devkit_functions.py and does not care which category
# asked. Nothing syncs a device file for a non-local ability, so the directory is made here
# and given the same engine. Without it the daemon's every call returns
# "devkit_functions.py not found", which it reads as "not mine" and goes quiet for good.
if [ -e "$SHIPPED" ]; then
  mkdir -p "$CAPS/astral-daemon"
  cp "$SHIPPED" "$CAPS/astral-daemon/" 2>/dev/null || true
  echo "daemon:     $(md5sum "$CAPS/astral-daemon/devkit_functions.py" | cut -c1-8) in local_capabilities/astral-daemon"
fi

mkdir -p ~/astral-voice/state ~/.config/systemd/user
cat > ~/.config/systemd/user/astral-hub.service <<UNIT
[Unit]
Description=Astral local loop (version two): wake, local STT, ranked local answers, local TTS
After=pipewire.service

[Service]
WorkingDirectory=%h/astral-voice/hub-v2
Environment=PATH=%h/opt/julia/bin:%h/.cargo/bin:/usr/local/bin:/usr/bin:/bin
Environment=LD_LIBRARY_PATH=%h/astral-voice/whisper.cpp/build/bin
ExecStartPre=/usr/bin/pactl set-source-volume @DEFAULT_SOURCE@ 160%
ExecStart=%h/astral-voice/kws-venv/bin/python3 live_hub.py
Restart=always
RestartSec=3
StandardOutput=append:%h/astral-voice/astral-hub.log
StandardError=append:%h/astral-voice/astral-hub.log

[Install]
WantedBy=default.target
UNIT
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
  $PY measure_costs.py --runs 40 >/dev/null 2>&1 || true
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
  systemctl --user enable astral-slate.service >/dev/null 2>&1 || true
  systemctl --user restart astral-slate.service || true
fi
echo "kiosk:      $(systemctl --user is-active openhome-dashboard.service || true)"
echo "slate:      $(systemctl --user is-active astral-slate.service 2>/dev/null || echo absent)"
echo "astral-hub: $(systemctl --user is-active astral-hub.service || true)"
echo "oracle:     $(ls ~/slate/ada/slate_exact/lib/libslate_exact_c.so 2>/dev/null || echo absent)"
echo "wake:       $($PY -c 'import wake_phrase as w; print(", ".join(w.WAKE_PHRASES) + " (phrase recogniser)" if w.available() else "hey mycroft (no phrase model on this machine)")')"
echo "sounds:     $(ls ~/astral-voice/sounds 2>/dev/null | wc -l | tr -d ' ') files"
echo "library:    $($PY -c 'import library; s=library.sources(); print(f"{len(s)} sources: " + ", ".join(sorted({x[0] for x in s})) if s else "empty — drop files in ~/astral-voice/library")')"
echo "python:     $($PY -V)"
