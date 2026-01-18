import TicketBoard from "./components/TicketBoard";

const TICKETS_API_BASE_URL =
  import.meta.env.VITE_TICKETS_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:9000";

function App() {
  return (
    <div className="app-container">
      <header>
        <h1>Ticket-Dashboard</h1>
        <p>Eigenständiger Service für Schadenfälle und Action-Item-Übersichten.</p>
        <p className="ticket-api-hint">
          API: <code>{TICKETS_API_BASE_URL}</code>
        </p>
      </header>
      <main>
        <TicketBoard />
      </main>
    </div>
  );
}

export default App;
