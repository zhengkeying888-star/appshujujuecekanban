"""
数据迁移脚本：本地 Excel → Neon PostgreSQL

运行前必须先设置环境变量：
    export DATABASE_URL='postgresql://...-pooler.neon.tech/...?sslmode=require'

用法：
    python3 migrate_to_neon.py
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

from db import get_conn, table_exists, count_rows

# ============================================================
# 0. 配置
# ============================================================
DATA_DIR = Path(__file__).parent

AD_NAME_MAP = {
    '选课中心-名师好课': '名师好课',
    '选课中心-好课上新': '好课上新',
    '选课中心/商品列表': '选课中心',
    '学习页-banner广告': '学习页',
    '学习页-弹窗': '学习页',
    '个人主页-课程': '个人主页',
}

# 完课列（用于生成 completion_json）
COMPLETION_COLS = [
    '先导课是否完课', '是否第1节完课', '第2节是否完课', '第3节是否完课',
    '第4节是否完课', '第5节是否完课', '第6节是否完课', '第7节是否完课',
    '第8节是否完课', '第9节是否完课', '第10节是否完课',
]

# 到课列（用于生成 attendance_json）
ATTENDANCE_COLS = [
    '先导课是否到课', '是否第1节到课', '是否第2节到课', '是否第3节到课',
    '是否第4节到课', '是否第5节到课', '是否第6节到课', '是否第7节到课',
    '是否第8节到课', '是否第9节到课', '是否第10节到课',
]

BATCH_SIZE = 1000


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def run_schema():
    """执行建表语句"""
    schema_path = Path(__file__).parent / 'schema.sql'
    if not schema_path.exists():
        raise FileNotFoundError(f"schema.sql 不存在: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    with get_conn() as conn:
        with conn.cursor() as cur:
            # psycopg v3 execute 只支持单条语句，按分号拆分逐条执行
            for stmt in sql.split(';'):
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    cur.execute(stmt)
        conn.commit()
    log("Schema 创建完成")


def _to_jsonb_dict(row, cols):
    """把指定列转为 dict，过滤 NaN"""
    d = {}
    for c in cols:
        if c in row.index and pd.notna(row[c]):
            try:
                d[c] = int(float(row[c]))
            except (ValueError, TypeError):
                d[c] = str(row[c])
    return d


def migrate_backend():
    """迁移后链路数据"""
    log("开始迁移 backend_leads ...")
    excel_path = DATA_DIR / '更新4-5月app数据.xlsx'
    if not excel_path.exists():
        # fallback
        excel_path = DATA_DIR / 'APP线索广告位拆解 3-4月明细版本.xlsx'
    if not excel_path.exists():
        raise FileNotFoundError("找不到后链路数据文件（更新4-5月app数据.xlsx 或 APP线索广告位拆解 3-4月明细版本.xlsx）")

    df = pd.read_excel(excel_path)
    df = df[df['stat_month'] != '合计'].copy()
    total = len(df)
    log(f"读取后链路数据: {total} 行")

    # 数值转换
    for col in ['首单数', '首单流水', 'is_add_friend', '是否到课', 'LTV', '线索数']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    insert_sql = """
        INSERT INTO backend_leads (
            stat_month, order_time, tag_level_1, category_name, camp_name,
            sku_price, is_add_friend, first_order_count, first_order_revenue,
            attended, ltv, lead_count, user_id, sex, age, city, growth_level,
            completion_json, attendance_json, raw_json
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, %s::jsonb
        )
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            batch = []
            for _, row in df.iterrows():
                completion = _to_jsonb_dict(row, COMPLETION_COLS)
                attendance = _to_jsonb_dict(row, ATTENDANCE_COLS)
                # raw_json 只保留分析可能用到的扩展字段，避免过大
                raw = {}
                for c in ['广告位监控', 'tag_level_2', 'channel_name', 'teacher_name',
                          'province', 'city_level', 'model_name', 'occupation']:
                    if c in row.index and pd.notna(row[c]):
                        raw[c] = str(row[c])

                batch.append((
                    str(row.get('stat_month', '')),
                    row.get('order_time'),
                    str(row.get('tag_level_1', '')) if pd.notna(row.get('tag_level_1')) else None,
                    str(row.get('category_name', '')) if pd.notna(row.get('category_name')) else None,
                    str(row.get('camp_name', '')) if pd.notna(row.get('camp_name')) else None,
                    float(row['sku_price']) if pd.notna(row.get('sku_price')) else None,
                    int(row['is_add_friend']) if pd.notna(row.get('is_add_friend')) else None,
                    int(row['首单数']) if pd.notna(row.get('首单数')) else None,
                    float(row['首单流水']) if pd.notna(row.get('首单流水')) else None,
                    int(row['是否到课']) if pd.notna(row.get('是否到课')) else None,
                    float(row['LTV']) if pd.notna(row.get('LTV')) else None,
                    int(row['线索数']) if pd.notna(row.get('线索数')) else 1,
                    str(row.get('user_id', '')) if pd.notna(row.get('user_id')) else None,
                    str(row.get('sex', '')) if pd.notna(row.get('sex')) else None,
                    str(row.get('age', '')) if pd.notna(row.get('age')) else None,
                    str(row.get('city', '')) if pd.notna(row.get('city')) else None,
                    str(row.get('growth_level', '')) if pd.notna(row.get('growth_level')) else None,
                    json.dumps(completion, ensure_ascii=False) if completion else None,
                    json.dumps(attendance, ensure_ascii=False) if attendance else None,
                    json.dumps(raw, ensure_ascii=False) if raw else None,
                ))
                if len(batch) >= BATCH_SIZE:
                    cur.executemany(insert_sql, batch)
                    conn.commit()
                    batch.clear()
            if batch:
                cur.executemany(insert_sql, batch)
                conn.commit()

    n = count_rows('backend_leads')
    log(f"backend_leads 迁移完成: {n} 行")


def migrate_frontend():
    """迁移前链路数据（3-5月）"""
    log("开始迁移 frontend_daily ...")
    files = {
        '2026-03': DATA_DIR / 'APP广告位明细3月汇总.xlsx',
        '2026-04': DATA_DIR / '4月广告位明细.xlsx',
        '2026-05': DATA_DIR / '5.1-17广告位明细.xlsx',
    }

    insert_sql = """
        INSERT INTO frontend_daily (
            data_date, stat_month, ad_name, resource, category_name,
            exposure_uv, click_uv, sales_page_uv, leads,
            first_orders, first_order_amount, sku_price
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    total = 0
    with get_conn() as conn:
        with conn.cursor() as cur:
            for month, path in files.items():
                if not path.exists():
                    log(f"跳过: {path.name} 不存在")
                    continue
                df = pd.read_excel(path)
                log(f"读取 {path.name}: {len(df)} 行")
                # 字段名兼容（Base 中可能是 sku_price / category_name）
                if 'sku_price' in df.columns and '课程价格' not in df.columns:
                    df.rename(columns={'sku_price': '课程价格'}, inplace=True)
                if 'category_name' in df.columns and '品类名称' not in df.columns:
                    df.rename(columns={'category_name': '品类名称'}, inplace=True)
                for col in ['曝光uv', '点击uv', '售卖页浏览uv', '线索数', '首单订单数', '首单订单金额', '课程价格']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                batch = []
                for _, row in df.iterrows():
                    ad_name = str(row.get('广告位名称', '')) if pd.notna(row.get('广告位名称')) else None
                    resource = AD_NAME_MAP.get(ad_name, ad_name)
                    date_val = row.get('日期')
                    if pd.isna(date_val):
                        continue
                    batch.append((
                        date_val,
                        month,
                        ad_name,
                        resource,
                        str(row.get('品类名称', '')) if pd.notna(row.get('品类名称')) else None,
                        int(row['曝光uv']) if pd.notna(row.get('曝光uv')) else None,
                        int(row['点击uv']) if pd.notna(row.get('点击uv')) else None,
                        int(row['售卖页浏览uv']) if pd.notna(row.get('售卖页浏览uv')) else None,
                        int(row['线索数']) if pd.notna(row.get('线索数')) else None,
                        int(row['首单订单数']) if pd.notna(row.get('首单订单数')) else None,
                        float(row['首单订单金额']) if pd.notna(row.get('首单订单金额')) else None,
                        float(row['课程价格']) if pd.notna(row.get('课程价格')) else None,
                    ))
                    if len(batch) >= BATCH_SIZE:
                        cur.executemany(insert_sql, batch)
                        conn.commit()
                        total += len(batch)
                        batch.clear()
                if batch:
                    cur.executemany(insert_sql, batch)
                    conn.commit()
                    total += len(batch)

    n = count_rows('frontend_daily')
    log(f"frontend_daily 迁移完成: {n} 行")


def migrate_mau():
    """迁移月活数据"""
    log("开始迁移 mau_monthly ...")
    path = DATA_DIR / 'mau_data_3_4_5.xlsx'
    if not path.exists():
        raise FileNotFoundError(f"找不到 MAU 数据: {path}")
    df = pd.read_excel(path)
    log(f"读取 MAU 数据: {len(df)} 行")

    insert_sql = """
        INSERT INTO mau_monthly (stat_month, user_level, mau, ratio)
        VALUES (%s, %s, %s, %s)
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            batch = []
            for _, row in df.iterrows():
                batch.append((
                    str(row.get('月份', '')),
                    int(row['用户等级']) if pd.notna(row.get('用户等级')) else None,
                    int(row['月活人数']) if pd.notna(row.get('月活人数')) else None,
                    float(row['占比']) if pd.notna(row.get('占比')) else None,
                ))
            cur.executemany(insert_sql, batch)
            conn.commit()

    n = count_rows('mau_monthly')
    log(f"mau_monthly 迁移完成: {n} 行")


def migrate_dau():
    """迁移日活数据（只保留日期 + DAU + 新用户数）"""
    log("开始迁移 daily_dau ...")
    path = DATA_DIR / '日维度日活3-5月.xlsx'
    if not path.exists():
        raise FileNotFoundError(f"找不到 DAU 数据: {path}")
    df = pd.read_excel(path)
    log(f"读取 DAU 数据: {len(df)} 行")

    insert_sql = """
        INSERT INTO daily_dau (data_date, dau, new_users)
        VALUES (%s, %s, %s)
        ON CONFLICT (data_date) DO UPDATE SET
            dau = EXCLUDED.dau,
            new_users = EXCLUDED.new_users
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            batch = []
            for _, row in df.iterrows():
                batch.append((
                    row.get('日期'),
                    int(row['日活人数']) if pd.notna(row.get('日活人数')) else None,
                    int(row['当日新用户数']) if pd.notna(row.get('当日新用户数')) else None,
                ))
            cur.executemany(insert_sql, batch)
            conn.commit()

    n = count_rows('daily_dau')
    log(f"daily_dau 迁移完成: {n} 行")


def migrate_category():
    """迁移品类映射（正式品/孵化品 + 兴趣线/健康线/变美线）"""
    log("开始迁移 category_mapping ...")
    # 1. 正式品/孵化品
    cat_type_df = pd.read_csv(DATA_DIR / 'APP品类流量结构.csv', nrows=100)
    cat_type_df = cat_type_df.iloc[:, [1, 2]].dropna()
    cat_type_df.columns = ['品类', '品类区别']

    # 2. 兴趣线/健康线/变美线
    cat_attr_df = pd.read_excel(DATA_DIR / '【重要】品类归属.xlsx')

    # 合并
    mapping = {}
    for _, row in cat_type_df.iterrows():
        cat = str(row['品类']).strip()
        mapping[cat] = {'cat_type': str(row['品类区别']).strip()}
    for _, row in cat_attr_df.iterrows():
        cat = str(row['品类']).strip()
        attr = str(row['品类属性']).strip()
        if cat not in mapping:
            mapping[cat] = {}
        mapping[cat]['cat_attr'] = attr

    # 补充映射（与 generate_analysis.py 一致）
    mapping['中式美食制作'] = {'cat_type': '孵化品', 'cat_attr': '兴趣线'}
    mapping['养正变美'] = {'cat_type': '孵化品', 'cat_attr': '变美线'}
    mapping['开心晨练团'] = {'cat_type': '正式品', 'cat_attr': '健康线'}

    insert_sql = """
        INSERT INTO category_mapping (category_name, cat_type, cat_attr)
        VALUES (%s, %s, %s)
        ON CONFLICT (category_name) DO UPDATE SET
            cat_type = EXCLUDED.cat_type,
            cat_attr = EXCLUDED.cat_attr
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            batch = [(k, v.get('cat_type'), v.get('cat_attr')) for k, v in mapping.items()]
            cur.executemany(insert_sql, batch)
            conn.commit()

    n = count_rows('category_mapping')
    log(f"category_mapping 迁移完成: {n} 行")


def main():
    log("=" * 50)
    log("开始迁移数据到 Neon PostgreSQL")
    log("=" * 50)

    # 验证环境变量
    if not os.environ.get('DATABASE_URL'):
        log("错误: DATABASE_URL 环境变量未设置")
        log("请从 Vercel Dashboard → Storage → Neon 获取连接字符串并设置环境变量")
        sys.exit(1)

    # 建表
    run_schema()

    # 迁移各表
    migrate_backend()
    migrate_frontend()
    migrate_mau()
    migrate_dau()
    migrate_category()

    log("=" * 50)
    log("全部迁移完成")
    log("=" * 50)
    for tbl in ['backend_leads', 'frontend_daily', 'mau_monthly', 'daily_dau', 'category_mapping']:
        n = count_rows(tbl)
        log(f"  {tbl}: {n} 行")


if __name__ == '__main__':
    main()
