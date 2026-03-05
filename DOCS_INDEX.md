# DOCS_INDEX.md

这个索引用于快速定位 `manus-lite-lab` 的规范文档，帮助你或协作 AI 在不同阶段直达正确文档。

## 快速导航

1. [PRD.md](./PRD.md)
2. [APP_FLOW.md](./APP_FLOW.md)
3. [TECH_STACK.md](./TECH_STACK.md)
4. [FRONTEND_GUIDELINES.md](./FRONTEND_GUIDELINES.md)
5. [BACKEND_STRUCTURE.md](./BACKEND_STRUCTURE.md)
6. [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

---

## 什么时候看哪份文档

### 1) 我在定义目标 / 验收范围
- 看：`PRD.md`
- 你会得到：
  - 这是在做什么、为谁做
  - 什么必须做（In Scope）
  - 什么明确不做（Out of Scope）
  - 成功标准和边界场景

### 2) 我在梳理用户操作流程
- 看：`APP_FLOW.md`
- 你会得到：
  - 页面与路由清单
  - 每条关键流程的触发条件、步骤、成功/失败路径
  - 决策点（例如无 active 会话如何处理）

### 3) 我在装环境 / 锁依赖版本
- 看：`TECH_STACK.md`
- 你会得到：
  - 前后端依赖和版本
  - 运行环境要求
  - 本地模型与 endpoint 约束

### 4) 我在做 UI 或前端交互
- 看：`FRONTEND_GUIDELINES.md`
- 你会得到：
  - 视觉风格与设计 token
  - 布局与滚动规则
  - 组件行为规范和禁用项

### 5) 我在改后端表结构 / API / 流式协议
- 看：`BACKEND_STRUCTURE.md`
- 你会得到：
  - 数据库表结构、索引、约束
  - API 合约与 SSE 事件约定
  - provider 策略与异常映射

### 6) 我在安排开发顺序与回归测试
- 看：`IMPLEMENTATION_PLAN.md`
- 你会得到：
  - 分阶段实施路线与 DoD
  - 联调步骤
  - 测试矩阵与回归清单
  - 部署流程与环境变量清单

---

## 推荐使用顺序（给新同学 / 新会话）

1. `PRD.md`（先对齐目标）
2. `TECH_STACK.md`（确认环境）
3. `APP_FLOW.md`（明确交互流程）
4. `BACKEND_STRUCTURE.md` + `FRONTEND_GUIDELINES.md`（落实实现细节）
5. `IMPLEMENTATION_PLAN.md`（按步骤执行与验收）

---

## 维护约定

1. 代码变更后，如影响行为/协议/依赖，需同步更新对应文档。
2. 每次更新文档，保留文档尾部 `Last updated from codebase on YYYY-MM-DD`。
3. 若新增规范文档，请在本索引追加：
   - 文档链接
   - 适用场景
   - 推荐阅读时机

---

Last updated from codebase on 2026-03-05
