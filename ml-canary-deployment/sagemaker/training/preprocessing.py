"""Data preprocessing for content recommendation model.

This script preprocesses viewing history and content metadata
to create training features for the recommendation model.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args():
    """Parse preprocessing arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--input-data", type=str, required=True)
    parser.add_argument("--output-data", type=str, required=True)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--lookback-days", type=int, default=30)

    return parser.parse_args()


def load_viewing_history(data_path: str) -> pd.DataFrame:
    """Load user viewing history data.

    Args:
        data_path: Path to viewing history CSV.

    Returns:
        DataFrame with viewing history.
    """
    df = pd.read_csv(data_path)

    # Expected columns: user_id, content_id, watch_time, completion_rate, timestamp
    required_columns = ["user_id", "content_id", "watch_time", "completion_rate", "timestamp"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


def load_content_metadata(data_path: str) -> pd.DataFrame:
    """Load content metadata.

    Args:
        data_path: Path to content metadata CSV.

    Returns:
        DataFrame with content metadata.
    """
    df = pd.read_csv(data_path)

    # Expected columns: content_id, title, genre, duration_minutes, release_date, rating
    return df


def compute_user_features(
    viewing_history: pd.DataFrame,
    reference_date: datetime,
    lookback_days: int = 30,
) -> pd.DataFrame:
    """Compute user-level features.

    Args:
        viewing_history: User viewing history.
        reference_date: Reference date for feature computation.
        lookback_days: Number of days to look back.

    Returns:
        DataFrame with user features.
    """
    cutoff_date = reference_date - timedelta(days=lookback_days)

    # Filter to lookback window
    recent = viewing_history[viewing_history["timestamp"] >= cutoff_date]

    user_features = recent.groupby("user_id").agg({
        "watch_time": ["sum", "mean", "count"],
        "completion_rate": "mean",
        "content_id": "nunique",
        "timestamp": ["min", "max"],
    })

    user_features.columns = [
        "total_watch_time",
        "avg_watch_time",
        "num_sessions",
        "avg_completion_rate",
        "num_unique_content",
        "first_activity",
        "last_activity",
    ]

    user_features = user_features.reset_index()

    # Calculate recency
    user_features["recency_days"] = (
        reference_date - user_features["last_activity"]
    ).dt.days

    # Calculate session frequency
    user_features["sessions_per_day"] = (
        user_features["num_sessions"] / lookback_days
    )

    # Calculate genre diversity (entropy-based)
    genre_counts = recent.groupby(["user_id", "content_id"]).size().reset_index(name="count")
    genre_diversity = genre_counts.groupby("user_id")["content_id"].apply(
        lambda x: len(x) / len(x.index) if len(x.index) > 0 else 0
    )
    user_features = user_features.merge(
        genre_diversity.reset_index().rename(columns={"content_id": "genre_diversity"}),
        on="user_id",
        how="left",
    )

    return user_features


def compute_content_features(
    content_metadata: pd.DataFrame,
    viewing_history: pd.DataFrame,
    reference_date: datetime,
) -> pd.DataFrame:
    """Compute content-level features.

    Args:
        content_metadata: Content metadata.
        viewing_history: Viewing history for popularity computation.
        reference_date: Reference date.

    Returns:
        DataFrame with content features.
    """
    # Basic content features
    content_features = content_metadata.copy()

    # Encode categorical features
    if "genre" in content_features.columns:
        genre_dummies = pd.get_dummies(content_features["genre"], prefix="genre")
        content_features = pd.concat([content_features, genre_dummies], axis=1)
        # Create single encoded value for model
        content_features["genre_encoded"] = pd.factorize(content_features["genre"])[0]

    if "rating" in content_features.columns:
        content_features["rating_encoded"] = pd.factorize(content_features["rating"])[0]

    # Calculate popularity from viewing history
    content_popularity = viewing_history.groupby("content_id").agg({
        "user_id": "nunique",
        "watch_time": "sum",
        "completion_rate": "mean",
    }).reset_index()

    content_popularity.columns = [
        "content_id",
        "unique_viewers",
        "total_watch_time",
        "avg_completion_rate",
    ]

    # Normalize popularity score
    content_popularity["popularity_score"] = (
        content_popularity["unique_viewers"] /
        content_popularity["unique_viewers"].max()
    )

    content_features = content_features.merge(
        content_popularity, on="content_id", how="left"
    )

    # Fill missing popularity with 0
    content_features["popularity_score"] = content_features["popularity_score"].fillna(0)
    content_features["avg_completion_rate"] = content_features["avg_completion_rate"].fillna(0.5)

    # Calculate release recency
    if "release_date" in content_features.columns:
        content_features["release_date"] = pd.to_datetime(content_features["release_date"])
        content_features["release_recency_days"] = (
            reference_date - content_features["release_date"]
        ).dt.days

    return content_features


def compute_interaction_features(
    user_features: pd.DataFrame,
    content_features: pd.DataFrame,
    viewing_history: pd.DataFrame,
) -> pd.DataFrame:
    """Compute user-content interaction features.

    Args:
        user_features: User features.
        content_features: Content features.
        viewing_history: Viewing history.

    Returns:
        DataFrame with interaction features.
    """
    # Create all user-content pairs for training
    interactions = viewing_history[["user_id", "content_id", "completion_rate"]].copy()

    # Merge with user features
    interactions = interactions.merge(
        user_features[["user_id", "total_watch_time", "avg_completion_rate", "genre_diversity", "recency_days"]],
        on="user_id",
        how="left",
        suffixes=("", "_user"),
    )

    # Merge with content features
    content_cols = ["content_id", "popularity_score", "duration_minutes", "genre_encoded", "rating_encoded"]
    available_cols = [c for c in content_cols if c in content_features.columns]
    interactions = interactions.merge(
        content_features[available_cols],
        on="content_id",
        how="left",
    )

    # Create interaction features
    # User-genre affinity would require genre information in viewing history
    interactions["user_genre_affinity"] = np.random.rand(len(interactions))  # Placeholder

    return interactions


def create_training_samples(
    interactions: pd.DataFrame,
    train_ratio: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create training and validation samples.

    Args:
        interactions: Interaction features.
        train_ratio: Ratio for training split.

    Returns:
        Tuple of (training, validation) DataFrames.
    """
    # Shuffle data
    interactions = interactions.sample(frac=1, random_state=42).reset_index(drop=True)

    # Split by user to prevent data leakage
    users = interactions["user_id"].unique()
    np.random.shuffle(users)

    train_users = set(users[: int(len(users) * train_ratio)])

    train_data = interactions[interactions["user_id"].isin(train_users)]
    val_data = interactions[~interactions["user_id"].isin(train_users)]

    return train_data, val_data


def prepare_features_for_training(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare features for model training.

    Args:
        data: Interaction data.

    Returns:
        Tuple of (features, labels).
    """
    # Define feature columns
    feature_columns = [
        "total_watch_time",
        "avg_completion_rate_user",
        "genre_diversity",
        "recency_days",
        "popularity_score",
        "user_genre_affinity",
    ]

    # Add optional features if available
    optional_features = ["duration_minutes", "genre_encoded", "rating_encoded"]
    for col in optional_features:
        if col in data.columns:
            feature_columns.append(col)

    # Filter to available columns
    available_features = [c for c in feature_columns if c in data.columns]

    X = data[available_features].fillna(0)
    y = data["completion_rate"]  # Use completion rate as engagement target

    return X, y


def main():
    """Main preprocessing entry point."""
    args = parse_args()

    print(f"Loading data from {args.input_data}")
    input_path = Path(args.input_data)

    # Load data
    viewing_history = load_viewing_history(str(input_path / "viewing_history.csv"))
    content_metadata = load_content_metadata(str(input_path / "content_metadata.csv"))

    reference_date = viewing_history["timestamp"].max()
    print(f"Reference date: {reference_date}")

    # Compute features
    print("Computing user features...")
    user_features = compute_user_features(
        viewing_history, reference_date, args.lookback_days
    )

    print("Computing content features...")
    content_features = compute_content_features(
        content_metadata, viewing_history, reference_date
    )

    print("Computing interaction features...")
    interactions = compute_interaction_features(
        user_features, content_features, viewing_history
    )

    # Create train/validation splits
    print("Creating training samples...")
    train_data, val_data = create_training_samples(interactions, args.train_ratio)

    # Prepare features
    X_train, y_train = prepare_features_for_training(train_data)
    X_val, y_val = prepare_features_for_training(val_data)

    # Add labels to features
    train_df = X_train.copy()
    train_df["target"] = y_train

    val_df = X_val.copy()
    val_df["target"] = y_val

    # Save outputs
    output_path = Path(args.output_data)
    output_path.mkdir(parents=True, exist_ok=True)

    train_path = output_path / "train"
    val_path = output_path / "validation"
    train_path.mkdir(exist_ok=True)
    val_path.mkdir(exist_ok=True)

    train_df.to_csv(train_path / "train.csv", index=False)
    val_df.to_csv(val_path / "validation.csv", index=False)

    print(f"Training samples: {len(train_df)}")
    print(f"Validation samples: {len(val_df)}")
    print(f"Features: {list(X_train.columns)}")
    print(f"Output saved to {args.output_data}")


if __name__ == "__main__":
    main()
