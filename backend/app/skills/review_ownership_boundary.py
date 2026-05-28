import json
from typing import Any

from app.domain.actor_context import ActorContext
from app.target.types import ProbeCapture

_REVIEW_EDIT_PATH = "/rest/products/reviews"


def parse_review_edit_response_body(response_body: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def cross_actor_review_ownership_bypass_detected(
    probe: ProbeCapture, *, owner_email: str
) -> bool:
    if probe.actor_context != ActorContext.USER_B:
        return False
    if probe.request_method != "PATCH":
        return False
    if probe.request_path.rstrip("/") != _REVIEW_EDIT_PATH:
        return False
    if probe.response_status != 200:
        return False

    payload = parse_review_edit_response_body(probe.response_body)
    if payload is None:
        return False

    modified = payload.get("modified")
    if not isinstance(modified, int) or modified < 1:
        return False

    original = payload.get("original")
    if not isinstance(original, list) or not original:
        return False

    first = original[0]
    if not isinstance(first, dict):
        return False

    author = first.get("author")
    if not isinstance(author, str):
        return False

    return author.lower() == owner_email.lower()
