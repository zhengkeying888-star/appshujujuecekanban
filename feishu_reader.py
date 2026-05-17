"""从飞书多维表格读取数据的封装层"""
import subprocess
import json
import pandas as pd
from feishu_config import get_table_id, FEISHU_BASE_TOKEN


class FeishuDataSource:
    """飞书多维表格数据源"""

    def __init__(self, base_token: str = None):
        self.base_token = base_token or FEISHU_BASE_TOKEN
        if not self.base_token:
            raise ValueError("Feishu base token not configured")

    def _run_cli(self, cmd: list) -> dict:
        """执行 lark-cli 命令并解析 JSON 输出"""
        full_cmd = ['lark-cli', '--as', 'user'] + cmd
        result = subprocess.run(full_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"lark-cli failed: {result.stderr}")
        return json.loads(result.stdout)

    def read_table(self, table_name: str) -> pd.DataFrame:
        """读取指定表的全部数据"""
        table_id = get_table_id(table_name)
        # 先获取字段结构
        fields_resp = self._run_cli([
            'base', '+field-list',
            '--base-token', self.base_token,
            '--table-id', table_id,
        ])
        field_names = [f['field_name'] for f in fields_resp.get('items', [])]

        # 分页获取记录
        records = []
        page_token = None
        while True:
            cmd = [
                'base', '+record-list',
                '--base-token', self.base_token,
                '--table-id', table_id,
                '--limit', '500',
            ]
            if page_token:
                cmd.extend(['--page-token', page_token])

            resp = self._run_cli(cmd)
            items = resp.get('items', [])
            for item in items:
                record = {'record_id': item['record_id']}
                for field in field_names:
                    record[field] = item['fields'].get(field)
                records.append(record)

            if not resp.get('has_more'):
                break
            page_token = resp.get('page_token')

        df = pd.DataFrame(records)
        return df

    def read_backend_data(self, month: str) -> pd.DataFrame:
        """读取指定月份的后链路数据"""
        df = self.read_table('backend_data')
        return df[df['stat_month'] == month]

    def read_frontend_data(self, month: str) -> pd.DataFrame:
        """读取指定月份的前链路数据"""
        df = self.read_table('frontend_data')
        return df[df['stat_month'] == month]

    def read_category_mapping(self) -> pd.DataFrame:
        """读取品类映射表"""
        return self.read_table('category_mapping')

    def read_mau_data(self) -> pd.DataFrame:
        """读取月活数据"""
        return self.read_table('mau_data')
