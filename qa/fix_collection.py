import re
p = r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\build_collection.py'
s = open(p, encoding='utf-8').read()
# Fix misplaced quote in Bearer {{accessTokenX"}}]  ->  {{accessTokenX"}}]
# Broken: Bearer {{accessTokenUserA"}}]  (quote before closing braces)
# Fixed:  Bearer {{accessTokenUserA"}}]  (quote after closing braces)
pattern = re.compile(
    r'Bearer (accessTokenUserA|accessTokenUserB|accessTokenAdmin)\"(?=\}\])'
)
s, n1 = pattern.subn(lambda m: 'Bearer ' + m.group(1) + '}}"', s)
# Fix raw_body password: {{userAPassword"}} -> {{userAPassword"}} (quote misplaced)
pattern2 = re.compile(r'(userAPassword)\"(?=\")')
s, n2 = pattern2.subn(lambda m: m.group(1) + '\"}', s)
open(p, 'w', encoding='utf-8').write(s)
print('fixed bearer tokens:', n1)
print('fixed passwords:', n2)
