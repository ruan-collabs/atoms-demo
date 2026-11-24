# Mock / 人工配置登记及去除清单

本轮用户明确授权Mock完成本地开发验收。Mock永远公开标识、不做真实服务兜底；生产启动强制关闭。

最新演示范围：用户明确接受Mock专用opaque-origin沙箱，Railway已部署e2246a9并通过Mock公网闭环；以下M07/M09保留首次本地阶段描述，最新结果以RAILWAY_DEPLOYMENT_STATUS.md为准。真实生产域、模型、认证与密钥治理不由演示验收替代。

新增M10：DEV_MOCK_SANDBOX仅接受严格匹配的可信fixture；专用frame响应CSP sandbox与iframe均不含allow-same-origin，消息桥只允许限额任务数据，按账号/项目/预览或公开表面分区当前浏览器保存。

新增M11：DEV_INLINE_WORKER仅development且DEV_MOCK_MODEL=true可用，Platform生命周期启动Mock-only后台消费器；队列/构建仍在Postgres。真实模型需独立Worker，production拒绝此开关。

新增M12：Pipecat语音管线测试中仅STT使用模拟服务，其余运输/serializer/pipeline实际运行；真实Deepgram凭证未配置，不能算真实麦克风/网络转写通过。

| 编号 | 替代内容 | 位置/开关 | 本地验证 | 上线前必须做 |
|---|---|---|---|---|
| M01 | Google/邮件身份验证，固定Alice/Bob测试会话 | /dev-test，/api/dev/mock-login，DEV_MOCK_AUTH=true | 真实平台会话/CSRF/owner后续链路；不验证身份提供方 | DEV_MOCK_AUTH=false，撤销/清理Mock会话与测试账号，填GoogleOAuth或SMTP，真实授权/收码 |
| M02 | 模型连接测试 | 配置provider=mock，DEV_MOCK_MODEL=true | 服务端草稿/启用/删除真实，Mock仅保存非秘密fixture标记，不依赖主密钥；加密算法另由独立测试覆盖 | 禁用DEV_MOCK_MODEL、删除mock配置，用户真实Key服务端测试 |
| M03 | 规划/代码/迭代模型响应 | services/mock_model.py和fixtures/*，页面/产物有Mock标签 | 任务板/作品集两种真实可运行fixture；仅颜色差异迭代 | 真实模型生成两类不同产物与语义迭代；禁止发布Mock构建 |
| M04 | 上游失败/慢任务/非法产物 | [mock:fail]/[mock:slow]/[mock:invalid] | 失败保护/取消/超时真实平台路径 | 关闭mock模型后这些标记不得作为生产工具；真实上游错误/超时复验 |
| M05 | 认证/Google/模型网络自动化测试 | tests内monkeypatch、httpx模拟、临时RSA签名 | 算法与业务断言，不访问真实凭证 | 保留测试隔离，不把它当生产OAuth/模型联通验收 |
| M06 | 独立KMS/SecretManager | 本机.runtime/credential.key，权限0600 | AESGCM随机nonce及AAD真实，主密钥与库分离 | 使用生产Secret/KMS身份、配置独立权限/审计/轮换/备份删除策略；开发文件不得上传 |
| M07 | 公网应用域/TLS | localhost:8001/8002及project子域 | 真实HTTP独立服务/构建发布/访问；不是公网HTTPS | 配置PREVIEW_ORIGIN、APP_ORIGIN两套通配域DNS/TLS，部署Application服务；验证生产Cookie/CSP/HTTPS |
| M08 | 邮件传输 | MAIL_MODE=file及测试内模拟 | OTP真实生成/校验，未发送真实邮件 | smtp真实接入或明确disabled；production禁止file |
| M09 | Railway/CI/镜像实测 | 本地配置文件，无账号绑定 | 源码/编译/变量校验；没有云部署 | 自己账号部署真实数据库/平台/Worker/Application，Docker/CI运行与健康检查；本轮不制造假线上地址 |

## Fail-closed边界

- 生产APP_ENV=production禁止DEV_MOCK_AUTH/DEV_MOCK_MODEL=true。
- Mock会话数据库标记mock，开关关闭或生产不可使用；Mock邮箱身份也在生产拒绝。
- Mock模型配置在生产/开关关闭无法用于业务；Mock构建公开服务拒绝，发布接口拒绝。
- 真实模型上游错误直接返回脱敏错误，绝不自动换Mock、平台Key或其他账号Key。
- .env、.runtime/credential.key、数据库、会话、开发邮箱和签名预览临时URL不入源码交付包。

## 非Mock的真实本地能力

React页面/表单；PostgreSQL事务、用户隔离、配置密文与队列；独立Worker；取消/租约/事件；HTML结构与Node语法校验；成功构建快照；隔离iframe；localStorage任务操作；实际Application服务HTTP可达检查、发布指针更新与旧版保护；复制剪贴板反馈；浏览器自测证据。

## 仍有实现差距（不能用Mock遮掩）

- 阶段级完整响应与轮询已实现，没有逐token流式显示；45条AC中涉及逐token/完整上游恢复的要求不标全部通过。
- 生产最小权限KMS身份、备份删除标记恢复策略/保留期限、密钥轮换尚无云端验证。
- 元数据持久化在PostgreSQL，单页代码直接存数据库，无对象存储CDN；P0无外部资源因此可简化。
- 浏览器第三方存储分区会使嵌入/独立预览有不同本地数据空间；两者均不承诺同步。
- 未实现P1模板库/多Agent/代码编辑/版本回滚/团队/计费等，用户“剩余功能”按当前P0范围，不扩展到文档明确延期的P1/P2。
