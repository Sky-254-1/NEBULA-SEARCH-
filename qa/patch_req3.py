import re

p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_runner.py'
s = open(p, encoding='utf-8').read()

# 1) await init_db() in run()
if 'asyncio.run(init_db())' not in s:
    s = s.replace('init_db()\n', 'asyncio.run(init_db())\n', 1)

# 2) Make the final `raise RuntimeError(...)` in req() return instead of raise
if 'raise RuntimeError(f"request raised: {detail}") from exc' in s:
    s = s.replace(
        'raise RuntimeError(f"request raised: {detail}") from exc',
        'return resp, duration_ms',
    )

# 3) Verify the openapi block exists in test_health_system
openapi_marker = 'resp, d = self.req("GET", "/openapi.json")'
if openapi_marker not in s:
    raise SystemExit('openapi marker not found')

open(p, 'w', encoding='utf-8').write(s)
print('patched: init_db awaited; req returns synthetic 500 (no raise)')
