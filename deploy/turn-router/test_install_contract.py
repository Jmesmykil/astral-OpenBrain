"""Real file/filter and shell failure controls; no network or device mutation."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
INSTALLER = HERE.parent / "install_v2.sh"
SOURCE = INSTALLER.read_text()
spec = importlib.util.spec_from_file_location("check_installed", HERE / "check_installed.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class InstallContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openhome-install-contract-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_preflight_failure_precedes_all_writes(self):
        repo = self.root / "repo"
        (repo / "deploy/turn-router").mkdir(parents=True)
        (repo / "hub/data").mkdir(parents=True)
        shutil.copy2(INSTALLER, repo / "deploy/install_v2.sh")
        for name in ("check_installed.py", "protocol.json"):
            shutil.copy2(HERE / name, repo / "deploy/turn-router" / name)
        (repo / "hub/voice_turns.py").write_text("# requires paired browser\n")
        routes = repo / "hub/data/routes.json"
        routes.write_text('{"clouds":{"openhome":{"enabled":true}}}\n')
        original = routes.read_bytes()
        bins = self.root / "bin"
        bins.mkdir()
        for name, script in (("ssh", "exit 42"), ("ipconfig", "exit 43"), ("rsync", "exit 44")):
            path = bins / name
            path.write_text("#!/bin/sh\n" + script + "\n")
            path.chmod(0o755)
        result = subprocess.run(["zsh", str(repo / "deploy/install_v2.sh"), "user@fixture.invalid"],
                                env=dict(os.environ, PATH=str(bins) + os.pathsep + os.environ["PATH"]),
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 42)
        self.assertEqual(routes.read_bytes(), original)
        self.assertFalse((repo / "hub/data/lan.token").exists())

    def _installer_in(self, repo):
        (repo / "deploy/turn-router").mkdir(parents=True)
        shutil.copy2(INSTALLER, repo / "deploy/install_v2.sh")
        for name in ("check_installed.py", "protocol.json"):
            shutil.copy2(HERE / name, repo / "deploy/turn-router" / name)
        return repo / "deploy/install_v2.sh"

    def _tools(self, **scripts):
        bins = self.root / "bin"
        bins.mkdir(exist_ok=True)
        for name, script in scripts.items():
            path = bins / name
            path.write_text("#!/bin/sh\n" + script + "\n")
            path.chmod(0o755)
        return dict(os.environ, PATH=str(bins) + os.pathsep + os.environ["PATH"])

    def test_missing_hub_fails_first_in_one_sentence(self):
        installer = self._installer_in(self.root / "repo")
        calls = self.root / "calls"
        env = self._tools(ssh=f'echo "ssh $*" >> "{calls}"', rsync=f'echo "rsync $*" >> "{calls}"')
        result = subprocess.run(["zsh", str(installer), "user@fixture.invalid"], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1, result.stderr)
        self.assertIn("hub/", result.stderr)
        self.assertFalse(calls.exists(), "nothing reaches ssh or rsync")

    def test_ssh_uses_configuration_and_agent_unless_a_key_is_named(self):
        repo = self.root / "repo"
        installer = self._installer_in(repo)
        (repo / "hub").mkdir()
        (repo / "hub/voice_turns.py").write_text("# paired\n")
        seen = self.root / "seen"
        env = self._tools(ssh=f'echo "$* agent=${{SSH_AUTH_SOCK-unset}}" > "{seen}"; exit 42')
        env["SSH_AUTH_SOCK"] = "/fixture/agent.sock"
        env.pop("ASTRAL_SSH_KEY", None)
        subprocess.run(["zsh", str(installer), "user@device"], env=env, capture_output=True, timeout=10)
        line = seen.read_text()
        self.assertTrue(line.startswith("-o BatchMode=yes -o ConnectTimeout=8 user@device "), line)
        self.assertNotIn("-i ", line)
        self.assertIn("agent=/fixture/agent.sock", line)
        subprocess.run(["zsh", str(installer), "user@device"], env=dict(env, ASTRAL_SSH_KEY="/fixture/key"),
                       capture_output=True, timeout=10)
        line = seen.read_text()
        self.assertTrue(line.startswith("-i /fixture/key -o IdentitiesOnly=yes "), line)
        self.assertTrue(line.rstrip("\n").endswith(" agent="), "a named key is used without the agent")

    def test_lan_address_is_the_source_toward_the_device_or_one_clear_failure(self):
        repo = self.root / "repo"
        installer = self._installer_in(repo)
        (repo / "hub").mkdir()
        (repo / "hub/lan.py").write_text("PORT = 8790\n\ndef token():\n    pass\n")
        env = self._tools(
            ssh='if [ "$1" = "-G" ]; then echo "user fixture"; echo "hostname $FIXTURE_HOST"; exit 0; fi; exit 42',
            rsync="exit 44")
        env.pop("ASTRAL_LAN_ADDR", None)

        def run(host, **extra):
            return subprocess.run(["zsh", str(installer), "user@alias"], env=dict(env, FIXTURE_HOST=host, **extra),
                                  capture_output=True, text=True, timeout=20)
        found = run("127.0.0.1")
        self.assertEqual(found.returncode, 44, found.stderr)
        self.assertIn("'host': '127.0.0.1'", found.stdout, "ssh's host name for the alias, then its route")
        failed = run("fixture.invalid")
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(len(failed.stderr.strip().splitlines()), 1, failed.stderr)
        self.assertIn("ASTRAL_LAN_ADDR", failed.stderr)
        given = run("fixture.invalid", ASTRAL_LAN_ADDR="192.0.2.7")
        self.assertEqual(given.returncode, 44, given.stderr)
        self.assertIn("'host': '192.0.2.7'", given.stdout)

    def test_pair_and_served_asset_validation(self):
        node = self.root / "openhome_devkit/openhome-node-server/astral_turn_router.cjs"
        app = self.root / "openhome_devkit/openhome-dashboard-pi/src/App.tsx"
        node.parent.mkdir(parents=True)
        app.parent.mkdir(parents=True)
        node.write_bytes(b"bridge")
        native = node.with_name("astral_capability.cjs")
        native.write_bytes(b"native guard")
        app.write_bytes(b"app")
        digest = lambda b: hashlib.sha256(b).hexdigest()
        expected = {"bridge_sha256": digest(b"bridge"), "app_sha256": digest(b"app"),
                    "native_dispatch_sha256": digest(b"native guard"),
                    "assets": {"dist/index.html": digest(b"index")}}
        def get(url, authenticated=False):
            return b'{"ok":true,"connected":true}' if authenticated else b"index"
        self.assertTrue(checker.verify(self.root, expected, get)["ok"])
        native.write_bytes(b"old native dispatcher")
        with self.assertRaisesRegex(RuntimeError, "astral_capability"):
            checker.verify(self.root, expected, get)
        native.unlink()
        with self.assertRaisesRegex(RuntimeError, "astral_capability"):
            checker.verify(self.root, expected, get)
        native.write_bytes(b"native guard")
        app.write_bytes(b"old app")
        with self.assertRaisesRegex(RuntimeError, "App.tsx"):
            checker.verify(self.root, expected, get)
        app.write_bytes(b"app")
        with self.assertRaisesRegex(RuntimeError, "Served browser"):
            checker.verify(self.root, expected, lambda url, auth=False: get(url, auth) if auth else b"old index")
        with self.assertRaisesRegex(RuntimeError, "not registered"):
            checker.verify(self.root, expected, lambda url, auth=False: b'{"ok":true,"connected":false}')
        node.unlink()
        with self.assertRaisesRegex(RuntimeError, "astral_turn_router"):
            checker.verify(self.root, expected, get)

    def test_paired_restart_failures_are_not_masked_and_browser_stays_running(self):
        line = [line for line in SOURCE.splitlines() if "systemctl --user restart astral-hub.service" in line][-1]
        command = shlex.split(line)[-1]
        bins = self.root / "bin"
        bins.mkdir()
        controller = bins / "systemctl"
        controller.write_text("""#!/usr/bin/env python3
import os,sys
from pathlib import Path
args=' '.join(sys.argv[1:])
with Path(os.environ['FIXTURE_COMMAND_LOG']).open('a') as f:f.write(args+'\\n')
mode=os.environ['FIXTURE_FAULT']
if mode=='browser' and 'is-active --quiet openhome-dashboard.service' in args:sys.exit(3)
if mode=='restart' and 'restart astral-hub.service' in args:sys.exit(7)
if mode=='hub' and 'is-active astral-hub.service' in args:sys.exit(3)
sys.exit(0)
""")
        controller.chmod(0o755)
        for name, body in (("sleep", "exit 0"), ("tail", "echo END_OF_DEPLOY")):
            tool = bins / name
            tool.write_text("#!/bin/sh\n" + body + "\n")
            tool.chmod(0o755)
        log = self.root / "commands"
        for fault in ("browser", "restart", "hub", ""):
            with self.subTest(fault=fault):
                log.write_text("")
                env = dict(os.environ, PATH=str(bins) + os.pathsep + os.environ["PATH"],
                           FIXTURE_COMMAND_LOG=str(log), FIXTURE_FAULT=fault)
                result = subprocess.run(["bash", "-c", command], env=env, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode == 0, not bool(fault))
                self.assertEqual("END_OF_DEPLOY" in result.stdout, not bool(fault))
                self.assertNotIn("stop openhome-dashboard", log.read_text())
                if fault == "browser":
                    self.assertNotIn("restart astral-hub", log.read_text())

    def test_remote_route_merge_preserves_device_choices(self):
        block = SOURCE.split("<<'PYROUTES'\n", 1)[1].split("\nPYROUTES", 1)[0]
        path = self.root / "astral-voice/hub-v2/data/routes.json"
        path.parent.mkdir(parents=True)
        original = {"mac": {"host": "old", "port": 8790}, "phone": {"host": "owner-choice"},
                    "clouds": {"openhome": {"enabled": True}, "anthropic": {"enabled": False}},
                    "owner_extension": ["preserve me"]}
        path.write_text(json.dumps(original))
        with mock.patch.object(Path, "home", return_value=self.root), mock.patch.object(sys, "argv", ["-", "192.0.2.5"]):
            exec(compile(block, "actual-route-merge", "exec"), {})
        actual = json.loads(path.read_text())
        expected = dict(original, mac={"host": "192.0.2.5", "port": 8790}, cloud={"enabled": False})
        self.assertEqual(actual, expected)

    def test_actual_rsync_filters_preserve_device_routes_with_delete(self):
        segment = SOURCE.split("rsync -rlt --delete", 1)[1].split('"$HERE/hub/"', 1)[0]
        filters = []
        for line in segment.splitlines():
            if line.lstrip().startswith("`#"):
                continue
            filters.extend(word for word in shlex.split(line.replace("\\", ""))
                           if word.startswith("--include=") or word.startswith("--exclude="))
        src, dst = self.root / "src", self.root / "dst"
        for root in (src, dst):
            (root / "data").mkdir(parents=True)
        (src / "data/routes.json").write_text("local defaults")
        (dst / "data/routes.json").write_text("device choices")
        (src / "fresh.py").write_text("new source")
        (dst / "obsolete.py").write_text("old source")
        subprocess.run(["rsync", "-rlt", "--delete", *filters, str(src) + "/", str(dst) + "/"],
                       check=True, capture_output=True, timeout=10)
        self.assertEqual((dst / "data/routes.json").read_text(), "device choices")
        self.assertEqual((dst / "fresh.py").read_text(), "new source")
        self.assertFalse((dst / "obsolete.py").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
