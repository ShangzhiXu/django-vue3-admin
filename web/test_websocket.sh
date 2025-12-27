#!/bin/bash

echo "=========================================="
echo "WebSocket 连接测试"
echo "=========================================="

echo ""
echo "测试 Vite HMR WebSocket 连接..."
echo ""

# 测试本地 WebSocket 连接
echo "1. 测试本地 WebSocket (ws://127.0.0.1:8080)..."
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/8080' 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ 本地端口 8080 可访问"
else
    echo "   ✗ 本地端口 8080 不可访问"
fi

echo ""
echo "2. 测试 HTTPS WebSocket 代理..."
# 尝试通过 nginx 代理测试 WebSocket
curl -s -k -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  https://tongyuinspection.cloud/@vite/client 2>&1 | head -10

echo ""
echo "=========================================="
echo "如果看到 101 Switching Protocols，说明 WebSocket 代理正常"
echo "如果看到其他状态码，可能需要检查配置"
echo "=========================================="




