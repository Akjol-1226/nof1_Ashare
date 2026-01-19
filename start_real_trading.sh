#!/bin/bash

echo "🚀 启动AI股票交易系统 - 真实交易模式"
echo "====================================="

# 检查Python环境
echo "📋 检查环境..."
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js未安装"
    exit 1
fi

# 检查端口占用
echo "🔍 检查端口占用..."
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ 端口8888已被占用，请先停止其他服务"
    exit 1
fi

if lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ 端口3002已被占用，请先停止其他服务"
    exit 1
fi

echo "✅ 环境检查通过"

# 启动后端服务
echo ""
echo "🔧 启动后端服务..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..
echo "✅ 后端服务启动 (PID: $BACKEND_PID)"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否正常运行
if ! curl -s http://localhost:8888/ > /dev/null; then
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ 后端服务运行正常"

# 启动前端服务
echo ""
echo "🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ 前端服务启动 (PID: $FRONTEND_PID)"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
sleep 5

echo ""
echo "🎉 系统启动完成！"
echo "====================================="
echo "📊 前端界面: http://localhost:3002"
echo "🔗 后端API: http://localhost:8888"
echo "📈 WebSocket测试: file://$(pwd)/test_websocket_browser.html"
echo ""
echo "💡 当前状态:"
echo "   • 3个AI已配置: Qwen3-Max, Kimi K2, DeepSeek V3.1"
echo "   • 包含3天历史数据用于图表显示"
echo "   • WebSocket实时数据推送已配置"
echo ""
echo "⚠️  按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT

# 保持脚本运行
while true; do
    sleep 1

    # 检查服务是否还在运行
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ 后端服务异常退出"
        kill $FRONTEND_PID 2>/dev/null
        exit 1
    fi

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ 前端服务异常退出"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done
