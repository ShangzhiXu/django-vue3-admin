#!/bin/bash

echo "=========================================="
echo "重启 Vite 开发服务器"
echo "=========================================="

cd /root/django-vue3-admin/web

# 查找 Vite 进程
VITE_PIDS=$(pgrep -f "vite --force")

if [ -n "$VITE_PIDS" ]; then
    echo "找到 Vite 进程: $VITE_PIDS"
    echo ""
    echo "正在停止 Vite 进程..."
    
    # 获取父进程（shell）
    PARENT_PID=$(ps -o ppid= -p $(echo $VITE_PIDS | awk '{print $1}') | tr -d ' ')
    
    # 停止进程组
    kill -TERM $PARENT_PID 2>/dev/null || kill -9 $PARENT_PID 2>/dev/null
    
    sleep 2
    
    # 检查是否还在运行
    if pgrep -f "vite --force" > /dev/null; then
        echo "⚠  Vite 进程仍在运行，尝试强制停止..."
        pkill -9 -f "vite --force"
        sleep 1
    fi
    
    echo "✓ Vite 进程已停止"
else
    echo "未找到运行中的 Vite 进程"
fi

echo ""
echo "=========================================="
echo "请在新的终端窗口中运行以下命令启动 Vite:"
echo ""
echo "cd /root/django-vue3-admin/web"
echo "yarn dev"
echo ""
echo "或者按 Enter 键自动启动（可能需要几秒钟）..."
echo "=========================================="

read -t 5 -p "按 Enter 继续自动启动，或等待 5 秒..." || echo ""

echo ""
echo "正在启动 Vite..."
nohup yarn dev > /tmp/vite.log 2>&1 &
VITE_NEW_PID=$!

sleep 3

if ps -p $VITE_NEW_PID > /dev/null; then
    echo "✓ Vite 已启动 (PID: $VITE_NEW_PID)"
    echo "  日志文件: /tmp/vite.log"
    echo ""
    echo "查看日志: tail -f /tmp/vite.log"
    echo "检查状态: ps aux | grep vite"
else
    echo "✗ Vite 启动失败，请查看日志: cat /tmp/vite.log"
fi




