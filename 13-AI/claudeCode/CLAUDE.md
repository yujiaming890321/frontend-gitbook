# Claude

- install everything-claude-code

no guessing, ask me first if you are unsure.
保持代码整洁，重复的代码要提取抽象出来
有业务逻辑的方法要写英文注释写明原因

## 工作模式

先做计划，列出修改方案给用户确认后再实施。把方案生成md文件存储到 project/docs/plans。不要未经确认就直接改代码。

## Compact Instructions

When compressing, preserve in priority order:

1. Architecture decisions (NEVER summarize)
2. Modified files and their key changes
3. Current verification status (pass/fail)
4. Open TODOs and rollback notes
5. Tool outputs (can delete, keep pass/fail only)

## get claude code usage cost

use npx ccusage@latest
