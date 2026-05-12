# CLAUDE.md — APP 线索广告位复盘月报

## 项目概述

基于 `APP线索广告位拆解3-4月.xlsx`（约 3.6 万行投放明细）构建的单文件 HTML BI 看板，支持 3月/4月/3-4月对比三种视图切换与一键导出 HTML 月报。

## 技术栈

- **前端**：单文件 HTML，Tailwind CSS CDN + ECharts 5.5 + ECharts WordCloud 2.1.0
- **数据预处理**：Python 3 + pandas
- **字体**：Noto Sans SC + Inter + Material Symbols Outlined
- **输出**：`dashboard/index.html`（纯静态，无后端依赖）

## 文件结构

```
.
├── APP线索广告位拆解3-4月.xlsx   # 主数据源（35 列，含 stat_month, 广告资源位, 广告位素材, 线索数, 首单数, 首单流水, LTV, category_name, sku_price, 面向人群）
├── APP品类流量结构.csv            # 品类流量结构数据源（区分正式品/孵化品）
├── generate_analysis.py          # 数据清洗与聚合分析脚本
├── data_analysis_output.json     # 分析结果 JSON（被 dashboard 内嵌读取）
├── generate_dashboard.py         # HTML 看板生成器（Python f-string 模板）
├── dashboard/index.html          # 最终交付物（单文件可运行）
├── product_requirements.md       # PRD
└── CLAUDE.md                     # 本文件
```

## 构建流程

```
generate_analysis.py
  → 读取 Excel + CSV
  → 清洗、过滤合计行、计算指标
  → 输出 data_analysis_output.json

generate_dashboard.py
  → 读取 data_analysis_output.json
  → Python f-string 拼接 HTML（含内嵌 CSS + JS + RAW_DATA）
  → 输出 dashboard/index.html
```

**每次数据或模板改动后，必须依次运行两个脚本：**

```bash
python3 generate_analysis.py   # 生成 data_analysis_output.json
python3 generate_dashboard.py  # 生成 dashboard/index.html
```

## 关键约定（不可违背）

### 1. 转化率口径
- **唯一正确公式**：`SUM(首单数) / SUM(线索数)`
- **严禁**直接对原始数据中的 `转化率` 字段取 AVG
- 在 `generate_analysis.py` 中所有聚合函数（`agg`, `agg2`, `agg_rc`）均按此计算
- HTML 中也在「指标口径说明」区块明确告知用户

### 2. 合计行过滤
- 原始数据中存在 `stat_month == '合计'` 的汇总行
- **必须在任何计算前过滤**：`df = df[df['stat_month'] != '合计']`
- 漏过滤会导致数据翻倍（3月线索数会从 18,066 变成 36,132）

### 3. 卖点提取
- 从 `广告位素材` 字段中提取 `【】` 内的内容
- 正则：`re.search(r'【(.+?)】', text)`
- **不要**提取品类名或其他无关文本

### 4. 月份切换实现
- CSS 列级显隐：`body.view-march .col-april { display: none }`
- JS `updateKPI(month)` 动态更新 5 张 KPI 卡片数值
- JS `renderCharts()` 根据 `currentMonth` 切换趋势图/饼图/品类图/旭日图数据源
- 表格表头和单元格必须有 `col-march` / `col-april` / `col-compare` 类

### 5. 综合得分（资源位×品类）
- 仅对 4月线索数 ≥ 20 的组合计算
- `score = CVR_norm * 0.4 + GMV_norm * 0.35 + Leads_norm * 0.25`
- Min-Max 归一化到 0-100，基于所有达标组合

### 6. 价格带映射
- `0元` / `1.1元` / `3.9元` / `其他`
- 直接按 `sku_price` 精确匹配，不要四舍五入

### 7. 品类名称映射（正式品/孵化品）
- Excel `category_name` 与 CSV `品类` 优先精确匹配
- 未命中则 fallback 到包含匹配（Excel 名称包含于 CSV 名称，或反之）
- 仍未命中则标记为「未分类」
- 映射结果写入 `df['cat_type']`，用于价格带×品类类型分析和资源位×品类类型分析

### 8. ECharts 旭日图（价格带×品类类型）
- 两层结构：内圈 `r0: '20%', r: '55%'` = 价格带；外圈 `r0: '55%', r: '70%'` = 正式品/孵化品
- 外圈颜色固定：正式品 `#004ac6`，孵化品 `#4edea3`
- `label.formatter` 中**严禁使用 `\n`**（Python f-string 会将其转为真实换行，导致 JS 语法错误）

### 9. f-string 中的转义陷阱
- **严禁**在 f-string 内使用 `\n`、 `\'`、 `\"` 等反斜杠转义序列
- f-string 表达式中的反斜杠在 Python 3.12+ 之前直接报 SyntaxError；即使不报错，`
` 也会变成真实换行符注入 JS，导致整个 `renderCharts()` 函数解析失败、所有图表空白
- **正确做法**：用普通字符串拼接，或在 f-string 外预处理换行

### 10. 资源位衰退预警
- 规则：CVR 环比下滑 ≥ 10% 标黄「预警」，否则「正常」
- 数据来源：直接使用 `resource_efficiency` 中已计算的环比数据，无需额外聚合
- 呈现：在资源位效率矩阵表格最右列，用 badge 样式展示

### 11. 资源位×价格带效率矩阵
- 聚合维度：`广告资源位` × `price_band` × `stat_month`
- 每价格带展示 3 个指标：线索数、首单数、CVR（`SUM(首单数) / SUM(线索数)`）
- 底部汇总行：纵向合计全部 15 资源位在各价格带下的数据
- 月份切换采用 **tbody 级显隐**（而非列级显隐）：生成三个独立 tbody（`#rp-march` / `#rp-april` / `#rp-compare`），通过 CSS 控制 `display: none`
- 对比视图下 CVR 列附带环比变化（颜色 + 箭头）

## 15 个目标资源位（固定列表）

```python
TARGET_RESOURCES = [
    '选课中心', '首页弹窗', '学习页', '学习中心', '学习中心弹窗',
    '2025首页卡片1', '2025首页卡片5', '2025首页卡片10',
    '2025首页banner', '2025课程banner', '热门推荐', '好课上新',
    '名师好课', '个人主页', '社区koc'
]
```

## 新增模块注意事项

若后续增加新的分析模块，必须：
1. 在 `generate_analysis.py` 中新增计算逻辑，将结果写入 `data_analysis_output.json`
2. 在 `generate_dashboard.py` 中新增 HTML 区块和对应的 JS 图表初始化代码
3. 若涉及表格列，给表头和单元格加上 `col-march` / `col-april` / `col-compare` 类以支持月份切换
4. 若涉及图表，在 `renderCharts()` 中根据 `currentMonth` 切换数据（参考趋势图/饼图/品类图/旭日图写法）
5. 若涉及诊断文案动态数据，在 `generate_dashboard.py` 顶部 Python 逻辑中预计算，再注入 f-string

## 常见问题

| 问题 | 原因 | 解决 |
|-----|------|------|
| 3月线索数显示 36,132 | 合计行未过滤 | 检查 `df = df[df['stat_month'] != '合计']` 是否在计算前执行 |
| 卖点关键词提取错误 | 正则未匹配 `【】` | 确认使用 `re.search(r'【(.+?)】', text)` |
| 月份切换没区别 | CSS/JS 未正确注入 | 检查 `col-march/april/compare` 类、`updateKPI()`、`renderCharts()` 是否存在 |
| f-string SyntaxError | f-string 表达式中包含反斜杠转义引号 | 改用字符串拼接，不要在 f-string 内用 `\'` 或 `\"` |
| **所有 ECharts 图表空白** | f-string 中 `\n` 注入 JS 导致语法错误 | 将 `label: { formatter: '{b}\\n{d}%' }` 改为 `'{b} {d}%'` 或拼接处理 |
| 品类流量结构 CSV 解析错误 | 该 CSV 为左右并排双表格式 | 分别取左 8 列（4月）和右 8 列（3月）解析，参考 `generate_analysis.py` 第 210-256 行 |
| 品类名称映射不一致 | Excel `category_name` 与 CSV `品类` 命名差异 | 使用精确匹配 + 包含匹配 fallback，未命中标记「未分类」 |
| NameError 'apr' | `price_band_type` 计算在 CSV 解析之前 | 确保 `cat_type` 映射和 `price_band_type` 计算在 CSV 解析之后执行 |
| 价格带矩阵月份切换无效 | 同一 tbody 内混合了多个月份的行数据 | 使用三个独立 tbody（`#rp-march/april/compare`），通过 CSS 控制 tbody 显隐，而非列级显隐 |
| 健康状态列显示错位 | 表头新增了列但 tbody 行内未同步增加对应 td | 确保 `res_rows` 生成逻辑与表头 th 数量一致 |

## 数据验证基准

以下数值可作为每次修改后的快速校验：

| 指标 | 3月 | 4月 | 环比 |
|-----|-----|-----|------|
| 线索数 | 18,066 | 17,492 | -3.18% |
| 首单数 | 2,636 | 1,894 | -28.15% |
| 首单流水 | ¥454.58万 | ¥322.28万 | -29.10% |
| 整体转化率 | 7.30% | 5.41% | -25.89% |
| LTV 均值 | ¥125.97 | ¥92.12 | -26.88% |
| 0元课占比 | 80.15% | 80.77% | +0.62pp |
| 1.1元课占比 | 12.25% | 11.21% | -1.04pp |
| 3.9元课占比 | 4.90% | 5.82% | +0.92pp |
| 其他价格带占比 | 2.70% | 2.20% | -0.50pp |
