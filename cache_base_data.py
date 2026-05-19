#!/usr/bin/env python3
"""把飞书 Base 数据缓存到本地 CSV，供快速迭代使用"""
import os
from pathlib import Path
from feishu_reader import FeishuDataSource

CACHE_DIR = Path(__file__).parent / 'cached_data'
CACHE_DIR.mkdir(exist_ok=True)

ds = FeishuDataSource()

tables = [
    'backend_data_2026_03',
    'backend_data_2026_04',
    'backend_data_2026_05',
    'frontend_data_2026_03',
    'frontend_data_2026_04_p1',
    'frontend_data_2026_04_p2',
    'frontend_data_2026_05_p1',
    'frontend_data_2026_05_p2',
    'mau_data',
    'category_mapping',
    'daily_dau',
]

for name in tables:
    try:
        df = ds.read_table(name)
        path = CACHE_DIR / f'{name}.csv'
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f'[OK] {name}: {len(df)} rows -> {path}')
    except Exception as e:
        print(f'[ERR] {name}: {e}')

print('Cache complete.')
