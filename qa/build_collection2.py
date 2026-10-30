import json

BASE = "{{baseUrl}}"
COLL = {
  "info": {
    "name": "Nebula Search API — QA Regression Collection",
    "_postman_id": "nebula-search-qa-collection",
    "description": ("Functional, authorization, security, and regression tests for the Nebula Search API.\n"
                    "Uses environment variables only — no secrets or real tokens are stored here.\n"
                    "Run against a dedicated test environment (never production).\n"
                    "Base URL: {{baseUrl}}\n"
                    "Auth: Bearer {{accessTokenUserA}} / {{accessTokenUserB}} / {{accessTokenAdmin}}"),
    "schema": "https://schema.postman.com/collection/v2.1.0/collection.json",
    "version": "1.0.0"
  },
  "variable": [
    {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
    {"key": "responseTimeThresholdMs", "value": "2000", "type": "string"}
  ],
  "item": []
}

def folder(name):
    return {"name": name, "item": []}

def req(name, method, path, headers=None, raw_body=None, query=None):
    url_path = [p for p in path.split("/") if p]
    url = {"raw": BASE + path, "host": [BASE], "path": url_path}
    if query:
        url["query"] = query
    r = {
        "name": name,
        "request": {
            "method": method,
            "header": headers or [],
            "url": url,
            "body": None
        },
        "event": []
    }
    if raw_body is not None:
        r["request"]["body"] = {"mode": "raw", "raw": raw_body, "options": {"raw": {"language": "json"}}}
    return r

def auth_header(token):
    return {"key": "Authorization", "value": "Bearer " + token}

def test(item, lines):
    item["event"].append({"listen": "test", "script": {"exec": lines, "type": "text/javascript"}})
    return item

def add(folder_obj, item):
    folder_obj["item"].append(item)

T = "pm.test"
def t_ok(cond, msg):
    return "pm.test(%r, function () { pm.expect(%s).to.be.%s; });" % (msg, cond, "true" if cond.startswith("pm.response") else cond)
