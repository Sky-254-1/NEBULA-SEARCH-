import re
p = r'c:\Users\User\Downloads\NEBULA-SEARCH\backend\app\routes\indexing.py'
s = open(p, encoding='utf-8').read()
for kw in ['start_indexing','reindex_documents','cancel_job','retry_job','get_jobs','get_job','get_job_progress','get_metrics','get_dead_letter_queue_route','delete_dead_letter_job','get_scheduler_status']:
    idxs = [m.start() for m in re.finditer(re.escape(kw)+r'\s*\(', s)]
    print(kw, len(idxs))
    for i in idxs[:6]:
        print('   ', s[max(0,i-60):i+40].replace('\n',' '))
