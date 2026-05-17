#!/bin/bash
set -e

cd "/Users/zhengkeying/agent teams作业"
export USE_FEISHU=true

echo "========================================"
echo "APP线索广告位周报生成流水线"
echo "========================================"

echo ""
echo "[1/3] 生成周报数据..."
python3 generate_weekly_report.py

echo ""
echo "[2/3] 生成可视化图表..."
python3 generate_weekly_charts.py

echo ""
echo "[3/3] 创建飞书文档并插入图表..."
CURRENT_MONTH=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['meta']['current_month'])")
REPORT_DATE=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['meta']['report_date'])")
MTD_DAY=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['meta']['mtd_day'])")
PREV_MONTH=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['meta']['previous_month'])")

# 读取关键指标用于文档标题
LEADS=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['summary']['current']['leads'])")
GMV=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['summary']['current']['gmv'])")
LEADS_MOM=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['summary']['mom']['leads'])")
GMV_MOM=$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['summary']['mom']['gmv'])")

# 构建 XML 内容
XML_CONTENT=$(cat <<XML
<title>APP线索广告位周报 — ${CURRENT_MONTH} 月度进度</title>
<h1>一、核心指标概览</h1>
<callout emoji="📊"><p>数据截止: ${REPORT_DATE} | MTD范围: 1-${MTD_DAY}日 | 对比: ${PREV_MONTH}同期</p></callout>
<grid>
<column width-ratio="0.25"><p><b>线索数</b></p><p>${LEADS}</p><p>${LEADS_MOM}% vs 上月同期</p></column>
<column width-ratio="0.25"><p><b>GMV</b></p><p>¥$(echo "scale=1; ${GMV}/10000" | bc)万</p><p>${GMV_MOM}% vs 上月同期</p></column>
<column width-ratio="0.25"><p><b>转化率</b></p><p>$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['summary']['current']['cvr'])")%</p></column>
<column width-ratio="0.25"><p><b>线索生成率</b></p><p>$(python3 -c "import json; print(json.load(open('weekly_report_data.json'))['summary']['current']['lead_gen_rate'])")%</p></column>
</grid>
<h1>二、可视化图表</h1>
<p>图表见下方截图，包含资源位线索变化、GMV对比、品类及价格带下钻。</p>
<h1>三、归因与行动建议</h1>
<p>详见数据分析输出，核心关注资源位效率变化及目标达成差距。</p>
XML
)

# 创建飞书文档
DOC_RESULT=$(lark-cli docs +create --api-version v2 --content "$XML_CONTENT")
DOC_TOKEN=$(echo "$DOC_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['document']['document_id'])")
DOC_URL=$(echo "$DOC_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['document']['url'])")

# 插入图表截图
cd "output/chart-html/weekly-report-${CURRENT_MONTH}"
lark-cli docs +media-insert --doc "$DOC_TOKEN" --file screenshot.png

echo ""
echo "[4/4] 推送企微机器人..."
python3 -c "
import sys, os
sys.path.insert(0, '/Users/zhengkeying/agent teams作业')
from wecom_bot import send_weekly_report
import json
with open('weekly_report_data.json', 'r') as f:
    data = json.load(f)
send_weekly_report(data, feishu_url='${DOC_URL}')
"

echo ""
echo "========================================"
echo "周报生成完成！"
echo "飞书文档: ${DOC_URL}"
echo "图表HTML: /Users/zhengkeying/agent teams作业/output/chart-html/weekly-report-${CURRENT_MONTH}/index.html"
echo "数据JSON: /Users/zhengkeying/agent teams作业/weekly_report_data.json"
echo "========================================"
