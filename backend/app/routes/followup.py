"""
Endpoint für die Generierung von Follow-up E-Mails bei fehlenden Ticket-Feldern.
"""
from __future__ import annotations

import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from textwrap import dedent
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..config import settings
from ..llm.adapter import LLMAdapter
from ..llm.model_config import get_model_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/followup", tags=["followup"])


class FollowupRequest(BaseModel):
    """Request-Schema für Follow-up E-Mail Generierung."""
    ticket_id: int
    ticket_subject: str
    claimant_name: str | None = None
    claimant_email: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    claim_type: str | None = None
    description: str | None = None
    model_id: str | None = None


class FollowupResponse(BaseModel):
    """Response mit generierter E-Mail."""
    subject: str
    body: str
    recipient_email: str | None
    generated_by: str


FOLLOWUP_SYSTEM_MESSAGE = (
    "Du bist ein freundlicher Sachbearbeiter einer deutschen Versicherung. "
    "Schreibe professionelle, aber herzliche E-Mails auf Deutsch. "
    "Verwende Sie-Form und sei höflich aber direkt."
)

FOLLOWUP_PROMPT_TEMPLATE = dedent("""
    Erstelle eine freundliche Nachfrage-E-Mail an den Kunden, um fehlende Informationen für den Versicherungsfall zu erfragen.
    
    Ticket-Informationen:
    - Ticket-ID: #{ticket_id}
    - Betreff: {ticket_subject}
    - Kundenname: {claimant_name}
    - Schadensart: {claim_type}
    - Beschreibung: {description}
    
    Fehlende Felder, die erfragt werden müssen:
    {missing_fields_formatted}
    
    Antworte NUR mit einem JSON-Objekt in diesem Format:
    {{
        "subject": "Betreff der E-Mail (kurz, mit Ticket-Referenz)",
        "body": "Vollständiger E-Mail-Text mit Anrede, Hauptteil und Grußformel"
    }}
    
    Regeln:
    - Beginne mit "Sehr geehrte/r [Name]" oder "Sehr geehrte Damen und Herren" falls kein Name bekannt
    - Erkläre kurz, dass weitere Informationen für die Bearbeitung benötigt werden
    - Liste die fehlenden Informationen als nummerierte Liste auf
    - Erkläre bei jedem Punkt kurz, warum diese Information wichtig ist
    - Schließe mit freundlicher Grußformel ab
    - Unterschreibe mit "Ihr Versicherungs-Team"
    - Halte die E-Mail kompakt aber vollständig
""")

MISSING_FIELD_LABELS = {
    "claimant_name": "Name des Versicherungsnehmers",
    "claimant_email": "E-Mail-Adresse",
    "claimant_phone": "Telefonnummer",
    "policy_number": "Versicherungsschein-Nummer",
    "claim_date": "Datum der Schadensmeldung",
    "incident_date": "Datum des Schadensereignisses",
    "incident_location": "Ort des Schadensereignisses",
    "claim_amount": "Geschätzte Schadenshöhe",
    "description": "Detaillierte Schadensbeschreibung",
    "medical_report": "Ärztlicher Befund / Attest",
    "photos": "Fotos des Schadens",
    "damage_estimate": "Kostenvoranschlag",
}


def _format_missing_fields(fields: list[str]) -> str:
    """Formatiert die fehlenden Felder für den Prompt."""
    lines = []
    for field in fields:
        label = MISSING_FIELD_LABELS.get(field, field.replace("_", " ").title())
        lines.append(f"- {label}")
    return "\n".join(lines) if lines else "- Keine spezifischen Felder angegeben"


@router.post(
    "/generate",
    response_model=FollowupResponse,
    summary="Generiert eine Follow-up E-Mail für fehlende Ticket-Felder",
)
async def generate_followup_email(request: FollowupRequest) -> FollowupResponse:
    """
    Nutzt das LLM um eine personalisierte Nachfrage-E-Mail zu generieren,
    die den Kunden nach fehlenden Informationen fragt.
    """
    if not request.missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine fehlenden Felder angegeben - E-Mail-Generierung nicht erforderlich."
        )
    
    # Model auswählen
    model_id = request.model_id or settings.llm_default_model
    try:
        model_config = get_model_config(model_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unbekanntes Modell: {model_id}"
        ) from exc
    
    # Prompt zusammenbauen
    prompt = FOLLOWUP_PROMPT_TEMPLATE.format(
        ticket_id=request.ticket_id,
        ticket_subject=request.ticket_subject,
        claimant_name=request.claimant_name or "Unbekannt",
        claim_type=request.claim_type or "Nicht angegeben",
        description=request.description or "Keine Beschreibung vorhanden",
        missing_fields_formatted=_format_missing_fields(request.missing_fields),
    )
    
    # LLM aufrufen
    adapter = LLMAdapter(
        model_id=model_config.model_id,
        display_name=model_config.display_name,
        provider=model_config.provider,
        parameters=model_config.parameters,
    )
    try:
        result = await adapter.generate(
            prompt=prompt,
            system_message=FOLLOWUP_SYSTEM_MESSAGE,
        )
    except Exception as exc:
        logger.exception("LLM-Aufruf fehlgeschlagen")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM-Aufruf fehlgeschlagen: {exc}"
        ) from exc
    
    # JSON aus Antwort extrahieren
    try:
        # Versuche JSON zu parsen (auch wenn es in Markdown-Blöcken ist)
        content = result.get("content", "")
        # Entferne mögliche Markdown-Code-Blöcke
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        parsed = json.loads(content.strip())
        subject = parsed.get("subject", f"Rückfrage zu Ticket #{request.ticket_id}")
        body = parsed.get("body", "")
        
        if not body:
            raise ValueError("Leerer E-Mail-Body")
            
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(f"Konnte LLM-Antwort nicht parsen: {exc}, verwende Fallback")
        # Fallback: Generiere einfache E-Mail
        subject = f"Rückfrage zu Ihrem Versicherungsfall #{request.ticket_id}"
        body = _generate_fallback_email(request)
    
    return FollowupResponse(
        subject=subject,
        body=body,
        recipient_email=request.claimant_email,
        generated_by=model_id,
    )


def _generate_fallback_email(request: FollowupRequest) -> str:
    """Fallback-E-Mail falls LLM-Parsing fehlschlägt."""
    name = request.claimant_name or "Damen und Herren"
    greeting = f"Sehr geehrte/r {name}" if request.claimant_name else "Sehr geehrte Damen und Herren"
    
    fields_list = "\n".join(
        f"  {i+1}. {MISSING_FIELD_LABELS.get(f, f.replace('_', ' ').title())}"
        for i, f in enumerate(request.missing_fields)
    )
    
    return f"""{greeting},

vielen Dank für Ihre Schadensmeldung (Ticket #{request.ticket_id}).

Um Ihren Fall schnellstmöglich bearbeiten zu können, benötigen wir noch folgende Informationen von Ihnen:

{fields_list}

Bitte antworten Sie auf diese E-Mail mit den fehlenden Angaben oder kontaktieren Sie uns telefonisch.

Mit freundlichen Grüßen
Ihr Versicherungs-Team"""


# ─────────────────────────────────────────────────────────────────────────────
# E-Mail Send Endpoint
# ─────────────────────────────────────────────────────────────────────────────


class SendEmailRequest(BaseModel):
    """Request-Schema für E-Mail-Versand."""
    recipient_email: str
    subject: str
    body: str
    ticket_id: int | None = None


class SendEmailResponse(BaseModel):
    """Response-Schema für E-Mail-Versand."""
    success: bool
    message: str
    recipient_email: str


@router.post("/send", response_model=SendEmailResponse)
async def send_followup_email(request: SendEmailRequest) -> SendEmailResponse:
    """
    Sendet eine Follow-up E-Mail an den Kunden.
    
    Verwendet SMTP-Konfiguration aus den Settings.
    """
    # Prüfe ob SMTP konfiguriert ist
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP nicht konfiguriert - E-Mail wird nicht gesendet")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMTP-Server nicht konfiguriert. Bitte SMTP-Einstellungen in der .env Datei setzen."
        )
    
    if not request.recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Empfänger-E-Mail-Adresse angegeben."
        )
    
    try:
        # E-Mail erstellen
        msg = MIMEMultipart()
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = request.recipient_email
        msg["Subject"] = request.subject
        
        # Ticket-ID als Header hinzufügen falls vorhanden
        if request.ticket_id:
            msg["X-Ticket-ID"] = str(request.ticket_id)
        
        msg.attach(MIMEText(request.body, "plain", "utf-8"))
        
        # SMTP-Verbindung aufbauen und senden
        logger.info(f"Verbinde mit SMTP-Server {settings.smtp_host}:{settings.smtp_port}")
        
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"E-Mail erfolgreich gesendet an {request.recipient_email} (Ticket #{request.ticket_id})")
        
        return SendEmailResponse(
            success=True,
            message="E-Mail erfolgreich gesendet",
            recipient_email=request.recipient_email
        )
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP-Authentifizierungsfehler: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SMTP-Authentifizierung fehlgeschlagen. Bitte Zugangsdaten prüfen."
        )
    except smtplib.SMTPException as e:
        logger.error(f"SMTP-Fehler beim Senden: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fehler beim E-Mail-Versand: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unerwarteter Fehler beim E-Mail-Versand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unerwarteter Fehler: {str(e)}"
        )
