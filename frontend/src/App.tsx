import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

interface ModelInfo {
  model_id: string;
  display_name: string;
  supports_streaming: boolean;
  is_default: boolean;
}

type JobStatus = "queued" | "in_progress" | "completed" | "failed";

interface IngestResponse {
  job_id: number;
  model_id: string;
  model_display_name: string;
  status: JobStatus;
  created_at: string;
}

interface JobDetail {
  id: number;
  model_id: string;
  model_display_name: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  submitted_at: string | null;
  result_json: Record<string, unknown> | null;
  error_message: string | null;
  target_status: string | null;
  target_reference: string | null;
}

interface JobSubmitResponse {
  job: JobDetail;
  target_response?: Record<string, unknown> | null;
}

const TERMINAL_STATUSES: JobStatus[] = ["completed", "failed"];

function App() {
  const [text, setText] = useState("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [loadingModels, setLoadingModels] = useState(true);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<JobDetail | null>(null);
  const [targetResponse, setTargetResponse] = useState<Record<string, unknown> | null>(null);
  const [jobPolling, setJobPolling] = useState(false);

  const hasTerminalStatus = useMemo(
    () => (status: JobStatus | undefined | null) =>
      !!status && TERMINAL_STATUSES.includes(status),
    []
  );

  useEffect(() => {
    const loadModels = async () => {
      setLoadingModels(true);
      setModelError(null);
      try {
        const result = await fetch(`${API_BASE_URL}/models/`);
        if (!result.ok) {
          throw new Error(`Backend responded with status ${result.status}`);
        }
        const data = (await result.json()) as ModelInfo[];
        setModels(data);
        if (data.length > 0) {
          const defaultModel = data.find((model) => model.is_default) ?? data[0];
          setSelectedModel(defaultModel.model_id);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setModelError(message);
      } finally {
        setLoadingModels(false);
      }
    };

    void loadModels();
  }, []);

  const fetchJob = useCallback(async (jobId: number) => {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!response.ok) {
      throw new Error(`Job request failed with status ${response.status}`);
    }
    return (await response.json()) as JobDetail;
  }, []);

  useEffect(() => {
    if (!currentJob) {
      setJobPolling(false);
      return;
    }

    if (hasTerminalStatus(currentJob.status)) {
      setJobPolling(false);
      return;
    }

    let cancelled = false;
    setJobPolling(true);

    const poll = async () => {
      try {
        const job = await fetchJob(currentJob.id);
        if (cancelled) {
          return;
        }
        setCurrentJob(job);
        if (!hasTerminalStatus(job.status)) {
          timer = window.setTimeout(poll, 1500);
        } else {
          setJobPolling(false);
        }
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "Unknown error";
          setJobError(message);
          setJobPolling(false);
        }
      }
    };

    let timer = window.setTimeout(poll, 1000);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [currentJob, fetchJob, hasTerminalStatus]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedModel) {
      setError("Kein Modell ausgewählt.");
      return;
    }

    setLoading(true);
    setError(null);
    setJobError(null);
    setTargetResponse(null);
    setCurrentJob(null);

    try {
      const result = await fetch(`${API_BASE_URL}/ingest/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text, model_id: selectedModel }),
      });

      if (!result.ok) {
        throw new Error(`Backend responded with status ${result.status}`);
      }

      const data = (await result.json()) as IngestResponse;
      setCurrentJob({
        id: data.job_id,
        model_id: data.model_id,
        model_display_name: data.model_display_name,
        status: data.status,
        created_at: data.created_at,
        started_at: null,
        completed_at: null,
        submitted_at: null,
        result_json: null,
        error_message: null,
        target_status: null,
        target_reference: null,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const refreshJob = useCallback(async () => {
    if (!currentJob) {
      return;
    }
    try {
      const job = await fetchJob(currentJob.id);
      setCurrentJob(job);
      setJobError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setJobError(message);
    }
  }, [currentJob, fetchJob]);

  const handleSubmitToTarget = useCallback(async () => {
    if (!currentJob) {
      return;
    }
    setSubmitLoading(true);
    setJobError(null);
    setTargetResponse(null);

    try {
      const response = await fetch(`${API_BASE_URL}/jobs/${currentJob.id}/submit`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`Submit request failed with status ${response.status}`);
      }
      const data = (await response.json()) as JobSubmitResponse;
      setCurrentJob(data.job);
      setTargetResponse(data.target_response ?? null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setJobError(message);
    } finally {
      setSubmitLoading(false);
    }
  }, [currentJob]);

  const submitDisabled =
    loading ||
    loadingModels ||
    text.trim().length === 0 ||
    !selectedModel ||
    models.length === 0;

  const canSubmitToTarget =
    currentJob?.status === "completed" &&
    !submitLoading &&
    (currentJob?.target_status === null || currentJob?.target_status === "failed");

  return (
    <div className="app-container">
      <header>
        <h1>LLM Adapter Pipeline</h1>
        <p>Schicke Freitexte an das FastAPI-Backend, verarbeite sie mit einem Modell und verfolge den Status.</p>
      </header>

      <main>
        <form onSubmit={handleSubmit}>
          <label htmlFor="payload">Freitext / E-Mail-Inhalt</label>
          <textarea
            id="payload"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Füge hier deinen Text ein..."
            rows={10}
          />

          <label htmlFor="model">LLM-Modell</label>
          <select
            id="model"
            value={selectedModel}
            onChange={(event) => setSelectedModel(event.target.value)}
            disabled={loadingModels || models.length === 0}
          >
            {models.map((model) => (
              <option key={model.model_id} value={model.model_id}>
                {model.display_name}
              </option>
            ))}
          </select>

          <button type="submit" disabled={submitDisabled}>
            {loading ? "Sende..." : "Job erstellen"}
          </button>
        </form>

        {loadingModels && <p className="status">Modelle werden geladen…</p>}

        {currentJob && (
          <section className="result info">
            <div className="job-header">
              <h2>Job #{currentJob.id}</h2>
              <button className="secondary" type="button" onClick={refreshJob} disabled={jobPolling || submitLoading}>
                Aktualisieren
              </button>
            </div>
            <dl className="job-meta">
              <div>
                <dt>Status</dt>
                <dd className={`status-pill status-${currentJob.status}`}>
                  {currentJob.status.replace("_", " ")}
                  {jobPolling && " • aktualisiert"}
                </dd>
              </div>
              <div>
                <dt>Modell</dt>
                <dd>{currentJob.model_display_name}</dd>
              </div>
              <div>
                <dt>Erstellt</dt>
                <dd>{new Date(currentJob.created_at).toLocaleString()}</dd>
              </div>
              {currentJob.started_at && (
                <div>
                  <dt>Gestartet</dt>
                  <dd>{new Date(currentJob.started_at).toLocaleString()}</dd>
                </div>
              )}
              {currentJob.completed_at && (
                <div>
                  <dt>Fertig</dt>
                  <dd>{new Date(currentJob.completed_at).toLocaleString()}</dd>
                </div>
              )}
              {currentJob.submitted_at && (
                <div>
                  <dt>Ticketsystem</dt>
                  <dd>
                    {currentJob.target_status ?? "gesendet"}
                    {currentJob.target_reference ? ` (#${currentJob.target_reference})` : ""}
                  </dd>
                </div>
              )}
            </dl>

            {currentJob.error_message && (
              <div className="result error">
                <h3>Fehler</h3>
                <p>{currentJob.error_message}</p>
              </div>
            )}

            {currentJob.result_json && (
              <div className="result success">
                <h3>LLM Ergebnis</h3>
                <pre>{JSON.stringify(currentJob.result_json, null, 2)}</pre>
              </div>
            )}

            {canSubmitToTarget && (
              <button
                type="button"
                onClick={handleSubmitToTarget}
                className="primary"
                disabled={submitLoading}
              >
                {submitLoading ? "Übermittle…" : "An Ticketsystem senden"}
              </button>
            )}

            {targetResponse && (
              <div className="result neutral">
                <h3>Antwort des Ticketsystems</h3>
                <pre>{JSON.stringify(targetResponse, null, 2)}</pre>
              </div>
            )}
          </section>
        )}

        {(error || modelError || jobError) && (
          <section className="result error">
            <h2>Fehler</h2>
            {modelError && <p>{modelError}</p>}
            {error && <p>{error}</p>}
            {jobError && <p>{jobError}</p>}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
