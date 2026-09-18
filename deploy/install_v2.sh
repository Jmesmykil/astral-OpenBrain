#!/bin/zsh
# Put the version-two loop on the DevKit and wire it as the user service.
#
#   deploy/install_v2.sh [user@host]        (or set ASTRAL_DEVKIT)
#
# Copies the hub (engine, router, kernels, sounds, data) to ~/astral-voice/hub-v2 on the
# device, makes the chime files, points the LAN route at this Mac, installs the
# astral-hub user service running live_hub.py in the device's kws-venv, and prints the
# state. A paired turn-router browser stays running as the selected agent output;
# the hub owns microphone admission. Older unpaired releases retain kiosk exclusion.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=${1:-${ASTRAL_DEVKIT:?pass the DevKit as user@host, or set ASTRAL_DEVKIT}}
START=0; [[ "$2" == "--start" ]] && START=1
export SSH_AUTH_SOCK=
SSHC=(ssh -i "$HOME/.ssh/id_ed25519" -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8)
# Fail before any local or device write if the required browser pair is incompatible.
PAIR=0
if [[ -f "$HERE/hub/voice_turns.py" ]]; then
  PAIR=1
  CONTRACT=$(python3 -c 'import base64,pathlib,sys; print(base64.b64encode(pathlib.Path(sys.argv[1]).read_bytes()).decode())' "$HERE/deploy/turn-router/protocol.json")
  "${SSHC[@]}" "$T" python3 - "$CONTRACT" < "$HERE/deploy/turn-router/check_installed.py"
fi
MAC_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)

# the LAN route: the Pi asks THIS Mac; the token is shared by copying the file
python3 - "$HERE" "$MAC_IP" <<'PY'
import json, pathlib, sys
hub = pathlib.Path(sys.argv[1]) / "hub"
sys.path.insert(0, str(hub)); import lan
lan.token()
# The deployer's address is written only on the device (below), never into the repository:
# what ships must work in anybody's house. Machines that dial in to the gateway need no
# address at all; this fixed LAN route is the older way to reach a computer.
print("Mac route (device only):", {"host": sys.argv[2], "port": lan.PORT})
PY

# --delete, because a file removed here must be removed there. Without it the device
# kept an obsolete test_golden.py alive, which is the only reason a broken import in
# measure_costs.py went unnoticed for a day.
rsync -rlt --delete --chmod=u=rwX,go=rX -e "${SSHC[*]}" \
  --exclude='data/routes.json' \
  --include='*.py' --include='kernels/' --include='kernels/*.py' --include='fabric/' --include='fabric/*.py' \
  --include='tests/' --include='tests/*.py' --include='tests/fixtures/' --include='tests/fixtures/*.txt' --include='wake/' --include='wake/*.npz' \
  --include='data/' --include='data/*.json' \
  --include='data/lan.token' --include='data/sounds/' \
  `# data/costs is deliberately absent: a host's cost profile is measured ON that host,` \
  `# and copying this machine's numbers over the device's would make the fits table a fiction.` \
  --include='data/sounds/*.wav' \
  `# the shipped astral pack, every file: the sounds, their licences, and the MASTERED marker` \
  --include='data/sounds/astral/' --include='data/sounds/astral/*' --include='data/books/' --include='data/books/*.txt' --include='data/books/*.md' \
  --include='data/decks/' --include='data/decks/*.txt' \
  `# one file per field, and any the owner adds beside them` \
  --include='data/facts/' --include='data/facts/*.json' \
  `# the starter shelf: what ships is the example, what the card holds is the owner's` \
  --include='data/library/' --include='data/library/reference/' \
  --include='data/library/reference/*.tsv' --include='data/library/reference/*.md' \
  --include='data/state/' --exclude='*' "$HERE/hub/" "$T:~/astral-voice/hub-v2/"
# Device choices stay on the device. A deployment updates only this Mac's address.
"${SSHC[@]}" "$T" python3 - "$MAC_IP" <<'PYROUTES'
import json, os, pathlib, sys
path = pathlib.Path.home() / "astral-voice/hub-v2/data/routes.json"
cur = json.loads(path.read_text()) if path.exists() else {}
cur["mac"] = {"host": sys.argv[1], "port": 8790}
cur.setdefault("phone", {"host": None})
cur.setdefault("cloud", {"enabled": False})
tmp = path.with_suffix(".deploy-tmp")
tmp.write_text(json.dumps(cur, indent=2) + "\n")
if path.exists():
    tmp.chmod(path.stat().st_mode & 0o777)
os.replace(tmp, path)
print("Device routing choices preserved; Mac address refreshed.")
PYROUTES
rsync -lt --chmod=u=rwx,go=rx -e "${SSHC[*]}" "$HERE/deploy/on_device.sh" "$T:~/astral-voice/hub-v2/"
# The documents and the installer travel too, read-only, so the device can audit its own
# claims. Without them the honesty suite skipped on the device and RETURNED, taking the
# wake-phrase checks with it — the machine that actually wakes to those words was the one
# machine never checking that the README names them. Same for the installer: the rules
# that put the sound pack on this card could only be read on the machine that sent it.
"${SSHC[@]}" "$T" 'mkdir -p ~/astral-voice/deploy'
rsync -lt --chmod=u=rw,go=r -e "${SSHC[*]}" "$HERE/README.md" "$HERE/KNOWN-BUGS.md" \
  "$T:~/astral-voice/"
rsync -lt --chmod=u=rw,go=r -e "${SSHC[*]}" "$HERE/deploy/install_v2.sh" \
  "$T:~/astral-voice/deploy/"
# This machine's own cost profile, and only this machine's. The device decides whether to
# offer "ask the Mac" by reading the Mac's measured profile — _offerable() calls
# fits(cls, that_host) — so a stale copy is a stale answer. The device's was four days old
# and predated Slate being visible here, which means the device had spent four days
# certain the Mac could not do maths and never once offered it. The device's OWN profile
# is still never sent: those numbers must be measured where they are used.
MINE="$(cd "$HERE/hub" && python3 -c 'import costs; print(costs.host_id())')"
if [ -f "$HERE/hub/data/costs/$MINE.json" ]; then
  "${SSHC[@]}" "$T" 'mkdir -p ~/astral-voice/hub-v2/data/costs'
  rsync -lt --chmod=u=rw,go=r -e "${SSHC[*]}" "$HERE/hub/data/costs/$MINE.json" \
    "$T:~/astral-voice/hub-v2/data/costs/"
  echo "profile:    sent this machine's own ($MINE) so the device knows what it can defer here"
fi
# The shipped ability travels too: OpenHome's own routing calls this file, and until
# now nothing kept it current on the device.
"${SSHC[@]}" "$T" 'mkdir -p ~/astral-voice/hub-v2/shipped'
rsync -lt --chmod=u=rwX,go=rX -e "${SSHC[*]}" "$HERE/community/astral/devkit_functions.py" \
  "$HERE/community/astral/main.py" "$HERE/community/astral/background.py" \
  "$HERE/community/astral/requirements.txt" \
  "$HERE/community/astral/BOUNDARY.md" \
  "$T:~/astral-voice/hub-v2/shipped/"

# Everything device-side lives in on_device.sh, which was synced with the hub above.
"${SSHC[@]}" "$T" 'bash ~/astral-voice/hub-v2/on_device.sh'

# A deploy onto a RUNNING loop restarts it, whether or not --start was given. Without this,
# every fix made in a day was copied to the card and none of it ran: the service that
# started at 07:59 was still executing the 07:59 code at 10:30, twenty modules newer on
# disk, while the suite reported green and the owner kept catching bugs already "fixed".
if "${SSHC[@]}" "$T" 'systemctl --user is-active --quiet astral-hub.service'; then
  echo "astral-hub is running: restarting it so the deployed code is the running code"
  START=1
fi
if (( START && ! PAIR )); then
  "${SSHC[@]}" "$T" 'set -e; systemctl --user stop openhome-dashboard.service 2>/dev/null || { if systemctl --user is-active --quiet openhome-dashboard.service; then exit 1; fi; }; systemctl --user restart astral-hub.service; sleep 3; systemctl --user is-active astral-hub.service; tail -5 ~/astral-voice/astral-hub.log'
elif (( START )); then
  "${SSHC[@]}" "$T" 'set -e; systemctl --user is-active --quiet openhome-dashboard.service; systemctl --user restart astral-hub.service; sleep 3; systemctl --user is-active astral-hub.service; tail -5 ~/astral-voice/astral-hub.log'
else
  echo "installed, not started. Start with: deploy/install_v2.sh $T --start"
fi
