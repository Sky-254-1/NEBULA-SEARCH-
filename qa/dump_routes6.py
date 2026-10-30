import os, sys, json, logging, inspect
logging.basicConfig(level=logging.ERROR)
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL'] = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\test_openapi6.db'
os.environ['JWT_SECRET'] = 'test-secret-key-for-nebula-tests-only-0123456789'
os.environ['APP_ENV'] = 'development'
os.environ['CORS_ORIGINS'] = 'http://localhost:3000'
os.environ['RATE_LIMIT_PER_MINUTE'] = '10000'
os.environ['SIGNUP_RATE_LIMIT'] = '10000'
os.environ['LOGIN_RATE_LIMIT'] = '10000'
os.environ['REFRESH_RATE_LIMIT'] = '10000'
from app.config import get_settings
get_settings.cache_clear()
from app.main import app

AUTH_DEPS = {'get_current_user','require_admin','require_user','require_permission','require_role','get_current_user_token_payload'}
RATE_DEPS = {'rate_limit','limit_signup','limit_login','limit_refresh','rate_limit_auth'}

def dep_name(d):
    try:
        call = getattr(d, 'depends', None) or d
        fn = getattr(call, '__name__', None)
        if fn is None:
            f = getattr(call, 'func', None)
            fn = getattr(f, '__name__', None) if f else None
        if fn:
            return fn
    except Exception:
        pass
    return str(d)[:60]

rows = []
def add_route(r):
    path = getattr(r, 'path', None)
    if path is None:
        return
    methods = sorted(getattr(r, 'methods', []) or [])
    deps = []
    for d in getattr(r, 'dependencies', []) or []:
        deps.append(dep_name(d))
    ep = getattr(r, 'endpoint', None)
    ep_name = getattr(ep, '__name__', str(ep)) if ep else ''
    rows.append((path, ','.join(methods) if methods else '-', ep_name, deps))

for r in app.router.routes:
    if type(r).__name__ == '_IncludedRouter':
        for r2 in getattr(r.original_router, 'routes', []) or []:
            add_route(r2)
    else:
        add_route(r)

rows.sort(key=lambda x: (x[0], x[1]))
lines = []
lines.append('num routes %d' % len(rows))
for path, methods, ep_name, deps in rows:
    auth = [d for d in deps if d in AUTH_DEPS]
    rate = [d for d in deps if d in RATE_DEPS]
    tag = ''
    if auth: tag += '[AUTH:%s]' % ','.join(auth)
    if rate: tag += '[RATE:%s]' % ','.join(rate)
    lines.append('%-34s %-20s %-42s %s' % (methods, path, ep_name, tag))
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\routes_dump6.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done; %d routes' % len(rows))
