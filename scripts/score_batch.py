#!/usr/bin/env python3
"""score_batch — vibedollar 批量评分执行器 (脚本工具, 非 agent)。

宿主 agent (Claude/pi/任意 MCP agent) 的决策引擎决定"该评哪个订阅、用哪个标准",
本脚本只做它擅长的机械执行: 领取候选 → **并行** LLM 判真 → submit 回传 → 证据保存。
不含调度/跨订阅决策/何时跑的判断 — 那些归宿主 agent。

为什么脚本化 (用户定稿): 批量逐条判断并行化后, 脚本效率远超 agent 现场写循环;
agent 直接调本工具比自己写脚本高效得多。

用法:
    python3 score_batch.py --sub 12 --limit 20 \
        --judge judge_prompt.md [--parallel 8] [--out ./evidence] \
        [--threshold 60] [--dry-run]

入参 (全部显式 — 由宿主 agent 决定后传入):
    --sub       目标订阅 id (必填 — 单订阅单批)
    --limit     领取上限 (默认 10)
    --judge     判真标准文件 (默认 scripts/judge_prompt.md)
    --parallel  并行判真路数 (默认 8 — 批量效率核心)
    --out       证据输出目录 (可选; relevant 行落 csv/jsonl)
    --threshold score>=threshold → relevant (默认 60)
    --dry-run   只领取不判真不交还

返回 (stdout JSON — 宿主 agent 读取决定下一步):
    {"sub_id": 12, "claimed": N, "judged": N, "relevant": N,
     "submitted": N, "failed": N, "pending": [...ids],
     "submit_state": "ok|timeout_unclear|none"}
    # v2.1 (缺口2): submit_state 标注交还是否确认 —
    #   ok              = 收到服务端回执 (submitted = passed relevant 数)
    #   timeout_unclear = 交还超时, 不确定服务端是否已处理 → 宿主用
    #                     vibe_sub_health 的 delivered/pending 交叉核验,
    #                     别盲目重交 (服务端幂等: 已评分 id 返回 error 不双计)
    #   none            = 无提交 (空批/dry-run)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp import MCPClient  # noqa: E402

DEFAULT_THRESHOLD = 60
UA = "Mozilla/5.0 (compatible; vibedollar-score-batch/0.1)"

DEFAULT_JUDGE_PROMPT = """You are a lead-qualification analyst for ONE product. Decide whether the author of a
Reddit post is a real potential customer of the product described by the user.

1. Relevant = the author is IN the problem area the product solves and signals
   need/struggle right now (asking for advice, comparing tools, describing pain).
2. NOT relevant = unrelated topic, pure entertainment, methodology-only, or the
   author is clearly outside the product's demand-side scene.
3. Score 0-100 by fit (85-100 explicit; 60-84 in-scene; 30-59 weak; 0-29 no).
4. Output STRICT JSON only: {"verdict":"relevant"|"irrelevant","score":0-100,
   "reason":"one line"} — verdict relevant ONLY when score >= 60."""


def _load_judge_prompt(path: str) -> str:
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "judge_prompt.md")):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "judge_prompt.md"), encoding="utf-8") as f:
            return f.read()
    return DEFAULT_JUDGE_PROMPT


def _llm_judge(base: str, model: str, key: str, prompt: str,
               product: str, post: dict, timeout: int = 60,
               retries: int = 2) -> dict | None:
    """判真单条。网络瞬态失败 (SSL 握手/超时) 重试 retries 次 (指数退避)。"""
    import time as _t
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": (
                f"Product: {product}\n\n"
                f"Post (r/{post.get('subreddit', '?')}):\n"
                f"{post.get('title') or ''}\n{(post.get('body') or '')[:6000]}\n\n"
                "Output the strict JSON verdict.")},
        ],
        "temperature": 0.1,
        "max_tokens": 300,
    }).encode()
    url = base.rstrip("/") + "/chat/completions"
    last_err = ""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": UA,
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            text = data["choices"][0]["message"]["content"]
            break  # 成功
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            if attempt < retries:
                _t.sleep(1.5 * (attempt + 1))  # 1.5s → 3s
            else:
                print(f"  ⚠ LLM 判真失败: {last_err[:100]}", file=sys.stderr)
                return None
    text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    try:
        out = {"verdict": str(d.get("verdict", "irrelevant")).lower(),
               "score": int(d.get("score", 0)),
               "reason": str(d.get("reason", ""))[:300]}
        # 2026-09-21 (口径定稿): judge_prompt 现在要求**边界带 (score 40-70)** 回 confidence;
        #   有就带上 (服务端只存不用), 没有就不传 —— 与 --engine jev 同一条契约。
        if d.get("confidence") not in (None, ""):
            try:
                out["confidence"] = max(0.0, min(1.0, float(d["confidence"])))
            except (TypeError, ValueError):
                pass
        return out
    except Exception:  # noqa: BLE001
        return None


def _save_evidence(out_dir: str, sid: int, product: str,
                   judged: list, fmt: str = "csv") -> None:
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for p, pl in judged:
        if pl["verdict"] != "relevant":
            continue
        rows.append({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sub_id": sid, "product": product, "lead_id": pl["id"],
            "url": p.get("url") or "", "subreddit": p.get("subreddit") or "",
            "title": p.get("title") or "", "score": pl["score"],
            "reason": pl["reason"],
        })
    if not rows:
        return
    if fmt == "csv":
        fpath = os.path.join(out_dir, f"evidence_{time.strftime('%Y%m%d')}.csv")
        new = not os.path.exists(fpath)
        with open(fpath, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            if new:
                w.writeheader()
            w.writerows(rows)
    else:
        fpath = os.path.join(out_dir, f"evidence_{time.strftime('%Y%m%d')}.jsonl")
        with open(fpath, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"      📄 证据 {len(rows)} 条 → {fpath}")


# 升级带: max(p1,p2) 落在这个区间 = "连 Jev 自己都不确定" → 交 agent 复核。
# 2026-09-21 实测调参 (1145 条带独立盲判基准的真实线索, 见 docs/jev-shadow-eval §14):
#   判据A "两问不一致"(原实现): 升级 25%, **自动带错 10.1% 条目**
#   判据B "max(p) ∈ [0.3,0.7]" (现用): 升级 26%, **自动带错 5.1% 条目**
#   并集:                        升级 40%, 自动带错 3.8% 条目
# → **同样的升级率, 原判据的错误是两倍** —— 换代价明显更小。并集更保守但多判 14%。
#   "两问不一致"仍单独报出 (disagree), 它是个有用的信号, 但**不是**升级判据。
ESCALATE_LO, ESCALATE_HI = 0.3, 0.7


def jev_decide(is_buyer: float, acq_ask: float, thr: float = 0.5) -> dict:
    """Jev 两问结果的**级联决策** (纯函数, 可离线单测)。

    用两问 **OR** 保召回 (实测 FN=0 一条不漏; 单问 is_buyer 会漏), 用 `escalate`
    把**不确定的那批**标出来交给 agent 按 `judge_prompt.md` 复核 —— 这才是三段式:
    **高置信自动过 / 升级带交人**。升级判据见上面 ESCALATE_* 的实测调参。

    confidence: 判定侧最强证据离 0.5 边界的距离 (Noul 没有独立 confidence,
      按其概率的确定性折算到 [0,1]; 这就是回传给服务端的 `confidence` —— 服务端只存不用)。
    """
    p1, p2 = float(is_buyer or 0.0), float(acq_ask or 0.0)
    rel = (p1 >= thr) or (p2 >= thr)
    strong = max(p1, p2)
    conf = (strong - thr) * 2 if rel else (thr - strong) * 2
    conf = max(0.0, min(1.0, conf))
    # ⚠️ score 必须遵守 judge_prompt 的契约: relevant ⟺ score >= 60。
    #   OR 规则下会出现 max(p1,p2)=0.5 → relevant, 但 0.5*100 = 50 < 60 —— 契约被破坏:
    #   下游(与 judge_prompt 同源的判定/审计)会认为"score<60 却是 relevant"自相矛盾。
    #   (2026-09-21 隔离跑实测: 4239775=59 / 4239776=58 / 4238972=50 三条都是 relevant。)
    #   修法: 保留量级信号, 但把落到错误一侧的值夹到契约边界上。
    _sc = int(round(strong * 100))
    _sc = max(_sc, 60) if rel else min(_sc, 59)
    return {'relevant': rel,
            # 升级 = 落在不确定带 (不是"两问分歧" —— 实测后者同升级率下错误翻倍)
            'escalate': (ESCALATE_LO <= strong <= ESCALATE_HI),
            'disagree': ((p1 >= thr) != (p2 >= thr)),   # 单独报出, 供参考
            'confidence': round(conf, 3),
            'score': _sc,
            'is_buyer': round(p1, 3), 'acquisition_ask': round(p2, 3)}


# ── 每订阅的问句 (2026-09-21) ─────────────────────────────────────────────
# ⚠️ 为什么**不再内建**问句: 问句必须来自**该订阅自己的需求画像** (sd + judge_prompt)。
#   早先内建的 is_buyer/acquisition_ask 里, acquisition_ask 隐含"买家在求获客"这个假设 ——
#   那只对"卖给想获客的人"的产品成立 (vibedollar 正好是), 对美甲/剃须刀/SaaS 监控都不成立。
#   把某一个订阅的画像硬编码进通用引擎 = 换了个地方的隐藏语义机制 (core/01 禁止)。
#   现在问句写在 data/jev_<sid>.json (与 data/sd_<sid>.md 同族), 由 agent 按 scripts/jev_gen.md
#   从自己的 sd 推导。引擎只提供**通用结构**:
#     · 多个 need 问句取 OR (保召回)   · 可选闸门对 gate_yes ∧ ¬gate_no (治"漏掉的那一类")
#     · 升级带 = 任一**判定用**信号落在不确定带   · 契约: relevant ⟺ score >= 60
JEV_BAND_LO, JEV_BAND_HI = 0.3, 0.7


def jev_spec_path(sub_id: int) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data",
                        "jev_%s.json" % sub_id)


def jev_load_spec(sub_id: int, path: str = ""):
    """读该订阅的问句文件。**缺文件/格式错 = 明确报错并指向 jev_gen.md** (不给内建默认)。"""
    p = path or jev_spec_path(sub_id)
    if not os.path.exists(p):
        sys.exit("engine=jev 需要**该订阅自己的**问句文件: %s\n"
                 "  怎么写出适合你这个订阅的问句 -> 读 scripts/jev_gen.md\n"
                 "  (不要套用别的订阅的问句: 问句是需求画像的函数, 换产品就不成立)" % p)
    try:
        with open(p, encoding="utf-8") as fh:
            spec = json.load(fh)
    except Exception as e:  # noqa: BLE001
        sys.exit("问句文件读不了 (%s): %s" % (p, str(e)[:120]))
    if not isinstance(spec.get("questions"), dict) or not spec["questions"]:
        sys.exit("问句文件要有非空的 questions 字典: %s (见 scripts/jev_gen.md)" % p)
    spec.setdefault("band", [JEV_BAND_LO, JEV_BAND_HI])
    spec["_path"] = p
    return spec


def jev_build_questions(spec: dict):
    """按 spec 构造 Noul 字典 (name -> Noul)。questions 里的进 OR 腿; gate 对单独成两条。"""
    from typesafe_sdk import Noul
    out = {}
    for name, q in (spec.get("questions") or {}).items():
        out[name] = Noul(instructions={"question": q.get("question") or "",
                                       "answer_yes_when": list(q.get("answer_yes_when") or []),
                                       "answer_no_when": list(q.get("answer_no_when") or [])})
    g = spec.get("gate") or {}
    for leg in ("yes", "no"):
        if isinstance(g.get(leg), dict):
            q = g[leg]
            out["gate_" + leg] = Noul(instructions={
                "question": q.get("question") or "",
                "answer_yes_when": list(q.get("answer_yes_when") or []),
                "answer_no_when": list(q.get("answer_no_when") or [])})
    return out


def jev_compose(spec: dict, probs: dict, thr: float = 0.5) -> dict:
    """把 N 个概率合成判定 —— 纯函数, 可离线单测。

    语义: relevant = any(need >= thr) or (gate_yes >= thr and gate_no < thr)
    升级带: 任一**判定用**信号落在 [lo,hi] (need 取最大者; gate_yes)。
      实测 (263 条): 把 gate_no 也拉进带会把复核量从 44% 推到 55-63% 而收益相同, 故不进。
    契约: score >= 60 ⟺ relevant (与 judge_prompt 同契)。
    """
    lo, hi = (spec.get("band") or [JEV_BAND_LO, JEV_BAND_HI])[:2]
    needs = [float(probs[k]) for k in (spec.get("questions") or {}) if k in probs]
    gy = float(probs["gate_yes"]) if "gate_yes" in probs else None
    gn = float(probs["gate_no"]) if "gate_no" in probs else None
    rel = (any(p >= thr for p in needs)
           or (gy is not None and gy >= thr and (gn is None or gn < thr)))
    deciders = list(needs) + ([gy] if gy is not None else [])
    strong = max(deciders) if deciders else 0.0
    conf = (strong - thr) * 2 if rel else (thr - strong) * 2
    conf = max(0.0, min(1.0, conf))
    band = bool(deciders) and any(lo <= p <= hi for p in deciders)
    sc = int(round(strong * 100))
    sc = max(sc, 60) if rel else min(sc, 59)
    return {"relevant": rel, "escalate": band, "confidence": round(conf, 3), "score": sc,
            "probs": {k: round(float(v), 3) for k, v in probs.items()},
            "gate": (None if gy is None else
                     {"yes": round(gy, 3), "no": (None if gn is None else round(gn, 3))})}


def jev_reason(dec: dict) -> str:
    """机器记录 (**不是解释**): 每个问句的概率 + 闸门 + 结论。
    语义理由由 agent 在升级带里补 (judge_prompt 的契约)。"""
    parts = ["%s=%.2f" % (k, v) for k, v in (dec.get("probs") or {}).items()]
    g = dec.get("gate") or {}
    if g:
        parts.append("gate(yes=%.2f,no=%.2f)" % (g.get("yes") or 0, g.get("no") or 0))
    return "[jev] %s -> %s%s" % (" ".join(parts), "relevant" if dec["relevant"] else "irrelevant",
                                 " (落在不确定带, 建议 agent 复核)" if dec["escalate"] else "")


def jev_judge(ts_key: str, model: str, product: str, sdj: dict, post: dict, spec: dict = None):
    """调 TypeSafe/Jev 一次 (两问并行), 返回与 `_llm_judge` 同形的判定 + 置信/升级标记。

    **key 与成本都在消费方** (原则「模型层分工」第 3 条) —— 这里用的是你自己的
    TYPESAFE_API_KEY; 服务端不碰这个 key。
    """
    from typesafe_sdk import TypeSafeClient
    state = {'product': (product or '')[:600],
             'supply_side': str((sdj or {}).get('supply_side') or '')[:400],
             'demand_side': str((sdj or {}).get('demand_side') or '')[:400],
             'demand_pain': str((sdj or {}).get('demand_pain') or '')[:400],
             'post': {'subreddit': post.get('subreddit') or '',
                      'title': post.get('title') or '',
                      'body': str(post.get('body') or '')[:2500]}}
    qs = jev_build_questions(spec)
    with TypeSafeClient(api_key=ts_key) as client:
        r = client.system_one(state=state, model=model, questions=qs)
    dec = jev_compose(spec, {k: float(getattr(r.answers[k], 'noul', 0.0)) for k in qs})
    # reason: Jev **不给解释** —— 这里给的是**事实性的机器记录**, 不是理由;
    #   服务端只存不改 (原则第 4 条)。语义理由仍应由 agent 在升级带里补。
    dec['reason'] = jev_reason(dec)
    return dec

def main() -> None:
    ap = argparse.ArgumentParser(description="vibedollar 批量评分执行器 (单订阅单批)")
    ap.add_argument("--key", default=os.environ.get("VIBEDOLLAR_API_KEY", ""))
    ap.add_argument("--llm-key", default=os.environ.get("LLM_API_KEY", ""))
    ap.add_argument("--llm-base", default=os.environ.get(
        "LLM_BASE_URL", "https://api.deepseek.com/v1"))
    ap.add_argument("--llm-model", default=os.environ.get("LLM_MODEL", "deepseek-chat"))
    ap.add_argument("--sub", type=int, required=True, help="目标订阅 id (必填)")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--judge", default="", help="判真标准文件 (默认 scripts/judge_prompt.md)")
    ap.add_argument("--parallel", type=int, default=8, help="并行判真路数")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    ap.add_argument("--out", default="", help="证据输出目录 (可选)")
    ap.add_argument("--out-format", default="csv", choices=["csv", "json"])
    ap.add_argument("--dry-run", action="store_true")
    # ── 判定引擎 (2026-09-21): llm = 现行为 (自带 chat 模型); jev = TypeSafe 决策模型 ──
    ap.add_argument("--engine", default=os.environ.get("JUDGE_ENGINE", "llm"),
                    choices=["llm", "jev"],
                    help="llm (默认, OpenAI 兼容 chat) | jev (TypeSafe 两问级联)")
    ap.add_argument("--typesafe-key", default=os.environ.get("TYPESAFE_API_KEY", ""),
                    help="engine=jev 时必填 (你自己的 key; 环境变量 TYPESAFE_API_KEY)")
    ap.add_argument("--jev-model", default=os.environ.get("JEV_MODEL", "jev-latest"))
    ap.add_argument("--questions", default="", help="每订阅问句文件 (默认 data/jev_<sub>.json; 怎么写出自己的 -> scripts/jev_gen.md)")
    ap.add_argument("--record-answers", default="",
                    help="engine=jev 跑完后把两问答案落盘 (供日后 --replay-answers 离线复跑)")
    ap.add_argument("--replay-answers", default="",
                    help="离线回放: 用 --record-answers 的答案跑同一套级联 (零 API 调用)")
    args = ap.parse_args()

    if not args.key:
        sys.exit("缺少 vibedollar key — 设 VIBEDOLLAR_API_KEY 或 --key")
    if args.engine == "llm" and not args.llm_key and not args.dry_run:
        sys.exit("缺少 LLM key — 设 LLM_API_KEY 或 --llm-key (dry-run 除外)")
    if (args.engine == "jev" and not args.replay_answers
            and not args.typesafe_key and not args.dry_run):
        sys.exit("engine=jev 需要**你自己的** TypeSafe key — 设 TYPESAFE_API_KEY 或 --typesafe-key")

    prompt = _load_judge_prompt(args.judge)
    mc = MCPClient(args.key)

    # 单订阅领取
    r = mc.call("vibe_list_subs")
    data = r.get("data", r)
    product = ""
    sd_json_raw = ""
    for s in (data.get("subscriptions", []) if isinstance(data, dict) else []):
        if int(s.get("id") or 0) == args.sub:
            product = str(s.get("product") or "")
            sd_json_raw = str(s.get("sd_json") or "")
            break
    # 供需四段注入判真标准 (对齐前端 engCallLLM: system 尾部 [SUPPLY/DEMAND] —
    # sd 是评分判定口径; 缺失时降级为仅 product, 建议先跑 sd_gen.md)
    try:
        sdj = json.loads(sd_json_raw) if sd_json_raw else {}
        if sdj and isinstance(sdj, dict) and (
                sdj.get("demand_side") or sdj.get("demand_pain")
                or sdj.get("supply_side")):
            prompt += "\n\n[SUPPLY/DEMAND STRUCTURE]\nproduct: " + product + \
                "\nsupply side: " + str(sdj.get("supply_side") or "") + \
                "\ndemand side (target audience): " + str(sdj.get("demand_side") or "") + \
                "\ncore friction: " + str(sdj.get("core_friction") or "") + \
                "\ndemand pain (first person): " + str(sdj.get("demand_pain") or "")
    except Exception:  # noqa: BLE001 — sd 注入失败不影响判真 (降级纯 product)
        pass
    rr = mc.call("vibe_leads", {"subscription_id": args.sub, "limit": args.limit})
    d = rr.get("data", rr)
    posts = d.get("posts", []) if isinstance(d, dict) else []
    pending = d.get("pending", []) if isinstance(d, dict) else []
    leads = posts + pending
    out = {"sub_id": args.sub, "claimed": len(leads), "judged": 0,
           "relevant": 0, "submitted": 0, "failed": 0,
           "submit_state": "none",
           "engine": args.engine + ("/replay" if args.replay_answers else ""),
           "pending": [p.get("id") for p in pending if p.get("id")]}
    if not leads:
        print(json.dumps(out, ensure_ascii=False))
        return
    if args.dry_run:
        print(json.dumps(out, ensure_ascii=False))
        return

    # 并行判真 (效率核心 — 每路独立请求)
    judged: list = []
    fail = 0
    escalate_ids: list = []
    answers_out: dict = {}
    _replay = {}
    if args.replay_answers:
        try:
            with open(args.replay_answers, encoding='utf-8') as fh:
                _replay = json.load(fh).get('answers') or {}
        except Exception as e:  # noqa: BLE001
            sys.exit('读不到 --replay-answers 文件: %s' % str(e)[:120])

    # 顺序要紧: **回放先判** —— 回放是离线复算, 不该因为没有问句文件就失败
    _spec = None
    if args.replay_answers:
        try:
            _spec = jev_load_spec(args.sub, args.questions)
        except SystemExit:
            _spec = None   # 旧记录只有两问 -> 走 legacy 回放
    elif args.engine == "jev":
        _spec = jev_load_spec(args.sub, args.questions)

    def _one(p):
        """一个候选的判定 —— 三条路: 离线回放 / Jev / 原 chat LLM。"""
        lid = p.get('id')
        if _replay:
            row = _replay.get(str(lid))
            if not row:
                raise RuntimeError('replay 缺该条答案 (lead_id=%s)' % lid)
            # 回放: 记录里就有该订阅问句的答案 -> 用通用合成; 只有旧的两问记录才退回 legacy
            names = set(jev_build_questions(_spec)) if _spec else set()
            if names and names <= set(row):
                dec = jev_compose(_spec, {k: row[k] for k in names})
            else:
                dec = jev_decide(row.get('is_buyer'), row.get('acquisition_ask'))
            dec['reason'] = '[jev/replay] ' + jev_reason(dec).replace('[jev] ', '')
            return dec
        if args.engine == 'jev':
            dec = jev_judge(args.typesafe_key, args.jev_model, product, sdj, p, _spec)
            answers_out[str(lid)] = dict(dec.get('probs') or {},
                                          sub_id=args.sub, title=(p.get('title') or '')[:80])
            return dec
        return _llm_judge(args.llm_base, args.llm_model, args.llm_key, prompt, product, p)

    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        futs = {}
        for p in leads:
            if p.get('id') is None:
                continue
            futs[ex.submit(_one, p)] = (p, p.get('id'))
        for fu in as_completed(futs):
            p, lid = futs[fu]
            try:
                j = fu.result()
            except Exception as e:  # noqa: BLE001
                print('  ⚠️ 判真失败 lead_id=%s: %s' % (lid, str(e)[:80]), file=sys.stderr)
                j = None
            if not j:
                fail += 1
                continue
            # 判决来源: 引擎显式给 relevant 就用它 (Jev 级联是 OR 规则, 不等于阈值);
            #   否则沿用原行为 (score >= threshold)。
            verdict = ('relevant' if j['relevant'] else 'irrelevant') \
                if 'relevant' in j else \
                ('relevant' if j['score'] >= args.threshold else 'irrelevant')
            payload = {'id': int(lid), 'verdict': verdict,
                       'score': j['score'], 'reason': j['reason']}
            if j.get('confidence') is not None:
                payload['confidence'] = j['confidence']
            if j.get('escalate'):
                escalate_ids.append(int(lid))
            judged.append((p, payload))
    out["judged"] = len(judged)
    out["failed"] = fail
    if not judged:
        print(json.dumps(out, ensure_ascii=False))
        return

    # 交还
    scores = [payload for _, payload in judged]
    # v2.1 (缺口2): submitted 只回显 passed (relevant 数) — 无法回答"交还调用
    # 是否成功"。MCP 超时可能发生在请求前(未提交)或响应后(已提交但没收到回执) —
    # 脚本如实标注 submit_state: "ok"=收到回执 / "timeout_unclear"=超时不确定
    # (宿主需用 vibe_sub_health/vibe_keywords 交叉核验 pending 是否清空, 别重复
    # 提交已处理的 id — 服务端对已评分 id 返回 error 而非双计, 幂等安全)。
    try:
        resp = mc.call("vibe_submit_score", {"scores": scores})
        out["submitted"] = int(resp.get("passed") or 0)
        out["submit_state"] = "ok"
        out["submit_resp"] = {k: resp.get(k) for k in
                              ("passed", "rejected", "errors", "quota_used")
                              if resp.get(k) is not None}
    except Exception as e:  # noqa: BLE001
        out["failed"] += 1
        out["submit_state"] = "timeout_unclear"
        out["submit_err"] = str(e)[:150]
        print(f"  ❌ 交还超时/失败 (状态不确定 — 用 health 核验): {str(e)[:100]}",
              file=sys.stderr)
    out["relevant"] = sum(1 for _, pl in judged if pl["verdict"] == "relevant")
    # 升级带: 落在不确定带 max(p1,p2) ∈ [0.3,0.7] 的条目 —— 给人/agent 复核用; 不改变已交结果
    #   (2026-09-21 判据调整: 原为"两问不一致"; 1145 条实测同升级率下其自动带错误翻倍)
    out["escalate_ids"] = escalate_ids
    out["escalate_note"] = ("这些条目**落在不确定带 max(p1,p2) ∈ [%.1f,%.1f]** "
                            "(连 Jev 自己也不确定) → 建议用 judge_prompt 复核; "
                            "服务端只存你回传的 verdict/confidence, 不会替你改"
                            % (ESCALATE_LO, ESCALATE_HI))
    out["confidence_submitted"] = sum(1 for _, pl in judged if "confidence" in pl)
    if args.record_answers and answers_out:
        with open(args.record_answers, "w", encoding="utf-8") as fh:
            json.dump({"model": args.jev_model, "sub_id": args.sub,
                       "answers": answers_out}, fh, ensure_ascii=False, indent=1)
        out["recorded_answers"] = args.record_answers
    if args.out:
        _save_evidence(args.out, args.sub, product, judged, args.out_format)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
