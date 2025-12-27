#!/bin/bash

echo "=========================================="
echo "Vite + Nginx 配置检查"
echo "=========================================="

echo ""
echo "1. 检查 Vite 进程..."
VITE_PIDS=$(pgrep -f "vite --force")
if [ -n "$VITE_PIDS" ]; then
    echo "   ✓ Vite 正在运行 (PID: $VITE_PIDS)"
else
    echo "   ✗ Vite 未运行"
fi

echo ""
echo "2. 检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":8080"; then
    echo "   ✓ 端口 8080 正在监听"
else
    echo "   ✗ 端口 8080 未监听"
fi

if netstat -tlnp 2>/dev/null | grep -q ":443"; then
    echo "   ✓ 端口 443 正在监听"
else
    echo "   ✗ 端口 443 未监听"
fi

echo ""
echo "3. 检查环境变量配置..."
cd /root/django-vue3-admin/web
if [ -f .env ]; then
    echo "   ✓ .env 文件存在"
    echo "   当前 HMR 配置:"
    grep "VITE_HMR" .env | sed 's/^/     /'
else
    echo "   ✗ .env 文件不存在"
fi

echo ""
echo "4. 测试本地连接..."
if curl -s http://127.0.0.1:8080 > /dev/null 2>&1; then
    echo "   ✓ Vite 本地连接正常"
else
    echo "   ✗ Vite 本地连接失败"
fi

echo ""
echo "5. 测试 HTTPS 域名连接..."
if curl -s -k https://tongyuinspection.cloud > /dev/null 2>&1; then
    echo "   ✓ HTTPS 域名连接正常"
else
    echo "   ✗ HTTPS 域名连接失败"
fi

echo ""
echo "=========================================="
echo "如果 Vite 正在运行，请重启它以加载新配置："
echo "1. 在运行 yarn dev 的终端按 Ctrl+C 停止"
echo "2. 重新运行: cd /root/django-vue3-admin/web && yarn dev"
echo "=========================================="




