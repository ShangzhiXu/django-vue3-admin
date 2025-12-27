# HTTPS 域名访问配置说明

## 当前配置状态

✅ Nginx 已配置并运行
✅ SSL 证书已配置
✅ WebSocket 代理已配置
✅ Vite HMR 配置已更新
✅ 环境变量已设置

## 重要：重启 Vite 开发服务器

**Vite 需要在启动时加载环境变量，所以必须重启才能应用新的 HMR 配置。**

### 重启步骤：

1. **停止当前的 Vite 进程**
   - 找到运行 `yarn dev` 的终端窗口
   - 按 `Ctrl+C` 停止 Vite

2. **重新启动 Vite**
   ```bash
   cd /root/django-vue3-admin/web
   yarn dev
   ```

3. **验证配置**
   - 启动后，检查控制台输出，应该看到类似：
     ```
     VITE v5.4.21  ready in xxx ms
     ➜  Local:   http://localhost:8080/
     ➜  Network: http://10.2.0.8:8080/
     ```
   - **不应该**再看到 `WebSocket server error` 或 `EADDRNOTAVAIL` 错误

## 访问地址

- **HTTPS 域名**: https://tongyuinspection.cloud
- **本地 IP**: http://101.42.41.173:8080

## 如果仍然有问题

### 1. 检查浏览器控制台
打开浏览器开发者工具（F12），查看 Console 标签页，看是否有错误信息：
- WebSocket 连接错误
- HMR 连接失败
- 其他错误

### 2. 检查网络请求
在浏览器开发者工具的 Network 标签页中：
- 查看是否有失败的请求（红色）
- 查看 WebSocket 连接（WS/WSS）是否建立成功

### 3. 检查 Vite 日志
查看运行 `yarn dev` 的终端，看是否有错误信息

### 4. 运行诊断脚本
```bash
cd /root/django-vue3-admin/web
./check_config.sh
```

## 配置详情

### Nginx 配置
- 文件位置: `/etc/nginx/sites-available/default`
- WebSocket 代理: 已配置
- SSL 证书: 已配置

### Vite 配置
- 文件位置: `/root/django-vue3-admin/web/vite.config.ts`
- HMR 配置: 通过环境变量动态配置

### 环境变量
- 文件位置: `/root/django-vue3-admin/web/.env`
- HMR 主机: `tongyuinspection.cloud`
- HMR 协议: `wss`
- HMR 端口: `443`

## 常见问题

### Q: 页面可以加载但 HMR 不工作？
A: 检查浏览器控制台的 WebSocket 连接，确保 nginx 正确代理了 WebSocket 请求。

### Q: 仍然看到 WebSocket 错误？
A: 确保 Vite 已重启，并且 `.env` 文件中的 HMR 配置已正确设置。

### Q: 通过 IP 可以访问，但域名不行？
A: 检查 DNS 解析和 SSL 证书配置。




