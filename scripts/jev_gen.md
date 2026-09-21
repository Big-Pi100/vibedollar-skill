# jev_gen.md — 写出**你这个订阅自己的**判定问句 (TypeSafe/Jev 用)

> **为什么每个订阅必须自己写**: 问句是**你的需求画像**的函数。举反例就清楚了 ——
> 「作者是不是在为获客/找用户发愁」这个问句, 对"把产品卖给想获客的人"(如 vibedollar 自己)成立,
> 对**美甲机、电动剃须刀、SaaS 监控工具**都不成立: 那些买家根本不会问"我怎么获客"。
> 把某一个订阅的问句硬编码进通用引擎, 就是**换了个地方的隐藏语义机制**
> (见 docs/core/01 §模型层分工原则)。
>
> **所以**: 本文件只教**结构**, 不给你词句。下面出现的例子都标注了"这是 X 订阅的画像, 不是模板"。

## 1. 引擎提供什么 (通用, 你不用管)

`score_batch.py --engine jev` 读 `data/jev_<sid>.json`, 然后:

- **一次调用并行问**你写的所有问句 (TypeSafe 的 fan-out);
- **合成语义** (固定, 不可配): `relevant = any(need >= 0.5) or (gate_yes >= 0.5 and gate_no < 0.5)`;
- **升级带**: 任一**判定用**信号落在 `band` (默认 `[0.3, 0.7]`) → 标 `escalate`, 交你按
  `judge_prompt.md` 复核 (实测: 把 `gate_no` 也拉进带会把复核量翻倍而收益相同, 故不拉);
- **契约**: `score >= 60` ⟺ `relevant`; `confidence` = 最强判定信号离 0.5 的距离×2;
- `reason` 是**机器记录**(逐问句概率), 不是解释 —— 语义理由由你在升级带里补;
- 离线回放 (`--record-answers` / `--replay-answers`): 记录里有的问句名才能回放。

## 1.5 ⚠️ 起点: 先用那一个**产品相对**的问句 (跨产品实测)

2026-09-21 把 vibedollar 自己的 4 个问句原样搬到 **6 个不同领域**的产品上跑 (标签用客户自己的判定):

| 产品 | `is_buyer` 单问 | vibedollar 两问 | vibedollar 四问 |
|---|---|---|---|
| 遛狗排班 / 抗拖延 / 视觉教学 / 非营利 / 自由职业税务 / 线索工具 | **0.89 合计** | 0.82 | **0.77** |

**6 个产品无一例外都变差** —— 每加一条别人的腿就掉一档。所以:

- ⚠️ **样本不能按模型的输出挑**: 在"模型判无关"的条目上验证"增加召回"的改动, 必然高估它
  (355 实测: 那样抽样的结论是闸门把误差减半; 换成**平衡随机样本**后, 同一个闸门变成**负贡献** —— 0.864 降到 0.812)
  - **起点用 `is_buyer` 这一条**(它靠 state 注入做到产品相对, 是唯一跨产品稳的基线);
- 每加一条**产品专属**的腿, 必须在**该产品自己的标签**上证明不劣于基线, 否则不加;
- **别把任何一个产品的问句当模板** —— 包括本文件后面那个例子。


## 2. 结构 (照这个写)

```json
{
  "sub_id": 355,
  "derived_from": "data/sd_355.md @ <日期> 的 demand_side / demand_pain",
  "band": [0.3, 0.7],
  "questions": {
    "<need_1>": {"question": "...", "answer_yes_when": ["..."], "answer_no_when": ["..."]},
    "<need_2>": {"question": "...", "answer_yes_when": ["..."], "answer_no_when": ["..."]}
  },
  "gate": {
    "yes": {"question": "...", "answer_yes_when": ["..."], "answer_no_when": ["..."]},
    "no":  {"question": "...", "answer_yes_when": ["..."], "answer_no_when": ["..."]}
  }
}
```

- **`questions` (1-4 条)**: 每条问"作者**自己**有没有这个产品要解决的那个未解需求"。**取 OR** ——
  多写几条是为了**保召回**(漏判比多判贵), 不是为了更准。
  - 词句必须来自 `demand_side`/`demand_pain`(买家**自己会说的话**), 不是产品功能词;
  - 每条都要写 `answer_no_when` —— **写明反例比写明正例更能约束模型**;
  - 有竞争工具/替代方案对比时, 加一条"在比较/嫌贵"的问句很划算 (高意图)。
- **`gate` (可选, 成对)**: 治"**漏掉的那一类**"。`yes` = "作者属于那个漏掉的类",
  `no` = "作者属于口径明确**排除**的类"(照抄 `judge_prompt.md` 的 NO 列表)。
  语义是 `yes ∧ ¬no` —— **合取, 不是又一条 OR 腿**(OR 会把排除类也放进来)。
  - 经验: `no` 这一问基本就是"作者是不是卖方/同行/在晒已跑通的系统"。**这一条往往可以跨订阅复用**,
    因为口径的 NO 列表本来就大同小异; `yes` 才是你的画像独有的。

## 3. 例子: vibedollar 这个订阅 (⚠️ **这是它的画像, 不是模板**)

它的 demand_side 是「独立开发者/首次做 SaaS·App、有产品或 pre-launch、在找第一批客户」。
它曾经漏掉的一类是「**自己做早期产品、在 Reddit 求 honest feedback / 求首批用户**」——
所以它加了一对闸门:

```json
"questions": {
  "is_buyer":  {"question": "The state holds a PRODUCT and a Reddit POST. Is the post author a potential buyer for that product — do they express a need this product solves, or ask how to solve it themselves?", "...": "..."},
  "acquisition_ask": {"question": "Is the post author asking for help GETTING CUSTOMERS, users, sales, traction or audience — is growth/acquisition their own problem here?", "...": "..."}
},
"gate": {
  "yes": {"question": "Is the post author asking OTHER PEOPLE for something for a product THAT THEY THEMSELVES are building or have just launched — feedback, testers, early users, or help getting adoption?"},
  "no":  {"question": "Is the post author NOT a potential buyer — are they a seller/supplier/peer, or showing off a system that already works?"}
}
```

**注意 `acquisition_ask` 本身就带这个订阅的画像** ("买家在求获客") ——
你的产品如果不是卖给"想获客的人", **这条问句对你是错的**, 要按你自己的 demand_pain 重写。

## 4. 怎么验证你写的问句 (别跳过 —— 不验证就是主观)

这是 2026-09-21 在 vibedollar 上跑出来的**可复制流程**:

1. **先跑一批真实的**: `score_batch.py --sub <sid> --limit 30 --engine jev --record-answers run.json`,
   然后**只复核升级带** (`escalate_ids`), 按 `judge_prompt.md` 自己判 —— 不一致的用
   `vibe_submit_score(override=True)` 覆盖。
2. **聚类你改判的那些条目** —— 如果它们**集中在同一个类**(vibedollar 那次 14 条里 11 条是同一类),
   那就是你的问句**漏掉了一个边界清晰的类** → 给它加一对 `gate`。
   (如果改判的条目**散在各处**, 那是噪声, 不是缺类, 别乱加问句。)
3. ⚠️ **样本要按标签分层, 而且要先确认 sd 描述的是买家**: 20 条随机抽的样本里往往只有 0–2 个正例,
   那样既奖励不了召回也没有统计力 (355 能做出消融, 是因为它有 250 条**平衡**标签)。
   另外先检查 `sd_gen` 出来的 `demand_side` 是否描述了**买家本人** —— 实测有产品的 demand_side 写的是
   **终端客户**而不是买家 (卖排班 app 给遛狗人, 却把"需要遛狗的宠物主"当成 demand_side); 那种情况下**任何问句都救不了**。
4. **给"自动带"贴标签再定价** ⚠️: 合成结果里**大部分条目是自动判的、没人复核** ——
   那里才是静默错误住的地方。从"模型判 irrelevant 且没人复核"的条目里**按新问句的概率分层抽样**
   (高/低各半), 做成**剥掉一切模型痕迹**的盲包独立盲判, 然后比:
   | 设计 | 与本批真标签的误差 |
   |---|---|
   | 现状 (不加闸门) | ? |
   | 加闸门 `yes ∧ ¬no` | ? |
   只有**在真标签上不劣于现状**, 才真正采用。
4. **升级带的带宽**也要一起量: 把新问句也拉进 `band` 会多复核多少? 值不值?
   (vibedollar 实测: 只拉 `gate_yes` → 复核量 37%→44%, 值; 连 `gate_no` 一起拉 → 55-63%, 不值。)

> ⚠️ **别用模型自己的输出当基准**。第一轮做这件事时, 我拿"未被复核的条目上模型的判定"当真值,
> 于是三种改进看起来**都更差**; 补齐真标签后结论**反转** —— 最好的设计把误差从 41 降到 18。
> **没有标签就没有定价。**

## 5. 放在哪

随包带一份**实例** `scripts/jev_example.json`(就是 vibedollar 这个订阅的问句) —— 它的用处**只有一个**:
让你看清格式和"闸门对怎么写"。**别直接用它**: 那份问句是 vibedollar 的需求画像的函数。
照上面四节从**你自己的 `data/sd_<sid>.md`** 推出你自己的, 落到 `data/jev_<sid>.json`。

## 6. 放在哪 (路径)

`data/jev_<sid>.json` (与 `data/sd_<sid>.md` 同族, 每订阅一份)。
`score_batch.py --engine jev` 找不到它会**直接报错**并指回本文件 —— 这是刻意的:
**宁可让你写一份自己的, 也不要让你套用别人的。**
