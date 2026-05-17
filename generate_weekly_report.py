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
    title = doc_title or f"APP 线索广告位投放周报（{datetime.now().strftime('%Y-%m-%d')}）"

    # 创建文档
    create_cmd = [
        'lark-cli', 'docs', '+create',
        '--api-version', 'v2',
        '--content', xml_content,
    ]
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"创建飞书文档失败: {result.stderr}")

    resp = json.loads(result.stdout)
    doc_url = resp.get('url', '')
    print(f"飞书文档已创建: {doc_url}")
    return doc_url


def main():
    """主入口：生成周报并写入飞书文档"""
    xml = generate_weekly_report()
    url = write_to_feishu_doc(xml)
    print(f"周报已发布: {url}")


if __name__ == '__main__':
    main()
