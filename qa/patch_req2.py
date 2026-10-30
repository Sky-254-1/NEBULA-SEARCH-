import re

p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_runner.py'
s = open(p, encoding='utf-8').read()

# 1) await init_db() in run()
s = s.replace('        init_db()\n', '        asyncio.run(init_db())\n', 1)

# 2) Make req() return a synthetic 500 response instead of raising
old_req_start = s.index('    def req(self')
old_req_end = s.index('    def assert_status(self')
new_req = '''    def req(self, method, path, token=None, json=None, params=None,
            data=None, files=None, headers=None, expect_content_type="application/json"):
        h = dict(headers or {})
        if token:
            h["Authorization"] = f"Bearer {token}"
        t0 = time.perf_counter()
        try:
            resp = self.client.request(method, path, json=json, params=params,
                                       data=data, files=files, headers=h)
        except Exception as exc:
            # Unhandled app-level errors (e.g. OpenAPI pydantic ValidationError)
            # propagate as exceptions. Record as a 500 synthetic response so the
            # test harness can still assert on it.
            body = str(exc)
            match = re.search(r'\\d+ validation errors for OpenAPI', body)
            detail = body[-1000:]
            resp = types.SimpleNamespace(
                status_code=500,
                headers={"content-type": "application/json"},
                text=json.dumps({"detail": "OpenAPI schema generation failed: "
                                        + (match.group(0) if match else "unknown error")}),
                _app_exception=repr(exc),
            )
            duration_ms = (time.perf_counter() - t0) * 1000
            return resp, duration_ms
        duration_ms = (time.perf_counter() - t0) * 1000
        return resp, duration_ms

'''
s = s[:old_req_start] + new_req + s[old_req_end:]

# 3) Rewrite the openapi.json test block in test_health_system to handle synthetic 500
old_block = '''        resp, d = self.req("GET", "/openapi.json")
        if resp.status_code == 500:
            self.record("openapi schema generates", cat, "failed",
                        "returns 200 valid OpenAPI", "HTTP 500",
                        "critical", "GET /openapi.json no token", d,
                        "OpenAPI schema generation raises pydantic ValidationError "
                        "(SuggestionItem/SuggestionsResponse examples must be lists; $ref required)",
                        request={"method":"GET","path":"/openapi.json"},
                        response={"status":500,"body":resp.text[:500]})
        else:
            self.check("openapi schema generates", cat, resp, d, 200, "critical",
                       required_fields=["openapi","info","paths"],
                       steps="GET /openapi.json no token")'''
new_block = '''        resp, d = self.req("GET", "/openapi.json")
        if resp.status_code == 500:
            self.record("openapi schema generates", cat, "failed",
                        "returns 200 valid OpenAPI", "HTTP 500",
                        "critical", "GET /openapi.json no token", d,
                        "OpenAPI schema generation raises pydantic ValidationError "
                        "(SuggestionItem/SuggestionsResponse examples must be lists; $ref required)",
                        request={"method":"GET","path":"/openapi.json"},
                        response={"status":500,"body":resp.text[:500]})
        else:
            self.check("openapi schema generates", cat, resp, d, 200, "critical",
                       required_fields=["openapi","info","paths"],
                       steps="GET /openapi.json no token")'''
if old_block not in s:
    raise SystemExit('OLD_BLOCK not found')
s = s.replace(old_block, new_block)

open(p, 'w', encoding='utf-8').write(s)
print('patched: init_db awaited, req resilient, openapi block handled')
