# vibedollar — 帮你找到正在等你的客户

> **Reddit 上正在抱怨、求方案的潜在客户，vibedollar 把他们带给你。**

基于你的产品描述，vibedollar **持续抓取** Reddit 上的潜在客户线索（帖子+评论，含作者与正文）。线索在你**首次领取**时计费；用你自己的 LLM 评分是**免费**的。

- [English README](README.md)
- [SKILL (English)](SKILL.md) · [SKILL (中文)](SKILL.zh-CN.md)

---

## 什么时候用它

| 场景 | 用法 |
|------|------|
| 冷启动获客 | `vibe_subscribe` → 系统持续跟踪，线索自动积累，点进帖子直接触达潜在客户 |
| 验证产品点子 | 订阅后看积累的线索：有 N 条强需求信号 → 值得做 |
| 持续获客 | `vibe_subscribe` → `vibe_leads` 领取线索（按领取计费）→ 评分 → 触达 |
| 给投资人/团队证明 | 积累的线索（你已领取确认的）就是现成的"需求真实性论证" |

**核心商业模式：为你领取的线索付费**。线索在**首次领取**时计费；评分、重复查看、导出全部免费。计费由服务端按领取记账，无需你自报，也不会重复计费。

---

## MCP 工具

| 工具 | 能干什么 | 成本 |
|:-----|:---------|:-----|
| `vibe_register` / `vibe_verify` | 两步注册获取 API key | 免费 |
| `vibe_balance` | 查余额 / tier / 本月领取额度与每日上限 | 免费 |
| `vibe_subscribe` | 订阅产品（输入描述，后台持续抓取候选） | 免费 |
| `vibe_leads` | 领取线索（含作者/正文/系统参考分 + `billing` 记账块） | **按领取条数计费** |
| `vibe_submit_score` | 评分回传：`relevant` 进交付列表，`irrelevant` 回灌优化 | **免费** |
| `vibe_score_discuss` | 查看/回应你与系统参考评分的分歧（标准对齐） | 免费 |
| `vibe_list_subs` / `vibe_unsubscribe` | 订阅管理 | 免费 |
| `vibe_delivered` / `vibe_get_delivered` | 已交付线索（回访） | 免费 |
| `vibe_mark_leads` | 标记线索结果（valid/contacted） | 免费 |
| `vibe_recover_key` / `vibe_recover_verify` | 找回 API key（邮箱验证后发到邮箱）| 免费 |

**计费说明**：线索在**首次领取**时计费（Free 1,000/月 · Starter 5,000/月，超出 $5/千条 · Pro 30,000/月，超出 $3.50/千条）；**评分、重复查看、导出免费**。每日交付上限（Free/Starter 1,000、Pro 3,000）超出部分顺延次日，永不丢失。

---

## 快速开始

1. **连接服务**（远程托管，无需本地部署）：在 MCP 客户端添加端点 `https://mcp.vibedollar.net/mcp`
2. **注册获取 API key**（两步）：
   ```
   vibe_register(email="you@example.com")   # 发送 6 位邮箱验证码
   vibe_verify(email="you@example.com", code="123456")  # 验证码验证, 返回 api_key
   ```
   API key 同时通过邮件发送到你的邮箱。解锁领取额度：订阅 Starter/Pro，或自由充值钱包（微信 ¥1~¥1000 / Creem $1~$200）。Free 档本身已含每月 1,000 条。
3. **配置鉴权 Header**：`Authorization: Bearer <key>`（部分客户端不支持自定义 Authorization 时用 `Api-Key: <key>`）
4. **查余额/额度**：`vibe_balance()`（key 自动从请求头读取，返回 `claim_quota` 用量块）
5. **网页自助注册**：`https://vibedollar.net/account.html`（注册/验证/支付全流程）

---

## 推荐流程

```
vibe_subscribe(product="team wiki tool for small teams")
    → {"ok": true, "subscription_id": 12, "message": "订阅创建成功, 后台正在跟踪..."}
vibe_list_subs()                          # 查看订阅状态 + 待领取数
vibe_leads(subscription_id=12, limit=10)  # 领取 10 条（按领取计费）
    → {"id": 1, "title": "...", "url": "...", "score": 90, "reason": "...", ...,
       "billing": {"claimed_batch": 10, "free_items": 10, "charge_usd": 0.0,
                   "claimed_this_month": 10, "claimed_quota": 5000,
                   "daily_used": 10, "daily_cap": 1000}}
vibe_submit_score(scores=[
    {"id": 1, "verdict": "relevant",   "score": 90, "reason": "直接求方案"},
    {"id": 2, "verdict": "irrelevant", "score": 10, "reason": "与产品无关"},
])
    → {"ok": true, "passed": 1, "rejected": 1, "quota_used": 1, "quota_limit": 3000}  # 评分免费
```

规则：
- **线索在你首次领取时计费**：`vibe_leads` 返回 `billing` 块（本批条数、免费/计费拆分、扣费、本月用量、每日上限）
- **评分免费**：`verdict="relevant"` 把线索移入交付列表（`vibe_delivered` 可查）；`irrelevant` 回灌优化
- **不相关也请回传**（`irrelevant`）：这是系统学习你评价标准的方式，回传越多推送越准
- 每条线索只能评分一次（重复回传会被拒绝）
- 线索的 `score` 是系统参考分（仅供参考，以你的判断为准）
- **每日上限**：Free/Starter 1,000 条、Pro 3,000 条；超出部分次日自动继续，不丢货
- 已领取未评分线索会带 id 返回（不会锁死订阅）；7 天未评分自动过期释放

---

## 定价

| 档位 | 价格 | **每月可领取线索**（首次领取时计费） | 每日上限 | 限速 |
|:-----|:-----|:--------------------------------------|:---------|:-----|
| **Free** | 注册即用 | **1,000 条/月** —— 想多快用完都行 | 1,000 条/日 | 5 req/min |
| **Starter** | **$19/mo** | **5,000 条/月**，超出按 **$5/千条** | 1,000 条/日 | 10 req/min |
| **Pro** | **$79/mo** | **30,000 条/月**，超出按 **$3.50/千条** | 3,000 条/日 | 20 req/min |
| **钱包充值** | 自由金额（Creem $1~$200 / 微信 ¥1~¥1000） | 用于**超出月额度后**的领取 | — | — |

- **计费单位 = 你领取的线索**：1 个帖子或 1 条评论 = 1 线索（发帖人/评论者都是潜在客户），**首次领取时计费**；评分、重复查看、导出免费。
- **每日交付上限**：Free/Starter 1,000 条/日、Pro 3,000 条/日；**超出顺延次日，永不丢失**（只是当天慢一点，不会重复计费）。
- **超出月额度**：按 $5/千条（Starter）或 $3.50/千条（Pro）从钱包扣；钱包不足则暂停交付、线索保留。Free 无超额——1,000 条用完请升级。
- **公平使用（不计费）**：我方为账号每日拉取/匹配量设上限（Free 5,000 / Starter 25,000 / Pro 50,000 条），正常使用远不会触及；超出仅顺延次日。
- **不做用量诱导**：订阅多少 sub、多少关键词完全由你的需求决定——我们不会推销用不到的额度，也不靠"解锁"逼升级。
- **订阅升级**：Creem（海外）或微信扫码支付开通，支付后自动置档；**年付 8 折**（后续启用）；**无试用**。

---

## 支付与订阅开通（Agent 工作流）

**用户唯一需要做的动作是「扫码付款」**——注册、下单、生成二维码、确认开通全部由你（Agent）完成。

1. **确认/注册 api_key**：`vibe_balance()` 确认 → 未注册则 `vibe_register(email)` → 用户给验证码 → `vibe_verify` 拿 key。**不要要求用户自己注册**。
2. **按用户位置选择支付渠道**：
   | 用户位置 | 渠道 | 价格 |
   |---------|------|------|
   | 海外（默认）| **Creem**（美元卡）| Starter $19/mo / Pro $79/mo / Top-up $1~$200 |
   | 中国大陆 | **微信支付**（人民币）| Starter ¥136.8/mo / Pro ¥568.8/mo / Top-up ¥1~¥1000 |
3. **生成支付入口**：
   - **Creem**：`POST https://mcp.vibedollar.net/creem/checkout` `{"api_key": "<key>", "plan": "starter|pro|topup", "email": "..."}` → `{"url": "<支付链接>"}` → 发链接给用户。**不要把 api_key 放进 URL**。
   - **微信**：`POST https://mcp.vibedollar.net/pay/native` `{"api_key": "<key>", "email": "...", "tier": "starter|pro|topup"}` → `code_url` → 生成二维码给用户扫。充值需加 `"amount_cents": <人民币×100>`。
4. **用户付款 → 确认开通**：轮询 `GET https://mcp.vibedollar.net/pay/orders/<out_trade_no>` 或重查 `vibe_balance()`——微信回调/Creem webhook 自动置 tier/加 credit。确认话术按新口径说清（"Starter 已开通：本月 5,000 条领取额度、每日 1,000 条，超出按 $5/千条从钱包扣"）。

常见情况：
- 用户已有 key → 直接用，不重复注册
- 用户会用网页 → 引导打开 `https://vibedollar.net/account.html` 自助完成（等价流程）
- 支付后 tier 未更新 → 等 1-2 秒重查；仍异常报告 `out_trade_no` 联系 support@vibedollar.net
- 用户看到"今日上限已满" → 说明这是**节流不是额度**：次日 00:00 自动继续，不丢货、无需充值
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

## 当前状态（2026-09-10）

- **按领取计费（2026-09-10）**：线索在**首次领取**时计费；评分、重复查看、导出免费（服务端按领取记账，可核验）
- **数据服务架构**：服务端 = 纯数据/状态层（采集 + 匹配 + SQL 状态迁移）；评分与词表调优归你（你的 LLM）
- **2026-09-05 工具扩展**：新增 9 个管理工具——keywords/keyword_add/keyword_remove（词表管理）、sd_update（供需判定口径）、sub_health/opt_log（交付健康驱动调优）、rejected/recover_lead（回收复核）、subs（来源统计）
- **2026-09-06 keyword_add_batch**：`vibe_keyword_add_batch` 一次调用加 N 词（逐条语义同 keyword_add）——初始词/扩词用批量而非循环，留在账号限流窗内
- **交付评估（2026-09-10）**：`vibe_sub_health.assessment` 给出"当前搜索面能否填满你的领取额度"（`projected_items_month` vs `commitment_remaining`）与瓶颈归因（supply_ceiling/word_face/capacity/collecting/no_data/ok）
- **回收流程**：判 `irrelevant` 进 `vibe_rejected`；可用 `vibe_recover_lead` 恢复重评
- **防滥用**：每日交付上限 + 入库公平使用上限 + 已领取校验
