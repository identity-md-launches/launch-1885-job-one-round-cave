#!/usr/bin/env python3
"""Exact, offline CSV reconciliation. Python standard library only."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
csv.field_size_limit(MAX_BYTES)


class InputError(ValueError):
    pass


def load_table(path, keys):
    """Read a bounded UTF-8 CSV inside the current workspace, preserving strings."""
    path = Path(path).resolve()
    if not path.is_relative_to(Path.cwd().resolve()):
        raise InputError('input must be inside the current working directory')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise InputError(f'{path.name}: exceeds {MAX_BYTES} bytes')
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
        header = next(reader, None)
        if not header or any(not h for h in header):
            raise InputError(f'{path.name}: missing or empty column name')
        if len(set(header)) != len(header):
            raise InputError(f'{path.name}: duplicate column name')
        if any(k not in header for k in keys):
            raise InputError(f'{path.name}: key columns missing: {sorted(set(keys) - set(header))}')
        groups = {}
        count = 0
        for record, values in enumerate(reader, 2):
            count += 1
            if count > MAX_ROWS:
                raise InputError(f'{path.name}: exceeds {MAX_ROWS} data records')
            if len(values) != len(header):
                raise InputError(f'{path.name}: record {record} has {len(values)} fields; expected {len(header)}')
            row = dict(zip(header, values))
            key = tuple(row[k] for k in keys)
            groups.setdefault(key, []).append({'record': record, 'values': row})
        return header, groups, count
    except (UnicodeDecodeError, csv.Error) as exc:
        raise InputError(f'{path.name}: invalid UTF-8 CSV: {exc}') from exc


def reconcile(before, after, keys, ignore=()):
    if not keys or len(set(keys)) != len(keys):
        raise InputError('provide distinct, nonempty key columns')
    if set(keys) & set(ignore):
        raise InputError('key columns cannot be ignored')
    bh, bg, bn = load_table(before, keys)
    ah, ag, an = load_table(after, keys)
    missing_ignored = set(ignore) - (set(bh) | set(ah))
    if missing_ignored:
        raise InputError(f'ignored columns do not exist: {sorted(missing_ignored)}')
    bcols, acols = set(bh) - set(ignore), set(ah) - set(ignore)
    common = sorted((bcols & acols) - set(keys))
    added, removed, changed, ambiguous = [], [], [], []
    unchanged = 0
    def key_object(key):
        return dict(zip(keys, key))
    def projected(row):
        return {k: v for k, v in row.items() if k not in ignore}
    for key in sorted(bg.keys() | ag.keys()):
        b, a = bg.get(key, []), ag.get(key, [])
        if len(b) > 1 or len(a) > 1:
            ambiguous.append({'key': key_object(key), 'before': b, 'after': a})
        elif not b:
            added.append({'key': key_object(key), 'record': a[0]['record'], 'values': projected(a[0]['values'])})
        elif not a:
            removed.append({'key': key_object(key), 'record': b[0]['record'], 'values': projected(b[0]['values'])})
        else:
            delta = {c: {'before': b[0]['values'][c], 'after': a[0]['values'][c]}
                     for c in common if b[0]['values'][c] != a[0]['values'][c]}
            if delta:
                changed.append({'key': key_object(key), 'before_record': b[0]['record'],
                                'after_record': a[0]['record'], 'fields': delta})
            else:
                unchanged += 1
    schema = {'added_columns': sorted(acols - bcols), 'removed_columns': sorted(bcols - acols)}
    different = bool(added or removed or changed or ambiguous or any(schema.values()))
    return {'format': 'csv-reconcile/v1', 'keys': list(keys), 'ignored_columns': sorted(set(ignore)),
            'equal': not different, 'complete': not ambiguous, 'schema': schema,
            'summary': {'before_records': bn, 'after_records': an, 'added': len(added),
                        'removed': len(removed), 'changed': len(changed),
                        'unchanged_on_common_columns': unchanged, 'ambiguous_keys': len(ambiguous)},
            'added': added, 'removed': removed, 'changed': changed, 'ambiguous': ambiguous}


def render_text(result):
    """Render a compact Markdown report for a worker's terminal handoff."""
    summary = result['summary']
    state = 'equal' if result['equal'] else 'different'
    lines = [f"# CSV reconciliation: {state}", '',
             f"Keys: {', '.join(result['keys'])}",
             f"Rows: {summary['before_records']} before, {summary['after_records']} after; "
             f"{summary['added']} added, {summary['removed']} removed, "
             f"{summary['changed']} changed, "
             f"{summary['unchanged_on_common_columns']} unchanged on common columns, "
             f"{summary['ambiguous_keys']} ambiguous keys.",
             f"Schema columns added: {', '.join(result['schema']['added_columns']) or 'none'}; "
             f"removed: {', '.join(result['schema']['removed_columns']) or 'none'}.",
             f"Comparison complete: {'yes' if result['complete'] else 'no; resolve duplicate keys'}."]

    def value(item):
        return json.dumps(item, ensure_ascii=False, sort_keys=True)

    sections = (
        ('Added', result['added']),
        ('Removed', result['removed']),
        ('Changed', result['changed']),
        ('Ambiguous keys', result['ambiguous']),
    )
    for title, rows in sections:
        lines.extend(['', f'## {title}'])
        if not rows:
            lines.append('None.')
            continue
        for row in rows:
            key = value(row['key'])
            if title in ('Added', 'Removed'):
                lines.append(f"- Key {key}, record {row['record']}: {value(row['values'])}")
            elif title == 'Changed':
                delta = ', '.join(
                    f"{column}: {value(change['before'])} → {value(change['after'])}"
                    for column, change in row['fields'].items())
                lines.append(f"- Key {key}: {delta}")
            else:
                lines.append(f"- Key {key}: {len(row['before'])} before row(s), "
                             f"{len(row['after'])} after row(s); no automatic pairing.")
                lines.append(f"  Before: {value(row['before'])}")
                lines.append(f"  After: {value(row['after'])}")
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', help='baseline CSV under the current directory')
    parser.add_argument('after', help='candidate CSV under the current directory')
    parser.add_argument('--key', action='append', required=True, help='key column; repeat for a composite key')
    parser.add_argument('--ignore', action='append', default=[], help='non-key column to exclude')
    parser.add_argument('--format', choices=('json', 'text'), default='json',
                        help='report format (default: json; text is readable Markdown)')
    args = parser.parse_args(argv)
    try:
        result = reconcile(args.before, args.after, args.key, args.ignore)
    except (InputError, OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(render_text(result) if args.format == 'text' else
          json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result['equal'] else 1


if __name__ == '__main__':
    sys.exit(main())
