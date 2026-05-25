#!/usr/bin/env python3
"""APP 线索广告位自动报告流水线（Base 数据源）

统一入口：自动检测 Base 变化 → 拉取数据 → 生成看板 → 输出飞书周报/月报

Usage:
    python3 pipeline_orchestrator.py           # 检测变化后执行
    python3 pipeline_orchestrator.py --force   # 强制执行，跳过变化检测
    python3 pipeline_orchestrator.py --weekly  # 仅执行周报流水线
    python3 pipeline_orchestrator.py --monthly # 仅执行月报/看板流水线
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 企微推送
sys.path.insert(0, str(Path(__file__).parent))
from wecom_bot import send_weekly_report

PROJECT_DIR = Path(__file__).parent.resolve()
STATE_FILE = PROJECT_DIR / '.auto_report_state.json'
LAST_DOC_FILE = PROJECT_DIR / '.last_weekly_doc.json'

# 各数据源表名（与 feishu_config.py 对应）
DATA_TABLES = [
    'backend_data_2026_03',
    'backend_data_2026_04',
    'backend_data_2026_05',
    'frontend_data_2026_03',
    'frontend_data_2026_04_p1',
    'frontend_data_2026_04_p2',
    'frontend_data_2026_05',
    'mau_data',
    'category_mapping',
    'daily_dau',
]


def run_script(script_name: str, env: dict = None, cwd: Path = None) -> subprocess.CompletedProcess:
    """运行项目中的 Python 脚本"""
    script_path = (cwd or PROJECT_DIR) / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    cmd = [sys.executable, str(script_path)]
    merged_env = {**os.environ, **(env or {})}
    result = subprocess.run(cmd, capture_output=True, text=True, env=merged_env, cwd=str(cwd or PROJECT_DIR))

    print(result.stdout, end='')
    if result.returncode != 0:
        print(f"\n[ERROR] {script_name} failed (exit {result.returncode}):\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"{script_name} failed")
    return result


def load_state() -> dict:
    """加载上次处理状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    """保存处理状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_base_update(state: dict) -> tuple[bool, str]:
    """检测 Base 是否有新数据

    简化策略：对比上次运行时各脚本的输出文件修改时间。
    未来可扩展为直接查询 Base 最新记录日期/总数。
    """
    # 如果从未运行过，视为有变化
    if not state:
        return True, "首次运行"

    # 检查关键输出文件是否存在且较新
    outputs = state.get('outputs', {})
    dashboard_json = PROJECT_DIR / 'data_analysis_output.json'
    weekly_json = PROJECT_DIR / 'weekly_report_data.json'

    if not dashboard_json.exists() or not weekly_json.exists():
        return True, "输出文件缺失"

    # 如果输出文件生成时间早于今天 00:00，且今天是新的一天，视为可能有变化
    # 实际项目中建议用 Base 查询替代
    last_run = state.get('last_run')
    if last_run:
        last_run_dt = datetime.fromisoformat(last_run)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if last_run_dt < today:
            return True, f"上次运行是 {last_run_dt.date()}，已跨天"

    return False, "数据已是最新"


def run_monthly_pipeline(env: dict) -> dict:
    """执行月报/看板流水线"""
    outputs = {}

    print(">>> [1/6] generate_analysis.py — 数据清洗与聚合")
    run_script("generate_analysis.py", env)
    outputs["dashboard_json"] = str(PROJECT_DIR / "data_analysis_output.json")

    print(">>> [2/6] generate_dashboard_v2.py — 生成 BI 看板")
    run_script("generate_dashboard_v2.py", env)
    outputs["dashboard_html"] = str(PROJECT_DIR / "dashboard" / "v2" / "index.html")

    return outputs


def run_weekly_pipeline(env: dict) -> dict:
    """执行周报流水线"""
    outputs = {}

    print(">>> [3/6] generate_weekly_report.py — 生成周报数据")
    run_script("generate_weekly_report.py", env)
    outputs["weekly_json"] = str(PROJECT_DIR / "weekly_report_data.json")

    print(">>> [4/6] generate_weekly_charts.py — 生成周报图表")
    run_script("generate_weekly_charts.py", env)

    print(">>> [5/6] run_weekly_pipeline.py — 输出飞书周报文档")
    run_script("run_weekly_pipeline.py", env)

    # 读取生成的文档链接
    feishu_url = ''
    if LAST_DOC_FILE.exists():
        with open(LAST_DOC_FILE, 'r', encoding='utf-8') as f:
            doc_meta = json.load(f)
        feishu_url = doc_meta.get('url', '')
        outputs["feishu_doc_url"] = feishu_url

    # 企微推送
    weekly_json_path = PROJECT_DIR / 'weekly_report_data.json'
    if weekly_json_path.exists():
        with open(weekly_json_path, 'r', encoding='utf-8') as f:
            weekly_data = json.load(f)
        print(">>> [6/6] 企微推送 — 发送周报摘要")
        ok = send_weekly_report(weekly_data, feishu_url=feishu_url)
        outputs["wecom_sent"] = ok
    else:
        outputs["wecom_sent"] = False

    return outputs


def run_pipeline(force: bool = False, weekly: bool = True, monthly: bool = True) -> dict:
    """执行完整报告流水线"""
    use_neon = os.environ.get('USE_NEON', 'false').lower() == 'true'
    use_feishu = os.environ.get('USE_FEISHU', 'false').lower() == 'true' and not use_neon
    source_name = "Neon PostgreSQL" if use_neon else ("飞书 Base" if use_feishu else "本地 Excel")

    print("=" * 60)
    print("APP 线索广告位 — 自动报告流水线")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据源: {source_name}")
    print(f"模式: force={force}, weekly={weekly}, monthly={monthly}")
    print("=" * 60)
    print()

    state = load_state()

    # 1. 检测变化
    if not force:
        has_update, reason = check_base_update(state)
        if not has_update:
            print(f"[SKIP] 无需执行: {reason}")
            return {"status": "skipped", "reason": reason}
        print(f"[DETECT] 检测到变化: {reason}")
    else:
        print("[FORCE] 跳过变化检测，强制执行")

    # 2. 设置环境变量
    env = {}
    if use_neon:
        env["USE_NEON"] = "true"
    elif use_feishu:
        env["USE_FEISHU"] = "true"
    outputs = {}

    try:
        if monthly:
            monthly_outputs = run_monthly_pipeline(env)
            outputs.update(monthly_outputs)

        if weekly:
            weekly_outputs = run_weekly_pipeline(env)
            outputs.update(weekly_outputs)

        # 3. 保存状态
        state = {
            "last_run": datetime.now().isoformat(),
            "outputs": outputs,
        }
        save_state(state)

        print()
        print("=" * 60)
        print("流水线执行成功")
        print("=" * 60)
        for k, v in outputs.items():
            print(f"  • {k}: {v}")
        print("=" * 60)

        return {"status": "success", "outputs": outputs}

    except RuntimeError as e:
        print()
        print("=" * 60)
        print(f"流水线执行失败: {e}")
        print("=" * 60)
        return {"status": "error", "message": str(e)}


if __name__ == '__main__':
    force = '--force' in sys.argv
    weekly_only = '--weekly' in sys.argv
    monthly_only = '--monthly' in sys.argv

    if weekly_only and monthly_only:
        print("[ERROR] --weekly 和 --monthly 不能同时使用")
        sys.exit(1)

    weekly = not monthly_only
    monthly = not weekly_only

    result = run_pipeline(force=force, weekly=weekly, monthly=monthly)
    sys.exit(0 if result["status"] == "success" else 1)
