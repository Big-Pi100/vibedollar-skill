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
        return {"verdict": str(d.get("verdict", "irrelevant")).lower(),
                "score": int(d.get("score", 0)),
                "reason": str(d.get("reason", ""))[:300]}
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
    args = ap.parse_args()

    if not args.key:
        sys.exit("缺少 vibedollar key — 设 VIBEDOLLAR_API_KEY 或 --key")
    if not args.llm_key and not args.dry_run:
        sys.exit("缺少 LLM key — 设 LLM_API_KEY 或 --llm-key (dry-run 除外)")

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
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        futs = {}
        for p in leads:
            lid = p.get("id")
            if lid is None:
                continue
            futs[ex.submit(_llm_judge, args.llm_base, args.llm_model,
                           args.llm_key, prompt, product, p)] = (p, lid)
        for fu in as_completed(futs):
            p, lid = futs[fu]
            j = fu.result()
            if not j:
                fail += 1
                continue
            payload = {"id": int(lid),
                       "verdict": "relevant" if j["score"] >= args.threshold
                       else "irrelevant",
                       "score": j["score"], "reason": j["reason"]}
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
    if args.out:
        _save_evidence(args.out, args.sub, product, judged, args.out_format)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
