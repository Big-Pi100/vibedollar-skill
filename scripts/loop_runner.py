#!/usr/bin/env python3
"""loop_runner — 订阅循环的**定时器模板** (客户侧, BYOK; 2026-09-22).

为什么需要它: skill 把循环交给宿主 agent, 但**没有宿主侧定时器**时, 循环会停在半路 ——
线上实测过三种半截: ① intake 不动 (8 个客户订阅里 6 个判定停在 11~14 天前或从未判过);
② outreach 不动 (sub 355 交付 655 条只有 166 条有草稿, 最近 10 条全无草稿; 345/367 草稿 0 条);
③ word_face 不动 (跑通了也一直 0 交付)。本模板补的是"按时跑"这一层, 判定口径仍用 skill 的
judge_prompt.md, 服务端零语义不变。

它做两段, **都是机械动作**:
  intake   = 调 scripts/score_batch.py (领取 → 并行判真 → 交回)
  outreach = 对"该写但没草稿"的交付线索取任务书 → 用你的 LLM 写 ≤18 词 → 交回服务端复核落库
**绝不自动发帖**: 发帖是对外动作, 必须由你/你的 agent 决定; 发出后调 vibe_outreach_sent(lead_id),
有结果再调 vibe_mark_leads(outcome=valid|invalid|contacted)。

凭据 (BYOK, 全部走环境变量或参数, 模板不读任何数据库):
  VIBEDOLLAR_API_KEY / --key        你的 vibedollar key
  LLM_API_KEY / --llm-key           你自己的 LLM key (判真 + 写草稿)
  VIBEDOLLAR_MCP_URL / --mcp-url    MCP 端点 (默认 https://mcp.vibedollar.net/mcp;
                                    自建/内网部署时用它指向你的端点)

成本闸门 (默认保守; 领取即计费):
  --limit N            每次每订阅最多领 N 条 (默认 10)
  --daily-cap N        每订阅每日最多领 N 条 (默认 60) —— 状态落在 --state 指定的 JSON
  --outreach-per-sub N 每次每订阅最多补 N 条草稿 (默认 5)
  --stage intake|outreach|both (默认 both; outreach 不领取)

装成定时任务 (每 30 分钟一轮; 稳态每天一次也够 —— 见 SKILL.md "Loop cadence"):
  cron:
    */30 * * * * cd /path/to/vibedollar-skill && VIBEDOLLAR_API_KEY=... LLM_API_KEY=... \
      python3 scripts/loop_runner.py >> loop_runner.log 2>&1
  systemd (两个文件):
    # ~/.config/systemd/user/vibedollar-loop.service
    [Service]
    Type=oneshot
    WorkingDirectory=/path/to/vibedollar-skill
    Environment=VIBEDOLLAR_API_KEY=... LLM_API_KEY=...
    ExecStart=/usr/bin/python3 scripts/loop_runner.py
    # ~/.config/systemd/user/vibedollar-loop.timer
    [Timer]
    OnCalendar=*:0/30
    Persistent=true
    [Install]
    WantedBy=timers.target
    # systemctl --user enable --now vibedollar-loop.timer
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp import MCPClient  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT_MAX_WORDS = 18


def _log(msg: str, log_path: str = "") -> None:
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    if log_path:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass


def _load_state(path: str) -> dict:
    try:
        d = json.load(open(path, encoding="utf-8"))
        if d.get("date") == time.strftime("%Y-%m-%d"):
            return d
    except Exception:  # noqa: BLE001
        pass
    return {"date": time.strftime("%Y-%m-%d"), "claimed": {}}


def _save_state(path: str, d: dict) -> None:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def _llm_write_draft(prompt: str, llm_key: str, base: str, model: str,
                     timeout: int = 90) -> str:
    body = json.dumps({"model": model, "temperature": 0.4, "max_tokens": 400,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + llm_key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    txt = ((d.get("choices") or [{}])[0].get("message", {}) or {}).get("content", "") or ""
    txt = txt.strip().strip('"').replace("\n", " ").strip()
    w = txt.split()
    return " ".join(w[:DRAFT_MAX_WORDS]) if len(w) > DRAFT_MAX_WORDS else txt


def _subs(mc: MCPClient) -> list:
    r = mc.call("vibe_list_subs")
    d = r.get("data", r) if isinstance(r, dict) else {}
    out = []
    for s in (d.get("subscriptions", []) if isinstance(d, dict) else []):
        if str(s.get("status") or "active") != "active":
            continue
        out.append({"id": int(s.get("id") or 0), "product": str(s.get("product") or "")[:40],
                    "dropped": bool(s.get("sd_missing"))})
    return [s for s in out if s["id"]]


def _outreach(args, mc: MCPClient, sid: int, state: dict) -> int:
    """给该订阅"该写但没草稿"的交付线索补草稿 (服务端口径: has_draft 空 且 draft_skip 空)。"""
    try:
        r = mc.call("vibe_delivered", {"subscription_id": sid, "limit": 50})
    except Exception as e:  # noqa: BLE001
        _log("sub%s 取已交付失败: %s" % (sid, str(e)[:80]), args.state_log)
        return 0
    d = r.get("data", r) if isinstance(r, dict) else {}
    rows = d.get("posts") or d.get("delivered") or []
    todo = [x for x in rows
            if x.get("delivered_id") and not x.get("has_draft") and not x.get("draft_skip")]
    n_ok = 0
    for x in todo[:args.outreach_per_sub]:
        dlid = int(x["delivered_id"])
        try:
            adv = mc.call("vibe_outreach_advice",
                          {"delivered_id": dlid, "include_body": True})
            pr = (adv or {}).get("draft_prompt") or ""
            if not pr:
                continue                      # 服务端否决 (draft_skip) 或该线索不该回
            txt = _llm_write_draft(pr, args.llm_key, args.llm_base, args.llm_model)
            if not txt:
                continue
            sv = mc.call("vibe_outreach_advice", {"delivered_id": dlid, "draft": txt})
            bad = ((sv or {}).get("draft_check") or {}).get("errors")
            if bad:
                _log("sub%s 草稿被复核打回 id=%s: %s" % (sid, dlid, str(bad)[:100]), args.state_log)
            else:
                n_ok += 1
        except Exception as e:  # noqa: BLE001 — 单条失败不影响其余
            _log("sub%s 写草稿失败 id=%s: %s" % (sid, dlid, str(e)[:80]), args.state_log)
        time.sleep(1.0)
    if todo:
        _log("sub%s 触达: 该写 %d 条 → 落库 %d 条草稿 (发出仍需你/你的 agent: vibe_outreach_sent)"
             % (sid, len(todo), n_ok), args.state_log)
    return n_ok


def main() -> int:
    ap = argparse.ArgumentParser(description="订阅循环定时器模板 (intake + 写草稿)")
    ap.add_argument("--key", default=os.environ.get("VIBEDOLLAR_API_KEY", ""))
    ap.add_argument("--llm-key", default=os.environ.get("LLM_API_KEY", ""))
    ap.add_argument("--llm-base", default=os.environ.get("LLM_BASE", "https://api.deepseek.com/v1"))
    ap.add_argument("--llm-model", default=os.environ.get("LLM_MODEL", "deepseek-chat"))
    ap.add_argument("--mcp-url", default=os.environ.get("VIBEDOLLAR_MCP_URL", ""))
    ap.add_argument("--subs", default="", help="只跑这些订阅 id (逗号分隔; 空=账号下全部 active)")
    ap.add_argument("--stage", default="both", choices=("intake", "outreach", "both"))
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--daily-cap", type=int, default=60)
    ap.add_argument("--outreach-per-sub", type=int, default=5)
    ap.add_argument("--state", default=os.path.join(HERE, "..", "data",
                                                    "loop_runner_state.json"))
    ap.add_argument("--log", default="", help="日志文件 (可选)")
    ap.add_argument("--sleep", type=float, default=5.0)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    args.state_log = args.log

    if not args.key:
        sys.exit("缺少 vibedollar key — 设 VIBEDOLLAR_API_KEY 或 --key")
    if args.llm_key and args.llm_base:
        os.environ.setdefault("LLM_API_KEY", args.llm_key)
        os.environ.setdefault("LLM_BASE", args.llm_base)
        os.environ.setdefault("LLM_MODEL", args.llm_model)
    mc = MCPClient(args.key, url=args.mcp_url) if args.mcp_url else MCPClient(args.key)

    subs = _subs(mc)
    want = [int(x) for x in args.subs.split(",") if x.strip()]
    if want:
        subs = [s for s in subs if s["id"] in want]
    if not subs:
        _log("没有适格订阅 (检查 key / --subs)", args.log)
        return 0

    state = _load_state(args.state)
    claimed = state.get("claimed") or {}
    picked = 0
    for s in subs:
        sid = s["id"]
        used = int(claimed.get(str(sid), 0))
        left = args.daily_cap - used
        if args.stage != "outreach":
            if left <= 0:
                _log("sub%s 当日额度用尽 (%d/%d) — 跳过 intake"
                     % (sid, used, args.daily_cap), args.log)
            elif args.dry_run:
                _log("sub%s %s → 将领取≤%d (dry-run, 不领取)" % (sid, s["product"], min(args.limit, left)), args.log)
            else:
                cmd = [sys.executable, os.path.join(HERE, "score_batch.py"),
                       "--sub", str(sid), "--limit", str(min(args.limit, left)),
                       "--key", args.key, "--llm-key", args.llm_key, "--engine", "llm",
                       "--llm-base", args.llm_base, "--llm-model", args.llm_model,
                       "--judge", os.path.join(HERE, "judge_prompt.md")]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       timeout=args.timeout, cwd=os.path.dirname(HERE),
                                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                    res = {}
                    for line in reversed((r.stdout or "").strip().splitlines()):
                        if line.strip().startswith("{"):
                            try:
                                res = json.loads(line)
                                break
                            except Exception:  # noqa: BLE001
                                pass
                    claimed[str(sid)] = used + int(res.get("claimed") or 0)
                    _log("sub%s [%s] intake → claimed=%s judged=%s relevant=%s submitted=%s%s"
                         % (sid, s["product"], res.get("claimed"), res.get("judged"),
                            res.get("relevant"), res.get("submitted"),
                            "" if r.returncode == 0 else " ⚠️rc=%d %s" % (r.returncode, (r.stderr or "")[-70:])),
                         args.log)
                except subprocess.TimeoutExpired:
                    _log("sub%s intake 超时 (%ds)" % (sid, args.timeout), args.log)
                except Exception as e:  # noqa: BLE001
                    _log("sub%s intake 失败: %s" % (sid, str(e)[:90]), args.log)
        if args.stage in ("outreach", "both") and not args.dry_run:
            try:
                _outreach(args, mc, sid, state)
            except Exception as e:  # noqa: BLE001
                _log("sub%s 触达失败: %s" % (sid, str(e)[:90]), args.log)
        picked += 1
        if args.sleep:
            time.sleep(args.sleep)
    state["claimed"] = claimed
    _save_state(args.state, state)
    _log("完成: %d 个订阅 (当日累计领取 %s)"
         % (picked, {k: v for k, v in claimed.items() if v}), args.log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
