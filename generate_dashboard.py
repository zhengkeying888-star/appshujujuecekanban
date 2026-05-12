import json

with open('/Users/zhengkeying/agent teams作业/data_analysis_output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Helpers

def fmt(n, t='int'):
    if t == 'int':
        return f"{int(n):,}"
    if t == 'pct':
        return f"{n*100:.2f}%"
    if t == 'pct1':
        return f"{n*100:.1f}%"
    if t == 'wan':
        return f"¥{n/10000:.1f}万"
    if t == 'float':
        return f"{n:.2f}"
    return str(n)

def mom_color(v):
    if v > 0:
        return 'text-secondary'
    elif v < 0:
        return 'text-error'
    return 'text-on-surface-variant'

def mom_arrow(v):
    if v > 0:
        return 'arrow_upward'
    elif v < 0:
        return 'arrow_downward'
    return 'horizontal_rule'

def status_badge(status):
    colors = {
        '增长': 'bg-green-100 text-green-800',
        '衰退': 'bg-red-100 text-red-800',
        '新出现': 'bg-blue-100 text-blue-800',
        '已下架': 'bg-gray-200 text-gray-600',
        '稳定': 'bg-yellow-100 text-yellow-800'
    }
    return colors.get(status, 'bg-gray-100 text-gray-800')

def priority_badge(p):
    colors = {'P0': 'bg-red-600 text-white', 'P1': 'bg-orange-500 text-white', 'P2': 'bg-blue-500 text-white'}
    return colors.get(p, 'bg-gray-500 text-white')

def cat_type_badge(t):
    colors = {'正式品': 'bg-blue-100 text-blue-800', '孵化品': 'bg-green-100 text-green-800'}
    return colors.get(t, 'bg-gray-100 text-gray-800')

# Build existing sections
res_rows = ""
for r in data['resource_efficiency']:
    res = r['resource']
    m3 = r['2026-03']
    m4 = r['2026-04']
    mom = r['环比']
    c = mom_color(mom['线索数']['value'])
    a = mom_arrow(mom['线索数']['value'])
    res_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3 font-medium">{res}</td>
      <td class="py-2 px-3 text-right col-march">{fmt(m3['线索数'])}</td>
      <td class="py-2 px-3 text-right col-march">{fmt(m3['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right col-march">{fmt(m3['首单流水'], 'wan')}</td>
      <td class="py-2 px-3 text-right font-semibold text-primary col-april">{fmt(m4['线索数'])}</td>
      <td class="py-2 px-3 text-right font-semibold col-april">{fmt(m4['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right col-april">{fmt(m4['首单流水'], 'wan')}</td>
      <td class="py-2 px-3 text-right {c} col-compare"><span class="material-symbols-outlined text-[14px] align-middle">{a}</span> {mom['线索数']['value']:.1f}%</td>
      <td class="py-2 px-3 text-right {mom_color(mom['转化率']['value'])} col-compare">{mom['转化率']['value']:.1f}%</td>
      <td class="py-2 px-3 text-right {mom_color(mom['首单流水']['value'])} col-compare">{mom['首单流水']['value']:.1f}%</td>
    </tr>"""

sp_rows = ""
for sp in data['selling_point_analysis'][:20]:
    badge = status_badge(sp['status'])
    sp_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3 font-medium">{sp['keyword']}</td>
      <td class="py-2 px-3 text-right col-march">{fmt(sp['2026-03']['线索数'])}</td>
      <td class="py-2 px-3 text-right col-march">{fmt(sp['2026-03']['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right font-semibold text-primary col-april">{fmt(sp['2026-04']['线索数'])}</td>
      <td class="py-2 px-3 text-right font-semibold col-april">{fmt(sp['2026-04']['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right {mom_color(sp['环比']['线索数']['value'])} col-compare">{sp['环比']['线索数']['value']:.1f}%</td>
      <td class="py-2 px-3 col-compare"><span class="px-2 py-0.5 rounded text-xs font-semibold {badge}">{sp['status']}</span></td>
    </tr>"""

ba_rows = ""
for ba in data['best_audience'][:15]:
    ba_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3">{ba['category']}</td>
      <td class="py-2 px-3">{ba['price']}</td>
      <td class="py-2 px-3 font-medium text-primary">{ba['best_audience']}</td>
      <td class="py-2 px-3 text-right">{fmt(ba['leads'])}</td>
      <td class="py-2 px-3 text-right font-semibold text-secondary">{fmt(ba['cvr'], 'pct1')}</td>
    </tr>"""

cp_rows = ""
for cp in data['category_price_matrix'][:20]:
    cp_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3">{cp['category']}</td>
      <td class="py-2 px-3">{cp['price']}</td>
      <td class="py-2 px-3 text-right">{fmt(cp['线索数'])}</td>
      <td class="py-2 px-3 text-right">{fmt(cp['首单数'])}</td>
      <td class="py-2 px-3 text-right">{fmt(cp['首单流水'], 'wan')}</td>
      <td class="py-2 px-3 text-right font-semibold">{fmt(cp['转化率'], 'pct1')}</td>
    </tr>"""

fd_rows = ""
for fd in data['four_dim_cross'][:15]:
    fd_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3">{fd['category']}</td>
      <td class="py-2 px-3">{fd['price']}</td>
      <td class="py-2 px-3">{fd['audience']}</td>
      <td class="py-2 px-3 font-medium">{fd['selling_point']}</td>
      <td class="py-2 px-3 text-right">{fmt(fd['2026-04']['线索数'])}</td>
      <td class="py-2 px-3 text-right">{fmt(fd['2026-04']['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right {mom_color(fd['环比']['线索数']['value'])}">{fd['环比']['线索数']['value']:.1f}%</td>
    </tr>"""

action_cards = ""
for act in data['action_items']:
    badge = priority_badge(act['priority'])
    action_cards += f"""
    <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-4 flex flex-col gap-2 shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
      <div class="flex items-center gap-2">
        <span class="px-2 py-0.5 rounded text-xs font-bold {badge}">{act['priority']}</span>
        <span class="font-medium text-on-surface">{act['action']}</span>
      </div>
      <div class="text-helper text-on-surface-variant">依据：{act['basis']}</div>
    </div>"""

td_rows = ""
for td in data['threedim'][:20]:
    td_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3">{td['category']}</td>
      <td class="py-2 px-3">{td['price']}</td>
      <td class="py-2 px-3">{td['audience']}</td>
      <td class="py-2 px-3 text-right">{fmt(td['2026-04']['线索数'])}</td>
      <td class="py-2 px-3 text-right">{fmt(td['2026-04']['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right {mom_color(td['环比']['线索数']['value'])}">{td['环比']['线索数']['value']:.1f}%</td>
      <td class="py-2 px-3 text-right {mom_color(td['环比']['转化率']['value'])}">{td['环比']['转化率']['value']:.1f}%</td>
    </tr>"""

# NEW: Category traffic rows
ct_rows = ""
for ct in data['category_traffic'][:20]:
    type_badge = cat_type_badge(ct['type'])
    ct_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3">{ct['category']} <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold {type_badge}">{ct['type']}</span></td>
      <td class="py-2 px-3 text-right col-march">{fmt(ct['march']['leads'])}</td>
      <td class="py-2 px-3 text-right col-april">{fmt(ct['april']['leads'])}</td>
      <td class="py-2 px-3 text-right {mom_color(ct['mom']['leads'])} col-compare">{ct['mom']['leads']:.1f}%</td>
      <td class="py-2 px-3 text-right col-april">{fmt(ct['april']['cvr'], 'pct1')}</td>
      <td class="py-2 px-3 text-right {mom_color(ct['mom']['cvr'])} col-compare">{ct['mom']['cvr']:.1f}%</td>
      <td class="py-2 px-3 text-right col-april">{fmt(ct['april']['gmv'], 'wan')}</td>
      <td class="py-2 px-3 text-right {mom_color(ct['mom']['gmv'])} col-compare">{ct['mom']['gmv']:.1f}%</td>
    </tr>"""

# NEW: Recommendation rows
rec_rows = ""
for rec in data['resource_category_recommendations']:
    top = rec['top3']
    avoid = rec['avoid']
    top_cells = ""
    for i, t in enumerate(top):
        arrow = '↑' if t['mom_leads'] > 0 else ('↓' if t['mom_leads'] < 0 else '—')
        color = 'text-secondary' if t['mom_leads'] > 0 else ('text-error' if t['mom_leads'] < 0 else 'text-on-surface-variant')
        top_cells += f"""
        <td class="py-2 px-3">
          <div class="font-medium">{t['category']}</div>
          <div class="text-xs text-on-surface-variant">线索{fmt(t['leads'])} | CVR{fmt(t['cvr'], 'pct1')} | 得分{t['score']:.1f} <span class="{color}">{arrow}{abs(t['mom_leads']):.1f}%</span></div>
        </td>"""
    if len(top) < 3:
        for _ in range(3 - len(top)):
            top_cells += '<td class="py-2 px-3 text-on-surface-variant">—</td>'
    avoid_cell = f"""
    <td class="py-2 px-3 text-error">
      <div class="font-medium">{avoid['category']}</div>
      <div class="text-xs">线索{fmt(avoid['leads'])} | CVR{fmt(avoid['cvr'], 'pct1')} | 得分{avoid['score']:.1f}</div>
    </td>""" if avoid else '<td class="py-2 px-3 text-on-surface-variant">—</td>'
    rec_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3 font-medium">{rec['resource']}</td>
      {top_cells}
      {avoid_cell}
    </tr>"""

# NEW: Per-resource detail cards
rc_detail_cards = ""
for rcd in data['resource_category_detail']:
    res = rcd['resource']
    cats_html = ""
    for rc in rcd['categories'][:8]:
        a4 = rc['2026-04']
        m3 = rc['2026-03']
        mom_v = rc['环比']['线索数']['value']
        mom_c = mom_color(mom_v)
        cats_html += f"""
        <tr class="border-b border-surface-variant">
          <td class="py-1.5 px-2">{rc['category']}</td>
          <td class="py-1.5 px-2 text-right col-march">{fmt(m3['线索数'])}</td>
          <td class="py-1.5 px-2 text-right font-semibold text-primary col-april">{fmt(a4['线索数'])}</td>
          <td class="py-1.5 px-2 text-right {mom_c} col-compare">{mom_v:.1f}%</td>
          <td class="py-1.5 px-2 text-right col-april">{fmt(a4['转化率'], 'pct1')}</td>
          <td class="py-1.5 px-2 text-right col-april">{fmt(a4['首单流水'], 'wan')}</td>
          <td class="py-1.5 px-2 text-right font-semibold text-primary">{rc['score']:.1f}</td>
        </tr>"""
    if not cats_html:
        cats_html = '<tr><td colspan="7" class="py-2 px-3 text-on-surface-variant">数据不足</td></tr>'

    rc_detail_cards += f"""
    <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-3 flex flex-col gap-2 shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
      <div class="flex justify-between items-center cursor-pointer group" onclick="toggleRC(this)">
        <div class="font-medium text-on-surface flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">chevron_right</span>
          {res}
        </div>
        <div class="text-xs text-on-surface-variant">{len(rcd['categories'])} 个品类</div>
      </div>
      <div class="hidden mt-2">
        <table class="w-full text-left border-collapse font-body-main text-body-main text-xs">
          <thead>
            <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
              <th class="py-1.5 px-2 font-normal">品类</th>
              <th class="py-1.5 px-2 font-normal text-right col-march">3月线索</th>
              <th class="py-1.5 px-2 font-normal text-right col-april">4月线索</th>
              <th class="py-1.5 px-2 font-normal text-right col-compare">环比</th>
              <th class="py-1.5 px-2 font-normal text-right col-april">CVR</th>
              <th class="py-1.5 px-2 font-normal text-right col-april">GMV</th>
              <th class="py-1.5 px-2 font-normal text-right">得分</th>
            </tr>
          </thead>
          <tbody class="text-on-surface">
            {cats_html}
          </tbody>
        </table>
      </div>
    </div>"""

# NEW: Resource type efficiency rows
rte_rows = ""
for rte in data['resource_type_efficiency']:
    res = rte['resource']
    formal = rte['types'].get('正式品', {'leads': 0, 'share': 0, '转化率': 0})
    hatch = rte['types'].get('孵化品', {'leads': 0, 'share': 0, '转化率': 0})
    tag = rte.get('tag', '')
    tag_html = f'<span class="px-2 py-0.5 rounded text-xs font-semibold bg-orange-100 text-orange-800">{tag}</span>' if tag else '<span class="text-on-surface-variant text-xs">—</span>'
    rte_rows += f"""
    <tr class="border-b border-surface-variant hover:bg-surface-container-low transition-colors">
      <td class="py-2 px-3 font-medium">{res}</td>
      <td class="py-2 px-3 text-right">{fmt(formal['leads'])}</td>
      <td class="py-2 px-3 text-right">{formal['share']:.1f}%</td>
      <td class="py-2 px-3 text-right">{fmt(formal['转化率'], 'pct1')}</td>
      <td class="py-2 px-3 text-right">{fmt(hatch['leads'])}</td>
      <td class="py-2 px-3 text-right">{hatch['share']:.1f}%</td>
      <td class="py-2 px-3 text-right">{fmt(hatch['转化率'], 'pct1')}</td>
      <td class="py-2 px-3">{tag_html}</td>
    </tr>"""

# NEW: Price band diagnosis insight
pb = data['price_band_distribution']
zero_m3 = next((p for p in pb if p['price_band'] == '0元'), {'march': {'share': 0}, 'april': {'share': 0}, 'share_mom': 0})
zero_m4_share = zero_m3['april']['share']
zero_m3_share = zero_m3['march']['share']
zero_mom_pp = zero_m3['share_mom']

pb_diagnosis = ""
if abs(zero_mom_pp) >= 1:
    direction = "上升" if zero_mom_pp > 0 else "下降"
    pb_diagnosis = f"此外，0元课线索占比从 {zero_m3_share:.1f}% {direction}至 {zero_m4_share:.1f}%（{zero_mom_pp:+.1f}pp），"
    if zero_mom_pp > 0:
        pb_diagnosis += "低价引流结构加重，需关注高价值转化。"
    else:
        pb_diagnosis += "低价引流占比收窄，高价值课结构优化。"
else:
    pb_diagnosis = "0元课线索占比保持稳定。"

js_data = json.dumps(data, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>APP 线索广告位复盘月报</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;700&family=Inter:wght@400;600&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js"></script>
<script id="tailwind-config">
    tailwind.config = {{
      darkMode: "class",
      theme: {{
        extend: {{
          colors: {{
            "surface-variant": "#e0e3e6",
            "surface-container-lowest": "#ffffff",
            "outline": "#737686",
            "background": "#f7f9fc",
            "on-surface-variant": "#434655",
            "primary-fixed": "#dbe1ff",
            "outline-variant": "#c3c6d7",
            "on-error-container": "#93000a",
            "on-primary-fixed": "#00174b",
            "on-secondary": "#ffffff",
            "surface-container-highest": "#e0e3e6",
            "inverse-primary": "#b4c5ff",
            "error": "#ba1a1a",
            "secondary-container": "#6cf8bb",
            "inverse-on-surface": "#eff1f4",
            "on-background": "#191c1e",
            "secondary-fixed-dim": "#4edea3",
            "on-surface": "#191c1e",
            "surface-container-high": "#e6e8eb",
            "primary": "#004ac6",
            "surface": "#f7f9fc",
            "surface-dim": "#d8dadd",
            "error-container": "#ffdad6",
            "surface-container-low": "#f2f4f7",
            "tertiary": "#943700",
            "surface-bright": "#f7f9fc",
            "on-primary-container": "#eeefff",
            "on-secondary-container": "#00714d",
            "surface-tint": "#0053db",
            "tertiary-container": "#bc4800",
            "secondary": "#006c49",
            "surface-container": "#eceef1",
            "primary-fixed-dim": "#b4c5ff",
            "primary-container": "#2563eb",
            "on-primary": "#ffffff",
            "on-error": "#ffffff"
          }},
          borderRadius: {{
            DEFAULT: "0.125rem",
            lg: "0.25rem",
            xl: "0.5rem",
            full: "0.75rem"
          }},
          spacing: {{
            "card-gap": "20px",
            "element-tight": "8px",
            "container-padding": "24px",
            "element-loose": "16px",
            base: "4px",
            gutter: "16px"
          }},
          fontFamily: {{
            h1: ["Noto Sans SC"],
            "metric-sm": ["Inter"],
            "metric-lg": ["Inter"],
            "body-main": ["Noto Sans SC"],
            helper: ["Noto Sans SC"],
            "label-caps": ["Inter"]
          }},
          fontSize: {{
            h1: ["30px", {{ lineHeight: "38px", fontWeight: "700" }}],
            "metric-sm": ["18px", {{ lineHeight: "24px", fontWeight: "600" }}],
            "metric-lg": ["24px", {{ lineHeight: "32px", fontWeight: "600" }}],
            "body-main": ["14px", {{ lineHeight: "22px", fontWeight: "400" }}],
            helper: ["12px", {{ lineHeight: "16px", fontWeight: "400" }}],
            "label-caps": ["12px", {{ lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "600" }}]
          }}
        }}
      }}
    }}
</script>
<style>
  body {{ font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif; }}
  .chart-container {{ width: 100%; height: 100%; min-height: 300px; }}
  .material-symbols-outlined {{ font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24; }}
  .fade-in {{ animation: fadeIn 0.4s ease-in-out; }}
  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  .table-scroll {{ overflow-x: auto; }}
  .table-scroll table {{ min-width: 640px; }}
  .metric-def {{ cursor: help; border-bottom: 1px dashed #737686; }}
  /* Month view column hiding */
  body.view-march .col-april, body.view-march .col-compare {{ display: none !important; }}
  body.view-april .col-march, body.view-april .col-compare {{ display: none !important; }}
  body.view-compare .col-march, body.view-compare .col-april, body.view-compare .col-compare {{ display: table-cell !important; }}
</style>
</head>
<body class="bg-background min-h-screen flex flex-col font-body-main text-on-surface view-compare" id="app-body">

<header class="bg-surface-container-lowest h-[64px] border-b border-outline-variant shadow-sm flex justify-between items-center px-container-padding w-full">
  <div class="flex items-center gap-4">
    <h1 class="font-h1 text-metric-sm font-bold text-on-surface">APP 线索广告位复盘月报</h1>
    <span class="text-on-surface-variant font-helper text-helper ml-2">2026年3-4月投放分析</span>
  </div>
  <div class="flex items-center gap-6">
    <nav class="flex gap-4" id="month-nav">
      <button class="px-3 py-1 rounded text-on-surface-variant hover:text-primary transition-colors" data-month="march" onclick="setMonth('march')">3月</button>
      <button class="px-3 py-1 rounded text-on-surface-variant hover:text-primary transition-colors" data-month="april" onclick="setMonth('april')">4月</button>
      <button class="px-3 py-1 rounded text-primary font-bold border-b-2 border-primary pb-1" data-month="compare" onclick="setMonth('compare')">3-4月对比</button>
    </nav>
    <button class="bg-primary-container text-on-primary font-label-caps text-label-caps px-4 py-2 rounded-[6px] hover:bg-surface-tint transition-colors active:scale-[0.98]" onclick="exportReport()">导出 HTML 月报</button>
  </div>
</header>

<main class="flex-grow max-w-[1440px] w-full mx-auto p-container-padding flex flex-col gap-card-gap">

<!-- Problem Diagnosis -->
<section class="w-full bg-error-container border border-error/20 rounded-lg p-4 flex items-start gap-3 fade-in">
  <span class="material-symbols-outlined text-error text-2xl">crisis_alert</span>
  <div>
    <div class="font-metric-sm text-metric-sm font-semibold text-error">核心问题诊断</div>
    <div class="font-body-main text-body-main text-on-surface-variant mt-1">
      4月整体线索数环比下降 <span class="font-bold text-error">3.18%</span>（-574），首单流水环比下降 <span class="font-bold text-error">29.1%</span>（-¥66.2万），转化率从 7.30% 跌至 5.41%。GMV 下滑幅度远大于线索下滑幅度，说明<strong>转化效率恶化是核心问题</strong>，而非单纯流量减少。{pb_diagnosis}
    </div>
  </div>
</section>

<!-- KPI Overview -->
<section class="grid grid-cols-5 gap-gutter w-full fade-in" id="kpi-section">
  <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose flex flex-col gap-element-tight shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <div class="font-body-main text-body-main text-on-surface-variant">月度线索数</div>
    <div class="flex items-end gap-2">
      <span class="font-metric-lg text-[32px] font-bold text-on-surface leading-none" id="kpi-leads">17,492</span>
      <span class="flex items-center text-error font-helper text-helper" id="kpi-leads-mom"><span class="material-symbols-outlined text-[16px]">arrow_downward</span> 3.18%</span>
    </div>
    <div class="font-helper text-helper text-on-surface-variant mt-1" id="kpi-leads-abs">-574 较上月</div>
  </div>
  <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose flex flex-col gap-element-tight shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <div class="font-body-main text-body-main text-on-surface-variant">GMV（首单流水）</div>
    <div class="flex items-end gap-2">
      <span class="font-metric-lg text-[32px] font-bold text-on-surface leading-none" id="kpi-gmv">¥161.1万</span>
      <span class="flex items-center text-error font-helper text-helper" id="kpi-gmv-mom"><span class="material-symbols-outlined text-[16px]">arrow_downward</span> 29.1%</span>
    </div>
    <div class="font-helper text-helper text-on-surface-variant mt-1" id="kpi-gmv-abs">-¥66.2万 较上月</div>
  </div>
  <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose flex flex-col gap-element-tight shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <div class="font-body-main text-body-main text-on-surface-variant">
      <span class="metric-def" title="转化率 = SUM(首单数) / SUM(线索数)。严禁直接对原始字段取 AVG，行级转化率在聚合时会导致均值偏差。">整体转化率</span>
    </div>
    <div class="flex items-end gap-2">
      <span class="font-metric-lg text-[32px] font-bold text-on-surface leading-none" id="kpi-cvr">5.41%</span>
      <span class="flex items-center text-error font-helper text-helper" id="kpi-cvr-mom"><span class="material-symbols-outlined text-[16px]">arrow_downward</span> 25.9%</span>
    </div>
    <div class="font-helper text-helper text-on-surface-variant mt-1" id="kpi-cvr-abs">-1.89pp 较上月</div>
  </div>
  <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose flex flex-col gap-element-tight shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <div class="font-body-main text-body-main text-on-surface-variant">资源位数量</div>
    <div class="flex items-end gap-2">
      <span class="font-metric-lg text-[32px] font-bold text-on-surface leading-none" id="kpi-slots">26</span>
      <span class="flex items-center text-on-surface-variant font-helper text-helper"><span class="material-symbols-outlined text-[16px]">horizontal_rule</span> 0%</span>
    </div>
    <div class="font-helper text-helper text-on-surface-variant mt-1">0 较上月</div>
  </div>
  <div class="bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose flex flex-col gap-element-tight shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <div class="font-body-main text-body-main text-on-surface-variant">LTV 均值</div>
    <div class="flex items-end gap-2">
      <span class="font-metric-lg text-[32px] font-bold text-on-surface leading-none" id="kpi-ltv">¥92.12</span>
      <span class="flex items-center text-error font-helper text-helper" id="kpi-ltv-mom"><span class="material-symbols-outlined text-[16px]">arrow_downward</span> 26.8%</span>
    </div>
    <div class="font-helper text-helper text-on-surface-variant mt-1" id="kpi-ltv-abs">-¥33.69 较上月</div>
  </div>
</section>

<!-- Action Items -->
<section class="w-full flex flex-col gap-4 fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">assignment</span> 次月行动建议
  </h2>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
    {action_cards}
  </div>
</section>

<!-- Trend Charts -->
<section class="flex gap-gutter w-full h-[400px] fade-in">
  <div class="w-2/3 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col">
    <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-2 border-b border-surface-variant pb-2">月度线索与 GMV 趋势</h2>
    <div id="trend-chart" class="chart-container flex-grow"></div>
  </div>
  <div class="w-1/3 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col">
    <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-2 border-b border-surface-variant pb-2">资源位线索占比</h2>
    <div id="pie-chart" class="chart-container flex-grow"></div>
  </div>
</section>

<!-- Category Traffic Structure -->
<section class="w-full flex flex-col gap-card-gap fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">trending_up</span> 品类流量结构变化（正式品 vs 孵化品）
  </h2>
  <div class="flex gap-gutter w-full h-[360px]">
    <div class="w-2/3 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col">
      <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-2">各品类线索量</h3>
      <div id="category-bar-chart" class="chart-container flex-grow"></div>
    </div>
    <div class="w-1/3 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col">
      <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-2">正式品 / 孵化品 占比</h3>
      <div id="category-pie-chart" class="chart-container flex-grow"></div>
    </div>
  </div>
  <div class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-3">品类明细（Top 20）</h3>
    <div class="table-scroll" style="max-height: 400px; overflow-y: auto;">
      <table class="w-full text-left border-collapse font-body-main text-body-main">
        <thead>
          <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
            <th class="py-2 px-3 font-normal">品类</th>
            <th class="py-2 px-3 font-normal text-right col-march">3月线索</th>
            <th class="py-2 px-3 font-normal text-right col-april">4月线索</th>
            <th class="py-2 px-3 font-normal text-right col-compare">线索环比</th>
            <th class="py-2 px-3 font-normal text-right col-april">4月转化率</th>
            <th class="py-2 px-3 font-normal text-right col-compare">转化率环比</th>
            <th class="py-2 px-3 font-normal text-right col-april">4月GMV</th>
            <th class="py-2 px-3 font-normal text-right col-compare">GMV环比</th>
          </tr>
        </thead>
        <tbody class="text-on-surface">
          {ct_rows}
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- Price Band Distribution -->
<section class="w-full flex flex-col gap-card-gap fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">pie_chart</span> 价格带全局占比
  </h2>
  <div class="flex gap-gutter w-full h-[320px]">
    <div class="w-1/2 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col">
      <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-2">3月价格带分布</h3>
      <div id="price-band-march-chart" class="chart-container flex-grow"></div>
    </div>
    <div class="w-1/2 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] flex flex-col">
      <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-2">4月价格带分布</h3>
      <div id="price-band-april-chart" class="chart-container flex-grow"></div>
    </div>
  </div>
</section>

<!-- Resource Type Efficiency -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">category</span> 资源位 × 品类类型效率（正式品 vs 孵化品）
  </h2>
  <div class="mb-3 text-helper text-on-surface-variant">
    各资源位上正式品与孵化品的线索占比及转化率对比。橙色标签提示结构优化机会。
  </div>
  <div class="table-scroll">
    <table class="w-full text-left border-collapse font-body-main text-body-main">
      <thead>
        <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
          <th class="py-2 px-3 font-normal">资源位</th>
          <th class="py-2 px-3 font-normal text-right">正式品线索</th>
          <th class="py-2 px-3 font-normal text-right">正式品占比</th>
          <th class="py-2 px-3 font-normal text-right">正式品CVR</th>
          <th class="py-2 px-3 font-normal text-right">孵化品线索</th>
          <th class="py-2 px-3 font-normal text-right">孵化品占比</th>
          <th class="py-2 px-3 font-normal text-right">孵化品CVR</th>
          <th class="py-2 px-3 font-normal">洞察标签</th>
        </tr>
      </thead>
      <tbody class="text-on-surface">
        {rte_rows}
      </tbody>
    </table>
  </div>
</section>

<!-- Resource Efficiency -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">bar_chart</span> 资源位效率矩阵（15个核心资源位）
  </h2>
  <div class="table-scroll">
    <table class="w-full text-left border-collapse font-body-main text-body-main">
      <thead>
        <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
          <th class="py-2 px-3 font-normal">资源位</th>
          <th class="py-2 px-3 font-normal text-right col-march">3月线索</th>
          <th class="py-2 px-3 font-normal text-right col-march">3月转化率</th>
          <th class="py-2 px-3 font-normal text-right col-march">3月GMV</th>
          <th class="py-2 px-3 font-normal text-right text-primary col-april">4月线索</th>
          <th class="py-2 px-3 font-normal text-right col-april">4月转化率</th>
          <th class="py-2 px-3 font-normal text-right col-april">4月GMV</th>
          <th class="py-2 px-3 font-normal text-right col-compare">线索环比</th>
          <th class="py-2 px-3 font-normal text-right col-compare">转化率环比</th>
          <th class="py-2 px-3 font-normal text-right col-compare">GMV环比</th>
        </tr>
      </thead>
      <tbody class="text-on-surface">
        {res_rows}
      </tbody>
    </table>
  </div>
</section>

<!-- Resource x Category Heatmap -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">grid_on</span> 资源位 x 品类 综合得分热力图
  </h2>
  <div class="mb-3 text-helper text-on-surface-variant">
    综合得分 = 转化率x40% + GMVx35% + 线索量x25%（均已归一化）。颜色越深代表该资源位与该品类的匹配度越高。
  </div>
  <div id="heatmap-chart" class="chart-container" style="height: 480px;"></div>
</section>

<!-- Resource Category Recommendations -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">recommend</span> 资源位品类推荐矩阵
  </h2>
  <div class="mb-3 text-helper text-on-surface-variant">
    每个资源位推荐 Top 3 品类（按综合得分排序），右侧为「避雷品类」（该资源位上效率显著偏低的品类）。
  </div>
  <div class="table-scroll">
    <table class="w-full text-left border-collapse font-body-main text-body-main">
      <thead>
        <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
          <th class="py-2 px-3 font-normal">资源位</th>
          <th class="py-2 px-3 font-normal">推荐①</th>
          <th class="py-2 px-3 font-normal">推荐②</th>
          <th class="py-2 px-3 font-normal">推荐③</th>
          <th class="py-2 px-3 font-normal">避雷品类</th>
        </tr>
      </thead>
      <tbody class="text-on-surface">
        {rec_rows}
      </tbody>
    </table>
  </div>
</section>

<!-- Per-Resource Category Detail Cards -->
<section class="w-full flex flex-col gap-card-gap fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">expand_circle_right</span> 逐资源位品类明细（点击展开）
  </h2>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-gutter">
    {rc_detail_cards}
  </div>
</section>

<!-- Selling Point Analysis -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">sell</span> 素材卖点效果分析（Top 20）
  </h2>
  <div class="table-scroll">
    <table class="w-full text-left border-collapse font-body-main text-body-main">
      <thead>
        <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
          <th class="py-2 px-3 font-normal">卖点关键词</th>
          <th class="py-2 px-3 font-normal text-right col-march">3月线索</th>
          <th class="py-2 px-3 font-normal text-right col-march">3月转化率</th>
          <th class="py-2 px-3 font-normal text-right text-primary col-april">4月线索</th>
          <th class="py-2 px-3 font-normal text-right col-april">4月转化率</th>
          <th class="py-2 px-3 font-normal text-right col-compare">线索环比</th>
          <th class="py-2 px-3 font-normal text-right col-compare">状态</th>
        </tr>
      </thead>
      <tbody class="text-on-surface">
        {sp_rows}
      </tbody>
    </table>
  </div>
</section>

<!-- 3D Cross Analysis -->
<section class="flex flex-col gap-card-gap w-full fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">hub</span> 三维交叉分析（品类 x 价格带 x 人群）
  </h2>
  <div class="flex gap-gutter w-full">
    <div class="w-1/2 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
      <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-3">最佳人群映射（按转化率排序）</h3>
      <div class="table-scroll" style="max-height: 400px; overflow-y: auto;">
        <table class="w-full text-left border-collapse font-body-main text-body-main">
          <thead>
            <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
              <th class="py-2 px-3 font-normal">品类</th>
              <th class="py-2 px-3 font-normal">价格带</th>
              <th class="py-2 px-3 font-normal">最佳人群</th>
              <th class="py-2 px-3 font-normal text-right">线索数</th>
              <th class="py-2 px-3 font-normal text-right">转化率</th>
            </tr>
          </thead>
          <tbody class="text-on-surface">
            {ba_rows}
          </tbody>
        </table>
      </div>
    </div>
    <div class="w-1/2 bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
      <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-3">品类 x 价格带 产出矩阵</h3>
      <div class="table-scroll" style="max-height: 400px; overflow-y: auto;">
        <table class="w-full text-left border-collapse font-body-main text-body-main">
          <thead>
            <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
              <th class="py-2 px-3 font-normal">品类</th>
              <th class="py-2 px-3 font-normal">价格带</th>
              <th class="py-2 px-3 font-normal text-right">线索数</th>
              <th class="py-2 px-3 font-normal text-right">首单数</th>
              <th class="py-2 px-3 font-normal text-right">GMV</th>
              <th class="py-2 px-3 font-normal text-right">转化率</th>
            </tr>
          </thead>
          <tbody class="text-on-surface">
            {cp_rows}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)]">
    <h3 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-3">品类 x 价格带 x 人群 环比变化排行（Top 20）</h3>
    <div class="table-scroll" style="max-height: 400px; overflow-y: auto;">
      <table class="w-full text-left border-collapse font-body-main text-body-main">
        <thead>
          <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
            <th class="py-2 px-3 font-normal">品类</th>
            <th class="py-2 px-3 font-normal">价格带</th>
            <th class="py-2 px-3 font-normal">人群</th>
            <th class="py-2 px-3 font-normal text-right">4月线索</th>
            <th class="py-2 px-3 font-normal text-right">4月转化率</th>
            <th class="py-2 px-3 font-normal text-right">线索环比</th>
            <th class="py-2 px-3 font-normal text-right">转化率环比</th>
          </tr>
        </thead>
        <tbody class="text-on-surface">
          {td_rows}
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- 4D Cross Analysis -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">auto_graph</span> 四维交叉最佳组合（品类 x 价格带 x 人群 x 卖点）
  </h2>
  <div class="table-scroll" style="max-height: 500px; overflow-y: auto;">
    <table class="w-full text-left border-collapse font-body-main text-body-main">
      <thead>
        <tr class="font-label-caps text-label-caps text-on-surface-variant border-b border-surface-variant bg-surface-container-low">
          <th class="py-2 px-3 font-normal">品类</th>
          <th class="py-2 px-3 font-normal">价格带</th>
          <th class="py-2 px-3 font-normal">人群</th>
          <th class="py-2 px-3 font-normal">卖点</th>
          <th class="py-2 px-3 font-normal text-right">4月线索</th>
          <th class="py-2 px-3 font-normal text-right">4月转化率</th>
          <th class="py-2 px-3 font-normal text-right">线索环比</th>
        </tr>
      </thead>
      <tbody class="text-on-surface">
        {fd_rows}
      </tbody>
    </table>
  </div>
</section>

<!-- WordCloud -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-4 border-b border-surface-variant pb-2 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">cloud</span> 卖点词云（按线索量加权）
  </h2>
  <div id="wordcloud-chart" class="chart-container" style="height: 350px;"></div>
</section>

<!-- Metrics Definitions -->
<section class="w-full bg-surface-container-low border border-surface-variant rounded-lg p-4 fade-in">
  <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface mb-3 flex items-center gap-2">
    <span class="material-symbols-outlined text-primary">info</span> 指标口径说明
  </h2>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-helper text-on-surface-variant">
    <div>
      <strong class="text-on-surface">转化率</strong> = SUM(首单数) / SUM(线索数)。原始数据中的「转化率」字段为行级数值，在聚合到资源位/品类/月份维度时，必须重新按此公式计算，严禁直接取 AVG。
    </div>
    <div>
      <strong class="text-on-surface">GMV（首单流水）</strong> = SUM(首单流水)。按统计月份汇总，单位元。
    </div>
    <div>
      <strong class="text-on-surface">环比</strong> = (本月值 - 上月值) / 上月值 x 100%。当上月值为 0 时显示「—」。
    </div>
    <div>
      <strong class="text-on-surface">LTV 均值</strong> = AVG(LTV)，算术平均，保留 2 位小数。
    </div>
    <div>
      <strong class="text-on-surface">综合得分</strong> = 转化率_normx40% + GMV_normx35% + 线索量_normx25%。各维度先做 Min-Max 归一化（0-100）再加权。
    </div>
    <div>
      <strong class="text-on-surface">数据过滤</strong>：原始数据中的「合计」行（stat_month = '合计'）已剔除，避免重复统计。
    </div>
  </div>
</section>

<!-- Data Detail -->
<section class="w-full bg-surface-container-lowest border border-surface-variant rounded-lg p-element-loose shadow-[0_2px_4px_rgba(0,0,0,0.04)] fade-in">
  <div class="flex justify-between items-center cursor-pointer border-b border-surface-variant pb-2 group" onclick="toggleDetail()">
    <h2 class="font-metric-sm text-metric-sm font-semibold text-on-surface">数据明细</h2>
    <span class="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors" id="detail-icon">expand_more</span>
  </div>
  <div class="hidden mt-4" id="detail-content">
    <p class="text-helper text-on-surface-variant mb-2">点击「导出 HTML 月报」可获取完整明细表格。此处展示关键汇总维度。</p>
    <div class="grid grid-cols-2 gap-gutter">
      <div>
        <h4 class="font-semibold mb-2">月度汇总</h4>
        <table class="w-full text-left border-collapse font-body-main text-body-main text-sm">
          <thead><tr class="border-b border-surface-variant text-on-surface-variant"><th class="py-1 px-2">月份</th><th class="py-1 px-2 text-right">线索数</th><th class="py-1 px-2 text-right">首单数</th><th class="py-1 px-2 text-right">GMV</th><th class="py-1 px-2 text-right">转化率</th></tr></thead>
          <tbody>
            <tr class="border-b border-surface-variant"><td class="py-1 px-2">2026-03</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-03']['线索数'])}</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-03']['首单数'])}</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-03']['首单流水'], 'wan')}</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-03']['转化率'], 'pct1')}</td></tr>
            <tr class="border-b border-surface-variant"><td class="py-1 px-2">2026-04</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-04']['线索数'])}</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-04']['首单数'])}</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-04']['首单流水'], 'wan')}</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['2026-04']['转化率'], 'pct1')}</td></tr>
          </tbody>
        </table>
      </div>
      <div>
        <h4 class="font-semibold mb-2">环比概览</h4>
        <table class="w-full text-left border-collapse font-body-main text-body-main text-sm">
          <thead><tr class="border-b border-surface-variant text-on-surface-variant"><th class="py-1 px-2">指标</th><th class="py-1 px-2 text-right">环比幅度</th><th class="py-1 px-2 text-right">绝对变化</th></tr></thead>
          <tbody>
            <tr class="border-b border-surface-variant"><td class="py-1 px-2">线索数</td><td class="py-1 px-2 text-right text-error">{data['monthly_summary']['环比']['线索数']['value']:.2f}%</td><td class="py-1 px-2 text-right">{data['monthly_summary']['环比']['线索数']['abs']}</td></tr>
            <tr class="border-b border-surface-variant"><td class="py-1 px-2">首单数</td><td class="py-1 px-2 text-right text-error">{data['monthly_summary']['环比']['首单数']['value']:.2f}%</td><td class="py-1 px-2 text-right">{data['monthly_summary']['环比']['首单数']['abs']}</td></tr>
            <tr class="border-b border-surface-variant"><td class="py-1 px-2">首单流水</td><td class="py-1 px-2 text-right text-error">{data['monthly_summary']['环比']['首单流水']['value']:.2f}%</td><td class="py-1 px-2 text-right">{fmt(data['monthly_summary']['环比']['首单流水']['abs'], 'wan')}</td></tr>
            <tr class="border-b border-surface-variant"><td class="py-1 px-2">转化率</td><td class="py-1 px-2 text-right text-error">{data['monthly_summary']['环比']['转化率']['value']:.2f}%</td><td class="py-1 px-2 text-right">{data['monthly_summary']['环比']['转化率']['abs']*100:.2f}pp</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>

</main>

<footer class="bg-surface-container-low h-[40px] border-t border-outline-variant flex justify-between items-center px-container-padding w-full mt-auto">
  <div class="text-on-surface-variant font-helper text-helper">数据更新至：2026-04-30</div>
  <div class="text-on-surface-variant font-helper text-helper">转化率 = 首单数 / 线索数 | 数据来源：广告投放管理系统</div>
</footer>

<script>
const RAW_DATA = {js_data};
let currentMonth = 'compare';

function fmtNum(n) {{
  return n.toLocaleString('zh-CN');
}}

function momArrow(v) {{
  if (v > 0) return 'arrow_upward';
  if (v < 0) return 'arrow_downward';
  return 'horizontal_rule';
}}

function momColorClass(v) {{
  if (v > 0) return 'text-secondary';
  if (v < 0) return 'text-error';
  return 'text-on-surface-variant';
}}

function updateKPI(month) {{
  const ms = RAW_DATA.monthly_summary;
  const m3 = ms['2026-03'];
  const m4 = ms['2026-04'];
  const mom = ms['环比'];

  let leads, gmv, cvr, slots, ltv, leadsMom, gmvMom, cvrMom, ltvMom, leadsAbs, gmvAbs, cvrAbs, ltvAbs;

  if (month === 'march') {{
    leads = m3['线索数']; gmv = m3['首单流水']; cvr = m3['转化率']; slots = m3['资源位数量']; ltv = m3['LTV均值'];
    leadsMom = null; gmvMom = null; cvrMom = null; ltvMom = null;
    leadsAbs = null; gmvAbs = null; cvrAbs = null; ltvAbs = null;
  }} else if (month === 'april') {{
    leads = m4['线索数']; gmv = m4['首单流水']; cvr = m4['转化率']; slots = m4['资源位数量']; ltv = m4['LTV均值'];
    leadsMom = mom['线索数']['value']; gmvMom = mom['首单流水']['value']; cvrMom = mom['转化率']['value']; ltvMom = mom['LTV均值']['value'];
    leadsAbs = mom['线索数']['abs']; gmvAbs = mom['首单流水']['abs']; cvrAbs = mom['转化率']['abs']; ltvAbs = mom['LTV均值']['abs'];
  }} else {{
    leads = m4['线索数']; gmv = m4['首单流水']; cvr = m4['转化率']; slots = m4['资源位数量']; ltv = m4['LTV均值'];
    leadsMom = mom['线索数']['value']; gmvMom = mom['首单流水']['value']; cvrMom = mom['转化率']['value']; ltvMom = mom['LTV均值']['value'];
    leadsAbs = mom['线索数']['abs']; gmvAbs = mom['首单流水']['abs']; cvrAbs = mom['转化率']['abs']; ltvAbs = mom['LTV均值']['abs'];
  }}

  document.getElementById('kpi-leads').textContent = fmtNum(leads);
  document.getElementById('kpi-gmv').textContent = '¥' + (gmv/10000).toFixed(1) + '万';
  document.getElementById('kpi-cvr').textContent = (cvr*100).toFixed(2) + '%';
  document.getElementById('kpi-slots').textContent = slots;
  document.getElementById('kpi-ltv').textContent = '¥' + ltv.toFixed(2);

  function setMom(id, value, abs, isPct) {{
    const el = document.getElementById(id);
    const absEl = document.getElementById(id.replace('-mom', '-abs'));
    if (value === null) {{
      el.innerHTML = '<span class="flex items-center text-on-surface-variant font-helper text-helper"><span class="material-symbols-outlined text-[16px]">horizontal_rule</span> —</span>';
      absEl.textContent = '— 较上月';
      return;
    }}
    const arrow = momArrow(value);
    const color = momColorClass(value);
    const suffix = isPct ? '%' : '';
    const absSuffix = isPct ? 'pp' : '';
    el.innerHTML = '<span class="flex items-center ' + color + ' font-helper text-helper"><span class="material-symbols-outlined text-[16px]">' + arrow + '</span> ' + Math.abs(value).toFixed(1) + suffix + '</span>';
    absEl.textContent = (value > 0 ? '+' : '') + (isPct ? (abs*100).toFixed(2) : abs) + absSuffix + ' 较上月';
  }}

  setMom('kpi-leads-mom', leadsMom, leadsAbs, false);
  setMom('kpi-gmv-mom', gmvMom, gmvAbs, false);
  setMom('kpi-cvr-mom', cvrMom, cvrAbs, true);
  setMom('kpi-ltv-mom', ltvMom, ltvAbs, false);
}}

function setMonth(m) {{
  currentMonth = m;
  document.querySelectorAll('#month-nav button').forEach(btn => {{
    if(btn.dataset.month === m) {{
      btn.className = 'px-3 py-1 rounded text-primary font-bold border-b-2 border-primary pb-1';
    }} else {{
      btn.className = 'px-3 py-1 rounded text-on-surface-variant hover:text-primary transition-colors';
    }}
  }});

  // Update body class for CSS column hiding
  document.body.classList.remove('view-march', 'view-april', 'view-compare');
  document.body.classList.add('view-' + m);

  updateKPI(m);
  renderCharts();
}}

function renderCharts() {{
  const mData = RAW_DATA.trend.march;
  const aData = RAW_DATA.trend.april;

  // Trend chart
  const trendEl = document.getElementById('trend-chart');
  if(trendEl) {{
    const chart = echarts.init(trendEl);
    let series = [];
    let xAxis = [];
    if(currentMonth === 'march') {{
      xAxis = mData.map(d => d.date);
      series = [
        {{ name: '线索数', type: 'line', data: mData.map(d=>d.线索数), smooth: true, itemStyle: {{ color: '#004ac6' }}, areaStyle: {{ opacity: 0.1 }} }},
        {{ name: 'GMV(万)', type: 'line', yAxisIndex: 1, data: mData.map(d=>d.首单流水), smooth: true, itemStyle: {{ color: '#006c49' }} }}
      ];
    }} else if(currentMonth === 'april') {{
      xAxis = aData.map(d => d.date);
      series = [
        {{ name: '线索数', type: 'line', data: aData.map(d=>d.线索数), smooth: true, itemStyle: {{ color: '#004ac6' }}, areaStyle: {{ opacity: 0.1 }} }},
        {{ name: 'GMV(万)', type: 'line', yAxisIndex: 1, data: aData.map(d=>d.首单流水), smooth: true, itemStyle: {{ color: '#006c49' }} }}
      ];
    }} else {{
      xAxis = mData.map(d => '03-' + d.date).concat(aData.map(d => '04-' + d.date));
      series = [
        {{ name: '3月线索', type: 'line', data: mData.map(d=>d.线索数).concat(new Array(aData.length).fill(null)), smooth: true, itemStyle: {{ color: '#b4c5ff' }} }},
        {{ name: '4月线索', type: 'line', data: new Array(mData.length).fill(null).concat(aData.map(d=>d.线索数)), smooth: true, itemStyle: {{ color: '#004ac6' }}, areaStyle: {{ opacity: 0.1 }} }},
        {{ name: '3月GMV', type: 'line', yAxisIndex: 1, data: mData.map(d=>d.首单流水).concat(new Array(aData.length).fill(null)), smooth: true, itemStyle: {{ color: '#4edea3' }} }},
        {{ name: '4月GMV', type: 'line', yAxisIndex: 1, data: new Array(mData.length).fill(null).concat(aData.map(d=>d.首单流水)), smooth: true, itemStyle: {{ color: '#006c49' }} }}
      ];
    }}
    chart.setOption({{
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
      legend: {{ bottom: 0 }},
      grid: {{ left: 60, right: 60, top: 20, bottom: 40 }},
      xAxis: {{ type: 'category', data: xAxis, boundaryGap: false }},
      yAxis: [
        {{ type: 'value', name: '线索数', position: 'left', axisLine: {{ show: true, lineStyle: {{ color: '#004ac6' }} }} }},
        {{ type: 'value', name: 'GMV(万)', position: 'right', axisLine: {{ show: true, lineStyle: {{ color: '#006c49' }} }} }}
      ],
      series: series
    }});
  }}

  // Pie chart (resource share)
  const pieEl = document.getElementById('pie-chart');
  if(pieEl) {{
    const chart = echarts.init(pieEl);
    let pieData;
    if (currentMonth === 'march') {{
      pieData = RAW_DATA.resource_efficiency.map(r => ({{
        name: r.resource,
        value: r['2026-03'].线索数
      }})).sort((a,b) => b.value - a.value);
    }} else {{
      pieData = RAW_DATA.resource_efficiency.map(r => ({{
        name: r.resource,
        value: r['2026-04'].线索数
      }})).sort((a,b) => b.value - a.value);
    }}
    const top5 = pieData.slice(0, 5);
    const other = pieData.slice(5).reduce((s, i) => s + i.value, 0);
    if(other > 0) top5.push({{ name: '其他', value: other }});
    chart.setOption({{
      tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}} ({{d}}%)' }},
      series: [{{
        type: 'pie',
        radius: ['45%', '75%'],
        avoidLabelOverlap: true,
        itemStyle: {{ borderRadius: 6, borderColor: '#fff', borderWidth: 2 }},
        label: {{ show: true, formatter: '{{b}}\\n{{d}}%' }},
        data: top5
      }}]
    }});
  }}

  // Category bar chart
  const catBarEl = document.getElementById('category-bar-chart');
  if(catBarEl) {{
    const chart = echarts.init(catBarEl);
    const cats = RAW_DATA.category_traffic.slice(0, 15);
    let xData, formalData, hatchData, momData;
    if (currentMonth === 'march') {{
      xData = cats.map(c => c.category);
      formalData = cats.map(c => c.type === '正式品' ? c.march.leads : 0);
      hatchData = cats.map(c => c.type === '孵化品' ? c.march.leads : 0);
      momData = cats.map(() => 0);
    }} else if (currentMonth === 'april') {{
      xData = cats.map(c => c.category);
      formalData = cats.map(c => c.type === '正式品' ? c.april.leads : 0);
      hatchData = cats.map(c => c.type === '孵化品' ? c.april.leads : 0);
      momData = cats.map(c => c.mom.leads);
    }} else {{
      xData = cats.map(c => c.category);
      formalData = cats.map(c => c.type === '正式品' ? c.april.leads : 0);
      hatchData = cats.map(c => c.type === '孵化品' ? c.april.leads : 0);
      momData = cats.map(c => c.mom.leads);
    }}
    chart.setOption({{
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      legend: {{ data: ['正式品', '孵化品', '环比%'], bottom: 0 }},
      grid: {{ left: 80, right: 60, top: 20, bottom: 40 }},
      xAxis: {{ type: 'category', data: xData, axisLabel: {{ rotate: 30, fontSize: 10 }} }},
      yAxis: [
        {{ type: 'value', name: '线索数', position: 'left' }},
        {{ type: 'value', name: '环比%', position: 'right' }}
      ],
      series: [
        {{ name: '正式品', type: 'bar', stack: 'total', data: formalData, itemStyle: {{ color: '#004ac6' }} }},
        {{ name: '孵化品', type: 'bar', stack: 'total', data: hatchData, itemStyle: {{ color: '#4edea3' }} }},
        {{ name: '环比%', type: 'line', yAxisIndex: 1, data: momData, itemStyle: {{ color: '#ba1a1a' }}, symbol: 'circle' }}
      ]
    }});
  }}

  // Category pie chart (正式品 vs 孵化品)
  const catPieEl = document.getElementById('category-pie-chart');
  if(catPieEl) {{
    const chart = echarts.init(catPieEl);
    let formalLeads = 0, hatchLeads = 0;
    RAW_DATA.category_traffic.forEach(c => {{
      const src = (currentMonth === 'march') ? c.march : c.april;
      if(c.type === '正式品') formalLeads += src.leads;
      else if(c.type === '孵化品') hatchLeads += src.leads;
    }});
    chart.setOption({{
      tooltip: {{ trigger: 'item' }},
      series: [{{
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {{ borderRadius: 6, borderColor: '#fff', borderWidth: 2 }},
        label: {{ formatter: '{{b}}\\n{{d}}%' }},
        data: [
          {{ name: '正式品', value: formalLeads, itemStyle: {{ color: '#004ac6' }} }},
          {{ name: '孵化品', value: hatchLeads, itemStyle: {{ color: '#4edea3' }} }}
        ]
      }}]
    }});
  }}

  // Price band sunburst charts
  const pbMarchEl = document.getElementById('price-band-march-chart');
  const pbAprilEl = document.getElementById('price-band-april-chart');
  if(pbMarchEl) {{
    const chart = echarts.init(pbMarchEl);
    const pbData = RAW_DATA.price_band_type ? RAW_DATA.price_band_type['2026-03'] : [];
    if(currentMonth === 'april') {{
      chart.clear();
    }} else {{
      chart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p) {{ return p.name + ': ' + p.value.toLocaleString(); }} }},
        series: [{{
          type: 'sunburst',
          radius: ['20%', '70%'],
          itemStyle: {{ borderRadius: 4, borderColor: '#fff', borderWidth: 2 }},
          label: {{ formatter: '{{b}}' }},
          levels: [
            {{}},
            {{ r0: '20%', r: '55%', label: {{ rotate: 'tangential', fontSize: 11 }} }},
            {{ r0: '55%', r: '70%', label: {{ align: 'right', fontSize: 10 }} }}
          ],
          data: pbData.map(d => ({{
            name: d.name,
            value: d.value,
            children: d.children.map(c => ({{
              name: c.name,
              value: c.value,
              itemStyle: {{ color: c.name === '正式品' ? '#004ac6' : '#4edea3' }}
            }}))
          }}))
        }}]
      }});
    }}
  }}
  if(pbAprilEl) {{
    const chart = echarts.init(pbAprilEl);
    const pbData = RAW_DATA.price_band_type ? RAW_DATA.price_band_type['2026-04'] : [];
    if(currentMonth === 'march') {{
      chart.clear();
    }} else {{
      chart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p) {{ return p.name + ': ' + p.value.toLocaleString(); }} }},
        series: [{{
          type: 'sunburst',
          radius: ['20%', '70%'],
          itemStyle: {{ borderRadius: 4, borderColor: '#fff', borderWidth: 2 }},
          label: {{ formatter: '{{b}}' }},
          levels: [
            {{}},
            {{ r0: '20%', r: '55%', label: {{ rotate: 'tangential', fontSize: 11 }} }},
            {{ r0: '55%', r: '70%', label: {{ align: 'right', fontSize: 10 }} }}
          ],
          data: pbData.map(d => ({{
            name: d.name,
            value: d.value,
            children: d.children.map(c => ({{
              name: c.name,
              value: c.value,
              itemStyle: {{ color: c.name === '正式品' ? '#004ac6' : '#4edea3' }}
            }}))
          }}))
        }}]
      }});
    }}
  }}

  // Heatmap
  const heatmapEl = document.getElementById('heatmap-chart');
  if(heatmapEl) {{
    const chart = echarts.init(heatmapEl);
    const cats = RAW_DATA.top_categories;
    const ress = RAW_DATA.resource_efficiency.map(r => r.resource);
    const hData = RAW_DATA.heatmap_data.map(h => [ress.indexOf(h.resource), cats.indexOf(h.category), h.score]);
    chart.setOption({{
      tooltip: {{ position: 'top' }},
      grid: {{ left: 100, right: 40, top: 20, bottom: 80 }},
      xAxis: {{ type: 'category', data: cats, splitArea: {{ show: true }}, axisLabel: {{ rotate: 30, fontSize: 10 }} }},
      yAxis: {{ type: 'category', data: ress, splitArea: {{ show: true }} }},
      visualMap: {{
        min: 0,
        max: RAW_DATA.heatmap_max,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        inRange: {{ color: ['#f2f4f7', '#dbe1ff', '#004ac6'] }}
      }},
      series: [{{
        name: '综合得分',
        type: 'heatmap',
        data: hData,
        label: {{ show: true, fontSize: 9 }},
        emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' }} }}
      }}]
    }});
  }}

  // WordCloud
  const wcEl = document.getElementById('wordcloud-chart');
  if(wcEl) {{
    const chart = echarts.init(wcEl);
    chart.setOption({{
      tooltip: {{ show: true }},
      series: [{{
        type: 'wordCloud',
        shape: 'circle',
        left: 'center',
        top: 'center',
        width: '90%',
        height: '90%',
        sizeRange: [14, 56],
        rotationRange: [-45, 45],
        rotationStep: 15,
        gridSize: 12,
        drawOutOfBound: false,
        textStyle: {{
          fontFamily: 'Noto Sans SC',
          fontWeight: 'bold',
          color: function () {{
            const palette = ['#004ac6', '#2563eb', '#0053db', '#006c49', '#4edea3', '#943700', '#bc4800'];
            return palette[Math.floor(Math.random() * palette.length)];
          }}
        }},
        emphasis: {{ focus: 'self', textStyle: {{ shadowBlur: 10, shadowColor: '#333' }} }},
        data: RAW_DATA.wordcloud
      }}]
    }});
  }}

  window.addEventListener('resize', () => {{
    ['trend-chart','pie-chart','category-bar-chart','category-pie-chart','heatmap-chart','wordcloud-chart'].forEach(id => {{
      const el = document.getElementById(id);
      if(el) {{
        const inst = echarts.getInstanceByDom(el);
        if(inst) inst.resize();
      }}
    }});
  }});
}}

function toggleDetail() {{
  const el = document.getElementById('detail-content');
  const icon = document.getElementById('detail-icon');
  if(el.classList.contains('hidden')) {{
    el.classList.remove('hidden');
    icon.textContent = 'expand_less';
  }} else {{
    el.classList.add('hidden');
    icon.textContent = 'expand_more';
  }}
}}

function toggleRC(header) {{
  const content = header.nextElementSibling;
  const icon = header.querySelector('.material-symbols-outlined');
  if(content.classList.contains('hidden')) {{
    content.classList.remove('hidden');
    icon.textContent = 'expand_more';
  }} else {{
    content.classList.add('hidden');
    icon.textContent = 'chevron_right';
  }}
}}

function exportReport() {{
  const btn = document.querySelector('button[onclick="exportReport()"]');
  const originalText = btn.textContent;
  btn.textContent = '导出中...';
  btn.disabled = true;

  setTimeout(() => {{
    document.querySelectorAll('.chart-container').forEach(el => {{
      const chart = echarts.getInstanceByDom(el);
      if(chart) {{
        const img = document.createElement('img');
        img.src = chart.getDataURL({{ type: 'png', pixelRatio: 2 }});
        img.style.width = '100%';
        img.style.height = 'auto';
        img.className = 'chart-static';
        el.appendChild(img);
      }}
    }});

    const clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll('.chart-container').forEach(el => {{
      const staticImg = el.querySelector('.chart-static');
      if(staticImg) {{
        el.innerHTML = '';
        el.appendChild(staticImg);
      }}
    }});
    clone.querySelectorAll('button, nav').forEach(el => el.remove());
    clone.querySelectorAll('.hidden').forEach(el => el.classList.remove('hidden'));

    const html = '<!DOCTYPE html>\\n' + clone.outerHTML;
    const blob = new Blob([html], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'APP线索广告位月报_2026年4月_' + new Date().toISOString().slice(0,10).replace(/-/g,'') + '.html';
    a.click();
    URL.revokeObjectURL(url);

    document.querySelectorAll('.chart-static').forEach(el => el.remove());
    btn.textContent = originalText;
    btn.disabled = false;
  }}, 800);
}}

window.addEventListener('DOMContentLoaded', () => {{
  updateKPI('compare');
  renderCharts();
}});
</script>
</body>
</html>
'''

with open('/Users/zhengkeying/agent teams作业/dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Dashboard generated: dashboard/index.html")
print(f"Size: {len(html)} chars")
