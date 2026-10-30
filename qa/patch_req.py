import re

p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_runner.py'
s = open(p, encoding='utf-8').read()

# 1) Add 'import types' near the top
if 'import types' not in s:
    s = s.replace('import time', 'import types\nimport time', 1)

# 2) Replace the req() method body with a resilient version
start = s.index('    def req(self')
end = s.index('    def assert_status(self')
new = '''    def req(self, method, path, token=None, json=None, params=None,
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
            detail = body[-800:]
            resp = types.SimpleNamespace(
                status_code=500,
                headers={"content-type": "application/json"},
                text='{"detail": "OpenAPI schema generation failed"}',
            )
            duration_ms = (time.perf_counter() - t0) * 1000
            raise RuntimeError(f"request raised: {detail}") from exc
        duration_ms = (time.perf_counter() - t0) * 1000
        return resp, duration_ms

'''
s = s[:start] + new + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('patched req + import types')
