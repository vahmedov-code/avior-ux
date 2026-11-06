"""Offline regressions: no credentials or real HTTP requests are used."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parent))
import wordstat_collect as collector


class SmokeTests(unittest.TestCase):
    def exercise(self, response, limit=22, http_error=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            class Opener:
                def open(self, request, timeout):
                    calls.append(request.full_url)
                    if http_error:
                        raise HTTPError(request.full_url, 403, 'Forbidden', {}, None)
                    body = {'results': []} if request.full_url.endswith('/regions') else response
                    return io.StringIO(json.dumps(body))

            args = ['collector', '--smoke-first', '--max-calls', str(limit),
                    '--out', str(root / 'out'), '--cache', str(root / 'cache')]
            with patch.object(sys, 'argv', args), patch.dict(os.environ, {
                'YANDEX_API_KEY': 'test-placeholder', 'YANDEX_FOLDER_ID': 'test-folder'
            }), patch.object(collector, 'build_opener', return_value=Opener()), \
                patch.object(collector.time, 'sleep'), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = collector.main()
                metadata = None
                if code == 0:
                    metadata = collector.read_json(root / 'out/metadata.json')
                    self.assertEqual(collector.main(), 0)
                    self.assertEqual(len(calls), metadata['api_calls_this_run'])
            return code, calls, metadata

    def test_total_only_response_is_valid_and_cached(self):
        code, calls, metadata = self.exercise({'totalCount': '7'})
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 22)
        self.assertEqual(len(metadata['top_response_details']), 11)
        self.assertTrue(all(item['results_count'] == item['associations_count'] == 0
                            for item in metadata['top_response_details']))

    def test_explicit_empty_lists_are_valid(self):
        code, calls, _ = self.exercise({'totalCount': '7', 'results': [], 'associations': []})
        self.assertEqual((code, len(calls)), (0, 22))

    def test_limit_includes_probe(self):
        code, calls, _ = self.exercise({'totalCount': '7'}, limit=1)
        self.assertEqual((code, len(calls)), (1, 1))

    def test_http_error_does_not_retry_or_continue(self):
        code, calls, _ = self.exercise({}, http_error=True)
        self.assertEqual((code, len(calls)), (1, 1))

    def test_missing_total_is_rejected(self):
        code, calls, _ = self.exercise({'results': []})
        self.assertEqual((code, len(calls)), (1, 1))

    def test_non_list_associations_are_rejected(self):
        code, calls, _ = self.exercise({'totalCount': '7', 'associations': {}})
        self.assertEqual((code, len(calls)), (1, 1))


if __name__ == '__main__':
    unittest.main()
