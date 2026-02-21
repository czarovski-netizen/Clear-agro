from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Iterable


def telegram_enabled() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def build_alerts_message(title: str, period: str, alerts: Iterable[tuple[str, object]]) -> str:
    lines = [f"{title}", f"Periodo: {period}", ""]
    for label, value in alerts:
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def send_telegram_message(text: str) -> tuple[bool, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False, "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID nao configurados"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    return send_telegram_payload(payload)


def send_telegram_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return False, "TELEGRAM_BOT_TOKEN nao configurado"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        if data.get("ok"):
            return True, "Mensagem enviada ao Telegram"
        return False, f"Erro Telegram: {data.get('description', 'falha desconhecida')}"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return False, f"HTTP {exc.code}: {detail[:180]}"
    except Exception as exc:  # nosec B110
        return False, f"Falha de envio: {exc}"


def send_telegram_message_to_chat(chat_id: str | int, text: str) -> tuple[bool, str]:
    payload = {
        "chat_id": str(chat_id),
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    return send_telegram_payload(payload)


def get_telegram_updates(offset: int | None = None, timeout: int = 25) -> tuple[bool, list[dict[str, Any]], str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return False, [], "TELEGRAM_BOT_TOKEN nao configurado"
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    payload: dict[str, Any] = {"timeout": timeout}
    if offset is not None:
        payload["offset"] = offset
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        if not data.get("ok"):
            return False, [], str(data.get("description", "Erro no getUpdates"))
        return True, data.get("result", []), "ok"
    except Exception as exc:  # nosec B110
        return False, [], f"Falha getUpdates: {exc}"
