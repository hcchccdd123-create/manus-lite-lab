# IMPLEMENTATION_PLAN.md

## 1. 当前目标
在现有基线上持续稳定：
- 会话隔离流式对话
- Think 独立展示
- 草稿态 + 延迟入历史
- 可部署到 OpenCloudOS
- 具备可扩展的 Agent Runtime（Reasoning Loop + Tools）

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
- 删除按钮在 `conversation-item` hover 时可见

### Phase 3 - Think 与持久化（已完成）
输入：SSE 多事件流。
输出：ThinkPanel（缩略 + 居中放大）+ IndexedDB 持久化。
DoD：
- `message.thinking` 可实时展示
- think 可缩略展示与放大查看
- 刷新后会话/消息/think 可恢复
- message-scroll 自动滚底 + 手动接管 + 一键恢复可用

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
- 默认 Provider 切换为 GLM（`glm-4.7`）
- 输入区支持 Deep Thinking 开关并透传 `enable_thinking`
- Think 缩略浮层（`70x70`）与居中放大交互稳定（含 Genie 风格开合动画）
- 全局业务滚动条样式统一且不污染第三方组件

### Phase 6 - Agent Runtime 基础闭环（规划中）
输入：现有聊天流与 provider 抽象。
输出：支持模型在一次会话中进行多步推理与工具调用。
DoD：
- 新增 Agent Loop 执行器，支持 `thinking -> tool_call -> tool_result -> ... -> final_answer`
- 每轮推理具备统一步号（`step_no`）与最大步数限制（`max_steps`）
- 工具调用支持最小可用工具集（如 `web_search`、`calculator`、`fetch_url`）及统一超时/错误处理
- Tool Result 注入上下文后自动继续下一轮推理
- 超过最大步数时返回标准化终止结果（含终止原因）
- SSE 新增可观测事件：`agent.step`、`agent.tool_call`、`agent.tool_result`、`agent.final`

### Phase 7 - 前端 Agent 可视化与调试体验（规划中）
输入：Agent Runtime 后端闭环。
输出：前端可理解并展示 Agent 执行过程。
DoD：
- 消息区支持 Agent 步骤流展示（thinking/tool_call/tool_result/final_answer）
- Tool Call 卡片展示工具名、参数、耗时、状态（success/error/timeout）
- Agent 推理中支持“进行中”状态提示与结束态汇总
- 在不破坏原有 Chat 体验的前提下，支持隐藏/展开 Agent 细节
- IndexedDB 增加 Agent 事件持久化，刷新后可回放

## 3. 联调执行清单
1. 启动后端：`cd llm-python && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. 启动前端：`cd web-vue3-vite && npm run dev`
3. 验证 `GET /api/v1/health`
4. 草稿态发送首问，确认“首条流内容后才入左栏”
5. 并发测试：A 流式中切到 B 并发发送
6. 验证删除流程：hover 删除 -> 弹窗确认 -> 列表与本地数据同步
7. Agent 用例：同一问题触发至少 1 次工具调用并返回 `final_answer`
8. Agent 异常用例：工具超时/参数错误时，循环可恢复或标准化终止

## 4. 测试矩阵

### 单元测试
- SSE 解析（LF/CRLF 边界）
- think 解析状态机
- pending/reveal 状态机
- Agent loop 状态机（步进、终止、异常分支）
- 工具参数校验与错误映射

### 集成测试
- 会话创建与消息落库
- 流式事件顺序
- 摘要触发与快照写入
- provider 错误映射
- Agent 工具调用链路（tool_call -> tool_result -> final_answer）
- 达到最大步数时终止行为与返回结构

### 手工冒烟
- 草稿态居中输入
- 并发会话不串流
- Think 缩略展示与居中放大
- 刷新恢复与删除回退
- 删除按钮在整条 `conversation-item` hover 时可见
- Think 缩略模块不遮挡输入框/发送按钮
- 消息区底部留白在 100% / 125% / 150% 缩放下可读
- message-scroll 手动上滚后显示恢复按钮，点击后滚底并恢复自动滚动
- Deep Thinking 开关状态变化后，stream payload `enable_thinking` 同步
- 移动端输入框左侧 Think 入口可用
- 滚动条 hover/active 反馈与跨浏览器一致性
- Agent 推理步骤 UI 与实际事件顺序一致
- tool_call 卡片参数展示正确，tool_result 可回看
- Agent 终止原因（final/step_limit/error）可读

## 5. 回归清单
- 草稿态入口（刷新 + New）
- 左栏 loading 与流状态一致
- 首条流内容 reveal 规则
- 删除弹窗视觉统一与行为正确
- IndexedDB 数据一致性
- 默认新会话 provider/model 为 `glm` / `glm-4.7`
- 缩略 Think 定位：`top:-50px; left:30px`
- 缩略 Think 外透明区不拦截 pointer 事件
- `message-scroll` `padding-bottom: 80px` 生效
- `message-scroll` 自动滚底暂停/恢复逻辑正确
- 业务滚动条蓝色细条 + hover 加亮；第三方组件不被污染
- Agent 事件持久化后刷新回放正确
- 工具异常不会导致整个会话崩溃

## 6. OpenCloudOS 部署步骤（后端）
1. 上传代码到目标目录（示例：`/opt/manus-lite-chat/app`）
2. 创建并激活虚拟环境（示例：`/opt/manus-lite-chat/venv`）
3. 安装依赖并配置 `.env`
4. 执行部署脚本：`scripts/deploy_opencloudos_backend.sh`
5. 用 systemd 管理服务并验证健康检查

## 7. 关键环境变量
- `DB_URL`
- `DEFAULT_PROVIDER`
- `GLM_MODEL`
- `DEFAULT_MODEL_OLLAMA`
- `OLLAMA_BASE_URL`
- `GLM_API_KEY` / `GLM_BASE_URL`
- `CODEX_API_KEY` / `CODEX_BASE_URL`
- `MEMORY_WINDOW_SIZE`
- `SUMMARY_TRIGGER_MESSAGES`
- `ENABLE_PROVIDER_FALLBACK`
- `AGENT_ENABLED`
- `AGENT_MAX_STEPS`
- `AGENT_STEP_TIMEOUT_MS`
- `TOOL_DEFAULT_TIMEOUT_MS`

## 8. 下一轮建议
1. 增加前端 e2e（Playwright）覆盖 Agent 可视化与工具调用链路。
2. 为 Agent Runtime 增加工具沙箱与权限白名单（按环境配置）。
3. 对 `provider_call_logs` + Agent step logs 增加可观测页面（调试态）。

---
Last updated from codebase on 2026-03-06
