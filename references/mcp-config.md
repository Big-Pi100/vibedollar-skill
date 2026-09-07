# vibedollar MCP Client Config（参考 — 一次性配置, 按需加载）

> 何时读本文件：首次连接 vibedollar MCP、换 MCP 客户端、配 header 鉴权。

## 连接配置

```json
{
  "mcpServers": {
    "vibedollar": {
      "type": "http",
      "url": "https://mcp.vibedollar.net/mcp",
      "headers": {
        "Authorization": "Bearer <your-key>"
      }
    }
  }
}
```

Some clients (Claude Desktop / Cursor) allow headers via env/config; set
`Authorization: Bearer <key>` on the server headers per their docs. Alternative
header: `Api-Key: <key>`.

## 连接后首次流程

Connect → `vibe_register` → configure the key in the header → call data tools
(Reddit collection, matching and state are vibedollar's; judging and keyword
tuning are yours — see SKILL.md **Managing delivery health**).

## 协议（本地脚本用, 如 scripts/mcp.py）

MCP Streamable HTTP: `POST {url}/mcp`, headers `Accept: application/json,
text/event-stream`, session 经 `Mcp-Session-Id` 维持; `tools/call` 前先
`initialize`。纯 stdlib 客户端见 `scripts/mcp.py`。
