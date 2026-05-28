from app.skills.basket_boundary import (
    cross_actor_basket_access_detected,
    requested_basket_id_from_path,
)
from app.domain.actor_context import ActorContext
from app.target.types import ProbeCapture


def test_requested_basket_id_from_path():
    assert requested_basket_id_from_path("/rest/basket/42") == 42
    assert requested_basket_id_from_path("/rest/basket/42/") == 42
    assert requested_basket_id_from_path("/rest/user/whoami") is None


def test_cross_actor_basket_access_detected_for_juice_shop_payload():
    probe = ProbeCapture(
        scenario="Cross-actor basket read",
        actor_context=ActorContext.USER_B,
        request_method="GET",
        request_path="/rest/basket/7",
        request_headers={},
        response_status=200,
        response_headers={},
        response_body='{"id":7,"UserId":2,"Products":[{"id":1,"name":"Apple Juice"}]}',
    )

    assert cross_actor_basket_access_detected(probe) is True
