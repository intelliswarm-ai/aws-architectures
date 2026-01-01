"""Service for Amazon Comprehend operations."""

import uuid
from datetime import datetime

import boto3
from aws_lambda_powertools import Logger

from common.config import get_settings
from common.exceptions import ComprehendError
from common.models import (
    CallTranscript,
    ComprehendJobStatus,
    EntityResult,
    EntityType,
    JobStatus,
    KeyPhraseResult,
    Sentiment,
    SentimentResult,
    SentimentScore,
)

logger = Logger()
settings = get_settings()


def get_comprehend_client():
    """Get Comprehend client."""
    return boto3.client("comprehend", region_name=settings.aws_region)


class ComprehendService:
    """Service for Amazon Comprehend sentiment analysis."""

    def __init__(self, client=None):
        self.client = client or get_comprehend_client()

    def detect_sentiment(
        self,
        text: str,
        language: str = "en",
    ) -> SentimentResult:
        """Detect sentiment for text synchronously."""
        if not text.strip():
            return SentimentResult(
                sentiment=Sentiment.NEUTRAL,
                score=SentimentScore(
                    positive=0.0, negative=0.0, neutral=1.0, mixed=0.0
                ),
                language=language,
            )

        try:
            # Truncate text to Comprehend limit (5000 bytes)
            text_bytes = text.encode("utf-8")[:5000].decode("utf-8", errors="ignore")

            response = self.client.detect_sentiment(
                Text=text_bytes,
                LanguageCode=language,
            )

            score = SentimentScore(
                positive=response["SentimentScore"]["Positive"],
                negative=response["SentimentScore"]["Negative"],
                neutral=response["SentimentScore"]["Neutral"],
                mixed=response["SentimentScore"]["Mixed"],
            )

            return SentimentResult(
                sentiment=Sentiment(response["Sentiment"]),
                score=score,
                language=language,
            )

        except self.client.exceptions.TextSizeLimitExceededException:
            logger.warning("Text too large for sentiment detection, truncating")
            return self.detect_sentiment(text[:2500], language)
        except Exception as e:
            logger.error(f"Error detecting sentiment: {e}")
            raise ComprehendError(
                f"Failed to detect sentiment: {e}",
                operation="detect_sentiment",
            )

    def detect_entities(
        self,
        text: str,
        language: str = "en",
    ) -> list[EntityResult]:
        """Extract entities from text."""
        if not text.strip():
            return []

        try:
            text_bytes = text.encode("utf-8")[:5000].decode("utf-8", errors="ignore")

            response = self.client.detect_entities(
                Text=text_bytes,
                LanguageCode=language,
            )

            entities = []
            for entity in response["Entities"]:
                try:
                    entity_type = EntityType(entity["Type"])
                except ValueError:
                    entity_type = EntityType.OTHER

                entities.append(
                    EntityResult(
                        text=entity["Text"],
                        entity_type=entity_type,
                        score=entity["Score"],
                        begin_offset=entity.get("BeginOffset"),
                        end_offset=entity.get("EndOffset"),
                    )
                )

            return entities

        except Exception as e:
            logger.error(f"Error detecting entities: {e}")
            raise ComprehendError(
                f"Failed to detect entities: {e}",
                operation="detect_entities",
            )

    def detect_key_phrases(
        self,
        text: str,
        language: str = "en",
    ) -> list[KeyPhraseResult]:
        """Extract key phrases from text."""
        if not text.strip():
            return []

        try:
            text_bytes = text.encode("utf-8")[:5000].decode("utf-8", errors="ignore")

            response = self.client.detect_key_phrases(
                Text=text_bytes,
                LanguageCode=language,
            )

            return [
                KeyPhraseResult(
                    text=phrase["Text"],
                    score=phrase["Score"],
                    begin_offset=phrase.get("BeginOffset"),
                    end_offset=phrase.get("EndOffset"),
                )
                for phrase in response["KeyPhrases"]
            ]

        except Exception as e:
            logger.error(f"Error detecting key phrases: {e}")
            raise ComprehendError(
                f"Failed to detect key phrases: {e}",
                operation="detect_key_phrases",
            )

    def detect_language(self, text: str) -> str:
        """Detect dominant language in text."""
        if not text.strip():
            return "en"

        try:
            text_bytes = text.encode("utf-8")[:5000].decode("utf-8", errors="ignore")

            response = self.client.detect_dominant_language(Text=text_bytes)

            if response["Languages"]:
                return response["Languages"][0]["LanguageCode"]
            return "en"

        except Exception as e:
            logger.warning(f"Error detecting language, defaulting to en: {e}")
            return "en"

    def start_sentiment_batch_job(
        self,
        input_s3_uri: str,
        output_s3_uri: str,
        language: str = "en",
        job_name: str | None = None,
    ) -> ComprehendJobStatus:
        """Start a batch sentiment analysis job."""
        if not job_name:
            job_name = f"{settings.comprehend_job_prefix}-{uuid.uuid4().hex[:8]}"

        try:
            response = self.client.start_sentiment_detection_job(
                InputDataConfig={
                    "S3Uri": input_s3_uri,
                    "InputFormat": "ONE_DOC_PER_LINE",
                },
                OutputDataConfig={
                    "S3Uri": output_s3_uri,
                },
                DataAccessRoleArn=settings.comprehend_role_arn,
                JobName=job_name,
                LanguageCode=language,
            )

            return ComprehendJobStatus(
                job_id=response["JobId"],
                job_name=job_name,
                status=JobStatus(response["JobStatus"]),
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
                submit_time=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error starting batch job: {e}")
            raise ComprehendError(
                f"Failed to start batch job: {e}",
                operation="start_sentiment_detection_job",
            )

    def start_entities_batch_job(
        self,
        input_s3_uri: str,
        output_s3_uri: str,
        language: str = "en",
        job_name: str | None = None,
    ) -> ComprehendJobStatus:
        """Start a batch entity detection job."""
        if not job_name:
            job_name = f"{settings.comprehend_job_prefix}-entities-{uuid.uuid4().hex[:8]}"

        try:
            response = self.client.start_entities_detection_job(
                InputDataConfig={
                    "S3Uri": input_s3_uri,
                    "InputFormat": "ONE_DOC_PER_LINE",
                },
                OutputDataConfig={
                    "S3Uri": output_s3_uri,
                },
                DataAccessRoleArn=settings.comprehend_role_arn,
                JobName=job_name,
                LanguageCode=language,
            )

            return ComprehendJobStatus(
                job_id=response["JobId"],
                job_name=job_name,
                status=JobStatus(response["JobStatus"]),
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
                submit_time=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error starting entities batch job: {e}")
            raise ComprehendError(
                f"Failed to start entities batch job: {e}",
                operation="start_entities_detection_job",
            )

    def get_job_status(self, job_id: str, job_type: str = "sentiment") -> ComprehendJobStatus:
        """Get status of a batch job."""
        try:
            if job_type == "sentiment":
                response = self.client.describe_sentiment_detection_job(JobId=job_id)
                job = response["SentimentDetectionJobProperties"]
            else:
                response = self.client.describe_entities_detection_job(JobId=job_id)
                job = response["EntitiesDetectionJobProperties"]

            return ComprehendJobStatus(
                job_id=job["JobId"],
                job_name=job.get("JobName", ""),
                status=JobStatus(job["JobStatus"]),
                submit_time=job.get("SubmitTime"),
                end_time=job.get("EndTime"),
                input_s3_uri=job["InputDataConfig"]["S3Uri"],
                output_s3_uri=job.get("OutputDataConfig", {}).get("S3Uri"),
                message=job.get("Message"),
            )

        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            raise ComprehendError(
                f"Failed to get job status: {e}",
                job_id=job_id,
                operation="describe_job",
            )

    def analyze_transcript(self, transcript: CallTranscript) -> dict:
        """Perform full analysis on a transcript."""
        language = transcript.language

        # Detect language if enabled
        if settings.enable_language_detection:
            detected = self.detect_language(transcript.get_full_text())
            if detected:
                language = detected

        # Overall sentiment
        overall_sentiment = self.detect_sentiment(
            transcript.get_full_text(),
            language,
        )

        # Customer sentiment
        customer_sentiment = None
        customer_text = transcript.get_customer_text()
        if customer_text:
            customer_sentiment = self.detect_sentiment(customer_text, language)

        # Agent sentiment
        agent_sentiment = None
        agent_text = transcript.get_agent_text()
        if agent_text:
            agent_sentiment = self.detect_sentiment(agent_text, language)

        # Entities
        entities = []
        if settings.enable_entity_extraction:
            entities = self.detect_entities(transcript.get_full_text(), language)

        # Key phrases
        key_phrases = []
        if settings.enable_key_phrase_extraction:
            key_phrases = self.detect_key_phrases(transcript.get_full_text(), language)

        return {
            "overall_sentiment": overall_sentiment,
            "customer_sentiment": customer_sentiment,
            "agent_sentiment": agent_sentiment,
            "entities": entities,
            "key_phrases": key_phrases,
            "language": language,
        }
