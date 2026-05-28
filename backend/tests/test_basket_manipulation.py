from app.skills.basket_manipulation import (
    extract_quantity_from_payload,
    negative_basket_quantity_manipulation_detected,
)
from app.domain.actor_context import ActorContext
from app.target.types import ProbeCapture


def test_extract_quantity_from_payload_supports_nested_data():
    assert extract_quantity_from_payload({"data": {"quantity": -2}}) == -2


def test_negative_basket_quantity_manipulation_detected_for_juice_shop_shape():
    probe = ProbeCapture(
        scenario="Negative basket quantity",
        actor_context=ActorContext.USER_A,
        request_method="POST",
        request_path="/api/BasketItems/",
        request_headers={},
        response_status=201,
        response_headers={},
        response_body='{"data":{"ProductId":1,"quantity":-1}}',
    )

    assert negative_basket_quantity_manipulation_detected(probe) is True
