# Atoms V1.2 本地开发与自测报告

**结论：本地 Mock 辅助业务闭环通过；未达到真实生产 P0 全项验收。**

## 当前真实核心与自动化结果（2026-11-24）

真实DeepSeek规划/流式完整代码、构建保存、opaque iframe任务新增/完成/删除/刷新、真实主题迭代与稳定URL发布更新已在线验证。不是固定Mock产物；首成功构建为已有模型完整输出重新校验，不再次调用模型。最终122后端/27前端/build及Alembic check通过，最新源码c3e18b0与CI45410356880成功。详细现场结果与限制见APPLICATION_SANDBOX_ACCEPTANCE.md、RAILWAY_DEPLOYMENT_STATUS.md。第二类真实需求、重部署恢复、异常沙箱路径和真实语音完整事件仍待验，不改下文历史事实、不声称生产45项全过。

## 历史T-030核心交互增量（本地开发，2026-11-24）

用户设计已确认；预览/代码/活动三视图、真实SSE内容适配、持久增量恢复、独立服务心跳与新任务门禁、历史queued防自动消费已实现。完整109后端/25前端及构建、Alembic check通过。本地浏览器无Worker拒绝且草稿保留；开启Worker后Mock构建1、预览新增任务刷新恢复、紫色迭代构建2且任务保留。详细见CORE_INTERACTION_DEVELOPMENT.md。未调用真实DeepSeek，未更新GitHub/Railway，线上真实角色仍未部署。下文旧“无逐token”等是历史状态；当前协议实现通过替身测试，真实流式仍待联调。

## 最新增量验收（2026-11-24）

本地最新91后端/18前端及构建通过，远端CI 45339583822成功含Docker build；Railway e2246a9及Mock沙箱/Mock-only后台选项已上线。公网浏览器完成匿名工作台、Query提交后登录恢复、Mock检查保存、任务生成、任务新增编辑完成、刷新、主题迭代、发布与匿名分享刷新。详细证据与限制见INCREMENTAL_ACCEPTANCE.md、RAILWAY_DEPLOYMENT_STATUS.md。

下文保留首次本地V1.2历史记录，不能将其中旧“Railway/CI未测”作为最新状态。真实DeepSeek和真实语音均未调用，正式生产验收仍未完成。

## 首次本地验收历史

执行窗口：2026-11-23 至 2026-11-24（本机 Asia/Shanghai）。当前代码v0.2.0。需求全文重新读取V1.2 revision156，保留用户新增Google登录。用户授权独立完成且人工配置卡点用Mock，不再等待用户二次确认。

## 1. 真实启动与自动化结果

| 项目 | 结果 | 证据 |
|---|---|---|
| PostgreSQL16真实实例 | PASS；127.0.0.1:55432，项目专用集群 | /api/health、迁移revision、测试连接 |
| React/Vite | PASS；localhost:5173 | 浏览器实际DOM与截图 |
| Python平台API | PASS；127.0.0.1:8000 | /api/health、后端测试 |
| 独立后台Worker | PASS；Postgres持久队列 | 刷新/离开后完成、取消、租约单测 |
| 隔离预览Application | PASS；p-project.localhost:8001 | 真实iframe、独立打开、localStorage操作 |
| 公开Application | PASS；a-project.localhost:8002 | 访客空态、真实HTTP资源、发布更新 |
| 后端集成测试 | **70项通过，0失败** | docs/backend-test-results.xml |
| 前端单测 | **11项通过，0失败** | docs/frontend-test-results.xml |
| TypeScript + Vite生产构建 | PASS | npm --prefix frontend run build |
| Alembic迁移/重复升级/schema检查 | PASS | alembic check无漂移 |
| npm生产依赖审计 | PASS；返回0已报告漏洞 | 官方registry audit；非全量安全审计 |
| Google/SMTP真实供应商 | MOCK/待配置 | GOOGLE_LOGIN.md、MOCK_REGISTER.md |
| 真实模型上游 | MOCK/待配置 | Mock响应明确标识，真实路径未收费联调 |
| Railway公网/Docker/CI | NOT RUN | 无账号、DNS/TLS；本机无Docker运行环境 |

测试中的数据库是独立临时atoms_test库，非SQLite；每次结束清理，不删除项目atoms库。测试凭证使用随机临时密钥/非秘密fixture，Google交换与供应商网络采用测试替身。70项测试不等于需求45条AC全数通过。

## 2. 浏览器实测证据索引

所有以下DOM来自实际浏览器导航、点击、输入、刷新；不是生成的“通过截图”。文本保存于docs/evidence，截图editor-preview.png展示构建2紫色任务板与Mock标签。完整文件已随源码保存。

| 证据 | 实际动作与观察 | 裁决 |
|---|---|---|
| 01-model-gate.txt | Mock登录后关闭C05，仍只有模型门禁，无工作台业务 | PASS |
| 02-tested-not-saved.txt | 服务端Mock测试通过但未保存，仍需配置 | PASS |
| 03-build-after-refresh.txt | 首次构建刷新恢复“执行中断”，没有伪成功 | 缺陷证据，后续修复 |
| 04-build-success.txt | 修复后显式重试，构建1真实保存，iframe加载 | PASS |
| 05-task-persistence.txt | 预览新增任务→完成→编辑→刷新，记录及统计保留 | PASS |
| 06-independent-preview.txt | 独立预览新增记录→刷新仍存在 | PASS |
| 07-publication.txt | 确认发布→可达检查→published状态→真实URL | PASS（本地HTTP） |
| 08-public-visitor-empty.txt | 公开应用无需Key，无平台聊天/邮箱，初始0任务 | PASS |
| 09-public-delete.txt | 公开任务新增/刷新后删除确认，0任务 | PASS |
| 10-iteration-after-navigation.txt | 提交紫色迭代后离开工作台，回来构建2，旧任务仍在 | PASS |
| 11-update-publication.txt | 原URL保持、更新成功后不再显示未发布更改 | PASS |
| 12-failed-iteration-old-preview.txt | [mock:fail]迭代失败，构建2及已有任务可用 | PASS；记录中旧超时提示已修复 |
| 13-portfolio-interaction.txt | 创建第二类作品集，点击联系方式后出现示例信息 | PASS（明确Mock产物） |
| 14-rename-search.txt | 重命名后项目搜索显示新名称，可预览筛选 | PASS |
| 15-cancel-old-build.txt | [mock:slow]→停止弹窗→确认→已停止，作品集构建1保留 | PASS |
| 16-final-preview.txt | 修复超时提示后最终iframe正常、构建2及记录保留 | PASS |
| 17-delete-config-gate.txt | 专门删除配置后门禁重锁，项目未删除 | PASS |
| 18-owner-isolation.txt | Bob配置后访问Alice project，404不可访问 | PASS |
| 20-config-restored-on-login.txt | Alice退出后重登，服务端Mock配置恢复，无须重输Key | PASS |
| live-smoke.json | 最终真实运行服务首构建、双可达发布、迭代旧线上保留、稳定URL更新 | PASS（Mock身份/模型，平台链路真实） |
| 19-bob-empty-projects.txt | Bob项目列表0，不展示Alice项目 | PASS |

额外实际结果：复制链接按钮成功反馈“已复制”；不同项目预览/公开Origin；嵌入预览与顶层独立打开受浏览器第三方存储分区影响，二者不共享记录，但各自刷新保留。该差异已列边界，不伪装云同步。

## 3. 发现并修复

1. **阶段消息幂等键超出36字限制**，首构建转interrupted。修正为固定长度摘要，显式重试后真实构建成功；原失败保留，未自动重发未知计费请求。
2. **iframe与CSP不允许form** 导致任务添加未提交。按最小权限追加allow-forms，仍CSP form-action none防导航；复测新增、完成、编辑、删除通过。
3. **预览已经ready仍15秒后出现超时提示**。修复ready状态判断；最终预览证据无误报。
4. 旧V1.1浏览器Key存储/直连适配移除；API接收Key只在受保护测试配置链路，默认前端不保存，退出不删服务端密文。
5. 补齐Mock会话标记、开关关闭拒绝、生产Mock邮箱身份/模型/构建拒绝；随机密钥测试、AAD调包、DNS固定IP和错误路径测试。
6. 发布从仅核验预览完善为预览及公开候选双可达+artifact SHA256核验；模拟服务错误回滚测试保留旧publishedBuildId。
7. 迁移生成的未知名称downgrade约束修正；生产不执行破坏性downgrade。后续schema新增版本。

工具操作过程中遇到浏览器DOM重渲染造成旧ref失效、select需使用value、iframe文本提取需snapshot而非get_page_text：重新观察后复测，不把工具断言失败当产品已修复；证据只采用有真实观察的结果。

## 4. 实现与未完成差距

已落地平台核心：GoogleOAuth/邮箱OTP代码、owner/CSRF；服务端配置测试草稿/加密保存/删除；真实Postgres任务队列与独立Worker；规划、生成、一次修复、迭代；取消/租约/超时/失败保护；结构与JS语法校验、成功快照/保存重试；隔离预览与公开发布更新；搜索、筛选、重命名、消息恢复。

**不作全部完成声明的差距：**
- 真实模型语义能力未用用户API Key测试；本次两类产物是明确Mock fixture。真实Provider、加密和执行链路代码已实现，但必须上游联调后才能通过AC-08/32/37等真实项。
- 阶段轮询和完整规划/构建消息已实现，**没有逐token流式聊天输出**；不把阶段日志冒充token流。
- 生产KMS独立身份、最低解密权限、审计/轮换、备份保留/删除标记恢复治理未部署验证；当前AESGCM为成熟认证加密，开发文件主密钥不是KMS。不能声称满足完整AC-38/42/43生产治理。
- 后台接受任务持续运行已验证，但生产Worker崩溃、网络分区/供应商计费未知状态需真实staging复验；已用租约/取消单测验证保守不重放。
- 生成代码仅内联HTML/CSS/JS；无对象存储/CDN和任意后端部署，无P1手动代码编辑、团队、计费、完整版本恢复。
- 原P06要求公网HTTPS；当前仅localhost独立HTTP服务，未部署Railway或配置wildcard DNS/TLS。不制造假公网地址。
- 桌面当前浏览器797×819实际跑通，窄屏标签可用；1440/1280性能目标和所有手机尺寸未全量测量。

## 5. 45条需求验收映射

| 范围 | 状态与证据 |
|---|---|
| AC-01/02/03 | OTP真实逻辑自动化；邮件传输Mock，Google也未真实授权；不是供应商通过 |
| AC-04/05 | 会话/退出/过期自动化；Alice/Bob浏览器越权与列表隔离PASS |
| AC-06/07 | 输入校验/非法需求测试与示例只填入观察；中文IME代码保护，未单独IME人工测试 |
| AC-08 | 两类不同可运行Mock产物PASS；真实模型生成NOT RUN |
| AC-09/10/11/12/13 | 导航后台继续、单项目单活动、错误/预算、停止/重试去重PASS（上游Mock） |
| AC-14/15/17/18/21 | 任务CRUD、预览刷新、颜色迭代、失败停止旧版保留PASS；存储损坏路径有代码，禁用/配额异常未完整浏览器注入 |
| AC-16/29/38/41/42/44 | 权限/隔离/API不回显/AESGCM/DNS出站及语法安全测试PASS；生产KMS/全量日志/仓库审计未部署 |
| AC-19 | 已有候选仅重试保存不新run测试PASS；真实数据库中断全链路未注入 |
| AC-20/36 | 服务端配置恢复/删除代码与浏览器删除/账号隔离PASS；新设备与供应商Key真实NOT RUN |
| AC-22/23/24/25/27/40 | 本地公开服务可达、旧版本保护、稳定URL更新、预览数据隔离、复制PASS；公网HTTPSNOT RUN |
| AC-26 | 浏览器名称搜索/重命名、API筛选分页PASS；拉取断网仅代码路径 |
| AC-28/30 | 本机启动/深链PASS，生产域和1440/1280多端/时延NOT RUN |
| AC-31/34/35 | 关闭门禁、测试未保存、字段失效、测试幂等/到期自动化PASS；上游为Mock |
| AC-32/33/37 | 真实Provider路径及错误分类/固定配置代码已实现；真实供应商请求NOT RUN，不能标实模型通过 |
| AC-39/45 | 后台退出继续、租约到期及旧Worker拒绝测试PASS；真实生产进程故障NOT RUN |
| AC-43 | 主库删除密文、停止任务与晚成果拒绝PASS；备份恢复删除标记策略未落实 |

## 6. 所有Mock及上线去除

完整登记在MOCK_REGISTER.md：M01身份、M02连接、M03模型产物、M04故障延时、M05自动化网络替身、M06开发文件主密钥、M07本地应用域/TLS、M08邮件、M09Railway/CI未实测。后五项包含开发替代/未配置，不误称已经上线功能。

上线必须：DEV_MOCK_AUTH=false、DEV_MOCK_MODEL=false；清测试身份/配置/Mock产物，不导入测试库；Google/SMTP真实配置；独立CREDENTIAL_MASTER_KEY/KMS权限与治理；真实模型测试并生成任务板/作品集；配置Application两套独立wildcard DNS/TLS；Railway平台/Worker/Application/Postgres实际部署；Docker镜像/CI/staging复测；验证无Key泄漏、HTTPS会话与45条生产验收。

## 7. 交付与重跑

代码仍在主项目目录。源码包排除.env、运行库、密钥文件与临时预览签名地址，保留测试、Mock登记、启动脚本、部署配置与DOM/截图证据。
重跑：bash scripts/test.sh。浏览器从 /dev-test开始，Mock标签必须可见；不能使用Mock路径验证真实Google授权。

当前保留本地服务运行方便查看，后台没有活动计费任务。真实用户提供方配置为空，本轮未发送真实模型收费请求、未创建Railway付费服务。
