"""Bedrock service for foundation model inference."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_bedrock_runtime_client
from src.common.config import get_settings
from src.common.exceptions import BedrockThrottlingError, ContentFilterError, QueryError

logger = Logger()
tracer = Tracer()


class BedrockService:
    """Service for interacting with Amazon Bedrock foundation models."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_bedrock_runtime_client()

    @tracer.capture_method
    def generate_response(
        self,
        prompt: str,
        context: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """
        Generate a response using Claude on Bedrock.

        Args:
            prompt: The user's question or prompt
            context: Optional context from retrieved documents
            system_prompt: Optional system prompt override
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with 'text', 'input_tokens', 'output_tokens', 'stop_reason'
        """
        max_tokens = max_tokens or self.settings.bedrock_max_tokens
        temperature = temperature if temperature is not None else self.settings.bedrock_temperature

        # Build system prompt
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        # Build messages
        messages = []

        if context:
            user_content = f"""Use the following context to answer the question. If the answer cannot be found in the context, say so.

<context>
{context}
</context>

<question>
{prompt}
</question>"""
        else:
            user_content = prompt

        messages.append({"role": "user", "content": user_content})

        # Build request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": messages,
        }

        logger.debug(
            "Invoking Bedrock model",
            model_id=self.settings.bedrock_model_id,
            max_tokens=max_tokens,
        )

        try:
            response = self.client.invoke_model(
                modelId=self.settings.bedrock_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            response_body = json.loads(response["body"].read())

            # Extract response text
            text = ""
            if response_body.get("content"):
                for block in response_body["content"]:
                    if block.get("type") == "text":
                        text += block.get("text", "")

            return {
                "text": text,
                "input_tokens": response_body.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response_body.get("usage", {}).get("output_tokens", 0),
                "stop_reason": response_body.get("stop_reason", ""),
                "model_id": self.settings.bedrock_model_id,
            }

        except self.client.exceptions.ThrottlingException as e:
            logger.warning("Bedrock throttling", error=str(e))
            raise BedrockThrottlingError(
                model_id=self.settings.bedrock_model_id,
                retry_after=60,
            )

        except self.client.exceptions.ModelErrorException as e:
            error_msg = str(e)
            if "content filter" in error_msg.lower():
                raise ContentFilterError(
                    message="Content blocked by Bedrock guardrails",
                    filter_type="model_filter",
                )
            raise QueryError(
                message=f"Model error: {error_msg}",
                reason="model_error",
            )

        except Exception as e:
            logger.exception("Bedrock invocation failed")
            raise QueryError(
                message=f"Failed to generate response: {str(e)}",
                reason="bedrock_error",
            )

    @tracer.capture_method
    def generate_with_citations(
        self,
        prompt: str,
        context_chunks: list[dict[str, Any]],
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate a response with citation markers.

        Args:
            prompt: The user's question
            context_chunks: List of context chunks with metadata

        Returns:
            Dict with 'text', 'citations', token counts
        """
        # Format context with citation markers
        context_parts = []
        for i, chunk in enumerate(context_chunks):
            context_parts.append(f"[{i + 1}] {chunk.get('content', '')}")

        context = "\n\n".join(context_parts)

        system_prompt = """You are a helpful assistant that answers questions based on provided context.
When you use information from the context, cite it using [N] where N is the source number.
If you cannot find the answer in the context, say so.
Be concise and accurate."""

        response = self.generate_response(
            prompt=prompt,
            context=context,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

        # Extract citation numbers from response
        import re
        citation_pattern = r'\[(\d+)\]'
        cited_numbers = set(int(m) for m in re.findall(citation_pattern, response["text"]))

        # Map citations to source chunks
        citations = []
        for num in sorted(cited_numbers):
            if 1 <= num <= len(context_chunks):
                chunk = context_chunks[num - 1]
                citations.append({
                    "citation_number": num,
                    "chunk_id": chunk.get("chunk_id"),
                    "document_id": chunk.get("document_id"),
                    "source_uri": chunk.get("source_uri"),
                    "content_preview": chunk.get("content", "")[:200],
                })

        response["citations"] = citations
        return response

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for RAG queries."""
        return """You are a helpful, accurate, and concise assistant.
Your role is to answer questions based on the provided context.
Follow these guidelines:
1. Base your answers only on the provided context
2. If the context doesn't contain enough information, say so
3. Be concise but thorough
4. Use a professional and helpful tone
5. If asked to do something outside your capabilities, politely decline"""

    @tracer.capture_method
    def summarize(
        self,
        text: str,
        max_length: int = 500,
    ) -> str:
        """
        Summarize the given text.

        Args:
            text: Text to summarize
            max_length: Approximate maximum length of summary

        Returns:
            Summarized text
        """
        prompt = f"""Summarize the following text in approximately {max_length} characters or less.
Maintain the key points and important details.

Text to summarize:
{text}

Summary:"""

        response = self.generate_response(
            prompt=prompt,
            max_tokens=max_length // 2,  # Rough token estimate
            temperature=0.0,
        )

        return response["text"].strip()
