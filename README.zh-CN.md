# vibedollar — 帮你找到正在等你的客户

> **Reddit 上正在抱怨、求方案的潜在客户，vibedollar 把他们带给你。**

基于你的产品描述，vibedollar **持续抓取** Reddit 上的潜在客户线索（帖子+评论，含作者与正文），你的 agent 用自己的 LLM 判断相关性，**评分通过的才计费**（按效果付费）。

- [English README](README.md)
- [SKILL (English)](SKILL.md) · [SKILL (中文)](SKILL.zh-CN.md)

---

## 什么时候用它

| 场景 | 用法 |
|------|------|
| 冷启动获客 | `vibe_subscribe` → 系统持续跟踪，线索自动积累，点进帖子直接触达潜在客户 |
| 验证产品点子 | 订阅后看积累的线索：有 N 条强需求信号 → 值得做 |
| 持续获客 | `vibe_subscribe` → `vibe_leads` 领候选（免费）→ 评分 → 通过才计费 |
| 给投资人/团队证明 | 积累的线索（你评分确认相关的）就是现成的"需求真实性论证" |

**核心商业模式：按效果付费** —— 候选线索免费，你（你的 agent）评分判断相关性，`relevant` 的才计费（1 条 = 1 配额）。没评上的不花钱。

---

## MCP 工具

| 工具 | 能干什么 | 成本 |
|:-----|:---------|:-----|
| `vibe_register` / `vibe_verify` | 两步注册获取 API key | 免费 |
| `vibe_balance` | 查余额 / tier / 配额余量 | 免费 |
| `vibe_subscribe` | 订阅产品（输入描述，后台持续抓取候选） | 免费 |
| `vibe_leads` | 领取候选线索（含作者/正文/系统参考分） | **免费** |
| `vibe_submit_score` | 评分回传：`relevant` 计 1 配额进交付，`irrelevant` 回灌优化 | **通过才扣** |
| `vibe_score_discuss` | 查看/回应你与系统参考评分的分歧（标准对齐） | 免费 |
| `vibe_list_subs` / `vibe_unsubscribe` | 订阅管理 | 免费 |
| `vibe_delivered` / `vibe_get_delivered` | 已交付线索（回访） | 免费 |
| `vibe_mark_leads` | 标记线索结果（valid/contacted） | 免费 |
| `vibe_recover_key` / `vibe_recover_verify` | 找回 API key（邮箱验证后发到邮箱）| 免费 |

**计费说明**：候选线索**免费**；`vibe_submit_score` 判定 `relevant` 的候选计 1 配额/条并进交付列表，`irrelevant` 不计费（回灌优化，推送越来越准）。每批候选需全部评分后再取下一批。另有 **$1 Welcome Credit** 新客福利（每人限一次）。

---

## 快速开始

1. **连接服务**（远程托管，无需本地部署）：在 MCP 客户端添加端点 `https://mcp.vibedollar.net/mcp`
2. **注册获取 API key**（两步）：
   ```
   vibe_register(email="you@example.com")   # 发送 6 位邮箱验证码
   vibe_verify(email="you@example.com", code="123456")  # 验证码验证, 返回 api_key
   ```
   API key 同时通过邮件发送到你的邮箱。付费解锁：订阅 Starter/Pro，或自由充值钱包（微信 ¥1~¥1000 / Creem $1~$200）；另有 **$1 Welcome Credit** 新客福利。
3. **配置鉴权 Header**：`Authorization: Bearer <key>`（部分客户端不支持自定义 Authorization 时用 `Api-Key: <key>`）
4. **查余额/配额**：`vibe_balance()`（key 自动从请求头读取）
5. **网页自助注册**：`https://vibedollar.net/account.html`（注册/验证/支付全流程）

---

## 推荐流程

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "订阅创建成功, 后台正在跟踪..."}
vibe_list_subs()                          # 查看订阅状态 + 待领取数
vibe_leads(subscription_id=12, limit=10)  # 免费领取候选
    → {"id": 1, "title": "...", "url": "...", "score": 90, "reason": "...", ...}
vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "直接求方案"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "与产品无关"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}
```

规则：
- **候选免费**：`vibe_leads` 不扣任何配额
- **通过才计费**：`verdict="relevant"` 扣 1 配额/条，计入交付列表（`vibe_delivered` 可查）
- **不相关也请回传**（`irrelevant`）：这是系统学习你评价标准的方式，回传越多推送越准
- 每条候选只能评分一次（重复回传会被拒绝）
- 候选的 `score` 是系统参考分（仅供参考，以你的判断为准）
- **先处理再取下一批**：已领取候选全部评分后解锁下一批；未处理完再次领取会返回待处理列表（id 可找回，不会锁死订阅）；7 天未评分自动过期释放

---

## 定价

| 档位 | 价格 | **帮你找到潜在客户**（评分通过的交付） | 限速 |
|:-----|:-----|:----------------------------------------|:-----|
| **Free** | 注册即用 | **30 个/月**（demo：1 个订阅，单次领 20 条；超额走钱包 $0.05/条）| 30 req/min |
| **Starter** | **$39/mo** | **800 个/月**（评分通过才计费；候选免费，每批取完评分后解锁下一批；单次领 30 条）| 60 req/min |
| **Pro** | **$79/mo** | **3000 个/月**（评分通过才计费；候选免费；单次领 50 条）| 120 req/min |
| **钱包充值** | 自由金额（Creem $1~$200 / 微信 ¥1~¥1000） | 配额用完后按 **$0.05/条** 续用 | 无 |

- **"个" = 评分通过的线索**：1 个帖子或 1 条评论 = 1 线索（发帖人/评论者都是潜在客户）；候选免费，`relevant` 才计 1 配额，剩余不足自动限制，不会超卖。
- **配额用完后续用**：月配额用完后自动从钱包扣 $0.05/条（余额不足提示充值）；free 档每月 30 条免费额度，超额同样走钱包。
- **注册不送额度**：注册拿 key 后需订阅 Starter/Pro 解锁交付额度，或充值钱包；另有 $1 Welcome Credit 新客福利（每人限一次）。
- **订阅升级**：Creem（海外）或微信扫码支付开通，支付后自动置档；**年付 8 折**（后续启用）；**无试用**。

---

## 支付与订阅开通（Agent 工作流）

**用户唯一需要做的动作是「扫码付款」**——注册、下单、生成二维码、确认开通全部由你（Agent）完成。

1. **确认/注册 api_key**：`vibe_balance()` 确认 → 未注册则 `vibe_register(email)` → 用户给验证码 → `vibe_verify` 拿 key。**不要要求用户自己注册**。
2. **按用户位置选择支付渠道**：
   | 用户位置 | 渠道 | 价格 |
   |---------|------|------|
   | 海外（默认）| **Creem**（美元卡）| Starter $39/mo / Pro $79/mo / Welcome Credit $1 / Top-up $1~$200 |
   | 中国大陆 | **微信支付**（人民币）| Starter ¥280.8/mo / Pro ¥568.8/mo / Welcome Credit ¥0.01 / Top-up ¥1~¥1000 |
3. **生成支付入口**：
   - **Creem**：`POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|welcome_credit|topup", "email": "..."}` → `{"url": "<支付链接>"}` → 发链接给用户。**不要把 api_key 放进 URL**。
   - **微信**：`POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|welcome_credit|topup"}` → `code_url` → 生成二维码给用户扫。充值需加 `"amount_cents": <人民币×100>`。
4. **用户付款 → 确认开通**：轮询 `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` 或重查 `vibe_balance()`——微信回调/Creem webhook 自动置 tier/加 credit。

常见情况：
- 用户已有 key → 直接用，不重复注册
- 用户会用网页 → 引导打开 `https://vibedollar.net/account.html` 自助完成（等价流程）
- 支付后 tier 未更新 → 等 1-2 秒重查；仍异常报告 `out_trade_no` 联系 support@vibedollar.net
- 取消订阅：Starter/Pro 到期降级（不立即切断），无需 agent 操作

---

## 接入方式

```json
{
  "mcpServers": {
    "vibedollar": {
      "type": "http",
      "url": "https://mcp.vibedollar.net/mcp",
      "headers": {
        "Authorization": "Bearer <你的key>"
      }
    }
  }
}
```

部分客户端（Claude Desktop / Cursor）支持在环境变量或配置里声明 headers——按客户端文档配置即可。兼容备选：`Api-Key: <key>` 请求头。

连接后先 `vibe_register` 注册获取 key，配到请求头，之后直接调用数据工具（线索抓取与搜索方向优化由我们完成，你负责评分判断）。

---

## 当前状态（2026-08-21）

- **v3.1 用户评分模式**：候选免费 → 你的 agent 评分 → `relevant` 才计费（按效果付费）
- **后台管线**：订阅产品后持续抓取 Reddit，候选自动积累
- **反馈闭环**：你的评分（含不相关）回灌优化推送；分歧可查看对齐（标准校准）
- **防滥用**：候选批次解锁制 + 已领取校验 + 一致性护栏
