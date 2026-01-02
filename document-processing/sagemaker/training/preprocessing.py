"""
Data preprocessing utilities for document classification training.

This module provides functions to prepare training data from
processed documents in S3.
"""

import json
import logging
from pathlib import Path
from typing import Any

import boto3
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_processed_documents(
    bucket: str,
    prefix: str = "processed/",
    output_dir: str = "/tmp/training_data",
) -> Path:
    """Download processed documents from S3."""
    s3 = boto3.client("s3")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # List objects
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    downloaded = 0
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".json"):
                local_path = output_path / Path(key).name
                s3.download_file(bucket, key, str(local_path))
                downloaded += 1

    logger.info(f"Downloaded {downloaded} files to {output_path}")
    return output_path


def extract_features_from_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract training features from a processed document."""
    metadata = doc.get("metadata", {})

    # Get extraction results
    extraction = metadata.get("extraction", {})
    word_count = extraction.get("words", 0)
    page_count = extraction.get("pages", 1)
    extraction_confidence = extraction.get("confidence", 0)
    has_tables = len(extraction.get("tables", [])) > 0
    has_forms = len(extraction.get("forms", [])) > 0

    # Get analysis results
    analysis = metadata.get("analysis", {})
    entities = analysis.get("entities", [])
    entity_count = len(entities)
    key_phrases = analysis.get("key_phrases", [])
    key_phrase_count = len(key_phrases)
    pii_entities = analysis.get("pii_entities", [])
    has_pii = len(pii_entities) > 0
    moderation_labels = analysis.get("moderation_labels", [])
    is_moderation_flagged = len(moderation_labels) > 0
    sentiment = analysis.get("sentiment", {})
    sentiment_label = sentiment.get("sentiment", "NEUTRAL") if sentiment else "NEUTRAL"

    # Get inference results (for labeled data)
    inference = metadata.get("inference", {})
    predicted_class = inference.get("predicted_class", "OTHER")

    return {
        # Features
        "word_count": word_count,
        "page_count": page_count,
        "extraction_confidence": extraction_confidence,
        "entity_count": entity_count,
        "key_phrase_count": key_phrase_count,
        "has_tables": has_tables,
        "has_forms": has_forms,
        "has_pii": has_pii,
        "is_moderation_flagged": is_moderation_flagged,
        "sentiment": sentiment_label,
        # Label (from manual annotation or previous prediction)
        "label": doc.get("label", predicted_class),
        # Metadata
        "document_id": doc.get("document_id"),
        "document_type": doc.get("document_type"),
    }


def prepare_training_dataset(
    data_dir: str | Path,
    output_path: str | Path,
    min_samples_per_class: int = 10,
) -> pd.DataFrame:
    """Prepare training dataset from processed documents."""
    data_dir = Path(data_dir)
    output_path = Path(output_path)

    all_features = []

    # Process all JSON files
    for json_file in data_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                doc = json.load(f)
                features = extract_features_from_document(doc)
                all_features.append(features)
        except Exception as e:
            logger.warning(f"Failed to process {json_file}: {e}")

    if not all_features:
        raise ValueError(f"No valid documents found in {data_dir}")

    # Create DataFrame
    df = pd.DataFrame(all_features)
    logger.info(f"Extracted features from {len(df)} documents")

    # Check class distribution
    class_counts = df["label"].value_counts()
    logger.info(f"Class distribution:\n{class_counts}")

    # Filter classes with too few samples
    valid_classes = class_counts[class_counts >= min_samples_per_class].index
    df_filtered = df[df["label"].isin(valid_classes)]

    if len(df_filtered) < len(df):
        logger.warning(
            f"Filtered out {len(df) - len(df_filtered)} samples "
            f"from classes with < {min_samples_per_class} samples"
        )

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Saved training data to {output_path}")

    return df_filtered


def generate_synthetic_data(
    num_samples: int = 1000,
    output_path: str | Path = "/tmp/training_data/synthetic.csv",
) -> pd.DataFrame:
    """Generate synthetic training data for testing."""
    import random

    random.seed(42)
    classes = ["INVOICE", "CONTRACT", "REPORT", "RESUME", "OTHER"]

    data = []
    for _ in range(num_samples):
        doc_class = random.choice(classes)

        # Generate features based on class
        if doc_class == "INVOICE":
            word_count = random.randint(200, 800)
            page_count = random.randint(1, 3)
            has_tables = random.random() > 0.3
            entity_count = random.randint(10, 30)
        elif doc_class == "CONTRACT":
            word_count = random.randint(2000, 10000)
            page_count = random.randint(5, 20)
            has_tables = random.random() > 0.7
            entity_count = random.randint(30, 100)
        elif doc_class == "REPORT":
            word_count = random.randint(1000, 5000)
            page_count = random.randint(3, 15)
            has_tables = random.random() > 0.4
            entity_count = random.randint(20, 50)
        elif doc_class == "RESUME":
            word_count = random.randint(300, 1000)
            page_count = random.randint(1, 3)
            has_tables = random.random() > 0.8
            entity_count = random.randint(15, 40)
        else:
            word_count = random.randint(100, 3000)
            page_count = random.randint(1, 10)
            has_tables = random.random() > 0.5
            entity_count = random.randint(5, 50)

        data.append({
            "word_count": word_count,
            "page_count": page_count,
            "extraction_confidence": random.uniform(0.7, 1.0),
            "entity_count": entity_count,
            "key_phrase_count": random.randint(5, 30),
            "has_tables": has_tables,
            "has_forms": random.random() > 0.6,
            "has_pii": random.random() > 0.8,
            "is_moderation_flagged": random.random() > 0.95,
            "label": doc_class,
        })

    df = pd.DataFrame(data)

    # Save to CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated {num_samples} synthetic samples to {output_path}")

    return df


def upload_training_data(
    local_path: str | Path,
    bucket: str,
    prefix: str = "training-data/",
) -> str:
    """Upload training data to S3."""
    s3 = boto3.client("s3")
    local_path = Path(local_path)

    s3_key = f"{prefix}{local_path.name}"
    s3.upload_file(str(local_path), bucket, s3_key)

    s3_uri = f"s3://{bucket}/{s3_key}"
    logger.info(f"Uploaded {local_path} to {s3_uri}")

    return s3_uri


if __name__ == "__main__":
    # Generate synthetic data for testing
    df = generate_synthetic_data(num_samples=1000)
    print(f"Generated dataset shape: {df.shape}")
    print(f"Class distribution:\n{df['label'].value_counts()}")
