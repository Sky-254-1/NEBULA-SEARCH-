p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
import re
for i, line in enumerate(s.splitlines(), 1):
    if 'accessTokenUserA' in line and ('Bearer' in line or 'Authorization' in line):
        print(i, repr(line[:200]))
print('total lines', len(s.splitlines()))
