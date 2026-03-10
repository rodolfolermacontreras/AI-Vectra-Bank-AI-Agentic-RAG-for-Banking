# AI Vectra Bank -- Banking Multi-Agent RAG System

Udacity "Microsoft Azure AI Foundry" Nanodegree -- Project 4

## Overview

A multi-agent banking intelligence system that orchestrates six specialised AI
agents using Microsoft Semantic Kernel to process complex banking queries. The
system uses sequential orchestration where each agent builds on the findings of
the previous one, producing a comprehensive banking analysis report.

## Architecture

### System Topology

```mermaid
flowchart TB
    subgraph UI["User Interface Layer"]
        direction LR
        StreamlitApp["Streamlit Web App<br/><i>app.py</i>"]
        CLI["CLI Entry Point<br/><i>main_starter.py --demo/--all/--test</i>"]
    end

    subgraph Orchestration["Semantic Kernel Orchestration Layer"]
        direction TB
        Orch["SequentialOrchestration<br/><i>EnhancedBankingSequentialOrchestration</i>"]
        SharedState["SharedState<br/><i>Thread-safe context</i>"]
        Orch --- SharedState
    end

    subgraph AgentLayer["Specialized Banking Agent Layer"]
        direction LR
        A1["1. Data Gatherer"]
        A2["2. Fraud Analyst"]
        A3["3. Loan Analyst"]
        A4["4. Support Specialist"]
        A5["5. Risk Analyst"]
        A6["6. Synthesis Coordinator"]
    end

    subgraph DataLayer["Data Source Layer"]
        direction LR
        SQL[("Azure SQL<br/>Database<br/><i>data_connector.py</i>")]
        Chroma[("ChromaDB<br/>Vector Store<br/><i>chroma_manager.py</i>")]
        Blob["Azure Blob / Local<br/>Storage<br/><i>blob_connector.py</i>"]
    end

    subgraph AILayer["Azure AI Foundry"]
        direction LR
        GPT["GPT-4o<br/>Chat Completion"]
        Ada["text-embedding-ada-002<br/>1536-dim Embeddings"]
    end

    StreamlitApp --> Orch
    CLI --> Orch
    Orch --> A1 --> A2 --> A3 --> A4 --> A5 --> A6
    A6 --> |EnhancedBankingReport| UI

    A1 & A2 & A3 & A4 & A5 & A6 -.-> GPT
    A1 --> SQL
    A1 --> Chroma
    A1 --> Blob
    Chroma -.-> Ada
    Blob --> |RAG Ingestion| Chroma
```

### Agent Pipeline Sequence

```mermaid
sequenceDiagram
    participant U as User / Streamlit UI
    participant O as Sequential Orchestrator
    participant DG as Data Gatherer
    participant FA as Fraud Analyst
    participant LA as Loan Analyst
    participant SS as Support Specialist
    participant RA as Risk Analyst
    participant SC as Synthesis Coordinator
    participant DB as Azure SQL + ChromaDB

    U->>O: Submit Query + Customer ID
    O->>DB: Load customer profile + RAG search
    DB-->>O: Profile + policy context
    O->>DG: Customer data + policy framework
    DG-->>O: Structured data summary
    O->>FA: Data summary + transactions
    FA-->>O: Fraud risk score + indicators
    O->>LA: Profile + fraud assessment
    LA-->>O: Loan eligibility + terms
    O->>SS: Full context accumulated
    SS-->>O: Product recommendations
    O->>RA: All agent findings
    RA-->>O: Enterprise risk score (0-100)
    O->>SC: Consolidated findings
    SC-->>O: Executive report JSON
    O-->>U: EnhancedBankingReport
```

### Data Flow

```mermaid
flowchart LR
    subgraph Ingestion["Document Ingestion Pipeline"]
        MD["Markdown Policy<br/>Documents"] --> Chunk["Chunking &<br/>Processing<br/><i>rag_utils.py</i>"]
        Chunk --> Embed["Ada-002<br/>Embedding"]
        Embed --> Store[("ChromaDB<br/>6 Collections")]
    end

    subgraph Runtime["Runtime Query Processing"]
        Q["User Query"] --> Hybrid["Hybrid Search<br/><i>chroma_manager.py</i>"]
        Store --> Hybrid
        Hybrid --> Context["RAG Policy<br/>Context"]
    end

    subgraph SQLPipe["SQL Pipeline"]
        AzSQL[("Azure SQL<br/>Database")] --> DC["DataConnector"]
        DC --> Profile["Customer<br/>Profile"]
    end

    Context --> Agents["6-Agent<br/>Pipeline"]
    Profile --> Agents
    Agents --> Report["EnhancedBankingReport<br/>JSON"]
    Report --> Display["Streamlit UI /<br/>Console Output"]
```

**Data Sources**:
- Azure SQL Database -- customer transactions and financial data
- ChromaDB -- banking policy vectors with Azure text-embedding-ada-002 (RAG)
- Azure Blob Storage / local files -- raw policy documents

> **Detailed architecture diagrams** (system topology, data flow, agent
> orchestration) are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Streamlit UI

The project includes an interactive web dashboard built with Streamlit:

```bash
cd src
streamlit run app.py
```

**Features:**
- **Dashboard** -- Overview of agents, data sources, and customer profiles
- **Run Analysis** -- Submit queries to the full 6-agent pipeline interactively
- **Report Viewer** -- Browse and inspect all saved JSON reports
- **Architecture** -- Interactive Mermaid diagrams of the system

## Project Structure

```
Project_4/
  src/                        # Python source code
    app.py                    # Streamlit web UI
    main_starter.py           # CLI entry point and orchestration
    azure_embedding.py        # Azure OpenAI embedding function for ChromaDB
    blob_connector.py         # Document storage connector
    chroma_manager.py         # ChromaDB vector store manager
    rag_utils.py              # Document processing and RAG utilities
    shared_state.py           # Thread-safe state management
    data_connector.py         # Azure SQL Database connector
    models.py                 # Pydantic data models
  data/
    sql/                      # Database scripts
      create.sql              # Table schema
      insert.sql              # Sample transaction data
      query.sql               # Reference queries
  docs/                       # Documentation and screenshots
    ARCHITECTURE.md           # Architecture diagrams (Mermaid)
    PROJECT_STATUS_REVIEW.md  # Project progress tracking
    VERSIONS.md               # Branch and version tracking
  screenshots/                # Azure portal screenshots for submission
  session_memory/             # Session-by-session development logs
  Seed_code/                  # Original starter code (reference)
  reports/                    # Generated analysis reports (gitignored)
  logs/                       # Runtime logs (gitignored)
  .env                        # Credentials (gitignored -- never commit)
  env.example                 # Credential template (safe to commit)
  requirements.txt            # Python dependencies
  DEVELOPMENT_RULES.md        # Team development standards
  README.md                   # This file
```

## Prerequisites

- Python 3.12
- Azure subscription with:
  - Azure OpenAI Service (GPT-4 / GPT-4o + text-embedding-ada-002 deployed)
  - Azure SQL Database
  - Azure Blob Storage (optional -- local fallback included)
- ODBC Driver 18 for SQL Server

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/rodolfolermacontreras/AI-Vectra-Bank-AI-Agentic-RAG-for-Banking.git
cd AI-Vectra-Bank-AI-Agentic-RAG-for-Banking

# 2. Create and activate virtual environment
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp env.example .env
# Edit .env with your Azure credentials

# 5. Provision Azure SQL and load data
# Run data/sql/create.sql then data/sql/insert.sql on your Azure SQL instance
```

## Usage

```bash
cd src

# Launch the Streamlit web UI
streamlit run app.py

# Or use the CLI:
python main_starter.py --test    # Component validation tests
python main_starter.py --demo    # Single demo scenario
python main_starter.py --all     # Full 5-scenario evaluation suite
```

## Tech Stack

| Component | Version |
|-----------|---------||
| Python | 3.12 |
| semantic-kernel | 1.37.0 |
| streamlit | 1.40+ |
| chromadb | 1.0.20 |
| openai | 1.x |
| azure-ai-inference | 1.x |
| python-docx | 1.2.0 |
| pyodbc | 5.2.0 |
| pydantic | 2.x |
| python-dotenv | 1.x |
| Azure OpenAI | GPT-4o, text-embedding-ada-002 |

## License

This project is part of the Udacity Microsoft Azure AI Foundry Nanodegree.
