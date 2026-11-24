# V1.2架构与执行边界

React→平台FastAPI→PostgreSQL，浏览器不直连模型、不保存Key。
配置Key仅在受保护POST测试短暂存在→AESGCM测试草稿15分钟→用户明确保存后启用密文。所有业务按user/config/project owner和配置版本硬门禁；主密钥来自独立环境Secret或仅开发文件，AAD绑定owner/config/version。

PostgreSQL持久任务队列→独立Worker FOR UPDATE SKIP LOCKED认领→锁定config版本→按需解密→规划/生成/一次修复→HTML/Node--check校验→不可变BuildArtifact→事务切currentBuildId。Worker token/租约、取消和凭证删除检查防晚回包；未知上游结果失败/中断，不自动重发可能计费请求。普通退出/导航只断页面轮询，不停任务。

成功预览由app.application_server在p-project.preview-origin运行；公开由a-project.application-origin运行。不同project/preview/public独立Origin及storage，平台session host-only。iframe允许script/same-origin/forms，不允许弹窗/顶层导航，CSP connect-src none。消息严格检查source/origin，只接收ready/error，不收凭证。JS仅浏览器执行，Node在服务器只做语法解析。

发布任务持久化→检查保存构建SHA256→实际HTTP读取隔离预览与公开候选，响应X-Artifact-SHA256核对→成功才切publishedBuildId及稳定URL。失败保留旧指针；晚发布job_key不匹配不可覆盖。

API：认证/Google；dev/mock-login仅开发；model-config GET/test/save/delete；projects创建/搜索/筛选/重命名；snapshot完整消息/任务/构建；generate/stop/retry/retry-save；build/preview-link/publication/publish。

数据库持久平台数据；生成业务数据仅浏览器本地。Chrome iframe存储分区和top-level storage可能不同，不能作为同步承诺。构建号变化不改storage key，发布不搬运预览数据。

生产治理未完成：Google/SMTP真实联调、真实供应商测试、独立KMS最小身份/审计/轮换/删除恢复/备份策略、Railway域/TLS/数据库备份、Docker镜像实测。阶段轮询不是逐token流式。实际状态见SELF_TEST.md、MOCK_REGISTER.md。
