# Atoms Demo · 本地可运行构建平台

这是**根据用户需求生成可运行应用的平台**，不是固定任务板业务应用。生成器具备对话式迭代能力；真实模型路径与开发Mock严格分开。

## GitHub 与 Railway 交付

源码仓库： https://github.com/ruan-collabs/atoms-demo 。当前Railway演示与验收状态以 docs/RAILWAY_DEPLOYMENT_STATUS.md 为准。Mock专用沙箱无需自有通配域：无same-origin权限的iframe，仅按账号/项目/预览或公开表面保存白名单任务数据；Mock-only后台可由Platform lifespan启动，生产禁用。真实模型使用独立Worker；应用运行可选独立源Application或APPLICATION_SANDBOX=true的opaque iframe，二者需独立验收，不能仅换path当隔离。

**真实核心链路已验证，完整production验收仍未完成。** 用户Google会话和用户DeepSeek配置经独立Worker完成规划/流式代码，opaque iframe可新增/完成/删除并刷新恢复；主题迭代构建2及稳定/apps链接发布更新通过。项目/消息/密文配置/构建/发布保存在PostgreSQL；生成应用的受限JSON数据仅当前浏览器、分项目与private/public保存，不承诺云同步。现场结果与未验范围见 docs/APPLICATION_SANDBOX_ACCEPTANCE.md 和 docs/RAILWAY_DEPLOYMENT_STATUS.md。

**不要直接把本机 .env、.runtime、数据库、密钥、浏览器自测原始证据上传。** 仓库只包含示例变量和明确标识的Mock实现；生产 APP_ENV=production、DEV_MOCK_AUTH=false、DEV_MOCK_MODEL=false。当前仍为用户授权development演示，保留Mock入口但真实任务不降级Mock；生产密钥权限/备份治理、第二类真实应用和完整安全验收仍待补齐。opaque方案不要求自有通配域，但必须验证实际隔离。完整清单见 docs/PREDEPLOY_CHECKLIST.md 和 docs/MOCK_REGISTER.md。

React + TypeScript + Vite / FastAPI Python3.11 / PostgreSQL / 独立后台Worker。
按需求V1.2实现，另按用户要求保留Google OAuth；非公开资料不随公开仓库提交。

## 当前能力与真实边界

已实现：Google OAuth/邮箱OTP代码、会话与owner隔离；服务端模型测试与AESGCM加密保存；服务器硬门禁；项目/首条消息/run原子写入；持久化PostgreSQL后台队列；规划/生成/一次修复/迭代；事件轮询恢复；停止、删除配置、超时与Worker租约；不可变构建、结构/JS语法校验、保存重试；独立源预览与公开发布/更新，稳定公开URL；项目搜索/状态筛选/重命名/消息恢复；窄屏聊天/预览标签。

本机启用用户明确授权的开发Mock登录、模型连接及模型fixture。Mock登录不是Google/邮箱身份验证；Mock产物不是AI模型生成。数据库、Worker、事务、加密、构建保存、浏览器真实运行与发布指针不是Mock。真实模型路径使用用户加密保存的Key，仅调用绑定允许HTTPS供应商；失败不会自动切Mock或平台Key。

**本地Mock闭环通过不等于真实生产P0的45条验收全部通过。** 最新本地增量回归与真实供应商限制见 docs/INCREMENTAL_ACCEPTANCE.md；原始浏览器证据和HTML报告仅本地保留，不公开提交。当前GitHub CI单测、前端build与Docker镜像build通过，详见 docs/GITHUB_DELIVERY.md；真实生产链路仍未验收。

## 本地运行

当前机器：数据库127.0.0.1:55432，平台 http://localhost:5173，API8000，预览8001，公开应用8002。

1. uv sync --project backend --frozen --extra test；npm --prefix frontend ci。
2. 使用自己的PostgreSQL，或macOS Homebrew PostgreSQL16下运行 bash scripts/start-local-db.sh。
3. .env.example复制到.env，DATABASE_URL配置到数据库；本机专用库为 postgresql://atoms@127.0.0.1:55432/atoms。
4. 开发密钥仅本机：生成32随机字节放 .runtime/credential.key，权限0600；或在独立环境变量CREDENTIAL_MASTER_KEY提供32字节URL-safe base64。不要提交密钥。
5. backend/.venv/bin/alembic -c backend/alembic.ini upgrade head。
6. 独立终端运行 bash scripts/start-backend.sh、bash scripts/start-frontend.sh、bash scripts/start-worker.sh。
7. 独立终端运行 bash scripts/start-application.sh 和 PORT=8002 bash scripts/start-application.sh。

开发Mock明确开启：.env设置 DEV_MOCK_AUTH=true、DEV_MOCK_MODEL=true。通过 /dev-test进入Alice/Bob测试账号；选择开发Mock模型→同意→测试→加密保存启用，再创建项目。生产默认false且APP_ENV=production禁止true。已签发Mock会话和Mock产物也拒绝用于生产。

Mock控制（仅开发）：[mock:fail]上游失败、[mock:invalid]非法HTML、[mock:slow]每阶段20秒延时；修复/停止/超时用例见测试与报告。默认Mock是根据任务板/作品集需求选fixture，并支持保留代码仅变色。没有假称能生成任意应用。

本地真实模型配置在弹窗填写；HTTP只允许localhost开发，生产用HTTPS。Key提交后只在加密密文中保存，前端状态无Key；测试草稿15分钟过期；退出不删除配置。删除停止后续执行并清库密文，不保证供应商退费或备份瞬时物理抹除。

## 运行及部署结构

- app.main：平台API与React静态资源，不执行生成的JS。
- app.worker：独立后台进程，PostgreSQL FOR UPDATE SKIP LOCKED认领任务，提交成果前检查租约/版本/owner/取消。
- app.application_server：独立源运行选项。APPLICATION_SANDBOX=true时改用/api/application-sandbox专用frame与/apps、/preview包装入口；iframe无allow-same-origin、CSP禁止网络和导航。仅异步atomsStorage的限额JSON桥可保存当前项目数据，确认写成功后才显示保存。Mock仍走严格可信fixture，不扩大旧Mock例外。
- 规划为受限完整JSON响应；真实生成使用content-only SSE流式接收并持久化到Postgres，前端按run/revision/offset增量轮询恢复；Mock仅返回完整fixture，不伪装逐token流。代码只读，完整校验保存后才运行。
- 本地应用数据仅各存储分区；浏览器iframe第三方存储分区可能使“嵌入预览”和“独立打开预览”也不共享记录。刷新同一表面可保留，发布不迁移预览数据。
- 生成候选无外部资源，CSP断网络，禁止嵌入、顶层导航/弹窗、凭证读取；仅Node --check语法解析，不运行服务器命令。

## 测试与增量

bash scripts/test.sh运行后端真实临时PostgreSQL集成测试、前端单测、编译、迁移一致性和账本校验。测试只允许loopback独立临时库，结束删除测试库，不清用户atoms数据库。单例：backend/.venv/bin/python -m pytest backend/tests/test_generation.py -k lease -q。

UI证据由实际浏览器点击/输入/刷新获取，docs/evidence/*.txt不是自动伪造断言；截图是浏览器实测。测试中的上游网络/Google交换模拟清楚登记，不计为真实上游已接通。

Railway参见 docs/RAILWAY.md 和 docs/RAILWAY_DEPLOYMENT_STATUS.md。演示开启 DEV_MOCK_SANDBOX=true、DEV_INLINE_WORKER=true 时仅运行Mock fixture任务，正式切production必须关闭。真实模型拓扑需要独立Worker/Application安全源和稳定Secret。语音实时转文字通过Pipecat STT-only管线。火山新版控制台配置VOICE_PROVIDER=volcengine、VOICE_ENABLED=true、VOLC_ASR_API_KEY、VOLC_ASR_RESOURCE_ID（匹配开通服务），固定官方双向流式；无需App ID/Access Token。详细安全与验收见docs/VOICE_INPUT.md。兼容Deepgram时显式VOICE_PROVIDER=deepgram、DEEPGRAM_API_KEY，无自动切供应商。

新增需求先入TODO；每次schema更新新增Alembic版本。不可自动删除生产数据或改写已应用迁移；备份/expand-contract迁移后再部署。Mock注册、生产待办和验收情况都在docs/SELF_TEST.md中。

## 核心交互增量 T-030（历史本地开发，后续已部署）

预览/代码/活动三视图、结构化需求摘要、真实阶段反馈、桌面/手机预览宽度、模型与发布状态门禁已实现。无可用Worker时拒绝创建新任务并保留输入；Worker心跳每5秒刷新，20秒过期。Application与publication独立角色分别设置APPLICATION_ROLE。心跳只证明进程可用，不证明DNS/TLS或供应商成功。

新增迁移a7c932e108df为旧run记录标dispatch_version=0，新真实Worker只消费新契约version1，不启动就执行旧需求。历史queued由用户显式重新提交或停止；重新提交保留旧任务历史。流式修复用revision重置，重复轮询不重复文本；未知上游不自动重发。真实API SSE有内容与跨chunk泄漏检查，测试上游替身不算实供应商验收。详情见docs/CORE_INTERACTION_DEVELOPMENT.md。
