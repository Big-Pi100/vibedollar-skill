# vibedollar 定价 / 支付 / 接入配置（参考 — 低频, 按需加载）

> 何时读本文件：用户问价格 / 升级 / 充值 / 支付后确认开通 / key 找回 / 首次接 MCP。
> 日常用 vibedollar 工具不需要读 —— 调 `vibe_balance()` 即可看领取额度用量。

## 定价

| 档位 | 价格 | **每月可领取线索**（首次领取时计费） | 每日上限 | 限速 |
|------|------|--------------------------------------|----------|------|
| **Free** | 注册即用 | **1,000 条/月** —— 想多快用完都行 | 1,000 条/日 | 5 req/min |
| **Starter** | **$19/mo** | **5,000 条/月**，超出按 **$5/千条** | 1,000 条/日 | 10 req/min |
| **Pro** | **$79/mo** | **30,000 条/月**，超出按 **$3.50/千条** | 3,000 条/日 | 20 req/min |
| **Wallet Top-up** | **自由金额**（Creem $1~$200 / 微信 ¥1~¥1000，任意次数） | 用于**超出月额度后**的领取 | — | — |

- **计费单位 = 你领取的线索**：1 个帖子或 1 条评论 = 1 线索（发帖人/评论者都是潜在客户），**首次领取时计费**；**评分、重复查看、导出全部免费**（服务端按领取记账，可核验）。
- **每日交付上限**：Free/Starter 1,000 条/日、Pro 3,000 条/日；**超出部分顺延次日，永不丢失**（当天只是慢一点，不会重复计费）。
- **超出月额度**：按 **$5/千条**（Starter）或 **$3.50/千条**（Pro）从钱包扣；钱包不足则暂停交付、线索继续保留。Free 档无超额：1,000 条用完请升级。
- **公平使用（不计费）**：我方为账号每日拉取/匹配量设上限（Free 5,000 / Starter 25,000 / Pro 50,000 条），正常使用远不会触及；超出仅顺延次日。
- **不做用量诱导**：订阅多少 sub、多少关键词完全由用户自己的需求决定 —— 我们不会推销用不到的额度，也不靠"解锁"逼升级。
- **订阅升级（Starter/Pro）**：Creem（海外）或微信扫码支付开通（`mcp.vibedollar.net`，支付后自动置档）；**年付 8 折**（后续启用）；**无试用**。

## 支付与订阅开通（Agent 工作流）

**用户唯一需要做的动作是「扫码付款」**——注册、下单、生成二维码、确认开通全部由 Agent 完成。当用户表达升级/充值/付费意图时，按以下流程执行：

### 步骤 1：确认/注册 api_key
- 调 `vibe_balance()` 确认当前账号是否有 api_key 与 tier；报 `"Missing API key"` 则说明未配置 Header
- 若用户还没有 key：调 `vibe_register(email=...)` → 把收到的验证码给用户（用户转发邮箱里的 6 位码）→ 调 `vibe_verify(email, code)` 完成注册拿到 `api_key`
- **不要要求用户自己注册**——注册是 Agent 的职责，用户只需要提供 email 和验证码

### 步骤 2：按用户位置选择支付渠道
| 用户位置 | 渠道 | 价格 |
|---------|------|------|
| 海外（默认） | **Creem**（美元卡）| Starter $19/mo / Pro $79/mo / Wallet Top-up $1~$200（Pay What You Want） |
| 中国大陆 | **微信支付**（人民币）| Starter ¥99/mo / Pro ¥399/mo / Wallet Top-up ¥1~¥1000 |

### 步骤 3：生成支付入口
- **Creem（海外）**：调 `POST https://mcp.vibedollar.net/creem/checkout`（body: `{"api_key": "<key>", "plan": "starter|pro|topup", "email": "..."}`）→ 返回 `{"ok": true, "url": "<支付链接>"}` → 把 `url` 发给用户（充值 `plan=topup` 时，用户会在 Creem 页面自行输入金额 $1~$200）。**不要把 api_key 放进 URL**（GET 直链已下线：api_key 进 URL 会落入访问日志与浏览器历史）
- **微信（国内）**：调 `POST https://mcp.vibedollar.net/pay/native`（body: `{"api_key": "<key>", "email": "...", "tier": "starter|pro|topup"}`）→ 返回 `code_url` → **把 code_url 生成二维码**（或提示用户用微信扫一扫）→ 发给用户扫码（充值 `tier: "topup"` 时 body 需加 `"amount_cents": <人民币×100>`，如 ¥36 → 3600）

### 步骤 4：用户扫码付款 → 确认开通
- 用户扫码付款后，轮询订单状态：`GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` 或再次调 `vibe_balance()` 确认 tier/credit 已更新
- **支付成功后自动置 tier / 加 credit**（微信回调 / Creem webhook 自动完成，无需人工干预）
- 给用户确认（按新口径说清楚）："Starter 已开通：本月 5,000 条领取额度、每日上限 1,000 条，超出按 $5/千条从钱包扣"（Pro 同理：30,000 条 / 3,000 条/日 / $3.50 千条）

### 用量怎么向用户解释（新口径）
- 读 `vibe_balance()` → `claim_quota` 块：`month_used / month_limit`、`daily_used / daily_cap`、`wallet_usd`、`over_price_per_1k`
- 读 `vibe_sub_health(subscription_id)` → `assessment` 块：当前搜索面能否填满额度（`projected_items_month` vs `commitment_remaining`）与 `gap_reason`（`supply_ceiling` / `word_face` / `capacity` / `collecting` / `no_data` / `ok`）。若归因是供给顶，**加 sub 远比加词有效**（加词只是重新归因已有语料）
- 用户看到"今日上限已满"时说明：**这是节流不是额度**，次日 00:00 自动继续，不丢货、不用充值

### 常见情况处理
- 用户已在别处有 key：直接用那个 key 下单，不重复注册
- **用户自己会用网页**：也可以直接引导用户打开 `https://vibedollar.net/account.html` 自助完成注册/验证/支付全流程（无需 agent 介入）——与上述 Agent 流程等价
- 支付后 tier 未更新：等 1-2 秒重查 `vibe_balance()`；若仍异常，报告 `out_trade_no` 给用户联系 support@vibedollar.net
- 取消订阅：Starter/Pro 到期降级（不立即切断），无需 agent 操作

## 接入方式（MCP 客户端配置）

MCP 客户端配置示例（**关键：在 headers 里配 `Authorization: Bearer <key>`**）：

```json
{
  "mcpServers": {
    "vibedollar": {
      "type": "http",
      "url": "https://mcp.vibedollar.net/mcp",
      "headers": { "Authorization": "Bearer <your-key>" }
    }
  }
}
```

部分客户端（Claude Desktop / Cursor）支持通过 env/config 配 headers，按各客户端文档把
`Authorization: Bearer <key>` 配到 server headers。备用 header：`Api-Key: <key>`。

### 连接后首次流程
连接 → `vibe_register` → 把 key 配进 header → 调数据工具（Reddit 采集/匹配/状态是
vibedollar 的；判真与词表调优是你的 —— 见 SKILL.md **Agent 决策循环**）。

### 协议（本地脚本用，如 scripts/mcp.py）
MCP Streamable HTTP：`POST {url}/mcp`，headers `Accept: application/json,
text/event-stream`；session 经 `Mcp-Session-Id` 维持；`tools/call` 前先 `initialize`。
纯 stdlib 客户端见 `scripts/mcp.py`。
