#!/bin/bash
# nof1.AShare 停止脚本

echo "🛑 停止 nof1.AShare 系统..."
echo ""

cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 方法1: 杀死 start_system.sh 及其所有子进程
echo "查找并终止 start_system.sh 进程..."
START_PIDS=$(pgrep -f "start_system.sh")
if [ ! -z "$START_PIDS" ]; then
    for pid in $START_PIDS; do
        echo "终止 start_system.sh (PID: $pid) 及其子进程..."
        # 获取进程组ID并杀死整个进程组
        PGID=$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' ')
        if [ ! -z "$PGID" ]; then
            # 杀死整个进程组（包括所有子进程）
            kill -TERM -$PGID 2>/dev/null || true
            sleep 1
            kill -9 -$PGID 2>/dev/null || true
        fi
        # 确保主进程被终止
        kill -9 $pid 2>/dev/null || true
    done
fi

# 方法2: 从PID文件读取并终止
if [ -f "$PROJECT_ROOT/.backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/.backend.pid")
    echo "停止后端进程 (PID: $BACKEND_PID)..."
    kill -9 $BACKEND_PID 2>/dev/null || true
    rm "$PROJECT_ROOT/.backend.pid"
fi

if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/.frontend.pid")
    echo "停止前端进程 (PID: $FRONTEND_PID)..."
    kill -9 $FRONTEND_PID 2>/dev/null || true
    rm "$PROJECT_ROOT/.frontend.pid"
fi

# 方法3: 强制杀死所有与项目相关的Python进程
echo ""
echo "清理所有残留的Python进程..."
# 杀死所有包含项目路径的Python进程
pkill -9 -f "python.*nof1.Ashare" 2>/dev/null || true
pkill -9 -f "python.*main.py" 2>/dev/null || true
# 杀死multiprocessing子进程
pkill -9 -f "multiprocessing.resource_tracker" 2>/dev/null || true
pkill -9 -f "multiprocessing.spawn" 2>/dev/null || true

# 杀死前端进程
echo "清理所有残留的Node.js进程..."
pkill -9 -f "next.*3002" 2>/dev/null || true
pkill -9 -f "node.*nof1.Ashare.*frontend" 2>/dev/null || true

# 杀死tail进程
pkill -9 -f "tail.*nof1.Ashare/logs" 2>/dev/null || true

sleep 2

# 方法4: 强制清理端口占用
echo "强制清理端口占用..."
# 清理8888端口
PORT_8888_PID=$(lsof -ti:8888 2>/dev/null)
if [ ! -z "$PORT_8888_PID" ]; then
    echo "终止占用8888端口的进程: $PORT_8888_PID"
    kill -9 $PORT_8888_PID 2>/dev/null || true
fi

# 清理3002端口
PORT_3002_PID=$(lsof -ti:3002 2>/dev/null)
if [ ! -z "$PORT_3002_PID" ]; then
    echo "终止占用3002端口的进程: $PORT_3002_PID"
    kill -9 $PORT_3002_PID 2>/dev/null || true
fi

sleep 1

echo ""
echo "✅ 系统已停止"
echo ""

# 验证
if lsof -i:8888 > /dev/null 2>&1; then
    echo "⚠️  端口8888仍被占用"
else
    echo "✓ 端口8888已释放"
fi

if lsof -i:3002 > /dev/null 2>&1; then
    echo "⚠️  端口3002仍被占用"
else
    echo "✓ 端口3002已释放"
fi

# 检查是否还有残留进程
REMAINING_PROCS=$(ps aux | grep -E "nof1.Ashare.*(python|node)" | grep -v grep | wc -l)
if [ "$REMAINING_PROCS" -gt 0 ]; then
    echo ""
    echo "⚠️  警告：发现 $REMAINING_PROCS 个残留进程"
    echo "残留进程："
    ps aux | grep -E "nof1.Ashare.*(python|node)" | grep -v grep
else
    echo ""
    echo "✓ 所有进程已清理"
fi

