"""
Nebula Search Engine — Load Testing with Locust.

Usage:
    pip install locust
    locust -f tests/load/locustfile.py --host=http://localhost:8000
    # Then open http://localhost:8089

For distributed testing:
    locust -f tests/load/locustfile.py --master
    locust -f tests/load/locustfile.py --worker
"""

import random
import uuid
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


class NebulaSearchUser(HttpUser):
    """Simulates a real user interacting with Nebula Search."""

    wait_time = between(1, 5)
    
    def on_start(self):
        """Login on start to simulate authenticated user."""
        self.email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "Test@12345678"
        self.token = None
        self.headers = {}
        
        # Try to signup first (may fail if user exists)
        with self.client.post(
            "/api/v1/auth/signup",
            json={"email": self.email, "password": self.password},
            catch_response=True,
            name="signup",
        ) as resp:
            if resp.status_code == 201:
                resp.success()
            elif resp.status_code == 409:
                resp.success()  # User already exists is fine
        
        # Login
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
            catch_response=True,
            name="login",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token") or data.get("token")
                if self.token:
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    resp.success()
            elif resp.status_code == 423:
                # Locked out, use different user
                resp.failure("Account locked")

    @task(5)
    def health_check(self):
        """Health check endpoint - most called."""
        with self.client.get("/health", name="health", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Health check failed: {resp.status_code}")

    @task(3)
    def search_query(self):
        """Simulate search queries."""
        queries = ["python programming", "machine learning", "web development",
                    "data science", "artificial intelligence", "cloud computing",
                    "docker kubernetes", "react js", "fastapi", "postgresql",
                    "search engine", "information retrieval"]
        query = random.choice(queries)
        
        with self.client.get(
            f"/api/v1/search?q={query}",
            headers=self.headers,
            name="search",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (401, 429):
                resp.success()  # Rate limited or auth issue - still normal
            else:
                resp.failure(f"Search failed: {resp.status_code}")

    @task(2)
    def vector_search(self):
        """Simulate vector/semantic search."""
        queries = ["neural networks", "natural language processing",
                    "computer vision", "deep learning", "transformers"]
        query = random.choice(queries)
        
        with self.client.post(
            "/api/v1/vector/search",
            json={"query": query, "top_k": 5},
            headers=self.headers,
            name="vector_search",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (401, 429):
                resp.success()
            else:
                resp.failure(f"Vector search failed: {resp.status_code}")

    @task(2)
    def autocomplete(self):
        """Test autocomplete endpoint."""
        prefixes = ["py", "mac", "web", "dat", "art", "clo", "doc", "rea", "sea", "inf"]
        prefix = random.choice(prefixes)
        
        with self.client.get(
            f"/api/v1/autocomplete?q={prefix}",
            headers=self.headers,
            name="autocomplete",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (401, 429):
                resp.success()
            else:
                resp.failure(f"Autocomplete failed: {resp.status_code}")

    @task(1)
    def get_profile(self):
        """Get user profile."""
        if not self.token:
            return
        with self.client.get(
            "/api/v1/users/profile",
            headers=self.headers,
            name="get_profile",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 401:
                resp.success()  # Token expired - normal
            else:
                resp.failure(f"Profile failed: {resp.status_code}")

    @task(1)
    def get_dashboard_stats(self):
        """Get analytics dashboard."""
        if not self.token:
            return
        with self.client.get(
            "/api/v1/analytics/dashboard",
            headers=self.headers,
            name="dashboard",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (401, 429):
                resp.success()
            else:
                resp.failure(f"Dashboard failed: {resp.status_code}")

    @task(1)
    def get_metrics(self):
        """Test Prometheus metrics endpoint."""
        with self.client.get("/metrics", name="metrics", catch_response=True) as resp:
            if resp.status_code in (200, 501):
                resp.success()
            else:
                resp.failure(f"Metrics failed: {resp.status_code}")

    @task(1)
    def get_recommendations(self):
        """Test recommendations."""
        if not self.token:
            return
        with self.client.get(
            "/api/v1/recommendations/",
            headers=self.headers,
            name="recommendations",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (401, 429):
                resp.success()
            else:
                resp.failure(f"Recommendations failed: {resp.status_code}")

    @task(1)
    def spell_check(self):
        """Test spell correction."""
        misspellings = ["pyhton", "macine", "webb", "databse", "artficial"]
        word = random.choice(misspellings)
        
        with self.client.get(
            f"/api/v1/spell/check?q={word}",
            headers=self.headers,
            name="spell_check",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code in (401, 429):
                resp.success()
            else:
                resp.failure(f"Spell check failed: {resp.status_code}")


@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    """Log when test environment starts."""
    if isinstance(environment.runner, MasterRunner):
        print("Nebula Search Load Test started in master mode")
    else:
        print("Nebula Search Load Test worker started")


@events.quitting.add_listener
def on_locust_quitting(environment, **_kwargs):
    """Log test summary on quit."""
    stats = environment.runner.stats
    print(f"\n=== NEBULA SEARCH LOAD TEST RESULTS ===")
    print(f"Total requests: {stats.num_requests}")
    print(f"Failures: {stats.num_failures}")
    print(f"Avg response time: {stats.avg_response_time:.2f}ms")
    print(f"P95 response time: {stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"P99 response time: {stats.get_response_time_percentile(0.99):.2f}ms")
    print(f"RPS: {stats.total_rps:.2f}")
    print("=" * 40)