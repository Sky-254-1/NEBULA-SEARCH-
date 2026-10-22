"""GraphQL route for Nebula Search API."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.search.graphql.schema import schema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graphql", tags=["graphql"])


@router.post("/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint."""
    try:
        data = await request.json()
        query = data.get("query")
        variables = data.get("variables", {})

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Execute the query
        result = schema.execute_sync(
            query,
            variable_values=variables,
            context_value={"request": request}
        )

        if result.errors:
            logger.error(f"GraphQL errors: {result.errors}")
            return JSONResponse(
                status_code=400,
                content={
                    "errors": [str(error) for error in result.errors],
                    "data": result.data
                }
            )

        return {"data": result.data}

    except Exception as e:
        logger.error(f"GraphQL endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playground")
async def graphql_playground():
    """GraphQL playground for testing queries."""
    return {
        "message": "GraphQL Playground is disabled in production. Use /docs for API documentation."
    }


@router.get("/schema")
async def graphql_schema():
    """Get GraphQL schema as JSON."""
    return {
        "data": schema.introspect()
    }
