import os, sys, json
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL'] = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\test_openapi.db'
os.environ['JWT_SECRET'] = 'test-secret-key-for-nebula-tests-only'
os.environ['APP_ENV'] = 'testing'
os.environ['CORS_ORIGINS'] = 'http://localhost:3000'
os.environ['RATE_LIMIT_PER_MINUTE'] = '10000'
os.environ['SIGNUP_RATE_LIMIT'] = '10000'
os.environ['LOGIN_RATE_LIMIT'] = '10000'
os.environ['REFRESH_RATE_LIMIT'] = '10000'
from app.config import get_settings
get_settings.cache_clear()
from app.main import app
from fastapi.testclient import TestClient
spec = None
with TestClient(app) as c:
    r = c.get('/openapi.json')
    print('openapi status', r.status_code)
    spec = r.json()
paths = spec.get('paths', {})
rows = []
for p, methods in paths.items():
    for m, op in methods.items():
        if m in ('parameters',):
            continue
        rows.append((m.upper(), p, op.get('summary',''), op.get('operationId',''), op.get('tags',[]), op.get('security',[])))
rows.sort()
print('num paths', len(paths), 'num operations', len(rows))
for r_ in rows:
    print(r_[0], r_[1], '|', r_[2], '| tags=', r_[4], '| security=', r_[5])
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\openapi_spec.json','w') as f:
    json.dump(spec, f, indent=2)
print('saved spec')
