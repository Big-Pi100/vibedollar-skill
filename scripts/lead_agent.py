#!/usr/bin/env python3
"""vibedollar Lead Agent — headless auto mode (无头自动模式).

Runs the full vibedollar loop the way the product intends: an agent claims
candidate leads, judges them with YOUR OWN LLM (any OpenAI-compatible API),
and submits scores back through MCP. Only verdicts you judge "relevant"
count against your vibedollar delivery quota; candidates are free.

This is the same loop vibedollar's own marketing fleet runs (dogfooded in
production) — packaged here so any user can run it with just two keys:
  - VIBEDOLLAR_API_KEY  (from vibe_verify / your account page)
  - LLM_API_KEY         (any OpenAI-compatible provider: DeepSeek, OpenAI, ...)

Judgment rubric: edit `judge_prompt.md` next to this script to match YOUR
definition of a good customer (the file is a plain, editable template).

Usage:
  export VIBEDOLLAR_API_KEY=...            # vibedollar key
  export LLM_API_KEY=...                   # your LLM key
  export LLM_BASE_URL=https://api.deepseek.com/v1   # OpenAI-compatible base
  export LLM_MODEL=deepseek-chat
  python3 lead_agent.py --limit 10                  # one pass, all subs
  python3 lead_agent.py --sub 12 --out ./evidence   # one sub + save relevant
  python3 lead_agent.py --loop 3600                 # hourly daemon loop
  python3 lead_agent.py --dry-run                   # claim only, no LLM/no submit

All settings also available as CLI flags (see --help). No vibedollar-internal
dependencies — pure stdlib (urllib), works anywhere Python 3.9+ runs.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.request

MCP_URL = os.environ.get("VIBEDOLLAR_MCP_URL", "https://mcp.vibedollar.net/mcp")
HTTP_TIMEOUT = 60
MAX_SCORE_BATCH = 50          # 对齐 vibe_submit_score 单批上限
PROTOCOL_VERSION = "2025-03-26"
DEFAULT_THRESHOLD = 60        # score >= threshold → verdict=relevant (editable)
UA = "Mozilla/5.0 (compatible; vibedollar-lead-agent/0.1; +https://vibedollar.net)"

# 判真模板兜底 (scripts/judge_prompt.md 存在则优先 — 用户可编辑)
DEFAULT_JUDGE_PROMPT = """You are a lead-qualification analyst for ONE product. Decide whether the author of a
Reddit post is a real potential customer of the product described by the user.

Judgment rules:
1. RELEVANT = the author (a) clearly faces the problem the product solves, OR
   (b) is actively doing / investing in the activity the product serves —
   sharing results, asking technique questions, discussing the category —
   even if the post never mentions the product. Prospects do not name
   products; people who name your product are already buyers, not prospects.
2. NOT relevant = unrelated topic, pure entertainment, methodology-only
   discussion, or the author is clearly outside the product's demand-side scene.
3. Score 0-100 by fit:
   - 85-100: explicit pain / request that the product directly solves
   - 60-84:  clearly in-scene and actively invested (persona confirmed)
   - 30-59:  weak / edge relevance
   - 0-29:   unrelated or out-of-scene
4. Output STRICT JSON only, no other text:
   {"verdict": "relevant"|"irrelevant", "score": <0-100>, "reason": "one line"}
   verdict = "relevant" ONLY when score >= 60.

(Edit this rubric in judge_prompt.md to tune it to your own market.)
"""


# ── 迷你 MCP Streamable HTTP 客户端 (生产验证同款: collector.py) ──────────
class MCPClient:
    def __init__(self, api_key: str):
        self._key = api_key
        self._session = ""

    def _request(self, method: str, params: dict) -> dict:
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) % 100000,
            "method": method,
            "params": params,
        }).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self._key}",
            "User-Agent": UA,
        }
        if self._session:
            headers["Mcp-Session-Id"] = self._session
        req = urllib.request.Request(MCP_URL, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                if method == "initialize":
                    sid = resp.headers.get("Mcp-Session-Id") or ""
                    self._session = sid
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"MCP HTTP {e.code}: {e.read()[:200]}")
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"MCP 连接失败: {e}")
        data = self._parse(raw)
        err = data.get("error") or data.get("result", {}).get("error")
        if err:
            raise RuntimeError(f"MCP {method} 失败: {err}")
        text = ""
        for c in data.get("result", {}).get("content", []):
            if c.get("type") == "text":
                text += c.get("text", "")
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    @staticmethod
    def _parse(raw: str) -> dict:
        """SSE 或 JSON — 取最后一个 JSON 对象。"""
        raw = raw.strip()
        if raw.startswith("event:") or "\ndata:" in raw:
            chunks = [ln[5:].strip() for ln in raw.splitlines()
                      if ln.startswith("data:") and ln[5:].strip()]
            if chunks:
                try:
                    return json.loads(chunks[-1])
                except json.JSONDecodeError:
                    pass
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def initialize(self):
        self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "vibedollar-lead-agent", "version": "0.1.0"},
        })

    def call(self, name: str, arguments: dict | None = None) -> dict:
        if not self._session:
            self.initialize()
        return self._request("tools/call", {"name": name, "arguments": arguments or {}})


# ── 用户 LLM 判真 (openai-compatible chat completions) ────────────────────
def _llm_judge(base: str, model: str, key: str, prompt: str,
               product: str, post: dict, timeout: int = 60) -> dict | None:
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
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": UA,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        text = data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001 — 网络/解析失败 → 该条跳过
        print(f"  ⚠ LLM 判真失败: {str(e)[:100]}")
        return None
    # 容错解析 (剥 markdown 代码块, 取首个 JSON 对象)
    import re
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


def _load_judge_prompt() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "judge_prompt.md")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return DEFAULT_JUDGE_PROMPT


def _post_id_of(p: dict) -> str:
    import re as _re
    u = str(p.get("url") or p.get("permalink") or "")
    m = _re.search(r"/comments/([a-z0-9]+)", u)
    return m.group(1) if m else str(p.get("post_id") or "")


def _env_or(name: str, default: str = "") -> str:
    return os.environ.get(name) or default


def run_pass(mc: MCPClient, args, prompt: str, threshold: int) -> dict:
    """单轮: 列订阅 → 每 sub 领取 → 判真 → 交还 → (可选)存证据。"""
    _ls = mc.call("vibe_list_subs")
    if isinstance(_ls, dict) and isinstance(_ls.get("data"), dict):
        _ls = _ls["data"]          # {"ok":true,"data":{"subscriptions":[...]}}
    subs = _ls.get("subscriptions", []) if isinstance(_ls, dict) else []
    if not isinstance(subs, list):
        subs = []
    active = [s for s in subs if s.get("status") in (None, "", "active")]
    if args.sub:
        active = [s for s in active if int(s.get("id") or 0) == args.sub]
    tot = {"subs": 0, "claimed": 0, "judged": 0, "relevant": 0,
           "submitted": 0, "failed": 0}

    for s in active:
        sid = int(s.get("id") or 0)
        product = str(s.get("product") or "")
        if not sid:
            continue
        tot["subs"] += 1
        try:
            r = mc.call("vibe_leads",
                        {"subscription_id": sid, "limit": args.limit})
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ sub {sid} 领取失败: {str(e)[:80]}")
            tot["failed"] += 1
            continue
        if isinstance(r, dict) and isinstance(r.get("data"), dict):
            r = r["data"]          # {"ok":true,"data":{"posts":[...],"pending":[...]}}
        posts = r.get("posts", []) if isinstance(r, dict) else []
        pending = r.get("pending", []) if isinstance(r, dict) else []
        leads = posts + pending
        if not leads:
            print(f"  · sub {sid} 无候选")
            continue
        tot["claimed"] += len(leads)
        if args.dry_run:
            print(f"  · sub {sid} (dry) 候选 {len(leads)} — 不判真不交还")
            continue
        print(f"  → sub {sid} 候选 {len(leads)} — 判真中…")

        # 判真 (顺序执行, 稳优先; 大批可后续加并行)
        judged = []  # (lead, verdict_payload)
        for p in leads:
            lid = p.get("id")
            if lid is None:
                continue
            j = _llm_judge(args.llm_base, args.llm_model, args.llm_key,
                           prompt, product, p)
            if not j:
                continue  # 判真失败 → 留 sent, 下轮 pending 重试
            # verdict 由 score 阈值判定 (不盲信 LLM 自报字段 — 门槛可调)
            payload = {"id": int(lid),
                       "verdict": "relevant" if j["score"] >= threshold
                       else "irrelevant",
                       "score": j["score"], "reason": j["reason"]}
            judged.append((p, payload))
        tot["judged"] += len(judged)
        if not judged:
            continue

        # 交还 (vibe_submit_score — relevant 才计费)
        scores = [payload for _, payload in judged]
        try:
            resp = mc.call("vibe_submit_score", {"scores": scores})
            tot["submitted"] += int(resp.get("passed") or 0)
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ sub {sid} 交还失败: {str(e)[:80]}")
            tot["failed"] += 1
        # 证据落盘 (可选 --out; csv/jsonl)
        if args.out:
            _save_evidence(args.out, sid, product, judged)
        rel = sum(1 for _, pl in judged if pl["verdict"] == "relevant")
        tot["relevant"] += rel
        print(f"  ✅ sub {sid}: 判 {len(judged)} | relevant {rel} | "
              f"交还 {len(scores)}")
    return tot


def _save_evidence(out_dir: str, sid: int, product: str,
                   judged: list) -> None:
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for p, pl in judged:
        if pl["verdict"] != "relevant":
            continue
        rows.append({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sub_id": sid,
            "product": product,
            "lead_id": pl["id"],
            "url": p.get("url") or "",
            "subreddit": p.get("subreddit") or "",
            "title": p.get("title") or "",
            "score": pl["score"],
            "reason": pl["reason"],
        })
    if not rows:
        return
    fmt = getattr(_save_evidence, "fmt", "csv")
    if fmt == "csv":
        fpath = os.path.join(out_dir, f"evidence_{time.strftime('%Y%m%d')}.csv")
        new = not os.path.exists(fpath)
        with open(fpath, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"      📄 证据 {len(rows)} 条 → {fpath}")
    else:
        fpath = os.path.join(out_dir, f"evidence_{time.strftime('%Y%m%d')}.jsonl")
        with open(fpath, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"      📄 证据 {len(rows)} 条 → {fpath}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="vibedollar Lead Agent — claim → judge (your LLM) → submit")
    ap.add_argument("--key", default=_env_or("VIBEDOLLAR_API_KEY"),
                    help="vibedollar api key (env VIBEDOLLAR_API_KEY)")
    ap.add_argument("--llm-key", default=_env_or("LLM_API_KEY"),
                    help="你的 LLM key (env LLM_API_KEY)")
    ap.add_argument("--llm-base", default=_env_or("LLM_BASE_URL",
                                                  "https://api.deepseek.com/v1"),
                    help="openai-compatible base (env LLM_BASE_URL)")
    ap.add_argument("--llm-model", default=_env_or("LLM_MODEL", "deepseek-chat"),
                    help="model (env LLM_MODEL)")
    ap.add_argument("--sub", type=int, default=0, help="只处理指定订阅 id")
    ap.add_argument("--limit", type=int, default=10, help="每订阅领取上限")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help="verdict=relevant 的 score 门槛")
    ap.add_argument("--out", default="", help="证据输出目录 (csv/jsonl)")
    ap.add_argument("--out-format", default="csv", choices=["csv", "json"])
    ap.add_argument("--loop", type=int, default=0,
                    help="循环间隔秒 (0=单轮退出)")
    ap.add_argument("--dry-run", action="store_true", help="只领取不判真不交还")
    args = ap.parse_args()
    _save_evidence.fmt = args.out_format
    if not args.key:
        sys.exit("缺少 vibedollar key — 设 VIBEDOLLAR_API_KEY 或 --key")
    if not args.llm_key and not args.dry_run:
        sys.exit("缺少 LLM key — 设 LLM_API_KEY 或 --llm-key (dry-run 除外)")

    prompt = _load_judge_prompt()
    mc = MCPClient(args.key)
    while True:
        t0 = time.time()
        try:
            tot = run_pass(mc, args, prompt, args.threshold)
            print(f"轮次汇总: 订阅 {tot['subs']} | 候选 {tot['claimed']} | "
                  f"判真 {tot['judged']} | relevant {tot['relevant']} | "
                  f"交还通过 {tot['submitted']} | 失败 {tot['failed']}"
                  + (" (dry-run)" if args.dry_run else ""))
        except Exception as e:  # noqa: BLE001 — 单轮异常不崩
            print(f"⚠ 轮次失败: {str(e)[:200]}")
        if not args.loop:
            break
        time.sleep(max(1, args.loop - (time.time() - t0)))


if __name__ == "__main__":
    main()
