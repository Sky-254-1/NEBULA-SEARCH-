"""Test backend startup to check for any errors or warnings."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))


async def main():
    """Test backend startup."""
    print("=" * 60)
    print("TESTING BACKEND STARTUP")
    print("=" * 60)
    
    try:
        print("\n[PASS] Importing app.main...")
        from app.main import app
        print("  App imported successfully")
        
        print("\n[PASS] Checking app configuration...")
        from app.config import get_settings
        settings = get_settings()
        print(f"  App environment: {settings.app_env}")
        print(f"  Database: {'PostgreSQL' if settings.uses_postgres else 'SQLite'}")
        print(f"  JWT secret length: {len(settings.jwt_secret)}")
        
        print("\n[PASS] Testing database connection...")
        from app.database import init_db
        await init_db()
        print("  Database initialized successfully")
        
        print("\n[PASS] Checking routes...")
        routes = [route.path for route in app.routes]
        print(f"  Total routes: {len(routes)}")
        
        print("\n[SUCCESS] Backend startup test passed!")
        print("\nBackend is ready to run with:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] Backend startup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)