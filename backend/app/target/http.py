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
