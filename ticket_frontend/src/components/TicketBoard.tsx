import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import TicketDetail from "./TicketDetail";

const TICKETS_API_BASE_URL =
  import.meta.env.VITE_TICKETS_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:9000";

type TicketStatus = "todo" | "in_progress" | "waiting_for_customer" | "done";
type TicketPriority = "low" | "medium" | "high" | "urgent";

type StatusFilter = TicketStatus | "all";

type ActionSource = "llm" | "agent" | "system";

interface ActionItem {
  id: string;
  title: string;
  details: string | null;
  suggested_by: ActionSource;
  status: "open" | "done";
}

interface Ticket {
  id: number;
  ticket_id: string | null;
  subject: string;
  summary: string;
  claimant_name: string | null;
  claimant_email: string | null;
  claimant_phone: string | null;
  description: string | null;
  priority: TicketPriority;
  status: TicketStatus;
  policy_number: string | null;
  claim_type: string | null;
  claim_date: string | null;
  incident_date: string | null;
  incident_location: string | null;
  claim_amount: number | null;
  missing_fields: string[];
  has_missing_critical_fields: boolean;
  action_items: ActionItem[];
  next_steps: string | null;
  created_timestamp: string | null;
  source_job_id: number | null;
  source_model_id: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_LABELS: Record<TicketStatus, string> = {
  todo: "Todo",
  in_progress: "In Arbeit",
  waiting_for_customer: "Warten auf Kunde",
  done: "Erledigt",
};

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: "Niedrig",
  medium: "Normal",
  high: "Hoch",
  urgent: "Dringend",
};

const ACTION_PRESETS = [
  {
    type: "request_documents",
    title: "Unterlagen anfordern",
    details: "Arztbericht, Fotos oder Rechnungen beim Kunden anfordern",
    suggested_by: "agent" as ActionSource,
  },
  {
    type: "assign_adjuster",
    title: "Gutachter beauftragen",
    details: "Termin zur Schadenaufnahme vereinbaren",
    suggested_by: "agent" as ActionSource,
  },
  {
    type: "validate_claim",
    title: "Schaden prüfen",
    details: "Deckung und Schadenshöhe prüfen",
    suggested_by: "agent" as ActionSource,
  },
];

const statusOrder: TicketStatus[] = ["todo", "in_progress", "waiting_for_customer", "done"];

const formatDate = (isoDate: string) =>
  new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(isoDate));

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(amount);

const TicketBoard = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [formState, setFormState] = useState({
    subject: "",
    claimantName: "",
    priority: "medium" as TicketPriority,
    description: "",
    actionType: ACTION_PRESETS[0]?.type ?? "request_documents",
  });

  const filteredTickets = useMemo(() => {
    return tickets
      .filter((ticket) => (statusFilter === "all" ? true : ticket.status === statusFilter))
      .sort((a, b) => statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status));
  }, [tickets, statusFilter]);

  const actionOptions = useMemo(() => ACTION_PRESETS, []);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${TICKETS_API_BASE_URL}/tickets`);
      if (!response.ok) {
        throw new Error(`Ticket-Service antwortete mit Status ${response.status}`);
      }
      const data = (await response.json()) as Ticket[];
      setTickets(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unbekannter Fehler";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchTickets();
  }, [fetchTickets]);

  const handleCreateTicket = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.subject.trim()) {
      return;
    }
    const preset = actionOptions.find((option) => option.type === formState.actionType);
    const payload = {
      subject: formState.subject.trim(),
      summary: formState.subject.trim(),
      claimant_name: formState.claimantName.trim() || null,
      description: formState.description.trim() || null,
      priority: formState.priority,
      action_items: preset
        ? [
            {
              title: preset.title,
              details: preset.details,
              suggested_by: preset.suggested_by ?? "agent",
            },
          ]
        : [],
      missing_fields: [],
    };

    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch(`${TICKETS_API_BASE_URL}/tickets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`Ticket konnte nicht erstellt werden (Status ${response.status})`);
      }
      const ticket = (await response.json()) as Ticket;
      setTickets((prev) => [ticket, ...prev]);
      setFormState((prev) => ({
        ...prev,
        subject: "",
        claimantName: "",
        description: "",
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unbekannter Fehler";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusChange = async (ticketId: number, nextStatus: TicketStatus) => {
    setError(null);
    try {
      const response = await fetch(`${TICKETS_API_BASE_URL}/tickets/${ticketId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!response.ok) {
        throw new Error(`Ticket konnte nicht aktualisiert werden (Status ${response.status})`);
      }
      const updated = (await response.json()) as Ticket;
      setTickets((prev) => prev.map((ticket) => (ticket.id === ticketId ? updated : ticket)));
      // Auch selectedTicket aktualisieren, wenn es geöffnet ist
      if (selectedTicket?.id === ticketId) {
        setSelectedTicket(updated);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unbekannter Fehler";
      setError(message);
    }
  };

  return (
    <section className="ticket-board">
      <div className="ticket-board__intro">
        <h2>Tickets & Aktionen</h2>
        <p>
          Dieser Service zeigt sowohl manuell erstellte Schadenfälle als auch Einträge, die aus der LLM-Pipeline stammen.
        </p>
        <button className="secondary" type="button" onClick={() => fetchTickets()} disabled={loading}>
          {loading ? "Aktualisiere…" : "Tickets neu laden"}
        </button>
      </div>

      <form className="ticket-form" onSubmit={handleCreateTicket}>
        <h3>Neues Ticket</h3>
        <div className="ticket-form__grid">
          <label>
            Betreff / Zusammenfassung
            <input
              type="text"
              value={formState.subject}
              onChange={(event) => setFormState((prev) => ({ ...prev, subject: event.target.value }))}
              placeholder="z.B. Wasserschaden oder Unfall"
              required
            />
          </label>
          <label>
            Versicherungsnehmer
            <input
              type="text"
              value={formState.claimantName}
              onChange={(event) => setFormState((prev) => ({ ...prev, claimantName: event.target.value }))}
              placeholder="Name des Versicherten"
            />
          </label>
          <label>
            Priorität
            <select
              value={formState.priority}
              onChange={(event) => setFormState((prev) => ({ ...prev, priority: event.target.value as TicketPriority }))}
            >
              {Object.entries(PRIORITY_LABELS).map(([priority, label]) => (
                <option key={priority} value={priority}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Vorgeschlagene Aktion
            <select
              value={formState.actionType}
              onChange={(event) => setFormState((prev) => ({ ...prev, actionType: event.target.value }))}
            >
              {actionOptions.map((option) => (
                <option key={option.type} value={option.type}>
                  {option.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Kurzbeschreibung
            <textarea
              value={formState.description}
              onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))}
              rows={3}
              placeholder="Was ist zu tun?"
            />
          </label>
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? "Speichere…" : "Ticket anlegen"}
        </button>
      </form>

      <div className="ticket-filters">
        <label>
          Status
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}>
            <option value="all">Alle</option>
            {statusOrder.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <div className="result error">{error}</div>}

      <div className="ticket-table-wrapper">
        <table className="ticket-table">
          <thead>
            <tr>
              <th>Ticket</th>
              <th>Versicherungsnehmer</th>
              <th>Status</th>
              <th>Priorität</th>
              <th>Aktualisiert</th>
            </tr>
          </thead>
          <tbody>
            {filteredTickets.map((ticket) => (
              <tr
                key={ticket.id}
                className={`ticket-row ${ticket.has_missing_critical_fields ? "has-critical-missing" : ""}`}
                onClick={() => setSelectedTicket(ticket)}
                style={{ cursor: "pointer" }}
              >
                <td>
                  <div className="ticket-title">
                    <strong>#{ticket.id}</strong>
                    <span>{ticket.subject}</span>
                    {ticket.has_missing_critical_fields && <span className="critical-indicator">⚠️</span>}
                  </div>
                </td>
                <td>
                  <div className="ticket-meta-compact">
                    <span>{ticket.claimant_name ?? "–"}</span>
                  </div>
                </td>
                <td>
                  <span className={`status-badge status-${ticket.status}`}>{STATUS_LABELS[ticket.status]}</span>
                </td>
                <td>
                  <span className={`priority-pill priority-${ticket.priority}`}>
                    {PRIORITY_LABELS[ticket.priority]}
                  </span>
                </td>
                <td>
                  <span className="ticket-date">{formatDate(ticket.updated_at)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Ticket Detail Modal */}
      {selectedTicket && (
        <TicketDetail
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onStatusChange={(status) => handleStatusChange(selectedTicket.id, status)}
        />
      )}
    </section>
  );
};

export default TicketBoard;
