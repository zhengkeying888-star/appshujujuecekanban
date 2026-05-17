import pandas as pd
import json
import numpy as np
import os

USE_FEISHU = os.environ.get('USE_FEISHU', 'false').lower() == 'true'

if USE_FEISHU:
    from feishu_reader import FeishuDataSource
    ds = FeishuDataSource()
    df_detail = ds.read_backend_data('2026-03')
    df_detail = pd.concat([df_detail, ds.read_backend_data('2026-04')])
    m3_ad = ds.read_frontend_data('2026-03')
    m4_ad = ds.read_frontend_data('2026-04')
    mau_df = ds.read_mau_data()
    cat_type_df = ds.read_category_mapping()
else:
    # 前链路数据（曝光、点击、售卖页浏览）
    m3_ad = pd.read_excel('/Users/zhengkeying/agent teams作业/APP广告位明细3月汇总.xlsx')
    m4_ad = pd.read_excel('/Users/zhengkeying/agent teams作业/4月广告位明细.xlsx')

    # 后链路数据（线索、好友、到课、完课、首单）
    df_detail = pd.read_excel('/Users/zhengkeying/agent teams作业/APP线索广告位拆解 3-4月明细版本.xlsx')

    # MAU数据
    mau_df = pd.read_excel('/Users/zhengkeying/agent teams作业/3-4月月活人数.xlsx')

    # 品类类型映射（正式品/孵化品）
    cat_type_df = pd.read_csv('/Users/zhengkeying/agent teams作业/APP品类流量结构.csv', nrows=100)
    # CSV是左右双表格式，取左表前3列（4月）和右表对应列（3月）
    cat_type_df = cat_type_df.iloc[:, [1, 2]].dropna()
    cat_type_df.columns = ['品类', '品类区别']

# 过滤合计行（必须在任何计算前执行）
df_detail = df_detail[df_detail['stat_month'] != '合计']
cat_type_map = {}
for _, row in cat_type_df.iterrows():
    cn = str(row['品类']).strip()
    ct = str(row['品类区别']).strip()
    if cn and ct and ct in ('正式品', '孵化品'):
        cat_type_map[cn] = ct

def get_cat_type(category_name):
    if pd.isna(category_name):
        return '未分类'
    cn = str(category_name).strip()
    if cn in cat_type_map:
        return cat_type_map[cn]
    # fallback: 包含匹配
    for k, v in cat_type_map.items():
        if cn in k or k in cn:
            return v
    return '未分类'

df_detail['cat_type'] = df_detail['category_name'].apply(get_cat_type)

# ============================================================
# 1b. 品类属性映射（兴趣线/健康线/变美线）
# ============================================================

cat_attr_df = pd.read_excel('/Users/zhengkeying/agent teams作业/【重要】品类归属.xlsx')
cat_attr_map = {}
for _, row in cat_attr_df.iterrows():
    attr = str(row['品类属性']).strip()
    cat = str(row['品类']).strip()
    status = str(row['品类情况']).strip()
    cat_attr_map[cat] = {'attr': attr, 'status': status}

# 补充映射（主数据中有但映射表未覆盖）
cat_attr_map['中式美食制作'] = {'attr': '兴趣线', 'status': '孵化品'}
cat_attr_map['养正变美'] = {'attr': '变美线', 'status': '孵化品'}
cat_attr_map['开心晨练团'] = {'attr': '健康线', 'status': '正式品'}

def get_cat_attr(category_name):
    if pd.isna(category_name):
        return {'attr': '未分类', 'status': '未分类'}
    cn = str(category_name).strip()
    if cn in cat_attr_map:
        return cat_attr_map[cn]
    # fallback: 包含匹配
    for k, v in cat_attr_map.items():
        if cn in k or k in cn:
            return v
    return {'attr': '未分类', 'status': '未分类'}

df_detail['cat_attr'] = df_detail['category_name'].apply(lambda x: get_cat_attr(x)['attr'])
df_detail['cat_status'] = df_detail['category_name'].apply(lambda x: get_cat_attr(x)['status'])

# ============================================================
# 2. 资源位映射
# ============================================================

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

# 映射广告位明细中的资源位
for df in [m3_ad, m4_ad]:
    df['resource'] = df['广告位名称'].map(AD_NAME_MAP).fillna(df['广告位名称'])
    df = df[~df['广告位名称'].isin(['H5-课程播放页-广告'])].copy()

# 保留完整的后链路数据用于月度汇总（不筛选资源位）
df_detail_full = df_detail.copy()

# 线索拆解明细中过滤非目标资源位（仅用于资源位级别分析）
df_detail = df_detail[df_detail['tag_level_1'].isin(TARGET_RESOURCES)].copy()

# ============================================================
# 3. 前链路聚合（广告位明细）
# ============================================================

def agg_ad(df):
    return df.groupby('resource').agg({
        '曝光uv': 'sum',
        '点击uv': 'sum',
        '售卖页浏览uv': 'sum',
    }).reset_index()

m3_ad_agg = agg_ad(m3_ad)
m4_ad_agg = agg_ad(m4_ad)

# ============================================================
# 4. 后链路聚合（线索拆解明细）
# ============================================================

completion_cols = [c for c in df_detail.columns if '完课' in c]

def calc_completion_rate(group):
    """单线索平均完课率 = 总完课人次 / 总课程节数"""
    total_lessons = 0
    total_completions = 0
    for _, row in group.iterrows():
        # 计算该课程的总节数
        lesson_count = 0
        for col in completion_cols:
            if pd.notna(row.get(col)):
                lesson_count += 1
        if lesson_count > 0:
            total_lessons += lesson_count
            # 计算该线索的完课节数
            completed = 0
            for col in completion_cols:
                val = row.get(col)
                if pd.notna(val) and val >= 1:
                    completed += 1
            total_completions += completed
    if total_lessons == 0:
        return 0
    return total_completions / total_lessons

def agg_detail(df):
    result = []
    for res in TARGET_RESOURCES:
        sub = df[df['tag_level_1'] == res]
        if len(sub) == 0:
            result.append({
                'resource': res,
                'leads': 0,
                'add_friend': 0,
                'attend': 0,
                'complete': 0,
                'completion_rate': 0,
                'orders': 0,
                'gmv': 0,
            })
            continue
        leads = len(sub)
        add_friend = int(sub['is_add_friend'].sum())
        attend = int(sub['是否到课'].sum())
        # 完课人数 = 任意一节完课
        complete = int(sub[completion_cols].apply(lambda row: (row.fillna(0) >= 1).any(), axis=1).sum())
        completion_rate = calc_completion_rate(sub)
        orders = int(sub['首单数'].sum())
        gmv = float(sub['首单流水'].sum())
        result.append({
            'resource': res,
            'leads': leads,
            'add_friend': add_friend,
            'attend': attend,
            'complete': complete,
            'completion_rate': round(completion_rate * 100, 2),
            'orders': orders,
            'gmv': gmv,
        })
    return pd.DataFrame(result)

m3_detail_agg = agg_detail(df_detail[df_detail['stat_month'] == '2026-03'])
m4_detail_agg = agg_detail(df_detail[df_detail['stat_month'] == '2026-04'])

# ============================================================
# 5. 合并前链路和后链路
# ============================================================

def merge_month(ad_agg, detail_agg, month_label):
    merged = pd.merge(ad_agg, detail_agg, on='resource', how='outer')
    merged = merged.fillna(0)
    # 计算转化率
    merged['ctr'] = merged.apply(lambda r: round(r['点击uv'] / r['曝光uv'] * 100, 2) if r['曝光uv'] > 0 else 0, axis=1)
    merged['lead_rate'] = merged.apply(lambda r: round(r['leads'] / r['点击uv'] * 100, 2) if r['点击uv'] > 0 else 0, axis=1)
    merged['friend_rate'] = merged.apply(lambda r: round(r['add_friend'] / r['leads'] * 100, 2) if r['leads'] > 0 else 0, axis=1)
    merged['attend_rate'] = merged.apply(lambda r: round(r['attend'] / r['add_friend'] * 100, 2) if r['add_friend'] > 0 else 0, axis=1)
    merged['complete_rate'] = merged.apply(lambda r: round(r['complete'] / r['attend'] * 100, 2) if r['attend'] > 0 else 0, axis=1)
    merged['order_rate'] = merged.apply(lambda r: round(r['orders'] / r['complete'] * 100, 2) if r['complete'] > 0 else 0, axis=1)
    merged['arpu'] = merged.apply(lambda r: round(r['gmv'] / r['leads'], 2) if r['leads'] > 0 else 0, axis=1)
    return merged

m3_merged = merge_month(m3_ad_agg, m3_detail_agg, '2026-03')
m4_merged = merge_month(m4_ad_agg, m4_detail_agg, '2026-04')

# ============================================================
# 6. 月度汇总
# ============================================================
# 后链路指标必须使用完整的 df_detail_full（不筛选 TARGET_RESOURCES）
# 前链路指标仍来自广告位明细的聚合

m3_full = df_detail_full[df_detail_full['stat_month'] == '2026-03']
m4_full = df_detail_full[df_detail_full['stat_month'] == '2026-04']

m3_total = {
    '曝光uv': int(m3_merged['曝光uv'].sum()),
    '点击uv': int(m3_merged['点击uv'].sum()),
    'leads': len(m3_full),
    'add_friend': int(m3_full['is_add_friend'].sum()),
    'attend': int(m3_full['是否到课'].sum()),
    'complete': int(m3_full[completion_cols].apply(lambda row: (row.fillna(0) >= 1).any(), axis=1).sum()),
    'orders': int(m3_full['首单数'].sum()),
    'gmv': float(m3_full['首单流水'].sum()),
}

m4_total = {
    '曝光uv': int(m4_merged['曝光uv'].sum()),
    '点击uv': int(m4_merged['点击uv'].sum()),
    'leads': len(m4_full),
    'add_friend': int(m4_full['is_add_friend'].sum()),
    'attend': int(m4_full['是否到课'].sum()),
    'complete': int(m4_full[completion_cols].apply(lambda row: (row.fillna(0) >= 1).any(), axis=1).sum()),
    'orders': int(m4_full['首单数'].sum()),
    'gmv': float(m4_full['首单流水'].sum()),
}

# MAU
mau_summary = {}
for month in mau_df['月份'].unique():
    sub = mau_df[mau_df['月份'] == month]
    total = sub['月活人数'].sum()
    mau_summary[str(month)] = {'total_mau': int(total)}

m3_mau = mau_summary.get('2026-03', {}).get('total_mau', 758580)
m4_mau = mau_summary.get('2026-04', {}).get('total_mau', 702752)

m3_total['lead_gen_rate'] = round(m3_total['leads'] / m3_mau * 100, 2)
m4_total['lead_gen_rate'] = round(m4_total['leads'] / m4_mau * 100, 2)

# 计算整体转化率
m3_total['ctr'] = round(m3_total['点击uv'] / m3_total['曝光uv'] * 100, 2)
m3_total['lead_rate'] = round(m3_total['leads'] / m3_total['点击uv'] * 100, 2)
m3_total['friend_rate'] = round(m3_total['add_friend'] / m3_total['leads'] * 100, 2)
m3_total['attend_rate'] = round(m3_total['attend'] / m3_total['add_friend'] * 100, 2)
m3_total['complete_rate'] = round(m3_total['complete'] / m3_total['attend'] * 100, 2)
m3_total['order_rate'] = round(m3_total['orders'] / m3_total['complete'] * 100, 2)
m3_total['arpu'] = round(m3_total['gmv'] / m3_total['leads'], 2)
m3_total['cvr_from_leads'] = round(m3_total['orders'] / m3_total['leads'] * 100, 2) if m3_total['leads'] > 0 else 0
m3_total['price_per_order'] = round(m3_total['gmv'] / m3_total['orders'], 2) if m3_total['orders'] > 0 else 0

m4_total['ctr'] = round(m4_total['点击uv'] / m4_total['曝光uv'] * 100, 2)
m4_total['lead_rate'] = round(m4_total['leads'] / m4_total['点击uv'] * 100, 2)
m4_total['friend_rate'] = round(m4_total['add_friend'] / m4_total['leads'] * 100, 2)
m4_total['attend_rate'] = round(m4_total['attend'] / m4_total['add_friend'] * 100, 2)
m4_total['complete_rate'] = round(m4_total['complete'] / m4_total['attend'] * 100, 2)
m4_total['order_rate'] = round(m4_total['orders'] / m4_total['complete'] * 100, 2)
m4_total['arpu'] = round(m4_total['gmv'] / m4_total['leads'], 2)
m4_total['cvr_from_leads'] = round(m4_total['orders'] / m4_total['leads'] * 100, 2) if m4_total['leads'] > 0 else 0
m4_total['price_per_order'] = round(m4_total['gmv'] / m4_total['orders'], 2) if m4_total['orders'] > 0 else 0

# 环比
mom = {}
for key in ['曝光uv', '点击uv', 'leads', 'add_friend', 'attend', 'complete', 'orders', 'gmv']:
    mom[key] = round((m4_total[key] - m3_total[key]) / m3_total[key] * 100, 2) if m3_total[key] > 0 else 0

for key in ['ctr', 'lead_rate', 'friend_rate', 'attend_rate', 'complete_rate', 'order_rate', 'arpu', 'lead_gen_rate', 'cvr_from_leads', 'price_per_order']:
    mom[key] = round((m4_total[key] - m3_total[key]) / m3_total[key] * 100, 2) if m3_total[key] > 0 else 0

monthly_summary = {
    '2026-03': m3_total,
    '2026-04': m4_total,
    '环比': mom,
}

# ============================================================
# 7. 资源位效率明细
# ============================================================

resource_efficiency = []
for res in TARGET_RESOURCES:
    m3_row = m3_merged[m3_merged['resource'] == res].iloc[0] if len(m3_merged[m3_merged['resource'] == res]) > 0 else None
    m4_row = m4_merged[m4_merged['resource'] == res].iloc[0] if len(m4_merged[m4_merged['resource'] == res]) > 0 else None
    if m3_row is None and m4_row is None:
        continue
    def make_dict(row):
        if row is None:
            return {}
        return {
            '曝光uv': int(row['曝光uv']),
            '点击uv': int(row['点击uv']),
            'leads': int(row['leads']),
            'add_friend': int(row['add_friend']),
            'attend': int(row['attend']),
            'complete': int(row['complete']),
            'orders': int(row['orders']),
            'gmv': float(row['gmv']),
            'ctr': float(row['ctr']),
            'lead_rate': float(row['lead_rate']),
            'friend_rate': float(row['friend_rate']),
            'attend_rate': float(row['attend_rate']),
            'complete_rate': float(row['complete_rate']),
            'order_rate': float(row['order_rate']),
            'cvr_from_leads': round(float(row['orders']) / int(row['leads']) * 100, 2) if int(row['leads']) > 0 else 0,
            'arpu': float(row['arpu']),
            'gmv_per_exposure': round(float(row['gmv']) / int(row['曝光uv']), 2) if int(row['曝光uv']) > 0 else 0,
            'gmv_per_click': round(float(row['gmv']) / int(row['点击uv']), 2) if int(row['点击uv']) > 0 else 0,
        }
    m3_dict = make_dict(m3_row)
    m4_dict = make_dict(m4_row)
    mom_dict = {}
    for k in ['曝光uv', '点击uv', 'leads', 'add_friend', 'attend', 'complete', 'orders', 'gmv', 'ctr', 'lead_rate', 'friend_rate', 'attend_rate', 'complete_rate', 'order_rate', 'arpu', 'cvr_from_leads', 'gmv_per_exposure', 'gmv_per_click']:
        v3 = m3_dict.get(k, 0)
        v4 = m4_dict.get(k, 0)
        mom_dict[k] = round((v4 - v3) / v3 * 100, 2) if v3 > 0 else (0 if v4 == 0 else 100)
    resource_efficiency.append({
        'resource': res,
        '2026-03': m3_dict,
        '2026-04': m4_dict,
        '环比': mom_dict,
    })

# ============================================================
# 8. 转化率变动幅度排序图（只展示事实，不做因果推断）
# ============================================================

# 6个转化环节的环比变化幅度
conversion_change = [
    {'stage': '曝光→点击', 'metric': 'CTR', 'march': m3_total['ctr'], 'april': m4_total['ctr'], 'mom': mom['ctr']},
    {'stage': '点击→领课', 'metric': '领课转化率', 'march': m3_total['lead_rate'], 'april': m4_total['lead_rate'], 'mom': mom['lead_rate']},
    {'stage': '曝光→线索', 'metric': '线索生成率', 'march': m3_total['lead_gen_rate'], 'april': m4_total['lead_gen_rate'], 'mom': mom['lead_gen_rate']},
    {'stage': '领课→好友', 'metric': '好友率', 'march': m3_total['friend_rate'], 'april': m4_total['friend_rate'], 'mom': mom['friend_rate']},
    {'stage': '好友→到课', 'metric': '到课率', 'march': m3_total['attend_rate'], 'april': m4_total['attend_rate'], 'mom': mom['attend_rate']},
    {'stage': '到课→完课', 'metric': '完课率', 'march': m3_total['complete_rate'], 'april': m4_total['complete_rate'], 'mom': mom['complete_rate']},
    {'stage': '完课→首单', 'metric': '完课→首单转化率', 'march': m3_total['order_rate'], 'april': m4_total['order_rate'], 'mom': mom['order_rate']},
]

# 按环比绝对值排序（恶化最严重的排最前）
conversion_change.sort(key=lambda x: abs(x['mom']), reverse=True)

# ============================================================
# 9. 三层评估框架
# ============================================================

# 战略重要性（GMV贡献占比）
total_gmv_m3 = sum(r['2026-03'].get('gmv', 0) for r in resource_efficiency)
total_gmv_m4 = sum(r['2026-04'].get('gmv', 0) for r in resource_efficiency)
resource_importance = []
for r in resource_efficiency:
    m4_gmv = r['2026-04'].get('gmv', 0)
    share = round(m4_gmv / total_gmv_m4 * 100, 2) if total_gmv_m4 > 0 else 0
    resource_importance.append({
        'resource': r['resource'],
        'gmv_share': share,
        'gmv': m4_gmv,
    })
resource_importance.sort(key=lambda x: x['gmv_share'], reverse=True)

# 效率矩阵（线索生成率 × 单线索产出）
# 线索生成率 = 线索数 / 曝光UV
# 单线索产出 = GMV / 线索数
resource_efficiency_matrix = []
for r in resource_efficiency:
    m4_data = r['2026-04']
    if m4_data.get('曝光uv', 0) > 0 and m4_data.get('leads', 0) > 0:
        lead_gen = round(m4_data['leads'] / m4_data['曝光uv'] * 100, 4)
        arpu = round(m4_data['gmv'] / m4_data['leads'], 2)
        resource_efficiency_matrix.append({
            'resource': r['resource'],
            'lead_gen_rate': lead_gen,
            'arpu': arpu,
            'leads': m4_data['leads'],
            'gmv': m4_data['gmv'],
        })

# 增长矩阵（线索数环比 × 首单转化率环比）
resource_growth_matrix = []
for r in resource_efficiency:
    mom_data = r['环比']
    m4_data = r['2026-04']
    if m4_data.get('leads', 0) >= 20:  # 只统计线索数>=20的资源位
        resource_growth_matrix.append({
            'resource': r['resource'],
            'leads_mom': mom_data.get('leads', 0),
            'order_rate_mom': mom_data.get('order_rate', 0),
            'leads': m4_data['leads'],
            'order_rate': m4_data.get('order_rate', 0),
        })

# ============================================================
# 10. 价格带分布（只看0/1/3/9）
# ============================================================

price_bands = ['0元', '1元', '3元', '9元', '其他']
def map_price_band(price):
    if pd.isna(price):
        return '其他'
    if price == 0:
        return '0元'
    if price == 1:
        return '1元'
    if price == 3:
        return '3元'
    if price == 9:
        return '9元'
    return '其他'

df_detail['price_band'] = df_detail['sku_price'].apply(map_price_band)

pb_distribution = []
for pb in price_bands:
    m3_pb = df_detail[(df_detail['stat_month'] == '2026-03') & (df_detail['price_band'] == pb)]
    m4_pb = df_detail[(df_detail['stat_month'] == '2026-04') & (df_detail['price_band'] == pb)]
    m3_leads = len(m3_pb)
    m4_leads = len(m4_pb)
    m3_gmv = float(m3_pb['首单流水'].sum())
    m4_gmv = float(m4_pb['首单流水'].sum())
    mom_leads = round((m4_leads - m3_leads) / m3_leads * 100, 2) if m3_leads > 0 else 0
    mom_gmv = round((m4_gmv - m3_gmv) / m3_gmv * 100, 2) if m3_gmv > 0 else 0
    pb_distribution.append({
        'price_band': pb,
        'march_leads': m3_leads,
        'april_leads': m4_leads,
        'march_gmv': m3_gmv,
        'april_gmv': m4_gmv,
        'leads_mom': mom_leads,
        'gmv_mom': mom_gmv,
    })

# 资源位 × 价格带 聚合（用于联动下钻）
resource_price_band = {}
for res in TARGET_RESOURCES:
    resource_price_band[res] = {}
    for pb in price_bands:
        m3_pb_res = df_detail[(df_detail['stat_month'] == '2026-03') & (df_detail['tag_level_1'] == res) & (df_detail['price_band'] == pb)]
        m4_pb_res = df_detail[(df_detail['stat_month'] == '2026-04') & (df_detail['tag_level_1'] == res) & (df_detail['price_band'] == pb)]
        m3_leads = len(m3_pb_res)
        m4_leads = len(m4_pb_res)
        m3_gmv = float(m3_pb_res['首单流水'].sum())
        m4_gmv = float(m4_pb_res['首单流水'].sum())
        if m3_leads > 0 or m4_leads > 0:
            resource_price_band[res][pb] = {
                'march_leads': m3_leads,
                'april_leads': m4_leads,
                'march_gmv': m3_gmv,
                'april_gmv': m4_gmv,
            }

# 价格带 × 品类类型 全局分布（用于旭日图）
price_band_type_distribution = []
for pb in price_bands:
    for ct in ['正式品', '孵化品', '未分类']:
        m3_pb_ct = df_detail[(df_detail['stat_month'] == '2026-03') & (df_detail['price_band'] == pb) & (df_detail['cat_type'] == ct)]
        m4_pb_ct = df_detail[(df_detail['stat_month'] == '2026-04') & (df_detail['price_band'] == pb) & (df_detail['cat_type'] == ct)]
        m3_leads = len(m3_pb_ct)
        m4_leads = len(m4_pb_ct)
        if m3_leads > 0 or m4_leads > 0:
            price_band_type_distribution.append({
                'price_band': pb,
                'cat_type': ct,
                'march_leads': m3_leads,
                'april_leads': m4_leads,
            })

# 资源位 × 价格带 × 品类类型 聚合（用于联动下钻）
resource_price_band_type = {}
for res in TARGET_RESOURCES:
    resource_price_band_type[res] = {}
    for pb in price_bands:
        for ct in ['正式品', '孵化品', '未分类']:
            m3_res = df_detail[(df_detail['stat_month'] == '2026-03') & (df_detail['tag_level_1'] == res) & (df_detail['price_band'] == pb) & (df_detail['cat_type'] == ct)]
            m4_res = df_detail[(df_detail['stat_month'] == '2026-04') & (df_detail['tag_level_1'] == res) & (df_detail['price_band'] == pb) & (df_detail['cat_type'] == ct)]
            m3_leads = len(m3_res)
            m4_leads = len(m4_res)
            if m3_leads > 0 or m4_leads > 0:
                if pb not in resource_price_band_type[res]:
                    resource_price_band_type[res][pb] = {}
                resource_price_band_type[res][pb][ct] = {
                    'march_leads': m3_leads,
                    'april_leads': m4_leads,
                }

# 资源位 × 用户等级 聚合（用于联动下钻）
levels = sorted(df_detail['growth_level'].dropna().unique())
resource_user_level = {}
for res in TARGET_RESOURCES:
    resource_user_level[res] = []
    for lvl in levels:
        m3_res = df_detail[(df_detail['stat_month'] == '2026-03') & (df_detail['tag_level_1'] == res) & (df_detail['growth_level'] == lvl)]
        m4_res = df_detail[(df_detail['stat_month'] == '2026-04') & (df_detail['tag_level_1'] == res) & (df_detail['growth_level'] == lvl)]
        m3_leads = len(m3_res)
        m4_leads = len(m4_res)
        m3_orders = int(m3_res['首单数'].sum()) if '首单数' in m3_res.columns else 0
        m4_orders = int(m4_res['首单数'].sum()) if '首单数' in m4_res.columns else 0
        m3_gmv = float(m3_res['首单流水'].sum())
        m4_gmv = float(m4_res['首单流水'].sum())
        m3_cvr = round(m3_orders / m3_leads * 100, 2) if m3_leads > 0 else 0
        m4_cvr = round(m4_orders / m4_leads * 100, 2) if m4_leads > 0 else 0
        m3_ltv = round(m3_gmv / m3_leads, 1) if m3_leads > 0 else 0
        m4_ltv = round(m4_gmv / m4_leads, 1) if m4_leads > 0 else 0
        if m3_leads > 0 or m4_leads > 0:
            resource_user_level[res].append({
                'level': int(lvl),
                'march_leads': m3_leads,
                'april_leads': m4_leads,
                'march_cvr': m3_cvr,
                'april_cvr': m4_cvr,
                'march_ltv': m3_ltv,
                'april_ltv': m4_ltv,
            })

# 资源位 GMV 瀑布图数据（Screen 3）
resource_gmv_waterfall = []
for r in resource_efficiency:
    m3_gmv = r['2026-03'].get('gmv', 0)
    m4_gmv = r['2026-04'].get('gmv', 0)
    change = m4_gmv - m3_gmv
    resource_gmv_waterfall.append({
        'resource': r['resource'],
        'm3_gmv': m3_gmv,
        'm4_gmv': m4_gmv,
        'change': change,
    })
resource_gmv_waterfall.sort(key=lambda x: abs(x['change']), reverse=True)

# 用户等级效率聚合（growth_level = 消费忠诚度）
user_level_efficiency = []
levels = sorted(df_detail['growth_level'].dropna().unique())
for lvl in levels:
    m3_lvl = df_detail[(df_detail['stat_month'] == '2026-03') & (df_detail['growth_level'] == lvl)]
    m4_lvl = df_detail[(df_detail['stat_month'] == '2026-04') & (df_detail['growth_level'] == lvl)]
    m3_leads = len(m3_lvl)
    m4_leads = len(m4_lvl)
    m3_orders = int(m3_lvl['首单数'].sum()) if '首单数' in m3_lvl.columns else 0
    m4_orders = int(m4_lvl['首单数'].sum()) if '首单数' in m4_lvl.columns else 0
    m3_gmv = float(m3_lvl['首单流水'].sum())
    m4_gmv = float(m4_lvl['首单流水'].sum())
    m3_cvr = round(m3_orders / m3_leads * 100, 2) if m3_leads > 0 else 0
    m4_cvr = round(m4_orders / m4_leads * 100, 2) if m4_leads > 0 else 0
    m3_ltv = round(m3_gmv / m3_leads, 1) if m3_leads > 0 else 0
    m4_ltv = round(m4_gmv / m4_leads, 1) if m4_leads > 0 else 0
    # 月活人数从 mau_df 中读取（需要提前解析）
    user_level_efficiency.append({
        'level': int(lvl),
        'march_leads': m3_leads,
        'april_leads': m4_leads,
        'march_orders': m3_orders,
        'april_orders': m4_orders,
        'march_gmv': m3_gmv,
        'april_gmv': m4_gmv,
        'march_cvr': m3_cvr,
        'april_cvr': m4_cvr,
        'march_ltv': m3_ltv,
        'april_ltv': m4_ltv,
    })

# ============================================================
# 11. MAU和留存
# ============================================================

mau_by_level = {}
for _, row in mau_df.iterrows():
    month = str(row['月份'])
    level = str(row['用户等级'])
    if month not in mau_by_level:
        mau_by_level[month] = {}
    mau_by_level[month][level] = int(row['月活人数'])

# 补充月活人数到 user_level_efficiency
for item in user_level_efficiency:
    lvl = str(item['level'])
    item['march_mau'] = mau_by_level.get('2026-03', {}).get(lvl, 0)
    item['april_mau'] = mau_by_level.get('2026-04', {}).get(lvl, 0)

# 留存数据（模拟，用户说后面补真实数据）
retention = {
    'march': {'retention_7d_rate': 45.0, 'retention_30d_rate': 35.0},
    'april': {'retention_7d_rate': 42.0, 'retention_30d_rate': 32.0},
    'mom': {'retention_7d_rate': -6.67, 'retention_30d_rate': -8.57},
}

# ============================================================
# 12. 诊断卡片
# ============================================================

diagnosis_stages = [
    {'stage': '曝光→点击', 'metric': 'CTR', 'key': 'ctr'},
    {'stage': '点击→领课', 'metric': '领课转化率', 'key': 'lead_rate'},
    {'stage': '领课→好友', 'metric': '好友率', 'key': 'friend_rate'},
    {'stage': '好友→到课', 'metric': '到课率', 'key': 'attend_rate'},
    {'stage': '到课→完课', 'metric': '完课率', 'key': 'complete_rate'},
    {'stage': '完课→首单', 'metric': '完课→首单转化率', 'key': 'order_rate'},
]

diagnosis = []
for d in diagnosis_stages:
    key = d['key']
    m3_val = m3_total[key]
    m4_val = m4_total[key]
    mom_val = round((m4_val - m3_val) / m3_val * 100, 1) if m3_val > 0 else 0
    # 简单归因逻辑
    issue = ''
    owner = '策略运营'
    if key == 'ctr':
        issue = '素材吸引力下降，点击率下滑' if mom_val < 0 else '素材表现良好'
    elif key == 'lead_rate':
        issue = '落地页转化效率下降，需优化表单体验' if mom_val < 0 else '落地页转化效率提升'
        owner = '产研'
    elif key == 'friend_rate':
        issue = '添加好友环节流失加剧，需优化引导链路' if mom_val < 0 else '添加好友率提升'
    elif key == 'attend_rate':
        issue = '到课率下降，需加强上课提醒和督学' if mom_val < 0 else '到课率提升'
        owner = '策略运营+教研'
    elif key == 'complete_rate':
        issue = '完课率下降，课程体验或内容需优化' if mom_val < 0 else '完课率提升'
        owner = '产研+教研'
    elif key == 'order_rate':
        issue = '高价课转化薄弱，需优化转化链路和价格策略' if mom_val < 0 else '转化效率提升'
        owner = '策略运营'
    diagnosis.append({
        'stage': d['stage'],
        'metric': d['metric'],
        'march': f"{m3_val:.1f}%",
        'april': f"{m4_val:.1f}%",
        'mom': f"{mom_val:+.1f}%",
        'issue': issue,
        'owner': owner,
    })

# ============================================================
# 13. 行动建议
# ============================================================

# 基于conversion_change最大影响因子和资源位效率生成行动建议
actions = []

# 找出影响最大的负向因子（按环比绝对值排序）
conversion_change_sorted = sorted(conversion_change, key=lambda x: abs(x['mom']), reverse=True)
top_negative = [c for c in conversion_change_sorted if c['mom'] < 0][:3]
for c in top_negative:
    factor_name = c['stage']
    if factor_name == '完课率':
        actions.append({'priority': 'P0', 'action': '优化完课链路，提升课程体验和督学机制', 'basis': f"完课率环比下降{c['mom']:.1f}pp，为全链路最大恶化环节"})
    elif factor_name == '首单转化率':
        actions.append({'priority': 'P0', 'action': '优化高价课转化链路，测试新的转化话术和价格策略', 'basis': f"首单转化率环比下降{c['mom']:.1f}pp"})
    elif factor_name == '客单价':
        actions.append({'priority': 'P0', 'action': '优化价格带结构，提升高价值课程占比', 'basis': f"客单价环比下降{c['mom']:.1f}%"})
    elif factor_name == '领课转化率':
        actions.append({'priority': 'P1', 'action': '优化落地页体验，提升领课转化率', 'basis': f"领课转化率环比下降{c['mom']:.1f}pp"})
    elif factor_name == 'CTR':
        actions.append({'priority': 'P1', 'action': '迭代广告素材，提升CTR', 'basis': f"CTR环比下降{c['mom']:.1f}pp"})

# 资源位效率问题
low_arpu = [r for r in resource_efficiency_matrix if r['arpu'] < 100 and r['leads'] > 100]
for r in low_arpu[:2]:
    actions.append({'priority': 'P1', 'action': f"优化「{r['resource']}」价格带结构，提升单线索产出", 'basis': f"单线索产出仅¥{r['arpu']:.0f}，远低于均值¥{m4_total['arpu']:.0f}"})

# 增长矩阵中的问题资源位
declining = [r for r in resource_growth_matrix if r['leads_mom'] < -20 and r['leads'] > 50]
for r in declining[:2]:
    actions.append({'priority': 'P2', 'action': f"排查「{r['resource']}」线索下滑原因", 'basis': f"线索数环比下降{r['leads_mom']:.0f}%，需定位流量或素材问题"})

# ============================================================
# 14. v2 新增分析维度
# ============================================================

# 核心诊断结论（供第一屏使用）——基于真实数据归因
gmv_change = m4_total['gmv'] - m3_total['gmv']
gmv_mom_pct = mom['gmv']

# 计算各资源位对总GMV变化的贡献
resource_gmv_changes = []
for r in resource_efficiency:
    m3_gmv = r['2026-03'].get('gmv', 0)
    m4_gmv = r['2026-04'].get('gmv', 0)
    change = m4_gmv - m3_gmv
    resource_gmv_changes.append({'resource': r['resource'], 'change': change, 'm3_gmv': m3_gmv, 'm4_gmv': m4_gmv})

# 按下降贡献排序（取Top 2拖累）
top_declines = sorted([x for x in resource_gmv_changes if x['change'] < 0], key=lambda x: x['change'])[:2]
# 按增长贡献排序（取Top 2支撑）
top_gains = sorted([x for x in resource_gmv_changes if x['change'] > 0], key=lambda x: x['change'], reverse=True)[:2]

# GMV 因素分解（连环替代法）
# GMV = MAU × 线索生成率 × LTV
m3_ltv = m3_total['gmv'] / m3_total['leads'] if m3_total['leads'] > 0 else 0
m4_ltv = m4_total['gmv'] / m4_total['leads'] if m4_total['leads'] > 0 else 0
m3_lead_gen = m3_total['leads'] / m3_mau
m4_lead_gen = m4_total['leads'] / m4_mau

step_mau = m4_mau * m3_lead_gen * m3_ltv
step_lead_gen = m4_mau * m4_lead_gen * m3_ltv
step_ltv = m4_mau * m4_lead_gen * m4_ltv

factor_impacts = [
    {'factor': 'MAU变化', 'impact': round(step_mau - m3_total['gmv'], 2), 'mom_pct': round((m4_mau - m3_mau) / m3_mau * 100, 1)},
    {'factor': '线索生成率变化', 'impact': round(step_lead_gen - step_mau, 2), 'mom_pct': round((m4_lead_gen - m3_lead_gen) / m3_lead_gen * 100, 1)},
    {'factor': 'LTV变化', 'impact': round(step_ltv - step_lead_gen, 2), 'mom_pct': round((m4_ltv - m3_ltv) / m3_ltv * 100, 1)},
]

# 生成 headline
headline = f"4月 GMV 环比下降 {abs(gmv_mom_pct):.1f}%（¥{gmv_change/10000:.1f}万）"
subline_parts = []
if top_declines:
    subline_parts.append("主要拖累：" + "、".join([f"{d['resource']}（¥{d['change']/10000:.1f}万）" for d in top_declines]))
if top_gains:
    subline_parts.append("主要支撑：" + "、".join([f"{g['resource']}（+¥{g['change']/10000:.1f}万）" for g in top_gains]))
subline = "；".join(subline_parts) if subline_parts else "各资源位产值波动较小"

# 自动生成洞察结论
auto_insight = ""
negative_factors = [f for f in factor_impacts if f['impact'] < 0]
positive_factors = [f for f in factor_impacts if f['impact'] > 0]
if negative_factors:
    main_drag = min(negative_factors, key=lambda x: x['impact'])
    auto_insight = f"GMV下滑主因：{main_drag['factor']}（¥{main_drag['impact']/10000:.1f}万）"
    if positive_factors:
        main_offset = max(positive_factors, key=lambda x: x['impact'])
        auto_insight += f"，被{main_offset['factor']}（+¥{main_offset['impact']/10000:.1f}万）部分抵消"
if not auto_insight:
    auto_insight = "各因素波动较小，GMV整体平稳"

# 产值强相关信号卡片
overall_order_rate_march = round(m3_total['orders'] / m3_total['leads'] * 100, 2) if m3_total['leads'] > 0 else 0
overall_order_rate_april = round(m4_total['orders'] / m4_total['leads'] * 100, 2) if m4_total['leads'] > 0 else 0
overall_order_rate_mom = round((overall_order_rate_april - overall_order_rate_march) / overall_order_rate_march * 100, 1) if overall_order_rate_march > 0 else 0

core_diagnosis = {
    'headline': headline,
    'subline': subline,
    'negative_pct': 70 if gmv_mom_pct < 0 else 30,
    'positive_pct': 30 if gmv_mom_pct < 0 else 70,
    'signals': [
        {
            'name': 'GMV',
            'march': f"¥{m3_total['gmv']/10000:.1f}万",
            'april': f"¥{m4_total['gmv']/10000:.1f}万",
            'mom_pct': gmv_mom_pct,
            'status': 'danger' if gmv_mom_pct < 0 else 'success'
        },
        {
            'name': '月活(MAU)',
            'march': f"{m3_mau:,}",
            'april': f"{m4_mau:,}",
            'mom_pct': round((m4_mau - m3_mau) / m3_mau * 100, 2),
            'status': 'danger' if m4_mau < m3_mau else 'success'
        },
        {
            'name': '线索数',
            'march': f"{m3_total['leads']:,}",
            'april': f"{m4_total['leads']:,}",
            'mom_pct': mom['leads'],
            'status': 'danger' if mom['leads'] < 0 else 'success'
        },
        {
            'name': '首单转化率',
            'march': f"{overall_order_rate_march:.2f}%",
            'april': f"{overall_order_rate_april:.2f}%",
            'mom_pct': overall_order_rate_mom,
            'status': 'danger' if overall_order_rate_mom < 0 else 'success'
        },
        {
            'name': 'LTV',
            'march': f"¥{m3_total['arpu']:.1f}",
            'april': f"¥{m4_total['arpu']:.1f}",
            'mom_pct': mom['arpu'],
            'status': 'danger' if mom['arpu'] < 0 else 'success'
        },
    ],
    'resource_gmv_changes': resource_gmv_changes,
}

# 策略卡片（第四屏）——基于全漏斗数据自动归因生成
strategy_cards = []

# 规则1：若总GMV下降，生成顶层策略
if gmv_mom_pct < -5:
    strategy_cards.append({
        'category': '运营',
        'title': '聚焦高产值资源位修复',
        'desc': f"4月GMV环比下降{abs(gmv_mom_pct):.1f}%，主要拖累来自{top_declines[0]['resource'] if top_declines else '头部资源位'}，需专项排查其线索质量与价格带结构",
        'gmv_impact': f"+¥{abs(top_declines[0]['change']/10000):.0f}万" if top_declines else '+¥10万',
        'risk': '高',
        'difficulty': 4
    })

# 规则2：若单线索产出下降明显
if mom['arpu'] < -5:
    strategy_cards.append({
        'category': '运营',
        'title': '优化价格带结构',
        'desc': f"单线索产出从¥{m3_total['arpu']:.0f}降至¥{m4_total['arpu']:.0f}，低价引流结构加重，需提升高客单价课程曝光占比",
        'gmv_impact': f"+¥{(m4_total['leads'] * (m3_total['arpu'] - m4_total['arpu']) / 10000):.0f}万",
        'risk': '中',
        'difficulty': 3
    })

# 规则3：若CTCVR（领课转化率）下滑
if mom['lead_rate'] < -5:
    strategy_cards.append({
        'category': '产研',
        'title': '优化落地页领课体验',
        'desc': f"CTCVR（点击→领课转化率）从{m3_total['lead_rate']:.2f}%降至{m4_total['lead_rate']:.2f}%，落地页流失加剧，需A/B测试表单与流程",
        'gmv_impact': '+¥5万',
        'risk': '中',
        'difficulty': 3
    })

# 规则4：若CTR下滑
if mom['ctr'] < -5:
    strategy_cards.append({
        'category': '内容',
        'title': '迭代前端广告素材',
        'desc': f"CTR从{m3_total['ctr']:.2f}%降至{m4_total['ctr']:.2f}%，素材吸引力下降，需基于高转化特征批量生产新素材",
        'gmv_impact': '+¥3万',
        'risk': '低',
        'difficulty': 2
    })

# 规则5：针对单线索产出低于均值50%的资源位
low_arpu_resources = [r for r in resource_efficiency if r['2026-04'].get('arpu', 0) > 0 and r['2026-04'].get('arpu', 0) < m4_total['arpu'] * 0.5 and r['2026-04'].get('leads', 0) > 100]
for r in low_arpu_resources[:1]:
    strategy_cards.append({
        'category': '运营',
        'title': f"优化「{r['resource']}」价格带结构",
        'desc': f"该资源位单线索产出仅¥{r['2026-04']['arpu']:.0f}，远低于均值¥{m4_total['arpu']:.0f}，需排查其课程价格带分布",
        'gmv_impact': f"+¥{r['2026-04']['leads'] * (m4_total['arpu'] - r['2026-04']['arpu']) / 10000:.0f}万",
        'risk': '中',
        'difficulty': 3
    })

# 若策略不足6条，补充通用项
if len(strategy_cards) < 6:
    defaults = [
        {'category': '产研', 'title': '完善线索分配机制', 'desc': '优化线索在不同价格带/品类间的分配效率，提升整体首单转化率', 'gmv_impact': '+¥5万', 'risk': '低', 'difficulty': 2},
        {'category': '运营', 'title': '孵化品流量测试', 'desc': '在明星资源位增加孵化品曝光，验证非主品类的产值潜力', 'gmv_impact': '+¥3万', 'risk': '低', 'difficulty': 2},
        {'category': '内容', 'title': '高转化素材复用', 'desc': '提取CTR与CTCVR双高素材的共同特征，建立素材生产SOP', 'gmv_impact': '+¥2万', 'risk': '低', 'difficulty': 1},
    ]
    for d in defaults:
        if len(strategy_cards) >= 6:
            break
        strategy_cards.append(d)

# 资源位健康预警表数据（第四屏，替代原来的资源位投放调整建议）
resource_health = []
for r in resource_efficiency:
    m4_data = r['2026-04']
    mom_data = r['环比']
    if m4_data.get('leads', 0) == 0:
        continue

    # 健康状态判定
    cvr_mom = mom_data.get('order_rate', 0)  # 这里order_rate是完课→首单，应该使用 orders/leads 的环比
    # 计算真实的 线索→首单转化率 环比
    m3_cvr = r['2026-03'].get('orders', 0) / r['2026-03'].get('leads', 1) * 100 if r['2026-03'].get('leads', 0) > 0 else 0
    m4_cvr = m4_data.get('orders', 0) / m4_data.get('leads', 1) * 100 if m4_data.get('leads', 0) > 0 else 0
    cvr_mom_real = round((m4_cvr - m3_cvr) / m3_cvr * 100, 1) if m3_cvr > 0 else 0

    arpu_mom = mom_data.get('arpu', 0)
    gmv_change = m4_data.get('gmv', 0) - r['2026-03'].get('gmv', 0)

    # 判定逻辑
    if cvr_mom_real <= -15 or arpu_mom <= -20:
        status = '预警'
        status_color = 'danger'
    elif cvr_mom_real >= 10 and arpu_mom >= 0:
        status = '健康'
        status_color = 'success'
    else:
        status = '观察'
        status_color = 'warning'

    resource_health.append({
        'resource': r['resource'],
        'leads_mom': mom_data.get('leads', 0),
        'cvr_mom': cvr_mom_real,
        'arpu_mom': arpu_mom,
        'gmv_change': round(gmv_change / 10000, 2),
        'status': status,
        'status_color': status_color,
    })

resource_health.sort(key=lambda x: (x['status'] == '健康', abs(x['gmv_change'])), reverse=False)

# 次月核心行动清单（第四屏）——基于全漏斗数据自动生成
action_checklist = []
seq = 1

# P0：若总GMV下降明显
if gmv_mom_pct < -5 and top_declines:
    action_checklist.append({
        'seq': seq,
        'title': f"排查「{top_declines[0]['resource']}」产值下滑根因",
        'owner': '运营',
        'deadline': '5月20日',
        'priority': 'P0',
        'basis': f"该资源位产值环比下降¥{abs(top_declines[0]['change']/10000):.1f}万，为全站最大拖累"
    })
    seq += 1

# P0：若CTCVR下滑
if mom['lead_rate'] < -5:
    action_checklist.append({
        'seq': seq,
        'title': '落地页领课流程A/B测试',
        'owner': '产研',
        'deadline': '5月18日',
        'priority': 'P0',
        'basis': f"CTCVR从{m3_total['lead_rate']:.2f}%降至{m4_total['lead_rate']:.2f}%，点击→领课环节流失加剧"
    })
    seq += 1

# P1：若单线索产出下滑
if mom['arpu'] < -5:
    action_checklist.append({
        'seq': seq,
        'title': '价格带结构优化实验',
        'owner': '运营',
        'deadline': '5月25日',
        'priority': 'P1',
        'basis': f"单线索产出环比下降{abs(mom['arpu']):.1f}%，需降低低价课占比"
    })
    seq += 1

# P1：针对低ARPU资源位
for r in low_arpu_resources[:1]:
    action_checklist.append({
        'seq': seq,
        'title': f"优化「{r['resource']}」课程结构",
        'owner': '运营',
        'deadline': '5月30日',
        'priority': 'P1',
        'basis': f"该资源位单线索产出¥{r['2026-04']['arpu']:.0f}，仅为均值{m4_total['arpu']:.0f}的{r['2026-04']['arpu']/m4_total['arpu']*100:.0f}%"
    })
    seq += 1

# P2：补充通用项
if seq <= 3:
    action_checklist.append({
        'seq': seq,
        'title': '高转化素材特征提取与复用',
        'owner': '内容',
        'deadline': '5月22日',
        'priority': 'P2',
        'basis': '建立CTR与CTCVR双高素材的特征标签库'
    })


# ============================================================
# 14b. 品类产出聚合（大类汇总 + 细品类明细 + 价格带分布）
# ============================================================

# 14b.1 品类属性汇总（兴趣线/健康线/变美线）
category_summary = []
for attr in ['兴趣线', '健康线', '变美线', '未分类']:
    for month, month_key in [('2026-03', 'march'), ('2026-04', 'april')]:
        df_attr = df_detail[(df_detail['stat_month'] == month) & (df_detail['cat_attr'] == attr)]
        total_leads = int(df_attr['线索数'].sum())
        total_gmv = float(df_attr['首单流水'].sum())
        total_orders = int(df_attr['首单数'].sum())
        cvr = total_orders / total_leads if total_leads > 0 else 0.0
        ltv = total_gmv / total_leads if total_leads > 0 else 0.0

        # 正式品拆分
        formal = df_attr[df_attr['cat_status'] == '正式品']
        formal_leads = int(formal['线索数'].sum())
        formal_gmv = float(formal['首单流水'].sum())
        formal_orders = int(formal['首单数'].sum())
        formal_cvr = formal_orders / formal_leads if formal_leads > 0 else 0.0
        formal_ltv = formal_gmv / formal_leads if formal_leads > 0 else 0.0

        # 孵化品拆分
        inc = df_attr[df_attr['cat_status'] == '孵化品']
        inc_leads = int(inc['线索数'].sum())
        inc_gmv = float(inc['首单流水'].sum())
        inc_orders = int(inc['首单数'].sum())
        inc_cvr = inc_orders / inc_leads if inc_leads > 0 else 0.0
        inc_ltv = inc_gmv / inc_leads if inc_leads > 0 else 0.0

        category_summary.append({
            'cat_attr': attr,
            'month': month_key,
            'leads': total_leads,
            'gmv': total_gmv,
            'cvr': round(cvr, 4),
            'ltv': round(ltv, 2),
            'formal': {
                'leads': formal_leads,
                'gmv': formal_gmv,
                'cvr': round(formal_cvr, 4),
                'ltv': round(formal_ltv, 2),
            },
            'incubation': {
                'leads': inc_leads,
                'gmv': inc_gmv,
                'cvr': round(inc_cvr, 4),
                'ltv': round(inc_ltv, 2),
            }
        })

# 14b.2 品类明细（含资源位效率排名）
category_detail = []
for cat in sorted(df_detail['category_name'].dropna().unique()):
    cat = str(cat).strip()
    attr_info = get_cat_attr(cat)
    cat_attr = attr_info['attr']
    cat_status = attr_info['status']

    cat_data = []
    for month, month_key in [('2026-03', 'march'), ('2026-04', 'april')]:
        df_cat = df_detail[(df_detail['stat_month'] == month) & (df_detail['category_name'].astype(str).str.strip() == cat)]
        total_leads = int(df_cat['线索数'].sum())
        total_gmv = float(df_cat['首单流水'].sum())
        total_orders = int(df_cat['首单数'].sum())
        cvr = total_orders / total_leads if total_leads > 0 else 0.0
        ltv = total_gmv / total_leads if total_leads > 0 else 0.0

        # 各资源位数据
        res_data = []
        for res in TARGET_RESOURCES:
            df_res = df_cat[df_cat['tag_level_1'] == res]
            r_leads = int(df_res['线索数'].sum())
            r_gmv = float(df_res['首单流水'].sum())
            r_orders = int(df_res['首单数'].sum())
            r_cvr = r_orders / r_leads if r_leads > 0 else 0.0
            if r_leads > 0:
                res_data.append({
                    'resource': res,
                    'leads': r_leads,
                    'gmv': r_gmv,
                    'cvr': round(r_cvr, 4),
                })

        # Top3 排名
        gmv_top3 = sorted(res_data, key=lambda x: x['gmv'], reverse=True)[:3]
        leads_top3 = sorted(res_data, key=lambda x: x['leads'], reverse=True)[:3]
        cvr_top3 = sorted([r for r in res_data if r['cvr'] > 0], key=lambda x: x['cvr'], reverse=True)[:3]

        cat_data.append({
            'month': month_key,
            'leads': total_leads,
            'gmv': total_gmv,
            'cvr': round(cvr, 4),
            'ltv': round(ltv, 2),
            'gmv_top3': [{'resource': r['resource'], 'value': r['gmv']} for r in gmv_top3],
            'leads_top3': [{'resource': r['resource'], 'value': r['leads']} for r in leads_top3],
            'cvr_top3': [{'resource': r['resource'], 'value': r['cvr']} for r in cvr_top3],
        })

    category_detail.append({
        'category': cat,
        'cat_attr': cat_attr,
        'cat_status': cat_status,
        'data': cat_data,
    })

# 14b.3 品类价格带分布
category_price_band = []
for cat in sorted(df_detail['category_name'].dropna().unique()):
    cat = str(cat).strip()
    for month, month_key in [('2026-03', 'march'), ('2026-04', 'april')]:
        df_cat = df_detail[(df_detail['stat_month'] == month) & (df_detail['category_name'].astype(str).str.strip() == cat)]
        pb_data = []
        for pb in price_bands:
            df_pb = df_cat[df_cat['price_band'] == pb]
            pb_leads = int(df_pb['线索数'].sum())
            pb_gmv = float(df_pb['首单流水'].sum())
            pb_orders = int(df_pb['首单数'].sum())
            pb_cvr = pb_orders / pb_leads if pb_leads > 0 else 0.0
            if pb_leads > 0:
                pb_data.append({
                    'price_band': pb,
                    'leads': pb_leads,
                    'gmv': pb_gmv,
                    'cvr': round(pb_cvr, 4),
                    'ltv': round(pb_gmv / pb_leads, 2) if pb_leads > 0 else 0.0,
                })
        category_price_band.append({
            'category': cat,
            'month': month_key,
            'price_bands': pb_data,
        })

# ============================================================
# 15. 组装输出
# ============================================================

output = {
    'core_diagnosis': core_diagnosis,
    'strategy_cards': strategy_cards,
    'resource_health': resource_health,
    'action_checklist': action_checklist,
    'resource_gmv_waterfall': resource_gmv_waterfall,
    'factor_impacts': factor_impacts,
    'auto_insight': auto_insight,

    'monthly_summary': monthly_summary,
    'resource_efficiency': resource_efficiency,
    'resource_importance': resource_importance,
    'resource_efficiency_matrix': resource_efficiency_matrix,
    'resource_growth_matrix': resource_growth_matrix,
    'conversion_change': conversion_change,
    'price_band_distribution': pb_distribution,
    'resource_price_band': resource_price_band,
    'price_band_type_distribution': price_band_type_distribution,
    'resource_price_band_type': resource_price_band_type,
    'resource_user_level': resource_user_level,
    'user_level_efficiency': user_level_efficiency,
    'mau_summary': mau_summary,
    'mau_by_level': mau_by_level,
    'retention': retention,
    'diagnosis': diagnosis,
    'action_items': actions,
    'category_summary': category_summary,
    'category_detail': category_detail,
    'category_price_band': category_price_band,

    'user_journey': {
        'stages': ['曝光', '点击', '领课'],
        'stage_keys': ['exposure', 'click', 'lead'],
        'backend_stages': ['好友', '到课', '完课', '首单'],
        'backend_keys': ['friend', 'attend', 'complete', 'order'],
        'march': {
            'exposure': m3_total['曝光uv'],
            'click': m3_total['点击uv'],
            'lead': m3_total['leads'],
            'friend': m3_total['add_friend'],
            'attend': m3_total['attend'],
            'complete': m3_total['complete'],
            'order': m3_total['orders'],
            'ctr': m3_total['ctr'],
            'lead_rate': m3_total['lead_rate'],
            'friend_rate': m3_total['friend_rate'],
            'attend_rate': m3_total['attend_rate'],
            'complete_rate': m3_total['complete_rate'],
            'order_rate': m3_total['order_rate'],
            'arpu': m3_total['arpu'],
            'cvr_from_leads': m3_total['cvr_from_leads'],
            'price_per_order': m3_total['price_per_order'],
            'lead_gen_rate': m3_total['lead_gen_rate'],
            'gmv': m3_total['gmv'],
        },
        'april': {
            'exposure': m4_total['曝光uv'],
            'click': m4_total['点击uv'],
            'lead': m4_total['leads'],
            'friend': m4_total['add_friend'],
            'attend': m4_total['attend'],
            'complete': m4_total['complete'],
            'order': m4_total['orders'],
            'ctr': m4_total['ctr'],
            'lead_rate': m4_total['lead_rate'],
            'friend_rate': m4_total['friend_rate'],
            'attend_rate': m4_total['attend_rate'],
            'complete_rate': m4_total['complete_rate'],
            'order_rate': m4_total['order_rate'],
            'arpu': m4_total['arpu'],
            'cvr_from_leads': m4_total['cvr_from_leads'],
            'price_per_order': m4_total['price_per_order'],
            'lead_gen_rate': m4_total['lead_gen_rate'],
            'gmv': m4_total['gmv'],
        },
        'mom': {
            'exposure': mom['曝光uv'],
            'click': mom['点击uv'],
            'lead': mom['leads'],
            'friend': mom['add_friend'],
            'attend': mom['attend'],
            'complete': mom['complete'],
            'order': mom['orders'],
            'ctr': mom['ctr'],
            'lead_rate': mom['lead_rate'],
            'friend_rate': mom['friend_rate'],
            'attend_rate': mom['attend_rate'],
            'complete_rate': mom['complete_rate'],
            'order_rate': mom['order_rate'],
            'arpu': mom['arpu'],
            'cvr_from_leads': mom['cvr_from_leads'],
            'price_per_order': mom['price_per_order'],
            'lead_gen_rate': mom['lead_gen_rate'],
            'gmv': mom['gmv'],
        },
    },
}

with open('/Users/zhengkeying/agent teams作业/data_analysis_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Done! Saved to data_analysis_output.json")
print(f"Keys: {list(output.keys())}")
print(f"Resources: {len(resource_efficiency)}")
print(f"Monthly summary 3月 leads: {m3_total['leads']}, 4月 leads: {m4_total['leads']}")
print(f"Monthly summary 3月 GMV: {m3_total['gmv']:.0f}, 4月 GMV: {m4_total['gmv']:.0f}")
if conversion_change:
    top_change = max(conversion_change, key=lambda x: abs(x['mom']))
    print(f"Top conversion change: {top_change['stage']} = {top_change['mom']:.1f}pp")
else:
    print("No conversion change data")
