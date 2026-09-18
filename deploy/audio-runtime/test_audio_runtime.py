#!/usr/bin/env python3
"""Desk tests for the audio runtime candidate. No device, no subprocess, no audio.

They prove properties of the plan/backup/rollback/verify logic against fake facts and fake
file states, and the self-consistency of the packaged bytes. They do not mirror strings from
the implementation: every expectation is an observable outcome (which files change, which
restart level results, what a rollback would do, which runtime property fails a check)."""
import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_runtime as ar

HERE = Path(__file__).resolve().parent
MANIFEST = ar.load_manifest(HERE)
BY_NAME = {t['name']: t for t in MANIFEST}


def configured():
    """Device state in which every target already carries the candidate bytes."""
    return {t['dst']: {'exists': True, 'sha': t['sha'], 'mode': t['mode'], 'uid': 0 if t['owner'] == 'root' else 1000, 'gid': 0 if t['owner'] == 'root' else 1000} for t in MANIFEST}


def absent():
    return {'exists': False, 'sha': None, 'mode': None, 'uid': None, 'gid': None}


class FakeSystemd:
    """A stateful user manager: restart of a unit does NOT touch its dependents, so a sequence
    that relies on Requires= propagation ends with the hub down."""
    def __init__(self, active=('astral-hub', 'astral-aec', 'wireplumber', 'pipewire', 'pipewire-pulse', 'openhome-dashboard')):
        self.state = {u: 'active' for u in active}; self.log = []
    def ctl(self, scope, verb, *units):
        self.log.append((verb,) + units)
        for u in units:
            if verb in ('stop',): self.state[u] = 'inactive'
            elif verb in ('start',): self.state[u] = 'active'
            elif verb == 'restart': self.state[u] = 'active'      # only this unit
    def run(self, seq):
        for step in seq:
            self.ctl(*step)
        return self


# Any device's own levels: nothing below depends on particular numbers.
SAVED = {'SPEAKER_VOLUME': '40', 'MIC_SENSITIVITY': '120'}
LIVE = {'speaker': '40%', 'microphone': '120%'}


def good_facts():
    return {'hostname': 'openhome', 'asound_cards': ' 2 [sndrpigooglevoi]: RPi-simple - snd_rpi_googlevoicehat_soundcar',
            'pipewire_version': '1.4.2', 'wireplumber_version': '0.5.8', 'aec_webrtc_plugin': True,
            'system_active': {'rtkit-daemon': 'active', 'polkit': 'active'}, 'user': 'openhome',
            'sudo_noninteractive': True, 'backup_root_writable': True,
            'env_levels': dict(SAVED), 'recorded_levels': ar.levels_record(SAVED, LIVE, 'fixture'),
            'levels_record_path': '/backups/' + ar.LEVELS_RECORD, 'hub_unit_present': True,
            'room_test_running': False, 'service_states': {}}


def good_obs():
    nodes = {n: {'node.latency': '960/48000', 'state': 'running'} for n in ('astral_aec_capture', 'astral_aec_reference', 'astral_echo_cancel')}
    nodes['alsa_output.platform-soc_sound.pro-output-0'] = {'api.alsa.headroom': '1024', 'audio.position': '[ FL FR ]', 'node.group': 'pro-audio-2'}
    nodes['alsa_input.platform-soc_sound.pro-input-0'] = {'api.alsa.headroom': '1024', 'audio.position': 'AUX0,AUX1', 'node.group': 'pro-audio-2'}
    return {
        'threads': ['  1 2 openhome  RR     20 data-loop.0'] * 4, 'rt_comms': ['pipewire', 'wireplumber', 'pipewire-pulse', 'pw-cli'],
        'pkcheck_rc': 0, 'force_quantum': '960', 'nodes': nodes,
        'links': [('alsa_output.platform-soc_sound.pro-output-0:monitor_FL', 'astral_aec_reference:input_FL'),
                  ('alsa_output.platform-soc_sound.pro-output-0:monitor_FR', 'astral_aec_reference:input_FR'),
                  ('alsa_input.platform-soc_sound.pro-input-0:capture_AUX0', 'astral_aec_capture:input_FL'),
                  ('alsa_input.platform-soc_sound.pro-input-0:capture_AUX1', 'astral_aec_capture:input_FR')],
        'hub': {'Requires': 'app.slice basic.target astral-aec.service', 'After': 'astral-aec.service basic.target pipewire.service',
                'Environment': 'PATH=/x ASTRAL_MIC_SOURCE=astral_echo_cancel ASTRAL_MIC_AEC=1'},
        'captures': [{'binary': 'pacat', 'target': 'astral_echo_cancel'}],
        'volumes': dict(LIVE), 'recorded_levels': ar.levels_record(SAVED, LIVE, 'fixture'),
        'sink_mute': False, 'raw_mute': True, 'aec_mute': True,
        'active': {n: 'active' for n in ('astral-aec', 'astral-hub', 'wireplumber', 'pipewire')},
        'wireplumber_start_ts': 200.0, 'wireplumber_rules_mtime': 100.0, 'aec_start_ts': 300.0, 'aec_dropins_mtime': 100.0,
        'files': {t['dst']: t['sha'] for t in MANIFEST},
    }


def failing(results):
    return sorted(name for name, ok, _ in results if not ok)


class Package(unittest.TestCase):
    def test_seven_targets_and_bytes_are_self_consistent(self):
        self.assertEqual(len(MANIFEST), 7)
        for t in MANIFEST:
            self.assertEqual(ar.sha_bytes((HERE / 'files' / t['src']).read_bytes()), t['sha'])
            self.assertGreater(t['size'], 0)
        self.assertEqual(sum(1 for t in MANIFEST if t['owner'] == 'root'), 1)

    def test_packaged_bytes_carry_the_measured_properties(self):
        # properties the device review measured, read from the bytes rather than from the code
        block = (HERE / 'files' / BY_NAME['40-aec-block.conf']['src']).read_text()
        self.assertIn('node.latency=960/48000', block); self.assertIn('monitor.mode=true', block)
        self.assertIn('target.object=alsa_output.platform-soc_sound.pro-output-0', block)
        timing = (HERE / 'files' / BY_NAME['30-graph-timing.conf']['src']).read_text()
        self.assertIn('clock.force-quantum 960', timing); self.assertIn('ExecStopPost', timing)
        hat = (HERE / 'files' / BY_NAME['51-astral-voicehat-headroom.conf']['src']).read_text()
        self.assertIn('node.link-group = null', hat); self.assertIn('api.alsa.headroom = 1024', hat); self.assertIn('[ FL FR ]', hat)
        browser = (HERE / 'files' / BY_NAME['52-astral-browser-state.conf']['src']).read_text()
        self.assertIn('state.restore-props = false', browser); self.assertIn('Stream/Output/Audio', browser)
        self.assertNotIn('Stream/Input', browser)                     # capture streams keep their state
        hub = (HERE / 'files' / BY_NAME['20-single-router.conf']['src']).read_text()
        self.assertIn('Requires=astral-aec.service', hub); self.assertIn('After=astral-aec.service', hub)
        self.assertIn('ASTRAL_MIC_AEC=1', hub); self.assertIn('ASTRAL_MIC_SOURCE=astral_echo_cancel', hub)
        rule = (HERE / 'files' / BY_NAME['49-openhome-rtkit.rules']['src']).read_text()
        self.assertIn('subject.user == "openhome"', rule)
        for action in ('acquire-real-time', 'acquire-high-priority'):
            self.assertIn(action, rule)
        self.assertNotIn('lightdm', rule)


class Plan(unittest.TestCase):
    def test_configured_device_needs_nothing(self):
        p = ar.plan(MANIFEST, configured())
        self.assertEqual(p['changes'], []); self.assertEqual(p['level'], 'none')
        self.assertEqual(ar.restart_sequence('none'), [])

    def test_restart_level_follows_the_most_demanding_change(self):
        cases = {'20-single-router.conf': 'hub', '40-aec-block.conf': 'aec', '30-graph-timing.conf': 'aec',
                 'astral-aec.service': 'aec', '52-astral-browser-state.conf': 'wireplumber',
                 '51-astral-voicehat-headroom.conf': 'wireplumber', '49-openhome-rtkit.rules': 'audio-stack'}
        for name, level in cases.items():
            cur = configured(); cur[BY_NAME[name]['dst']] = {'exists': True, 'sha': 'deadbeef'}
            p = ar.plan(MANIFEST, cur)
            self.assertEqual([c['name'] for c in p['changes']], [name]); self.assertEqual(p['level'], level, name)
        cur = configured()
        cur[BY_NAME['20-single-router.conf']['dst']] = {'exists': False, 'sha': None}
        cur[BY_NAME['52-astral-browser-state.conf']['dst']] = {'exists': False, 'sha': None}
        self.assertEqual(ar.plan(MANIFEST, cur)['level'], 'wireplumber')

    def test_every_level_ends_with_the_hub_up_on_a_manager_without_dependent_propagation(self):
        for level in ('hub', 'aec', 'wireplumber', 'audio-stack'):
            sd = FakeSystemd().run(ar.restart_sequence(level))
            self.assertEqual(sd.state['astral-hub'], 'active', level)
            self.assertEqual(sd.state['astral-aec'], 'active', level)
            if level != 'hub':
                stops = [i for i, e in enumerate(sd.log) if e[0] == 'stop' and 'astral-hub' in e]
                aec = [i for i, e in enumerate(sd.log) if e[0] in ('restart', 'start') and 'astral-aec' in e]
                starts = [i for i, e in enumerate(sd.log) if e[0] == 'start' and 'astral-hub' in e]
                self.assertTrue(stops and aec and starts and stops[0] < aec[0] < starts[-1], (level, sd.log))
        # the property the fake enforces: a bare restart of the AEC leaves a dependent hub down
        sd = FakeSystemd().run([('user', 'restart', 'astral-aec')])
        self.assertEqual(sd.state['astral-hub'], 'active')      # it never went down, so it never needed a start
        sd = FakeSystemd().run([('user', 'stop', 'astral-hub'), ('user', 'restart', 'astral-aec')])
        self.assertEqual(sd.state['astral-hub'], 'inactive', 'without an explicit start the hub stays down')

    def test_restart_sequences_keep_the_hub_behind_the_aec(self):
        for level in ('aec', 'wireplumber', 'audio-stack'):
            seq = ar.restart_sequence(level)
            names = [s for s in seq]
            aec_start = max(i for i, s in enumerate(names) if 'astral-aec' in s)
            hub_starts = [i for i, s in enumerate(names) if 'astral-hub' in s and s[1] in ('start', 'restart')]
            self.assertTrue(all(i > aec_start for i in hub_starts), level)
        self.assertIn(('user', 'start', 'astral-hub'), ar.restart_sequence('aec'))
        self.assertIn(('user', 'stop', 'astral-hub'), ar.restart_sequence('aec'))
        stack = ar.restart_sequence('audio-stack')
        self.assertLess(stack.index(('user', 'start', 'pipewire', 'pipewire-pulse', 'wireplumber')), stack.index(('user', 'start', 'astral-aec')))
        self.assertLess(stack.index(('user', 'start', 'astral-aec')), stack.index(('user', 'start', 'astral-hub')))


class Preconditions(unittest.TestCase):
    def test_good_facts_pass(self):
        self.assertEqual(ar.check_preconditions(good_facts()), [])

    def test_each_wrong_fact_aborts(self):
        for key, value in (('asound_cards', ''),
                           ('aec_webrtc_plugin', False), ('user', 'root'), ('sudo_noninteractive', False), ('backup_root_writable', False),
                           ('env_levels', dict(SAVED, SPEAKER_VOLUME='70')), ('hub_unit_present', False), ('room_test_running', True)):
            f = good_facts(); f[key] = value
            with self.assertRaises(ar.PreconditionError, msg=key):
                ar.check_preconditions(f)
        f = good_facts(); f['system_active']['rtkit-daemon'] = 'inactive'
        with self.assertRaises(ar.PreconditionError):
            ar.check_preconditions(f)

    def test_what_it_was_verified_on_is_reported_not_refused(self):
        f = dict(good_facts(), hostname='kitchen', pipewire_version='1.2.7', wireplumber_version='0.4.17')
        warnings = ar.check_preconditions(f)
        self.assertEqual(len(warnings), 3, warnings)
        for word in ('kitchen', '1.2.7', '0.4.17'):
            self.assertTrue(any(word in w for w in warnings), word)

    def test_levels_are_held_to_this_devices_record_never_to_fixed_numbers(self):
        for saved in ({'SPEAKER_VOLUME': '14', 'MIC_SENSITIVITY': '30'}, {'SPEAKER_VOLUME': '50', 'MIC_SENSITIVITY': '160'}, {}):
            f = dict(good_facts(), env_levels=saved, recorded_levels=None)
            self.assertEqual(ar.check_preconditions(f), [], 'before any record, whatever the device has passes')
            f['recorded_levels'] = ar.levels_record(saved, {'speaker': '14%', 'microphone': '30%'}, 'fixture')
            self.assertEqual(ar.check_preconditions(f), [], 'the recorded levels pass')
        f = dict(good_facts(), env_levels={'SPEAKER_VOLUME': '50', 'MIC_SENSITIVITY': '160'})
        with self.assertRaises(ar.PreconditionError) as refused:
            ar.check_preconditions(f)
        self.assertIn(f['levels_record_path'], str(refused.exception), 'the refusal says how to record anew')
        record = ar.levels_record(SAVED, dict(LIVE, sink_mute=False), 'at')
        self.assertEqual(record, {'recorded_at': 'at', 'env_levels': SAVED, 'levels': LIVE})


class Rollback(unittest.TestCase):
    RULE = BY_NAME['49-openhome-rtkit.rules']['dst']; BROWSER = BY_NAME['52-astral-browser-state.conf']['dst']
    HAT = BY_NAME['51-astral-voicehat-headroom.conf']['dst']

    def transaction(self):
        """Before: the polkit rule absent, the browser rule at old bytes with an odd mode/owner,
        everything else already at candidate bytes. Plan writes exactly those two."""
        before = configured()
        before[self.RULE] = absent()
        before[self.BROWSER] = {'exists': True, 'sha': 'oldsha', 'mode': '600', 'uid': 0, 'gid': 0}
        plan = ar.plan(MANIFEST, before)
        meta = ar.backup_meta(MANIFEST, before, good_facts(), {'sink_mute': False, 'levels': {'speaker': '50%', 'microphone': '160%'}}, plan)
        return before, plan, meta

    def test_meta_records_actual_pre_state_and_planned_scope(self):
        before, plan, meta = self.transaction()
        rec = {t['name']: t for t in meta['targets']}
        self.assertEqual(sorted(c['name'] for c in plan['changes']), ['49-openhome-rtkit.rules', '52-astral-browser-state.conf'])
        self.assertFalse(rec['49-openhome-rtkit.rules']['existed']); self.assertTrue(rec['49-openhome-rtkit.rules']['planned'])
        b = rec['52-astral-browser-state.conf']
        self.assertEqual((b['sha_before'], b['mode_before'], b['uid_before'], b['gid_before']), ('oldsha', '600', 0, 0), 'actual metadata, not the template')
        self.assertFalse(rec['51-astral-voicehat-headroom.conf']['planned'])
        self.assertTrue(all(not t['installed'] for t in meta['targets']))

    def test_full_apply_then_rollback_reverses_exactly_the_two_writes_with_recorded_metadata(self):
        before, plan, meta = self.transaction()
        for c in plan['changes']:
            ar.mark_installed(meta, c['name'])
        rp = ar.rollback_plan(meta, configured())
        ops = {o['dst']: o for o in rp['ops']}
        self.assertEqual(set(ops), {self.RULE, self.BROWSER}); self.assertEqual(rp['level'], 'audio-stack')
        self.assertEqual(ops[self.RULE]['op'], 'remove'); self.assertTrue(ops[self.RULE]['via_sudo'])
        r = ops[self.BROWSER]
        self.assertEqual((r['op'], r['mode'], r['uid'], r['gid']), ('restore', '600', 0, 0))
        self.assertIn(('51-astral-voicehat-headroom.conf', 'not written by this transaction'), rp['noops'])

    def test_unplanned_target_changed_by_someone_else_is_left_alone(self):
        before, plan, meta = self.transaction()
        for c in plan['changes']:
            ar.mark_installed(meta, c['name'])
        now = configured(); now[self.HAT] = {'exists': True, 'sha': 'someone-elses-edit', 'mode': '664', 'uid': 1000, 'gid': 1000}
        rp = ar.rollback_plan(meta, now)
        self.assertNotIn(self.HAT, [o['dst'] for o in rp['ops']])
        self.assertIn(('51-astral-voicehat-headroom.conf', 'not written by this transaction'), rp['noops'])

    def test_partial_apply_rolls_back_only_what_was_written(self):
        before, plan, meta = self.transaction()
        ar.mark_installed(meta, '52-astral-browser-state.conf')      # apply died before the polkit rule
        now = configured(); now[self.RULE] = absent()
        rp = ar.rollback_plan(meta, now)
        self.assertEqual([o['dst'] for o in rp['ops']], [self.BROWSER])
        self.assertIn(('49-openhome-rtkit.rules', 'not written by this transaction'), rp['noops'])
        self.assertEqual(rp['level'], 'wireplumber')

    def test_already_at_pre_install_bytes_is_a_noop(self):
        before, plan, meta = self.transaction()
        for c in plan['changes']:
            ar.mark_installed(meta, c['name'])
        now = configured(); now[self.BROWSER] = dict(before[self.BROWSER])
        rp = ar.rollback_plan(meta, now)
        self.assertEqual([o['dst'] for o in rp['ops']], [self.RULE])
        self.assertIn(('52-astral-browser-state.conf', 'already at its pre-install bytes'), rp['noops'])

    def test_independent_mutation_after_apply_refuses_for_existing_and_absent_originals(self):
        for dst in (self.BROWSER, self.RULE):
            before, plan, meta = self.transaction()
            for c in plan['changes']:
                ar.mark_installed(meta, c['name'])
            now = configured(); now[dst] = dict(now[dst], sha='edited-by-another-actor')
            with self.assertRaises(ar.RollbackRefused, msg=dst):
                ar.rollback_plan(meta, now)

    def test_concurrent_deletion_refuses(self):
        for dst in (self.BROWSER, self.RULE):
            before, plan, meta = self.transaction()
            for c in plan['changes']:
                ar.mark_installed(meta, c['name'])
            now = configured(); now[dst] = absent()
            with self.assertRaises(ar.RollbackRefused, msg=dst):
                ar.rollback_plan(meta, now)

    def test_second_rollback_is_a_noop_for_what_the_first_already_did(self):
        before, plan, meta = self.transaction()
        for c in plan['changes']:
            ar.mark_installed(meta, c['name'])
        now = configured(); now[self.RULE] = absent()                                   # the first rollback removed it
        rp = ar.rollback_plan(meta, now, done={'49-openhome-rtkit.rules'})
        self.assertEqual([o['dst'] for o in rp['ops']], [self.BROWSER])
        self.assertIn(('49-openhome-rtkit.rules', 'already rolled back'), rp['noops'])

    def test_rollback_of_an_unchanged_install_is_empty(self):
        plan = ar.plan(MANIFEST, configured())
        meta = ar.backup_meta(MANIFEST, configured(), good_facts(), {'sink_mute': False}, plan)
        rp = ar.rollback_plan(meta, configured())
        self.assertEqual(rp['ops'], []); self.assertEqual(rp['level'], 'none')


class AudioSafety(unittest.TestCase):
    def test_never_unmutes_microphones_and_only_preserves_levels(self):
        before = {'speaker': '50%', 'microphone': '160%'}
        for level in ar.LEVELS:
            for mute_before in (True, False):
                ops = ar.audio_restore_ops(mute_before, level, before, dict(before))
                self.assertFalse(any('set-source-mute' in o for o in ops))
                self.assertFalse(any('set-sink-input-mute' in o for o in ops))
                self.assertEqual(any(o[1] == 'set-sink-mute' for o in ops), mute_before is False)
                self.assertFalse(any('volume' in o[1] for o in ops))          # nothing drifted: no level command at all
        drifted = ar.audio_restore_ops(True, 'audio-stack', before, {'speaker': '100%', 'microphone': '100%'})
        self.assertEqual(sorted(o[1:] for o in drifted), sorted([('set-sink-volume', 'SINK', '50%'), ('set-source-volume', 'RAW', '160%')]))
        # a device that was at other levels before is returned to those, never to a fixed number
        other = ar.audio_restore_ops(True, 'audio-stack', {'speaker': '40%', 'microphone': '120%'}, {'speaker': '50%', 'microphone': '160%'})
        self.assertEqual(sorted(o[1:] for o in other), sorted([('set-sink-volume', 'SINK', '40%'), ('set-source-volume', 'RAW', '120%')]))
        self.assertEqual(ar.audio_restore_ops(True, 'aec', before, {'speaker': '100%', 'microphone': '100%'}), [])   # only a stack restart may restore levels
        self.assertEqual(ar.audio_restore_ops(True, 'none', before, before), [])
        self.assertEqual(ar.audio_restore_ops(True, 'audio-stack', None, {'speaker': '100%', 'microphone': '100%'}), [])   # unknown before: leave alone


class ParsePwDump(unittest.TestCase):
    def node(self, name, props, state='running', info=True):
        o = {'type': 'PipeWire:Interface:Node', 'id': 1}
        o['info'] = {'state': state, 'props': props} if info else None
        return o

    def test_invalid_utf8_null_info_and_secrets_are_tolerated_and_filtered(self):
        nodes = [self.node('alsa_output.platform-soc_sound.pro-output-0', {'node.name': 'alsa_output.platform-soc_sound.pro-output-0', 'audio.position': ['FL', 'FR'],
                                                                           'api.alsa.headroom': '1024', 'node.group': 'pro-audio-2', 'node.link-group': None,
                                                                           'application.token': 'SECRET-DO-NOT-PRINT', 'media.name': 'caf\udce9'}),
                 self.node('astral_echo_cancel', {'node.name': 'astral_echo_cancel', 'node.latency': '960/48000'}),
                 self.node('broken', {}, info=False),
                 {'type': 'PipeWire:Interface:Node', 'id': 9, 'info': {'props': None}},
                 {'type': 'PipeWire:Interface:Client', 'id': 3, 'info': {'props': {'node.name': 'not-a-node'}}}]
        raw = json.dumps(nodes).encode('utf-8', 'surrogatepass') + b'\n'
        raw = raw.replace(b'caf', b'caf\xff')                      # an invalid byte inside a string value
        out = ar.parse_pw_dump(raw)
        self.assertEqual(set(out), {'alsa_output.platform-soc_sound.pro-output-0', 'astral_echo_cancel'})
        hat = out['alsa_output.platform-soc_sound.pro-output-0']
        self.assertEqual(hat['audio.position'], '[ FL FR ]'); self.assertEqual(hat['api.alsa.headroom'], '1024')
        self.assertNotIn('node.link-group', hat)                          # null value dropped: reads as absent
        self.assertNotIn('application.token', hat); self.assertNotIn('media.name', hat)
        self.assertNotIn('SECRET', json.dumps(out))
        self.assertEqual(out['astral_echo_cancel']['state'], 'running')
        self.assertEqual(ar.parse_pw_dump(b'not json'), {}); self.assertEqual(ar.parse_pw_dump(None), {}); self.assertEqual(ar.parse_pw_dump(b'{}'), {})

    def test_string_position_is_kept_verbatim(self):
        raw = json.dumps([self.node('alsa_input.platform-soc_sound.pro-input-0', {'node.name': 'alsa_input.platform-soc_sound.pro-input-0', 'audio.position': 'AUX0,AUX1'})]).encode()
        self.assertEqual(ar.parse_pw_dump(raw)['alsa_input.platform-soc_sound.pro-input-0']['audio.position'], 'AUX0,AUX1')


class Verify(unittest.TestCase):
    def test_current_device_shape_passes(self):
        self.assertEqual(failing(ar.verify(good_obs(), MANIFEST)), [])

    def test_each_runtime_property_is_checked_on_its_own(self):
        def broken(mutate):
            o = copy.deepcopy(good_obs()); mutate(o); return failing(ar.verify(o, MANIFEST))
        self.assertIn('rtkit.four-data-loops-RR20', broken(lambda o: o.__setitem__('threads', ['  1 2 openhome  TS      - data-loop.0'] * 4)))
        self.assertIn('rtkit.four-data-loops-RR20', broken(lambda o: o.__setitem__('rt_comms', ['pipewire', 'wireplumber', 'pipewire-pulse'])))
        self.assertIn('rtkit.polkit-authorized', broken(lambda o: o.__setitem__('pkcheck_rc', 1)))
        self.assertIn('graph.force-quantum-960', broken(lambda o: o.__setitem__('force_quantum', '480')))
        self.assertIn('aec.astral_echo_cancel.latency-960-running', broken(lambda o: o['nodes']['astral_echo_cancel'].__setitem__('node.latency', '480/48000')))
        self.assertIn('aec.astral_aec_reference.latency-960-running', broken(lambda o: o['nodes']['astral_aec_reference'].__setitem__('state', 'suspended')))
        self.assertIn('hat.pro-output-0.no-link-group', broken(lambda o: o['nodes']['alsa_output.platform-soc_sound.pro-output-0'].__setitem__('node.link-group', 'pro-audio-2')))
        self.assertIn('hat.pro-input-0.headroom-1024', broken(lambda o: o['nodes']['alsa_input.platform-soc_sound.pro-input-0'].__setitem__('api.alsa.headroom', '32')))
        self.assertIn('hat.pro-output-0.position', broken(lambda o: o['nodes']['alsa_output.platform-soc_sound.pro-output-0'].__setitem__('audio.position', 'AUX0,AUX1')))
        self.assertIn('link.astral_aec_reference:input_FL', broken(lambda o: o.__setitem__('links', o['links'][2:])))
        self.assertIn('hub.requires-astral-aec', broken(lambda o: o['hub'].__setitem__('Requires', 'app.slice basic.target')))
        self.assertIn('hub.env-aec-source', broken(lambda o: o['hub'].__setitem__('Environment', 'ASTRAL_MIC_AEC=0')))
        self.assertIn('capture.no-browser-capture', broken(lambda o: o['captures'].append({'binary': 'chromium', 'target': None})))
        self.assertIn('capture.one-hub-capture-on-aec', broken(lambda o: o.__setitem__('captures', [])))
        self.assertIn('levels.speaker-as-installed', broken(lambda o: o['volumes'].__setitem__('speaker', '70%')))
        self.assertIn('levels.microphone-as-installed', broken(lambda o: o['volumes'].__setitem__('microphone', '100%')))
        self.assertIn('wireplumber.started-after-rules', broken(lambda o: o.__setitem__('wireplumber_start_ts', 50.0)))
        self.assertIn('wireplumber.started-after-rules', broken(lambda o: o.__setitem__('wireplumber_start_ts', 99.9)))    # 0.1 s before the write: not loaded, no slack
        self.assertNotIn('wireplumber.started-after-rules', broken(lambda o: o.__setitem__('wireplumber_start_ts', 100.139)))   # the device's measured 0.139 s after
        self.assertIn('wireplumber.started-after-rules', broken(lambda o: o.__setitem__('wireplumber_rules_mtime', None)))
        self.assertIn('aec.started-after-dropins', broken(lambda o: o.__setitem__('aec_start_ts', None)))
        self.assertIn('aec.started-after-dropins', broken(lambda o: o.__setitem__('aec_start_ts', 50.0)))
        self.assertIn('file.49-openhome-rtkit.rules', broken(lambda o: o['files'].__setitem__(BY_NAME['49-openhome-rtkit.rules']['dst'], None)))
        self.assertIn('service.astral-hub.active', broken(lambda o: o['active'].__setitem__('astral-hub', 'failed')))

    def test_levels_are_judged_against_the_record_or_only_reported_before_one(self):
        o = dict(good_obs(), volumes={'speaker': '50%', 'microphone': '160%'})
        self.assertEqual(failing(ar.verify(o, MANIFEST)), ['levels.microphone-as-installed', 'levels.speaker-as-installed'])
        o['recorded_levels'] = None
        results = ar.verify(o, MANIFEST)
        self.assertEqual(failing(results), [])
        self.assertIn('none recorded yet', dict((n, d) for n, _, d in results)['info.levels'])

    def test_mute_state_is_reported_not_judged(self):
        o = good_obs(); o['sink_mute'] = True; o['raw_mute'] = False
        self.assertEqual(failing(ar.verify(o, MANIFEST)), [])
        info = dict((n, d) for n, _, d in ar.verify(o, MANIFEST) if n.startswith('info.'))
        self.assertIn('mute=True', info['info.sink-mute']); self.assertIn('raw=False', info['info.source-mutes'])


class Home(unittest.TestCase):
    def test_astral_home_then_a_home_with_astral_installed_then_the_devkit_user(self):
        import os
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            installed, bare = Path(d) / 'installed', Path(d) / 'bare'
            (installed / 'astral-voice').mkdir(parents=True)
            bare.mkdir()
            with mock.patch.dict(os.environ, {'ASTRAL_HOME': '/srv/astral'}):
                self.assertEqual(ar.astral_home(), '/srv/astral')
            with mock.patch.dict(os.environ, {'ASTRAL_HOME': ''}):
                with mock.patch.object(Path, 'home', return_value=installed):
                    self.assertEqual(ar.astral_home(), str(installed))
                with mock.patch.object(Path, 'home', return_value=bare):
                    self.assertEqual(ar.astral_home(), '/home/openhome')


if __name__ == '__main__':
    unittest.main(verbosity=1)
