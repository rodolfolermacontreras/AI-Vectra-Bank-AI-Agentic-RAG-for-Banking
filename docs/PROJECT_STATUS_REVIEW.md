# Project Status Review -- AI Vectra Bank

> Banking Multi-Agent RAG System
> Udacity "Microsoft Azure AI Foundry" Nanodegree -- Project 4
> Repo: https://github.com/rodolfolermacontreras/AI-Vectra-Bank-AI-Agentic-RAG-for-Banking

---

## Current Status Summary

| Area                     | Status      | Notes                                          |
|--------------------------|-------------|-------------------------------------------------|
| Project structure        | DONE        | src/, data/sql/, docs/, session_memory/         |
| Python environment       | DONE        | 3.12 venv, all packages installed               |
| Source code              | DONE        | 6 agents, orchestration, models, data connector |
| Component tests          | DONE        | 23/23 passing with live Azure services          |
| Azure OpenAI (chat)      | DONE        | gpt-4o deployed on final-project-udacity-ai     |
| Azure OpenAI (embedding) | DONE        | text-embedding-ada-002 deployed, ChromaDB wired |
| Azure SQL Database       | NOT STARTED | Need to provision and populate                  |
| Full evaluation (--all)  | NOT STARTED | Blocked on Azure SQL                            |
| Screenshots              | NOT STARTED | Azure portal captures for submission            |
| Reflective report        | NOT STARTED | Required for Udacity submission                 |
| Git repo                 | DONE        | dev branch, PR #1 merged, conventional commits  |

---

## Update 4 -- 2026-02-17 (Session 5)

**Phase**: Azure AI Foundry deployment and live integration

### What was done

- Received new Udacity cloud credentials (old Project 3 credentials expired)
- Discovered Azure AI Foundry resource `final-project-udacity-ai` via REST API probing
- Found serverless models available (Phi-4, DeepSeek-R1, Cohere-embed-v3-english)
- Deployed **gpt-4o** (Global Standard, 50K TPM) via Azure Foundry portal
- Deployed **text-embedding-ada-002** (Global Standard, 120K TPM) via Azure Foundry portal
- Updated `.env` with new endpoint and API key
- Updated `azure_embedding.py` API version to `2024-06-01`
- Added `openai` and `azure-ai-inference` to `requirements.txt`
- Verified all 4 integration points: OpenAI SDK chat, OpenAI SDK embeddings,
  Semantic Kernel `AzureChatCompletion`, and `AzureOpenAIEmbeddingFunction`
- Cleaned stale ChromaDB (will rebuild with 1536-dim Azure embeddings on next run)
- Removed 7 temporary discovery/probe scripts
- Committed and pushed to `dev` branch

### Test results

```
  TESTS: 23/23 passed, 0/23 failed
```

---

## Update 3 -- 2026-02-16 (Sessions 3-4)

**Phase**: Azure embedding integration, architecture diagrams, course notes

### What was done

- Created `src/azure_embedding.py` -- ChromaDB-compatible Azure OpenAI embedding function
- Modified `src/chroma_manager.py` -- embedding_function parameter + conflict handling
- Modified `src/main_starter.py` -- Azure embedding integration + test
- Created `docs/ARCHITECTURE.md` -- 3 Mermaid diagrams (system, data flow, orchestration)
- Created `screenshots/README.md` -- submission checklist
- Updated `README.md` with Mermaid diagram + project structure
- Created PR #1 and merged `dev/azure-embeddings-and-diagrams` into `main`
- Created fresh `dev` branch from updated `main`
- Created comprehensive `docs/COURSE_NOTES.md` (~989 lines)
- All committed and pushed

### Test results

```
  TESTS: 23/23 passed, 0/23 failed
```

---

## Update 2 -- 2026-02-15 (Session 2)

**Phase**: Code cleanup, documentation, git setup

### What was done

- Removed ALL emoji and unicode characters from src/ files per DEVELOPMENT_RULES
  - `src/main_starter.py`: replaced emojis with ASCII equivalents ([PASS], [FAIL], [AGENT], etc.)
  - `src/models.py`: replaced checkmark/cross emojis with [PASS]/[FAIL]
  - Em-dashes replaced with `--`, ellipsis with `...`
- Fixed path resolution for new directory structure
  - Added `PROJECT_ROOT` constant in `main_starter.py` (resolves to project root from src/)
  - Fixed `load_dotenv()` in both `main_starter.py` and `data_connector.py` to load `.env` from project root
  - Fixed `logs/` and `reports/` paths to write under project root, not cwd
- Re-ran tests: **21/21 passing** (up from 18/19 -- agent creation now works with real Azure creds)
- Created comprehensive `PROJECT_STATUS_REVIEW.md` (this file)
- Created `session_memory/` directory for session-by-session tracking
- Initialised git repository and pushed initial code to GitHub

### Test results

```
  TESTS: 21/21 passed, 0/21 failed
```

### Decisions made

1. **Python 3.12 over 3.14**: pydantic-core fails to build on 3.14 (Rust compilation). 3.12 works cleanly.
2. **gpt-4o not gpt-4**: the Azure deployment name from Project 3 is `gpt-4o`.
3. **No emoji policy**: DEVELOPMENT_RULES mandate ASCII-only output to avoid Windows cp1252 encoding crashes.
4. **Seed code untouched**: blob_connector.py, chroma_manager.py, rag_utils.py, shared_state.py kept as-is.

---

## Update 1 -- 2026-02-15 (Session 1)

**Phase**: Initial project scaffolding and implementation

### What was done

- Read and analysed all Udacity seed code files
- Created project directory structure (src/, data/sql/, docs/, reports/, logs/)
- Implemented `src/models.py` -- Pydantic models for banking report
- Implemented `src/data_connector.py` -- Azure SQL connector with fallback
- Completed `src/main_starter.py` -- full 6-agent sequential orchestration with CLI
- Set up Python 3.12 virtual environment
- Installed all packages (semantic-kernel, chromadb, pyodbc, python-docx, pydantic, python-dotenv)
- Created .gitignore, env.example, DEVELOPMENT_RULES.md, README.md

### What failed / issues encountered

1. **Python 3.14 venv**: pydantic-core requires Rust compilation, no pre-built wheel for 3.14. Fix: recreated with `py -3.12`.
2. **Unicode crash on Windows**: emojis in print statements caused `UnicodeEncodeError` on cp1252 console. Workaround: `-X utf8` flag. Permanent fix: removed all emojis in Session 2.
3. **Agent creation test failure (1/19)**: placeholder credentials (`<your-resource>`) rejected by AzureChatCompletion. Fix: real credentials from Project 3.

### Files created

| File | Purpose |
|------|---------|
| `src/main_starter.py` | Main orchestration, 6 agents, CLI (~1400 lines) |
| `src/models.py` | Pydantic models (~218 lines) |
| `src/data_connector.py` | Azure SQL connector (~305 lines) |
| `src/__init__.py` | Package init |
| `data/sql/create.sql` | Table schema (copied from seed) |
| `data/sql/insert.sql` | Sample data (copied from seed) |
| `data/sql/query.sql` | Reference queries (copied from seed) |
| `env.example` | Credential template |
| `.gitignore` | Ignore rules |
| `requirements.txt` | Pinned dependencies |
| `README.md` | Project overview |
| `DEVELOPMENT_RULES.md` | Dev standards |

---

## BIG PICTURE PLAN

### Phase 1: Foundation (DONE)
- [x] Read and understand seed code
- [x] Set up Python 3.12 environment
- [x] Implement models, data connector, orchestration
- [x] Pass all component tests (23/23)
- [x] Clean up code (no emojis, proper paths)
- [x] Create project documentation
- [x] Push initial code to GitHub

### Phase 2: Azure AI Foundry (DONE)
- [x] Deploy gpt-4o on final-project-udacity-ai
- [x] Deploy text-embedding-ada-002 on final-project-udacity-ai
- [x] Implement Azure embedding function for ChromaDB
- [x] Verify Semantic Kernel + OpenAI SDK integration
- [x] Create architecture diagrams (Mermaid)
- [x] Merge via PR #1, push to dev

### Phase 3: Azure SQL Database (NEXT)
- [ ] Provision Azure SQL Database in Regroup_8kkYx8D resource group
- [ ] Run create.sql to create transactions table
- [ ] Run insert.sql to populate sample data
- [ ] Update .env with SQL connection string
- [ ] Verify DataConnector works with live database

### Phase 4: Full Evaluation
- [ ] Run `--demo` with live Azure SQL + OpenAI
- [ ] Run `--all` for complete 5-scenario evaluation
- [ ] Review generated reports for quality
- [ ] Capture all screenshots (Azure portal + terminal)

### Phase 5: Submission
- [ ] Write reflective report (LaTeX or Word)
- [ ] Compile all screenshots
- [ ] Final code review and cleanup
- [ ] Submit to Udacity

---

## Azure Resources

| Resource | Value | Status |
|----------|-------|--------|
| Subscription | Udacity-410 (052d7bab-...-c5b4d14f6cb4) | Active |
| Resource Group | Regroup_8kkYx8D (eastus) | Active |
| AI Foundry Account | final-project-udacity-ai | Active |
| AI Foundry Project | project-4-udacity-multi-ai-rag | Active |
| Chat Deployment | gpt-4o (2024-11-20, Global Standard) | Verified |
| Embedding Deployment | text-embedding-ada-002 (v2, Global Standard) | Verified |
| Endpoint | final-project-udacity-ai.cognitiveservices.azure.com | Verified |
| Azure SQL | (not provisioned) | Pending |
| Blob Storage | (using local fallback) | Optional |

---

## Tech Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.12 | 3.14 incompatible with pydantic-core |
| semantic-kernel | 1.37.0 | Microsoft AI orchestration |
| chromadb | 1.0.20 | Vector store for RAG |
| openai | 1.x | Azure OpenAI SDK |
| azure-ai-inference | 1.x | Azure AI Model Inference SDK |
| python-docx | 1.2.0 | Report generation |
| pyodbc | 5.2.0 | Azure SQL connectivity |
| pydantic | 2.11.10 | Data validation |
| python-dotenv | 1.2.1 | Environment management |
