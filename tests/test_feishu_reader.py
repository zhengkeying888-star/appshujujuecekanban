import json
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from feishu_reader import FeishuDataSource


class TestFeishuDataSource(unittest.TestCase):

    def test_init_requires_token(self):
        with self.assertRaises(ValueError):
            FeishuDataSource(base_token='')

    @patch('feishu_reader.subprocess.run')
    def test_read_table_parses_records(self, mock_run):
        # 第一次调用: +field-list, 第二次调用: +record-list
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout=json.dumps({
                    'items': [
                        {'field_name': 'stat_month'},
                        {'field_name': '线索数'},
                    ],
                }),
                stderr='',
            ),
            MagicMock(
                returncode=0,
                stdout=json.dumps({
                    'items': [
                        {'record_id': 'r1', 'fields': {'stat_month': '2026-03', '线索数': 100}}
                    ],
                    'has_more': False,
                }),
                stderr='',
            ),
        ]
        ds = FeishuDataSource(base_token='test_token')
        df = ds.read_table('backend_data')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['stat_month'], '2026-03')

    @patch('feishu_reader.subprocess.run')
    def test_read_table_paginates(self, mock_run):
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout=json.dumps({
                    'items': [
                        {'field_name': 'stat_month'},
                    ],
                }),
                stderr='',
            ),
            MagicMock(
                returncode=0,
                stdout=json.dumps({
                    'items': [
                        {'record_id': 'r1', 'fields': {'stat_month': '2026-03'}}
                    ],
                    'has_more': True,
                    'page_token': 'next_page_123',
                }),
                stderr='',
            ),
            MagicMock(
                returncode=0,
                stdout=json.dumps({
                    'items': [
                        {'record_id': 'r2', 'fields': {'stat_month': '2026-04'}}
                    ],
                    'has_more': False,
                }),
                stderr='',
            ),
        ]
        ds = FeishuDataSource(base_token='test_token')
        df = ds.read_table('backend_data')
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['stat_month'], '2026-03')
        self.assertEqual(df.iloc[1]['stat_month'], '2026-04')


if __name__ == '__main__':
    unittest.main()
