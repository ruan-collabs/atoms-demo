# 决策记录

> 本文件只追加关键方向决策，不覆盖历史。被推翻的决策应标记为“已取代”，并链接新决策。

## D-010｜去除空闲语音说明（2026-11-24）

T-028按用户要求去除空闲语音长说明及同文悬浮提示，空状态不渲染提示行；图标title仅操作名称。此项更新D-009的常驻说明展示规则，保留录音连接/停止收尾/错误状态、浏览器权限与既有音频安全边界，不改变发送或录音触发行为。

## D-009｜录音按钮纯图标与无二次确认（2026-11-24）

T-027：用户要求工作台/编辑器的麦克风放在发送按钮旁、只保留Mic图标，移除业务window.confirm。主动点击即申请麦克风，浏览器原生首次权限不移除；供应商/费用/原音频不落盘与不自动Query的告知留在title和输入框下方。录音高亮、再次点击停止，连接可取消、收尾时锁定发送，错误可见。不扩大到自动录音或生成任务。

## D-008｜火山新版API Key实时ASR（2026-11-24）

用户最终选择火山引擎并添加VOICE_PROVIDER/VOLC_ASR_API_KEY/VOLC_ASR_RESOURCE_ID/VOICE_ENABLED，D-007的Deepgram供应商选择已被本决策取代，保留兼容但不自动切换。T-026用Pipecat WebSocket运输+自定义火山ASR FrameProcessor；官方固定bigmodel_async双向流式，200ms PCM16/16k mono，X-Api-Key和匹配资源ID，公共DNS固定IP/Host/TLS SNI、无环境代理与重定向。全量文字覆盖而非追加避免重复，停止录音后等待最终包，麦克风立即释放但输入/发送仍锁定至收尾。原音频与Key不落盘日志，权限/时限/并发/限额保留。真实短录音由用户选择同意并说话，不自动采集私人音频。

## D-007｜语音继续使用Deepgram实时转写（2026-11-24）

T-025核实DeepSeek官方ASR指南 https://api-docs.deepseek.com/guides/asr/ ：一次上传完整录音，明确不支持流式识别。用户在明确权衡后选择“保留实时转写：Deepgram + DeepSeek”，不接受停止录音后再转文字作为替代。因此T-025由T-021既有Pipecat + Deepgram STT方案替代；应用生成仍使用用户DeepSeek配置。不实施DeepSeek批量ASR、不做分段上传伪实时、无本轮代码改动或新部署；真实语音仍需Deepgram凭证和麦克风验收。

## D-004｜Railway先发布Mock阶段HTTPS入口（2026-11-24）

T-015替代T-013本轮完整生产部署目标。用户明确要求暂不处理真实登录，目前处于Mock阶段，只验部署成功和外网HTTPS可访问。使用Railway自带域名，APP_ENV为development且Mock明确标识；不改production禁Mock规则，不将演示称为真实身份/模型验收。不要求两套wildcard来阻挡平台页面上线，但生成应用独立预览和发布仍未公网验收。真实Key与敏感信息不得输入公开共享测试账号。本轮不扩展为真实认证、付费套餐或安全策略降级。

## D-005｜访客浏览与语音输入增量（2026-11-24）

T-019允许无登录态展示公共工作台及输入需求；只在提交Query时要求登录，保留待提交文本，登录后恢复但不自动执行计费请求。私有项目与配置API仍鉴权；登录后模型门禁保留。T-020优先DeepSeek官方接口适配，本轮不测试真实Key或发起真实模型调用。T-021为用户确认的语音输入实时转文字，不是语音播报；Pipecat STT凭证稍后由用户配置，文本确认后手动发送，不自动提交Query。

## D-006｜Mock专用opaque-origin沙箱（2026-11-24）

T-022：用户明确选择Mock专用沙箱预览。只对标识为Mock的fixture使用iframe srcdoc + sandbox allow-scripts/allow-forms（初版设想，现采用下文D-006实施补充），不授予allow-same-origin；平台父组件提供有白名单和限额的应用数据桥，按账号/项目/预览或公开表面分区保存在当前浏览器。数据写入确认后才显示成功，不向子页面传会话/Key/平台API能力。消息校验event.source、随机通道、类型与数据结构；真实模型产物保持独立Application安全源设计，不套用此Mock例外。Mock分享可用平台HTML包装壳，无平台身份能力；独立预览需owner登录，公开分享只在发布指针有效时可达。保存代码/项目/任务在PostgreSQL，预览内业务数据明确为当前浏览器，不承诺跨端同步。

目前没有关键方向决策。（初始化时的历史占位，现已有下列决策。）

## D-006实施补充｜专用frame URL而非srcdoc（2026-11-24）

实测srcdoc继承父页面CSP无法执行fixture内联脚本。最终改用受保护frame资源URL，响应与iframe同时强制sandbox allow-scripts allow-forms、无allow-same-origin；frame专用CSP禁止connect/frame/form导航，父页面仍不执行产物。按规范化后的可信fixture精确匹配，不放宽任意生成HTML。真实浏览器访问child document返回SecurityError，保存桥需要ACK后才应用状态。Mock-only后台通过Platform lifecycle运行，无需新建独立Railway Worker；真实模型拓扑不变。关联T-022。

## D-001｜基础框架而非完整P0（2026-11-23）

T-001/T-002：本轮交付React+FastAPI+PostgreSQL基础框架，一个App服务托管静态React及API，独立Postgres。只实现认证、模型连接测试门禁、项目/消息持久化；生成、独立源预览和实际发布不做假能力，后续T-005接入。前后端源码仍分目录。

## D-002｜Google登录纳入本轮（2026-11-23）

T-006：用户当前要求覆盖原需求中OAuth为P1的取舍，新增Google OAuth授权码登录，保留邮箱OTP。Google用户按sub稳定关联，不自动按相同邮箱合并已有账号；回调成功仍需模型测试配置。缺OAuth Client凭证时入口禁用，真实联调标阻塞。此变更不回写原需求云文档。

## 2026-11-23｜基础版本边界（T-001 / T-002 / T-005）

- 以用户要求的基础框架为本轮目标，不把完整P0当本轮已实现交付。
- React+TypeScript+Vite；Python3.11+FastAPI；PostgreSQL+SQLAlchemy+Alembic。
- Railway使用App容器托管React静态资源与API，加独立Postgres；先减少部署服务数，源码仍前后端分层。
- 用户模型Key仅浏览器内存或明确选择的账号本地存储，真实测试需要可用Key与供应商CORS，不启用平台代理或假成功。
- 邮件开发适配只写本地随机OTP；生产禁止file模式，SMTP或明确disabled。未提供SMTP不宣称真实邮件验收通过。
- AI任务、构建、隔离预览和发布执行列为后续增量；无生成产物时不提供假公开链接。
- 本轮没有实际Railway登录/Project/云服务创建、GitHub推送或Docker实测。

## D-003｜V1.2与用户授权Mock（2026-11-24）

T-005/T-007/T-008：D-001基础范围与旧浏览器Key方案已由当前指令和最新版需求V1.2 revision156取代。服务器受保护配置接口测试、AESGCM密文保存、独立PostgreSQL后台Worker执行；浏览器只恢复状态。用户授权登录和人工配置卡点使用显式开发Mock，不再暂停等待真实凭证。Google生产实现保留，Mock不是Google授权验收。

平台、Worker、隔离预览及公开应用分服务；每项目独立子域名隔离存储。开发localhost可运行，真实HTTPS wildcard DNS/TLS和Railway账户仍必须上线配置。Mock模式、开发密钥文件及测试数据严禁进入生产，实际供应商/KMS/公网验收不能由Mock替代。

任务板fixture和作品集fixture作为公开标记的Mock产物，真正模型路径不使用它们作为兜底。API返回模型错误而不偷偷切Mock。普通退出不删除服务端凭证、不取消接受任务；专门删除立即禁用并停止后续执行。

