# 项目状态

- 项目名称：Atoms
- 项目目标：建立 React + Python + PostgreSQL 的 Railway 可部署基础框架，支持后续增量迭代
- 当前阶段：代码已推送公开GitHub，CI含Docker镜像build通过；真实Railway上线未完成
- 当前焦点：无
- 阻塞事项：真实Google/SMTP/模型凭证、KMS权限与备份治理、Railway账号/DNS通配域/TLS；逐token流式未实现
- 下一步：在Railway按docs/PREDEPLOY_CHECKLIST.md配置角色和生产Secrets，关闭Mock，完成公网真实验收
- 最后更新：2026-11-24

## 当前摘要

V1.2服务端加密配置、独立PostgreSQL Worker、生成/迭代/取消恢复、隔离预览及本地公开发布更新已实现。本轮公开GitHub ruan-collabs/atoms-demo main已推送，首次94份源码下载校验一致，CI成功含Docker镜像build；代码交付见docs/GITHUB_DELIVERY.md。实际浏览器Mock闭环证据仅本地保留；本轮回归70后端/11前端通过。真实身份与模型、生产KMS和Railway公网、镜像run、逐token流式仍未验收，不标生产AC全通过。

## 项目扩展字段

- 项目类型：React TypeScript + FastAPI Python + PostgreSQL，Railway单App加数据库
- 验证方式：scripts/test.sh；docs/*test-results.xml；docs/SELF_TEST.md
