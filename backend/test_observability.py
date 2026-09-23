"""Test observability stack components."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))


async def main():
    """Test all observability components."""
    print("=" * 70)
    print("TESTING OBSERVABILITY STACK")
    print("=" * 70)
    
    results = []
    
    # Test 1: Structured JSON Logging
    print("\n[TEST 1] Structured JSON Logging")
    print("-" * 70)
    try:
        import logging
        from app.config import get_settings
        import os
        os.environ["APP_ENV"] = "development"
        os.environ["DATABASE_URL"] = "file:test_obs.db"
        get_settings.cache_clear()
        
        # Verify JSON formatter exists
        from app.main import _JsonFormatter
        formatter = _JsonFormatter()
        
        # Create a test log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.request_id = "test-123"
        
        formatted = formatter.format(record)
        import json
        parsed = json.loads(formatted)
        
        assert parsed["message"] == "Test message"
        assert parsed["request_id"] == "test-123"
        assert parsed["level"] == "INFO"
        
        print("  [PASS] JSON formatter working correctly")
        print(f"  Sample output: {formatted}")
        results.append(("JSON Logging", True))
    except Exception as e:
        print(f"  [FAIL] JSON logging failed: {e}")
        results.append(("JSON Logging", False))
    
    # Test 2: Prometheus Metrics
    print("\n[TEST 2] Prometheus Metrics Endpoint")
    print("-" * 70)
    try:
        from app.main import app, _HAS_PROMETHEUS
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Check if prometheus is available
        if not _HAS_PROMETHEUS:
            print("  [WARN] prometheus_client not installed - metrics disabled")
            print("  Install with: pip install prometheus-client")
            results.append(("Prometheus Metrics", None))
        else:
            # Test /metrics endpoint (direct path, not versioned)
            response = client.get("/metrics")
            assert response.status_code == 200
            assert "nebula_http_requests_total" in response.text or "nebula_" in response.text
            
            print("  [PASS] /metrics endpoint accessible")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            print(f"  Metrics present: {'nebula_' in response.text}")
            results.append(("Prometheus Metrics", True))
    except Exception as e:
        print(f"  [FAIL] Prometheus metrics test failed: {e}")
        results.append(("Prometheus Metrics", False))
    
    # Test 3: Request ID Tracing
    print("\n[TEST 3] Request ID Tracing")
    print("-" * 70)
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Make request without X-Request-ID header
        response = client.get("/")
        assert response.status_code in [200, 404, 405]  # Any valid response
        
        # Check that X-Request-ID header is present
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
        
        print("  [PASS] Request ID middleware working")
        print(f"  Generated request ID: {request_id}")
        
        # Test with custom request ID
        response2 = client.get("/", headers={"X-Request-ID": "custom-id-123"})
        assert response2.headers["X-Request-ID"] == "custom-id-123"
        
        print("  [PASS] Custom request IDs preserved")
        results.append(("Request ID Tracing", True))
    except Exception as e:
        print(f"  [FAIL] Request ID tracing failed: {e}")
        results.append(("Request ID Tracing", False))
    
    # Test 4: Sentry Integration
    print("\n[TEST 4] Sentry Error Tracking")
    print("-" * 70)
    try:
        from app.config import get_settings
        import os
        
        # Check if Sentry is configured
        settings = get_settings()
        
        if not settings.sentry_dsn:
            print("  [WARN] SENTRY_DSN not configured - Sentry disabled")
            print("  Set SENTRY_DSN environment variable to enable")
            results.append(("Sentry Integration", None))
        else:
            # Verify Sentry SDK is initialized
            import sentry_sdk
            hub = sentry_sdk.Hub.current
            client = hub.client
            assert client is not None
            print("  [PASS] Sentry SDK initialized")
            print(f"  DSN configured: {settings.sentry_dsn[:20]}...")
            results.append(("Sentry Integration", True))
    except ImportError:
        print("  [WARN] sentry-sdk not installed")
        print("  Install with: pip install sentry-sdk")
        results.append(("Sentry Integration", None))
    except Exception as e:
        print(f"  [FAIL] Sentry integration test failed: {e}")
        results.append(("Sentry Integration", False))
    
    # Test 5: OpenTelemetry
    print("\n[TEST 5] OpenTelemetry Tracing")
    print("-" * 70)
    try:
        from app.config import get_settings
        settings = get_settings()
        
        if not settings.otel_exporter_otlp_endpoint:
            print("  [WARN] OTEL_EXPORTER_OTLP_ENDPOINT not configured")
            print("  Set OTEL_EXPORTER_OTLP_ENDPOINT to enable distributed tracing")
            results.append(("OpenTelemetry", None))
        else:
            print("  [PASS] OpenTelemetry configured")
            print(f"  Endpoint: {settings.otel_exporter_otlp_endpoint}")
            results.append(("OpenTelemetry", True))
    except Exception as e:
        print(f"  [FAIL] OpenTelemetry test failed: {e}")
        results.append(("OpenTelemetry", False))
    
    # Test 6: MetricsMiddleware
    print("\n[TEST 6] MetricsMiddleware")
    print("-" * 70)
    try:
        from app.main import app
        from app.services.monitoring import metrics
        
        # Make some requests to generate metrics
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Make a few requests
        for _ in range(3):
            client.get("/")
        
        # Check metrics were recorded
        summary = metrics.get_metrics_summary()
        assert summary["requests"]["total"] > 0
        
        print("  [PASS] MetricsMiddleware recording requests")
        print(f"  Total requests tracked: {summary['requests']['total']}")
        print(f"  Average response time: {summary['requests']['avg_response_time_ms']:.2f}ms")
        results.append(("MetricsMiddleware", True))
    except Exception as e:
        print(f"  [FAIL] MetricsMiddleware test failed: {e}")
        results.append(("MetricsMiddleware", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("OBSERVABILITY TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, v in results if v is True)
    failed = sum(1 for _, v in results if v is False)
    warnings = sum(1 for _, v in results if v is None)
    
    for test_name, result in results:
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[WARN]"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Warnings (optional components): {warnings}")
    
    if failed > 0:
        print("\n[FAIL] Some critical observability components failed!")
        return 1
    else:
        print("\n[SUCCESS] All critical observability components working!")
        if warnings > 0:
            print("\nNote: Some optional components are not configured.")
            print("This is expected for development environments.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)