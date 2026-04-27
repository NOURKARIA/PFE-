# Mermaid Diagrams For The Project

This file contains a complete Mermaid pack for the current codebase (`FastAPI + NLP + Vision + Playwright + Reporting`).

## 1) System Context

```mermaid
flowchart LR
    U[User or QA Engineer]
    API[FastAPI Backend]
    WEB[Target Websites]
    NLP[NLP Models<br/>DistilBERT Intent + NER]
    VISION[Vision Stack<br/>YOLO + OpenCV + OCR]
    PW[Playwright Runtime]
    REP[Reports Storage<br/>reports/json + reports/html + screenshots]

    U -->|HTTP Requests| API
    API --> NLP
    API --> PW
    PW --> WEB
    API --> VISION
    API --> REP
    VISION --> API
    NLP --> API
    API -->|JSON or HTML Response| U
```

## 2) Backend Component Diagram

```mermaid
flowchart TB
    subgraph API["app/api"]
      H[health.py]
      NLPAPI[nlp_parsing.py]
      MAPAPI[semantic_mapping.py]
      DETAPI[ql_detection.py]
      SEGAPI[segmentation.py]
      GENAPI[test_generation.py]
      EXEAPI[test_execution.py]
      REPAPI[reporting.py]
    end

    subgraph Services["app/services"]
      NLPSVC[nlp_service.py]
      MAPSVC[mapping_service.py]
      VISSVC[vision_service.py]
      SEGSVC[segmentation_service.py]
      GENSVC[generator_service.py]
      EXESVC[executor_service.py]
      REPSVC[report_service.py]
    end

    subgraph ModelsAndUtils["app/models + app/utils + nlp"]
      ICLS[nlp/intent_classifier.py]
      ENER[nlp/entity_extractor.py]
      YOLOM[models/yolo_model.py]
      GHP[utils/gherkin_parser.py]
      IMG[utils/image_processing.py]
      SIM[utils/text_similarity.py]
    end

    NLPAPI --> NLPSVC
    MAPAPI --> MAPSVC
    DETAPI --> VISSVC
    SEGAPI --> SEGSVC
    GENAPI --> NLPSVC
    GENAPI --> GENSVC
    EXEAPI --> EXESVC
    EXEAPI --> REPSVC
    REPAPI --> REPSVC

    NLPSVC --> GHP
    NLPSVC --> ICLS
    NLPSVC --> ENER
    NLPSVC --> MAPSVC
    VISSVC --> YOLOM
    VISSVC --> IMG
    VISSVC --> SIM
    EXESVC --> NLPSVC
    EXESVC --> GENSVC
    EXESVC --> VISSVC
```

## 3) API Endpoints Map

```mermaid
flowchart LR
    C[Client]
    C --> E1[GET /health]
    C --> E2[POST /api/ia/parse-gherkin]
    C --> E3[POST /api/ia/semantic-mapping]
    C --> E4[POST /api/ia/detect-ui]
    C --> E5[POST /api/ia/segment]
    C --> E6[POST /api/ia/generate-test]
    C --> E7[POST /api/ia/execute-test]
    C --> E8[GET /api/ia/reports]
    C --> E9[GET /api/ia/reports/{execution_id}]
    C --> E10[GET /api/ia/reports/{execution_id}/summary]
```

## 4) NLP Parsing Pipeline

```mermaid
flowchart TD
    A[Raw Gherkin Text] --> B[parse_gherkin_text]
    B --> C{Scenarios and Steps Found?}
    C -- No --> D[Return status=error]
    C -- Yes --> E[For each step]
    E --> F[EntityExtractor.extract_entities]
    E --> G[IntentClassifier.predict_intent]
    F --> H[Build nlp_result payload]
    G --> H
    H --> I[MappingService.map_to_action]
    I --> J[Build ActionStepResponse]
    J --> K[Build GherkinParseResponse]
    K --> L[Return status=success]
```

## 5) Semantic Mapping Logic

```mermaid
flowchart TD
    A[Input: intent, target, values, element_type]
    A --> B{Intent}
    B -->|NAVIGATION| M1[navigate]
    B -->|ACTION_CLICK| M2[click]
    B -->|ACTION_TYPE| M3[input]
    B -->|VERIFICATION| M4[assert]
    B -->|UNKNOWN| M5[manual_check]

    A --> C[_build_selector_candidates]
    C --> D{text selectors}
    C --> E{element_type}
    E -->|button| F[role/button/xpath selectors]
    E -->|input| G[input placeholder/name/id/xpath]
    E -->|link| H[a selectors]
    E -->|other| I[no extra selectors]

    D --> J[selector_candidates]
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K[First selector as primary]
    K --> L[Output ActionStep]
```

## 6) Vision Detection and OCR Pipeline

```mermaid
flowchart TD
    A[Input Screenshot Path] --> B[YOLOModelWrapper.predict]
    B --> C{Model Available?}
    C -- No --> D[Return empty list]
    C -- Yes --> E[Build element per box]
    E --> F[Label, confidence, box, center]
    F --> G{include_ocr or target_text?}
    G -- No --> H[strategy=yolo]
    G -- Yes --> I[crop_element]
    I --> J[summarize_patch]
    J --> K[OCR text + edge features]
    K --> L[TextSimilarity.is_match]
    L --> M[strategy=yolo+opencv+ocr]
    H --> N[refine_yolo_labels]
    M --> N
    N --> O[_merge_overlapping_elements]
    O --> P[_sort_elements]
    P --> Q[Return ranked detections]
```

## 7) Execute-Test Self-Healing Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API as /api/ia/execute-test
    participant Exec as ExecutorService
    participant NLP as NLPService
    participant Gen as GeneratorService
    participant Browser as Playwright Page
    participant Vision as VisionService
    participant Reports as ReportService

    Client->>API: POST url + step
    API->>Exec: start_session(url)
    Exec->>Browser: launch + goto(url)
    API->>Exec: execute_gherkin_step(step)
    Exec->>NLP: process_step(step)
    NLP-->>Exec: action_data
    Exec->>Gen: generate_and_execute(action_data)

    alt Plan A success
        Gen-->>Exec: success + plan_a_selector_playwright
    else Plan A fails
        Gen--x Exec: exception or error
        Exec->>Browser: take fallback screenshot
        Exec->>Vision: detect_and_read(target_text)
        Vision-->>Exec: matched element center
        Exec->>Browser: click or type by coordinates
        Exec-->>Exec: result plan_b_yolo_ocr
    end

    Exec->>Browser: take step screenshot
    Exec->>Reports: save_both_reports(execution_report)
    Reports-->>API: json/html paths
    API-->>Client: status completed + result + report paths
```

## 8) Step Execution State Machine

```mermaid
stateDiagram-v2
    [*] --> SessionStarted
    SessionStarted --> StepReceived
    StepReceived --> NLPProcessed
    NLPProcessed --> PlanA

    PlanA --> StepPassed: Selector execution success
    PlanA --> PlanB: Selector execution failed

    PlanB --> StepPassed: Vision fallback success
    PlanB --> StepFailed: Vision fallback failed

    StepPassed --> Reported
    StepFailed --> Reported
    Reported --> [*]
```

## 9) Reporting Lifecycle

```mermaid
sequenceDiagram
    participant Exec as ExecutorService
    participant RS as ReportService
    participant FS as File System
    participant API as reporting.py
    participant Client

    Exec->>RS: get_execution_report()
    Exec->>RS: save_both_reports(report)
    RS->>RS: generate_json_report()
    RS->>FS: write reports/json/report_<id>_<ts>.json
    RS->>RS: generate_html_report()
    RS->>FS: write reports/html/report_<id>_<ts>.html

    Client->>API: GET /api/ia/reports
    API->>RS: list_json_reports()
    RS-->>API: report file list
    API-->>Client: summaries

    Client->>API: GET /api/ia/reports/{execution_id}
    API->>RS: load_json_report(path)
    RS-->>API: ExecutionReport
    API-->>Client: json payload or rendered html content
```

## 10) Core Data Model (Schemas)

```mermaid
classDiagram
    class GherkinParseRequest {
      +string gherkin_text
    }
    class ActionParameters {
      +string value
      +string identifier
      +string element_type
    }
    class ActionStepResponse {
      +string step_text
      +string intent
      +string playwright_method
      +ActionParameters parameters
      +float confidence_score
    }
    class ScenarioResponse {
      +string scenario_name
      +List~ActionStepResponse~ actions
    }
    class GherkinParseResponse {
      +string feature_name
      +List~ScenarioResponse~ scenarios
      +string status
    }

    class ActionStep {
      +string step_text
      +string intent
      +string playwright_method
      +string selector
      +string value
      +dict metadata
    }

    class UIElement {
      +string label
      +float confidence
      +List~float~ box
      +List~float~ center
      +string text
      +bool is_match
      +string strategy
    }

    class ReportStep {
      +string step_text
      +string action
      +string selector
      +string plan_used
      +string status
      +float duration
      +string screenshot_path
    }
    class ReportSummary {
      +int total_steps
      +int passed_steps
      +int failed_steps
      +int plan_a_steps
      +int plan_b_steps
      +float duration
    }
    class ExecutionReport {
      +string execution_id
      +string status
      +datetime started_at
      +datetime finished_at
      +float duration
      +List~ReportStep~ steps
      +ReportSummary summary
      +List~string~ screenshots
    }

    GherkinParseResponse "1" --> "*" ScenarioResponse
    ScenarioResponse "1" --> "*" ActionStepResponse
    ActionStepResponse "1" --> "1" ActionParameters
    ExecutionReport "1" --> "*" ReportStep
    ExecutionReport "1" --> "1" ReportSummary
```

## 11) Deployment Diagram (Docker Compose)

```mermaid
flowchart LR
    subgraph Host["Developer or Server Host"]
      subgraph Docker["Docker Compose"]
        APP[ai-agent container<br/>uvicorn app.main:app]
      end
      M1[./reports]
      M2[./trained_models]
    end

    EXT[Client or Browser]

    EXT -->|HTTP 8000| APP
    APP <-->|bind mount| M1
    APP <-->|bind mount| M2
```

## 12) Tests and Benchmark Coverage

```mermaid
flowchart TB
    T0[pytest tests]

    subgraph UnitAndServiceTests
      T1[test_nlp_service.py]
      T2[test_mapping_service.py]
      T3[test_vision_service.py]
      T4[test_generator_service.py]
      T5[test_executor_service.py]
      T6[test_report_service.py]
      T7[test_text_similarity.py]
    end

    subgraph LiveBenchmarkOptIn
      T8[test_inference_unseen_sites.py]
      S1[Wikipedia]
      S2[Python.org]
      S3[GitHub Login]
      ENV[RUN_LIVE_INFERENCE=1]
    end

    T0 --> T1
    T0 --> T2
    T0 --> T3
    T0 --> T4
    T0 --> T5
    T0 --> T6
    T0 --> T7
    T0 --> T8
    ENV --> T8
    T8 --> S1
    T8 --> S2
    T8 --> S3
```

## 13) Inference Benchmark Sequence (Unseen Sites)

```mermaid
sequenceDiagram
    participant Pytest
    participant API as /api/ia/execute-test
    participant Site as Unseen Website
    participant Engine as Plan A and Plan B
    participant Reports

    Pytest->>API: POST (url, step)
    API->>Site: open target URL
    API->>Engine: execute step
    alt Selector works
      Engine-->>API: plan_a_selector_playwright
    else Selector fails
      Engine-->>API: plan_b_yolo_ocr
    end
    API->>Reports: persist json and html
    API-->>Pytest: status completed + plan_used + execution_id
```

