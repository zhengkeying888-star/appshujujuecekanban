"""从飞书多维表格读取数据的封装层"""
import subprocess
import json
import pandas as pd
from feishu_config import get_table_id, get_base_token


class FeishuDataSource:
    """飞书多维表格数据源"""

    def __init__(self, base_token: str = None):
        self.base_token = base_token or get_base_token()
        if not self.base_token:
            raise ValueError("Feishu base token not configured")

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
        table_id = get_table_id(table_name)
        # 先获取字段结构
        fields_resp = self._run_cli([
            'base', '+field-list',
            '--base-token', self.base_token,
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
                '--base-token', self.base_token,
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
