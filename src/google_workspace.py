from __future__ import annotations

import base64
import csv
import json
import os
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
GOOGLE_DIR = ROOT / "data" / "google"
CLIENT_SECRET_FILE = Path(
    os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE", str(GOOGLE_DIR / "client_secret.json"))
)
TOKEN_FILE = Path(os.getenv("GOOGLE_OAUTH_TOKEN_FILE", str(GOOGLE_DIR / "token.json")))
SERVICE_ACCOUNT_FILE = Path(
    os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", str(GOOGLE_DIR / "service_account.json"))
)
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
SERVICE_ACCOUNT_JSON_B64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64", "").strip()
PUBLIC_SHEETS_BASE_URL = os.getenv("GOOGLE_SHEETS_PUBLIC_CSV_URL", "").strip()

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _ensure_google_dir() -> None:
    GOOGLE_DIR.mkdir(parents=True, exist_ok=True)


def _load_service_account_info() -> dict[str, Any] | None:
    payload = SERVICE_ACCOUNT_JSON
    if not payload and SERVICE_ACCOUNT_JSON_B64:
        payload = base64.b64decode(SERVICE_ACCOUNT_JSON_B64).decode("utf-8")
    if not payload and SERVICE_ACCOUNT_FILE.exists():
        payload = SERVICE_ACCOUNT_FILE.read_text(encoding="utf-8")
    if not payload:
        return None
    return json.loads(payload)


def _build_public_sheet_csv_url(spreadsheet_id: str, range_name: str) -> str:
    if PUBLIC_SHEETS_BASE_URL:
        base_url = PUBLIC_SHEETS_BASE_URL.rstrip("?&")
        if "spreadsheet" in base_url and "?" in base_url:
            return f"{base_url}&sheet={quote(range_name.split('!')[0])}" if "!" in range_name else base_url
        return base_url
    sheet_name = ""
    csv_range = ""
    if "!" in range_name:
        sheet_name, csv_range = range_name.split("!", 1)
    else:
        sheet_name = range_name
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv"
    if sheet_name:
        url += f"&sheet={quote(sheet_name)}"
    if csv_range:
        url += f"&range={quote(csv_range)}"
    return url


def _read_public_sheet_range(spreadsheet_id: str, range_name: str) -> list[list[Any]]:
    url = _build_public_sheet_csv_url(spreadsheet_id, range_name)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        return []
    reader = csv.reader(StringIO(text))
    return [row for row in reader]


def get_google_sheets_credentials(scopes: list[str] | None = None) -> Credentials:
    use_scopes = scopes or SHEETS_SCOPES
    service_account_info = _load_service_account_info()
    if service_account_info:
        return service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=use_scopes,
        )
    return get_google_credentials(scopes=use_scopes)


def get_google_credentials(
    scopes: list[str] | None = None, force_reauth: bool = False
) -> Credentials:
    _ensure_google_dir()
    use_scopes = scopes or DEFAULT_SCOPES
    creds: Credentials | None = None

    if TOKEN_FILE.exists() and not force_reauth:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), use_scopes)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"Arquivo OAuth nao encontrado: {CLIENT_SECRET_FILE}. "
                "Baixe o OAuth Client ID (Desktop app) no Google Cloud e salve nesse caminho."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), use_scopes)
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def build_google_service(service_name: str, version: str, scopes: list[str] | None = None) -> Any:
    creds = get_google_credentials(scopes=scopes)
    return build(service_name, version, credentials=creds)


def build_google_sheets_service(
    service_name: str = "sheets", version: str = "v4", scopes: list[str] | None = None
) -> Any:
    creds = get_google_sheets_credentials(scopes=scopes)
    return build(service_name, version, credentials=creds)


def gmail_profile() -> dict[str, Any]:
    svc = build_google_service("gmail", "v1")
    return svc.users().getProfile(userId="me").execute()


def list_calendars() -> list[dict[str, Any]]:
    svc = build_google_service("calendar", "v3")
    data = svc.calendarList().list(maxResults=50).execute()
    return data.get("items", [])


def list_drive_files(page_size: int = 10) -> list[dict[str, Any]]:
    svc = build_google_service("drive", "v3")
    data = (
        svc.files()
        .list(
            pageSize=page_size,
            fields="files(id,name,mimeType,modifiedTime,owners(displayName))",
        )
        .execute()
    )
    return data.get("files", [])


def read_sheet_range(spreadsheet_id: str, range_name: str) -> list[list[Any]]:
    service_account_info = _load_service_account_info()
    if service_account_info:
        svc = build_google_sheets_service()
        data = (
            svc.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return data.get("values", [])
    return _read_public_sheet_range(spreadsheet_id, range_name)


def write_sheet_range(
    spreadsheet_id: str,
    range_name: str,
    values: list[list[Any]],
    value_input_option: str = "USER_ENTERED",
) -> dict[str, Any]:
    svc = build_google_sheets_service()
    body = {"values": values}
    data = (
        svc.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body,
        )
        .execute()
    )
    return data
