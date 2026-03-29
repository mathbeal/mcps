# API Documentation

All servers expose a FastMCP HTTP API. When a server is running, its OpenAPI spec is available at:

```
http://localhost:<port>/openapi.json
http://localhost:<port>/docs        (Swagger UI)
```

## Endpoints by server

| Server   | Port | OpenAPI spec                          | Swagger UI                       |
|----------|------|---------------------------------------|----------------------------------|
| gps      | 8101 | http://localhost:8101/openapi.json    | http://localhost:8101/docs       |
| wingfoil | 8102 | http://localhost:8102/openapi.json    | http://localhost:8102/docs       |

## MCP protocol

Servers accept MCP messages at the root path via POST. The streamable-http transport
supports both single-response and streaming (SSE) modes.

```
POST http://localhost:<port>/
Content-Type: application/json

{ "jsonrpc": "2.0", "method": "tools/call", "params": { ... } }
```

For tool schemas, call the `tools/list` method or inspect the Swagger UI.
