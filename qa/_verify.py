import json, os

deliverables = {
    'qa_report.json': r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_report.json',
    'qa_report.md': r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_report.md',
    'qa_runner.py': r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_runner.py',
    'build_collection2.py': r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection2.py',
}

print('=== DELIVERABLES CHECK ===')
for name, path in deliverables.items():
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    status = 'OK' if exists else 'MISSING'
    print(f'  {name}: {status} ({size} bytes)')

d = json.load(open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_report.json', encoding='utf-8'))
print()
print('=== QA SUMMARY ===')
print(json.dumps(d['summary'], indent=2))
print(f'Total tests: {d["total"]}')

cats = set(r['category'] for r in d['results'])
print(f'Categories covered: {len(cats)}')
for c in sorted(cats):
    cnt = sum(1 for r in d['results'] if r['category'] == c)
    print(f'  - {c} ({cnt} tests)')

fails = [r for r in d['results'] if r['status'] == 'failed']
print(f'Failures: {len(fails)}')
blocked = [r for r in d['results'] if r['status'] == 'blocked']
print(f'Blocked: {len(blocked)}')
if blocked:
    for b in blocked:
        print(f'  - {b["category"]}: {b["name"]}')
