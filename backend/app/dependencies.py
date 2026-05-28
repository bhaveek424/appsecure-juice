import httpx

from app.config import get_settings


def check_target_application() -> bool:
    settings = get_settings()
    try:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            response = client.get(settings.target_application_url)
            return response.status_code < 500
    except httpx.HTTPError:
        return False


def check_zap() -> bool:
    settings = get_settings()
    version_url = f"{settings.zap_api_url.rstrip('/')}/JSON/core/view/version/"
    headers: dict[str, str] = {}
    api_key = settings.zap_api_key.get_secret_value()
    if api_key:
        headers["X-ZAP-API-Key"] = api_key

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(version_url, headers=headers)
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def dependency_status() -> dict[str, dict[str, bool]]:
    return {
        "target_application": {"reachable": check_target_application()},
        "zap": {"reachable": check_zap()},
    }


def overall_status(dependencies: dict[str, dict[str, bool]]) -> str:
    ready = all(dep["reachable"] for dep in dependencies.values())
    return "ok" if ready else "degraded"
