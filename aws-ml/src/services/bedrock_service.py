"""Bedrock service for generative AI operations."""

import json
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import GenerationError, RetryableError
from src.common.models import GenerativeResult
from src.common.utils import truncate_text

logger = Logger()

# Maximum context window (Claude 3 Sonnet)
MAX_INPUT_TOKENS = 100000


class BedrockService:
    """Service for generative AI using Amazon Bedrock."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def generate_summary(
        self,
        document_id: str,
        text: str,
        max_length: int = 500,
    ) -> GenerativeResult:
        """Generate a summary of the document text."""
        if not self.settings.enable_summarization:
            return GenerativeResult(document_id=document_id)

        prompt = f"""Please provide a concise summary of the following document in {max_length} words or less.
Focus on the main points, key findings, and important details.

Document:
{truncate_text(text, 50000)}

Summary:"""

        response = self._invoke_model(document_id, prompt)

        return GenerativeResult(
            document_id=document_id,
            summary=response["text"],
            model_id=self.settings.bedrock_model_id,
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def generate_qa_pairs(
        self,
        document_id: str,
        text: str,
        num_pairs: int = 5,
    ) -> GenerativeResult:
        """Generate question-answer pairs from document."""
        if not self.settings.enable_qa_generation:
            return GenerativeResult(document_id=document_id)

        prompt = f"""Based on the following document, generate {num_pairs} question-answer pairs that would help someone understand the key information in this document.

Format your response as a JSON array with objects containing "question" and "answer" fields.

Document:
{truncate_text(text, 50000)}

Q&A Pairs (JSON array):"""

        response = self._invoke_model(document_id, prompt)

        # Parse Q&A pairs from response
        questions = self._parse_qa_response(response["text"])

        return GenerativeResult(
            document_id=document_id,
            questions=questions,
            model_id=self.settings.bedrock_model_id,
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def extract_topics(
        self,
        document_id: str,
        text: str,
        max_topics: int = 10,
    ) -> GenerativeResult:
        """Extract main topics from document."""
        prompt = f"""Identify the {max_topics} most important topics or themes in the following document.
Return them as a simple list, one topic per line.

Document:
{truncate_text(text, 50000)}

Topics:"""

        response = self._invoke_model(document_id, prompt)

        # Parse topics from response
        topics = [
            line.strip().lstrip("- •").strip()
            for line in response["text"].split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        return GenerativeResult(
            document_id=document_id,
            topics=topics[:max_topics],
            model_id=self.settings.bedrock_model_id,
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def extract_action_items(
        self,
        document_id: str,
        text: str,
    ) -> GenerativeResult:
        """Extract action items or tasks from document."""
        prompt = f"""Identify any action items, tasks, or next steps mentioned in the following document.
Return them as a simple list, one action item per line.
If no action items are found, return "No action items found."

Document:
{truncate_text(text, 50000)}

Action Items:"""

        response = self._invoke_model(document_id, prompt)

        # Parse action items from response
        action_items = []
        if "no action items" not in response["text"].lower():
            action_items = [
                line.strip().lstrip("- •[]").strip()
                for line in response["text"].split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

        return GenerativeResult(
            document_id=document_id,
            action_items=action_items,
            model_id=self.settings.bedrock_model_id,
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def process_document(
        self,
        document_id: str,
        text: str,
    ) -> GenerativeResult:
        """
        Comprehensive document processing.
        Generates summary, Q&A, topics, and action items in one call.
        """
        prompt = f"""Analyze the following document and provide:
1. A concise summary (2-3 paragraphs)
2. 5 question-answer pairs about the key information
3. Up to 10 main topics or themes
4. Any action items or next steps mentioned

Format your response as JSON with the following structure:
{{
    "summary": "...",
    "questions": [{{"question": "...", "answer": "..."}}],
    "topics": ["topic1", "topic2"],
    "action_items": ["item1", "item2"]
}}

Document:
{truncate_text(text, 40000)}

Analysis (JSON):"""

        response = self._invoke_model(document_id, prompt)

        # Parse JSON response
        try:
            result = json.loads(self._extract_json(response["text"]))
            return GenerativeResult(
                document_id=document_id,
                summary=result.get("summary", ""),
                questions=result.get("questions", []),
                topics=result.get("topics", []),
                action_items=result.get("action_items", []),
                model_id=self.settings.bedrock_model_id,
                input_tokens=response["input_tokens"],
                output_tokens=response["output_tokens"],
            )
        except json.JSONDecodeError:
            # Fall back to raw text as summary
            return GenerativeResult(
                document_id=document_id,
                summary=response["text"],
                model_id=self.settings.bedrock_model_id,
                input_tokens=response["input_tokens"],
                output_tokens=response["output_tokens"],
            )

    def _invoke_model(
        self,
        document_id: str,
        prompt: str,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Invoke Bedrock model with prompt."""
        try:
            model_id = self.settings.bedrock_model_id
            max_tokens = max_tokens or self.settings.bedrock_max_tokens

            # Format request for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": self.settings.bedrock_temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = self.clients.bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            result = json.loads(response["body"].read().decode("utf-8"))

            # Extract text from Claude response
            content = result.get("content", [])
            text = content[0].get("text", "") if content else ""

            return {
                "text": text,
                "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                "output_tokens": result.get("usage", {}).get("output_tokens", 0),
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("ThrottlingException", "ServiceUnavailableException"):
                raise RetryableError(
                    f"Bedrock throttled: {e}",
                    document_id=document_id,
                    retry_after_seconds=10,
                )
            if error_code == "ModelNotReadyException":
                raise RetryableError(
                    f"Bedrock model not ready: {e}",
                    document_id=document_id,
                    retry_after_seconds=30,
                )
            raise GenerationError(
                f"Bedrock invocation failed: {e}",
                document_id=document_id,
                model_id=self.settings.bedrock_model_id,
            )

    def _parse_qa_response(self, text: str) -> list[dict[str, str]]:
        """Parse Q&A pairs from model response."""
        try:
            # Try to parse as JSON
            json_text = self._extract_json(text)
            qa_pairs = json.loads(json_text)
            if isinstance(qa_pairs, list):
                return qa_pairs
        except (json.JSONDecodeError, ValueError):
            pass

        # Fall back to simple parsing
        qa_pairs = []
        lines = text.split("\n")
        current_q = ""

        for line in lines:
            line = line.strip()
            if line.lower().startswith(("q:", "question:")):
                current_q = line.split(":", 1)[1].strip()
            elif line.lower().startswith(("a:", "answer:")) and current_q:
                answer = line.split(":", 1)[1].strip()
                qa_pairs.append({"question": current_q, "answer": answer})
                current_q = ""

        return qa_pairs

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may have surrounding content."""
        # Find JSON array or object
        start_chars = ["{", "["]
        end_chars = ["}", "]"]

        for start, end in zip(start_chars, end_chars):
            start_idx = text.find(start)
            if start_idx >= 0:
                # Find matching closing bracket
                depth = 0
                for i, char in enumerate(text[start_idx:], start_idx):
                    if char == start:
                        depth += 1
                    elif char == end:
                        depth -= 1
                        if depth == 0:
                            return text[start_idx : i + 1]

        return text
