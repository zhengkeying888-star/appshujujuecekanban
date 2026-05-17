import unittest
from unittest.mock import patch, mock_open
import json
from generate_weekly_report import (
    build_kpi_cards,
    build_resource_top5,
    build_strategy_summary,
    generate_weekly_report,
)


class TestWeeklyReport(unittest.TestCase):

    def test_build_kpi_cards_returns_grid(self):
        data = {
            'monthly_summary': {
                '2026-03': {'leads': 18066, 'gmv': 2271977, 'cvr_from_leads': 7.29, 'arpu': 125.8},
                '2026-04': {'leads': 17492, 'gmv': 1993411, 'cvr_from_leads': 6.72, 'arpu': 114.0},
                '环比': {'leads': -3.18, 'gmv': -12.26, 'cvr_from_leads': -7.82, 'arpu': -9.38},
            }
        }
        result = build_kpi_cards(data)
        self.assertIn('<grid>', result)
        self.assertIn('17,492', result)

    def test_build_resource_top5_returns_table(self):
        data = {
            'resource_efficiency': [
                {
                    'resource': '选课中心',
                    '2026-04': {'leads': 5000, 'gmv': 500000, 'cvr_from_leads': 6.72},
                },
                {
                    'resource': '首页弹窗',
                    '2026-04': {'leads': 3000, 'gmv': 300000, 'cvr_from_leads': 5.50},
                },
                {
                    'resource': '学习页',
                    '2026-04': {'leads': 2000, 'gmv': 200000, 'cvr_from_leads': 4.80},
                },
                {
                    'resource': '热门推荐',
                    '2026-04': {'leads': 1500, 'gmv': 150000, 'cvr_from_leads': 3.90},
                },
                {
                    'resource': '好课上新',
                    '2026-04': {'leads': 1000, 'gmv': 100000, 'cvr_from_leads': 3.20},
                },
                {
                    'resource': '名师好课',
                    '2026-04': {'leads': 800, 'gmv': 80000, 'cvr_from_leads': 2.80},
                },
            ]
        }
        result = build_resource_top5(data)
        self.assertIn('<table>', result)
        self.assertIn('选课中心', result)
        # CVR should be formatted as 6.72%, not 672.00%
        self.assertIn('6.72%', result)
        self.assertNotIn('672.00%', result)

    def test_build_strategy_summary_returns_items(self):
        data = {
            'strategy_cards': [
                {
                    'category': '资源位优化',
                    'title': '提升选课中心转化',
                    'desc': '通过优化素材提升选课中心转化率',
                    'gmv_impact': '+5%',
                    'risk': '低',
                },
                {
                    'category': '价格带调整',
                    'title': '增加3.9元课投放',
                    'desc': '3.9元课转化表现优异，建议加大投放',
                    'gmv_impact': '+3%',
                    'risk': '中',
                },
            ]
        }
        result = build_strategy_summary(data)
        self.assertIn('资源位优化', result)
        self.assertIn('提升选课中心转化', result)
        self.assertIn('+5%', result)
        self.assertIn('低', result)

    def test_generate_report_creates_file(self):
        with patch('generate_weekly_report.load_analysis_data') as mock_load:
            mock_load.return_value = {
                'monthly_summary': {
                    '2026-03': {'leads': 18066, 'gmv': 2271977, 'cvr_from_leads': 7.29, 'arpu': 125.8},
                    '2026-04': {'leads': 17492, 'gmv': 1993411, 'cvr_from_leads': 6.72, 'arpu': 114.0},
                    '环比': {'leads': -3.18, 'gmv': -12.26, 'cvr_from_leads': -7.82, 'arpu': -9.38},
                },
                'resource_efficiency': [
                    {
                        'resource': '选课中心',
                        '2026-04': {'leads': 5000, 'gmv': 500000, 'cvr_from_leads': 6.72},
                    }
                ],
                'strategy_cards': [
                    {
                        'category': '资源位优化',
                        'title': '测试',
                        'desc': '测试描述',
                        'gmv_impact': '+1%',
                        'risk': '低',
                    }
                ],
            }
            with patch('builtins.open', mock_open()) as mock_file:
                xml = generate_weekly_report('test_output.xml')
                mock_file.assert_called_once_with('test_output.xml', 'w', encoding='utf-8')
                self.assertIn('APP 线索广告位投放周报', xml)


if __name__ == '__main__':
    unittest.main()
