# vibedollar — 帮你找到正在等你的客户

> **Reddit 上正在抱怨、求方案的潜在客户，vibedollar 把他们带给你。**

vibedollar 基于你的产品描述，**持续抓取** Reddit 上的潜在客户线索（帖子+评论，含作者与正文），你的 agent 用自己的 LLM 判断相关性，**评分通过的才计费**（按效果付费）。

1. **MCP 服务**（mcp.vibedollar.net）—— Agent 注册后订阅产品，候选线索自动积累，你的 agent 评分后领取，**零配置**（只输入产品描述）
2. **SKILL**（vibedollar-skill/）—— 让 vibedollar 能力变成 agent 的"肌肉记忆"

---

## 一、产品形态

| 形态 | 面向 | 模式 | 状态 |
|:-----|:-----|:-----|:-----|
| **MCP 服务**（mcp.vibedollar.net） | AI Agent 直接调用 | FastMCP，订阅制：候选免费，**评分通过才计费** | 🟢 已上线 |
| **SKILL**（vibedollar-skill/） | 任何 AI Agent | 免费（含工具接入说明） | 🟢 已就绪 |

**核心商业模式：按效果付费** —— 候选线索免费给你，你（你的 agent）评分判断相关性，`relevant` 的才计费（1 条 = 1 配额）。没评上的不花钱。

---

## 二、MCP 服务：候选线索 + 你的评分

通过 MCP，任何 AI Agent 注册获取 API key（两步注册：邮箱验证码，key 邮件送达）→ 订阅后领取候选 → 评分计费。注册不送额度；付费方式：订阅 Starter/Pro（$39/$79 月），或自由充值钱包（微信 ¥1~¥1000 / Creem $1~$200），另有 $1 Welcome Credit 新客福利：

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

> 详细能力说明、示例、工作流见 **[docs/mcp-service-guide.md](docs/mcp-service-guide.md)**。

**计费说明**：候选线索**免费**；`vibe_submit_score` 判定 `relevant` 的候选计 1 配额/条并进交付列表，`irrelevant` 不计费（回灌优化，推送越来越准）。每批候选需全部评分后再取下一批。另有 $1 Welcome Credit 新客福利（每人限一次）。

---

## 三、当前状态（2026-08-20）

- **v3.1 用户评分模式**：候选免费 → 你的 agent 评分 → `relevant` 才计费（按效果付费）
- **后台管线**：订阅产品后持续抓取 Reddit（搜索方向/数据源自动优化），候选自动积累
- **反馈闭环**：你的评分（含不相关）回灌优化推送；分歧可查看对齐（标准校准）
- **防滥用**：候选批次解锁制 + 已领取校验 + 一致性护栏

---

## 四、快速开始（开发环境）

```bash
# MCP 服务（stdio 模式）
python mcp_server.py

# 测试
python -m pytest tests/ -q
```

Windows 可靠后台运行：`scripts/run_batch.bat`（顺序执行每日流水线，替代 Git Bash 无 nohup 的问题）。

---

## 六、目录结构

```
pipeline/          # 核心管线
  vibe_product_demo.py   # batch 导入入口（checkpoint/grounding/founder 确定性）
  batch_fetch_starter.py # 案例抓取 + 官方页解析
  enrich_cases.py        # 字段补全流水线（EnrichRunner）
  story_writer.py        # Tier1 故事重写（8-gram + grounding 双门）
  geo_site_generator.py  # 静态站生成（JSON-LD 结构化）
  enrich_common.py       # 公共层（checkpoint/原子写/Grounding/_norm_number）
  llm.py / search.py / config.py
knowledge/         # 知识库（cases/*.yaml + index.yaml + toolchains/）
data/              # 线索数据 / checkpoint / 日志 / mcp_store.db
prompts/           # LLM 提示词（vibe_discover / enrich_fields / story_rewrite）
scripts/           # run_batch.bat 等运维脚本
docs/              # 文档
tests/             # 测试
mcp_server.py      # MCP 服务（FastMCP，12 个工具）
vibedollar-skill/  # SKILL 发布物
```

---

## 七、安全提示

- 服务器 SSH 使用 ed25519 密钥（`vibedollar_ed25519`），已禁用 root 登录
- GitHub Secrets 仅保留 `VPS_SSH_KEY`（CI 部署用）
- **LLM 调用铁律**：所有 `call_llm` 统一用 `config.max_tokens=65536` / `config.input_chars=64000`，禁止硬编码独立限制
