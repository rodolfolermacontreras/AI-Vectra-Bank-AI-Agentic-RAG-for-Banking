"""
AI Vectra Bank -- Streamlit UI for the Banking Multi-Agent RAG System.

Provides an interactive dashboard to run the six-agent sequential
orchestration pipeline, visualise reports, and explore past evaluations.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — ensure src/ imports work
# ---------------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))

# Load environment variables before any import that needs them
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# Local imports (deferred so .env is loaded first)
from models import EnhancedBankingReport, CustomerProfile, RiskLevel

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

CUSTOMER_PROFILES = {
    "12345": {
        "name": "Premium Customer",
        "income": 75_000,
        "credit_score": 780,
        "account_type": "Premium Plus",
        "risk_tier": "Low",
        "products": ["Checking", "Savings", "Mortgage", "Investment", "Credit Card"],
    },
    "67890": {
        "name": "Standard Customer",
        "income": 45_000,
        "credit_score": 680,
        "account_type": "Standard",
        "risk_tier": "Medium",
        "products": ["Checking", "Savings", "Credit Card"],
    },
    "11111": {
        "name": "Basic Customer",
        "income": 28_000,
        "credit_score": 580,
        "account_type": "Basic",
        "risk_tier": "High",
        "products": ["Checking"],
    },
}

SAMPLE_QUERIES = [
    "I need comprehensive financial planning including investments and retirement options. Please also review my account for any suspicious activity and assess my loan eligibility.",
    "I noticed unusual transactions on my account. Can you investigate potential fraud and review my security?",
    "I'd like to apply for a personal loan. What are my options and eligibility?",
    "Please provide a complete risk assessment of my banking portfolio and suggest ways to improve my financial health.",
    "What banking products would you recommend for someone in my financial situation?",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def risk_color(level: str) -> str:
    """Map risk level to a colour."""
    mapping = {
        "low": "#28a745",
        "medium": "#ffc107",
        "high": "#fd7e14",
        "critical": "#dc3545",
    }
    return mapping.get(level.lower(), "#6c757d")


def risk_emoji(level: str) -> str:
    """Map risk level to an icon."""
    mapping = {
        "low": "✅",
        "medium": "⚠️",
        "high": "🔶",
        "critical": "🔴",
    }
    return mapping.get(level.lower(), "❓")


def load_saved_reports() -> list:
    """Load all JSON reports from the reports/ directory."""
    reports = []
    for path in sorted(REPORTS_DIR.glob("*.json"), reverse=True):
        if path.name == "evaluation_summary.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_filename"] = path.name
            reports.append(data)
        except Exception:
            pass
    return reports


def run_async(coro):
    """Run an async coroutine from synchronous Streamlit code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Vectra Bank — Multi-Agent Banking Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.85; font-size: 0.95rem; }

    /* Metric cards */
    .metric-card {
        background: #f8f9fa;
        border-left: 4px solid;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .metric-card h3 { margin: 0 0 0.3rem 0; font-size: 0.85rem; color: #6c757d; text-transform: uppercase; }
    .metric-card .value { font-size: 1.6rem; font-weight: 700; }

    /* Agent cards */
    .agent-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .agent-card .agent-name { font-weight: 600; color: #0f3460; }
    .agent-card .agent-status { font-size: 0.85rem; color: #6c757d; }

    /* Report section */
    .report-section {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .report-section h4 { color: #0f3460; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem; }

    /* Sidebar accent */
    [data-testid="stSidebar"] { background-color: #f0f2f6; }

    /* Hide Streamlit footer */
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>🏦 AI Vectra Bank</h1>
        <p>Multi-Agent Banking Intelligence System &bull; Powered by Azure AI Foundry &amp; Semantic Kernel</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/bank-building.png",
        width=64,
    )
    st.title("Navigation")
    page = st.radio(
        "Select a page",
        ["🏠 Dashboard", "🚀 Run Analysis", "📊 Report Viewer", "🏗️ Architecture"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### System Info")
    st.markdown(
        f"""
        - **Python**: {sys.version_info.major}.{sys.version_info.minor}
        - **Project**: AI Vectra Bank
        - **Agents**: 6 (Sequential)
        - **LLM**: Azure GPT-4o
        - **Embeddings**: Ada-002
        """
    )
    st.divider()
    st.caption("Udacity — Microsoft Azure AI Foundry Nanodegree • Project 4")


# ======================================================================
# Shared report display function (defined before pages that reference it)
# ======================================================================


def _display_report(data: dict, from_live: bool = False):
    """Render a report (dict) as a rich Streamlit layout."""
    # --- Header metrics ---
    st.divider()
    st.subheader(f"Report: {data.get('report_id', 'N/A')}")

    m1, m2, m3, m4, m5 = st.columns(5)

    risk_level = data.get("risk_assessment", "medium")
    m1.metric("Risk Score", f"{data.get('risk_score', 0):.0f} / 100")
    m2.metric("Risk Level", f"{risk_emoji(risk_level)} {risk_level.title()}")
    m3.metric(
        "Fraud Risk",
        f"{risk_emoji(data.get('fraud_risk_level', 'low'))} "
        f"{data.get('fraud_risk_level', 'low').title()}",
    )
    m4.metric("Loan Eligible", "Yes" if data.get("loan_eligibility") else "No")
    m5.metric(
        "Financial Health",
        f"{data.get('financial_health_score', 50):.0f} / 100",
    )

    # --- Executive Summary ---
    st.divider()
    st.subheader("Executive Summary")
    summary = data.get("summary", "")
    if summary:
        st.markdown(summary[:3000])

    # --- Key Findings ---
    findings = data.get("key_findings", [])
    if findings:
        st.subheader("Key Findings")
        for f in findings:
            st.markdown(f"- {f}")

    # --- Risk & Compliance columns ---
    col_risk, col_comply = st.columns(2)

    with col_risk:
        st.subheader("Risk Profile")
        metrics = data.get("processing_metrics", {})
        st.markdown(f"- **Risk Score:** {data.get('risk_score', 'N/A')}")
        st.markdown(f"- **Assessment:** {data.get('risk_assessment', 'N/A')}")
        st.markdown(f"- **Fraud Level:** {data.get('fraud_risk_level', 'N/A')}")
        st.markdown(f"- **Compliance:** {data.get('compliance_status', 'N/A')}")

    with col_comply:
        st.subheader("Financial Overview")
        st.markdown(
            f"- **Health Score:** {data.get('financial_health_score', 'N/A')}"
        )
        st.markdown(
            f"- **Loan Eligibility:** {'Yes' if data.get('loan_eligibility') else 'No'}"
        )
        if metrics:
            st.markdown(
                f"- **Income:** ${metrics.get('customer_income', 0):,.2f}"
            )
            st.markdown(
                f"- **Credit Score:** {metrics.get('customer_credit_score', 'N/A')}"
            )

    # --- Recommendations & Actions ---
    recs = data.get("recommendations", [])
    actions = data.get("next_best_actions", [])

    col_rec, col_act = st.columns(2)
    with col_rec:
        st.subheader("Recommendations")
        for r in recs:
            st.markdown(f"- {r}")
    with col_act:
        st.subheader("Next Best Actions")
        for a in actions:
            st.markdown(f"- {a}")

    # --- Agent Contributions ---
    contributions = data.get("agent_contributions", {})
    if contributions:
        st.divider()
        st.subheader("Agent Contributions")
        tabs = st.tabs(list(contributions.keys()))
        for tab, (agent_name, output) in zip(tabs, contributions.items()):
            with tab:
                st.markdown(output[:5000])

    # --- Agent Activations ---
    activations = data.get("agent_activations", [])
    if activations:
        st.divider()
        st.subheader("Agent Performance")
        perf_cols = st.columns(min(len(activations), 6))
        for col, act in zip(perf_cols, activations):
            with col:
                status = "PASS" if act.get("success") else "FAIL"
                name = act.get("agent_name", "Unknown").replace("Enhanced_", "")
                duration = act.get("duration_seconds", 0)
                st.metric(
                    f"[{status}] {name}",
                    f"{duration:.1f}s",
                )

    # --- Processing Metrics ---
    metrics = data.get("processing_metrics", {})
    if metrics:
        st.divider()
        st.subheader("Processing Metrics")
        pm1, pm2, pm3, pm4 = st.columns(4)
        pm1.metric(
            "Total Time",
            f"{metrics.get('total_processing_time_seconds', 0):.1f}s",
        )
        pm2.metric("Agents Activated", metrics.get("agents_activated", 0))
        pm3.metric("Policies Referenced", metrics.get("policies_referenced", 0))
        pm4.metric("RAG Results", metrics.get("rag_results_returned", 0))

    # --- Raw JSON ---
    with st.expander("Raw JSON Report"):
        st.json(data)


# ======================================================================
# PAGE: Dashboard
# ======================================================================
if page == "🏠 Dashboard":
    st.header("System Dashboard")

    # ---------- summary metrics ----------
    saved = load_saved_reports()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saved Reports", len(saved))
    col2.metric("Customer Profiles", len(CUSTOMER_PROFILES))
    col3.metric("AI Agents", 6)
    col4.metric("Data Sources", 3)

    st.divider()

    # ---------- agent overview ----------
    st.subheader("Agent Pipeline Overview")
    agents_info = [
        ("1. Data Gatherer", "Aggregates customer financial data, transaction history, and account details."),
        ("2. Fraud Analyst", "Analyses transaction patterns for anomalies and assigns fraud risk scores."),
        ("3. Loan Analyst", "Evaluates loan eligibility based on income, credit score, and DTI ratio."),
        ("4. Support Specialist", "Identifies cross-sell opportunities and personalised product recommendations."),
        ("5. Risk Analyst", "Calculates enterprise risk scores across credit, market, operational, and compliance dimensions."),
        ("6. Synthesis Coordinator", "Consolidates all agent findings into an executive-ready report."),
    ]

    cols = st.columns(3)
    for idx, (name, desc) in enumerate(agents_info):
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="agent-card">
                    <div class="agent-name">🤖 {name}</div>
                    <div class="agent-status">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # ---------- data sources ----------
    st.subheader("Data Sources")
    ds1, ds2, ds3 = st.columns(3)
    with ds1:
        st.markdown("#### 🗄️ Azure SQL Database")
        st.markdown("Customer transactions, financial records, and account data.")
    with ds2:
        st.markdown("#### 🔍 ChromaDB (RAG)")
        st.markdown("Banking policy vectors indexed with Azure text-embedding-ada-002.")
    with ds3:
        st.markdown("#### 📁 Blob / Local Storage")
        st.markdown("Raw policy documents: fraud detection, risk assessment, loan eligibility, etc.")

    # ---------- customer preview ----------
    st.divider()
    st.subheader("Customer Profiles")
    for cid, info in CUSTOMER_PROFILES.items():
        with st.expander(f"Customer {cid} — {info['name']} ({info['risk_tier']} Risk)"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Annual Income", f"${info['income']:,}")
            c2.metric("Credit Score", info["credit_score"])
            c3.metric("Account Type", info["account_type"])
            st.markdown(f"**Banking Products:** {', '.join(info['products'])}")

# ======================================================================
# PAGE: Run Analysis
# ======================================================================
elif page == "🚀 Run Analysis":
    st.header("Run Multi-Agent Analysis")
    st.markdown(
        "Submit a customer query to run the full six-agent sequential "
        "orchestration pipeline. The system will process the query through "
        "all agents and produce a comprehensive banking report."
    )

    col_left, col_right = st.columns([2, 1])

    with col_left:
        customer_id = st.selectbox(
            "Select Customer",
            list(CUSTOMER_PROFILES.keys()),
            format_func=lambda x: f"Customer {x} — {CUSTOMER_PROFILES[x]['name']}",
        )

        query_option = st.radio(
            "Query Input",
            ["Select a sample query", "Write a custom query"],
            horizontal=True,
        )

        if query_option == "Select a sample query":
            customer_query = st.selectbox("Sample Queries", SAMPLE_QUERIES)
        else:
            customer_query = st.text_area(
                "Enter your banking query",
                height=100,
                placeholder="e.g., Review my account for suspicious activity and assess my loan eligibility...",
            )

    with col_right:
        st.markdown("### Customer Preview")
        info = CUSTOMER_PROFILES[customer_id]
        st.markdown(f"**Name:** {info['name']}")
        st.markdown(f"**Income:** ${info['income']:,}")
        st.markdown(f"**Credit Score:** {info['credit_score']}")
        st.markdown(f"**Risk Tier:** {risk_emoji(info['risk_tier'])} {info['risk_tier']}")
        st.markdown(f"**Products:** {len(info['products'])}")

    st.divider()

    if st.button("🚀 Run Analysis Pipeline", type="primary", use_container_width=True):
        if not customer_query or not customer_query.strip():
            st.error("Please enter or select a query.")
        else:
            # Import the orchestration class
            try:
                from main_starter import EnhancedBankingSequentialOrchestration

                progress_bar = st.progress(0, text="Initialising system...")
                status_container = st.empty()

                with st.spinner("Running 6-agent sequential orchestration..."):
                    progress_bar.progress(10, text="Loading documents and customer profiles...")

                    system = EnhancedBankingSequentialOrchestration()

                    progress_bar.progress(30, text="Executing agent pipeline...")

                    start_time = time.time()
                    report = run_async(
                        system.run_enhanced_analysis(customer_id, customer_query)
                    )
                    elapsed = time.time() - start_time

                    progress_bar.progress(90, text="Generating report...")

                    # Save report
                    report_path = REPORTS_DIR / f"ui_report_{report.report_id}.json"
                    report_path.write_text(
                        report.model_dump_json(indent=2), encoding="utf-8"
                    )

                    progress_bar.progress(100, text="Done!")

                st.success(
                    f"Analysis complete in {elapsed:.1f}s — "
                    f"Report ID: **{report.report_id}**"
                )

                # Display the report inline
                _display_report(report.model_dump(), from_live=True)

            except Exception as exc:
                st.error(f"Pipeline error: {exc}")
                st.exception(exc)

# ======================================================================
# PAGE: Report Viewer
# ======================================================================
elif page == "📊 Report Viewer":
    st.header("Report Viewer")

    saved = load_saved_reports()
    if not saved:
        st.info("No saved reports found. Run an analysis first or check the `reports/` directory.")
    else:
        # Build dropdown labels
        labels = []
        for r in saved:
            rid = r.get("report_id", "unknown")
            cid = r.get("customer_id", "?")
            ts = r.get("generated_at", "")
            labels.append(f"{rid} — Customer {cid} ({ts[:19] if ts else 'N/A'})")

        selected_idx = st.selectbox(
            "Select a report",
            range(len(labels)),
            format_func=lambda i: labels[i],
        )

        report_data = saved[selected_idx]
        _display_report(report_data, from_live=False)

# ======================================================================
# PAGE: Architecture
# ======================================================================
elif page == "🏗️ Architecture":
    st.header("System Architecture")
    st.markdown(
        "The AI Vectra Bank system uses a **sequential multi-agent orchestration** "
        "pattern built on Microsoft Semantic Kernel. Six specialised AI agents "
        "process banking queries in sequence, each building on the findings of "
        "the previous agent."
    )

    st.subheader("High-Level Architecture")
    st.markdown(
        """
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
                A1["1. Data Gatherer"]
                A2["2. Fraud Analyst"]
                A3["3. Loan Analyst"]
                A4["4. Support Specialist"]
                A5["5. Risk Analyst"]
                A6["6. Synthesis Coordinator"]
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

            Query --> Orch
            Orch --> A1 --> A2 --> A3 --> A4 --> A5 --> A6
            A6 --> Report

            A1 & A2 & A3 & A4 & A5 & A6 --> GPT
            A1 --> SQL
            A1 --> Chroma
            Chroma --> Ada
            A1 --> Blob
        ```
        """
    )

    st.subheader("Agent Pipeline Flow")
    st.markdown(
        """
        ```mermaid
        sequenceDiagram
            participant U as User / UI
            participant O as Orchestrator
            participant DG as Data Gatherer
            participant FA as Fraud Analyst
            participant LA as Loan Analyst
            participant SS as Support Specialist
            participant RA as Risk Analyst
            participant SC as Synthesis Coordinator

            U->>O: Submit Query + Customer ID
            O->>DG: Customer data + policies
            DG-->>O: Structured data summary
            O->>FA: Data summary + transactions
            FA-->>O: Fraud risk score & indicators
            O->>LA: Profile + fraud assessment
            LA-->>O: Loan eligibility & terms
            O->>SS: Full context so far
            SS-->>O: Product recommendations
            O->>RA: All agent findings
            RA-->>O: Enterprise risk score
            O->>SC: Consolidated findings
            SC-->>O: Executive report
            O-->>U: EnhancedBankingReport
        ```
        """
    )

    st.subheader("Data Flow")
    st.markdown(
        """
        ```mermaid
        flowchart LR
            subgraph Ingestion["Document Ingestion"]
                MD["Markdown Policies"] --> Chunk["Chunking<br/>rag_utils.py"]
                Chunk --> Embed["Ada-002<br/>Embeddings"]
                Embed --> Store["ChromaDB<br/>Collections"]
            end

            subgraph Query["Query Processing"]
                Q["User Query"] --> Hybrid["Hybrid Search<br/>chroma_manager.py"]
                Store --> Hybrid
                Hybrid --> Context["RAG Context"]
            end

            subgraph SQL["SQL Pipeline"]
                DB[("Azure SQL")] --> Fetch["DataConnector"]
                Fetch --> Profile["Customer<br/>Profile"]
            end

            Context --> Agents["Agent Pipeline"]
            Profile --> Agents
            Agents --> Report["JSON Report"]
        ```
        """
    )

    st.subheader("Technology Stack")
    tech_data = {
        "Component": [
            "Orchestration",
            "LLM",
            "Embeddings",
            "Vector Store",
            "Database",
            "Document Store",
            "Data Models",
            "UI Framework",
        ],
        "Technology": [
            "Microsoft Semantic Kernel 1.37",
            "Azure OpenAI GPT-4o",
            "text-embedding-ada-002 (1536-dim)",
            "ChromaDB 1.0.20",
            "Azure SQL Database",
            "Azure Blob / Local Fallback",
            "Pydantic v2",
            "Streamlit",
        ],
        "Purpose": [
            "Sequential agent orchestration",
            "Agent reasoning & text generation",
            "Document vectorisation for RAG",
            "Semantic search over banking policies",
            "Customer transactions & financial data",
            "Raw policy document storage",
            "Validated data models with type safety",
            "Interactive web dashboard",
        ],
    }
    st.table(tech_data)
