# 项目 TODO

> 本文件是全部工作项的唯一权威来源。历史事项只改变状态，不删除。

## 字段与状态

- 状态：待处理、进行中、阻塞、待验收、已完成、已废弃、已被替代
- 优先级：P0、P1、P2、P3
- 使用 `python3 tools/project_guard.py add . ...` 新增事项。
- 使用 `python3 tools/project_guard.py transition . T-001 ...` 变更状态。

## T-001 | 搭建基础前后端与数据库框架

- 状态：已完成
- 阶段：框架
- 优先级：P0
- 验收条件：React页面与FastAPI登录项目接口可运行，PostgreSQL迁移与数据隔离有效，未实现P0能力明确标识
- 依赖：无
- 替代关系：无
- 执行证据：README.md; backend/app; frontend/src; docs/backend-test-results.xml; docs/frontend-test-results.xml
- 变更说明：2026-11-23：基础框架代码与自动化验证完成，不包含完整P0生成发布
- 最后更新：2026-11-23

## T-002 | Railway部署配置与增量更新说明

- 状态：已完成
- 阶段：部署
- 优先级：P0
- 验收条件：Docker构建、PORT、数据库变量、迁移、生产安全校验与README齐全；实际云部署状态如实记录
- 依赖：无
- 替代关系：无
- 执行证据：Dockerfile; railway.json; docs/RAILWAY.md; backend/run.py; .env.example
- 变更说明：2026-11-23：部署配置和说明齐全；未实际云部署或Docker构建已明确记录
- 最后更新：2026-11-23

## T-003 | 本地启动和自动化自测

- 状态：已完成
- 阶段：验证
- 优先级：P0
- 验收条件：真实PostgreSQL启动，前后端运行，API测试、前端构建与浏览器测试有报告
- 依赖：无
- 替代关系：无
- 执行证据：docs/SELF_TEST.md; docs/evidence; docs/backend-test-results.xml; docs/frontend-test-results.xml
- 变更说明：2026-11-24：已完成实际Mock浏览器闭环与自动化，自测限制明确登记
- 最后更新：2026-11-24

## T-004 | 修正自检发现的会话与页面边界问题

- 状态：已完成
- 阶段：验证
- 优先级：P0
- 验收条件：CSRF跨标签稳定，验证码重发挑战正确，窄屏可退出，草稿与保存状态不误导
- 依赖：无
- 替代关系：无
- 执行证据：docs/SELF_TEST.md; backend/tests; frontend/src/lib/draft.ts; frontend/src/pages/Verify.tsx
- 变更说明：2026-11-23：边界问题代码修复并自动化回归，真实浏览器复核仍由T-003追踪
- 最后更新：2026-11-23

## T-005 | 后续接入真实AI生成、独立源预览与发布

- 状态：待验收
- 阶段：增量
- 优先级：P1
- 验收条件：用户后续启动此增量后完成run租约、用户Key编排、构建校验与真实发布；当前不执行
- 依赖：无
- 替代关系：无
- 执行证据：backend/app/worker.py; docs/evidence/live-smoke.json; docs/SELF_TEST.md
- 变更说明：2026-11-24：生成迭代取消预览本地发布已实现并Mock闭环通过；真实模型公网和逐token仍未全验收
- 最后更新：2026-11-24

## T-006 | 接入Google OAuth登录

- 状态：已完成
- 阶段：认证
- 优先级：P0
- 验收条件：真实Google OAuth授权码流程、state/nonce与ID token校验，生产安全回调，稳定Google用户映射，缺凭证明确禁用；真实Google联调状态如实记录
- 依赖：无
- 替代关系：无
- 执行证据：docs/GOOGLE_LOGIN.md; .runtime/google-login-smoke.json; https://github.com/ruan-collabs/atoms-demo/actions/runs/45348425104
- 变更说明：2026-11-24：用户两次真实Google授权成功，Query恢复、模型门禁、退出401与同账号复用验证通过；不算真实模型或生产全验收
- 最后更新：2026-11-24

## T-007 | 开发Mock与完整本地验收证据

- 状态：已完成
- 阶段：验证
- 优先级：P0
- 验收条件：开发Mock登录/模型显式标识，生产强制禁用，浏览器业务闭环证据及上线去Mock清单齐全
- 依赖：无
- 替代关系：无
- 执行证据：docs/MOCK_REGISTER.md; docs/evidence; docs/SELF_TEST.md
- 变更说明：2026-11-24：开发Mock全部明确登记，生产拒绝，实际浏览器证据及自测报告齐全
- 最后更新：2026-11-24

## T-008 | 切换V1.2服务端加密模型配置与后台Worker

- 状态：待验收
- 阶段：模型
- 优先级：P0
- 验收条件：服务端测试草稿15分钟、AESGCM绑定owner版本、硬门禁、Worker独立后台与取消租约、SSRF受控出站，Mock生产禁用
- 依赖：无
- 替代关系：无
- 执行证据：backend/tests/test_generation.py; docs/SELF_TEST.md
- 变更说明：2026-11-24：服务端AESGCM/硬门禁/Worker已通过本地测试；生产KMS权限备份治理未配置
- 最后更新：2026-11-24

## T-009 | 修复浏览器闭环发现的Worker与预览问题

- 状态：已完成
- 阶段：验证
- 优先级：P0
- 验收条件：生成阶段消息幂等键合法，真实Worker完成并保存构建，预览加载和行为证据完整
- 依赖：无
- 替代关系：无
- 执行证据：docs/evidence/04-build-success.txt; docs/evidence/16-final-preview.txt
- 变更说明：2026-11-24：Worker消息长度、表单sandbox和预览超时误报已修复并复测
- 最后更新：2026-11-24

## T-010 | 预览嵌入与独立打开存储差异说明

- 状态：已完成
- 阶段：验证
- 优先级：P1
- 验收条件：记录浏览器第三方存储分区导致iframe与顶层同Origin数据差异，不将其当跨端同步或数据迁移
- 依赖：无
- 替代关系：无
- 执行证据：docs/SELF_TEST.md; docs/MOCK_REGISTER.md
- 变更说明：2026-11-24：记录嵌入与顶层存储分区差异，不承诺同步
- 最后更新：2026-11-24

## T-011 | 完善发布可达核验与生产去Mock门禁

- 状态：已完成
- 阶段：上线
- 优先级：P0
- 验收条件：真实公开资源核验失败保留旧版，生产Mock数据/配置不执行，部署角色分离和上线上配置项记录
- 依赖：无
- 替代关系：无
- 执行证据：docs/evidence/live-smoke.json; backend/tests/test_generation.py; docs/RAILWAY.md
- 变更说明：2026-11-24：双可达及SHA256发布核验、Mock会话和产物生产拒绝、部署说明完善
- 最后更新：2026-11-24

## T-012 | 核查Railway部署并安全推送GitHub

- 状态：已完成
- 阶段：部署
- 优先级：P0
- 验收条件：核对安全与交付规则，检查部署与Mock/凭证泄漏，确定仓库和分支，仅推送必要源码并回读commit证据，不执行Railway部署
- 依赖：无
- 替代关系：无
- 执行证据：docs/GITHUB_DELIVERY.md; docs/PREDEPLOY_CHECKLIST.md; https://github.com/ruan-collabs/atoms-demo/commit/951819e07f685286a2da4d73546da18e73591b7c; https://github.com/ruan-collabs/atoms-demo/actions/runs/45317051622
- 变更说明：2026-11-24：公开仓库main已推送94份审核源码；远端ZIP SHA256逐文件一致；本地70后端/11前端/生产build与GitHub CI含Docker镜像build成功；Railway未部署
- 最后更新：2026-11-24

## T-013 | 从GitHub源码部署Railway并验证生产上线边界

- 状态：已被替代
- 阶段：上线
- 优先级：P0
- 验收条件：使用ruan-collabs/atoms-demo main创建Railway持久化数据库与三个运行角色，关闭Mock，配置稳定密钥与HTTPS，验证迁移健康和公网；缺认证或通配域时明确阻塞，不冒称完整闭环
- 依赖：无
- 替代关系：T-015
- 执行证据：docs/RAILWAY_DEPLOYMENT_STATUS.md; https://railway.com/project/0df6d4d5-c36e-4762-8817-a853fe4298e2
- 变更说明：2026-11-24：当前部署目标改为显式Mock演示入口；真实生产完整验收不在本轮执行
- 最后更新：2026-11-24

## T-014 | 适配Railway新服务不支持Config-as-code的部署规则

- 状态：已完成
- 阶段：上线
- 优先级：P0
- 验收条件：将启动迁移健康规则正确设置到Railway界面，核实用户最新要求的显式development Mock阶段变量，不修改production禁Mock规则
- 依赖：无
- 替代关系：无
- 执行证据：docs/RAILWAY_DEPLOYMENT_STATUS.md; https://atoms-demo-production-57bed089.up.railway.app/api/health
- 变更说明：2026-11-24：Railway UI已应用python run.py、alembic upgrade head、/api/health；显式development Mock变量已核实，外网健康正常；生产安全规则未改
- 最后更新：2026-11-24

## T-015 | 发布显式Mock阶段Railway HTTPS演示入口

- 状态：已完成
- 阶段：演示部署
- 优先级：P0
- 验收条件：按用户新要求从GitHub main发布Railway提供的HTTPS入口，数据库健康与前端外网可访问，明确Mock与未验生成预览发布，不接真实身份及用户Key，不改production禁Mock规则
- 依赖：无
- 替代关系：无
- 执行证据：docs/RAILWAY_DEPLOYMENT_STATUS.md; https://atoms-demo-production-57bed089.up.railway.app/dev-test; https://atoms-demo-production-57bed089.up.railway.app/api/health
- 变更说明：2026-11-24：GitHub main部署成功，浏览器渲染及无账号HTTPS请求页面与静态资源HTTP200，Postgres迁移健康ok，Mock标签清晰，真实身份与生成预览发布未验明确
- 最后更新：2026-11-24

## T-016 | 固化安全规则与项目验收门禁

- 状态：已完成
- 阶段：规则
- 优先级：P0
- 验收条件：核对项目规则，安全与部署检查项写入维护清单，AGENTS和项目规则指向清单；Mock演示与正式验收区分，不上传非公开资料、不改代码部署
- 依赖：无
- 替代关系：无
- 执行证据：AGENTS.md; PROJECT_RULES.md; docs/PREDEPLOY_CHECKLIST.md; PROJECT_STATE.md
- 变更说明：2026-11-24：固定红线、最小闭环、部署排查、凭证与额度规则固化到现有清单，AGENTS和项目规则引用，Mock阶段与最终验收区分；未推送或改部署
- 最后更新：2026-11-24

## T-017 | 移除文档来源归因并保留交付规则

- 状态：已完成
- 阶段：规则
- 优先级：P0
- 验收条件：相关项目文件去除特定材料名称与来源表述；安全规则部署要求验收事实不变，保留历史待办与证据；不修改原始附件或远端
- 依赖：无
- 替代关系：无
- 执行证据：docs/PREDEPLOY_CHECKLIST.md; PROJECT_RULES.md; PROJECT_STATE.md; README.md; TODO.md; docs/GITHUB_DELIVERY.md
- 变更说明：2026-11-24：项目Markdown中的特定材料名称与来源描述已去除，改为项目检查规则与非公开资料表述；保留安全验收内容和历史待办证据；未修改原始附件或远端
- 最后更新：2026-11-24

## T-018 | 回归修复Mock演示核心生成预览持久化链路

- 状态：已完成
- 阶段：验证
- 优先级：P0
- 验收条件：实际测试Mock入口、连接保存、生成迭代、可交互预览、刷新恢复；修复缺陷且分别记录本地与Railway结果，不以页面200代替闭环
- 依赖：无
- 替代关系：无
- 执行证据：docs/RAILWAY_DEPLOYMENT_STATUS.md; docs/INCREMENTAL_ACCEPTANCE.md; .runtime/railway-sandbox-smoke.json
- 变更说明：2026-11-24：Mock无主密钥配置及公网生成交互刷新迭代发布通过；真实供应商不算已验
- 最后更新：2026-11-24

## T-019 | 支持未登录浏览核心页及提交Query后登录恢复

- 状态：已完成
- 阶段：交互
- 优先级：P0
- 验收条件：访客可浏览公共工作台和输入需求，提交后无登录才转登录，保留Query并登录后恢复，私有项目接口仍鉴权隔离
- 依赖：无
- 替代关系：无
- 执行证据：docs/INCREMENTAL_ACCEPTANCE.md; frontend/src/lib/pending-query.test.ts; frontend/src/pages/Dashboard.tsx
- 变更说明：2026-11-24：公共工作台与项目壳匿名可见，提交才登录，Query一次恢复不自动生成；本地浏览器实测与16前端/89后端及构建通过，未上线
- 最后更新：2026-11-24

## T-020 | 完善DeepSeek官方接口适配且不进行真实调用

- 状态：已完成
- 阶段：模型
- 优先级：P0
- 验收条件：官方base URL请求格式模型错误处理适配并契约单测，不调用真实供应商或绕过已通过的连接门禁，不公开Key
- 依赖：无
- 替代关系：无
- 执行证据：backend/tests/test_provider.py; docs/INCREMENTAL_ACCEPTANCE.md
- 变更说明：2026-11-24：DeepSeek官方请求模型预设错误与截断契约适配并模拟HTTP单测，无真实模型调用；真实凭证加密保持
- 最后更新：2026-11-24

## T-021 | 接入Pipecat实现Query语音实时转文字

- 状态：待验收
- 阶段：语音
- 优先级：P1
- 验收条件：用户明确选择语音输入实时转文字，提供安全的Pipecat服务端接入可配置STT凭证、麦克风启停和临时最终文本交互，未配置明确禁用；不自动发送Query，真实联调由凭证配置后验收
- 依赖：无
- 替代关系：无
- 执行证据：backend/tests/test_voice.py; frontend/src/lib/pending-query.test.ts; docs/INCREMENTAL_ACCEPTANCE.md
- 变更说明：2026-11-24：Pipecat实时语音转文字接口/采样/按钮已实现，真实Pipecat管线配模拟STT测试通过；缺实际语音供应商凭证，真实麦克风端到端未验
- 最后更新：2026-11-24

## T-022 | 实现Mock专用沙箱预览并上线公网闭环

- 状态：已完成
- 阶段：演示部署
- 优先级：P0
- 验收条件：Mock iframe无same-origin权限，通信验证source与通道，仅持久化白名单应用数据按项目隔离；保留真实模型独立域路径；更新GitHub/Railway Worker并公网回归生成预览恢复迭代发布
- 依赖：无
- 替代关系：无
- 执行证据：docs/RAILWAY_DEPLOYMENT_STATUS.md; backend/tests/test_mock_sandbox.py; .runtime/railway-sandbox-smoke.json; https://github.com/ruan-collabs/atoms-demo/actions/runs/45339583822
- 变更说明：2026-11-24：用户授权沙箱已部署e2246a9；无same-origin权限、白名单保存与公网匿名分享刷新通过
- 最后更新：2026-11-24

## T-023 | Google真实登录调试前加固HTTPS会话Cookie与出站

- 状态：已完成
- 阶段：认证
- 优先级：P0
- 验收条件：HTTPS演示Cookie启用Secure；Google交换不使用环境代理；保留state/nonce/PKCE与回放拒绝；自动化通过，不向日志或源码写凭证
- 依赖：无
- 替代关系：无
- 执行证据：backend/tests/test_google.py; docs/GOOGLE_LOGIN.md; https://github.com/ruan-collabs/atoms-demo/commit/bf0f60d17d92584497d76fcb380d751180c9d170
- 变更说明：2026-11-24：HTTPS Secure Cookie、默认APP_SECRET拒绝及Google固定出站修复已部署；94后端/18前端/构建与CI通过
- 最后更新：2026-11-24

## T-024 | 验证Railway加密主密钥与DeepSeek真实连接测试

- 状态：进行中
- 阶段：模型
- 优先级：P0
- 验收条件：确认用户新增主密钥部署生效，仅点击既有DeepSeek配置连接测试并回读脱敏结果，不读取或记录Key、不生成应用、不自动重复计费请求
- 依赖：无
- 替代关系：无
- 执行证据：待补充
- 变更说明：2026-11-24：用户已添加加密主密钥并授权真实连接测试，替代本轮不调用的临时限制；不扩大为生成部署
- 最后更新：2026-11-24

## T-025 | 核实并接入DeepSeek语音识别替代Deepgram

- 状态：已被替代
- 阶段：语音
- 优先级：P1
- 验收条件：核实DeepSeek官方ASR及流式协议，支持时接入Pipecat与已加密用户Key，限额鉴权和不落音频；不支持实时或无法核实时说明阻塞，不冒称流式或偷偷换供应商
- 依赖：无
- 替代关系：T-021
- 执行证据：DECISIONS.md; https://api-docs.deepseek.com/guides/asr/
- 变更说明：2026-11-24：官方DeepSeek ASR不支持流式，用户已明确保留实时转写方案，继续既有T-021语音接入；未改代码部署
- 最后更新：2026-11-24

## T-026 | 切换火山新版API Key实时语音识别并上线

- 状态：待验收
- 阶段：语音
- 优先级：P1
- 验收条件：火山新版X-Api-Key鉴权、官方双向流式协议、Pipecat运输保留、转写去重停止收尾与限额安全；不读密钥值；测试构建部署及短录音真实验收分别记录
- 依赖：无
- 替代关系：无
- 执行证据：docs/VOICE_INPUT.md; backend/tests/test_volcengine_asr.py; https://github.com/ruan-collabs/atoms-demo/actions/runs/45369863718
- 变更说明：2026-11-24：火山8b0c413代码CI与Railway部署通过；短录音接管后文本变化但未直接抓到interim/final事件，真实流式完整验收不冒称完成
- 最后更新：2026-11-24

## T-027 | 麦克风图标移到发送旁并取消二次确认

- 状态：已完成
- 阶段：交互
- 优先级：P1
- 验收条件：工作台和编辑器发送按钮旁纯麦克风图标；直接点击申请麦克风，无业务确认弹窗；保留浏览器权限、供应商告知、录音停止/收尾/错误状态及发送锁定；测试部署和界面回读
- 依赖：无
- 替代关系：无
- 执行证据：docs/VOICE_INPUT.md; frontend/src/components/voice-input.test.ts; https://github.com/ruan-collabs/atoms-demo/actions/runs/45372756267
- 变更说明：2026-11-24：7485c4f已部署；公网工作台及本地编辑器同排相邻纯Mic图标回读，点击无confirm组件测试、99后端/21前端/构建及CI通过；浏览器权限保留
- 最后更新：2026-11-24

## T-028 | 移除麦克风空闲提示文案

- 状态：已完成
- 阶段：交互
- 优先级：P1
- 验收条件：移除指定空闲提示及其悬浮文案，不留空白提示行；保留录音收尾错误与浏览器权限；前端测试构建及Railway回读
- 依赖：无
- 替代关系：无
- 执行证据：frontend/src/components/voice-input.test.ts; https://github.com/ruan-collabs/atoms-demo/commit/a6254eff592e60e135b306dedcff77ad411f8893
- 变更说明：2026-11-24：a6254ef已部署；公网空闲提示与空行消失、Mic标题仅操作名，21前端测试及构建通过，录音错误逻辑不变
- 最后更新：2026-11-24

## T-029 | 参考录屏设计核心生成交互与卡住状态反馈

- 状态：已完成
- 阶段：设计
- 优先级：P0
- 验收条件：读取截图与录屏交互，核实等待Worker原因；先交付独立视觉设计稿及状态流，不照搬视频，不开发或部署新交互；用户确认后进入开发
- 依赖：无
- 替代关系：无
- 执行证据：docs/core-interaction-design/brief.md; https://bytedance.larkoffice.com/docx/VGO3d1esdoCcLqx8Wb5cHEEsn0a
- 变更说明：2026-11-24：用户明确开始开发，三态设计方向已确认
- 最后更新：2026-11-24

## T-030 | 实现已确认核心生成交互与真实执行门禁

- 状态：已完成
- 阶段：开发
- 优先级：P0
- 验收条件：执行器心跳与无服务门禁，旧queued不自动消费；真实DeepSeek内容流式及脱敏事件，三视图状态UI，独立源预览；保留认证模型语音规则；自动化与本地浏览器闭环分别验收，未部署不称线上已修复
- 依赖：无
- 替代关系：无
- 执行证据：docs/CORE_INTERACTION_DEVELOPMENT.md; docs/APPLICATION_SANDBOX_ACCEPTANCE.md; https://github.com/ruan-collabs/atoms-demo/actions/runs/45410356880
- 变更说明：2026-11-24：三态交互和持久流式恢复已实现并部署；真实生成运行及主题迭代通过。应用运行方案依用户D-012改为opaque iframe，完整扩展验收由T-032继续
- 最后更新：2026-11-24

## T-031 | 同步核心交互源码并部署真实Worker角色

- 状态：已完成
- 阶段：上线
- 优先级：P0
- 验收条件：安全同步公开GitHub固定commit并核验CI/Railway迁移；独立Worker引用稳定密钥与数据库，不读取Key或消费旧version0排队；真实预览域TLS缺失如实阻塞，不放宽隔离；公网界面与真实执行分别验收
- 依赖：无
- 替代关系：无
- 执行证据：docs/RAILWAY_DEPLOYMENT_STATUS.md; docs/APPLICATION_SANDBOX_ACCEPTANCE.md; https://github.com/ruan-collabs/atoms-demo/actions/runs/45410356880
- 变更说明：2026-11-24：固定133份应用源码核验、CI成功，Platform与独立真实Worker同版本Active、迁移健康；旧queued未自动消费、Worker无公网，部署收尾记录已更新
- 最后更新：2026-11-24

## T-032 | 实现真实生成应用的同域入口隔离沙箱

- 状态：待验收
- 阶段：开发上线
- 优先级：P0
- 验收条件：Railway path包装入口；生成HTML在opaque iframe运行无same-origin；专用受限JSON存储桥ACK后保存、owner/project/public隔离；不传会话Key平台API、Mock仍严格fixture；安全及真实生成交互回归，部署证据分别记录
- 依赖：无
- 替代关系：无
- 执行证据：docs/APPLICATION_SANDBOX_ACCEPTANCE.md; docs/RAILWAY_DEPLOYMENT_STATUS.md; https://atoms-demo-production-57bed089.up.railway.app/apps/03d682c4-fdcd-490f-8fb4-6b69c98eb154
- 变更说明：2026-11-24：真实生成交互持久化、主题迭代公开更新、Platform/Worker重部署后会话/配置元信息/构建2/消息/私人公开记录恢复通过；第二类真实应用、保存失败/对抗安全、无痕手机与生产治理仍待验
- 最后更新：2026-11-24

## T-033 | 移除预览加载成功后的固定状态提示并上线

- 状态：已完成
- 阶段：交互
- 优先级：P1
- 验收条件：真实及Mock预览、独立预览、公开应用加载成功后无固定提示或空白状态栏；加载中与失败提示保留，隔离与存储逻辑不变；前端测试构建、GitHub同步与Railway界面回读
- 依赖：无
- 替代关系：无
- 执行证据：frontend/src/components/preview-status.test.ts; docs/RAILWAY_DEPLOYMENT_STATUS.md; https://github.com/ruan-collabs/atoms-demo/commit/5a81c12b07b0c0cef6ab5d6d5fa9f4ad2ae9d178; https://github.com/ruan-collabs/atoms-demo/actions/runs/45416749606
- 变更说明：2026-11-24：成功提示与占位节点已统一移除，加载和运行/存储错误保留；32前端测试/build及CI通过。Railway已部署，真实编辑器、独立与公开预览无提示且原记录保留，隔离不变，无模型调用
- 最后更新：2026-11-24

## T-034 | 排查最近生成失败并增加最多三次有界自动重试

- 状态：已完成
- 阶段：修复上线
- 优先级：P0
- 验收条件：回读最近两次失败项目与Railway Worker/平台日志定位原因；修复输出截断/契约问题并测试；首次失败后最多3次有界自动重试，退避、取消/配置版本/预算/租约有效，安全拒绝不降级、未知计费不盲重放；同步源码并上线回读
- 依赖：无
- 替代关系：无
- 执行证据：backend/tests/test_generation_retry.py; docs/RAILWAY_DEPLOYMENT_STATUS.md; https://github.com/ruan-collabs/atoms-demo/actions/runs/45422147983; https://atoms-demo-production-57bed089.up.railway.app/projects/ab065566-2556-4c99-8006-b7c9a33e3e33
- 变更说明：2026-11-24：Worker/Platform日志正常、末次输出中途截断和8K限额及localStorage规划冲突已定位修复；3次共享有界自动重试、安全错误与未知计费不重放、脱敏日志已部署071e1f3。137后端32前端/build/迁移与CI成功，原失败笔记构建1新增标签及刷新恢复通过；重试故障用隔离替身测试，不冒称真实故障现场
- 最后更新：2026-11-24

## T-035 | 收敛Google登录页与DeepSeek模型入口并上线

- 状态：待验收
- 阶段：交互上线
- 优先级：P1
- 验收条件：登录页只提供Google业务登录，移除邮箱表单与其他业务入口；模型默认DeepSeek，其他供应商禁用且hover/键盘焦点提示模型未上线；不破坏既有会话/配置/Mock测试专用入口；组件测试构建与Railway界面回读
- 依赖：无
- 替代关系：无
- 执行证据：frontend/src/components/model-availability.test.ts; backend/tests/test_model_availability.py; frontend/src/pages/Login.tsx
- 变更说明：2026-11-25：Google-only登录页、默认DeepSeek与OpenAI/custom禁用hover/焦点提示、真实账号隐藏Mock选择及后端新配置拒绝已实现；36前端139后端/build与迁移检查通过，准备GitHub/Railway同步，保留既有会话配置
- 最后更新：2026-11-25

<!-- 待办由守门器追加到此处 -->
