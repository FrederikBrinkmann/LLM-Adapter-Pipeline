import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

const TICKETS_API_BASE_URL =
  import.meta.env.VITE_TICKETS_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:9000";

type TicketStatus = "todo" | "in_progress" | "waiting_for_customer" | "done";
type TicketPriority = "low" | "medium" | "high" | "urgent";
type TicketDomain = "insurance" | "ecommerce" | "logistics" | "general";

type StatusFilter = TicketStatus | "all";
type DomainFilter = TicketDomain | "all";

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
  subject: string;
  summary: string;
  customer: string | null;
  domain: string | null;
  description: string | null;
  priority: TicketPriority;
  status: TicketStatus;
  policy_number: string | null;
  claim_type: string | null;
  missing_fields: string[];
  action_items: ActionItem[];
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

const DOMAIN_LABELS: Record<TicketDomain, string> = {
  insurance: "Versicherung",
  ecommerce: "E-Commerce",
  logistics: "Logistik",
  general: "Allgemein",
};

const ACTION_PRESETS: Record<
  TicketDomain,
  { type: string; title: string; details: string; suggested_by?: ActionSource }[]
> = {
  insurance: [
    {
      type: "survey",
      title: "Schadensprüfung",
      details: "Gutachter zuweisen und Kontakt herstellen",
    },
    {
      type: "documents",
      title: "Dokumente anfordern",
      details: "Fehlende Nachweise bei Kundin erfragen",
    },
  ],
  ecommerce: [
    { type: "return", title: "Retoure freigeben", details: "Retourenlabel erstellen" },
    { type: "exchange", title: "Umtausch vorbereiten", details: "Ersatzprodukt reservieren" },
  ],
  logistics: [
    { type: "tracking", title: "Sendung verfolgen", details: "Carrier kontaktieren" },
    { type: "pickup", title: "Abholung planen", details: "Slot mit Kunde abstimmen" },
  ],
  general: [
    { type: "follow_up", title: "Rückfrage senden", details: "Kund:in um mehr Infos bitten" },
  ],
};

const statusOrder: TicketStatus[] = ["todo", "in_progress", "waiting_for_customer", "done"];

const formatDate = (isoDate: string) =>
  new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(isoDate));

const TicketBoard = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [domainFilter, setDomainFilter] = useState<DomainFilter>("all");
  const [formState, setFormState] = useState({
    subject: "",
    customer: "",
    domain: "insurance" as TicketDomain,
    priority: "medium" as TicketPriority,
    description: "",
    actionType: ACTION_PRESETS.insurance[0]?.type ?? "survey",
  });

  const filteredTickets = useMemo(() => {
    return tickets
      .filter((ticket) => (statusFilter === "all" ? true : ticket.status === statusFilter))
      .filter((ticket) =>
        domainFilter === "all" ? true : (ticket.domain ?? "general") === domainFilter
      )
      .sort((a, b) => statusOrder.indexOf(a.status) - statusOrder.indexOf(b.status));
  }, [tickets, statusFilter, domainFilter]);

  const actionOptions = useMemo(() => ACTION_PRESETS[formState.domain], [formState.domain]);

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
      customer: formState.customer.trim() || null,
      domain: formState.domain,
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
        customer: "",
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
          Dieser Service zeigt sowohl manuell erstellte Tickets als auch Einträge, die aus der LLM-Pipeline stammen.
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
              placeholder="z.B. Retoure oder Schadensmeldung"
              required
            />
          </label>
          <label>
            Kunde / Team
            <input
              type="text"
              value={formState.customer}
              onChange={(event) => setFormState((prev) => ({ ...prev, customer: event.target.value }))}
              placeholder="Name oder Company"
            />
          </label>
          <label>
            Domäne
            <select
              value={formState.domain}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  domain: event.target.value as TicketDomain,
                  actionType: ACTION_PRESETS[event.target.value as TicketDomain][0]?.type ?? prev.actionType,
                }))
              }
            >
              {Object.entries(DOMAIN_LABELS).map(([domain, label]) => (
                <option key={domain} value={domain}>
                  {label}
                </option>
              ))}
            </select>
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
        <label>
          Domäne
          <select value={domainFilter} onChange={(event) => setDomainFilter(event.target.value as DomainFilter)}>
            <option value="all">Alle Bereiche</option>
            {Object.entries(DOMAIN_LABELS).map(([domain, label]) => (
              <option key={domain} value={domain}>
                {label}
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
              <th>Kunde / Domäne</th>
              <th>Status</th>
              <th>Priorität</th>
              <th>Action Items & fehlende Felder</th>
              <th>Aktualisiert</th>
            </tr>
          </thead>
          <tbody>
            {filteredTickets.map((ticket) => (
              <tr key={ticket.id}>
                <td>
                  <div className="ticket-title">
                    <strong>#{ticket.id}</strong>
                    <span>{ticket.subject}</span>
                    {ticket.claim_type && <small>Typ: {ticket.claim_type}</small>}
                  </div>
                  {ticket.summary && <p className="ticket-description">{ticket.summary}</p>}
                  {ticket.source_job_id && (
                    <small className="muted">
                      Aus Job #{ticket.source_job_id} ({ticket.source_model_id ?? "unbekannt"})
                    </small>
                  )}
                </td>
                <td>
                  <div className="ticket-meta">
                    <span>{ticket.customer ?? "–"}</span>
                    <small>{ticket.domain ? DOMAIN_LABELS[ticket.domain as TicketDomain] ?? ticket.domain : "Allgemein"}</small>
                    {ticket.policy_number && <small>Police: {ticket.policy_number}</small>}
                  </div>
                </td>
                <td>
                  <select
                    className="ticket-status-select"
                    value={ticket.status}
                    onChange={(event) => handleStatusChange(ticket.id, event.target.value as TicketStatus)}
                  >
                    {statusOrder.map((status) => (
                      <option key={status} value={status}>
                        {STATUS_LABELS[status]}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <span className={`priority-pill priority-${ticket.priority}`}>
                    {PRIORITY_LABELS[ticket.priority]}
                  </span>
                </td>
                <td>
                  <div className="action-grid">
                    {ticket.action_items.map((action) => (
                      <div key={action.id} className="action-card">
                        <span className="action-card__label">{action.title}</span>
                        {action.details && <p>{action.details}</p>}
                        <small>Quelle: {action.suggested_by.toUpperCase()}</small>
                      </div>
                    ))}
                    {ticket.action_items.length === 0 && <span className="muted">Keine Vorschläge</span>}
                    {ticket.missing_fields.length > 0 && (
                      <div className="missing-fields">
                        <strong>Fehlende Angaben:</strong>
                        <div>
                          {ticket.missing_fields.map((field) => (
                            <span key={field} className="missing-pill">
                              {field}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </td>
                <td>
                  <span className="ticket-date">{formatDate(ticket.updated_at)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default TicketBoard;
