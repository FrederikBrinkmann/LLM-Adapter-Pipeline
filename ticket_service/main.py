from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .schemas import Ticket, TicketCreate, TicketUpdate
from .storage import TicketNotFoundError, store

app = FastAPI(
    title="Ticket Demo Service",
    description="Lightweight insurance claim board that accepts structured JSON payloads from the LLM pipeline.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tickets", response_model=list[Ticket], tags=["tickets"], summary="List all tickets")
def list_tickets() -> list[Ticket]:
    return store.list_tickets()


@app.get("/tickets/{ticket_id}", response_model=Ticket, tags=["tickets"], summary="Get ticket details")
def get_ticket(ticket_id: int) -> Ticket:
    try:
        return store.get_ticket(ticket_id)
    except TicketNotFoundError as exc:  # pragma: no cover - FastAPI handles response
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post(
    "/tickets",
    response_model=Ticket,
    tags=["tickets"],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ticket",
)
def create_ticket(ticket_in: TicketCreate) -> Ticket:
    return store.create_ticket(ticket_in)


@app.patch(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    tags=["tickets"],
    summary="Update ticket fields (status, priority, notes, action items)",
)
def update_ticket(ticket_id: int, ticket_update: TicketUpdate) -> Ticket:
    try:
        return store.update_ticket(ticket_id, ticket_update)
    except TicketNotFoundError as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


__all__ = ["app"]
