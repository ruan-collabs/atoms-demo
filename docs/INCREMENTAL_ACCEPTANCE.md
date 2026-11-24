# 核心链路与语音输入增量验收

## 本轮结论

2026-11-24最终增量：源码e2246a9已推送，固定提交ZIP的113份文件与本地逐字节一致；CI https://github.com/ruan-collabs/atoms-demo/actions/runs/45339583822 成功（Linux后端、前端、Docker build）。Railway已启用DEV_MOCK_SANDBOX/DEV_INLINE_WORKER并部署成功；公网实测访客Query登录恢复、Mock配置检查保存、后台生成、任务新增/编辑/完成/刷新、迭代构建2、发布与匿名公开分享刷新通过。

收尾文档提交f76ad5已在Railway自动重部署成功，113份文件与当时本地一致；重部署后重新Mock登录恢复配置，原项目、消息、构建2、失败记录和发布均在，私有预览及公开分享任务数据保留。手机流量/无痕GUI未代验，正式生产不算通过。

生成应用是明确标识的Mock fixture，不是本轮真实AI调用。语音按钮与Pipecat STT管线已上线，/api/voice/status明确未配置；真实语音仍待验收，DeepSeek本轮只验证HTTP模拟契约。

## 本轮前期历史结论

本地代码已实现访客浏览、Query登录恢复、Mock无主密钥配置、DeepSeek接口适配及Pipecat语音转写接入。本地Mock核心链路通过；Railway旧版本复现配置失败，新代码尚未推送或部署，不能宣称线上已修复。

## 1. Mock问题与核心回归

### 线上复现

/dev-test登录Alice成功；选择Mock并检查配置时返回“加密密钥不可用，操作已拒绝”。此外现有部署无Worker/Application服务，因此修复配置后也不能只靠平台页面完成生成预览。未输入真实Key，未改Railway配置。

### 代码修复

- Mock没有用户凭证，仅保存固定的非秘密fixture标记，检查、保存及Worker不依赖主加密密钥。
- 真实供应商仍按AESGCM密文保存；production继续禁Mock，未做明文兜底。
- 共享Mock账号拒绝配置真实供应商Key，避免共享身份泄漏。
- 修复已配置账号重新Mock登录时，配置异步恢复仍残留弹窗的问题。

### 实际本地浏览器回归

访客工作台 → 输入需求 → 点击发送才跳登录 → 进入Mock演示 → Query恢复且未自动生成 → 手动提交 → 独立Worker规划/生成/校验/保存构建1 → iframe预览加载 → 独立预览新增任务 → 刷新仍在 → 编辑任务并完成 → 刷新仍在 → 平台刷新恢复消息和构建 → 对话改紫色 → 构建2 → 旧任务及完成状态保留。

实际本地服务HTTP验收：发布构建2，Worker完成隔离预览/公开资源SHA256可达检查，发布状态published，公开HTML含紫色迭代。源产物是明确标识的fixture，不是真AI输出。

本地生成项目：0ee2043c-10e7-4834-be7b-16af0ce033f0；证据/.runtime/incremental-smoke.json（非公开工作记录）。没有删除用户原项目。

## 2. 未登录浏览和Query恢复

- /dashboard可以展示和输入，无登录不立即跳转。
- /projects展示访客说明，不读取私人项目；私有编辑深链退回公共工作台。
- 提交Query时未登录才跳/login；sessionStorage保留待提交内容，最长4000字、30分钟有效、恢复后消费一次。
- 登录后只恢复文本，不自动发起生成或计费；无模型则提示配置。
- 私有项目与配置API仍保留身份、CSRF、owner隔离。
- 登录页新增Mock演示与先浏览工作台入口，修正旧浏览器Key方案条款。

## 3. DeepSeek

官方接口：https://api.deepseek.com/chat/completions；Bearer认证，messages/model/max_tokens/stream=False。默认预设切为DeepSeek，base URL=https://api.deepseek.com，模型deepseek-flash，可编辑；兼容标准/v1路径。请求显式thinking.disabled，避免把推理文本当最终HTML。

按当前官方文档适配模型ID与请求参数；不硬编码用户Key，不以旧文档模型名证明当前可用。保留公共DNS/IP绑定、TLS SNI、允许名单、无重定向/环境代理；对400/401/402/403/429/5xx、非法结构、截断或拒绝输出分别脱敏处理。

本轮只跑HTTP模拟契约单测，没有请求真实DeepSeek，没有输入真实Key，也未取消真实连接测试门禁。

官方依据：https://api-docs.deepseek.com/api/create-chat-completion/ ；https://api-docs.deepseek.com/zh-cn/index.html。

## 4. Pipecat实时语音转文字

用户已确认：语音输入实时转文字，不是AI语音播报；服务凭证稍后配置。

- 依赖pipecat-ai[deepgram,websocket]已加入后端manifest/锁文件/Docker依赖。
- Query和编辑器输入框加入语音按钮；只在HTTPS/loopback且浏览器支持时采样。用户点击并同意后才请求麦克风，不自动录音。
- AudioWorklet采集mono PCM16、16kHz；经同源WebSocket传到Pipecat STT-only管线；临时转写替换、最终文本追加，序号去重，最多4000字。
- 识别文本仅填输入框，不自动提交Query；转写期间禁止发送/手动编辑，停止后可确认。
- 服务端必须登录、精确Origin；单账号一个连接、进程并发上限2（可配置1–4）、会话默认60秒（最大120）、音频包和总量上限。
- 凭证只在服务端，脱敏SDK日志；不保存原始音频，不接LLM/TTS。
- /api/voice/status未配置明确提示，/api/voice/ws缺凭证拒绝，不伪造识别。

环境变量（仅Platform）：VOICE_ENABLED=true、DEEPGRAM_API_KEY=<用户在环境中配置>、VOICE_MODEL=nova-2、VOICE_LANGUAGE=zh-CN、VOICE_MAX_SECONDS=60、VOICE_MAX_CONNECTIONS=2。此为可配置STT适配选择，不代表用户已有凭证一定属于Deepgram；若凭证供应商不同需要换适配器。

模拟STT测试仅替换STT服务，Pipecat WebSocket/serializer/worker真实运行：音频包→interim/final转写→关闭释放连接。真实麦克风端到端和Deepgram网络/计费未验；需要用户配置对应服务凭证后再做。

官方依据：https://docs.pipecat.ai/api-reference/server/services/stt/deepgram ；https://docs.pipecat.ai/api-reference/server/services/transport/fastapi-websocket。WebSocket用于当前原型；官方客户端生产建议WebRTC，本轮不声称媒体网络生产质量已验。

## 5. 自动化与部署状态

最新回归：89后端、16前端通过，TypeScript/Vite生产构建通过。后端包含不依赖主密钥Mock生成、共享账号拒真Key、DeepSeek契约/错误、Pipecat模拟STT管线及身份/Origin保护。未做本轮Linux镜像build或远端CI。

GitHub/Railway尚未更新；本地后台服务已启动便于复核。线上原域依然旧代码。

用户已选择Mock专用opaque-origin沙箱，源码实现完成并准备同步GitHub/Railway。沙箱只接收严格匹配的可信fixture，iframe不授予same-origin权限，数据桥按账号/项目/预览或公开表面分区且只接受限额任务结构。Mock-only后台可通过Platform lifespan启动，队列仍在PostgreSQL；production禁用该选项。真实模型仍保留独立子域设计。最新沙箱本地回归91后端/18前端及构建通过，实际浏览器已验证SecurityError同源隔离、新增任务与刷新恢复、公开分享。公网仍待本轮部署后验证。

关联T-018–T-021；真实供应商和语音联调不因本地测试通过而标完成。
