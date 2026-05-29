import json
import re
from typing import Any
from urllib.parse import quote

from app.domain.actor_context import ActorContext
from app.target.types import ProbeCapture

_COUPON_PATH_PATTERN = re.compile(
    r"^/rest/basket/(?P<basket_id>\d+)/coupon/(?P<coupon>.+)$"
)
_INVALID_PROBE_COUPON = "appsecure-invalid-coupon-probe"


def invalid_coupon_probe_code() -> str:
    return _INVALID_PROBE_COUPON


def coupon_apply_path(basket_id: int, coupon_code: str) -> str:
    return f"/rest/basket/{basket_id}/coupon/{quote(coupon_code, safe='')}"


def parse_coupon_apply_response(probe: ProbeCapture) -> dict[str, Any] | None:
    if probe.response_status != 200:
        return None
    try:
        payload = json.loads(probe.response_body)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def discount_from_apply_response(probe: ProbeCapture) -> int | None:
    payload = parse_coupon_apply_response(probe)
    if payload is None:
        return None
    discount = payload.get("discount")
    if isinstance(discount, bool):
        return None
    try:
        return int(discount)
    except (TypeError, ValueError):
        return None


def basket_id_from_coupon_path(path: str) -> int | None:
    match = _COUPON_PATH_PATTERN.match(path)
    if match is None:
        return None
    return int(match.group("basket_id"))


def coupon_reuse_violation_detected(
    first_probe: ProbeCapture,
    second_probe: ProbeCapture,
) -> bool:
    first_discount = discount_from_apply_response(first_probe)
    second_discount = discount_from_apply_response(second_probe)
    if first_discount is None or second_discount is None:
        return False
    if first_discount <= 0:
        return False
    return second_discount > first_discount


def cross_actor_coupon_violation_detected(
    probe: ProbeCapture,
    *,
    actor_basket_id: int,
    other_basket_id: int,
) -> bool:
    if probe.actor_context != ActorContext.USER_B:
        return False
    if actor_basket_id == other_basket_id:
        return False

    requested_basket_id = basket_id_from_coupon_path(probe.request_path)
    if requested_basket_id != other_basket_id:
        return False

    discount = discount_from_apply_response(probe)
    return discount is not None and discount > 0


def invalid_coupon_accepted_detected(probe: ProbeCapture) -> bool:
    if invalid_coupon_probe_code() not in probe.request_path:
        return False
    discount = discount_from_apply_response(probe)
    return discount is not None and discount > 0
