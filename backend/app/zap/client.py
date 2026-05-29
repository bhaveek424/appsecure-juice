from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx

from app.config import get_settings


@dataclass(frozen=True)
class ZapProgress:
    phase: str
    percent: int
    current_step: str


class ZapClient(Protocol):
    def run_scan(
        self,
        target_url: str,
        progress_callback: Callable[[ZapProgress], None],
    ) -> list[dict[str, Any]]: ...

    def stop_active_scans(self) -> None: ...


class HttpZapClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.zap_api_url.rstrip("/")
        self._api_key = settings.zap_api_key.get_secret_value()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        if self._api_key:
            query["apikey"] = self._api_key
        url = f"{self._base_url}{path}?{urlencode(query)}"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
        return payload

    def run_scan(
        self,
        target_url: str,
        progress_callback: Callable[[ZapProgress], None],
    ) -> list[dict[str, Any]]:
        progress_callback(
            ZapProgress(
                phase="spider",
                percent=0,
                current_step="Starting spider scan",
            )
        )
        self._get("/JSON/spider/action/scan/", {"url": target_url})
        self._wait_for_completion(
            "/JSON/spider/view/status/",
            phase="spider",
            progress_callback=progress_callback,
            start_percent=0,
            end_percent=45,
            running_step="Spider scan in progress",
            complete_step="Spider scan complete",
        )

        progress_callback(
            ZapProgress(
                phase="ascan",
                percent=50,
                current_step="Starting active scan",
            )
        )
        self._get("/JSON/ascan/action/scan/", {"url": target_url})
        self._wait_for_completion(
            "/JSON/ascan/view/status/",
            phase="ascan",
            progress_callback=progress_callback,
            start_percent=50,
            end_percent=95,
            running_step="Active scan in progress",
            complete_step="Active scan complete",
        )

        progress_callback(
            ZapProgress(
                phase="alerts",
                percent=100,
                current_step="Collecting scanner findings",
            )
        )
        alerts_payload = self._get("/JSON/core/view/alerts/", {"baseurl": target_url})
        return list(alerts_payload.get("alerts", []))

    def stop_active_scans(self) -> None:
        self._get("/JSON/spider/action/stop/")
        self._get("/JSON/ascan/action/stop/")

    def _wait_for_completion(
        self,
        status_path: str,
        *,
        phase: str,
        progress_callback: Callable[[ZapProgress], None],
        start_percent: int,
        end_percent: int,
        running_step: str,
        complete_step: str,
    ) -> None:
        import time

        while True:
            status_payload = self._get(status_path)
            status_value = int(status_payload.get("status", "100"))
            span = max(end_percent - start_percent, 1)
            percent = start_percent + int((status_value / 100) * span)
            progress_callback(
                ZapProgress(
                    phase=phase,
                    percent=min(percent, end_percent),
                    current_step=running_step if status_value < 100 else complete_step,
                )
            )
            if status_value >= 100:
                return
            time.sleep(1)


class MockZapClient:
    def __init__(self, alerts: list[dict[str, Any]] | None = None) -> None:
        self.stop_calls = 0
        self._alerts = alerts or [
            {
                "alert": "Cross Site Scripting",
                "name": "Cross Site Scripting",
                "risk": "High",
                "riskcode": "3",
                "url": "http://juice-shop:3000/#/search",
                "desc": "Reflected XSS",
                "solution": "Encode output",
                "evidence": "<script>",
                "confidence": "Medium",
            }
        ]

    def run_scan(
        self,
        target_url: str,
        progress_callback: Callable[[ZapProgress], None],
    ) -> list[dict[str, Any]]:
        _ = target_url
        progress_callback(
            ZapProgress(
                phase="spider",
                percent=25,
                current_step="Spider scan in progress",
            )
        )
        progress_callback(
            ZapProgress(
                phase="ascan",
                percent=75,
                current_step="Active scan in progress",
            )
        )
        progress_callback(
            ZapProgress(
                phase="alerts",
                percent=100,
                current_step="Collecting scanner findings",
            )
        )
        return list(self._alerts)

    def stop_active_scans(self) -> None:
        self.stop_calls += 1
