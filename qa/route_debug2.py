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
incs=[r for r in app.router.routes if type(r).__name__=='_IncludedRouter']
lines.append('num included routers: %d' % len(incs))
inc=incs[0]
lines.append('type: %s' % type(inc))
lines.append('attrs: %s' % [a for a in dir(inc) if not a.startswith('__')])
for a in ['path','prefix','router','routes','endpoint','methods']:
    lines.append('  %s = %r' % (a, getattr(inc, a, 'MISSING')))
rt=getattr(inc,'router',None)
if rt:
    lines.append('router type: %s' % type(rt))
    rts=getattr(rt,'routes',None)
    lines.append('router routes count: %s' % (len(rts) if rts is not None else None))
    for r2 in (rts or [])[:8]:
        lines.append('   sub: %s | path=%s | methods=%s | ep=%s' % (type(r2).__name__, getattr(r2,'path',None), getattr(r2,'methods',None), getattr(getattr(r2,'endpoint',None),'__name__',None) if getattr(r2,'endpoint',None) else None))
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\route_debug2.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
