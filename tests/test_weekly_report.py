import unittest
from unittest.mock import patch, mock_open
import json
from generate_weekly_report import build_kpi_cards, build_resource_top5, generate_weekly_report


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

    def test_generate_report_creates_file(self):
        with patch('generate_weekly_report.load_analysis_data') as mock_load:
            mock_load.return_value = {
                'monthly_summary': {
                    '2026-03': {'leads': 18066, 'gmv': 2271977, 'cvr_from_leads': 7.29, 'arpu': 125.8},
                    '2026-04': {'leads': 17492, 'gmv': 1993411, 'cvr_from_leads': 6.72, 'arpu': 114.0},
                    '环比': {'leads': -3.18, 'gmv': -12.26, 'cvr_from_leads': -7.82, 'arpu': -9.38},
                },
                'resource_efficiency': [],
                'strategy_cards': [],
            }
            with patch('builtins.open', mock_open()) as mock_file:
                xml = generate_weekly_report('test_output.xml')
                mock_file.assert_called_once_with('test_output.xml', 'w', encoding='utf-8')
                self.assertIn('APP 线索广告位投放周报', xml)


if __name__ == '__main__':
    unittest.main()
