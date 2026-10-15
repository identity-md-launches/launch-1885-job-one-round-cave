#!/usr/bin/env python3
"""Carry saved HTTP health and freshness evidence into exact keyed CSV reviews."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

import cache_lens
import reconcile

COLUMNS = ('url', 'final_url', 'probe_ok', 'status', 'body_sha256',
           'cache_type', 'evaluated_at', 'verdict', 'current_age_seconds',
           'freshness_lifetime_seconds', 'remaining_seconds', 'warnings',
           'source_sha256')


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def reject_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


def snapshot(path, shared=False, at=None):
    """One exact row per requested URL; reject incomplete or ambiguous evidence."""
    path = cache_lens.workspace_file(path)
    with path.open('rb') as stream:
        raw = stream.read(cache_lens.LIMIT + 1)
    if len(raw) > cache_lens.LIMIT:
        raise ValueError('report exceeds 1 MiB')
    report = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    explanation = cache_lens.inspect(report, shared, at)
    probe = report.get('probe') if report.get('schema') == 'deadline-sentry/v1' else report
    if type(probe.get('ok')) is not bool:
        raise ValueError('probe must retain boolean health result')
    if report.get('schema') == 'deadline-sentry/v1' and report.get('ok') is not probe['ok']:
        raise ValueError('wrapper health contradicts completed probe')
    for field in ('url', 'final_url'):
        url = probe.get(field)
        if not isinstance(url, str) or any(ord(c) <= 32 or ord(c) == 127 for c in url):
            raise ValueError('missing or invalid ' + field)
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment):
            raise ValueError('need public nonsecret HTTPS URLs')
    hop = probe['hops'][-1]
    digest = hop.get('body_sha256')
    if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('completed body digest missing or invalid')
    row = {'url': probe['url'], 'final_url': probe['final_url'],
           'probe_ok': str(probe['ok']).lower(), 'status': str(hop['status']),
           'body_sha256': digest, 'source_sha256': hashlib.sha256(raw).hexdigest()}
    for field in COLUMNS:
        if field in row:
            continue
        value = explanation[field]
        row[field] = (json.dumps(value, ensure_ascii=True, separators=(',', ':'))
                      if isinstance(value, list) or value is None else str(value))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue()


def compare(before, after):
    for path in (before, after):
        header, groups, count = reconcile.load_table(path, ['url'])
        if header != list(COLUMNS) or not count:
            raise ValueError('need nonempty HTTP evidence CSV snapshots')
        if any(not key[0] or len(rows) != 1 for key, rows in groups.items()):
            raise ValueError('snapshot URLs must be unique and nonempty')
    return reconcile.reconcile(before, after, ['url'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest='command', required=True)
    snap = commands.add_parser('snapshot', help='explain one completed saved probe as CSV')
    snap.add_argument('report')
    snap.add_argument('--shared', action='store_true')
    snap.add_argument('--at', help='explicit evaluation time; default: recorded header receipt')
    diff = commands.add_parser('compare', help='compare saved CSV snapshots by requested URL')
    diff.add_argument('before')
    diff.add_argument('after')
    args = parser.parse_args(argv)
    try:
        if args.command == 'snapshot':
            output = snapshot(args.report, args.shared, args.at)
            code = 0
        else:
            result = compare(args.before, args.after)
            output = json.dumps(result, indent=2, ensure_ascii=True) + '\n'
            code = 0 if result['equal'] else 1
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError, RecursionError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
