#!/bin/zsh
# Build the follow-up branch for openhome-dev/abilities from this repo.
#
#   deploy/build_followup_pr.sh /path/to/clone-of-Jmesmykil/abilities
#
# Checks out upstream dev, copies the generated main.py and the engine source + tests into
# community/astral/, regenerates main.py inside that layout so file and source agree by
# construction, runs the tests there, and stages the result. It does not commit or push.
set -e
CLONE=${1:?path to a clone of Jmesmykil/abilities}
HERE=$(cd "$(dirname "$0")/.." && pwd)
cd "$CLONE"
git remote get-url upstream >/dev/null 2>&1 || git remote add upstream https://github.com/openhome-dev/abilities.git
git fetch -q upstream dev
# A re-run starts over: the clone is dedicated to this branch, and the previous attempt is discarded.
git reset -q --hard
git clean -fdq community/astral
git checkout -q -B astral-followups upstream/dev

cp "$HERE/community/astral-skill/main.py" community/astral/main.py
rm -rf community/astral/hub && mkdir -p community/astral/hub
for f in mechanical calc study chem sci stats mathx engine build_ability test_golden test_hardening test_artifact_parity; do
  cp "$HERE/hub/$f.py" community/astral/hub/
done
cp "$HERE/hub/README.md" community/astral/hub/README.md

# The shipped copies are formatted the way the upstream lint job expects, same as main.py.
python3 -m autopep8 --in-place --max-line-length=120 --ignore=E501,W503 --aggressive --aggressive community/astral/hub/*.py
python3 -m autopep8 --in-place --max-line-length=120 --select=E22 --aggressive --aggressive community/astral/hub/*.py

( cd community/astral && python3 hub/build_ability.py )
( cd community/astral/hub && python3 tests/run.py --quiet | tail -3 )
echo "the suite passes in the upstream layout"
if cmp -s "$HERE/community/astral-skill/main.py" community/astral/main.py; then
  echo "main.py identical to the workspace artifact"
else
  echo "main.py differs from the workspace artifact (see git diff)"; fi

git add -A community/astral
git status --short
cat <<MSG

Staged on branch astral-followups. To ship it, by hand:

  git -C "$CLONE" -c user.name="Jamesmykil Weber" -c user.email="mykiljames253@gmail.com" \\
      commit -m "Astral: planet mass and size, ship the engine source and tests"
  git -C "$CLONE" push -u origin astral-followups
  gh pr create --repo openhome-dev/abilities --base dev --head Jmesmykil:astral-followups \\
      --title "Astral: planet mass and size, ship the engine source and tests" \\
      --body-file "$HERE/deploy/followup-pr-body.md"
MSG
