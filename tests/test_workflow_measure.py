import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / 'skills/game-workflow-supervision/scripts/workflow_measure.py'
spec = importlib.util.spec_from_file_location('workflow_measure', SCRIPT)
measure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure)


class MeasureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'planning/workflow-runs/fixture-run').mkdir(parents=True)
        (self.root / 'source.md').write_text('# Fixture source\n', encoding='utf-8')
        self.started = datetime(2026, 10, 10, tzinfo=timezone.utc)

    def start(self, **kwargs):
        return measure.begin(self.root, 'fixture-run', 'phase-1', phase='implementation', scope='real-work',
                             conditions=['Includes tool waiting; one author'], sources=['source.md'],
                             clock=lambda: self.started, **kwargs)

    def finish(self, seconds=10, **kwargs):
        return measure.end(self.root, 'fixture-run', 'phase-1',
                           clock=lambda: self.started + timedelta(seconds=seconds), **kwargs)

    def test_ten_seconds_and_begin_end_retries_preserve_actual_times(self):
        first = self.start()
        (self.root / 'source.md').write_text('# Source changed after begin\n', encoding='utf-8')
        self.assertEqual(first, self.start())
        result = self.finish()
        self.assertEqual(10, result['event']['data']['value'])
        before = (self.root / result['rawPath']).read_bytes()
        self.assertEqual(result, self.finish(100))
        self.assertEqual(before, (self.root / result['rawPath']).read_bytes())
        self.assertEqual({'id', 'scope', 'metric', 'kind', 'value', 'unit', 'source'}, set(result['event']['data']))
        self.assertIsNone(result['revision'])

    def test_changed_begin_arguments_and_missing_start_reject(self):
        with self.assertRaises(FileNotFoundError):
            self.finish()
        self.start()
        with self.assertRaises(measure.MeasureError):
            measure.begin(self.root, 'fixture-run', 'phase-1', phase='review', scope='real-work',
                          conditions=['Includes tool waiting; one author'], sources=['source.md'])

    def test_negative_interval_and_explicit_clock_anomaly_are_unmeasured(self):
        self.start()
        data = self.finish(-1)['event']['data']
        self.assertEqual('unmeasured', data['kind'])
        self.assertIsNone(data['value'])
        raw = json.loads((self.root / data['source']).read_text(encoding='utf-8'))
        self.assertTrue(raw['reason'])
        measure.begin(self.root, 'fixture-run', 'anomaly', phase='review', scope='behavior-test',
                      conditions=['One scenario'], sources=['source.md'], clock=lambda: self.started)
        data = measure.end(self.root, 'fixture-run', 'anomaly', clock_anomaly='System clock adjusted')['event']['data']
        self.assertEqual('unmeasured', data['kind'])

    def test_invalid_clock_and_corrupt_nonfinite_raw(self):
        self.start()
        result = measure.end(self.root, 'fixture-run', 'phase-1', clock=lambda: 'not-a-time')
        self.assertEqual('unmeasured', result['event']['data']['kind'])
        target = self.root / result['rawPath']
        raw = json.loads(target.read_text(encoding='utf-8'))
        raw['value'] = float('nan')
        target.write_text(json.dumps(raw), encoding='utf-8')
        with self.assertRaises(measure.MeasureError):
            self.finish()

    def test_event_write_failure_keeps_first_end_and_retry_value(self):
        self.start()
        atomic = measure.support().sibling('dashboard').atomic
        def fail_event(target, data):
            if target.name.endswith('.event.json'):
                raise OSError('Injected event write failure')
            atomic(target, data)
        with self.assertRaises(OSError):
            self.finish(writer=fail_event)
        result = self.finish(100)
        self.assertEqual(10, result['event']['data']['value'])
        self.assertEqual((self.started + timedelta(seconds=10)).isoformat(),
                         json.loads((self.root / result['rawPath']).read_text(encoding='utf-8'))['endedAt'])
        (self.root / result['eventPath']).write_text('{}', encoding='utf-8')
        with self.assertRaises(measure.MeasureError):
            self.finish()

    def test_external_source_and_invalid_ids_reject(self):
        for locator in ('../outside.md', 'C:/outside.md', 'missing.md', 'planning'):
            with self.subTest(locator=locator), self.assertRaises((ValueError, OSError)):
                measure.begin(self.root, 'fixture-run', 'bad', phase='review', scope='real-work',
                              conditions=['Fixture'], sources=[locator])
        with self.assertRaises(measure.MeasureError):
            measure.begin(self.root, '../bad', 'bad', phase='review', scope='real-work',
                          conditions=['Fixture'], sources=['source.md'])

    def test_linked_source_rejects_when_host_supports_symlinks(self):
        link = self.root / 'linked.md'
        try:
            link.symlink_to(self.root / 'source.md')
        except OSError:
            self.skipTest('Host cannot create symlinks without extra permission')
        with self.assertRaises(ValueError):
            measure.begin(self.root, 'fixture-run', 'linked', phase='review', scope='real-work',
                          conditions=['Fixture'], sources=['linked.md'])

    def test_existing_record_accepts_event_and_retries_without_revision_growth(self):
        from test_workflow_state import StateTests
        fixture = StateTests()
        fixture.setUp()
        self.addCleanup(lambda: shutil.rmtree(fixture.root))
        fixture.tool.init(fixture.root, fixture.initial())
        measure.begin(fixture.root, 'fixture-run', 'recorded', phase='review', scope='behavior-test',
                      conditions=['Record adapter fixture'], sources=['artifact/code.py'], clock=lambda: self.started)
        result = measure.end(fixture.root, 'fixture-run', 'recorded', clock=lambda: self.started + timedelta(seconds=10))
        before = fixture.state()['revision']
        self.assertEqual(before, result['revision'])
        fixture.tool.record(fixture.root, 'fixture-run', result['event'], result['revision'])
        after = fixture.state()['revision']
        fixture.tool.record(fixture.root, 'fixture-run', result['event'], after)
        self.assertEqual(after, fixture.state()['revision'])
        self.assertEqual(10, fixture.state()['measurements'][0]['value'])


if __name__ == '__main__':
    unittest.main()
