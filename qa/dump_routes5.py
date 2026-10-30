import os, sys, json, logging, inspect
logging.basicConfig(level=logging.ERROR)
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL'] = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\test_openapi5.db'
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
def walk(router, prefix=''):
    prefix_path = getattr(router, 'prefix_path', '') or ''
    full_prefix = prefix + prefix_path
    for r in getattr(router, 'routes', []) or []:
        rtype = type(r).__name__
        # nested router
        orig = getattr(r, 'original_router', None)
        if orig is not None:
            walk(orig, full_prefix)
            continue
        path = getattr(r, 'path', None)
        if path is None:
            continue
        methods = sorted(getattr(r, 'methods', []) or [])
        deps = []
        for d in getattr(r, 'dependencies', []) or []:
            deps.append(dep_name(d))
        ep = getattr(r, 'endpoint', None)
        ep_name = getattr(ep, '__name__', str(ep)) if ep else ''
        rows.append((full_prefix + path, ','.join(methods) if methods else '-', ep_name, deps))

# top level app.router
walk(app.router)
# also direct app.routes that are APIRoute (already covered by app.router)
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
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\routes_dump5.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done; %d routes' % len(rows))
