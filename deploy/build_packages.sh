#!/bin/sh
# Assemble the two deployable ability archives from the single copies of their sources.
#
# The platform uploads one self-contained ZIP per ability, and both abilities call the
# same shim on the device. Keeping a second copy of devkit_functions.py in the tree to
# satisfy that would be three files free to drift apart with nothing checking they agree,
# which is the problem hub/build_ability.py already exists to prevent. So the shim and the
# pinned requirements are copied at build time and are never stored twice.
#
#   sh deploy/build_packages.sh [outdir]        # default: build/
#
# Your own names go in an untracked config.local.json beside each config.json. Ability
# names are unique across every OpenHome account, not just yours, so the shipped files
# carry CHANGE-ME placeholders: deploying a taken name fails with "already exists in other
# users account", and that message names the wrong culprit. Any key the local file sets
# replaces the shipped value in the built package; the shipped file is never edited.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
OUT=${1:-$ROOT/build}
SRC=$ROOT/community/astral

for f in main.py devkit_functions.py requirements.txt config.json README.md BOUNDARY.md background.py; do
  [ -s "$SRC/$f" ] || { echo "missing or empty $SRC/$f" >&2; exit 1; }
done
for f in config.json README.md; do
  [ -s "$ROOT/community/astral-daemon/$f" ] || { echo "missing $ROOT/community/astral-daemon/$f" >&2; exit 1; }
done

# config <source dir> <package dir>: the shipped config.json, with config.local.json over it.
config() {
  if [ -f "$1/config.local.json" ]; then
    python3 - "$1/config.json" "$1/config.local.json" "$2/config.json" <<'PY'
import json, sys
shipped, local, out = sys.argv[1:4]
with open(shipped) as f:
    config = json.load(f)
with open(local) as f:
    override = json.load(f)
unknown = sorted(set(override) - set(config))
if unknown:
    sys.exit(local + " sets keys config.json does not have: " + ", ".join(unknown))
config.update(override)
with open(out, "w") as f:
    f.write(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
PY
  else
    cp "$1/config.json" "$2/config.json"
  fi
}

rm -rf "$OUT"
mkdir -p "$OUT/foreground" "$OUT/daemon"

# The foreground ability: the platform matches a trigger word and hands over the turn.
cp "$SRC/__init__.py" "$SRC/main.py" "$SRC/devkit_functions.py" "$SRC/requirements.txt" \
   "$SRC/README.md" "$SRC/BOUNDARY.md" "$OUT/foreground/"
config "$SRC" "$OUT/foreground"

# The daemon: same engine, no trigger word, so background.py IS its main.py. It carries
# its own shim copy because the platform package must stand alone, and it is the same
# bytes as the foreground one for as long as this script is what builds them.
cp "$SRC/background.py" "$OUT/daemon/main.py"
cp "$SRC/__init__.py" "$SRC/devkit_functions.py" "$SRC/requirements.txt" "$OUT/daemon/"
cp "$ROOT/community/astral-daemon/README.md" "$OUT/daemon/"
config "$ROOT/community/astral-daemon" "$OUT/daemon"

cmp -s "$OUT/foreground/devkit_functions.py" "$OUT/daemon/devkit_functions.py" \
  || { echo "the two shims differ, which this script exists to make impossible" >&2; exit 1; }

echo "built:"
for d in foreground daemon; do
  echo "  $OUT/$d  ($(ls "$OUT/$d" | wc -l | tr -d ' ') files)"
done
echo
echo "validate:  OPENHOME_NO_UPDATE=1 openhome validate $OUT/foreground --json"
echo "           OPENHOME_NO_UPDATE=1 openhome validate $OUT/daemon --json"
echo
echo "The daemon reports 'resume_normal_flow() must be called'. That rule is correct for a"
echo "foreground ability, which holds the turn and must give it back, and wrong for a daemon,"
echo "which never takes it. See community/astral-daemon/README.md."
echo
for d in foreground daemon; do
  if grep -q '"CHANGE-ME' "$OUT/$d/config.json"; then
    echo "$d still has the CHANGE-ME placeholder name: put your own unique_name and name in"
    echo "  config.local.json beside its source config.json, then build again."
  fi
done
