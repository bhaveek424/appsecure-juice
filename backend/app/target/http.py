import httpx

from app.config import get_settings
from app.domain.actor_context import ActorContext
from app.skills.coupon_logic import coupon_apply_path
from app.target.types import AuthenticatedActor, ProbeCapture


class HttpTargetClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.target_application_url.rstrip("/")

    def register_user(self, email: str, password: str) -> None:
        payload = {
            "email": email,
            "password": password,
            "passwordRepeat": password,
            "securityQuestion": {"id": 1, "answer": "review"},
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{self._base_url}/api/Users/", json=payload)
            if response.status_code not in {201, 400}:
                response.raise_for_status()

    def login(
        self, email: str, password: str, actor_context: ActorContext
    ) -> AuthenticatedActor:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self._base_url}/rest/user/login",
                json={"email": email, "password": password},
            )
            response.raise_for_status()
            body = response.json()
            token = body["authentication"]["token"]
            bid = int(body["authentication"]["bid"])

            whoami = client.get(
                f"{self._base_url}/rest/user/whoami",
                headers={"Authorization": f"Bearer {token}"},
            )
            whoami.raise_for_status()
            user_id = int(whoami.json()["user"]["id"])

        return AuthenticatedActor(
            actor_context=actor_context,
            user_id=user_id,
            basket_id=bid,
            token=token,
        )

    def probe_cross_actor_basket_access(
        self,
        actor: AuthenticatedActor,
        other_basket_id: int,
    ) -> ProbeCapture:
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Accept": "application/json",
        }
        path = f"/rest/basket/{other_basket_id}"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{self._base_url}{path}", headers=headers)

        return ProbeCapture(
            scenario="Cross-actor basket read",
            actor_context=actor.actor_context,
            request_method="GET",
            request_path=path,
            request_headers=headers,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.text[:2000],
        )

    def probe_negative_basket_quantity(
        self,
        actor: AuthenticatedActor,
    ) -> ProbeCapture:
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        path = "/api/BasketItems/"
        payload = {
            "ProductId": 1,
            "quantity": -1,
            "BasketId": str(actor.basket_id),
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self._base_url}{path}",
                headers=headers,
                json=payload,
            )

        return ProbeCapture(
            scenario="Negative basket quantity",
            actor_context=actor.actor_context,
            request_method="POST",
            request_path=path,
            request_headers=headers,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.text[:2000],
        )

    def ensure_user_product_review(
        self,
        actor: AuthenticatedActor,
        product_id: int,
        message: str,
        author_email: str,
    ) -> str:
        path = f"/rest/products/{product_id}/reviews"
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=30.0) as client:
            existing = client.get(f"{self._base_url}{path}", headers=headers)
            existing.raise_for_status()
            body = existing.json()
            reviews = body.get("data", body) if isinstance(body, dict) else body
            if isinstance(reviews, list):
                for review in reviews:
                    if not isinstance(review, dict):
                        continue
                    if review.get("author") == author_email:
                        review_id = review.get("_id") or review.get("id")
                        if review_id is not None:
                            return str(review_id)

            create = client.put(
                f"{self._base_url}{path}",
                headers=headers,
                json={"message": message, "author": author_email},
            )
            if create.status_code not in {200, 201}:
                create.raise_for_status()

            refreshed = client.get(f"{self._base_url}{path}", headers=headers)
            refreshed.raise_for_status()
            refreshed_body = refreshed.json()
            refreshed_reviews = (
                refreshed_body.get("data", refreshed_body)
                if isinstance(refreshed_body, dict)
                else refreshed_body
            )
            if not isinstance(refreshed_reviews, list):
                raise RuntimeError("Unexpected reviews response shape")

            for review in refreshed_reviews:
                if not isinstance(review, dict):
                    continue
                if review.get("author") == author_email:
                    review_id = review.get("_id") or review.get("id")
                    if review_id is not None:
                        return str(review_id)

        raise RuntimeError("Failed to create or locate User A product review")

    def probe_cross_actor_review_edit(
        self,
        actor: AuthenticatedActor,
        review_id: str,
        new_message: str,
    ) -> ProbeCapture:
        path = "/rest/products/reviews"
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Content-Type": "application/json",
        }
        payload = {"id": review_id, "message": new_message}
        with httpx.Client(timeout=30.0) as client:
            response = client.patch(
                f"{self._base_url}{path}",
                headers=headers,
                json=payload,
            )

        return ProbeCapture(
            scenario="Cross-actor review edit",
            actor_context=actor.actor_context,
            request_method="PATCH",
            request_path=path,
            request_headers=headers,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.text[:2000],
        )

    def probe_apply_coupon(
        self,
        actor: AuthenticatedActor,
        basket_id: int,
        coupon_code: str,
        *,
        scenario: str,
    ) -> ProbeCapture:
        headers = {
            "Authorization": f"Bearer {actor.token}",
            "Accept": "application/json",
        }
        path = coupon_apply_path(basket_id, coupon_code)
        with httpx.Client(timeout=30.0) as client:
            response = client.put(f"{self._base_url}{path}", headers=headers)

        return ProbeCapture(
            scenario=scenario,
            actor_context=actor.actor_context,
            request_method="PUT",
            request_path=path,
            request_headers=headers,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response.text[:2000],
        )
