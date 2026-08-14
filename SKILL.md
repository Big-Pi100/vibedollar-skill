---
name: vibedollar
description: >-
  vibedollar 帮独立开发者找到第一批客户——基于你的产品描述，返回 Reddit 上正在抱怨/求方案的
  潜在客户线索（帖子+评论+相关性标注+需求论证报告），配 470+ 真实独立开发案例库做市场验证。
  远程托管免部署，零 LLM 依赖（BYOK）。付费解锁：Starter $39/mo 或 Pro $79/mo；也可自由充值钱包额度（微信 ¥1~¥1000 / Creem $1~$200，任意次数）。
---

# vibedollar — 帮你找到正在等你的客户

**你要的客户正在 Reddit 上抱怨、求方案，vibedollar 把他们带给你。**

产品做出来了，但那些正在解决你问题的帖子和评论，你用常规搜索找不到。
输入你的产品描述，vibedollar 返回一批**潜在客户线索**：相关帖子与评论，每条都带作者和"为什么相关"的标注——点进去就能直接触达。

配套 **470+ 真实独立开发案例库**：搜到需求立刻看谁做成过、收入多少、什么打法。

**本服务只提供数据，不做分析** —— 所有分析由你自己的 LLM 完成（BYOK，用户自带模型，零 LLM 依赖）。

## 什么时候用它

| 场景 | 用法 |
|------|------|
| 冷启动获客 | `vibe_reddit` → 一批正在抱怨/求方案的潜在客户，点进帖子直接触达 |
| 验证产品点子 | 先搜需求再写代码：有 N 条强需求信号 → 值得做 |
| 市场调研 / 竞品机会 | `vibe_knowledge` 查类似案例的收入、渠道、打法 |
| 给投资人/团队证明 | `vibe_reddit` 的 report 就是现成的"需求真实性论证" |

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
| `vibe_knowledge` | `product_type, min_revenue, limit` | 查知识库类似案例/渠道/工具链（480+案例）：输入品类（marketplace/saas/ai_tool…）或收入门槛（min_revenue），知识库优先命中；未命中自动全网搜索补充 | 订阅档内可用 / 超出后 $0.05/次 | Header |
| `vibe_reddit` | `product, keywords, max_results` | **找到潜在客户**：输入**产品描述**（推荐）或直接给关键词，返回相关帖子+评论（title/url/subreddit/score/comments/body，评论含作者 + **相关性标注**：为什么像潜在客户）+ **需求论证报告**（论证确实有潜在客户真实存在） | 含在档位额度内 / 超出额度后按 $0.05/条线索扣费 | Header |
| `vibe_discover` | `keywords, subreddit, max_results` | **发现需求**：搜 Reddit 抱怨帖并提炼**用户需求**（每条帖子的 need/pain + 信号强弱 strong/medium/weak）——适合还没做产品、想先看"什么被抱怨/被需要"的场景。输入关键词（可限 subreddit），返回需求列表 | 与 vibe_reddit 同额度（1 帖=1 线索）/ 超出后 $0.05/条 | Header |

> 除 `vibe_register` 外，所有工具通过 HTTP 请求头 `Authorization: Bearer <api_key>` 鉴权，
> **工具参数中不再出现 api_key**（key 不裸奔、不进调用日志）。

## 两个数据工具怎么配合（推荐工作流）

两个工具服务于冷启动的两个不同环节，**从远到近**推进：

| 环节 | 工具 | 回答的问题 | 输出 |
|------|------|-----------|------|
| **验证市场** | `vibe_knowledge` | 这个品类做没做成？天花板多高？谁做成了？（按品类聚合 / 按收入筛案例）| 收入中位数 / 获客渠道 Top / 工具链 Top / 类似案例 / 新案例候选 |
| **找到客户** | `vibe_reddit` | 谁正在抱怨/求方案？怎么触达？（搜 Reddit）| 帖子+评论（作者可见）+ 相关性标注 + 需求论证报告 |

**推荐顺序**：`vibe_knowledge`（验证品类可行 + 看先例）→ `vibe_reddit`（找到真实客户，直接触达）。

**一个核心区别**：只有 `vibe_reddit` 产出**可以直接触达的人**（评论作者）；`vibe_knowledge` 产出**决策信息**（要不要做、怎么做）。预算有限时优先投 `vibe_reddit`。

## 用法示例

```
# 1. 注册（两步: 先发验证码, 验证后发 key; 无需鉴权）
vibe_register(email="founder@example.com")
# → {"ok": true, "status": "pending", "message": "验证码已发送到邮箱", "email": "founder@example.com"}
vibe_verify(email="founder@example.com", code="123456")
# → {"ok": true, "api_key": "vibedollar_ab12...", "credit_usd": 0.0, "tier": "free"}
#   (api_key 同时通过邮件发送到邮箱, 请妥善保存)

# 2. 配置好 Authorization: Bearer <key> 后直接调用，不再传 api_key
# 市场验证: 查类似案例（聚合视图: 收入中位数/渠道Top/工具链Top/TOP3摘要）
# 未订阅 = free 档 0 配额: 每次调用按 $0.05 从钱包扣; 无余额则返回 "Insufficient credit" 引导充值
vibe_knowledge(product_type="saas", limit=5)
# → {"ok": true, "data": {"view": "aggregate", "matched_count": 12, "median_revenue_mrr": 8500,
#     "top_channels": [...], "top_tools": [...], "top_cases": [...]},
#     "cost_usd": 0.05, "quota": {"used": 1, "limit": 0, "reset_in_days": 24}}

# 3. 找到潜在客户: 搜 Reddit（订阅档内免费; 未订阅 free 档 0 线索 → 超量按 $0.05/条线索扣费 从钱包扣;
#    无余额则返回 "Insufficient credit" 引导充值/订阅）
# 方式 A（推荐）: 输入产品描述
vibe_reddit(product="team wiki tool for small teams", max_results=10)
# 方式 B: 直接给搜索关键词
vibe_reddit(keywords="team wiki collaboration", max_results=10)
# → {"ok": true, "data": {"posts": [{title, url, subreddit, score, comments_count, body, comments}, ...],
#     "report": {"summary": "找到 4 个相关讨论、5 条表达需求的评论——潜在客户真实存在",
#                "signal_stats": {"posts_total": 4, "comments_total": 9, "signal_comments": 5,
#                                 "strong_signal_comments": 3, "avg_signal_score": 61.4},
#                "intent_breakdown": [{"category": "pain_point", "label": "痛点抱怨", "count": 3}, ...],
#                "top_subreddits": [{"subreddit": "r/SaaS", "posts": 2}, ...],
#                "top_evidence": [{"post_title": "...", "subreddit": "r/SaaS", "author": "...",
#                                  "comment": "...", "score": 90, "tags": [...]}, ...],
#                "verdict": {"level": "strong", "conclusion": "明确存在真实需求——..."}}},
#     "cost_usd": 0.05, "quota": {"used": 1, "limit": 0, "reset_in_days": 24}}

# 4. 知识库按收入门槛查案例（知识库优先，未命中自动搜索补充；升级订阅后全量明细）
vibe_knowledge(min_revenue=10000, limit=5)
# → {"ok": true, "data": {"view": "aggregate", "matched_count": N, "similar_cases": [...], "search_results": [...], "searched": false}}

# 5. 查余额/tier/配额（key 从 Header 读取）
vibe_balance()
# → {"ok": true, "api_key": "vibedollar_ab12...", "credit_usd": 0.0, "tier": "free",
#     "quota": {"vibe_knowledge": {"used": 1, "limit": 0, "reset_in_days": 24}, ...}}
```

## Agent 使用提示

- **始终先注册再配置 Header**：注册返回的 key 配到客户端请求头（`Authorization: Bearer <key>`），
  未带 Header 会返回 `"Missing API key"`，未注册的 key 返回 `"Unknown API key"`。
- **看 `quota` 块做自我管理**：每次调用响应带 `quota: {used, limit, reset_in_days}`，
  用尽前主动提示用户升级（Starter/Pro）或接受 reddit 超量按“超出额度后按 $0.05/条线索扣费”扣费。
- **聚合视图（未订阅时）**：`vibe_knowledge` 返回统计值 + TOP3 案例摘要（不导出全量明细）；
  升级 Starter/Pro 后获得全量明细（含渠道/工具链/全部案例字段）。
- **检查 `remaining_credit`**：余额不足时 `vibe_reddit` 超量扣费返回 `"Insufficient credit"`。
- **`vibe_reddit` 返回帖子 + 评论（带相关性标注）+ 需求论证报告**：每条帖子和评论都带作者，**每条评论标注为什么像潜在客户**——点进帖子即可触达，这些人就是你的潜在客户。body 截断 500 字符、每条评论截断 300 字符、每帖最多 5 条评论；**报告（report）论证"确实有 N 个潜在客户真实存在"**——信号统计 + 最强需求证据 + 结论（strong/medium/weak），帮你向自己/团队/投资人证明需求真实。
- **输入产品描述即可（推荐）**：`vibe_reddit(product="你的产品一句话")` —— 无需自己找词，直接拿到潜在客户；也可直接给 `keywords`。
- **典型工作流**：vibe_reddit（找到潜在客户：谁在抱怨/求方案 + 为什么相关）→ vibe_knowledge（看同行做成没、收入多少）→ 用你自己的 LLM 综合分析。

## 定价

| 档位 | 价格 | **帮你找到潜在客户**（vibe_reddit 帖子+评论） | 知识库 | 限速 |
|------|------|----------------------------------------|--------|------|
| **Starter** | **$39/mo** | **500 个/月**（帖子+评论+相关性标注+需求论证报告，点进即触达） | 全量明细（limit≤20+筛选） | 60 req/min |
| **Pro** | **$79/mo** | **3000 个/月**（帖子+评论+相关性标注+需求论证报告，点进即触达） | 全量明细（limit≤50） | 120 req/min |
| **Wallet Top-up** | **自由金额**（Creem $1~$200 / 微信 ¥1~¥1000，任意次数） | 不占订阅档位；钱包额度用于 vibe_reddit 超量扣费（超出额度后按 $0.05/条线索扣费） | 无 | 无 |

- **"个"= 潜在客户线索**：1 个帖子或 1 条评论 = 1 线索（发帖人/评论者都是潜在客户，点进帖子即可触达）；线索额度按实际返回的帖子数+评论数消耗，剩余不足时单次自动限制，不会超卖。
- **注册不送额度**：注册获取 API key 后，需选择 Starter/Pro 订阅，或自由充值钱包额度（微信 ¥1~¥1000 / Creem $1~$200，任意次数）用于 vibe_reddit 超量扣费（**超出额度后按 $0.05/条线索扣费**）；另有 **$1 Welcome Credit** 新客福利（每人限一次）。
- **vibe_knowledge**：辅助工具（市场验证），订阅档内可用；超出后按 $0.05/次扣费。
- **订阅升级（Starter/Pro）**：Creem（海外）或微信扫码支付开通（`mcp.vibedollar.net`，支付后自动置档）；**年付 8 折**（后续启用）；**无试用**。
- **自由充值（Wallet Top-up）**：钱包支持自由金额充值（微信 ¥1~¥1000 / Creem $1~$200，任意次数），余额用于 vibe_reddit 超量扣费（超出额度后按 $0.05/条线索扣费）；另保留 $1 Welcome Credit 新客福利（每人限一次）。

## 支付与订阅开通（Agent 工作流）

**用户唯一需要做的动作是「扫码付款」**——注册、下单、生成二维码、确认开通全部由你（Agent）完成。当用户表达升级/充值/付费意图时，按以下流程执行：

### 步骤 1：确认/注册 api_key
- 调 `vibe_balance()` 确认当前账号是否有 api_key 与 tier；报 `"Missing API key"` 则说明未配置 Header
- 若用户还没有 key：调 `vibe_register(email=...)` → 把收到的验证码给用户（用户转发邮箱里的 6 位码）→ 调 `vibe_verify(email, code)` 完成注册拿到 `api_key`
- **不要要求用户自己注册**——注册是你的职责，用户只需要提供 email 和验证码

### 步骤 2：按用户位置选择支付渠道
| 用户位置 | 渠道 | 价格 |
|---------|------|------|
| 海外（默认） | **Creem**（美元卡）| Starter $39/mo / Pro $79/mo / Welcome Credit $1.00 / Wallet Top-up $1~$200（Pay What You Want） |
| 中国大陆 | **微信支付**（人民币）| Starter ¥280.8/mo / Pro ¥568.8/mo / Welcome Credit ¥0.01 / Wallet Top-up ¥1~¥1000 |

### 步骤 3：生成支付入口
- **Creem（海外）**：调 `POST https://mcp.vibedollar.net/creem/checkout`（body: `{"api_key": "<key>", "plan": "starter|pro|welcome_credit|topup", "email": "..."}`）→ 返回 `{"ok": true, "url": "<支付链接>"}` → 把 `url` 发给用户（充值 `plan=topup` 时，用户会在 Creem 页面自行输入金额 $1~$200）。**不要把 api_key 放进 URL**（GET 直链已下线：api_key 进 URL 会落入隧道/访问日志与浏览器历史）
- **微信（国内）**：调 `POST https://mcp.vibedollar.net/pay/native`（body: `{"api_key": "<key>", "email": "...", "tier": "starter|pro|welcome_credit|topup"}`）→ 返回 `code_url` → **把 code_url 生成二维码**（或提示用户用微信扫一扫）→ 发给用户扫码（充值 `tier: "topup"` 时 body 需加 `"amount_cents": <人民币×100>`，如 ¥36 → 3600）

### 步骤 4：用户扫码付款 → 确认开通
- 用户扫码付款后，轮询订单状态：`GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` 或再次调 `vibe_balance()` 确认 tier/credit 已更新
- **支付成功后自动置 tier / 加 credit**（微信回调 / Creem webhook 自动完成，无需人工干预）
- 给用户确认：升级到 Starter（500 线索/月）、升级到 Pro（3000 线索/月），或充值成功（钱包已到账 $X 额度）

### 常见情况处理
- 用户已在别处有 key：直接用那个 key 下单，不重复注册
- **用户自己会用网页**：也可以直接引导用户打开 `https://vibedollar.net/account.html` 自助完成注册/验证/支付全流程（无需 agent 介入）——与上述 Agent 流程等价
- 支付后 tier 未更新：等 1-2 秒重查 `vibe_balance()`；若仍异常，报告 `out_trade_no` 给用户联系 support@vibedollar.net
- 取消订阅：Starter/Pro 到期降级（不立即切断），无需 agent 操作

## 接入方式

MCP 客户端配置示例（**关键：在 headers 里配 `Authorization: Bearer <key>`**）：

```json
{
  "mcpServers": {
    "vibedollar": {
      "type": "http",
      "url": "https://mcp.vibedollar.net/mcp",
      "headers": {
        "Authorization": "Bearer vibedollar_你的key"
      }
    }
  }
}
```

部分客户端（如 Claude Desktop / Cursor）也支持在环境变量或配置里单独声明 headers，
按客户端文档把 `Authorization: Bearer <key>` 配到该 server 的请求头即可。

> 兼容备选：若客户端不允许自定义 `Authorization` 头，也可用 `Api-Key: <key>` 请求头，服务端同样识别。

连接后先 `vibe_register` 注册获取 `api_key`，再把它配到请求头，之后调用数据工具（全部零 LLM 依赖，BYOK）。
