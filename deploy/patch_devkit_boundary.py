"""Restrict the audited root WebSocket control service to its local callers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

BEFORE_SHA256 = "bf964d6f0d430f31d7d865da596aea21481f5b0b0675bc7c805b1cde99f6d38c"
FIRST_BOUNDARY_SHA256 = "b0e9746cb3c99c48ae25383ce130c2a2c57f9b91513bb06ebc74a44bfb51d3ac"
CONNECTION = 'wss.on("connection", (ws) => {'
GUARDED_CONNECTION = CONNECTION + '\n  ws.on("error", error => {\n    console.error("Local WebSocket error:", error.code || "WS_ERROR");\n  });'
BEFORE = 'const wss = new WebSocketServer({ port: PORT });'
AFTER = 'const wss = new WebSocketServer(require("./astral_ws_boundary.cjs")(PORT));'


def apply(target, write=False):
    if target.is_symlink():
        raise ValueError("Refusing a symbolic-link platform source")
    before = target.read_bytes()
    source = before.decode()
    helper = target.with_name("astral_ws_boundary.cjs")
    shipped = Path(__file__).with_name("astral_ws_boundary.cjs")
    if helper.is_symlink() or not helper.is_file() or helper.read_bytes() != shipped.read_bytes():
        raise ValueError("Install the reviewed boundary helper beside index.js first")
    if source.count(AFTER) == 1 and BEFORE not in source and source.count(GUARDED_CONNECTION) == 1:
        return dict(status="already_current", target=str(target))
    old_hash = hashlib.sha256(before).hexdigest()
    if old_hash not in (BEFORE_SHA256, FIRST_BOUNDARY_SHA256) or source.count(CONNECTION) != 1:
        raise ValueError("Platform source differs from the audited version; inspect before patching")
    after = source.replace(BEFORE, AFTER).replace(CONNECTION, GUARDED_CONNECTION).encode()
    subprocess.run(["node", "--check"], input=after, check=True, capture_output=True)
    subprocess.run(["node", "--check", str(helper)], check=True, capture_output=True)
    result = dict(status="ready", target=str(target), before_sha256=old_hash,
                  after_sha256=hashlib.sha256(after).hexdigest(),
                  helper_sha256=hashlib.sha256(shipped.read_bytes()).hexdigest())
    if write:
        previous = target.stat()
        backup = target.with_name(target.name + ".before-astral-boundary-" + old_hash[:16])
        if backup.is_symlink() or (backup.exists() and backup.read_bytes() != before):
            raise ValueError("Backup path is unsafe or contains different bytes")
        if not backup.exists():
            with backup.open("xb") as f:
                f.write(before)
            backup.chmod(stat.S_IMODE(previous.st_mode))
        fd, name = tempfile.mkstemp(prefix=".astral-boundary-", dir=target.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(after)
                f.flush()
                os.fsync(f.fileno())
            tmp.chmod(stat.S_IMODE(previous.st_mode))
            if os.geteuid() == 0:
                os.chown(tmp, previous.st_uid, previous.st_gid)
            if target.read_bytes() != before or target.is_symlink():
                raise ValueError("Platform source changed during patch preparation")
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        result.update(status="applied", backup=str(backup))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.target, args.apply), indent=2))
