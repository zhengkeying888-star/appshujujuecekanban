#!/bin/bash
# 设置定时任务

PROJECT_DIR="/Users/zhengkeying/agent teams作业"
CRON_WEEKLY="0 9 * * 1 cd \"$PROJECT_DIR\" && USE_FEISHU=true python3 generate_weekly_report.py >> cron.log 2>&1"
CRON_MONTHLY="0 9 1 * * cd \"$PROJECT_DIR\" && USE_FEISHU=true python3 generate_analysis.py && python3 generate_dashboard_v2.py >> cron.log 2>&1"

# 添加到当前用户的 crontab
(crontab -l 2>/dev/null; echo "$CRON_WEEKLY"; echo "$CRON_MONTHLY") | crontab -

echo "定时任务已配置:"
crontab -l | grep -E "weekly_report|generate_analysis"
