"""周报数据生成器：MTD 进度 + 同期对比 + 归因分析"""
import pandas as pd
import json
import os
from datetime import datetime, timedelta

USE_FEISHU = os.environ.get('USE_FEISHU', 'false').lower() == 'true'

# ============================================================
# 0. 目标配置（请按实际业务目标更新）
# ============================================================
GOALS = {
    '2026-05': {'leads': 18500, 'gmv': 2400000},   # 示例：较4月提升约5%
    '2026-04': {'leads': 17492, 'gmv': 2271977},   # 上月实际，作为基准
}

AD_NAME_MAP = {
    '选课中心-名师好课': '名师好课',
    '选课中心-好课上新': '好课上新',
    '选课中心/商品列表': '选课中心',
    '学习页-banner广告': '学习页',
    '学习页-弹窗': '学习页',
    '个人主页-课程': '个人主页',
}

TARGET_RESOURCES = [
    '选课中心', '首页弹窗', '学习页', '学习中心弹窗',
    '2025首页卡片1', '2025首页卡片5', '2025首页卡片10',
    '2025课程banner', '热门推荐',
    '好课上新', '名师好课', '个人主页'
]

# ============================================================
# 1. 数据读取
# ============================================================
if USE_FEISHU:
    from feishu_reader import FeishuDataSource
    ds = FeishuDataSource()
    df_backend = ds.read_backend_data('2026-04')
    df_backend = pd.concat([df_backend, ds.read_backend_data('2026-03')], ignore_index=True)
    ad_cur = ds.read_frontend_data('2026-04')
    ad_prev = ds.read_frontend_data('2026-03')
    mau_df = ds.read_mau_data()
else:
    df_backend = pd.read_excel('/Users/zhengkeying/agent teams作业/APP线索广告位拆解 3-4月明细版本.xlsx')
    ad_cur = pd.read_excel('/Users/zhengkeying/agent teams作业/4月广告位明细.xlsx')
    ad_prev = pd.read_excel('/Users/zhengkeying/agent teams作业/APP广告位明细3月汇总.xlsx')
    mau_df = pd.read_excel('/Users/zhengkeying/agent teams作业/3-4月月活人数.xlsx')

# 过滤合计行
df_backend = df_backend[df_backend['stat_month'] != '合计'].copy()

# 数值转换
df_backend['order_time'] = pd.to_datetime(df_backend['order_time'], errors='coerce')
for col in ['首单数', '首单流水', 'is_add_friend', '是否到课']:
    if col in df_backend.columns:
        df_backend[col] = pd.to_numeric(df_backend[col], errors='coerce')
for col in df_backend.columns:
    if '完课' in col or '到课' in col or col.startswith('是否第'):
        df_backend[col] = pd.to_numeric(df_backend[col], errors='coerce')

# 前端数据转换
for col in ['曝光uv', '点击uv', '售卖页浏览uv', '线索数', '首单订单数', '首单订单金额', '课程价格']:
    if col in ad_cur.columns:
        ad_cur[col] = pd.to_numeric(ad_cur[col], errors='coerce')
    if col in ad_prev.columns:
        ad_prev[col] = pd.to_numeric(ad_prev[col], errors='coerce')

# 映射资源位
for ad in [ad_cur, ad_prev]:
    ad['resource'] = ad['广告位名称'].map(AD_NAME_MAP).fillna(ad['广告位名称'])
    ad.drop(ad[ad['广告位名称'].isin(['H5-课程播放页-广告'])].index, inplace=True)

# ============================================================
# 2. 确定当前月份与 MTD 范围
# ============================================================
latest_date = df_backend['order_time'].max()
current_month = latest_date.strftime('%Y-%m')
prev_month = (latest_date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
latest_day = latest_date.day

print(f'最新数据日期: {latest_date.date()}')
print(f'当前月份: {current_month}，对比月份: {prev_month}')
print(f'MTD 范围: 1-{latest_day} 日')

# ============================================================
# 3. MTD 数据切片
# ============================================================
def filter_mtd(df, month_str, max_day):
    """筛选某月份 1号 ~ max_day 的数据"""
    sub = df[df['stat_month'] == month_str].copy()
    sub['day'] = sub['order_time'].dt.day
    return sub[sub['day'] <= max_day]

cur_mtd = filter_mtd(df_backend, current_month, latest_day)
prev_mtd = filter_mtd(df_backend, prev_month, latest_day)

# 前端 MTD
cur_ad = ad_cur.copy()
prev_ad = ad_prev.copy()

# ============================================================
# 4. 核心指标计算
# ============================================================
def calc_metrics(backend_df, ad_df, mau_total):
    leads = len(backend_df)
    orders = int(backend_df['首单数'].sum())
    gmv = float(backend_df['首单流水'].sum())
    add_friend = int(backend_df['is_add_friend'].sum())
    attend = int(backend_df['是否到课'].sum())

    completion_cols = [c for c in backend_df.columns if '完课' in c]
    complete = int(backend_df[completion_cols].apply(
        lambda row: (row.fillna(0) >= 1).any(), axis=1
    ).sum())

    cvr = round(orders / leads * 100, 2) if leads > 0 else 0
    arpu = round(gmv / leads, 2) if leads > 0 else 0

    exposure = int(ad_df['曝光uv'].sum()) if '曝光uv' in ad_df.columns else 0
    click = int(ad_df['点击uv'].sum()) if '点击uv' in ad_df.columns else 0
    lead_rate = round(leads / exposure * 100, 2) if exposure > 0 else 0
    ctr = round(click / exposure * 100, 2) if exposure > 0 else 0

    lead_gen_rate = round(leads / mau_total * 100, 2) if mau_total > 0 else 0

    return {
        'leads': leads,
        'orders': orders,
        'gmv': gmv,
        'add_friend': add_friend,
        'attend': attend,
        'complete': complete,
        'cvr': cvr,
        'arpu': arpu,
        'exposure': exposure,
        'click': click,
        'lead_rate': lead_rate,
        'ctr': ctr,
        'lead_gen_rate': lead_gen_rate,
    }

cur_mau = mau_df[mau_df['月份'].astype(str) == current_month]['月活人数'].sum() if '月份' in mau_df.columns else 0
prev_mau = mau_df[mau_df['月份'].astype(str) == prev_month]['月活人数'].sum() if '月份' in mau_df.columns else 0

cur_metrics = calc_metrics(cur_mtd, cur_ad, cur_mau)
prev_metrics = calc_metrics(prev_mtd, prev_ad, prev_mau)

# ============================================================
# 5. 目标差距
# ============================================================
goal = GOALS.get(current_month, GOALS.get('2026-05', {'leads': 0, 'gmv': 0}))
cur_metrics['leads_gap'] = goal['leads'] - cur_metrics['leads']
cur_metrics['gmv_gap'] = goal['gmv'] - cur_metrics['gmv']
cur_metrics['leads_goal'] = goal['leads']
cur_metrics['gmv_goal'] = goal['gmv']

# ============================================================
# 6. 资源位归因
# ============================================================
def resource_attribution(backend_df, ad_df):
    sub = backend_df[backend_df['tag_level_1'].isin(TARGET_RESOURCES)].copy()
    res = []
    for r in TARGET_RESOURCES:
        b = sub[sub['tag_level_1'] == r]
        a = ad_df[ad_df['resource'] == r] if 'resource' in ad_df.columns else pd.DataFrame()
        leads = len(b)
        orders = int(b['首单数'].sum())
        gmv = float(b['首单流水'].sum())
        cvr = round(orders / leads * 100, 2) if leads > 0 else 0
        exposure = int(a['曝光uv'].sum()) if '曝光uv' in a.columns else 0
        lead_rate = round(leads / exposure * 100, 2) if exposure > 0 else 0
        res.append({
            'resource': r,
            'leads': leads,
            'orders': orders,
            'gmv': gmv,
            'cvr': cvr,
            'exposure': exposure,
            'lead_rate': lead_rate,
        })
    return pd.DataFrame(res)

cur_res = resource_attribution(cur_mtd, cur_ad)
prev_res = resource_attribution(prev_mtd, prev_ad)

res_merged = pd.merge(cur_res, prev_res, on='resource', suffixes=('_cur', '_prev'), how='outer').fillna(0)
res_merged['leads_change'] = res_merged['leads_cur'] - res_merged['leads_prev']
res_merged['leads_mom'] = round(res_merged['leads_change'] / res_merged['leads_prev'] * 100, 2).replace([float('inf'), -float('inf')], 0).fillna(0)
res_merged['gmv_change'] = res_merged['gmv_cur'] - res_merged['gmv_prev']
res_merged['cvr_change'] = res_merged['cvr_cur'] - res_merged['cvr_prev']

res_merged['impact'] = res_merged['leads_change'].abs()
res_merged = res_merged.sort_values('impact', ascending=False)

top_movers = []
for _, row in res_merged.head(5).iterrows():
    top_movers.append({
        'resource': row['resource'],
        'leads_cur': int(row['leads_cur']),
        'leads_prev': int(row['leads_prev']),
        'leads_change': int(row['leads_change']),
        'leads_mom': float(row['leads_mom']),
        'gmv_cur': float(row['gmv_cur']),
        'gmv_prev': float(row['gmv_prev']),
        'cvr_cur': float(row['cvr_cur']),
        'cvr_prev': float(row['cvr_prev']),
        'lead_rate_cur': float(row['lead_rate_cur']),
        'lead_rate_prev': float(row['lead_rate_prev']),
    })

# ============================================================
# 7. 品类归因（Top 1 资源位下钻）
# ============================================================
top_resource = top_movers[0]['resource'] if top_movers else None

category_breakdown = []
if top_resource:
    for month, mtd_df in [('cur', cur_mtd), ('prev', prev_mtd)]:
        sub = mtd_df[(mtd_df['tag_level_1'] == top_resource) & (mtd_df['category_name'].notna())]
        cat_agg = sub.groupby('category_name').agg({'首单数': 'sum', '首单流水': 'sum'}).reset_index()
        cat_agg['leads'] = sub.groupby('category_name').size().values
        cat_agg = cat_agg.sort_values('leads', ascending=False).head(5)
        for _, row in cat_agg.iterrows():
            category_breakdown.append({
                'month': month,
                'resource': top_resource,
                'category': row['category_name'],
                'leads': int(row['leads']),
                'orders': int(row['首单数']),
                'gmv': float(row['首单流水']),
                'cvr': round(row['首单数'] / row['leads'] * 100, 2) if row['leads'] > 0 else 0,
            })

# ============================================================
# 8. 价格带归因
# ============================================================
def map_price_band(price):
    if price == 0:
        return '0元'
    if price == 1.1:
        return '1.1元'
    if price == 3.9:
        return '3.9元'
    return '其他'

price_band_breakdown = []
if top_resource:
    for month, mtd_df in [('cur', cur_mtd), ('prev', prev_mtd)]:
        sub = mtd_df[(mtd_df['tag_level_1'] == top_resource)].copy()
        sub['price_band'] = pd.to_numeric(sub['sku_price'], errors='coerce').apply(map_price_band)
        pb_agg = sub.groupby('price_band').size().reset_index(name='leads')
        pb_agg = pb_agg.sort_values('leads', ascending=False)
        for _, row in pb_agg.iterrows():
            price_band_breakdown.append({
                'month': month,
                'resource': top_resource,
                'price_band': row['price_band'],
                'leads': int(row['leads']),
            })

# ============================================================
# 9. 组装输出
# ============================================================
output = {
    'meta': {
        'report_type': 'weekly_mtd',
        'current_month': current_month,
        'previous_month': prev_month,
        'mtd_day': latest_day,
        'report_date': latest_date.strftime('%Y-%m-%d'),
        'data_source': 'feishu' if USE_FEISHU else 'local',
    },
    'summary': {
        'current': cur_metrics,
        'previous': prev_metrics,
        'mom': {
            'leads': round((cur_metrics['leads'] - prev_metrics['leads']) / prev_metrics['leads'] * 100, 2) if prev_metrics['leads'] else 0,
            'gmv': round((cur_metrics['gmv'] - prev_metrics['gmv']) / prev_metrics['gmv'] * 100, 2) if prev_metrics['gmv'] else 0,
            'cvr': round(cur_metrics['cvr'] - prev_metrics['cvr'], 2),
            'lead_gen_rate': round(cur_metrics['lead_gen_rate'] - prev_metrics['lead_gen_rate'], 2),
            'lead_rate': round(cur_metrics['lead_rate'] - prev_metrics['lead_rate'], 2),
            'arpu': round(cur_metrics['arpu'] - prev_metrics['arpu'], 2),
        },
    },
    'resource_movers': top_movers,
    'category_breakdown': category_breakdown,
    'price_band_breakdown': price_band_breakdown,
    'all_resources': res_merged[['resource', 'leads_cur', 'leads_prev', 'leads_change', 'leads_mom', 'gmv_cur', 'gmv_prev']].to_dict('records'),
}

out_path = '/Users/zhengkeying/agent teams作业/weekly_report_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'周报数据已生成: {out_path}')
print(f'当前MTD线索数: {cur_metrics["leads"]}，上月同期: {prev_metrics["leads"]}，环比: {output["summary"]["mom"]["leads"]}%')
print(f'当前MTD GMV: ¥{cur_metrics["gmv"]:.0f}，上月同期: ¥{prev_metrics["gmv"]:.0f}，环比: {output["summary"]["mom"]["gmv"]}%')
print(f'目标线索: {goal["leads"]}，差距: {cur_metrics["leads_gap"]}')
print(f'目标GMV: ¥{goal["gmv"]:.0f}，差距: ¥{cur_metrics["gmv_gap"]:.0f}')
if top_movers:
    print(f'影响最大资源位: {top_movers[0]["resource"]}，线索变化: {top_movers[0]["leads_change"]}')
