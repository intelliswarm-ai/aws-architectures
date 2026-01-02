"""Flask application for EC2 health checks and monitoring."""

import threading
from datetime import datetime

from flask import Flask, jsonify

from ..common.config import settings
from .worker import get_worker

app = Flask(__name__)

# Start time for uptime calculation
START_TIME = datetime.utcnow()


@app.route("/health")
def health_check():
    """Health check endpoint for ALB/ASG.

    Returns 200 if the worker is running and healthy.
    """
    worker = get_worker()

    if not worker.running:
        return jsonify({
            "status": "unhealthy",
            "reason": "Worker not running",
        }), 503

    return jsonify({
        "status": "healthy",
        "processor_id": worker.transaction_service.processor_id,
        "uptime_seconds": (datetime.utcnow() - START_TIME).total_seconds(),
    })


@app.route("/stats")
def get_stats():
    """Get processing statistics."""
    worker = get_worker()
    stats = worker.get_stats()

    return jsonify({
        "processor_id": worker.transaction_service.processor_id,
        "running": worker.running,
        "num_threads": worker.num_threads,
        "statistics": stats,
        "uptime_seconds": (datetime.utcnow() - START_TIME).total_seconds(),
    })


@app.route("/ready")
def readiness_check():
    """Readiness check for Kubernetes-style deployments.

    Returns 200 when the worker is ready to process messages.
    """
    worker = get_worker()

    if not worker.running:
        return jsonify({
            "ready": False,
            "reason": "Worker not running",
        }), 503

    return jsonify({
        "ready": True,
        "processor_id": worker.transaction_service.processor_id,
    })


def create_app():
    """Create and configure the Flask application."""
    return app


def start_with_worker():
    """Start Flask app with the transaction worker."""
    # Start the worker in a background thread
    worker = get_worker()
    worker_thread = threading.Thread(
        target=worker.start,
        name="worker-main",
    )
    worker_thread.daemon = True
    worker_thread.start()

    return app


if __name__ == "__main__":
    application = start_with_worker()
    application.run(host="0.0.0.0", port=8080)
