"""周报图表生成器：调用 chart skill 生成可视化图表"""
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
cat_breakdown = data['category_breakdown']
pb_breakdown = data['price_band_breakdown']
top_resource = movers[0]['resource'] if movers else ''

# KPI 卡片 HTML
kpi_html = f'''
<div class="kpi-row">
  <div class="kpi-card">
    <div class="label">线索数</div>
    <div class="value">{cur['leads']:,}</div>
    <div class="change {'up' if mom['leads'] >= 0 else 'down'}">{'↑' if mom['leads'] >= 0 else '↓'} {abs(mom['leads'])}% vs 上月同期</div>
    <div style="font-size:12px;color:#888;margin-top:4px;">目标: {cur['leads_goal']:,}，差距: {cur['leads_gap']:+}</div>
  </div>
  <div class="kpi-card">
    <div class="label">GMV</div>
    <div class="value">¥{cur['gmv']/10000:.1f}万</div>
    <div class="change {'up' if mom['gmv'] >= 0 else 'down'}">{'↑' if mom['gmv'] >= 0 else '↓'} {abs(mom['gmv'])}% vs 上月同期</div>
    <div style="font-size:12px;color:#888;margin-top:4px;">目标: ¥{cur['gmv_goal']/10000:.1f}万，差距: ¥{cur['gmv_gap']/10000:.1f}万</div>
  </div>
  <div class="kpi-card">
    <div class="label">转化率 (CVR)</div>
    <div class="value">{cur['cvr']}%</div>
    <div class="change {'up' if mom['cvr'] >= 0 else 'down'}">{'↑' if mom['cvr'] >= 0 else '↓'} {abs(mom['cvr'])}pp vs 上月同期</div>
  </div>
  <div class="kpi-card">
    <div class="label">线索生成率</div>
    <div class="value">{cur['lead_gen_rate']}%</div>
    <div class="change {'up' if mom['lead_gen_rate'] >= 0 else 'down'}">{'↑' if mom['lead_gen_rate'] >= 0 else '↓'} {abs(mom['lead_gen_rate'])}pp vs 上月同期</div>
  </div>
</div>
'''

body_html = f'''
<div class="grid-2">
  <div class="chart-box">
    <div class="chart-title">资源位线索变化 Top5</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，按线索数变化量排序</div>
    <div id="chart-movers" style="width:100%;height:280px;"></div>
  </div>
  <div class="chart-box">
    <div class="chart-title">资源位 GMV 对比</div>
    <div class="chart-subtitle">本月MTD vs 上月同期，单位：万元</div>
    <div id="chart-gmv" style="width:100%;height:280px;"></div>
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
</div>
'''

# 图表 JS
chart_js = f'''
window.CHART_INSTANCES = [];
window.CHART_LAYOUT = 'grid';
const darkOpt = {{ backgroundColor: 'transparent' }};

// 1. 资源位线索变化
const c1 = echarts.init(document.getElementById('chart-movers'), 'dark');
c1.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    axisPointer: {{ type: 'shadow' }},
    formatter: params => {{
      const p = params[0];
      return p.name + '<br/>线索变化：<b>' + (p.value > 0 ? '+' : '') + p.value + ' 条</b>';
    }}
  }},
  grid: {{ top: 10, right: 60, bottom: 20, left: 90 }},
  xAxis: {{
    type: 'value',
    name: '线索变化（条）',
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
  series: [{{
    type: 'bar',
    data: {json.dumps([m['leads_change'] for m in movers[::-1]])},
    itemStyle: {{
      borderRadius: [0, 4, 4, 0],
      color: p => p.value >= 0 ? '#4edea3' : '#ff6b6b'
    }},
    label: {{
      show: true,
      position: 'right',
      formatter: p => (p.value > 0 ? '+' : '') + p.value + '条',
      color: '#c8cdd6',
      fontSize: 11
    }}
  }}]
}});
CHART_INSTANCES.push(c1);

// 2. 资源位 GMV 对比
const c2 = echarts.init(document.getElementById('chart-gmv'), 'dark');
c2.setOption({{
  ...darkOpt,
  tooltip: {{
    trigger: 'axis',
    formatter: params => {{
      let s = params[0].name + '<br/>';
      params.forEach(p => {{
        s += p.marker + ' ' + p.seriesName + '：<b>¥' + p.value.toFixed(1) + '万</b><br/>';
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
    name: 'GMV（万元）',
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
    {{ type: 'bar', name: '{meta['current_month']}', data: {json.dumps([round(m['gmv_cur']/10000,1) for m in movers[::-1]])}, itemStyle: {{ color: '#004ac6', borderRadius: [0,4,4,0] }} }},
    {{ type: 'bar', name: '{meta['previous_month']}', data: {json.dumps([round(m['gmv_prev']/10000,1) for m in movers[::-1]])}, itemStyle: {{ color: '#4a5568', borderRadius: [0,4,4,0] }} }}
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
