#!/bin/bash

echo "=========================================="
echo "HTTPS 访问验证脚本"
echo "=========================================="

echo ""
echo "1. 检查 Vite 是否运行..."
if pgrep -f "vite --force" > /dev/null; then
    echo "   ✓ Vite 正在运行"
    VITE_START_TIME=$(ps -o lstart= -p $(pgrep -f "vite --force" | head -1) 2>/dev/null)
    echo "   启动时间: $VITE_START_TIME"
else
    echo "   ✗ Vite 未运行"
    echo "   请运行: cd /root/django-vue3-admin/web && yarn dev"
    exit 1
fi

echo ""
echo "2. 检查环境变量是否加载..."
cd /root/django-vue3-admin/web
if grep -q "VITE_HMR_HOST=tongyuinspection.cloud" .env; then
    echo "   ✓ HMR 配置已设置"
else
    echo "   ✗ HMR 配置未设置"
fi

echo ""
echo "3. 测试本地连接..."
if curl -s http://127.0.0.1:8080 > /dev/null 2>&1; then
    echo "   ✓ 本地连接正常"
else
    echo "   ✗ 本地连接失败"
fi

echo ""
echo "4. 测试 HTTPS 域名连接..."
RESPONSE=$(curl -s -k -o /dev/null -w "%{http_code}" https://tongyuinspection.cloud)
if [ "$RESPONSE" = "200" ]; then
    echo "   ✓ HTTPS 连接正常 (HTTP $RESPONSE)"
else
    echo "   ✗ HTTPS 连接异常 (HTTP $RESPONSE)"
fi

echo ""
echo "5. 检查 Vite 客户端脚本..."
if curl -s -k https://tongyuinspection.cloud/@vite/client | grep -q "HMRContext"; then
    echo "   ✓ Vite 客户端脚本可访问"
else
    echo "   ✗ Vite 客户端脚本不可访问"
fi

echo ""
echo "=========================================="
echo "浏览器测试步骤："
echo "1. 打开浏览器访问: https://tongyuinspection.cloud"
echo "2. 按 F12 打开开发者工具"
echo "3. 查看 Console 标签页，检查是否有错误"
echo "4. 查看 Network 标签页，筛选 WS/WSS，检查 WebSocket 连接"
echo ""
echo "如果看到 WebSocket 错误，请："
echo "- 确保 Vite 已重启（启动时间应该是最近的时间）"
echo "- 检查浏览器控制台的完整错误信息"
echo "=========================================="




