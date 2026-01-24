"""Inference script for SageMaker real-time endpoint.

This script handles model loading and prediction for the content
recommendation model, optimized for sub-100ms latency.

SageMaker will call the following functions:
- model_fn: Load model from disk
- input_fn: Deserialize request data
- predict_fn: Run inference
- output_fn: Serialize response
"""

import json
import os
import time
from typing import Any

import numpy as np
import xgboost as xgb


def model_fn(model_dir: str) -> dict[str, Any]:
    """Load model and metadata from disk.

    Called once when the container starts.

    Args:
        model_dir: Directory containing model artifacts.

    Returns:
        Dictionary containing model and metadata.
    """
    print(f"Loading model from {model_dir}")
    start_time = time.perf_counter()

    # Load XGBoost model
    model_path = os.path.join(model_dir, "xgboost-model")
    model = xgb.Booster()
    model.load_model(model_path)

    # Load feature metadata
    metadata_path = os.path.join(model_dir, "feature_metadata.json")
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    # Load model config
    config_path = os.path.join(model_dir, "model_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    load_time = (time.perf_counter() - start_time) * 1000
    print(f"Model loaded in {load_time:.2f}ms")

    return {
        "model": model,
        "metadata": metadata,
        "config": config,
    }


def input_fn(request_body: str, content_type: str = "application/json") -> dict[str, Any]:
    """Deserialize and validate request data.

    Args:
        request_body: Raw request body.
        content_type: Content type of request.

    Returns:
        Parsed request data.

    Raises:
        ValueError: If content type is not supported.
    """
    if content_type == "application/json":
        data = json.loads(request_body)

        # Validate required fields
        if "features" not in data:
            raise ValueError("Request must contain 'features' field")

        return data

    elif content_type == "text/csv":
        # Parse CSV format: comma-separated feature values
        lines = request_body.strip().split("\n")
        features_list = []
        for line in lines:
            values = [float(v.strip()) for v in line.split(",")]
            features_list.append(values)

        return {"features": features_list, "format": "batch"}

    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data: dict[str, Any], model_dict: dict[str, Any]) -> dict[str, Any]:
    """Run model inference.

    Args:
        input_data: Parsed request data.
        model_dict: Model and metadata from model_fn.

    Returns:
        Prediction results.
    """
    start_time = time.perf_counter()

    model = model_dict["model"]
    metadata = model_dict["metadata"]
    num_features = metadata["num_features"]

    # Extract features
    features = input_data.get("features")

    # Handle different input formats
    if isinstance(features, dict):
        # Single request with named features
        feature_values = _extract_feature_values(features, metadata["feature_names"])
        X = np.array([feature_values])
    elif isinstance(features, list):
        if all(isinstance(f, dict) for f in features):
            # Batch request with named features
            X = np.array([
                _extract_feature_values(f, metadata["feature_names"])
                for f in features
            ])
        else:
            # Batch request with raw values
            X = np.array(features)
            if X.ndim == 1:
                X = X.reshape(1, -1)
    else:
        raise ValueError("Invalid features format")

    # Validate feature count
    if X.shape[1] != num_features:
        raise ValueError(
            f"Expected {num_features} features, got {X.shape[1]}"
        )

    # Create DMatrix and predict
    dmatrix = xgb.DMatrix(X)
    predictions = model.predict(dmatrix)

    inference_time = (time.perf_counter() - start_time) * 1000

    return {
        "predictions": predictions.tolist(),
        "inference_time_ms": inference_time,
        "batch_size": len(predictions),
        "request_id": input_data.get("request_id"),
        "user_id": input_data.get("user_id"),
    }


def output_fn(prediction: dict[str, Any], accept: str = "application/json") -> tuple[str, str]:
    """Serialize prediction response.

    Args:
        prediction: Prediction results from predict_fn.
        accept: Accepted content type.

    Returns:
        Tuple of (serialized response, content type).
    """
    if accept == "application/json":
        # Format predictions for recommendation response
        predictions = prediction.get("predictions", [])

        response = {
            "predictions": [
                {
                    "score": float(score),
                    "rank": idx + 1,
                }
                for idx, score in enumerate(
                    sorted(enumerate(predictions), key=lambda x: x[1], reverse=True)
                )
            ][:20],  # Return top 20 recommendations
            "metadata": {
                "inference_time_ms": prediction.get("inference_time_ms", 0),
                "batch_size": prediction.get("batch_size", 0),
                "request_id": prediction.get("request_id"),
                "user_id": prediction.get("user_id"),
            },
        }

        return json.dumps(response), accept

    elif accept == "text/csv":
        predictions = prediction.get("predictions", [])
        csv_output = "\n".join(str(p) for p in predictions)
        return csv_output, accept

    else:
        raise ValueError(f"Unsupported accept type: {accept}")


def _extract_feature_values(
    features: dict[str, Any],
    feature_names: list[str],
) -> list[float]:
    """Extract feature values in correct order.

    Args:
        features: Dictionary of feature name to value.
        feature_names: Expected feature names in order.

    Returns:
        List of feature values.
    """
    values = []
    for name in feature_names:
        if name in features:
            values.append(float(features[name]))
        else:
            # Use default value for missing features
            values.append(0.0)
    return values


# For local testing
if __name__ == "__main__":
    # Test with sample data
    import tempfile

    # Create mock model
    print("Creating mock model for testing...")

    # Generate sample training data
    np.random.seed(42)
    X_sample = np.random.randn(100, 16)
    y_sample = np.random.randn(100)

    dtrain = xgb.DMatrix(X_sample, label=y_sample)
    params = {"max_depth": 3, "eta": 0.1, "objective": "reg:squarederror"}
    model = xgb.train(params, dtrain, num_boost_round=10)

    # Save to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        model.save_model(os.path.join(tmpdir, "xgboost-model"))

        metadata = {
            "feature_names": [f"feature_{i}" for i in range(16)],
            "num_features": 16,
        }
        with open(os.path.join(tmpdir, "feature_metadata.json"), "w") as f:
            json.dump(metadata, f)

        config = {"model_type": "xgboost"}
        with open(os.path.join(tmpdir, "model_config.json"), "w") as f:
            json.dump(config, f)

        # Test inference
        model_dict = model_fn(tmpdir)

        request = {
            "user_id": "user123",
            "request_id": "req123",
            "features": {f"feature_{i}": np.random.randn() for i in range(16)},
        }

        input_data = input_fn(json.dumps(request))
        prediction = predict_fn(input_data, model_dict)
        response, _ = output_fn(prediction)

        print("Test response:")
        print(json.dumps(json.loads(response), indent=2))
