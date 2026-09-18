#!/bin/bash
# Speak to the device and read back what it did — the check no suite can make.
#
# Seven defects were found this way on 2026-09-06, every one of them after a full run of
# 5,000+ checks passed on both machines. What the suites cannot see is the device deciding
# it was not being spoken to: "and another one" after its own joke, discarded as not a
# request; "who are you" acknowledged instead of answered because the floor was open;
# "cancel the timer" heard as "canceled" and matched by nothing. None of those is a wrong
# answer. They are turns that never became questions.
#
#   ssh <device> 'bash -s' < deploy/acoustic-sweep.sh <<'TURNS'
#   open brain tell me a joke
#   open brain and another one
#   TURNS
#
# It raises the speaker to hear itself and PUTS IT BACK — the listening level belongs to
# whoever lives with the device and is not ours to leave changed. Follow-ups belong next
# to the turn they follow: adjacency is what produced "what do the books say about tell
# me a joke".
set -u
_WAS=$(pactl get-sink-volume @DEFAULT_SINK@ | head -1 | grep -o '[0-9]*%' | head -1)
_restore() { pactl set-sink-volume @DEFAULT_SINK@ "$_WAS"; echo "[speaker back to $_WAS]"; }
trap _restore EXIT INT TERM
# Wait out anything the device is already saying — a deploy restarts it, and its greeting
# will talk over the first turn and cost you a measurement that looks like a defect.
for _i in $(seq 1 90); do pgrep -x mpv >/dev/null 2>&1 || break; sleep 1; done
sleep 5
pactl set-sink-volume @DEFAULT_SINK@ 70%
#!/bin/bash
# A conversation spoken into the device's own microphone, in the order a person says it.
# Follow-ups sit next to the turn before them on purpose: that adjacency is what produced
# "what do the books say about tell me a joke".
# The device's own paths: this runs there, as the user the hub runs as.
A=${ASTRAL_HOME:-$HOME}/astral-voice
L=$A/astral-hub.log
# Where each spoken turn is synthesised: ASTRAL_SWEEP_DIR, else a fresh temporary directory.
CK=${ASTRAL_SWEEP_DIR:-$(mktemp -d)}
mkdir -p "$CK"
say_turn() {
  local text="$1"
  for i in $(seq 1 90); do pgrep -x mpv >/dev/null 2>&1 || break; sleep 1; done
  sleep 2
  local n0=$(wc -l < $L)
  cd "$A/hub-v2"
  UTT="$text" "$A/kws-venv/bin/python3" -c "
import sys,os; sys.path.insert(0,'.')
import live_hub, subprocess
subprocess.run([live_hub.PIPER,'--model',live_hub.voice_now(),'--output_file','$CK/s.wav'], input=os.environ['UTT'], capture_output=True, text=True)
" >/dev/null 2>&1
  mpv --no-terminal --no-video --really-quiet --volume=100 $CK/s.wav >/dev/null 2>&1
  local end=$(echo "$(date +%s.%N) + 80" | bc)
  while [ "$(echo "$(date +%s.%N) < $end" | bc)" = "1" ]; do
    tail -n +$((n0+1)) $L | grep -aqE '^\[said\]|^\[ignored|^\[floor|heard nothing' && break
    sleep 0.1
  done
  sleep 0.5
  local heard=$(tail -n +$((n0+1)) $L | grep -a '^\[heard\]' | head -1 | cut -c9-72)
  local said=$(tail -n +$((n0+1)) $L | grep -a '^\[said\]' | head -1 | cut -c8-150)
  local cls=$(tail -n +$((n0+1)) $L | grep -a '^\[route\]' | head -1 | sed 's/.*class=\([a-z_]*\).*/\1/')
  printf 'SAID   %s\nHEARD  %s\nCLASS  %s\nANSWER %s\n\n' "$text" "${heard:-—}" "${cls:-—}" "${said:-— NOTHING SAID —}"
}
while IFS= read -r t; do [ -n "$t" ] && say_turn "$t"; done
