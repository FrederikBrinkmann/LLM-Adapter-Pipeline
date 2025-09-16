import { FormEvent, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

interface BackendResponse {
  message: string;
  length: number;
}

function App() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<BackendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await fetch(`${API_BASE_URL}/ingest/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
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
          <button type="submit" disabled={loading || text.trim().length === 0}>
            {loading ? "Sende..." : "An Backend senden"}
          </button>
        </form>

        {response && (
          <section className="result success">
            <h2>Backend-Antwort</h2>
            <pre>{JSON.stringify(response, null, 2)}</pre>
          </section>
        )}

        {error && (
          <section className="result error">
            <h2>Fehler</h2>
            <p>{error}</p>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
