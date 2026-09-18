#!/usr/bin/env python3
"""Pure planning, backup, rollback and verification logic for the openhome audio runtime.

No subprocess, no filesystem side effects here: the device runner (install-audio-runtime.py)
gathers facts and executes the plan; the desk tests drive this module with fakes.
"""
import hashlib, json, os
from pathlib import Path


def astral_home():
    """ASTRAL_HOME, else the running user's home when Astral is installed there, else the stock
    DevKit user's home."""
    if os.environ.get('ASTRAL_HOME'):
        return os.environ['ASTRAL_HOME']
    home = Path.home()
    return str(home) if (home / 'astral-voice').is_dir() else '/home/openhome'


HOME = astral_home()

# restart levels, ordered: a higher level includes everything below it
LEVELS = ['none', 'hub', 'aec', 'wireplumber', 'audio-stack']

# Each target: candidate file (relative to files/), device path, mode, owner, restart level.
TARGETS = [
    dict(name='astral-aec.service', src='systemd-user/astral-aec.service',
         dst=HOME + '/.config/systemd/user/astral-aec.service', mode='664', owner='openhome', level='aec'),
    dict(name='30-graph-timing.conf', src='systemd-user/astral-aec.service.d/30-graph-timing.conf',
         dst=HOME + '/.config/systemd/user/astral-aec.service.d/30-graph-timing.conf', mode='664', owner='openhome', level='aec'),
    dict(name='40-aec-block.conf', src='systemd-user/astral-aec.service.d/40-aec-block.conf',
         dst=HOME + '/.config/systemd/user/astral-aec.service.d/40-aec-block.conf', mode='664', owner='openhome', level='aec'),
    dict(name='20-single-router.conf', src='systemd-user/astral-hub.service.d/20-single-router.conf',
         dst=HOME + '/.config/systemd/user/astral-hub.service.d/20-single-router.conf', mode='644', owner='openhome',
         level='hub', install_via_sudo=True),   # directory is root-owned 755
    dict(name='51-astral-voicehat-headroom.conf', src='wireplumber.conf.d/51-astral-voicehat-headroom.conf',
         dst=HOME + '/.config/wireplumber/wireplumber.conf.d/51-astral-voicehat-headroom.conf', mode='664', owner='openhome', level='wireplumber'),
    dict(name='52-astral-browser-state.conf', src='wireplumber.conf.d/52-astral-browser-state.conf',
         dst=HOME + '/.config/wireplumber/wireplumber.conf.d/52-astral-browser-state.conf', mode='664', owner='openhome', level='wireplumber'),
    dict(name='49-openhome-rtkit.rules', src='polkit-rules.d/49-openhome-rtkit.rules',
         dst='/etc/polkit-1/rules.d/49-openhome-rtkit.rules', mode='644', owner='root', level='audio-stack', install_via_sudo=True),
]

# What the packaged configuration needs.
EXPECTED = dict(card='snd_rpi_googlevoicehat', quantum='960', latency='960/48000')
# What it was captured and verified on (ORIGIN.txt). A difference is reported, not refused:
# apply backs up every target, verifies the result, and rollback restores the exact bytes.
VERIFIED_ON = dict(hostname='openhome', pipewire='1.4.2', wireplumber='0.5.8')
# The first apply on a device records its speaker and microphone levels here, in the backup
# root. Later runs are held to that record, never to numbers from another device.
LEVELS_RECORD = 'installed-levels.json'

# The only node properties the verifier reads from pw-dump. Everything else (including any
# client-supplied strings) is dropped before it reaches a report.
NODE_PROPS = ('node.name', 'media.class', 'node.latency', 'node.link-group', 'node.group',
              'api.alsa.headroom', 'api.alsa.period-size', 'audio.position', 'node.driver')

# The running service must have started no earlier than its config file was written. Both sides
# are sub-second (CLOCK_MONOTONIC start converted to wall clock; st_mtime), so no slack is applied.
# On the device WirePlumber started 0.139 s after its rule file and the AEC unit 0.380 s after its
# drop-in; both pass strictly. The wall-clock ExecMainStartTimestamp is reported beside it.
START_AFTER_WRITE_TOLERANCE = 0.0


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(candidate_dir):
    """Targets with the sha256 of the candidate bytes. Raises if a candidate file is missing."""
    out = []
    for t in TARGETS:
        data = (Path(candidate_dir) / 'files' / t['src']).read_bytes()
        out.append(dict(t, sha=sha_bytes(data), size=len(data)))
    return out


def parse_pw_dump(raw):
    """{node.name: {whitelisted prop: str, 'state': str}} from raw pw-dump bytes.

    pw-dump can carry invalid UTF-8 and null members, so: decode with replacement, tolerate a
    null or missing info/props, drop None values, keep only NODE_PROPS, and spell a list-valued
    audio.position the way WirePlumber rules do ("[ FL FR ]")."""
    if raw is None:
        return {}
    text = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
    try:
        dump = json.loads(text)
    except ValueError:
        return {}
    out = {}
    for o in dump if isinstance(dump, list) else []:
        if not isinstance(o, dict) or o.get('type') != 'PipeWire:Interface:Node':
            continue
        info = o.get('info') or {}
        props = info.get('props') or {}
        name = props.get('node.name')
        if not isinstance(name, str):
            continue
        rec = {}
        for k in NODE_PROPS:
            v = props.get(k)
            if v is None:
                continue
            if k == 'audio.position' and isinstance(v, list):
                v = '[ ' + ' '.join(str(x) for x in v) + ' ]'
            rec[k] = v if isinstance(v, str) else json.dumps(v)
        state = info.get('state')
        rec['state'] = state if isinstance(state, str) else ''
        out[name] = rec
    return out


class PreconditionError(RuntimeError):
    pass


def check_preconditions(facts):
    """facts: dict gathered read-only by the runner. Returns the warnings, or raises with every
    failure listed. The saved levels are compared with the ones recorded on this device when
    the runtime was installed; before any record there is nothing to compare, and apply
    records them."""
    bad, warnings = [], []
    if facts.get('hostname') != VERIFIED_ON['hostname']:
        warnings.append('hostname is %r; verified on %r' % (facts.get('hostname'), VERIFIED_ON['hostname']))
    if EXPECTED['card'] not in (facts.get('asound_cards') or ''):
        bad.append('VoiceHAT card not present in /proc/asound/cards')
    for stack in ('pipewire', 'wireplumber'):
        found = facts.get(stack + '_version')
        if not str(found or '').startswith(VERIFIED_ON[stack]):
            warnings.append('%s version %r; verified on %s' % (stack, found, VERIFIED_ON[stack]))
    if not facts.get('aec_webrtc_plugin'):
        bad.append('libspa-aec-webrtc.so not found')
    for unit in ('rtkit-daemon', 'polkit'):
        if facts.get('system_active', {}).get(unit) != 'active':
            bad.append('%s is not active' % unit)
    if facts.get('user') != 'openhome':
        bad.append('must run as openhome')
    if not facts.get('sudo_noninteractive'):
        bad.append('sudo -n is required for the root-owned targets')
    if not facts.get('backup_root_writable'):
        bad.append('backup root is not writable')
    recorded = facts.get('recorded_levels')
    if recorded is not None and facts.get('env_levels') != recorded.get('env_levels'):
        bad.append('~/.env levels %r differ from %r, recorded when the runtime was installed; put them '
                   'back, or remove %s to record the current ones at the next apply'
                   % (facts.get('env_levels'), recorded.get('env_levels'), facts.get('levels_record_path', LEVELS_RECORD)))
    if not facts.get('hub_unit_present'):
        bad.append('astral-hub.service base unit missing')
    if facts.get('room_test_running'):
        bad.append('a room test holds the calibration lock')
    if bad:
        raise PreconditionError('; '.join(bad))
    return warnings


def levels_record(env_levels, levels, at):
    """What the first apply on a device records: its saved (~/.env) and live levels."""
    return {'recorded_at': at, 'env_levels': dict(env_levels or {}),
            'levels': {'speaker': levels.get('speaker'), 'microphone': levels.get('microphone')}}


def plan(manifest, current):
    """current: {dst: {'exists': bool, 'sha': str|None}}.
    Returns {'changes': [...], 'unchanged': [...], 'level': str}."""
    changes, unchanged = [], []
    level = 'none'
    for t in manifest:
        cur = current.get(t['dst'], {'exists': False, 'sha': None})
        if cur['exists'] and cur['sha'] == t['sha']:
            unchanged.append(t['name'])
        else:
            changes.append(dict(name=t['name'], dst=t['dst'], existed=cur['exists'], from_sha=cur['sha'], to_sha=t['sha'], level=t['level']))
            if LEVELS.index(t['level']) > LEVELS.index(level):
                level = t['level']
    return {'changes': changes, 'unchanged': unchanged, 'level': level}


def restart_sequence(level):
    """Ordered service actions for a restart level. 'none' means no restart at all."""
    if level == 'none':
        return []
    seq = [('user', 'daemon-reload')]
    if level == 'hub':
        return seq + [('user', 'restart', 'astral-hub')]
    if level == 'aec':
        # explicit: the hub is stopped first and started last; nothing relies on Requires=
        # propagation, so a manager that does not restart dependents still ends with the hub up
        return seq + [('user', 'stop', 'astral-hub'), ('user', 'restart', 'astral-aec'), ('user', 'start', 'astral-hub')]
    if level == 'wireplumber':
        # WirePlumber re-creates the HAT nodes; the AEC streams must be re-created after
        # them so both links (capture, sink-monitor reference) are made fresh
        return seq + [('user', 'stop', 'astral-hub'), ('user', 'stop', 'astral-aec'),
                      ('user', 'restart', 'wireplumber'), ('user', 'start', 'astral-aec'), ('user', 'start', 'astral-hub')]
    if level == 'audio-stack':
        # RTKit is asked once at module load: the whole graph must be re-created
        return seq + [('user', 'stop', 'astral-hub'), ('user', 'stop', 'openhome-dashboard'), ('user', 'stop', 'astral-aec'),
                      ('user', 'stop', 'wireplumber', 'pipewire-pulse', 'pipewire'),
                      ('user', 'start', 'pipewire', 'pipewire-pulse', 'wireplumber'),
                      ('user', 'start', 'astral-aec'), ('user', 'start', 'openhome-dashboard'), ('user', 'start', 'astral-hub')]
    raise ValueError(level)


def backup_meta(manifest, current, facts, audio_before, plan_result):
    """What a rollback needs. `current` carries the ACTUAL pre-state of every target (exists, sha,
    mode, uid, gid); `plan_result` says which targets this transaction intends to write. `installed`
    starts False everywhere and is set by mark_installed() as each file is written, so a rollback
    only ever touches what this transaction actually wrote."""
    planned = {c['name'] for c in plan_result['changes']}
    targets = []
    for t in manifest:
        cur = current.get(t['dst'], {}) or {}
        targets.append(dict(name=t['name'], dst=t['dst'], backup=t['name'],
                            existed=bool(cur.get('exists', False)), sha_before=cur.get('sha'),
                            mode_before=cur.get('mode'), uid_before=cur.get('uid'), gid_before=cur.get('gid'),
                            sha_installed=t['sha'], planned=t['name'] in planned, installed=False,
                            install_via_sudo=bool(t.get('install_via_sudo'))))
    return {
        'targets': targets,
        'services': facts.get('service_states', {}),
        'audio_before': audio_before,
        'sink_mute_before': audio_before.get('sink_mute'),
        'levels_before': audio_before.get('levels'),
    }


def mark_installed(meta, name):
    for t in meta['targets']:
        if t['name'] == name:
            t['installed'] = True
            return
    raise KeyError(name)


class RollbackRefused(RuntimeError):
    pass


def rollback_plan(meta, current, done=()):
    """Ops to return the targets THIS transaction wrote to their pre-install state.

    Per target: not installed by us (unplanned, or a partial apply never reached it) -> no-op.
    Already back at its pre-install bytes -> no-op. Already rolled back (`done`) -> no-op.
    Still carrying exactly the bytes we installed -> restore the backup (existed) or remove
    (absent before). Anything else is another actor's work and the whole rollback is refused:
    bytes that are neither ours nor the original, or a file that is gone although we never
    delete during apply."""
    ops, noops, refusals = [], [], []
    for t in meta['targets']:
        cur = current.get(t['dst'], {'exists': False, 'sha': None})
        if not t.get('installed'):
            noops.append((t['name'], 'not written by this transaction'))
            continue
        if t['name'] in done:
            noops.append((t['name'], 'already rolled back'))
            continue
        if not cur['exists']:
            refusals.append((t['name'], 'missing now; this transaction never deleted it'))
            continue
        if t['existed'] and cur['sha'] == t['sha_before']:
            noops.append((t['name'], 'already at its pre-install bytes'))
            continue
        if cur['sha'] != t['sha_installed']:
            refusals.append((t['name'], 'bytes are neither the installed ones nor the originals'))
            continue
        if t['existed']:
            ops.append(dict(op='restore', name=t['name'], dst=t['dst'], backup=t['backup'],
                            mode=t['mode_before'], uid=t['uid_before'], gid=t['gid_before'], via_sudo=t['install_via_sudo']))
        else:
            ops.append(dict(op='remove', name=t['name'], dst=t['dst'], via_sudo=t['install_via_sudo']))
    if refusals:
        raise RollbackRefused('; '.join('%s: %s' % r for r in refusals))
    level = 'none'
    for o in ops:
        lvl = next(x['level'] for x in TARGETS if x['dst'] == o['dst'])
        if LEVELS.index(lvl) > LEVELS.index(level):
            level = lvl
    return {'ops': ops, 'noops': noops, 'level': level}


def audio_restore_ops(sink_mute_before, level, levels_before, levels_after):
    """Only ever preserves: the sink mute returns to what it was, and after a full stack restart
    the speaker/microphone levels return to `levels_before` if they drifted. The runner passes the
    levels recorded on this device at install, or before any record the pre-apply ones. Never
    unmutes a microphone or the browser, never sets any other level."""
    ops = []
    if level == 'audio-stack' and levels_before:
        if levels_after.get('speaker') != levels_before.get('speaker'):
            ops.append(('pactl', 'set-sink-volume', 'SINK', levels_before['speaker']))
        if levels_after.get('microphone') != levels_before.get('microphone'):
            ops.append(('pactl', 'set-source-volume', 'RAW', levels_before['microphone']))
    if sink_mute_before is False:
        ops.append(('pactl', 'set-sink-mute', 'SINK', '0'))
    return ops


# ---------------------------------------------------------------- verification (pure) --------

def verify(obs, manifest=None):
    """obs: observations gathered read-only by the runner. Returns list of (check, ok, detail)."""
    out = []
    def add(name, ok, detail=''):
        out.append((name, bool(ok), detail))

    rr = [l for l in obs.get('threads', []) if ' RR ' in l and ' 20 ' in l]
    comms = obs.get('rt_comms', [])
    add('rtkit.four-data-loops-RR20', len(rr) >= 4 and {'pipewire', 'pipewire-pulse', 'wireplumber', 'pw-cli'} <= set(comms), '%d RR20 loops: %s' % (len(rr), sorted(set(comms))))
    add('rtkit.polkit-authorized', obs.get('pkcheck_rc') == 0, 'pkcheck rc=%r' % obs.get('pkcheck_rc'))
    add('graph.force-quantum-960', obs.get('force_quantum') == EXPECTED['quantum'], 'clock.force-quantum=%r' % obs.get('force_quantum'))
    nodes = obs.get('nodes', {})
    for n in ('astral_aec_capture', 'astral_aec_reference', 'astral_echo_cancel'):
        p = nodes.get(n, {})
        add('aec.%s.latency-960-running' % n, p.get('node.latency') == EXPECTED['latency'] and p.get('state') == 'running', json.dumps({k: p.get(k) for k in ('node.latency', 'state')}))
    for n, pos in (('alsa_output.platform-soc_sound.pro-output-0', '[ FL FR ]'), ('alsa_input.platform-soc_sound.pro-input-0', 'AUX0,AUX1')):
        p = nodes.get(n, {})
        add('hat.%s.no-link-group' % n.split('.')[-1], p and 'node.link-group' not in p, 'link-group=%r' % p.get('node.link-group'))
        add('hat.%s.headroom-1024' % n.split('.')[-1], p.get('api.alsa.headroom') == '1024', 'headroom=%r' % p.get('api.alsa.headroom'))
        add('hat.%s.position' % n.split('.')[-1], p.get('audio.position') == pos, 'position=%r' % p.get('audio.position'))
    links = set(tuple(l) for l in obs.get('links', []))
    for a, b in (('alsa_output.platform-soc_sound.pro-output-0:monitor_FL', 'astral_aec_reference:input_FL'),
                 ('alsa_output.platform-soc_sound.pro-output-0:monitor_FR', 'astral_aec_reference:input_FR'),
                 ('alsa_input.platform-soc_sound.pro-input-0:capture_AUX0', 'astral_aec_capture:input_FL'),
                 ('alsa_input.platform-soc_sound.pro-input-0:capture_AUX1', 'astral_aec_capture:input_FR')):
        add('link.' + b, (a, b) in links, '%s -> %s' % (a, b))
    hub = obs.get('hub', {})
    add('hub.requires-astral-aec', 'astral-aec.service' in hub.get('Requires', ''), hub.get('Requires', ''))
    add('hub.after-astral-aec', 'astral-aec.service' in hub.get('After', ''), hub.get('After', ''))
    env = hub.get('Environment', '')
    add('hub.env-aec-source', 'ASTRAL_MIC_AEC=1' in env and 'ASTRAL_MIC_SOURCE=astral_echo_cancel' in env, env)
    caps = obs.get('captures', [])
    hubcap = [c for c in caps if c.get('binary') == 'pacat' and c.get('target') == 'astral_echo_cancel']
    add('capture.one-hub-capture-on-aec', len(hubcap) == 1, '%d hub captures' % len(hubcap))
    add('capture.no-browser-capture', not any(c.get('binary') == 'chromium' for c in caps), 'chromium captures: %d' % sum(1 for c in caps if c.get('binary') == 'chromium'))
    vol = obs.get('volumes', {})
    recorded = (obs.get('recorded_levels') or {}).get('levels')
    if recorded:
        for which in ('speaker', 'microphone'):
            add('levels.%s-as-installed' % which, vol.get(which) == recorded.get(which),
                '%s=%r, recorded at install %r' % (which, vol.get(which), recorded.get(which)))
    else:
        add('info.levels', True, 'speaker=%r microphone=%r; none recorded yet (the first apply records them)'
            % (vol.get('speaker'), vol.get('microphone')))
    for svc in ('astral-aec', 'astral-hub', 'wireplumber', 'pipewire'):
        add('service.%s.active' % svc, obs.get('active', {}).get(svc) == 'active', obs.get('active', {}).get(svc))
    # the running WirePlumber and AEC unit were started no earlier than their config files were written
    for name, start_key, mtime_key, wall_key in (
            ('wireplumber.started-after-rules', 'wireplumber_start_ts', 'wireplumber_rules_mtime', 'wireplumber_start_wall'),
            ('aec.started-after-dropins', 'aec_start_ts', 'aec_dropins_mtime', 'aec_start_wall')):
        start, mtime = obs.get(start_key), obs.get(mtime_key)
        ok = start is not None and mtime is not None and start >= mtime - START_AFTER_WRITE_TOLERANCE
        add(name, ok, 'start=%r (%s) config_mtime=%r; strict, no slack' % (start, obs.get(wall_key, '?'), mtime))
    if manifest:
        for t in manifest:
            cur = obs.get('files', {}).get(t['dst'])
            add('file.' + t['name'], cur == t['sha'], 'device sha %s' % (cur or 'missing'))
    # informational, never changed by the runner
    out.append(('info.sink-mute', True, 'sink mute=%r (not changed by this tool)' % obs.get('sink_mute')))
    out.append(('info.source-mutes', True, 'raw=%r aec=%r (not changed by this tool)' % (obs.get('raw_mute'), obs.get('aec_mute'))))
    return out
