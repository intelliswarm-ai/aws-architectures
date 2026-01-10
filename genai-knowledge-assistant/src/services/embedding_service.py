"""Embedding service for text vectorization."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_bedrock_runtime_client
from src.common.config import get_settings
from src.common.exceptions import BedrockThrottlingError, EmbeddingError

logger = Logger()
tracer = Tracer()


class EmbeddingService:
    """Service for generating text embeddings using Bedrock."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_bedrock_runtime_client()

    @tracer.capture_method
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise EmbeddingError(
                message="Cannot generate embedding for empty text",
                text_length=0,
            )

        # Truncate if necessary (Titan has a limit)
        max_chars = 8000
        if len(text) > max_chars:
            logger.warning(
                "Truncating text for embedding",
                original_length=len(text),
                max_length=max_chars,
            )
            text = text[:max_chars]

        try:
            model_id = self.settings.bedrock_embedding_model_id

            if "titan" in model_id.lower():
                return self._generate_titan_embedding(text)
            elif "cohere" in model_id.lower():
                return self._generate_cohere_embedding(text)
            else:
                raise EmbeddingError(
                    message=f"Unsupported embedding model: {model_id}",
                    model_id=model_id,
                )

        except BedrockThrottlingError:
            raise
        except EmbeddingError:
            raise
        except Exception as e:
            logger.exception("Embedding generation failed")
            raise EmbeddingError(
                message=f"Failed to generate embedding: {str(e)}",
                model_id=self.settings.bedrock_embedding_model_id,
                text_length=len(text),
            )

    @tracer.capture_method
    def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 10,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.debug(
                "Processing embedding batch",
                batch_start=i,
                batch_size=len(batch),
            )

            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)

        return embeddings

    def _generate_titan_embedding(self, text: str) -> list[float]:
        """Generate embedding using Amazon Titan."""
        request_body = {
            "inputText": text,
        }

        # Titan V2 supports dimensions and normalization
        if "v2" in self.settings.bedrock_embedding_model_id.lower():
            request_body["dimensions"] = self.settings.opensearch_vector_dimension
            request_body["normalize"] = True

        response = self.client.invoke_model(
            modelId=self.settings.bedrock_embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        embedding = response_body.get("embedding", [])

        if not embedding:
            raise EmbeddingError(
                message="Empty embedding returned from Titan",
                model_id=self.settings.bedrock_embedding_model_id,
            )

        return embedding

    def _generate_cohere_embedding(self, text: str) -> list[float]:
        """Generate embedding using Cohere."""
        request_body = {
            "texts": [text],
            "input_type": "search_document",
        }

        response = self.client.invoke_model(
            modelId=self.settings.bedrock_embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        embeddings = response_body.get("embeddings", [[]])

        if not embeddings or not embeddings[0]:
            raise EmbeddingError(
                message="Empty embedding returned from Cohere",
                model_id=self.settings.bedrock_embedding_model_id,
            )

        return embeddings[0]

    @tracer.capture_method
    def generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding optimized for query/search.

        For Cohere models, this uses 'search_query' input type.
        For Titan, it's the same as document embedding.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        if "cohere" in self.settings.bedrock_embedding_model_id.lower():
            request_body = {
                "texts": [query],
                "input_type": "search_query",
            }

            response = self.client.invoke_model(
                modelId=self.settings.bedrock_embedding_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            response_body = json.loads(response["body"].read())
            embeddings = response_body.get("embeddings", [[]])

            if not embeddings or not embeddings[0]:
                raise EmbeddingError(
                    message="Empty query embedding returned",
                    model_id=self.settings.bedrock_embedding_model_id,
                )

            return embeddings[0]

        # For Titan, use standard embedding
        return self.generate_embedding(query)

    @property
    def vector_dimension(self) -> int:
        """Get the vector dimension for the current embedding model."""
        return self.settings.opensearch_vector_dimension
