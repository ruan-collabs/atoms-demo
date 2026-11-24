# Google 登录接入

## 已有代码

后端服务端授权码流程：POST /api/auth/google/start → Google 授权页面 → GET /api/auth/google/callback → /dashboard。
使用state、防重放nonce、S256 PKCE、HttpOnly临时Cookie和一次性数据库挑战；服务端交换code、验证Google签名/issuer/audience/expiry/nonce/email_verified后签发平台HttpOnly会话。
Google Client Secret仅存后端环境；Google access/refresh/ID token不写数据库、不交给React，不请求Drive/Gmail等权限。应用启动脚本禁用access log，避免callback授权码进入应用请求日志；部署边缘日志也需按平台能力限制采集/保留。

Google身份按provider+sub稳定关联到平台User，而非把邮箱当Google唯一标识。同一sub后续登录复用原User和Workspace，邮箱变更不把账号迁给别人。
已有邮箱账号首次Google回调不会自动合并或绑定，以免错误关联；会提示继续邮箱登录。显式双重验证绑定尚未实现。已有Google关联User可用相同邮箱OTP登录，是邮箱持有权的第二种认证方式；部署前按实际业务风险评估。

登录之后仍经过模型配置门禁。Google登录与邮件SMTP独立：MAIL_MODE=disabled时可用已配置Google登录，但邮箱不可用。

## 需要你配置的两项

- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

本地填项目根 .env；线上填Railway App的Variables。不要把Secret发在聊天、前端源码、GitHub或共享文档中。
未配置时API meta返回google_login=false，登录页显示“使用Google登录 · 待配置”并禁用；不会固定回包冒充登录成功。
同时配置两项后须重启后端，或在Railway重新部署；.env变更不会自动触发Python热重载。

## Google Cloud控制台设置

使用自己的Google Cloud项目，设置OAuth同意页面，再创建OAuth Client，应用类型选择Web application。
最小scope为openid email；测试模式将需要登录的账号加入测试用户。根据Google当前控制台要求维护应用名称、支持邮箱、隐私政策与域名。

Authorized redirect URIs必须与后端PUBLIC_ORIGIN拼接的回调一致：

- 本地Vite：http://localhost:5173/api/auth/google/callback
- 本地单服务：http://localhost:8000/api/auth/google/callback（此时PUBLIC_ORIGIN也设为http://localhost:8000）
- Railway：实际App HTTPS Origin + /api/auth/google/callback

开发时回调走Vite /api代理，保持Cookie同一个localhost站点；不要在5173登录后把回调改成127.0.0.1:8000。后端不依赖客户端传入redirect或Host头构造Google回调。

官方参考：
https://developers.google.com/identity/openid-connect/openid-connect?hl=id
（核对redirect_uri、state、nonce和sub稳定性；以Google控制台实际配置为准。）

## 真实联调检查

1. 配置两项凭证与精确redirect URI，重启后端。
2. 勾选演示条款，点击Google登录，由用户自行选择账号并完成授权。
3. 回到dashboard应有真实平台会话与一个用户/工作区，且自动要求模型配置；不跳过门禁。
4. 退出并再次Google登录应复用原用户；拒绝授权、失效state、重放和错误签名不得创建登录态。
5. 在Railway域名单独复测，localhost结果不代替生产回调验收。

## 本轮验证边界

已新增数据库迁移及可执行OAuth代码。自动化回调测试模拟Google网络响应；ID token校验测试使用临时RSA签名，覆盖签名/issuer/audience/expiry/nonce/email验证。它们不是一次真实Google账号授权。
目前没有你的Google OAuth Client配置，真实Google登录暂阻塞，界面不会把它标成可用。无需在此轮提供真实模型Key。
