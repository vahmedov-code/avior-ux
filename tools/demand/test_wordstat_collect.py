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
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).parent))
import wordstat_collect as collector


class SmokeTests(unittest.TestCase):
    def exercise(self, response, limit=22, http_error=False, config=None, tree=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            class Opener:
                def open(self, request, timeout):
                    calls.append(request.full_url)
                    if http_error:
                        raise HTTPError(request.full_url, 403, 'Forbidden', {}, None)
                    body = (tree if request.full_url.endswith('/getRegionsTree') else
                            {'results': []} if request.full_url.endswith('/regions') else response)
                    return io.StringIO(json.dumps(body))

            args = ['collector', '--smoke-first', '--max-calls', str(limit),
                    '--out', str(root / 'out'), '--cache', str(root / 'cache')]
            if config is not None:
                collector.dump(root / 'config.json', config)
                args.extend(['--config', str(root / 'config.json')])
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

    def test_region_tree_resolves_labels_and_counts_free_call(self):
        config = {'num_phrases': 100, 'regions': [{'label': 'placeholder', 'ids': ['225']}],
                  'groups': [{'name': 'test', 'seeds': ['test phrase']}],
                  'collect_city_distribution': True, 'collect_region_tree': True}
        tree = {'regions': [{'id': '225', 'label': 'Russia', 'children': []}]}
        code, calls, metadata = self.exercise({'totalCount': '7'}, limit=3, config=config, tree=tree)
        self.assertEqual((code, len(calls)), (0, 3))
        self.assertEqual(metadata['config']['regions'][0]['label'], 'Russia')

    def test_full_expanded_plan_uses_241_calls_and_cached_rerun(self):
        config = collector.read_json(Path(__file__).with_name('research-repair-expanded.json'))
        tree = {'regions': [{'id': '225', 'label': 'Russia', 'children': [
            {'id': '1', 'label': 'Moscow region', 'children': [
                {'id': '213', 'label': 'Moscow'}]},
            {'id': '10174', 'label': 'Leningrad region', 'children': [
                {'id': '2', 'label': 'Saint Petersburg'}]}]}]}
        code, calls, metadata = self.exercise({'totalCount': '7'}, limit=241, config=config, tree=tree)
        self.assertEqual((code, len(calls)), (0, 241))
        self.assertEqual(len(metadata['top_response_details']), 200)
        self.assertEqual(sum(url.endswith('/getRegionsTree') for url in calls), 1)
        self.assertEqual(sum(url.endswith('/regions') for url in calls), 40)

    def test_missing_region_stops_after_probe_and_tree(self):
        config = {'regions': [{'label': 'placeholder', 'ids': ['213']}],
                  'groups': [{'name': 'test', 'seeds': ['test phrase']}],
                  'collect_city_distribution': True, 'collect_region_tree': True}
        tree = {'regions': [{'id': '225', 'label': 'Russia', 'children': []}]}
        code, calls, _ = self.exercise({'totalCount': '7'}, limit=3, config=config, tree=tree)
        self.assertEqual((code, len(calls)), (1, 2))

    def test_network_timeout_keeps_cache_and_resumes_without_repeating_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = {'phrase': 'test'}
            client = collector.Client('test-folder', root / 'cache', max_calls=2, timeout=90)
            opener = unittest.mock.Mock()
            opener.open.side_effect = [io.StringIO('{"totalCount":"7"}'), URLError(TimeoutError())]
            with patch.dict(os.environ, {'YANDEX_API_KEY': 'test-placeholder'}), \
                patch.object(collector, 'build_opener', return_value=opener), \
                patch.object(collector.time, 'sleep'):
                client.call('topRequests', payload)
                with self.assertRaisesRegex(RuntimeError, 'TimeoutError'):
                    client.call('regions', payload)
            self.assertEqual(client.calls, 2)
            self.assertEqual(len(list((root / 'cache').glob('*.json'))), 1)
            self.assertEqual(opener.open.call_count, 2)
            self.assertEqual(opener.open.call_args.kwargs['timeout'], 90)
            resumed = collector.Client('test-folder', root / 'cache', max_calls=1, timeout=90)
            with patch.dict(os.environ, {'YANDEX_API_KEY': 'test-placeholder'}), \
                patch.object(collector, 'build_opener', return_value=opener), \
                patch.object(collector.time, 'sleep'):
                resumed.call('topRequests', payload)
                self.assertEqual(resumed.calls, 0)
                opener.open.side_effect = [io.StringIO('{"results":[]}')]
                resumed.call('regions', payload)
            self.assertEqual(resumed.calls, 1)
            self.assertEqual(len(list((root / 'cache').glob('*.json'))), 2)

    def test_empty_hidden_key_stops_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = ['collector', '--prompt-credentials', '--smoke-first',
                    '--cache', str(root / 'cache'), '--out', str(root / 'out')]
            with patch.object(sys, 'argv', args), \
                patch.dict(os.environ, {'YANDEX_FOLDER_ID': 'test-folder'}, clear=True), \
                patch.object(sys.stdin, 'isatty', return_value=True), \
                patch.object(collector.getpass, 'getpass', return_value=''), \
                patch.object(collector, 'build_opener') as opener, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(collector.main(), 1)
                opener.assert_not_called()

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
