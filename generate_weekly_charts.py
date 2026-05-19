"""周报图表生成器：调用 chart skill 生成可视化图表（前链路版）"""
import json
import sys
import os

# 加载 chart skill 的 build_chart 模块
sys.path.insert(0, '/Users/zhengkeying/.claude/skills/chart/scripts')
import build_chart

# 修复输出目录（Mac 本地无 /data/workspace）
build_chart.CHART_HTML_DIR = os.path.join('/Users/zhengkeying/agent teams作业', 'output', 'chart-html')

from build_chart import create_project, build_chart_custom, save_chart, save_data, screenshot_chart

# 读取周报数据
with open('/Users/zhengkeying/agent teams作业/weekly_report_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

meta = data['meta']
summary = data['summary']
cur = summary['current']
prev = summary['previous']
mom = summary['mom']
movers = data['resource_movers']
gainers = data.get('top_gainers', [])
losers = data.get('top_losers', [])
cat_breakdown = data['category_breakdown']
pb_breakdown = data['price_band_breakdown']
top_resource = movers[0]['resource'] if movers else ''

# 资源位效率趋势数据（用于 CTR / 线索生成率 变化图）
eff_trends = data.get('resource_efficiency_trends', [])
eff_trends_valid = [r for r in eff_trends if r.get('exposure_cur', 0) > 0 or r.get('exposure_prev', 0) > 0]
ctr_change_data = sorted(eff_trends_valid, key=lambda x: x['ctr_change'], reverse=True)
lr_change_data = sorted(eff_trends_valid, key=lambda x: x['lead_rate_change'], reverse=True)

# KPI 卡片 HTML（前链路漏斗）
kpi_html = f'''
<div class="kpi-row">
  <div class="kpi-card">
    <div class="label">线索数（后端）</div>
    <div class="value">{cur['leads_backend']:,}</div>
    <div class="change {'up' if mom['leads'] >= 0 else 'down'}">{'↑' if mom['leads'] >= 0 else '↓'} {abs(mom['leads'])}% vs 上月同期</div>
    <div style="font-size:12px;color:#888;margin-top:4px;">目标: {cur['leads_goal']:,}，差距: {cur['leads_gap']:+}</div>
  </div>
  <div class="kpi-card">
    <div class="label">曝光 UV</div>
    <div class="value">{cur['exposure']:,}</div>
    <div class="change {'up' if mom['exposure'] >= 0 else 'down'}">{'↑' if mom['exposure'] >= 0 else '↓'} {abs(mom['exposure'])}% vs 上月同期</div>
  </div>
  <div class="kpi-card">
    <div class="label">点击 UV</div>
    <div class="value">{cur['click']:,}</div>
    <div class="change {'up' if mom['click'] >= 0 else 'down'}">{'↑' if mom['click'] >= 0 else '↓'} {abs(mom['click'])}% vs 上月同期</div>
  </div>
  <div class="kpi-card">
    <div class="label">CTR（点击率）</div>
    <div class="value">{cur['ctr']}%</div>
    <div class="change {'up' if mom['ctr'] >= 0 else 'down'}">{'↑' if mom['ctr'] >= 0 else '↓'} {abs(mom['ctr'])}pp vs 上月同期</div>
  </div>
  <div class="kpi-card">
    <div class="label">线索生成率</div>
    <div class="value">{cur['lead_rate']}%</div>
    <div class="change {'up' if mom['lead_rate'] >= 0 else 'down'}">{'↑' if mom['lead_rate'] >= 0 else '↓'} {abs(mom['lead_rate'])}pp vs 上月同期</div>
    <div style="font-size:12px;color:#888;margin-top:4px;">线索 / 曝光UV</div>
  </div>
</div>
'''

# 日度趋势数据准备
daily_trends = data.get('daily_trends', {})
max_day = meta['mtd_day']
days = list(range(1, max_day + 1))
m3_vals = [next((x['leads'] for x in daily_trends.get('2026-03', []) if x['day'] == d), 0) for d in days]
m4_vals = [next((x['leads'] for x in daily_trends.get('2026-04', []) if x['day'] == d), 0) for d in days]
m5_vals = [next((x['leads'] for x in daily_trends.get('2026-05', []) if x['day'] == d), 0) for d in days]

# 日度线索生成率数据准备
daily_lgr = data.get('daily_lead_gen_rate', {})
m3_lgr = [next((x['rate'] for x in daily_lgr.get('2026-03', []) if x['day'] == d), 0) for d in days]
m4_lgr = [next((x['rate'] for x in daily_lgr.get('2026-04', []) if x['day'] == d), 0) for d in days]
m5_lgr = [next((x['rate'] for x in daily_lgr.get('2026-05', []) if x['day'] == d), 0) for d in days]

body_html = f'''
<div class="chart-box" style="margin-bottom:20px;">
  <div class="chart-title">日度线索趋势（同期对比）</div>
  <div class="chart-subtitle">3月/4月/5月 1-{max_day}日 后端线索数 + 线索生成率（右轴）</div>
  <div id="chart-daily-trend" style="width:100%;height:360px;"></div>
</div>
<div class="grid-2">
  <div class="chart-box">
    <div class="chart-title">上升 Top 3</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，线索增长最多</div>
    <div id="chart-gainers" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">下降 Top 3</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，线索下降最多</div>
    <div id="chart-losers" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">资源位 CTR 对比</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，点击率 (%)</div>
    <div id="chart-ctr" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">「{top_resource}」品类线索分布</div>
    <div class="chart-subtitle">Top 资源位下钻：各品类线索数对比</div>
    <div id="chart-category" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">「{top_resource}」价格带线索分布</div>
    <div class="chart-subtitle">Top 资源位下钻：各价格带线索数对比</div>
    <div id="chart-priceband" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">资源位 CTR 变化</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，CTR 变化（pp）</div>
    <div id="chart-ctr-change" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">资源位 线索生成率 变化</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，线索生成率变化（pp）</div>
    <div id="chart-lr-change" style="width:100%;height:280px;"></div>
  </div>
</div>
'''

# 图表 JS
chart_js = f'''
window.CHART_INSTANCES = [];
window.CHART_LAYOUT = 'grid';
const darkOpt = {{ backgroundColor: 'transparent' }};

// 1. 上升 Top3
const c1 = echarts.init(document.getElementById('chart-gainers'), 'dark');
c1.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    axisPointer: {{ type: 'shadow' }},
    formatter: params => {{
      const p = params[0];
      return p.name + '<br/>线索变化：<b>+' + p.value + ' 条</b>';
    }}
  }},
  grid: {{ top: 10, right: 60, bottom: 20, left: 90 }},
  xAxis: {{
    type: 'value',
    name: '线索增长（条）',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'category',
    data: {json.dumps([m['resource'] for m in gainers[::-1]], ensure_ascii=False)},
    axisLabel: {{ color: '#c8cdd6', fontSize: 12 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [{{
    type: 'bar',
    data: {json.dumps([m['leads_change'] for m in gainers[::-1]])},
    itemStyle: {{
      borderRadius: [0, 4, 4, 0],
      color: '#4edea3'
    }},
    label: {{
      show: true,
      position: 'right',
      formatter: p => '+' + p.value + '条',
      color: '#c8cdd6',
      fontSize: 11
    }}
  }}]
}});
CHART_INSTANCES.push(c1);

// 1b. 下降 Top3
const c1b = echarts.init(document.getElementById('chart-losers'), 'dark');
c1b.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    axisPointer: {{ type: 'shadow' }},
    formatter: params => {{
      const p = params[0];
      return p.name + '<br/>线索变化：<b>' + p.value + ' 条</b>';
    }}
  }},
  grid: {{ top: 10, right: 60, bottom: 20, left: 90 }},
  xAxis: {{
    type: 'value',
    name: '线索下降（条）',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'category',
    data: {json.dumps([m['resource'] for m in losers[::-1]], ensure_ascii=False)},
    axisLabel: {{ color: '#c8cdd6', fontSize: 12 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [{{
    type: 'bar',
    data: {json.dumps([m['leads_change'] for m in losers[::-1]])},
    itemStyle: {{
      borderRadius: [0, 4, 4, 0],
      color: '#ff6b6b'
    }},
    label: {{
      show: true,
      position: 'right',
      formatter: p => p.value + '条',
      color: '#c8cdd6',
      fontSize: 11
    }}
  }}]
}});
CHART_INSTANCES.push(c1b);

// 2. 资源位 CTR 对比
const c2 = echarts.init(document.getElementById('chart-ctr'), 'dark');
c2.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    formatter: params => {{
      let s = params[0].name + '<br/>';
      params.forEach(p => {{
        s += p.marker + ' ' + p.seriesName + '：<b>' + p.value.toFixed(2) + '%</b><br/>';
      }});
      return s;
    }}
  }},
  legend: {{
    data: ['{meta['current_month']}', '{meta['previous_month']}'],
    textStyle: {{ color: '#c8cdd6', fontSize: 11 }},
    top: 0
  }},
  grid: {{ top: 30, right: 40, bottom: 20, left: 90 }},
  xAxis: {{
    type: 'value',
    name: 'CTR (%)',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'category',
    data: {json.dumps([m['resource'] for m in movers[::-1]], ensure_ascii=False)},
    axisLabel: {{ color: '#c8cdd6', fontSize: 12 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [
    {{ type: 'bar', name: '{meta['current_month']}', data: {json.dumps([m['ctr_cur'] for m in movers[::-1]])}, itemStyle: {{ color: '#004ac6', borderRadius: [0,4,4,0] }} }},
    {{ type: 'bar', name: '{meta['previous_month']}', data: {json.dumps([m['ctr_prev'] for m in movers[::-1]])}, itemStyle: {{ color: '#4a5568', borderRadius: [0,4,4,0] }} }}
  ]
}});
CHART_INSTANCES.push(c2);
'''

if cat_breakdown:
    cur_cats = [c for c in cat_breakdown if c['month'] == 'cur']
    prev_cats = [c for c in cat_breakdown if c['month'] == 'prev']
    cat_names = list(dict.fromkeys([c['category'] for c in cur_cats + prev_cats]))
    cur_vals = [next((c['leads'] for c in cur_cats if c['category'] == n), 0) for n in cat_names]
    prev_vals = [next((c['leads'] for c in prev_cats if c['category'] == n), 0) for n in cat_names]

    chart_js += f'''
// 3. 品类分布
const c3 = echarts.init(document.getElementById('chart-category'), 'dark');
c3.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    formatter: params => {{
      let s = params[0].name + '<br/>';
      params.forEach(p => {{
        s += p.marker + ' ' + p.seriesName + '：<b>' + p.value + ' 条</b><br/>';
      }});
      return s;
    }}
  }},
  legend: {{
    data: ['{meta['current_month']}', '{meta['previous_month']}'],
    textStyle: {{ color: '#c8cdd6', fontSize: 11 }},
    top: 0
  }},
  grid: {{ top: 30, right: 20, bottom: 50, left: 60 }},
  xAxis: {{
    type: 'category',
    data: {json.dumps(cat_names, ensure_ascii=False)},
    axisLabel: {{ rotate: 30, color: '#888', fontSize: 11 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'value',
    name: '线索数（条）',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [
    {{ type: 'bar', name: '{meta['current_month']}', data: {cur_vals}, itemStyle: {{ color: '#004ac6', borderRadius: [4,4,0,0] }} }},
    {{ type: 'bar', name: '{meta['previous_month']}', data: {prev_vals}, itemStyle: {{ color: '#4a5568', borderRadius: [4,4,0,0] }} }}
  ]
}});
CHART_INSTANCES.push(c3);
'''
else:
    chart_js += '''
const c3 = echarts.init(document.getElementById('chart-category'), 'dark');
c3.setOption({ ...darkOpt, title: { text: '无品类下钻数据', left: 'center', textStyle: { color: '#888' } } });
CHART_INSTANCES.push(c3);
'''

if pb_breakdown:
    cur_pb = [c for c in pb_breakdown if c['month'] == 'cur']
    prev_pb = [c for c in pb_breakdown if c['month'] == 'prev']
    pb_names = list(dict.fromkeys([c['price_band'] for c in cur_pb + prev_pb]))
    cur_pb_vals = [next((c['leads'] for c in cur_pb if c['price_band'] == n), 0) for n in pb_names]
    prev_pb_vals = [next((c['leads'] for c in prev_pb if c['price_band'] == n), 0) for n in pb_names]

    chart_js += f'''
// 4. 价格带分布
const c4 = echarts.init(document.getElementById('chart-priceband'), 'dark');
c4.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    formatter: params => {{
      let s = params[0].name + '<br/>';
      params.forEach(p => {{
        s += p.marker + ' ' + p.seriesName + '：<b>' + p.value + ' 条</b><br/>';
      }});
      return s;
    }}
  }},
  legend: {{
    data: ['{meta['current_month']}', '{meta['previous_month']}'],
    textStyle: {{ color: '#c8cdd6', fontSize: 11 }},
    top: 0
  }},
  grid: {{ top: 30, right: 20, bottom: 30, left: 60 }},
  xAxis: {{
    type: 'category',
    data: {json.dumps(pb_names, ensure_ascii=False)},
    axisLabel: {{ color: '#888', fontSize: 12 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'value',
    name: '线索数（条）',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [
    {{ type: 'bar', name: '{meta['current_month']}', data: {cur_pb_vals}, itemStyle: {{ color: '#004ac6', borderRadius: [4,4,0,0] }} }},
    {{ type: 'bar', name: '{meta['previous_month']}', data: {prev_pb_vals}, itemStyle: {{ color: '#4a5568', borderRadius: [4,4,0,0] }} }}
  ]
}});
CHART_INSTANCES.push(c4);
'''
else:
    chart_js += '''
const c4 = echarts.init(document.getElementById('chart-priceband'), 'dark');
c4.setOption({ ...darkOpt, title: { text: '无价格带下钻数据', left: 'center', textStyle: { color: '#888' } } });
CHART_INSTANCES.push(c4);
'''

# 5. 资源位 CTR 变化
chart_js += f'''
const c5 = echarts.init(document.getElementById('chart-ctr-change'), 'dark');
c5.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    axisPointer: {{ type: 'shadow' }},
    formatter: params => {{
      const p = params[0];
      const sign = p.value >= 0 ? '+' : '';
      return p.name + '<br/>CTR变化：<b>' + sign + p.value.toFixed(2) + 'pp</b>';
    }}
  }},
  grid: {{ top: 10, right: 60, bottom: 20, left: 90 }},
  xAxis: {{
    type: 'value',
    name: 'CTR变化（pp）',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'category',
    data: {json.dumps([m['resource'] for m in ctr_change_data[::-1]], ensure_ascii=False)},
    axisLabel: {{ color: '#c8cdd6', fontSize: 12 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [{{
    type: 'bar',
    data: {json.dumps([m['ctr_change'] for m in ctr_change_data[::-1]])},
    itemStyle: {{
      borderRadius: [0, 4, 4, 0],
      color: p => p.value >= 0 ? '#4edea3' : '#ff6b6b'
    }},
    label: {{
      show: true,
      position: 'right',
      formatter: p => {{ const sign = p.value >= 0 ? '+' : ''; return sign + p.value.toFixed(2) + 'pp'; }},
      color: '#c8cdd6',
      fontSize: 11
    }}
  }}]
}});
CHART_INSTANCES.push(c5);

// 6. 资源位线索生成率变化
const c6 = echarts.init(document.getElementById('chart-lr-change'), 'dark');
c6.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    axisPointer: {{ type: 'shadow' }},
    formatter: params => {{
      const p = params[0];
      const sign = p.value >= 0 ? '+' : '';
      return p.name + '<br/>线索生成率变化：<b>' + sign + p.value.toFixed(2) + 'pp</b>';
    }}
  }},
  grid: {{ top: 10, right: 60, bottom: 20, left: 90 }},
  xAxis: {{
    type: 'value',
    name: '线索生成率变化（pp）',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: {{
    type: 'category',
    data: {json.dumps([m['resource'] for m in lr_change_data[::-1]], ensure_ascii=False)},
    axisLabel: {{ color: '#c8cdd6', fontSize: 12 }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  series: [{{
    type: 'bar',
    data: {json.dumps([m['lead_rate_change'] for m in lr_change_data[::-1]])},
    itemStyle: {{
      borderRadius: [0, 4, 4, 0],
      color: p => p.value >= 0 ? '#4edea3' : '#ff6b6b'
    }},
    label: {{
      show: true,
      position: 'right',
      formatter: p => {{ const sign = p.value >= 0 ? '+' : ''; return sign + p.value.toFixed(2) + 'pp'; }},
      color: '#c8cdd6',
      fontSize: 11
    }}
  }}]
}});
CHART_INSTANCES.push(c6);

// 7. 日度线索趋势（同期对比）
const c7 = echarts.init(document.getElementById('chart-daily-trend'), 'dark');
c7.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    backgroundColor: '#334155',
    borderColor: 'rgba(148,163,184,0.2)',
    textStyle: {{ color: '#f8fafc' }},
    formatter: params => {{
      let s = params[0].axisValue + '日<br/>';
      params.forEach(p => {{
        if (p.seriesName.includes('生成率')) {{
          s += p.marker + ' ' + p.seriesName + '：<b>' + p.value.toFixed(3) + '%</b><br/>';
        }} else {{
          s += p.marker + ' ' + p.seriesName + '：<b>' + p.value + ' 条</b><br/>';
        }}
      }});
      return s;
    }}
  }},
  legend: {{
    data: ['3月', '4月', '5月', '3月生成率', '4月生成率', '5月生成率'],
    textStyle: {{ color: '#c8cdd6', fontSize: 11 }},
    top: 0,
    itemWidth: 14,
    itemHeight: 8
  }},
  grid: {{ top: 36, right: 70, bottom: 20, left: 60 }},
  xAxis: {{
    type: 'category',
    data: {json.dumps(days)},
    name: '日期',
    nameTextStyle: {{ color: '#888', fontSize: 11 }},
    axisLabel: {{ color: '#888' }},
    axisLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
  }},
  yAxis: [
    {{
      type: 'value',
      name: '线索数（条）',
      nameTextStyle: {{ color: '#888', fontSize: 11 }},
      axisLabel: {{ color: '#888' }},
      splitLine: {{ lineStyle: {{ color: '#2a2d3a' }} }}
    }},
    {{
      type: 'value',
      name: '线索生成率(%)',
      nameTextStyle: {{ color: '#888', fontSize: 11 }},
      axisLabel: {{ color: '#888', formatter: '{{value}}%' }},
      splitLine: {{ show: false }},
      position: 'right'
    }}
  ],
  series: [
    {{ type: 'line', name: '3月', data: {json.dumps(m3_vals)}, smooth: true, symbol: 'circle', symbolSize: 4, lineStyle: {{ width: 2 }}, itemStyle: {{ color: '#4a5568' }} }},
    {{ type: 'line', name: '4月', data: {json.dumps(m4_vals)}, smooth: true, symbol: 'circle', symbolSize: 4, lineStyle: {{ width: 2 }}, itemStyle: {{ color: '#8b5cf6' }} }},
    {{ type: 'line', name: '5月', data: {json.dumps(m5_vals)}, smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: {{ width: 3 }}, itemStyle: {{ color: '#3b82f6' }}, z: 10 }},
    {{ type: 'line', name: '3月生成率', yAxisIndex: 1, data: {json.dumps(m3_lgr)}, smooth: true, symbol: 'none', lineStyle: {{ width: 1.5, type: 'dashed' }}, itemStyle: {{ color: 'rgba(74,85,104,0.6)' }} }},
    {{ type: 'line', name: '4月生成率', yAxisIndex: 1, data: {json.dumps(m4_lgr)}, smooth: true, symbol: 'none', lineStyle: {{ width: 1.5, type: 'dashed' }}, itemStyle: {{ color: 'rgba(139,92,246,0.6)' }} }},
    {{ type: 'line', name: '5月生成率', yAxisIndex: 1, data: {json.dumps(m5_lgr)}, smooth: true, symbol: 'none', lineStyle: {{ width: 2.5, type: 'dashed' }}, itemStyle: {{ color: 'rgba(59,130,246,0.8)' }} }}
  ]
}});
CHART_INSTANCES.push(c7);
'''

project_name = f'weekly-report-{meta["current_month"]}'
project_dir = create_project(project_name, description=f'APP线索广告位周报 {meta["current_month"]} MTD', data_sources=['weekly_report_data.json'])

# 额外 CSS：chart-subtitle 样式
extra_css = '''
.chart-subtitle { font-size: 12px; color: #888; margin-bottom: 6px; margin-top: -4px; }
'''

html = build_chart_custom(
    title=f'APP线索广告位周报 — {meta["current_month"]} 月度进度',
    subtitle=f'数据截止: {meta["report_date"]} | MTD范围: 1-{meta["mtd_day"]}日 | 对比: {meta["previous_month"]}同期',
    body_html=body_html,
    chart_js=chart_js,
    kpi_html=kpi_html,
    extra_css=extra_css,
    layout='grid'
)

save_chart(html, project_dir=project_dir)
save_data(data, project_dir=project_dir)

screenshot_path = screenshot_chart(project_dir)

print(f'图表项目已生成: {project_dir}')
print(f'HTML: {project_dir}/index.html')
if screenshot_path:
    print(f'截图: {screenshot_path}')
