"""周报数据生成器（前链路版）：MTD 进度 + 同期对比 + 前链路漏斗归因"""
import pandas as pd
import json
import os
from datetime import datetime, timedelta

USE_FEISHU = os.environ.get('USE_FEISHU', 'false').lower() == 'true'

# ============================================================
# 0. 目标配置（请按实际业务目标更新）
# ============================================================
GOALS = {
    '2026-05': {'leads': 18500},
    '2026-04': {'leads': 17492},
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
    df_backend = ds.read_backend_data('2026-03')
    df_backend = pd.concat([df_backend, ds.read_backend_data('2026-04')], ignore_index=True)
    df_backend = pd.concat([df_backend, ds.read_backend_data('2026-05')], ignore_index=True)
    ad_data = {
        '2026-03': ds.read_frontend_data('2026-03'),
        '2026-04': ds.read_frontend_data('2026-04'),
        '2026-05': ds.read_frontend_data('2026-05'),
    }
    df_mau = ds.read_mau_data()
else:
    # 后链路数据（3-5月合并）
    df_backend = pd.read_excel('/Users/zhengkeying/agent teams作业/更新4-5月app数据.xlsx')
    # 前链路数据（按月分文件）
    ad_data = {
        '2026-03': pd.read_excel('/Users/zhengkeying/agent teams作业/APP广告位明细3月汇总.xlsx'),
        '2026-04': pd.read_excel('/Users/zhengkeying/agent teams作业/4月广告位明细.xlsx'),
        '2026-05': pd.read_excel('/Users/zhengkeying/agent teams作业/5.1-17广告位明细.xlsx'),
    }
    df_mau = pd.read_excel('/Users/zhengkeying/agent teams作业/mau_data_3_4_5.xlsx')

# 过滤合计行
df_backend = df_backend[df_backend['stat_month'] != '合计'].copy()

# 数值转换（后链路）
df_backend['order_time'] = pd.to_datetime(df_backend['order_time'], errors='coerce')
for col in ['首单数', '首单流水', 'is_add_friend', '是否到课']:
    if col in df_backend.columns:
        df_backend[col] = pd.to_numeric(df_backend[col], errors='coerce')
for col in df_backend.columns:
    if '完课' in col or '到课' in col or col.startswith('是否第'):
        df_backend[col] = pd.to_numeric(df_backend[col], errors='coerce')

# 前端数据转换 + 映射资源位（对所有月份）
for month_key, ad in ad_data.items():
    # 兼容 Base 字段名（sku_price → 课程价格；category_name → 品类名称）
    if 'sku_price' in ad.columns and '课程价格' not in ad.columns:
        ad.rename(columns={'sku_price': '课程价格'}, inplace=True)
    if 'category_name' in ad.columns and '品类名称' not in ad.columns:
        ad.rename(columns={'category_name': '品类名称'}, inplace=True)
    for col in ['曝光uv', '点击uv', '售卖页浏览uv', '线索数', '首单订单数', '首单订单金额', '课程价格']:
        if col in ad.columns:
            ad[col] = pd.to_numeric(ad[col], errors='coerce')
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
# 3. MTD 数据切片（后链路）
# ============================================================
def filter_mtd(df, month_str, max_day):
    """筛选某月份 1号 ~ max_day 的数据"""
    sub = df[df['stat_month'] == month_str].copy()
    sub['day'] = sub['order_time'].dt.day
    return sub[sub['day'] <= max_day]

cur_mtd_backend = filter_mtd(df_backend, current_month, latest_day)
prev_mtd_backend = filter_mtd(df_backend, prev_month, latest_day)

# 后端线索数（用于目标差距）
backend_leads_cur = len(cur_mtd_backend)
backend_leads_prev = len(prev_mtd_backend)

# ============================================================
# 4. 前端 MTD 数据切片（按日期过滤）
# ============================================================
def filter_frontend_mtd(ad_df, max_day):
    """筛选前链路数据 1号 ~ max_day"""
    if ad_df.empty:
        return ad_df.copy()
    sub = ad_df.copy()
    sub['day'] = pd.to_datetime(sub['日期'], errors='coerce').dt.day
    return sub[sub['day'] <= max_day]

ad_cur_full = ad_data.get(current_month, pd.DataFrame())
ad_prev_full = ad_data.get(prev_month, pd.DataFrame())

cur_ad = filter_frontend_mtd(ad_cur_full, latest_day)
prev_ad = filter_frontend_mtd(ad_prev_full, latest_day)

# ============================================================
# 5. 核心指标计算（前链路漏斗）
# ============================================================
def calc_frontend_metrics(ad_df):
    """基于前链路数据计算漏斗指标"""
    leads = int(ad_df['线索数'].sum()) if '线索数' in ad_df.columns else 0
    exposure = int(ad_df['曝光uv'].sum()) if '曝光uv' in ad_df.columns else 0
    click = int(ad_df['点击uv'].sum()) if '点击uv' in ad_df.columns else 0
    browse = int(ad_df['售卖页浏览uv'].sum()) if '售卖页浏览uv' in ad_df.columns else 0

    ctr = round(click / exposure * 100, 2) if exposure > 0 else 0
    lead_rate = round(leads / exposure * 100, 2) if exposure > 0 else 0
    browse_rate = round(browse / click * 100, 2) if click > 0 else 0

    return {
        'leads': leads,
        'exposure': exposure,
        'click': click,
        'browse': browse,
        'ctr': ctr,
        'lead_rate': lead_rate,
        'browse_rate': browse_rate,
    }

cur_front = calc_frontend_metrics(cur_ad)
prev_front = calc_frontend_metrics(prev_ad)

# ============================================================
# 6. 月活数据计算
# ============================================================
# 兼容 Base 字段名（月份 → 数据月份；月活人数 → 月活人数）
if '月份' in df_mau.columns and '数据月份' not in df_mau.columns:
    df_mau.rename(columns={'月份': '数据月份'}, inplace=True)
if '月活人数' in df_mau.columns:
    df_mau['月活人数'] = pd.to_numeric(df_mau['月活人数'], errors='coerce')

mau_by_month = {}
for month in df_mau['数据月份'].unique():
    sub = df_mau[df_mau['数据月份'] == month]
    mau_by_month[str(month)] = int(sub['月活人数'].sum())

cur_mau = mau_by_month.get(current_month, 0)
prev_mau = mau_by_month.get(prev_month, 0)
cur_front['mau'] = cur_mau
prev_front['mau'] = prev_mau

# ============================================================
# 7. 目标差距（基于后链路总线索数）
# ============================================================
goal = GOALS.get(current_month, GOALS.get('2026-05', {'leads': 0}))
cur_front['leads_backend'] = backend_leads_cur
prev_front['leads_backend'] = backend_leads_prev
cur_front['leads_gap'] = goal['leads'] - backend_leads_cur
cur_front['leads_goal'] = goal['leads']

# ============================================================
# 7. 资源位归因（前链路数据）
# ============================================================
def resource_frontend_attribution(ad_df):
    """基于前链路数据按资源位聚合"""
    res = []
    for r in TARGET_RESOURCES:
        a = ad_df[ad_df['resource'] == r] if 'resource' in ad_df.columns else pd.DataFrame()
        leads = int(a['线索数'].sum()) if '线索数' in a.columns else 0
        exposure = int(a['曝光uv'].sum()) if '曝光uv' in a.columns else 0
        click = int(a['点击uv'].sum()) if '点击uv' in a.columns else 0
        ctr = round(click / exposure * 100, 2) if exposure > 0 else 0
        lead_rate = round(leads / exposure * 100, 2) if exposure > 0 else 0
        res.append({
            'resource': r,
            'leads': leads,
            'exposure': exposure,
            'click': click,
            'ctr': ctr,
            'lead_rate': lead_rate,
        })
    return pd.DataFrame(res)

cur_res = resource_frontend_attribution(cur_ad)
prev_res = resource_frontend_attribution(prev_ad)

res_merged = pd.merge(cur_res, prev_res, on='resource', suffixes=('_cur', '_prev'), how='outer').fillna(0)
res_merged['leads_change'] = res_merged['leads_cur'] - res_merged['leads_prev']
res_merged['leads_mom'] = round(res_merged['leads_change'] / res_merged['leads_prev'] * 100, 2).replace([float('inf'), -float('inf')], 0).fillna(0)
res_merged['ctr_change'] = round(res_merged['ctr_cur'] - res_merged['ctr_prev'], 2)
res_merged['lead_rate_change'] = round(res_merged['lead_rate_cur'] - res_merged['lead_rate_prev'], 2)

res_merged['impact'] = res_merged['leads_change'].abs()
res_merged = res_merged.sort_values('impact', ascending=False)

def build_mover_dict(row):
    return {
        'resource': row['resource'],
        'leads_cur': int(row['leads_cur']),
        'leads_prev': int(row['leads_prev']),
        'leads_change': int(row['leads_change']),
        'leads_mom': float(row['leads_mom']),
        'exposure_cur': int(row['exposure_cur']),
        'exposure_prev': int(row['exposure_prev']),
        'click_cur': int(row['click_cur']),
        'click_prev': int(row['click_prev']),
        'ctr_cur': float(row['ctr_cur']),
        'ctr_prev': float(row['ctr_prev']),
        'lead_rate_cur': float(row['lead_rate_cur']),
        'lead_rate_prev': float(row['lead_rate_prev']),
    }

top_movers = [build_mover_dict(row) for _, row in res_merged.head(5).iterrows()]

gainers = res_merged[res_merged['leads_change'] > 0].sort_values('leads_change', ascending=False)
losers = res_merged[res_merged['leads_change'] < 0].sort_values('leads_change', ascending=True)

top_gainers = [build_mover_dict(row) for _, row in gainers.head(3).iterrows()]
top_losers = [build_mover_dict(row) for _, row in losers.head(3).iterrows()]

# ============================================================
# 8. 品类归因（前链路数据）
# ============================================================
top_resource = top_movers[0]['resource'] if top_movers else None

category_breakdown = []
if top_resource:
    for month, ad_df in [('cur', cur_ad), ('prev', prev_ad)]:
        sub = ad_df[(ad_df['resource'] == top_resource) & (ad_df['品类名称'].notna())]
        if sub.empty:
            continue
        cat_agg = sub.groupby('品类名称').agg({
            '线索数': 'sum',
            '曝光uv': 'sum',
            '点击uv': 'sum',
        }).reset_index()
        cat_agg = cat_agg.sort_values('线索数', ascending=False).head(5)
        for _, row in cat_agg.iterrows():
            exposure = int(row['曝光uv'])
            click = int(row['点击uv'])
            leads = int(row['线索数'])
            category_breakdown.append({
                'month': month,
                'resource': top_resource,
                'category': row['品类名称'],
                'leads': leads,
                'exposure': exposure,
                'click': click,
                'ctr': round(click / exposure * 100, 2) if exposure > 0 else 0,
                'lead_rate': round(leads / exposure * 100, 2) if exposure > 0 else 0,
            })

# 品类全量对比（用于上升/下降 Top5）
category_movers = []
if not cur_ad.empty and not prev_ad.empty:
    cur_cat_all = cur_ad[cur_ad['品类名称'].notna()].groupby('品类名称')['线索数'].sum().reset_index()
    prev_cat_all = prev_ad[prev_ad['品类名称'].notna()].groupby('品类名称')['线索数'].sum().reset_index()
    cat_merged = pd.merge(cur_cat_all, prev_cat_all, on='品类名称', how='outer', suffixes=('_cur', '_prev')).fillna(0)
    cat_merged['leads_change'] = cat_merged['线索数_cur'] - cat_merged['线索数_prev']
    cat_merged['leads_mom'] = cat_merged.apply(lambda r: round(r['leads_change'] / r['线索数_prev'] * 100, 2) if r['线索数_prev'] > 0 else 0, axis=1)
    cat_gainers = cat_merged[cat_merged['leads_change'] > 0].sort_values('leads_change', ascending=False).head(5)
    cat_losers = cat_merged[cat_merged['leads_change'] < 0].sort_values('leads_change', ascending=True).head(5)
    for _, row in cat_gainers.iterrows():
        category_movers.append({'category': row['品类名称'], 'leads_cur': int(row['线索数_cur']), 'leads_prev': int(row['线索数_prev']), 'leads_change': int(row['leads_change']), 'leads_mom': float(row['leads_mom']), 'direction': 'up'})
    for _, row in cat_losers.iterrows():
        category_movers.append({'category': row['品类名称'], 'leads_cur': int(row['线索数_cur']), 'leads_prev': int(row['线索数_prev']), 'leads_change': int(row['leads_change']), 'leads_mom': float(row['leads_mom']), 'direction': 'down'})

# ============================================================
# 9. 价格带归因（前链路数据）
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
    for month, ad_df in [('cur', cur_ad), ('prev', prev_ad)]:
        sub = ad_df[ad_df['resource'] == top_resource].copy()
        if sub.empty:
            continue
        sub['price_band'] = pd.to_numeric(sub['课程价格'], errors='coerce').apply(map_price_band)
        pb_agg = sub.groupby('price_band').agg({'线索数': 'sum', '曝光uv': 'sum'}).reset_index()
        pb_agg = pb_agg.sort_values('线索数', ascending=False)
        for _, row in pb_agg.iterrows():
            price_band_breakdown.append({
                'month': month,
                'resource': top_resource,
                'price_band': row['price_band'],
                'leads': int(row['线索数']),
                'exposure': int(row['曝光uv']),
            })

# ============================================================
# 10. 日度线索趋势（后端，按日期聚合）
# ============================================================
df_backend['day'] = df_backend['order_time'].dt.day
daily_trends = {}
for month in ['2026-03', '2026-04', '2026-05']:
    sub = df_backend[df_backend['stat_month'] == month]
    daily = sub.groupby('day').size().reset_index(name='leads')
    daily = daily.sort_values('day')
    daily_trends[month] = [{'day': int(row['day']), 'leads': int(row['leads'])} for _, row in daily.iterrows()]

# ============================================================
# 11. 日活数据读取与线索生成率计算
# ============================================================
df_dau = pd.read_excel('/Users/zhengkeying/agent teams作业/日维度日活3-5月.xlsx')
df_dau['日期'] = pd.to_datetime(df_dau['日期'], errors='coerce')
df_dau['month'] = df_dau['日期'].dt.strftime('%Y-%m')
df_dau['day'] = df_dau['日期'].dt.day

daily_dau = {}
daily_lead_gen_rate = {}
for month in ['2026-03', '2026-04', '2026-05']:
    dau_sub = df_dau[df_dau['month'] == month].sort_values('day')
    dau_list = [{'day': int(row['day']), 'dau': int(row['日活人数'])} for _, row in dau_sub.iterrows()]
    daily_dau[month] = dau_list

    # 线索生成率 = 线索数 / 日活
    leads_map = {d['day']: d['leads'] for d in daily_trends.get(month, [])}
    rate_list = []
    for d in dau_list:
        day = d['day']
        dau_val = d['dau']
        leads_val = leads_map.get(day, 0)
        rate = round(leads_val / dau_val * 100, 3) if dau_val > 0 else 0
        rate_list.append({'day': day, 'rate': rate, 'leads': leads_val, 'dau': dau_val})
    daily_lead_gen_rate[month] = rate_list

# ============================================================
# 12. 组装输出
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
        'current': cur_front,
        'previous': prev_front,
        'mom': {
            'leads': round((backend_leads_cur - backend_leads_prev) / backend_leads_prev * 100, 2) if backend_leads_prev else 0,
            'exposure': round((cur_front['exposure'] - prev_front['exposure']) / prev_front['exposure'] * 100, 2) if prev_front['exposure'] else 0,
            'click': round((cur_front['click'] - prev_front['click']) / prev_front['click'] * 100, 2) if prev_front['click'] else 0,
            'ctr': round(cur_front['ctr'] - prev_front['ctr'], 2),
            'lead_rate': round(cur_front['lead_rate'] - prev_front['lead_rate'], 2),
            'browse_rate': round(cur_front['browse_rate'] - prev_front['browse_rate'], 2),
            'mau': round((cur_mau - prev_mau) / prev_mau * 100, 2) if prev_mau else 0,
        },
    },
    'resource_movers': top_movers,
    'top_gainers': top_gainers,
    'top_losers': top_losers,
    'category_breakdown': category_breakdown,
    'category_movers': category_movers,
    'price_band_breakdown': price_band_breakdown,
    'resource_efficiency_trends': res_merged[['resource', 'ctr_cur', 'ctr_prev', 'ctr_change', 'lead_rate_cur', 'lead_rate_prev', 'lead_rate_change']].to_dict('records'),
    'all_resources': res_merged[['resource', 'leads_cur', 'leads_prev', 'leads_change', 'leads_mom', 'exposure_cur', 'exposure_prev', 'ctr_cur', 'ctr_prev', 'lead_rate_cur', 'lead_rate_prev']].to_dict('records'),
    'daily_trends': daily_trends,
    'daily_dau': daily_dau,
    'daily_lead_gen_rate': daily_lead_gen_rate,
}

out_path = '/Users/zhengkeying/agent teams作业/weekly_report_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'周报数据已生成: {out_path}')
print(f'当前MTD线索数(后端): {backend_leads_cur}，上月同期: {backend_leads_prev}，环比: {output["summary"]["mom"]["leads"]}%')
print(f'当前MTD线索数(前端): {cur_front["leads"]}，上月同期: {prev_front["leads"]}')
print(f'当前MTD曝光UV: {cur_front["exposure"]}，点击UV: {cur_front["click"]}，CTR: {cur_front["ctr"]}%')
print(f'线索生成率: {cur_front["lead_rate"]}%，上月同期: {prev_front["lead_rate"]}%')
print(f'目标线索: {goal["leads"]}，差距: {cur_front["leads_gap"]}')
if top_movers:
    print(f'影响最大资源位: {top_movers[0]["resource"]}，线索变化: {top_movers[0]["leads_change"]}')
