from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.actor_context import ActorContext


@dataclass(frozen=True)
class AuthenticatedActor:
    actor_context: ActorContext
    user_id: int
    basket_id: int
    token: str


@dataclass(frozen=True)
class ProbeCapture:
    scenario: str
    actor_context: ActorContext
    request_method: str
    request_path: str
    request_headers: dict[str, str]
    response_status: int
    response_headers: dict[str, str]
    response_body: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "actor_context": self.actor_context.value,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "request_headers": self.request_headers,
            "response_status": self.response_status,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
        }


class TargetClient(Protocol):
    def register_user(self, email: str, password: str) -> None: ...

    def login(self, email: str, password: str, actor_context: ActorContext) -> AuthenticatedActor: ...

    def probe_cross_actor_basket_access(
        self,
        actor: AuthenticatedActor,
        other_basket_id: int,
    ) -> ProbeCapture: ...

    def ensure_user_product_review(
        self,
        actor: AuthenticatedActor,
        product_id: int,
        message: str,
        author_email: str,
    ) -> str: ...

    def probe_cross_actor_review_edit(
        self,
        actor: AuthenticatedActor,
        review_id: str,
        new_message: str,
    ) -> ProbeCapture: ...
