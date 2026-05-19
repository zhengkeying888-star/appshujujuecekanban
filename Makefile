# APP 线索广告位 — 自动化报告工作流
# 统一入口：make <target>

.PHONY: help cache monthly weekly full push open

PYTHON := python3
PROJECT := $(shell pwd)

help:
	@echo "可用命令:"
	@echo "  make cache    — 缓存飞书 Base 数据到本地 CSV（加速迭代）"
	@echo "  make monthly  — 生成本地 BI 看板（月报）"
	@echo "  make weekly   — 生成飞书周报文档"
	@echo "  make full     — 执行完整流水线（看板 + 周报）"
	@echo "  make open     — 在浏览器打开本地看板"
	@echo "  make push     — 提交并推送到 GitHub"

cache:
	$(PYTHON) cache_base_data.py

monthly:
	$(PYTHON) pipeline_orchestrator.py --monthly --force

weekly:
	$(PYTHON) pipeline_orchestrator.py --weekly --force

full:
	$(PYTHON) pipeline_orchestrator.py --force

open:
	open "$(PROJECT)/dashboard/v2/index.html"

push:
	git add -A
	git commit -m "chore: update dashboard & weekly report ($$(date +%Y-%m-%d))" || true
	git push origin main
