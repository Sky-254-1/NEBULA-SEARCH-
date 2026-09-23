"""OpenAPI/Swagger documentation configuration."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


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
        
        # Add enterprise API information
        openapi_schema["info"]["x-api-version"] = "2.0.0"
        openapi_schema["info"]["x-api-lifecycle"] = {
            "current": "v2",
            "deprecated": ["v1"],
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
                "description": "JWT access token obtained from /api/v1/auth/login"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for service accounts"
            }
        }
        
        # Add global security requirement
        openapi_schema["security"] = [{"BearerAuth": []}]
        
        # Add standard error responses
        openapi_schema["components"]["responses"] = {
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
    
    app.openapi = custom_openapi


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