import json
import re
from typing import Any

from app.domain.actor_context import ActorContext
from app.target.types import ProbeCapture

_BASKET_PATH_PATTERN = re.compile(r"^/rest/basket/(?P<id>\d+)(?:/|$)")


def requested_basket_id_from_path(path: str) -> int | None:
    match = _BASKET_PATH_PATTERN.match(path)
    if match is None:
        return None
    return int(match.group("id"))


def parse_basket_response_body(response_body: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def basket_payload_matches_juice_shop_shape(payload: dict[str, Any]) -> bool:
    basket_id = payload.get("id")
    if basket_id is None:
        return False

    if "Products" in payload:
        return isinstance(payload["Products"], list)

    if "items" in payload:
        return isinstance(payload["items"], list)

    return "UserId" in payload


def cross_actor_basket_access_detected(probe: ProbeCapture) -> bool:
    if probe.response_status != 200 or probe.actor_context != ActorContext.USER_B:
        return False

    requested_id = requested_basket_id_from_path(probe.request_path)
    if requested_id is None:
        return False

    payload = parse_basket_response_body(probe.response_body)
    if payload is None:
        return False

    try:
        returned_id = int(payload["id"])
    except (KeyError, TypeError, ValueError):
        return False

    if returned_id != requested_id:
        return False

    return basket_payload_matches_juice_shop_shape(payload)
