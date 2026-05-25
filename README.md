# APP 线索广告位数据决策看板

APP 线索广告位复盘月报 + 周报自动化工作流。基于飞书多维表格（Base）或本地 Excel 数据源，自动生成：

- **BI 看板**（`dashboard/v2/index.html`）：月报级多屏叙事看板，支持 3月/4月/5月/对比/周报视图切换
- **飞书周报文档**：MTD 进度 + 同期对比 + 前链路漏斗归因
- **周报图表**（`output/chart-html/`）：ECharts 交互图表 + PNG 截图

## 快速开始

### 1. 依赖安装

```bash
pip install pandas openpyxl
# 可选：飞书 Base 数据源需要 lark-cli
# npm install -g @larksuite/lark-cli
```

### 2. 配置飞书 Base（可选，默认使用本地 Excel）

设置环境变量覆盖 Base token（推荐）：

```bash
export FEISHU_BASE_TOKEN="your_base_token"
```

或在 `.env` 文件中配置（`.env` 已加入 `.gitignore`）：

```bash
FEISHU_BASE_TOKEN=your_base_token
```

### 3. 运行工作流

| 命令 | 说明 |
|------|------|
| `make cache` | 缓存飞书 Base 数据到本地 CSV（加速迭代） |
| `make monthly` | 仅生成本地 BI 看板（月报） |
| `make weekly` | 仅生成飞书周报文档 |
| `make full` | 执行完整流水线（看板 + 周报） |
| `make open` | 在浏览器打开本地看板 |

等价于直接调用：

```bash
# 完整流水线
python3 pipeline_orchestrator.py --force

# 仅月报/看板
python3 pipeline_orchestrator.py --monthly --force

# 仅周报
python3 pipeline_orchestrator.py --weekly --force
```

## 项目结构

```
.
├── pipeline_orchestrator.py      # 统一入口：检测 → 拉取 → 分析 → 输出
├── run_weekly_pipeline.py        # 周报专用流水线（数据 → 图表 → 飞书文档）
├── generate_analysis.py          # 数据清洗与聚合 → data_analysis_output.json
├── generate_dashboard_v2.py      # BI 看板生成器 → dashboard/v2/index.html
├── generate_weekly_report.py     # 周报数据生成器 → weekly_report_data.json
├── generate_weekly_charts.py     # 周报图表生成器 → output/chart-html/
├── feishu_reader.py              # 飞书 Base 数据读取封装
├── neon_reader.py                # Neon PostgreSQL 数据读取封装
├── db.py                         # 数据库连接管理（psycopg v3）
├── schema.sql                    # PostgreSQL 建表语句
├── migrate_to_neon.py            # 本地 Excel → Neon 数据迁移脚本
├── feishu_config.py              # Base 表配置（table_id / token）
├── cache_base_data.py            # Base → 本地 CSV 缓存
├── dashboard/v2/index.html       # 最终交付物（本地看板）
├── Makefile                      # 便捷命令封装
└── README.md                     # 本文档
```

## 数据源

支持三种数据源模式，通过环境变量切换：

### 模式 A：飞书 Base（团队协作）

数据存储在飞书多维表格，支持多人协作更新：

```bash
export USE_FEISHU=true
export USE_FEISHU_CACHE=true   # 启用本地 CSV 缓存，加速迭代
make full
```

Base 表清单：

| 表名 | 说明 |
|------|------|
| `backend_data_2026_03/04/05` | 后链路线索明细（按月拆分） |
| `frontend_data_2026_03/04_p1/04_p2/05_p1/05_p2` | 前链路广告位明细（按月拆分） |
| `mau_data` | 月活数据 |
| `daily_dau` | 日活数据 |
| `category_mapping` | 品类映射 |

### 模式 B：Neon PostgreSQL（推荐，Vercel 部署）

数据存储在 Vercel 集成的 Neon 数据库，支持云端查询和长期归档：

**首次配置步骤：**

1. 在 [Vercel Dashboard](https://vercel.com/dashboard) → Storage → 创建 Neon 数据库
2. 复制 `DATABASE_URL`（确保是 **pooled** 连接串，含 `-pooler.`）
3. 设置环境变量并迁移数据：

```bash
# 设置连接字符串
export DATABASE_URL='postgresql://user:pass@host-pooler.neon.tech/dbname?sslmode=require'

# 安装依赖
pip install -r requirements.txt

# 迁移本地 Excel 数据到 Neon（一次性）
make neon-migrate

# 后续运行流水线
make neon-full
```

数据库表结构：

| 表名 | 说明 |
|------|------|
| `backend_leads` | 后链路线索明细（核心字段 + JSONB 扩展） |
| `frontend_daily` | 前链路日汇总 |
| `mau_monthly` | 月活数据 |
| `daily_dau` | 日活数据 |
| `category_mapping` | 品类映射 |

### 模式 C：本地 Excel（单机运行）

不使用任何外部数据源，直接读取本地 Excel 文件。需确保以下文件存在：

- `更新4-5月app数据.xlsx` — 后链路数据
- `APP广告位明细3月汇总.xlsx` / `4月广告位明细.xlsx` / `5.1-17广告位明细.xlsx` — 前链路数据
- `mau_data_3_4_5.xlsx` — 月活数据
- `日维度日活3-5月.xlsx` — 日活数据

## 命令速查

| 命令 | 说明 |
|------|------|
| `make cache` | 缓存飞书 Base 数据到本地 CSV |
| `make monthly` / `make weekly` / `make full` | 飞书 Base 模式运行 |
| `make neon-migrate` | 本地 Excel → Neon 迁移 |
| `make neon-monthly` / `make neon-weekly` / `make neon-full` | Neon 模式运行 |
| `make open` | 打开本地看板 |
| `make push` | 提交并推送到 GitHub |

## 流水线说明

```
飞书 Base / 本地 Excel
  → pipeline_orchestrator.py
    → generate_analysis.py        → data_analysis_output.json
    → generate_dashboard_v2.py    → dashboard/v2/index.html
    → generate_weekly_report.py   → weekly_report_data.json
    → generate_weekly_charts.py   → output/chart-html/
    → run_weekly_pipeline.py      → 飞书文档
```

## 关键约定

- **转化率口径**：`SUM(首单数) / SUM(线索数)`，严禁对原始 `转化率` 字段取 AVG
- **合计行过滤**：计算前必须过滤 `stat_month == '合计'` 的行
- **资源位列表**（`TARGET_RESOURCES`）与**广告位名称映射**（`AD_NAME_MAP`）为业务契约，修改需经明确授权

## 提交与推送

```bash
make push
```

或手动：

```bash
git add -A
git commit -m "chore: update dashboard & weekly report"
git push origin main
```
