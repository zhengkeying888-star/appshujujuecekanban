import json, os

DATA_PATH = '/Users/zhengkeying/agent teams作业/data_analysis_output.json'
OUTPUT_PATH = '/Users/zhengkeying/agent teams作业/dashboard/v2/index.html'

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Unpack data
cd = data['core_diagnosis']
strategy_cards = data['strategy_cards']
resource_health = data['resource_health']
action_checklist = data['action_checklist']
resource_gmv_waterfall = data['resource_gmv_waterfall']
factor_impacts = data['factor_impacts']
auto_insight = data['auto_insight']
ms = data['monthly_summary']
re_list = data['resource_efficiency']
rem = data['resource_efficiency_matrix']
rgm = data['resource_growth_matrix']
cc = data['conversion_change']
pbd = data['price_band_distribution']
rpb = data.get('resource_price_band', {})
pbtd = data.get('price_band_type_distribution', [])
rpbt = data.get('resource_price_band_type', {})
rul = data.get('resource_user_level', {})
cat_summary = data.get('category_summary', [])
cat_detail = data.get('category_detail', [])
cat_price_band = data.get('category_price_band', [])
mau_summary = data['mau_summary']
mau_by_level = data['mau_by_level']
retention = data['retention']
user_journey = data['user_journey']

m3 = ms['2026-03']
m4 = ms['2026-04']

def fmt_money(n):
    return f"¥{n/10000:.1f}万"

def fmt_pct(n):
    return f"{n:.2f}%"

def fmt_int(n):
    return f"{int(n):,}"

def mom_sign(v):
    if v > 0:
        return f"+{v:.1f}%"
    return f"{v:.1f}%"

# Prepare JSON for JS injection
raw_data_json = json.dumps(data, ensure_ascii=False)
march_funnel_json = json.dumps([
    {'value': user_journey['march']['exposure'], 'name': '曝光 UV'},
    {'value': user_journey['march']['click'], 'name': '点击 UV'},
    {'value': user_journey['march']['lead'], 'name': '线索数'},
], ensure_ascii=False)
april_funnel_json = json.dumps([
    {'value': user_journey['april']['exposure'], 'name': '曝光 UV'},
    {'value': user_journey['april']['click'], 'name': '点击 UV'},
    {'value': user_journey['april']['lead'], 'name': '线索数'},
], ensure_ascii=False)

mau_gmv_json = json.dumps([
    {'month': '3月', 'mau': mau_summary.get('2026-03', {}).get('total_mau', 758580), 'gmv': round(m3['gmv']/10000, 1)},
    {'month': '4月', 'mau': mau_summary.get('2026-04', {}).get('total_mau', 702752), 'gmv': round(m4['gmv']/10000, 1)},
], ensure_ascii=False)
factor_impacts_json = json.dumps(factor_impacts, ensure_ascii=False)
user_journey_json = json.dumps(user_journey, ensure_ascii=False)
resource_price_band_json = json.dumps(rpb, ensure_ascii=False)
price_band_type_distribution_json = json.dumps(pbtd, ensure_ascii=False)
resource_price_band_type_json = json.dumps(rpbt, ensure_ascii=False)
resource_user_level_json = json.dumps(rul, ensure_ascii=False)
category_summary_json = json.dumps(cat_summary, ensure_ascii=False)
category_detail_json = json.dumps(cat_detail, ensure_ascii=False)
category_price_band_json = json.dumps(cat_price_band, ensure_ascii=False)

def build_sunburst_data(pb_data, month='april'):
    key = 'april_leads' if month == 'april' else 'march_leads'
    pb_colors = {'0元': '#3b82f6', '1元': '#8b5cf6', '3元': '#06b6d4', '9元': '#f59e0b', '其他': '#64748b'}
    cat_colors = {'正式品': '#3b82f6', '孵化品': '#10b981', '未分类': '#64748b'}
    result = []
    for pb in ['0元', '1元', '3元', '9元', '其他']:
        children = []
        for ct in ['正式品', '孵化品', '未分类']:
            items = [d for d in pb_data if d.get('price_band') == pb and d.get('cat_type') == ct]
            val = sum(d.get(key, 0) for d in items)
            if val > 0:
                children.append({'name': ct, 'value': val, 'itemStyle': {'color': cat_colors.get(ct, '#64748b')}})
        if children:
            result.append({'name': pb, 'itemStyle': {'color': pb_colors.get(pb, '#64748b')}, 'children': children})
    return result

sunburst_global_json = json.dumps(build_sunburst_data(pbtd, 'april'), ensure_ascii=False)

# Helper to build signal cards HTML
def build_signal_cards():
    cards = []
    for sig in cd['signals']:
        color = 'var(--danger)' if sig['status'] == 'danger' else 'var(--success)'
        glow = f"box-shadow:0 0 20px {'rgba(239,68,68,0.2)' if sig['status'] == 'danger' else 'rgba(16,185,129,0.2)'}"
        arrow = '↓' if sig['mom_pct'] < 0 else '↑'
        badge_class = 'badge-danger' if sig['status'] == 'danger' else 'badge-success'
        cards.append(f'''<div class="card signal-card animate-in" style="{glow}">
      <div class="left-border" style="background:{color}"></div>
      <div class="flex justify-between items-center" style="margin-bottom:8px">
        <span class="metric-name">{sig['name']}</span>
        <span class="badge {badge_class}">{arrow} {abs(sig['mom_pct']):.1f}%</span>
      </div>
      <div class="metric-value">{sig['april']}</div>
      <div class="metric-change">vs 3月: {sig['march']} → {sig['april']}</div>
    </div>''')
    return '\n'.join(cards)

# Build diagnosis cards for screen 2
diagnosis_sorted = sorted(cc, key=lambda x: x['mom'])
def build_diagnosis_cards():
    cards = []
    for d_item in diagnosis_sorted[:3]:
        status_color = 'var(--danger)' if d_item['mom'] < 0 else 'var(--success)'
        arrow = '↓' if d_item['mom'] < 0 else '↑'
        cards.append(f'''<div class="card animate-in" style="border-left:3px solid {status_color}">
      <div class="flex justify-between items-center" style="margin-bottom:8px">
        <span style="font-size:16px;font-weight:700">{d_item['metric']}</span>
        <span class="badge badge-info">{d_item.get('owner','运营')}</span>
      </div>
      <div style="font-size:20px;font-weight:700;margin-bottom:4px">
        {d_item['march']}% <span style="color:var(--text-tertiary)">→</span> {d_item['april']}% <span style="color:{status_color}">{arrow}{abs(d_item['mom']):.1f}%</span>
      </div>
      <div style="font-size:14px;color:var(--text-secondary)">{d_item.get('issue','')}</div>
    </div>''')
    return '\n'.join(cards)

# Build resource ranking table
re_top = sorted(re_list, key=lambda x: x['2026-04']['leads'], reverse=True)[:10]
def build_resource_table():
    rows = []
    for idx, r in enumerate(re_top, 1):
        m4 = r['2026-04']
        mom = r['环比']
        gmv_mom = mom['gmv']
        row_class = 'growth' if gmv_mom > 0 else 'decline'
        arrow = '↑' if gmv_mom > 0 else '↓'
        color = 'text-success' if gmv_mom > 0 else 'text-danger'
        gpe = m4.get('gmv_per_exposure', 0)
        gpc = m4.get('gmv_per_click', 0)
        rows.append(f'''<tr class="{row_class}" data-resource="{r['resource']}">
              <td style="font-weight:700;color:var(--text-tertiary)">#{idx}</td>
              <td>{r['resource']}</td>
              <td>{fmt_int(m4['leads'])}</td>
              <td>{fmt_pct(m4['lead_rate'])}</td>
              <td>{fmt_pct(m4['order_rate'])}</td>
              <td>¥{gpe:.2f}</td>
              <td>¥{gpc:.2f}</td>
              <td>{fmt_money(m4['gmv'])} <span class="{color}">{arrow}{abs(gmv_mom):.0f}%</span></td>
            </tr>''')
    return '\n'.join(rows)

# Build strategy cards
def build_strategy_cards():
    cards = []
    for sc in strategy_cards:
        cat_class = {'产研': 'product', '运营': 'ops', '内容': 'content'}.get(sc['category'], 'product')
        dots = ''.join([('<div class="dot filled"></div>' if i < sc['difficulty'] else '<div class="dot"></div>') for i in range(5)])
        cards.append(f'''<div class="card strategy-card animate-in">
      <div><span class="cat-tag {cat_class}">{sc['category']}</span></div>
      <div class="st-title">{sc['title']}</div>
      <div class="st-desc">{sc['desc']}</div>
      <div class="st-footer">
        <span class="text-success">预计 GMV 影响: {sc['gmv_impact']}</span>
        <span class="text-warning">风险: {sc['risk']}</span>
      </div>
      <div class="dots">{dots}</div>
    </div>''')
    return '\n'.join(cards)

# Build resource health table (replaces allocation table)
def build_health_table():
    rows = []
    for h in resource_health:
        status_color = {'danger': 'var(--danger)', 'success': 'var(--success)', 'warning': 'var(--warning)'}.get(h['status_color'], 'var(--text-tertiary)')
        status_bg = {'danger': 'rgba(239,68,68,0.1)', 'success': 'rgba(16,185,129,0.1)', 'warning': 'rgba(245,158,11,0.1)'}.get(h['status_color'], 'transparent')
        cvr_arrow = '↑' if h['cvr_mom'] > 0 else '↓'
        arpu_arrow = '↑' if h['arpu_mom'] > 0 else '↓'
        gmv_arrow = '↑' if h['gmv_change'] > 0 else '↓'
        cvr_color = 'text-success' if h['cvr_mom'] > 0 else 'text-danger'
        arpu_color = 'text-success' if h['arpu_mom'] > 0 else 'text-danger'
        gmv_color = 'text-success' if h['gmv_change'] > 0 else 'text-danger'
        rows.append(f'''<tr>
            <td>{h['resource']}</td>
            <td><span class="badge" style="background:{status_bg};color:{status_color};border:1px solid {status_color}">{h['status']}</span></td>
            <td class="{cvr_color}">{cvr_arrow}{abs(h['cvr_mom']):.1f}%</td>
            <td class="{arpu_color}">{arpu_arrow}{abs(h['arpu_mom']):.1f}%</td>
            <td class="{gmv_color}">{gmv_arrow}¥{abs(h['gmv_change']):.1f}万</td>
          </tr>''')
    return '\n'.join(rows)

# Build category summary cards (screen 3)
def build_category_summary_cards():
    attr_order = ['兴趣线', '健康线', '变美线']
    attr_colors = {'兴趣线': '#3b82f6', '健康线': '#10b981', '变美线': '#8b5cf6'}
    cards = []
    for attr in attr_order:
        m3_data = next((c for c in cat_summary if c['cat_attr'] == attr and c['month'] == 'march'), None)
        m4_data = next((c for c in cat_summary if c['cat_attr'] == attr and c['month'] == 'april'), None)
        if not m3_data or not m4_data:
            continue
        leads_mom = (m4_data['leads'] - m3_data['leads']) / m3_data['leads'] * 100 if m3_data['leads'] > 0 else 0
        gmv_mom = (m4_data['gmv'] - m3_data['gmv']) / m3_data['gmv'] * 100 if m3_data['gmv'] > 0 else 0
        cvr_mom = (m4_data['cvr'] - m3_data['cvr']) * 100
        ltv_mom = (m4_data['ltv'] - m3_data['ltv']) / m3_data['ltv'] * 100 if m3_data['ltv'] > 0 else 0
        color = attr_colors.get(attr, '#3b82f6')
        cards.append(f'''<div class="card animate-in" style="border-top:3px solid {color}">
      <div style="font-size:16px;font-weight:700;margin-bottom:16px;color:{color}">{attr}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div>
          <div style="font-size:12px;color:var(--text-tertiary)">线索数</div>
          <div style="font-size:20px;font-weight:700">{fmt_int(m4_data['leads'])}</div>
          <div style="font-size:12px;color:{'var(--success)' if leads_mom >= 0 else 'var(--danger)'}">{leads_mom:+.1f}%</div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-tertiary)">GMV</div>
          <div style="font-size:20px;font-weight:700">{fmt_money(m4_data['gmv'])}</div>
          <div style="font-size:12px;color:{'var(--success)' if gmv_mom >= 0 else 'var(--danger)'}">{gmv_mom:+.1f}%</div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-tertiary)">转化率</div>
          <div style="font-size:20px;font-weight:700">{m4_data['cvr']*100:.2f}%</div>
          <div style="font-size:12px;color:{'var(--success)' if cvr_mom >= 0 else 'var(--danger)'}">{cvr_mom:+.1f}pp</div>
        </div>
        <div>
          <div style="font-size:12px;color:var(--text-tertiary)">单线索产出</div>
          <div style="font-size:20px;font-weight:700">¥{m4_data['ltv']:.1f}</div>
          <div style="font-size:12px;color:{'var(--success)' if ltv_mom >= 0 else 'var(--danger)'}">{ltv_mom:+.1f}%</div>
        </div>
      </div>
      <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border-subtle)">
        <div style="font-size:12px;color:var(--text-tertiary);margin-bottom:4px">正式品 / 孵化品</div>
        <div style="display:flex;justify-content:space-between;font-size:13px">
          <span>线索: {fmt_int(m4_data['formal']['leads'])} / {fmt_int(m4_data['incubation']['leads'])}</span>
          <span>GMV: {fmt_money(m4_data['formal']['gmv'])} / {fmt_money(m4_data['incubation']['gmv'])}</span>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-top:2px">
          <span>CVR: {m4_data['formal']['cvr']*100:.2f}% / {m4_data['incubation']['cvr']*100:.2f}%</span>
          <span>LTV: ¥{m4_data['formal']['ltv']:.1f} / ¥{m4_data['incubation']['ltv']:.1f}</span>
        </div>
      </div>
    </div>''')
    return '\n'.join(cards)

# Build category detail table (screen 3)
def build_category_detail_table():
    attr_order = {'兴趣线': 0, '健康线': 1, '变美线': 2, '未分类': 3}
    sorted_cats = sorted(cat_detail, key=lambda x: (attr_order.get(x['cat_attr'], 99), -x['data'][1]['gmv'] if len(x['data']) > 1 else 0))
    rows = []
    for cd in sorted_cats:
        cat = cd['category']
        attr = cd['cat_attr']
        status = cd['cat_status']
        status_badge = '<span class="badge badge-success" style="font-size:11px">正式品</span>' if status == '正式品' else '<span class="badge badge-warning" style="font-size:11px">孵化品</span>' if status == '孵化品' else '<span class="badge" style="font-size:11px;background:var(--bg-elevated);color:var(--text-tertiary)">未分类</span>'
        # April data (index 1)
        d = cd['data'][1] if len(cd['data']) > 1 else cd['data'][0]
        m = cd['data'][0] if len(cd['data']) > 1 else None
        leads = d['leads']
        gmv = d['gmv']
        cvr = d['cvr'] * 100
        ltv = d['ltv']
        gmv_top3 = ' / '.join([f"{t['resource']}({t['value']/10000:.1f}万)" for t in d.get('gmv_top3', [])])
        leads_top3 = ' / '.join([f"{t['resource']}({t['value']})" for t in d.get('leads_top3', [])])
        cvr_top3 = ' / '.join([f"{t['resource']}({t['value']*100:.2f}%)" for t in d.get('cvr_top3', [])])
        # Month-over-month
        if m:
            leads_mom = (leads - m['leads']) / m['leads'] * 100 if m['leads'] > 0 else 0
            gmv_mom = (gmv - m['gmv']) / m['gmv'] * 100 if m['gmv'] > 0 else 0
            cvr_mom = (d['cvr'] - m['cvr']) * 100
            ltv_mom = (ltv - m['ltv']) / m['ltv'] * 100 if m['ltv'] > 0 else 0
            leads_str = f"{fmt_int(leads)} <span style=\"font-size:11px;color:{'var(--success)' if leads_mom >= 0 else 'var(--danger)'}\">{leads_mom:+.1f}%</span>"
            gmv_str = f"{fmt_money(gmv)} <span style=\"font-size:11px;color:{'var(--success)' if gmv_mom >= 0 else 'var(--danger)'}\">{gmv_mom:+.1f}%</span>"
            cvr_str = f"{cvr:.2f}% <span style=\"font-size:11px;color:{'var(--success)' if cvr_mom >= 0 else 'var(--danger)'}\">{cvr_mom:+.1f}pp</span>"
            ltv_str = f"¥{ltv:.1f} <span style=\"font-size:11px;color:{'var(--success)' if ltv_mom >= 0 else 'var(--danger)'}\">{ltv_mom:+.1f}%</span>"
        else:
            leads_str = fmt_int(leads)
            gmv_str = fmt_money(gmv)
            cvr_str = f"{cvr:.2f}%"
            ltv_str = f"¥{ltv:.1f}"
        rows.append(f'''<tr class="cat-row" data-category="{cat}" data-attr="{attr}">
          <td><strong>{cat}</strong><br>{status_badge}</td>
          <td>{attr}</td>
          <td>{leads_str}</td>
          <td>{gmv_str}</td>
          <td>{cvr_str}</td>
          <td>{ltv_str}</td>
          <td style="font-size:12px;color:var(--text-secondary)">{gmv_top3}</td>
          <td style="font-size:12px;color:var(--text-secondary)">{leads_top3}</td>
          <td style="font-size:12px;color:var(--text-secondary)">{cvr_top3}</td>
        </tr>''')
    return '\n'.join(rows)

# Build action cards by owner (screen 1 bottom)
def build_owner_cards():
    owners = {'产研': 'code', '运营': 'campaign', '内容': 'brush'}
    cards = []
    for owner, icon in owners.items():
        items = [sc for sc in strategy_cards if sc['category'] == owner]
        if not items:
            continue
        items_html = '\n'.join([
            f'''<div>
              <span class="badge badge-{'danger' if sc['risk'] == '高' else 'warning'}" style="margin-bottom:4px">{sc['risk']}风险</span>
              <div style="font-size:15px;font-weight:600;margin-top:4px">{sc['title']}</div>
              <div style="font-size:13px;color:var(--text-secondary)">{sc['desc'][:40]}...</div>
            </div>'''
            for sc in items[:2]
        ])
        cards.append(f'''<div class="card action-card animate-in" style="border-top:3px solid var(--accent-primary)">
      <div class="section-title" style="margin-bottom:12px">
        <span class="material-symbols-outlined">{icon}</span>
        {owner}侧
      </div>
      <div style="display:flex;flex-direction:column;gap:12px">
        {items_html}
      </div>
    </div>''')
    return '\n'.join(cards)

# Build checklist
def build_checklist():
    items = []
    for ac in action_checklist:
        p_class = 'p0' if ac['priority'] == 'P0' else ''
        basis_html = f'<div style="font-size:12px;color:var(--text-tertiary);margin-top:4px">依据: {ac.get("basis","")}</div>' if ac.get('basis') else ''
        items.append(f'''<div class="checklist-item {p_class}">
        <div class="checklist-num">{ac['seq']}</div>
        <div class="checklist-content">
          <div class="checklist-title">{ac['title']}</div>
          {basis_html}
          <div class="checklist-meta">
            <span class="badge badge-info">{ac['owner']}</span>
            <span>截止日期: {ac['deadline']}</span>
            <span class="badge {'badge-danger' if ac['priority']=='P0' else 'badge-warning'}">{ac['priority']}</span>
          </div>
        </div>
      </div>''')
    return '\n'.join(items)

# Build HTML
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>APP 商业化决策看板 v2</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root {{
  --bg-base: #0f172a;
  --bg-surface: #1e293b;
  --bg-elevated: #334155;
  --border-subtle: rgba(148,163,184,0.12);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --accent-primary: #3b82f6;
  --accent-gradient: linear-gradient(135deg, #3b82f6, #8b5cf6);
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter','Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg-base);color:var(--text-primary);line-height:1.5;min-height:100vh}}
a{{text-decoration:none;color:inherit}}
.card{{background:var(--bg-surface);border:1px solid var(--border-subtle);border-radius:16px;padding:24px;box-shadow:0 4px 24px rgba(0,0,0,0.3);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}}
.card:hover{{transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,0.4);border-color:rgba(148,163,184,0.2)}}
.section-title{{font-size:16px;font-weight:600;color:var(--text-primary);margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.section-title .material-symbols-outlined{{font-size:20px;color:var(--accent-primary)}}
.badge{{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600}}
.badge-success{{background:rgba(16,185,129,0.15);color:var(--success)}}
.badge-danger{{background:rgba(239,68,68,0.15);color:var(--danger)}}
.badge-warning{{background:rgba(245,158,11,0.15);color:var(--warning)}}
.badge-info{{background:rgba(59,130,246,0.15);color:var(--accent-primary)}}
.btn-primary{{background:var(--accent-gradient);color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:14px;font-weight:500;cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:filter .2s ease,transform .2s ease}}
.btn-primary:hover{{filter:brightness(1.1);transform:scale(1.02)}}
.text-success{{color:var(--success)}}
.text-danger{{color:var(--danger)}}
.text-warning{{color:var(--warning)}}
.text-secondary{{color:var(--text-secondary)}}
.text-tertiary{{color:var(--text-tertiary)}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}}
.grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}}
.grid-5{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}}
.flex{{display:flex}}
.flex-col{{flex-direction:column}}
.items-center{{align-items:center}}
.justify-between{{justify-content:space-between}}
.gap-2{{gap:8px}}
.gap-3{{gap:12px}}
.gap-4{{gap:16px}}
.mt-4{{margin-top:16px}}
.mt-5{{margin-top:20px}}
.w-full{{width:100%}}
.h-full{{height:100%}}
.navbar{{position:fixed;top:0;left:0;right:0;height:64px;background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);backdrop-filter:blur(12px);z-index:1000;display:flex;align-items:center;justify-content:space-between;padding:0 32px}}
.nav-left{{display:flex;align-items:center;gap:12px}}
.nav-logo{{font-size:20px;font-weight:700;background:var(--accent-gradient);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nav-sub{{font-size:13px;color:var(--text-tertiary);background:var(--bg-elevated);padding:2px 8px;border-radius:6px}}
.nav-tabs{{display:flex;gap:4px;background:var(--bg-elevated);padding:4px;border-radius:8px}}
.nav-tab{{padding:6px 16px;border-radius:8px;font-size:14px;font-weight:500;color:var(--text-secondary);cursor:pointer;border:none;background:transparent;transition:all .2s}}
.nav-tab.active{{background:var(--accent-gradient);color:#fff}}
.main-content{{padding:88px 32px 32px;max-width:1440px;margin:0 auto}}
.screen{{margin-bottom:40px}}
.screen-title{{font-size:24px;font-weight:700;margin-bottom:20px;color:var(--text-primary)}}
.hero-card{{position:relative;overflow:hidden}}
.hero-card::before{{content:'';position:absolute;top:0;left:0;width:4px;height:100%;background:var(--accent-primary);border-radius:16px 0 0 16px}}
.hero-label{{font-size:11px;font-weight:600;color:var(--accent-primary);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}}
.hero-title{{font-size:32px;font-weight:700;color:var(--text-primary);margin-bottom:8px}}
.hero-sub{{font-size:16px;color:var(--text-secondary);margin-bottom:16px}}
.progress-bar{{display:flex;height:6px;border-radius:3px;overflow:hidden;background:var(--bg-elevated)}}
.progress-bar .red{{background:var(--danger);height:100%}}
.progress-bar .green{{background:var(--success);height:100%}}
.progress-labels{{display:flex;justify-content:space-between;margin-top:6px;font-size:12px;color:var(--text-tertiary)}}
.signal-card{{position:relative;padding:20px}}
.signal-card .left-border{{position:absolute;left:0;top:16px;bottom:16px;width:3px;border-radius:0 3px 3px 0}}
.signal-card .metric-name{{font-size:13px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}}
.signal-card .metric-value{{font-size:40px;font-weight:700;color:var(--text-primary);font-variant-numeric:tabular-nums;letter-spacing:-.02em}}
.signal-card .metric-change{{font-size:13px;color:var(--text-tertiary);margin-top:4px}}
.data-table{{width:100%;border-collapse:separate;border-spacing:0}}
.data-table th{{background:var(--bg-elevated);color:var(--text-tertiary);font-size:12px;font-weight:600;text-transform:uppercase;padding:12px 16px;text-align:left}}
.data-table td{{padding:14px 16px;border-bottom:1px solid var(--border-subtle);font-size:14px;color:var(--text-primary)}}
.data-table tr:hover td{{background:var(--bg-elevated)}}
.data-table tr.growth td{{background:rgba(16,185,129,0.06)}}
.data-table tr.decline td{{background:rgba(239,68,68,0.06)}}
.data-table tr.highlight-row td{{background:rgba(59,130,246,0.15) !important;box-shadow:inset 2px 0 0 var(--accent-primary)}}
.action-card{{border-left:3px solid transparent}}
.action-card.product{{border-left-color:var(--accent-primary)}}
.action-card.ops{{border-left-color:var(--success)}}
.action-card.content{{border-left-color:var(--warning)}}
.strategy-card{{display:flex;flex-direction:column;gap:12px}}
.strategy-card .cat-tag{{display:inline-block;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:600}}
.strategy-card .cat-tag.product{{background:rgba(59,130,246,0.15);color:var(--accent-primary)}}
.strategy-card .cat-tag.ops{{background:rgba(16,185,129,0.15);color:var(--success)}}
.strategy-card .cat-tag.content{{background:rgba(245,158,11,0.15);color:var(--warning)}}
.strategy-card .st-title{{font-size:18px;font-weight:700}}
.strategy-card .st-desc{{font-size:14px;color:var(--text-secondary);line-height:1.6}}
.strategy-card .st-footer{{display:flex;justify-content:space-between;align-items:center;font-size:13px;margin-top:auto;padding-top:12px;border-top:1px solid var(--border-subtle)}}
.dots{{display:flex;gap:4px}}
.dot{{width:8px;height:8px;border-radius:50%;background:var(--border-subtle)}}
.dot.filled{{background:var(--accent-primary)}}
.checklist-item{{display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid var(--border-subtle)}}
.checklist-item:last-child{{border-bottom:none}}
.checklist-item.p0{{border-left:3px solid var(--danger);padding-left:16px;margin-left:-3px}}
.checklist-num{{width:32px;height:32px;border-radius:50%;background:var(--accent-primary);color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0}}
.checklist-content{{flex:1}}
.checklist-title{{font-size:16px;font-weight:600}}
.checklist-meta{{display:flex;gap:12px;margin-top:4px;font-size:13px;color:var(--text-secondary)}}
.footer{{text-align:center;padding:40px 0;font-size:13px;color:var(--text-tertiary);border-top:1px solid var(--border-subtle);margin-top:40px}}
@keyframes fadeInUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
.animate-in{{animation:fadeInUp .6s cubic-bezier(.16,1,.3,1) forwards;opacity:0}}
</style>
</head>
<body>
<nav class="navbar">
  <div class="nav-left">
    <span class="material-symbols-outlined" style="color:var(--accent-primary)">monitoring</span>
    <div>
      <div class="nav-logo">APP 商业化决策看板</div>
    </div>
    <span class="nav-sub">2026年3-4月</span>
  </div>
  <div class="nav-tabs">
    <button type="button" class="nav-tab active" onclick="setMonth('march', this)">3月</button>
    <button type="button" class="nav-tab" onclick="setMonth('april', this)">4月</button>
    <button type="button" class="nav-tab" onclick="setMonth('compare', this)">对比分析</button>
  </div>
  <button type="button" class="btn-primary" onclick="exportReport(this)">
    <span class="material-symbols-outlined" style="font-size:16px">download</span>
    导出 HTML 月报
  </button>
</nav>

<div class="main-content">

<!-- Screen 1 -->
<div class="screen" id="screen1">
  <div class="screen-title">1. 诊断结论</div>
  <div class="card hero-card animate-in" style="margin-bottom:20px">
    <div class="hero-label">诊断结论</div>
    <div class="hero-title">{cd['headline']}</div>
    <div class="hero-sub">{cd['subline']}</div>
    <div style="margin-top:12px;padding:10px 14px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.15);border-radius:8px;font-size:14px;color:var(--accent-primary);display:flex;align-items:center;gap:6px">
      <span class="material-symbols-outlined" style="font-size:18px">lightbulb</span>
      <span>{auto_insight}</span>
    </div>
    <div class="progress-bar">
      <div class="red" style="width:{cd['negative_pct']}%"></div>
      <div class="green" style="width:{cd['positive_pct']}%"></div>
    </div>
    <div class="progress-labels">
      <span>负向驱动因素 ({cd['negative_pct']}%)</span>
      <span>正向抵消因素 ({cd['positive_pct']}%)</span>
    </div>
  </div>
  <div class="grid-5" style="margin-bottom:20px">
    {build_signal_cards()}
  </div>
  <div class="grid-2" style="margin-bottom:20px">
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">tune</span>
        GMV 三大杠杆环比变化
      </div>
      <div id="leverage-compare-chart" style="width:100%;height:280px"></div>
    </div>
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">waterfall_chart</span>
        GMV 因素分解（连环替代法）
      </div>
      <div id="gmv-waterfall-chart" style="width:100%;height:280px"></div>
    </div>
  </div>
  <div class="grid-2" style="margin-bottom:20px">
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">trending_down</span>
        前端入口效率变化
        <span style="font-size:11px;color:var(--text-tertiary);margin-left:auto">CTR = 点击UV / 曝光UV | CTCVR = 线索数 / 点击UV</span>
      </div>
      <div id="conversion-change-chart" style="width:100%;height:340px"></div>
    </div>
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">trending_down</span>
        后端转化效率变化
        <span style="font-size:11px;color:var(--text-tertiary);margin-left:auto">首单转化率 = 首单数 / 线索数 | 单线索产出 = GMV / 线索数</span>
      </div>
      <div id="backend-efficiency-chart" style="width:100%;height:340px"></div>
    </div>
  </div>
  <div class="grid-2">
    {build_owner_cards()}
  </div>
</div>

<!-- Screen 2 -->
<div class="screen" id="screen2">
  <div class="screen-title">2. 转化链路全景</div>
  <div style="display:grid;grid-template-columns:55% 45%;gap:20px;margin-bottom:20px">
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">filter_alt</span>
        前链路效率（曝光 → 线索）
      </div>
      <div id="funnel-chart" style="width:100%;height:420px"></div>
      <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border-subtle)">
        <div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">后链路效率（线索 → 首单）</div>
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
          <div style="flex:1;text-align:center">
            <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:10px;padding:10px 4px">
              <div style="font-size:14px;font-weight:700;color:var(--accent-primary)">{user_journey['april']['friend_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--text-tertiary);margin-top:2px">3月 {user_journey['march']['friend_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--{'danger' if user_journey['mom']['friend_rate'] < 0 else 'success'});margin-top:2px">{'↓' if user_journey['mom']['friend_rate'] < 0 else '↑'}{abs(user_journey['mom']['friend_rate']):.1f}%</div>
              <div style="font-size:11px;color:var(--text-secondary);margin-top:4px">好友</div>
              <div style="font-size:12px;color:var(--text-primary);margin-top:2px">{fmt_int(user_journey['april']['friend'])}</div>
            </div>
          </div>
          <div style="color:var(--text-tertiary)">→</div>
          <div style="flex:1;text-align:center">
            <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:10px;padding:10px 4px">
              <div style="font-size:14px;font-weight:700;color:var(--accent-primary)">{user_journey['april']['attend_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--text-tertiary);margin-top:2px">3月 {user_journey['march']['attend_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--{'danger' if user_journey['mom']['attend_rate'] < 0 else 'success'});margin-top:2px">{'↓' if user_journey['mom']['attend_rate'] < 0 else '↑'}{abs(user_journey['mom']['attend_rate']):.1f}%</div>
              <div style="font-size:11px;color:var(--text-secondary);margin-top:4px">到课</div>
              <div style="font-size:12px;color:var(--text-primary);margin-top:2px">{fmt_int(user_journey['april']['attend'])}</div>
            </div>
          </div>
          <div style="color:var(--text-tertiary)">→</div>
          <div style="flex:1;text-align:center">
            <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:10px;padding:10px 4px">
              <div style="font-size:14px;font-weight:700;color:var(--accent-primary)">{user_journey['april']['complete_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--text-tertiary);margin-top:2px">3月 {user_journey['march']['complete_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--{'danger' if user_journey['mom']['complete_rate'] < 0 else 'success'});margin-top:2px">{'↓' if user_journey['mom']['complete_rate'] < 0 else '↑'}{abs(user_journey['mom']['complete_rate']):.1f}%</div>
              <div style="font-size:11px;color:var(--text-secondary);margin-top:4px">完课</div>
              <div style="font-size:12px;color:var(--text-primary);margin-top:2px">{fmt_int(user_journey['april']['complete'])}</div>
            </div>
          </div>
          <div style="color:var(--text-tertiary)">→</div>
          <div style="flex:1;text-align:center">
            <div style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:10px;padding:10px 4px">
              <div style="font-size:14px;font-weight:700;color:var(--accent-primary)">{user_journey['april']['order_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--text-tertiary);margin-top:2px">3月 {user_journey['march']['order_rate']:.1f}%</div>
              <div style="font-size:11px;color:var(--{'danger' if user_journey['mom']['order_rate'] < 0 else 'success'});margin-top:2px">{'↓' if user_journey['mom']['order_rate'] < 0 else '↑'}{abs(user_journey['mom']['order_rate']):.1f}%</div>
              <div style="font-size:11px;color:var(--text-secondary);margin-top:4px">首单</div>
              <div style="font-size:12px;color:var(--text-primary);margin-top:2px">{fmt_int(user_journey['april']['order'])}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">compare_arrows</span>
        各阶段转化率对比
      </div>
      <div id="stage-compare-chart" style="width:100%;height:340px"></div>
      <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border-subtle)">
        <div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px">产值结果对比</div>
        <div id="gmv-ltv-compare-chart" style="width:100%;height:180px"></div>
      </div>
    </div>
  </div>
  <div class="grid-3">
    {build_diagnosis_cards()}
  </div>
</div>

<!-- Screen 3 -->
<div class="screen" id="screen3">
  <div class="screen-title">3. 根因下钻</div>
  <div class="card animate-in" style="margin-bottom:20px">
    <div class="section-title">
      <span class="material-symbols-outlined">scatter_plot</span>
      资源位效率矩阵
    </div>
    <div id="efficiency-matrix-chart" style="width:100%;height:440px"></div>
  </div>
  <div class="card animate-in" style="margin-bottom:20px">
    <div class="section-title">
      <span class="material-symbols-outlined">waterfall_chart</span>
      资源位 GMV 瀑布图（3月 → 4月变化量）
    </div>
    <div id="resource-gmv-waterfall-chart" style="width:100%;height:280px"></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">trending_up</span>
        资源位增长矩阵
      </div>
      <div id="growth-matrix-chart" style="width:100%;height:380px"></div>
    </div>
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">sort</span>
        资源位效率 TOP10
      </div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>排名</th><th>资源位</th><th>线索数</th><th>线索生成率</th><th>首单转化率</th><th>单曝光产出</th><th>单点击产出</th><th>GMV</th>
            </tr>
          </thead>
          <tbody>
            {build_resource_table()}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="grid-3">
    <div class="card animate-in">
      <div class="section-title" style="justify-content:space-between">
        <span><span class="material-symbols-outlined">donut_large</span> <span id="price-band-title">价格带结构</span></span>
        <span>
          <span id="price-band-hint" style="font-size:11px;color:var(--text-tertiary);margin-right:8px;display:none">点击空白处取消选择</span>
          <span id="price-band-reset" style="font-size:12px;color:#3b82f6;cursor:pointer;display:none" onclick="resetPriceBand()">↺ 重置</span>
        </span>
      </div>
      <div id="price-band-chart" style="width:100%;height:280px"></div>
    </div>
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">brightness_7</span>
        价格带 × 品类类型
      </div>
      <div id="sunburst-chart" style="width:100%;height:280px"></div>
    </div>
    <div class="card animate-in">
      <div class="section-title">
        <span class="material-symbols-outlined">group</span>
        用户等级效率分析
      </div>
      <div id="mau-chart" style="width:100%;height:280px"></div>
    </div>
  </div>

  <!-- 品类产出分析 -->
  <div class="card animate-in" style="margin-bottom:20px">
    <div class="section-title">
      <span class="material-symbols-outlined">category</span>
      品类产出分析
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px">
      {build_category_summary_cards()}
    </div>
    <div style="overflow-x:auto">
      <table class="data-table" id="category-detail-table">
        <thead>
          <tr>
            <th>品类</th>
            <th>品类属性</th>
            <th>线索数</th>
            <th>GMV</th>
            <th>首单转化率</th>
            <th>单线索产出</th>
            <th>GMV Top3</th>
            <th>线索 Top3</th>
            <th>CVR Top3</th>
          </tr>
        </thead>
        <tbody>
          {build_category_detail_table()}
        </tbody>
      </table>
    </div>
    <div id="category-price-band-drilldown" style="margin-top:20px;display:none">
      <div style="font-size:16px;font-weight:700;margin-bottom:12px;color:var(--text-primary)">
        <span id="selected-category-name"></span> 价格带结构
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <div id="category-price-band-chart" style="width:100%;height:280px"></div>
        <div id="category-price-band-table" style="width:100%"></div>
      </div>
    </div>
  </div>
</div>

<!-- Screen 4 -->
<div class="screen" id="screen4">
  <div class="screen-title">4. 策略建议</div>
  <div class="grid-3" style="margin-bottom:20px">
    {build_strategy_cards()}
  </div>
  <div class="card animate-in" style="margin-bottom:20px">
    <div class="section-title">
      <span class="material-symbols-outlined">health_and_safety</span>
      资源位健康预警
    </div>
    <div style="overflow-x:auto">
      <table class="data-table">
        <thead>
          <tr><th>资源位</th><th>健康状态</th><th>线索→首单转化率环比</th><th>单线索产出环比</th><th>GMV变化</th></tr>
        </thead>
        <tbody>
          {build_health_table()}
        </tbody>
      </table>
    </div>
  </div>
  <div class="card animate-in">
    <div class="section-title">
      <span class="material-symbols-outlined">checklist</span>
      次月核心行动清单
    </div>
    <div>
      {build_checklist()}
    </div>
  </div>
</div>

<div class="footer">APP 商业化决策看板 · 2026年3-4月</div>

</div>

<script>
const RAW_DATA = {raw_data_json};
let currentMonth = 'march';

function setMonth(m, el) {{
  currentMonth = m;
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  renderCharts();
}}

function renderCharts() {{
  // 1. Front-end Efficiency Chart: 各资源位 CTR / CTCVR 对比
  const ccChart = echarts.init(document.getElementById('conversion-change-chart'));
  const feResData = RAW_DATA.resource_efficiency || [];
  const feTopRes = feResData.sort((a, b) => (b['2026-04'].leads || 0) - (a['2026-04'].leads || 0)).slice(0, 8);
  const feCategories = feTopRes.map(r => r.resource);
  const feCtrMarch = feTopRes.map(r => (r['2026-03'].ctr || 0));
  const feCtrApril = feTopRes.map(r => (r['2026-04'].ctr || 0));
  const feCtcvrMarch = feTopRes.map(r => (r['2026-03'].lead_rate || 0));
  const feCtcvrApril = feTopRes.map(r => (r['2026-04'].lead_rate || 0));
  ccChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      axisPointer: {{type: 'shadow'}},
      formatter: function(p) {{
        const res = p[0].name;
        const d = feTopRes.find(r => r.resource === res);
        if (!d) return res;
        return '<div style="font-weight:600;margin-bottom:4px">' + res + '</div>' +
               '<div>CTR: 3月 ' + (d['2026-03'].ctr || 0).toFixed(2) + '% / 4月 ' + (d['2026-04'].ctr || 0).toFixed(2) + '%</div>' +
               '<div>CTCVR: 3月 ' + (d['2026-03'].lead_rate || 0).toFixed(2) + '% / 4月 ' + (d['2026-04'].lead_rate || 0).toFixed(2) + '%</div>';
      }}
    }},
    legend: {{bottom: 0, textStyle: {{color: '#94a3b8', fontSize: 11}}}},
    grid: {{left: 100, right: 40, top: 20, bottom: 40}},
    xAxis: {{
      type: 'value',
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8', formatter: '{{value}}%'}}
    }},
    yAxis: {{
      type: 'category',
      data: feCategories,
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#f8fafc', fontSize: 11}}
    }},
    series: [
      {{
        name: '3月 CTR', type: 'bar',
        data: feCtrMarch,
        itemStyle: {{color: 'rgba(59,130,246,0.5)', borderRadius: [4,0,0,4]}},
        barMaxWidth: 12
      }},
      {{
        name: '4月 CTR', type: 'bar',
        data: feCtrApril,
        itemStyle: {{color: '#3b82f6', borderRadius: [0,4,4,0]}},
        barMaxWidth: 12
      }},
      {{
        name: '3月 CTCVR', type: 'bar',
        data: feCtcvrMarch,
        itemStyle: {{color: 'rgba(139,92,246,0.5)', borderRadius: [4,0,0,4]}},
        barMaxWidth: 12
      }},
      {{
        name: '4月 CTCVR', type: 'bar',
        data: feCtcvrApril,
        itemStyle: {{color: '#8b5cf6', borderRadius: [0,4,4,0]}},
        barMaxWidth: 12
      }}
    ]
  }});

  // 1.2 Back-end Efficiency Chart: 各资源位 首单转化率 / 单线索产出 对比
  const beChart = echarts.init(document.getElementById('backend-efficiency-chart'));
  const beResData = RAW_DATA.resource_efficiency || [];
  const beTopRes = beResData.sort((a, b) => (b['2026-04'].leads || 0) - (a['2026-04'].leads || 0)).slice(0, 8);
  const beCategories = beTopRes.map(r => r.resource);
  const beCvrMarch = beTopRes.map(r => (r['2026-03'].cvr_from_leads || 0));
  const beCvrApril = beTopRes.map(r => (r['2026-04'].cvr_from_leads || 0));
  const beArpuMarch = beTopRes.map(r => (r['2026-03'].arpu || 0));
  const beArpuApril = beTopRes.map(r => (r['2026-04'].arpu || 0));
  beChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      axisPointer: {{type: 'shadow'}},
      formatter: function(p) {{
        const res = p[0].name;
        const d = beTopRes.find(r => r.resource === res);
        if (!d) return res;
        const cvrMom = ((d['2026-04'].cvr_from_leads || 0) - (d['2026-03'].cvr_from_leads || 0));
        const arpuMom = d['2026-03'].arpu > 0 ? ((d['2026-04'].arpu - d['2026-03'].arpu) / d['2026-03'].arpu * 100) : 0;
        return '<div style="font-weight:600;margin-bottom:4px">' + res + '</div>' +
               '<div>首单转化率(CVR): 3月 ' + (d['2026-03'].cvr_from_leads || 0).toFixed(2) + '% / 4月 ' + (d['2026-04'].cvr_from_leads || 0).toFixed(2) + '% (环比' + (cvrMom >= 0 ? '+' : '') + cvrMom.toFixed(2) + 'pp)</div>' +
               '<div>单线索产出(ARPU): 3月 ¥' + (d['2026-03'].arpu || 0).toFixed(1) + ' / 4月 ¥' + (d['2026-04'].arpu || 0).toFixed(1) + ' (环比' + (arpuMom >= 0 ? '+' : '') + arpuMom.toFixed(1) + '%)</div>' +
               '<div style="font-size:11px;color:#94a3b8;margin-top:4px">公式: 首单转化率 = SUM(首单数) / SUM(线索数) | 单线索产出 = GMV / 线索数</div>';
      }}
    }},
    legend: {{bottom: 0, textStyle: {{color: '#94a3b8', fontSize: 11}}}},
    grid: {{left: 100, right: 60, top: 20, bottom: 50}},
    xAxis: [
      {{
        type: 'value', name: '首单转化率',
        position: 'bottom',
        axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
        splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
        axisLabel: {{color: '#94a3b8', formatter: '{{value}}%'}}
      }},
      {{
        type: 'value', name: '单线索产出(¥)',
        position: 'top',
        axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
        splitLine: {{show: false}},
        axisLabel: {{color: '#94a3b8', formatter: '¥{{value}}'}}
      }}
    ],
    yAxis: {{
      type: 'category',
      data: beCategories,
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#f8fafc', fontSize: 11}}
    }},
    series: [
      {{
        name: '3月 首单转化率', type: 'bar',
        xAxisIndex: 0,
        data: beCvrMarch,
        itemStyle: {{color: 'rgba(16,185,129,0.5)', borderRadius: [4,0,0,4]}},
        barMaxWidth: 10
      }},
      {{
        name: '4月 首单转化率', type: 'bar',
        xAxisIndex: 0,
        data: beCvrApril,
        itemStyle: {{color: '#10b981', borderRadius: [0,4,4,0]}},
        barMaxWidth: 10
      }},
      {{
        name: '3月 单线索产出', type: 'line',
        xAxisIndex: 1,
        data: beArpuMarch,
        symbol: 'circle', symbolSize: 6,
        lineStyle: {{color: 'rgba(245,158,11,0.5)', width: 2}},
        itemStyle: {{color: 'rgba(245,158,11,0.5)'}},
        label: {{show: false}}
      }},
      {{
        name: '4月 单线索产出', type: 'line',
        xAxisIndex: 1,
        data: beArpuApril,
        symbol: 'circle', symbolSize: 6,
        lineStyle: {{color: '#f59e0b', width: 2}},
        itemStyle: {{color: '#f59e0b'}},
        label: {{show: false}}
      }}
    ]
  }});

  // 1.5 GMV Leverage Change Chart (环比幅度)
  const ujLev = RAW_DATA.user_journey;
  const levChart = echarts.init(document.getElementById('leverage-compare-chart'));
  const levData = [
    {{name: '线索生成率', value: ujLev.mom.lead_gen_rate}},
    {{name: '首单转化率', value: ujLev.mom.cvr_from_leads}},
    {{name: 'LTV', value: ujLev.mom.arpu}},
  ];
  levChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      formatter: function(p) {{
        const d = levData[p[0].dataIndex];
        const arrow = d.value > 0 ? '↑' : '↓';
        const color = d.value > 0 ? '#10b981' : '#ef4444';
        return '<div style="font-weight:600;margin-bottom:4px">' + d.name + '</div>' +
               '<div style="color:' + color + '">' + arrow + Math.abs(d.value).toFixed(1) + '%</div>';
      }}
    }},
    grid: {{left: 100, right: 60, top: 20, bottom: 20}},
    xAxis: {{
      type: 'value',
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8', formatter: '{{value}}%'}}
    }},
    yAxis: {{
      type: 'category',
      data: levData.map(d => d.name),
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#f8fafc', fontSize: 13}}
    }},
    series: [{{
      type: 'bar',
      data: levData.map(d => ({{
        value: d.value,
        itemStyle: {{
          color: d.value >= 0 ? '#10b981' : '#ef4444',
          borderRadius: d.value >= 0 ? [0,4,4,0] : [4,0,0,4]
        }}
      }})),
      barHeight: 20,
      label: {{
        show: true,
        position: d => d.value >= 0 ? 'right' : 'left',
        color: '#f8fafc',
        fontSize: 13,
        fontWeight: 600,
        formatter: p => {{
          const d = levData[p.dataIndex];
          const sign = d.value >= 0 ? '+' : '';
          return sign + d.value.toFixed(1) + '%';
        }}
      }}
    }}]
  }});

  // 1.6 GMV Waterfall Chart
  const fi = {factor_impacts_json};
  const ujWf = {user_journey_json};
  const wfChart = echarts.init(document.getElementById('gmv-waterfall-chart'));
  const startVal = ujWf.march.gmv / 10000;
  const endVal = ujWf.april.gmv / 10000;
  const wfCategories = ['3月GMV', ...fi.map(f => f.factor), '4月GMV'];
  let cumulative = startVal;
  const wfInvisible = [0];
  const wfValues = [{{value: startVal, itemStyle: {{color: '#3b82f6'}}}}];
  fi.forEach(f => {{
    const val = f.impact / 10000;
    if (val >= 0) {{
      wfInvisible.push(cumulative);
      wfValues.push({{value: val, itemStyle: {{color: '#10b981'}}}});
      cumulative += val;
    }} else {{
      cumulative += val;
      wfInvisible.push(cumulative);
      wfValues.push({{value: Math.abs(val), itemStyle: {{color: '#ef4444'}}}});
    }}
  }});
  wfInvisible.push(0);
  wfValues.push({{value: endVal, itemStyle: {{color: '#8b5cf6'}}}});
  wfChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      axisPointer: {{type: 'shadow'}},
      formatter: function(params) {{
        const idx = params[0].dataIndex;
        const name = wfCategories[idx];
        if (idx === 0) return '<div style="font-weight:600">' + name + '</div><div>¥' + startVal.toFixed(1) + '万</div>';
        if (idx === wfCategories.length - 1) return '<div style="font-weight:600">' + name + '</div><div>¥' + endVal.toFixed(1) + '万</div>';
        const f = fi[idx - 1];
        const color = f.impact >= 0 ? '#10b981' : '#ef4444';
        const sign = f.impact >= 0 ? '+' : '';
        return '<div style="font-weight:600">' + name + '</div><div style="color:' + color + '">' + sign + '¥' + (f.impact/10000).toFixed(1) + '万 (' + (f.mom_pct > 0 ? '+' : '') + f.mom_pct + '%)</div>';
      }}
    }},
    grid: {{left: 80, right: 20, top: 20, bottom: 40}},
    xAxis: {{
      type: 'category',
      data: wfCategories,
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#94a3b8', fontSize: 11, interval: 0, rotate: 15}}
    }},
    yAxis: {{
      type: 'value', name: 'GMV(万)',
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8'}}
    }},
    series: [
      {{
        name: 'base', type: 'bar', stack: 'total',
        itemStyle: {{color: 'transparent'}},
        data: wfInvisible
      }},
      {{
        name: 'change', type: 'bar', stack: 'total',
        data: wfValues,
        label: {{
          show: true, position: 'top', color: '#f8fafc', fontSize: 11,
          formatter: function(p) {{
            const idx = p.dataIndex;
            if (idx === 0) return '¥' + startVal.toFixed(0) + '万';
            if (idx === wfCategories.length - 1) return '¥' + endVal.toFixed(0) + '万';
            const f = fi[idx - 1];
            const sign = f.impact >= 0 ? '+' : '';
            return sign + '¥' + (f.impact/10000).toFixed(1) + '万';
          }}
        }}
      }}
    ]
  }});

  // 1.7 Resource GMV Waterfall Chart (Screen 3)
  const rfwChart = echarts.init(document.getElementById('resource-gmv-waterfall-chart'));
  const rfwData = RAW_DATA.resource_gmv_waterfall || [];
  const rfwCategories = ['3月GMV'];
  const rfwInvisible = [0];
  const rfwValues = [{{value: Math.abs(rfwData.reduce((s,r) => s + r.m3_gmv, 0))/10000, itemStyle: {{color: '#3b82f6'}}}}];
  let rfwCumulative = rfwData.reduce((s,r) => s + r.m3_gmv, 0) / 10000;
  rfwData.forEach(r => {{
    const val = r.change / 10000;
    if (val >= 0) {{
      rfwInvisible.push(rfwCumulative);
      rfwValues.push({{value: val, itemStyle: {{color: '#10b981'}}, name: r.resource}});
      rfwCumulative += val;
    }} else {{
      rfwCumulative += val;
      rfwInvisible.push(rfwCumulative);
      rfwValues.push({{value: Math.abs(val), itemStyle: {{color: '#ef4444'}}, name: r.resource}});
    }}
    rfwCategories.push(r.resource);
  }});
  rfwInvisible.push(0);
  rfwValues.push({{value: Math.abs(rfwData.reduce((s,r) => s + r.m4_gmv, 0))/10000, itemStyle: {{color: '#8b5cf6'}}}});
  rfwCategories.push('4月GMV');
  rfwChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      axisPointer: {{type: 'shadow'}},
      formatter: function(params) {{
        const idx = params[0].dataIndex;
        const name = rfwCategories[idx];
        if (idx === 0) return '<div style="font-weight:600">3月总GMV</div><div>¥' + (rfwData.reduce((s,r) => s + r.m3_gmv, 0)/10000).toFixed(1) + '万</div>';
        if (idx === rfwCategories.length - 1) return '<div style="font-weight:600">4月总GMV</div><div>¥' + (rfwData.reduce((s,r) => s + r.m4_gmv, 0)/10000).toFixed(1) + '万</div>';
        const r = rfwData[idx - 1];
        const color = r.change >= 0 ? '#10b981' : '#ef4444';
        const sign = r.change >= 0 ? '+' : '';
        return '<div style="font-weight:600">' + r.resource + '</div><div style="color:' + color + '">' + sign + '¥' + (r.change/10000).toFixed(1) + '万</div>';
      }}
    }},
    grid: {{left: 80, right: 20, top: 20, bottom: 40}},
    xAxis: {{
      type: 'category',
      data: rfwCategories,
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#94a3b8', fontSize: 10, interval: 0, rotate: 20}}
    }},
    yAxis: {{
      type: 'value', name: 'GMV(万)',
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8'}}
    }},
    series: [
      {{
        name: 'base', type: 'bar', stack: 'total',
        itemStyle: {{color: 'transparent'}},
        data: rfwInvisible
      }},
      {{
        name: 'change', type: 'bar', stack: 'total',
        data: rfwValues,
        label: {{
          show: true, position: 'top', color: '#f8fafc', fontSize: 10,
          formatter: function(p) {{
            const idx = p.dataIndex;
            if (idx === 0) return '¥' + (rfwData.reduce((s,r) => s + r.m3_gmv, 0)/10000).toFixed(0) + '万';
            if (idx === rfwCategories.length - 1) return '¥' + (rfwData.reduce((s,r) => s + r.m4_gmv, 0)/10000).toFixed(0) + '万';
            const r = rfwData[idx - 1];
            const sign = r.change >= 0 ? '+' : '';
            return sign + '¥' + (r.change/10000).toFixed(1) + '万';
          }}
        }}
      }}
    ]
  }});

  // 2. Funnel Chart (split: front-end + back-end)
  const funnelChart = echarts.init(document.getElementById('funnel-chart'));
  const uj = {user_journey_json};
  const isMarch = currentMonth === 'march';
  const ujData = isMarch ? uj.march : uj.april;

  const frontItems = [
    {{name: '曝光 UV', key: 'exposure', rateKey: 'ctr', color: ['#1e3a5f','#3b82f6']}},
    {{name: '点击 UV', key: 'click', rateKey: 'lead_rate', color: ['#312e5a','#8b5cf6']}},
    {{name: '线索数', key: 'lead', rateKey: 'lead_gen_rate', color: ['#1e3a3a','#10b981']}}
  ];
  const backItems = [
    {{name: '线索数', key: 'lead', rateKey: 'friend_rate', color: ['#1e3a3a','#10b981']}},
    {{name: '好友', key: 'friend', rateKey: 'attend_rate', color: ['#3a1e1e','#f59e0b']}},
    {{name: '到课', key: 'attend', rateKey: 'complete_rate', color: ['#1e3a2f','#06b6d4']}},
    {{name: '完课', key: 'complete', rateKey: 'order_rate', color: ['#2a1e3a','#a855f7']}},
    {{name: '首单', key: 'order', rateKey: 'arpu', color: ['#3a2a1e','#ec4899']}}
  ];

  function makeFunnelLabel(item, p, isArpu) {{
    const rate = ujData[item.rateKey];
    const mom = uj.mom[item.rateKey];
    const momArrow = mom > 0 ? '↑' : '↓';
    const rateStr = isArpu ? '¥' + rate.toFixed(0) : rate.toFixed(1) + '%';
    return p.name + '\\n' + p.value.toLocaleString() + '\\n' + rateStr + ' ' + momArrow + Math.abs(mom).toFixed(1) + '%';
  }}

  function makeTooltip(item, p, isArpu) {{
    const rate = ujData[item.rateKey];
    const mom = uj.mom[item.rateKey];
    const momArrow = mom > 0 ? '↑' : '↓';
    const momColor = mom > 0 ? '#10b981' : '#ef4444';
    const rateLabel = isArpu ? '客单价: ¥' + rate.toFixed(1) : '转化率: ' + rate.toFixed(2) + '%';
    return '<div style="font-weight:600;margin-bottom:4px">' + p.name + '</div>' +
           '<div>数值: ' + p.value.toLocaleString() + '</div>' +
           '<div>' + rateLabel + '</div>' +
           '<div style="color:' + momColor + '">环比: ' + momArrow + Math.abs(mom).toFixed(1) + '%' + '</div>';
  }}

  funnelChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'item',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      formatter: function(p) {{
        const idx = p.dataIndex;
        const seriesIdx = p.seriesIndex;
        const item = seriesIdx === 0 ? frontItems[idx] : backItems[idx];
        return makeTooltip(item, p, item.rateKey === 'arpu');
      }}
    }},
    series: [
      {{
        name: '前链路',
        type: 'funnel',
        top: '2%', height: '45%',
        left: '10%', width: '80%',
        minSize: '20%', maxSize: '100%',
        sort: 'descending', gap: 2,
        label: {{
          show: true, position: 'inside', color: '#fff', fontSize: 12,
          formatter: function(p) {{ return makeFunnelLabel(frontItems[p.dataIndex], p, false); }}
        }},
        itemStyle: {{
          borderColor: 'transparent',
          color: function(p) {{
            const c = frontItems[p.dataIndex].color;
            return new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:c[0]}},{{offset:1,color:c[1]}}]);
          }}
        }},
        data: frontItems.map(item => ({{name: item.name, value: ujData[item.key]}}))
      }},
      {{
        name: '后链路',
        type: 'funnel',
        top: '52%', height: '45%',
        left: '10%', width: '80%',
        minSize: '10%', maxSize: '60%',
        sort: 'descending', gap: 2,
        label: {{
          show: true, position: 'inside', color: '#fff', fontSize: 11,
          formatter: function(p) {{ return makeFunnelLabel(backItems[p.dataIndex], p, backItems[p.dataIndex].rateKey === 'arpu'); }}
        }},
        itemStyle: {{
          borderColor: 'transparent',
          color: function(p) {{
            const c = backItems[p.dataIndex].color;
            return new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:c[0]}},{{offset:1,color:c[1]}}]);
          }}
        }},
        data: backItems.map(item => ({{name: item.name, value: ujData[item.key]}}))
      }}
    ]
  }});

  // 3. Stage Compare Chart
  const scChart = echarts.init(document.getElementById('stage-compare-chart'));
  const stages = ['CTR', '领课转化率', '好友率', '到课率', '完课率', '首单转化率'];
  const marchRates = [2.1, 6.7, 69.78, 97.12, 75.61, 14.93];
  const aprilRates = [1.27, 5.8, 69.74, 89.12, 76.15, 14.91];
  scChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}}
    }},
    legend: {{data: ['3月', '4月'], bottom: 0, textStyle: {{color: '#94a3b8'}}}},
    grid: {{left: 80, right: 20, top: 20, bottom: 40}},
    xAxis: {{
      type: 'value',
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8', formatter: '{{value}}%'}}
    }},
    yAxis: {{
      type: 'category',
      data: stages,
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#f8fafc', fontSize: 13}}
    }},
    series: [
      {{name: '3月', type: 'bar', data: marchRates, itemStyle: {{color: 'rgba(59,130,246,0.5)', borderRadius: [4,0,0,4]}}, barHeight: 14}},
      {{name: '4月', type: 'bar', data: aprilRates, itemStyle: {{color: '#3b82f6', borderRadius: [0,4,4,0]}}, barHeight: 14}}
    ]
  }});

  // 3.5 GMV & LTV Compare Chart
  const glChart = echarts.init(document.getElementById('gmv-ltv-compare-chart'));
  glChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}}
    }},
    legend: {{data: ['GMV(万)', '客单价(LTV)'], bottom: 0, textStyle: {{color: '#94a3b8', fontSize: 11}}}},
    grid: {{left: 50, right: 50, top: 20, bottom: 30}},
    xAxis: {{
      type: 'category',
      data: ['3月', '4月'],
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#f8fafc'}}
    }},
    yAxis: [
      {{type: 'value', name: 'GMV(万)', position: 'left', axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}}, splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}}, axisLabel: {{color: '#94a3b8'}}}},
      {{type: 'value', name: 'LTV(元)', position: 'right', axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}}, splitLine: {{show: false}}, axisLabel: {{color: '#94a3b8'}}}}
    ],
    series: [
      {{name: 'GMV(万)', type: 'bar', data: [ujLev.march.gmv/10000, ujLev.april.gmv/10000], yAxisIndex: 0, itemStyle: {{color: 'rgba(59,130,246,0.6)', borderRadius: [4,4,0,0]}}}},
      {{name: '客单价(LTV)', type: 'line', data: [ujLev.march.price_per_order, ujLev.april.price_per_order], yAxisIndex: 1, symbol: 'circle', symbolSize: 8, lineStyle: {{color: '#10b981', width: 2}}, itemStyle: {{color: '#10b981'}}}}
    ]
  }});

  // 4. Efficiency Matrix
  const emChart = echarts.init(document.getElementById('efficiency-matrix-chart'));
  const emData = RAW_DATA.resource_efficiency_matrix.map(r => ({{
    name: r.resource,
    value: [parseFloat(r.lead_gen_rate.toFixed(2)), parseFloat(r.arpu.toFixed(0))],
    leads: r.leads,
    gmv: r.gmv
  }}));
  const xVals = emData.map(d => d.value[0]).sort((a,b)=>a-b);
  const yVals = emData.map(d => d.value[1]).sort((a,b)=>a-b);
  const xMedian = xVals[Math.floor(xVals.length/2)];
  const yMedian = yVals[Math.floor(yVals.length/2)];
  emChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      formatter: function(p) {{
        return '<div style="font-weight:600">' + p.name + '</div>' +
               '<div>线索数: ' + (p.data.leads?.toLocaleString()||'') + '</div>' +
               '<div>GMV: ¥' + ((p.data.gmv||0)/10000).toFixed(1) + '万</div>' +
               '<div>线索生成率: ' + p.value[0] + '%</div>' +
               '<div>单线索产出: ¥' + p.value[1] + '</div>';
      }}
    }},
    grid: {{left: 60, right: 60, top: 40, bottom: 40}},
    xAxis: {{
      type: 'log', logBase: 10, min: 0.005, name: '线索生成率(%)',
      nameTextStyle: {{color: '#94a3b8'}},
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8', formatter: function(v) {{ return v >= 1 ? v.toFixed(0) + '%' : v.toFixed(2) + '%'; }}}}
    }},
    yAxis: {{
      type: 'value', name: '单线索产出(元)',
      nameTextStyle: {{color: '#94a3b8'}},
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8'}}
    }},
    series: [{{
      type: 'scatter',
      data: emData,
      symbolSize: function(p, params) {{
        const gmv = params.data.gmv || 0;
        return Math.max(12, Math.min(40, gmv / 30000));
      }},
      itemStyle: {{
        color: function(p) {{
          const x = p.value[0], y = p.value[1];
          if (x >= xMedian && y >= yMedian) return '#10b981';
          if (x >= xMedian && y < yMedian) return '#f59e0b';
          if (x < xMedian && y >= yMedian) return '#3b82f6';
          return '#64748b';
        }},
        borderColor: '#fff', borderWidth: 1,
        cursor: 'pointer'
      }},
      emphasis: {{
        scale: 1.5,
        itemStyle: {{ shadowBlur: 12, shadowColor: 'rgba(255,255,255,0.6)' }}
      }},
      label: {{show: true, position: 'top', color: '#94a3b8', fontSize: 11, formatter: '{{b}}'}},
      markArea: {{
        silent: true,
        data: [
          [{{name: '明星资源位', xAxis: xMedian, yAxis: yMedian, itemStyle: {{color: 'rgba(16,185,129,0.06)'}}, label: {{position: 'insideTopRight', color: '#10b981', fontSize: 14, fontWeight: 'bold'}}}}, {{xAxis: 'max', yAxis: 'max'}}],
          [{{name: '流量粗放', xAxis: xMedian, yAxis: 'min', itemStyle: {{color: 'rgba(245,158,11,0.06)'}}, label: {{position: 'insideBottomRight', color: '#f59e0b', fontSize: 14, fontWeight: 'bold'}}}}, {{xAxis: 'max', yAxis: yMedian}}],
          [{{name: '精准入口', xAxis: 'min', yAxis: yMedian, itemStyle: {{color: 'rgba(59,130,246,0.06)'}}, label: {{position: 'insideTopLeft', color: '#3b82f6', fontSize: 14, fontWeight: 'bold'}}}}, {{xAxis: xMedian, yAxis: 'max'}}],
          [{{name: '观察淘汰', xAxis: 'min', yAxis: 'min', itemStyle: {{color: 'rgba(148,163,184,0.06)'}}, label: {{position: 'insideBottomLeft', color: '#64748b', fontSize: 14, fontWeight: 'bold'}}}}, {{xAxis: xMedian, yAxis: yMedian}}]
        ]
      }},
      markLine: {{
        silent: true,
        lineStyle: {{color: 'rgba(148,163,184,0.3)', type: 'dashed'}},
        data: [{{xAxis: xMedian}}, {{yAxis: yMedian}}]
      }}
    }}]
  }});

  // Efficiency Matrix click → drill-down to resource price band
  const rpbData = RAW_DATA.resource_price_band || {{}};
  const pbColors = ['#3b82f6', '#8b5cf6', '#06b6d4', '#64748b'];
  const globalPbData = RAW_DATA.price_band_distribution;
  function updatePriceBandChart(resourceName) {{
    const titleEl = document.getElementById('price-band-title');
    const resetEl = document.getElementById('price-band-reset');
    const hintEl = document.getElementById('price-band-hint');
    let marchPb, aprilPb;
    if (resourceName && rpbData[resourceName]) {{
      titleEl.textContent = resourceName + ' · 价格带结构';
      resetEl.style.display = 'inline';
      if (hintEl) hintEl.style.display = 'inline';
      const resPb = rpbData[resourceName];
      const pbKeys = Object.keys(resPb);
      marchPb = pbKeys.filter(k => resPb[k].march_leads > 0).map((k,i) => ({{
        value: resPb[k].march_leads, name: k, itemStyle: {{color: pbColors[i % pbColors.length]}}
      }}));
      aprilPb = pbKeys.filter(k => resPb[k].april_leads > 0).map((k,i) => ({{
        value: resPb[k].april_leads, name: k, itemStyle: {{color: pbColors[i % pbColors.length]}}
      }}));
    }} else {{
      titleEl.textContent = '价格带结构';
      resetEl.style.display = 'none';
      if (hintEl) hintEl.style.display = 'none';
      marchPb = globalPbData.filter(d => d.march_leads > 0).map((d,i) => ({{
        value: d.march_leads, name: d.price_band, itemStyle: {{color: pbColors[i % pbColors.length]}}
      }}));
      aprilPb = globalPbData.filter(d => d.april_leads > 0).map((d,i) => ({{
        value: d.april_leads, name: d.price_band, itemStyle: {{color: pbColors[i % pbColors.length]}}
      }}));
    }}
    pbChart.setOption({{
      series: [
        {{data: marchPb}},
        {{data: aprilPb}}
      ]
    }});
  }}
  function highlightTableRow(name) {{
    document.querySelectorAll('.data-table tbody tr').forEach(tr => {{
      tr.classList.toggle('highlight-row', tr.dataset.resource === name);
    }});
  }}
  function clearTableHighlight() {{
    document.querySelectorAll('.data-table tbody tr').forEach(tr => tr.classList.remove('highlight-row'));
  }}
  function resetAllHighlights() {{
    selectedResource = null;
    updatePriceBandChart(null);
    updateSunburstChart(null);
    updateMauChart(null);
    emChart.setOption({{ series: [{{ data: emData }}] }});
    gmChart.setOption({{ series: [{{ data: gmData }}] }});
    clearTableHighlight();
  }}
  window.resetPriceBand = function() {{ resetAllHighlights(); }};

  // Category price band drilldown
  let selectedCategory = null;
  const cpbChart = echarts.init(document.getElementById('category-price-band-chart'));
  const catPriceBandData = RAW_DATA.category_price_band || [];
  function updateCategoryPriceBandChart(categoryName) {{
    const drilldownEl = document.getElementById('category-price-band-drilldown');
    const nameEl = document.getElementById('selected-category-name');
    if (!categoryName) {{
      drilldownEl.style.display = 'none';
      cpbChart.clear();
      return;
    }}
    drilldownEl.style.display = 'block';
    nameEl.textContent = categoryName;
    const monthKey = currentMonth === 'march' ? 'march' : (currentMonth === 'april' ? 'april' : 'april');
    const cpb = catPriceBandData.find(d => d.category === categoryName && d.month === monthKey);
    const cpbCompare = currentMonth === 'compare' ? catPriceBandData.find(d => d.category === categoryName && d.month === 'march') : null;
    if (!cpb) return;
    const pbNames = ['0元', '1元', '3元', '9元', '其他'];
    const pbColors = {{'0元': '#3b82f6', '1元': '#8b5cf6', '3元': '#06b6d4', '9元': '#f59e0b', '其他': '#64748b'}};
    const series = [];
    if (cpbCompare) {{
      series.push({{
        name: '3月',
        type: 'pie',
        radius: ['40%', '55%'],
        center: ['30%', '50%'],
        data: pbNames.map(pb => {{
          const item = cpbCompare.price_bands.find(p => p.price_band === pb);
          return {{ value: item ? item.leads : 0, name: pb }};
        }}),
        label: {{ formatter: '{{b}} {{d}}%', color: '#94a3b8', fontSize: 11 }},
        itemStyle: {{ color: (p) => pbColors[p.name] || '#64748b' }}
      }});
      series.push({{
        name: '4月',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['70%', '50%'],
        data: pbNames.map(pb => {{
          const item = cpb.price_bands.find(p => p.price_band === pb);
          return {{ value: item ? item.leads : 0, name: pb }};
        }}),
        label: {{ formatter: '{{b}} {{d}}%', color: '#f8fafc', fontSize: 11 }},
        itemStyle: {{ color: (p) => pbColors[p.name] || '#64748b' }}
      }});
    }} else {{
      series.push({{
        name: '价格带',
        type: 'pie',
        radius: ['40%', '70%'],
        data: pbNames.map(pb => {{
          const item = cpb.price_bands.find(p => p.price_band === pb);
          return {{ value: item ? item.leads : 0, name: pb }};
        }}),
        label: {{ formatter: '{{b}} {{d}}%', color: '#f8fafc', fontSize: 11 }},
        itemStyle: {{ color: (p) => pbColors[p.name] || '#64748b' }}
      }});
    }}
    cpbChart.setOption({{
      backgroundColor: 'transparent',
      tooltip: {{ trigger: 'item', backgroundColor: '#334155', borderColor: 'rgba(148,163,184,0.2)', textStyle: {{ color: '#f8fafc' }} }},
      legend: {{ bottom: 0, textStyle: {{ color: '#94a3b8', fontSize: 11 }} }},
      series: series
    }}, true);
    // Build detail table
    const tableEl = document.getElementById('category-price-band-table');
    let tableHtml = '<table class="data-table"><thead><tr><th>价格带</th><th>线索数</th><th>GMV</th><th>转化率</th><th>单线索产出</th></tr></thead><tbody>';
    pbNames.forEach(pb => {{
      const item = cpb.price_bands.find(p => p.price_band === pb);
      if (item) {{
        tableHtml += `<tr><td>{{pb}}</td><td>{{item.leads}}</td><td>¥{{(item.gmv/10000).toFixed(1)}}万</td><td>{{(item.cvr*100).toFixed(2)}}%</td><td>¥{{item.ltv.toFixed(1)}}</td></tr>`;
      }}
    }});
    tableHtml += '</tbody></table>';
    tableEl.innerHTML = tableHtml;
  }}

  // Category row click
  document.querySelectorAll('#category-detail-table tbody tr').forEach(tr => {{
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', function(e) {{
      e.stopPropagation();
      const cat = this.dataset.category;
      if (selectedCategory === cat) {{
        selectedCategory = null;
        this.classList.remove('highlight-row');
        updateCategoryPriceBandChart(null);
        resetAllHighlights();
      }} else {{
        document.querySelectorAll('#category-detail-table tbody tr').forEach(r => r.classList.remove('highlight-row'));
        this.classList.add('highlight-row');
        selectedCategory = cat;
        updateCategoryPriceBandChart(cat);
        // Linkage: highlight resources in efficiency matrix where this category has top3
        const catData = (RAW_DATA.category_detail || []).find(d => d.category === cat);
        if (catData && emChart) {{
          const monthIdx = currentMonth === 'march' ? 0 : 1;
          const d = catData.data[monthIdx] || catData.data[0];
          const topResources = new Set([
            ...(d.gmv_top3 || []).map(t => t.resource),
            ...(d.leads_top3 || []).map(t => t.resource),
            ...(d.cvr_top3 || []).map(t => t.resource)
          ]);
          emChart.setOption({{
            series: [{{
              data: emData.map(item => ({{
                ...item,
                itemStyle: {{ opacity: topResources.has(item.name) ? 1 : 0.2 }}
              }}))
            }}]
          }});
        }}
      }}
    }});
  }});

  let selectedResource = null;
  const getEmColor = (x, y) => {{
    if (x >= xMedian && y >= yMedian) return '#10b981';
    if (x >= xMedian && y < yMedian) return '#f59e0b';
    if (x < xMedian && y >= yMedian) return '#3b82f6';
    return '#64748b';
  }};
  const getGmColor = (x, y) => {{
    if (x >= 0 && y >= 0) return '#10b981';
    if (x < 0 && y >= 0) return '#3b82f6';
    if (x >= 0 && y < 0) return '#f59e0b';
    return '#ef4444';
  }};
  emChart.on('click', function(params) {{
    const name = params?.data?.name || params?.name;
    if (params?.componentType === 'series' && name && rpbData[name]) {{
      if (selectedResource === name) {{ resetAllHighlights(); return; }}
      selectedResource = name;
      updatePriceBandChart(name);
      updateSunburstChart(name);
      updateMauChart(name);
      // Efficiency matrix: highlight selected, dim others
      emChart.setOption({{
        series: [{{
          data: emData.map(d => ({{
            name: d.name, value: d.value, leads: d.leads, gmv: d.gmv,
            itemStyle: d.name === name ? {{
              color: getEmColor(d.value[0], d.value[1]),
              shadowBlur: 16, shadowColor: 'rgba(255,255,255,0.7)',
              borderColor: '#fff', borderWidth: 2, opacity: 1
            }} : {{
              color: 'rgba(100,116,139,0.5)',
              opacity: 0.5,
              borderColor: 'transparent'
            }}
          }}))
        }}]
      }});
      // Growth matrix: same highlight
      gmChart.setOption({{
        series: [{{
          data: gmData.map(d => ({{
            name: d.name, value: d.value, gmv: d.gmv,
            itemStyle: d.name === name ? {{
              color: getGmColor(d.value[0], d.value[1]),
              shadowBlur: 16, shadowColor: 'rgba(255,255,255,0.7)',
              borderColor: '#fff', borderWidth: 2, opacity: 1
            }} : {{
              color: 'rgba(100,116,139,0.5)',
              opacity: 0.5,
              borderColor: 'transparent'
            }}
          }}))
        }}]
      }});
      // TOP10 table: highlight row
      highlightTableRow(name);
    }} else {{
      // Clicked empty area: reset
      resetAllHighlights();
    }}
  }});
  // Also reset when clicking blank canvas (zrender layer)
  emChart.getZr().on('click', function(zrParams) {{
    if (!zrParams.target) {{
      resetAllHighlights();
    }}
  }});

  // 5. Growth Matrix
  const gmChart = echarts.init(document.getElementById('growth-matrix-chart'));
  const gmData = RAW_DATA.resource_growth_matrix.map(r => ({{
    name: r.resource,
    value: [parseFloat(r.leads_mom.toFixed(1)), parseFloat(r.order_rate_mom.toFixed(1))],
    gmv: r.gmv
  }}));
  gmChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      formatter: function(p) {{
        return '<div style="font-weight:600">' + p.name + '</div>' +
               '<div>线索环比: ' + p.value[0] + '%</div>' +
               '<div>首单转化率环比: ' + p.value[1] + '%</div>' +
               '<div>4月GMV: ¥' + ((p.data.gmv||0)/10000).toFixed(1) + '万</div>';
      }}
    }},
    grid: {{left: 60, right: 40, top: 40, bottom: 40}},
    xAxis: {{
      type: 'value', name: '线索数环比(%)',
      nameTextStyle: {{color: '#94a3b8'}},
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8'}}
    }},
    yAxis: {{
      type: 'value', name: '首单转化率环比(%):',
      nameTextStyle: {{color: '#94a3b8'}},
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
      axisLabel: {{color: '#94a3b8'}}
    }},
    series: [{{
      type: 'scatter',
      data: gmData,
      symbolSize: function(p, params) {{
        const gmv = params.data.gmv || 0;
        return Math.max(10, Math.min(35, gmv / 35000));
      }},
      itemStyle: {{
        color: function(p) {{
          const x = p.value[0], y = p.value[1];
          if (x >= 0 && y >= 0) return '#10b981';
          if (x < 0 && y >= 0) return '#3b82f6';
          if (x >= 0 && y < 0) return '#f59e0b';
          return '#ef4444';
        }},
        borderColor: '#fff', borderWidth: 1,
        cursor: 'pointer'
      }},
      emphasis: {{
        scale: 1.5,
        itemStyle: {{ shadowBlur: 12, shadowColor: 'rgba(255,255,255,0.6)' }}
      }},
      label: {{show: true, position: 'top', color: '#94a3b8', fontSize: 10, formatter: '{{b}}'}},
      markLine: {{
        silent: true,
        lineStyle: {{color: 'rgba(148,163,184,0.3)', type: 'dashed'}},
        data: [{{xAxis: 0}}, {{yAxis: 0}}]
      }}
    }}]
  }});

  // 6. Price Band Donut
  const pbChart = echarts.init(document.getElementById('price-band-chart'));
  const pbData = RAW_DATA.price_band_distribution;
  const marchPb = pbData.filter(d => d.march_leads > 0).map((d,i) => ({{value: d.march_leads, name: d.price_band, itemStyle: {{color: pbColors[i % pbColors.length]}}}}));
  const aprilPb = pbData.filter(d => d.april_leads > 0).map((d,i) => ({{value: d.april_leads, name: d.price_band, itemStyle: {{color: pbColors[i % pbColors.length]}}}}));
  pbChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      formatter: '{{b}}: {{c}} ({{d}}%)'
    }},
    legend: {{bottom: 0, textStyle: {{color: '#94a3b8', fontSize: 11}}, itemWidth: 10, itemHeight: 10}},
    series: [
      {{
        name: '3月', type: 'pie',
        radius: ['45%', '65%'], center: ['30%', '45%'],
        label: {{show: true, color: '#94a3b8', fontSize: 11, formatter: '{{b}} {{d}}%'}},
        labelLine: {{lineStyle: {{color: 'rgba(148,163,184,0.3)'}}}},
        data: marchPb
      }},
      {{
        name: '4月', type: 'pie',
        radius: ['45%', '65%'], center: ['70%', '45%'],
        label: {{show: true, color: '#94a3b8', fontSize: 11, formatter: '{{b}} {{d}}%'}},
        labelLine: {{lineStyle: {{color: 'rgba(148,163,184,0.3)'}}}},
        data: aprilPb
      }}
    ]
  }});

  // 7. Sunburst
  const sbChart = echarts.init(document.getElementById('sunburst-chart'));
  const sbGlobalData = {sunburst_global_json};
  function updateSunburstChart(resourceName) {{
    const rpbtData = RAW_DATA.resource_price_band_type || {{}};
    const pbColors = {{'0元': '#3b82f6', '1元': '#8b5cf6', '3元': '#06b6d4', '9元': '#f59e0b', '其他': '#64748b'}};
    const catColors = {{'正式品': '#3b82f6', '孵化品': '#10b981', '未分类': '#64748b'}};
    let data;
    if (resourceName && rpbtData[resourceName]) {{
      const resData = rpbtData[resourceName];
      data = [];
      for (const pb of ['0元', '1元', '3元', '9元', '其他']) {{
        if (!resData[pb]) continue;
        const children = [];
        for (const ct of ['正式品', '孵化品', '未分类']) {{
          const val = resData[pb][ct]?.april_leads || 0;
          if (val > 0) children.push({{name: ct, value: val, itemStyle: {{color: catColors[ct] || '#64748b'}}}});
        }}
        if (children.length > 0) data.push({{name: pb, itemStyle: {{color: pbColors[pb] || '#64748b'}}, children: children}});
      }}
    }} else {{
      data = sbGlobalData;
    }}
    sbChart.setOption({{ series: [{{ data: data }}] }});
  }}
  sbChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}}
    }},
    series: [{{
      type: 'sunburst',
      radius: ['20%', '70%'],
      data: sbGlobalData,
      label: {{color: '#f8fafc', fontSize: 11}},
      itemStyle: {{borderColor: '#1e293b', borderWidth: 2}}
    }}]
  }});

  // 8. User Level Efficiency Combo Chart
  const mauChart = echarts.init(document.getElementById('mau-chart'));
  const uleData = RAW_DATA.user_level_efficiency || [];
  const uleLevels = uleData.map(d => 'L' + d.level);
  const uleMarchLTV = uleData.map(d => d.march_ltv);
  const uleAprilLTV = uleData.map(d => d.april_ltv);
  const uleMarchCVR = uleData.map(d => d.march_cvr);
  const uleAprilCVR = uleData.map(d => d.april_cvr);
  function updateMauChart(resourceName) {{
    const rulData = RAW_DATA.resource_user_level || {{}};
    let mLTV, aLTV, mCVR, aCVR;
    if (resourceName && rulData[resourceName]) {{
      const resLevels = rulData[resourceName];
      const levelMap = {{}};
      for (const item of resLevels) levelMap['L' + item.level] = item;
      mLTV = uleLevels.map(l => levelMap[l]?.march_ltv || 0);
      aLTV = uleLevels.map(l => levelMap[l]?.april_ltv || 0);
      mCVR = uleLevels.map(l => levelMap[l]?.march_cvr || 0);
      aCVR = uleLevels.map(l => levelMap[l]?.april_cvr || 0);
    }} else {{
      mLTV = uleMarchLTV; aLTV = uleAprilLTV; mCVR = uleMarchCVR; aCVR = uleAprilCVR;
    }}
    mauChart.setOption({{
      series: [
        {{data: mLTV}}, {{data: aLTV}}, {{data: mCVR}}, {{data: aCVR}}
      ]
    }});
  }}
  mauChart.setOption({{
    backgroundColor: 'transparent',
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#334155',
      borderColor: 'rgba(148,163,184,0.2)',
      textStyle: {{color: '#f8fafc'}},
      axisPointer: {{type: 'cross', crossStyle: {{color: 'rgba(148,163,184,0.3)'}}}}
    }},
    legend: {{top: 0, textStyle: {{color: '#94a3b8', fontSize: 11}}, itemWidth: 10, itemHeight: 10}},
    grid: {{left: 60, right: 60, top: 40, bottom: 30}},
    xAxis: {{
      type: 'category',
      data: uleLevels,
      axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
      axisLabel: {{color: '#94a3b8', fontSize: 12}},
      axisTick: {{alignWithLabel: true}}
    }},
    yAxis: [
      {{
        type: 'value', name: 'LTV(元)',
        nameTextStyle: {{color: '#94a3b8'}},
        axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
        splitLine: {{lineStyle: {{color: 'rgba(148,163,184,0.1)', type: 'dashed'}}}},
        axisLabel: {{color: '#94a3b8'}}
      }},
      {{
        type: 'value', name: '首单转化率(%)',
        nameTextStyle: {{color: '#94a3b8'}},
        axisLine: {{lineStyle: {{color: 'rgba(148,163,184,0.2)'}}}},
        splitLine: {{show: false}},
        axisLabel: {{color: '#94a3b8', formatter: '{{value}}%'}}
      }}
    ],
    series: [
      {{
        name: '3月LTV', type: 'bar',
        data: uleMarchLTV,
        itemStyle: {{color: '#3b82f6', borderRadius: [4,4,0,0]}},
        barGap: '20%'
      }},
      {{
        name: '4月LTV', type: 'bar',
        data: uleAprilLTV,
        itemStyle: {{color: '#8b5cf6', borderRadius: [4,4,0,0]}}
      }},
      {{
        name: '3月转化率', type: 'line', yAxisIndex: 1,
        data: uleMarchCVR,
        symbol: 'circle', symbolSize: 6,
        lineStyle: {{color: '#10b981', width: 2}},
        itemStyle: {{color: '#10b981'}},
        label: {{show: true, position: 'top', color: '#10b981', fontSize: 10, formatter: '{{c}}%'}}
      }},
      {{
        name: '4月转化率', type: 'line', yAxisIndex: 1,
        data: uleAprilCVR,
        symbol: 'circle', symbolSize: 6,
        lineStyle: {{color: '#f59e0b', width: 2, type: 'dashed'}},
        itemStyle: {{color: '#f59e0b'}},
        label: {{show: true, position: 'bottom', color: '#f59e0b', fontSize: 10, formatter: '{{c}}%'}}
      }}
    ]
  }});
}}

function exportReport(btn) {{
  btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px">hourglass_top</span>生成中...';
  setTimeout(() => {{
    const blob = new Blob([document.documentElement.outerHTML], {{type: 'text/html'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'APP商业化决策看板_2026年3-4月.html';
    a.click();
    URL.revokeObjectURL(url);
    btn.innerHTML = '<span class="material-symbols-outlined" style="font-size:16px">download</span>导出 HTML 月报';
  }}, 500);
}}

window.addEventListener('load', () => {{
  renderCharts();
  document.querySelectorAll('.animate-in').forEach((el, i) => {{
    el.style.animationDelay = (i * 80) + 'ms';
    // fallback: ensure visibility even if animation is disabled
    setTimeout(() => {{ el.style.opacity = '1'; }}, 800 + i * 80);
  }});
}});

window.addEventListener('resize', () => {{
  ['conversion-change-chart','backend-efficiency-chart','leverage-compare-chart','gmv-waterfall-chart','resource-gmv-waterfall-chart','funnel-chart','stage-compare-chart','gmv-ltv-compare-chart','efficiency-matrix-chart','growth-matrix-chart','price-band-chart','sunburst-chart','mau-chart','category-price-band-chart'].forEach(id => {{
    const chart = echarts.getInstanceByDom(document.getElementById(id));
    if (chart) chart.resize();
  }});
}});
</script>

<div style="max-width:1200px;margin:0 auto;padding:20px 20px 40px;color:var(--text-tertiary);font-size:12px;line-height:1.8">
  <div style="border-top:1px solid var(--border-subtle);padding-top:16px;margin-bottom:12px"></div>
  <strong style="color:var(--text-secondary)">指标口径说明：</strong>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;margin-top:8px">
    <div>• CTR = 点击UV / 曝光UV</div>
    <div>• CTCVR（点击转化率/领课转化率）= 线索数 / 点击UV</div>
    <div>• 线索生成率 = 线索数 / 曝光UV</div>
    <div>• 好友率 = 加好友数 / 线索数</div>
    <div>• 到课率 = 到课数 / 加好友数</div>
    <div>• 完课率 = 完课数 / 到课数</div>
    <div>• 完课→首单转化率 = 首单数 / 完课数</div>
    <div>• 线索→首单转化率 = 首单数 / 线索数</div>
    <div>• 单线索产出(LTV) = GMV / 线索数</div>
    <div>• 单曝光产出 = GMV / 曝光UV</div>
    <div>• 单点击产出 = GMV / 点击UV</div>
  </div>
</div>

</body>
</html>
'''

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Done! Written to {OUTPUT_PATH}")
print(f"File size: {len(html_content):,} bytes")
