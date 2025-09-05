from __future__ import annotations
from flask import Blueprint, request, jsonify

from hunter.services.candidates import (
    add_candidate_from_resume, get_candidate_full, query_candidates
)

from hunter.utils.helpers import jsonify_safe

bp = Blueprint("candidates", __name__)

@bp.post("/candidates/from_resume")
def create_candidate_from_resume():
    """Ingest a parsed resume JSON and create/link candidate features.
    Body: the parsed resume dict as described by the service.
    Returns: summary with candidate_uid and counts of linked entities.
    """
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Body must be a JSON object"}), 400
    try:
        summary = add_candidate_from_resume(payload)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    return jsonify(summary), 201


@bp.get("/candidates/<string:uid>/full")
def read_candidate_full(uid: str):
    """Fetch a candidate and all linked features by uid."""
    # print(uid)
    try:
        data = get_candidate_full(uid)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    
    # print(jsonify_safe(data))
    return jsonify(jsonify_safe(data)), 200


@bp.post("/candidates/search")
def search_candidates():
    """Filter candidates by features without scoring.
    Body mirrors the must_have structure from /candidates/match with skip/limit and include_fields.
    """
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Body must be a JSON object"}), 400
    try:
        resp = query_candidates(payload)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    return jsonify(resp), 200
    
    
    
