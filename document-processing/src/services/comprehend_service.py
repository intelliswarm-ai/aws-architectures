"""Comprehend service for NLP analysis."""

from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import NonRetryableError, RetryableError
from src.common.models import AnalysisResult, EntityResult, SentimentResult
from src.common.utils import truncate_text

logger = Logger()

# Comprehend limits
MAX_TEXT_BYTES = 5000  # 5KB for sync operations
MAX_BATCH_SIZE = 25


class ComprehendService:
    """Service for NLP analysis using Amazon Comprehend."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def analyze_text(
        self,
        text: str,
        document_id: str,
        detect_pii: bool = True,
    ) -> AnalysisResult:
        """
        Perform comprehensive NLP analysis on text.
        Includes entities, sentiment, key phrases, and language detection.
        """
        # Truncate text if too long
        text = truncate_text(text, MAX_TEXT_BYTES)

        if not text.strip():
            return AnalysisResult(document_id=document_id)

        try:
            # Detect language first
            language = self._detect_language(text)

            # Run analyses in parallel would be ideal, but for simplicity we do sequentially
            entities = self._detect_entities(text, language)
            sentiment = self._detect_sentiment(text, language)
            key_phrases = self._detect_key_phrases(text, language)

            # Optionally detect PII
            pii_entities = []
            if detect_pii and self.settings.enable_pii_detection:
                pii_entities = self._detect_pii(text, language)

            return AnalysisResult(
                document_id=document_id,
                entities=entities,
                key_phrases=key_phrases,
                sentiment=sentiment,
                language=language,
                pii_entities=pii_entities,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("ThrottlingException", "ProvisionedThroughputExceededException"):
                raise RetryableError(
                    f"Comprehend throttled: {e}",
                    document_id=document_id,
                    retry_after_seconds=30,
                )
            raise NonRetryableError(
                f"Comprehend analysis failed: {e}",
                document_id=document_id,
            )

    def _detect_language(self, text: str) -> str:
        """Detect dominant language in text."""
        response = self.clients.comprehend.detect_dominant_language(Text=text)
        languages = response.get("Languages", [])

        if languages:
            # Return highest confidence language
            best = max(languages, key=lambda x: x.get("Score", 0))
            return best.get("LanguageCode", "en")
        return "en"

    def _detect_entities(self, text: str, language: str) -> list[EntityResult]:
        """Detect named entities in text."""
        response = self.clients.comprehend.detect_entities(
            Text=text,
            LanguageCode=language,
        )

        entities = []
        for entity in response.get("Entities", []):
            entities.append(
                EntityResult(
                    text=entity.get("Text", ""),
                    entity_type=entity.get("Type", "OTHER"),
                    score=entity.get("Score", 0),
                    begin_offset=entity.get("BeginOffset"),
                    end_offset=entity.get("EndOffset"),
                )
            )

        logger.info(
            "Detected entities",
            count=len(entities),
            language=language,
        )
        return entities

    def _detect_sentiment(self, text: str, language: str) -> SentimentResult:
        """Detect sentiment in text."""
        response = self.clients.comprehend.detect_sentiment(
            Text=text,
            LanguageCode=language,
        )

        scores = response.get("SentimentScore", {})
        return SentimentResult(
            sentiment=response.get("Sentiment", "NEUTRAL"),
            positive=scores.get("Positive", 0),
            negative=scores.get("Negative", 0),
            neutral=scores.get("Neutral", 0),
            mixed=scores.get("Mixed", 0),
        )

    def _detect_key_phrases(self, text: str, language: str) -> list[str]:
        """Detect key phrases in text."""
        response = self.clients.comprehend.detect_key_phrases(
            Text=text,
            LanguageCode=language,
        )

        # Return top key phrases by score
        phrases = response.get("KeyPhrases", [])
        sorted_phrases = sorted(phrases, key=lambda x: x.get("Score", 0), reverse=True)

        return [p.get("Text", "") for p in sorted_phrases[:20]]

    def _detect_pii(self, text: str, language: str) -> list[EntityResult]:
        """Detect PII entities in text."""
        try:
            response = self.clients.comprehend.detect_pii_entities(
                Text=text,
                LanguageCode=language,
            )

            pii_entities = []
            for entity in response.get("Entities", []):
                pii_entities.append(
                    EntityResult(
                        text=text[entity.get("BeginOffset", 0) : entity.get("EndOffset", 0)],
                        entity_type=entity.get("Type", "OTHER"),
                        score=entity.get("Score", 0),
                        begin_offset=entity.get("BeginOffset"),
                        end_offset=entity.get("EndOffset"),
                    )
                )

            logger.info("Detected PII entities", count=len(pii_entities))
            return pii_entities

        except ClientError as e:
            # PII detection may not be available in all languages
            logger.warning(f"PII detection failed: {e}")
            return []

    def classify_document(
        self,
        text: str,
        endpoint_arn: str,
    ) -> dict[str, Any]:
        """Classify document using custom Comprehend classifier."""
        text = truncate_text(text, MAX_TEXT_BYTES)

        response = self.clients.comprehend.classify_document(
            Text=text,
            EndpointArn=endpoint_arn,
        )

        classes = response.get("Classes", [])
        if classes:
            top_class = max(classes, key=lambda x: x.get("Score", 0))
            return {
                "class": top_class.get("Name"),
                "confidence": top_class.get("Score", 0),
                "all_classes": {c.get("Name"): c.get("Score", 0) for c in classes},
            }
        return {"class": None, "confidence": 0, "all_classes": {}}

    def batch_detect_entities(
        self,
        texts: list[str],
        language: str = "en",
    ) -> list[list[EntityResult]]:
        """Detect entities in batch of texts."""
        # Truncate and filter empty texts
        processed_texts = [truncate_text(t, MAX_TEXT_BYTES) for t in texts if t.strip()]

        if not processed_texts:
            return []

        results: list[list[EntityResult]] = []

        # Process in batches of MAX_BATCH_SIZE
        for i in range(0, len(processed_texts), MAX_BATCH_SIZE):
            batch = processed_texts[i : i + MAX_BATCH_SIZE]

            response = self.clients.comprehend.batch_detect_entities(
                TextList=batch,
                LanguageCode=language,
            )

            for result in response.get("ResultList", []):
                entities = [
                    EntityResult(
                        text=e.get("Text", ""),
                        entity_type=e.get("Type", "OTHER"),
                        score=e.get("Score", 0),
                        begin_offset=e.get("BeginOffset"),
                        end_offset=e.get("EndOffset"),
                    )
                    for e in result.get("Entities", [])
                ]
                results.append(entities)

        return results
