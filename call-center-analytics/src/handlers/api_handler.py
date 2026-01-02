"""Lambda handler for REST API endpoints."""

import json
from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.api_gateway import Response

from common.config import get_settings
from common.exceptions import OpenSearchError, ValidationError
from services.analytics_service import AnalyticsService
from services.opensearch_service import OpenSearchService

logger = Logger()
tracer = Tracer()
settings = get_settings()

app = APIGatewayRestResolver()


def get_opensearch_service() -> OpenSearchService:
    """Get OpenSearch service instance."""
    return OpenSearchService()


def get_analytics_service() -> AnalyticsService:
    """Get Analytics service instance."""
    return AnalyticsService()


@app.get("/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/calls")
def list_calls() -> dict[str, Any]:
    """List and search calls with filters."""
    params = app.current_event.query_string_parameters or {}

    sentiment = params.get("sentiment")
    agent_id = params.get("agent_id")
    customer_id = params.get("customer_id")
    query = params.get("q")
    page = int(params.get("page", 1))
    page_size = min(int(params.get("page_size", 20)), settings.max_page_size)

    # Parse date filters
    date_from = None
    date_to = None
    if params.get("date_from"):
        date_from = datetime.fromisoformat(params["date_from"])
    if params.get("date_to"):
        date_to = datetime.fromisoformat(params["date_to"])

    try:
        opensearch = get_opensearch_service()
        result = opensearch.search_calls(
            sentiment=sentiment,
            agent_id=agent_id,
            customer_id=customer_id,
            date_from=date_from,
            date_to=date_to,
            query_text=query,
            page=page,
            page_size=page_size,
        )
        return result
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@app.get("/calls/<call_id>")
def get_call(call_id: str) -> dict[str, Any]:
    """Get a specific call analysis by ID."""
    try:
        opensearch = get_opensearch_service()
        call = opensearch.get_call_analysis(call_id)

        if not call:
            return Response(
                status_code=404,
                content_type="application/json",
                body=json.dumps({"error": "Call not found"}),
            )

        return call
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@app.get("/stats")
def get_statistics() -> dict[str, Any]:
    """Get aggregated call statistics."""
    params = app.current_event.query_string_parameters or {}

    days = int(params.get("days", 7))

    try:
        analytics = get_analytics_service()
        return analytics.get_dashboard_summary(days=days)
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@app.get("/stats/trend")
def get_sentiment_trend() -> dict[str, Any]:
    """Get sentiment trend over time."""
    params = app.current_event.query_string_parameters or {}

    days = int(params.get("days", 30))
    interval = params.get("interval", "day")

    try:
        analytics = get_analytics_service()
        trend = analytics.get_sentiment_trend(days=days, interval=interval)
        return {"trend": trend, "days": days, "interval": interval}
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@app.get("/agents")
def list_agents() -> dict[str, Any]:
    """List top agents by performance."""
    params = app.current_event.query_string_parameters or {}

    limit = int(params.get("limit", 10))
    days = int(params.get("days", 30))
    sort_by = params.get("sort_by", "satisfaction")

    try:
        analytics = get_analytics_service()
        agents = analytics.get_top_agents(
            limit=limit,
            days=days,
            sort_by=sort_by,
        )
        return {"agents": agents, "limit": limit, "days": days}
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@app.get("/agents/<agent_id>/metrics")
def get_agent_metrics(agent_id: str) -> dict[str, Any]:
    """Get metrics for a specific agent."""
    params = app.current_event.query_string_parameters or {}

    days = int(params.get("days", 30))
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=days)

    try:
        opensearch = get_opensearch_service()
        metrics = opensearch.get_agent_metrics(
            agent_id=agent_id,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "agent_id": metrics.agent_id,
            "agent_name": metrics.agent_name,
            "total_calls": metrics.total_calls,
            "positive_calls": metrics.positive_calls,
            "negative_calls": metrics.negative_calls,
            "satisfaction_rate": round(metrics.satisfaction_rate * 100, 1),
            "avg_call_duration": round(metrics.avg_call_duration, 0),
            "avg_sentiment_score": round(metrics.avg_sentiment_score, 3),
            "top_entities": metrics.top_entities,
            "period": {"days": days},
        }
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@app.get("/insights")
def get_insights() -> dict[str, Any]:
    """Get call insights and recommendations."""
    params = app.current_event.query_string_parameters or {}

    days = int(params.get("days", 7))

    try:
        analytics = get_analytics_service()
        return analytics.get_call_insights(days=days)
    except OpenSearchError as e:
        return Response(
            status_code=500,
            content_type="application/json",
            body=json.dumps({"error": e.message}),
        )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Main Lambda handler for API Gateway."""
    return app.resolve(event, context)
