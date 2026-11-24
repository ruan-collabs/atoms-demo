# Railway V1.2部署

## 服务拓扑

1. Platform：根Dockerfile，railway.json；React静态托管+FastAPI8000，读取PORT。
2. Worker：同Dockerfile，选择railway.worker.json；启动python -m app.worker，无公共入口。
3. Application：同Dockerfile，选择railway.application.json；启动python run_application.py，/health。
4. PostgreSQL：独立持久化服务。Platform预部署执行alembic upgrade head，Worker/Application同库只读取各角色需要的数据。

可使用一个Application服务同时绑定 *.preview.example.com 与 *.apps.example.com，但它们必须和平台域名不同，且每项目子域稳定。生产域名要有自己的DNS/TLS wildcard配置；Railway默认单一服务域名不能直接充当每项目存储隔离的通配域。**此项未配不得宣称生成应用已公网发布。** 可先上线平台壳，再完成Application域名后跑完整验收。

## 变量

- APP_ENV=production。
- DATABASE_URL引用实际Postgres服务，例如${{Postgres.DATABASE_URL}}。
- APP_SECRET：独立随机至少32字符，切换生产同时撤销开发会话。
- CREDENTIAL_MASTER_KEY：32随机字节URL-safe base64，通过独立SecretManager/Railway Secret变量管理，不能存库/源码；需要设定访问权限、轮换和备份删除策略。
- PUBLIC_ORIGIN：平台精确HTTPS Origin，无尾斜线。
- PREVIEW_ORIGIN=https://preview.example.com，APP_ORIGIN=https://apps.example.com；wildcard子域都指向Application服务并有TLS。
- DEV_MOCK_AUTH=false，DEV_MOCK_MODEL=false；生产为true启动即拒绝。不要导入本地Mock账号/构建/发布记录。
- GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET：真实OAuth配置，仅Platform；callback为PUBLIC_ORIGIN/api/auth/google/callback，详情见GOOGLE_LOGIN.md。
- MAIL_MODE=smtp（配置发件人与TLS SMTP凭证）或disabled（仅邮箱不可用，Google可独立使用）；禁止file。
- MODEL_ALLOWED_ORIGINS：精确HTTPS服务目标允许名单；默认OpenAI/DeepSeek。服务端DNS公共IP与TLS SNI绑定，不跟随重定向、不读取环境代理。
- RUN_BUDGET_SECONDS=180，LEASE_SECONDS=60（可选）。

当前代码采用AESGCM认证加密，AAD绑定owner/config/version；本地文件主密钥是开发替代，不是KMS。生产使用环境Secret的成熟算法路径已实现，但独立KMS身份、轮换、审计与备份删除治理尚需实际部署验证，记录为上线阻塞。

## 部署步骤

1. 把源码推自己的GitHub，忽略.env/.runtime/本地密钥和测试产物；不要提交真实Key/Cookie/验证码。仓库：https://github.com/ruan-collabs/atoms-demo 。上线门禁按 PREDEPLOY_CHECKLIST.md 执行；推送不等于部署完成。
2. Railway创建Postgres、Platform、Worker和Application服务，所有代码root保持项目根，配置对应config-as-code路径。
3. 为Platform生成公共域，设置PUBLIC_ORIGIN与OAuth回调。
4. 绑定真实Application两套通配域并配置TLS。记录映射规则，确认p-project与a-project请求只到Application而非Platform。
5. 注入独立密钥Secret；未配置或Mock开关违规则启动失败，不用明文兜底。
6. Platform迁移成功、健康检查通过，再启动Worker/Application；配置真实模型，真实生成任务板与作品集并执行45条验收中的生产项。
7. 验证关闭浏览器后台任务继续、取消/删除Key、公开资源HTTP可达和构建校验、未更新线上不变、更新后稳定链接替换。

官方参考：https://docs.railway.com/reference/config-as-code

## 当前真实状态

源码已推送公开GitHub仓库，源码提交951819e，GitHub Actions运行45317051622成功（后端、前端和Docker镜像build）。本地服务已自测；尚未在Railway账号创建服务、未配置DNS/TLS或生产SecretManager，Docker镜像run与真实公网生产链路尚未验收。仅镜像build成功不能证明部署后可用。详见GITHUB_DELIVERY.md。

不要把开发Mock或localhost链接作为已上线证据。用户本轮授权不二次确认，因此人工配置卡点记录后继续开发，不申请真实凭证或创建付费资源。
