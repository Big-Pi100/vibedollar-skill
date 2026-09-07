# vibedollar 定价 / 支付 / 接入配置（参考 — 低频, 按需加载）

> 何时读本文件：用户问价格 / 升级 / 充值 / 支付后确认开通 / key 找回 / 首次接 MCP。
> 日常用 vibedollar 工具不需要读 —— 调 `vibe_balance()` 即可看配额。

## 定价

| 档位 | 价格 | **帮你找到潜在客户**（评分通过的交付） | 限速 |
|------|------|----------------------------------------|------|
| **Free** | 注册即用 | **30 个/月**（demo 试用：1 个订阅，单次领 20 条；超额走钱包 $0.05/条）| 30 req/min |
| **Starter** | **$39/mo** | **800 个/月**（评分通过的线索才计费；候选免费，每批取完评分后解锁下一批；单次领 30 条）| 60 req/min |
| **Pro** | **$79/mo** | **3000 个/月**（评分通过的线索才计费；候选免费，每批取完评分后解锁下一批；单次领 50 条）| 120 req/min |
| **Wallet Top-up** | **自由金额**（Creem $1~$200 / 微信 ¥1~¥1000，任意次数） | 不占订阅档位；**配额用完后续用钱包按 $0.05/条扣费**（按效果付费延伸）| 无 |

- **"个"= 评分通过的线索**：1 个帖子或 1 条评论 = 1 线索（发帖人/评论者都是潜在客户）；**候选免费**，`vibe_submit_score` 判定 `relevant` 才计 1 配额，剩余不足时自动限制，不会超卖。**按效果计费**：没评上不花钱。
- **配额用完后续用**：月配额用完后，评分通过的线索自动从钱包扣 $0.05/条（余额不足会提示充值）；free 档每月有 30 条免费额度，超额同样走钱包。
- **注册不送额度**：注册获取 API key 后，需选择 Starter/Pro 订阅解锁交付额度，或自由充值钱包额度；另有 **$1 Welcome Credit** 新客福利（每人限一次）。
- **订阅升级（Starter/Pro）**：Creem（海外）或微信扫码支付开通（`mcp.vibedollar.net`，支付后自动置档）；**年付 8 折**（后续启用）；**无试用**。
- **自由充值（Wallet Top-up）**：钱包支持自由金额充值（微信 ¥1~¥1000 / Creem $1~$200，任意次数），余额用于订阅/交付增值场景；另保留 $1 Welcome Credit 新客福利（每人限一次）。

## 支付与订阅开通（Agent 工作流）

**用户唯一需要做的动作是「扫码付款」**——注册、下单、生成二维码、确认开通全部由 Agent 完成。当用户表达升级/充值/付费意图时，按以下流程执行：

### 步骤 1：确认/注册 api_key
- 调 `vibe_balance()` 确认当前账号是否有 api_key 与 tier；报 `"Missing API key"` 则说明未配置 Header
- 若用户还没有 key：调 `vibe_register(email=...)` → 把收到的验证码给用户（用户转发邮箱里的 6 位码）→ 调 `vibe_verify(email, code)` 完成注册拿到 `api_key`
- **不要要求用户自己注册**——注册是 Agent 的职责，用户只需要提供 email 和验证码

### 步骤 2：按用户位置选择支付渠道
| 用户位置 | 渠道 | 价格 |
|---------|------|------|
| 海外（默认） | **Creem**（美元卡）| Starter $39/mo / Pro $79/mo / Welcome Credit $1.00 / Wallet Top-up $1~$200（Pay What You Want） |
| 中国大陆 | **微信支付**（人民币）| Starter ¥280.8/mo / Pro ¥568.8/mo / Welcome Credit ¥0.01 / Wallet Top-up ¥1~¥1000 |

### 步骤 3：生成支付入口
- **Creem（海外）**：调 `POST https://mcp.vibedollar.net/creem/checkout`（body: `{"api_key": "<key>", "plan": "starter|pro|welcome_credit|topup", "email": "..."}`）→ 返回 `{"ok": true, "url": "<支付链接>"}` → 把 `url` 发给用户（充值 `plan=topup` 时，用户会在 Creem 页面自行输入金额 $1~$200）。**不要把 api_key 放进 URL**（GET 直链已下线：api_key 进 URL 会落入访问日志与浏览器历史）
- **微信（国内）**：调 `POST https://mcp.vibedollar.net/pay/native`（body: `{"api_key": "<key>", "email": "...", "tier": "starter|pro|welcome_credit|topup"}`）→ 返回 `code_url` → **把 code_url 生成二维码**（或提示用户用微信扫一扫）→ 发给用户扫码（充值 `tier: "topup"` 时 body 需加 `"amount_cents": <人民币×100>`，如 ¥36 → 3600）

### 步骤 4：用户扫码付款 → 确认开通
- 用户扫码付款后，轮询订单状态：`GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` 或再次调 `vibe_balance()` 确认 tier/credit 已更新
- **支付成功后自动置 tier / 加 credit**（微信回调 / Creem webhook 自动完成，无需人工干预）
- 给用户确认：升级到 Starter（800 线索/月）、升级到 Pro（3000 线索/月），或充值成功（钱包已到账 $X 额度）

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
vibedollar 的；判真与词表调优是你的 —— 见 SKILL.md **交付健康管理**）。

### 协议（本地脚本用，如 scripts/mcp.py）
MCP Streamable HTTP：`POST {url}/mcp`，headers `Accept: application/json,
text/event-stream`；session 经 `Mcp-Session-Id` 维持；`tools/call` 前先 `initialize`。
纯 stdlib 客户端见 `scripts/mcp.py`。
