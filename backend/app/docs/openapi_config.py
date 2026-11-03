"""OpenAPI/Swagger documentation configuration."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from app.models.schemas import APIError


def configure_openapi(app: FastAPI):
    """Configure OpenAPI schema with enterprise documentation."""
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )
        
        # Keep the semantic application version separate from URI versions.
        openapi_schema["info"]["x-api-version"] = app.version
        openapi_schema["info"]["x-api-route-versions"] = ["v1", "v2"]
        openapi_schema["info"]["x-api-lifecycle"] = {
            "current": "v2",
            "deprecated": ["v1"],
            "deprecation_dates": {
                "v1": "2026-12-31"
            },
            "sunset_dates": {
                "v1": "2027-06-30"
            }
        }
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT access token from /api/v1/auth/login; cookie authentication may also be enabled"
            }
        }

        def requires_bearer(dependant) -> bool:
            call = getattr(dependant, "call", None)
            module = getattr(call, "__module__", "")
            name = getattr(call, "__name__", "")
            if module.endswith("services.auth") and name in {
                "get_current_user", "role_checker", "permission_checker"
            }:
                return True
            return any(requires_bearer(child) for child in dependant.dependencies)

        # FastAPI 0.12x+ keeps included routers deferred in app.routes. OpenAPI
        # generation expands them, but iterating app.routes directly only sees
        # `_IncludedRouter` wrappers, so auth/error metadata was silently lost.
        routes = []
        pending = list(app.routes)
        seen_routers = set()
        while pending:
            route = pending.pop()
            if isinstance(route, APIRoute):
                routes.append(route)
                continue
            original_router = getattr(route, "original_router", None)
            if original_router is not None and id(original_router) not in seen_routers:
                seen_routers.add(id(original_router))
                pending.extend(original_router.routes)

        for route in routes:
            path_item = openapi_schema["paths"].get(route.path)
            if not path_item:
                continue
            for method in route.methods or ():
                operation = path_item.get(method.lower())
                if operation is None:
                    continue
                if route.path.startswith("/api/"):
                    operation.setdefault("responses", {}).setdefault(
                        "default",
                        {
                            "description": "API error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIError"}
                                }
                            },
                        },
                    )
                if requires_bearer(route.dependant):
                    operation["security"] = [{"BearerAuth": []}]
                    operation.setdefault("responses", {}).setdefault(
                        "401", {"$ref": "#/components/responses/UnauthorizedError"}
                    )
                    operation.setdefault("responses", {}).setdefault(
                        "403", {"$ref": "#/components/responses/ForbiddenError"}
                    )
                if route.path == "/api/v1/indexing/jobs" and method.upper() == "POST":
                    accepted = operation.get("responses", {}).get("202")
                    if accepted is not None:
                        accepted.setdefault("headers", {})["Location"] = {
                            "description": "URI of the created indexing job resource",
                            "schema": {"type": "string"},
                        }

        components = openapi_schema.setdefault("components", {})
        schemas = components.setdefault("schemas", {})
        error_schema = APIError.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        definitions = error_schema.pop("$defs", {})
        schemas.update(definitions)
        schemas["APIError"] = error_schema
        
        # Add standard error responses
        components["responses"] = {
            "UnauthorizedError": {
                "description": "Authentication required",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/APIError"},
                        "example": {
                            "status": "error",
                            "error_code": "UNAUTHORIZED",
                            "message": "Missing or invalid authentication",
                            "validation_errors": [],
                            "request_id": "123e4567-e89b-12d3-a456-426614174000",
                            "timestamp": 1709452800.0
                        }
                    }
                }
            },
            "ForbiddenError": {
                "description": "Insufficient permissions",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/APIError"},
                        "example": {
                            "status": "error",
                            "error_code": "FORBIDDEN",
                            "message": "Admin role required",
                            "validation_errors": [],
                            "request_id": "123e4567-e89b-12d3-a456-426614174000",
                            "timestamp": 1709452800.0
                        }
                    }
                }
            },
            "RateLimitError": {
                "description": "Rate limit exceeded",
                "headers": {
                    "X-RateLimit-Limit": {
                        "schema": {"type": "integer"},
                        "description": "Request limit per window"
                    },
                    "X-RateLimit-Remaining": {
                        "schema": {"type": "integer"},
                        "description": "Remaining requests in window"
                    },
                    "X-RateLimit-Reset": {
                        "schema": {"type": "integer"},
                        "description": "Unix timestamp when limit resets"
                    },
                    "Retry-After": {
                        "schema": {"type": "integer"},
                        "description": "Seconds to wait before retrying"
                    }
                },
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/APIError"},
                        "example": {
                            "status": "error",
                            "error_code": "RATE_LIMIT_EXCEEDED",
                            "message": "Rate limit exceeded. Try again shortly.",
                            "validation_errors": [],
                            "request_id": "123e4567-e89b-12d3-a456-426614174000",
                            "timestamp": 1709452800.0
                        }
                    }
                }
            },
            "ValidationError": {
                "description": "Validation error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/APIError"},
                        "example": {
                            "status": "error",
                            "error_code": "VALIDATION_ERROR",
                            "message": "Request validation failed",
                            "validation_errors": [
                                {"field": "email", "message": "Invalid email format"},
                                {"field": "password", "message": "Password too short"}
                            ],
                            "request_id": "123e4567-e89b-12d3-a456-426614174000",
                            "timestamp": 1709452800.0
                        }
                    }
                }
            }
        }
        
        # Add standard response headers
        openapi_schema["components"]["headers"] = {
            "X-Request-ID": {
                "description": "Unique request identifier for tracing",
                "schema": {"type": "string", "format": "uuid"}
            },
            "X-RateLimit-Limit": {
                "description": "Request limit per time window",
                "schema": {"type": "integer"}
            },
            "X-RateLimit-Remaining": {
                "description": "Remaining requests in current window",
                "schema": {"type": "integer"}
            },
            "X-RateLimit-Reset": {
                "description": "Unix timestamp when rate limit resets",
                "schema": {"type": "integer"}
            }
        }
        
        # Add examples to common schemas
        if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
            # Add examples to AuthRequest
            if "AuthRequest" in openapi_schema["components"]["schemas"]:
                openapi_schema["components"]["schemas"]["AuthRequest"]["example"] = {
                    "email": "user@example.com",
                    "password": "SecurePass123!"  # nosec
                }
            
            # Add examples to AuthResponse
            if "AuthResponse" in openapi_schema["components"]["schemas"]:
                openapi_schema["components"]["schemas"]["AuthResponse"]["example"] = {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # nosec
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # nosec
                    "token_type": "bearer",  # nosec
                    "expires_in": 1800
                }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    setattr(app, "openapi", custom_openapi)


# Standard error codes
class ErrorCodes:
    """Standard API error codes."""
    
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"  # nosec
    TOKEN_EXPIRED = "TOKEN_EXPIRED"  # nosec
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    
    # Authorization errors
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ADMIN_REQUIRED = "ADMIN_REQUIRED"
    
    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Business logic errors
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_STATE = "INVALID_STATE"
