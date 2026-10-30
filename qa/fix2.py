p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
broken = 'accessTokenUserA"}}}]})'
fixed = 'accessTokenUserA"}}]})'
n = s.count(broken)
s = s.replace(broken, fixed)
open(p, 'w', encoding='utf-8').write(s)
print('replaced', n)
