# Railway 上线与公开仓库门禁

本清单用于项目安全、部署与交付检查。GitHub 推送成功不等于 Railway 公网部署完成。

## 固定交付红线（每次开发、推送、部署、提交前必查）

1. **链接真正可达**：正式提交须有稳定外网入口，实际无痕窗口与手机流量核验；[localhost](https://localhost)或临时隧道不能作为唯一交付。页面 HTTP200、Railway Online、镜像 build 都不能代替真实核心流程验收。

2. **仓库公开且无凭证**：public 仓库可未登录读取源码与 README。真实 API Key、密码、Token、Cookie、OTP、主加密密钥不得进入源码、Git 历史、前端、生成 HTML、普通日志或发布包；发现泄漏先撤销 / 轮换，再清理历史，不能只删文件。

3. **真实交互与持久化**：最终必须跑通 “输入需求 → AI 生成代码 / 应用 → 直接运行并可交互的 iframe 预览 → 保存并刷新 / 重开恢复”。纯聊天、固定笔记 / 待办 / 记账业务应用、只能看不能运行的代码 / 文字 / 图片、纯静态页面、无持久化、全假 PoC 不能当最终交付。

4. **避免跑题与堆半成品**：核心是应用生成器，不以全量复刻 Atoms 或搭复杂多智能体架构替代最小闭环。先稳定核心闭环，再做一个深的延展能力；优先级为外网可用、核心流程、持久化、亮点、额外功能。

5. **演示不是正式验收**：用户可以明确授权 Mock 阶段公开演示，但必须标识 Mock、共享账号及不可输入真实 Key / 敏感数据；不得将固定 fixture、预存结果或视频冒充现场 AI 生成。生产真实服务不得偷偷切 Mock 或绕过用户模型门禁。无 Key / 额度耗尽的兜底需显式提供，不能用兜底结果证明真实模型接通。

6. **状态只按证据标记**：没有实际执行证据保持待验收 / 阻塞；单测、构建、页面上线、Mock 闭环、真实生产闭环分别记录，不合并宣称全通过。

## 部署坑点与排查门禁



* 监听 0.0.0.0，读取平台 PORT；域名目标端口与运行端口匹配，EXPOSE 不是监听设置。遇到 502 先核端口 / 启动日志 / 健康检查，不只看部署成功状态。

* 数据库、上传文件、生成结果必须在持久化数据库或挂载 volume，不依赖容器临时层；验证刷新、重开和重部署 / 重启后的恢复，禁止用清库修部署。

* requirements.txt/package.json 与锁文件完整；依赖失败先核版本、下载源、网络和构建目录，只有必要时调整可信镜像源，不盲改或禁用安全校验。

* Secrets 通过运行环境或 Secret 管理注入；用户模型 Key 按受保护服务端配置、加密持久化方案处理，不硬编码。稳定主密钥不得随每次部署重生成。

* 检查实际生效的 Root Directory、Dockerfile、启动命令、迁移、健康路径、变量和角色。仓库配置文件存在不代表托管平台已采用；当前平台规则需实时核实。

* 平台自带 HTTPS 域可用于平台页面入口；生成应用安全源分离、每项目隔离及 DNS/TLS 属于独立验收，不能据一个平台域名宣称它们完成。

* 境外模型超时先核服务区域、供应商目标、DNS、出站连通与时限；需要更换供应商或代理时遵守允许名单，不关闭 SSRF/CSP/TLS 校验来兜底。

* GitHub 认证 / 网络失败先区分 OAuth、SSH 或 PAT 权限与连通问题，不使用账号密码代替 push 凭证，不把凭证写日志。远端领先先检查差异并保留历史，不强推覆盖用户改动。

* 上传前检查忽略清单和候选密钥模式并人工复核；排除.env、虚拟环境、node\_modules、缓存、数据库、密钥及大附件。单文件超过 100MB 不得直接提交；原始私密材料不公开。

* 提前部署稳定占位版并保留缓冲，后续增量更新；不把部署和 GitHub 上传拖到最后。

## 额度与最终交付要求



* 开发阶段先 Mock、本地调 prompt；Atoms 只用于有限体验 / 收尾演示，不当反复全量开发环境。控制上下文与输出大小；如做赛马，优先 2–3 路而非 5 路，不因此自动新增赛马功能。

* 无 Key / 断网 / 额度耗尽要有清晰错误与显式示例兜底；预存产物或视频仅作标明来源的备用，不能替代可用真实核心流程。

* 正式交付前检查 README 中的本地运行、技术栈、实现取舍、完成 / 未完成范围及后续优先级，提交材料须带正确在线链接和公开仓库地址；未授权不自动向外部提交文档写入。

* 最近实际部署和验收状态只维护在 RAILWAY\_DEPLOYMENT\_STATUS.md、SELF\_TEST.md、MOCK\_REGISTER.md，不把本清单的固定规则写成已通过结论。

## 已做源码检查



* Platform 和 Application 均监听 0.0.0.0，并读取 PORT；EXPOSE 8000 只是镜像元数据，不能取代运行时 PORT。

* 根 Dockerfile 多阶段编译前端并安装 backend/requirements.txt；前端 package-lock.json、后端 uv.lock 保留便于复现。

* 项目 / 消息 / 任务 / 构建 / 发布数据保存在 PostgreSQL，不依赖容器临时磁盘；本地 compose 数据库有 named volume。Railway 必须使用独立持久化 Postgres，不能上传本机数据库。

* .gitignore/.dockerignore 排除 .env、.runtime、虚拟环境、node\_modules、密钥文件、本地数据库、原始浏览器证据、构建缓存和大附件。

* 服务端用户 API Key 是应用运行时用户配置，不是写死到源码的环境密钥；在服务器认证加密保存。平台 APP\_SECRET、CREDENTIAL\_MASTER\_KEY、OAuth/SMTP 凭证只能用 Railway Secret / 环境变量注入，不放公开仓库。

## Railway 配置顺序



1. 从 GitHub ruan-collabs/atoms-demo 的 main 分支部署。所有服务 Root Directory 都为项目根，使用 Dockerfile，不直接启动 Vite 开发服务。

2. 新建并保留 PostgreSQL 持久化服务；注入实际 DATABASE\_URL。不要用 compose 的演示密码或本机 127.0.0.1 地址。

3. Platform/Worker/Application 分别采用 railway.json、railway.worker.json、railway.application.json 所描述的角色规则；实际平台不支持旧 config-as-code 时，在 UI 设置等价启动、迁移和健康规则并核实生效。Worker 不开放公共 HTTP 入口；仅 Platform 执行 preDeploy 迁移，迁移成功后再启动其他角色。

4. APP\_ENV=production；DEV\_MOCK\_AUTH=false；DEV\_MOCK\_MODEL=false；MAIL\_MODE=smtp 或 disabled，file 禁止。至少真实 Google OAuth 或 SMTP 一个认证路径可用；邮箱禁用时不要声称邮件可登录。

5. 注入独立随机 APP\_SECRET 和 32 随机字节 base64 的 CREDENTIAL\_MASTER\_KEY；平台与 Worker 保持稳定一致，不每次重部署重新生成，否则旧凭证无法解密。密钥管理访问隔离、轮换、备份治理须上线前落实。

6. 平台 PUBLIC\_ORIGIN 为精确 HTTPS Origin；PREVIEW\_ORIGIN 与 APP\_ORIGIN 为不同安全源，两套每项目 wildcard 域名和 TLS 指向 Application。Railway 默认单一服务域名不是通配域。未完成域名不要把预览 / 发布标已可用。

7. 明确保留 Provider HTTPS 目标允许名单、公共 DNS/IP 验证、禁止重定向和凭证泄漏。不因连通失败关闭 SSRF/CSP 或改成明文 Key。

## 上线红线



* 禁止把 .env、真实 API Key、主加密密钥、Cookie、OTP、数据库内容、非公开资料或原始自测截图 / DOM 上传公开仓库。

* 禁止把 Mock 生成产物当作真实 AI 结果。开发 Mock 保留用于本地演示，页面明确提示，生产启动拒绝开启。显式演示兜底不等于允许生产偷偷切 Mock 或绕过用户模型配置。

* 禁止用页面上线、单测或 Mock 闭环宣称真实供应商、完整生产链路和 45 条生产验收全部通过；最新逐项结果以 RAILWAY\_DEPLOYMENT\_STATUS.md 和 SELF\_TEST.md 为准。

* 禁止临时隧道或[localhost](https://localhost)成为唯一提交访问链接。不得执行清库、删除生产数据、改写已应用迁移、强推远端覆盖用户历史来 “修部署”。

* 禁止把真实 Key 写入前端、生成的 HTML、普通日志或 Git 历史；意外泄漏先撤销 / 轮换供应商 Key，再清理历史，不靠删文件掩盖。

## 部署后才能打勾的项目



* [x] GitHub 公开仓库已由独立网页读取验证可访问，完整 README 与 94 份源码下载校验一致。

* [x] GitHub CI 镜像实际 build 成功；后端 / 前端单测与前端 build 通过。

* [ ] Platform/Worker/Application 在 Railway 实际启动及健康检查通过；镜像 run / 公网链路仍待验收。

* [ ] 无痕窗口打开真实 HTTPS 平台及生成应用；再由用户以手机流量访问一次，排除缓存与内网假象。

* [ ] 真用户登录 → 真 Key 服务器测试 / 加密保存 → 真 AI 生成 → iframe 可操作 → 迭代 → 刷新 / 重开恢复 → 发布 / 更新。

* [ ] 容器重启 / 重部署后项目、消息、加密配置与构建仍在；没有容器临时层数据丢失。

* [ ] 关闭浏览器后台任务继续；取消 / 删除 Key 阻止后续调用；已发生费用不作退费承诺。

本清单为持续执行规则，不授予任何外部写入或部署权限。每轮操作遵守用户当前明确范围；Mock 演示与真实生产分别验收，最新范围和结果见项目状态与部署记录。