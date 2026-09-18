#!/usr/bin/env python3
"""Durable installer for the current openhome audio runtime. Self-contained; runs on the device
as openhome from any checkout path.

  plan      read-only: which of the seven targets differ and what restart level that implies
  verify    read-only: actual runtime properties (RT loops, quantum, block, links, hub deps, levels)
  apply     install differing targets with a backup, restart only the level the diff requires
  rollback  <backup-dir>: restore the backed-up state, same restart rule

Never unmutes a microphone or the browser, never changes a level except, after a full stack
restart, to return it to the levels recorded on this device when the runtime was installed (the
first apply records them in the backup root; before that, the pre-apply ones). The sink mute is
returned to what it was. If nothing differs, apply makes no change and no restart.
"""
import argparse, fcntl, json, os, pwd, shutil, socket, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_runtime as ar

CANDIDATE = Path(__file__).resolve().parent
DEFAULT_BACKUP_ROOT = Path(ar.HOME) / 'astral-voice/platform-hardening/audio-runtime-backups'
DEFAULT_ROOM_LOCK = Path(ar.HOME) / 'astral-voice/platform-hardening/.acoustic-calibration.lock'


def run(argv, check=True, timeout=60):
    p = subprocess.run([str(x) for x in argv], capture_output=True, timeout=timeout)
    out = p.stdout.decode('utf-8', errors='replace'); err = p.stderr.decode('utf-8', errors='replace')
    if check and p.returncode:
        raise RuntimeError('Command failed: %s %s' % (argv[:5], err[:400]))
    return subprocess.CompletedProcess(argv, p.returncode, out, err)


def ctl(scope, *args, check=True):
    return run((['systemctl', '--user'] if scope == 'user' else ['sudo', '-n', 'systemctl']) + list(args), check=check)


class DeviceAudio:
    """The minimal pause/state helper the installer needs. Mirrors the device's established
    paused shape: sink muted, both microphones muted, Chromium output streams muted."""
    SINK = 'alsa_output.platform-soc_sound.pro-output-0'
    RAW = 'alsa_input.platform-soc_sound.pro-input-0'
    AEC = 'astral_echo_cancel'

    def audio(self, kind):
        return json.loads(run(['pactl', '--format=json', 'list', kind]).stdout)

    def state(self):
        keys = ['index', 'name', 'mute', 'volume', 'source', 'sink']
        out = {}
        for kind in ('sinks', 'sources', 'sink-inputs', 'source-outputs'):
            rows = []
            for v in self.audio(kind):
                props = v.get('properties') or {}
                rows.append({k: v.get(k) for k in keys} | {'binary': props.get('application.process.binary'),
                                                          'target': props.get('target.object'), 'app': props.get('application.name')})
            out[kind] = rows
        return out

    def pause(self):
        run(['pactl', 'set-sink-mute', self.SINK, '1'])
        run(['pactl', 'set-source-mute', self.RAW, '1'])
        run(['pactl', 'set-source-mute', self.AEC, '1'], check=False)
        for x in self.audio('sink-inputs'):
            if (x.get('properties') or {}).get('application.process.binary') == 'chromium':
                run(['pactl', 'set-sink-input-mute', str(x['index']), '1'])

    def wait_browser(self, seconds=150):
        """After the kiosk is started: its output stream exists and it holds no microphone."""
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.pause()
            try:
                outs = [x for x in self.audio('sink-inputs') if (x.get('properties') or {}).get('application.process.binary') == 'chromium']
                caps = [x for x in self.audio('source-outputs') if (x.get('properties') or {}).get('application.process.binary') == 'chromium']
                if outs and not caps:
                    return
            except Exception:
                pass
            time.sleep(2)
        raise RuntimeError('Browser output did not appear (or it holds a microphone)')

    def levels(self, st=None):
        st = st or self.state()
        sink = next(x for x in st['sinks'] if x['name'] == self.SINK)
        raw = next(x for x in st['sources'] if x['name'] == self.RAW)
        return {'speaker': sink['volume']['front-left']['value_percent'], 'microphone': raw['volume']['aux0']['value_percent'],
                'sink_mute': sink['mute']}


def file_state(dst, via_sudo):
    """exists, sha256 and the ACTUAL mode/uid/gid of the file as found (None when absent)."""
    absent = {'exists': False, 'sha': None, 'mode': None, 'uid': None, 'gid': None}
    if via_sudo and dst.startswith('/etc/'):
        p = run(['sudo', '-n', 'sha256sum', dst], check=False)
        if p.returncode:
            return absent
        st = run(['sudo', '-n', 'stat', '-c', '%a %u %g', dst]).stdout.split()
        return {'exists': True, 'sha': p.stdout.split()[0], 'mode': st[0], 'uid': int(st[1]), 'gid': int(st[2])}
    path = Path(dst)
    if not path.exists():
        return absent
    st = path.stat()
    return {'exists': True, 'sha': ar.sha_bytes(path.read_bytes()), 'mode': '%o' % (st.st_mode & 0o7777), 'uid': st.st_uid, 'gid': st.st_gid}


def current_state(manifest):
    return {t['dst']: file_state(t['dst'], t.get('install_via_sudo')) for t in manifest}


def read_levels_record(backup_root):
    """The levels recorded on this device at install, or None before the first apply."""
    record = Path(backup_root) / ar.LEVELS_RECORD
    return json.loads(record.read_text()) if record.exists() else None


def gather_facts(args):
    env = {}
    envfile = Path(ar.HOME) / '.env'
    if envfile.exists():
        for line in envfile.read_text(errors='replace').splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                if k in ('SPEAKER_VOLUME', 'MIC_SENSITIVITY'):
                    env[k] = v.strip()
    def ver(cmd):
        p = run([cmd, '--version'], check=False)
        for line in (p.stdout + p.stderr).splitlines():
            if 'Compiled with' in line:
                return line.split()[-1]
        return ''
    room_running = False
    lock = Path(args.room_lock)
    if lock.exists():
        try:
            with lock.open('a') as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(f, fcntl.LOCK_UN)
                except BlockingIOError:
                    room_running = True
        except OSError:
            pass
    backup_root = Path(args.backup_root)
    try:
        backup_root.mkdir(parents=True, exist_ok=True, mode=0o700); writable = os.access(backup_root, os.W_OK)
    except OSError:
        writable = False
    return {
        'hostname': socket.gethostname(),
        'asound_cards': Path('/proc/asound/cards').read_text(errors='replace') if Path('/proc/asound/cards').exists() else '',
        'pipewire_version': ver('pipewire'), 'wireplumber_version': ver('wireplumber'),
        'aec_webrtc_plugin': bool(list(Path('/usr/lib').glob('*/spa-0.2/aec/libspa-aec-webrtc.so'))),
        'system_active': {u: run(['systemctl', 'is-active', u], check=False).stdout.strip() for u in ('rtkit-daemon', 'polkit')},
        'user': pwd.getpwuid(os.getuid()).pw_name,
        'sudo_noninteractive': run(['sudo', '-n', 'true'], check=False).returncode == 0,
        'backup_root_writable': writable,
        'env_levels': env,
        'hub_unit_present': (Path(ar.HOME) / '.config/systemd/user/astral-hub.service').exists(),
        'room_test_running': room_running,
        'recorded_levels': read_levels_record(args.backup_root),
        'levels_record_path': str(Path(args.backup_root) / ar.LEVELS_RECORD),
        'service_states': {n: {'active': ctl('user', 'is-active', n, check=False).stdout.strip(),
                               'enabled': ctl('user', 'is-enabled', n, check=False).stdout.strip()}
                           for n in ('astral-aec', 'astral-hub', 'openhome-dashboard', 'wireplumber', 'pipewire', 'pipewire-pulse')},
    }


def links():
    pairs, current = [], None
    for line in run(['pw-link', '-l'], check=False).stdout.splitlines():
        if not line.startswith(' '):
            current = line.strip()
        elif '|->' in line and current:
            pairs.append((current, line.split('|->', 1)[1].strip()))
    return pairs


def observe(d, manifest, recorded_levels=None):
    threads = [l for l in run(['ps', '-eLo', 'pid,tid,user,cls,rtprio,comm']).stdout.splitlines() if 'openhome' in l and 'data-loop' in l]
    rt_comms = []
    for l in threads:
        if ' RR ' in l:
            rt_comms.append(run(['ps', '-o', 'comm=', '-p', l.split()[0]], check=False).stdout.strip())
    pipewire_pid = ctl('user', 'show', 'pipewire', '-p', 'MainPID', '--value').stdout.strip()
    meta = run(['pw-metadata', '-n', 'settings'], check=False).stdout
    fq = next((l.split("value:'")[1].split("'")[0] for l in meta.splitlines() if 'clock.force-quantum' in l and "value:'" in l), None)
    st = d.state()
    lv = d.levels(st)
    aec = next((x for x in st['sources'] if x['name'] == d.AEC), {})
    raw = next(x for x in st['sources'] if x['name'] == d.RAW)
    hub = {key: ctl('user', 'show', 'astral-hub', '-p', key, '--value').stdout.strip() for key in ('Requires', 'After', 'Environment')}
    def start_ts(unit):
        v = ctl('user', 'show', unit, '-p', 'ExecMainStartTimestampMonotonic', '--value').stdout.strip()
        return int(v) / 1e6 if v.isdigit() else None
    def start_wall(unit):
        return ctl('user', 'show', unit, '-p', 'ExecMainStartTimestamp', '--value').stdout.strip()
    boot_offset = time.time() - time.monotonic()   # CLOCK_MONOTONIC -> wall clock, the base systemd reports
    def newest_mtime(paths):
        existing = [p for p in paths if p.exists()]
        return max(p.stat().st_mtime for p in existing) if existing else None
    rules = [Path(t['dst']) for t in manifest if t['level'] == 'wireplumber']
    dropins = [Path(t['dst']) for t in manifest if t['level'] == 'aec']
    pw = subprocess.run(['pw-dump'], capture_output=True, timeout=20)
    wp_start, aec_start = start_ts('wireplumber'), start_ts('astral-aec')
    return {
        'threads': threads, 'rt_comms': rt_comms,
        'pkcheck_rc': run(['pkcheck', '--action-id', 'org.freedesktop.RealtimeKit1.acquire-real-time', '--process', pipewire_pid], check=False).returncode,
        'force_quantum': fq, 'nodes': ar.parse_pw_dump(pw.stdout), 'links': links(), 'hub': hub,
        'captures': [{'binary': x['binary'], 'target': x['target']} for x in st['source-outputs']],
        'volumes': {'speaker': lv['speaker'], 'microphone': lv['microphone']},
        'sink_mute': lv['sink_mute'], 'raw_mute': raw['mute'], 'aec_mute': aec.get('mute'),
        'active': {n: ctl('user', 'is-active', n, check=False).stdout.strip() for n in ('astral-aec', 'astral-hub', 'wireplumber', 'pipewire')},
        'wireplumber_start_ts': None if wp_start is None else wp_start + boot_offset, 'wireplumber_rules_mtime': newest_mtime(rules),
        'aec_start_ts': None if aec_start is None else aec_start + boot_offset, 'aec_dropins_mtime': newest_mtime(dropins),
        'wireplumber_start_wall': start_wall('wireplumber'), 'aec_start_wall': start_wall('astral-aec'),
        'files': {t['dst']: file_state(t['dst'], t.get('install_via_sudo'))['sha'] for t in manifest},
        'recorded_levels': recorded_levels,
    }


def install_file(t, src: Path):
    """Install candidate bytes with the template's mode/owner (apply)."""
    if t.get('install_via_sudo'):
        run(['sudo', '-n', 'install', '-D', '-m', t['mode'], '-o', t['owner'], '-g', t['owner'], str(src), t['dst']])
    else:
        dst = Path(t['dst']); dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + '.tmp-audio-runtime')
        tmp.write_bytes(src.read_bytes()); os.chmod(tmp, int(t['mode'], 8)); os.replace(tmp, dst)


def restore_file(op, src: Path):
    """Put the backed-up bytes back with the mode/uid/gid recorded from the actual pre-state."""
    mode = op.get('mode') or '644'
    uid, gid = op.get('uid'), op.get('gid')
    if op.get('via_sudo') or (uid is not None and uid != os.getuid()):
        run(['sudo', '-n', 'install', '-D', '-m', mode, '-o', str(uid if uid is not None else os.getuid()),
             '-g', str(gid if gid is not None else os.getgid()), str(src), op['dst']])
    else:
        dst = Path(op['dst']); dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + '.tmp-audio-runtime')
        tmp.write_bytes(src.read_bytes()); os.chmod(tmp, int(mode, 8)); os.replace(tmp, dst)


def wait_ready(d, level):
    def until(seconds, pred, what):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            try:
                if pred():
                    return
            except Exception:
                pass
            time.sleep(.5)
        raise RuntimeError(what)
    if level in ('audio-stack', 'wireplumber'):
        until(25, lambda: any(x.get('name') == d.RAW for x in d.audio('sources')), 'HAT audio did not return')
    if level in ('audio-stack', 'wireplumber', 'aec'):
        until(20, lambda: any(x.get('name') == d.AEC for x in d.audio('sources')), 'AEC source did not return')
    if level == 'audio-stack':
        d.pause(); d.wait_browser()
    def hub_ready():
        d.pause(); s = d.state()
        caps = [x for x in s['source-outputs'] if x['binary'] == 'pacat']
        return len(caps) == 1 and caps[0]['target'] == d.AEC and not any(x['binary'] != 'chromium' for x in s['sink-inputs'])
    until(75, hub_ready, 'Hub not ready after restart')


def do_restart(d, level, before, report, recorded_levels=None):
    seq = ar.restart_sequence(level)
    report['restart'] = {'level': level, 'sequence': seq}
    if not seq:
        return
    d.pause()
    for step in seq:
        ctl(*step)
    wait_ready(d, level)
    after = d.levels()
    target = (recorded_levels or {}).get('levels') or {'speaker': before['speaker'], 'microphone': before['microphone']}
    ops = ar.audio_restore_ops(before['sink_mute'], level, target,
                               {'speaker': after['speaker'], 'microphone': after['microphone']})
    report['audio_restore_ops'] = ops
    for op in ops:
        run([a.replace('SINK', d.SINK).replace('RAW', d.RAW) for a in op])


def cmd_plan(args, manifest):
    p = ar.plan(manifest, current_state(manifest))
    print(json.dumps(p, indent=2)); return 0 if not p['changes'] else 3


def cmd_verify(args, manifest):
    results = ar.verify(observe(DeviceAudio(), manifest, read_levels_record(args.backup_root)), manifest)
    ok = all(r[1] for r in results)
    for name, good, detail in results:
        print('%s %s %s' % ('PASS' if good else 'FAIL', name, detail))
    report_dir = Path(args.report_dir); report_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    out = report_dir / ('audio-runtime-verify-%s.json' % time.strftime('%Y%m%d-%H%M%S'))
    out.write_text(json.dumps({'at': time.time(), 'ok': ok, 'results': results}, indent=2))
    print(json.dumps({'ok': ok, 'failed': [r[0] for r in results if not r[1]], 'report': str(out)})); return 0 if ok else 4


def settle_audio(d, sink_mute_before, report, reason):
    """The final audio shape after an error: the paused shape (microphones and browser muted)
    with the sink mute returned to its pre-transaction value. Never unmutes a microphone."""
    try:
        d.pause()
        for op in ar.audio_restore_ops(sink_mute_before, 'none', None, None):
            run([a.replace('SINK', d.SINK).replace('RAW', d.RAW) for a in op])
        report['audio_final'] = {'paused': True, 'sink_mute': sink_mute_before, 'reason': reason}
    except Exception as e:
        report['audio_final'] = {'error': type(e).__name__ + ': ' + str(e)[:200], 'reason': reason}


def warn(warnings):
    for w in warnings:
        print('warning: ' + w, file=sys.stderr)
    return warnings


def cmd_apply(args, manifest):
    facts = gather_facts(args); warnings = warn(ar.check_preconditions(facts))
    d = DeviceAudio()
    if facts['recorded_levels'] is None:
        # The first apply on this device records its levels; later runs are held to them.
        facts['recorded_levels'] = ar.levels_record(facts['env_levels'], d.levels(),
                                                    time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        Path(facts['levels_record_path']).write_text(json.dumps(facts['recorded_levels'], indent=2))
    current = current_state(manifest)
    p = ar.plan(manifest, current)
    if not p['changes']:
        print(json.dumps({'applied': False, 'reason': 'already configured', 'unchanged': p['unchanged'], 'restart': 'none'}))
        return 0
    before_state = d.state(); before = d.levels(before_state)
    backup = Path(args.backup_root) / ('rollback-' + time.strftime('%Y%m%d-%H%M%S')); backup.mkdir(mode=0o700)
    meta = ar.backup_meta(manifest, current, facts, {'state': before_state, 'sink_mute': before['sink_mute'],
                                                     'levels': {'speaker': before['speaker'], 'microphone': before['microphone']}}, p)
    for t in meta['targets']:
        if t['existed']:
            if t['install_via_sudo'] and t['dst'].startswith('/etc/'):
                (backup / t['backup']).write_bytes(subprocess.run(['sudo', '-n', 'cat', t['dst']], capture_output=True, check=True).stdout)
            else:
                shutil.copy2(t['dst'], backup / t['backup'])
    meta['plan'] = p; meta['candidate'] = str(CANDIDATE); meta['at'] = time.time()
    def save_meta():
        (backup / 'meta.json').write_text(json.dumps(meta, indent=2))
    save_meta()
    report = {'backup': str(backup), 'plan': p, 'installed': [], 'warnings': warnings}
    try:
        d.pause()                                    # before the first byte changes; polkit reloads on write
        report['paused_before_write'] = True
        for ch in p['changes']:
            t = next(x for x in manifest if x['name'] == ch['name'])
            install_file(t, CANDIDATE / 'files' / t['src'])
            ar.mark_installed(meta, ch['name']); save_meta()
            report['installed'].append(ch['name'])
        after = current_state(manifest)
        bad = [t['name'] for t in manifest if after[t['dst']]['sha'] != t['sha']]
        if bad:
            raise RuntimeError('Installed bytes do not match candidate: %s' % bad)
        if not args.no_restart:
            do_restart(d, p['level'], before, report, facts['recorded_levels'])
        else:
            report['restart'] = {'level': p['level'], 'sequence': [], 'deferred': True}
            for op in ar.audio_restore_ops(before['sink_mute'], 'none', None, None):
                run([a.replace('SINK', d.SINK).replace('RAW', d.RAW) for a in op])
        report['verify'] = ar.verify(observe(d, manifest, facts['recorded_levels']), manifest)
        report['ok'] = all(r[1] for r in report['verify'])
        report['applied'] = True
    except Exception as e:
        report['error'] = type(e).__name__ + ': ' + str(e)[:500]; report['applied'] = False
        settle_audio(d, before['sink_mute'], report, 'apply failed')
    (backup / 'apply-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report.get(k) for k in ('applied', 'ok', 'error', 'installed', 'backup', 'audio_final')} | {'restart': report.get('restart', {}).get('level')}))
    return 0 if report.get('applied') and report.get('ok') else 5


def cmd_rollback(args, manifest):
    facts = gather_facts(args); warn(ar.check_preconditions(facts))   # the same guard as apply: no room test, sane host
    backup = Path(args.backup)
    meta = json.loads((backup / 'meta.json').read_text())
    state_path = backup / 'rollback-state.json'
    done = set(json.loads(state_path.read_text()).get('done', [])) if state_path.exists() else set()
    d = DeviceAudio()
    rp = ar.rollback_plan(meta, current_state(manifest), done)     # raises RollbackRefused: nothing is touched
    report = {'backup': str(backup), 'rollback_plan': rp, 'done': []}
    before = d.levels()
    if not rp['ops']:
        report['restored'] = True; report['reason'] = 'nothing to roll back'
        (backup / 'rollback-report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps({'restored': True, 'reason': report['reason'], 'noops': rp['noops']})); return 0
    try:
        d.pause()                                    # before any file returns to its old bytes
        report['paused_before_write'] = True
        for op in rp['ops']:
            if op['op'] == 'restore':
                restore_file(op, backup / op['backup'])
            else:
                run(['sudo', '-n', 'rm', '--', op['dst']] if op['via_sudo'] else ['rm', '--', op['dst']])
            done.add(op['name']); state_path.write_text(json.dumps({'done': sorted(done)}))
            report['done'].append(op)
        do_restart(d, rp['level'], before, report, facts['recorded_levels'])
        report['restored'] = True
    except Exception as e:
        report['error'] = type(e).__name__ + ': ' + str(e)[:500]; report['restored'] = False
        settle_audio(d, before['sink_mute'], report, 'rollback failed')
    (backup / 'rollback-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report.get(k) for k in ('restored', 'error', 'audio_final')} | {'level': rp['level'], 'noops': rp['noops']}))
    return 0 if report.get('restored') else 6


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--backup-root', default=str(DEFAULT_BACKUP_ROOT), help='where rollback-<ts>/ directories are created')
    ap.add_argument('--report-dir', default=None, help='where verify reports are written (default: backup root)')
    ap.add_argument('--room-lock', default=str(DEFAULT_ROOM_LOCK), help='a held flock here means a room test is running; only checked if the file exists')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('plan'); sub.add_parser('verify')
    a = sub.add_parser('apply'); a.add_argument('--no-restart', action='store_true', help='install files only; the restart level is reported, not executed')
    r = sub.add_parser('rollback'); r.add_argument('backup')
    args = ap.parse_args()
    args.report_dir = args.report_dir or args.backup_root
    manifest = ar.load_manifest(CANDIDATE)
    if args.cmd in ('apply', 'rollback'):
        os.umask(0o077)
        Path(args.backup_root).mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = (Path(args.backup_root) / '.audio-runtime.lock').open('a')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('another audio-runtime apply/rollback is running'); return 2
    return {'plan': cmd_plan, 'verify': cmd_verify, 'apply': cmd_apply, 'rollback': cmd_rollback}[args.cmd](args, manifest)


if __name__ == '__main__':
    sys.exit(main())
