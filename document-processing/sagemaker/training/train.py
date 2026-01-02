"""
SageMaker Training Script for Document Classification.

This script trains an XGBoost model to classify documents based on
extracted features from text analysis.
"""

import argparse
import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Document classes
DOCUMENT_CLASSES = ["INVOICE", "CONTRACT", "REPORT", "RESUME", "OTHER"]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train document classifier")

    # Hyperparameters
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--eta", type=float, default=0.2)
    parser.add_argument("--gamma", type=float, default=4)
    parser.add_argument("--min-child-weight", type=float, default=6)
    parser.add_argument("--subsample", type=float, default=0.7)
    parser.add_argument("--num-round", type=int, default=100)
    parser.add_argument("--objective", type=str, default="multi:softmax")
    parser.add_argument("--num-class", type=int, default=5)

    # SageMaker environment
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAINING", "/opt/ml/input/data/training"))
    parser.add_argument("--validation", type=str, default=os.environ.get("SM_CHANNEL_VALIDATION", ""))

    return parser.parse_args()


def load_data(data_path: str) -> pd.DataFrame:
    """Load training data from CSV or JSON files."""
    data_path = Path(data_path)
    all_data = []

    # Load all CSV files
    for csv_file in data_path.glob("*.csv"):
        logger.info(f"Loading {csv_file}")
        df = pd.read_csv(csv_file)
        all_data.append(df)

    # Load all JSON files
    for json_file in data_path.glob("*.json"):
        logger.info(f"Loading {json_file}")
        with open(json_file) as f:
            data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
                all_data.append(df)

    if not all_data:
        raise ValueError(f"No data files found in {data_path}")

    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Loaded {len(combined_df)} samples")

    return combined_df


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, LabelEncoder]:
    """Prepare feature matrix and labels."""
    # Define feature columns
    numeric_features = [
        "word_count",
        "page_count",
        "extraction_confidence",
        "entity_count",
        "key_phrase_count",
    ]

    boolean_features = [
        "has_tables",
        "has_forms",
        "has_pii",
        "is_moderation_flagged",
    ]

    # Ensure all columns exist
    for col in numeric_features + boolean_features:
        if col not in df.columns:
            df[col] = 0

    # Convert boolean to int
    for col in boolean_features:
        df[col] = df[col].astype(int)

    # Build feature matrix
    feature_cols = numeric_features + boolean_features
    X = df[feature_cols].values.astype(np.float32)

    # Handle missing values
    X = np.nan_to_num(X, nan=0.0)

    # Encode labels
    label_encoder = LabelEncoder()
    label_encoder.fit(DOCUMENT_CLASSES)

    if "label" in df.columns:
        y = label_encoder.transform(df["label"].values)
    elif "document_class" in df.columns:
        y = label_encoder.transform(df["document_class"].values)
    else:
        raise ValueError("No label column found in data")

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Label distribution: {np.bincount(y)}")

    return X, y, label_encoder


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    args: argparse.Namespace,
) -> xgb.Booster:
    """Train XGBoost model."""
    # Create DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    # XGBoost parameters
    params = {
        "max_depth": args.max_depth,
        "eta": args.eta,
        "gamma": args.gamma,
        "min_child_weight": args.min_child_weight,
        "subsample": args.subsample,
        "objective": args.objective,
        "num_class": args.num_class,
        "eval_metric": "mlogloss",
    }

    # Train with early stopping
    evals = [(dtrain, "train"), (dval, "validation")]

    model = xgb.train(
        params,
        dtrain,
        num_boost_round=args.num_round,
        evals=evals,
        early_stopping_rounds=10,
        verbose_eval=10,
    )

    return model


def evaluate_model(
    model: xgb.Booster,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_encoder: LabelEncoder,
) -> dict:
    """Evaluate model performance."""
    dtest = xgb.DMatrix(X_test)
    y_pred = model.predict(dtest)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(
        y_test,
        y_pred,
        target_names=label_encoder.classes_,
        output_dict=True,
    )
    conf_matrix = confusion_matrix(y_test, y_pred)

    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"Classification Report:\n{classification_report(y_test, y_pred, target_names=label_encoder.classes_)}")

    return {
        "accuracy": accuracy,
        "classification_report": report,
        "confusion_matrix": conf_matrix.tolist(),
    }


def save_model(
    model: xgb.Booster,
    label_encoder: LabelEncoder,
    metrics: dict,
    model_dir: str,
):
    """Save model artifacts."""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    # Save XGBoost model
    model_path = model_dir / "xgboost-model"
    model.save_model(str(model_path))
    logger.info(f"Saved model to {model_path}")

    # Save label encoder
    encoder_path = model_dir / "label_encoder.joblib"
    joblib.dump(label_encoder, encoder_path)
    logger.info(f"Saved label encoder to {encoder_path}")

    # Save metrics
    metrics_path = model_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")

    # Save model metadata
    metadata = {
        "model_type": "xgboost",
        "classes": list(label_encoder.classes_),
        "num_classes": len(label_encoder.classes_),
        "features": [
            "word_count",
            "page_count",
            "extraction_confidence",
            "entity_count",
            "key_phrase_count",
            "has_tables",
            "has_forms",
            "has_pii",
            "is_moderation_flagged",
        ],
    }
    metadata_path = model_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")


def main():
    """Main training function."""
    args = parse_args()

    logger.info("Starting training job")
    logger.info(f"Arguments: {args}")

    # Load data
    logger.info(f"Loading data from {args.train}")
    df = load_data(args.train)

    # Prepare features
    X, y, label_encoder = prepare_features(df)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Use validation set if provided, otherwise split from training
    if args.validation and Path(args.validation).exists():
        val_df = load_data(args.validation)
        X_val, y_val, _ = prepare_features(val_df)
    else:
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
        )

    logger.info(f"Training set size: {len(X_train)}")
    logger.info(f"Validation set size: {len(X_val)}")
    logger.info(f"Test set size: {len(X_test)}")

    # Train model
    logger.info("Training model...")
    model = train_model(X_train, y_train, X_val, y_val, args)

    # Evaluate model
    logger.info("Evaluating model...")
    metrics = evaluate_model(model, X_test, y_test, label_encoder)

    # Save model
    logger.info(f"Saving model to {args.model_dir}")
    save_model(model, label_encoder, metrics, args.model_dir)

    logger.info("Training complete!")


if __name__ == "__main__":
    main()
