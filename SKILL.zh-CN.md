---
name: vibedollar
description: "vibedollar 帮助独立开发者找到第一批客户。基于你的产品描述，持续抓取 Reddit 上正在抱怨或求方案的潜在客户线索（帖子与评论），支持订阅持续监控。你的 agent 用自己的 LLM 判断相关性，评分通过才计费（按效果付费）。远程托管免部署。付费解锁：Starter 39/mo 或 Pro 79/mo；也可自由充值钱包额度。"
---

# vibedollar — 帮你找到正在等你的客户

> [English SKILL](SKILL.md) · [English README](README.md) · [中文 README](README.zh-CN.md)

vibedollar 监控 Reddit，找出那些正在主动寻找用户所建产品的帖子和评论，作为评分后的**潜在客户线索**。分工：vibedollar 运行数据服务（Reddit 采集、候选匹配入池、状态层——词表 / 供需判定口径 / 回收 / 健康）；**宿主 agent 决定什么算好客户**——用自带 LLM key 评分候选，并驱动调优（见下文**交付健康管理**与**供给侧决策**）。


## 什么时候用它

| 场景 | 用法 |
|------|------|
| 冷启动获客 | `vibe_subscribe` → 系统持续跟踪，线索自动积累，点进帖子直接触达潜在客户 |
| 验证产品点子 | 订阅后看积累的线索：有 N 条强需求信号 → 值得做 |
| 持续获客 | `vibe_subscribe` → 系统持续跟踪，候选自动积累，`vibe_leads` 领候选 → 评分通过进交付 |
| 给投资人/团队证明 | 积累的线索（你评分确认相关的）就是现成的"需求真实性论证" |

## 快速开始

1. **连接服务**（远程托管，无需本地部署）: 在 MCP 客户端添加端点
   `https://mcp.vibedollar.net/mcp`（FastMCP HTTP transport）
2. **注册获取 API key**（两步注册：先发验证码，验证后发 key；注册不送额度，之后选择订阅或充值解锁）:
   ```
   调用工具: vibe_register(email="you@example.com")   # 发送 6 位邮箱验证码
   调用工具: vibe_verify(email="you@example.com", code="123456")  # 验证码验证, 返回 api_key
   ```
   > 验证成功后，API key **同时通过邮件发送**到你的邮箱（也可在注册成功页一次性查看）。请妥善保存 key。
   > 付费解锁方式：订阅 Starter/Pro，或自由充值钱包额度（微信 ¥1~¥1000 / Creem $1~$200，任意次数）；另有 **$1 Welcome Credit** 新客福利（每人限一次）。钱包余额用于 Reddit 线索超量扣费。
3. **配置鉴权 Header**: 把拿到的 key 配到 MCP 客户端请求头（见下方「接入方式」），
   之后调用数据工具**不需要再传 api_key 参数**
4. **查余额/配额**: `vibe_balance()`（key 自动从请求头读取，返回 tier + 各工具配额余量）
5. **也支持网页自助注册**：打开 `https://vibedollar.net/account.html` 可完成注册/验证/支付全流程（用户可直接在网页操作，无需配置 MCP）

## 可用工具

| 工具 | 参数 | 说明 | 成本 | 鉴权 |
|------|------|------|------|------|
| `vibe_register` | `email` | 注册第 1 步: 发送 6 位邮箱验证码 | 免费 | 无需 |
| `vibe_verify` | `email, code` | 注册第 2 步: 验证码验证, 返回 api_key（同时邮件发送） | 免费 | 无需 |
| `vibe_balance` | `（无）` | 查余额/tier/配额余量（key 走 Header） | 免费 | Header |
| `vibe_subscribe` | `product` | **订阅持续监控**：输入产品描述，系统持续抓取匹配入池（词表由你的 agent 按健康缺口扩/停——见"交付健康管理"） | 免费（候选免费） | Header |
| `vibe_leads` | `subscription_id, limit` | **领取候选线索**（免费）：返回候选（含系统参考分），供你评分。评分通过才计费。**单次上限：free 20 / Starter 30 / Pro 50 条**（实际返回 = min(limit, 档位上限)）| **免费** | Header |
| `vibe_submit_score` | `scores` | **评分回传**：对候选评分，`relevant` 才计入交付（扣 1 配额/条），`irrelevant` 回灌优化 | 通过才扣档位额度 | Header |
| `vibe_score_discuss` | `limit, respond_id, response` | **评分分歧对齐（可选）**：查看你与系统参考评分不一致的候选，可说明你的理由——我们据此校准标准，推送更贴合你的判断 | 免费 | Header |
| `vibe_set_notify` | `enabled` | 邮件提醒开关：候选积压时是否发邮件通知你（默认开启，可关闭）| 免费 | Header |
| `vibe_list_subs` | `（无）` | 查看我的订阅列表及候选线索积累状态 | 免费 | Header |
| `vibe_unsubscribe` | `subscription_id` | 取消订阅（已积累的线索保留） | 免费 | Header |
| `vibe_mark_leads` | `lead_ids, outcome` | 标记线索结果（valid 有效 / invalid 无效 / contacted 已触达）——帮你跟踪线索跟进质量 | 免费 | Header |
| `vibe_get_delivered` | `lead_id` | 单条已交付线索详情（回访用） | 免费 | Header |
| `vibe_delivered` | `limit, offset` | 已交付线索列表（回访历史客户） | 免费 | Header |
| `vibe_recover_key` | `email` | **丢了 API key？** 第 1 步：给已注册邮箱发验证码（无鉴权）| 免费 | 无 |
| `vibe_recover_verify` | `email, code` | 第 2 步：验证码验证后，key 邮件发送到邮箱（无鉴权）| 免费 | 无 |

> 除 `vibe_register` 外，所有工具通过 HTTP 请求头 `Authorization: Bearer <api_key>` 鉴权，
> **工具参数中不再出现 api_key**（key 不裸奔、不进调用日志）。

### 管理工具（2026-09-05 —— 词表 / 健康 / 回收 / 判定口径）

| 工具 | 参数 | 作用 | 费用 | 鉴权 |
|------|------|------|------|------|
| `vibe_keywords` | `subscription_id`, `status`(可选) | **词表 + 命中统计**（query/hit/pooled/avg-score/source）：当前靠哪些词在匹配、每个词表现如何——扩/停前先读它 | 免费 | Header |
| `vibe_keyword_add` | `subscription_id, kw, kw_type, source` | **加词扩召回**。`source=manual`（默认）= 你的词、受保护不会被自动停；`source=auto` = 编排器加的词（未来弱了可被停）。同词覆盖 auto 词 = 你接管（变 manual）| 免费 | Header |
| `vibe_keyword_add_batch` | `subscription_id, keywords`(list of `{kw, kw_type}`), `source`(默认 auto) | **一次调用加 N 词**（逐条语义同 `vibe_keyword_add`）——初始词/扩词列表请用批量而非循环，留在账号限流窗内（free 5 / starter 10 / pro 20 每 60s）。单词失败不影响整批；返回 `{added, total, results}` | 免费 | Header |
| `vibe_keyword_remove` | `subscription_id, kw, force` | **停用词**（→ removed 不再匹配）。默认只停 manual 词；`force=true` 仅供编排器停 auto 弱词——手动勿用 | 免费 | Header |
| `vibe_sd_update` | `subscription_id, supply_side, demand_side, core_friction, demand_pain` | **设供需判定口径**（四段，服务端持久化）——这是评分引擎的官方判定上下文，每次评分注入为 [SUPPLY/DEMAND]。空字段保留旧值；你编辑后后端永不覆盖 | 免费 | Header |
| `vibe_sub_health` | `subscription_id` | **交付健康（零 LLM）**：配额 / 承诺日线（2×配额÷30）/ 今日入池 / 候选存量(new+sent) / 缺口 / 采集是否足量 / 上次优化。据此决定是否扩词 | 免费 | Header |
| `vibe_opt_log` | `subscription_id, outcome, reason, n_new_kw, n_replaced` | **记录一次扩词/优化事件**（写入优化历史，健康页可见）——扩/停后调用，闭环可审计 | 免费 | Header |
| `vibe_rejected` | `subscription_id, limit` | **回收历史**：引擎判不相关的候选（含理由分），跨会话持久 | 免费 | Header |
| `vibe_recover_lead` | `lead_id` | **恢复误判线索**：从回收池回到待评分队列，可重新评分（通过不重复计费）| 免费 | Header |
| `vibe_subs` | `subscription_id` | **来源 sub 命中统计**（各 sub 入池/状态分布）——哪些 subreddit 真在贡献。注意与 `vibe_list_subs`（你的订阅列表）区分 | 免费 | Header |
| `vibe_supply_status` | `subscription_id` | **语料供给状态快照（零 LLM，2026-09-07）**：拉取池规模 / 储备分层 / 词搜最近运行 / **近 7 天 post_store 入帖趋势**（语料是否还在增长）/ 名录新鲜度（总量 + 最后更新）/ ArcticShift 限流态（共享熔断，跨进程）。用于区分：*词面耗尽*（应扩词）vs *语料边界窄*（应扩 sub）vs *名录旧*（catalog 需月度刷新）vs *采集停* vs *限流中* | 免费 | Header |
| `vibe_search_probe` | `subscription_id`, `query`, `subreddits`, `limit`(≤5) | **池外定向搜索探测（ArcticShift，2026-09-07）**：扩词前先在目标 sub 内搜这个词——即时验证"这个词在那边到底能不能搜出帖子"（防盲扩）。命中的帖幂等入库共享语料；**不入你的 lead_pool**（匹配仍由词驱动）。与 `sub_pull`（只覆盖池内 sub）互补 | 免费 | Header |

> 费用说明：上面 10 个是读写状态操作——候选仍免费，仍只在 `vibe_submit_score` 判 `relevant` 时按效果计费（若未来有任一收费，最终计费口径会单独确认）。

### 交付健康管理（承诺缺口驱动的调优循环）

后端承诺的是**数据交付**：Reddit 采集 + 匹配入池。你的职责是让池子持续喂给你的买家画像——健康就是循环驱动器：

```
1. vibe_sub_health(subscription_id)        → 日线 / 今日入池 / 存量 / 缺口 / 采集足量
2. 若缺口（今日入池低于日线，或存量 < 20）且采集足量:
     vibe_keywords(subscription_id)         → 当前词 + 命中统计
     （你的 LLM）给出扩/停建议            → keyword_add(source=auto) / keyword_remove(force)
     vibe_opt_log(...)                      → 记录本次优化事件
3. 若缺口但采集不足: 后端今天拉得少——不要反复扩词，等数据
```

这取代旧的"系统自动调优"叙事：**你（你的 agent）是调优者**，服务端是纯数据/状态层。同一循环也跑在 vibedollar Web 工作台编排器与我们的营销舰队里。

### 供给侧决策（2026-09-07 —— 扩词 vs 扩语料 vs 等待）

`gap`（健康）是*交付*信号——但日线**不是**每日入池目标（首日存量匹配爆发巨大，稳态是少量增量）。判断"扩词是否还有用"要看**边际产出**，不是看日线：

```
1. vibe_supply_status(subscription_id) → 池规模 / 7 天入帖趋势 / 名录新鲜度 / 是否限流
2. 若 arctic.limited: 暂停供给动作（probe/扩词/扩 sub）等限流解除 —— 物理等待，非冷却
3. 若趋势健康且存量 > 0: 先评池（快环）——不要动词表
4. 近期新扩的词仍有命中（hit>0）？→ 继续扩（只用 probe 验证过的词）
5. 新词大量零命中（被自动退役）→ 词面已扫净 → 转向扩语料：widen subs
   （在刷新后的名录里重跑）或深挖已入池 sub（vibe_expand_sub）
6. 名录 last_updated_at 很旧 → 名录需要月度刷新（后端职责 —— alert，别自己扫）
```

关键习惯：**扩词前先 probe** —— `vibe_search_probe(query, [subs])` 几秒告诉你这词在那边
有没有帖子；盲扩后等 30min pipeline 统计，词表就是这样烂掉的。零命中词用
`vibe_keyword_remove(force=true)` 停（auto 词）——服务端也会自动退役它们（F3）。

## 获客方式（订阅即所有，2026-08-17 起纯订阅模式；2026-08-20 起候选+评分计费）

vibedollar 只提供**订阅模式**——输入产品描述，系统持续跟踪，候选线索自动积累，随时领取评分。

| 方式 | 工具 | 适用 | 输出 |
|------|------|------|------|
| **订阅监控** | `vibe_subscribe` + `vibe_leads` + `vibe_submit_score` | 所有场景：验证需求 / 持续获客 / 冷启动 | 候选免费，评分通过才计费 |

**推荐流程**：`vibe_subscribe(product)` 订阅你的产品 → 后台持续分析 Reddit，候选线索自动积累 → `vibe_leads` 免费领取候选 → **你用自己的 LLM 评分 → `vibe_submit_score` 回传** → 评"相关"的才计入交付（才扣配额）。

### 评分回传格式（用户 agent 调用规范）

```
vibe_leads(subscription_id=12, limit=10)
    → 候选列表: [{"id": 1, "title": "...", "url": "...", "score": 系统参考分, ...}, ...]
    （limit 传超过档位上限时按上限返回: free 20 / Starter 30 / Pro 50）

vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "直接求方案"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "与产品无关"},
    ...
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}
```

规则：
- **候选免费**：`vibe_leads` 不扣任何配额
- **通过才计费**：`verdict="relevant"` 的候选扣 1 配额/条，计入交付列表（`vibe_delivered` 可查）
- **不相关也请回传**（`irrelevant`）：这是状态层学习你评价标准的方式——每次 `irrelevant` 会降权产生该候选的词（服务端纯 SQL 状态迁移，不做 LLM）
- **每条候选每轮领取评一次；判 `irrelevant` 的进回收池**（`vibe_rejected` 可查）——若事后（如点开原文后）觉得判错了，用 `vibe_recover_lead` 恢复再评。判 `relevant` 即最终（已计费）
- 候选的 `score` 字段是系统参考分（仅供你参考，以你的判断为准）

## 本地脚本工具（批量执行器 —— 机械动作用脚本，决策归你）

**宿主 agent 是决策引擎**（何时做/做什么/为什么）。下面的脚本是**纯执行器**：各自高效
完成一个机械批量动作（逐条并行判真）——比现场写循环快得多。宿主决定何时调用、传什么参；
脚本返回结构化 JSON 供下一步决策。脚本**不自带调度、不自循环**。

**首次使用**：先跑一次 `--dry-run` 验证 key 与连通性（只领取、不判真、不交还），确认无误再花 LLM 调用。

### `scripts/score_batch.py` —— 评单个订阅的一批（领取→判真→交还）

| 参数 | 含义 |
|-------|------|
| `--sub` | 目标订阅 id（**必填** —— 单订阅单批）|
| `--limit` | 领取上限（默认 10）|
| `--judge` | 你的判真模板路径（默认 `scripts/judge_prompt.md`）|
| `--parallel` | 并行判真路数（默认 8 —— 效率核心）|
| `--threshold` | score ≥ 门槛 → `relevant`（默认 60）|
| `--out` | 证据输出目录（可选；relevant 行存 csv/jsonl）|
| `--dry-run` | 只领取，不判真不交还 |

```bash
export VIBEDOLLAR_API_KEY=...        # 你的 vibedollar key
export LLM_API_KEY=...               # 你的 LLM key
export LLM_BASE_URL=https://api.deepseek.com/v1
export LLM_MODEL=deepseek-chat
python3 scripts/score_batch.py --sub 12 --limit 20 --parallel 8 [--out ./evidence]
```

返回 JSON：`{sub_id, claimed, judged, relevant, submitted, failed, pending[]}` ——
读它再决定下一步（评别的订阅 / 扩词 / 等待）。

- **判真标准是你的**：编辑 `scripts/judge_prompt.md`（纯文本模板）定义"什么样的帖子算好客户"；
  `--threshold` 设 relevant 门槛
- **费用**：候选免费；`relevant` 才计 vibedollar 配额（按效果付费）；判真的 LLM 调用费走**你自己的 key**
- **失败安全**：某条判真失败不丢——留 pending 下轮重试；`vibe_leads` 返回 `locked`+pending 列表
  直到评完为止，把领的全评了（relevant 或 irrelevant）就解锁下一批

### `scripts/mcp.py` —— 共享 MCP 客户端（库，非 CLI）

供其他本地脚本 import：`from mcp import MCPClient`。不由你直接调用。

> **为什么用脚本而不是你自己写循环**：批量动作是机械的（领 N 条 → 逐条用你的 LLM 判 →
> 交还）。脚本把逐条判真并行化并返回干净 JSON —— 你仍是决策者，脚本替你干重复体力活，
> 比你每次现场手写循环快得多。

## 订阅模式（持续监控，不用反复调用）

不想每次手动查询？订阅一个产品，系统会**持续跟踪**，线索自动积累，你随时查看即可：

```
vibe_subscribe(product="team wiki tool for small teams")   # 创建订阅（只需产品描述）
    → {"ok": true, "subscription_id": 12, "message": "订阅创建成功, 后台正在跟踪..."}
    ↓ 系统持续跟踪，线索积累（无需你操作）
vibe_list_subs()                                          # 查看订阅状态 + 待领取数
    → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "...", "new_leads": 7}]}}
    ↓
vibe_leads(subscription_id=12, limit=10)                  # 领取候选线索（免费，秒回）
    → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7}}
    ↓ 你的 agent 评分后回传
vibe_submit_score(scores=[{"id": 1, "verdict": "relevant", "score": 90, "reason": "..."}])
    → {"ok": true, "passed": 1, "quota_used": 1, ...}
```

**适用场景**：
- 产品定位已确定，希望**持续获取**新出现的潜在客户，而不是想起来才查一次
- 词表不用手工维护——订阅产品描述即可；当交付落后于承诺线时，由**你的 agent** 读健康工具扩/停词（见"交付健康管理"）
- **评分通过才消耗配额**（按效果付费），订阅本身不额外收费
- **先处理再取下一批**：已领取的候选需全部评分（相关/不相关都算）后，才能领取下一批；未处理完时再次领取会返回**待处理候选列表（含 id）**——直接用这些 id 评分即可解锁下一批（id 丢了也能找回，不会锁死订阅）。长期未评分的候选（7 天）会自动过期释放。

**取消订阅**用 `vibe_unsubscribe`（已积累线索保留）。

## 订阅数据的分析用法（拿到线索后怎么用——服务本身不额外提供）

订阅数据 = **真实用户正在表达真实需求的原话**（谁 + 在哪 + 怎么说）。这不只是"线索列表"，可以往下游用：

### ① 目标客户访谈（理解客户——PMF 前关键一环）
```
数据源: vibe_leads 返回的候选（帖主 + 原话 + 版块）
用法:
  - 访谈对象池: 候选帖主就是"正在表达你解决的那个痛点"的人——
    比泛泛的"目标人群画像"更精准（他们已经用母语说出了需求）
  - 访谈问题弹药: 从候选帖里提取他们实际问的问题、纠结的点、
    对比过的方案——做成访谈提纲（问他们真实关心的事, 不猜）
  - 语言对齐: 用他们的原话写产品描述/落地页——用户读起来
    "这就是给我做的"
```

### ② 前 100 位客户（冷启动——从"发现"到"触达"）
```
数据源: 评分通过的交付线索（vibe_delivered——帖主可联系）
用法:
  - 优先名单: 按 score/reason 排序——"直接求方案"的帖主最先联系
  - 联系文案: 引用候选帖里的真实需求（"看到你在 Reddit 问 X"）——
    比群发模板回复率高（敲门砖——个性化证据开场）
  - 节奏: 每周处理一批（评分→筛选→联系→跟进）——候选持续积累,
    第一批客户来自第一批交付线索
```

### ③ SEO/GEO 优化数据（内容策略——从"搜索词"到"用户语言"）
```
数据源: 订阅词表（你的产品领域用户在 Reddit 的真实表达）+ 候选帖
用法:
  - 内容骨架: 从候选帖提取"用户怎么描述问题"——写标题/H1/FAQ
    用他们的语言（比优化过的关键词更真实——AI 引擎偏好引用
    真实社区语言）
  - 证据引用: 候选帖作为文章里的真实需求证据（公开帖——可引用
    描述模式, 不点名帖主）
  - 词表迭代: 看候选帖反复出现的表达 → 更新你的内容关键词
    （vibedollar 的评分回传本身也在优化你的订阅方向——双循环）
```

**共同点**：这三个用法都**复用你已拿到的订阅数据**——不新增服务/不改接口，是数据资产的下游应用。服务提供"发现需求的人 + 他们的原话"，你怎么用（访谈/触达/内容）由你的 agent 决定。

## 用法示例

```
# 1. 注册（两步: 先发验证码, 验证后发 key; 无需鉴权）
vibe_register(email="founder@example.com")
# → {"ok": true, "status": "pending", "message": "验证码已发送到邮箱", "email": "founder@example.com"}
vibe_verify(email="founder@example.com", code="123456")
# → {"ok": true, "api_key": "vibedollar_ab12...", "credit_usd": 0.0, "tier": "free"}
#   (api_key 同时通过邮件发送到邮箱, 请妥善保存)

# 2. 配置好 Authorization: Bearer <key> 后直接调用，不再传 api_key
# 订阅产品 → 后台持续跟踪 → 领取候选 → 评分通过才计费（配额内）
vibe_subscribe(product="team wiki tool for small teams")
# → {"ok": true, "subscription_id": 12, "product": "team wiki tool for small teams",
#     "message": "订阅创建成功, 后台正在搜索线索。几分钟后用 vibe_leads 查看。"}
#    ↓ 后台持续分析 Reddit, 线索自动积累 (无需你操作)
vibe_list_subs()
# → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "team wiki tool for small teams", "new_leads": 7}]}}
vibe_leads(subscription_id=12, limit=10)
# → {"ok": true, "data": {"posts": [{"id": 1, "title": "...", "url": "...", "subreddit": "...", "score": 90, "reason": "..."}], "count": 7}}

# 3. 查余额/tier/配额（key 从 Header 读取）
vibe_balance()
# → {"ok": true, "api_key": "vibedollar_ab12...", "credit_usd": 0.0, "tier": "free",
#     "quota": {...}}
```

## Agent 使用提示

- **用户丢了 API key？** 引导找回（无需重新注册）：
  ```
  vibe_recover_key(email=...)          # 给已注册邮箱发验证码
  vibe_recover_verify(email=..., code=...)  # 验证 → key 邮件发送到邮箱
  ```
  （或引导打开 https://vibedollar.net/account.html → "Lost your API key? Recover it"）
- **始终先注册再配置 Header**：注册返回的 key 配到客户端请求头（`Authorization: Bearer <key>`），
  未带 Header 会返回 `"Missing API key"`，未注册的 key 返回 `"Unknown API key"`。
- **看 `quota` 块做自我管理**：每次调用响应带 `quota: {scope, used, limit}`（如 `{"scope": "3000/mo", "used": 5, "limit": 3000}` = 已用 5/3000），
  用尽前主动提示用户升级（Starter/Pro）。
- **`vibe_leads` 返回候选线索（完整帖子+评论，免费）**：候选含 `id`、title、url、正文——你的 agent 读内容判断相关性，用 `vibe_submit_score` 回传评分。
- **评分通过才计费**：`verdict="relevant"` 的候选计 1 配额并进交付列表（`vibe_delivered` 可查）；`irrelevant` 也请回传（我们据此优化搜索方向，推送会越来越准）。
- **先处理再取下一批**：已领取的候选评分处理完后，才能领取下一批（未处理时会提示先完成当前批次的评分）。
- **订阅模式**：`vibe_subscribe(product)` 创建持续监控 → `vibe_list_subs()` 看状态 → `vibe_leads(subscription_id)` 领候选 → `vibe_submit_score` 评分 → `vibe_unsubscribe` 取消（候选保留）。
- **典型工作流**：`vibe_subscribe`（订阅产品，后台持续抓取）→ `vibe_leads` 领候选 → 你的 agent 用你的 LLM 评分 → `vibe_submit_score` 回传 → 通过的进交付列表（验证需求 + 找到第一批客户）。


## 定价 / 支付 / 接入（参考文档）

定价档位、钱包充值、Agent 支付开通全流程、MCP 客户端连接配置都在 `references/` —— 按需读取：

- **定价与支付**：用户问价格 / 升级 / 充值 / 支付后确认开通时，读 `references/billing.zh-CN.md`。日常快速查配额：调 `vibe_balance()` —— 响应带 `quota: {scope, used, limit}`。
- **MCP 接入配置**：首次连接或换客户端时，读 `references/billing.zh-CN.md` 的"接入方式"节（端点 URL + `Authorization: Bearer <key>` header 配置）。
