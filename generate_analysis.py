import pandas as pd
import json
import re
from collections import defaultdict

# 1. Read and clean main data
print("Reading Excel...")
df = pd.read_excel('/Users/zhengkeying/agent teams作业/APP线索广告位拆解3-4月.xlsx', sheet_name='APP线索广告位拆解')
print(f"Total rows: {len(df)}")

df = df[df['stat_month'] != '合计'].copy()
print(f"After filtering 合计: {len(df)}")

TARGET_RESOURCES = [
    '选课中心', '首页弹窗', '学习页', '学习中心', '学习中心弹窗',
    '2025首页卡片1', '2025首页卡片5', '2025首页卡片10',
    '2025首页banner', '2025课程banner', '热门推荐', '好课上新',
    '名师好课', '个人主页', '社区koc'
]

def price_band(price):
    if price == 0:
        return '0元'
    elif price == 1.1:
        return '1.1元'
    elif price == 3.9:
        return '3.9元'
    else:
        return '其他'

df['price_band'] = df['sku_price'].apply(price_band)

def extract_selling_point(text):
    if pd.isna(text):
        return None
    m = re.search(r'【(.+?)】', str(text))
    return m.group(1) if m else None

df['selling_point'] = df['广告位素材'].apply(extract_selling_point)

# 2. Monthly summary
print("Computing monthly summary...")
summary = {}
for month, group in df.groupby('stat_month'):
    leads = int(group['线索数'].sum())
    orders = int(group['首单数'].sum())
    gmv = float(group['首单流水'].sum())
    cvr = orders / leads if leads > 0 else 0
    ltv_avg = float(group['LTV'].mean()) if 'LTV' in group.columns else 0
    slots = group['广告资源位'].nunique()
    summary[month] = {
        '线索数': leads, '首单数': orders, '首单流水': round(gmv, 2),
        '转化率': round(cvr, 4), 'LTV均值': round(ltv_avg, 2), '资源位数量': slots
    }

mom = {}
m3 = summary.get('2026-03', {})
m4 = summary.get('2026-04', {})
for key in ['线索数', '首单数', '首单流水', '转化率', 'LTV均值']:
    v3 = m3.get(key, 0)
    v4 = m4.get(key, 0)
    pct = (v4 - v3) / v3 * 100 if v3 != 0 else 0
    mom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}

monthly_summary = {'2026-03': m3, '2026-04': m4, '环比': mom}

# 3. Resource efficiency
print("Computing resource efficiency...")
resource_efficiency = []
for res in TARGET_RESOURCES:
    r3 = df[(df['stat_month'] == '2026-03') & (df['广告资源位'] == res)]
    r4 = df[(df['stat_month'] == '2026-04') & (df['广告资源位'] == res)]

    def agg(g):
        leads = int(g['线索数'].sum())
        orders = int(g['首单数'].sum())
        gmv = float(g['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        ltv = float(g['LTV'].mean()) if len(g) > 0 and 'LTV' in g.columns else 0
        return {'线索数': leads, '首单数': orders, '首单流水': round(gmv, 2),
                '转化率': round(cvr, 4), 'LTV均值': round(ltv, 2)}

    a3 = agg(r3)
    a4 = agg(r4)
    rmom = {}
    for key in ['线索数', '首单数', '首单流水', '转化率']:
        v3 = a3[key]
        v4 = a4[key]
        pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
        rmom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}

    resource_efficiency.append({'resource': res, '2026-03': a3, '2026-04': a4, '环比': rmom})
resource_efficiency.sort(key=lambda x: x['2026-04']['线索数'], reverse=True)

# 3b. Resource health status (decline warning)
print("Computing resource health status...")
resource_health_status = []
for r in resource_efficiency:
    cvr_mom = r['环比']['转化率']['value']
    status = '预警' if cvr_mom <= -10 else '正常'
    resource_health_status.append({
        'resource': r['resource'],
        'cvr_mom': round(cvr_mom, 2),
        'status': status
    })

# 3c. Resource × price band matrix
print("Computing resource × price band matrix...")
resource_price_band_matrix = []
for res in TARGET_RESOURCES:
    for pb in ['0元', '1.1元', '3.9元', '其他']:
        row = {'resource': res, 'price_band': pb}
        for month in ['2026-03', '2026-04']:
            g = df[(df['广告资源位'] == res) & (df['price_band'] == pb) & (df['stat_month'] == month)]
            leads = int(g['线索数'].sum())
            orders = int(g['首单数'].sum())
            gmv = float(g['首单流水'].sum())
            cvr = orders / leads if leads > 0 else 0
            row[month] = {
                '线索数': leads,
                '首单数': orders,
                '首单流水': round(gmv, 2),
                '转化率': round(cvr, 4)
            }
        rmom = {}
        for key in ['线索数', '首单数', '首单流水', '转化率']:
            v3 = row['2026-03'][key]
            v4 = row['2026-04'][key]
            pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
            rmom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}
        row['环比'] = rmom
        resource_price_band_matrix.append(row)

# 3d. Resource × price band total (summary row)
resource_price_band_total = {}
for pb in ['0元', '1.1元', '3.9元', '其他']:
    resource_price_band_total[pb] = {}
    for month in ['2026-03', '2026-04']:
        g = df[(df['price_band'] == pb) & (df['stat_month'] == month)]
        leads = int(g['线索数'].sum())
        orders = int(g['首单数'].sum())
        gmv = float(g['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        resource_price_band_total[pb][month] = {
            '线索数': leads,
            '首单数': orders,
            '首单流水': round(gmv, 2),
            '转化率': round(cvr, 4)
        }
    rmom = {}
    for key in ['线索数', '首单数', '首单流水', '转化率']:
        v3 = resource_price_band_total[pb]['2026-03'][key]
        v4 = resource_price_band_total[pb]['2026-04'][key]
        pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
        rmom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}
    resource_price_band_total[pb]['环比'] = rmom

# 4. Selling point analysis
print("Computing selling point analysis...")
sp_data = {}
for month, group in df.groupby('stat_month'):
    sp_data[month] = {}
    for sp, g in group.groupby('selling_point'):
        if pd.isna(sp) or sp == '' or sp == 'None':
            continue
        leads = int(g['线索数'].sum())
        orders = int(g['首单数'].sum())
        gmv = float(g['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        count = len(g)
        sp_data[month][sp] = {'线索数': leads, '首单数': orders, '首单流水': round(gmv, 2),
                              '转化率': round(cvr, 4), 'count': count}

selling_point_analysis = []
all_sps = set(sp_data.get('2026-03', {}).keys()) | set(sp_data.get('2026-04', {}).keys())
for sp in all_sps:
    m3d = sp_data.get('2026-03', {}).get(sp, {'线索数': 0, '首单数': 0, '首单流水': 0, '转化率': 0, 'count': 0})
    m4d = sp_data.get('2026-04', {}).get(sp, {'线索数': 0, '首单数': 0, '首单流水': 0, '转化率': 0, 'count': 0})
    sp_mom = {}
    for key in ['线索数', '首单数', '首单流水', '转化率']:
        v3 = m3d[key]
        v4 = m4d[key]
        pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
        sp_mom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}

    if m3d['count'] == 0 and m4d['count'] > 0:
        status = '新出现'
    elif m3d['count'] > 0 and m4d['count'] == 0:
        status = '已下架'
    elif sp_mom['线索数']['value'] > 20:
        status = '增长'
    elif sp_mom['线索数']['value'] < -20:
        status = '衰退'
    else:
        status = '稳定'

    selling_point_analysis.append({
        'keyword': sp, '2026-03': m3d, '2026-04': m4d, '环比': sp_mom, 'status': status
    })
selling_point_analysis.sort(key=lambda x: x['2026-04']['线索数'], reverse=True)

# 5. Four-dim cross
print("Computing four-dim cross analysis...")
four_dim_cross = []
for (cat, price, aud, sp), g in df.groupby(['category_name', 'price_band', '面向人群', 'selling_point']):
    if pd.isna(sp) or sp == '' or sp == 'None':
        continue
    m3g = g[g['stat_month'] == '2026-03']
    m4g = g[g['stat_month'] == '2026-04']

    def agg2(gg):
        leads = int(gg['线索数'].sum())
        orders = int(gg['首单数'].sum())
        gmv = float(gg['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        return {'线索数': leads, '首单数': orders, '首单流水': round(gmv, 2), '转化率': round(cvr, 4)}

    a3 = agg2(m3g)
    a4 = agg2(m4g)
    fd_mom = {}
    for key in ['线索数', '首单数', '首单流水', '转化率']:
        v3 = a3[key]
        v4 = a4[key]
        pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
        fd_mom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}

    four_dim_cross.append({
        'category': cat, 'price': price, 'audience': aud, 'selling_point': sp,
        '2026-03': a3, '2026-04': a4, '环比': fd_mom
    })
four_dim_cross.sort(key=lambda x: x['2026-04']['线索数'], reverse=True)

# 6. Best audience
print("Computing best audience...")
best_audience = []
for (cat, price), g in df.groupby(['category_name', 'price_band']):
    best_cvr = 0
    best_aud = None
    best_leads = 0
    best_orders = 0
    for aud, gg in g.groupby('面向人群'):
        leads = int(gg['线索数'].sum())
        orders = int(gg['首单数'].sum())
        cvr = orders / leads if leads > 0 else 0
        if cvr > best_cvr and leads >= 50:
            best_cvr = cvr
            best_aud = aud
            best_leads = leads
            best_orders = orders
    if best_aud:
        best_audience.append({
            'category': cat, 'price': price, 'best_audience': best_aud,
            'cvr': round(best_cvr, 4), 'leads': best_leads, 'orders': best_orders
        })
best_audience.sort(key=lambda x: x['cvr'], reverse=True)

# 7. Category-price matrix
print("Computing category-price matrix...")
category_price_matrix = []
for (cat, price), g in df.groupby(['category_name', 'price_band']):
    leads = int(g['线索数'].sum())
    orders = int(g['首单数'].sum())
    gmv = float(g['首单流水'].sum())
    cvr = orders / leads if leads > 0 else 0
    category_price_matrix.append({
        'category': cat, 'price': price, '线索数': leads, '首单数': orders,
        '首单流水': round(gmv, 2), '转化率': round(cvr, 4)
    })
category_price_matrix.sort(key=lambda x: x['线索数'], reverse=True)

# 7b. Price band distribution
print("Computing price band distribution...")
pb_data = {}
for month, group in df.groupby('stat_month'):
    total = group['线索数'].sum()
    pb_data[month] = {}
    for pb, g in group.groupby('price_band'):
        leads = int(g['线索数'].sum())
        pb_data[month][pb] = {
            'leads': leads,
            'share': round(leads / total * 100, 2) if total > 0 else 0
        }

price_band_distribution = []
for pb in ['0元', '1.1元', '3.9元', '其他']:
    m3d = pb_data.get('2026-03', {}).get(pb, {'leads': 0, 'share': 0})
    m4d = pb_data.get('2026-04', {}).get(pb, {'leads': 0, 'share': 0})
    share_mom = m4d['share'] - m3d['share']
    price_band_distribution.append({
        'price_band': pb,
        'march': m3d,
        'april': m4d,
        'share_mom': round(share_mom, 2)
    })

# 8. Category traffic structure (from CSV)
print("Parsing category traffic CSV...")
cat_df = pd.read_csv('/Users/zhengkeying/agent teams作业/APP品类流量结构.csv')

# Parse April side
apr = cat_df.iloc[:, [0,1,2,3,4,5,6,7]].copy()
apr.columns = ['月份','品类','品类区别','例子数','首单数','转化率','首单流水','ltv']
apr = apr[apr['月份'] == '2026-04'].copy()
apr = apr[apr['品类'].notna() & (apr['品类'] != '合计')]

# Parse March side
mar = cat_df.iloc[:, [9,10,11,12,13,14,15,16]].copy()
mar.columns = ['月份','品类','品类区别','例子数','首单数','转化率','首单流水','ltv']
mar = mar[mar['月份'] == '2026-03'].copy()
mar = mar[mar['品类'].notna() & (mar['品类'] != '合计')]

def parse_num(x):
    if pd.isna(x):
        return 0
    if isinstance(x, str):
        x = x.replace(',', '').replace('%', '').replace('¥', '').strip()
        if x == '' or x == '#N/A':
            return 0
        try:
            return float(x)
        except:
            return 0
    return float(x)

def parse_cat_row(row):
    return {
        'category': str(row['品类']).strip(),
        'type': str(row['品类区别']).strip() if pd.notna(row['品类区别']) else '未知',
        'leads': int(parse_num(row['例子数'])),
        'orders': int(parse_num(row['首单数'])),
        'cvr': parse_num(row['转化率']) / 100 if isinstance(row['转化率'], str) and '%' in row['转化率'] else parse_num(row['转化率']),
        'gmv': parse_num(row['首单流水']),
        'ltv': parse_num(row['ltv'])
    }

apr_dict = {}
for _, row in apr.iterrows():
    r = parse_cat_row(row)
    apr_dict[r['category']] = r

mar_dict = {}
for _, row in mar.iterrows():
    r = parse_cat_row(row)
    mar_dict[r['category']] = r

category_traffic = []
all_cats = set(apr_dict.keys()) | set(mar_dict.keys())
for cat in all_cats:
    a = apr_dict.get(cat, {'category': cat, 'type': '未知', 'leads': 0, 'orders': 0, 'cvr': 0, 'gmv': 0, 'ltv': 0})
    m = mar_dict.get(cat, {'category': cat, 'type': '未知', 'leads': 0, 'orders': 0, 'cvr': 0, 'gmv': 0, 'ltv': 0})
    # Use type from whichever side has data, prefer April
    cat_type = a['type'] if a['type'] != '未知' else m['type']
    cvr_a = a['cvr']
    cvr_m = m['cvr']
    leads_a = a['leads']
    leads_m = m['leads']
    gmv_a = a['gmv']
    gmv_m = m['gmv']

    mom_leads = (leads_a - leads_m) / leads_m * 100 if leads_m != 0 else (0 if leads_a == 0 else 100)
    mom_gmv = (gmv_a - gmv_m) / gmv_m * 100 if gmv_m != 0 else (0 if gmv_a == 0 else 100)
    mom_cvr = (cvr_a - cvr_m) / cvr_m * 100 if cvr_m != 0 else 0

    category_traffic.append({
        'category': cat,
        'type': cat_type,
        'march': {'leads': leads_m, 'orders': m['orders'], 'cvr': round(cvr_m, 4), 'gmv': round(gmv_m, 2), 'ltv': round(m['ltv'], 2)},
        'april': {'leads': leads_a, 'orders': a['orders'], 'cvr': round(cvr_a, 4), 'gmv': round(gmv_a, 2), 'ltv': round(a['ltv'], 2)},
        'mom': {
            'leads': round(mom_leads, 2),
            'gmv': round(mom_gmv, 2),
            'cvr': round(mom_cvr, 2)
        }
    })

category_traffic.sort(key=lambda x: x['april']['leads'], reverse=True)

# 8b. Build cat_type mapping and assign to df
cat_type_map = {}
for _, row in apr.iterrows():
    cat_type_map[str(row['品类']).strip()] = str(row['品类区别']).strip() if pd.notna(row['品类区别']) else '未知'
for _, row in mar.iterrows():
    c = str(row['品类']).strip()
    if c not in cat_type_map:
        cat_type_map[c] = str(row['品类区别']).strip() if pd.notna(row['品类区别']) else '未知'

def get_cat_type(cat):
    if pd.isna(cat):
        return '未知'
    cat = str(cat).strip()
    if cat in cat_type_map:
        return cat_type_map[cat]
    for csv_cat, t in cat_type_map.items():
        if csv_cat in cat or cat in csv_cat:
            return t
    return '未分类'

df['cat_type'] = df['category_name'].apply(get_cat_type)

# 8c. Price band distribution by product type (正式品 vs 孵化品)
print("Computing price band distribution by type...")
price_band_type = {}
for month, group in df.groupby('stat_month'):
    price_band_type[month] = []
    for pb, g in group.groupby('price_band'):
        total = int(g['线索数'].sum())
        children = []
        for cat_type, gg in g.groupby('cat_type'):
            if cat_type in ['正式品', '孵化品']:
                leads = int(gg['线索数'].sum())
                children.append({'name': cat_type, 'value': leads})
        price_band_type[month].append({
            'name': pb,
            'value': total,
            'children': children
        })

# 9. Resource × Category analysis
print("Computing resource × category analysis...")
resource_category = []
for (res, cat), g in df.groupby(['广告资源位', 'category_name']):
    if res not in TARGET_RESOURCES:
        continue
    m3g = g[g['stat_month'] == '2026-03']
    m4g = g[g['stat_month'] == '2026-04']

    def agg_rc(gg):
        leads = int(gg['线索数'].sum())
        orders = int(gg['首单数'].sum())
        gmv = float(gg['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        return {'线索数': leads, '首单数': orders, '首单流水': round(gmv, 2), '转化率': round(cvr, 4)}

    a3 = agg_rc(m3g)
    a4 = agg_rc(m4g)
    rc_mom = {}
    for key in ['线索数', '首单数', '首单流水', '转化率']:
        v3 = a3[key]
        v4 = a4[key]
        pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
        rc_mom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}

    resource_category.append({
        'resource': res, 'category': cat,
        '2026-03': a3, '2026-04': a4, '环比': rc_mom
    })

# Compute composite scores (only for combos with April leads >= 20)
rc_for_score = [rc for rc in resource_category if rc['2026-04']['线索数'] >= 20]
if rc_for_score:
    max_leads = max(rc['2026-04']['线索数'] for rc in rc_for_score)
    max_gmv = max(rc['2026-04']['首单流水'] for rc in rc_for_score)
    max_cvr = max(rc['2026-04']['转化率'] for rc in rc_for_score)
    min_gmv = min(rc['2026-04']['首单流水'] for rc in rc_for_score)
    min_cvr = min(rc['2026-04']['转化率'] for rc in rc_for_score)
    min_leads = min(rc['2026-04']['线索数'] for rc in rc_for_score)
else:
    max_leads = max_gmv = max_cvr = min_gmv = min_cvr = min_leads = 1

def norm(val, min_v, max_v):
    if max_v == min_v:
        return 50
    return (val - min_v) / (max_v - min_v) * 100

for rc in resource_category:
    a4 = rc['2026-04']
    if a4['线索数'] >= 20:
        score = (norm(a4['转化率'], min_cvr, max_cvr) * 0.4 +
                 norm(a4['首单流水'], min_gmv, max_gmv) * 0.35 +
                 norm(a4['线索数'], min_leads, max_leads) * 0.25)
    else:
        score = 0
    rc['score'] = round(score, 2)

# Sort by score desc
resource_category.sort(key=lambda x: x['score'], reverse=True)

# Heatmap data: top 15 categories by total April leads
cat_totals = {}
for rc in resource_category:
    cat_totals[rc['category']] = cat_totals.get(rc['category'], 0) + rc['2026-04']['线索数']
top_cats = sorted(cat_totals.keys(), key=lambda c: cat_totals[c], reverse=True)[:15]

heatmap_data = []
heatmap_max = 0
for res in TARGET_RESOURCES:
    for cat in top_cats:
        rc = next((x for x in resource_category if x['resource'] == res and x['category'] == cat), None)
        if rc and rc['score'] > 0:
            heatmap_data.append({'resource': res, 'category': cat, 'score': rc['score']})
            if rc['score'] > heatmap_max:
                heatmap_max = rc['score']

# 10. Recommendations
print("Computing recommendations...")
resource_category_recommendations = []
for res in TARGET_RESOURCES:
    res_cats = [rc for rc in resource_category if rc['resource'] == res and rc['2026-04']['线索数'] >= 20]
    res_cats.sort(key=lambda x: x['score'], reverse=True)

    top3 = res_cats[:3]
    # Avoid = lowest score category with meaningful volume
    avoid = res_cats[-1] if len(res_cats) >= 4 else None

    avg_cvr = sum(rc['2026-04']['转化率'] for rc in res_cats) / len(res_cats) if res_cats else 0
    if avoid and avoid['2026-04']['转化率'] > avg_cvr * 0.7:
        # If the lowest score isn't significantly bad, pick one with CVR < 50% avg
        bad = [rc for rc in res_cats if rc['2026-04']['转化率'] < avg_cvr * 0.5]
        avoid = bad[-1] if bad else avoid

    resource_category_recommendations.append({
        'resource': res,
        'top3': [{'category': rc['category'], 'score': rc['score'], 'leads': rc['2026-04']['线索数'],
                  'cvr': rc['2026-04']['转化率'], 'gmv': rc['2026-04']['首单流水'],
                  'mom_leads': rc['环比']['线索数']['value']} for rc in top3],
        'avoid': {'category': avoid['category'], 'score': avoid['score'], 'leads': avoid['2026-04']['线索数'],
                  'cvr': avoid['2026-04']['转化率'], 'gmv': avoid['2026-04']['首单流水']} if avoid else None,
        'avg_cvr': round(avg_cvr, 4)
    })

# 10b. Resource × category type efficiency
print("Computing resource × category type efficiency...")

resource_type_efficiency = []
for res in TARGET_RESOURCES:
    rdf = df[df['广告资源位'] == res]
    res_total = int(rdf['线索数'].sum())
    if res_total == 0:
        continue

    row = {'resource': res, 'total_leads': res_total, 'types': {}}
    for cat_type in ['正式品', '孵化品', '未知', '未分类']:
        tg = rdf[rdf['cat_type'] == cat_type]
        leads = int(tg['线索数'].sum())
        orders = int(tg['首单数'].sum())
        gmv = float(tg['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        share = round(leads / res_total * 100, 2) if res_total > 0 else 0
        row['types'][cat_type] = {
            'leads': leads, 'orders': orders, '首单流水': round(gmv, 2),
            '转化率': round(cvr, 4), 'share': share
        }

    # Recommendation tag
    formal = row['types'].get('正式品', {})
    hatch = row['types'].get('孵化品', {})
    row['tag'] = ''
    if hatch.get('转化率', 0) > formal.get('转化率', 0) and hatch.get('share', 0) < 20 and hatch.get('leads', 0) >= 20:
        row['tag'] = '建议加推孵化品'
    elif formal.get('share', 0) > 90 and formal.get('转化率', 0) < 0.03 and formal.get('leads', 0) > 500:
        row['tag'] = '正式品效率偏低，需排查'

    resource_type_efficiency.append(row)
resource_type_efficiency.sort(key=lambda x: x['total_leads'], reverse=True)

# 11. Resource category detail (per-resource cards)
resource_category_detail = []
for res in TARGET_RESOURCES:
    res_cats = [rc for rc in resource_category if rc['resource'] == res]
    res_cats.sort(key=lambda x: x['score'], reverse=True)
    resource_category_detail.append({
        'resource': res,
        'categories': res_cats
    })

# 12. Action items
print("Generating action items...")
actions = []
for r in resource_efficiency:
    if r['环比']['线索数']['value'] < -30 and r['2026-03']['线索数'] > 500:
        res_name = r['resource']
        decline = r['环比']['线索数']['value']
        actions.append({
            'priority': 'P0',
            'action': '紧急排查「' + res_name + '」投放衰退原因',
            'basis': '4月线索' + str(r['2026-04']['线索数']) + '，环比下降' + str(round(decline, 1)) + '%，需立即复盘素材与人群定向'
        })

for sp in selling_point_analysis[:5]:
    if sp['status'] == '增长' or sp['status'] == '新出现':
        sp_name = sp['keyword']
        actions.append({
            'priority': 'P0',
            'action': '加大「' + sp_name + '」素材投放',
            'basis': '4月线索' + str(sp['2026-04']['线索数']) + '，转化率' + str(round(sp['2026-04']['转化率']*100, 1)) + '%，状态：' + sp['status']
        })

for ba in best_audience[:5]:
    cat_name = ba['category']
    price_name = ba['price']
    aud_name = ba['best_audience']
    cvr_pct = round(ba['cvr']*100, 1)
    actions.append({
        'priority': 'P1',
        'action': '在「' + cat_name + '|' + price_name + '」价格带加大对「' + aud_name + '」人群的投放',
        'basis': '该人群转化率' + str(cvr_pct) + '%，为同品类价格带最优'
    })

actions.append({
    'priority': 'P1',
    'action': '全月GMV下降29.1%，需优化高价值资源位转化漏斗',
    'basis': '首单数环比下降28.2%，首单流水环比下降29.1%，LTV均值下降26.8%'
})

for sp in selling_point_analysis:
    if sp['status'] == '新出现' and sp['2026-04']['线索数'] >= 100:
        sp_name = sp['keyword']
        actions.append({
            'priority': 'P2',
            'action': '测试新卖点「' + sp_name + '」扩量可行性',
            'basis': '4月新出现线索' + str(sp['2026-04']['线索数']) + '，需观察持续表现'
        })

for r in resource_efficiency:
    if r['2026-04']['线索数'] > 500 and r['2026-04']['转化率'] < 0.03:
        res_name = r['resource']
        cvr_pct = round(r['2026-04']['转化率']*100, 1)
        actions.append({
            'priority': 'P2',
            'action': '优化「' + res_name + '」转化链路',
            'basis': '线索量高(' + str(r['2026-04']['线索数']) + ')但转化率仅' + str(cvr_pct) + '%，存在浪费'
        })

# 13. Creative analysis
print("Computing creative analysis...")
creative_analysis = []
for sp in selling_point_analysis[:15]:
    creative_analysis.append({
        'keyword': sp['keyword'],
        'count': sp['2026-04']['count'] + sp['2026-03']['count'],
        'm3_leads': sp['2026-03']['线索数'],
        'm4_leads': sp['2026-04']['线索数'],
        'm3_cvr': sp['2026-03']['转化率'],
        'm4_cvr': sp['2026-04']['转化率'],
        'm3_gmv': sp['2026-03']['首单流水'],
        'm4_gmv': sp['2026-04']['首单流水'],
        'status': sp['status'],
        'mom_leads': sp['环比']['线索数']['value']
    })

# 14. Wordcloud
wordcloud = [{'name': sp['keyword'], 'value': sp['2026-04']['线索数'] + sp['2026-03']['线索数']} for sp in selling_point_analysis[:30]]

# 15. Trend data
print("Computing trend data...")
trend = {'march': [], 'april': []}
df['order_date'] = pd.to_datetime(df['order_time'], errors='coerce')
df['day_str'] = df['order_date'].dt.strftime('%m-%d')
for month_code, month_name in [('2026-03', 'march'), ('2026-04', 'april')]:
    mg = df[df['stat_month'] == month_code]
    daily = mg.groupby('day_str').agg({'线索数': 'sum', '首单流水': 'sum', '首单数': 'sum'}).reset_index()
    for _, row in daily.iterrows():
        trend[month_name].append({
            'date': row['day_str'],
            '线索数': int(row['线索数']),
            '首单流水': round(row['首单流水'] / 10000, 2),
            '首单数': int(row['首单数'])
        })
    trend[month_name].sort(key=lambda x: x['date'])

# 16. 3D analysis
print("Computing 3D analysis...")
threedim = []
for (cat, price, aud), g in df.groupby(['category_name', 'price_band', '面向人群']):
    m3g = g[g['stat_month'] == '2026-03']
    m4g = g[g['stat_month'] == '2026-04']

    def agg3(gg):
        leads = int(gg['线索数'].sum())
        orders = int(gg['首单数'].sum())
        gmv = float(gg['首单流水'].sum())
        cvr = orders / leads if leads > 0 else 0
        return {'线索数': leads, '首单数': orders, '首单流水': round(gmv, 2), '转化率': round(cvr, 4)}

    a3 = agg3(m3g)
    a4 = agg3(m4g)
    td_mom = {}
    for key in ['线索数', '首单数', '首单流水', '转化率']:
        v3 = a3[key]
        v4 = a4[key]
        pct = (v4 - v3) / v3 * 100 if v3 != 0 else (0 if v4 == 0 else 100)
        td_mom[key] = {'value': round(pct, 2), 'abs': round(v4 - v3, 2)}

    threedim.append({
        'category': cat, 'price': price, 'audience': aud,
        '2026-03': a3, '2026-04': a4, '环比': td_mom
    })
threedim.sort(key=lambda x: x['2026-04']['线索数'], reverse=True)

# Assemble output
output = {
    'monthly_summary': monthly_summary,
    'resource_efficiency': resource_efficiency,
    'selling_point_analysis': selling_point_analysis,
    'four_dim_cross': four_dim_cross,
    'best_audience': best_audience,
    'category_price_matrix': category_price_matrix,
    'action_items': actions,
    'creative_analysis': creative_analysis,
    'wordcloud': wordcloud,
    'trend': trend,
    'threedim': threedim,
    'category_traffic': category_traffic,
    'resource_category': resource_category,
    'heatmap_data': heatmap_data,
    'heatmap_max': round(heatmap_max, 2),
    'top_categories': top_cats,
    'resource_category_recommendations': resource_category_recommendations,
    'resource_category_detail': resource_category_detail,
    'price_band_distribution': price_band_distribution,
    'price_band_type': price_band_type,
    'resource_type_efficiency': resource_type_efficiency,
    'resource_health_status': resource_health_status,
    'resource_price_band_matrix': resource_price_band_matrix,
    'resource_price_band_total': resource_price_band_total
}

with open('/Users/zhengkeying/agent teams作业/data_analysis_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Done! Saved to data_analysis_output.json")
print("Keys:", list(output.keys()))
print("Resources:", len(resource_efficiency))
print("Selling points:", len(selling_point_analysis))
print("Four-dim:", len(four_dim_cross))
print("Category traffic:", len(category_traffic))
print("Resource-category combos:", len(resource_category))
print("Heatmap cells:", len(heatmap_data))
print("Actions:", len(actions))
print("Price bands:", len(price_band_distribution))
print("Resource type efficiency:", len(resource_type_efficiency))
