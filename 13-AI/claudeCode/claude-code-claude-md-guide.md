# Claude Code 如何读取 CLAUDE.md

## 概述

Claude Code 使用分层的、上下文感知的加载机制来读取 `CLAUDE.md` 文件。该系统确保 Claude 获得相关的指导信息，更具体的指令通常会覆盖更宽泛的指令。所有加载的内容会以 `<system-reminder>` 标签注入到 Claude 的系统上下文中。

---

## 一、支持的文件名

| 文件名 | 说明 |
|--------|------|
| `CLAUDE.md` | 主要指令文件（各层级通用） |
| `CLAUDE.local.md` | 本地变体，不纳入版本控制，用于个人配置 |
| `.claude/CLAUDE.md` | 项目 `.claude` 目录下的指令文件 |
| `.claude/rules/*.md` | 模块化规则文件，支持按路径作用域加载 |

---

## 二、搜索层级与优先级（从高到低）

### 1. 企业策略（最高优先级）

- **位置**：
  - macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`
  - Linux: `/etc/claude-code/CLAUDE.md`
- **用途**：由 IT 或 DevOps 团队管理，强制执行组织范围内的指令、安全策略、合规要求和强制编码标准
- **适用范围**：所有用户、所有项目

### 2. 用户级指令

- **位置**：`~/.claude/CLAUDE.md`
- **用途**：包含适用于所有项目的个人偏好和配置
- **示例**：代码风格偏好、个人工具快捷方式、默认语言设置等

### 3. 项目级指令

- **位置**：
  - `./CLAUDE.md`（项目根目录）
  - `./.claude/CLAUDE.md`
- **用途**：团队共享的项目特定指令，如项目架构、编码标准、常用工作流、构建命令和测试指令
- **加载方式**：Claude Code 启动时自动加载项目根目录及其**所有祖先目录**中的 `CLAUDE.md` 文件（祖先目录加载）
- **通常纳入版本控制**

### 4. 模块化规则文件

- **位置**：`.claude/rules/*.md`（如 `.claude/rules/code-style.md`）
- **用途**：将项目指令拆分为多个模块化文件，适用于大型项目
- **加载方式**：
  - 没有 `paths` 字段的规则文件 → 启动时加载，优先级与 `.claude/CLAUDE.md` 相同
  - 有 `paths` 字段的规则文件 → 按需加载，仅当 Claude 读取匹配路径的文件时才触发
- **路径作用域示例**（YAML frontmatter）：
  ```yaml
  ---
  paths:
    - "src/components/**/*.tsx"
  ---
  React 组件必须使用函数式组件和 hooks。
  ```

### 5. 子目录 CLAUDE.md（最低优先级）

- **位置**：当前工作目录的子目录中的 `CLAUDE.md` 文件
- **加载方式**：**不在启动时加载**，而是当 Claude 读取该子目录中的文件时按需加载
- **适用场景**：monorepo 或包含独立模块的项目

---

## 三、加载流程图

```
启动 Claude Code
    │
    ├── 1. 加载企业策略
    │     /Library/Application Support/ClaudeCode/CLAUDE.md (macOS)
    │     /etc/claude-code/CLAUDE.md (Linux)
    │
    ├── 2. 加载用户级指令
    │     ~/.claude/CLAUDE.md
    │
    ├── 3. 加载项目级指令（含祖先目录遍历）
    │     从当前目录向上遍历，加载每个祖先目录的 CLAUDE.md
    │     ./CLAUDE.md
    │     ./.claude/CLAUDE.md
    │
    ├── 4. 加载通用规则文件
    │     .claude/rules/*.md（无 paths 字段的）
    │
    └── [运行中] 按需加载
          ├── 路径匹配的规则文件（有 paths 字段的 .claude/rules/*.md）
          └── 子目录的 CLAUDE.md（读取子目录文件时触发）
```

---

## 四、内容注入方式

加载后的内容会以 `<system-reminder>` 标签包裹，注入到 Claude 的系统上下文中：

```xml
<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below...

Contents of /Library/Application Support/ClaudeCode/CLAUDE.md (user's private global instructions for all projects):
[企业/全局指令内容]

Contents of /Users/username/project/CLAUDE.md (project instructions, checked into the codebase):
[项目级指令内容]
</system-reminder>
```

---

## 五、冲突解决机制

- 各层级指令通常是**叠加的**，所有层级的内容同时贡献给 Claude 的上下文
- 当指令冲突时，Claude 使用判断力协调冲突，**倾向于更具体的指导**
- 一般优先级：企业策略 > 用户级 > 项目级 > 规则文件 > 子目录

---

## 六、特殊功能

### @import 引用

在 `CLAUDE.md` 中可以使用 `@` 语法引用其他文件：

```markdown
参考项目的 @README.md 了解项目结构
参考 @package.json 了解依赖
```

### --add-dir 标志

- 使用 `--add-dir` 标志允许 Claude 访问额外目录
- 默认情况下，这些额外目录中的 `CLAUDE.md` **不会被加载**
- 设置环境变量 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 可启用加载
- 适用于 monorepo 中共享标准或跨项目使用

### MEMORY.md 自动记忆系统

- 位置：`~/.claude/projects/<project>/memory/MEMORY.md`
- 自动加载，但有大小限制（超过 200 行会被截断）
- 详细笔记应写入独立的主题文件，按需读取

---

## 七、最佳实践

| 建议 | 说明 |
|------|------|
| 控制在 200 行以内 | 过长的文件消耗更多上下文，可能降低遵循度 |
| 使用 Markdown 结构 | 使用标题和列表组织指令，提高清晰度 |
| 指令要具体简洁 | 使用祈使句形式（如 "使用 unknown 代替 any"） |
| 避免冗余信息 | 不要包含 Claude 已知的常识（如标准语言惯例） |
| 大量文档用 @import | 避免在 CLAUDE.md 中嵌入大段文本，改用引用 |
| 利用模块化规则 | 大型项目应将指令拆分到 `.claude/rules/` 中 |
| 区分共享与个人配置 | 共享配置放 `CLAUDE.md`，个人配置放 `CLAUDE.local.md` |

---

## 八、完整文件位置速查

```
/Library/Application Support/ClaudeCode/CLAUDE.md   ← 企业策略 (macOS)
/etc/claude-code/CLAUDE.md                           ← 企业策略 (Linux)
~/.claude/CLAUDE.md                                  ← 用户全局指令
./CLAUDE.md                                          ← 项目根目录指令
./CLAUDE.local.md                                    ← 项目本地指令（不纳入版本控制）
./.claude/CLAUDE.md                                  ← 项目 .claude 目录指令
./.claude/rules/*.md                                 ← 模块化规则文件
./子目录/CLAUDE.md                                    ← 子目录指令（按需加载）
~/.claude/projects/<project>/memory/MEMORY.md        ← 自动记忆文件
```
