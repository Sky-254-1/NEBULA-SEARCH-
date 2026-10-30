import os, sys, logging
logging.basicConfig(level=logging.ERROR)
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL']=r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\t.db'
os.environ['JWT_SECRET']='test-secret-key-for-nebula-tests-only-0123456789'
os.environ['APP_ENV']='development'
os.environ['CORS_ORIGINS']='http://localhost:3000'
os.environ['RATE_LIMIT_PER_MINUTE']='10000'
from app.config import get_settings; get_settings.cache_clear()
from app.main import app
lines=[]
for r in app.router.routes:
    path=getattr(r,'path',None)
    sub=getattr(r,'routes',None)
    n=len(sub) if sub is not None else 0
    methods=getattr(r,'methods',None)
    ep=getattr(r,'endpoint',None)
    epn=getattr(ep,'__name__',None) if ep else None
    lines.append('%s | path=%s | methods=%s | subroutes=%s | endpoint=%s' % (type(r).__name__, path, methods, n, epn))
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\route_debug.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done', len(lines))
