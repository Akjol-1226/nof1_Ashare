#!/bin/bash

# nof1.AShare 后端启动脚本

echo "=================================="
echo "  nof1.AShare - 后端启动"
echo "=================================="
echo ""

# 检查端口占用
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口8888已被占用，尝试停止现有进程..."
    PID=$(lsof -Pi :8888 -sTCP:LISTEN -t)
    kill -9 $PID 2>/dev/null
    sleep 1
fi

cd "$(dirname "$0")"

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    echo "激活虚拟环境..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

cd backend

echo "启动后端服务..."
echo "服务地址: http://localhost:8888"
echo "API文档: http://localhost:8888/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 main.py
