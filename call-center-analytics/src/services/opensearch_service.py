"""Service for Amazon OpenSearch operations."""

from datetime import datetime
from typing import Any

import boto3
from aws_lambda_powertools import Logger
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from common.config import get_settings
from common.exceptions import OpenSearchError
from common.models import (
    AgentMetrics,
    AnalyticsMetrics,
    CallAnalysis,
    Sentiment,
)

logger = Logger()
settings = get_settings()


def get_opensearch_client() -> OpenSearch:
    """Get OpenSearch client with AWS auth."""
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        settings.aws_region,
        "es",
        session_token=credentials.token,
    )

    return OpenSearch(
        hosts=[{"host": settings.opensearch_endpoint, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )


class OpenSearchService:
    """Service for OpenSearch operations."""

    def __init__(self, client: OpenSearch | None = None):
        self.client = client or get_opensearch_client()
        self.transcripts_index = settings.opensearch_transcripts_index
        self.analytics_index = settings.opensearch_analytics_index

    def create_indices(self) -> None:
        """Create OpenSearch indices with mappings."""
        transcripts_mapping = {
            "mappings": {
                "properties": {
                    "callId": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "duration": {"type": "integer"},
                    "agentId": {"type": "keyword"},
                    "agentName": {"type": "text"},
                    "customerId": {"type": "keyword"},
                    "customerPhone": {"type": "keyword"},
                    "queueName": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "fullText": {"type": "text", "analyzer": "standard"},
                    "customerText": {"type": "text", "analyzer": "standard"},
                    "agentText": {"type": "text", "analyzer": "standard"},
                    "sentiment": {"type": "keyword"},
                    "sentimentScore": {
                        "properties": {
                            "positive": {"type": "float"},
                            "negative": {"type": "float"},
                            "neutral": {"type": "float"},
                            "mixed": {"type": "float"},
                        }
                    },
                    "customerSentiment": {"type": "keyword"},
                    "agentSentiment": {"type": "keyword"},
                    "entities": {
                        "type": "nested",
                        "properties": {
                            "text": {"type": "text"},
                            "type": {"type": "keyword"},
                            "score": {"type": "float"},
                        },
                    },
                    "keyPhrases": {"type": "text"},
                    "analyzedAt": {"type": "date"},
                    "comprehendJobId": {"type": "keyword"},
                    "segments": {
                        "type": "nested",
                        "properties": {
                            "speaker": {"type": "keyword"},
                            "startTime": {"type": "float"},
                            "endTime": {"type": "float"},
                            "text": {"type": "text"},
                            "sentiment": {"type": "keyword"},
                        },
                    },
                }
            },
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
            },
        }

        try:
            if not self.client.indices.exists(index=self.transcripts_index):
                self.client.indices.create(
                    index=self.transcripts_index,
                    body=transcripts_mapping,
                )
                logger.info(f"Created index: {self.transcripts_index}")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise OpenSearchError(
                f"Failed to create index: {e}",
                index=self.transcripts_index,
                operation="create_index",
            )

    def index_call_analysis(self, analysis: CallAnalysis) -> str:
        """Index a call analysis document."""
        try:
            doc = analysis.to_opensearch_doc()
            response = self.client.index(
                index=self.transcripts_index,
                id=analysis.call_id,
                body=doc,
                refresh=True,
            )
            logger.info(f"Indexed call {analysis.call_id}")
            return response["_id"]
        except Exception as e:
            logger.error(f"Error indexing call analysis: {e}")
            raise OpenSearchError(
                f"Failed to index call analysis: {e}",
                index=self.transcripts_index,
                operation="index",
            )

    def get_call_analysis(self, call_id: str) -> dict[str, Any] | None:
        """Get a call analysis by ID."""
        try:
            response = self.client.get(
                index=self.transcripts_index,
                id=call_id,
            )
            return response["_source"]
        except Exception as e:
            if "NotFoundError" in str(type(e)):
                return None
            logger.error(f"Error getting call analysis: {e}")
            raise OpenSearchError(
                f"Failed to get call analysis: {e}",
                index=self.transcripts_index,
                operation="get",
            )

    def search_calls(
        self,
        sentiment: str | None = None,
        agent_id: str | None = None,
        customer_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        query_text: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Search calls with filters."""
        must_clauses = []
        filter_clauses = []

        if sentiment:
            filter_clauses.append({"term": {"sentiment": sentiment.upper()}})

        if agent_id:
            filter_clauses.append({"term": {"agentId": agent_id}})

        if customer_id:
            filter_clauses.append({"term": {"customerId": customer_id}})

        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from.isoformat()
            if date_to:
                date_range["lte"] = date_to.isoformat()
            filter_clauses.append({"range": {"timestamp": date_range}})

        if query_text:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["fullText", "keyPhrases"],
                    }
                }
            )

        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses,
            }
        }

        try:
            response = self.client.search(
                index=self.transcripts_index,
                body={
                    "query": query,
                    "from": (page - 1) * page_size,
                    "size": page_size,
                    "sort": [{"timestamp": {"order": "desc"}}],
                },
            )

            return {
                "total": response["hits"]["total"]["value"],
                "page": page,
                "page_size": page_size,
                "calls": [hit["_source"] for hit in response["hits"]["hits"]],
            }
        except Exception as e:
            logger.error(f"Error searching calls: {e}")
            raise OpenSearchError(
                f"Failed to search calls: {e}",
                index=self.transcripts_index,
                operation="search",
            )

    def get_analytics_metrics(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> AnalyticsMetrics:
        """Get aggregated analytics metrics."""
        filter_clauses = []

        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from.isoformat()
            if date_to:
                date_range["lte"] = date_to.isoformat()
            filter_clauses.append({"range": {"timestamp": date_range}})

        query = {
            "bool": {
                "must": [{"match_all": {}}],
                "filter": filter_clauses,
            }
        }

        aggs = {
            "sentiment_counts": {"terms": {"field": "sentiment"}},
            "avg_duration": {"avg": {"field": "duration"}},
            "avg_positive_score": {"avg": {"field": "sentimentScore.positive"}},
            "avg_negative_score": {"avg": {"field": "sentimentScore.negative"}},
        }

        try:
            response = self.client.search(
                index=self.transcripts_index,
                body={
                    "query": query,
                    "aggs": aggs,
                    "size": 0,
                },
            )

            sentiment_buckets = {
                b["key"]: b["doc_count"]
                for b in response["aggregations"]["sentiment_counts"]["buckets"]
            }

            return AnalyticsMetrics(
                total_calls=response["hits"]["total"]["value"],
                positive_calls=sentiment_buckets.get("POSITIVE", 0),
                negative_calls=sentiment_buckets.get("NEGATIVE", 0),
                neutral_calls=sentiment_buckets.get("NEUTRAL", 0),
                mixed_calls=sentiment_buckets.get("MIXED", 0),
                avg_duration=response["aggregations"]["avg_duration"]["value"] or 0,
                avg_positive_score=response["aggregations"]["avg_positive_score"]["value"] or 0,
                avg_negative_score=response["aggregations"]["avg_negative_score"]["value"] or 0,
                period_start=date_from,
                period_end=date_to,
            )
        except Exception as e:
            logger.error(f"Error getting analytics metrics: {e}")
            raise OpenSearchError(
                f"Failed to get analytics metrics: {e}",
                index=self.transcripts_index,
                operation="aggregate",
            )

    def get_agent_metrics(
        self,
        agent_id: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> AgentMetrics:
        """Get metrics for a specific agent."""
        filter_clauses = [{"term": {"agentId": agent_id}}]

        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["gte"] = date_from.isoformat()
            if date_to:
                date_range["lte"] = date_to.isoformat()
            filter_clauses.append({"range": {"timestamp": date_range}})

        query = {
            "bool": {
                "must": [{"match_all": {}}],
                "filter": filter_clauses,
            }
        }

        aggs = {
            "sentiment_counts": {"terms": {"field": "sentiment"}},
            "avg_duration": {"avg": {"field": "duration"}},
            "avg_sentiment": {"avg": {"field": "sentimentScore.positive"}},
            "top_entities": {
                "nested": {"path": "entities"},
                "aggs": {
                    "entity_texts": {
                        "terms": {"field": "entities.text.keyword", "size": 10}
                    }
                },
            },
            "agent_name": {"terms": {"field": "agentName.keyword", "size": 1}},
        }

        try:
            response = self.client.search(
                index=self.transcripts_index,
                body={
                    "query": query,
                    "aggs": aggs,
                    "size": 0,
                },
            )

            sentiment_buckets = {
                b["key"]: b["doc_count"]
                for b in response["aggregations"]["sentiment_counts"]["buckets"]
            }

            agent_name = None
            if response["aggregations"]["agent_name"]["buckets"]:
                agent_name = response["aggregations"]["agent_name"]["buckets"][0]["key"]

            top_entities = []
            entity_buckets = response["aggregations"]["top_entities"]["entity_texts"]["buckets"]
            top_entities = [b["key"] for b in entity_buckets]

            return AgentMetrics(
                agent_id=agent_id,
                agent_name=agent_name,
                total_calls=response["hits"]["total"]["value"],
                positive_calls=sentiment_buckets.get("POSITIVE", 0),
                negative_calls=sentiment_buckets.get("NEGATIVE", 0),
                avg_call_duration=response["aggregations"]["avg_duration"]["value"] or 0,
                avg_sentiment_score=response["aggregations"]["avg_sentiment"]["value"] or 0,
                top_entities=top_entities,
                period_start=date_from,
                period_end=date_to,
            )
        except Exception as e:
            logger.error(f"Error getting agent metrics: {e}")
            raise OpenSearchError(
                f"Failed to get agent metrics: {e}",
                index=self.transcripts_index,
                operation="aggregate",
            )

    def get_sentiment_trend(
        self,
        date_from: datetime,
        date_to: datetime,
        interval: str = "day",
    ) -> list[dict[str, Any]]:
        """Get sentiment trend over time."""
        query = {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "timestamp": {
                                "gte": date_from.isoformat(),
                                "lte": date_to.isoformat(),
                            }
                        }
                    }
                ]
            }
        }

        aggs = {
            "sentiment_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "calendar_interval": interval,
                },
                "aggs": {
                    "sentiment_counts": {"terms": {"field": "sentiment"}},
                    "avg_positive": {"avg": {"field": "sentimentScore.positive"}},
                },
            }
        }

        try:
            response = self.client.search(
                index=self.transcripts_index,
                body={
                    "query": query,
                    "aggs": aggs,
                    "size": 0,
                },
            )

            trend = []
            for bucket in response["aggregations"]["sentiment_over_time"]["buckets"]:
                sentiment_counts = {
                    b["key"]: b["doc_count"]
                    for b in bucket["sentiment_counts"]["buckets"]
                }
                trend.append({
                    "date": bucket["key_as_string"],
                    "total": bucket["doc_count"],
                    "positive": sentiment_counts.get("POSITIVE", 0),
                    "negative": sentiment_counts.get("NEGATIVE", 0),
                    "neutral": sentiment_counts.get("NEUTRAL", 0),
                    "avg_positive_score": bucket["avg_positive"]["value"],
                })

            return trend
        except Exception as e:
            logger.error(f"Error getting sentiment trend: {e}")
            raise OpenSearchError(
                f"Failed to get sentiment trend: {e}",
                index=self.transcripts_index,
                operation="aggregate",
            )
