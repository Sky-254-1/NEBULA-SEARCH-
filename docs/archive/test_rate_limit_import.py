import sys
sys.path.insert(0, 'backend')

try:
    from app.middleware.rate_limit import get_limiter, rate_limit_exceeded_handler, slowapi_middleware, RateLimitHeadersMiddleware
    print('✓ All rate limit imports successful')
    print(f'  - get_limiter: {get_limiter}')
    print(f'  - rate_limit_exceeded_handler: {rate_limit_exceeded_handler}')
    print(f'  - slowapi_middleware: {slowapi_middleware}')
    print(f'  - RateLimitHeadersMiddleware: {RateLimitHeadersMiddleware}')
except ImportError as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)