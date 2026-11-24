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

- 状态：阻塞
- 阶段：认证
- 优先级：P0
- 验收条件：真实Google OAuth授权码流程、state/nonce与ID token校验，生产安全回调，稳定Google用户映射，缺凭证明确禁用；真实Google联调状态如实记录
- 依赖：无
- 替代关系：无
- 执行证据：docs/GOOGLE_LOGIN.md; backend/tests/test_google.py; backend/alembic/versions/3e6794627349_google_oauth_identities_and_challenges.py
- 变更说明：2026-11-23：Google OAuth代码与迁移自测通过，但缺真实Client ID/Secret，无法真实授权联调
- 最后更新：2026-11-23

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

## T-012 | 依据避坑指南核查Railway部署并安全推送GitHub

- 状态：进行中
- 阶段：部署
- 优先级：P0
- 验收条件：完整读取指南红线，检查部署与Mock/凭证泄漏，确定仓库和分支，仅推送必要源码并回读commit证据，不执行Railway部署
- 依赖：无
- 替代关系：无
- 执行证据：待补充
- 变更说明：首次登记
- 最后更新：2026-11-24

<!-- 待办由守门器追加到此处 -->
