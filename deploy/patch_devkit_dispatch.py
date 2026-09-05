"""Replace only the audited native capability dispatch branch, preserving other actions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

BEFORE_SHA256 = "dc82db687c480e5d03204235695485008ba7127655071cd4eb0b8d36a2de9413"
START = 'else if (data.type === "devkit-capability") {'
END = 'else if (data.type === "devkit-action-mqtt") {'
AFTER = START + '\n        require("./astral_capability.cjs")(ws, data.data);\n      }'


def apply(target, write=False):
    if target.is_symlink():
        raise ValueError("Refusing a symbolic-link platform source")
    before = target.read_bytes()
    source = before.decode()
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("Expected exactly one native dispatch branch")
    start, end = source.index(START), source.index(END)
    old = source[start:end].rstrip()
    if old == AFTER:
        return dict(status="already_current", target=str(target))
    if hashlib.sha256((old + "\n").encode()).hexdigest() != BEFORE_SHA256:
        raise ValueError("Native dispatch differs from the audited version; inspect before patching")
    helper = target.with_name("astral_capability.cjs")
    shipped = Path(__file__).with_name("astral_capability.cjs")
    if not helper.is_file() or helper.read_bytes() != shipped.read_bytes():
        raise ValueError("Install the verified dispatch helper beside index.js before patching")
    after = (source[:start] + AFTER + "\n\n       " + source[end:]).encode()
    # Syntax checking does not import ws or start the platform server.
    subprocess.run(["node", "--check"], input=after, check=True, capture_output=True)
    old_hash = hashlib.sha256(before).hexdigest()
    result = dict(status="ready", target=str(target), before_sha256=old_hash,
                  after_sha256=hashlib.sha256(after).hexdigest(),
                  helper_sha256=hashlib.sha256(shipped.read_bytes()).hexdigest())
    if write:
        backup = target.with_name(target.name + ".before-astral-dispatch-" + old_hash[:16])
        if backup.exists() and backup.read_bytes() != before:
            raise ValueError("Backup name already contains different bytes")
        if not backup.exists():
            with backup.open("xb") as f: f.write(before)
            backup.chmod(stat.S_IMODE(target.stat().st_mode))
        fd, name = tempfile.mkstemp(prefix=".astral-dispatch-", dir=target.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd,"wb") as f:
                f.write(after); f.flush(); os.fsync(f.fileno())
            tmp.chmod(stat.S_IMODE(target.stat().st_mode))
            if target.read_bytes() != before:
                raise ValueError("Platform source changed during patch preparation")
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        result.update(status="applied", backup=str(backup))
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--apply", action="store_true")
    args=parser.parse_args()
    print(json.dumps(apply(args.target,args.apply),indent=2))
