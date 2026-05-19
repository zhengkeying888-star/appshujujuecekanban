"""飞书多维表格配置"""
import os

# Base token 从环境变量读取，避免硬编码
FEISHU_BASE_TOKEN = os.environ.get('FEISHU_BASE_TOKEN', '')

# 从环境变量读取，避免硬编码到代码中
DEFAULT_BASE_TOKEN = ''

# 表名到 table_id 的映射
# 由于 Feishu Base 单表 20,000 行限制，大表按月拆分存储
# 配置生成时间: 2026-05-18 (auto-import)
TABLE_IDS = {
    'backend_data_2026_03': 'tblk7EGDdChCNUrJ',
    'backend_data_2026_04': 'tbl3obhk2Doap4Va',
    'backend_data_2026_05': 'tbl6rNSEijJWhL3K',
    'frontend_data_2026_03': 'tbl44NQmxKxkpcsZ',
    'frontend_data_2026_04_p1': 'tbl14kvzZj3MUo5Y',
    'frontend_data_2026_04_p2': 'tbl1Xl6YmqvLLEuU',
    'frontend_data_2026_05_p1': 'tbl2lky6BViMASzp',
    'frontend_data_2026_05_p2': 'tbl3DDvYFfbHwHRZ',
    'mau_data': 'tbl70aoVb6J0hMOc',
    'category_mapping': 'tbl4QyHq9kfagZnl',
    'daily_dau': 'tbl4I9Q6TjrpFD49',
}

# Base token 映射（不同表分布在不同 Base 中，每个导入的 Excel 对应一个独立 Base）
BASE_TOKENS = {
    'backend_data_2026_03': 'XKpjb0136a5jucsH29jcQZuPn4c',
    'backend_data_2026_04': 'Z5oPbsZOMaJ29wsifSocyis8n6S',
    'backend_data_2026_05': 'NOa6bfBXLaxbQHsrStEcTYMgnBb',
    'frontend_data_2026_03': 'MtLRbz9A9aKHcIsT2vWcWiWPnkd',
    'frontend_data_2026_04_p1': 'TH0Ob6bzbaTmtEsGJDUcqEryn3e',
    'frontend_data_2026_04_p2': 'AHLSb4MUSakZA6sdJVacMCKJnfc',
    'frontend_data_2026_05_p1': 'FnB6b1jrtaigzmsBTOgcDxPUnxe',
    'frontend_data_2026_05_p2': 'SVM7bM4QcadVkasYmm3cC6PVn9b',
    'mau_data': 'HNIibkb2kaQtLhs18BGcevHzn0d',
    'category_mapping': 'Gc5Ob1lVxati84sIyapcRcbLnXZ',
    'daily_dau': 'RSUcbvFpuahhT1svm8YcNWhFnwc',
}


def get_table_id(name: str) -> str:
    """获取指定表的 table_id"""
    if name not in TABLE_IDS:
        raise ValueError(f"Unknown table name: {name}")
    return TABLE_IDS[name]


def get_base_token(table_name: str = None) -> str:
    """获取 Base token

    优先级：
    1. 环境变量 FEISHU_BASE_TOKEN_<TABLE_NAME>（如 FEISHU_BASE_TOKEN_MAU_DATA）
    2. BASE_TOKENS 映射中的硬编码值
    3. 全局环境变量 FEISHU_BASE_TOKEN
    """
    if table_name:
        env_key = f"FEISHU_BASE_TOKEN_{table_name.upper()}"
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val
        if table_name in BASE_TOKENS:
            return BASE_TOKENS[table_name]
    return FEISHU_BASE_TOKEN or DEFAULT_BASE_TOKEN
