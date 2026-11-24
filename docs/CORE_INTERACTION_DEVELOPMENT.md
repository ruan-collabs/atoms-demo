# 核心生成交互开发记录（T-030）

## 本轮范围

用户已确认三态设计并要求开始开发。本轮完成本地源码增量与验证，未推送GitHub、未更新Railway、未新增云服务、未调用真实DeepSeek或录音。线上目前的真实Worker/Application缺失仍需后续部署解决，不能据本地通过宣称线上已修复。

## 已实现

- 项目编辑器：需求对话/公开结构化规划卡、真实阶段、预览/代码/活动三视图、生成字节、版本与服务状态、手机/桌面宽度、改写建议只填草稿、保持纯麦克风紧邻发送。
- 无可用Worker时后端503拒绝新run，前端保留需求，工作台可只读检查服务。心跳5秒写一次，20秒过期；Mock-only心跳不满足真实模型。
- DeepSeek/OpenAI内容流式消费（SSE）、固定公共IP/Host/TLS SNI、禁代理和重定向；不展示reasoning；跨chunk凭证拦截、响应大小与超时限制；stream_text/bytes持久化，run/revision/offset增量恢复去重。规划仍受限完整响应；Mock只展示完整fixture，不假装token流。
- 新迁移a7c932e108df，追加心跳表、流式字段与dispatch_version；旧真实queued默认为0，新Worker不消费。用户显式重新提交会取消旧任务并保留记录，生成新的version1任务。新真实queued等待超过60秒则中断待手动重试，不晚到自动计费。
- 完整代码安全校验并保存后才运行，隔离源iframe继续保留。ready/error桥增加build_id，并验证source/origin/build。Application预览和公开实例分别设置APPLICATION_ROLE=application/publication，分别报告心跳；未配置时发布禁用、接口503，不提供假URL。

## 自动化证据

完整后端109项通过（真实临时loopback PostgreSQL，隔离测试数据库自动回收）；前端25项通过；TypeScript/Vite生产构建通过；Alembic check无漂移。最后补充queued时限、Key长度和服务恢复effect后再次42项核心后端回归、25项前端及构建通过，Alembic check仍无漂移。

新增测试：test_stream_provider.py的真实协议解析+上游HTTP替身，content-only/DONE与stop/截断/跨chunkKey；test_readiness.py的无服务拒绝、Mock-only与过期心跳、legacy不消费且手动重试、stream reset/owner、真实provider调用路径替身与保存、预览发布心跳分离。前端generation.test.ts及editor.test.ts覆盖去重/修复revision、blocked而非生成、公开计划与只读服务检查、纯Mic相邻及无假代码。

以上不是真实供应商调用证明。

## 实际浏览器结果

本地端口5173/8000/8001/8002与独立Worker真实启动；使用既有明确Mock身份与Mock配置。

- Worker启动前工作台提交需求，503“生成服务未就绪”，完整输入保留；未创建新项目。
- Worker启动后同需求手动提交，项目07a4421b-6150-4165-ad6b-8f05c1f68d05保存构建1，结构化规划卡、三个视图和发布入口可见；独立Application iframe返回ready，无15秒误报。
- 预览真实新增“新版交互验收任务”，统计1；刷新平台后仍存在。
- 代码标签显示index.html与保存的代码，活动标签显示实际阶段和服务状态。
- 发送紫色迭代，构建2保存，自动预览；任务仍在。图形截图实际紫色主题与版本2，不是设计渲染。
- 显式[ mock:fail ]迭代后显示生成失败与供应商失败；版本2保持，原任务仍可操作，未切Mock以外兜底或覆盖成功构建。

本轮UI测试是Mock产物而非真实模型；不外推火山语音、Google、公开发布与公网真实生成。原语音配置本地未配置提示保留，不改变线上火山配置。

## 下一步部署边界

1. 推送前仅必要源码与文档，排除原截图视频、.runtime、Key与本地数据库；本机git无正常提交历史，远端固定commit逐文件差异对照。
2. Platform先追加迁移，再启动新版本角色。稳定APP_SECRET/CREDENTIAL_MASTER_KEY须在Platform/Worker/Application一致，不重新生成；Worker不开放公网。
3. 真实预览/公开服务配置每项目独立安全源DNS/TLS；只心跳不证明域名可达。Railway默认单域不能冒充wildcard。明确预览与公开APPLICATION_ROLE，检查实际域与HTTPS。
4. 不自动执行历史queued。迁移时旧version0保护保留，用户在新UI手动重新提交后才执行。
5. 真Key连接与两类不同需求真实生成、交互、刷新、迭代、失败旧版保护、发布和重部署持久化独立验收；未完成保持待验收。
