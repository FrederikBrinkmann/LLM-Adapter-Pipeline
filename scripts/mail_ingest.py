#!/usr/bin/env python3
"""
Pollt ein IMAP-Postfach und legt neue Mails als Jobs über /ingest/ an.

Konfiguration via Umgebungsvariablen:
- MAIL_IMAP_HOST (erforderlich), MAIL_IMAP_PORT (default 993)
- MAIL_IMAP_USER, MAIL_IMAP_PASSWORD
- MAIL_IMAP_FOLDER (default: INBOX)
- MAIL_POLL_INTERVAL (Sekunden, default 30)
- MAIL_MODEL_ID (optional, falls nicht gesetzt wird Default-Modell genutzt)
- MAIL_API_BASE (default: http://127.0.0.1:8000)
"""

from __future__ import annotations

import email
import imaplib
import os
import re
import ssl
import sys
import time
from email.header import decode_header
from typing import Optional

import httpx


def env(key: str, default: Optional[str] = None, required: bool = False) -> str | None:
    value = os.getenv(key, default)
    if required and not value:
        raise RuntimeError(f"Environment variable {key} is required")
    return value


def decode_subject(msg: email.message.Message) -> str:
    subject = msg.get("Subject", "")
    decoded_parts = decode_header(subject)
    parts: list[str] = []
    for value, encoding in decoded_parts:
        if isinstance(value, bytes):
            try:
                parts.append(value.decode(encoding or "utf-8", errors="ignore"))
            except LookupError:
                parts.append(value.decode("utf-8", errors="ignore"))
        else:
            parts.append(str(value))
    return " ".join(parts).strip()


def extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            if disposition == "attachment":
                continue
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="ignore").strip()
        # Fallback: HTML als Text extrahieren
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                    return strip_html(text)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="ignore").strip()
    return ""


def strip_html(html: str) -> str:
    # Sehr einfacher HTML-Stripper, nur für Fallback.
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def submit_ingest(api_base: str, text: str, model_id: Optional[str]) -> int:
    url = f"{api_base.rstrip('/')}/ingest/"
    payload = {"text": text}
    if model_id:
        payload["model_id"] = model_id
    with httpx.Client(timeout=15.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return int(data["job_id"])


def main() -> None:
    host = env("MAIL_IMAP_HOST", required=True)
    port = int(env("MAIL_IMAP_PORT", "993"))
    user = env("MAIL_IMAP_USER", required=True)
    password = env("MAIL_IMAP_PASSWORD", required=True)
    folder = env("MAIL_IMAP_FOLDER", "INBOX")
    poll_interval = int(env("MAIL_POLL_INTERVAL", "30"))
    model_id = env("MAIL_MODEL_ID")
    api_base = env("MAIL_API_BASE", "http://127.0.0.1:8000")

    ssl_context = ssl.create_default_context()

    while True:
        try:
            with imaplib.IMAP4_SSL(host, port, ssl_context=ssl_context) as imap:
                imap.login(user, password)
                imap.select(folder)
                status, data = imap.search(None, "UNSEEN")
                if status != "OK":
                    print(f"[warn] Suche nach UNSEEN fehlgeschlagen: {status}")
                uids = data[0].split() if data and data[0] else []
                for uid in uids:
                    status, msg_data = imap.fetch(uid, "(RFC822)")
                    if status != "OK" or not msg_data:
                        print(f"[warn] Fetch fehlgeschlagen für UID {uid}")
                        continue
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = decode_subject(msg)
                    body = extract_body(msg)
                    text = (subject + "\n\n" + body).strip()

                    if not text:
                        print(f"[warn] Leere Mail übersprungen (UID {uid})")
                        imap.store(uid, "+FLAGS", "\\Seen")
                        continue

                    try:
                        job_id = submit_ingest(api_base, text, model_id)
                        print(f"[info] Mail UID {uid.decode()} -> Job {job_id}")
                        imap.store(uid, "+FLAGS", "\\Seen")
                    except Exception as exc:  # noqa: BLE001
                        print(f"[error] Ingest fehlgeschlagen für UID {uid}: {exc}")
                        # Nicht als gesehen markieren, damit Retry möglich ist.
                imap.logout()
        except KeyboardInterrupt:
            print("\n[info] Beendet.")
            sys.exit(0)
        except Exception as exc:  # noqa: BLE001
            print(f"[error] IMAP-Loop Fehler: {exc}")
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
