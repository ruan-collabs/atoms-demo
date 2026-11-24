# GitHub 代码交付记录

- 仓库：https://github.com/ruan-collabs/atoms-demo ，公开，main。
- 首次完整源码提交：https://github.com/ruan-collabs/atoms-demo/commit/951819e07f685286a2da4d73546da18e73591b7c 。
- 远端源码ZIP下载后，对照脱敏清单逐文件SHA256一致：94文件，无缺失/多余。其后仅同步本交付记录及账本状态。
- 本轮本地回归：70项后端、11项前端通过，前端生产构建通过。
- GitHub CI：https://github.com/ruan-collabs/atoms-demo/actions/runs/45317051622 ，成功；包含后端集成测试、前端测试和生产build、Docker镜像build。1条Action运行时Node弃用警告，不影响本次成功；未做镜像run或Railway上线。

## 避坑与红线处理
- 补全.gitignore/.dockerignore；上传按显式未忽略文件清单，排除.env、.runtime、密钥、数据库、依赖目录、构建缓存、原始浏览器证据、生成附件和私密招聘文档。移除README私密需求链接。
- 上传文件全部为文本，单文件远低于100MB；保留依赖清单和锁文件。
- 检查provider/GitHub token/私钥模式未发现强候选；敏感字段仅开发示例/单测常量。此扫描不是绝对无泄漏证明，生产仍需安全审查。
- PORT动态读取、0.0.0.0监听、PostgreSQL持久化、应用安全源分离和生产拒绝Mock逻辑保留。
- 指南的Mock兜底建议仅用于明确本地演示，不覆盖真实上线禁用Mock或用户Key门禁；不把固定fixture当真实AI结果。

## Railway 仍需配置
生产Secret、真实Google或SMTP、用户模型服务、Platform/Worker/Application/PostgreSQL角色、两套应用通配DNS/TLS及KMS权限/轮换/备份治理。详见RAILWAY.md、PREDEPLOY_CHECKLIST.md、MOCK_REGISTER.md。

当前已完成代码推送与镜像build，不代表线上Demo可用。部署后需无痕与手机流量访问、真实闭环、重启持久化、后台任务及权限验证。
