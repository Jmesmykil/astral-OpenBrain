# deploy

Device-side files that are not part of the community submission.

`devkit-config.json` is the local capability's `config.json` as the node server expects
it at `~/openhome_devkit/local_capabilities/astral/config.json`. It carries the
`unique_name` and the `matching_hotwords` list, which is what decides whether a spoken
phrase reaches Astral at all or goes to the cloud agent.

It lives here rather than in `community/astral/` on purpose. A community ability has no
`config.json` — trigger words are platform-managed and set in the dashboard — so
shipping one inside that directory would break the upstream contribution shape. It also
should not live only on the device, because then the file that decides what the ability
can hear would exist nowhere anybody can read it.

The hotword list has to keep pace with the engine. An answer the engine can compute but
no hotword reaches is an answer that does not exist, out loud.

Deployed by:

```bash
python3 hub/verify_on_device.py --deploy
```

## The sync only runs one way

`shell_scripts/download_local_abilities.sh` on the DevKit POSTs the device API key to
`$SERVER_URL/api/sdk/.../`, downloads a ZIP of the agent's capabilities, and unpacks it
over `~/openhome_devkit/local_capabilities/`. Cloud to device. There is no upload path
on the device, nothing on the device reads `matching_hotwords` (checked: no file under
`openhome_devkit/` outside `local_capabilities/` references it), and no OpenHome CLI is
installed.

Two consequences, both verified on 2026-08-17:

1. Anything deployed by hand here is live immediately but lasts only until that sync
   runs. Nothing schedules it — no cron entry, no systemd timer, no caller anywhere in
   the tree — so it runs when someone or something asks for it, which in practice means
   re-onboarding the device or an action from the dashboard.
2. Hotwords take effect through the cloud, not the device. Editing this file makes the
   device's copy correct; it does not by itself teach the agent to route a new phrase.
   That registration happens on app.openhome.com against the agent, and it needs an
   account login.
