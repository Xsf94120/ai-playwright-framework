#!/usr/bin/env bash
# 一键重建开发环境（前端依赖 + 后端 venv + Playwright 浏览器）。
# 环境被重置后运行：bash scripts/setup.sh
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> [1/4] 安装前端依赖"
( cd frontend && pnpm install )

echo "==> [2/4] 重建后端 venv"
if [ ! -f backend/.venv/bin/python ]; then
  python3 -m venv backend/.venv
fi
backend/.venv/bin/pip install --upgrade pip -q

echo "==> [3/4] 安装后端依赖"
( cd backend && .venv/bin/pip install -e . -q )

echo "==> [4/4] 安装 Playwright Chromium"
backend/.venv/bin/python -m playwright install chromium

echo "==> 完成。运行 'pnpm dev' 启动服务。"
