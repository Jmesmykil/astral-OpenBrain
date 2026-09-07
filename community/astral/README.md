# Astral — OpenHome local ability

Astral sends a transcribed request to the DevKit, where the local hub or compiled
`astral-kernel` computes an answer. OpenHome handles the speech and agent session. When
neither engine can answer an ordinary request, the ability returns the turn to the agent.
An absent or failed engine is reported distinctly.

The package passes the creator's OpenHome CLI validator. Authenticated deployment,
assignment and a spoken platform request are still pending in the current completion
audit. The 2.2.3 compiled artifact is installed and verified on the device. Its versioned
dependency is pinned by SHA-256. The DevKit downloaded that public dependency with pip
hash checking, and it matches the installed, verified artifact.

## Answers on the device

The compiled layer covers time and date, arithmetic, money and unit conversions, grades,
chemistry, physics, statistics and number tools. The shim reads DevKit telemetry and can
publish supported MQTT device commands. With the local hub installed, it also reaches
the library, definitions, timers, notes and native mathematics on the card.

| Example | Deterministic answer |
|---|---|
| What is twenty percent of eighty? | 20 percent of 80 is 16. |
| Convert ten pounds to kilograms. | 10 pounds is 4.54 kilograms. |
| How many feet in a mile? | 1 mile is 5280 feet. |
| Molar mass of water. | The molar mass of water (H2O) is 18.015 grams per mole. |
| Standard deviation of 4 6 8 10. | The sample standard deviation of 4, 6, 8, 10 is 2.58, around a mean of 7. |
| Is 91 prime? | No, 91 isn't prime. It's 7 times 13. |

A computed answer and a correctly transcribed spoken request are separate requirements.
Fast arithmetic does not establish end-to-end voice latency or transcription accuracy.
The hub can use an optional local model for appropriate assistance; the exact arithmetic
path does not require one.

## Install and verify

Use the creator's persistent fork of `Jmesmykil/openhome-cli`, which carries the DevKit
validator fix. From the development checkout:

```sh
OPENHOME_NO_UPDATE=1 openhome validate community/astral --json
bundle_dir="$(mktemp -d)"
(cd community && zip "$bundle_dir/astral.zip" \
  astral/__init__.py astral/main.py astral/devkit_functions.py astral/requirements.txt \
  astral/config.json astral/README.md astral/BOUNDARY.md)
```

The CLI uploads a ZIP; it does not zip directories or read deployment metadata from
`config.json`. The archive above contains the foreground ability under `astral/` and
excludes the optional background daemon, caches and private hub. Keep the ZIP path for
the existing account draft's **Upload ZIP** control, or use the CLI with configured
credentials:

```sh
OPENHOME_NO_UPDATE=1 openhome deploy "$bundle_dir/astral.zip" \
  --name astral --category local
```

That command asks for the description and comma-separated trigger phrases; use the
values in `community/astral/config.json`. For unattended use, supply `--description`,
`--triggers` and `--json` as well. An existing browser login does not automatically
configure the CLI. Use an existing authenticated account workflow when available;
`openhome login` is only needed to configure missing CLI credentials.

Inspect existing records before uploading. Resume or update the intended Astral draft;
do not follow a duplicate-name suggestion to delete an existing ability. Read the target
agent's assigned set before `openhome assign`, retain every existing selection and add
only Astral. A `trigger` check can invoke the configured platform agent, so first confirm
the intended local route and inference policy.

Local abilities require a connected DevKit. Keep a sanitized receipt for installation
and assignment, then test the actual spoken route. Local package validation is not a
platform deployment receipt.

The native DevKit sync installs `devkit_functions.py` and `requirements.txt`. The
companion hub installer refreshes both files for an existing Astral installation.
Older local `config.json` and README files are historical metadata; the current
platform dispatcher does not use them to register account hotwords or assignments.
See the [native integration corrections](../../deploy/PLATFORM-HARDENING.md) for the
checked device sync/dispatch patches and their verification boundaries.

`requirements.txt` identifies the separately licensed wheel for CPython 3.13 on Linux
aarch64. The private hub is optional for the compiled exact-answer classes and required
for the wider on-card functionality. See [BOUNDARY.md](BOUNDARY.md) and the repository's
[release procedure](../../RELEASE.md).

## Routes and microphone ownership

The foreground ability can offer a named route and take a reply. A refusal, uncertain
mention or ambiguous comparison does not select a machine. This ability runs inside an
OpenHome session: its return to the platform agent is distinct from an outbound request
made by the fully local loop.

The optional background daemon is a separate ability category. It has its own deployment
and voice-race acceptance requirements; it is not proved by foreground validation.

For the fully local speech path, run the local loop described in
[HANDOFF.md](../../HANDOFF.md). The kiosk and local loop must not both own the microphone.
OpenHome owns volume and microphone sensitivity; the loop does not force those settings.

## License and scope

These integration files are MIT. `astral-kernel` is a proprietary compiled dependency.
The private engine sources are not included in this ability. The proposed harness bridge
remains future work.
