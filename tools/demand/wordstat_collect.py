#!/usr/bin/env python3
"""Collect official Yandex Search API Wordstat data. Python 3.10+, stdlib only."""
import argparse
import csv
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
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


class Client:
    def __init__(self, folder, cache, max_calls=30, offline=False):
        self.folder, self.cache = folder, cache
        self.max_calls, self.offline, self.calls = max_calls, offline, 0
        self.cache.mkdir(parents=True, exist_ok=True)

    def call(self, method, payload):
        body = dict(payload, folderId=self.folder)
        key = hashlib.sha256(json.dumps([method, body], sort_keys=True).encode()).hexdigest()
        path = self.cache / (key + '.json')
        if path.exists():
            saved = read_json(path)
            return saved['response'], saved['collected_at']
        if self.offline:
            raise RuntimeError('В кеше отсутствует ответ. Нужен сбор через API.')
        if self.calls >= self.max_calls:
            raise RuntimeError('Достигнут лимит API-вызовов; ответы сохранены. Повторите запуск для продолжения.')
        token = os.environ.get('YANDEX_API_KEY')
        if not token:
            raise RuntimeError('Задайте YANDEX_API_KEY локально. Не отправляйте ключ в чат.')
        self.calls += 1
        request = Request(BASE + method, data=json.dumps(body).encode(), headers={
            'Authorization': 'Api-Key ' + token, 'Content-Type': 'application/json'}, method='POST')
        try:
            with build_opener(NoRedirect()).open(request, timeout=40) as response:
                result = json.load(response)
        except HTTPError as exc:
            raise RuntimeError(f'API вернул HTTP {exc.code}. Проверьте права, квоту и настройки каталога; автоповтора нет.') from None
        except URLError:
            raise RuntimeError('Ошибка соединения с API. Ответ не сохранён; повторите позже.') from None
        if not isinstance(result, dict) or not isinstance(result.get('results', []), list):
            raise RuntimeError('Неожиданный формат ответа API; сбор остановлен.')
        stamp = datetime.now(timezone.utc).isoformat()
        dump(path, {'method': method, 'request': body, 'collected_at': stamp, 'response': result})
        time.sleep(1)
        return result, stamp


def csv_write(path, columns, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            # Avoid spreadsheet formula execution when an API phrase begins with a formula marker.
            writer.writerow({k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v)
                             for k, v in row.items()})


def collect(config, client, output):
    candidates, totals, distributions = {}, [], []
    output.mkdir(parents=True, exist_ok=True)
    for group in config['groups']:
        for seed in group['seeds']:
            for region_set in config['regions']:
                payload = {'phrase': seed, 'numPhrases': str(config.get('num_phrases', 100)),
                           'regions': region_set['ids'], 'devices': ['DEVICE_ALL']}
                result, stamp = client.call('topRequests', payload)
                scope = region_set['label']
                totals.append(dict(group=group['name'], seed=seed, region=scope,
                                   count=result.get('totalCount', ''), collected_at=stamp))
                for kind in ('results', 'associations'):
                    for item in result.get(kind, []):
                        phrase = item['phrase']
                        key = (group['name'], scope, kind, phrase)
                        if key not in candidates:
                            candidates[key] = dict(group=group['name'], region=scope, kind=kind,
                                phrase=phrase, count=item['count'], review=review(phrase), seeds=seed,
                                collected_at=stamp)
                        else:
                            candidates[key]['seeds'] += ' | ' + seed
            if config.get('collect_city_distribution', True):
                result, stamp = client.call('regions', {'phrase': seed, 'region': 'REGION_CITIES',
                                                       'devices': ['DEVICE_ALL']})
                for item in result.get('results', []):
                    distributions.append(dict(group=group['name'], seed=seed, region_id=item['region'],
                        count=item['count'], share=item.get('share', ''),
                        affinity_index=item.get('affinityIndex', ''), collected_at=stamp))
    csv_write(output / 'candidates.csv', ['group','region','kind','phrase','count','review','seeds','collected_at'], candidates.values())
    csv_write(output / 'seed_totals.csv', ['group','seed','region','count','collected_at'], totals)
    csv_write(output / 'cities.csv', ['group','seed','region_id','count','share','affinity_index','collected_at'], distributions)
    dump(output / 'metadata.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'api_calls_this_run': client.calls,
        'config': config, 'notes': ['Частотности пересекаются: не суммировать.',
        'Широкая частотность, не число людей/кликов/покупателей.',
        'Оценки цены клика и прибыли отсутствуют: нужны Директ и данные продаж.',
        'Похожие запросы (associations) требуют отдельной проверки.',
        'Для обновления данных используйте новую папку кеша.']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('research.json'))
    parser.add_argument('--out', type=Path, default=Path('wordstat-results'))
    parser.add_argument('--cache', type=Path, default=Path('wordstat-cache'))
    parser.add_argument('--max-calls', type=int, default=30)
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
        if not 1 <= config.get('num_phrases', 100) <= 2000 or args.max_calls < 1:
            raise ValueError('Некорректный лимит.')
        for r in config['regions']:
            if not r['ids'] or len(r['ids']) > 100 or not all(str(i).isdigit() for i in r['ids']):
                raise ValueError('Нужны идентификаторы регионов; пустой список запрещён во избежание сбора по всему миру.')
        maximum = len(seeds) * (len(config['regions']) + int(config.get('collect_city_distribution', True)))
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
        folder = os.environ.get('YANDEX_FOLDER_ID', '')
        if not folder:
            raise ValueError('Задайте YANDEX_FOLDER_ID — идентификатор каталога Yandex Cloud.')
        client = Client(folder, args.cache, args.max_calls, args.offline)
        if args.smoke_first:
            payload = {'phrase': seeds[0], 'numPhrases': str(config.get('num_phrases', 100)),
                       'regions': config['regions'][0]['ids'], 'devices': ['DEVICE_ALL']}
            result, _ = client.call('topRequests', payload)
            if 'totalCount' not in result or not isinstance(result.get('results'), list):
                raise RuntimeError('Пробный ответ не содержит ожидаемые поля; сбор остановлен.')
            print(f'Проба успешна. Новых вызовов: {client.calls}. Продолжаю с общим лимитом {args.max_calls}.')
        collect(config, client, args.out)
        print(f'Готово: {args.out.resolve()}. API-вызовов: {client.calls}')
        return 0
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
