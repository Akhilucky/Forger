from __future__ import annotations

import json
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from forge.generator.engine import Engine
from forge.generator.inference import guess_field_type


MOCK_ENDPOINTS: dict[str, list[dict]] = {}


def _infer_columns_from_path(path: str) -> list[dict]:
    path = path.strip("/").lower()
    if not path or path == "api":
        path = "data"
    parts = path.split("/")
    resource = parts[-1] if parts else "data"

    schemas = {
        "users": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "age", "type": "integer"},
            {"name": "phone", "type": "string"},
            {"name": "city", "type": "string"},
            {"name": "state", "type": "string"},
        ],
        "products": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "price", "type": "float"},
            {"name": "category", "type": "string"},
            {"name": "in_stock", "type": "boolean"},
        ],
        "orders": [
            {"name": "id", "type": "integer"},
            {"name": "user_id", "type": "integer"},
            {"name": "product_id", "type": "integer"},
            {"name": "quantity", "type": "integer"},
            {"name": "total", "type": "float"},
            {"name": "status", "type": "string"},
            {"name": "created_at", "type": "string"},
        ],
        "customers": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "company", "type": "string"},
            {"name": "industry", "type": "string"},
        ],
        "transactions": [
            {"name": "id", "type": "integer"},
            {"name": "amount", "type": "float"},
            {"name": "currency", "type": "string"},
            {"name": "status", "type": "string"},
            {"name": "timestamp", "type": "string"},
            {"name": "merchant", "type": "string"},
        ],
        "employees": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "department", "type": "string"},
            {"name": "job_title", "type": "string"},
            {"name": "salary", "type": "float"},
        ],
        "posts": [
            {"name": "id", "type": "integer"},
            {"name": "title", "type": "string"},
            {"name": "content", "type": "string"},
            {"name": "author", "type": "string"},
            {"name": "published_at", "type": "string"},
            {"name": "tags", "type": "string"},
        ],
    }

    resource_singular = resource.rstrip("s") if resource.endswith("s") else resource
    for key, cols in schemas.items():
        if key == resource or key.rstrip("s") == resource_singular:
            return cols
    return schemas.get("users", [{"name": "id", "type": "integer"}, {"name": "value", "type": "string"}])


class MockHandler(BaseHTTPRequestHandler):
    engine: Engine = Engine()
    columns: list[dict] = []

    def _respond(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _parse_query(self) -> dict:
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        return {k: v[0] for k, v in qs.items()}

    def do_OPTIONS(self):
        self._respond({})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/" or path == "":
            endpoints = MOCK_ENDPOINTS or {
                "/users": "GET /users — list users",
                "/users/:id": "GET /users/1 — get one user",
                "/products": "GET /products — list products",
                "/orders": "GET /orders — list orders",
                "/customers": "GET /customers — list customers",
                "/employees": "GET /employees — list employees",
                "/posts": "GET /posts — list posts",
                "/transactions": "GET /transactions — list transactions",
                "/api/<resource>": "Any plural noun auto-generates an endpoint",
            }
            return self._respond({
                "service": "Forge Mock API",
                "version": "0.2.0",
                "endpoints": endpoints,
            })

        params = self._parse_query()
        count = min(int(params.get("_count", params.get("count", "10"))), 10000)

        path_parts = path.strip("/").split("/")
        resource_path = "/".join(p for p in path_parts if not p.isdigit())

        item_id = None
        for p in path_parts:
            if p.isdigit():
                item_id = int(p)
                break

        columns = self.columns
        if not columns:
            if resource_path in MOCK_ENDPOINTS:
                columns = MOCK_ENDPOINTS[resource_path]
            else:
                columns = _infer_columns_from_path(resource_path)

        if item_id is not None:
            record = self.engine.generate_from_spec(columns, 1)
            if record:
                record[0]["id"] = item_id
            return self._respond(record[0] if record else {})

        records = self.engine.generate_from_spec(columns, count)
        next_id = 1
        for r in records:
            if "id" in r:
                r["id"] = next_id
                next_id += 1

        resp = {
            "data": records,
            "count": len(records),
            "endpoint": f"/{resource_path}",
        }

        page = params.get("_page", params.get("page", "1"))
        if page.isdigit() and int(page) > 0:
            resp["page"] = int(page)
            resp["total_pages"] = 10

        return self._respond(resp)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}
        return self._respond({
            "status": "created",
            "resource": parsed.path,
            "body": data,
        }, 201)

    def log_message(self, format, *args):
        pass


def start_mock_server(
    port: int = 8000,
    columns: list[dict] | None = None,
    schema_file: str | None = None,
    silent: bool = False,
):
    if schema_file:
        import yaml
        with open(schema_file) as f:
            schemas = yaml.safe_load(f) or {}
            for resource, cols in schemas.items():
                if isinstance(cols, list):
                    MOCK_ENDPOINTS[resource] = cols

    server = HTTPServer(("0.0.0.0", port), MockHandler)
    if columns:
        MockHandler.columns = columns

    if not silent:
        print(f"⚡ Forge Mock API running on http://localhost:{port}")
        print(f"   Try: curl http://localhost:{port}/users")
        print(f"   Try: curl http://localhost:{port}/users/5")
        print(f"   Try: curl http://localhost:{port}/products?count=50")
        print(f"   Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if not silent:
            print("\n✗ Server stopped")
        server.server_close()
