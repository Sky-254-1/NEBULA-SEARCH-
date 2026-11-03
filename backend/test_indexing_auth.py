"""Test indexing endpoint authentication."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test indexing start without auth
resp = client.post('/api/v1/indexing/start', json={'document_id': 1})
print(f'Status without auth: {resp.status_code}')
print(f'Response without auth: {resp.text[:200]}')

# Test indexing start with a dummy auth header
resp2 = client.post('/api/v1/indexing/start', json={'document_id': 1}, headers={'Authorization': 'Bearer invalid'})
print(f'Status with invalid Bearer: {resp2.status_code}')
print(f'Response with invalid Bearer: {resp2.text[:200]}')

# Test with valid auth (need to login first)
print("\n=== Testing with valid token ===")
# Need to login first to get a valid token
login_resp = client.post('/api/v1/auth/login', json={'email': 'test@example.com', 'password': 'Test1234!'})
print(f'Login status: {login_resp.status_code}')
if login_resp.status_code == 200:
    token = login_resp.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    auth_resp = client.post('/api/v1/indexing/start', json={'document_id': 1}, headers=headers)
    print(f'Status with valid token: {auth_resp.status_code}')
    print(f'Response with valid token: {auth_resp.text[:200]}')