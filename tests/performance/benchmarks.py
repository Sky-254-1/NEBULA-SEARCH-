"""
Performance benchmarks for Nebula Search Engine.

This module provides utilities for measuring and validating performance
of critical API endpoints against defined benchmarks.
"""

import time
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from statistics import mean, median, stdev
from fastapi.testclient import TestClient
from app.services.auth import create_access_token


@dataclass
class PerformanceTarget:
    """Performance target definition."""
    endpoint: str
    method: str
    target_p95_ms: float
    target_p99_ms: float
    target_avg_ms: float
    max_memory_mb: Optional[float] = None
    description: str = ""


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    endpoint: str
    method: str
    total_requests: int
    success_count: int
    failure_count: int
    min_ms: float
    max_ms: float
    avg_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    stddev_ms: float
    passed: bool
    failures: List[str]


class PerformanceBenchmark:
    """Performance benchmarking utility."""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.results: List[BenchmarkResult] = []
        
        # Define performance targets
        self.targets = [
            PerformanceTarget(
                endpoint="/api/v1/auth/login",
                method="POST",
                target_p95_ms=200,
                target_p99_ms=500,
                target_avg_ms=150,
                description="User authentication"
            ),
            PerformanceTarget(
                endpoint="/api/v1/search",
                method="POST",
                target_p95_ms=500,
                target_p99_ms=1000,
                target_avg_ms=300,
                description="Web search"
            ),
            PerformanceTarget(
                endpoint="/api/v1/documents/",
                method="GET",
                target_p95_ms=200,
                target_p99_ms=400,
                target_avg_ms=100,
                description="List documents"
            ),
            PerformanceTarget(
                endpoint="/api/v1/users/profile",
                method="GET",
                target_p95_ms=150,
                target_p99_ms=300,
                target_avg_ms=80,
                description="Get user profile"
            ),
            PerformanceTarget(
                endpoint="/api/v1/notifications/",
                method="GET",
                target_p95_ms=200,
                target_p99_ms=400,
                target_avg_ms=100,
                description="List notifications"
            ),
            PerformanceTarget(
                endpoint="/api/v1/admin/stats",
                method="GET",
                target_p95_ms=300,
                target_p99_ms=600,
                target_avg_ms=200,
                description="System statistics"
            ),
        ]
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authentication header."""
        token = create_access_token("test@example.com", role="user")
        return {"Authorization": f"Bearer {token}"}
    
    def _get_admin_auth_header(self) -> Dict[str, str]:
        """Get admin authentication header."""
        token = create_access_token("admin@example.com", role="admin")
        return {"Authorization": f"Bearer {token}"}
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from list of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def benchmark_endpoint(
        self,
        endpoint: str,
        method: str,
        iterations: int = 100,
        auth_required: bool = True,
        admin_required: bool = False,
        **kwargs
    ) -> BenchmarkResult:
        """Benchmark a single endpoint.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            iterations: Number of requests to make
            auth_required: Whether authentication is required
            admin_required: Whether admin privileges are required
            **kwargs: Additional arguments for the request
        
        Returns:
            BenchmarkResult with performance metrics
        """
        times: List[float] = []
        failures: List[str] = []
        success_count = 0
        
        headers = {}
        if admin_required:
            headers = self._get_admin_auth_header()
        elif auth_required:
            headers = self._get_auth_header()
        
        for i in range(iterations):
            try:
                start_time = time.perf_counter()
                
                if method.upper() == "GET":
                    response = self.client.get(endpoint, headers=headers, params=kwargs.get("params"))
                elif method.upper() == "POST":
                    response = self.client.post(endpoint, headers=headers, json=kwargs.get("json"))
                elif method.upper() == "PUT":
                    response = self.client.put(endpoint, headers=headers, json=kwargs.get("json"))
                elif method.upper() == "DELETE":
                    response = self.client.delete(endpoint, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                end_time = time.perf_counter()
                elapsed_ms = (end_time - start_time) * 1000
                
                if response.status_code < 400:
                    times.append(elapsed_ms)
                    success_count += 1
                else:
                    failures.append(f"Request {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                failures.append(f"Request {i+1}: {str(e)}")
        
        if not times:
            return BenchmarkResult(
                endpoint=endpoint,
                method=method,
                total_requests=iterations,
                success_count=0,
                failure_count=iterations,
                min_ms=0,
                max_ms=0,
                avg_ms=0,
                median_ms=0,
                p95_ms=0,
                p99_ms=0,
                stddev_ms=0,
                passed=False,
                failures=failures
            )
        
        # Calculate statistics
        min_ms = min(times)
        max_ms = max(times)
        avg_ms = mean(times)
        median_ms = median(times)
        p95_ms = self._calculate_percentile(times, 95)
        p99_ms = self._calculate_percentile(times, 99)
        stddev_ms = stdev(times) if len(times) > 1 else 0
        
        # Find target for this endpoint
        target = next((t for t in self.targets if t.endpoint == endpoint), None)
        
        # Check if passed
        passed = True
        if target:
            if p95_ms > target.target_p95_ms:
                passed = False
            if p99_ms > target.target_p99_ms:
                passed = False
            if avg_ms > target.target_avg_ms:
                passed = False
        
        return BenchmarkResult(
            endpoint=endpoint,
            method=method,
            total_requests=iterations,
            success_count=success_count,
            failure_count=iterations - success_count,
            min_ms=min_ms,
            max_ms=max_ms,
            avg_ms=avg_ms,
            median_ms=median_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
            stddev_ms=stddev_ms,
            passed=passed,
            failures=failures
        )
    
    def run_all_benchmarks(self, iterations: int = 100) -> List[BenchmarkResult]:
        """Run all defined benchmarks.
        
        Args:
            iterations: Number of iterations per endpoint
        
        Returns:
            List of benchmark results
        """
        results = []
        
        for target in self.targets:
            print(f"\nBenchmarking {target.method} {target.endpoint}...")
            result = self.benchmark_endpoint(
                endpoint=target.endpoint,
                method=target.method,
                iterations=iterations,
                auth_required=True,
                admin_required="/admin" in target.endpoint
            )
            results.append(result)
            self.results.append(result)
            
            # Print result
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} - avg: {result.avg_ms:.2f}ms, p95: {result.p95_ms:.2f}ms, p99: {result.p99_ms:.2f}ms")
        
        return results
    
    def print_summary(self):
        """Print summary of all benchmarks."""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print(f"\nTotal Benchmarks: {total}")
        print(f"Passed: {passed}/{total} ({100*passed/total if total > 0 else 0:.1f}%)")
        print(f"Failed: {total - passed}/{total}")
        
        print("\nDetailed Results:")
        print("-" * 80)
        print(f"{'Endpoint':<40} {'Method':<6} {'Avg':<10} {'p95':<10} {'p99':<10} {'Status':<10}")
        print("-" * 80)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{result.endpoint:<40} {result.method:<6} {result.avg_ms:>8.2f}ms {result.p95_ms:>8.2f}ms {result.p99_ms:>8.2f}ms {status:<10}")
        
        print("-" * 80)
        
        # Show failures
        failures = [r for r in self.results if not r.passed]
        if failures:
            print("\nFailed Benchmarks:")
            for result in failures:
                print(f"\n  {result.method} {result.endpoint}")
                print(f"    Target p95: {next((t.target_p95_ms for t in self.targets if t.endpoint == result.endpoint), 'N/A')}ms")
                print(f"    Actual p95: {result.p95_ms:.2f}ms")
                print(f"    Target avg: {next((t.target_avg_ms for t in self.targets if t.endpoint == result.endpoint), 'N/A')}ms")
                print(f"    Actual avg: {result.avg_ms:.2f}ms")
                if result.failures:
                    print(f"    Failures: {len(result.failures)}")
                    for failure in result.failures[:5]:  # Show first 5 failures
                        print(f"      - {failure}")
        
        print("\n" + "="*80)


def run_quick_benchmark(client: TestClient) -> bool:
    """Run quick performance benchmark.
    
    Args:
        client: FastAPI test client
    
    Returns:
        True if all benchmarks passed, False otherwise
    """
    benchmark = PerformanceBenchmark(client)
    results = benchmark.run_all_benchmarks(iterations=50)
    benchmark.print_summary()
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    # Run benchmarks when executed directly
    from app.main import app
    
    client = TestClient(app)
    success = run_quick_benchmark(client)
    
    if not success:
        print("\n❌ Some benchmarks failed!")
        exit(1)
    else:
        print("\n✅ All benchmarks passed!")
        exit(0)