"""从飞书多维表格读取数据的封装层"""
import os
import subprocess
import json
import pandas as pd
from pathlib import Path
from feishu_config import get_table_id, get_base_token


# 防御性字段映射：若 Base 中字段名被改为纯中文，自动映射回代码使用的列名
# 当前 Base 列名与原始 Excel 一致（中英文混合），此映射暂不生效，为未来结构调整预留
FIELD_MAP = {
    '数据月份': 'stat_month',
    '订单时间': 'order_time',
    '广告资源位': 'tag_level_1',
    '活动名称': 'camp_name',
    '品类名称': 'category_name',
    '课程价格': 'sku_price',
    '是否加好友': 'is_add_friend',
    '首单数': '首单数',
    '首单流水': '首单流水',
    '是否到课': '是否到课',
    '曝光UV': '曝光uv',
    '点击UV': '点击uv',
    '售卖页浏览UV': '售卖页浏览uv',
    '线索数': '线索数',
    '首单订单数': '首单订单数',
    '首单订单金额': '首单订单金额',
    '日活人数': '日活人数',
    '月份': '月份',
    '用户等级': '用户等级',
    '月活人数': '月活人数',
    '占比': '占比',
    '品类': '品类',
    '品类区别': '品类区别',
}


CACHE_DIR = Path(__file__).parent / 'cached_data'

class FeishuDataSource:
    """飞书多维表格数据源（支持本地 CSV 缓存加速）"""

    def __init__(self, base_token: str = None, cache_dir: str = None):
        self.base_token = base_token or get_base_token()
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self.use_cache = os.environ.get('USE_FEISHU_CACHE', 'false').lower() == 'true'

    def _run_cli(self, cmd: list[str]) -> dict:
        """执行 lark-cli 命令并解析 JSON 输出"""
        full_cmd = ['lark-cli', '--as', 'user'] + cmd
        # record-list 默认输出 markdown，必须显式指定 JSON 格式
        if cmd[0] == 'base' and cmd[1] == '+record-list':
            full_cmd.append('--format')
            full_cmd.append('json')
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            stderr_msg = result.stderr.strip() if result.stderr else 'unknown error'
            raise RuntimeError(f"lark-cli failed: {stderr_msg}")
        if result.stderr:
            stderr_msg = result.stderr.strip()
            raise RuntimeError(f"lark-cli stderr: {stderr_msg}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            stdout_preview = result.stdout[:500]
            raise RuntimeError(f"lark-cli JSON parse error: {e}. stdout preview: {stdout_preview}")

    def read_table(self, table_name: str) -> pd.DataFrame:
        """读取指定表的全部数据"""
        # 若启用缓存且本地 CSV 存在，直接读取（加速迭代）
        if self.use_cache:
            cache_path = self.cache_dir / f'{table_name}.csv'
            if cache_path.exists():
                df = pd.read_csv(cache_path, dtype=str, keep_default_na=True)
                # 数值列自动转换
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except Exception:
                        pass
                return df
        table_id = get_table_id(table_name)
        # 优先使用表级别的 base token（不同表可能分布在不同 Base）
        base_token = get_base_token(table_name) or self.base_token
        if not base_token:
            raise ValueError(f"Base token not configured for table: {table_name}")
        # 先获取字段结构
        fields_resp = self._run_cli([
            'base', '+field-list',
            '--base-token', base_token,
            '--table-id', table_id,
        ])
        # field-list 返回结构: data.fields，字段对象使用 'name' 键
        field_items = fields_resp.get('data', {}).get('fields', [])
        field_names = [f['name'] for f in field_items]

        # 分页获取记录（使用 offset 分页，limit 最大 200）
        records = []
        offset = 0
        limit = 200
        while True:
            cmd = [
                'base', '+record-list',
                '--base-token', base_token,
                '--table-id', table_id,
                '--limit', str(limit),
                '--offset', str(offset),
            ]

            resp = self._run_cli(cmd)
            data_section = resp.get('data', {})
            # --format json 返回 2D 数组结构
            rows = data_section.get('data', [])
            resp_fields = data_section.get('fields', field_names)
            record_ids = data_section.get('record_id_list', [])

            for i, row in enumerate(rows):
                record = {'record_id': record_ids[i] if i < len(record_ids) else ''}
                for j, value in enumerate(row):
                    if j < len(resp_fields):
                        record[resp_fields[j]] = value
                records.append(record)

            if not data_section.get('has_more'):
                break
            offset += len(rows)

        # 使用 record 中实际出现的所有字段，避免 field-list 与 record-list 字段不一致导致丢列
        df = pd.DataFrame(records)
        cols = ['record_id'] + [c for c in df.columns if c != 'record_id']
        df = df[cols]
        # 防御性：Base 某些字段（如被误识别为单选/多选）会返回单元素列表，自动展平为标量
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
        # 应用字段名映射（防御性：若 Base 字段名与代码不一致，自动对齐）
        rename_dict = {k: v for k, v in FIELD_MAP.items() if k in df.columns and v not in df.columns}
        if rename_dict:
            df = df.rename(columns=rename_dict)
        return df

    def read_backend_data(self, month: str) -> pd.DataFrame:
        """读取指定月份的后链路数据"""
        table_name = f'backend_data_{month.replace("-", "_")}'
        df = self.read_table(table_name)
        return df[df['stat_month'] == month]

    def read_frontend_data(self, month: str) -> pd.DataFrame:
        """读取指定月份的前链路数据"""
        if month == '2026-04':
            # 4月前链路数据超过 20,000 行，拆分为 p1 和 p2 两张表
            df1 = self.read_table('frontend_data_2026_04_p1')
            df2 = self.read_table('frontend_data_2026_04_p2')
            df = pd.concat([df1, df2], ignore_index=True)
        elif month == '2026-05':
            # 5月前链路数据超过 20,000 行，拆分为 p1 和 p2 两张表
            df1 = self.read_table('frontend_data_2026_05_p1')
            df2 = self.read_table('frontend_data_2026_05_p2')
            df = pd.concat([df1, df2], ignore_index=True)
        else:
            table_name = f'frontend_data_{month.replace("-", "_")}'
            df = self.read_table(table_name)
        return df[df['stat_month'] == month]

    def read_category_mapping(self) -> pd.DataFrame:
        """读取品类映射表"""
        return self.read_table('category_mapping')

    def read_mau_data(self) -> pd.DataFrame:
        """读取月活数据"""
        return self.read_table('mau_data')

    def read_daily_dau(self, month: str = None) -> pd.DataFrame:
        """读取日活数据（日维度）

        Args:
            month: 月份，如 '2026-05'。为 None 时返回全部数据。
        """
        df = self.read_table('daily_dau')
        if month and '数据月份' in df.columns:
            df = df[df['数据月份'] == month]
        return df
