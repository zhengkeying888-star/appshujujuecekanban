# 企微机器人配置指南

## 1. 获取 Webhook URL（1分钟）

**方式 A：已有群机器人**
- 打开企微群 → 点击右上角「···」→「群机器人」
- 找到「郑可盈的机器人」→ 点击「查看详情」→ 复制 Webhook 地址

**方式 B：新建群机器人**
- 打开企微群 → 点击右上角「···」→「群机器人」→「添加机器人」
- 输入名字：「周报机器人」→ 点击「确定」
- 复制 Webhook 地址（格式：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx`）

## 2. 设置环境变量

打开终端，执行：

```bash
# 把下面的 URL 换成你复制的真实地址
echo 'export WECOM_BOT_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"' >> ~/.zshrc

# 立即生效
source ~/.zshrc

# 验证是否设置成功
echo $WECOM_BOT_WEBHOOK
```

> 如果用的 bash，把 `~/.zshrc` 换成 `~/.bash_profile`

## 3. 测试发送

```bash
cd "/Users/zhengkeying/agent teams作业"
python3 -c "
import json
from wecom_bot import send_weekly_report
with open('weekly_report_data.json') as f:
    data = json.load(f)
send_weekly_report(data, feishu_url='测试链接')
"
```

看到「消息发送成功」且企微群里收到消息，即配置完成。

## 4. 定时任务自动推送

已配置每周一 9:03 AM 自动跑周报流水线，完成后会自动推送到企微。

如需调整时间或关闭：
```bash
# 查看定时任务
/claude/tasks

# 删除定时任务
/CronDelete 任务ID
```
