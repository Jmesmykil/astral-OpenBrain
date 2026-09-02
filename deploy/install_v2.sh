#!/bin/zsh
# Put the version-two loop on the DevKit and wire it as the user service.
#
#   deploy/install_v2.sh [openhome@192.168.1.23]
#
# Copies the hub (engine, router, kernels, sounds, data) to ~/astral-voice/hub-v2 on the
# device, makes the chime files, points the LAN route at this Mac, installs the
# astral-hub user service running live_hub.py in the device's kws-venv, and prints the
# state. Idempotent. Does not start the service unless --start is given, because the
# OpenHome kiosk and this loop must not both own the microphone.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=${1:-openhome@192.168.1.23}
START=0; [[ "$2" == "--start" ]] && START=1
export SSH_AUTH_SOCK=
SSHC=(ssh -i "$HOME/.ssh/id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8)
MAC_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)

# the LAN route: the Pi asks THIS Mac; the token is shared by copying the file
python3 - "$HERE" "$MAC_IP" <<'PY'
import json, pathlib, sys
hub = pathlib.Path(sys.argv[1]) / "hub"
sys.path.insert(0, str(hub)); import lan
lan.token()
routes = hub / "data/routes.json"
cur = json.loads(routes.read_text()) if routes.exists() else {}
cur["mac"] = {"host": sys.argv[2], "port": lan.PORT}
cur.setdefault("phone", {"host": None})
routes.write_text(json.dumps(cur, indent=2) + "\n")
print("routes:", cur)
PY

rsync -rlt --chmod=ugo=rwX -e "${SSHC[*]}" \
  --include='*.py' --include='kernels/' --include='kernels/*.py' \
  --include='tests/' --include='tests/*.py' --include='wake/' --include='wake/*.npz' \
  --include='data/' --include='data/*.json' \
  --include='data/lan.token' --include='data/sounds/' \
  `# data/costs is deliberately absent: a host's cost profile is measured ON that host,` \
  `# and copying this machine's numbers over the device's would make the fits table a fiction.` \
  --include='data/sounds/*.wav' --include='data/books/' --include='data/books/*.txt' --include='data/books/*.md' \
  --include='data/state/' --exclude='*' "$HERE/hub/" "$T:~/astral-voice/hub-v2/"

"${SSHC[@]}" "$T" 'set -e
cd ~/astral-voice/hub-v2
python3 sounds.py make >/dev/null
# Books live on the card where they can be dropped in, not inside the hub. The sample
# ships so the class has something to read before the first real book arrives.
mkdir -p ~/astral-voice/books
for b in data/books/*.txt data/books/*.md; do [ -e "$b" ] && cp -n "$b" ~/astral-voice/books/ || true; done
python3 books.py index >/dev/null
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
echo "kiosk:      $(systemctl --user is-active openhome-dashboard.service || true)"
echo "astral-hub: $(systemctl --user is-active astral-hub.service || true)"
echo "oracle:     $(ls ~/slate/ada/slate_exact/lib/libslate_exact_c.so 2>/dev/null || echo absent)"
echo "sounds:     $(ls ~/astral-voice/sounds 2>/dev/null | wc -l | tr -d " ") files"
echo "python:     $(~/astral-voice/kws-venv/bin/python3 -V)"'

if (( START )); then
  "${SSHC[@]}" "$T" 'systemctl --user stop openhome-dashboard.service 2>/dev/null || true; systemctl --user restart astral-hub.service; sleep 3; systemctl --user is-active astral-hub.service; tail -5 ~/astral-voice/astral-hub.log'
else
  echo "installed, not started. Start with: deploy/install_v2.sh $T --start   (stops the OpenHome kiosk first: one mic, one owner)"
fi
