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
            client = collector.Client('test-folder', root / 'cache', max_calls=2, timeout=90, retries=0)
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
            resumed = collector.Client('test-folder', root / 'cache', max_calls=1, timeout=90, retries=0)
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
        self.assertEqual((code, len(calls)), (2, 1))

    def test_http_error_does_not_retry_or_continue(self):
        code, calls, _ = self.exercise({}, http_error=True)
        self.assertEqual((code, len(calls)), (1, 1))

    def test_invalid_total_is_rejected(self):
        code, calls, _ = self.exercise({'totalCount': 'invalid', 'results': []})
        self.assertEqual((code, len(calls)), (1, 1))

    def test_omitted_default_zero_response_is_valid(self):
        code, calls, _ = self.exercise({})
        self.assertEqual((code, len(calls)), (0, 22))

    def test_non_list_associations_are_rejected(self):
        code, calls, _ = self.exercise({'totalCount': '7', 'associations': {}})
        self.assertEqual((code, len(calls)), (1, 1))



class ResilienceTests(unittest.TestCase):
    def request_scenario(self, effects, *, limit=10, retries=2):
        with tempfile.TemporaryDirectory() as directory:
            client = collector.Client('test-folder', Path(directory), max_calls=limit,
                                      retries=retries, retry_delay=2, timeout=45)
            opener = unittest.mock.Mock()
            opener.open.side_effect = effects
            failure = None
            output = io.StringIO()
            with patch.dict(os.environ, {'YANDEX_API_KEY': 'test-secret'}), \
                patch.object(collector, 'build_opener', return_value=opener), \
                patch.object(collector.time, 'sleep') as sleep, \
                contextlib.redirect_stdout(output):
                try:
                    client.call('regions', {'phrase': 'test'})
                except RuntimeError as exc:
                    failure = exc
            cache_text = ''.join(p.read_text(encoding='utf-8') for p in Path(directory).glob('*.json'))
            self.assertNotIn('test-secret', cache_text + output.getvalue() + str(failure))
            return client.calls, opener.open.call_count, failure, cache_text, [c.args[0] for c in sleep.call_args_list]

    def test_timeout_retries_then_succeeds_with_exponential_wait(self):
        calls, opens, error, cache, delays = self.request_scenario([
            URLError(TimeoutError('test-secret')), TimeoutError('test-secret'),
            io.StringIO('{"results":[]}')])
        self.assertEqual((calls, opens), (3, 3))
        self.assertIsNone(error)
        self.assertIn('response', cache)
        self.assertEqual(delays, [2, 4, 1])

    def test_retry_exhaustion_is_recoverable_and_not_cached(self):
        calls, opens, error, cache, delays = self.request_scenario([TimeoutError()] * 3)
        self.assertEqual((calls, opens), (3, 3))
        self.assertIsInstance(error, collector.RecoverableAPIError)
        self.assertEqual(cache, '')
        self.assertEqual(delays, [2, 4])

    def test_global_limit_counts_failed_attempts_and_prevents_extra_retry(self):
        calls, opens, error, cache, delays = self.request_scenario([TimeoutError()] * 6, limit=2, retries=5)
        self.assertEqual((calls, opens), (2, 2))
        self.assertIsInstance(error, collector.CallLimitError)
        self.assertEqual(cache, '')
        self.assertEqual(delays, [2])

    def test_retry_timeouts_increase_but_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            client = collector.Client('test-folder', Path(directory), max_calls=3, timeout=45)
            opener = unittest.mock.Mock()
            opener.open.side_effect = [TimeoutError(), TimeoutError(), io.StringIO('{"results":[]}')]
            with patch.dict(os.environ, {'YANDEX_API_KEY': 'test-placeholder'}), \
                patch.object(collector, 'build_opener', return_value=opener), \
                patch.object(collector.time, 'sleep'), contextlib.redirect_stdout(io.StringIO()):
                client.call('regions', {'phrase': 'test'})
            self.assertEqual([c.kwargs['timeout'] for c in opener.open.call_args_list], [45, 90, 135])

    def test_invalid_tree_is_not_cached_or_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            client = collector.Client('test-folder', Path(directory))
            opener = unittest.mock.Mock()
            opener.open.return_value = io.StringIO('{"regions":[]}')
            with patch.dict(os.environ, {'YANDEX_API_KEY': 'test-placeholder'}), \
                patch.object(collector, 'build_opener', return_value=opener), \
                patch.object(collector.time, 'sleep'):
                with self.assertRaises(RuntimeError):
                    client.call('getRegionsTree', {})
            self.assertEqual(client.calls, 1)
            self.assertEqual(list(Path(directory).glob('*.json')), [])

    def test_offline_partial_does_not_prompt_retry_or_open_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            collector.dump(root / 'config.json', {
                'regions': [{'label': 'Russia', 'ids': ['225']}],
                'groups': [{'name': 'test', 'seeds': ['alpha']}],
                'collect_city_distribution': False})
            args = ['collector', '--offline', '--config', str(root / 'config.json'),
                    '--cache', str(root / 'cache'), '--out', str(root / 'out')]
            with patch.object(sys, 'argv', args), \
                patch.dict(os.environ, {'YANDEX_FOLDER_ID': 'test-folder'}, clear=True), \
                patch.object(collector, 'build_opener') as opener, \
                patch.object(collector.getpass, 'getpass') as prompt, \
                patch.object(collector.time, 'sleep') as sleep, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(collector.main(), 2)
                opener.assert_not_called()
                prompt.assert_not_called()
                sleep.assert_not_called()
            metadata = collector.read_json(root / 'out/metadata.json')
            self.assertFalse(metadata['complete'])
            self.assertEqual(metadata['api_calls_this_run'], 0)
            self.assertEqual(metadata['top_responses'], 0)
            self.assertEqual(len(metadata['pending_requests']), 1)

    def test_rate_limit_retry_after_is_respected(self):
        calls, opens, error, _, delays = self.request_scenario([
            HTTPError('https://example.test', 429, 'test-secret', {'Retry-After': '5'}, None),
            io.StringIO('{"results":[]}')])
        self.assertEqual((calls, opens), (2, 2))
        self.assertIsNone(error)
        self.assertEqual(delays, [5, 1])

    def test_temporary_http_errors_are_retried(self):
        for status in [408, 500, 502, 503, 504]:
            with self.subTest(status=status):
                calls, opens, error, _, _ = self.request_scenario([
                    HTTPError('https://example.test', status, 'test-secret', {}, None),
                    io.StringIO('{"results":[]}')])
                self.assertEqual((calls, opens), (2, 2))
                self.assertIsNone(error)

    def test_bad_request_and_auth_errors_are_not_retried(self):
        for status in [400, 401, 403, 404]:
            with self.subTest(status=status):
                calls, opens, error, cache, delays = self.request_scenario([
                    HTTPError('https://example.test', status, 'test-secret', {}, None)])
                self.assertEqual((calls, opens), (1, 1))
                self.assertIsInstance(error, RuntimeError)
                self.assertNotIsInstance(error, collector.RecoverableAPIError)
                self.assertEqual((cache, delays), ('', []))

    def test_tls_certificate_failure_is_not_retried(self):
        calls, opens, error, cache, delays = self.request_scenario([
            URLError(collector.ssl.SSLCertVerificationError(1, 'test-secret'))])
        self.assertEqual((calls, opens), (1, 1))
        self.assertNotIsInstance(error, collector.RecoverableAPIError)
        self.assertEqual((cache, delays), ('', []))

    def test_truncated_response_is_retried(self):
        calls, opens, error, _, _ = self.request_scenario([
            collector.IncompleteRead(b'partial'), io.StringIO('{"results":[]}')])
        self.assertEqual((calls, opens), (2, 2))
        self.assertIsNone(error)

    def main_scenario(self, *, passes=1, limit=30, failed_method='regions', rerun=False, prompt=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {'num_phrases': 100, 'regions': [{'label': 'Russia', 'ids': ['225']}],
                      'collect_city_distribution': failed_method == 'regions',
                      'groups': [{'name': 'test', 'seeds': ['alpha', 'beta']}]}
            collector.dump(root / 'config.json', config)
            log = []
            failures = 0

            class Opener:
                def open(self, request, timeout):
                    nonlocal failures
                    method = request.full_url.rsplit('/', 1)[-1]
                    phrase = json.loads(request.data)['phrase']
                    log.append((method, phrase))
                    if method == failed_method and phrase == 'alpha' and failures < 2:
                        failures += 1
                        raise URLError(TimeoutError('test-secret'))
                    body = {'totalCount': '7'} if method == 'topRequests' else {'results': []}
                    return io.StringIO(json.dumps(body))

            args = ['collector', '--config', str(root / 'config.json'), '--out', str(root / 'out'),
                    '--cache', str(root / 'cache'), '--max-calls', str(limit),
                    '--retries', '1', '--retry-delay', '0', '--passes', str(passes)]
            if prompt:
                args.append('--prompt-credentials')
            env = {'YANDEX_FOLDER_ID': 'test-folder'}
            if not prompt:
                env['YANDEX_API_KEY'] = 'test-secret'
            text = io.StringIO()
            with patch.object(sys, 'argv', args), patch.dict(os.environ, env, clear=True), \
                patch.object(sys.stdin, 'isatty', return_value=True), \
                patch.object(collector.getpass, 'getpass', return_value='test-secret') as getpass, \
                patch.object(collector, 'build_opener', return_value=Opener()), \
                patch.object(collector.time, 'sleep'), \
                contextlib.redirect_stdout(text), contextlib.redirect_stderr(text):
                code = collector.main()
                metadata = collector.read_json(root / 'out/metadata.json')
                totals = list(collector.csv.DictReader((root / 'out/seed_totals.csv').open(encoding='utf-8-sig')))
                first_count = len(log)
                second = None
                if rerun:
                    second_code = collector.main()
                    second = (second_code, collector.read_json(root / 'out/metadata.json'), len(log)-first_count)
                self.assertEqual(getpass.call_count, int(prompt))
            self.assertNotIn('test-secret', text.getvalue())
            return code, metadata, totals, log, first_count, second

    def test_city_timeout_does_not_block_primary_results_or_other_cities(self):
        code, metadata, totals, log, count, second = self.main_scenario(rerun=True)
        self.assertEqual(code, 2)
        self.assertFalse(metadata['complete'])
        self.assertEqual(metadata['top_responses'], 2)
        self.assertEqual(metadata['city_responses'], 1)
        self.assertEqual(len(totals), 2)
        self.assertEqual(len(metadata['pending_requests']), 1)
        self.assertEqual(log[:2], [('topRequests', 'alpha'), ('topRequests', 'beta')])
        self.assertEqual(count, 5)
        self.assertEqual(second[0], 0)
        self.assertTrue(second[1]['complete'])
        self.assertEqual(second[2], 1)

    def test_second_pass_recovers_with_one_hidden_key_entry(self):
        code, metadata, _, log, count, _ = self.main_scenario(passes=2, prompt=True)
        self.assertEqual(code, 0)
        self.assertTrue(metadata['complete'])
        self.assertEqual(metadata['pending_requests'], [])
        self.assertEqual((count, len(log)), (6, 6))
        self.assertEqual(log.count(('topRequests', 'alpha')), 1)
        self.assertEqual(log.count(('topRequests', 'beta')), 1)

    def test_failed_frequency_is_not_written_as_zero(self):
        code, metadata, totals, _, _, _ = self.main_scenario(failed_method='topRequests')
        self.assertEqual(code, 2)
        self.assertFalse(metadata['complete'])
        self.assertEqual([r['seed'] for r in totals], ['beta'])
        self.assertEqual(metadata['pending_requests'][0]['seed'], 'alpha')

    def test_call_limit_is_shared_across_all_passes(self):
        code, metadata, _, log, count, _ = self.main_scenario(passes=3, limit=3)
        self.assertEqual(code, 2)
        self.assertFalse(metadata['complete'])
        self.assertEqual((count, len(log), metadata['api_calls_this_run']), (3, 3, 3))

if __name__ == '__main__':
    unittest.main()
