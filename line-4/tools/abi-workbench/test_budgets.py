"""Budget boundaries and alias amplification, without network or file writes."""
import contextlib
import io
import unittest
from unittest.mock import patch
import abi_workbench as abi


class BudgetTests(unittest.TestCase):
    def test_hex_boundary_and_selector_allowance(self):
        with patch.object(abi, 'MAX_DATA_BYTES', 32):
            self.assertEqual(abi.parse_data('0x'+'00'*32), bytes(32))
            self.assertEqual(len(abi.parse_data('0x'+'00'*36, call=True)), 36)
            for call, size in [(False, 33), (True, 37)]:
                with self.assertRaisesRegex(ValueError, 'budget'):
                    abi.parse_data('0x'+'00'*size, call=call)

    def test_json_utf8_boundary(self):
        text = '["🐸"]'
        with patch.object(abi, 'MAX_ARGS_BYTES', len(text.encode())):
            self.assertEqual(abi.parse_args(text), ['🐸'])
            with self.assertRaisesRegex(ValueError, 'input limit'):
                abi.parse_args(text+' ')

    def test_deep_and_duplicate_json(self):
        for text in ['['*2000+']'*2000, '[{"a":1,"a":2}]']:
            with self.assertRaises(ValueError):
                abi.parse_args(text)

    def test_tuple_parameter_limit(self):
        p = [{'type': 'bool'}]*(abi.MAX_PARAMS+1)
        for action in [lambda: abi.encode_tuple(p, [True]*len(p)),
                       lambda: abi.decode_tuple(p, bytes(32*len(p)))]:
            with self.assertRaisesRegex(ValueError, 'parameters'):
                action()

    def test_aggregate_encoding_and_multibyte_value(self):
        p = [{'type': 'string'}]*2
        with patch.object(abi, 'MAX_DATA_BYTES', 160):
            self.assertEqual(len(abi.encode_tuple(p, ['a', ''])), 160)
            with self.assertRaisesRegex(ValueError, 'budget'):
                abi.encode_tuple(p, ['a', 'b'])
            with self.assertRaisesRegex(ValueError, 'budget'):
                abi.encode_value('string', '🐸'*40)

    def test_aliases_charged_before_copy(self):
        p = [{'type': 'bytes'}]*3
        # Three pointers to a single 64-byte tail. Physical bytes fit 160;
        # canonical decoded footprint would need 288 bytes.
        data = abi.word(96)*3 + abi.word(1) + b'x'.ljust(32, b'\0')
        with patch.object(abi, 'MAX_DATA_BYTES', 160):
            with self.assertRaisesRegex(ValueError, 'decoded tuple'):
                abi.decode_tuple(p, data)

    def test_direct_decode_size_and_declared_huge_length(self):
        with patch.object(abi, 'MAX_DATA_BYTES', 64):
            with self.assertRaisesRegex(ValueError, 'input data'):
                abi.decode_tuple([], bytes(96))
            with self.assertRaisesRegex(ValueError, 'decoded tuple'):
                abi.decode_tuple([{'type': 'bytes'}], abi.word(32)+abi.word(2**255))

    def test_cli_refusal_without_success_output(self):
        for command, flag, text in [('encode', '--args', ' '*33),
                                     ('decode', '--data', '0x'+'00'*33),
                                     ('decode-call', '--data', '0x'+'00'*37)]:
            out, err = io.StringIO(), io.StringIO()
            with patch.object(abi, 'MAX_DATA_BYTES', 32), patch.object(abi, 'MAX_ARGS_BYTES', 32), \
                 patch.object(abi, 'load_function', return_value=({'outputs': []}, 'f()')), \
                 patch('sys.argv', ['abi', command, '--abi', 'unused.json', '--function', 'f', flag, text]), \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(abi.main(), 2)
            self.assertEqual(out.getvalue(), '')
            self.assertTrue(err.getvalue().startswith('error: '))


if __name__ == '__main__':
    unittest.main()
