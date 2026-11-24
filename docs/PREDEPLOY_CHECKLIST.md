# Railway 上线与公开仓库门禁

本清单依据用户提供的《Atoms笔试避坑指南_v2》部署与红线要求整理，不公开原始招聘材料。GitHub 推送成功不等于 Railway 公网部署完成。

## 已做源码检查
- Platform 和 Application 均监听 0.0.0.0，并读取 PORT；EXPOSE 8000 只是镜像元数据，不能取代运行时 PORT。
- 根 Dockerfile 多阶段编译前端并安装 backend/requirements.txt；前端 package-lock.json、后端 uv.lock 保留便于复现。
- 项目/消息/任务/构建/发布数据保存在 PostgreSQL，不依赖容器临时磁盘；本地 compose 数据库有 named volume。Railway 必须使用独立持久化 Postgres，不能上传本机数据库。
- .gitignore/.dockerignore 排除 .env、.runtime、虚拟环境、node_modules、密钥文件、本地数据库、原始浏览器证据、构建缓存和大附件。
- 服务端用户 API Key 是应用运行时用户配置，不是写死到源码的环境密钥；在服务器认证加密保存。平台 APP_SECRET、CREDENTIAL_MASTER_KEY、OAuth/SMTP 凭证只能用 Railway Secret/环境变量注入，不放公开仓库。

## Railway 配置顺序
1. 从 GitHub ruan-collabs/atoms-demo 的 main 分支部署。所有服务 Root Directory 都为项目根，使用 Dockerfile，不直接启动 Vite 开发服务。
2. 新建并保留 PostgreSQL 持久化服务；注入实际 DATABASE_URL。不要用 compose 的演示密码或本机 127.0.0.1 地址。
3. Platform 用 railway.json，Worker 用 railway.worker.json，Application 用 railway.application.json。Worker不开放公共HTTP入口。仅Platform执行preDeploy迁移，迁移成功后再启动其他角色。
4. APP_ENV=production；DEV_MOCK_AUTH=false；DEV_MOCK_MODEL=false；MAIL_MODE=smtp或disabled，file禁止。至少真实Google OAuth或SMTP一个认证路径可用；邮箱禁用时不要声称邮件可登录。
5. 注入独立随机APP_SECRET和32随机字节base64的CREDENTIAL_MASTER_KEY；平台与Worker保持稳定一致，不每次重部署重新生成，否则旧凭证无法解密。密钥管理访问隔离、轮换、备份治理须上线前落实。
6. 平台PUBLIC_ORIGIN为精确HTTPS Origin；PREVIEW_ORIGIN与APP_ORIGIN为不同安全源，两套每项目wildcard域名和TLS指向Application。Railway默认单一服务域名不是通配域。未完成域名不要把预览/发布标已可用。
7. 明确保留Provider HTTPS目标允许名单、公共DNS/IP验证、禁止重定向和凭证泄漏。不因连通失败关闭SSRF/CSP或改成明文Key。

## 上线红线
- 禁止把 .env、真实API Key、主加密密钥、Cookie、OTP、数据库内容、私密招聘原文或原始自测截图/DOM上传公开仓库。
- 禁止把Mock生成产物当作真实AI结果。开发Mock保留用于本地演示，页面明确提示，生产启动拒绝开启。指南的演示兜底建议不等于允许生产偷偷切Mock或绕过用户模型配置。
- 禁止声称45条生产验收全部通过；目前真实供应商、Railway公网、Docker实测、KMS权限及备份治理仍未验收。
- 禁止临时隧道或localhost成为唯一提交访问链接。不得执行清库、删除生产数据、改写已应用迁移、强推远端覆盖用户历史来“修部署”。
- 禁止把真实Key写入前端、生成的HTML、普通日志或Git历史；意外泄漏先撤销/轮换供应商Key，再清理历史，不靠删文件掩盖。

## 部署后才能打勾的项目
- [x] GitHub公开仓库已由独立网页读取验证可访问，完整README与94份源码下载校验一致。
- [x] GitHub CI镜像实际build成功；后端/前端单测与前端build通过。
- [ ] Platform/Worker/Application在Railway实际启动及健康检查通过；镜像run/公网链路仍待验收。
- [ ] 无痕窗口打开真实HTTPS平台及生成应用；再由用户以手机流量访问一次，排除缓存与内网假象。
- [ ] 真用户登录 → 真Key服务器测试/加密保存 → 真AI生成 → iframe可操作 → 迭代 → 刷新/重开恢复 → 发布/更新。
- [ ] 容器重启/重部署后项目、消息、加密配置与构建仍在；没有容器临时层数据丢失。
- [ ] 关闭浏览器后台任务继续；取消/删除Key阻止后续调用；已发生费用不作退费承诺。

本次范围：安全发布现有源码与部署说明；不创建Railway资源、不支付、不配置真实Key、不宣称已经上线。
