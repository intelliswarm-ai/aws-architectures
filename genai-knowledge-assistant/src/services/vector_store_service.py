"""Vector store service for OpenSearch Serverless operations."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_opensearch_serverless_client
from src.common.config import get_settings
from src.common.exceptions import OpenSearchError, ResourceNotFoundError

logger = Logger()
tracer = Tracer()


class VectorStoreService:
    """Service for vector storage and search using OpenSearch Serverless."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_opensearch_serverless_client()
        self._http_client = None

    def _get_http_client(self):
        """Get HTTP client for OpenSearch API calls."""
        if self._http_client is None:
            from opensearchpy import OpenSearch, RequestsHttpConnection
            from requests_aws4auth import AWS4Auth
            import boto3

            credentials = boto3.Session().get_credentials()
            auth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                self.settings.aws_region,
                "aoss",
                session_token=credentials.token,
            )

            self._http_client = OpenSearch(
                hosts=[{"host": self.settings.opensearch_collection_endpoint, "port": 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=60,
            )

        return self._http_client

    @tracer.capture_method
    def create_index(self, index_name: str | None = None) -> dict[str, Any]:
        """
        Create a vector index in OpenSearch.

        Args:
            index_name: Name of the index (uses default if not provided)

        Returns:
            Index creation response
        """
        index_name = index_name or self.settings.opensearch_index_name
        client = self._get_http_client()

        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 512,
                }
            },
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": self.settings.opensearch_vector_dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 512,
                                "m": 16,
                            },
                        },
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "text"},
                            "source_uri": {"type": "keyword"},
                            "created_at": {"type": "date"},
                            "tags": {"type": "keyword"},
                        },
                    },
                }
            },
        }

        try:
            if client.indices.exists(index=index_name):
                logger.info("Index already exists", index=index_name)
                return {"acknowledged": True, "index": index_name, "existed": True}

            response = client.indices.create(index=index_name, body=index_body)
            logger.info("Index created", index=index_name)
            return response

        except Exception as e:
            logger.exception("Failed to create index")
            raise OpenSearchError(
                message=f"Failed to create index: {str(e)}",
                index=index_name,
                operation="create_index",
            )

    @tracer.capture_method
    def index_document(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Index a document chunk with its embedding.

        Args:
            chunk_id: Unique ID for this chunk
            document_id: Parent document ID
            content: Text content of the chunk
            embedding: Vector embedding
            metadata: Additional metadata

        Returns:
            Indexing response
        """
        index_name = index_name or self.settings.opensearch_index_name
        client = self._get_http_client()

        doc_body = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
        }

        try:
            response = client.index(
                index=index_name,
                id=chunk_id,
                body=doc_body,
                refresh=True,
            )
            return response

        except Exception as e:
            logger.exception("Failed to index document")
            raise OpenSearchError(
                message=f"Failed to index document: {str(e)}",
                index=index_name,
                operation="index",
            )

    @tracer.capture_method
    def bulk_index(
        self,
        documents: list[dict[str, Any]],
        index_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Bulk index multiple document chunks.

        Args:
            documents: List of documents with chunk_id, document_id, content, embedding
            index_name: Target index name

        Returns:
            Bulk indexing response with success/failure counts
        """
        index_name = index_name or self.settings.opensearch_index_name
        client = self._get_http_client()

        actions = []
        for doc in documents:
            actions.append({"index": {"_index": index_name, "_id": doc["chunk_id"]}})
            actions.append({
                "chunk_id": doc["chunk_id"],
                "document_id": doc["document_id"],
                "content": doc["content"],
                "embedding": doc["embedding"],
                "metadata": doc.get("metadata", {}),
            })

        try:
            response = client.bulk(body=actions, refresh=True)

            # Count successes and failures
            success_count = 0
            failure_count = 0
            errors = []

            for item in response.get("items", []):
                if item.get("index", {}).get("status", 500) < 300:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(item.get("index", {}).get("error", {}))

            return {
                "success_count": success_count,
                "failure_count": failure_count,
                "errors": errors[:10],  # Limit error details
            }

        except Exception as e:
            logger.exception("Bulk indexing failed")
            raise OpenSearchError(
                message=f"Bulk indexing failed: {str(e)}",
                index=index_name,
                operation="bulk_index",
            )

    @tracer.capture_method
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        score_threshold: float = 0.0,
        filters: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filters: Optional filters (e.g., document_id, tags)
            index_name: Target index name

        Returns:
            List of matching documents with scores
        """
        index_name = index_name or self.settings.opensearch_index_name
        client = self._get_http_client()

        # Build KNN query
        query_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": top_k,
                    }
                }
            },
            "_source": ["chunk_id", "document_id", "content", "metadata"],
        }

        # Add filters if provided
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {key: value}})
                else:
                    filter_clauses.append({"term": {key: value}})

            query_body["query"] = {
                "bool": {
                    "must": [query_body["query"]],
                    "filter": filter_clauses,
                }
            }

        try:
            response = client.search(index=index_name, body=query_body)

            results = []
            for hit in response.get("hits", {}).get("hits", []):
                score = hit.get("_score", 0)

                # Apply score threshold
                if score < score_threshold:
                    continue

                source = hit.get("_source", {})
                results.append({
                    "chunk_id": source.get("chunk_id"),
                    "document_id": source.get("document_id"),
                    "content": source.get("content"),
                    "score": score,
                    "metadata": source.get("metadata", {}),
                })

            return results

        except Exception as e:
            logger.exception("Search failed")
            raise OpenSearchError(
                message=f"Search failed: {str(e)}",
                index=index_name,
                operation="search",
            )

    @tracer.capture_method
    def delete_by_document_id(
        self,
        document_id: str,
        index_name: str | None = None,
    ) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of deleted chunks
        """
        index_name = index_name or self.settings.opensearch_index_name
        client = self._get_http_client()

        query_body = {
            "query": {
                "term": {"document_id": document_id}
            }
        }

        try:
            response = client.delete_by_query(
                index=index_name,
                body=query_body,
                refresh=True,
            )
            return response.get("deleted", 0)

        except Exception as e:
            logger.exception("Delete by document ID failed")
            raise OpenSearchError(
                message=f"Delete failed: {str(e)}",
                index=index_name,
                operation="delete_by_query",
            )

    @tracer.capture_method
    def get_document_chunks(
        self,
        document_id: str,
        index_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            List of chunks
        """
        index_name = index_name or self.settings.opensearch_index_name
        client = self._get_http_client()

        query_body = {
            "size": 1000,
            "query": {
                "term": {"document_id": document_id}
            },
            "sort": [{"chunk_id": "asc"}],
            "_source": ["chunk_id", "content", "metadata"],
        }

        try:
            response = client.search(index=index_name, body=query_body)

            return [
                {
                    "chunk_id": hit["_source"]["chunk_id"],
                    "content": hit["_source"]["content"],
                    "metadata": hit["_source"].get("metadata", {}),
                }
                for hit in response.get("hits", {}).get("hits", [])
            ]

        except Exception as e:
            logger.exception("Failed to get document chunks")
            raise OpenSearchError(
                message=f"Failed to get chunks: {str(e)}",
                index=index_name,
                operation="search",
            )
