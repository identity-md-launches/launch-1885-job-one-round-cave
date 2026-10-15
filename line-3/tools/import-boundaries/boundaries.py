#!/usr/bin/env python3
"""Summarize explicit local imports crossing Python package groups, without execution."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def load_mapper():
    path = Path(__file__).resolve().parents[1] / 'import-map' / 'import_map.py'
    spec = importlib.util.spec_from_file_location('line3_boundary_mapper', path)
    mapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mapper)
    return mapper


def summarize(report, depth=1, denies=()):
    """Group exact module names by their first depth dotted components."""
    if type(depth) is not int or depth < 1:
        raise ValueError('depth must be a positive integer')
    records = {item['module']: item for item in report['modules']}
    group_of = {name: '.'.join(name.split('.')[:depth]) for name in records}
    groups = sorted(set(group_of.values()))
    denied = set(denies)
    for source, target in denied:
        if source not in groups or target not in groups:
            raise ValueError('deny rule names unknown group: ' + source + ':' + target)
        if source == target:
            raise ValueError('deny rule must cross two different groups')
    crossings = {}
    internal = 0
    for edge in report['edges']:
        source, target = edge['from'], edge['to']
        pair = group_of[source], group_of[target]
        if pair[0] == pair[1]:
            internal += 1
            continue
        # Preserve all source occurrences, not only one representative import.
        evidence = [{'line': item['line'], 'target': item['target']}
                    for item in records[source]['imports']
                    if item.get('resolved') == target and item['kind'] == 'local']
        crossings.setdefault(pair, []).append({
            'from': source, 'to': target, 'path': records[source]['path'],
            'occurrences': sorted(evidence, key=lambda item: (item['line'], item['target']))})
    links = [{'from': pair[0], 'to': pair[1], 'denied': pair in denied,
              'module_edge_count': len(edges),
              'edges': sorted(edges, key=lambda item: (item['from'], item['to']))}
             for pair, edges in sorted(crossings.items())]
    dynamic = [{'module': item['module'], 'path': item['path'], 'line': line}
               for item in report['modules'] for line in item['dynamic_import_lines']]
    return {'depth': depth,
            'groups': [{'name': group, 'modules': sorted(
                name for name in records if group_of[name] == group)} for group in groups],
            'boundaries': links,
            'deny_rules': [{'from': a, 'to': b} for a, b in sorted(denied)],
            'issues': report['issues'], 'cycles': report['cycles'],
            'dynamic_imports': dynamic,
            'summary': {'module_count': len(records), 'group_count': len(groups),
                        'internal_edge_count': internal,
                        'crossing_edge_count': sum(x['module_edge_count'] for x in links),
                        'boundary_count': len(links),
                        'violating_edge_count': sum(x['module_edge_count'] for x in links if x['denied'])},
            'scope': 'Explicit static local imports only; groups are dotted prefixes, not inferred architecture. '
                     'Missing edges are not proof of isolation. Package initialization, dynamic imports, '
                     'external callers and runtime conditions are not modeled.'}


def scan(root, mapper):
    workspace = Path.cwd().resolve()
    root = root.resolve()
    if not root.is_relative_to(workspace) or not root.is_dir():
        raise ValueError('root must be an existing directory inside the current workspace')
    for source in mapper.source_files(root):
        if not source.resolve().is_relative_to(workspace):
            raise ValueError('source resolves outside the current workspace')
    return mapper.inspect(root)


def format_text(result):
    lines = [f"Groups: {result['summary']['group_count']}; "
             f"crossing imports: {result['summary']['crossing_edge_count']}; "
             f"denied imports: {result['summary']['violating_edge_count']}"]
    for link in result['boundaries']:
        lines.append(f"{link['from']} -> {link['to']}" + (' [DENIED]' if link['denied'] else ''))
        for edge in link['edges']:
            for item in edge['occurrences']:
                lines.append(f"  {edge['path']}:{item['line']} {edge['from']} -> {edge['to']} ({item['target']})")
    lines.append(f"Warnings: {len(result['issues'])} issues, {len(result['cycles'])} cycle groups, "
                 f"{len(result['dynamic_imports'])} dynamic imports")
    lines.append(result['scope'])
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, help='explicit import root within the current workspace')
    parser.add_argument('--depth', type=int, default=1, help='dotted prefix components per group (default 1)')
    parser.add_argument('--deny', action='append', default=[], metavar='FROM:TO',
                        help='forbid one directed group boundary; repeatable, exact group names')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--strict', action='store_true', help='also fail for scan issues, cycles or dynamic imports')
    args = parser.parse_args(argv)
    try:
        if args.depth < 1:
            raise ValueError('depth must be a positive integer')
        denies = []
        for rule in args.deny:
            parts = rule.split(':')
            if len(parts) != 2 or not all(parts):
                raise ValueError('deny rule must be FROM:TO')
            denies.append(tuple(parts))
        result = summarize(scan(args.root, load_mapper()), args.depth, denies)
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        print('import-boundaries: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_text(result))
    warnings = result['issues'] or result['cycles'] or result['dynamic_imports']
    return int(bool(result['summary']['violating_edge_count'] or args.strict and warnings))


if __name__ == '__main__':
    sys.exit(main())
