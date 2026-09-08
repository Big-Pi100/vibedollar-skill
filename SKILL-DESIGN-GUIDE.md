# vibedollar-skill 设计工作规范（Skill Design Guide）

> 来源：CodeBuddy/WorkBuddy 生态 skill-creator 元技能（builtin，路径
> `D:\Program Files\WorkBuddy\resources\app.asar.unpacked\resources\plugins\
> workbuddy-builtin\skills\skill-creator\`）。本文件 = 提炼后的**强制工作规范**：
> vibedollar-skill 的一切设计、开发、迭代**必须**遵守本文，不得凭印象临时发挥。
>
> 适用范围：`publish/vibedollar-skill`（GitHub `Big-Pi100/vibedollar-skill`）的
> SKILL.md / scripts / references / assets 设计与修改。

---

## 1. Skill 是什么

Skill = **模块化自包含包**，扩展宿主 agent（Claude/pi/任意 MCP agent）的能力：
给 agent "入职指南"——特定领域的程序性知识（procedural knowledge）是模型本身
不具备的。Skill 不是 agent；它被宿主 agent 加载后，宿主用自己的 loop 驱动。

**四类内容**（skill 提供什么）：
1. 专门工作流（多步程序）
2. 工具集成（文件格式/API 操作指引）
3. 领域知识（schema/业务逻辑）
4. 捆绑资源（复杂重复任务的 scripts/references/assets）

---

## 2. Skill 解剖学 + 渐进式披露（核心设计原则）

```
skill-name/
├── SKILL.md       ← 必填：方法论/流程/触发条件（触发时加载, <5k 词）
├── scripts/       ← 可执行代码：无需读进 context 可直接运行（无限）
├── references/    ← 按需加载的参考文档（schema/API/政策/定价）——太大塞不进 SKILL.md 的
└── assets/        ← 模板/图标/字体：用于输出而非阅读
```

**三级加载机制（省 context 是第一设计原则）**：
1. **元数据**（name+description）~100 词：始终在 context
2. **SKILL.md 正文** <5k 词：触发时加载
3. **bundled resources** 无限：按需加载（scripts 可不读 context 直接执行）

**推论（强制）**：
- 低频/一次性内容（定价表、支付流程、客户端配置、政策）→ 放 **references/**，SKILL.md
  只留一句话指引 + 引用
- 机械重复动作（批量并行处理）→ 放 **scripts/**（agent 直接调比现场写循环高效）
- SKILL.md 正文只留：工具契约 + 决策知识 + 触发条件

---

## 3. frontmatter 硬性要求

```yaml
---
name: <hyphen-case, ≤40 字符>          # 必填
description: <第三人称, 不含 < 或 >>     # 必填
agent_created: true                    # 仅 WorkBuddy 本地自建必须加 → 否则 SkillManage 无法改/删
---
```

**三个易踩坑**：
1. 路径错位：文档写 `~/.codebuddy/skills/`，实际 WorkBuddy 用 `~/.workbuddy/skills/`
2. 忘加 `agent_created: true` → 自己写的 skill 改不动
3. 编辑 marketplace 已装 skill 后没写 `"userModified": true` 到 `_skillhub_meta.json`
   或 `_knot_meta.json` → 下次市场更新静默覆盖

### 3b. 跨平台分发（GitHub 通用 skill — vibedollar-skill 场景）

**平台特有元数据不进仓库源文件；各平台安装时自己加。** vibedollar-skill 会被
Claude / pi / 任意 MCP agent / WorkBuddy 等多个宿主拉取，SKILL.md 必须平台中立：

| 字段 | 归属 |
|---|---|
| `name` + `description` | 源文件保留（通用最小集 — 所有平台认可）|
| `agent_created` / `userModified` | WorkBuddy **安装/编辑时**补，不进源文件 |
| `license` | 可留（平台无关）|

**安装到不同宿主**：
- WorkBuddy → `~/.workbuddy/skills/<name>/`，宿主自行补 agent_created/meta，用户不改 SKILL.md
- Claude / 其他 MCP agent → 按各宿主的 skill 目录约定放置（如 `.claude/skills/`）；
  vibedollar-skill 是 MCP 远程工具型 skill，连 `mcp.vibedollar.net/mcp` 即用
- **写作纪律**：SKILL.md 不出现任何宿主名（"在 WorkBuddy 里…"等），只描述工具/端点/
  决策知识 —— 保持任何 agent 可消费

---

## 4. 六步创建流程

### Step 1：理解用法（concrete examples）
- 问/推导：什么用户语句会触发？功能边界？给具体例子。
- 每个例子想清楚"从零执行要什么"。
- 结论：skill 该支持什么功能有清晰认知。

### Step 2：规划可复用内容
- 分析每个例子 → 哪些 scripts（重复机械代码）/ references（大文档）/
  assets（输出素材）值得存。**避免全塞**；只留真会被重复用到的。

### Step 3：初始化
- 新 skill 跑 `scripts/init_skill.py <name> [--path]` 生成骨架（SKILL.md 模板 +
  scripts/references/assets 示例）。
- 位置：user skill（`~/.workbuddy/skills/`，跨项目）vs project skill
  （`.workbuddy/skills/`，随仓库共享）。不确定 → user skill。

### Step 4：编辑
**写作风格（强制）**：整篇用**祈使/不定式**（verb-first："To do X, do Y"），
**不用第二人称**（禁 "You should..." / "If you need to..."）。
客观、指令式——为 AI 消费而写。

SKILL.md 回答三个问题：
1. 目的（几句话）
2. 何时用（触发条件）
3. 怎么用（引用全部 reusable contents，让 agent 知道怎么调）

删除 init 生成的示例文件（多数 skill 不需要全部三类目录）。

### Step 5：打包
`scripts/package_skill.py <dir>`：先 validate（frontmatter/命名/结构/资源引用）再
打 zip。validate 失败报错退出，修完重跑。

### Step 6：迭代
真实任务里用 → 发现卡点/低效 → 改 SKILL.md 或资源 → 再测。

---

## 5. 编辑已装 skill 的规范

1. 先读现有 SKILL.md 及相关文件，理解现状再改
2. 应用用户要求的编辑
3. **保存后**：若目录有 `_skillhub_meta.json` / `_knot_meta.json` → 写
   `"userModified": true`（防市场更新覆盖）；无 meta 文件（本地创建）→ 跳过
4. 告知用户编辑已保存、未来更新会先询问

**重要**：只在文件真写入后标 userModified；新建 skill 不标（仅 marketplace 装的有意义）。

---

## 6. vibedollar-skill 审查清单（每次改完自查）

| # | 检查项 | 通过标准 |
|---|---|---|
| 1 | frontmatter | name hyphen-case ≤40；description 第三人称无尖括号；**跨平台通用 skill 只保留 name+description，不加 agent_created（平台安装时补）**；仅纯本地自建加 agent_created: true |
| 2 | 渐进披露 | 定价/支付/配置/政策在 references/ 不在 SKILL.md 正文；SKILL.md <5k 词 |
| 3 | 写作风格 | 全篇祈使/不定式，无第二人称叙述 |
| 4 | 资源引用 | SKILL.md 引用全部 scripts/references，说明何时调、入参、返回 |
| 5 | scripts 定位 | 纯执行器（无自调度/无决策）；决策归宿主 agent；显式入参 |
| 6 | 示例清理 | 无 init 模板占位文件残留 |
| 7 | 双语同步 | SKILL.md 与 SKILL.zh-CN.md 结构一致（可不同译法，不可缺段）|
| 8 | 迭代留痕 | 每次真实使用后记录 struggle → 更新点（可入 git log）|

---

## 7. 当前审查已知差距（待修复队列）

- [x] **A. 无 references/**：Pricing / Payment & activation / MCP client config 已拆到
      `references/billing.md` + `references/billing.zh-CN.md` + `references/mcp-config.md`；
      SKILL.md 正文降到 <5k 词（f34b36d）
- [x] **A2. 低频内容二次清理（2026-09-08）**：渐进披露只做了一半 —— 注册流程（Quick start /
      用法示例 / Agent tips 三处重复）、定价解锁明细（zh 快速开始）、下游用例（"Ways to use the
      data" 50 行 + zh 3 用法）仍整段留在正文。本次：注册收敛为一句指引（完整流程指
      billing.md）；定价明细从正文删除；下游用例整体迁移到新 `references/use-cases.md` +
      `references/use-cases.zh-CN.md`；zh "用法示例"（重复注册演示）删除；双语段落结构对齐
      （EN/ZH 各 16 节）；SKILL.md 307→248 行（3602→3157 词），SKILL.zh-CN.md 309→247 行
- [x] **A2.2. 决策循环落 SKILL.md（2026-09-08）**：v2 决策循环（判据②③/决策表/验证门控/
      审计日志）原设计由 lead_agent.py 承载，裁决砍内嵌 agent 后未迁移到新载体 → SKILL.md
      只有两段零散提示，agent 跑到"stock>0 → score first"后无下一步（345 A2 实测暴露）。
      本次：新增 **"Agent decision loop (per subscription, per round)"** 节（EN/ZH 同步）——
      perceive/plan/act/verify 四步 + 决策表；**A. 评分反馈优先闭环**（词 0 delivered +
      ≥2 irrelevant → 当轮 `vibe_keyword_remove(force)` 退役，不等服务端每日批）；
      B. NEW30 边际产出（created_at 近 30 天词命中率 → 扩或停）；C. collecting_ok/catalog
      判据③；决策表 6 行；verify 门控 + 策略切换纪律（无时钟冷却）；审计日志要求。
      替换旧 "Delivery-health tuning"（gap 驱动已过时）+ "Supply-side decisions" 两节；
      EN 248→306 行（3157→3505 词），ZH 247→301 行，双语各 15 节仍对齐。
- [x] **A2.3. row-1 判据歧义修正（2026-09-08，子 agent 干净上下文实测反馈）**：
      `n_rejected` 是跨评分者累计，非"你的评分"专属 → row-1 / Plan-A 补仲裁规则：
      `invalid_sample` 显示跨主题垃圾 = 噪声词可 retire；本领域内合理却被拒 = 疑似误判
      → `vibe_recover_lead` 恢复，不凭它 retire。决策表 row-1 同步改
      "0 delivered + ≥2 rejected, invalid_sample off-topic"。
      （后端字段化建议另记 vibedollar docs/agent-loop-tool-gaps-record-20260908.md）
- [x] **A2.4. 打磨 prompt 资产化（2026-09-08，用户指正）**：sdGen/kwInit/kwOpt/ENG_SYS_CORE
      全活在前端 `site/js/app.js` orchPrompts()，v2 §8.2 "prompt 资产统一放
      vibedollar-skill/scripts/*.md 单源免漂移" 只做了裁决未执行 → skill 无供需生成/扩词
      模板，判真也不注入 sd（前端带 [SUPPLY/DEMAND]，skill score_batch 只拼 product）。
      本次：资产化 `scripts/sd_gen.md` / `kw_init.md` / `kw_opt.md` /
      `eng_sys_core.md`（只读 — 计费契约）；judge_prompt.md 对齐 ENG_SYS_CORE（炫耀帖/
      成熟卖家排除 0-29，契约段不可改）；score_batch.py 从 vibe_list_subs 读 sd_json 注入
      system；SKILL.md/zh 新增 "Setup & tuning prompts" 资产表（顺序：sd → kw → judge），
      修复旧节名交叉引用；前端单源迁移仍待做（app.js 与 scripts/*.md 并存，阶段 C 收口）。
- [x] **A2.5. 决策循环 v2.1 交付驱动重写（2026-09-08，用户裁决⑥⑦）**：旧决策循环
      "评分→retire→等服务端批" 停摆于全 irrelevant —— 无交付目标判定、词错被当"需求
      到头"、SKILL.md 还写"server also penalizes/retires"（把 agent 决策外包给服务端批）。
      本次：决策循环改 **交付目标驱动**（§0 目标检查：本月 delivered vs 承诺 → 未达成
      必须 act 换方向，唯一停止 = 方向穷尽后 report_exhausted）；新增 §2 健康数据语义表
      （每个返回字段的含义 + agent 该决定的动作）；全 irrelevant → retire → **从 sd
      重生成词面**（sd_gen/kw_init）而非放弃；服务端零决策措辞（无 server penalize/无
      F2-wait）。后端同步 A1.5：F3/F2/decide_kw 自动退役停用、consume_feedback 只聚合。
- [x] **B. frontmatter 无 agent_created**：已决 — 跨平台通用 skill 不加（§3b）
- [x] **C. 开场第二人称叙述**：已改祈使/客观（f34b36d）
- [x] **D. score_batch.py 使用引导**：已加"先 --dry-run 验证连通"（f34b36d）
