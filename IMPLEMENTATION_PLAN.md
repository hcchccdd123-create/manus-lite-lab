# IMPLEMENTATION_PLAN.md

## 1. 当前目标
在现有基线上持续稳定：
- 会话隔离流式对话
- Think 独立展示
- 草稿态 + 延迟入历史
- 可部署到 OpenCloudOS

## 2. 分阶段执行（状态）

### Phase 0 - 基线可运行（已完成）
输入：项目目录与初始脚手架。
输出：前后端本地启动成功。
DoD：
- 后端 `uvicorn` 可启动
- 前端 `vite` 可启动
- `GET /api/v1/health` 可用

### Phase 1 - 后端聊天闭环（已完成）
输入：FastAPI + SQLite。
输出：会话、消息、非流/流式聊天闭环。
DoD：
- 会话 CRUD 可用
- `/chat` 与 `/chat/stream` 可用
- 消息持久化可回放

### Phase 2 - 前端基础会话体验（已完成）
输入：Vue3 + Pinia。
输出：会话列表、消息区、输入发送。
DoD：
- 可发起会话聊天
- 流式消息可实时渲染
- 左栏 loading 与会话状态同步

### Phase 3 - Think 与持久化（已完成）
输入：SSE 多事件流。
输出：ThinkPanel/Modal + IndexedDB 持久化。
DoD：
- `message.thinking` 可实时展示
- think 可折叠与放大
- 刷新后会话/消息/think 可恢复

### Phase 4 - 草稿态与历史展示规则（已完成）
输入：现有会话交互。
输出：更接近 Manus 风格的会话创建行为。
DoD：
- 刷新默认草稿态
- `+ New` 不立即创建历史项
- 首发后 pending 会话仅在首条流内容到达时 reveal
- 标题取首问前 20 字

### Phase 5 - 稳定性与部署（进行中）
输入：本地可用版本。
输出：OpenCloudOS 可持续部署版本。
DoD：
- 部署脚本可执行
- systemd 服务可运行
- 生产环境变量模板完整

## 3. 联调执行清单
1. 启动后端：`cd llm-python && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. 启动前端：`cd web-vue3-vite && npm run dev`
3. 验证 `GET /api/v1/health`
4. 草稿态发送首问，确认“首条流内容后才入左栏”
5. 并发测试：A 流式中切到 B 并发发送
6. 验证删除流程：hover 删除 -> 弹窗确认 -> 列表与本地数据同步

## 4. 测试矩阵

### 单元测试
- SSE 解析（LF/CRLF 边界）
- think 解析状态机
- pending/reveal 状态机

### 集成测试
- 会话创建与消息落库
- 流式事件顺序
- 摘要触发与快照写入
- provider 错误映射

### 手工冒烟
- 草稿态居中输入
- 并发会话不串流
- Think 展示与折叠
- 刷新恢复与删除回退

## 5. 回归清单
- 草稿态入口（刷新 + New）
- 左栏 loading 与流状态一致
- 首条流内容 reveal 规则
- 删除弹窗视觉统一与行为正确
- IndexedDB 数据一致性

## 6. OpenCloudOS 部署步骤（后端）
1. 上传代码到目标目录（示例：`/opt/manus-lite-chat/app`）
2. 创建并激活虚拟环境（示例：`/opt/manus-lite-chat/venv`）
3. 安装依赖并配置 `.env`
4. 执行部署脚本：`scripts/deploy_opencloudos_backend.sh`
5. 用 systemd 管理服务并验证健康检查

## 7. 关键环境变量
- `DB_URL`
- `DEFAULT_PROVIDER`
- `DEFAULT_MODEL_OLLAMA`
- `OLLAMA_BASE_URL`
- `GLM_API_KEY` / `GLM_BASE_URL`
- `CODEX_API_KEY` / `CODEX_BASE_URL`
- `MEMORY_WINDOW_SIZE`
- `SUMMARY_TRIGGER_MESSAGES`
- `ENABLE_PROVIDER_FALLBACK`

## 8. 下一轮建议
1. 增加前端 e2e（Playwright）覆盖 pending/reveal 与并发流式。
2. 增加流式断开重试策略（可配置次数与退避）。
3. 对 `provider_call_logs` 增加前端可观测页面（调试态）。

---
Last updated from codebase on 2026-03-05
