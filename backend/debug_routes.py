"""Debug script to check mounted routes."""

print("Loading app.main...")
import app.main
print(f"app.main loaded: {app.main}")

from app.main import app
print(f"app loaded: {app}")
print(f"app.routes: {app.routes}")

print("\n=== All Routes ===")
for route in app.routes:
    print(f"  Type: {type(route).__name__}, Path: {getattr(route, 'path', 'N/A')}")

print("\n=== Looking for admin routes ===")
for route in app.routes:
    path = getattr(route, 'path', '')
    if 'admin' in path.lower():
        print(f"  {type(route).__name__}: {path}")

print("\n=== Router Admin Routes ===")
from app.routes.admin import router
for r in router.routes:
    if hasattr(r, "path"):
        print(f"  {r.path}")
