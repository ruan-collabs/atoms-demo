# 项目状态

- 项目名称：Atoms
- 项目目标：建立 React + Python + PostgreSQL 的 Railway 可部署基础框架，支持后续增量迭代
- 当前阶段：核心生成交互本地开发完成，云部署与真实供应商闭环待验收
- 当前焦点：T-030本地增量收尾；T-005/T-008真实执行与隔离预览上线
- 阻塞事项：Railway真实Worker与Application未部署；域名TLS待配置，未调用真实DeepSeek
- 待验收范围：真实生成/预览/发布公网闭环、真实语音完整事件与模型连接测试、生产Secret治理
- 下一步：同步必要源码与追加迁移后，配置独立Worker/Application和隔离源；旧queued保留等待用户手动重新提交
- 最后更新：2026-11-24

## 当前摘要

V1.2服务端加密配置、独立PostgreSQL Worker、生成/迭代/取消恢复、隔离预览及本地公开发布更新已实现。本轮公开GitHub ruan-collabs/atoms-demo main已推送，首次94份源码下载校验一致，CI成功含Docker镜像build；代码交付见docs/GITHUB_DELIVERY.md。实际浏览器Mock闭环证据仅本地保留；本轮回归70后端/11前端通过。本轮Railway项目selfless-contentment已连接GitHub main，Postgres与postgres-volume已创建。按用户最新Mock阶段要求，平台UI启动/迁移/健康与development Mock变量已应用，Deploy成功，外网HTTPS及前端资源HTTP200，健康检查status=ok且迁移46670bfb6eb1。演示入口https://atoms-demo-production-57bed089.up.railway.app/dev-test。Worker/Application和稳定加密配置未接通，不声称生成预览发布闭环完成。详细进度见docs/RAILWAY_DEPLOYMENT_STATUS.md。真实身份与模型、生产密钥治理、完整公网链路、逐token流式仍未验收，不标生产AC全通过。

## 最新增量

T-029设计已获用户明确批准；T-030新增三视图编辑器、公开规划卡、真实内容流式及持久恢复、Worker/Application/公开实例心跳门禁、历史queued防自动消费。完整109后端/25前端与生产构建通过，Alembic无漂移；本地浏览器无Worker时503且草稿保留，新Mock构建1新增任务刷新恢复、紫色迭代构建2保留原任务。真provider路径用上游替身测试，不算真实DeepSeek。未推送GitHub或部署Railway，详见docs/CORE_INTERACTION_DEVELOPMENT.md。下文保留历史记录。

T-018线上复现Mock配置缺主密钥，已改为非秘密fixture标记无需主密钥，真实供应商仍加密且共享Mock账号拒真Key。本地浏览器完成生成、任务交互刷新、改色迭代、项目恢复和实际发布，89后端/16前端及构建通过。T-019访客可浏览工作台/项目壳，提交Query后登录并恢复文本，不自动计费执行。T-020DeepSeek按官方当前模型预设及请求错误契约适配，不真实调用。T-021Pipecat STT实时转文字接口/按钮/采样已实现，真实管线用模拟STT通过，真实音频凭证未配置。细节见docs/INCREMENTAL_ACCEPTANCE.md。最新沙箱代码e2246a9已推GitHub并逐文件核验113份源码，远端CI 45339583822成功含Docker build。Railway已应用Mock沙箱/Mock-only后台开关并成功上线；公网Mock生成、交互、刷新恢复、迭代、失败旧版保护、匿名分享刷新均通过。真实语音未配、真实DeepSeek未调用。本地最新91后端/18前端及构建通过。收尾文档f76ad5已同步远端且触发Railway成功重部署，重新Mock登录后配置、项目、消息、构建2与发布恢复，预览/公开任务数据仍在；最后补充回读记录仅本地保存。

## 固定执行约束

项目安全规则与部署检查项已固化至docs/PREDEPLOY_CHECKLIST.md，AGENTS.md和PROJECT_RULES.md要求每次开发、推送、部署、交付前读取执行。当前Mock页面上线只是阶段交付，不满足最终真实生成→运行交互→持久化闭环的验收。规则以项目自身要求表述，不保留外部材料名称或来源归因。本轮仅修改本地说明文件，未推送GitHub或改Railway配置。

## 项目扩展字段

- 项目类型：React TypeScript + FastAPI Python + PostgreSQL，Railway单App加数据库
- 验证方式：scripts/test.sh；docs/*test-results.xml；docs/SELF_TEST.md
