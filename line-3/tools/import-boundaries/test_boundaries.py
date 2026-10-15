"""Offline behavior checks; generated fixtures stay in test/scratch."""

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import random
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('boundary_tool', Path(__file__).with_name('boundaries.py'))
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)
EXAMPLE = Path(__file__).parent / 'examples'


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.mapper = B.load_mapper()

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = B.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_example_retains_exact_evidence_and_internal_edges(self):
        result = B.summarize(self.mapper.inspect(EXAMPLE))
        self.assertEqual(result['summary'], {'module_count': 4, 'group_count': 3,
                         'internal_edge_count': 1, 'crossing_edge_count': 3,
                         'boundary_count': 3, 'violating_edge_count': 0})
        self.assertEqual(result['boundaries'][0]['edges'], [{
            'from': 'domain.service', 'to': 'storage.store', 'path': 'domain/service.py',
            'occurrences': [{'line': 2, 'target': 'storage import store'}]}])
        self.assertEqual(result['issues'], [])

    def test_rule_is_directional_and_deduplicated(self):
        report = self.mapper.inspect(EXAMPLE)
        denied = B.summarize(report, denies=[('ui', 'storage'), ('ui', 'storage')])
        self.assertEqual(denied['summary']['violating_edge_count'], 1)
        self.assertEqual(denied['deny_rules'], [{'from': 'ui', 'to': 'storage'}])
        reversed_rule = B.summarize(report, denies=[('storage', 'ui')])
        self.assertEqual(reversed_rule['summary']['violating_edge_count'], 0)

    def test_depth_changes_groups_without_losing_module_edges(self):
        result = B.summarize(self.mapper.inspect(EXAMPLE), depth=2)
        self.assertEqual(result['summary']['group_count'], 4)
        self.assertEqual(result['summary']['crossing_edge_count'], 4)
        self.assertEqual(result['summary']['internal_edge_count'], 0)

    def test_invalid_rules_and_depth_are_refused(self):
        report = self.mapper.inspect(EXAMPLE)
        for depth in [0, -1, True, 1.5]:
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                B.summarize(report, depth)
        for rule in [('ui', 'missing'), ('ui', 'ui')]:
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                B.summarize(report, denies=[rule])
        for args in [['--deny', 'ui'], ['--deny', 'ui:'], ['--deny', 'ui:storage:domain'],
                     ['--deny', 'ui:typo'], ['--depth', '0']]:
            code, out, err = self.invoke([str(EXAMPLE)] + args)
            self.assertEqual(code, 2)
            self.assertEqual(out, '')
            self.assertTrue(err)

    def test_cli_json_status_and_text_evidence(self):
        code, out, err = self.invoke([str(EXAMPLE), '--json', '--strict'])
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(json.loads(out)['summary']['crossing_edge_count'], 3)
        code, out, err = self.invoke([str(EXAMPLE), '--deny', 'ui:storage'])
        self.assertEqual(code, 1)
        self.assertIn('ui -> storage [DENIED]', out)
        self.assertIn('ui/main.py:2', out)
        self.assertFalse(err)

    def test_warnings_and_strict_status_are_preserved_without_execution(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary)
            marker = root / 'executed'
            (root / 'main.py').write_text(
                f"open({str(marker)!r}, 'w').write('ran')\n"
                "import importlib\nimportlib.import_module('helper')\nimport main\n",
                encoding='utf-8')
            (root / 'broken.py').write_text('def bad(\n', encoding='utf-8')
            result = B.summarize(B.scan(root, self.mapper))
            self.assertEqual(len(result['issues']), 1)
            self.assertEqual(result['cycles'], [['main']])
            self.assertEqual(result['dynamic_imports'][0]['line'], 3)
            self.assertEqual(self.invoke([str(root), '--json'])[0], 0)
            self.assertEqual(self.invoke([str(root), '--strict'])[0], 1)
            self.assertFalse(marker.exists())

    def test_repeated_imports_keep_both_locations(self):
        report = self.mapper.inspect(EXAMPLE)
        module = next(x for x in report['modules'] if x['module'] == 'ui.main')
        repeated = copy.deepcopy(module['imports'][0])
        repeated['line'] = 19
        module['imports'].append(repeated)
        result = B.summarize(report)
        link = next(x for x in result['boundaries'] if (x['from'], x['to']) == ('ui', 'domain'))
        self.assertEqual([x['line'] for x in link['edges'][0]['occurrences']], [1, 19])
        self.assertEqual(link['module_edge_count'], 1)

    def test_empty_tree_and_unknown_groups(self):
        report = {'modules': [], 'edges': [], 'issues': [], 'cycles': []}
        result = B.summarize(report)
        self.assertEqual(result['summary']['module_count'], 0)
        self.assertEqual(result['boundaries'], [])
        with self.assertRaisesRegex(ValueError, 'unknown group'):
            B.summarize(report, denies=[('a', 'b')])

    def test_order_does_not_change_report(self):
        report = self.mapper.inspect(EXAMPLE)
        baseline = B.summarize(report)
        rng = random.Random(737)
        for _ in range(30):
            rng.shuffle(report['modules'])
            rng.shuffle(report['edges'])
            for item in report['modules']:
                rng.shuffle(item['imports'])
            self.assertEqual(B.summarize(report), baseline)

    def test_outside_root_is_rejected_before_mapper(self):
        class NoReads:
            def source_files(self, root):
                raise AssertionError('must not enumerate outside workspace')
        with self.assertRaisesRegex(ValueError, 'inside the current workspace'):
            B.scan(Path('/tmp'), NoReads())


if __name__ == '__main__':
    unittest.main()
