# Atoms Demo · 本地可运行构建平台

这是**根据用户需求生成可运行应用的平台**，不是固定任务板业务应用。生成器具备对话式迭代能力；真实模型路径与开发Mock严格分开。

## GitHub 与 Railway 交付

源码仓库： https://github.com/ruan-collabs/atoms-demo 。本次只推送源码和部署配置，尚未完成 Railway 公网部署。部署时使用项目根目录 Dockerfile，Platform、Worker、Application 分别使用 railway.json、railway.worker.json、railway.application.json，另建持久化 PostgreSQL。

**不要直接把本机 .env、.runtime、数据库、密钥、浏览器自测原始证据上传。** 仓库只包含示例变量和明确标识的Mock实现；生产 APP_ENV=production、DEV_MOCK_AUTH=false、DEV_MOCK_MODEL=false。真实Google/SMTP/模型、独立密钥治理及应用通配域名缺失仍属上线阻塞。完整清单见 docs/PREDEPLOY_CHECKLIST.md 和 docs/MOCK_REGISTER.md。

React + TypeScript + Vite / FastAPI Python3.11 / PostgreSQL / 独立后台Worker。
按需求V1.2实现，另按用户要求保留Google OAuth；私密需求与招聘材料不随公开仓库提交。

## 当前能力与真实边界

已实现：Google OAuth/邮箱OTP代码、会话与owner隔离；服务端模型测试与AESGCM加密保存；服务器硬门禁；项目/首条消息/run原子写入；持久化PostgreSQL后台队列；规划/生成/一次修复/迭代；事件轮询恢复；停止、删除配置、超时与Worker租约；不可变构建、结构/JS语法校验、保存重试；独立源预览与公开发布/更新，稳定公开URL；项目搜索/状态筛选/重命名/消息恢复；窄屏聊天/预览标签。

本机启用用户明确授权的开发Mock登录、模型连接及模型fixture。Mock登录不是Google/邮箱身份验证；Mock产物不是AI模型生成。数据库、Worker、事务、加密、构建保存、浏览器真实运行与发布指针不是Mock。真实模型路径使用用户加密保存的Key，仅调用绑定允许HTTPS供应商；失败不会自动切Mock或平台Key。

**本地Mock闭环通过不等于真实生产P0的45条验收全部通过。** 真实Google/SMTP、真实模型上游、生产密钥治理、DNS/TLS、Railway部署尚未配置，清单见 docs/MOCK_REGISTER.md。自测证据见 docs/SELF_TEST.md 和 docs/evidence/，HTML可视报告在 artifacts/Atoms自测报告.html。

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
- app.application_server：仅运行保存成功的HTML，无平台身份API。每项目独立 p-project子域预览与a-project子域公开应用；二者不同安全源。
- 阶段供应商请求是非流式完成接口，阶段与消息实时持久化后轮询；没有实现逐token流式展示，报告已列差距。
- 本地应用数据仅各存储分区；浏览器iframe第三方存储分区可能使“嵌入预览”和“独立打开预览”也不共享记录。刷新同一表面可保留，发布不迁移预览数据。
- 生成候选无外部资源，CSP断网络，禁止嵌入、顶层导航/弹窗、凭证读取；仅Node --check语法解析，不运行服务器命令。

## 测试与增量

bash scripts/test.sh运行后端真实临时PostgreSQL集成测试、前端单测、编译、迁移一致性和账本校验。测试只允许loopback独立临时库，结束删除测试库，不清用户atoms数据库。单例：backend/.venv/bin/python -m pytest backend/tests/test_generation.py -k lease -q。

UI证据由实际浏览器点击/输入/刷新获取，docs/evidence/*.txt不是自动伪造断言；截图是浏览器实测。测试中的上游网络/Google交换模拟清楚登记，不计为真实上游已接通。

Railway参见 docs/RAILWAY.md。v0.2拓扑需平台+Worker+隔离应用服务（可共用Application服务绑定两套独立wildcard域）+PostgreSQL。真实公网部署需要用户账户、DNS/TLS和SecretManager；本轮未创建付费服务或声称在线。

新增需求先入TODO；每次schema更新新增Alembic版本。不可自动删除生产数据或改写已应用迁移；备份/expand-contract迁移后再部署。Mock注册、生产待办和验收情况都在docs/SELF_TEST.md中。
