#!/bin/bash

echo "=========================================="
echo "资源加载测试"
echo "=========================================="

BASE_URL="https://tongyuinspection.cloud"

echo ""
echo "测试关键资源文件..."

RESOURCES=(
    "/@vite/client"
    "/src/main.ts"
    "/node_modules/.vite/deps/vue.js"
    "/src/stores/tagsViewRoutes.ts"
)

for resource in "${RESOURCES[@]}"; do
    echo ""
    echo "测试: $resource"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -k "$BASE_URL$resource")
    if [ "$STATUS" = "200" ]; then
        echo "  ✓ 状态码: $STATUS"
    else
        echo "  ✗ 状态码: $STATUS"
    fi
done

echo ""
echo "=========================================="
echo "如果所有资源都返回 200，说明服务器端正常"
echo "浏览器无法加载可能是缓存问题"
echo "=========================================="
