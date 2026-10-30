import os, sys, json, logging, traceback
logging.basicConfig(level=logging.ERROR)
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL'] = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\test_openapi2.db'
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
out = []
spec = None
try:
    with TestClient(app) as c:
        r = c.get('/openapi.json')
        out.append('openapi status %s' % r.status_code)
        spec = r.json()
    paths = spec.get('paths', {})
    rows = []
    for p, methods in paths.items():
        for m, op in methods.items():
            if m == 'parameters':
                continue
            rows.append((m.upper(), p, op.get('summary',''), op.get('operationId',''), op.get('tags',[]), op.get('security',[])))
    rows.sort()
    out.append('num paths %d num operations %d' % (len(paths), len(rows)))
    for r_ in rows:
        out.append('%s %s | %s | tags=%s | security=%s' % r_)
except Exception as e:
    out.append('ERROR: %s' % e)
    out.append(traceback.format_exc())
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\routes_dump2.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(out))
if spec:
    with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\openapi_spec.json','w',encoding='utf-8') as f:
        json.dump(spec, f, indent=2)
print('done')
