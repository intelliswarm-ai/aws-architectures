"""Service for analytics and aggregation operations."""

from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger

from common.config import get_settings
from common.models import (
    AgentMetrics,
    AnalyticsMetrics,
    CallAnalysis,
    Sentiment,
)
from services.opensearch_service import OpenSearchService

logger = Logger()
settings = get_settings()


class AnalyticsService:
    """Service for call analytics operations."""

    def __init__(self, opensearch_service: OpenSearchService | None = None):
        self.opensearch = opensearch_service or OpenSearchService()

    def get_dashboard_summary(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get summary data for dashboard."""
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)

        # Current period metrics
        current_metrics = self.opensearch.get_analytics_metrics(
            date_from=date_from,
            date_to=date_to,
        )

        # Previous period for comparison
        prev_date_from = date_from - timedelta(days=days)
        prev_metrics = self.opensearch.get_analytics_metrics(
            date_from=prev_date_from,
            date_to=date_from,
        )

        # Calculate changes
        def calc_change(current: float, previous: float) -> float:
            if previous == 0:
                return 0
            return ((current - previous) / previous) * 100

        return {
            "period": {
                "days": days,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "metrics": {
                "total_calls": current_metrics.total_calls,
                "total_calls_change": calc_change(
                    current_metrics.total_calls, prev_metrics.total_calls
                ),
                "positive_rate": round(current_metrics.positive_rate * 100, 1),
                "positive_rate_change": calc_change(
                    current_metrics.positive_rate, prev_metrics.positive_rate
                ),
                "negative_rate": round(current_metrics.negative_rate * 100, 1),
                "negative_rate_change": calc_change(
                    current_metrics.negative_rate, prev_metrics.negative_rate
                ),
                "avg_duration": round(current_metrics.avg_duration, 0),
                "avg_duration_change": calc_change(
                    current_metrics.avg_duration, prev_metrics.avg_duration
                ),
            },
            "sentiment_distribution": {
                "positive": current_metrics.positive_calls,
                "negative": current_metrics.negative_calls,
                "neutral": current_metrics.neutral_calls,
                "mixed": current_metrics.mixed_calls,
            },
        }

    def get_sentiment_trend(
        self,
        days: int = 30,
        interval: str = "day",
    ) -> list[dict[str, Any]]:
        """Get sentiment trend over time."""
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)

        return self.opensearch.get_sentiment_trend(
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )

    def get_top_agents(
        self,
        limit: int = 10,
        days: int = 30,
        sort_by: str = "satisfaction",
    ) -> list[dict[str, Any]]:
        """Get top performing agents."""
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)

        # Get all calls in period to extract unique agents
        search_result = self.opensearch.search_calls(
            date_from=date_from,
            date_to=date_to,
            page_size=1000,
        )

        # Get unique agent IDs
        agent_ids = set()
        for call in search_result["calls"]:
            agent_ids.add(call["agentId"])

        # Get metrics for each agent
        agent_metrics = []
        for agent_id in agent_ids:
            metrics = self.opensearch.get_agent_metrics(
                agent_id=agent_id,
                date_from=date_from,
                date_to=date_to,
            )
            agent_metrics.append({
                "agent_id": metrics.agent_id,
                "agent_name": metrics.agent_name,
                "total_calls": metrics.total_calls,
                "positive_calls": metrics.positive_calls,
                "negative_calls": metrics.negative_calls,
                "satisfaction_rate": round(metrics.satisfaction_rate * 100, 1),
                "avg_duration": round(metrics.avg_call_duration, 0),
            })

        # Sort agents
        if sort_by == "satisfaction":
            agent_metrics.sort(key=lambda x: x["satisfaction_rate"], reverse=True)
        elif sort_by == "calls":
            agent_metrics.sort(key=lambda x: x["total_calls"], reverse=True)
        elif sort_by == "negative":
            agent_metrics.sort(key=lambda x: x["negative_calls"], reverse=True)

        return agent_metrics[:limit]

    def get_call_insights(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get insights from recent calls."""
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)

        # Get negative calls for insights
        negative_calls = self.opensearch.search_calls(
            sentiment="NEGATIVE",
            date_from=date_from,
            date_to=date_to,
            page_size=100,
        )

        # Extract common issues from negative calls
        entity_counts: dict[str, int] = {}
        phrase_counts: dict[str, int] = {}

        for call in negative_calls["calls"]:
            for entity in call.get("entities", []):
                text = entity.get("text", "").lower()
                if text:
                    entity_counts[text] = entity_counts.get(text, 0) + 1

            for phrase in call.get("keyPhrases", []):
                phrase_lower = phrase.lower()
                phrase_counts[phrase_lower] = phrase_counts.get(phrase_lower, 0) + 1

        # Get top issues
        top_entities = sorted(
            entity_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]
        top_phrases = sorted(
            phrase_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "period": {
                "days": days,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "negative_calls_analyzed": negative_calls["total"],
            "top_mentioned_entities": [
                {"text": text, "count": count} for text, count in top_entities
            ],
            "common_phrases": [
                {"phrase": phrase, "count": count} for phrase, count in top_phrases
            ],
            "recommendations": self._generate_recommendations(
                negative_calls["total"],
                top_entities,
                top_phrases,
            ),
        }

    def _generate_recommendations(
        self,
        negative_count: int,
        top_entities: list[tuple[str, int]],
        top_phrases: list[tuple[str, int]],
    ) -> list[str]:
        """Generate actionable recommendations from insights."""
        recommendations = []

        if negative_count > 50:
            recommendations.append(
                f"High volume of negative calls ({negative_count}). "
                "Consider reviewing agent training programs."
            )

        # Look for common issues in entities
        for entity, count in top_entities[:3]:
            if count > 5:
                recommendations.append(
                    f"'{entity}' mentioned in {count} negative calls. "
                    "Investigate related issues."
                )

        # Look for problematic phrases
        problem_indicators = ["wait", "slow", "problem", "issue", "frustrated"]
        for phrase, count in top_phrases:
            if any(indicator in phrase for indicator in problem_indicators):
                if count > 3:
                    recommendations.append(
                        f"'{phrase}' appears frequently in negative calls. "
                        "Review related processes."
                    )
                    break

        if not recommendations:
            recommendations.append(
                "No critical issues detected. Continue monitoring call quality."
            )

        return recommendations

    def calculate_quality_score(
        self,
        analysis: CallAnalysis,
    ) -> float:
        """Calculate a quality score for a call (0-100)."""
        score = 50.0  # Base score

        # Sentiment component (up to 30 points)
        sentiment_scores = {
            Sentiment.POSITIVE: 30,
            Sentiment.NEUTRAL: 15,
            Sentiment.MIXED: 5,
            Sentiment.NEGATIVE: -10,
        }
        score += sentiment_scores.get(analysis.overall_sentiment.sentiment, 0)

        # Customer sentiment component (up to 20 points)
        if analysis.customer_sentiment:
            customer_scores = {
                Sentiment.POSITIVE: 20,
                Sentiment.NEUTRAL: 10,
                Sentiment.MIXED: 0,
                Sentiment.NEGATIVE: -15,
            }
            score += customer_scores.get(analysis.customer_sentiment.sentiment, 0)

        # Duration component (normalize long calls)
        if analysis.transcript.duration > 0:
            # Penalize very short (<60s) or very long (>600s) calls
            if analysis.transcript.duration < 60:
                score -= 5
            elif analysis.transcript.duration > 600:
                score -= 10

        # Ensure score is within bounds
        return max(0, min(100, score))
