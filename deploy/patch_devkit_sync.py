"""Apply the reviewed capability-sync method only to the audited platform version."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import textwrap

AUDITED_METHOD_SHA256 = {
    "07eac3993a20669800cceca28a0b859ec45f26c44f9a04591f3c29421838fe5a",  # original platform method
    "e63376beea908f5bc91cca501def130a7317de30920196ab34520e6ebd86f64b",  # first staged-sync repair
}


def method(source):
    matches = [n for n in ast.walk(ast.parse(source))
               if isinstance(n, ast.AsyncFunctionDef) and n.name == "sync_local_capabilities"]
    if len(matches) != 1:
        raise ValueError("Expected exactly one sync_local_capabilities method")
    node = matches[0]
    return node, ast.get_source_segment(source, node)


def apply(target, replacement, write=False):
    if target.is_symlink():
        raise ValueError("Refusing a symbolic-link platform source")
    before = target.read_bytes()
    source = before.decode("utf-8")
    old_node, old_method = method(source)
    new_node, new_method = method(replacement.read_text())
    if ast.dump(old_node) == ast.dump(new_node):
        return {"status": "already_current", "target": str(target)}
    digest = hashlib.sha256((old_method + "\n").encode()).hexdigest()
    if digest not in AUDITED_METHOD_SHA256:
        raise ValueError("Platform sync method differs from the audited version; inspect before patching")
    lines = source.splitlines(keepends=True)
    lines[old_node.lineno - 1:old_node.end_lineno] = [textwrap.indent(new_method, " " * old_node.col_offset) + "\n"]
    after = "".join(lines).encode()
    compile(after, str(target), "exec")
    old_hash = hashlib.sha256(before).hexdigest()
    result = dict(status="ready", target=str(target), before_sha256=old_hash,
                  after_sha256=hashlib.sha256(after).hexdigest())
    if write:
        backup = target.with_name(target.name + ".before-astral-sync-" + old_hash[:16])
        if backup.exists() and backup.read_bytes() != before:
            raise ValueError("Backup name already contains different bytes")
        if not backup.exists():
            with backup.open("xb") as f:
                f.write(before)
            backup.chmod(stat.S_IMODE(target.stat().st_mode))
        fd, name = tempfile.mkstemp(prefix=".astral-sync-", dir=target.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "wb") as f:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.target, Path(__file__).with_name("platform_sync_method.py"), args.apply), indent=2))
