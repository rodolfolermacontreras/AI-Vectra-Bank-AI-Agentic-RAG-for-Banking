"""
AI Vectra Bank -- Streamlit UI for the Banking Multi-Agent RAG System.

Provides a professional interactive dashboard to run the six-agent
sequential orchestration pipeline, visualise reports, explore past
evaluations, and inspect the live agent workflow.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from models import EnhancedBankingReport, CustomerProfile, RiskLevel  # noqa: E402

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

AGENT_STAGES = [
    {
        "id": "data_gatherer",
        "name": "Data Gatherer",
        "short": "DG",
        "desc": "Aggregates customer financial data, transaction history, and account details from Azure SQL and document stores.",
        "inputs": "Customer ID, Query",
        "outputs": "Structured data summary",
        "color": "#2563eb",
    },
    {
        "id": "fraud_analyst",
        "name": "Fraud Analyst",
        "short": "FA",
        "desc": "Analyses transaction patterns for anomalies, flags suspicious activity, and assigns fraud risk scores using RAG-retrieved policies.",
        "inputs": "Data summary, Transactions",
        "outputs": "Fraud risk score and indicators",
        "color": "#dc2626",
    },
    {
        "id": "loan_analyst",
        "name": "Loan Analyst",
        "short": "LA",
        "desc": "Evaluates loan eligibility based on income, credit score, DTI ratio, and the fraud assessment from the previous stage.",
        "inputs": "Profile, Fraud assessment",
        "outputs": "Loan eligibility and terms",
        "color": "#059669",
    },
    {
        "id": "support_specialist",
        "name": "Support Specialist",
        "short": "SS",
        "desc": "Identifies cross-sell opportunities and personalised product recommendations based on the customer's full financial context.",
        "inputs": "Full context so far",
        "outputs": "Product recommendations",
        "color": "#7c3aed",
    },
    {
        "id": "risk_analyst",
        "name": "Risk Analyst",
        "short": "RA",
        "desc": "Calculates enterprise-level risk scores across credit, market, operational, and compliance dimensions.",
        "inputs": "All agent findings",
        "outputs": "Enterprise risk score",
        "color": "#d97706",
    },
    {
        "id": "synthesis_coordinator",
        "name": "Synthesis Coordinator",
        "short": "SC",
        "desc": "Consolidates all agent findings into a single executive-ready report with recommendations and next-best actions.",
        "inputs": "Consolidated findings",
        "outputs": "EnhancedBankingReport",
        "color": "#0f766e",
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def risk_color(level: str) -> str:
    mapping = {"low": "#059669", "medium": "#d97706", "high": "#ea580c", "critical": "#dc2626"}
    return mapping.get(level.lower(), "#6b7280")


def risk_label(level: str) -> str:
    mapping = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH", "critical": "CRITICAL"}
    return mapping.get(level.lower(), "UNKNOWN")


def load_saved_reports() -> list:
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
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _render_pipeline_html(active_index: int = -1, completed: list | None = None) -> str:
    """Return an HTML/CSS animated pipeline visualisation.

    ``active_index``  – stage currently executing (-1 = none)
    ``completed``     – list of booleans per stage (True = done)
    """
    if completed is None:
        completed = [False] * len(AGENT_STAGES)

    nodes_html = ""
    for i, stage in enumerate(AGENT_STAGES):
        if completed[i]:
            border = f"2px solid {stage['color']}"
            bg = stage["color"] + "18"
            badge = f'<span class="wf-badge wf-done">DONE</span>'
            dot_cls = "wf-dot wf-dot-done"
        elif i == active_index:
            border = f"2px solid {stage['color']}"
            bg = stage["color"] + "10"
            badge = f'<span class="wf-badge wf-active">RUNNING</span>'
            dot_cls = "wf-dot wf-dot-active"
        else:
            border = "1px solid #d1d5db"
            bg = "#f9fafb"
            badge = '<span class="wf-badge wf-idle">IDLE</span>'
            dot_cls = "wf-dot"

        connector = ""
        if i < len(AGENT_STAGES) - 1:
            line_color = stage["color"] if completed[i] else "#d1d5db"
            connector = f'<div class="wf-connector" style="background:{line_color}"></div>'

        nodes_html += f"""
        <div class="wf-step">
            <div class="wf-node" style="border:{border};background:{bg}">
                <div class="wf-header">
                    <span class="{dot_cls}" style="--clr:{stage['color']}"></span>
                    <span class="wf-num">Stage {i+1}</span>
                    {badge}
                </div>
                <div class="wf-title" style="color:{stage['color']}">{stage['name']}</div>
                <div class="wf-meta"><span>In: {stage['inputs']}</span></div>
                <div class="wf-meta"><span>Out: {stage['outputs']}</span></div>
            </div>
            {connector}
        </div>
        """

    return f"""
    <style>
        .wf-pipeline {{ display:flex; align-items:flex-start; gap:0; overflow-x:auto; padding:1rem 0; }}
        .wf-step {{ display:flex; align-items:center; flex-shrink:0; }}
        .wf-node {{
            width:180px; padding:14px 16px; border-radius:10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .wf-header {{ display:flex; align-items:center; gap:6px; margin-bottom:6px; }}
        .wf-num {{ font-size:11px; color:#6b7280; font-weight:600; text-transform:uppercase; letter-spacing:.5px; }}
        .wf-badge {{
            font-size:9px; font-weight:700; padding:2px 6px; border-radius:4px;
            letter-spacing:.5px; margin-left:auto;
        }}
        .wf-idle {{ background:#f3f4f6; color:#9ca3af; }}
        .wf-active {{ background:#dbeafe; color:#2563eb; animation: pulse 1.5s infinite; }}
        .wf-done {{ background:#d1fae5; color:#059669; }}
        .wf-title {{ font-size:13px; font-weight:700; margin-bottom:6px; }}
        .wf-meta {{ font-size:10px; color:#6b7280; line-height:1.4; }}
        .wf-dot {{
            width:8px; height:8px; border-radius:50%; background:#d1d5db; flex-shrink:0;
        }}
        .wf-dot-active {{ background:var(--clr); animation: pulse 1.5s infinite; }}
        .wf-dot-done {{ background:var(--clr); }}
        .wf-connector {{
            width:32px; height:2px; flex-shrink:0;
        }}
        @keyframes pulse {{
            0%,100% {{ opacity:1; }}
            50% {{ opacity:.4; }}
        }}
    </style>
    <div class="wf-pipeline">{nodes_html}</div>
    """


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Vectra Bank | Multi-Agent Banking Intelligence",
    page_icon="V",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS — clean, professional, no emojis
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --navy: #0f172a;
        --navy-mid: #1e293b;
        --accent: #2563eb;
        --accent-light: #dbeafe;
        --green: #059669;
        --amber: #d97706;
        --red: #dc2626;
        --gray-50: #f8fafc;
        --gray-100: #f1f5f9;
        --gray-200: #e2e8f0;
        --gray-400: #94a3b8;
        --gray-600: #475569;
        --gray-900: #0f172a;
    }

    /* Banner */
    .vb-banner {
        background: linear-gradient(135deg, var(--navy) 0%, var(--navy-mid) 100%);
        color: #fff; padding: 1.6rem 2rem; border-radius: 10px;
        margin-bottom: 1.5rem; display:flex; align-items:center; gap:1.2rem;
    }
    .vb-banner .vb-logo {
        width:48px; height:48px; border-radius:8px;
        background:var(--accent); display:flex; align-items:center; justify-content:center;
        font-size:22px; font-weight:800; color:#fff; flex-shrink:0; letter-spacing:-1px;
    }
    .vb-banner h1 { margin:0; font-size:1.55rem; font-weight:700; letter-spacing:-.3px; }
    .vb-banner p  { margin:2px 0 0; font-size:.88rem; opacity:.75; }

    /* Sidebar */
    [data-testid="stSidebar"] { background:#f8fafc; }
    .sidebar-brand { font-size:1.1rem; font-weight:700; color:var(--navy); margin-bottom:.6rem; }

    /* Section headers inside content */
    .sec-label {
        font-size:.72rem; font-weight:700; text-transform:uppercase;
        letter-spacing:1px; color:var(--gray-400); margin-bottom:.6rem;
    }

    /* Agent cards */
    .ag-card {
        background:#fff; border:1px solid var(--gray-200); border-radius:8px;
        padding:1rem 1.1rem; margin-bottom:.55rem;
        border-left:3px solid var(--accent);
        transition: box-shadow .15s;
    }
    .ag-card:hover { box-shadow:0 2px 8px rgba(0,0,0,.06); }
    .ag-card .ag-name { font-size:.92rem; font-weight:700; color:var(--navy); }
    .ag-card .ag-desc { font-size:.82rem; color:var(--gray-600); margin-top:3px; line-height:1.45; }

    /* Data source cards */
    .ds-card {
        background:var(--gray-50); border:1px solid var(--gray-200);
        border-radius:8px; padding:1rem 1.1rem;
    }
    .ds-card .ds-title { font-weight:700; font-size:.9rem; color:var(--navy); }
    .ds-card .ds-text  { font-size:.82rem; color:var(--gray-600); margin-top:4px; line-height:1.4; }

    /* KPI row */
    .kpi-row { display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.2rem; }
    .kpi-item {
        flex:1 1 140px; background:#fff; border:1px solid var(--gray-200);
        border-radius:8px; padding:.85rem 1rem; min-width:140px;
    }
    .kpi-item .kpi-label { font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.8px; color:var(--gray-400); }
    .kpi-item .kpi-val   { font-size:1.4rem; font-weight:700; color:var(--navy); margin-top:2px; }

    /* Risk badge inline */
    .risk-badge {
        display:inline-block; padding:2px 10px; border-radius:4px;
        font-size:.78rem; font-weight:700; letter-spacing:.4px;
    }

    /* Hide Streamlit footer */
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="vb-banner">
        <div class="vb-logo">VB</div>
        <div>
            <h1>AI Vectra Bank</h1>
            <p>Multi-Agent Banking Intelligence System &mdash; Azure AI Foundry &bull; Semantic Kernel</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">AI Vectra Bank</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["Dashboard", "Run Analysis", "Report Viewer", "Architecture"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**System**")
    st.caption(
        f"Python {sys.version_info.major}.{sys.version_info.minor}  |  "
        "Agents: 6 (Sequential)\n\n"
        "LLM: Azure GPT-4o  |  Embeddings: Ada-002"
    )
    st.divider()
    st.caption("Udacity  /  Microsoft Agentic AI Nanodegree  /  Project 4")


# ======================================================================
# Shared report renderer
# ======================================================================


def _display_report(data: dict, from_live: bool = False):
    """Render a report dictionary as a professional Streamlit layout."""

    st.divider()
    st.subheader(f"Report  {data.get('report_id', 'N/A')}")

    # --- KPI strip ---
    risk_level = data.get("risk_assessment", "medium")
    fraud_level = data.get("fraud_risk_level", "low")
    kpis_html = f"""
    <div class="kpi-row">
        <div class="kpi-item">
            <div class="kpi-label">Risk Score</div>
            <div class="kpi-val">{data.get('risk_score', 0):.0f}<span style="font-size:.85rem;color:var(--gray-400)"> / 100</span></div>
        </div>
        <div class="kpi-item">
            <div class="kpi-label">Risk Level</div>
            <div class="kpi-val"><span class="risk-badge" style="background:{risk_color(risk_level)}22;color:{risk_color(risk_level)}">{risk_label(risk_level)}</span></div>
        </div>
        <div class="kpi-item">
            <div class="kpi-label">Fraud Risk</div>
            <div class="kpi-val"><span class="risk-badge" style="background:{risk_color(fraud_level)}22;color:{risk_color(fraud_level)}">{risk_label(fraud_level)}</span></div>
        </div>
        <div class="kpi-item">
            <div class="kpi-label">Loan Eligible</div>
            <div class="kpi-val">{'Yes' if data.get('loan_eligibility') else 'No'}</div>
        </div>
        <div class="kpi-item">
            <div class="kpi-label">Financial Health</div>
            <div class="kpi-val">{data.get('financial_health_score', 50):.0f}<span style="font-size:.85rem;color:var(--gray-400)"> / 100</span></div>
        </div>
    </div>
    """
    st.markdown(kpis_html, unsafe_allow_html=True)

    # --- Executive summary ---
    summary = data.get("summary", "")
    if summary:
        st.markdown("#### Executive Summary")
        st.markdown(summary[:3000])

    # --- Key findings ---
    findings = data.get("key_findings", [])
    if findings:
        st.markdown("#### Key Findings")
        for f in findings:
            st.markdown(f"- {f}")

    # --- Two-column detail ---
    col_risk, col_fin = st.columns(2)
    with col_risk:
        st.markdown("#### Risk Profile")
        st.markdown(f"- **Risk Score:** {data.get('risk_score', 'N/A')}")
        st.markdown(f"- **Assessment:** {data.get('risk_assessment', 'N/A')}")
        st.markdown(f"- **Fraud Level:** {data.get('fraud_risk_level', 'N/A')}")
        st.markdown(f"- **Compliance:** {data.get('compliance_status', 'N/A')}")
    with col_fin:
        st.markdown("#### Financial Overview")
        st.markdown(f"- **Health Score:** {data.get('financial_health_score', 'N/A')}")
        st.markdown(f"- **Loan Eligibility:** {'Yes' if data.get('loan_eligibility') else 'No'}")
        metrics = data.get("processing_metrics", {})
        if metrics:
            st.markdown(f"- **Income:** ${metrics.get('customer_income', 0):,.2f}")
            st.markdown(f"- **Credit Score:** {metrics.get('customer_credit_score', 'N/A')}")

    # --- Recommendations / Next actions ---
    recs = data.get("recommendations", [])
    actions = data.get("next_best_actions", [])
    col_rec, col_act = st.columns(2)
    with col_rec:
        st.markdown("#### Recommendations")
        for r in recs:
            st.markdown(f"- {r}")
    with col_act:
        st.markdown("#### Next Best Actions")
        for a in actions:
            st.markdown(f"- {a}")

    # --- Agent contributions ---
    contributions = data.get("agent_contributions", {})
    if contributions:
        st.divider()
        st.markdown("#### Agent Contributions")
        tabs = st.tabs(list(contributions.keys()))
        for tab, (agent_name, output) in zip(tabs, contributions.items()):
            with tab:
                st.markdown(output[:5000])

    # --- Agent activations ---
    activations = data.get("agent_activations", [])
    if activations:
        st.divider()
        st.markdown("#### Agent Performance")
        perf_cols = st.columns(min(len(activations), 6))
        for col, act in zip(perf_cols, activations):
            with col:
                status = "PASS" if act.get("success") else "FAIL"
                name = act.get("agent_name", "Unknown").replace("Enhanced_", "")
                duration = act.get("duration_seconds", 0)
                st.metric(f"{name}  [{status}]", f"{duration:.1f}s")

    # --- Processing metrics ---
    metrics = data.get("processing_metrics", {})
    if metrics:
        st.divider()
        st.markdown("#### Processing Metrics")
        pm1, pm2, pm3, pm4 = st.columns(4)
        pm1.metric("Total Time", f"{metrics.get('total_processing_time_seconds', 0):.1f}s")
        pm2.metric("Agents Activated", metrics.get("agents_activated", 0))
        pm3.metric("Policies Referenced", metrics.get("policies_referenced", 0))
        pm4.metric("RAG Results", metrics.get("rag_results_returned", 0))

    # --- Raw JSON ---
    with st.expander("View Raw JSON"):
        st.json(data)


# ======================================================================
# PAGE: Dashboard
# ======================================================================
if page == "Dashboard":
    st.header("System Dashboard")

    # --- Summary KPIs ---
    saved = load_saved_reports()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Saved Reports", len(saved))
    k2.metric("Customer Profiles", len(CUSTOMER_PROFILES))
    k3.metric("AI Agents", 6)
    k4.metric("Data Sources", 3)

    # ---- Dynamic Workflow Visualisation ----
    st.divider()
    st.markdown('<div class="sec-label">Agent Workflow Pipeline</div>', unsafe_allow_html=True)
    st.caption(
        "The pipeline below shows the six sequential stages that every customer query passes through. "
        "Each stage builds on the output of the previous one before the Synthesis Coordinator "
        "produces the final executive report."
    )

    # Render the interactive pipeline (all idle on dashboard)
    components.html(_render_pipeline_html(active_index=-1), height=160, scrolling=True)

    # Expandable detail cards for each stage
    for i, stage in enumerate(AGENT_STAGES):
        with st.expander(f"Stage {i+1}  —  {stage['name']}"):
            st.markdown(stage["desc"])
            c1, c2 = st.columns(2)
            c1.markdown(f"**Receives:** {stage['inputs']}")
            c2.markdown(f"**Produces:** {stage['outputs']}")

    # ---- Data Sources ----
    st.divider()
    st.markdown('<div class="sec-label">Data Sources</div>', unsafe_allow_html=True)
    ds1, ds2, ds3 = st.columns(3)
    with ds1:
        st.markdown(
            '<div class="ds-card"><div class="ds-title">Azure SQL Database</div>'
            '<div class="ds-text">Customer transactions, financial records, and account data.</div></div>',
            unsafe_allow_html=True,
        )
    with ds2:
        st.markdown(
            '<div class="ds-card"><div class="ds-title">ChromaDB  (RAG Vector Store)</div>'
            '<div class="ds-text">Banking policy vectors indexed with text-embedding-ada-002.</div></div>',
            unsafe_allow_html=True,
        )
    with ds3:
        st.markdown(
            '<div class="ds-card"><div class="ds-title">Blob / Local Storage</div>'
            '<div class="ds-text">Raw policy documents: fraud detection, risk assessment, loan eligibility.</div></div>',
            unsafe_allow_html=True,
        )

    # ---- Customer Profiles ----
    st.divider()
    st.markdown('<div class="sec-label">Customer Profiles</div>', unsafe_allow_html=True)
    for cid, info in CUSTOMER_PROFILES.items():
        with st.expander(f"Customer {cid}  —  {info['name']}  ({info['risk_tier']} risk)"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Annual Income", f"${info['income']:,}")
            c2.metric("Credit Score", info["credit_score"])
            c3.metric("Account Type", info["account_type"])
            st.markdown(f"**Banking Products:** {', '.join(info['products'])}")


# ======================================================================
# PAGE: Run Analysis
# ======================================================================
elif page == "Run Analysis":
    st.header("Run Multi-Agent Analysis")
    st.markdown(
        "Submit a customer query to execute the full six-agent sequential "
        "pipeline. Each stage is visualised in real time below."
    )

    col_left, col_right = st.columns([2, 1])

    with col_left:
        customer_id = st.selectbox(
            "Select Customer",
            list(CUSTOMER_PROFILES.keys()),
            format_func=lambda x: f"Customer {x}  —  {CUSTOMER_PROFILES[x]['name']}",
        )
        query_option = st.radio(
            "Query Input", ["Sample query", "Custom query"], horizontal=True,
        )
        if query_option == "Sample query":
            customer_query = st.selectbox("Sample Queries", SAMPLE_QUERIES)
        else:
            customer_query = st.text_area(
                "Enter your banking query", height=100,
                placeholder="e.g., Review my account for suspicious activity and assess my loan eligibility...",
            )

    with col_right:
        st.markdown("**Customer Preview**")
        info = CUSTOMER_PROFILES[customer_id]
        st.markdown(f"**Name:** {info['name']}")
        st.markdown(f"**Income:** ${info['income']:,}")
        st.markdown(f"**Credit Score:** {info['credit_score']}")
        st.markdown(f"**Risk Tier:** {info['risk_tier']}")
        st.markdown(f"**Products:** {len(info['products'])}")

    st.divider()

    # --- Live pipeline placeholder ---
    pipeline_slot = st.empty()
    pipeline_slot.markdown("")  # clear

    if st.button("Run Analysis Pipeline", type="primary", use_container_width=True):
        if not customer_query or not customer_query.strip():
            st.error("Please enter or select a query.")
        else:
            try:
                from main_starter import EnhancedBankingSequentialOrchestration

                # Show pipeline as all-idle
                completed = [False] * 6
                components.html(
                    _render_pipeline_html(active_index=0, completed=completed),
                    height=160, scrolling=True,
                )

                progress = st.progress(0, text="Initialising system...")
                status_msg = st.empty()

                with st.spinner("Running 6-agent sequential orchestration..."):
                    progress.progress(5, text="Stage 1/6  Data Gatherer...")
                    system = EnhancedBankingSequentialOrchestration()

                    progress.progress(15, text="Executing agent pipeline...")
                    start_time = time.time()
                    report = run_async(
                        system.run_enhanced_analysis(customer_id, customer_query)
                    )
                    elapsed = time.time() - start_time

                    progress.progress(95, text="Generating report...")

                    report_path = REPORTS_DIR / f"ui_report_{report.report_id}.json"
                    report_path.write_text(
                        report.model_dump_json(indent=2), encoding="utf-8"
                    )
                    progress.progress(100, text="Complete")

                # Show pipeline completed
                components.html(
                    _render_pipeline_html(active_index=-1, completed=[True] * 6),
                    height=160, scrolling=True,
                )

                st.success(
                    f"Analysis complete in {elapsed:.1f}s  —  "
                    f"Report ID: **{report.report_id}**"
                )
                _display_report(report.model_dump(), from_live=True)

            except Exception as exc:
                st.error(f"Pipeline error: {exc}")
                st.exception(exc)


# ======================================================================
# PAGE: Report Viewer
# ======================================================================
elif page == "Report Viewer":
    st.header("Report Viewer")

    saved = load_saved_reports()
    if not saved:
        st.info("No saved reports found. Run an analysis or check the reports/ directory.")
    else:
        labels = []
        for r in saved:
            rid = r.get("report_id", "unknown")
            cid = r.get("customer_id", "?")
            ts = r.get("generated_at", "")
            labels.append(f"{rid}  —  Customer {cid}  ({ts[:19] if ts else 'N/A'})")

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
elif page == "Architecture":
    st.header("System Architecture")
    st.markdown(
        "AI Vectra Bank uses a **sequential multi-agent orchestration** "
        "pattern built on Microsoft Semantic Kernel. Six specialised AI agents "
        "process banking queries in sequence, each building on the findings of "
        "the previous agent."
    )

    # --- Live pipeline reference ---
    st.markdown('<div class="sec-label">Pipeline Overview</div>', unsafe_allow_html=True)
    components.html(
        _render_pipeline_html(active_index=-1, completed=[True] * 6),
        height=160, scrolling=True,
    )

    st.divider()
    st.markdown("#### High-Level Architecture")
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
        Orch["Sequential Orchestrator"]
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
        SQL[("Azure SQL")]
        Chroma[("ChromaDB")]
        Blob["Blob Storage"]
    end

    subgraph AILayer["Azure AI Foundry"]
        direction LR
        GPT["GPT-4o"]
        Ada["Ada-002 Embeddings"]
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

    st.markdown("#### Agent Pipeline Sequence")
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

    st.markdown("#### Data Flow")
    st.markdown(
        """
```mermaid
flowchart LR
    subgraph Ingestion["Document Ingestion"]
        MD["Markdown Policies"] --> Chunk["Chunking"]
        Chunk --> Embed["Ada-002 Embeddings"]
        Embed --> Store["ChromaDB Collections"]
    end

    subgraph Query["Query Processing"]
        Q["User Query"] --> Hybrid["Hybrid Search"]
        Store --> Hybrid
        Hybrid --> Context["RAG Context"]
    end

    subgraph SQL["SQL Pipeline"]
        DB[("Azure SQL")] --> Fetch["DataConnector"]
        Fetch --> Profile["Customer Profile"]
    end

    Context --> Agents["Agent Pipeline"]
    Profile --> Agents
    Agents --> Report["JSON Report"]
```
        """
    )

    st.divider()
    st.markdown("#### Technology Stack")
    tech_data = {
        "Component": [
            "Orchestration", "LLM", "Embeddings", "Vector Store",
            "Database", "Document Store", "Data Models", "UI Framework",
        ],
        "Technology": [
            "Microsoft Semantic Kernel 1.37", "Azure OpenAI GPT-4o",
            "text-embedding-ada-002 (1536-dim)", "ChromaDB 1.0.20",
            "Azure SQL Database", "Azure Blob / Local Fallback",
            "Pydantic v2", "Streamlit",
        ],
        "Purpose": [
            "Sequential agent orchestration", "Agent reasoning and generation",
            "Document vectorisation for RAG", "Semantic search over banking policies",
            "Customer transactions and financial data", "Raw policy document storage",
            "Validated data models with type safety", "Interactive web dashboard",
        ],
    }
    st.table(tech_data)
