#!/usr/bin/env python3
"""Collect official Yandex Search API Wordstat data. Python 3.10+, stdlib only."""
import argparse
import csv
import getpass
import hashlib
from http.client import IncompleteRead, RemoteDisconnected
import json
import os
from pathlib import Path
import re
import socket
import ssl
import sys
import time
import warnings
from datetime import datetime, timezone
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

BASE = 'https://searchapi.api.cloud.yandex.net/v2/wordstat/'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def dump(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def review(phrase):
    if re.search(r'бесплат|скачать|своими руками|самостоятельно|ваканси|обучени|курс|исходник', phrase.lower()):
        return 'Проверить: обучение/бесплатное/работа'
    return 'Проверить вручную намерение и соответствие продукту'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def validate_response(method, result):
    if not isinstance(result, dict) or 'error' in result:
        raise RuntimeError('Неожиданный формат ответа API; ответ не кешируется.')
    if method == 'getRegionsTree':
        nodes = result.get('regions')
        if not isinstance(nodes, list) or not nodes:
            raise RuntimeError('Некорректное дерево регионов; ответ не кешируется.')
        pending = list(nodes)
        while pending:
            node = pending.pop()
            if (not isinstance(node, dict) or not isinstance(node.get('id'), str)
                    or not isinstance(node.get('label'), str)
                    or not isinstance(node.get('children', []), list)):
                raise RuntimeError('Некорректная строка дерева регионов; ответ не кешируется.')
            pending.extend(node.get('children', []))
        return
    if method == 'topRequests':
        if (not str(result.get('totalCount', '0')).isdigit()
                or (result and not any(k in result for k in ('totalCount', 'results', 'associations')))):
            raise RuntimeError('Некорректный ответ topRequests; ответ не кешируется.')
        kinds = ('results', 'associations')
    elif method == 'regions':
        kinds = ('results',)
    else:
        kinds = ()
    for kind in kinds:
        items = result.get(kind, [])
        if not isinstance(items, list):
            raise RuntimeError('Некорректный список в ответе API; ответ не кешируется.')
        for item in items:
            field = 'region' if method == 'regions' else 'phrase'
            if (not isinstance(item, dict) or not isinstance(item.get(field), str)
                    or not str(item.get('count', '0')).isdigit()):
                raise RuntimeError('Некорректная строка в ответе API; ответ не кешируется.')


class RecoverableAPIError(RuntimeError):
    """A transient request failure; keep other work and report pending requests."""


class CallLimitError(RecoverableAPIError):
    pass


class Client:
    def __init__(self, folder, cache, max_calls=30, offline=False, timeout=40,
                 retries=2, retry_delay=2):
        self.timeout, self.retries, self.retry_delay = timeout, retries, retry_delay
        self.folder, self.cache = folder, cache
        self.max_calls, self.offline, self.calls = max_calls, offline, 0
        self.cache.mkdir(parents=True, exist_ok=True)

    def call(self, method, payload):
        body = dict(payload, folderId=self.folder)
        key = hashlib.sha256(json.dumps([method, body], sort_keys=True).encode()).hexdigest()
        path = self.cache / (key + '.json')
        if path.exists():
            saved = read_json(path)
            validate_response(method, saved['response'])
            return saved['response'], saved['collected_at']
        if self.offline:
            raise RecoverableAPIError('В кеше отсутствует ответ; офлайн-запрос не выполняется.')
        token = os.environ.get('YANDEX_API_KEY')
        if not token:
            raise RuntimeError('Задайте YANDEX_API_KEY локально. Не отправляйте ключ в чат.')
        request = Request(BASE + method, data=json.dumps(body).encode(), headers={
            'Authorization': 'Api-Key ' + token, 'Content-Type': 'application/json'}, method='POST')
        for attempt in range(self.retries + 1):
            if self.calls >= self.max_calls:
                raise CallLimitError('Достигнут общий лимит попыток API; успешные ответы в кеше.')
            self.calls += 1
            retry_after = 0
            try:
                with build_opener(NoRedirect()).open(request, timeout=min(self.timeout * (attempt + 1), 300)) as response:
                    result = json.load(response)
            except HTTPError as exc:
                code = exc.code
                header = exc.headers.get('Retry-After', '') if exc.headers else ''
                exc.close()
                if code not in (408, 429, 500, 502, 503, 504):
                    raise RuntimeError(f'API вернул HTTP {code}. '
                                       'Ошибка не повторяется автоматически; проверьте доступ и параметры.') from None
                detail = f'HTTP {code}'
                if header.isdigit():
                    retry_after = int(header)
                    if retry_after > 60:
                        raise RuntimeError(f'API вернул HTTP {code} и просит ждать более 60 с. '
                                           'Сбор остановлен; кеш сохранён.') from None
            except (URLError, TimeoutError, ConnectionError, ssl.SSLError,
                    IncompleteRead, RemoteDisconnected) as exc:
                reason = getattr(exc, 'reason', exc)
                if isinstance(reason, ssl.SSLCertVerificationError):
                    raise RuntimeError('Не удалось проверить TLS-сертификат API; '
                                       'автоматических повторов нет.') from None
                if isinstance(reason, TimeoutError) or 'timed out' in str(reason).lower():
                    category = 'превышено время ожидания'
                elif isinstance(reason, ssl.SSLError):
                    category = 'сбой TLS-соединения'
                elif isinstance(reason, socket.gaierror):
                    category = 'сбой DNS'
                else:
                    category = 'обрыв или недоступность соединения'
                detail = f'{category}; {type(reason).__name__}'
            else:
                validate_response(method, result)
                stamp = datetime.now(timezone.utc).isoformat()
                dump(path, {'method': method, 'request': body, 'collected_at': stamp, 'response': result})
                time.sleep(1)
                return result, stamp
            if attempt >= self.retries:
                raise RecoverableAPIError(f'{method}: {detail}; '
                                          f'исчерпаны {self.retries + 1} попытки, ответ не получен.')
            if self.calls >= self.max_calls:
                raise CallLimitError('Достигнут общий лимит попыток API; успешные ответы в кеше.')
            delay = max(min(self.retry_delay * (2 ** attempt), 30), retry_after)
            print(f'Временный сбой {method} ({detail}). '
                  f'Повтор {attempt + 1}/{self.retries} через {delay} с; '
                  f'попыток API: {self.calls}/{self.max_calls}.', flush=True)
            time.sleep(delay)


def csv_write(path, columns, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            # Avoid spreadsheet formula execution when an API phrase begins with a formula marker.
            writer.writerow({k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v)
                             for k, v in row.items()})


def collect(config, client, output):
    candidates, totals, distributions, detail_counts, pending = {}, [], [], [], []
    output.mkdir(parents=True, exist_ok=True)
    city_responses = 0

    def fetch(method, payload, group='', seed='', region=''):
        try:
            return client.call(method, payload)
        except RecoverableAPIError as exc:
            pending.append(dict(method=method, payload=payload, group=group,
                                seed=seed, region=region, error=str(exc)))
            if not isinstance(exc, CallLimitError):
                print(f'Отложено: {method}, {seed or "дерево регионов"}. '
                      'Продолжаю остальные запросы.', flush=True)
            return None

    if config.get('collect_region_tree', False):
        fetched = fetch('getRegionsTree', {})
        if fetched is not None:
            tree, stamp = fetched
            if not isinstance(tree.get('regions'), list) or not tree['regions']:
                raise RuntimeError('API не вернул дерево регионов; сбор остановлен.')
            labels = {}
            nodes = list(tree['regions'])
            while nodes:
                node = nodes.pop()
                labels[str(node['id'])] = node['label']
                nodes.extend(node.get('children', []))
            for scope in config['regions']:
                if any(str(region_id) not in labels for region_id in scope['ids']):
                    raise RuntimeError('Регион плана отсутствует в дереве Wordstat; сбор остановлен.')
                if len(scope['ids']) == 1:
                    scope['label'] = labels[str(scope['ids'][0])]
            dump(output / 'regions_tree.json', {'collected_at': stamp, 'regions': tree['regions']})

    # Collect primary frequencies before optional global city distributions.
    for group in config['groups']:
        for seed in group['seeds']:
            completed = 0
            for region_set in config['regions']:
                payload = {'phrase': seed, 'numPhrases': str(config.get('num_phrases', 100)),
                           'regions': region_set['ids'], 'devices': ['DEVICE_ALL']}
                fetched = fetch('topRequests', payload, group['name'], seed, region_set['label'])
                if fetched is None:
                    continue
                result, stamp = fetched
                completed += 1
                scope = region_set['label']
                detail_counts.append(dict(group=group['name'], seed=seed, region=scope,
                    results_count=len(result.get('results', [])),
                    associations_count=len(result.get('associations', []))))
                totals.append(dict(group=group['name'], seed=seed, region=scope,
                                   count=result.get('totalCount', '0'), collected_at=stamp))
                for kind in ('results', 'associations'):
                    for item in result.get(kind, []):
                        phrase = item['phrase']
                        key = (group['name'], scope, kind, phrase)
                        if key not in candidates:
                            candidates[key] = dict(group=group['name'], region=scope, kind=kind,
                                phrase=phrase, count=item.get('count', '0'), review=review(phrase), seeds=seed,
                                collected_at=stamp)
                        else:
                            candidates[key]['seeds'] += ' | ' + seed
            print(f'Частотности: {seed}: {completed}/{len(config["regions"])} регионов; '
                  f'попыток API: {client.calls}.', flush=True)

    if config.get('collect_city_distribution', True):
        for group in config['groups']:
            for seed in group['seeds']:
                fetched = fetch('regions', {'phrase': seed, 'region': 'REGION_CITIES',
                                            'devices': ['DEVICE_ALL']}, group['name'], seed)
                if fetched is None:
                    continue
                result, stamp = fetched
                city_responses += 1
                for item in result.get('results', []):
                    distributions.append(dict(group=group['name'], seed=seed, region_id=item['region'],
                        count=item.get('count', '0'), share=item.get('share', ''),
                        affinity_index=item.get('affinityIndex', ''), collected_at=stamp))
                print(f'Города: {seed}. Попыток API: {client.calls}.', flush=True)
    csv_write(output / 'candidates.csv', ['group','region','kind','phrase','count','review','seeds','collected_at'], candidates.values())
    csv_write(output / 'seed_totals.csv', ['group','seed','region','count','collected_at'], totals)
    csv_write(output / 'cities.csv', ['group','seed','region_id','count','share','affinity_index','collected_at'], distributions)
    metadata = {'created_at': datetime.now(timezone.utc).isoformat(),
        'complete': not pending, 'pending_requests': pending,
        'api_calls_this_run': client.calls, 'config': config,
        'top_responses': len(totals), 'city_responses': city_responses,
        'top_response_details': detail_counts, 'notes': [
        'Частотности пересекаются: не суммировать.',
        'Широкая частотность, не число людей/кликов/покупателей.',
        'Опущенные нулевые поля успешного proto3-ответа нормализованы в 0.',
        'Неуспешные запросы отсутствуют в CSV и перечислены в pending_requests, это не нулевой спрос.',
        'Оценки цены клика и прибыли отсутствуют: нужны Директ и данные продаж.',
        'Похожие запросы (associations) требуют отдельной проверки.',
        'Для обновления данных используйте новую папку кеша.']}
    dump(output / 'metadata.json', metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('research.json'))
    parser.add_argument('--out', type=Path, default=Path('wordstat-results'))
    parser.add_argument('--cache', type=Path, default=Path('wordstat-cache'))
    parser.add_argument('--max-calls', type=int, default=30)
    parser.add_argument('--timeout', type=float, default=40, help='Ожидание ответа API в секундах (1–300)')
    parser.add_argument('--retries', type=int, default=2, help='Повторы временного сбоя (0–5), учитываются в max-calls')
    parser.add_argument('--retry-delay', type=float, default=2, help='Начальная пауза между повторами (0–30 секунд)')
    parser.add_argument('--passes', type=int, default=2, help='Проходы для отложенных запросов с общим лимитом (1–3)')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--plan', action='store_true', help='Показать план без API-вызовов')
    parser.add_argument('--prompt-credentials', action='store_true',
                        help='Запросить отсутствующие переменные доступа локально; ключ вводится скрыто')
    parser.add_argument('--smoke-first', action='store_true',
                        help='Проверить первую фразу перед сбором, используя общий кеш и лимит')
    args = parser.parse_args()
    try:
        config = read_json(args.config)
        seeds = [s for g in config['groups'] for s in g['seeds']]
        if not seeds or any(not s.strip() or len(s) > 400 for s in seeds):
            raise ValueError('Нужны непустые фразы до 400 символов.')
        if (not 1 <= config.get('num_phrases', 100) <= 2000 or args.max_calls < 1
                or not 1 <= args.timeout <= 300 or not 0 <= args.retries <= 5
                or not 0 <= args.retry_delay <= 30 or not 1 <= args.passes <= 3):
            raise ValueError('Некорректный лимит.')
        for r in config['regions']:
            if not r['ids'] or len(r['ids']) > 100 or not all(str(i).isdigit() for i in r['ids']):
                raise ValueError('Нужны идентификаторы регионов; пустой список запрещён во избежание сбора по всему миру.')
        maximum = (len(seeds) * (len(config['regions']) + int(config.get('collect_city_distribution', True)))
                   + int(config.get('collect_region_tree', False)))
        print(f'Фраз: {len(seeds)}. До {maximum} запросов без кеша. Лимит запуска: {args.max_calls}.')
        if args.plan:
            return 0
        if args.prompt_credentials and not args.offline:
            if not sys.stdin.isatty():
                raise ValueError('Для скрытого ввода откройте интерактивный терминал.')
            if not os.environ.get('YANDEX_FOLDER_ID'):
                os.environ['YANDEX_FOLDER_ID'] = input('YANDEX_FOLDER_ID: ').strip()
            if not os.environ.get('YANDEX_API_KEY'):
                with warnings.catch_warnings():
                    warnings.simplefilter('error', getpass.GetPassWarning)
                    os.environ['YANDEX_API_KEY'] = getpass.getpass('YANDEX_API_KEY (hidden): ').strip()
            if not os.environ.get('YANDEX_API_KEY'):
                raise ValueError('Ключ не введён. Вставьте секретный API-ключ в скрытый ввод до Enter.')
        folder = os.environ.get('YANDEX_FOLDER_ID', '')
        if not folder:
            raise ValueError('Задайте YANDEX_FOLDER_ID — идентификатор каталога Yandex Cloud.')
        client = Client(folder, args.cache, args.max_calls, args.offline, args.timeout,
                        args.retries, args.retry_delay)
        if args.smoke_first:
            payload = {'phrase': seeds[0], 'numPhrases': str(config.get('num_phrases', 100)),
                       'regions': config['regions'][0]['ids'], 'devices': ['DEVICE_ALL']}
            result, _ = client.call('topRequests', payload)
            if (not str(result.get('totalCount', '0')).isdigit()
                    or any(not isinstance(result.get(k, []), list) for k in ('results', 'associations'))):
                raise RuntimeError('Пробный ответ не содержит ожидаемые поля; сбор остановлен.')
            print(f'Проба успешна. Новых вызовов: {client.calls}. Продолжаю с общим лимитом {args.max_calls}.')
            if not result.get('results') and not result.get('associations'):
                print('API вернул только общую частотность без детализации фраз; это отмечается в metadata.json.')
        for pass_index in range(args.passes):
            metadata = collect(config, client, args.out)
            if metadata['complete']:
                print(f'Готово: {args.out.resolve()}. Попыток API: {client.calls}')
                return 0
            if args.offline or client.calls >= client.max_calls or pass_index + 1 >= args.passes:
                break
            print(f'Повторный проход для {len(metadata["pending_requests"])} отложенных запросов; '
                  'успешные ответы берутся из кеша.', flush=True)
            time.sleep(min(args.retry_delay * 4, 30))
        print(f'Сохранён частичный результат: {args.out.resolve()}. '
              f'Осталось запросов: {len(metadata["pending_requests"])}. '
              'Список в metadata.json; завершённым сбор не отмечен.', file=sys.stderr)
        return 2
    except getpass.GetPassWarning:
        print('Ошибка: терминал не поддерживает скрытый ввод. Ключ не запрашивался.', file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('Ввод отменён; сбор остановлен.', file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        print(f'Ошибка: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
