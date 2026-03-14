import { useState } from "react";

type TicketStatus = "todo" | "in_progress" | "waiting_for_customer" | "done";
type TicketPriority = "low" | "medium" | "high" | "urgent";
type ActionSource = "llm" | "agent" | "system";

// API Base URLs
const BACKEND_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

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

interface FollowupEmail {
  subject: string;
  body: string;
  recipient_email: string | null;
  generated_by: string;
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

const formatDate = (isoDate: string) =>
  new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(isoDate));

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(amount);

interface TicketDetailProps {
  ticket: Ticket;
  onClose: () => void;
  onStatusChange: (status: TicketStatus) => Promise<void>;
}

const TicketDetail = ({ ticket, onClose, onStatusChange }: TicketDetailProps) => {
  const [followupEmail, setFollowupEmail] = useState<FollowupEmail | null>(null);
  const [editedEmail, setEditedEmail] = useState<{ subject: string; body: string } | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState<string | null>(null);

  const handleStatusChange = async (newStatus: TicketStatus) => {
    try {
      await onStatusChange(newStatus);
    } catch (err) {
      console.error("Status update failed:", err);
    }
  };

  const handleGenerateFollowup = async () => {
    setIsGenerating(true);
    setEmailError(null);
    setEmailSuccess(null);
    setFollowupEmail(null);
    setEditedEmail(null);

    try {
      const response = await fetch(`${BACKEND_API_BASE_URL}/followup/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_id: ticket.id,
          ticket_subject: ticket.subject,
          claimant_name: ticket.claimant_name,
          claimant_email: ticket.claimant_email,
          missing_fields: ticket.missing_fields,
          claim_type: ticket.claim_type,
          description: ticket.description,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unbekannter Fehler" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data = (await response.json()) as FollowupEmail;
      setFollowupEmail(data);
      setEditedEmail({ subject: data.subject, body: data.body });
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : "E-Mail konnte nicht generiert werden");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendEmail = async () => {
    if (!editedEmail || !ticket.claimant_email) {
      setEmailError("Keine E-Mail-Adresse des Kunden vorhanden");
      return;
    }

    setIsSending(true);
    setEmailError(null);

    try {
      const backendUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      
      const response = await fetch(`${backendUrl}/followup/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient_email: ticket.claimant_email,
          subject: editedEmail.subject,
          body: editedEmail.body,
          ticket_id: ticket.id,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "E-Mail konnte nicht gesendet werden");
      }

      // Status auf "Warten auf Kunde" setzen
      await onStatusChange("waiting_for_customer");
      
      setEmailSuccess(`E-Mail wurde an ${ticket.claimant_email} gesendet`);
      setFollowupEmail(null);
      setEditedEmail(null);
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : "E-Mail konnte nicht gesendet werden");
    } finally {
      setIsSending(false);
    }
  };

  const handleCancelEmail = () => {
    setFollowupEmail(null);
    setEditedEmail(null);
    setEmailError(null);
    setEmailSuccess(null);
  };

  return (
    <div className="ticket-detail-overlay" onClick={onClose}>
      <div className="ticket-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-detail-header">
          <div className="ticket-detail-title">
            <h2>#{ticket.id} — {ticket.subject}</h2>
            {ticket.ticket_id && <span className="ticket-id-badge">{ticket.ticket_id}</span>}
            {ticket.has_missing_critical_fields && (
              <span className="critical-badge">⚠️ Kritische Felder fehlen</span>
            )}
          </div>
          <button className="close-btn" onClick={onClose} type="button">
            ✕
          </button>
        </div>

        <div className="ticket-detail-content">
          {/* Status & Priority Bar */}
          <div className="detail-section compact">
            <div className="detail-field">
              <label>Status</label>
              <select
                value={ticket.status}
                onChange={(e) => handleStatusChange(e.target.value as TicketStatus)}
                className="status-select"
              >
                {Object.entries(STATUS_LABELS).map(([status, label]) => (
                  <option key={status} value={status}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="detail-field">
              <label>Priorität</label>
              <span className={`priority-badge priority-${ticket.priority}`}>
                {PRIORITY_LABELS[ticket.priority]}
              </span>
            </div>
          </div>

          {/* LLM-Output Felder: Claimant Information */}
          <div className="detail-section">
            <h3>👤 Versicherungsnehmer</h3>
            <div className="detail-grid-2">
              <div className="detail-field">
                <label>Name</label>
                <span className={ticket.claimant_name ? "" : "empty"}>{ticket.claimant_name || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Email</label>
                <span className={ticket.claimant_email ? "" : "empty"}>{ticket.claimant_email || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Telefon</label>
                <span className={ticket.claimant_phone ? "" : "empty"}>{ticket.claimant_phone || "–"}</span>
              </div>
            </div>
          </div>

          {/* Claim Information */}
          <div className="detail-section">
            <h3>📋 Schadendaten</h3>
            <div className="detail-grid-2">
              <div className="detail-field">
                <label>Versicherung (Police)</label>
                <span className={ticket.policy_number ? "" : "empty"}>{ticket.policy_number || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Schadenstyp</label>
                <span className={ticket.claim_type ? "" : "empty"}>{ticket.claim_type || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Schadendatum</label>
                <span className={ticket.claim_date ? "" : "empty"}>{ticket.claim_date || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Unfalldatum</label>
                <span className={ticket.incident_date ? "" : "empty"}>{ticket.incident_date || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Unfallort</label>
                <span className={ticket.incident_location ? "" : "empty"}>{ticket.incident_location || "–"}</span>
              </div>
              <div className="detail-field">
                <label>Schadenshöhe</label>
                <span className={ticket.claim_amount ? "" : "empty"}>
                  {typeof ticket.claim_amount === "number" ? formatCurrency(ticket.claim_amount) : "–"}
                </span>
              </div>
            </div>
          </div>

          {/* Description & Details */}
          <div className="detail-section">
            <h3>📝 Zusammenfassung</h3>
            <p className="detail-summary">{ticket.summary}</p>
            {ticket.description && (
              <>
                <h4>Beschreibung</h4>
                <p className="detail-description">{ticket.description}</p>
              </>
            )}
          </div>

          {/* Action Items */}
          {ticket.action_items.length > 0 && (
            <div className="detail-section">
              <h3>✓ Action Items ({ticket.action_items.length})</h3>
              <div className="action-items-list">
                {ticket.action_items.map((action) => (
                  <div key={action.id} className="action-item-detail">
                    <div className="action-item-header">
                      <strong>{action.title}</strong>
                      <small className={`source-badge source-${action.suggested_by}`}>
                        {action.suggested_by.toUpperCase()}
                      </small>
                    </div>
                    {action.details && <p>{action.details}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing Fields */}
          {ticket.missing_fields.length > 0 && (
            <div className={`detail-section ${ticket.has_missing_critical_fields ? "critical-section" : ""}`}>
              <h3>📌 Fehlende Angaben ({ticket.missing_fields.length})</h3>
              <div className="missing-fields-list">
                {ticket.missing_fields.map((field) => (
                  <span key={field} className={`field-pill ${ticket.has_missing_critical_fields ? "critical" : ""}`}>
                    {field}
                  </span>
                ))}
              </div>

              {/* Followup Email Section */}
              <div className="followup-section">
                {emailError && <div className="followup-error">❌ {emailError}</div>}
                {emailSuccess && <div className="followup-success">✅ {emailSuccess}</div>}

                {!followupEmail && !emailSuccess && (
                  <button
                    className="followup-generate-btn"
                    onClick={handleGenerateFollowup}
                    disabled={isGenerating}
                  >
                    {isGenerating ? "⏳ Generiere E-Mail..." : "✉️ Nachfrage-E-Mail generieren"}
                  </button>
                )}

                {followupEmail && editedEmail && (
                  <div className="followup-preview">
                    <h4>📧 E-Mail Vorschau</h4>
                    <div className="followup-field">
                      <label>An:</label>
                      <span className={ticket.claimant_email ? "" : "empty"}>
                        {ticket.claimant_email || "Keine E-Mail-Adresse vorhanden"}
                      </span>
                    </div>
                    <div className="followup-field">
                      <label>Betreff:</label>
                      <input
                        type="text"
                        value={editedEmail.subject}
                        onChange={(e) => setEditedEmail({ ...editedEmail, subject: e.target.value })}
                        className="followup-subject-input"
                      />
                    </div>
                    <div className="followup-field">
                      <label>Nachricht:</label>
                      <textarea
                        value={editedEmail.body}
                        onChange={(e) => setEditedEmail({ ...editedEmail, body: e.target.value })}
                        className="followup-body-textarea"
                        rows={12}
                      />
                    </div>
                    <div className="followup-meta">
                      <small>Generiert von: {followupEmail.generated_by}</small>
                    </div>
                    <div className="followup-actions">
                      <button
                        className="followup-send-btn"
                        onClick={handleSendEmail}
                        disabled={isSending || !ticket.claimant_email}
                      >
                        {isSending ? "⏳ Sende..." : "📤 E-Mail senden"}
                      </button>
                      <button
                        className="followup-regenerate-btn"
                        onClick={handleGenerateFollowup}
                        disabled={isGenerating}
                      >
                        🔄 Neu generieren
                      </button>
                      <button className="followup-cancel-btn" onClick={handleCancelEmail}>
                        ✕ Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Next Steps */}
          {ticket.next_steps && (
            <div className="detail-section">
              <h3>➜ Nächste Schritte</h3>
              <p className="next-steps-text">{ticket.next_steps}</p>
            </div>
          )}

          {/* Metadata */}
          <div className="detail-section metadata">
            <h3>ℹ️ Informationen</h3>
            <div className="metadata-grid">
              <div className="metadata-item">
                <label>Erstellt</label>
                <span>{formatDate(ticket.created_at)}</span>
              </div>
              <div className="metadata-item">
                <label>Aktualisiert</label>
                <span>{formatDate(ticket.updated_at)}</span>
              </div>
              {ticket.created_timestamp && (
                <div className="metadata-item">
                  <label>LLM-Timestamp</label>
                  <span>{ticket.created_timestamp}</span>
                </div>
              )}
              {ticket.source_job_id && (
                <div className="metadata-item">
                  <label>Job-ID</label>
                  <span>#{ticket.source_job_id}</span>
                </div>
              )}
              {ticket.source_model_id && (
                <div className="metadata-item">
                  <label>LLM-Modell</label>
                  <span>{ticket.source_model_id}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicketDetail;
