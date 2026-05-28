import json
from typing import Any

from app.domain.actor_context import ActorContext
from app.target.types import ProbeCapture

_BASKET_ITEMS_PATH = "/api/BasketItems/"


def extract_quantity_from_payload(payload: dict[str, Any]) -> int | None:
    if "quantity" in payload:
        try:
            return int(payload["quantity"])
        except (TypeError, ValueError):
            return None

    data = payload.get("data")
    if isinstance(data, dict) and "quantity" in data:
        try:
            return int(data["quantity"])
        except (TypeError, ValueError):
            return None

    return None


def parse_basket_item_response_body(response_body: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def negative_basket_quantity_manipulation_detected(probe: ProbeCapture) -> bool:
    if probe.request_path.rstrip("/") != _BASKET_ITEMS_PATH.rstrip("/"):
        return False

    if probe.request_method.upper() != "POST":
        return False

    if probe.actor_context != ActorContext.USER_A:
        return False

    if probe.response_status not in {200, 201}:
        return False

    payload = parse_basket_item_response_body(probe.response_body)
    if payload is None:
        return False

    quantity = extract_quantity_from_payload(payload)
    return quantity is not None and quantity < 0
