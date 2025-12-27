# 生产环境部署配置说明

## 域名配置：tongyuinspection.cloud

### 1. Nginx 配置

已更新 `docker_env/nginx/my.conf` 文件，支持 `tongyuinspection.cloud` 域名。

**主要配置项：**
- `server_name`: 已添加 `tongyuinspection.cloud` 和 `www.tongyuinspection.cloud`
- 支持 HTTPS（443 端口）
- 前端路由支持（`try_files` 配置）
- API 代理配置

**SSL 证书配置：**
如果需要启用 HTTPS，请在 nginx 配置中取消注释以下行并配置证书路径：
```nginx
ssl_certificate /etc/nginx/ssl/tongyuinspection.cloud.crt;
ssl_certificate_key /etc/nginx/ssl/tongyuinspection.cloud.key;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

### 2. 前端环境变量配置

创建 `web/.env.production` 文件（如果不存在），配置如下：

```env
# 生产环境配置
VITE_API_URL=/api
VITE_API_BACKEND_URL=https://tongyuinspection.cloud/api
VITE_PUBLIC_PATH=/
VITE_PORT=3000
VITE_DIST_PATH=dist
```

### 3. Django 后端配置

确保 `backend/conf/env.py` 文件中包含以下配置：

```python
ALLOWED_HOSTS = ["tongyuinspection.cloud", "www.tongyuinspection.cloud", "*"]
```

当前配置 `ALLOWED_HOSTS = ["*"]` 已允许所有域名，无需修改。

### 4. 部署步骤

#### 方式一：使用 Docker Compose

1. **更新 nginx 配置**
   ```bash
   # 确保使用更新后的配置文件
   cp docker_env/nginx/my.conf docker_env/nginx/my.conf.backup
   ```

2. **构建并启动服务**
   ```bash
   docker-compose up -d --build
   ```

3. **检查服务状态**
   ```bash
   docker-compose ps
   ```

#### 方式二：手动部署

1. **构建前端**
   ```bash
   cd web
   yarn install
   yarn build
   ```

2. **配置 Nginx**
   - 将构建后的 `web/dist` 目录内容复制到 nginx 的静态文件目录
   - 使用 `docker_env/nginx/my.conf` 或 `docker_env/nginx/my-production.conf` 作为 nginx 配置

3. **启动后端服务**
   ```bash
   cd backend
   python manage.py runserver 0.0.0.0:8000
   # 或使用 uvicorn
   uvicorn application.asgi:application --port 8000 --host 0.0.0.0 --workers 8
   ```

### 5. 常见问题排查

#### 问题：无法访问 https://tongyuinspection.cloud

**检查清单：**
1. ✅ DNS 解析是否正确指向服务器 IP
2. ✅ Nginx 服务是否正常运行
3. ✅ 防火墙是否开放 80 和 443 端口
4. ✅ SSL 证书是否正确配置（如果使用 HTTPS）
5. ✅ Nginx 配置中的 `server_name` 是否包含域名
6. ✅ 前端静态文件是否正确部署
7. ✅ 后端服务是否正常运行

#### 问题：API 请求失败

**检查清单：**
1. ✅ Nginx 的 `/api/` 代理配置是否正确
2. ✅ 后端服务是否在运行（端口 8000）
3. ✅ Django 的 `ALLOWED_HOSTS` 是否包含域名
4. ✅ CORS 配置是否正确（当前已设置为允许所有）

#### 问题：前端路由 404

**解决方案：**
确保 nginx 配置中包含 `try_files` 指令：
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 6. 验证配置

访问以下 URL 验证配置：
- 前端页面：`https://tongyuinspection.cloud`
- 登录页面：`https://tongyuinspection.cloud/#/login`
- API 健康检查：`https://tongyuinspection.cloud/api/system/init/dictionary/`

### 7. 注意事项

1. **生产环境安全：**
   - 建议将 `DEBUG = False`
   - 配置 SSL 证书启用 HTTPS
   - 修改默认密码
   - 定期更新依赖包

2. **性能优化：**
   - 启用 gzip 压缩（已配置）
   - 配置静态文件缓存（已配置）
   - 使用 CDN 加速静态资源

3. **监控和日志：**
   - 配置日志轮转
   - 设置监控告警
   - 定期备份数据库

