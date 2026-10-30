import re
p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'.{25}accessTokenUserA.{25}', s):
    print(repr(m.group(0)))
    print('---')
