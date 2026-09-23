"""
Performance testing configuration for Nebula Search Engine.

This module defines performance targets, test scenarios, and configurations
for load testing and benchmarking.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PerformanceTarget:
    """Performance target for an endpoint."""
    endpoint: str
    method: str
    target_p95_ms: float
    target_p99_ms: float
    target_avg_ms: float
    target_throughput_rps: Optional[float] = None
    max_error_rate: float = 0.01
    description: str = ""


@dataclass
class LoadTestScenario:
    """Load test scenario definition."""
    name: str
    description: str
    num_users: int
    spawn_rate: int
    duration_seconds: int
    wait_time_min: float
    wait_time_max: float


# Performance Targets for Critical Endpoints
PERFORMANCE_TARGETS = [
    # Authentication Endpoints
    PerformanceTarget(
        endpoint="/api/v1/auth/login",
        method="POST",
        target_p95_ms=200,
        target_p99_ms=500,
        target_avg_ms=150,
        target_throughput_rps=50,
        description="User login authentication"
    ),
    PerformanceTarget(
        endpoint="/api/v1/auth/refresh",
        method="POST",
        target_p95_ms=100,
        target_p99_ms=200,
        target_avg_ms=50,
        target_throughput_rps=100,
        description="Token refresh"
    ),
    
    # Search Endpoints
    PerformanceTarget(
        endpoint="/api/v1/search",
        method="POST",
        target_p95_ms=500,
        target_p99_ms=1000,
        target_avg_ms=300,
        target_throughput_rps=20,
        description="Web search"
    ),
    PerformanceTarget(
        endpoint="/api/v1/vector/search",
        method="POST",
        target_p95_ms=500,
        target_p99_ms=1000,
        target_avg_ms=300,
        target_throughput_rps=20,
        description="Vector search"
    ),
    PerformanceTarget(
        endpoint="/api/v1/search/orchestrate",
        method="POST",
        target_p95_ms=600,
        target_p99_ms=1200,
        target_avg_ms=400,
        target_throughput_rps=15,
        description="Hybrid orchestrated search"
    ),
    PerformanceTarget(
        endpoint="/api/v1/ai/ask",
        method="POST",
        target_p95_ms=2000,
        target_p99_ms=4000,
        target_avg_ms=1500,
        target_throughput_rps=5,
        description="AI-powered search with answer generation"
    ),
    
    # Document Endpoints
    PerformanceTarget(
        endpoint="/api/v1/documents/",
        method="GET",
        target_p95_ms=200,
        target_p99_ms=400,
        target_avg_ms=100,
        target_throughput_rps=50,
        description="List user documents"
    ),
    PerformanceTarget(
        endpoint="/api/v1/documents/",
        method="POST",
        target_p95_ms=2000,
        target_p99_ms=4000,
        target_avg_ms=1500,
        target_throughput_rps=2,
        description="Upload document (10MB)"
    ),
    PerformanceTarget(
        endpoint="/api/v1/documents/{doc_id}",
        method="DELETE",
        target_p95_ms=300,
        target_p99_ms=600,
        target_avg_ms=200,
        target_throughput_rps=20,
        description="Delete document"
    ),
    
    # User Endpoints
    PerformanceTarget(
        endpoint="/api/v1/users/profile",
        method="GET",
        target_p95_ms=150,
        target_p99_ms=300,
        target_avg_ms=80,
        target_throughput_rps=100,
        description="Get user profile"
    ),
    PerformanceTarget(
        endpoint="/api/v1/users/profile",
        method="PUT",
        target_p95_ms=200,
        target_p99_ms=400,
        target_avg_ms=150,
        target_throughput_rps=50,
        description="Update user profile"
    ),
    
    # Notification Endpoints
    PerformanceTarget(
        endpoint="/api/v1/notifications/",
        method="GET",
        target_p95_ms=200,
        target_p99_ms=400,
        target_avg_ms=100,
        target_throughput_rps=100,
        description="List notifications"
    ),
    
    # Admin Endpoints
    PerformanceTarget(
        endpoint="/api/v1/admin/stats",
        method="GET",
        target_p95_ms=300,
        target_p99_ms=600,
        target_avg_ms=200,
        target_throughput_rps=30,
        description="System statistics"
    ),
    PerformanceTarget(
        endpoint="/api/v1/admin/users",
        method="GET",
        target_p95_ms=400,
        target_p99_ms=800,
        target_avg_ms=250,
        target_throughput_rps=20,
        description="List all users"
    ),
]


# Load Test Scenarios
LOAD_TEST_SCENARIOS = [
    # Normal Load - Typical daily usage
    LoadTestScenario(
        name="normal_load",
        description="Normal daily usage pattern",
        num_users=10,
        spawn_rate=2,
        duration_seconds=300,  # 5 minutes
        wait_time_min=1.0,
        wait_time_max=3.0
    ),
    
    # Peak Load - Expected peak usage
    LoadTestScenario(
        name="peak_load",
        description="Expected peak usage (e.g., business hours)",
        num_users=50,
        spawn_rate=5,
        duration_seconds=600,  # 10 minutes
        wait_time_min=0.5,
        wait_time_max=2.0
    ),
    
    # Stress Test - Beyond normal capacity
    LoadTestScenario(
        name="stress_test",
        description="Stress test to find breaking point",
        num_users=100,
        spawn_rate=10,
        duration_seconds=300,  # 5 minutes
        wait_time_min=0.1,
        wait_time_max=1.0
    ),
    
    # Endurance Test - Long-running stability
    LoadTestScenario(
        name="endurance_test",
        description="Long-running stability test",
        num_users=20,
        spawn_rate=2,
        duration_seconds=1800,  # 30 minutes
        wait_time_min=1.0,
        wait_time_max=3.0
    ),
    
    # Spike Test - Sudden traffic spike
    LoadTestScenario(
        name="spike_test",
        description="Sudden traffic spike simulation",
        num_users=200,
        spawn_rate=50,
        duration_seconds=120,  # 2 minutes
        wait_time_min=0.1,
        wait_time_max=0.5
    ),
]


# Test Configuration
class TestConfig:
    """Test configuration settings."""
    
    # Base URL for testing
    BASE_URL: str = "http://localhost:8000"
    
    # Test credentials
    TEST_USER_EMAIL: str = "test@example.com"
    TEST_USER_PASSWORD: str = "SecurePass123!"
    TEST_ADMIN_EMAIL: str = "admin@example.com"
    TEST_ADMIN_PASSWORD: str = "AdminPass123!"
    
    # Performance thresholds
    ACCEPTABLE_ERROR_RATE: float = 0.01  # 1%
    PERFORMANCE_REGRESSION_THRESHOLD: float = 1.20  # 20% degradation
    
    # Test iterations
    BENCHMARK_ITERATIONS: int = 100
    QUICK_BENCHMARK_ITERATIONS: int = 50
    
    # Database settings for testing
    TEST_DATABASE_URL: str = "test_nebula.db"
    TEST_JWT_SECRET: str = "test-jwt-secret-key"
    
    # Load test settings
    DEFAULT_NUM_USERS: int = 10
    DEFAULT_SPAWN_RATE: int = 2
    DEFAULT_DURATION: int = 300
    
    # Reporting
    GENERATE_HTML_REPORT: bool = True
    SAVE_RAW_DATA: bool = True
    REPORT_OUTPUT_DIR: str = "tests/performance/reports"


# Database Performance Targets
DATABASE_PERFORMANCE_TARGETS = {
    "simple_query": 50,  # ms
    "complex_query": 200,  # ms
    "full_text_search": 100,  # ms
    "vector_search": 300,  # ms
    "insert_operation": 50,  # ms
    "update_operation": 50,  # ms
    "delete_operation": 50,  # ms
}


# Cache Performance Targets
CACHE_PERFORMANCE_TARGETS = {
    "hit_ratio": 0.85,  # 85% cache hit rate
    "get_operation": 10,  # ms
    "set_operation": 20,  # ms
    "delete_operation": 10,  # ms
}


# API Response Time Targets (p95)
API_RESPONSE_TIME_TARGETS = {
    "health_check": 50,  # ms
    "authentication": 200,  # ms
    "search_web": 500,  # ms
    "search_vector": 500,  # ms
    "search_hybrid": 600,  # ms
    "search_ai": 2000,  # ms
    "document_list": 200,  # ms
    "document_upload": 2000,  # ms
    "document_delete": 300,  # ms
    "user_profile": 150,  # ms
    "notifications_list": 200,  # ms
    "admin_stats": 300,  # ms
}


# Resource Usage Targets
RESOURCE_USAGE_TARGETS = {
    "max_memory_mb": 512,  # Maximum memory usage per worker
    "max_cpu_percent": 80,  # Maximum CPU usage
    "max_database_connections": 20,  # Maximum concurrent DB connections
    "max_queue_size": 1000,  # Maximum job queue size
}


def get_target_for_endpoint(endpoint: str, method: str) -> Optional[PerformanceTarget]:
    """Get performance target for a specific endpoint.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method
    
    Returns:
        PerformanceTarget if found, None otherwise
    """
    for target in PERFORMANCE_TARGETS:
        if target.endpoint == endpoint and target.method == method:
            return target
    return None


def get_scenario_by_name(name: str) -> Optional[LoadTestScenario]:
    """Get load test scenario by name.
    
    Args:
        name: Scenario name
    
    Returns:
        LoadTestScenario if found, None otherwise
    """
    for scenario in LOAD_TEST_SCENARIOS:
        if scenario.name == name:
            return scenario
    return None


def get_all_scenarios() -> List[LoadTestScenario]:
    """Get all load test scenarios.
    
    Returns:
        List of all load test scenarios
    """
    return LOAD_TEST_SCENARIOS


def get_all_targets() -> List[PerformanceTarget]:
    """Get all performance targets.
    
    Returns:
        List of all performance targets
    """
    return PERFORMANCE_TARGETS