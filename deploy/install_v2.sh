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
# Never turned on by a deploy, and never dropped by one either: the switch is the
# creator's to throw, and a route that quietly vanished would take the offer with it.
cur.setdefault("cloud", {"enabled": False})
routes.write_text(json.dumps(cur, indent=2) + "\n")
print("routes:", cur)
PY

# --delete, because a file removed here must be removed there. Without it the device
# kept an obsolete test_golden.py alive, which is the only reason a broken import in
# measure_costs.py went unnoticed for a day.
rsync -rlt --delete --chmod=ugo=rwX -e "${SSHC[*]}" \
  --include='*.py' --include='kernels/' --include='kernels/*.py' \
  --include='tests/' --include='tests/*.py' --include='wake/' --include='wake/*.npz' \
  --include='data/' --include='data/*.json' \
  --include='data/lan.token' --include='data/sounds/' \
  `# data/costs is deliberately absent: a host's cost profile is measured ON that host,` \
  `# and copying this machine's numbers over the device's would make the fits table a fiction.` \
  --include='data/sounds/*.wav' --include='data/books/' --include='data/books/*.txt' --include='data/books/*.md' \
  --include='data/decks/' --include='data/decks/*.txt' \
  `# the starter shelf: what ships is the example, what the card holds is the owner's` \
  --include='data/library/' --include='data/library/reference/' \
  --include='data/library/reference/*.tsv' --include='data/library/reference/*.md' \
  --include='data/state/' --exclude='*' "$HERE/hub/" "$T:~/astral-voice/hub-v2/"
rsync -lt --chmod=ugo=rwx -e "${SSHC[*]}" "$HERE/deploy/on_device.sh" "$T:~/astral-voice/hub-v2/"
# The shipped ability travels too: OpenHome's own routing calls this file, and until
# now nothing kept it current on the device.
"${SSHC[@]}" "$T" 'mkdir -p ~/astral-voice/hub-v2/shipped'
rsync -lt --chmod=ugo=rwX -e "${SSHC[*]}" "$HERE/community/astral/devkit_functions.py" \
  "$HERE/community/astral/main.py" "$HERE/community/astral/background.py" \
  "$T:~/astral-voice/hub-v2/shipped/"

# Everything device-side lives in on_device.sh, which was synced with the hub above.
"${SSHC[@]}" "$T" 'bash ~/astral-voice/hub-v2/on_device.sh'

if (( START )); then
  "${SSHC[@]}" "$T" 'systemctl --user stop openhome-dashboard.service 2>/dev/null || true; systemctl --user restart astral-hub.service; sleep 3; systemctl --user is-active astral-hub.service; tail -5 ~/astral-voice/astral-hub.log'
else
  echo "installed, not started. Start with: deploy/install_v2.sh $T --start   (stops the OpenHome kiosk first: one mic, one owner)"
fi
