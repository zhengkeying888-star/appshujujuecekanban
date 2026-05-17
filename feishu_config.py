"""飞书多维表格配置"""
import os

# Base token 从环境变量读取，避免硬编码
FEISHU_BASE_TOKEN = os.environ.get('FEISHU_BASE_TOKEN', '')

# 表名到 table_id 的映射
TABLE_IDS = {
    'backend_data': os.environ.get('FEISHU_TABLE_BACKEND', ''),
    'frontend_data': os.environ.get('FEISHU_TABLE_FRONTEND', ''),
    'category_mapping': os.environ.get('FEISHU_TABLE_CATEGORY', ''),
    'mau_data': os.environ.get('FEISHU_TABLE_MAU', ''),
}

def get_table_id(name: str) -> str:
    """获取指定表的 table_id"""
    if name not in TABLE_IDS:
        raise ValueError(f"Unknown table name: {name}")
    return TABLE_IDS[name]
