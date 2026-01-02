"""Rekognition service for image analysis."""

from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import NonRetryableError, RetryableError
from src.common.models import AnalysisResult, ImageLabel

logger = Logger()


class RekognitionService:
    """Service for image analysis using Amazon Rekognition."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def analyze_image(
        self,
        bucket: str,
        key: str,
        document_id: str,
        detect_moderation: bool = True,
    ) -> AnalysisResult:
        """
        Perform comprehensive image analysis.
        Includes labels, text detection, and optional moderation.
        """
        try:
            # Detect labels (objects, scenes, concepts)
            labels = self._detect_labels(bucket, key)

            # Detect text in image
            detected_text = self._detect_text(bucket, key)

            # Optional moderation labels
            moderation_labels = []
            if detect_moderation and self.settings.enable_moderation:
                moderation_labels = self._detect_moderation_labels(bucket, key)

            return AnalysisResult(
                document_id=document_id,
                image_labels=labels,
                detected_text=detected_text,
                moderation_labels=moderation_labels,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("ThrottlingException", "ProvisionedThroughputExceededException"):
                raise RetryableError(
                    f"Rekognition throttled: {e}",
                    document_id=document_id,
                    retry_after_seconds=30,
                )
            if error_code == "InvalidS3ObjectException":
                raise NonRetryableError(
                    f"Invalid S3 object for Rekognition: {e}",
                    document_id=document_id,
                )
            raise NonRetryableError(
                f"Rekognition analysis failed: {e}",
                document_id=document_id,
            )

    def _detect_labels(
        self,
        bucket: str,
        key: str,
        max_labels: int = 50,
        min_confidence: float = 70.0,
    ) -> list[ImageLabel]:
        """Detect labels (objects, scenes, concepts) in image."""
        response = self.clients.rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=max_labels,
            MinConfidence=min_confidence,
        )

        labels = []
        for label in response.get("Labels", []):
            parents = [p.get("Name", "") for p in label.get("Parents", [])]
            categories = [c.get("Name", "") for c in label.get("Categories", [])]

            labels.append(
                ImageLabel(
                    name=label.get("Name", ""),
                    confidence=label.get("Confidence", 0),
                    parents=parents,
                    categories=categories,
                )
            )

        logger.info("Detected image labels", count=len(labels))
        return labels

    def _detect_text(self, bucket: str, key: str) -> list[str]:
        """Detect text in image."""
        response = self.clients.rekognition.detect_text(
            Image={"S3Object": {"Bucket": bucket, "Name": key}}
        )

        # Get LINE type detections (not WORD to avoid duplication)
        detected_text = []
        for detection in response.get("TextDetections", []):
            if detection.get("Type") == "LINE":
                text = detection.get("DetectedText", "")
                if text and detection.get("Confidence", 0) > 70:
                    detected_text.append(text)

        logger.info("Detected text in image", line_count=len(detected_text))
        return detected_text

    def _detect_moderation_labels(
        self,
        bucket: str,
        key: str,
        min_confidence: float = 60.0,
    ) -> list[dict[str, Any]]:
        """Detect moderation labels (inappropriate content)."""
        response = self.clients.rekognition.detect_moderation_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MinConfidence=min_confidence,
        )

        moderation_labels = []
        for label in response.get("ModerationLabels", []):
            moderation_labels.append(
                {
                    "name": label.get("Name", ""),
                    "parent_name": label.get("ParentName", ""),
                    "confidence": label.get("Confidence", 0),
                }
            )

        if moderation_labels:
            logger.warning(
                "Detected moderation labels",
                labels=[l["name"] for l in moderation_labels],
            )

        return moderation_labels

    def detect_faces(
        self,
        bucket: str,
        key: str,
        attributes: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Detect faces and facial attributes in image."""
        if attributes is None:
            attributes = ["DEFAULT"]

        response = self.clients.rekognition.detect_faces(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            Attributes=attributes,
        )

        faces = []
        for face in response.get("FaceDetails", []):
            face_data = {
                "confidence": face.get("Confidence", 0),
                "bounding_box": face.get("BoundingBox", {}),
                "age_range": face.get("AgeRange", {}),
                "smile": face.get("Smile", {}),
                "gender": face.get("Gender", {}),
                "emotions": face.get("Emotions", []),
            }
            faces.append(face_data)

        logger.info("Detected faces", count=len(faces))
        return faces

    def compare_faces(
        self,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        similarity_threshold: float = 80.0,
    ) -> list[dict[str, Any]]:
        """Compare faces between two images."""
        response = self.clients.rekognition.compare_faces(
            SourceImage={"S3Object": {"Bucket": source_bucket, "Name": source_key}},
            TargetImage={"S3Object": {"Bucket": target_bucket, "Name": target_key}},
            SimilarityThreshold=similarity_threshold,
        )

        matches = []
        for match in response.get("FaceMatches", []):
            matches.append(
                {
                    "similarity": match.get("Similarity", 0),
                    "face": match.get("Face", {}),
                }
            )

        return matches

    def recognize_celebrities(
        self,
        bucket: str,
        key: str,
    ) -> list[dict[str, Any]]:
        """Recognize celebrities in image."""
        response = self.clients.rekognition.recognize_celebrities(
            Image={"S3Object": {"Bucket": bucket, "Name": key}}
        )

        celebrities = []
        for celeb in response.get("CelebrityFaces", []):
            celebrities.append(
                {
                    "name": celeb.get("Name", ""),
                    "id": celeb.get("Id", ""),
                    "confidence": celeb.get("MatchConfidence", 0),
                    "urls": celeb.get("Urls", []),
                }
            )

        return celebrities
