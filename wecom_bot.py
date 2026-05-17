"""
企微机器人推送模块（复用策略复盘项目）
支持 markdown / text 消息推送
"""
import requests
import json
import os
from typing import Optional


class WeComBot:
    """企微群机器人"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_markdown(self, title: str, content: str) -> bool:
        """发送 Markdown 格式消息"""
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"**{title}**\n\n{content}"
            }
        }
        return self._send(payload)

    def send_text(self, content: str, mentioned_list: Optional[list] = None) -> bool:
        """发送文本消息"""
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or []
            }
        }
        return self._send(payload)

    def _send(self, payload: dict) -> bool:
        """发送请求"""
        if not self.webhook_url:
            print("[WeComBot] 未配置 webhook 地址，跳过发送")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()

            if result.get("errcode") == 0:
                print("[WeComBot] 消息发送成功")
                return True
            else:
                print(f"[WeComBot] 消息发送失败: {result}")
                return False

        except Exception as e:
            print(f"[WeComBot] 消息发送异常: {e}")
            return False


def get_bot() -> WeComBot:
    """从环境变量获取默认机器人实例"""
    webhook = os.environ.get('WECOM_BOT_WEBHOOK', '')
    return WeComBot(webhook)


def send_weekly_report(weekly_data: dict, feishu_url: str = '') -> bool:
    """
    发送周报摘要到企微
    """
    bot = get_bot()
    if not bot.webhook_url:
        print("[WeComBot] WECOM_BOT_WEBHOOK 未设置，跳过企微推送")
        return False

    meta = weekly_data.get('meta', {})
    summary = weekly_data.get('summary', {})
    cur = summary.get('current', {})
    mom = summary.get('mom', {})
    movers = weekly_data.get('resource_movers', [])

    # 构建 markdown 内容
    lines = [
        f"> 📅 数据截止: {meta.get('report_date', '-')} | MTD: 1-{meta.get('mtd_day', '-')}日 | 对比: {meta.get('previous_month', '-')}同期",
        "",
        "**📊 核心指标**",
        f"• 线索数: {int(cur.get('leads', 0)):,} ({mom.get('leads', 0):+.2f}%)",
        f"• GMV: ¥{cur.get('gmv', 0)/10000:.1f}万 ({mom.get('gmv', 0):+.2f}%)",
        f"• 转化率: {cur.get('cvr', 0)}% ({mom.get('cvr', 0):+.2f}pp)",
        f"• 线索生成率: {cur.get('lead_gen_rate', 0)}% ({mom.get('lead_gen_rate', 0):+.2f}pp)",
        "",
        "**📈 资源位变动 Top3**",
    ]

    for m in movers[:3]:
        arrow = '📈' if m['leads_change'] >= 0 else '📉'
        lines.append(f"{arrow} {m['resource']}: {m['leads_change']:+} 条 ({m['leads_mom']:+.1f}%)")

    # 目标差距
    leads_gap = cur.get('leads_gap', 0)
    gmv_gap = cur.get('gmv_gap', 0)
    if leads_gap != 0 or gmv_gap != 0:
        lines.append("")
        lines.append("**🎯 目标进度**")
        if leads_gap != 0:
            lines.append(f"• 线索差距: {leads_gap:+} 条")
        if gmv_gap != 0:
            lines.append(f"• GMV 差距: ¥{gmv_gap/10000:.1f}万")

    # 飞书文档链接
    if feishu_url:
        lines.append("")
        lines.append(f"📎 [查看完整报告]({feishu_url})")

    content = "\n".join(lines)
    title = f"APP线索广告位周报 — {meta.get('current_month', '-')} 月度进度"

    return bot.send_markdown(title=title, content=content)
