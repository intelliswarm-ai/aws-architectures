"""Data models for call sentiment analysis."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Speaker(str, Enum):
    """Speaker type in call transcript."""

    AGENT = "AGENT"
    CUSTOMER = "CUSTOMER"
    UNKNOWN = "UNKNOWN"


class Sentiment(str, Enum):
    """Sentiment classification."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"


class EntityType(str, Enum):
    """Entity types from Comprehend."""

    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    DATE = "DATE"
    QUANTITY = "QUANTITY"
    EVENT = "EVENT"
    TITLE = "TITLE"
    COMMERCIAL_ITEM = "COMMERCIAL_ITEM"
    OTHER = "OTHER"


class JobStatus(str, Enum):
    """Comprehend job status."""

    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOP_REQUESTED = "STOP_REQUESTED"
    STOPPED = "STOPPED"


class TranscriptSegment(BaseModel):
    """A segment of the call transcript."""

    speaker: Speaker
    start_time: float = Field(ge=0)
    end_time: float = Field(ge=0)
    text: str
    sentiment: Sentiment | None = None
    sentiment_score: dict[str, float] | None = None

    def to_opensearch_doc(self) -> dict[str, Any]:
        """Convert to OpenSearch document format."""
        return {
            "speaker": self.speaker.value,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "text": self.text,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "sentimentScore": self.sentiment_score,
        }


class CallTranscript(BaseModel):
    """Complete call transcript."""

    call_id: str
    timestamp: datetime
    duration: int = Field(ge=0, description="Call duration in seconds")
    agent_id: str
    agent_name: str | None = None
    customer_id: str
    customer_phone: str | None = None
    queue_name: str | None = None
    language: str = "en"
    segments: list[TranscriptSegment]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_full_text(self) -> str:
        """Get full transcript text."""
        return " ".join(seg.text for seg in self.segments)

    def get_customer_text(self) -> str:
        """Get only customer segments."""
        return " ".join(
            seg.text for seg in self.segments if seg.speaker == Speaker.CUSTOMER
        )

    def get_agent_text(self) -> str:
        """Get only agent segments."""
        return " ".join(
            seg.text for seg in self.segments if seg.speaker == Speaker.AGENT
        )

    def to_comprehend_input(self) -> str:
        """Format for Comprehend analysis."""
        return self.get_full_text()


class SentimentScore(BaseModel):
    """Sentiment confidence scores."""

    positive: float = Field(ge=0, le=1)
    negative: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)
    mixed: float = Field(ge=0, le=1)

    def get_dominant_sentiment(self) -> Sentiment:
        """Get the sentiment with highest score."""
        scores = {
            Sentiment.POSITIVE: self.positive,
            Sentiment.NEGATIVE: self.negative,
            Sentiment.NEUTRAL: self.neutral,
            Sentiment.MIXED: self.mixed,
        }
        return max(scores, key=scores.get)  # type: ignore


class SentimentResult(BaseModel):
    """Result of sentiment analysis."""

    sentiment: Sentiment
    score: SentimentScore
    language: str | None = None


class EntityResult(BaseModel):
    """Entity extracted from text."""

    text: str
    entity_type: EntityType
    score: float = Field(ge=0, le=1)
    begin_offset: int | None = None
    end_offset: int | None = None


class KeyPhraseResult(BaseModel):
    """Key phrase extracted from text."""

    text: str
    score: float = Field(ge=0, le=1)
    begin_offset: int | None = None
    end_offset: int | None = None


class CallAnalysis(BaseModel):
    """Complete analysis result for a call."""

    call_id: str
    transcript: CallTranscript
    overall_sentiment: SentimentResult
    customer_sentiment: SentimentResult | None = None
    agent_sentiment: SentimentResult | None = None
    entities: list[EntityResult] = Field(default_factory=list)
    key_phrases: list[KeyPhraseResult] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    comprehend_job_id: str | None = None

    def to_opensearch_doc(self) -> dict[str, Any]:
        """Convert to OpenSearch document format."""
        return {
            "callId": self.call_id,
            "timestamp": self.transcript.timestamp.isoformat(),
            "duration": self.transcript.duration,
            "agentId": self.transcript.agent_id,
            "agentName": self.transcript.agent_name,
            "customerId": self.transcript.customer_id,
            "customerPhone": self.transcript.customer_phone,
            "queueName": self.transcript.queue_name,
            "language": self.transcript.language,
            "fullText": self.transcript.get_full_text(),
            "customerText": self.transcript.get_customer_text(),
            "agentText": self.transcript.get_agent_text(),
            "sentiment": self.overall_sentiment.sentiment.value,
            "sentimentScore": {
                "positive": self.overall_sentiment.score.positive,
                "negative": self.overall_sentiment.score.negative,
                "neutral": self.overall_sentiment.score.neutral,
                "mixed": self.overall_sentiment.score.mixed,
            },
            "customerSentiment": (
                self.customer_sentiment.sentiment.value
                if self.customer_sentiment
                else None
            ),
            "agentSentiment": (
                self.agent_sentiment.sentiment.value if self.agent_sentiment else None
            ),
            "entities": [
                {
                    "text": e.text,
                    "type": e.entity_type.value,
                    "score": e.score,
                }
                for e in self.entities
            ],
            "keyPhrases": [kp.text for kp in self.key_phrases],
            "analyzedAt": self.analyzed_at.isoformat(),
            "comprehendJobId": self.comprehend_job_id,
            "segments": [seg.to_opensearch_doc() for seg in self.transcript.segments],
        }


class ComprehendJobStatus(BaseModel):
    """Status of a Comprehend analysis job."""

    job_id: str
    job_name: str
    status: JobStatus
    submit_time: datetime | None = None
    end_time: datetime | None = None
    input_s3_uri: str
    output_s3_uri: str | None = None
    message: str | None = None
    documents_processed: int = 0
    documents_failed: int = 0


class AnalyticsMetrics(BaseModel):
    """Aggregated analytics metrics."""

    total_calls: int = 0
    positive_calls: int = 0
    negative_calls: int = 0
    neutral_calls: int = 0
    mixed_calls: int = 0
    avg_duration: float = 0
    avg_positive_score: float = 0
    avg_negative_score: float = 0
    period_start: datetime | None = None
    period_end: datetime | None = None

    @property
    def positive_rate(self) -> float:
        """Calculate positive sentiment rate."""
        return self.positive_calls / self.total_calls if self.total_calls > 0 else 0

    @property
    def negative_rate(self) -> float:
        """Calculate negative sentiment rate."""
        return self.negative_calls / self.total_calls if self.total_calls > 0 else 0


class AgentMetrics(BaseModel):
    """Agent-specific performance metrics."""

    agent_id: str
    agent_name: str | None = None
    total_calls: int = 0
    positive_calls: int = 0
    negative_calls: int = 0
    avg_call_duration: float = 0
    avg_sentiment_score: float = 0
    top_entities: list[str] = Field(default_factory=list)
    period_start: datetime | None = None
    period_end: datetime | None = None

    @property
    def satisfaction_rate(self) -> float:
        """Calculate customer satisfaction rate."""
        return self.positive_calls / self.total_calls if self.total_calls > 0 else 0
