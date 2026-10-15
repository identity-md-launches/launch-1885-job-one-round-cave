"""Offline integration checks using retained public evidence and synthetic mutations."""
import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

import http_evidence as tool

OBSERVED = Path(__file__).with_name('observed-report.json')


class HandoffTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, name, data):
        path = self.root / name
        path.write_text(data, encoding='utf-8')
        return path

    def source(self):
        return json.loads(OBSERVED.read_text())

    def row(self, text):
        return list(csv.DictReader(io.StringIO(text)))[0]

    def test_real_historical_report_is_fresh_then_stale(self):
        a = self.row(tool.snapshot(OBSERVED, True))
        b = self.row(tool.snapshot(OBSERVED, True, '2026-10-15T19:03:45Z'))
        self.assertEqual(a['probe_ok'], 'true')
        self.assertEqual(a['url'], 'https://api.imd.fun/launches')
        self.assertEqual(a['verdict'], 'within_freshness_lifetime')
        self.assertEqual(b['verdict'], 'stale')
        self.assertEqual(a['body_sha256'], b['body_sha256'])
        self.assertEqual(a['source_sha256'], b['source_sha256'])
        self.assertNotEqual(a['evaluated_at'], b['evaluated_at'])

    def test_line2_review_explains_freshness_change_for_same_body(self):
        a = self.save('before.csv', tool.snapshot(OBSERVED, True))
        b = self.save('after.csv', tool.snapshot(OBSERVED, True, '2026-10-15T19:03:45Z'))
        result = tool.compare(a, b)
        self.assertEqual(result['summary']['changed'], 1)
        fields = result['changed'][0]['fields']
        self.assertEqual(fields['verdict']['after'], 'stale')
        self.assertNotIn('body_sha256', fields)
        self.assertTrue(tool.compare(a, a)['equal'])

    def test_failed_health_is_not_hidden_by_fresh_cache(self):
        source = self.source()
        source['ok'] = source['probe']['ok'] = False
        p = self.save('failed.json', json.dumps(source))
        row = self.row(tool.snapshot(p, True))
        self.assertEqual(row['probe_ok'], 'false')
        self.assertEqual(row['verdict'], 'within_freshness_lifetime')
        source['ok'] = True
        with self.assertRaises(ValueError):
            tool.snapshot(self.save('contradiction.json', json.dumps(source)), True)

    def test_incomplete_reports_and_missing_digest_are_rejected(self):
        source = self.source()
        for mutation in ('error', 'digest', 'url', 'headers'):
            bad = copy.deepcopy(source)
            if mutation == 'error':
                bad['probe']['error'] = {'kind': 'body'}
            elif mutation == 'digest':
                bad['probe']['hops'][-1].pop('body_sha256')
            elif mutation == 'url':
                bad['probe']['url'] = 'https://user:secret@example.com/'
            else:
                bad['probe']['hops'][-1].pop('cache_headers')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                tool.snapshot(self.save('bad.json', json.dumps(bad)))

    def test_ambiguous_csv_and_wrong_schema_are_rejected(self):
        text = tool.snapshot(OBSERVED)
        good = self.save('good.csv', text)
        # DictWriter serializes exactly one row, so repeating its data line duplicates a URL.
        for bad in (text + text.splitlines(keepends=True)[1], 'url\nhttps://example.com/\n',
                    ','.join(tool.COLUMNS) + '\n'):
            with self.assertRaises(ValueError):
                tool.compare(good, self.save('bad.csv', bad))

    def test_cli_error_has_no_partial_csv_and_json_inputs_are_bounded(self):
        for bad in ('{"x":1,"x":2}', '[NaN]', ' ' * (tool.cache_lens.LIMIT + 1), '{}'):
            path = self.save('bad.json', bad)
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = tool.main(['snapshot', str(path)])
            self.assertEqual(code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('error', json.loads(err.getvalue()))

    def test_workspace_boundary_and_determinism(self):
        self.assertEqual(tool.snapshot(OBSERVED), tool.snapshot(OBSERVED))
        with self.assertRaises(ValueError):
            tool.snapshot('/outside-workspace/not-opened.json')

    def test_cli_comparison_exit_codes(self):
        a = self.save('a.csv', tool.snapshot(OBSERVED))
        b = self.save('b.csv', tool.snapshot(OBSERVED, at='2026-10-15T19:03:45Z'))
        for other, expected in ((a, 0), (b, 1)):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tool.main(['compare', str(a), str(other)]), expected)


if __name__ == '__main__':
    unittest.main()
