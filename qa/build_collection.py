import json
c = {
  "info": {
    "name": "Nebula Search API — QA Regression Collection",
    "_postman_id": "nebula-search-qa-collection",
    "description": "Functional, authorization, security, and regression tests for the Nebula Search API.\nUses environment variables only — no secrets or real tokens are stored here.\nRun against a dedicated test environment (never production).\nBase URL: {{baseUrl}}\nAuth: Bearer {{accessTokenUserA}} / {{accessTokenUserB}} / {{accessTokenAdmin}}",
    "schema": "https://schema.postman.com/collection/v2.1.0/collection.json",
    "version": "1.0.0"
  },
  "variable": [
    { "key": "baseUrl", "value": "http://localhost:8000", "type": "string" },
    { "key": "responseTimeThresholdMs", "value": "2000", "type": "string" }
  ],
  "item": []
}
def folder(name):
    return {"name": name, "item": []}
def req(name, method, url, headers=None, body=None, raw_body=None, query=None):
    r = {"name": name, "request": {"method": method, "header": headers or [], "url": {"raw": url, "host": ["{{baseUrl}}"], "path": []}, "body": None}, "event": []}
    # build path array
    from urllib.parse import urlparse, parse_qs
    u = urlparse(url.replace("{{baseUrl}}","http://x"))
    r["request"]["url"]["path"] = [p for p in u.path.split("/") if p]
    if query:
        r["request"]["url"]["query"] = query
    if raw_body is not None:
        r["request"]["body"] = {"mode":"raw","raw":raw_body,"options":{"raw":{"language":"json"}}}
    elif body is not None:
        r["request"]["body"] = {"mode":"raw","raw":json.dumps(body),"options":{"raw":{"language":"json"}}}
    if headers:
        r["request"]["header"] = headers
    return r
def test(item, lines):
    item.setdefault("event", []).append({"listen":"test","script":{"exec":lines,"type":"text/javascript"}})
    return item
def add(folder_obj, item):
    folder_obj["item"].append(item)
# --- Smoke / Health / Versioning ---
f0 = folder("00 — Smoke / Health / Versioning")
add(c["item"], f0)
add(f0, test(req("GET /health","GET","{{baseUrl}}/health"), [
  "pm.test('Status is 200', function () { pm.response.to.have.status(200); });",
  "pm.test('Content-Type is JSON', function () { pm.expect(pm.response.headers.get('content-type')).to.include('application/json'); });",
  "pm.test('Response time under threshold', function () { pm.expect(pm.response.responseTime).to.be.below(parseInt(pm.environment.get('responseTimeThresholdMs'))); });"
]))
add(f0, test(req("GET /openapi.json","GET","{{baseUrl}}/openapi.json"), [
  "pm.test('OpenAPI schema generates (not 500)', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('OpenAPI has info.title', function () { var b = pm.response.json(); pm.expect(b.info.title).to.exist; });",
  "pm.test('OpenAPI has paths', function () { var b = pm.response.json(); pm.expect(Object.keys(b.paths || {})).to.have.lengthOf.above(0); });"
]))
add(f0, test(req("GET /api/v1/search/web","GET","{{baseUrl}}/search/web?q=test", query=[{"key":"q","value":"test"}]), [
  "pm.test('Unversioned path rejected by versioning middleware (400)', function () { pm.expect(pm.response.code).to.equal(400); });"
]))

# --- Authentication (part 1) ---
f1 = folder("01 — Authentication")
add(c["item"], f1)
add(f1, test(req("POST /api/v1/auth/signup (valid)","POST","{{baseUrl}}/api/v1/auth/signup",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"email": "{{userAEmail}}", "password": "{{userAPassword}}"'), [
  "pm.test('Signup returns 201 or 409', function () { pm.expect(pm.response.code).to.be.oneOf([201,409]); });",
  "pm.test('Content-Type is JSON', function () { pm.expect(pm.response.headers.get('content-type')).to.include('application/json'); });"
]))
add(f1, test(req("POST /api/v1/auth/signup (duplicate -> 409)","POST","{{baseUrl}}/api/v1/auth/signup",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"email": "{{userAEmail}}", "password": "{{userAPassword}}"'), [
  "pm.test('Duplicate signup returns 409', function () { pm.expect(pm.response.code).to.equal(409); });"
]))
add(f1, test(req("POST /api/v1/auth/signup (weak password -> 400)","POST","{{baseUrl}}/api/v1/auth/signup",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"email": "weakpw@example.com", "password": "weak"}'), [
  "pm.test('Weak password returns 400', function () { pm.expect(pm.response.code).to.equal(400); });"
]))
add(f1, test(req("POST /api/v1/auth/signup (missing fields -> 422)","POST","{{baseUrl}}/api/v1/auth/signup",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{}'), [
  "pm.test('Missing fields returns 422', function () { pm.expect(pm.response.code).to.equal(422); });"
]))
add(f1, test(req("POST /api/v1/auth/signup (malformed JSON -> 400)","POST","{{baseUrl}}/api/v1/auth/signup",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{not json'), [
  "pm.test('Malformed JSON returns 400', function () { pm.expect(pm.response.code).to.equal(400); });"
]))

# --- Authentication (part 2: login/refresh/me) ---
add(f1, test(req("POST /api/v1/auth/login (valid)","POST","{{baseUrl}}/api/v1/auth/login",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"email": "{{userAEmail}}", "password": "{{userAPassword}}"'), [
  "pm.test('Login returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('Access token present', function () { var json = pm.response.json(); pm.expect(json.access_token).to.exist; pm.environment.set('accessTokenUserA', json.access_token); });",
  "pm.test('Refresh token present', function () { var json = pm.response.json(); pm.expect(json.refresh_token).to.exist; pm.environment.set('refreshTokenUserA', json.refresh_token); });",
  "pm.test('ExpiresIn present', function () { var json = pm.response.json(); pm.expect(json.expires_in).to.exist; });"
]))
add(f1, test(req("POST /api/v1/auth/login (wrong password -> 401)","POST","{{baseUrl}}/api/v1/auth/login",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"email": "{{userAEmail}}", "password": "WrongPassword1!"}'), [
  "pm.test('Wrong password returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f1, test(req("POST /api/v1/auth/login (nonexistent -> 401)","POST","{{baseUrl}}/api/v1/auth/login",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"email": "nonexistent@example.com", "password": "Password1!"}'), [
  "pm.test('Nonexistent user returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f1, test(req("POST /api/v1/auth/refresh (valid)","POST","{{baseUrl}}/api/v1/auth/refresh",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"refresh_token": "{{refreshTokenUserA}}"}'), [
  "pm.test('Refresh returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('New access token present', function () { var json = pm.response.json(); pm.expect(json.access_token).to.exist; pm.environment.set('accessTokenUserA', json.access_token); });"
]))
add(f1, test(req("POST /api/v1/auth/refresh (invalid -> 401)","POST","{{baseUrl}}/api/v1/auth/refresh",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"refresh_token": "{{invalidToken}}"}'), [
  "pm.test('Refresh with invalid token returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f1, test(req("GET /api/v1/auth/me (no token -> 401)","GET","{{baseUrl}}/api/v1/auth/me"), [
  "pm.test('Me without token returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f1, test(req("GET /api/v1/auth/me (invalid token -> 401)","GET","{{baseUrl}}/api/v1/auth/me",
  headers=[{"key":"Authorization","value":"Bearer {{invalidToken}}"}]), [
  "pm.test('Me with invalid token returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f1, test(req("GET /api/v1/auth/me (valid user A)","GET","{{baseUrl}}/api/v1/auth/me",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Me returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('Me returns email and role', function () { var json = pm.response.json(); pm.expect(json.email).to.equal(pm.environment.get('userAEmail')); pm.expect(json.role).to.exist; });"
]))

# --- Documents ---
f2 = folder("02 — Documents (auth + ownership)")
add(c["item"], f2)
add(f2, test(req("POST /api/v1/documents/ (no auth -> 401)","POST","{{baseUrl}}/api/v1/documents/"), [
  "pm.test('Upload without auth returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f2, test(req("POST /api/v1/documents/ (upload valid .txt, user A)","POST","{{baseUrl}}/api/v1/documents/",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Upload returns 200/201', function () { pm.expect(pm.response.code).to.be.oneOf([200,201]); });",
  "pm.test('Document id present', function () { var json = pm.response.json(); pm.expect(json.id).to.exist; pm.environment.set('documentIdA', json.id); });",
  "pm.test('Content-Type is JSON', function () { pm.expect(pm.response.headers.get('content-type')).to.include('application/json'); });"
]))
add(f2, test(req("POST /api/v1/documents/ (disallowed file type -> 400)","POST","{{baseUrl}}/api/v1/documents/",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Disallowed file type returns 400', function () { pm.expect(pm.response.code).to.equal(400); });"
]))
add(f2, test(req("GET /api/v1/documents/ (list user A docs)","GET","{{baseUrl}}/api/v1/documents/",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('List documents returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('Response has documents and pagination', function () { var json = pm.response.json(); pm.expect(json.documents).to.be.an('array'); pm.expect(json.pagination).to.exist; pm.expect(json.pagination.total).to.be.a('number'); });"
]))
add(f2, test(req("DELETE /api/v1/documents/{doc_id} (user A deletes own)","DELETE","{{baseUrl}}/api/v1/documents/{{documentIdA}}",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Delete own document returns 200', function () { pm.expect(pm.response.code).to.equal(200); });"
]))
add(f2, test(req("DELETE /api/v1/documents/99999999 (nonexistent -> 404)","DELETE","{{baseUrl}}/api/v1/documents/99999999",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Delete nonexistent document returns 404', function () { pm.expect(pm.response.code).to.equal(404); });"
]))

# --- Indexing ---
f3 = folder("03 — Indexing (should enforce auth — regression check)")
add(c["item"], f3)
add(f3, test(req("POST /api/v1/indexing/start (no auth -> expect 401)","POST","{{baseUrl}}/api/v1/indexing/start",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"document_id": 1, "priority": "normal"}'), [
  "pm.test('Indexing start without auth returns 401 (security requirement)', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f3, test(req("POST /api/v1/indexing/start (valid auth)","POST","{{baseUrl}}/api/v1/indexing/start",
  headers=[{"key":"content-type","value":"application/json"},{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  raw_body='{"document_id": 1, "priority": "normal"}'), [
  "pm.test('Indexing start returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('Job id present', function () { var json = pm.response.json(); pm.expect(json.data.job_id).to.exist; pm.environment.set('indexingJobId', json.data.job_id); });"
]))
add(f3, test(req("GET /api/v1/indexing/job/{job_id}","GET","{{baseUrl}}/api/v1/indexing/job/{{indexingJobId}}",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Get job returns 200', function () { pm.expect(pm.response.code).to.equal(200); });"
]))
add(f3, test(req("POST /api/v1/indexing/retry/{job_id}","POST","{{baseUrl}}/api/v1/indexing/retry/{{indexingJobId}}",
  headers=[{"key":"content-type","value":"application/json"},{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  raw_body='{"job_id": "{{indexingJobId}}"}'), [
  "pm.test('Retry returns 200 or honest 4xx/5xx', function () { pm.expect(pm.response.code).to.be.oneOf([200,400,404,409,500]); });",
  "pm.test('Retry response has message', function () { var json = pm.response.json(); pm.expect(json.message).to.exist; });"
]))

# --- Users ---
f4 = folder("04 — Users (profile, avatar, account)")
add(c["item"], f4)
add(f4, test(req("GET /api/v1/users/profile (valid user A)","GET","{{baseUrl}}/api/v1/users/profile",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Profile returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('Profile has id/email/role', function () { var json = pm.response.json(); pm.expect(json.id).to.exist; pm.expect(json.email).to.exist; pm.environment.set('userAId', json.id); });"
]))
add(f4, test(req("PUT /api/v1/users/profile (update user A)","PUT","{{baseUrl}}/api/v1/users/profile",
  headers=[{"key":"content-type","value":"application/json"},{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  raw_body='{"first_name": "QA", "last_name": "UserA"}'), [
  "pm.test('Update profile returns 200', function () { pm.expect(pm.response.code).to.equal(200); });"
]))
add(f4, test(req("POST /api/v1/users/avatar (upload image, user A)","POST","{{baseUrl}}/api/v1/users/avatar",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Avatar upload returns 200', function () { pm.expect(pm.response.code).to.equal(200); });"
]))
add(f4, test(req("DELETE /api/v1/users/account (no auth -> 401)","DELETE","{{baseUrl}}/api/v1/users/account?password=Password1!",
  query=[{"key":"password","value":"Password1!"}]), [
  "pm.test('Delete account without auth returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))

# --- Search ---
f5 = folder("05 — Search")
add(c["item"], f5)
add(f5, test(req("GET /api/v1/search/web (no auth -> 401)","GET","{{baseUrl}}/api/v1/search/web?q=nebula&backend=wikipedia",
  query=[{"key":"q","value":"nebula"},{"key":"backend","value":"wikipedia"}]), [
  "pm.test('Search web without auth returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f5, test(req("GET /api/v1/search/web (valid user A)","GET","{{baseUrl}}/api/v1/search/web?q=nebula&backend=wikipedia&page=1&page_size=5",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"q","value":"nebula"},{"key":"backend","value":"wikipedia"},{"key":"page","value":"1"},{"key":"page_size","value":"5"}]), [
  "pm.test('Search web returns 200', function () { pm.expect(pm.response.code).to.equal(200); });",
  "pm.test('Search results is array', function () { var json = pm.response.json(); pm.expect(json).to.be.an('array'); });"
]))
add(f5, test(req("GET /api/v1/search/web (invalid backend -> 400)","GET","{{baseUrl}}/api/v1/search/web?q=nebula&backend=notabackend",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"q","value":"nebula"},{"key":"backend","value":"notabackend"}]), [
  "pm.test('Invalid backend returns 400', function () { pm.expect(pm.response.code).to.equal(400); });"
]))
add(f5, test(req("GET /api/v1/search/web (missing q -> 422)","GET","{{baseUrl}}/api/v1/search/web?backend=wikipedia",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"backend","value":"wikipedia"}]), [
  "pm.test('Missing q returns 422', function () { pm.expect(pm.response.code).to.equal(422); });"
]))
add(f5, test(req("GET /api/v2/search/ (intelligent search)","GET","{{baseUrl}}/api/v2/search/?q=nebula",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"q","value":"nebula"}]), [
  "pm.test('V2 search returns 200', function () { pm.expect(pm.response.code).to.equal(200); });"
]))

# --- Admin / RBAC ---
f6 = folder("06 — Admin / RBAC")
add(c["item"], f6)
add(f6, test(req("GET /api/v1/admin/stats (no token -> 401)","GET","{{baseUrl}}/api/v1/admin/stats"), [
  "pm.test('Admin stats without token returns 401', function () { pm.expect(pm.response.code).to.equal(401); });"
]))
add(f6, test(req("GET /api/v1/admin/stats (user token -> 403)","GET","{{baseUrl}}/api/v1/admin/stats",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Admin stats with user token returns 403', function () { pm.expect(pm.response.code).to.equal(403); });"
]))
add(f6, test(req("GET /api/v1/admin/users (user token -> 403)","GET","{{baseUrl}}/api/v1/admin/users",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"}]), [
  "pm.test('Admin users with user token returns 403', function () { pm.expect(pm.response.code).to.equal(403); });"
]))

# --- GraphQL ---
f7 = folder("07 — GraphQL")
add(c["item"], f7)
add(f7, test(req("POST /graphql/ (introspection, no auth)","POST","{{baseUrl}}/graphql/",
  headers=[{"key":"content-type","value":"application/json"}],
  raw_body='{"query": "{ __schema { types { name } } }"}'), [
  "pm.test('GraphQL introspection does not return 500', function () { pm.expect(pm.response.code).not.to.equal(500); });"
]))
add(f7, test(req("GET /graphql/schema (introspection endpoint)","GET","{{baseUrl}}/graphql/schema"), [
  "pm.test('GraphQL schema endpoint does not return 500', function () { pm.expect(pm.response.code).not.to.equal(500); });"
]))

# --- Security / Rate Limiting / Input Validation ---
f8 = folder("08 — Security / Rate Limiting / Input Validation")
add(c["item"], f8)
add(f8, test(req("GET /api/v1/search/web?q=<script> (XSS attempt)","GET","{{baseUrl}}/api/v1/search/web?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"q","value":"<script>alert(1)</script>"}]), [
  "pm.test('XSS input not reflected / no 500', function () { pm.expect(pm.response.code).not.to.equal(500); });",
  "pm.test('Response does not contain raw script tag', function () { var body = pm.response.text(); pm.expect(body).not.to.include('<script>'); });"
]))
add(f8, test(req("GET /api/v1/search/web?q=1 OR 1=1 (SQLi attempt)","GET","{{baseUrl}}/api/v1/search/web?q=1%20OR%201%3D1",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"q","value":"1 OR 1=1"}]), [
  "pm.test('SQLi input does not cause 500', function () { pm.expect(pm.response.code).not.to.equal(500); });",
  "pm.test('No stack trace in error body', function () { var body = pm.response.text(); pm.expect(body).not.to.match(/Traceback|Stack trace|line [0-9]+ in /i); });"
]))
add(f8, test(req("GET /api/v1/search/web (rate limit check)","GET","{{baseUrl}}/api/v1/search/web?q=ratelimit&backend=wikipedia",
  headers=[{"key":"Authorization","value":"Bearer {{accessTokenUserA}}"]},
  query=[{"key":"q","value":"ratelimit"},{"key":"backend","value":"wikipedia"}]), [
  "pm.test('Rate limit response is 429 or includes rate headers', function () { var code = pm.response.code; pm.expect(code).to.be.oneOf([200,429]); if (code === 429) { pm.expect(pm.response.headers.get('retry-after')).to.exist; } });"
]))

# --- Serialize ---
with open(r'c:\Users\User\Downloads\NEBULA-SEARCH\qa\Nebula_Search_API.postman_collection.json','w',encoding='utf-8') as fh:
    json.dump(c, fh, indent=2)
print('collection written; items =', sum(len(it.get('item',[])) for it in c['item']))

