# AI SDD Bootstrap Skill 设计文档

> 一个 Kimi Code CLI Skill，用于在新建项目时初始化 AI 编程工程化骨架，并在迭代过程中辅助生成 Spec、ADR 和 Harness。

## 1. 背景与目标

### 1.1 背景

基于 B 站 UP 主 **AI 林湛星 / 瑞林川** 的 6 个系列视频，以及 Karpathy 的经典 `CLAUDE.md`，总结出一套 AI 编程工程化方法：

- **Spec**：记录已固化的决策，按需加载
- **Harness**：可执行测试，锁住边界和不变量
- **ADR**：架构决策记录，沉淀重要选择
- **项目宪章**：`CLAUDE.md` / `AGENTS.md` 给 AI 的行为约束

### 1.2 目标

将上述方法封装成一个可复用的 Kimi Code CLI Skill，实现：

1. **分阶段初始化**：MVP 阶段只生成最小骨架，不提前建立文档/约束；架构稳定后再一键建立完整工程化框架
2. **辅助沉淀**：在编码过程中辅助生成 ADR、Feature Spec、Harness
3. **状态感知**：扫描项目状态，智能推荐下一步动作
4. **避免过早约束**：文档、ADR、Harness 都按需生成，不在探索期制造枷锁

## 2. 用户价值

- 降低新项目启动的认知负担
- 标准化项目工程化结构
- 把"事后总结"变成"事前脚手架"
- 减少重复劳动（写宪章、建目录、生成文档模板）
- 在迭代中持续沉淀 spec/harness，防止 AI 改坏旧功能

## 3. 核心设计原则

### 3.1 MVP 阶段只生成最小骨架

`init` 阶段绝不生成 Harness 代码，也不生成 docs/、CLAUDE.md、AI_HANDOFF.md 等完整工程化结构。只生成：

- `README.md`（MVP 版本）
- `AGENTS.md`（MVP 版本：鼓励探索，禁止过早约束）
- `.gitignore`

完整的 docs/ADR/spec/harness 框架由 `bootstrap-foundation` 在架构稳定后生成。

### 3.2 按需生成 Harness

Harness 只有在用户主动调用 `add-harness` 时才生成，且推荐在 `bootstrap-foundation` 之后使用。需要满足：

- 项目架构已稳定
- 用户明确知道要锁住哪个边界
- 有对应的 Feature Spec 或 ADR 可参考

### 3.3 行为宪法优先

`docs/guide/ai-behavior.md` 是最高优先级的必读文件，由 `CLAUDE.md` 和 `AGENTS.md` 直接引用。

### 3.4 元示例分离

具体文档（ADR、Feature Spec）保持空白或极简占位符。格式示例放在 `docs/examples/` 目录，标注为 `*.example.md`，避免污染主文件。

### 3.5 扫描 + 推荐，不替代判断

Skill 可以基于启发式规则推荐下一步，但所有决策最终由用户确认。

## 4. 功能设计

### 4.1 命令清单

| 命令 | 作用 | 触发场景 |
|------|------|---------|
| `init` | 初始化最小 MVP 骨架 | 新项目首次使用，探索期 |
| `bootstrap-foundation` | 建立完整 docs/ADR/spec/harness 框架 | MVP 验证完、架构稳定后 |
| `status` | 扫描项目状态并推荐下一步 | 编码过程中随时调用 |
| `add-adr` | 交互式生成新的 ADR | 需要记录架构决策时 |
| `add-spec` | 交互式生成新的 Feature Spec | 需要固化功能边界时 |
| `add-harness` | 按需生成 Harness 骨架 | 需要锁住核心流程时 |

### 4.2 init 流程

1. 检查当前目录是否已最小初始化（存在 `AGENTS.md`）
2. 如果已初始化，提示用户并询问是否覆盖
3. 询问项目技术栈（Node.js/TypeScript、Python、Rust、语言无关）
4. 生成最小 MVP 骨架：`README.md`（MVP 版）、`AGENTS.md`（MVP 版）、`.gitignore`
5. 输出初始化摘要，提示架构稳定后运行 `bootstrap-foundation`

### 4.3 bootstrap-foundation 流程

1. 检查当前目录是否已最小初始化
2. 询问项目技术栈（可复用 init 时的选择）
3. 生成完整工程化框架：
   - `docs/INDEX.md`
   - `docs/guide/ai-behavior.md`
   - `docs/guide/project-meta.md`（stage = foundation）
   - `docs/adr/`、`docs/feature/`、`docs/examples/`
   - `AI_HANDOFF.md`、`CLAUDE.md`
   - 更新 `AGENTS.md` 和 `README.md` 为 foundation 版本
4. 输出摘要，提示开始 `review-architecture`

### 4.4 status 流程

1. 扫描项目结构
2. 判断是否为最小初始化、是否已建立 foundation 框架
3. 统计 ADR / Feature Spec / Harness 数量
4. 读取当前 git 分支和未提交文件
5. 基于启发式规则生成推荐
6. 输出状态摘要和选项菜单

### 4.5 add-adr 流程

1. 询问 ADR 标题
2. 询问决策背景
3. 询问具体决策
4. 询问后果/权衡
5. 询问状态（proposed / accepted / deprecated）
6. 生成 `docs/adr/ADR-NNN-<short-title>.md`
7. 更新 `docs/INDEX.md`

### 4.6 add-spec 流程

1. 询问 feature 名称
2. 询问范围（做什么、不做什么）
3. 询问边界规则
4. 询问验收方式
5. 询问依赖
6. 生成 `docs/feature/<feature-name>.md`
7. 更新 `docs/INDEX.md`

### 4.7 add-harness 流程

1. 读取 `docs/guide/project-meta.md` 中的技术栈
2. 询问要覆盖的业务流程
3. 询问要锁住的边界
4. 根据技术栈生成对应测试骨架
5. 输出安装依赖和运行命令提示

## 5. 生成的文件结构

### 5.1 MVP 阶段（`init` 后）

```
project-root/
├── AGENTS.md          # MVP 版本：鼓励探索，禁止过早约束
├── README.md          # MVP 版本
└── .gitignore
```

### 5.2 Foundation 阶段（`bootstrap-foundation` 后）

```
project-root/
├── docs/
│   ├── INDEX.md                          # 文档索引
│   ├── adr/                              # 架构决策记录
│   │   └── .gitkeep
│   ├── feature/                          # 功能规格
│   │   └── .gitkeep
│   ├── guide/                            # 指南文档
│   │   ├── ai-behavior.md               # AI 行为宪法（完整）
│   │   └── project-meta.md              # 项目元信息（技术栈、阶段）
│   └── examples/                         # 元示例文件
│       ├── ADR-001.example.md
│       └── feature-spec.example.md
├── CLAUDE.md                             # Claude 项目宪章
├── AGENTS.md                             # Foundation 版本：通用 Agent 入口
├── AI_HANDOFF.md                         # AI 交接文档
└── README.md                             # 项目工程化说明
```

## 6. 核心文件内容设计

### 6.1 docs/guide/ai-behavior.md

包含两部分：

1. **Karpathy 风格行为指南**
   - Think Before Coding
   - Simplicity First
   - Surgical Changes
   - Goal-Driven Execution

2. **文档规范**
   - ADR 必须包含哪些章节
   - Feature Spec 必须包含哪些章节
   - Harness 必须包含哪些部分

### 6.2 CLAUDE.md

- 顶部强提示："Before any task, read `docs/guide/ai-behavior.md`."
- 项目宪章模板
- 如何调用 spec/harness/adr 的说明

### 6.3 AGENTS.md

- 顶部强提示："You MUST read `docs/guide/ai-behavior.md` before implementing."
- 通用 Agent 行为指南
- 工程化工作流说明
- 指向 CLAUDE.md 和 docs/INDEX.md 的链接

### 6.4 docs/INDEX.md

- 文档地图
- 按优先级分类列出所有文档
- 标注 `ai-behavior.md` 为必读

### 6.5 docs/examples/*.example.md

- 只展示格式，不涉及真实业务
- 用 `[待填写]`、`example-module` 等明显占位符
- 前后用强注释包裹

## 7. 技术栈适配

### 7.1 首发技术栈

**Node.js / TypeScript**

Harness 示例使用 Vitest：

```typescript
// tests/harness/example.spec.ts
import { describe, it, expect } from 'vitest';

describe('核心流程名称', () => {
  it('应该满足某个边界条件', () => {
    // TODO: 替换为真实业务逻辑
    expect(true).toBe(true);
  });
});
```

### 7.2 后续扩展技术栈

| 技术栈 | 测试框架 | Harness 目录 |
|--------|---------|-------------|
| Python | pytest | `tests/harness/` |
| Rust | cargo test | `tests/harness/` |
| 语言无关 | 无 | 只生成文档骨架 |

## 8. 智能化辅助逻辑

### 8.1 status 扫描项

- 是否已最小初始化（`AGENTS.md` 存在）
- 是否已建立 foundation 框架（`docs/`、`AI_HANDOFF.md`、`CLAUDE.md` 存在）
- 技术栈
- ADR 数量
- Feature Spec 数量
- Harness 数量
- 当前 git 分支
- 未提交文件列表
- 缺失的核心流程文档

### 8.2 启发式推荐规则

| 信号 | 推荐 |
|------|------|
| 分支名为 `feat/<name>` 且无对应 Feature Spec | 生成 Feature Spec |
| 改动路径含 `auth/` / `login/` / `payment/` / `permission/` | 考虑生成 Harness |
| 同一文件最近 3+ 次提交 | 可能是重复踩坑区，建议沉淀 ADR |
| 有 Feature Spec 但无 Harness | 建议补充 Harness |
| 项目无 ADR | 建议先沉淀第一条 ADR |

### 8.3 交互模式

Skill 永远先输出扫描结果和建议，然后让用户选择，不自动执行任何写入操作。

## 9. 错误处理

### 9.1 已初始化项目

如果检测到项目已初始化，询问用户：
- 覆盖所有文件
- 仅更新缺失文件
- 取消

### 9.2 未知技术栈

如果用户在 `add-harness` 时技术栈未记录，重新询问并更新 `project-meta.md`。

### 9.3 非 git 项目

`status` 命令在非标项目时跳过 git 相关扫描，只输出文件统计。

## 10. 扩展性

### 10.1 新增技术栈

新增技术栈只需要：
- 在 init 的技术栈选项中加入
- 新增对应的 harness 模板
- 更新 `project-meta.md` 的记录格式

### 10.2 新增文档类型

新增文档类型需要：
- 在 `ai-behavior.md` 中添加文档规范
- 新增空白模板
- 新增元示例文件
- 更新 `docs/INDEX.md`
- 新增对应的 `add-<type>` 命令

## 11. 边界与限制

- Skill 不能替代人对业务重要性的判断
- Skill 无法读取代码语义，只能基于文件路径和数量做启发式推荐
- Harness 模板需要用户根据真实业务替换
- 多技术栈支持是渐进式的，首发只支持 Node.js/TypeScript

## 12. 成功标准

- 用户可以在 1 分钟内完成新项目最小 MVP 初始化
- MVP 阶段不会生成过多文档和约束，不限制 AI 探索
- 架构稳定后，用户可以自然语言触发 `bootstrap-foundation` 建立完整框架
- 生成的文档结构清晰，AI 能正确识别和加载
- 在编码过程中调用 Skill，能获得合理的下一步建议
- 用户能轻松生成 ADR、Feature Spec、Harness，而不用手动复制模板

## 13. 实现计划概要

1. 创建 Skill 目录结构
2. 实现 `init` 命令
3. 实现 `status` 命令
4. 实现 `add-adr` 命令
5. 实现 `add-spec` 命令
6. 实现 `add-harness` 命令（首发 Node.js/TypeScript）
7. 编写 SKILL.md 文档
8. 测试并迭代
