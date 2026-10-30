import re
p = r'c:\Users\User\Downloads\NEBULA-SEARCH\backend\app\routes\indexing.py'
s = open(p, encoding='utf-8').read()

# start_indexing
s = s.replace('async def start_indexing(request: StartIndexRequest) -> APIResponse:',
              'async def start_indexing(request: StartIndexRequest, email: str = Depends(get_current_user)) -> APIResponse:', 1)
# reindex_documents
s = s.replace('async def reindex_documents(request: ReindexRequest) -> APIResponse:',
              'async def reindex_documents(request: ReindexRequest, email: str = Depends(get_current_user)) -> APIResponse:', 1)
# cancel_job
s = s.replace('async def cancel_job(job_id: str) -> APIResponse:',
              'async def cancel_job(job_id: str, email: str = Depends(get_current_user)) -> APIResponse:', 1)
# retry_job
s = s.replace('async def retry_job(job_id: str, db=Depends(get_db)) -> APIResponse:',
              'async def retry_job(job_id: str, db=Depends(get_db), email: str = Depends(get_current_user)) -> APIResponse:', 1)
# get_jobs
s = s.replace('async def get_jobs() -> APIResponse:',
              'async def get_jobs(email: str = Depends(get_current_user)) -> APIResponse:', 1)
# get_job
s = s.replace('async def get_job(job_id: str) -> APIResponse:',
              'async def get_job(job_id: str, email: str = Depends(get_current_user)) -> APIResponse:', 1)
# get_job_progress
s = s.replace('async def get_job_progress(job_id: str) -> APIResponse:',
              'async def get_job_progress(job_id: str, email: str = Depends(get_current_user)) -> APIResponse:', 1)
# get_metrics
s = s.replace('async def get_metrics() -> APIResponse:',
              'async def get_metrics(email: str = Depends(get_current_user)) -> APIResponse:', 1)
# get_dead_letter_queue_route
s = s.replace('async def get_dead_letter_queue_route() -> APIResponse:',
              'async def get_dead_letter_queue_route(email: str = Depends(get_current_user)) -> APIResponse:', 1)
# delete_dead_letter_job
s = s.replace('async def delete_dead_letter_job(job_id: str) -> APIResponse:',
              'async def delete_dead_letter_job(job_id: str, email: str = Depends(get_current_user)) -> APIResponse:', 1)
# get_scheduler_status
s = s.replace('async def get_scheduler_status() -> APIResponse:',
              'async def get_scheduler_status(email: str = Depends(get_current_user)) -> APIResponse:', 1)

# retry_job uses db=Depends(get_db) already; ensure get_db import present
if 'from app.database import get_db' not in s and 'get_db' not in s.split('from app')[0]:
    # add import after APIResponse import
    s = s.replace('from app.models.schemas import APIResponse',
                  'from app.models.schemas import APIResponse\nfrom app.database import get_db', 1)

open(p, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('indexing auth patches applied, syntax OK')
# verify
for ln in s.splitlines():
    if 'email: str = Depends(get_current_user)' in ln:
        print('  ', ln.strip())
