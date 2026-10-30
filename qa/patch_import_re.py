p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\qa_runner.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines(keepends=True)
out = []
added = False
for ln in lines:
    out.append(ln)
    if not added and ln.startswith('import re'):
        added = True
# If 'import re' not present at top, prepend after 'import time'
if not added:
    for i, ln in enumerate(out):
        if ln.startswith('import time'):
            out.insert(i+1, 'import re\n')
            added = True
            break
s = ''.join(out)
open(p, 'w', encoding='utf-8').write(s)
print('import re present at top:', 'import re' in s.splitlines()[0:12])
