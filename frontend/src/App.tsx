import { FormEvent, useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

interface ModelInfo {
  model_id: string;
  display_name: string;
  supports_streaming: boolean;
  is_default: boolean;
}

interface BackendResponse {
  model_id: string;
  model_display_name: string;
  result: Record<string, unknown>;
}

function App() {
  const [text, setText] = useState("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [loadingModels, setLoadingModels] = useState(true);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<BackendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modelError, setModelError] = useState<string | null>(null);

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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedModel) {
      setError("Kein Modell ausgewählt.");
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

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

      const data = (await result.json()) as BackendResponse;
      setResponse(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const submitDisabled =
    loading ||
    loadingModels ||
    text.trim().length === 0 ||
    !selectedModel ||
    models.length === 0;

  return (
    <div className="app-container">
      <header>
        <h1>LLM Adapter Pipeline</h1>
        <p>Schicke Freitexte an das FastAPI-Backend und erhalte eine Antwort.</p>
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
            {loading ? "Sende..." : "An Backend senden"}
          </button>
        </form>

        {loadingModels && (
          <p className="status">Modelle werden geladen…</p>
        )}

        {response && (
          <section className="result success">
            <h2>Backend-Antwort</h2>
            <p>
              <strong>Modell:</strong> {response.model_display_name}
            </p>
            <pre>{JSON.stringify(response.result, null, 2)}</pre>
          </section>
        )}

        {(error || modelError) && (
          <section className="result error">
            <h2>Fehler</h2>
            {modelError && <p>{modelError}</p>}
            {error && <p>{error}</p>}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
