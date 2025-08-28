from __future__ import annotations
import logging
from flask import Flask, jsonify
from pydantic import ValidationError

def create_app() -> Flask:
    app = Flask(__name__)

    # Blueprints
    from hunter.api.routes.candidates import bp as candidates_bp
    app.register_blueprint(candidates_bp, url_prefix="/v1")

    # Error handling for Pydantic
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return jsonify({"error": "validation_error", "details": err.errors()}), 400

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "not_found"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        logging.exception("Unhandled error")
        return jsonify({"error": "internal_server_error"}), 500

    return app