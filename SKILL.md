---
name: vibedollar
description: >-
  vibedollar 帮独立开发者找到第一批客户——基于你的产品描述，返回 Reddit 上正在抱怨/求方案的
  潜在客户线索（帖子+评论+相关性标注+需求论证报告），支持单次检索与订阅持续监控。
  远程托管免部署，零配置即用（含相关性/需求分析，服务端完成）。付费解锁：Starter $39/mo 或 Pro $79/mo；也可自由充值钱包额度（微信 ¥1~¥1000 / Creem $1~$200，任意次数）。
---

# vibedollar — 帮你找到正在等你的客户

**你要的客户正在 Reddit 上抱怨、求方案，vibedollar 把他们带给你。**

产品做出来了，但那些正在解决你问题的帖子和评论，你用常规搜索找不到。
输入你的产品描述，vibedollar 返回一批**潜在客户线索**：相关帖子与评论，每条都带作者和"为什么相关"的标注——点进去就能直接触达。

**相关性/需求分析已含在服务里** —— 每条线索标注为什么相关，附需求论证报告，无需你配置任何模型。

## 什么时候用它

| 场景 | 用法 |
|------|------|
| 冷启动获客 | `vibe_subscribe` → 系统持续跟踪，线索自动积累，点进帖子直接触达潜在客户 |
| 验证产品点子 | 订阅后看积累的线索：有 N 条强需求信号 → 值得做 |
| 持续获客 | `vibe_subscribe` → 系统持续跟踪，线索自动积累，随时 `vibe_leads` 领取 |
| 给投资人/团队证明 | 积累线索的 relevance 标注就是现成的"需求真实性论证" |

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
| `vibe_reddit` | `product, keywords, max_results` | **已下线**（保留兼容）——实时检索由订阅模式取代，调用返回引导文案指向 `vibe_subscribe` | — | Header |
| `vibe_subscribe` | `product` | **订阅持续监控**：输入产品描述，系统持续跟踪，线索自动积累（关键词/来源由系统管理，无需你操心） | 领取线索时扣档位额度 | Header |
| `vibe_leads` | `subscription_id, limit` | **领取订阅线索**：秒回已积累的潜在客户线索（不触发实时搜索）；领取后计入月配额 | 扣档位额度 | Header |
| `vibe_list_subs` | `（无）` | 查看我的订阅列表及每条待领取线索数 | 免费 | Header |
| `vibe_unsubscribe` | `subscription_id` | 取消订阅（已积累的线索保留） | 免费 | Header |
| `vibe_mark_leads` | `lead_ids, outcome` | 标记线索结果（valid 有效 / invalid 无效 / contacted 已触达）——帮你跟踪线索跟进质量 | 免费 | Header |
| `vibe_get_delivered` | `lead_id` | 单条已交付线索详情（回访用） | 免费 | Header |
| `vibe_delivered` | `limit, offset` | 已交付线索列表（回访历史客户） | 免费 | Header |

> 除 `vibe_register` 外，所有工具通过 HTTP 请求头 `Authorization: Bearer <api_key>` 鉴权，
> **工具参数中不再出现 api_key**（key 不裸奔、不进调用日志）。

## 获客方式（订阅即所有，2026-08-17 起纯订阅模式）

vibedollar 只提供**订阅模式**——实时检索（vibe_reddit）已下线，因为它受客户端超时窗口限制，无法保证稳定交付；订阅模式由后台管线运行，无超时压力，线索质量更高（更多搜索时间 + 失败源重试）。

| 方式 | 工具 | 适用 | 输出 |
|------|------|------|------|
| **订阅监控** | `vibe_subscribe` + `vibe_leads` | 所有场景：验证需求 / 持续获客 / 冷启动 | 线索自动积累，随时秒回领取 |

**推荐流程**：`vibe_subscribe(product)` 订阅你的产品 → 后台持续分析 Reddit，线索自动积累 → `vibe_leads` 随时领取。预算有限时，领取的线索即含相关性标注，可直接验证需求。

## 订阅模式（持续监控，不用反复调用）

不想每次手动查询？订阅一个产品，系统会**持续跟踪**，线索自动积累，你随时查看即可：

```
vibe_subscribe(product="team wiki tool for small teams")   # 创建订阅（只需产品描述）
    → {"ok": true, "subscription_id": 12, "message": "订阅创建成功, 后台正在跟踪..."}
    ↓ 系统持续跟踪，线索积累（无需你操作）
vibe_list_subs()                                          # 查看订阅状态 + 待领取数
    → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "...", "new_leads": 7}]}}
    ↓
vibe_leads(subscription_id=12, limit=10)                  # 领取积累的线索（秒回）
    → {"ok": true, "data": {"posts": [{"title": "...", "url": "...", "subreddit": "...", "score": 90}], "count": 7}}
```

**适用场景**：
- 产品定位已确定，希望**持续获取**新出现的潜在客户，而不是想起来才查一次
- 关键词/来源不用自己维护——订阅产品描述即可，系统管理搜索方向
- 领取线索才消耗配额，订阅本身不额外收费

**取消订阅**用 `vibe_unsubscribe`（已积累线索保留）。

## 用法示例

```
# 1. 注册（两步: 先发验证码, 验证后发 key; 无需鉴权）
vibe_register(email="founder@example.com")
# → {"ok": true, "status": "pending", "message": "验证码已发送到邮箱", "email": "founder@example.com"}
vibe_verify(email="founder@example.com", code="123456")
# → {"ok": true, "api_key": "vibedollar_ab12...", "credit_usd": 0.0, "tier": "free"}
#   (api_key 同时通过邮件发送到邮箱, 请妥善保存)

# 2. 配置好 Authorization: Bearer <key> 后直接调用，不再传 api_key
# 订阅产品 → 后台持续跟踪 → 领取线索（订阅档内免费; free 档 0 线索 → 超量按 $0.05/条线索扣费 从钱包扣;
#    无余额则返回 "Insufficient credit" 引导充值/订阅）
vibe_subscribe(product="team wiki tool for small teams")
# → {"ok": true, "subscription_id": 12, "product": "team wiki tool for small teams",
#     "message": "订阅创建成功, 后台正在搜索线索。几分钟后用 vibe_leads 查看。"}
#    ↓ 后台持续分析 Reddit, 线索自动积累 (无需你操作)
vibe_list_subs()
# → {"ok": true, "data": {"subscriptions": [{"id": 12, "product": "team wiki tool for small teams", "new_leads": 7}]}}
vibe_leads(subscription_id=12, limit=10)
# → {"ok": true, "data": {"posts": [{"title": "...", "url": "...", "subreddit": "...", "score": 90, "reason": "..."}], "count": 7}}

# 3. 查余额/tier/配额（key 从 Header 读取）
vibe_balance()
# → {"ok": true, "api_key": "vibedollar_ab12...", "credit_usd": 0.0, "tier": "free",
#     "quota": {...}}
```

## Agent 使用提示

- **始终先注册再配置 Header**：注册返回的 key 配到客户端请求头（`Authorization: Bearer <key>`），
  未带 Header 会返回 `"Missing API key"`，未注册的 key 返回 `"Unknown API key"`。
- **看 `quota` 块做自我管理**：每次调用响应带 `quota: {used, limit, reset_in_days}`，
  用尽前主动提示用户升级（Starter/Pro）或接受 reddit 超量按“超出额度后按 $0.05/条线索扣费”扣费。
- **检查 `remaining_credit`**：余额不足时订阅线索超量扣费返回 `"Insufficient credit"`。
- **`vibe_leads` 返回帖子 + 评论（带相关性标注）**：每条线索都带作者和**相关性标注：为什么像潜在客户**——点进帖子即可触达，这些人就是你的潜在客户。
- **订阅模式**：`vibe_subscribe(product)` 创建持续监控 → `vibe_list_subs()` 看状态 → `vibe_leads(subscription_id)` 秒回领取；`vibe_unsubscribe` 取消（线索保留）。
- **典型工作流**：`vibe_subscribe`（订阅产品，后台持续分析）→ `vibe_leads` 领取线索（验证需求 + 找到第一批客户）→ 用你自己的 LLM 综合分析。

## 定价

| 档位 | 价格 | **帮你找到潜在客户**（订阅线索） | 限速 |
|------|------|----------------------------------------|------|
| **Starter** | **$39/mo** | **800 个/月**（帖子+评论+相关性标注，点进即触达；含订阅模式领取） | 60 req/min |
| **Pro** | **$79/mo** | **3000 个/月**（帖子+评论+相关性标注，点进即触达；含订阅模式领取） | 120 req/min |
| **Wallet Top-up** | **自由金额**（Creem $1~$200 / 微信 ¥1~¥1000，任意次数） | 不占订阅档位；钱包额度用于订阅线索超量扣费（超出额度后按 $0.05/条线索扣费） | 无 |

- **"个"= 潜在客户线索**：1 个帖子或 1 条评论 = 1 线索（发帖人/评论者都是潜在客户，点进帖子即可触达）；线索额度按实际领取的帖子数+评论数消耗，剩余不足时单次自动限制，不会超卖。**订阅模式（`vibe_leads` 领取）计费**，领取时才计费，订阅本身不额外收费。
- **注册不送额度**：注册获取 API key 后，需选择 Starter/Pro 订阅，或自由充值钱包额度（微信 ¥1~¥1000 / Creem $1~$200，任意次数）用于订阅线索超量扣费（**超出额度后按 $0.05/条线索扣费**）；另有 **$1 Welcome Credit** 新客福利（每人限一次）。
- **订阅升级（Starter/Pro）**：Creem（海外）或微信扫码支付开通（`mcp.vibedollar.net`，支付后自动置档）；**年付 8 折**（后续启用）；**无试用**。
- **自由充值（Wallet Top-up）**：钱包支持自由金额充值（微信 ¥1~¥1000 / Creem $1~$200，任意次数），余额用于订阅线索超量扣费（超出额度后按 $0.05/条线索扣费）；另保留 $1 Welcome Credit 新客福利（每人限一次）。

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

连接后先 `vibe_register` 注册获取 `api_key`，再把它配到请求头，之后直接调用数据工具（相关性/需求分析服务端完成，开箱即用）。
