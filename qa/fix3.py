p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
n1 = s.count('raw_body=\'{"email": "{{userAEmail}}", "password": "{{userAPassword"\'')
s = s.replace('raw_body=\'{"email": "{{userAEmail}}", "password": "{{userAPassword"\'', 'raw_body=\'{"email": "{{userAEmail}}", "password": "{{userAPassword}}"\'')
n2 = s.count('accessTokenUserA"}]})')
s = s.replace('accessTokenUserA"}]})', 'accessTokenUserA"}}]})')
open(p, 'w', encoding='utf-8').write(s)
print('fixed password body:', n1, '; auth headers:', n2)
