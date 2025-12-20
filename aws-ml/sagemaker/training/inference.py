"""
SageMaker Inference Script for Document Classification.

This script provides the inference logic for the trained XGBoost model.
It's used by SageMaker hosting to serve predictions.
"""

import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import xgboost as xgb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model and encoder (loaded once)
model = None
label_encoder = None
metadata = None


def model_fn(model_dir: str):
    """
    Load model from the model_dir.

    Called once when the model is loaded.
    """
    global model, label_encoder, metadata

    model_dir = Path(model_dir)
    logger.info(f"Loading model from {model_dir}")

    # Load XGBoost model
    model_path = model_dir / "xgboost-model"
    model = xgb.Booster()
    model.load_model(str(model_path))
    logger.info("Loaded XGBoost model")

    # Load label encoder
    encoder_path = model_dir / "label_encoder.joblib"
    label_encoder = joblib.load(encoder_path)
    logger.info(f"Loaded label encoder with classes: {label_encoder.classes_}")

    # Load metadata
    metadata_path = model_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
        logger.info(f"Loaded metadata: {metadata}")

    return model


def input_fn(request_body: str, request_content_type: str):
    """
    Deserialize input data.

    Supports JSON format with feature dictionary or array.
    """
    logger.info(f"Content type: {request_content_type}")

    if request_content_type == "application/json":
        data = json.loads(request_body)

        # Handle single prediction or batch
        if isinstance(data, dict):
            # Single prediction
            features = extract_features(data)
            return np.array([features], dtype=np.float32)
        elif isinstance(data, list):
            # Batch prediction
            features = [extract_features(item) for item in data]
            return np.array(features, dtype=np.float32)
        else:
            raise ValueError(f"Unexpected data format: {type(data)}")

    elif request_content_type == "text/csv":
        # CSV format: comma-separated values
        lines = request_body.strip().split("\n")
        features = []
        for line in lines:
            values = [float(v) for v in line.split(",")]
            features.append(values)
        return np.array(features, dtype=np.float32)

    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")


def extract_features(data: dict) -> list:
    """Extract features from input dictionary."""
    # Define expected features in order
    feature_names = [
        "word_count",
        "page_count",
        "extraction_confidence",
        "entity_count",
        "key_phrase_count",
        "has_tables",
        "has_forms",
        "has_pii",
        "is_moderation_flagged",
    ]

    features = []
    for name in feature_names:
        value = data.get(name, 0)
        # Convert boolean to int
        if isinstance(value, bool):
            value = int(value)
        features.append(float(value))

    return features


def predict_fn(input_data: np.ndarray, model):
    """
    Make predictions using the model.
    """
    global label_encoder

    logger.info(f"Input shape: {input_data.shape}")

    # Create DMatrix
    dmatrix = xgb.DMatrix(input_data)

    # Get predictions
    predictions = model.predict(dmatrix)

    # Get class probabilities if available
    try:
        probabilities = model.predict(dmatrix, output_margin=False)
    except Exception:
        probabilities = None

    # Convert to class labels
    predicted_classes = label_encoder.inverse_transform(predictions.astype(int))

    return {
        "predictions": predictions.tolist(),
        "classes": predicted_classes.tolist(),
        "probabilities": probabilities.tolist() if probabilities is not None else None,
    }


def output_fn(prediction: dict, response_content_type: str):
    """
    Serialize predictions to response.
    """
    if response_content_type == "application/json":
        # Format response
        if len(prediction["classes"]) == 1:
            # Single prediction
            response = {
                "class": prediction["classes"][0],
                "confidence": float(max(prediction["probabilities"][0])) if prediction["probabilities"] else 0.0,
                "probabilities": {
                    class_name: float(prob)
                    for class_name, prob in zip(
                        label_encoder.classes_,
                        prediction["probabilities"][0] if prediction["probabilities"] else [],
                    )
                },
            }
        else:
            # Batch prediction
            response = {
                "predictions": [
                    {
                        "class": cls,
                        "confidence": float(max(probs)) if prediction["probabilities"] else 0.0,
                        "probabilities": {
                            class_name: float(prob)
                            for class_name, prob in zip(
                                label_encoder.classes_,
                                probs if prediction["probabilities"] else [],
                            )
                        },
                    }
                    for cls, probs in zip(
                        prediction["classes"],
                        prediction["probabilities"] or [[] for _ in prediction["classes"]],
                    )
                ]
            }

        return json.dumps(response)

    elif response_content_type == "text/csv":
        # Return class predictions as CSV
        return "\n".join(prediction["classes"])

    else:
        raise ValueError(f"Unsupported content type: {response_content_type}")


# For local testing
if __name__ == "__main__":
    # Test with sample data
    test_input = {
        "word_count": 1500,
        "page_count": 3,
        "extraction_confidence": 0.95,
        "entity_count": 25,
        "key_phrase_count": 10,
        "has_tables": True,
        "has_forms": False,
        "has_pii": False,
        "is_moderation_flagged": False,
    }

    print("Test input:", json.dumps(test_input, indent=2))

    # Load model from local path
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    if Path(model_dir).exists():
        model = model_fn(model_dir)
        features = input_fn(json.dumps(test_input), "application/json")
        prediction = predict_fn(features, model)
        output = output_fn(prediction, "application/json")
        print("Prediction:", output)
    else:
        print(f"Model directory not found: {model_dir}")
