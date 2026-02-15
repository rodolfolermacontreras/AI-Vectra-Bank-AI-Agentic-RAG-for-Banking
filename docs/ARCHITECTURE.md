# Architecture Diagrams -- AI Vectra Bank

## 1. System Architecture -- Component Topology

```mermaid
flowchart TB
    subgraph UserLayer["User Interface"]
        direction LR
        Query["Banking Query"]
        Report["Executive Report"]
    end

    subgraph Orchestration["Semantic Kernel Orchestration"]
        direction TB
        Orch["Sequential Orchestrator<br/>main_starter.py"]
    end

    subgraph AgentLayer["Specialized Banking Agents"]
        direction LR
        A1["Data Gatherer"]
        A2["Fraud Analyst"]
        A3["Loan Analyst"]
        A4["Support Specialist"]
        A5["Risk Analyst"]
        A6["Synthesis Coordinator"]
    end

    subgraph DataLayer["Data Sources"]
        direction LR
        SQL[("Azure SQL<br/>Database")]
        Chroma[("ChromaDB<br/>Vector Store")]
        Blob["Azure Blob<br/>Storage"]
    end

    subgraph AILayer["Azure AI Foundry"]
        direction LR
        GPT["GPT-4o<br/>Chat Completion"]
        Ada["text-embedding-ada-002<br/>Embeddings"]
    end

    subgraph Support["Supporting Infrastructure"]
        direction LR
        State["SharedState"]
        RAG["RAG Utilities"]
        Log["Logging"]
    end

    Query --> Orch
    Orch --> A1 --> A2 --> A3 --> A4 --> A5 --> A6
    A6 --> Report

    A1 -.-> SQL
    A1 -.-> Chroma
    A2 -.-> Chroma
    A3 -.-> Chroma
    A4 -.-> Chroma
    A5 -.-> Chroma

    Blob --> RAG --> Chroma

    A1 -.-> GPT
    A2 -.-> GPT
    A3 -.-> GPT
    A4 -.-> GPT
    A5 -.-> GPT
    A6 -.-> GPT

    Ada -.-> Chroma

    Orch -.-> State
    Orch -.-> Log
```

---

## 2. Data Flow and RAG Pipeline

```mermaid
flowchart LR
    subgraph Init["1. Initialization"]
        direction TB
        Q["User Query"] --> Intent["Identify Intent"]
        Intent --> Profile["Load Customer Profile"]
    end

    subgraph Gather["2. Data Gathering"]
        direction TB
        SQLFetch["Fetch from Azure SQL<br/>income, transactions"] --> Enrich["Enrich Profile"]
        BlobLoad["Load Policy Docs<br/>from Blob Storage"] --> RAGIngest["Ingest into ChromaDB<br/>via Ada-002 embeddings"]
    end

    subgraph Analysis["3. Multi-Agent Analysis"]
        direction TB
        FraudA["Fraud Analyst<br/>Risk Score + Indicators"]
        LoanA["Loan Analyst<br/>Eligibility + Terms"]
        SupportA["Support Specialist<br/>Relationship Assessment"]
        RiskA["Risk Analyst<br/>Enterprise Risk Score"]
        FraudA --> LoanA --> SupportA --> RiskA
    end

    subgraph Synthesis["4. Synthesis"]
        direction TB
        Synth["Synthesis Coordinator"]
        ExecReport["Executive Banking Report"]
        Synth --> ExecReport
    end

    Init --> Gather --> Analysis --> Synthesis
```

---

## 3. Agent Orchestration Logic

```mermaid
flowchart TD
    Start(["Banking Query"]) --> Orch{"Sequential<br/>Orchestrator"}

    Orch --> D1["Step 1: Data Gatherer<br/>Aggregate customer data"]
    D1 --> D2["Step 2: Fraud Analyst<br/>Detect anomalies"]
    D2 --> D3["Step 3: Loan Analyst<br/>Evaluate credit risk"]
    D3 --> D4["Step 4: Support Specialist<br/>Optimise experience"]
    D4 --> D5["Step 5: Risk Analyst<br/>Enterprise risk assessment"]
    D5 --> D6["Step 6: Synthesis Coordinator<br/>Executive report"]

    D6 --> Result(["EnhancedBankingReport"])

    D1 -. "context" .-> D2
    D2 -. "context" .-> D3
    D3 -. "context" .-> D4
    D4 -. "context" .-> D5
    D5 -. "context" .-> D6
```

---

## Component Summary

| Component | File | Responsibility |
|-----------|------|----------------|
| Orchestrator | `main_starter.py` | Sequential agent invocation, report assembly |
| Data Gatherer | Agent 1 | Customer profiling, data aggregation |
| Fraud Analyst | Agent 2 | Transaction anomaly detection |
| Loan Analyst | Agent 3 | Credit risk and loan evaluation |
| Support Specialist | Agent 4 | Customer experience optimisation |
| Risk Analyst | Agent 5 | Enterprise risk and compliance |
| Synthesis Coordinator | Agent 6 | Executive report generation |
| DataConnector | `data_connector.py` | Azure SQL Database queries |
| ChromaDBManager | `chroma_manager.py` | Vector store for RAG retrieval |
| BlobStorageConnector | `blob_connector.py` | Document storage and management |
| AzureEmbeddingFunction | `azure_embedding.py` | Azure Ada-002 embeddings for ChromaDB |
| RAG Utilities | `rag_utils.py` | Policy extraction and context preparation |
| SharedState | `shared_state.py` | Thread-safe state management |
| Pydantic Models | `models.py` | Data validation and report structure |
