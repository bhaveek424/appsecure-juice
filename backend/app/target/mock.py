from app.domain.actor_context import ActorContext
from app.target.types import AuthenticatedActor, ProbeCapture


class MockTargetClient:
    def __init__(
        self,
        *,
        boundary_violation: bool = True,
        checkout_manipulation_accepted: bool = False,
        review_ownership_violation: bool | None = None,
    ) -> None:
        self._boundary_violation = boundary_violation
        self._checkout_manipulation_accepted = checkout_manipulation_accepted
        self._review_ownership_violation = (
            review_ownership_violation
            if review_ownership_violation is not None
            else boundary_violation
        )
        self._users: dict[str, AuthenticatedActor] = {}
        self._reviews: dict[str, dict[str, str]] = {}

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

    def ensure_user_product_review(
        self,
        actor: AuthenticatedActor,
        product_id: int,
        message: str,
        author_email: str,
    ) -> str:
        review_id = f"review-{actor.user_id}-{product_id}"
        self._reviews[review_id] = {
            "author": author_email,
            "message": message,
            "product_id": str(product_id),
        }
        return review_id

    def probe_cross_actor_review_edit(
        self,
        actor: AuthenticatedActor,
        review_id: str,
        new_message: str,
    ) -> ProbeCapture:
        review = self._reviews.get(review_id, {"author": "user-a@review.local"})
        owner_email = review["author"]
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Content-Type": "application/json",
        }
        if self._review_ownership_violation:
            return ProbeCapture(
                scenario="Cross-actor review edit",
                actor_context=actor.actor_context,
                request_method="PATCH",
                request_path="/rest/products/reviews",
                request_headers=headers,
                response_status=200,
                response_headers={"Content-Type": "application/json"},
                response_body=(
                    '{"modified":1,"original":[{"_id":"'
                    + review_id
                    + '","author":"'
                    + owner_email
                    + '","message":"'
                    + new_message
                    + '"}]}'
                ),
            )

        return ProbeCapture(
            scenario="Cross-actor review edit",
            actor_context=actor.actor_context,
            request_method="PATCH",
            request_path="/rest/products/reviews",
            request_headers=headers,
            response_status=403,
            response_headers={"Content-Type": "application/json"},
            response_body='{"error":"Forbidden"}',
        )
