#!/usr/bin/env python3
"""Plan and apply an offline, exact-baseline keyed CSV patch. Standard library only."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
MAX_PLAN_BYTES = 64 * 1024 * 1024
csv.field_size_limit(MAX_BYTES)


class InputError(ValueError):
    pass


def read_local(path, limit):
    path = Path(path).resolve()
    if not path.is_relative_to(Path.cwd().resolve()):
        raise InputError('input must be inside the current working directory')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise InputError('input exceeds byte limit')
    return raw


def check_keys(keys):
    if (not isinstance(keys, list) or not keys or
            any(not isinstance(k, str) or not k for k in keys) or len(set(keys)) != len(keys)):
        raise InputError('provide distinct nonempty key columns')


def check_row(row, header, keys):
    if (not isinstance(row, dict) or set(row) != set(header) or
            any(not isinstance(v, str) for v in row.values())):
        raise InputError('row must contain exactly the header columns as strings')
    key = tuple(row[k] for k in keys)
    if any(v == '' for v in key):
        raise InputError('empty key components are refused')
    return key


def parse_table(raw, keys):
    check_keys(keys)
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
        header = next(reader, None)
        if (not header or any(not h for h in header) or len(set(header)) != len(header)
                or not set(keys) <= set(header)):
            raise InputError('invalid header or missing key column')
        rows = {}
        for number, values in enumerate(reader, 1):
            if number > MAX_ROWS:
                raise InputError('too many rows')
            if len(values) != len(header):
                raise InputError('ragged CSV row')
            row = dict(zip(header, values))
            key = check_row(row, header, keys)
            if key in rows:
                raise InputError('duplicate key: patching is ambiguous')
            rows[key] = row
        return header, rows
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError('invalid UTF-8 CSV: ' + str(exc)) from exc


def encode_table(header, rows):
    out = io.StringIO(newline='')
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(header)
    for key in sorted(rows):
        writer.writerow([rows[key][column] for column in header])
    raw = out.getvalue().encode('utf-8')
    if len(raw) > MAX_BYTES or len(rows) > MAX_ROWS:
        raise InputError('result exceeds CSV limits')
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def plan(before, after, keys):
    baseline = read_local(before, MAX_BYTES)
    target = read_local(after, MAX_BYTES)
    header, old = parse_table(baseline, keys)
    target_header, new = parse_table(target, keys)
    if set(header) != set(target_header):
        raise InputError('schema changes are not supported; reconcile them separately')
    operations = []
    for key in sorted(old.keys() | new.keys()):
        b, a = old.get(key), new.get(key)
        if b != a:
            operations.append({'before': b, 'after': a})
    result = {'format': 'csv-patch/v1', 'keys': keys, 'header': header,
              'baseline_sha256': digest(baseline),
              'result_sha256': digest(encode_table(header, new)), 'operations': operations}
    if len(json.dumps(result, ensure_ascii=False).encode('utf-8')) > MAX_PLAN_BYTES:
        raise InputError('plan exceeds byte limit')
    return result


def apply(baseline, patch):
    fields = {'format', 'keys', 'header', 'baseline_sha256', 'result_sha256', 'operations'}
    if not isinstance(patch, dict) or set(patch) != fields or patch['format'] != 'csv-patch/v1':
        raise InputError('invalid patch format')
    for name in ('baseline_sha256', 'result_sha256'):
        value = patch[name]
        if (not isinstance(value, str) or len(value) != 64 or
                any(c not in '0123456789abcdef' for c in value)):
            raise InputError('invalid SHA-256')
    raw = read_local(baseline, MAX_BYTES)
    if digest(raw) != patch['baseline_sha256']:
        raise InputError('baseline changed since review; create and review a new plan')
    keys = patch['keys']
    header, rows = parse_table(raw, keys)
    if patch['header'] != header:
        raise InputError('patch header does not match baseline')
    operations = patch['operations']
    if not isinstance(operations, list) or len(operations) > 2 * MAX_ROWS:
        raise InputError('invalid operations list')
    touched = set()
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) != {'before', 'after'}:
            raise InputError('invalid operation')
        b, a = operation['before'], operation['after']
        if b is None and a is None:
            raise InputError('empty operation')
        bk = check_row(b, header, keys) if b is not None else None
        ak = check_row(a, header, keys) if a is not None else None
        if b == a or (bk is not None and ak is not None and bk != ak):
            raise InputError('no-op or key-changing operation')
        key = bk if bk is not None else ak
        if key in touched:
            raise InputError('key occurs in multiple operations')
        touched.add(key)
        if rows.get(key) != b:
            raise InputError('operation precondition does not match baseline')
        if a is None:
            del rows[key]
        else:
            rows[key] = a
    result = encode_table(header, rows)
    if digest(result) != patch['result_sha256']:
        raise InputError('result digest mismatch; patch is incomplete or changed')
    return result


def inspect(baseline, patch):
    """Validate a patch against its exact baseline without emitting CSV bytes."""
    result = apply(baseline, patch)
    added = removed = changed = 0
    for operation in patch['operations']:
        if operation['before'] is None:
            added += 1
        elif operation['after'] is None:
            removed += 1
        else:
            changed += 1
    return {'format': patch['format'], 'keys': patch['keys'],
            'baseline_sha256': patch['baseline_sha256'],
            'result_sha256': hashlib.sha256(result).hexdigest(),
            'operations': {'added': added, 'removed': removed, 'changed': changed,
                           'total': len(patch['operations'])}, 'valid': True}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError('duplicate JSON field')
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('plan', help='print a reviewable JSON patch')
    p.add_argument('before')
    p.add_argument('after')
    p.add_argument('--key', action='append', required=True)
    a = commands.add_parser('apply', help='validate entire patch, then print resulting CSV')
    a.add_argument('baseline')
    a.add_argument('patch')
    i = commands.add_parser('inspect', help='validate patch and print a safe operation summary')
    i.add_argument('baseline')
    i.add_argument('patch')
    args = parser.parse_args(argv)
    try:
        if args.command == 'plan':
            output = json.dumps(plan(args.before, args.after, args.key), ensure_ascii=False, indent=2) + '\n'
        elif args.command == 'apply':
            patch = json.loads(read_local(args.patch, MAX_PLAN_BYTES), object_pairs_hook=unique_object)
            output = apply(args.baseline, patch).decode('utf-8')
        else:
            patch = json.loads(read_local(args.patch, MAX_PLAN_BYTES), object_pairs_hook=unique_object)
            output = json.dumps(inspect(args.baseline, patch), ensure_ascii=False, indent=2) + '\n'
    except (InputError, OSError, ValueError, TypeError, RecursionError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    if args.command == 'plan' and len(output.encode('utf-8')) > MAX_PLAN_BYTES:
        print(json.dumps({'error': 'serialized plan exceeds byte limit'}), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
