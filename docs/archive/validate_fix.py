import urllib.request
import json

base = "http://127.0.0.1:8000"
paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

for path in paths:
    try:
        with urllib.request.urlopen(base + path) as resp:
            print(f"GET {path}: {resp.status}")
    except Exception as e:
        print(f"GET {path}: ERROR {e}")

# Test /favicon.ico separately
try:
    req = urllib.request.Request(base + "/favicon.ico", method="HEAD")
    with urllib.request.urlopen(req) as resp:
        print(f"HEAD /favicon.ico: {resp.status}")
except Exception as e:
    print(f"HEAD /favicon.ico: ERROR {e}")