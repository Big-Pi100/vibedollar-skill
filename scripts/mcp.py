#!/usr/bin/env python3
"""vibedollar MCP Streamable HTTP 客户端 (共享基础 — 脚本工具库共用)。

纯 stdlib (urllib), 无 vibedollar 内部依赖。任何需要调 vibe_* 工具的本地脚本
import 本模块复用 (score_batch.py 等)。生产验证同款协议 (collector/lead_agent)。

用法:
    from mcp import MCPClient
    mc = MCPClient("vibedollar_api_key", url="https://mcp.vibedollar.net/mcp")
    mc.call("vibe_leads", {"subscription_id": 12, "limit": 10})
"""
from __future__ import annotations

import json
import os
import time
import urllib.request

MCP_URL = os.environ.get("VIBEDOLLAR_MCP_URL",
                         "https://mcp.vibedollar.net/mcp")
HTTP_TIMEOUT = 60
PROTOCOL_VERSION = "2025-03-26"
UA = "Mozilla/5.0 (compatible; vibedollar-skill-tools/0.1; +https://vibedollar.net)"


class MCPClient:
    def __init__(self, api_key: str, url: str = ""):
        self._key = api_key
        self._url = url or MCP_URL
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
        req = urllib.request.Request(self._url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                if method == "initialize":
                    sid = resp.headers.get("Mcp-Session-Id") or ""
                    if sid:
                        self._session = sid
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:  # noqa: BLE001
            raise RuntimeError(f"MCP HTTP {e.code}: {e.read()[:200]}")
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"MCP 连接失败: {e}")
        return self._parse(raw)

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
            "clientInfo": {"name": "vibedollar-skill-tools", "version": "0.1.0"},
        })

    def call(self, name: str, arguments: dict | None = None) -> dict:
        if not self._session:
            self.initialize()
        return self._request("tools/call", {"name": name, "arguments": arguments or {}})
