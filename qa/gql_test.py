import os, sys, asyncio
os.chdir(r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
sys.path.insert(0, r'c:\Users\User\Downloads\NEBULA-SEARCH\backend')
os.environ['DATABASE_URL']=r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\gql_t.db'
os.environ['JWT_SECRET']='test-secret-key-for-nebula-qa-0123456789abcdef'
os.environ['APP_ENV']='development'
os.environ['CORS_ORIGINS']='http://localhost:3000'
from app.config import get_settings; get_settings.cache_clear()
from app.database import init_db
from app.main import app
from fastapi.testclient import TestClient
asyncio.run(init_db())
c=TestClient(app)
query='query { __type(name: "Query") { name } }'
r=c.post('/graphql/', json={'query': query})
print('graphql POST', r.status_code, r.text[:300])
r2=c.get('/graphql/schema')
print('graphql schema', r2.status_code, r2.text[:200])
r3=c.get('/graphql/playground')
print('graphql playground', r3.status_code, r3.text[:200])
