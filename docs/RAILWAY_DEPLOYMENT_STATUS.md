# Railway Mock 阶段部署记录

## 最终回读补充

收尾文档提交f76ad55969b102344f7906f7977a6754070a5542已回读；固定ZIP113份文件与当时本地一致。Railway自动部署该提交后Active、Deployment successful；再次Mock登录，配置恢复且没有模型弹窗，原项目、全部消息、构建2、失败历史及发布仍在。私有预览已完成任务和匿名公开分享任务数据均保留，health仍ok。本段为重部署后追加的本地验收记录，远端f76ad5保留重部署前冻结证据，不为补充描述再次触发部署。

## 最新部署与公网验收（2026-11-24）

- GitHub源码：e2246a914fede5f3ffc9a45c9fe43bee19ee569a；固定commit ZIP 113份文件与本地逐字节一致，无多余文件。公开commit：https://github.com/ruan-collabs/atoms-demo/commit/e2246a914fede5f3ffc9a45c9fe43bee19ee569a 。
- CI成功：https://github.com/ruan-collabs/atoms-demo/actions/runs/45339583822 ；Linux后端测试、前端测试/构建、Docker build均在同一verify工作流中，1条Action运行时弃用警告。
- Railway同一Platform服务已按GitHub新源码成功Active，启用DEV_MOCK_SANDBOX=true、DEV_INLINE_WORKER=true。保留development、两个Mock开关、Postgres引用、MAIL_MODE=disabled、精确PUBLIC_ORIGIN；无真实Key或STT凭证注入，无付费套餐变更。
- 公网health为ok、PostgreSQL迁移46670bfb6eb1；meta.mock_sandbox=true。语音status.enabled=false，明确等待VOICE_ENABLED与DEEPGRAM_API_KEY。
- 线上实测：退出后/dashboard仍公开可见；输入不跳登录，发送才跳/login；Mock Alice回工作台恢复完整Query但不自动生成；Mock检查保存不再报缺主密钥；提交后由Mock-only后台规划生成并保存构建1。
- 公网沙箱实测新增、编辑、完成，刷新后标题与完成统计保留；访问iframe.document为SecurityError。提交紫色迭代保存构建2，旧任务与完成状态保留；发布得到稳定/mock-apps分享路径。显式[ mock:fail ]失败后构建2和既有任务仍在。
- 分享与预览初始任务数据独立；公开分享新增任务后刷新保留；退出登录后公开分享仍加载。独立web_fetch未携账号读取公开build成功，number=2、mock=true，含紫色主题。

演示入口：https://atoms-demo-production-57bed089.up.railway.app/dev-test 。访客工作台：https://atoms-demo-production-57bed089.up.railway.app/dashboard 。实际验收分享：https://atoms-demo-production-57bed089.up.railway.app/mock-apps/1eddadf0-080c-47d3-8cf3-7ea3a951991d 。

平台项目/消息/任务/构建/发布存在PostgreSQL；沙箱内部任务数据只保存在当前浏览器，不承诺跨端同步。浏览器执行器对HTTPS跨进程iframe的ref坐标定位报offscreen，表单交互用针对该child的CDP DOM回退实测，未放宽sandbox/CSP或伪造保存状态。

仍未验：手机流量与无痕GUI、真实认证、真实DeepSeek、真实语音/KMS/生产独立域。容器重部署后的Mock配置、项目、消息、构建、发布及浏览器任务恢复已在上述最终补充中验证。下文保留旧部署历史，不能作为当前线上状态。当前只完成用户授权的Mock阶段。

## 前期本地修复与旧部署历史

线上Mock配置已实际复现“加密密钥不可用，操作已拒绝”。本地代码已将Mock改为无需主密钥的非秘密fixture标记，并完成访客浏览/Query登录恢复、DeepSeek官方接口契约、Pipecat STT实时转文字接入。最新89后端/16前端测试及构建通过，本地浏览器生成交互、刷新恢复、迭代与实际发布通过。详情见INCREMENTAL_ACCEPTANCE.md。

用户已选择Mock专用沙箱。代码新增Mock沙箱与Mock-only后台执行选项，准备同步GitHub并启用DEV_MOCK_SANDBOX/DEV_INLINE_WORKER；部署完成前仍不能宣称旧线上版本已修复。真实语音凭证待配置，真实DeepSeek本轮不调用。

## 当前结论

已完成用户要求的 Mock 阶段 HTTPS 演示入口部署。此结果只证明平台页面公网可访问、PostgreSQL 连通和迁移已应用；不代表真实身份、模型生成、独立源预览或公开发布闭环通过。



* 推荐 Mock 演示入口：[https://atoms-demo-production-57bed089.up.railway.app/dev-test](https://atoms-demo-production-57bed089.up.railway.app/dev-test)

* 平台首页：[https://atoms-demo-production-57bed089.up.railway.app/](https://atoms-demo-production-57bed089.up.railway.app/)

* 健康检查：[https://atoms-demo-production-57bed089.up.railway.app/api/health](https://atoms-demo-production-57bed089.up.railway.app/api/health)

* 运行标识：[https://atoms-demo-production-57bed089.up.railway.app/api/meta](https://atoms-demo-production-57bed089.up.railway.app/api/meta)

* Railway 项目：[https://railway.com/project/0df6d4d5-c36e-4762-8817-a853fe4298e2](https://railway.com/project/0df6d4d5-c36e-4762-8817-a853fe4298e2)

* GitHub 源码：ruan-collabs/atoms-demo，main，源提交 8443a5e0233af7c60d0ccdd95b2133c49d407c3b。应用源码未修改。

## 部署与实际验证

Railway 服务 atoms-demo 当前 Active、Deployment successful。Deploy 日志确认 Uvicorn 在 0.0.0.0:8080 启动，HTTPS 域映射 8080 端口。Postgres 与 postgres-volume 已存在，无本机数据库导入。

Platform 设置通过 Railway 界面应用：Start Command=python run.py；Pre Deploy Command=alembic upgrade head；Healthcheck Path=/api/health。

实际变量：APP\_ENV=development；DATABASE\_URL 引用 Postgres.DATABASE\_URL；DEV\_MOCK\_AUTH=true；DEV\_MOCK\_MODEL=true；MAIL\_MODE=disabled；PUBLIC\_ORIGIN=[https://atoms-demo-production-57bed089.up.railway.app](https://atoms-demo-production-57bed089.up.railway.app)。Railway 环境名称仍为 production，但应用实际运行模式是用户明确授权的 development Mock，不是生产验收。



* 浏览器真实 HTTPS 打开首页，React 页面渲染，默认跳转 /login；真实 Google / 邮件入口未配置。

* /dev-test 正常显示明确 Mock 标签、固定 Alice/Bob 测试账号和非真实身份说明。

* 独立无账号 / 无 cookie HTTPS 请求：首页、/dev-test、JS 与 CSS 资源均 HTTP200。

* /api/health HTTP200：status=ok、database=postgresql、migration=46670bfb6eb1、version=0.2.0。

* /api/meta 确认 mock\_auth=true、mock\_model=true、google\_login=false、mail\_mode=disabled。

* 独立 web\_fetch 读取 /dev-test 成功，确认不依赖 Railway 登录会话。

未代替用户验证手机流量访问；未做无痕 GUI 窗口操作。未运行登录、用户模型配置、生成、持久化项目业务及容器重启验收。

## 明确未做与使用警告

Worker 和 Application 服务尚未创建，未配置独立预览 / 发布通配域 TLS，也未配置平台稳定加密主密钥，因此不能据 Mock 开关开启宣称生成配置 / 后台执行 / 预览发布可用。本轮只验用户指定的 HTTPS 部署和页面访问。

公开 Mock 测试账号是共享演示身份；不要输入真实 API Key、个人信息或敏感需求。真实认证、稳定独立 APP\_SECRET/CREDENTIAL\_MASTER\_KEY、Cookie 生产策略及 Secret 权限备份治理仍须在生产切换时落实，禁止将当前演示当正式服务。

代码 production 禁 Mock 规则未修改；未升级套餐或填写支付信息。平台与 Postgres 正在运行，会消耗 Railway 试用额度，额度耗尽 / 试用结束可能停机。

## 历史与配置差异

之前完整生产部署目标 T-013 由用户当前 Mock 阶段要求 T-015 替代。首次默认无变量部署曾停止，旧临时域名撤下；现在已应用新 Mock 配置并生成上述新域名，不使用旧域名。

Railway 当前新服务设置页声明旧 Config-as-code 不可启用；仓库 railway\*.json 没有自动应用，已用 UI 等价设置迁移启动健康检查。完整生产 Worker/Application 配置仍需后续单独验证。

关联待办：T-014、T-015。部署记录和项目账本仅本地更新，当前 GitHub 未追加这些收尾文档。