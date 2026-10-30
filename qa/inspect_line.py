p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
lines = s.splitlines()
ln = lines[166]
i = ln.find('accessTokenUserA')
seg = ln[i:i+22]
print('segment:', seg)
print('ordinals:', [ord(c) for c in seg])
print('has A-quote-brace-brace:', ('accessTokenUserA"' + '}}') in ln)
print('has A-brace-brace-quote:', ('}}' + '"') and ('accessTokenUserA' + '}}' + '"') in ln)
