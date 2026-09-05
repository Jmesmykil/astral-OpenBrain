# Native DevKit integration corrections

Verified on September 5, 2026. These patches repair the existing OpenHome platform
client and node dispatcher on the DevKit; they do not upload or assign an account
ability. The compiled Astral kernel remains release 2.2.3.

## What changed

The companion installer now carries both active platform execution inputs:
`devkit_functions.py` and the hash-pinned `requirements.txt`. It refuses missing or
empty staged inputs before refreshing the existing capability. Old local config and
README files are preserved as historical manual metadata. Native platform sync and
node dispatch do not read them to register account hotwords.

`platform_sync_method.py` validates the complete ZIP, Python entrypoints, paths, file
types, duplicates and size limits before installation. It stages a merge that preserves
unrelated capabilities and owner metadata, installs requirements into the **same root
Python interpreter the native dispatcher uses**, and reports dependency failures.
A filesystem-worker lock survives caller cancellation and serializes overlapping
installations. Failed promotion restores the prior directory; a failed rollback retains
its backup outside temporary cleanup. Successful sync does not claim that pip itself
can roll back partial changes to installed packages.

`astral_capability.cjs` confines execution to the configured capability directory and
uses a unique Python script for each request in the platform root, preserving Python's
existing import path. It removes the request file on completion/error and sends one
result. A failed or interrupted child remains a failure; an intentional silent decline
remains a successful response with no spoken text. MQTT and other message branches
remain unchanged.

## Audited application and recovery

The Python patchers refuse a source method/branch they have not audited. They validate
syntax, preserve unrelated code and save exact prior source bytes beside the target.
They do not silently accommodate a new upstream platform version.

Copy the source-controlled helper, patchers and tests to a staging folder on the device.
Run both test scripts there. Copy the identical `astral_capability.cjs` beside the node
server's `index.js` **before** applying its branch patch. The source guard verifies that
helper's bytes against the staged copy.

```sh
python3 test_platform_sync.py
node --test test_capability_dispatch.cjs
python3 patch_devkit_sync.py /home/openhome/openhome_devkit/openhome_devkit.py
python3 patch_devkit_dispatch.py /home/openhome/openhome_devkit/openhome-node-server/index.js
```

The preceding patcher commands preview. Add `--apply` to perform the checked replacement.
After passing tests against the installed source, restart only the changed platform
service: `openhome_devkit_client.service` for sync, `openhome_node_server.service` for
dispatch. Confirm current process starts and retained settings. Neither correction
requires restarting the Astral voice loop or its mathematics service.

The original backup suffixes on this audited device are
`openhome_devkit.py.before-astral-sync-ac788f5bf9d773ab` and
`index.js.before-astral-dispatch-2ae308ff4afa0a47`. Later managed changes have their own
hash-named backups. To recover from a platform compatibility failure, restore the
appropriate recorded source backup and restart the corresponding service. Keep the
receipt explaining which version was restored; the original platform code contains
the reproduced defects and is not a hardened release.

## Evidence and limits

The final installed sync method passed 19 fixture tests, including cancellation,
concurrency, archive/path failures, dependency failure, root interpreter selection and
rollback failure. The dispatch helper passed eight lifecycle/path/concurrency tests on
both hosts. Each patcher also passed six scoped source/backup checks.

Actual device-local WebSocket requests reached the native node server, root Python and
Astral hub: health, two simultaneous exact-answer requests and a rejected traversal
request all behaved as expected. No request files remained. Thirty samples each of
percentage arithmetic, units and equations produced 90 correct warm answers. Median
whole native request time was 605–616 ms; the first observed equation took 4.73 seconds.
This includes connection/process overhead, not ASR, synthesis or audible playback.
Profiling identified repeated imports and regular-expression compilation as the major
startup cost. Performance optimization remains open.

All 29 recorded owner/configuration hashes remained unchanged by the final platform
restart. The voice and mathematics processes retained their original PIDs. These
receipts do not prove authenticated account upload/assignment, human voice acceptance,
app-slider behavior or the sustained-operation pass. Those remain in the full plan.
