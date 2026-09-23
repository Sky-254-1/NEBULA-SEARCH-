"""CI script: verify app imports work correctly."""
import sys
sys.path.insert(0, ".")

from app.main import app
print(f"App: {app.title}")