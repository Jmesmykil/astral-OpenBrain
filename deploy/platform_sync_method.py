"""Replacement for the DevKit capability-sync method; applied with a source hash guard.

The platform module supplies asyncio, requests, subprocess, os, shutil, json and
its configuration. No network or process is started by importing this fragment.
"""

async def sync_local_capabilities(self):
    import fcntl
    import io
    import pathlib
    import re
    import stat
    import tempfile
    import zipfile

    try:
        response = await asyncio.to_thread(
            requests.post, f"{API_SERVER_URL}/api/sdk/get/devkit-capabilities/",
            json={"api_key": API_KEY}, timeout=30,
        )
        if response.status_code == 404:
            message = "No local capabilities found to sync."
        elif response.status_code != 200:
            raise RuntimeError(f"Failed to fetch capabilities: HTTP {response.status_code}")
        else:
            def install():
                caps = pathlib.Path(LOCAL_CAPABILITIES_DIR)
                if caps.is_symlink():
                    raise ValueError("Capability root must not be a symbolic link")
                limit = 64 * 1024 * 1024
                if not response.content or len(response.content) > limit:
                    raise ValueError("Empty or oversized capability bundle")
                incoming = {}
                expanded = 0
                with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
                    if len(bundle.infolist()) > 2048:
                        raise ValueError("Too many capability bundle entries")
                    for info in bundle.infolist():
                        if info.is_dir():
                            continue
                        parts = info.filename.split("/")
                        if (len(parts) != 2 or
                                not re.fullmatch(r"[A-Za-z0-9_-]+", parts[0]) or
                                parts[1] not in ("devkit_functions.py", "requirements.txt")):
                            raise ValueError("Invalid capability bundle path")
                        mode = stat.S_IFMT(info.external_attr >> 16)
                        if mode not in (0, stat.S_IFREG):
                            raise ValueError("Capability entries must be regular files")
                        expanded += info.file_size
                        if expanded > limit:
                            raise ValueError("Expanded capability bundle is too large")
                        cap_name, filename = parts
                        files = incoming.setdefault(cap_name, {})
                        if filename in files:
                            raise ValueError("Duplicate capability bundle file")
                        files[filename] = bundle.read(info)
                if not incoming:
                    raise ValueError("Capability bundle contains no executable abilities")
                for files in incoming.values():
                    script = files.get("devkit_functions.py")
                    if not script or not script.strip():
                        raise ValueError("Capability is missing its Python entrypoint")
                    compile(script, "devkit_functions.py", "exec")

                # Stage a merge: a download must not erase unrelated local
                # abilities or the owner's extra metadata. Validate before pip.
                # This lock belongs to the filesystem worker, so a cancelled
                # websocket task cannot release it while installation continues.
                with (caps.parent / f".{caps.name}.sync.lock").open("a") as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    with tempfile.TemporaryDirectory(prefix=".capability-sync-", dir=caps.parent) as tmp:
                        stage = pathlib.Path(tmp) / "next"
                        backup = caps.parent / (pathlib.Path(tmp).name + "-previous")
                        if caps.exists():
                            shutil.copytree(caps, stage, symlinks=True)
                        else:
                            stage.mkdir()
                        for cap_name, files in incoming.items():
                            target = stage / cap_name
                            if target.is_symlink():
                                raise ValueError("Capability directory must not be a symbolic link")
                            target.mkdir(exist_ok=True)
                            # Missing requirements means this new package has none.
                            # Never rerun dependencies retained from an older package.
                            if "requirements.txt" not in files:
                                (target / "requirements.txt").unlink(missing_ok=True)
                            for filename, data in files.items():
                                path = target / filename
                                if path.is_symlink():
                                    raise ValueError("Capability file must not be a symbolic link")
                                path.write_bytes(data)
                        for cap_name, files in incoming.items():
                            if "requirements.txt" in files:
                                # The node dispatcher runs sudo python3. Install into
                                # that interpreter, not the companion user's private site.
                                result = subprocess.run(
                                    ["sudo", "-n", "python3", "-m", "pip", "install", "-r", str(stage / cap_name / "requirements.txt"),
                                     "--break-system-packages"],
                                    capture_output=True, text=True, timeout=180,
                                )
                                if result.returncode:
                                    raise RuntimeError(f"Dependency installation failed for {cap_name}")
                        if caps.exists():
                            os.replace(caps, backup)
                        try:
                            os.replace(stage, caps)
                        except BaseException:
                            if backup.exists():
                                try:
                                    os.replace(backup, caps)
                                except OSError as exc:
                                    raise RuntimeError(f"Rollback failed; previous installation retained at {backup}") from exc
                            raise
                        # A failed rollback must leave its backup outside the
                        # temporary-directory cleanup. After success it is obsolete.
                        if backup.exists():
                            shutil.rmtree(backup, ignore_errors=True)
                return sorted(incoming)

            installed = await asyncio.to_thread(install)
            message = f"Synced {len(installed)} local capabilities: {', '.join(installed)}"
        result = {"success": True, "message": message}
    except Exception as exc:
        # Do not print credentials, response bodies, or pip output. A failed
        # dependency install is a failure even if pip changed some packages.
        result = {"success": False, "message": f"Sync failed: {exc}"}
    await self.ws.send(json.dumps(dict(result, response="alert", type="sync-capabilities")))
