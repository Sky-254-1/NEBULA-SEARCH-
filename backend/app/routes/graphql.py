"""GraphQL route for Nebula Search API."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.search.graphql.schema import schema
from app.services.auth import get_current_user_token_payload

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

        try:
            user = await get_current_user_token_payload(request)
        except HTTPException:
            user = None

        # Resolvers are asynchronous and protected fields use this verified
        # principal instead of a caller-supplied user ID.
        result = await schema.execute(
            query,
            variable_values=variables,
            context_value={"request": request, "user": user},
        )

        if result.errors:
            logger.warning("GraphQL request rejected with %d resolver error(s)", len(result.errors))
            return JSONResponse(
                status_code=200,
                content={
                    "errors": [
                        {"message": "GraphQL operation could not be completed"}
                        for _ in result.errors
                    ],
                    "data": result.data,
                }
            )

        return {"data": result.data}

    except HTTPException:
        raise
    except Exception:
        logger.exception("GraphQL endpoint failed")
        raise HTTPException(status_code=400, detail="Invalid GraphQL request")


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
