from app.domain.actor_context import ActorContext
from app.target.types import AuthenticatedActor, ProbeCapture


class MockTargetClient:
    def __init__(
        self,
        *,
        boundary_violation: bool = True,
        checkout_manipulation_accepted: bool = False,
    ) -> None:
        self._boundary_violation = boundary_violation
        self._checkout_manipulation_accepted = checkout_manipulation_accepted
        self._users: dict[str, AuthenticatedActor] = {}

    def register_user(self, email: str, password: str) -> None:
        _ = password

    def login(self, email: str, password: str, actor_context: ActorContext) -> AuthenticatedActor:
        _ = password
        if email in self._users:
            return self._users[email]

        user_id = 1 if actor_context == ActorContext.USER_A else 2
        basket_id = 10 if actor_context == ActorContext.USER_A else 20
        actor = AuthenticatedActor(
            actor_context=actor_context,
            user_id=user_id,
            basket_id=basket_id,
            token=f"token-{actor_context.value.replace(' ', '-').lower()}",
        )
        self._users[email] = actor
        return actor

    def probe_cross_actor_basket_access(
        self,
        actor: AuthenticatedActor,
        other_basket_id: int,
    ) -> ProbeCapture:
        if self._boundary_violation:
            return ProbeCapture(
                scenario="Cross-actor basket read",
                actor_context=actor.actor_context,
                request_method="GET",
                request_path=f"/rest/basket/{other_basket_id}",
                request_headers={
                    "Authorization": f"Bearer {actor.token}",
                    "Accept": "application/json",
                },
                response_status=200,
                response_headers={"Content-Type": "application/json"},
                response_body=(
                    '{"id":10,"UserId":1,"Products":[{"id":1,"name":"Apple Juice"}]}'
                ),
            )

        return ProbeCapture(
            scenario="Cross-actor basket read",
            actor_context=actor.actor_context,
            request_method="GET",
            request_path=f"/rest/basket/{other_basket_id}",
            request_headers={
                "Authorization": f"Bearer {actor.token}",
                "Accept": "application/json",
            },
            response_status=403,
            response_headers={"Content-Type": "application/json"},
            response_body='{"error":"Forbidden"}',
        )

    def probe_negative_basket_quantity(
        self,
        actor: AuthenticatedActor,
    ) -> ProbeCapture:
        path = "/api/BasketItems/"
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._checkout_manipulation_accepted:
            return ProbeCapture(
                scenario="Negative basket quantity",
                actor_context=actor.actor_context,
                request_method="POST",
                request_path=path,
                request_headers=headers,
                response_status=201,
                response_headers={"Content-Type": "application/json"},
                response_body=(
                    '{"ProductId":1,"BasketId":10,"quantity":-1,'
                    '"id":99}'
                ),
            )

        return ProbeCapture(
            scenario="Negative basket quantity",
            actor_context=actor.actor_context,
            request_method="POST",
            request_path=path,
            request_headers=headers,
            response_status=400,
            response_headers={"Content-Type": "application/json"},
            response_body='{"error":"Invalid quantity"}',
        )
