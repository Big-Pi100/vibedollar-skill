#!/usr/bin/env python3
"""sd_doc — 订阅供需分析的本地文档读写 (纯执行器, 无决策)。

背景 (v2.1 用户定稿): prompt 资产不用占位符替换机制 — 供需分析是**运行时数据
文档**, 生成/校准后存为本地 `data/sd_<sid>.md`, 判分/生词/优化时由宿主 agent
读取该文件、把内容注入 LLM user 消息 (agent 读文件 = 原生能力, 无需 replace)。
本脚本只做机械文件操作:

    python3 sd_doc.py fetch --sub 12        # 从 vibe_list_subs 拉 sd_json → 写 data/sd_12.md
                                            # (dry 只打印不写: 加 --dry-run)
    python3 sd_doc.py show  --sub 12        # 打印 data/sd_12.md 内容 (供核对)
    python3 sd_doc.py show  --sub 12 --values  # 只出四字段值 (剥离自描述头 —
                                            # 直接注入 LLM user 消息用, 防记号泄漏)
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
    ap.add_argument("--values", action="store_true",
                    help="show: 只出四字段值 (剥离自描述头, 供注入)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = _doc_path(args.sub)

    if args.cmd == "write":
        try:
            sd = json.loads(args.json)
        except json.JSONDecodeError:
            print("bad --json")
            return 2
        # v2.1 (2026-09-08): 800 上限校验 — 超限警告 (后端 vibe_sd_update 同限,
        # 不静默 — 提示 agent 重生成压缩段)
        over = {k: len(str(sd.get(k) or "")) for k in KEYS
                if len(str(sd.get(k) or "")) > 800}
        if over:
            print(f"⚠️ 字段超 800 上限 (后端会截断): "
                  f"{', '.join(f'{k}={n}' for k, n in over.items())}")
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
            content = f.read()
        if args.values:
            # --values: 只出四字段值 (剥离自描述头) — 供直接注入 LLM user 消息,
            # 避免整体粘贴把 "[SUPPLY/DEMAND STRUCTURE]" 说明行泄漏给 LLM
            sd = _from_md(path)
            for k in KEYS:
                print(str(sd.get(k) or ""))
        else:
            print(content)
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
    # v2.1 (2026-09-08): 后端已是 800 截断口径 — 若本地旧文档字段更长,
    # 提示漂移 (本地完整 vs 后端截断 → 需按 ≤800 重生成或用后端为准)
    if os.path.exists(path):
        try:
            local = _from_md(path)
            drift = [k for k in KEYS
                     if len(str(local.get(k) or "")) > len(str(sd.get(k) or ""))]
            if drift:
                print(f"⚠️ 本地文档比后端长 (后端 800 截断?) — 字段: {drift} — "
                      f"以后端为准已重写; 如需完整版请重生成 ≤800 段")
        except Exception:  # noqa: BLE001
            pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_to_md(args.sub, sd))
    print(f"fetched → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
