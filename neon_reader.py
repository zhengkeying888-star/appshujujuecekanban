"""Neon PostgreSQL 数据源封装层

接口与 feishu_reader.FeishuDataSource 保持一致，
支持通过环境变量 USE_NEON=true 在 generate_analysis.py / generate_weekly_report.py 中无缝切换。

环境变量：
  DATABASE_URL — Neon pooled connection string
"""
import os
import pandas as pd
import json
from datetime import datetime
from db import get_conn, query_to_df


class NeonDataSource:
    """Neon PostgreSQL 数据源"""

    def __init__(self):
        # 验证连接可用
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                ver = cur.fetchone()[0]
                print(f"[NeonDataSource] 已连接: {ver[:50]}...")

    def read_backend_data(self, month: str) -> pd.DataFrame:
        """读取指定月份的后链路数据"""
        sql = """
            SELECT
                stat_month,
                order_time,
                tag_level_1,
                category_name,
                camp_name,
                sku_price,
                is_add_friend,
                first_order_count AS "首单数",
                first_order_revenue AS "首单流水",
                attended AS "是否到课",
                ltv AS "LTV",
                lead_count AS "线索数",
                user_id,
                sex,
                age,
                city,
                growth_level,
                completion_json,
                attendance_json
            FROM backend_leads
            WHERE stat_month = %s
        """
        df = query_to_df(sql, params=(month,))

        # JSONB 展开为独立列（兼容 generate_analysis.py 中的完课/到课列访问）
        def _expand_jsonb(col_name):
            if col_name not in df.columns or df[col_name].isna().all():
                return
            parsed = df[col_name].apply(lambda x: json.loads(x) if pd.notna(x) and isinstance(x, str) else (x if pd.notna(x) else {}))
            if parsed.empty:
                return
            expanded = pd.DataFrame.from_records(parsed.tolist(), index=df.index)
            for c in expanded.columns:
                if c not in df.columns:
                    df[c] = expanded[c]

        _expand_jsonb('completion_json')
        _expand_jsonb('attendance_json')

        # 完课列确保为数值型（generate_analysis.py 会遍历这些列）
        completion_cols = [
            '先导课是否完课', '是否第1节完课', '第2节是否完课', '第3节是否完课',
            '第4节是否完课', '第5节是否完课', '第6节是否完课', '第7节是否完课',
            '第8节是否完课', '第9节是否完课', '第10节是否完课',
        ]
        for c in completion_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')

        # 数值列转换
        for col in ['首单数', '首单流水', 'is_add_friend', '是否到课', 'LTV', '线索数']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def read_backend_data_fast(self, month: str) -> pd.DataFrame:
        """快速读取后链路数据（不含 JSONB 扩展列，适合周报场景）"""
        sql = """
            SELECT
                stat_month,
                order_time,
                tag_level_1,
                category_name,
                camp_name,
                sku_price,
                is_add_friend,
                first_order_count AS "首单数",
                first_order_revenue AS "首单流水",
                attended AS "是否到课",
                ltv AS "LTV",
                lead_count AS "线索数",
                user_id,
                sex,
                age,
                city,
                growth_level
            FROM backend_leads
            WHERE stat_month = %s
        """
        df = query_to_df(sql, params=(month,))
        for col in ['首单数', '首单流水', 'is_add_friend', '是否到课', 'LTV', '线索数']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def read_frontend_data(self, month: str) -> pd.DataFrame:
        """读取指定月份的前链路数据"""
        sql = """
            SELECT
                data_date AS "日期",
                stat_month,
                ad_name AS "广告位名称",
                resource,
                category_name AS "品类名称",
                exposure_uv AS "曝光uv",
                click_uv AS "点击uv",
                sales_page_uv AS "售卖页浏览uv",
                leads AS "线索数",
                first_orders AS "首单订单数",
                first_order_amount AS "首单订单金额",
                sku_price AS "课程价格"
            FROM frontend_daily
            WHERE stat_month = %s
        """
        df = query_to_df(sql, params=(month,))

        for col in ['曝光uv', '点击uv', '售卖页浏览uv', '线索数', '首单订单数', '首单订单金额', '课程价格']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def read_mau_data(self) -> pd.DataFrame:
        """读取月活数据"""
        sql = """
            SELECT
                stat_month AS "月份",
                user_level AS "用户等级",
                mau AS "月活人数",
                ratio AS "占比"
            FROM mau_monthly
        """
        df = query_to_df(sql)
        df['月活人数'] = pd.to_numeric(df['月活人数'], errors='coerce')
        df['占比'] = pd.to_numeric(df['占比'], errors='coerce')
        return df

    def read_daily_dau(self, month: str = None) -> pd.DataFrame:
        """读取日活数据（日维度）

        Args:
            month: 月份，如 '2026-05'。为 None 时返回全部数据。
        """
        if month:
            sql = """
                SELECT data_date AS "日期", dau AS "日活人数", new_users
                FROM daily_dau
                WHERE TO_CHAR(data_date, 'YYYY-MM') = %s
                ORDER BY data_date
            """
            params = (month,)
        else:
            sql = """
                SELECT data_date AS "日期", dau AS "日活人数", new_users
                FROM daily_dau
                ORDER BY data_date
            """
            params = None
        df = query_to_df(sql, params=params)
        df['日活人数'] = pd.to_numeric(df['日活人数'], errors='coerce')
        return df

    def read_category_mapping(self) -> pd.DataFrame:
        """读取品类映射表"""
        sql = """
            SELECT
                category_name AS "品类",
                cat_type AS "品类区别",
                cat_attr AS "品类属性"
            FROM category_mapping
        """
        return query_to_df(sql)


def _test():
    """快速验证 Neon 数据源"""
    ds = NeonDataSource()
    for month in ['2026-03', '2026-04', '2026-05']:
        df = ds.read_backend_data(month)
        print(f"  {month} backend: {len(df)} 行")
    for month in ['2026-03', '2026-04', '2026-05']:
        df = ds.read_frontend_data(month)
        print(f"  {month} frontend: {len(df)} 行")
    print(f"  mau: {len(ds.read_mau_data())} 行")
    print(f"  dau: {len(ds.read_daily_dau())} 行")
    print(f"  category: {len(ds.read_category_mapping())} 行")


if __name__ == '__main__':
    _test()
