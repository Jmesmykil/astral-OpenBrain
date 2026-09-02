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
systemctl --user daemon-reload

# Measure this machine. Without a profile every class above the table layer is refused,
# and the table layer answers alone — which is survivable but is not the product. This is
# also the only way the fits table can be true: measured here, or somebody else's numbers.
HOST=$($PY -c 'import costs; print(costs.host_id())')
PROFILE="data/costs/$HOST.json"
if [ ! -s "$PROFILE" ]; then
  echo "no profile for $HOST yet: measuring, about a minute"
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
echo "kiosk:      $(systemctl --user is-active openhome-dashboard.service || true)"
echo "astral-hub: $(systemctl --user is-active astral-hub.service || true)"
echo "oracle:     $(ls ~/slate/ada/slate_exact/lib/libslate_exact_c.so 2>/dev/null || echo absent)"
echo "wake:       $($PY -c 'import wake_openbrain as w; print("hey mycroft + open brain" if w.available() else "hey mycroft only")')"
echo "sounds:     $(ls ~/astral-voice/sounds 2>/dev/null | wc -l | tr -d ' ') files"
echo "python:     $($PY -V)"
