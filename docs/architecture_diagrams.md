# Architekturdiagramme: Modellagnostische LLM-Pipeline

## 1. Systemübersicht (Komponentendiagramm)

```mermaid
flowchart TB
    subgraph Eingabe["Eingabeschicht"]
        E1[E-Mail-Quelle]
        E2[Web-Frontend]
        E3[API-Client]
    end

    subgraph Core["Kernpipeline"]
        API[REST-API]
        Queue[(Job-Speicher)]
        Worker[Worker-Prozess]
        
        subgraph Adapter["Adapter-Schicht"]
            direction TB
            Registry[Modell-Registry]
            PA[Provider A]
            PB[Provider B]
            PN[Provider N]
        end
    end

    subgraph External["Externe Dienste"]
        LLM1[Cloud-LLM]
        LLM2[Lokale Inferenz]
    end

    subgraph Output["Ausgabeschicht"]
        Target[Zielsystem]
        UI[Status-Dashboard]
    end

    E1 & E2 & E3 -->|Text + Modellwahl| API
    API -->|Job anlegen| Queue
    Worker -->|Job abholen| Queue
    Worker --> Registry
    Registry --> PA & PB & PN
    PA --> LLM1
    PB --> LLM2
    LLM1 & LLM2 -->|Strukturierte Antwort| Worker
    Worker -->|Ergebnis speichern| Queue
    API -->|Submit| Target
    API --> UI
```

---

## 2. Datenfluss (Sequenzdiagramm)

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API
    participant JobStore as Job-Speicher
    participant Worker
    participant Registry as Modell-Registry
    participant Provider
    participant LLM
    participant Target as Zielsystem

    Client->>API: POST /ingest (Text, Modell-ID)
    API->>Registry: Modell validieren
    Registry-->>API: Modell bestätigt
    API->>JobStore: Job anlegen (Status: wartend)
    API-->>Client: Job-ID, Status

    loop Polling
        Client->>API: GET /jobs/{id}
        API->>JobStore: Status abfragen
        JobStore-->>API: Aktueller Status
        API-->>Client: Status-Antwort
    end

    Worker->>JobStore: Nächsten Job abholen
    JobStore-->>Worker: Job (Status → in Bearbeitung)
    Worker->>Registry: Adapter für Modell
    Registry-->>Worker: Konfigurierter Adapter
    Worker->>Provider: Anfrage konstruieren
    Provider->>LLM: HTTP-Request
    LLM-->>Provider: JSON-Antwort
    Provider-->>Worker: Geparste Struktur
    Worker->>JobStore: Ergebnis speichern (Status: abgeschlossen)

    Client->>API: POST /jobs/{id}/submit
    API->>JobStore: Job + Ergebnis laden
    API->>API: Payload transformieren & validieren
    API->>Target: POST /tickets
    Target-->>API: Ticket-Referenz
    API->>JobStore: Referenz speichern (Status: übermittelt)
    API-->>Client: Erfolgsbestätigung
```

---

## 3. Job-Lebenszyklus (Zustandsdiagramm)

```mermaid
stateDiagram-v2
    [*] --> Wartend: Job angelegt

    Wartend --> InBearbeitung: Worker übernimmt
    
    InBearbeitung --> Abgeschlossen: LLM-Extraktion erfolgreich
    InBearbeitung --> Gescheitert: Fehler bei Verarbeitung
    
    Abgeschlossen --> Übermittelt: Submit an Zielsystem
    Abgeschlossen --> SubmitFehlgeschlagen: Zielsystem-Fehler
    
    Gescheitert --> [*]: Terminal
    Übermittelt --> [*]: Terminal
    SubmitFehlgeschlagen --> Übermittelt: Retry erfolgreich

    note right of Wartend
        Persistiert mit Eingabetext
        und gewähltem Modell
    end note

    note right of InBearbeitung
        Exklusiver Zugriff
        durch einen Worker
    end note

    note right of Abgeschlossen
        Strukturiertes Ergebnis
        gespeichert
    end note

    note right of Übermittelt
        Ticket-Referenz und
        Antwort gespeichert
    end note
```

---

## 4. Adapter-Muster (Strukturdiagramm)

```mermaid
classDiagram
    direction TB
    
    class AdapterSchnittstelle {
        <<interface>>
        +generate_structured(text) dict
    }
    
    class ModellKonfiguration {
        +modell_id: string
        +anzeigename: string
        +provider: string
        +parameter: dict
    }
    
    class ProviderHandler {
        <<interface>>
        +build_request(prompt, model, params) RequestSpec
        +parse_response(data, model) dict
        +format_http_error(error) string
    }
    
    class CloudProvider {
        +api_key: string
        +base_url: string
    }
    
    class LokaleInferenz {
        +host: string
        +port: int
    }
    
    class ModellRegistry {
        +get_model(id) Adapter
        +list_models() list
        +supports_provider(name) bool
    }

    AdapterSchnittstelle <|.. KonkreterAdapter
    KonkreterAdapter --> ModellKonfiguration: nutzt
    KonkreterAdapter --> ProviderHandler: delegiert an
    ProviderHandler <|.. CloudProvider
    ProviderHandler <|.. LokaleInferenz
    ModellRegistry --> ModellKonfiguration: verwaltet
    ModellRegistry --> KonkreterAdapter: erzeugt
```

---

## 5. Validierungsschichten (Schichtendiagramm)

```mermaid
flowchart TB
    subgraph LLM["LLM-Ausgabe"]
        Raw[Rohe Antwort]
    end

    subgraph V1["Schicht 1: Strukturvalidierung"]
        JSON[JSON-Parsing]
        Schema[Schema-Konformität]
    end

    subgraph V2["Schicht 2: Normalisierung"]
        Types[Typkonvertierung]
        Defaults[Standardwerte]
        Format[Formatvereinheitlichung]
    end

    subgraph V3["Schicht 3: Semantische Prüfung"]
        Critical[Kritische Felder prüfen]
        Missing[Fehlende Felder markieren]
    end

    subgraph V4["Schicht 4: Geschäftslogik"]
        Derive[Werte ableiten]
        Enrich[Payload anreichern]
    end

    subgraph Output["Ausgabe"]
        Ticket[Ticket-Payload]
        Flags[Qualitätsflags]
    end

    Raw --> JSON --> Schema
    Schema --> Types --> Defaults --> Format
    Format --> Critical --> Missing
    Missing --> Derive --> Enrich
    Enrich --> Ticket & Flags
```

---

## 6. Entkopplungsarchitektur (Deployment-Sicht)

```mermaid
flowchart LR
    subgraph Zone1["Eingangszone"]
        Ingest[Ingest-Endpunkt]
    end

    subgraph Zone2["Verarbeitungszone"]
        DB[(Persistenz)]
        W1[Worker 1]
        W2[Worker N]
    end

    subgraph Zone3["LLM-Zone"]
        Cloud[Cloud-APIs]
        Local[Lokale Modelle]
    end

    subgraph Zone4["Integrationszone"]
        Submit[Submit-Endpunkt]
        Target[Zielsystem]
    end

    Ingest -->|async| DB
    DB <-->|poll| W1 & W2
    W1 & W2 <-->|HTTP| Cloud & Local
    DB <--> Submit
    Submit -->|HTTP| Target

    style Zone1 fill:#e1f5fe
    style Zone2 fill:#fff3e0
    style Zone3 fill:#f3e5f5
    style Zone4 fill:#e8f5e9
```

---

## Legende

| Symbol | Bedeutung |
|--------|-----------|
| Rechteck | Komponente / Prozess |
| Zylinder | Persistenter Speicher |
| Gestrichelte Linie | Asynchrone Kommunikation |
| Durchgezogene Linie | Synchrone Kommunikation |
| Subgraph | Logische Gruppierung / Zone |

---

## Verwendung

Diese Diagramme sind in Mermaid-Syntax verfasst und können gerendert werden in:
- GitHub/GitLab Markdown-Vorschau
- VS Code mit Mermaid-Extension
- Mermaid Live Editor (https://mermaid.live)
- Export als SVG/PNG für LaTeX-Einbindung
