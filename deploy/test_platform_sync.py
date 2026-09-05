"""Device-sync fault injection: only temporary files and fixture network/processes."""
import asyncio
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import types
import unittest
import zipfile

SOURCE = Path(__file__).with_name("platform_sync_method.py").read_text()
OLD = b"# previous working shim\n"
NEW = b"# new working shim\n"


def bundle(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, content in entries:
            z.writestr(name, content)
    return out.getvalue()


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openhome-sync-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.caps = self.root / "caps"
        (self.caps / "astral").mkdir(parents=True)
        (self.caps / "unrelated").mkdir()
        (self.caps / "unrelated/devkit_functions.py").write_bytes(OLD)
        (self.caps / "astral/devkit_functions.py").write_bytes(OLD)
        (self.caps / "astral/config.json").write_bytes(b"owner metadata")
        self.messages = []
        self.pip_calls = []
        self.concurrent = 1
        self.max_pip_active = 0
        self.pip_active = 0
        self.http_status = 200
        self.pip_status = 0
        self.pip_exception = None
        self.replace_failure = set()
        self.body = bundle([("astral/devkit_functions.py", NEW), ("astral/requirements.txt", b"fixture==1")])
        async def send(s):
            self.messages.append(json.loads(s))
        self.client = types.SimpleNamespace(ws=types.SimpleNamespace(send=send))

    def invoke(self):
        def pip(*a, **kw):
            self.pip_calls.append((a, kw))
            if self.pip_exception:
                raise self.pip_exception
            if self.concurrent > 1:
                import time
                self.pip_active += 1
                self.max_pip_active = max(self.max_pip_active, self.pip_active)
                time.sleep(0.02)
                self.pip_active -= 1
            return types.SimpleNamespace(returncode=self.pip_status)
        def replace(src, dst):
            if Path(src).name in self.replace_failure or ("rollback" in self.replace_failure and str(src).endswith("-previous")):
                raise OSError("fixture rename failure")
            return os.replace(src, dst)
        scope = dict(asyncio=asyncio, os=types.SimpleNamespace(replace=replace), shutil=shutil, json=json,
                     API_KEY="fixture-key", API_SERVER_URL="https://fixture.invalid", LOCAL_CAPABILITIES_DIR=str(self.caps),
                     requests=types.SimpleNamespace(post=lambda *a, **kw:types.SimpleNamespace(status_code=self.http_status, content=self.body)),
                     subprocess=types.SimpleNamespace(run=pip))
        exec(compile(SOURCE, "platform_sync_method.py", "exec"), scope)
        async def dispatch():
            await asyncio.gather(*(scope["sync_local_capabilities"](self.client) for _ in range(self.concurrent)))
        asyncio.run(dispatch())
        self.assertEqual(len(self.messages), self.concurrent)
        return self.messages[-1]["success"]

    def preserved(self):
        self.assertEqual((self.caps / "astral/devkit_functions.py").read_bytes(), OLD)
        self.assertEqual((self.caps / "astral/config.json").read_bytes(), b"owner metadata")
        self.assertEqual((self.caps / "unrelated/devkit_functions.py").read_bytes(), OLD)

    def test_valid_merge_and_dependencies_for_native_interpreter(self):
        self.assertTrue(self.invoke())
        self.assertEqual((self.caps / "astral/devkit_functions.py").read_bytes(), NEW)
        self.assertEqual((self.caps / "astral/requirements.txt").read_bytes(), b"fixture==1")
        self.assertEqual((self.caps / "astral/config.json").read_bytes(), b"owner metadata")
        self.assertEqual((self.caps / "unrelated/devkit_functions.py").read_bytes(), OLD)
        self.assertEqual(len(self.pip_calls), 1)
        self.assertEqual(self.pip_calls[0][0][0][:5], ["sudo", "-n", "python3", "-m", "pip"])
        self.assertGreater(self.pip_calls[0][1]["timeout"], 0)
        self.assertFalse(list(self.root.glob(".capability-sync-*")))

    def test_fresh_install(self):
        shutil.rmtree(self.caps)
        self.assertTrue(self.invoke())
        self.assertEqual((self.caps / "astral/devkit_functions.py").read_bytes(), NEW)

    def test_invalid_archives_preserve_installation(self):
        bodies = [b"bad zip", b"", bundle([]),
                  bundle([("astral/requirements.txt", b"fixture")]),
                  bundle([("astral/devkit_functions.py", b"syntax error !!!")]),
                  bundle([("astral/devkit_functions.py", b"")])]
        for body in bodies:
            with self.subTest(body_size=len(body)):
                self.messages.clear(); self.body = body
                self.assertFalse(self.invoke()); self.preserved()
                self.assertFalse(self.pip_calls)

    def test_hostile_paths(self):
        sentinel = self.root / "requirements.txt"
        sentinel.write_bytes(b"outside")
        for name in ("../requirements.txt", "/astral/devkit_functions.py", "a/b/devkit_functions.py",
                     "./devkit_functions.py", "a\\b/devkit_functions.py", "astral/unknown.py"):
            with self.subTest(name=name):
                self.messages.clear(); self.body = bundle([(name, NEW)])
                self.assertFalse(self.invoke()); self.preserved()
                self.assertEqual(sentinel.read_bytes(), b"outside")
                self.assertFalse(self.pip_calls)

    def test_duplicate_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.body = bundle([("astral/devkit_functions.py", NEW), ("astral/devkit_functions.py", OLD)])
        self.assertFalse(self.invoke()); self.preserved()
        self.assertFalse(self.pip_calls)

    def test_archive_symlink_rejected(self):
        info = zipfile.ZipInfo("astral/devkit_functions.py")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.body = bundle([(info, b"../../outside")])
        self.assertFalse(self.invoke()); self.preserved()

    def test_existing_symlink_cannot_escape(self):
        outside = self.root / "outside.py"; outside.write_bytes(OLD)
        target = self.caps / "astral/devkit_functions.py"
        target.unlink(); target.symlink_to(outside)
        self.assertFalse(self.invoke())
        self.assertEqual(outside.read_bytes(), OLD)
        self.assertTrue(target.is_symlink())

    def test_root_symlink_rejected(self):
        original = self.caps
        self.caps = self.root / "linked-caps"; self.caps.symlink_to(original, target_is_directory=True)
        self.assertFalse(self.invoke()); self.preserved()
        self.assertFalse(self.pip_calls)

    def test_pip_failure_preserves_installation(self):
        self.pip_status = 7
        self.assertFalse(self.invoke()); self.preserved()

    def test_pip_exception_preserves_installation(self):
        self.pip_exception = TimeoutError("fixture timeout")
        self.assertFalse(self.invoke()); self.preserved()

    def test_http_failure(self):
        self.http_status = 401
        self.assertFalse(self.invoke()); self.preserved()
        self.assertFalse(self.pip_calls)

    def test_http_404_preserves_installation(self):
        self.http_status = 404
        self.assertTrue(self.invoke()); self.preserved()
        self.assertFalse(self.pip_calls)

    def test_rename_failure_restores_installation(self):
        self.replace_failure = {"next"}
        self.assertFalse(self.invoke()); self.preserved()

    def test_rollback_failure_keeps_recoverable_backup(self):
        self.replace_failure = {"next", "rollback"}
        self.assertFalse(self.invoke())
        backups = list(self.root.glob(".capability-sync-*-previous"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "astral/devkit_functions.py").read_bytes(), OLD)
        self.assertEqual((backups[0] / "unrelated/devkit_functions.py").read_bytes(), OLD)

    def test_concurrent_syncs_are_serialized(self):
        self.concurrent = 2
        self.assertTrue(self.invoke())
        self.assertTrue(all(m["success"] for m in self.messages))
        self.assertEqual(len(self.pip_calls), 2)
        self.assertEqual(self.max_pip_active, 1)
        self.assertEqual((self.caps / "unrelated/devkit_functions.py").read_bytes(), OLD)

    def test_cancelled_caller_keeps_worker_lock(self):
        import threading
        started, release = threading.Event(), threading.Event()
        calls = []
        def pip(*a, **kw):
            calls.append(1)
            if len(calls) == 1:
                started.set()
                if not release.wait(3):
                    raise TimeoutError("fixture release never arrived")
            return types.SimpleNamespace(returncode=0)
        scope = dict(asyncio=asyncio, os=os, shutil=shutil, json=json,
                     API_KEY="fixture-key", API_SERVER_URL="https://fixture.invalid", LOCAL_CAPABILITIES_DIR=str(self.caps),
                     requests=types.SimpleNamespace(post=lambda *a, **kw:types.SimpleNamespace(status_code=200, content=self.body)),
                     subprocess=types.SimpleNamespace(run=pip))
        exec(compile(SOURCE, "platform_sync_method.py", "exec"), scope)
        async def run():
            first = asyncio.create_task(scope["sync_local_capabilities"](self.client))
            self.assertTrue(await asyncio.to_thread(started.wait, 2))
            first.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await first
            # A distinct client must still wait for the cancelled caller's worker.
            second = asyncio.create_task(scope["sync_local_capabilities"](self.client))
            try:
                await asyncio.sleep(0.05)
                self.assertEqual(len(calls), 1)
            finally:
                release.set()
            await second
        asyncio.run(run())
        self.assertEqual(len(calls), 2)
        self.assertTrue(self.messages[-1]["success"])
        self.assertEqual((self.caps / "unrelated/devkit_functions.py").read_bytes(), OLD)

    def test_oversized_bundle_is_refused_before_processing(self):
        class Oversized(bytes):
            def __len__(self): return 64 * 1024 * 1024 + 1
        self.body = Oversized(self.body)
        self.assertFalse(self.invoke()); self.preserved()
        self.assertFalse(self.pip_calls)

    def test_excessive_entry_count_is_refused(self):
        self.body = bundle([(f"folder{i}/", b"") for i in range(2049)])
        self.assertFalse(self.invoke()); self.preserved()
        self.assertFalse(self.pip_calls)

    def test_removed_requirements_not_reinstalled(self):
        (self.caps / "astral/requirements.txt").write_bytes(b"obsolete")
        self.body = bundle([("astral/devkit_functions.py", NEW)])
        self.assertTrue(self.invoke())
        self.assertFalse((self.caps / "astral/requirements.txt").exists())
        self.assertFalse(self.pip_calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
