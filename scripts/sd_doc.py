#!/usr/bin/env python3
"""sd_doc — 订阅供需分析的本地文档读写 (纯执行器, 无决策)。

背景 (v2.1 用户定稿): prompt 资产不用占位符替换机制 — 供需分析是**运行时数据
文档**, 生成/校准后存为本地 `data/sd_<sid>.md`, 判分/生词/优化时由宿主 agent
读取该文件、把内容注入 LLM user 消息 (agent 读文件 = 原生能力, 无需 replace)。
本脚本只做机械文件操作:

    python3 sd_doc.py fetch --sub 12        # 从 vibe_list_subs 拉 sd_json → 写 data/sd_12.md
                                            # (dry 只打印不写: 加 --dry-run)
    python3 sd_doc.py show  --sub 12        # 打印 data/sd_12.md 内容 (供注入/核对)
    python3 sd_doc.py write --sub 12 --json '{...}'   # 手动写 sd (校准后) → data/sd_12.md
                                            # (不调 vibe_sd_update — 持久化由 agent 决定)

env: VIBEDOLLAR_API_KEY (fetch 用); MCP 走公共端点。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp import MCPClient  # noqa: E402

KEYS = ("supply_side", "demand_side", "core_friction", "demand_pain")


def _doc_path(sid: int) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", f"sd_{sid}.md")


def _to_md(sid: int, sd: dict) -> str:
    lines = [
        f"# Subscription {sid} — supply/demand profile",
        "",
        "Runtime data document. Inject this content into LLM user messages for",
        "scoring / keyword generation / optimization ([SUPPLY/DEMAND STRUCTURE]).",
        "Backend copy lives in product_subs.sd_json (vibe_sd_update) — keep in sync.",
        "",
        f"- subscription_id: {sid}",
    ]
    for k in KEYS:
        lines.append(f"- {k}: {str(sd.get(k) or '')}")
    return "\n".join(lines) + "\n"


def _from_md(path: str) -> dict:
    sd: dict = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            for k in KEYS:
                if line.startswith(f"- {k}:"):
                    sd[k] = line[len(f"- {k}:"):].strip()
    return sd


def main() -> int:
    ap = argparse.ArgumentParser(description="供需分析本地文档读写 (纯执行器)")
    ap.add_argument("cmd", choices=["fetch", "show", "write"])
    ap.add_argument("--sub", type=int, required=True)
    ap.add_argument("--json", default="", help="write: sd JSON (四段)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = _doc_path(args.sub)

    if args.cmd == "write":
        try:
            sd = json.loads(args.json)
        except json.JSONDecodeError:
            print("bad --json")
            return 2
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_to_md(args.sub, sd))
        print(f"written {path}")
        return 0

    if args.cmd == "show":
        if not os.path.exists(path):
            print(f"NO DOC {path} — run: sd_doc.py fetch --sub {args.sub}")
            return 1
        with open(path, encoding="utf-8") as f:
            print(f.read())
        return 0

    # fetch
    key = os.environ.get("VIBEDOLLAR_API_KEY", "")
    if not key:
        print("missing VIBEDOLLAR_API_KEY")
        return 2
    mc = MCPClient(key)
    ls = mc.call("vibe_list_subs")
    subs = ls.get("data", ls).get("subscriptions", [])
    sub = next((s for s in subs if int(s.get("id") or 0) == args.sub), None)
    if not sub:
        print(f"sub {args.sub} not found")
        return 1
    try:
        sd = json.loads(str(sub.get("sd_json") or "{}"))
    except json.JSONDecodeError:
        sd = {}
    if args.dry_run:
        print(_to_md(args.sub, sd))
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_to_md(args.sub, sd))
    print(f"fetched → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
