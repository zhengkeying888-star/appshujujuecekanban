"""周报自动化流水线：生成数据 → 生成图表 → 写入飞书文档（前链路版）"""
import json
import os
import subprocess
import sys
from datetime import datetime

# 配置
WEEKLY_DATA_PATH = '/Users/zhengkeying/agent teams作业/weekly_report_data.json'
CHART_SCRIPT = '/Users/zhengkeying/agent teams作业/generate_weekly_charts.py'
REPORT_CONTENT_PATH = '/Users/zhengkeying/agent teams作业/weekly_report_content.md'


def run_weekly_report():
    """运行周报数据生成"""
    print("=" * 50)
    print("[1/4] 生成周报数据...")
    result = subprocess.run(
        [sys.executable, '/Users/zhengkeying/agent teams作业/generate_weekly_report.py'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    print(result.stdout)
    return True


def run_weekly_charts():
    """运行周报图表生成"""
    print("[2/4] 生成周报图表...")
    result = subprocess.run(
        [sys.executable, CHART_SCRIPT],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    print(result.stdout)
    return True


def generate_report_content():
    """基于周报数据生成 Markdown 内容"""
    print("[3/4] 生成周报文档内容...")
    with open(WEEKLY_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data['meta']
    summary = data['summary']
    cur = summary['current']
    prev = summary['previous']
    mom = summary['mom']
    gainers = data.get('top_gainers', [])
    losers = data.get('top_losers', [])
    cat_breakdown = data['category_breakdown']
    cat_movers = data.get('category_movers', [])
    pb_breakdown = data['price_band_breakdown']

    # 品类分拆上升/下降
    cat_gainers = [c for c in cat_movers if c['direction'] == 'up']
    cat_losers = [c for c in cat_movers if c['direction'] == 'down']

    # 效率趋势关键发现（用于归因细拆文字描述）
    eff_trends = data.get('resource_efficiency_trends', [])
    eff_valid = [r for r in eff_trends if r.get('ctr_cur', 0) > 0 or r.get('ctr_prev', 0) > 0]
    ctr_best = max(eff_valid, key=lambda x: x['ctr_change']) if eff_valid else None
    ctr_worst = min(eff_valid, key=lambda x: x['ctr_change']) if eff_valid else None
    lr_best = max(eff_valid, key=lambda x: x['lead_rate_change']) if eff_valid else None
    lr_worst = min(eff_valid, key=lambda x: x['lead_rate_change']) if eff_valid else None

    # 日度线索趋势分析
    daily_trends = data.get('daily_trends', {})
    m3_daily = daily_trends.get('2026-03', [])
    m4_daily = daily_trends.get('2026-04', [])
    m5_daily = daily_trends.get('2026-05', [])
    m3_avg = round(sum(d['leads'] for d in m3_daily) / len(m3_daily), 0) if m3_daily else 0
    m4_avg = round(sum(d['leads'] for d in m4_daily) / len(m4_daily), 0) if m4_daily else 0
    m5_avg = round(sum(d['leads'] for d in m5_daily) / len(m5_daily), 0) if m5_daily else 0
    m5_peak = max(m5_daily, key=lambda x: x['leads']) if m5_daily else None
    m4_peak = max(m4_daily, key=lambda x: x['leads']) if m4_daily else None

    # 日活与线索生成率归因
    daily_dau = data.get('daily_dau', {})
    daily_lgr = data.get('daily_lead_gen_rate', {})
    mtd_day = meta['mtd_day']

    def avg_mtd(items, key):
        vals = [d[key] for d in items if d['day'] <= mtd_day]
        return round(sum(vals) / len(vals), 0) if vals else 0

    def avg_mtd_float(items, key):
        vals = [d[key] for d in items if d['day'] <= mtd_day]
        return round(sum(vals) / len(vals), 3) if vals else 0

    def total_mtd(items, key):
        return sum(d[key] for d in items if d['day'] <= mtd_day)

    m3_dau_avg = avg_mtd(daily_dau.get('2026-03', []), 'dau')
    m4_dau_avg = avg_mtd(daily_dau.get('2026-04', []), 'dau')
    m5_dau_avg = avg_mtd(daily_dau.get('2026-05', []), 'dau')
    m3_lgr_avg = avg_mtd_float(daily_lgr.get('2026-03', []), 'rate')
    m4_lgr_avg = avg_mtd_float(daily_lgr.get('2026-04', []), 'rate')
    m5_lgr_avg = avg_mtd_float(daily_lgr.get('2026-05', []), 'rate')

    m4_leads_mtd = total_mtd(daily_lgr.get('2026-04', []), 'leads')
    m5_leads_mtd = total_mtd(daily_lgr.get('2026-05', []), 'leads')
    leads_mom_pct = round((m5_leads_mtd - m4_leads_mtd) / m4_leads_mtd * 100, 1) if m4_leads_mtd else 0
    dau_mom_pct = round((m5_dau_avg - m4_dau_avg) / m4_dau_avg * 100, 1) if m4_dau_avg else 0
    lgr_mom_pct = round((m5_lgr_avg - m4_lgr_avg) / m4_lgr_avg * 100, 1) if m4_lgr_avg else 0

    # 归因判断
    if leads_mom_pct >= 0:
        if dau_mom_pct >= 0 and lgr_mom_pct >= 0:
            attribution = f"线索增长由**流量扩张**（DAU ↑{abs(dau_mom_pct)}%）与**效率提升**（生成率 ↑{abs(lgr_mom_pct)}%）双重驱动"
        elif dau_mom_pct < 0 <= lgr_mom_pct:
            attribution = f"在 DAU 下降 {abs(dau_mom_pct)}% 的背景下，线索增长完全由**转化效率驱动**（生成率 ↑{abs(lgr_mom_pct)}%）"
        elif dau_mom_pct >= 0 > lgr_mom_pct:
            attribution = f"线索增长主要由**流量扩张**（DAU ↑{abs(dau_mom_pct)}%）支撑，生成率下降 {abs(lgr_mom_pct)}% 形成部分拖累"
        else:
            attribution = "线索增长，但 DAU 与生成率均下滑，需排查数据口径"
    else:
        if dau_mom_pct < 0 and lgr_mom_pct < 0:
            attribution = f"线索下降受**流量收缩**（DAU ↓{abs(dau_mom_pct)}%）与**效率下滑**（生成率 ↓{abs(lgr_mom_pct)}%）双重拖累"
        elif dau_mom_pct >= 0 > lgr_mom_pct:
            attribution = f"在 DAU 增长 {abs(dau_mom_pct)}% 的背景下，线索下降主要由**转化效率下滑**（生成率 ↓{abs(lgr_mom_pct)}%）导致"
        else:
            attribution = f"线索下降主要由**流量收缩**（DAU ↓{abs(dau_mom_pct)}%）导致，生成率提升 {abs(lgr_mom_pct)}% 部分抵消"

    # Top 资源位（按影响绝对值最大）
    top_mover = data.get('resource_movers', [None])[0]
    if top_mover:
        top_resource = top_mover['resource']
        if top_mover['leads_change'] > 0:
            top_resource_note = f"「{top_resource}」（上升 +{int(top_mover['leads_change']):,} 条）"
        elif top_mover['leads_change'] < 0:
            top_resource_note = f"「{top_resource}」（下降 {int(top_mover['leads_change']):,} 条）"
        else:
            top_resource_note = f"「{top_resource}」"
    else:
        top_resource = '首页弹窗'
        top_resource_note = "「首页弹窗」"

    content = f"""# APP线索广告位周报 — {meta['current_month']} MTD（前链路漏斗）

> 数据截止: {meta['report_date']} | MTD范围: 1-{meta['mtd_day']}日 | 对比: {meta['previous_month']}同期
> **注：周报聚焦前链路漏斗（曝光→点击→线索），不涉及 CVR/GMV/LTV 等后链路指标**

## 一、总体指标达成情况

| 指标 | 本月MTD | 上月同期 | 环比 | 目标 | 差距 |
|------|---------|----------|------|------|------|
| 线索数（后端） | {cur['leads_backend']:,} | {prev['leads_backend']:,} | {'↑' if mom['leads'] >= 0 else '↓'} {abs(mom['leads'])}% | {cur['leads_goal']:,} | {cur['leads_gap']:+} |
| 曝光 UV | {cur['exposure']:,} | {prev['exposure']:,} | {'↑' if mom['exposure'] >= 0 else '↓'} {abs(mom['exposure'])}% | — | — |
| 点击 UV | {cur['click']:,} | {prev['click']:,} | {'↑' if mom['click'] >= 0 else '↓'} {abs(mom['click'])}% | — | — |
| CTR（点击率） | {cur['ctr']}% | {prev['ctr']}% | {'↑' if mom['ctr'] >= 0 else '↓'} {abs(mom['ctr'])}pp | — | — |
| 线索生成率 | {cur['lead_rate']}% | {prev['lead_rate']}% | {'↑' if mom['lead_rate'] >= 0 else '↓'} {abs(mom['lead_rate'])}pp | — | — |
| 月活 (MAU) | {cur.get('mau', 0):,} | {prev.get('mau', 0):,} | {'↑' if mom.get('mau', 0) >= 0 else '↓'} {abs(mom.get('mau', 0))}% | — | — |

**线索目标进度**：本月 MTD 线索 {cur['leads_backend']:,} 条，目标 {cur['leads_goal']:,} 条，达成率 {round(cur['leads_backend'] / cur['leads_goal'] * 100, 1) if cur['leads_goal'] else 0}%，缺口 {cur['leads_gap']:,} 条。

## 二、原因（双向归因）

本月线索数环比 **{'增长' if mom['leads'] >= 0 else '下降'} {abs(mom['leads'])}%**，主要由以下增长驱动因素与下降拖累因素共同作用：

### 2.1 增长驱动

**资源位上升 Top 3**

| 排名 | 资源位 | 本月线索 | 上月同期 | 变化 | 环比 | CTR变化 | 线索生成率变化 |
|------|--------|----------|----------|------|------|---------|----------------|
"""
    for idx, m in enumerate(gainers[:3], 1):
        ctr_chg = m['ctr_cur'] - m['ctr_prev']
        lr_chg = m['lead_rate_cur'] - m['lead_rate_prev']
        content += f"| {idx} | {m['resource']} | {m['leads_cur']:,} | {m['leads_prev']:,} | +{m['leads_change']:,} | ↑ {m['leads_mom']:.1f}% | {'↑' if ctr_chg >= 0 else '↓'} {abs(ctr_chg):.2f}pp | {'↑' if lr_chg >= 0 else '↓'} {abs(lr_chg):.2f}pp |\n"

    content += """
### 2.2 下降拖累

**资源位下降 Top 3**

| 排名 | 资源位 | 本月线索 | 上月同期 | 变化 | 环比 | CTR变化 | 线索生成率变化 |
|------|--------|----------|----------|------|------|---------|----------------|
"""
    for idx, m in enumerate(losers[:3], 1):
        ctr_chg = m['ctr_cur'] - m['ctr_prev']
        lr_chg = m['lead_rate_cur'] - m['lead_rate_prev']
        content += f"| {idx} | {m['resource']} | {m['leads_cur']:,} | {m['leads_prev']:,} | {m['leads_change']:,} | ↓ {abs(m['leads_mom']):.1f}% | {'↑' if ctr_chg >= 0 else '↓'} {abs(ctr_chg):.2f}pp | {'↑' if lr_chg >= 0 else '↓'} {abs(lr_chg):.2f}pp |\n"

    if cat_gainers or cat_losers:
        content += "\n**品类线索变化**\n\n"
        content += "| 品类 | 本月线索 | 上月同期 | 变化 | 环比 |\n"
        content += "|------|----------|----------|------|------|\n"
        for c in cat_gainers[:5]:
            content += f"| {c['category']} | {c['leads_cur']:,} | {c['leads_prev']:,} | ↑ {abs(c['leads_change']):,} | ↑ {abs(c['leads_mom']):.1f}% |\n"
        for c in cat_losers[:5]:
            content += f"| {c['category']} | {c['leads_cur']:,} | {c['leads_prev']:,} | ↓ {abs(c['leads_change']):,} | ↓ {abs(c['leads_mom']):.1f}% |\n"

    content += f"""\n## 三、下一步策略

1. **目标追赶**: 当前线索缺口 {cur['leads_gap']:,}，需加大高转化资源位投放力度，提升曝光规模。
2. **CTR 优化**: 重点迭代低 CTR 资源位的素材创意，提升点击吸引力。
3. **线索生成率修复**: 优化落地页体验和价格带结构，提升曝光→线索的转化效率。
4. **资源位调配**: 加推本月线索增长显著的资源位（如{top_resource}），减少低效资源位预算。

## 四、原因细拆

### 4.1 资源位效率趋势

**CTR 变化**
- CTR 提升最多：{ctr_best['resource'] if ctr_best else '—'}（{f"+{ctr_best['ctr_change']:.2f}pp" if ctr_best and ctr_best['ctr_change'] >= 0 else f"{ctr_best['ctr_change']:.2f}pp" if ctr_best else ''}）
- CTR 下降最多：{ctr_worst['resource'] if ctr_worst else '—'}（{f"{ctr_worst['ctr_change']:.2f}pp" if ctr_worst else ''}）

**线索生成率变化**
- 线索生成率提升最多：{lr_best['resource'] if lr_best else '—'}（{f"+{lr_best['lead_rate_change']:.2f}pp" if lr_best and lr_best['lead_rate_change'] >= 0 else f"{lr_best['lead_rate_change']:.2f}pp" if lr_best else ''}）
- 线索生成率下降最多：{lr_worst['resource'] if lr_worst else '—'}（{f"{lr_worst['lead_rate_change']:.2f}pp" if lr_worst else ''}）
"""

    if cat_breakdown:
        content += f"\n### 4.2 Top 资源位品类下钻\n\n"
        content += f"> 以下以本月线索变化最大的资源位{top_resource_note}为例进行下钻分析。\n\n"
        cur_cats = [c for c in cat_breakdown if c['month'] == 'cur']
        prev_cats = [c for c in cat_breakdown if c['month'] == 'prev']
        for c in cur_cats:
            prev_c = next((p for p in prev_cats if p['category'] == c['category']), None)
            if prev_c:
                cat_mom_val = (c['leads'] - prev_c['leads']) / prev_c['leads'] * 100 if prev_c['leads'] > 0 else 0
                arrow = '↑' if cat_mom_val >= 0 else '↓'
                content += f"- **{c['category']}**: 本月 {c['leads']} 条 (上月 {prev_c['leads']} 条, {arrow} {abs(cat_mom_val):.1f}%), CTR {c['ctr']}%, 线索生成率 {c['lead_rate']}%\n"
            else:
                content += f"- **{c['category']}**: 本月 {c['leads']} 条, CTR {c['ctr']}%, 线索生成率 {c['lead_rate']}%\n"

    if pb_breakdown:
        content += f"\n### 4.3 价格带结构\n\n"
        cur_pb = [c for c in pb_breakdown if c['month'] == 'cur']
        prev_pb = [c for c in pb_breakdown if c['month'] == 'prev']
        pb_summary = []
        for c in cur_pb:
            prev_p = next((p for p in prev_pb if p['price_band'] == c['price_band']), None)
            if prev_p:
                pb_mom_val = (c['leads'] - prev_p['leads']) / prev_p['leads'] * 100 if prev_p['leads'] > 0 else 0
                arrow = '↑' if pb_mom_val >= 0 else '↓'
                pb_summary.append(f"{c['price_band']} {c['leads']}条(上月{prev_p['leads']}条,{arrow}{abs(pb_mom_val):.1f}%)")
            else:
                pb_summary.append(f"{c['price_band']} {c['leads']}条")
        content += "本月「{}」价格带分布：{}。\n".format(top_resource, "；".join(pb_summary))

    if m3_daily or m4_daily or m5_daily:
        content += f"""\n### 4.4 日度线索趋势与流量-效率归因

**日均线索对比**
- 3月 1-{meta['mtd_day']}日 日均线索：{int(m3_avg):,} 条，日均DAU {int(m3_dau_avg):,}，平均线索生成率 {m3_lgr_avg:.3f}%
- 4月 1-{meta['mtd_day']}日 日均线索：{int(m4_avg):,} 条，日均DAU {int(m4_dau_avg):,}，平均线索生成率 {m4_lgr_avg:.3f}%
- 5月 1-{meta['mtd_day']}日 日均线索：{int(m5_avg):,} 条，日均DAU {int(m5_dau_avg):,}，平均线索生成率 {m5_lgr_avg:.3f}%

**峰值对比**
- 5月峰值：{m5_peak['day'] if m5_peak else '—'}日（{int(m5_peak['leads']) if m5_peak else 0:,} 条）
- 4月峰值：{m4_peak['day'] if m4_peak else '—'}日（{int(m4_peak['leads']) if m4_peak else 0:,} 条）

**趋势判断**
本月（5月）1-{meta['mtd_day']}日日均线索 {int(m5_avg):,} 条，{'高于' if m5_avg >= m4_avg else '低于'} 4月同期（{int(m4_avg):,} 条），{'高于' if m5_avg >= m3_avg else '低于'} 3月同期（{int(m3_avg):,} 条）。

**流量 vs 效率归因**
5月线索环比 **{'增长' if leads_mom_pct >= 0 else '下降'} {abs(leads_mom_pct)}%**，归因拆解如下：
- **流量端（DAU）**：日均日活 {int(m5_dau_avg):,}，环比 4月同期 {'↑' if dau_mom_pct >= 0 else '↓'} {abs(dau_mom_pct)}%，对线索为{'正向' if dau_mom_pct >= 0 else '负向'}贡献
- **效率端（线索生成率）**：均值 {m5_lgr_avg:.3f}%，环比 4月同期 {'↑' if lgr_mom_pct >= 0 else '↓'} {abs(lgr_mom_pct)}%，对线索为{'正向' if lgr_mom_pct >= 0 else '负向'}贡献

**核心判断**：{attribution}。增长质量{'较高' if dau_mom_pct < 0 <= leads_mom_pct else '需关注' if dau_mom_pct < 0 and leads_mom_pct < 0 else '良好'}。
"""

    content += f"""\n## 五、指标口径说明

**本月MTD**：本月 1 日至最新数据日期（{meta['mtd_day']}日）的累计数据，与上月同期的 1-{meta['mtd_day']}日做对比。

**所有率值公式定义**：

| 指标 | 公式 | 说明 |
|------|------|------|
| CTR（点击率） | 点击UV / 曝光UV × 100% | 衡量素材吸引力 |
| 线索生成率 | 线索数 / 曝光UV × 100% | 衡量曝光到线索的转化效率 |
| 线索环比 | (本月线索 − 上月同期线索) / 上月同期线索 × 100% | 基于后端总线索数 |
| 曝光环比 | (本月曝光 − 上月同期曝光) / 上月同期曝光 × 100% | 基于前链路曝光UV |
| CTR变化 | 本月CTR − 上月CTR | 单位：pp（百分点） |
| 线索生成率变化 | 本月线索生成率 − 上月线索生成率 | 单位：pp（百分点） |
    """

    with open(REPORT_CONTENT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"周报内容已保存: {REPORT_CONTENT_PATH}")
    return True


def write_to_feishu():
    """将周报内容写入飞书文档"""
    print("[4/4] 写入飞书文档...")
    with open(REPORT_CONTENT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    result = subprocess.run(
        ['lark-cli', 'docs', '+create', '--api-version', 'v2', '--doc-format', 'markdown', '--content', content],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False

    try:
        resp = json.loads(result.stdout)
        if resp.get('ok'):
            doc = resp['data']['document']
            print(f"飞书文档创建成功: {doc['url']}")
            # 保存文档URL到文件以便后续更新
            with open('/Users/zhengkeying/agent teams作业/.last_weekly_doc.json', 'w') as f:
                json.dump({'url': doc['url'], 'doc_id': doc['document_id'], 'date': datetime.now().isoformat()}, f)
            return True
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Output: {result.stdout}")
    return False


def main():
    print(f"开始执行周报流水线: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查数据文件是否存在
    if not os.path.exists('/Users/zhengkeying/agent teams作业/更新4-5月app数据.xlsx'):
        print("ERROR: 后链路数据文件不存在，请确认数据已更新")
        return 1

    if not run_weekly_report():
        return 1
    if not run_weekly_charts():
        return 1
    if not generate_report_content():
        return 1
    if not write_to_feishu():
        return 1

    print("=" * 50)
    print("周报流水线执行完成!")
    print(f"图表位置: /Users/zhengkeying/agent teams作业/output/chart-html/weekly-report-2026-05/")
    return 0


if __name__ == '__main__':
    sys.exit(main())
