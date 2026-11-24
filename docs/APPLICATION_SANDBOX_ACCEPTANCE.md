# Railway 同域入口安全沙箱增量（T-031 / T-032）

## 范围与方向

用户确认使用Railway自带域名、不同path作为包装入口，不配置自有wildcard。path不提供隔离；实际生成HTML运行在opaque iframe：父组件及响应CSP均sandbox allow-scripts allow-forms，无allow-same-origin、connect/frame/navigation能力。

生成应用使用固定异步atomsStorage契约，只能访问atoms-app:data:v1的JSON对象/数组，200KB、节点/深度/次数受限。父端验证source、null origin、随机通道、buildId；存储按owner/project/preview-public分区，浏览器localStorage写成功ACK后应用才更新UI。不会传平台API、cookie、CSRF或模型Key。生成应用无云同步承诺。

## 已上线基础

- 核心交互提交8e2fe3e及Worker消费隔离修复4b06b85，固定ZIP126份源码与本地一致；CI45397118750与45399504381成功。
- Railway平台更新成功、health migration=a7c932e108df；新增独立atoms-worker，无公网端口，启动python -m app.worker。
- Worker引用Postgres与平台APP_SECRET/CREDENTIAL_MASTER_KEY/PUBLIC_ORIGIN，不读取秘密值；所有Mock开关关闭，模型任务用用户密文解密。旧version0 queued未消费，线上原项目显示旧需求待确认、执行器可用。
- APPLICATION_SANDBOX=true在Platform/Worker均已应用并部署fed3c1b，固定133份源码一致，CI45405333555成功。Mock路径继续严格fixture，未更改。

## 本地验证

完整后端117项、前端27项、build通过；最后真实沙箱7项及build通过。测试包括CSP无same-origin、经典脚本/async存储契约、owner404、未发布公开404、公开版本指针、Mock拒真实沙箱。

本地专用测试项目aa51725b-6feb-4f9a-9ab6-ec0eae52f88f安装明确test_fixture，只验证运输与数据桥，不作为模型生成结果。实际浏览器新增sandbox-test-note、刷新保留；父访问iframe.document返回SecurityError且sandbox属性只有allow-scripts allow-forms。

## 真实模型联调进展

线上新验收项目03d682c4-fdcd-490f-8fb4-6b69c98eb154，使用用户真实Google会话和已配置deepseek-flash。

1. 首次在resolve_target前失败“服务目标未加入允许名单”，未保存构建。Worker引用平台未显式配置的MODEL_ALLOWED_ORIGINS解析为空；修正为平台已采用官方OpenAI/DeepSeek HTTPS允许名单，不关闭出站校验。
2. 配置部署完成后一次明确重试，真实返回规划与流式代码（UI已接收4.2KB），但凭证通用模式误匹配task-类名的sk-子串，拦截保存，没有应用版本。未自动循环调用模型。
3. 修正为独立token边界sk-/Bearer模式，真实Key精确跨chunk拦截仍保留；单一完整HTML从解释/代码围栏提取，不补造标签，不接受多个文档。46项核心后端回归通过。
4. cf05375已部署但流式holdback丢失前缀仍将task子串误判；3e3f96b保留32字符已发前缀并从tail起点检查，独立Key与跨chunk精确检测不放宽，8项流式测试通过。
5. 完整约9.6KB真实代码已取得，使用Promise.then保存成功再更新UI，await-only契约误判。c3e18b0接受等价异步写法；owner/配置版本/base-build/并发门禁下重新校验已有stream_text并保存，不再调用模型。重新校验已在线成功保存构建1，原失败历史不删除。

## 真实浏览器验收结果（2026-11-24）

- 真实项目输入需求、规划和流式代码来自deepseek-flash，不是Mock fixture。首成功构建1来自已有完整模型输出重新校验，无新增模型费用请求。
- 任务清单新增“真实DeepSeek沙箱验收”，勾选完成，整页刷新后记录及checked保留。
- 实际iframe.document读取返回SecurityError；sandbox为allow-scripts allow-forms，不含same-origin。这项只证明同源隔离，不能替代全部对抗测试。
- 发布构建1到稳定公开入口，访客初始空任务（不迁移私人数据）；添加“公开分享验收记录”，刷新保留。独立web_fetch无登录成功读取public元数据，number=1、mock=false、sandbox=true。
- 有限一次真实迭代改为紫色主题与“紫色日程清单”，自动生成并保存构建2。旧任务及完成状态保留；新增“迭代后新增测试”再删除，刷新确认该测试条目消失且原已完成任务仍在。
- 更新公开发布到构建2，原/apps URL不变，未发布更改提示消失；公开端刷新后标题更新、原公开记录保留。私人/公开两个数据分区不互混。
- health status=ok、Postgres、migration=a7c932e108df；Platform与Worker都Active且提交标题对应c3e18b0；Worker无公共HTTP入口。

公开验收应用：https://atoms-demo-production-57bed089.up.railway.app/apps/03d682c4-fdcd-490f-8fb4-6b69c98eb154

源码：https://github.com/ruan-collabs/atoms-demo/commit/c3e18b0ab7b1c8ca882a5ac206a0a971cae83b94

CI成功：https://github.com/ruan-collabs/atoms-demo/actions/runs/45410356880 （3e3f96b的45409046373与cf05375的45407668279也成功）。固定ZIP133份文件应用源码逐字节一致，PROJECT_STATE.md/TODO.md为本地新验收记录领先。最终122后端/27前端/build通过，Alembic check无漂移。测试供应商替身仍不是真实请求证据；真实请求依据上述在线操作。

## 未完成与限制

容器重部署后恢复、第二类不同真实应用、沙箱存储失败/对抗场景、无痕GUI/手机流量及真实音频interim/final完整事件仍待验。应用任务仅当前浏览器受限JSON持久化，项目、消息、密文配置、构建、发布在PostgreSQL；不承诺跨设备同步。APP_ENV保持development和明确Mock入口，不标完整production或45项全通过。不升级套餐、不清用户或云数据库、不旋转稳定密钥、不自动重跑原历史queued。
