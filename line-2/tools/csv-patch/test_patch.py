"""Behavioral checks with fixtures confined to test/scratch/."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import patch


class PatchTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, name, text):
        p = self.root / name
        p.write_bytes(text.encode('utf-8'))
        return p

    def pair(self):
        return (self.file('before.csv', 'id,v\na,old\nb,drop\nc,same\n'),
                self.file('after.csv', 'id,v\nd,new\nc,same\na,edited\n'))

    def test_add_remove_edit_and_deterministic_order(self):
        a, b = self.pair()
        p = patch.plan(a, b, ['id'])
        self.assertEqual(len(p['operations']), 3)
        self.assertEqual(patch.apply(a, p), b'id,v\na,edited\nc,same\nd,new\n')
        self.assertEqual(a.read_text(), 'id,v\na,old\nb,drop\nc,same\n')

    def test_stale_even_if_semantically_equal(self):
        a, b = self.pair()
        p = patch.plan(a, b, ['id'])
        a.write_bytes(a.read_bytes().replace(b'\n', b'\r\n'))
        with self.assertRaisesRegex(patch.InputError, 'changed since review'):
            patch.apply(a, p)

    def test_tampered_plan_and_preconditions(self):
        a, b = self.pair()
        original = patch.plan(a, b, ['id'])
        for alter in ('before', 'after', 'missing', 'duplicate', 'null', 'key'):
            p = copy.deepcopy(original)
            if alter == 'before':
                p['operations'][0]['before']['v'] = 'wrong'
            elif alter == 'after':
                p['operations'][0]['after']['v'] = 'unreviewed'
            elif alter == 'missing':
                p['operations'].pop()
            elif alter == 'duplicate':
                p['operations'].append(p['operations'][0])
            elif alter == 'null':
                p['operations'][0] = {'before': None, 'after': None}
            else:
                p['operations'][0]['after']['id'] = 'different'
            with self.subTest(alter=alter), self.assertRaises(patch.InputError):
                patch.apply(a, p)

    def test_ambiguous_empty_and_invalid_csv_refused(self):
        a, b = self.pair()
        for text in ('id,v\na,x\na,x\n', 'id,v\n,x\n', 'id,v\na\n',
                     'id,id\na,x\n', 'id,v\n"unterminated'):
            bad = self.file('bad.csv', text)
            with self.subTest(text=text), self.assertRaises(patch.InputError):
                patch.plan(a, bad, ['id'])

    def test_schema_refused_but_column_order_preserves_baseline(self):
        a, b = self.pair()
        swapped = self.file('swapped.csv', 'v,id\nnew,a\n')
        self.assertEqual(patch.apply(a, patch.plan(a, swapped, ['id'])), b'id,v\na,new\n')
        extra = self.file('extra.csv', 'id,v,extra\na,new,x\n')
        with self.assertRaisesRegex(patch.InputError, 'schema'):
            patch.plan(a, extra, ['id'])

    def test_composite_keys_multiline_unicode_and_literal_formula(self):
        a = self.file('a.csv', '\ufeffid,part,v\nab,c,"one\ntwo"\na,bc,=1+1\n')
        b = self.file('b.csv', 'id,part,v\na,bc,=1+1\nab,c,α\n')
        result = patch.apply(a, patch.plan(a, b, ['id', 'part']))
        self.assertEqual(result.decode(), 'id,part,v\na,bc,=1+1\nab,c,α\n')

    def test_header_only_and_no_change(self):
        a = self.file('a.csv', 'id,v\n')
        b = self.file('b.csv', 'id,v\na,x\n')
        self.assertEqual(patch.apply(a, patch.plan(a, b, ['id'])), b'id,v\na,x\n')
        self.assertEqual(patch.apply(b, patch.plan(b, a, ['id'])), b'id,v\n')
        self.assertEqual(patch.plan(b, b, ['id'])['operations'], [])

    def test_malformed_patch_shapes_and_hashes(self):
        a, b = self.pair()
        original = patch.plan(a, b, ['id'])
        for field, value in [('format', 'unknown'), ('keys', []), ('keys', ['id', 'id']),
                             ('keys', [4]), ('header', ['id']), ('operations', {}),
                             ('baseline_sha256', 'x'), ('result_sha256', None)]:
            p = copy.deepcopy(original)
            p[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(patch.InputError):
                patch.apply(a, p)

    def test_workspace_boundary_and_byte_limit(self):
        with self.assertRaises(patch.InputError):
            patch.read_local(Path.cwd().parent / 'not-read.csv', 10)
        a = self.file('a.csv', '12345')
        with self.assertRaises(patch.InputError):
            patch.read_local(a, 4)
        link = self.root / 'link.csv'
        link.symlink_to(Path.cwd().parent / 'not-read.csv')
        with self.assertRaises(patch.InputError):
            patch.read_local(link, 10)

    def test_cli_success_and_failure_have_no_partial_csv(self):
        a, b = self.pair()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = patch.main(['plan', str(a), str(b), '--key', 'id'])
        self.assertEqual(code, 0)
        p = self.file('patch.json', out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(patch.main(['apply', str(a), str(p)]), 0)
        self.assertIn('a,edited', out.getvalue())
        p.write_text('{"format":1,"format":2}')
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(patch.main(['apply', str(a), str(p)]), 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('duplicate JSON', err.getvalue())

    def test_inspect_validates_without_emitting_csv(self):
        a, b = self.pair()
        plan = patch.plan(a, b, ['id'])
        summary = patch.inspect(a, plan)
        self.assertEqual(summary['operations'],
                         {'added': 1, 'removed': 1, 'changed': 1, 'total': 3})
        self.assertTrue(summary['valid'])
        self.assertEqual(summary['result_sha256'], plan['result_sha256'])
        a.write_text('id,v\na,edited\n')
        with self.assertRaisesRegex(patch.InputError, 'changed since review'):
            patch.inspect(a, plan)


if __name__ == '__main__':
    unittest.main()
