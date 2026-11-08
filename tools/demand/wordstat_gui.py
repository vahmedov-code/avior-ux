"""Desktop interface for the AVIOR Wordstat collector (Windows, Python 3.10+)."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import wordstat_credentials as credentials
from wordstat_collect import dump, read_json

HERE = Path(__file__).resolve().parent
PRESETS = {
    'Автоматизация малого и среднего бизнеса': 'research-smb-automation.json',
    'Telegram и MAX': 'research-bot-platforms.json',
    'Лиды для ремонтных мастерских': 'research-repair-leads.json',
    'Расширенное исследование ремонта': 'research-repair-expanded.json',
    'Привлечение клиентов в ремонт': 'research-repair-acquisition.json',
    'Первое исследование ремонта': 'research.json',
}
CUSTOM = 'Свои запросы'
REGIONS = {
    '225': 'Россия',
    '1': 'Москва и область',
    '10174': 'Санкт-Петербург и Ленинградская область',
    '213': 'Москва',
    '2': 'Санкт-Петербург',
}


def prepared_plan(path):
    config = read_json(path)
    title = config.get('title', path.stem).strip()
    groups, regions = config['groups'], config['regions']
    count = config.get('num_phrases', 100)
    cities = config.get('collect_city_distribution', True)
    tree = config.get('collect_region_tree', False)
    if not title or type(count) is not int or not 1 <= count <= 2000:
        raise ValueError('Неверное название или лимит уточнений.')
    if type(cities) is not bool or type(tree) is not bool:
        raise ValueError('Неверные параметры распределения.')
    if not isinstance(groups, list) or not groups or not all(
        isinstance(group['name'], str) and group['name'].strip()
        and isinstance(group['seeds'], list) and group['seeds']
        and all(isinstance(seed, str) and seed.strip() and len(seed) <= 400 for seed in group['seeds'])
        for group in groups
    ):
        raise ValueError('Неверные группы фраз.')
    if not isinstance(regions, list) or not regions or not all(
        isinstance(region['label'], str) and region['label'].strip()
        and isinstance(region['ids'], list) and 1 <= len(region['ids']) <= 100
        and all(str(code).isdigit() for code in region['ids'])
        for region in regions
    ):
        raise ValueError('Неверные регионы.')
    return {
        'title': title, 'num_phrases': count,
        'groups': [{'name': group['name'], 'seeds': group['seeds']} for group in groups],
        'regions': [{'label': region['label'], 'ids': [str(code) for code in region['ids']]} for region in regions],
        'collect_city_distribution': cities, 'collect_region_tree': tree,
    }


class App:
    def __init__(self, root, storage, folder_id='', history=None, plans=None, icon=None):
        self.root, self.storage, self.history = root, storage, history
        self.plans, self.icon = plans, icon
        self.prepared = {}
        self.datasets = {}
        self.stats_rows = []
        self.visible_rows = {}
        self.pinned = []
        self.stats_dataset = tk.StringVar()
        self.stats_region = tk.StringVar(value='Россия')
        self.stats_filter = tk.StringVar()
        self.compare_status = tk.StringVar(value='Выбрано 0 из 4')
        self.process = None
        self.source_run = None
        self.run_dir = None
        self.stopped = False
        self.messages = queue.Queue()
        self.preset = tk.StringVar()
        self.folder_id = tk.StringVar(value=folder_id)
        self.api_key = tk.StringVar()
        self.key_status = tk.StringVar()
        self.plan_status = tk.StringVar()
        self.phrase_heading = tk.StringVar()
        self.city = tk.BooleanVar()
        self.regions = {code: tk.BooleanVar() for code in REGIONS}
        self.limit = tk.StringVar()
        self.summary = tk.StringVar()
        self.status = tk.StringVar(value='Готово к запуску')
        self.build()
        self.refresh_plans()
        self.refresh_key_status()
        self.refresh_datasets()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(80, self.poll)

    def build(self):
        root = self.root
        root.title('AVIOR Wordstat')
        if self.icon and self.icon.is_file():
            root.iconbitmap(default=str(self.icon))
        root.geometry('1060x700')
        root.minsize(880, 620)
        root.option_add('*Font', ('Segoe UI', 10))
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI Semibold', 21))
        style.configure('Subtitle.TLabel', foreground='#43556c')
        style.configure('Treeview', rowheight=25)
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='AVIOR Wordstat', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Исследование поискового спроса', style='Subtitle.TLabel').pack(anchor='w', pady=(0, 12))

        self.settings = ttk.Frame(frame)
        self.settings.pack(fill='x')
        form = ttk.LabelFrame(self.settings, text='Настройки сбора', padding=10)
        form.pack(fill='x')
        for column in range(3):
            form.columnconfigure(column, weight=1)
        for column, label in enumerate(('Исследование', 'Folder ID', 'API-ключ')):
            ttk.Label(form, text=label).grid(row=0, column=column, sticky='w', padx=4)
        self.picker = ttk.Combobox(form, textvariable=self.preset, state='readonly')
        self.picker.grid(row=1, column=0, sticky='ew', padx=4)
        self.picker.bind('<<ComboboxSelected>>', self.select_preset)
        self.folder_entry = ttk.Entry(form, textvariable=self.folder_id)
        self.folder_entry.grid(row=1, column=1, sticky='ew', padx=4)
        self.key_entry = ttk.Entry(form, textvariable=self.api_key, show='•')
        self.key_entry.grid(row=1, column=2, sticky='ew', padx=4)

        plan_controls = ttk.Frame(form)
        plan_controls.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0))
        if self.plans is not None:
            ttk.Button(plan_controls, text='Обновить планы', command=self.refresh_plans).pack(side='left')
            ttk.Label(plan_controls, textvariable=self.plan_status, style='Subtitle.TLabel').pack(side='left', padx=6)
        key_controls = ttk.Frame(form)
        key_controls.grid(row=2, column=2, sticky='e', pady=(5, 0))
        ttk.Button(key_controls, text='Сохранить ключ', command=self.save_key).pack(side='left')
        self.delete_key_button = ttk.Button(key_controls, text='Удалить', command=self.delete_key)
        self.delete_key_button.pack(side='left', padx=(4, 0))
        ttk.Label(form, textvariable=self.key_status, style='Subtitle.TLabel').grid(
            row=3, column=2, sticky='e', pady=(2, 0))

        self.geographic = ttk.Frame(form)
        self.geographic.grid(row=4, column=0, columnspan=3, sticky='w', pady=(8, 0))
        self.prepared_regions = ttk.Label(form, style='Subtitle.TLabel', wraplength=810)
        for code, label in REGIONS.items():
            control = ttk.Checkbutton(self.geographic, text=label, variable=self.regions[code], command=self.refresh)
            control.pack(side='left', padx=3)
        options = ttk.Frame(form)
        options.grid(row=5, column=0, columnspan=3, sticky='w', pady=(6, 0))
        self.city_check = ttk.Checkbutton(options, text='Распределение по городам', variable=self.city, command=self.refresh)
        self.city_check.pack(side='left')
        ttk.Label(options, text='Лимит попыток').pack(side='left', padx=(18, 4))
        self.limit_entry = ttk.Entry(options, textvariable=self.limit, width=7)
        self.limit_entry.pack(side='left')
        self.limit.trace_add('write', lambda *_: self.refresh())

        ttk.Label(form, textvariable=self.phrase_heading).grid(
            row=6, column=0, columnspan=3, sticky='w', pady=(8, 3))
        self.phrases = tk.Text(form, height=4, wrap='word', font=('Segoe UI', 10), undo=True)
        self.phrases.grid(row=7, column=0, columnspan=3, sticky='ew')
        self.phrases.bind('<<Modified>>', self.phrases_changed)

        ttk.Label(self.settings, textvariable=self.summary, style='Subtitle.TLabel', wraplength=960).pack(anchor='w', pady=(9, 5))
        actions = ttk.Frame(self.settings)
        actions.pack(fill='x', pady=(0, 7))
        self.start_button = ttk.Button(actions, text='Запустить сбор', command=self.start)
        self.start_button.pack(side='left')
        self.resume_button = ttk.Button(actions, text='Открыть или продолжить сбор', command=self.choose_resume)
        self.resume_button.pack(side='left', padx=5)
        self.stop_button = ttk.Button(actions, text='Остановить', state='disabled', command=self.stop)
        self.stop_button.pack(side='left', padx=5)
        self.open_button = ttk.Button(actions, text='Открыть папку сбора', state='disabled', command=self.open_folder)
        self.open_button.pack(side='right')

        self.tabs = ttk.Notebook(frame)
        self.tabs.pack(fill='both', expand=True)
        journal = ttk.Frame(self.tabs)
        results = ttk.Frame(self.tabs)
        self.tabs.add(journal, text='Журнал')
        self.tabs.add(results, text='Частотности')
        self.build_stats()
        self.tabs.bind('<<NotebookTabChanged>>', self.tab_changed)
        self.log = tk.Text(journal, wrap='word', height=8, state='disabled', bg='#f5f7fa', font=('Consolas', 10))
        log_scroll = ttk.Scrollbar(journal, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side='right', fill='y')
        self.log.pack(fill='both', expand=True)
        self.table = ttk.Treeview(results, columns=('group', 'seed', 'region', 'count'), show='headings')
        for column, label, width in [('group', 'Группа', 210), ('seed', 'Поисковая фраза', 395),
                                     ('region', 'Регион', 235), ('count', 'Частотность', 100)]:
            self.table.heading(column, text=label)
            self.table.column(column, width=width, minwidth=60, stretch=column == 'seed')
        result_scroll = ttk.Scrollbar(results, command=self.table.yview)
        self.table.configure(yscrollcommand=result_scroll.set)
        result_scroll.pack(side='right', fill='y')
        self.table.pack(fill='both', expand=True)
        bottom = ttk.Frame(frame)
        bottom.pack(fill='x', pady=(7, 0))
        ttk.Label(bottom, textvariable=self.status).pack(side='left')
        self.progress = ttk.Progressbar(bottom, mode='indeterminate', length=145)
        self.progress.pack(side='right')

    def tab_changed(self, _event):
        if self.tabs.index('current') == 2:
            self.settings.pack_forget()
        elif not self.settings.winfo_manager():
            self.settings.pack(fill='x', before=self.tabs)

    def build_stats(self):
        page = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(page, text='Статистика')
        filters = ttk.Frame(page)
        filters.pack(fill='x')
        filters.columnconfigure(0, weight=2)
        filters.columnconfigure(1, weight=1)
        filters.columnconfigure(2, weight=1)
        for i, label in enumerate(('Сохранённый сбор', 'Регион', 'Фильтр фраз и групп')):
            ttk.Label(filters, text=label).grid(row=0, column=i, sticky='w', padx=3)
        self.dataset_box = ttk.Combobox(filters, textvariable=self.stats_dataset, state='readonly', width=32)
        self.dataset_box.grid(row=1, column=0, sticky='ew', padx=3)
        self.dataset_box.bind('<<ComboboxSelected>>', lambda _: self.read_stats())
        self.region_box = ttk.Combobox(filters, textvariable=self.stats_region, state='readonly', width=22)
        self.region_box.grid(row=1, column=1, sticky='ew', padx=3)
        self.region_box.bind('<<ComboboxSelected>>', lambda _: self.filter_stats())
        ttk.Entry(filters, textvariable=self.stats_filter).grid(row=1, column=2, sticky='ew', padx=3)
        self.stats_filter.trace_add('write', lambda *_: self.filter_stats())

        self.available = self.stats_table(page, 5, 'extended')
        self.available.bind('<Double-1>', lambda _: self.add_comparison())
        actions = ttk.Frame(page)
        actions.pack(fill='x', pady=5)
        ttk.Button(actions, text='Добавить к сравнению', command=self.add_comparison).pack(side='left')
        ttk.Button(actions, text='Убрать выбранное', command=self.remove_comparison).pack(side='left', padx=5)
        ttk.Button(actions, text='Очистить', command=self.clear_comparison).pack(side='left')
        ttk.Label(actions, textvariable=self.compare_status).pack(side='right')

        self.comparison = self.stats_table(page, 4, 'extended', show_source=True)
        ttk.Label(page, text='Ctrl+клик выбирает несколько строк. Даты по Москве. Частотности за последние 30 дней на момент сбора.',
                  style='Subtitle.TLabel', wraplength=810).pack(anchor='w', pady=(5, 0))

    def stats_table(self, parent, height, selection, show_source=False):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, pady=(4, 0))
        columns = [('seed', 'Фраза', 400), ('region', 'Регион', 225),
                   ('date', 'Дата сбора', 100), ('count', 'Частотность', 95)]
        if show_source:
            columns = [('source', 'Сбор', 190), ('seed', 'Фраза', 290), ('region', 'Регион', 190),
                       ('date', 'Дата сбора', 100), ('count', 'Частотность', 95)]
        table = ttk.Treeview(frame, columns=[key for key, _, _ in columns], show='headings',
                             height=height, selectmode=selection)
        for key, text, width in columns:
            table.heading(key, text=text)
            table.column(key, width=width, minwidth=55, stretch=key == 'seed',
                         anchor='e' if key == 'count' else 'w')
        scroll = ttk.Scrollbar(frame, command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        table.pack(fill='both', expand=True)
        return table

    def refresh_datasets(self, preferred=None):
        folders = {meta.parent.parent for meta in self.storage.glob('*/results/metadata.json')}
        if self.history is not None:
            folders.update(meta.parent.parent for meta in self.history.glob('wordstat-*/results/metadata.json'))
        current = self.datasets.get(self.stats_dataset.get())
        folders.update(self.datasets.values())
        if preferred:
            folders.add(preferred)
        names = {
            'wordstat-bot-platforms-2026-11-08': 'Telegram и MAX · 08.11.2026',
            'wordstat-repair-leads-2026-11-07': 'Лиды для ремонта · 07.11.2026',
            'wordstat-repair-expanded-2026-11-07': 'Расширенный ремонт · 07.11.2026',
            'wordstat-private-2026-11-07': 'Первый срез ремонта · 07.11.2026',
        }
        datasets = {}
        def updated(path):
            marker = path / 'results/metadata.json'
            try:
                return marker.stat().st_mtime
            except OSError:
                return 0

        for path in sorted(folders, key=updated, reverse=True):
            if not (path / 'results/seed_totals.csv').is_file():
                continue
            label = names.get(path.name, path.name)
            try:
                name = read_json(path / 'session.json').get('research_name')
                if isinstance(name, str) and name:
                    label = f'{name} · {path.name[:16].replace("_", " ")}'
            except (OSError, ValueError, AttributeError):
                pass
            if label in datasets:
                label = f'{label} · {path.name}'
            if label in datasets:
                label = str(path)
            datasets[label] = path
        self.datasets = datasets
        self.dataset_box.configure(values=list(datasets))
        target = preferred or current
        selection = next((label for label, path in datasets.items() if path == target), '')
        self.stats_dataset.set(selection or next(iter(datasets), ''))
        self.read_stats()

    def read_stats(self):
        path = self.datasets.get(self.stats_dataset.get())
        self.stats_rows = []
        if path is not None:
            try:
                self.stats_rows = self.read_rows(path)
            except (OSError, UnicodeError, csv.Error):
                self.compare_status.set('Не удалось прочитать частотности')
        regions = list(dict.fromkeys(row['region'] for row in self.stats_rows))
        choices = ['Все регионы', *regions]
        self.region_box.configure(values=choices)
        if self.stats_region.get() not in choices:
            self.stats_region.set('Россия' if 'Россия' in choices else choices[0])
        self.filter_stats()

    @staticmethod
    def stats_values(row):
        timestamp = row.get('collected_at', '')
        try:
            observed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if observed.tzinfo is not None:
                observed = observed.astimezone(timezone(timedelta(hours=3)))
            day = observed.strftime('%d.%m.%Y')
        except ValueError:
            day = '—'
        return row['seed'], row['region'], day, row.get('count') or '—'

    def filter_stats(self):
        needle = self.stats_filter.get().strip().casefold()
        region = self.stats_region.get()
        self.available.delete(*self.available.get_children())
        self.visible_rows = {}
        for row in self.stats_rows:
            if region != 'Все регионы' and row['region'] != region:
                continue
            if needle not in f'{row["group"]} {row["seed"]}'.casefold():
                continue
            item = self.available.insert('', 'end', values=self.stats_values(row))
            self.visible_rows[item] = row

    def add_comparison(self):
        path = self.datasets.get(self.stats_dataset.get())
        selected = self.available.selection()
        if not selected or path is None:
            self.compare_status.set('Выберите строки в верхней таблице')
            return
        additions = []
        known = {(source, row['seed'], row['region']) for source, row in self.pinned}
        for item in selected:
            row = self.visible_rows[item]
            key = (path, row['seed'], row['region'])
            if key not in known:
                additions.append((path, row))
                known.add(key)
        if len(self.pinned) + len(additions) > 4:
            self.compare_status.set('Можно сравнить до 4 фраз. Уберите лишние строки.')
            return
        self.pinned.extend(additions)
        self.show_comparison()

    def remove_comparison(self):
        indexes = {int(item) for item in self.comparison.selection()}
        self.pinned = [entry for index, entry in enumerate(self.pinned) if index not in indexes]
        self.show_comparison()

    def clear_comparison(self):
        self.pinned.clear()
        self.show_comparison()

    def show_comparison(self):
        self.comparison.delete(*self.comparison.get_children())
        labels = {source: label for label, source in self.datasets.items()}
        for index, (source, row) in enumerate(self.pinned):
            values = (labels.get(source, source.name), *self.stats_values(row))
            self.comparison.insert('', 'end', iid=str(index), values=values)
        self.compare_status.set(f'Выбрано {len(self.pinned)} из 4')

    def refresh_plans(self):
        selected = self.preset.get()
        self.prepared = {}
        invalid = 0
        if self.plans is not None:
            try:
                paths = sorted(self.plans.glob('*.json'), key=lambda path: path.stat().st_mtime_ns, reverse=True)
            except OSError:
                paths = []
                invalid = 1
            for path in paths:
                try:
                    config = prepared_plan(path)
                except (OSError, ValueError, KeyError, TypeError, AttributeError):
                    invalid += 1
                    continue
                label = f'План · {config["title"]}'
                if label in self.prepared:
                    label = f'{label} ({path.stem})'
                while label in self.prepared:
                    label += ' ·'
                self.prepared[label] = config
        status = f'Готовых планов: {len(self.prepared)}'
        if invalid:
            status += f' · не прочитано: {invalid}'
        self.plan_status.set(status)
        choices = (*self.prepared, *PRESETS, CUSTOM)
        self.picker.configure(values=choices)
        if self.source_run or selected == CUSTOM:
            return
        self.preset.set((selected if selected in choices else CUSTOM) if selected else choices[0])
        self.select_preset()

    def refresh_key_status(self):
        try:
            saved = bool(credentials.read_key())
            self.key_status.set('Ключ сохранён в Windows' if saved else 'Ключ не сохранён')
            self.delete_key_button.configure(state='normal' if saved else 'disabled')
        except (OSError, ValueError):
            self.key_status.set('Хранилище Windows недоступно')
            self.delete_key_button.configure(state='normal')

    def save_key(self):
        key = self.api_key.get().strip()
        if not key:
            self.key_status.set('Введите API-ключ для сохранения')
            self.key_entry.focus_set()
            return
        try:
            credentials.save_key(key)
        except (OSError, ValueError):
            messagebox.showerror('API-ключ', 'Не удалось сохранить ключ в Windows.', parent=self.root)
            return
        self.api_key.set('')
        self.refresh_key_status()

    def delete_key(self):
        try:
            credentials.delete_key()
        except OSError:
            messagebox.showerror('API-ключ', 'Не удалось удалить сохранённый ключ.', parent=self.root)
            return
        self.api_key.set('')
        self.refresh_key_status()

    def select_preset(self, _event=None):
        self.source_run = None
        self.config = self.prepared.get(self.preset.get())
        preset = PRESETS.get(self.preset.get())
        if self.config is None:
            self.config = read_json(HERE / preset) if preset else {
                'num_phrases': 100, 'regions': [{'ids': ['225'], 'label': 'Россия'}],
                'collect_city_distribution': False, 'collect_region_tree': False, 'groups': [],
            }
        self.show_config()
        self.refresh()

    def show_config(self):
        fixed = self.source_run or self.preset.get() in self.prepared
        if fixed:
            self.geographic.grid_remove()
            labels = ', '.join(region['label'] for region in self.config['regions'])
            self.prepared_regions.configure(text=f'Регионы плана · {labels}')
            self.prepared_regions.grid(row=4, column=0, columnspan=3, sticky='w', pady=(8, 0))
        else:
            self.prepared_regions.grid_remove()
            self.geographic.grid()
        selected = {str(code) for region in self.config['regions'] for code in region['ids']}
        for code, variable in self.regions.items():
            variable.set(code in selected)
        self.city.set(self.config.get('collect_city_distribution', True))
        self.phrases.configure(state='normal')
        self.phrases.delete('1.0', 'end')
        self.phrases.insert('1.0', '\n'.join(seed for group in self.config['groups'] for seed in group['seeds']))
        self.phrases.edit_modified(False)
        custom = self.preset.get() == CUSTOM and not self.source_run
        self.phrase_heading.set('Поисковые фразы · одна фраза на строку' if custom else 'Поисковые фразы плана')
        self.phrases.configure(state='normal' if custom else 'disabled')
        self.city_check.configure(state='disabled' if fixed else 'normal')
        self.limit.set('')

    def phrases_changed(self, _event):
        if self.phrases.edit_modified():
            self.phrases.edit_modified(False)
            self.refresh()

    def current_config(self):
        if self.source_run or self.preset.get() in self.prepared:
            return self.config
        config = dict(self.config)
        config['regions'] = [
            {'label': label, 'ids': [code]} for code, label in REGIONS.items() if self.regions[code].get()
        ]
        config['collect_city_distribution'] = self.city.get()
        config['collect_region_tree'] = self.city.get() and self.config.get('collect_region_tree', False)
        if self.preset.get() == CUSTOM:
            seeds = list(dict.fromkeys(line.strip() for line in self.phrases.get('1.0', 'end').splitlines() if line.strip()))
            config['groups'] = [{'name': 'Свои запросы', 'seeds': seeds}]
        return config

    def estimate(self, config):
        phrases = sum(len(group['seeds']) for group in config['groups'])
        regions = len(config['regions'])
        cities = phrases if config.get('collect_city_distribution', True) else 0
        tree = int(config.get('collect_region_tree', False))
        top = phrases * regions
        cap_rate = 5 if cities else 2  # Копеек за попытку по тарифу от 08.11.2026.
        automatic_limit = min(max(2 * (top + cities + tree), 1), 10000 // cap_rate)
        limit = int(self.limit.get()) if self.limit.get().strip() else automatic_limit
        if limit < 1 or limit * cap_rate > 10000:
            raise ValueError(f'Лимит для этого плана должен быть от 1 до {10000 // cap_rate} попыток.')
        return phrases, regions, top + cities + tree, (top * 2 + cities * 5) / 100, limit, limit * cap_rate / 100

    def refresh(self):
        try:
            phrases, regions, planned, cost, limit, ceiling = self.estimate(self.current_config())
            self.summary.set(f'{phrases} фраз × {regions} регионов · {planned} запросов по плану · '
                             f'{cost:.2f} ₽ без кеша и повторов · предел {ceiling:.2f} ₽ ({limit} попыток) · тариф 08.11.2026')
        except ValueError:
            self.summary.set('Введите целый лимит попыток в пределах 100 ₽.')

    def choose_resume(self):
        folder = filedialog.askdirectory(parent=self.root, title='Выберите папку предыдущего сбора GUI', initialdir=self.storage)
        if not folder:
            return
        source = Path(folder)
        try:
            marker = source / 'results/metadata.json'
            metadata = read_json(marker) if marker.is_file() else {}
            if metadata and metadata.get('complete', True) and self.load_results(source):
                self.run_dir = source
                self.refresh_datasets(source)
                self.status.set('Открыт завершённый сбор')
                self.open_button.configure(state='normal')
                return
            saved_config = source / 'config.json'
            config = read_json(saved_config) if saved_config.is_file() else metadata['config']
            saved_session = source / 'session.json'
            if saved_session.is_file():
                folder_id = read_json(saved_session)['folder_id']
            else:
                cached = next((source / 'cache').glob('*.json'), None)
                if cached is None:
                    raise ValueError('В папке нет кеша.')
                folder_id = read_json(cached)['request']['folderId']
            if not (source / 'cache').is_dir() or not folder_id:
                raise ValueError('В папке нет кеша и настроек предыдущего сбора.')
        except (OSError, ValueError, KeyError, TypeError):
            messagebox.showerror('Папка сбора', 'Выберите папку сбора с результатами или сохранёнными настройками и кешем.', parent=self.root)
            return
        self.source_run = source
        self.config = config
        self.preset.set('Продолжение предыдущего сбора')
        self.folder_id.set(folder_id)
        self.resume_folder_id = folder_id
        self.show_config()
        self.refresh()
        self.status.set('Выбран кеш предыдущего сбора')

    def start(self):
        if self.process is not None:
            return
        key, folder = self.api_key.get().strip(), self.folder_id.get().strip()
        try:
            if not folder:
                raise ValueError('Укажите Folder ID.')
            if not key:
                try:
                    key = credentials.read_key()
                except (OSError, ValueError):
                    raise ValueError('Хранилище Windows недоступно. Введите API-ключ для этого запуска.') from None
            if not key:
                raise ValueError('Введите API-ключ. Его можно сохранить для следующих запусков.')
            config = self.current_config()
            phrases, regions, planned, _cost, limit, _ceiling = self.estimate(config)
            if not phrases or not regions or any(len(seed) > 400 for g in config['groups'] for seed in g['seeds']):
                raise ValueError('Выберите регион и добавьте фразы длиной до 400 символов.')
            if self.source_run and folder != self.resume_folder_id:
                raise ValueError('Для продолжения нужен Folder ID предыдущего сбора.')
            if not self.source_run and planned > limit:
                raise ValueError('Лимит попыток меньше плана. Увеличьте лимит или уменьшите число фраз и регионов.')
            self.storage.mkdir(parents=True, exist_ok=True)
            run_dir = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y-%m-%d_%H%M_'), dir=self.storage))
            cache = run_dir / 'cache'
            cache.mkdir()
            if self.source_run:
                for cached in (self.source_run / 'cache').glob('*.json'):
                    shutil.copy2(cached, cache / cached.name)
            dump(run_dir / 'config.json', config)
            research_name = config.get('title') or self.preset.get()
            dump(run_dir / 'session.json', {'folder_id': folder, 'research_name': research_name})
            python = Path(sys.executable)
            if python.name.lower() == 'pythonw.exe':
                python = python.with_name('python.exe')
            env = dict(os.environ, YANDEX_FOLDER_ID=folder, YANDEX_API_KEY=key, PYTHONIOENCODING='utf-8')
            command = [str(python), '-u', str(HERE / 'wordstat_collect.py'), '--config', str(run_dir / 'config.json'),
                       '--cache', str(cache), '--out', str(run_dir / 'results'), '--max-calls', str(limit),
                       '--timeout', '45', '--retries', '2', '--passes', '2']
            self.process = subprocess.Popen(
                command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding='utf-8', errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            messagebox.showerror('Запуск', str(exc).replace(key, '[скрыто]') if key else str(exc), parent=self.root)
            return
        self.api_key.set('')
        self.run_dir = run_dir
        self.stopped = False
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        self.table.delete(*self.table.get_children())
        self.tabs.select(0)
        self.status.set('Идёт сбор')
        self.start_button.configure(state='disabled')
        self.resume_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.open_button.configure(state='normal')
        self.progress.start(12)
        threading.Thread(target=self.read_process, args=(self.process, key), daemon=True).start()

    def read_process(self, process, key):
        with process.stdout as stream:
            for line in stream:
                self.messages.put(('log', line.replace(key, '[скрыто]')))
        self.messages.put(('exit', process.wait()))

    def poll(self):
        for _ in range(100):
            try:
                kind, value = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == 'log':
                self.log.configure(state='normal')
                self.log.insert('end', value)
                self.log.see('end')
                self.log.configure(state='disabled')
            else:
                self.finished(value)
        self.root.after(80, self.poll)

    def finished(self, code):
        self.process = None
        self.progress.stop()
        self.start_button.configure(state='normal')
        self.resume_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        if self.stopped:
            self.status.set('Остановлено. Кеш можно выбрать для продолжения.')
        elif code == 0:
            self.status.set('Сбор завершён')
        elif code == 2:
            self.status.set('Частичный результат. Кеш можно выбрать для продолжения.')
        else:
            self.status.set('Сбор завершился с ошибкой. Подробности в журнале.')
        if not self.stopped and code in (0, 2) and self.load_results(self.run_dir):
            self.refresh_datasets(self.run_dir)

    @staticmethod
    def read_rows(run_dir):
        with (run_dir / 'results/seed_totals.csv').open(encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)
            if not {'group', 'seed', 'region', 'count'}.issubset(reader.fieldnames or []):
                raise csv.Error('В таблице частотностей отсутствуют обязательные столбцы.')
            return list(reader)

    def load_results(self, run_dir):
        try:
            rows = self.read_rows(run_dir)
        except (OSError, UnicodeError, csv.Error):
            return False
        self.table.delete(*self.table.get_children())
        for row in rows:
            self.table.insert('', 'end', values=tuple(row.get(k, '') for k in ('group', 'seed', 'region', 'count')))
        self.tabs.select(1)
        return True

    def open_folder(self):
        if self.run_dir is not None:
            try:
                os.startfile(self.run_dir)
            except OSError as exc:
                messagebox.showerror('Папка сбора', str(exc), parent=self.root)

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.stopped = True
            self.status.set('Останавливаю сбор')
            self.stop_button.configure(state='disabled')
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass

    def close(self):
        if self.process is not None and self.process.poll() is None:
            if not messagebox.askyesno('Выход', 'Остановить сбор и закрыть окно? Полученные ответы останутся в кеше.', parent=self.root):
                return
            self.stop()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storage', type=Path, default=Path.home() / 'Documents' / 'Codex' / 'wordstat-gui')
    parser.add_argument('--folder-cache', type=Path)
    parser.add_argument('--history', type=Path)
    parser.add_argument('--plans', type=Path)
    parser.add_argument('--icon', type=Path)
    args = parser.parse_args()
    folder = os.environ.get('YANDEX_FOLDER_ID', '')
    if not folder and args.folder_cache:
        cached = next(args.folder_cache.glob('*.json'), None)
        if cached is not None:
            try:
                folder = read_json(cached)['request']['folderId']
            except (OSError, ValueError, KeyError, TypeError):
                pass
    root = tk.Tk()
    App(root, args.storage.resolve(), folder, args.history.resolve() if args.history else None,
        args.plans.resolve() if args.plans else None, args.icon)
    root.mainloop()


if __name__ == '__main__':
    main()
