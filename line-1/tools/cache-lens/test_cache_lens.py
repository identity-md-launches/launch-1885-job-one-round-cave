"""Offline HTTP cache evidence regressions; no network or fixture writes."""
import contextlib
import copy
import io
import json
import unittest
from unittest import mock
import cache_lens as lens


def observation(*headers, status=200):
    return {'schema': 'endpoint-sentry/v1', 'final_url': 'https://example.com/',
            'hops': [{'status': status,
                      'request_sent_at': '2026-10-15T12:00:00+00:00',
                      'headers_received_at': '2026-10-15T12:00:02+00:00',
                      'cache_headers': [['date', 'Thu, 15 Oct 2026 12:00:00 GMT'],
                                        *[list(pair) for pair in headers]]}]}


class CacheTests(unittest.TestCase):
    def test_age_equation_and_resident_time(self):
        r = lens.inspect(observation(('cache-control', 'max-age=60'), ('age', '10')),
                         at='2026-10-15T12:00:12Z')
        self.assertEqual(r['current_age_seconds'], 22)
        self.assertEqual(r['remaining_seconds'], 38)
        self.assertEqual(r['verdict'], 'within_freshness_lifetime')

    def test_apparent_age_dominates_and_boundary_is_stale(self):
        r = observation(('cache-control', 'max-age=60'))
        r['hops'][0]['cache_headers'][0][1] = 'Thu, 15 Oct 2026 11:59:02 GMT'
        self.assertEqual(lens.inspect(r)['current_age_seconds'], 60)
        self.assertEqual(lens.inspect(r)['verdict'], 'stale')

    def test_shared_precedence(self):
        r = observation(('cache-control', 'max-age=10, s-maxage="100"'), ('age', '20'))
        self.assertEqual(lens.inspect(r)['verdict'], 'stale')
        shared = lens.inspect(r, shared=True)
        self.assertEqual(shared['verdict'], 'within_freshness_lifetime')
        self.assertTrue(shared['stale_reuse_requires_validation'])
        self.assertEqual(shared['lifetime_source'], 's-maxage')

    def test_restrictions_override_apparent_freshness(self):
        for directive, shared, expected in [
                ('no-store', False, 'storage_forbidden'),
                ('private', True, 'shared_storage_forbidden'),
                ('no-cache="set-cookie, x-private"', False, 'revalidation_required')]:
            r = observation(('cache-control', 'max-age=999, ' + directive))
            self.assertEqual(lens.inspect(r, shared)['verdict'], expected)
        r = observation(('cache-control', 'max-age=999'), ('vary', 'Accept, *'))
        self.assertEqual(lens.inspect(r)['verdict'], 'revalidation_required')

    def test_expires_and_no_heuristics(self):
        r = observation(('expires', 'Thu, 15 Oct 2026 12:01:00 GMT'))
        self.assertEqual(lens.inspect(r)['freshness_lifetime_seconds'], 60)
        self.assertEqual(lens.inspect(observation())['verdict'], 'freshness_unknown')
        r = observation(('last-modified', 'Thu, 15 Oct 2026 11:00:00 GMT'))
        self.assertEqual(lens.inspect(r)['verdict'], 'freshness_unknown')
        self.assertTrue(lens.inspect(r)['validators_present']['last_modified'])

    def test_duplicate_and_malformed_numbers_never_fall_back(self):
        for headers in [
            [('cache-control', 'max-age=60, max-age=60')],
            [('cache-control', 'max-age=-1')],
            [('cache-control', 'max-age=1.5')],
            [('cache-control', 'max-age=60'), ('age', 'x')],
            [('cache-control', 'max-age=60'), ('age', '0'), ('age', '0')],
            [('cache-control', 'max-age=60'), ('date', 'bad')],
            [('cache-control', 'max-age=bad'), ('expires', 'Thu, 15 Oct 2026 12:01:00 GMT')]]:
            with self.subTest(headers=headers):
                r = lens.inspect(observation(*headers))
                self.assertEqual(r['verdict'], 'freshness_unknown')
                self.assertTrue(r['warnings'])
        r = lens.inspect(observation(('cache-control', 's-maxage=bad,max-age=60')), True)
        self.assertIsNone(r['freshness_lifetime_seconds'])

    def test_old_incomplete_and_wrapped_reports(self):
        r = observation(('cache-control', 'max-age=60'))
        self.assertEqual(lens.inspect({'schema': 'deadline-sentry/v1', 'probe': r}),
                         lens.inspect(r))
        for key in ['cache_headers', 'request_sent_at', 'headers_received_at']:
            old = copy.deepcopy(r)
            del old['hops'][0][key]
            with self.assertRaises(ValueError):
                lens.inspect(old)
        r['error'] = {'kind': 'body'}
        with self.assertRaises(ValueError):
            lens.inspect(r)

    def test_timestamps_and_future_date(self):
        r = observation(('cache-control', 'max-age=60'))
        for at in ['2026-10-15T12:00:01Z', '2026-10-15T12:00:02', 'nonsense']:
            with self.assertRaises(ValueError):
                lens.inspect(r, at=at)
        r['hops'][0]['cache_headers'][0][1] = 'Thu, 15 Oct 2026 12:01:00 GMT'
        self.assertEqual(lens.inspect(r)['current_age_seconds'], 2)

    def test_multiple_lines_and_quoted_commas(self):
        r = observation(('Cache-Control', 'max-age=60'),
                        ('cache-control', 'extension="a,b", must-revalidate'), ('etag', '"x"'))
        result = lens.inspect(r)
        self.assertTrue(result['validators_present']['etag'])
        self.assertTrue(result['stale_reuse_requires_validation'])
        self.assertEqual(result['freshness_lifetime_seconds'], 60)
        for value in ['max-age="60', 'max-age=', 'bad name=2', 'max-age="60"oops']:
            with self.assertRaises(ValueError):
                lens.directives([value])

    def test_non_200_and_unusable_date(self):
        self.assertEqual(lens.inspect(observation(status=503))['verdict'], 'unsupported_status')
        r = observation(('cache-control', 'max-age=60'))
        r['hops'][0]['cache_headers'].pop(0)
        self.assertEqual(lens.inspect(r)['verdict'], 'freshness_unknown')

    def test_cli_stdin_and_error_no_partial_success(self):
        for data, expected in [(json.dumps(observation()).encode(), 0),
                               (b'{"schema":1,"schema":2}', 2),
                               (b'{"x":NaN}', 2), (b'x' * (lens.LIMIT + 1), 2)]:
            output = io.StringIO()
            with mock.patch.object(lens.sys, 'stdin', io.TextIOWrapper(io.BytesIO(data))), \
                    contextlib.redirect_stdout(output):
                code = lens.main(['-'])
            self.assertEqual(code, expected)
            report = json.loads(output.getvalue())
            self.assertEqual('error' in report, expected == 2)

    def test_workspace_boundary(self):
        with self.assertRaises(ValueError):
            lens.workspace_file('/outside-workspace/report.json')


if __name__ == '__main__':
    unittest.main()
