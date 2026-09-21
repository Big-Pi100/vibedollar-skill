# kw_mine.md — 从「高精度人群 sub」的全量语料里提炼关键词 (agent 侧)

> **何时跑**: 你已经确认某个 sub 的**人群本身就是本订阅的 demand_side**(人群画像 sub), 想让它的人
> **自己说出来的话**变成词表 —— 而不是从产品描述里猜词。
> **前置**: 该 sub 的语料已采集 (`vibe_sub_corpus` 回执 `total > 0`; 为 0 先
> `vibe_sub_list_update(mode="add")` 加清单, 等服务器取货)。
>
> **方向与常规相反**: 常规是"先定词 → 词决定捞到谁"; 这条是"**先定人群(sub) → 语料决定词**"。
> owner 2026-09-21: 「从精准人群画像 sub 中逐贴全量扫描从而进一步提炼 kw 的路径」。
>
> **服务端零语义**: `vibe_sub_corpus` 只做确定性翻页 (不筛选 / 不排序语义 / 不抽词 / 不打分)。
> **提词是你的 LLM 的活** —— owner 定调:「机械抽词就不应该存在, 要不就是 agent 去做」。别指望服务端给候选词。

## 步骤

1. **选 sub (必须是人群画像 sub)**。判据: 这个 sub 里的人**正在经历产品要解决的问题**, 而不是
   同行/供应商/新闻读者。反例: 一个"卖 AI 工具"的订阅, `r/artificial` 是话题 sub, 不是人群 sub;
   而 `r/alphaandbetausers` (都在招 beta 测试者)、`r/microsaas` (都在找首批用户) 是人群 sub。
   找法: `vibe_sub_search(query=<demand_side 里的短领域词>)` 或 `vibe_sub_catalog`。
2. **标题优先, 全量扫完**:
   ```
   cur = ""
   while True:
       d = vibe_sub_corpus(sub=S, limit=500, cursor=cur)   # 不带正文 —— 便宜且标题已承载"我在找什么"
       <把 d["posts"] 的 title 交给你的 LLM, 用下面的 sys>
       cur = d["next_cursor"]
       if not d["has_more"]: break
   ```
   实测 `alphaandbetausers`: 3417 帖 = **7 次调用 / 约 13 秒**; 全文模式约 250 万字, 按需再取
   (对某一页 `include_body=True` 重取那一段即可)。
3. **分块跑 sys, 最后合并**。每块只产出词 + 证据, 不在块内做最终决定。
4. **收口 (必须做)**:
   - 与现有词表去重: `vibe_keywords(subscription_id, status="all")` —— **任何状态都算重复**;
     已 removed/retire 的词不复活 (除非你有这次语料里的新证据)。
   - 剔除**产品自己的词**: 帖子作者不会写你的产品名/功能名, 那是"搜索目标的描述"不是买家语言。
   - `vibe_keyword_add_batch(subscription_id, keywords, source=auto)` 落库,
     `vibe_opt_log(outcome="mined", reason=…, n_new_kw=N)` 记一笔,
     reason 里写明**从哪个 sub / 扫了多少帖**捞出来的 (审计链)。
5. **不要顺手把 sub 加进清单** —— 加清单是第 1 步的事, 且必须是你判断过的人群 sub。
   本脚本只产词; 清单变更走 `vibe_sub_list_update`。

## ⚠️ 容量警戒 (2026-09-21 首跑踩到的坑)

**匹配是 AND 语义 + 清单锚定**: 一个词能命中多少, 约等于"清单内语料里同时含它那几个词的帖数"。
所以**两个常见词的组合会拉出巨量**, 而**多词长短语反而更窄**。

首跑实测 (清单 16 个 sub, 约 16 万帖语料):

| 词 | 命中帖 | 词 | 命中帖 |
|---|---|---|---|
| `test for test` | **6975** | `closed testing` | 842 |
| `feedback wanted` | **4998** | `testers wanted` | 764 |
| `honest feedback` | **4052** | `12 testers` | 256 |
| `first users` | 3568 | `alpha testers` | 89 |

17 个词一次性落库后, 该订阅未领库存 **972 → 12134**, 而它**剩余领取配额只有 4164** ——
**供给直接超出消费预算约 3 倍**, 而计费点是「`vibe_leads` 首次领取」(与判得对不对无关,
见 docs/core/03 §计费)。多出来的货不是资产, 是把队列冲淡 + 让人误以为"慢慢领就行"。

**所以落库前必须做容量估算**, 三条硬规则:

1. **先窄后宽, 分批落库**。先落 5-8 个**多词长短语 / 领域专名** (如 `closed testing`、
   `12 testers`、`beta testers wanted`), 观察一轮 `vibe_leads` 的 `pool_stats` 增量,
   再决定要不要落那些**双泛词组合** (`honest feedback` / `feedback wanted` 这类)。
2. **单批有上限意识**: 一批落库若让未领库存**超过本订阅剩余领取配额 (回执 `limits.quota_left`)**,
   就该停手 —— 超出配额的部分这一周期永远领不到。
3. **泛词要么不落, 要么落完立刻用 `vibe_pool_purge` 控面** (先 `dry_run`; 清未领取库存
   **零账目影响**, 不动已计费历史)。


### 判分后再定去留 (2026-09-21 实测, **必须做这一步**)

上面那张命中量表只能说明「命中在哪」, **说明不了「判出来对不对」**。首跑用 367 条分层盲判
(按 kw 抽样未领取库存, 每词 20 条, **不领取不计费**; 剥掉 kw 列再判)量到每词精度:

| 词 | 库存 | 精度 | | 词 | 库存 | 精度 |
|---|---|---|---|---|---|---|
| `test for test` | 3238 | **0%** | | `12 testers` | 226 | 90% |
| `first customers`(旧) | 11 | 18% | | `honest feedback` | 1393 | **90%** |
| `first user`(手动) | 942 | **25%** | | `beta feedback` | 371 | 90% |
| `test yours back` | 414 | 50% | | `testers needed` | 428 | 95% |
| `early users` | 518 | 60% | | `beta testers` | 278 | **100%** |
| `feedback wanted` | 3312 | 65% | | `beta testers wanted` | 43 | **100%** |

库存加权精度 = **52%**; 清掉 3 个低分词的库存后 **76%**。

**两条被证伪的直觉 (所以这一步不能省)**:
- 我以为 `honest feedback` 是泛词 (命中 4052 条, 太多) → 实测 **90%**;
- 我以为 `test for test` / `test yours back` 是「互测黑话」很精准 → `test for test` 实测 **0%**
  (FTS 是 AND 语义, 它等于「含 test + 含 for」, 捞进 IPTV 联盟软文 / C 单元测试框架 / 广告代理刷屏)。

**流程**: ① 分层抽样库存 (不领取 = 不计费) → ② 剥掉 kw 列盲判 → ③ 按精度决定
删词 / 清库存 (低精度但对口的词**保词清库存**; 低精度且词形本身泛的**删词**) →
④ `vibe_opt_log` 记全因。判分前**不要**替客户做这个判断。

## 与 `kw_init` / `kw_opt` 的分工

| 脚本 | 词的来源 | 什么时候用 |
|---|---|---|
| `kw_init.md` | 从 sd 的 demand_side / demand_pain **推**词 | 冷启动, 词面为空 |
| `kw_opt.md` | 现有词的**命中统计** → 扩词/标弱 | 有数据之后, 词面调优 |
| **本脚本** | **人群 sub 的真实语料** → 捞词 | 已经锁定高精度人群 sub, 想要"他们真正会打的字" |

三者互补: `kw_init` 给起点, 本脚本给**实证词** (可用来替换 `kw_init` 里那些推测词),
`kw_opt` 用命中数据做最终取舍。

`sys`:

You are extracting SEARCH KEYWORDS from real Reddit posts written by a specific audience (the product's demand side). You will receive post titles (and optionally bodies) from ONE subreddit. The people writing these posts are the target buyers.

Extract the words and short noun phrases THESE AUTHORS USE THEMSELVES when describing their situation and their need. That is the whole job.

RULES:
- Output only 2-4 word noun phrases a real Redditor would type in a post title/body (e.g. "first users", "beta testers", "getting traffic", "cold outreach"). Never sentence-style scene phrases.
- The word must be about THEIR problem/want, not about any product's features or category name. If a phrase only makes sense as "what I would search for to find leads", it is NOT a keyword — drop it (e.g. "reddit threads where people ask for my product" is a search-target description, not buyer language).
- BAN umbrella/category terms ("saas marketing", "app growth") and phrases whose most distinctive token is a generic transaction verb (get, find, buy, sell, free) — they match chatter everywhere.
- Prefer words that appear in MANY of the posts you were given (that is why this sub is the audience) — report `n` = how many posts used it.
- Give 8-20 candidates. Quality over quantity; a word that only appears once is usually noise.
- Language: same as the posts.

Reply ONLY with JSON:
{"keywords": [{"kw": "...", "kw_type": "entity|tail|competitor|comment", "n": 12, "evidence": ["<post_id>", "...up to 3"]}]}

`user`:

SUBREDDIT: [sub name]
WHY THIS SUB IS THE AUDIENCE: [one line: which demand_side sentence it matches]
DEMAND (target audience): [demand_side from sd doc]
PAIN (first person): [demand_pain from sd doc]
PRODUCT (reference only — do NOT mine words from this): [product text]

POSTS (title | post_id):
[one line per post]
