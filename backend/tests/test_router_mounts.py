"""Regression guard: every router module in backend/app/routes/ must be mounted on the app."""

import importlib
import pathlib

import pytest

from app.main import app


ROUTER_DIR = pathlib.Path(__file__).resolve().parent.parent / "app" / "routes"

# Routers that are intentionally not mounted (temporarily disabled)
EXCLUDED_ROUTERS = {"graphql"}


@pytest.mark.parametrize(
    "module_name",
    [
        p.stem for p in ROUTER_DIR.glob("*.py")
        if p.name != "__init__.py" and p.stem not in EXCLUDED_ROUTERS
    ],
)
def test_router_is_mounted(module_name: str):
    """Each router file in backend/app/routes/ must be included in app.main."""
    # Import the router module dynamically
    module = importlib.import_module(f"app.routes.{module_name}")
    router = getattr(module, "router", None)
    assert router is not None, f"Module {module_name} has no 'router' attribute"

    # Collect all mounted router prefixes/paths from the FastAPI app
    mounted_paths: set[str] = set()
    for route in app.routes:
        if hasattr(route, "path"):
            mounted_paths.add(route.path)
        # _IncludedRouter has original_router which contains the actual router with paths
        if hasattr(route, "original_router"):
            original = route.original_router
            if hasattr(original, "routes"):
                for r in original.routes:
                    if hasattr(r, "path"):
                        mounted_paths.add(r.path)

    # Check that at least one route from this router appears in the app
    router_paths = [r.path for r in router.routes if hasattr(r, "path")]
    assert any(path in mounted_paths for path in router_paths), (
        f"Router {module_name} is not mounted in app.main. "
        f"Router routes: {router_paths}"
    )