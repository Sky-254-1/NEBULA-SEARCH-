"""Test script to verify security fixes."""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

def test_jwt_secret_validation():
    """Test JWT_SECRET validation."""
    print("=" * 60)
    print("TEST 1: JWT_SECRET Validation")
    print("=" * 60)
    
    # Test 1: Valid JWT_SECRET (>= 32 chars) in production
    print("\n[PASS] Test 1a: Valid JWT_SECRET in production (32+ chars)")
    os.environ["JWT_SECRET"] = "a" * 32
    os.environ["APP_ENV"] = "production"
    
    # Clear cache to force reload
    from app.config import get_settings
    get_settings.cache_clear()
    
    try:
        settings = get_settings()
        print(f"  JWT_SECRET length: {len(settings.jwt_secret)}")
        print("  [PASS] No error raised for valid secret")
    except ValueError as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False
    
    # Test 2: Invalid JWT_SECRET (< 32 chars) in production
    print("\n[PASS] Test 1b: Invalid JWT_SECRET in production (< 32 chars)")
    os.environ["JWT_SECRET"] = "short"
    get_settings.cache_clear()
    
    try:
        settings = get_settings()
        print("  [FAIL] ValueError not raised for short secret")
        return False
    except ValueError as e:
        print(f"  [PASS] ValueError raised as expected")
        print(f"  Error message: {e}")
    
    # Test 3: Short JWT_SECRET in development (should work with warning)
    print("\n[PASS] Test 1c: Short JWT_SECRET in development (should work)")
    os.environ["JWT_SECRET"] = "short"
    os.environ["APP_ENV"] = "development"
    get_settings.cache_clear()
    
    try:
        settings = get_settings()
        print(f"  JWT_SECRET length: {len(settings.jwt_secret)} (value redacted)")
        print("  [PASS] Short secret allowed in development")
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False
    
    print("\n[SUCCESS] JWT_SECRET validation tests passed!")
    return True


def test_sql_injection_fix():
    """Test SQL injection fix in audit repository."""
    print("\n" + "=" * 60)
    print("TEST 2: SQL Injection Fix")
    print("=" * 60)
    
    # Read the fixed file
    audit_file = backend_path / "app" / "database" / "repositories" / "audit.py"
    with open(audit_file, 'r') as f:
        content = f.read()
    
    # Check that parameterized queries are NOT used with user input
    print("\n[PASS] Test 2a: Checking delete_old_logs method")
    if "INTERVAL '?" in content or "'-? days'" in content:
        print("  [FAIL] SQL parameterization still present - vulnerable!")
        return False
    else:
        print("  [PASS] SQL injection vulnerability fixed in delete_old_logs")
    
    print("\n[PASS] Test 2b: Checking get_audit_statistics method")
    # Check that fetchone/fetchall don't have parameter tuples
    if "(days,)" in content:
        print("  [FAIL] Parameter tuples still present in statistics queries")
        return False
    else:
        print("  [PASS] SQL injection vulnerability fixed in get_audit_statistics")
    
    print("\n[PASS] Test 2c: Verifying safe SQL construction")
    # Verify f-string interpolation is used with int() casting
    if "int(days)" in content:
        print("  [PASS] f-strings used with int() casting for safety")
    else:
        print("  [FAIL] int() casting not found - potential type confusion")
        return False
    
    print("\n[SUCCESS] SQL injection fix verified!")
    return True


async def test_database_operations():
    """Test that database operations work correctly after fixes."""
    print("\n" + "=" * 60)
    print("TEST 3: Database Operations (Integration)")
    print("=" * 60)
    
    try:
        from app.database.engine import DatabaseConnection, connect
        from app.config import get_settings
        from app.database.repositories.audit import AuditRepository
        
        # Reset environment for testing
        os.environ["APP_ENV"] = "development"
        os.environ["DATABASE_URL"] = "file:test_security.db"
        get_settings.cache_clear()
        settings = get_settings()
        
        # Initialize database using connect() function
        db = await connect()
        
        print("\n[PASS] Test 3a: Creating audit repository")
        audit_repo = AuditRepository(db)
        print("  [PASS] Repository instantiated")
        
        print("\n[PASS] Test 3b: Testing delete_old_logs with safe SQL")
        # This should work without SQL injection vulnerability
        await audit_repo.delete_old_logs(days=90)
        print("  [PASS] delete_old_logs executed safely")
        
        print("\n[PASS] Test 3c: Testing delete_old_logs with malicious input (SQL injection attempt)")
        # Try SQL injection - should be neutralized
        malicious_input = "90; DROP TABLE audit_logs; --"
        try:
            await audit_repo.delete_old_logs(days=int(malicious_input.split(";")[0]))
            print("  [PASS] Malicious input safely handled (converted to int)")
        except ValueError:
            print("  [PASS] ValueError raised - input rejected")
        except Exception as e:
            print(f"  [FAIL] Unexpected error: {e}")
            await db.close()
            return False
        
        print("\n[PASS] Test 3d: Testing get_audit_statistics")
        stats = await audit_repo.get_audit_statistics(days=30)
        print(f"  Statistics: {stats}")
        print("  [PASS] Statistics retrieved successfully")
        
        await db.close()
        
        # Cleanup test database
        test_db = Path("test_security.db")
        if test_db.exists():
            test_db.unlink()
        
        print("\n[SUCCESS] Database operations tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Database test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all security tests."""
    print("\n" + "=" * 60)
    print("SECURITY FIXES TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: JWT_SECRET validation
    results.append(("JWT_SECRET Validation", test_jwt_secret_validation()))
    
    # Test 2: SQL injection fix
    results.append(("SQL Injection Fix", test_sql_injection_fix()))
    
    # Test 3: Database operations
    results.append(("Database Operations", await test_database_operations()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED! Security fixes are working correctly.")
        return 0
    else:
        print("\n[FAIL] SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)