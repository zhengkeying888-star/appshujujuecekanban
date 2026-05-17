"""周报生成器：读取 data_analysis_output.json，生成飞书文档 XML"""
import json
import subprocess
from datetime import datetime

REPORT_TEMPLATE = """<title>APP 线索广告位投放周报（{week_range}）</title>
<h1>一、核心指标概览</h1>
{kpis}
<h1>二、月度进度 vs 上月同期</h1>
{monthly_progress}
<h1>三、本周环比变化</h1>
{weekly_changes}
<h1>四、资源位效率 Top5</h1>
{resource_top5}
<h1>五、价格带结构变化</h1>
{price_band}
<h1>六、策略建议摘要</h1>
{strategy_summary}
"""


def load_analysis_data(path: str = 'data_analysis_output.json') -> dict:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"分析数据文件未找到: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {path} — {e}")


def build_kpi_cards(data: dict) -> str:
    """生成 KPI 卡片 XML（调用 data-report skill 能力）"""
    ms = data.get('monthly_summary', {})
    m3 = ms.get('2026-03', {})
    m4 = ms.get('2026-04', {})
    mom = ms.get('环比', {})

    cards = [
        ('当月累计线索数', f"{m4.get('leads', 0):,}", f"{mom.get('leads', 0):+.1f}%"),
        ('当月累计 GMV', f"¥{m4.get('gmv', 0)/10000:.1f}万", f"{mom.get('gmv', 0):+.1f}%"),
        ('首单转化率', f"{m4.get('cvr_from_leads', 0):.2f}%", f"{mom.get('cvr_from_leads', 0):+.1f}pp"),
        ('LTV 均值', f"¥{m4.get('arpu', 0):.1f}", f"{mom.get('arpu', 0):+.1f}%"),
    ]

    xml_parts = ['<grid>']
    for label, value, change in cards:
        color = 'green' if change.startswith('+') else 'red'
        xml_parts.append(
            f'<card><div style="font-size:12px;color:#666">{label}</div>'
            f'<div style="font-size:24px;font-weight:700">{value}</div>'
            f'<div style="font-size:12px;color:{color}">{change}</div></card>'
        )
    xml_parts.append('</grid>')
    return '\n'.join(xml_parts)


def build_price_band_chart(data: dict) -> str:
    """生成价格带圆环饼图（预留 chart skill 接口）"""
    pbd = data.get('price_band_distribution', [])
    if not pbd:
        return '<p>价格带数据不可用</p>'

    # 构造 ECharts 配置，供后续 chart skill 调用
    chart_config = {
        'type': 'pie',
        'radius': ['40%', '70%'],
        'data': [
            {'name': d['price_band'], 'value': d.get('april_leads', d.get('leads', 0))}
            for d in pbd
        ],
    }
    # 当前版本使用占位 div，后续可集成 chart skill 生成 base64 图片
    return f'<div style="width:100%;height:300px" data-chart="{json.dumps(chart_config, ensure_ascii=False)}"></div>'


def build_kpi_cards_enhanced(data: dict) -> str:
    """生成增强版 KPI 卡片（预留 data-report skill 接口）"""
    ms = data['monthly_summary']
    m4 = ms['2026-04']
    mom = ms['环比']

    cards = [
        {
            'label': '当月累计线索数',
            'value': f"{m4['leads']:,}",
            'change': f"{mom['leads']:+.1f}%",
            'status': 'danger' if mom['leads'] < 0 else 'success',
        },
        {
            'label': '当月累计 GMV',
            'value': f"¥{m4['gmv']/10000:.1f}万",
            'change': f"{mom['gmv']:+.1f}%",
            'status': 'danger' if mom['gmv'] < 0 else 'success',
        },
        {
            'label': '首单转化率',
            'value': f"{m4['cvr_from_leads']:.2f}%",
            'change': f"{mom['cvr_from_leads']:+.1f}pp",
            'status': 'danger' if mom['cvr_from_leads'] < 0 else 'success',
        },
        {
            'label': 'LTV 均值',
            'value': f"¥{m4['arpu']:.1f}",
            'change': f"{mom['arpu']:+.1f}%",
            'status': 'danger' if mom['arpu'] < 0 else 'success',
        },
    ]

    xml_parts = ['<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">']
    for card in cards:
        color = '#ef4444' if card['status'] == 'danger' else '#22c55e'
        xml_parts.append(
            f'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px">'
            f'<div style="font-size:12px;color:#6b7280">{card["label"]}</div>'
            f'<div style="font-size:28px;font-weight:700;margin-top:8px">{card["value"]}</div>'
            f'<div style="font-size:13px;color:{color};margin-top:4px">{card["change"]}</div>'
            f'</div>'
        )
    xml_parts.append('</div>')
    return '\n'.join(xml_parts)


def build_resource_top5(data: dict) -> str:
    """生成资源位 Top5 表格 XML"""
    re_list = data.get('resource_efficiency', [])
    top5 = sorted(re_list, key=lambda x: x.get('2026-04', {}).get('gmv', 0), reverse=True)[:5]

    rows = []
    for r in top5:
        name = r.get('resource', '未知资源位')
        m4 = r.get('2026-04', {})
        rows.append(
            f'<tr><td>{name}</td><td>{m4.get("leads", 0)}</td>'
            f'<td>¥{m4.get("gmv", 0)/10000:.1f}万</td>'
            f'<td>{m4.get("cvr_from_leads", 0):.2f}%</td></tr>'
        )

    return (
        '<table><thead><tr><th>资源位</th><th>线索数</th><th>GMV</th><th>转化率</th></tr></thead>'
        '<tbody>' + '\n'.join(rows) + '</tbody></table>'
    )


def build_strategy_summary(data: dict) -> str:
    """生成策略建议摘要"""
    cards = data.get('strategy_cards', [])
    if not cards:
        return '<p>暂无策略建议</p>'

    items = []
    for i, card in enumerate(cards[:3], 1):
        items.append(
            f'<p><strong>{i}. [{card.get("category", "未分类")}] {card.get("title", "无标题")}</strong></p>'
            f'<p>{card.get("desc", "")}</p>'
            f'<p>预计 GMV 影响: {card.get("gmv_impact", "--")} | 风险: {card.get("risk", "--")}</p>'
        )
    return '\n'.join(items)


def generate_weekly_report(output_path: str = None) -> str:
    """生成周报并返回 XML 字符串"""
    data = load_analysis_data()
    week_range = f"{datetime.now().strftime('%Y-%m-%d')} 所在周"

    report = REPORT_TEMPLATE.format(
        week_range=week_range,
        kpis=build_kpi_cards(data),
        monthly_progress='<p>月度进度数据待实现</p>',  # 需基于周数据计算
        weekly_changes='<p>周环比数据待实现</p>',
        resource_top5=build_resource_top5(data),
        price_band='<p>价格带结构待实现</p>',
        strategy_summary=build_strategy_summary(data),
    )

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


def write_to_feishu_doc(xml_content: str, doc_title: str = None) -> str:
    """将周报 XML 写入飞书文档，返回文档 URL"""
    # doc_title 保留用于 API 兼容性，实际文档标题取自 xml_content 中的 <title> 标签

    # 创建文档
    create_cmd = [
        'lark-cli', 'docs', '+create',
        '--api-version', 'v2',
        '--content', xml_content,
    ]
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"创建飞书文档失败: {result.stderr}")

    try:
        resp = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        preview = result.stdout[:500] if result.stdout else "<empty>"
        raise RuntimeError(f"飞书 API 响应 JSON 解析失败: {e} — stdout preview: {preview}")

    doc_url = resp.get('url', '')
    if not doc_url:
        preview = result.stdout[:500] if result.stdout else "<empty>"
        raise RuntimeError(f"飞书 API 响应中未包含文档 URL: {preview}")

    print(f"飞书文档已创建: {doc_url}")
    return doc_url


def main():
    """主入口：生成周报并写入飞书文档"""
    xml = generate_weekly_report()
    url = write_to_feishu_doc(xml)
    print(f"周报已发布: {url}")


if __name__ == '__main__':
    main()
