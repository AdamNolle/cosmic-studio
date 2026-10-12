"""Portable source-only stock packaging guards, not package/compiler evidence."""
import ast
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('studio_stock', Path(__file__).with_name('build_stock.py'))
stock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stock)


def literal(path, name):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError('Missing literal ' + name)


class StockPackageGuards(unittest.TestCase):
    def test_pins_match_existing_approved_builders(self):
        self.assertEqual(stock.PINS['cosmic-comp'], literal(ROOT / 'native/compositor/build.py', 'COMP'))
        self.assertEqual(stock.PINS['cosmic-panel'], literal(ROOT / 'native/build_shell.py', 'SOURCES')['cosmic-panel'][0])

    def test_publication_is_explicit_true_full_source_not_replacement_metadata(self):
        old = 'cosmic-comp (0.1) jammy; urgency=medium\n\n  * Original\n'
        revision = stock.PINS['cosmic-comp']
        version, text = stock.publication(old, 'cosmic-comp', revision)
        self.assertEqual(version, '0.1+studio.stock.git' + revision)
        self.assertTrue(text.endswith(old))
        self.assertIn('unmodified stock build from upstream commit ' + revision, text)
        for bad in (revision[:7], 'latest', 'f' * 39):
            with self.assertRaises(ValueError):
                stock.publication(old, 'cosmic-comp', bad)
        with self.assertRaises(ValueError):
            stock.publication(old, 'cosmic-panel', revision)

    def test_changed_stock_lock_is_refused_without_hiding_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'Cargo.lock').write_bytes(b'original')
            stock.verify_lock(source, b'original')
            (source / 'Cargo.lock').write_bytes(b'drifted')
            with self.assertRaises(RuntimeError):
                stock.verify_lock(source, b'original')
            self.assertEqual((source / 'Cargo.lock').read_bytes(), b'drifted')

    def test_only_publication_changelog_can_be_modified(self):
        with patch.object(stock.subprocess, 'check_output', return_value='debian/changelog\n'), \
             patch.object(stock.subprocess, 'run') as run:
            stock.verify_pristine(Path('owned-source-fixture'))
            self.assertIn('git diff --exit-code HEAD', run.call_args.args[0][-1])
        for changed in ('src/lib.rs\n', 'Cargo.lock\n', 'debian/rules\n', 'iced\n'):
            with patch.object(stock.subprocess, 'check_output', return_value=changed), \
                 patch.object(stock.subprocess, 'run') as run:
                with self.assertRaises(RuntimeError):
                    stock.verify_pristine(Path('owned-source-fixture'))
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
