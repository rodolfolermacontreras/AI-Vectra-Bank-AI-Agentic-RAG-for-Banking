# Reflective Report -- Banking Multi-Agent RAG System

**Project**: AI Vectra Bank -- Multi-Agent RAG System for Banking Intelligence  
**Course**: Microsoft Azure AI Foundry Nanodegree (Udacity)  
**Date**: February 2026  
**Author**: Rodolfo Lerma Contreras

---

## 1. Project Overview

This project implements a multi-agent banking intelligence system that
orchestrates six specialised AI agents using Microsoft Semantic Kernel.
The system processes complex banking queries through a sequential pipeline
where each agent contributes domain-specific analysis, ultimately producing
a comprehensive financial report.

The six agents are:

1. **Data Gatherer** -- retrieves customer data from Azure SQL Database
2. **Fraud Analyst** -- analyses transaction patterns for suspicious activity
3. **Loan Analyst** -- evaluates loan eligibility and credit risk
4. **Support Specialist** -- provides customer support recommendations
5. **Risk Analyst** -- performs comprehensive risk assessment using RAG
6. **Synthesis Coordinator** -- integrates all findings into a final report

---

## 2. Design Decisions

### 2.1 Sequential Orchestration Pattern

I chose sequential (pipeline) orchestration over parallel execution because
each agent's output enriches the context for the next agent. For example,
the Fraud Analyst needs transaction data from the Data Gatherer, and the
Risk Analyst needs fraud and loan findings to produce a meaningful risk
assessment. This sequential dependency makes a pipeline the natural fit.

The trade-off is latency -- a full run takes approximately 60 seconds because
each agent waits for its predecessor. However, the quality improvement from
accumulated context outweighs the performance cost for a banking use case
where thoroughness matters more than speed.

### 2.2 Azure OpenAI Embeddings for RAG

The project rubric required using Azure-hosted embeddings rather than
ChromaDB's default embedding function. I implemented a custom
`AzureOpenAIEmbeddingFunction` class that integrates with the Azure OpenAI
`text-embedding-ada-002` model (1536 dimensions). This class implements
ChromaDB's `EmbeddingFunction` protocol, allowing seamless drop-in replacement.

Key design choice: I used the REST API directly (via the `openai` Python SDK)
rather than the Azure AI Inference SDK, because `text-embedding-ada-002`
requires the `2024-06-01` API version which maps cleanly to the OpenAI
client's `AzureOpenAI` class.

### 2.3 Azure SQL Database for Customer Data

Rather than relying solely on sample/mock data, I provisioned a live Azure
SQL Database (`vectra-bank-db`) with 12 transaction records across 3 customer
profiles. The `DataConnector` class implements graceful fallback -- if the
Azure SQL connection is unavailable, it falls back to sample data, ensuring
the system works both online and offline.

### 2.4 Pydantic Models for Structured Output

All agent outputs are captured in Pydantic models (`CustomerProfile`,
`EnhancedBankingReport`) with field validation. This ensures type safety,
automatic serialisation to JSON for report storage, and clear contracts
between agents. Risk scores are clamped to 0--100, credit scores to 300--850,
and enums enforce valid status values.

### 2.5 Six ChromaDB Collections

I organised the vector store into six topic-specific collections
(fraud_detection, loan_policies, customer_support, risk_assessment,
transaction_monitoring, compliance) rather than a single collection. This
improves retrieval relevance because semantic search is scoped to the
appropriate policy domain for each agent.

---

## 3. Challenges and Solutions

### 3.1 Python Version Compatibility

**Challenge**: Initially attempted Python 3.14 (latest), but `pydantic-core`
failed to build from source (no pre-compiled wheel available).

**Solution**: Downgraded to Python 3.12, which has pre-built wheels for all
dependencies including `chromadb`, `semantic-kernel`, and `pydantic`.

### 3.2 Windows Console Encoding (cp1252)

**Challenge**: The seed code files (`chroma_manager.py`, `blob_connector.py`)
contained Unicode emoji characters (check marks, crosses) that crash on
Windows PowerShell terminals using cp1252 encoding. This caused 16 of 23
tests to fail silently with `UnicodeEncodeError`.

**Solution**: Replaced all emoji characters with ASCII equivalents
(`[OK]`, `[FAIL]`, `[ERROR]`). This is documented in `DEVELOPMENT_RULES.md`
as a project-wide standard: no emoji or extended Unicode in any `src/` file.

### 3.3 Azure Region Availability

**Challenge**: The Azure SQL Server creation failed in `eastus` with a
capacity error -- the region was blocked for the Udacity subscription.

**Solution**: Deployed to `westus` instead. This required no code changes
since the ODBC connection string abstracts the server location.

### 3.4 Azure Embedding API Version

**Challenge**: The `text-embedding-ada-002` model requires a specific API
version (`2024-06-01`). Using newer API versions returned 404 errors because
the embedding endpoint format differs across versions.

**Solution**: Hard-coded the `api_version="2024-06-01"` in the
`AzureOpenAIEmbeddingFunction` class and documented this requirement.

### 3.5 ChromaDB Stale State

**Challenge**: After switching Azure credentials, the local ChromaDB
(`chroma.sqlite3`) contained vectors generated with old embedding keys,
causing dimension mismatches.

**Solution**: Deleted the stale `chroma_db_banking/` directory to force a
clean rebuild on next run. The system recreates all collections and
re-embeds documents automatically on startup.

---

## 4. What I Learned

### 4.1 Multi-Agent Orchestration

Building a six-agent system taught me that agent design is as much about
**prompt engineering** as it is about code. Each agent's system prompt must
clearly define its scope, expected inputs, and output format. Agents that
receive vague instructions produce generic responses that don't help
downstream agents.

### 4.2 RAG Pipeline Design

Implementing RAG with Azure embeddings and ChromaDB reinforced that
**chunking strategy** matters enormously. The banking policy documents needed
to be split at logical boundaries (sections, paragraphs) rather than fixed
character counts to preserve semantic coherence in the retrieved chunks.

### 4.3 Azure Service Integration

Working with Azure AI Foundry, Azure SQL, and Azure OpenAI simultaneously
taught me the importance of **environment configuration management**. Using
`.env` files with `python-dotenv` and providing clear `env.example` templates
makes the project reproducible. The fallback patterns (e.g., `DataConnector`
falling back to sample data) make the system resilient to credential issues.

### 4.4 Testing Strategy

The 23-test suite covers models, connectors, embeddings, ChromaDB, RAG, SQL,
and orchestration. Having comprehensive tests caught the emoji encoding issue
immediately and verified that all Azure integrations were live after
credential changes. Automated testing is essential when working with external
services that can change state.

---

## 5. Evaluation Results

### 5.1 Test Suite (23/23 Pass)

All 23 automated tests pass with live Azure services:
- Model validation tests (5): Pydantic model creation and constraints
- Blob storage tests (3): Document upload and retrieval
- Embedding tests (2): Azure embedding generation (1536-dim vectors)
- ChromaDB tests (3): Collection management and document storage
- RAG tests (1): Semantic search with Azure embeddings
- SQL tests (3): Live Azure SQL connection, income and transaction queries
- Orchestration tests (6): Agent creation, naming, policy extraction

### 5.2 Demo Run (1 Scenario)

Single comprehensive scenario for customer 12345:
- All 6 agents activated successfully
- Risk score: 12/100 (low) -- appropriate for a customer with $75K income
  and 780 credit score
- Total processing time: ~62 seconds
- Report saved as structured JSON

### 5.3 Evaluation Suite (5/5 Scenarios Pass)

| Scenario | Customer | Risk Score | Assessment | Agents |
|----------|----------|-----------|------------|--------|
| 1 | 12345 | 12/100 | Low | 6/6 |
| 2 | 67890 | 52/100 | High | 6/6 |
| 3 | 11111 | 94/100 | Critical | 6/6 |
| 4 | 12345 | 12/100 | Low | 6/6 |
| 5 | 67890 | 52/100 | High | 6/6 |

The risk scores appropriately differentiate between customer profiles:
- Customer 12345 ($75K income, 780 credit) = consistently low risk
- Customer 67890 ($45K income, 620 credit) = consistently high risk
- Customer 11111 ($28K income, 520 credit) = consistently critical risk

---

## 6. Architecture Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | Sequential pipeline | Agent outputs depend on predecessors |
| LLM | gpt-4o (2024-11-20) | Best balance of quality and speed |
| Embeddings | text-embedding-ada-002 | Rubric requirement; 1536-dim vectors |
| Vector DB | ChromaDB (6 collections) | Lightweight, topic-scoped retrieval |
| SQL | Azure SQL Database | Live customer data with fallback |
| Framework | Semantic Kernel | Native Azure integration, agent support |
| Models | Pydantic v2 | Type safety, validation, JSON serialisation |
| Testing | Built-in test harness | 23 tests covering all integration points |

---

## 7. Suggestions for Improvement

Based on the testing and evaluation experience, two concrete improvements
would meaningfully enhance the system:

### 7.1 Parallel Agent Execution with Dependency Awareness

The current sequential pipeline takes approximately 60 seconds per scenario
because each agent waits for its predecessor to finish. In practice, some
agents are partially independent -- the Fraud Analyst and Loan Analyst both
depend on the Data Gatherer but not on each other. Introducing a
**dependency-aware parallel scheduler** (e.g., a DAG-based execution engine)
would allow Fraud and Loan analysis to run concurrently once the Data
Gatherer completes. Based on observed timings, this could reduce end-to-end
latency by 30--40%, bringing it closer to 35--40 seconds per scenario. The
Risk Analyst and Synthesis Coordinator would still wait for all upstream
agents, preserving correctness while improving throughput.

### 7.2 Conversation Memory for Multi-Turn Interactions

The system currently treats every query as a one-shot interaction -- there is
no memory of previous conversations. In a real banking support scenario, a
customer might ask about their loan eligibility, then follow up with
"what if I increase my down payment?" or "show me more detail on the fraud
flags." Adding a **session-based conversation memory** (e.g., using Semantic
Kernel's chat history or an external store like Redis) would allow agents to
reference prior context, avoid redundant data fetches, and deliver more
natural multi-turn dialogues. This would also improve the customer support
agent's ability to track issue resolution across interactions.

---

## 8. Conclusion

This project demonstrates a production-quality multi-agent banking system
that integrates Azure AI Foundry (GPT-4o), Azure OpenAI Embeddings
(text-embedding-ada-002), Azure SQL Database, and ChromaDB for RAG-based
policy retrieval. The sequential orchestration pattern ensures each agent
builds on accumulated context, producing thorough and contextually relevant
banking analysis reports.

The system successfully differentiates between low-risk, high-risk, and
critical-risk customer profiles, with risk scores that accurately reflect
each customer's financial situation. All 23 tests pass with live Azure
services, and all 5 evaluation scenarios complete successfully with all 6
agents activated.
