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
| Component tests          | DONE        | 21/21 passing                                   |
| Azure OpenAI connection  | DONE        | gpt-4o deployment verified                      |
| Azure SQL Database       | NOT STARTED | Need to provision and populate                  |
| Full evaluation (--all)  | NOT STARTED | Blocked on Azure SQL                            |
| Screenshots              | NOT STARTED | Azure portal captures for submission            |
| Reflective report        | NOT STARTED | Required for Udacity submission                 |
| Git repo                 | DONE        | Initial commit pushed to GitHub                 |

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
- [x] Pass all component tests
- [x] Connect to Azure OpenAI with real credentials
- [x] Clean up code (no emojis, proper paths)
- [x] Create project documentation
- [x] Push initial code to GitHub

### Phase 2: Azure Infrastructure (NEXT)
- [ ] Provision Azure SQL Database in Regroup_8kkYx8D resource group
- [ ] Run create.sql to create transactions table
- [ ] Run insert.sql to populate sample data
- [ ] Update .env with SQL connection string
- [ ] Verify DataConnector works with live database
- [ ] Take Azure portal screenshots

### Phase 3: Full Evaluation
- [ ] Run `--demo` with live Azure SQL + OpenAI
- [ ] Run `--all` for complete 5-scenario evaluation
- [ ] Review generated reports for quality
- [ ] Capture terminal output screenshots

### Phase 4: Submission
- [ ] Write reflective report
- [ ] Compile all screenshots
- [ ] Final code review and cleanup
- [ ] Submit to Udacity

---

## Azure Resources

| Resource | Value | Status |
|----------|-------|--------|
| Subscription | 052d7bab-4db1-4651-a14c-c5b4d14f6cb4 | Active |
| Resource Group | Regroup_8kkYx8D | Active |
| Azure OpenAI | udacity-travel-aoai | Verified working |
| Deployment | gpt-4o | Verified working |
| Azure SQL | (not provisioned) | Pending |
| Blob Storage | (using local fallback) | Optional |

---

## Tech Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.12 | 3.14 incompatible with pydantic-core |
| semantic-kernel | 1.37.0 | Microsoft AI orchestration |
| chromadb | 1.0.20 | Vector store for RAG |
| python-docx | 1.2.0 | Report generation |
| pyodbc | 5.2.0 | Azure SQL connectivity |
| pydantic | 2.11.10 | Data validation |
| python-dotenv | 1.2.1 | Environment management |
