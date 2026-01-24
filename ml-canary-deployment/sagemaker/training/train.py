"""Training script for content recommendation model.

This script trains an XGBoost model for media content recommendations
using user viewing history and content features.

The model predicts engagement scores for content recommendations,
optimized for sub-100ms inference latency in production.
"""

import argparse
import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, ndcg_score
from sklearn.model_selection import train_test_split


def parse_args():
    """Parse training arguments."""
    parser = argparse.ArgumentParser()

    # Hyperparameters
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--eta", type=float, default=0.3)
    parser.add_argument("--subsample", type=float, default=0.8)
    parser.add_argument("--colsample-bytree", type=float, default=0.8)
    parser.add_argument("--num-round", type=int, default=100)
    parser.add_argument("--early-stopping-rounds", type=int, default=10)
    parser.add_argument("--objective", type=str, default="reg:squarederror")
    parser.add_argument("--eval-metric", type=str, default="rmse")

    # SageMaker specific arguments
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument("--validation", type=str, default=os.environ.get("SM_CHANNEL_VALIDATION", "/opt/ml/input/data/validation"))
    parser.add_argument("--output-data-dir", type=str, default=os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data"))

    return parser.parse_args()


def load_data(data_dir: str) -> tuple[np.ndarray, np.ndarray]:
    """Load training data from CSV files.

    Args:
        data_dir: Directory containing CSV files.

    Returns:
        Tuple of features (X) and labels (y).
    """
    data_path = Path(data_dir)
    csv_files = list(data_path.glob("*.csv"))

    if not csv_files:
        raise ValueError(f"No CSV files found in {data_dir}")

    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)

    data = pd.concat(dfs, ignore_index=True)

    # Assume last column is target (engagement_score)
    X = data.iloc[:, :-1].values
    y = data.iloc[:, -1].values

    print(f"Loaded {len(X)} samples with {X.shape[1]} features")

    return X, y


def create_feature_metadata(num_features: int) -> dict:
    """Create feature metadata for model serving.

    Args:
        num_features: Number of input features.

    Returns:
        Feature metadata dictionary.
    """
    # Define expected features for media recommendation
    feature_names = [
        # User features
        "user_watch_time_30d",
        "user_sessions_30d",
        "user_avg_session_length",
        "user_completion_rate",
        "user_genre_diversity",
        "user_recency_days",
        # Content features
        "content_popularity_score",
        "content_release_recency",
        "content_duration_minutes",
        "content_genre_encoded",
        "content_rating_encoded",
        "content_avg_completion_rate",
        # Interaction features
        "user_genre_affinity",
        "time_of_day_encoded",
        "day_of_week_encoded",
        "device_type_encoded",
    ]

    # Pad or truncate to match actual feature count
    if len(feature_names) < num_features:
        feature_names.extend([f"feature_{i}" for i in range(len(feature_names), num_features)])
    else:
        feature_names = feature_names[:num_features]

    return {
        "feature_names": feature_names,
        "num_features": num_features,
        "model_type": "xgboost",
        "task": "recommendation_scoring",
    }


def train_model(args) -> xgb.Booster:
    """Train XGBoost model.

    Args:
        args: Training arguments.

    Returns:
        Trained XGBoost booster.
    """
    print("Loading training data...")
    X_train, y_train = load_data(args.train)

    # Load validation data if available
    X_val, y_val = None, None
    if os.path.exists(args.validation):
        try:
            X_val, y_val = load_data(args.validation)
            print(f"Loaded {len(X_val)} validation samples")
        except ValueError:
            print("No validation data found, using train/test split")
            X_train, X_val, y_train, y_val = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42
            )

    # Create DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val) if X_val is not None else None

    # Set training parameters
    params = {
        "max_depth": args.max_depth,
        "eta": args.eta,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "objective": args.objective,
        "eval_metric": args.eval_metric,
        "tree_method": "hist",  # Fast histogram-based algorithm
        "predictor": "cpu_predictor",
    }

    # Training watchlist
    watchlist = [(dtrain, "train")]
    if dval is not None:
        watchlist.append((dval, "validation"))

    print("Training model...")
    print(f"Parameters: {params}")

    # Train model
    model = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=args.num_round,
        evals=watchlist,
        early_stopping_rounds=args.early_stopping_rounds,
        verbose_eval=10,
    )

    print(f"Best iteration: {model.best_iteration}")
    print(f"Best score: {model.best_score}")

    # Evaluate on validation set
    if dval is not None:
        y_pred = model.predict(dval)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        print(f"Validation RMSE: {rmse:.4f}")

        # Calculate NDCG if we have enough samples
        if len(y_val) >= 10:
            try:
                ndcg = ndcg_score([y_val], [y_pred], k=10)
                print(f"Validation NDCG@10: {ndcg:.4f}")
            except Exception as e:
                print(f"Could not calculate NDCG: {e}")

    return model


def save_model(model: xgb.Booster, model_dir: str, num_features: int) -> None:
    """Save model and metadata.

    Args:
        model: Trained XGBoost booster.
        model_dir: Directory to save model.
        num_features: Number of input features.
    """
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)

    # Save XGBoost model in native format
    model_file = model_path / "xgboost-model"
    model.save_model(str(model_file))
    print(f"Model saved to {model_file}")

    # Save feature metadata
    metadata = create_feature_metadata(num_features)
    metadata_file = model_path / "feature_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {metadata_file}")

    # Save model config for inference
    config = {
        "model_type": "xgboost",
        "model_file": "xgboost-model",
        "feature_metadata_file": "feature_metadata.json",
        "best_iteration": model.best_iteration,
        "best_score": float(model.best_score) if model.best_score else None,
    }
    config_file = model_path / "model_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {config_file}")


def main():
    """Main training entry point."""
    print("Starting training job...")

    args = parse_args()
    print(f"Arguments: {args}")

    # Train model
    model = train_model(args)

    # Get number of features from training data
    X_train, _ = load_data(args.train)
    num_features = X_train.shape[1]

    # Save model
    save_model(model, args.model_dir, num_features)

    print("Training complete!")


if __name__ == "__main__":
    main()
