Q = '"'
p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
# Fix misplaced quote in Bearer {{accessTokenX"}}] -> {{accessTokenX"}}]
# Broken:  accessTokenUserA" }}
# Fixed:   accessTokenUserA }}
tokens = ['accessTokenUserA', 'accessTokenUserB', 'accessTokenAdmin',
          'userAPassword', 'userBPassword']
n = 0
for tok in tokens:
    broken = tok + Q + '}}'
    fixed = tok + '}}' + Q
    c = s.count(broken)
    s = s.replace(broken, fixed)
    n += c
open(p, 'w', encoding='utf-8').write(s)
print('replacements:', n)
import py_compile
try:
    py_compile.compile(p, doraise=True)
    print('compiles OK')
except py_compile.PyCompileError as e:
    print('STILL BROKEN:', e)
