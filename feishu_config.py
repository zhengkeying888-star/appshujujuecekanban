"""飞书多维表格配置"""
import os

# Base token 从环境变量读取，避免硬编码
FEISHU_BASE_TOKEN = os.environ.get('FEISHU_BASE_TOKEN', '')

# 从环境变量读取，避免硬编码到代码中
DEFAULT_BASE_TOKEN = ''

# 表名到 table_id 的映射
# 由于 Feishu Base 单表 20,000 行限制，大表按月拆分存储
TABLE_IDS = {
    'backend_data_2026_03': 'tbl37AoUcHoja43Z',
    'backend_data_2026_04': 'tbl4eIR7vry1aNtT',
    'frontend_data_2026_03': 'tblqUi4VIBG7dXhR',
    'frontend_data_2026_04_p1': 'tbl5yb8mweGFovdu',
    'frontend_data_2026_04_p2': 'tbl7EUPdiC7CQNOX',
    'mau_data': 'tbl3K8eZ7k2EkD9b',
    'category_mapping': 'tbl7ew4hqNsyEWo1',
}


def get_table_id(name: str) -> str:
    """获取指定表的 table_id"""
    if name not in TABLE_IDS:
        raise ValueError(f"Unknown table name: {name}")
    return TABLE_IDS[name]


def get_base_token() -> str:
    """获取 Base token，优先环境变量，fallback 到默认值"""
    return FEISHU_BASE_TOKEN or DEFAULT_BASE_TOKEN
