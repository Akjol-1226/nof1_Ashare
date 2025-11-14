#!/bin/bash

# nof1.AShare 启动脚本

echo "=================================="
echo "  nof1.AShare - 启动脚本"
echo "=================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.9+"
    exit 1
fi

echo "✅ Python已安装: $(python3 --version)"

# 检查依赖
echo ""
echo "检查Python依赖..."
if ! python3 -c "import akshare" &> /dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip3 install -r requirements.txt
else
    echo "✅ 依赖已安装"
fi

# 初始化数据库
echo ""
echo "初始化数据库..."
cd backend
python3 -c "from database import init_db; init_db()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 数据库初始化完成"
else
    echo "⚠️  数据库可能已初始化"
fi

# 启动后端
echo ""
echo "=================================="
echo "  启动后端服务"
echo "=================================="
echo ""
echo "后端将在 http://localhost:8000 启动"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 main.py


