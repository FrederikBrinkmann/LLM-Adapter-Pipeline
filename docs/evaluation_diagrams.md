# Evaluationsdiagramme: LLM-Pipeline

## 1. Faktorielles Design der Datengenerierung

```mermaid
flowchart TB
    subgraph Dim1["Dimension 1: Schadenstyp"]
        D1[Wasserschaden]
        D2[Autounfall]
        D3[Medizinisch]
        D4[Sturmschaden]
        D5[Diebstahl]
    end

    subgraph Dim2["Dimension 2: Emotionaler Ton"]
        T1[ruhig-strukturiert]
        T2[gestresst-panisch]
        T3[wütend-frustriert]
        T4[verwirrt-hilflos]
        T5[geschäftsmäßig]
    end

    subgraph Dim3["Dimension 3: Informationsvollständigkeit"]
        I1[vollständig]
        I2[teilweise]
        I3[minimal]
        I4[vage]
    end

    subgraph Result["Ergebnis"]
        Matrix["5 × 5 × 4 = 100 Testfälle"]
        Coverage[Vollständige Faktorenabdeckung]
    end

    Dim1 --> Matrix
    Dim2 --> Matrix
    Dim3 --> Matrix
    Matrix --> Coverage
```

---

## 2. Datengenerierungsprozess

```mermaid
flowchart LR
    subgraph Input["Eingabe"]
        Config[Konfiguration]
        Scenarios[Szenario-<br/>Beschreibungen]
    end

    subgraph Generation["Generierung"]
        Prompt[Prompt-<br/>Konstruktion]
        LLM[LLM-Aufruf<br/>GPT-4o]
        Raw[Rohe E-Mail]
    end

    subgraph QC["Qualitätskontrolle"]
        Length[Längenprüfung<br/>50-2000 Zeichen]
        Artifacts[Artefakt-<br/>Erkennung]
        Language[Sprach-<br/>Validierung]
        Decision{Akzeptiert?}
    end

    subgraph Output["Ausgabe"]
        Accept[Datensatz<br/>hinzufügen]
        Reject[Verwerfen &<br/>Neu generieren]
    end

    Config --> Prompt
    Scenarios --> Prompt
    Prompt --> LLM --> Raw
    Raw --> Length --> Artifacts --> Language --> Decision
    Decision -->|Ja| Accept
    Decision -->|Nein| Reject
    Reject -.->|Retry| Prompt

    style Decision fill:#fff3e0
    style Accept fill:#e8f5e9
    style Reject fill:#ffebee
```

---

## 3. Gold-Standard Erstellung

```mermaid
flowchart TB
    subgraph Phase1["Phase 1: Initiale Extraktion"]
        Emails[100 Test-E-Mails]
        Model[Referenzmodell<br/>GPT-5.2]
        Initial[Initiale<br/>Extraktionen]
    end

    subgraph Phase2["Phase 2: Manuelle Verifikation"]
        Review[Manuelle Prüfung<br/>jeder Extraktion]
        Correct[Korrekturen<br/>bei Bedarf]
        Annotate[Annotation<br/>fehlender Felder]
    end

    subgraph Phase3["Phase 3: Finalisierung"]
        Validate[Konsistenz-<br/>prüfung]
        Gold[Gold-Standard<br/>JSON]
    end

    Emails --> Model --> Initial
    Initial --> Review --> Correct --> Annotate
    Annotate --> Validate --> Gold

    style Gold fill:#fff9c4
```

---

## 4. Evaluationspipeline

```mermaid
sequenceDiagram
    autonumber
    participant DS as Datensatz
    participant GS as Gold-Standard
    participant Runner as Evaluation-Runner
    participant Model as LLM-Modell
    participant Metrics as Metrik-Berechnung
    participant Report as Report-Generator

    Runner->>DS: Lade E-Mails
    Runner->>GS: Lade Referenzdaten
    
    loop Für jedes Modell
        loop Für jede E-Mail
            Runner->>Model: Extraktion anfordern
            Note over Model: Messung Startzeit
            Model-->>Runner: Strukturierte Ausgabe
            Note over Model: Messung Endzeit
            Runner->>Metrics: Berechne Metriken
            Metrics-->>Runner: Einzelergebnis
        end
    end

    Runner->>Runner: Aggregiere Ergebnisse
    Runner->>Report: Generiere Bericht
    Report-->>Report: Markdown-Export
```

---

## 5. Metrik-Hierarchie

```mermaid
flowchart TB
    subgraph Top["Aggregierte Metriken"]
        Overall[Gesamt-Performance<br/>pro Modell]
    end

    subgraph Mid["Kategorisierte Metriken"]
        Structure[Strukturelle<br/>Qualität]
        Semantic[Semantische<br/>Qualität]
        Operational[Operative<br/>Qualität]
    end

    subgraph Detail["Einzelmetriken"]
        Schema[Schema-<br/>Validität]
        FieldAcc[Field<br/>Accuracy]
        CritAcc[Critical Field<br/>Accuracy]
        Precision[Missing Fields<br/>Precision]
        Recall[Missing Fields<br/>Recall]
        F1[Missing Fields<br/>F1-Score]
        Latency[Latenz<br/>in ms]
        ErrorRate[Fehler-<br/>Rate]
    end

    Overall --> Structure & Semantic & Operational
    
    Structure --> Schema
    Semantic --> FieldAcc & CritAcc
    Semantic --> Precision & Recall & F1
    Operational --> Latency & ErrorRate

    style Schema fill:#e3f2fd
    style FieldAcc fill:#e8f5e9
    style CritAcc fill:#e8f5e9
    style Precision fill:#fff3e0
    style Recall fill:#fff3e0
    style F1 fill:#fff3e0
    style Latency fill:#fce4ec
    style ErrorRate fill:#fce4ec
```

---

## 6. Vergleich Predicted vs. Gold-Standard

```mermaid
flowchart LR
    subgraph Predicted["LLM-Ausgabe"]
        P1[claimant_name: Max Müller]
        P2[policy_number: POL-2025-1234]
        P3[claim_type: damage]
        P4[claim_amount: 15000]
        P5[incident_date: 2023-10-05]
        P6[missing_fields: claim_date]
    end

    subgraph Gold["Gold-Standard"]
        G1[claimant_name: Max Müller]
        G2[policy_number: POL-2025-1234]
        G3[claim_type: damage]
        G4[claim_amount: 15000]
        G5[incident_date: 2023-10-05]
        G6[missing_fields: claim_date]
    end

    subgraph Comparison["Feldvergleich"]
        C1[✓ Match]
        C2[✓ Match]
        C3[✓ Match]
        C4[✓ Match]
        C5[✓ Match]
        C6[✓ Match]
    end

    P1 --> C1
    P2 --> C2
    P3 --> C3
    P4 --> C4
    P5 --> C5
    P6 --> C6

    G1 --> C1
    G2 --> C2
    G3 --> C3
    G4 --> C4
    G5 --> C5
    G6 --> C6

    style C1 fill:#c8e6c9
    style C2 fill:#c8e6c9
    style C3 fill:#c8e6c9
    style C4 fill:#c8e6c9
    style C5 fill:#c8e6c9
    style C6 fill:#c8e6c9
```

---

## 7. Missing Fields Metriken (Mengendiagramm-Darstellung)

```mermaid
flowchart TB
    subgraph Sets["Mengen"]
        direction LR
        Pred["Predicted Missing<br/>{A, B, C}"]
        Gold["Gold Missing<br/>{A, B, D}"]
    end

    subgraph Intersection["Schnittmenge"]
        TP["True Positives<br/>{A, B}<br/>TP = 2"]
    end

    subgraph Differences["Differenzen"]
        FP["False Positives<br/>{C}<br/>FP = 1"]
        FN["False Negatives<br/>{D}<br/>FN = 1"]
    end

    subgraph Metrics["Berechnete Metriken"]
        PrecCalc["Precision = TP/(TP+FP)<br/>= 2/3 = 0.67"]
        RecCalc["Recall = TP/(TP+FN)<br/>= 2/3 = 0.67"]
        F1Calc["F1 = 2×P×R/(P+R)<br/>= 0.67"]
    end

    Pred --> TP
    Gold --> TP
    Pred --> FP
    Gold --> FN
    
    TP --> PrecCalc
    FP --> PrecCalc
    TP --> RecCalc
    FN --> RecCalc
    PrecCalc --> F1Calc
    RecCalc --> F1Calc

    style TP fill:#c8e6c9
    style FP fill:#ffcdd2
    style FN fill:#ffcdd2
```

---

## 8. Informationsvollständigkeit und erwartete Ergebnisse

```mermaid
flowchart LR
    subgraph Levels["Info-Level"]
        L1[vollständig]
        L2[teilweise]
        L3[minimal]
        L4[vage]
    end

    subgraph Expected["Erwartete Eigenschaften"]
        E1["Alle kritischen Felder<br/>vorhanden"]
        E2["2-3 kritische Felder<br/>fehlen"]
        E3["Nur 1-2 konkrete<br/>Angaben"]
        E4["Keine spezifischen<br/>Daten"]
    end

    subgraph Impact["Auswirkung auf Metriken"]
        I1["Hohe Field Accuracy<br/>Wenige Missing Fields"]
        I2["Mittlere Accuracy<br/>Missing Fields erwartet"]
        I3["Niedrige Accuracy<br/>Viele Missing Fields"]
        I4["Sehr niedrige Accuracy<br/>Fast alle Felder fehlen"]
    end

    L1 --> E1 --> I1
    L2 --> E2 --> I2
    L3 --> E3 --> I3
    L4 --> E4 --> I4

    style L1 fill:#c8e6c9
    style L2 fill:#fff9c4
    style L3 fill:#ffe0b2
    style L4 fill:#ffcdd2
```

---

## 9. Modellvergleich (Radar-Darstellung konzeptionell)

```mermaid
flowchart TB
    subgraph Dimensions["Bewertungsdimensionen"]
        D1[Field Accuracy]
        D2[Critical Accuracy]
        D3[Schema Compliance]
        D4[Missing Fields F1]
        D5[Latenz<br/>invertiert]
        D6[Fehlerrate<br/>invertiert]
    end

    subgraph Models["Modelle"]
        M1[GPT-5.2]
        M2[GPT-4.1]
        M3[GPT-4o]
        M4[GPT-4.1-mini]
        M5[GPT-4o-mini]
    end

    subgraph Profile["Modellprofile"]
        P1["Höchste Genauigkeit<br/>Höhere Latenz"]
        P2["Ausgewogen<br/>Gute Balance"]
        P3["Etabliert<br/>Stabile Performance"]
        P4["Schnell<br/>Reduzierte Genauigkeit"]
        P5["Kostengünstig<br/>Basisperformance"]
    end

    M1 --> P1
    M2 --> P2
    M3 --> P3
    M4 --> P4
    M5 --> P5

    D1 & D2 & D3 & D4 & D5 & D6 --> Models
```

---

## 10. Evaluationsablauf (Zeitliche Sicht)

```mermaid
gantt
    title Evaluationsprozess
    dateFormat X
    axisFormat %s
    
    section Vorbereitung
    Datensatz laden           :a1, 0, 1
    Gold-Standard laden       :a2, 1, 2
    Modelle initialisieren    :a3, 2, 3
    
    section Modell 1
    E-Mail 1-25               :b1, 3, 8
    E-Mail 26-50              :b2, 8, 13
    E-Mail 51-75              :b3, 13, 18
    E-Mail 76-100             :b4, 18, 23
    
    section Modell 2
    E-Mail 1-25               :c1, 23, 28
    E-Mail 26-50              :c2, 28, 33
    E-Mail 51-75              :c3, 33, 38
    E-Mail 76-100             :c4, 38, 43
    
    section Abschluss
    Metriken aggregieren      :d1, 43, 44
    Report generieren         :d2, 44, 45
```

---

## Legende

| Symbol | Bedeutung |
|--------|-----------|
| Rechteck | Prozessschritt / Komponente |
| Raute | Entscheidung |
| Zylinder | Datenspeicher |
| Grün (fill:#c8e6c9/#e8f5e9) | Erfolg / Korrekt |
| Rot (fill:#ffcdd2/#ffebee) | Fehler / Inkorrekt |
| Gelb (fill:#fff9c4/#fff3e0) | Warnung / Teilweise |
| Blau (fill:#e3f2fd) | Strukturelle Dimension |

---

## Verwendung

Diese Diagramme ergänzen das Evaluationskapitel (Kapitel 5) der Thesis und können wie folgt referenziert werden:

| Diagramm | Abschnitt | Verwendung |
|----------|-----------|------------|
| 1. Faktorielles Design | 5.2.2 | Visualisierung der Variationsdimensionen |
| 2. Datengenerierung | 5.2.3 | Prozess der E-Mail-Erzeugung |
| 3. Gold-Standard | 5.3.1 | Erstellung der Referenzdaten |
| 4. Evaluationspipeline | 5.6.1 | Gesamtablauf der Evaluation |
| 5. Metrik-Hierarchie | 5.4 | Übersicht der Metriken |
| 6. Vergleich | 5.4.2 | Feldweiser Vergleich |
| 7. Missing Fields | 5.4.4 | Precision/Recall-Berechnung |
| 8. Info-Levels | 5.2.4 | Zusammenhang Vollständigkeit/Ergebnis |
| 9. Modellvergleich | 5.5 | Modellcharakteristika |
| 10. Zeitablauf | 5.6.1 | Sequentieller Prozess |

**Rendering**: Mermaid Live Editor (https://mermaid.live) oder VS Code mit Mermaid-Extension
