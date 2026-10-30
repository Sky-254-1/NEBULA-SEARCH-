import os, sys, json, logging, inspect
logging.basicConfig(level=logging.ERROR)
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL'] = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\test_openapi4.db'
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
        fn = getattr(call, '__name__', None) or getattr(call, 'func', None)
        if fn:
            return getattr(fn, '__name__', str(fn))
    except Exception:
        pass
    return str(d)[:60]

rows = []
def walk(routes, prefix=''):
    for r in routes:
        path = getattr(r, 'path', None)
        if path is None:
            continue
        full = prefix + path
        # sub-router
        sub = getattr(r, 'routes', None)
        if sub:
            walk(sub, full)
            continue
        methods = sorted(getattr(r, 'methods', []) or [])
        # dependencies
        deps = []
        for d in getattr(r, 'dependencies', []) or []:
            deps.append(dep_name(d))
        # endpoint name
        ep = getattr(r, 'endpoint', None)
        ep_name = getattr(ep, '__name__', str(ep)) if ep else ''
        rows.append((full, ','.join(methods) if methods else '-', ep_name, deps))

walk(app.routes)
rows.sort(key=lambda x: (x[0], x[1]))
lines = []
lines.append('num routes %d' % len(rows))
for path, methods, ep_name, deps in rows:
    auth = [d for d in deps if d in AUTH_DEPS]
    rate = [d for d in deps if d in RATE_DEPS]
    tag = ''
    if auth: tag += '[AUTH:%s]' % ','.join(auth)
    if rate: tag += '[RATE:%s]' % ','.join(rate)
    lines.append('%-32s %-18s %-40s %s' % (methods, path, ep_name, tag))
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\routes_dump4.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done; %d routes' % len(rows))
