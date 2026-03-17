# DOCS_INDEX.md

`manus-lite-lab` 项目文档总索引（Chat 产品、流程、技术、实现计划的单一入口）。

## 文档导航
1. [PRD.md](./PRD.md) - 产品目标、范围、用户故事、验收标准
2. [APP_FLOW.md](./APP_FLOW.md) - 页面与交互流程、异常分支
3. [TECH_STACK.md](./TECH_STACK.md) - 前后端技术栈与版本基线
4. [FRONTEND_GUIDELINES.md](./FRONTEND_GUIDELINES.md) - UI 视觉与交互规范
5. [BACKEND_STRUCTURE.md](./BACKEND_STRUCTURE.md) - 数据模型、API 合约、SSE 协议
6. [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - 分阶段执行与回归验收

## 推荐阅读顺序
1. 先读 `PRD.md` 对齐“要做什么”和“做到什么算完成”
2. 再读 `APP_FLOW.md` 明确用户路径和状态流转
3. 接着读 `TECH_STACK.md` 准备环境并确认版本
4. 并行查阅 `FRONTEND_GUIDELINES.md` 与 `BACKEND_STRUCTURE.md` 执行开发
5. 最后按 `IMPLEMENTATION_PLAN.md` 进行联调、回归与部署

## 快速查找场景
- 改 UI 或交互细节：`FRONTEND_GUIDELINES.md` + `APP_FLOW.md`
- 改接口或流式协议：`BACKEND_STRUCTURE.md` + `APP_FLOW.md`
- 排查 thinking 卡住/重复与终止原因：`BACKEND_STRUCTURE.md` + `IMPLEMENTATION_PLAN.md` + `FRONTEND_GUIDELINES.md`
- 排查自动联网搜索策略：`APP_FLOW.md` + `BACKEND_STRUCTURE.md`
- 新功能排期：`PRD.md` + `IMPLEMENTATION_PLAN.md`
- 环境问题排查：`TECH_STACK.md`

## 文档维护规则
- 任何影响产品行为、接口协议、依赖版本的代码变更，都要同步更新对应文档。
- 每份文档保留 `Last updated from codebase on YYYY-MM-DD`。
- 新增规范文档时，必须在本索引追加链接与适用场景。

---
Last updated from codebase on 2026-03-06
