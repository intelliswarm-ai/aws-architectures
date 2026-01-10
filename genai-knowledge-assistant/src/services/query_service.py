"""Query service for RAG-based question answering."""

import time
import uuid
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.config import get_settings
from src.common.exceptions import QueryError, ValidationError
from src.common.models import (
    QueryRequest,
    QueryResponse,
    QueryType,
    RetrievalResult,
)
from src.services.bedrock_service import BedrockService
from src.services.embedding_service import EmbeddingService
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.vector_store_service import VectorStoreService

logger = Logger()
tracer = Tracer()


class QueryService:
    """Service for processing RAG queries."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.bedrock_service = BedrockService()
        self.embedding_service = EmbeddingService()
        self.knowledge_base_service = KnowledgeBaseService()
        self.vector_store_service = VectorStoreService()

    @tracer.capture_method
    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a query using RAG pipeline.

        Args:
            request: Query request with question and options

        Returns:
            QueryResponse with answer and sources
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())

        logger.info(
            "Processing query",
            query_id=query_id,
            query_type=request.query_type.value,
            generate_response=request.generate_response,
        )

        # Validate query
        if not request.query.strip():
            raise ValidationError(
                message="Query cannot be empty",
                field="query",
            )

        try:
            # Choose retrieval method based on configuration
            if request.knowledge_base_id or self.settings.knowledge_base_id:
                # Use Bedrock Knowledge Base
                sources = self._retrieve_from_knowledge_base(request)
            else:
                # Use direct OpenSearch retrieval
                sources = self._retrieve_from_vector_store(request)

            # Generate response if requested
            answer = None
            tokens_used = 0

            if request.generate_response and sources:
                generation_result = self._generate_answer(
                    query=request.query,
                    sources=sources,
                )
                answer = generation_result["text"]
                tokens_used = generation_result.get("input_tokens", 0) + generation_result.get("output_tokens", 0)

            elif request.generate_response and not sources:
                # No sources found, generate acknowledgment
                answer = "I couldn't find relevant information in the knowledge base to answer your question. Could you please rephrase or provide more context?"

            latency_ms = int((time.time() - start_time) * 1000)

            return QueryResponse(
                query_id=query_id,
                query=request.query,
                answer=answer,
                sources=sources,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                model_id=self.settings.bedrock_model_id if answer else "",
                conversation_id=request.conversation_id,
            )

        except ValidationError:
            raise
        except QueryError:
            raise
        except Exception as e:
            logger.exception("Query processing failed")
            raise QueryError(
                message=f"Query failed: {str(e)}",
                query=request.query[:200],
                reason="processing_error",
            )

    @tracer.capture_method
    def _retrieve_from_knowledge_base(
        self,
        request: QueryRequest,
    ) -> list[RetrievalResult]:
        """Retrieve using Bedrock Knowledge Base."""
        knowledge_base_id = request.knowledge_base_id or self.settings.knowledge_base_id

        results = self.knowledge_base_service.retrieve(
            query=request.query,
            knowledge_base_id=knowledge_base_id,
            top_k=request.top_k,
            filters=request.filters if request.filters else None,
        )

        sources = []
        for result in results:
            if result["score"] >= request.score_threshold:
                sources.append(
                    RetrievalResult(
                        chunk_id=str(uuid.uuid4()),  # KB doesn't return chunk ID
                        document_id=result.get("metadata", {}).get("document_id", "unknown"),
                        content=result["content"],
                        score=result["score"],
                        source_uri=result.get("source_uri"),
                        metadata=None,  # Could parse metadata here
                    )
                )

        logger.info(
            "Retrieved from Knowledge Base",
            result_count=len(sources),
            threshold=request.score_threshold,
        )

        return sources

    @tracer.capture_method
    def _retrieve_from_vector_store(
        self,
        request: QueryRequest,
    ) -> list[RetrievalResult]:
        """Retrieve using direct OpenSearch vector search."""
        # Generate query embedding
        query_embedding = self.embedding_service.generate_query_embedding(request.query)

        # Search vector store
        results = self.vector_store_service.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filters if request.filters else None,
        )

        sources = []
        for result in results:
            sources.append(
                RetrievalResult(
                    chunk_id=result["chunk_id"],
                    document_id=result["document_id"],
                    content=result["content"],
                    score=result["score"],
                    source_uri=result.get("metadata", {}).get("source_uri"),
                    metadata=None,
                )
            )

        logger.info(
            "Retrieved from vector store",
            result_count=len(sources),
            threshold=request.score_threshold,
        )

        return sources

    @tracer.capture_method
    def _generate_answer(
        self,
        query: str,
        sources: list[RetrievalResult],
    ) -> dict[str, Any]:
        """Generate answer using retrieved context."""
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources):
            context_parts.append(f"[Source {i + 1}]\n{source.content}")

        context = "\n\n".join(context_parts)

        # Generate response with citations
        result = self.bedrock_service.generate_with_citations(
            prompt=query,
            context_chunks=[
                {
                    "content": s.content,
                    "chunk_id": s.chunk_id,
                    "document_id": s.document_id,
                    "source_uri": s.source_uri,
                }
                for s in sources
            ],
        )

        return result

    @tracer.capture_method
    def query_with_rag(
        self,
        query: str,
        knowledge_base_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Simple RAG query using Bedrock Knowledge Base's retrieve_and_generate.

        This is a simpler alternative that uses the built-in RAG capability.
        """
        result = self.knowledge_base_service.retrieve_and_generate(
            query=query,
            knowledge_base_id=knowledge_base_id,
        )

        return {
            "answer": result["answer"],
            "citations": result["citations"],
        }
