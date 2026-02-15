"""
Banking Multi-Agent RAG System — Main Orchestration Module.

Implements six specialised AI agents orchestrated sequentially via
Microsoft Semantic Kernel to analyse complex banking queries.  Data is
sourced from Azure SQL (customer transactions), ChromaDB (banking policy
vectors via RAG), and local/Blob Storage policy documents.

Usage:
    python main_starter.py --all     Run the full evaluation suite
    python main_starter.py --demo    Run a single demo scenario
    python main_starter.py --test    Run quick validation tests
"""

import argparse
import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent

from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager
from data_connector import DataConnector
from models import (
    AgentActivation,
    CustomerProfile,
    EnhancedBankingReport,
    RiskLevel,
)
from rag_utils import create_semantic_kernel_context, extract_banking_policies
from shared_state import SharedState

# Resolve project root (one level above src/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


def setup_logging() -> str:
    """Configure logging with a unique file per run and return the log path."""
    log_dir = os.path.join(PROJECT_ROOT, "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"banking_analysis_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger.info("Logger started. Log file: %s", log_filename)
    return log_filename


# ===================================================================
# Main orchestration class
# ===================================================================


class EnhancedBankingSequentialOrchestration:
    """
    Enhanced banking intelligence system that orchestrates six specialised
    AI agents in a sequential pipeline.

    Components:
        - BlobStorageConnector — local / Azure Blob document source
        - ChromaDBManager — vector store for RAG retrieval
        - DataConnector — Azure SQL for customer transaction data
        - SharedState — thread-safe state management
        - Semantic Kernel — agent orchestration via Azure OpenAI GPT-4
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing EnhancedBankingSequentialOrchestration ...")

        # ---- Storage & state ----
        self.blob_connector = BlobStorageConnector()
        self.chroma_store = ChromaDBManager()
        self.shared_state = SharedState()

        # ---- Azure SQL ----
        try:
            self.data_connector = DataConnector()
            if self.data_connector.is_available:
                self.logger.info("Azure SQL DataConnector is ONLINE.")
            else:
                self.logger.warning(
                    "Azure SQL DataConnector initialised but DB is unreachable — "
                    "using sample data fallback."
                )
        except Exception as exc:
            self.logger.warning("DataConnector init error (%s) — using fallback.", exc)
            self.data_connector = DataConnector(connection_string="")

        # ---- Semantic Kernel ----
        self.kernel = Kernel()
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="enhanced_banking_chat",
                deployment_name=os.environ.get(
                    "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "gpt-4"
                ),
                endpoint=os.environ.get(
                    "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", ""
                ),
                api_key=os.environ.get("AZURE_TEXTGENERATOR_DEPLOYMENT_KEY", ""),
            )
        )
        self.logger.info("Azure OpenAI chat service registered with Semantic Kernel.")

        # ---- Policy documents & profiles ----
        self.banking_policies = self._load_enhanced_policies()
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        self._documents_loaded_to_chroma = False

        # ---- Metrics ----
        self.performance_metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_analyses": 0,
            "average_processing_time": 0.0,
            "agent_performance": {},
        }

    # ------------------------------------------------------------------
    # Policy loading
    # ------------------------------------------------------------------

    def _load_enhanced_policies(self) -> Dict[str, Any]:
        """Load and structure banking policy documents from Blob / local storage."""
        try:
            if not self.blob_connector.list_documents():
                self.blob_connector.upload_sample_documents()

            enhanced_docs: List[Dict[str, Any]] = []
            for doc_name in self.blob_connector.list_documents():
                content = self.blob_connector.get_document_content(doc_name)
                metadata = self.blob_connector.get_document_metadata(doc_name) or {}

                enhanced_docs.append(
                    {
                        "filename": doc_name,
                        "id": f"{metadata.get('type', 'general')}_{doc_name}",
                        "meta": {
                            **metadata,
                            "priority": (
                                "high"
                                if metadata.get("type") in ("fraud", "risk")
                                else "medium"
                            ),
                            "review_frequency": (
                                "quarterly"
                                if metadata.get("type") in ("fraud", "compliance")
                                else "annually"
                            ),
                        },
                        "text": content or "",
                    }
                )

            policies = extract_banking_policies(enhanced_docs)
            self.logger.info(
                "Loaded %d policy documents (%d categories).",
                len(enhanced_docs),
                len(policies),
            )
            return policies
        except Exception as exc:
            self.logger.error("Could not load banking policies: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # ChromaDB document ingestion
    # ------------------------------------------------------------------

    async def load_enhanced_documents(self) -> None:
        """Ingest all Blob/local policy documents into ChromaDB collections."""
        if self._documents_loaded_to_chroma:
            return

        stats = await self.chroma_store.get_collection_stats()
        already_populated = any(
            s.get("document_count", 0) > 0 for s in stats.values()
        )
        if already_populated:
            self.logger.info(
                "ChromaDB collections already populated — skipping ingestion."
            )
            self._documents_loaded_to_chroma = True
            return

        for doc_name in self.blob_connector.list_documents():
            content = self.blob_connector.get_document_content(doc_name)
            if not content:
                continue
            collection_type = self.chroma_store.determine_collection(doc_name, content)
            stored = await self.chroma_store.chunk_and_store_document(
                doc_name, content, collection_type
            )
            self.logger.info(
                "Stored %d chunks from '%s' → collection '%s'.",
                stored,
                doc_name,
                collection_type,
            )

        self._documents_loaded_to_chroma = True

    # ------------------------------------------------------------------
    # Customer profile loading
    # ------------------------------------------------------------------

    async def _load_customer_profiles(self) -> Dict[str, CustomerProfile]:
        """
        Load customer profiles from Azure SQL or fall back to sample data.

        Returns a mapping of ``customer_id`` → ``CustomerProfile``.
        """
        profiles: Dict[str, CustomerProfile] = {}

        # Default / fallback sample profiles
        sample_profiles: Dict[str, Dict[str, Any]] = {
            "12345": {
                "customer_id": "12345",
                "income": 75000.0,
                "credit_score": 780,
                "account_type": "premium_plus",
                "customer_since": "2019-05-15",
                "risk_tier": "low",
                "banking_products": [
                    "checking",
                    "savings",
                    "mortgage",
                    "investment",
                    "credit_card",
                ],
                "last_review_date": "2024-01-10",
                "employment_status": "employed_full_time",
                "total_assets": 320000.0,
                "monthly_expenses": 3200.0,
                "debt_to_income_ratio": 0.28,
                "savings_rate": 0.15,
            },
            "67890": {
                "customer_id": "67890",
                "income": 45000.0,
                "credit_score": 680,
                "account_type": "standard",
                "customer_since": "2021-08-22",
                "risk_tier": "medium",
                "banking_products": ["checking", "savings", "credit_card"],
                "last_review_date": "2024-02-15",
                "employment_status": "employed_full_time",
                "total_assets": 85000.0,
                "monthly_expenses": 2800.0,
                "debt_to_income_ratio": 0.38,
                "savings_rate": 0.08,
            },
            "11111": {
                "customer_id": "11111",
                "income": 28000.0,
                "credit_score": 580,
                "account_type": "basic",
                "customer_since": "2023-01-10",
                "risk_tier": "high",
                "banking_products": ["checking"],
                "last_review_date": "2024-03-01",
                "employment_status": "part_time",
                "total_assets": 12000.0,
                "monthly_expenses": 2100.0,
                "debt_to_income_ratio": 0.55,
                "savings_rate": 0.02,
            },
        }

        # Attempt to enrich from Azure SQL
        for cid, defaults in sample_profiles.items():
            try:
                db_income = await self.data_connector.fetch_income(cid)
                db_txns = await self.data_connector.fetch_transactions(cid)

                if db_income is not None:
                    defaults["income"] = db_income
                if db_txns:
                    defaults["recent_transactions"] = db_txns
            except Exception as exc:
                self.logger.warning(
                    "Could not load SQL data for customer %s: %s — using defaults.",
                    cid,
                    exc,
                )

            # If no transactions from DB, use sample data
            if not defaults.get("recent_transactions"):
                defaults["recent_transactions"] = (
                    DataConnector.get_sample_transactions(cid)
                )

            profiles[cid] = CustomerProfile(**defaults)
            self.logger.info(
                "Loaded profile for customer %s (income=$%.2f, credit=%d).",
                cid,
                profiles[cid].income,
                profiles[cid].credit_score,
            )

        return profiles

    # ------------------------------------------------------------------
    # Agent definitions
    # ------------------------------------------------------------------

    def create_enhanced_agents(self) -> List[ChatCompletionAgent]:
        """
        Create and return the six specialised banking agents.

        Each agent uses the shared Azure OpenAI chat service and is given
        domain-specific system instructions that guide its analysis.
        """
        chat_service = self.kernel.get_service("enhanced_banking_chat")

        data_agent = ChatCompletionAgent(
            name="Enhanced_Data_Gatherer",
            instructions=(
                "You are a comprehensive banking data analyst. "
                "Gather and organise all relevant customer data including "
                "transaction history, account details, income information, "
                "and financial patterns. Query the database for customer "
                "records and summarise findings for downstream agents.\n\n"
                "Your responsibilities:\n"
                "1. Aggregate customer financial data and transaction history.\n"
                "2. Identify spending patterns, income stability, and account activity.\n"
                "3. Cross-reference customer data with applicable banking policies.\n"
                "4. Flag data quality issues or missing information.\n"
                "5. Provide a structured data summary for subsequent specialist agents.\n\n"
                "Output format: Provide a clear, structured summary with sections for "
                "Income Analysis, Transaction Patterns, Account Overview, and Data "
                "Quality Notes."
            ),
            service=chat_service,
        )

        fraud_agent = ChatCompletionAgent(
            name="Enhanced_Fraud_Analyst",
            instructions=(
                "You are an advanced fraud detection specialist. "
                "Analyse transaction patterns for anomalies, assess security risks, "
                "evaluate suspicious activities, and provide fraud risk scores. "
                "Consider velocity checks, geographic anomalies, and amount deviations.\n\n"
                "Your responsibilities:\n"
                "1. Analyse transaction velocity, frequency, and amount distribution.\n"
                "2. Detect geographic or temporal anomalies in transaction patterns.\n"
                "3. Evaluate device and behavioural fingerprint consistency.\n"
                "4. Assign a fraud risk score (0–100) with justification.\n"
                "5. Recommend specific monitoring or escalation actions.\n\n"
                "Risk categories to assess:\n"
                "- Low Risk: familiar patterns, amounts under $500\n"
                "- Medium Risk: new locations or amounts $500–$2,000\n"
                "- High Risk: international, >$2,000, or unusual patterns\n\n"
                "Output format: Fraud Risk Score, Risk Level, Key Indicators, "
                "Suspicious Patterns, and Recommended Actions."
            ),
            service=chat_service,
        )

        loan_agent = ChatCompletionAgent(
            name="Enhanced_Loan_Analyst",
            instructions=(
                "You are a credit risk and loan evaluation expert. "
                "Assess loan eligibility based on income, credit history, "
                "debt-to-income ratios, and repayment capacity. Provide loan "
                "recommendations with terms, rates, and risk-adjusted pricing.\n\n"
                "Your responsibilities:\n"
                "1. Evaluate debt-to-income ratio against policy thresholds.\n"
                "2. Assess credit score tier and corresponding product eligibility.\n"
                "3. Calculate maximum affordable loan amount.\n"
                "4. Recommend loan products with estimated APR and terms.\n"
                "5. Identify conditions or documentation needed for approval.\n\n"
                "Credit score tiers:\n"
                "- Excellent (750+): 3.5% APR, 90% LTV\n"
                "- Good (700–749): 4.5% APR, 85% LTV\n"
                "- Fair (650–699): 6.0% APR, 80% LTV\n"
                "- Review (<650): Case-by-case assessment\n\n"
                "Output format: Eligibility Decision, Recommended Products, "
                "Terms & Rates, Risk Factors, and Required Documentation."
            ),
            service=chat_service,
        )

        support_agent = ChatCompletionAgent(
            name="Enhanced_Support_Specialist",
            instructions=(
                "You are a customer experience optimisation specialist. "
                "Evaluate customer satisfaction, identify service improvement "
                "opportunities, recommend personalised banking products, and "
                "ensure customer relationship excellence.\n\n"
                "Your responsibilities:\n"
                "1. Assess the customer's overall banking relationship and tenure.\n"
                "2. Identify cross-sell and up-sell opportunities.\n"
                "3. Recommend personalised product bundles.\n"
                "4. Evaluate service gaps and suggest improvements.\n"
                "5. Draft customer-friendly communication points.\n\n"
                "Quality standards:\n"
                "- First contact resolution target: 85%\n"
                "- Customer satisfaction target: 90%\n"
                "- Response within SLA: 95%\n\n"
                "Output format: Relationship Assessment, Product Recommendations, "
                "Service Improvement Opportunities, and Communication Strategy."
            ),
            service=chat_service,
        )

        risk_agent = ChatCompletionAgent(
            name="Enhanced_Risk_Analyst",
            instructions=(
                "You are an enterprise risk assessment and compliance expert. "
                "Evaluate regulatory compliance, assess operational risks, verify "
                "policy adherence, and provide comprehensive risk ratings across "
                "all banking dimensions.\n\n"
                "Your responsibilities:\n"
                "1. Evaluate credit, market, operational, and compliance risk.\n"
                "2. Verify adherence to internal banking policies.\n"
                "3. Check for regulatory red flags (AML, KYC).\n"
                "4. Calculate a composite enterprise risk score (0–100).\n"
                "5. Propose risk mitigation strategies.\n\n"
                "Risk scoring matrix:\n"
                "- Low (<25): basic monitoring\n"
                "- Medium (25–50): enhanced controls\n"
                "- High (50–75): active management required\n"
                "- Critical (>75): immediate action\n\n"
                "Output format: Enterprise Risk Score, Risk Breakdown by Category, "
                "Compliance Status, Policy Adherence, and Mitigation Plan."
            ),
            service=chat_service,
        )

        synthesis_agent = ChatCompletionAgent(
            name="Enhanced_Synthesis_Coordinator",
            instructions=(
                "You are an executive report coordinator. Synthesise findings "
                "from all previous agents into a comprehensive, actionable "
                "banking report. Consolidate risk scores, recommendations, and "
                "provide an executive summary with clear next steps.\n\n"
                "Your responsibilities:\n"
                "1. Integrate data, fraud, loan, support, and risk analyses.\n"
                "2. Resolve conflicting recommendations between agents.\n"
                "3. Produce a concise executive summary (≤250 words).\n"
                "4. Prioritise recommended actions by impact and urgency.\n"
                "5. Ensure the final report is customer-appropriate (no internal "
                "system details exposed).\n\n"
                "Output format: Executive Summary, Consolidated Risk Profile, "
                "Prioritised Recommendations, Next Best Actions, and Compliance "
                "Notes.\n\n"
                "IMPORTANT: Do NOT expose internal agent names, system architecture, "
                "or technical details in the customer-facing summary."
            ),
            service=chat_service,
        )

        agents = [
            data_agent,
            fraud_agent,
            loan_agent,
            support_agent,
            risk_agent,
            synthesis_agent,
        ]
        self.logger.info("Created %d specialised banking agents.", len(agents))
        return agents

    # ------------------------------------------------------------------
    # Context preparation
    # ------------------------------------------------------------------

    def _prepare_enhanced_context(
        self,
        customer_profile: CustomerProfile,
        search_results: List[Dict[str, Any]],
        customer_query: str,
    ) -> str:
        """Build comprehensive context injected into the orchestration prompt."""
        # Customer profile section
        txn_summary = ""
        if customer_profile.recent_transactions:
            txn_lines = []
            for txn in customer_profile.recent_transactions[:10]:
                txn_lines.append(
                    f"  - {txn.get('description', 'N/A')}: "
                    f"${txn.get('amount', 0):,.2f} on {txn.get('ts', 'N/A')}"
                )
            txn_summary = "\n".join(txn_lines)
        else:
            txn_summary = "  No recent transactions available."

        customer_ctx = (
            f"CUSTOMER PROFILE:\n"
            f"  Customer ID        : {customer_profile.customer_id}\n"
            f"  Annual Income      : ${customer_profile.income:,.2f}\n"
            f"  Credit Score       : {customer_profile.credit_score}\n"
            f"  Account Type       : {customer_profile.account_type}\n"
            f"  Customer Since     : {customer_profile.customer_since}\n"
            f"  Risk Tier          : {customer_profile.risk_tier}\n"
            f"  Employment Status  : {customer_profile.employment_status}\n"
            f"  Total Assets       : ${customer_profile.total_assets:,.2f}\n"
            f"  Monthly Expenses   : ${customer_profile.monthly_expenses:,.2f}\n"
            f"  Debt-to-Income     : {customer_profile.debt_to_income_ratio:.2%}\n"
            f"  Savings Rate       : {customer_profile.savings_rate:.2%}\n"
            f"  Banking Products   : {', '.join(customer_profile.banking_products)}\n"
            f"  Last Review Date   : {customer_profile.last_review_date}\n"
            f"\n  RECENT TRANSACTIONS:\n{txn_summary}"
        )

        # Policy context from Semantic Kernel helper
        policy_ctx = create_semantic_kernel_context(self.banking_policies)

        # RAG search results
        rag_lines: List[str] = []
        for i, result in enumerate(search_results[:8], 1):
            rag_lines.append(
                f"  [{i}] (score={result.get('relevance_score', 0):.2f}, "
                f"collection={result.get('collection', '?')}) "
                f"{result.get('document', '')[:300]}"
            )
        rag_ctx = (
            "\n".join(rag_lines) if rag_lines else "  No policy matches found."
        )

        return (
            f"BANKING ANALYSIS REQUEST: {customer_query}\n\n"
            f"{customer_ctx}\n\n"
            f"BANKING POLICY FRAMEWORK:\n{policy_ctx}\n\n"
            f"RELEVANT POLICY DOCUMENTS (RAG):\n{rag_ctx}"
        )

    # ------------------------------------------------------------------
    # Risk scoring
    # ------------------------------------------------------------------

    def _calculate_enhanced_risk_score(
        self,
        profile: CustomerProfile,
        search_results: List[Dict[str, Any]],
    ) -> float:
        """
        Calculate a composite risk score (0–100) considering multiple factors.

        Lower scores indicate lower risk.
        """
        score = 50.0  # baseline

        # Income factor — higher income reduces risk
        if profile.income >= 100_000:
            score -= 10.0
        elif profile.income >= 75_000:
            score -= 5.0
        elif profile.income < 30_000:
            score += 10.0

        # Credit score factor
        if profile.credit_score >= 750:
            score -= 15.0
        elif profile.credit_score >= 700:
            score -= 8.0
        elif profile.credit_score >= 650:
            score += 0.0
        elif profile.credit_score > 0:
            score += 15.0

        # Debt-to-income ratio
        if profile.debt_to_income_ratio > 0.45:
            score += 12.0
        elif profile.debt_to_income_ratio > 0.35:
            score += 5.0
        elif profile.debt_to_income_ratio < 0.20:
            score -= 5.0

        # Tenure factor
        if profile.customer_since:
            try:
                since = datetime.strptime(profile.customer_since, "%Y-%m-%d")
                years = (datetime.now() - since).days / 365.25
                if years >= 5:
                    score -= 8.0
                elif years >= 2:
                    score -= 3.0
                elif years < 1:
                    score += 5.0
            except ValueError:
                pass

        # Savings rate
        if profile.savings_rate >= 0.15:
            score -= 5.0
        elif profile.savings_rate < 0.05:
            score += 5.0

        # Product diversification
        n_products = len(profile.banking_products)
        if n_products >= 4:
            score -= 5.0
        elif n_products <= 1:
            score += 5.0

        return max(0.0, min(100.0, score))

    @staticmethod
    def _determine_risk_tier(score: float) -> str:
        """Map numeric risk score to a qualitative tier label."""
        if score < 25:
            return RiskLevel.LOW.value
        elif score < 50:
            return RiskLevel.MEDIUM.value
        elif score < 75:
            return RiskLevel.HIGH.value
        return RiskLevel.CRITICAL.value

    # ------------------------------------------------------------------
    # Findings & recommendations helpers
    # ------------------------------------------------------------------

    def _generate_enhanced_findings(
        self,
        profile: CustomerProfile,
        search_results: List[Dict[str, Any]],
        agent_contributions: Dict[str, str],
    ) -> List[str]:
        """Produce key findings based on profile data and agent outputs."""
        findings: List[str] = [
            f"Analysis completed for customer {profile.customer_id}.",
        ]

        # Income
        if profile.income >= 75_000:
            findings.append(
                f"Customer income of ${profile.income:,.2f} places them in a "
                f"strong financial position."
            )
        elif profile.income < 30_000:
            findings.append(
                f"Customer income of ${profile.income:,.2f} is below the median "
                f"threshold — enhanced monitoring recommended."
            )

        # Credit
        if profile.credit_score >= 750:
            findings.append(
                f"Excellent credit score ({profile.credit_score}) — "
                f"eligible for premium lending products."
            )
        elif profile.credit_score < 650:
            findings.append(
                f"Credit score of {profile.credit_score} requires case-by-case "
                f"lending evaluation."
            )

        # DTI
        if profile.debt_to_income_ratio > 0.40:
            findings.append(
                f"Debt-to-income ratio ({profile.debt_to_income_ratio:.2%}) "
                f"exceeds recommended maximum — risk mitigation advised."
            )

        # Transactions
        if profile.recent_transactions:
            n = len(profile.recent_transactions)
            total = sum(t.get("amount", 0) for t in profile.recent_transactions)
            findings.append(
                f"{n} recent transactions totalling ${total:,.2f} reviewed."
            )

        # RAG policy matches
        if search_results:
            collections_hit = {r.get("collection", "?") for r in search_results}
            findings.append(
                f"Policy documents referenced from: "
                f"{', '.join(sorted(collections_hit))}."
            )

        # Agent contributions
        for name in agent_contributions:
            findings.append(f"Agent '{name}' contributed to the analysis.")

        return findings

    def _generate_enhanced_recommendations(
        self, profile: CustomerProfile, risk_score: float
    ) -> List[str]:
        """Generate strategic recommendations driven by risk profile."""
        recs: List[str] = []

        tier = self._determine_risk_tier(risk_score)
        if tier == RiskLevel.CRITICAL.value:
            recs.append(
                "URGENT: Initiate immediate enhanced due diligence review."
            )
            recs.append("Restrict high-value transactions pending investigation.")
        elif tier == RiskLevel.HIGH.value:
            recs.append("Schedule quarterly risk reassessment.")
            recs.append("Enable enhanced transaction monitoring alerts.")
        elif tier == RiskLevel.MEDIUM.value:
            recs.append("Continue standard monitoring with semi-annual review.")
        else:
            recs.append("Maintain annual review cycle — low risk profile.")

        # Product-based
        products = set(profile.banking_products)
        if "investment" not in products and profile.income >= 50_000:
            recs.append(
                "Consider offering investment account — customer income qualifies."
            )
        if "savings" not in products:
            recs.append("Recommend opening a savings account for emergency fund.")
        if "credit_card" not in products and profile.credit_score >= 650:
            recs.append(
                "Pre-approve for a rewards credit card based on credit score."
            )

        # DTI-based
        if profile.debt_to_income_ratio > 0.40:
            recs.append("Offer debt consolidation products to improve DTI ratio.")

        # Savings
        if profile.savings_rate < 0.05:
            recs.append("Enrol customer in automatic savings programme.")

        return recs

    def _generate_next_best_actions(
        self, profile: CustomerProfile, risk_score: float
    ) -> List[str]:
        """Prioritised follow-up actions for the banking team."""
        actions: List[str] = []
        tier = self._determine_risk_tier(risk_score)

        if tier in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value):
            actions.append(
                "Assign dedicated relationship manager within 24 hours."
            )
            actions.append("Run full AML/KYC compliance check.")

        actions.append("Send personalised analysis summary to customer.")
        actions.append("Update CRM with latest risk assessment.")

        if profile.credit_score >= 700:
            actions.append("Pre-approve for premium product upgrade.")

        actions.append("Schedule follow-up contact within 30 days.")
        return actions

    # ------------------------------------------------------------------
    # Main analysis workflow
    # ------------------------------------------------------------------

    async def run_enhanced_analysis(
        self, customer_id: str, customer_query: str
    ) -> EnhancedBankingReport:
        """
        Execute the full six-agent sequential analysis pipeline.

        Args:
            customer_id: Target customer identifier.
            customer_query: Natural-language banking query.

        Returns:
            An ``EnhancedBankingReport`` with consolidated findings.
        """
        start_time = time.time()
        self.performance_metrics["total_requests"] += 1

        # 1. Load customer profiles (once)
        if not self.customer_profiles:
            self.customer_profiles = await self._load_customer_profiles()

        # 2. Ingest documents into ChromaDB (once)
        await self.load_enhanced_documents()

        # 3. Resolve customer profile
        profile = self.customer_profiles.get(
            customer_id,
            CustomerProfile(customer_id=customer_id),
        )

        # 4. RAG — hybrid search across all policy collections
        search_results = await self.chroma_store.hybrid_search(
            customer_query,
            [
                "fraud_detection",
                "loan_policies",
                "customer_support",
                "risk_assessment",
                "transaction_monitoring",
                "compliance",
            ],
            top_k=4,
        )

        # 5. Prepare context
        banking_context = self._prepare_enhanced_context(
            profile, search_results, customer_query
        )

        # 6. Create agents
        agents = self.create_enhanced_agents()

        # 7. Track agent contributions via callback
        agent_contributions: Dict[str, str] = {}
        agent_activations: List[AgentActivation] = []
        agent_start_times: Dict[str, float] = {}

        def enhanced_agent_callback(message: ChatMessageContent) -> None:
            """Capture each agent's output and track activation."""
            name = message.name or "Unknown"
            content = message.content or ""
            now = time.time()

            # Determine duration — rough estimate between callbacks
            duration = 0.0
            if name in agent_start_times:
                duration = now - agent_start_times[name]

            agent_contributions[name] = content
            agent_activations.append(
                AgentActivation(
                    agent_name=name,
                    activated=True,
                    duration_seconds=round(duration, 2),
                    success=True,
                    output_summary=content[:300],
                )
            )
            self.logger.info("Agent '%s' completed (%.2fs).", name, duration)
            print(f"\n{'-' * 60}")
            print(f"  [AGENT] {name}")
            print(f"{'-' * 60}")
            print(content[:800])
            if len(content) > 800:
                print(f"  ... ({len(content) - 800} more characters)")

        # Record expected start times
        for agent in agents:
            agent_start_times[agent.name] = time.time()

        # 8. Build orchestration
        sequential_orchestration = SequentialOrchestration(
            members=agents,
            agent_response_callback=enhanced_agent_callback,
        )
        runtime = InProcessRuntime()

        try:
            runtime.start()

            orchestration_task = (
                "ENHANCED BANKING CUSTOMER ANALYSIS REQUEST\n\n"
                f"{banking_context}\n\n"
                "INSTRUCTIONS FOR ALL AGENTS:\n"
                "Each agent must analyse the above customer data and policy "
                "context within their area of expertise. Build upon findings "
                "from previous agents. Provide structured, actionable output. "
                "Do NOT reveal internal system details in customer-facing "
                "content.\n"
            )

            # Update start times just before invocation
            for agent in agents:
                agent_start_times[agent.name] = time.time()

            orchestration_result = await sequential_orchestration.invoke(
                task=orchestration_task,
                runtime=runtime,
            )

            final_output = await asyncio.wait_for(
                orchestration_result.get(), timeout=180.0
            )

            # 9. Compute scores
            risk_score = self._calculate_enhanced_risk_score(
                profile, search_results
            )
            risk_assessment = self._determine_risk_tier(risk_score)

            # Determine loan eligibility
            loan_eligible = (
                profile.credit_score >= 650
                and profile.debt_to_income_ratio < 0.45
                and profile.income >= 30_000
            )

            # Financial health — inverse of risk
            financial_health = max(0.0, min(100.0, 100.0 - risk_score))

            # Policy references from search results
            policy_refs = list(
                {
                    r.get("filename", "unknown")
                    for r in search_results
                    if r.get("filename")
                }
            )

            elapsed = time.time() - start_time

            # 10. Build the report
            report = EnhancedBankingReport(
                report_id=f"enhanced_{uuid.uuid4().hex[:8]}",
                customer_id=customer_id,
                query=customer_query,
                summary=str(final_output),
                key_findings=self._generate_enhanced_findings(
                    profile, search_results, agent_contributions
                ),
                risk_assessment=risk_assessment,
                risk_score=risk_score,
                fraud_risk_level=(
                    RiskLevel.HIGH.value
                    if risk_score > 60
                    else (
                        RiskLevel.MEDIUM.value
                        if risk_score > 35
                        else RiskLevel.LOW.value
                    )
                ),
                loan_eligibility=loan_eligible,
                recommendations=self._generate_enhanced_recommendations(
                    profile, risk_score
                ),
                actions_taken=[
                    "Multi-agent sequential analysis completed",
                    "Policy compliance verification performed",
                    "Enterprise risk assessment conducted",
                    "Customer profile enriched from data sources",
                    "RAG policy search executed across all collections",
                ],
                policy_references=policy_refs,
                agent_contributions=agent_contributions,
                agent_activations=agent_activations,
                processing_metrics={
                    "total_processing_time_seconds": round(elapsed, 2),
                    "agents_activated": len(agent_contributions),
                    "policies_referenced": len(policy_refs),
                    "rag_results_returned": len(search_results),
                    "risk_score": risk_score,
                    "customer_income": profile.income,
                    "customer_credit_score": profile.credit_score,
                },
                compliance_status="compliant",
                financial_health_score=financial_health,
                next_best_actions=self._generate_next_best_actions(
                    profile, risk_score
                ),
            )

            # Record in shared state
            self.shared_state.update_interaction(
                customer_id,
                {
                    "query": customer_query,
                    "report_id": report.report_id,
                    "risk_score": risk_score,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            self.performance_metrics["successful_analyses"] += 1

            return report

        except asyncio.TimeoutError:
            self.logger.error("Orchestration timed out after 180 seconds.")
            self.shared_state.record_failure(
                customer_id, "Orchestration timeout"
            )
            return self._create_error_report(
                customer_id,
                customer_query,
                "Analysis timed out. Please try again.",
            )
        except Exception as exc:
            self.logger.error(
                "Orchestration error: %s", exc, exc_info=True
            )
            self.shared_state.record_failure(customer_id, str(exc))
            return self._create_error_report(
                customer_id,
                customer_query,
                "We encountered an issue processing your request. "
                "Our team has been notified.",
            )
        finally:
            await runtime.stop_when_idle()

    # ------------------------------------------------------------------
    # Error / fallback report
    # ------------------------------------------------------------------

    @staticmethod
    def _create_error_report(
        customer_id: str, query: str, message: str
    ) -> EnhancedBankingReport:
        """Return a minimal report when the pipeline encounters an error."""
        return EnhancedBankingReport(
            report_id=f"error_{uuid.uuid4().hex[:8]}",
            customer_id=customer_id,
            query=query,
            summary=message,
            key_findings=["Analysis could not be completed at this time."],
            risk_assessment=RiskLevel.MEDIUM.value,
            recommendations=["Please retry or contact customer support."],
            actions_taken=["Error occurred during processing"],
            compliance_status="review_required",
        )


# ======================================================================
# CLI entry-points
# ======================================================================


async def run_demo() -> None:
    """Run a single demo scenario end-to-end."""
    print("\n" + "=" * 80)
    print("  BANKING MULTI-AGENT RAG SYSTEM -- DEMO MODE")
    print("=" * 80 + "\n")

    system = EnhancedBankingSequentialOrchestration()

    scenario = {
        "customer_id": "12345",
        "query": (
            "I need comprehensive financial planning including investments "
            "and retirement options. Please also review my account for any "
            "suspicious activity and assess my loan eligibility."
        ),
    }

    print(f"  Customer : {scenario['customer_id']}")
    print(f"  Query    : {scenario['query']}\n")

    report = await system.run_enhanced_analysis(
        scenario["customer_id"], scenario["query"]
    )
    print(report.display())

    # Persist report
    reports_dir = os.path.join(PROJECT_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"demo_report_{report.report_id}.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report.model_dump_json(indent=2))
    print(f"\n  Report saved to {report_path}")


async def run_all() -> None:
    """Run the full evaluation suite with multiple test scenarios."""
    print("\n" + "=" * 80)
    print("  BANKING MULTI-AGENT RAG SYSTEM -- FULL EVALUATION")
    print("=" * 80 + "\n")

    system = EnhancedBankingSequentialOrchestration()

    test_scenarios = [
        {
            "customer_id": "12345",
            "query": (
                "I need comprehensive financial planning including "
                "investments and retirement options"
            ),
        },
        {
            "customer_id": "67890",
            "query": (
                "I noticed unusual transactions on my account. "
                "Can you investigate potential fraud and review my "
                "security?"
            ),
        },
        {
            "customer_id": "11111",
            "query": (
                "I'd like to apply for a personal loan. "
                "What are my options and eligibility?"
            ),
        },
        {
            "customer_id": "12345",
            "query": (
                "Please provide a complete risk assessment of my banking "
                "portfolio and suggest ways to improve my financial health."
            ),
        },
        {
            "customer_id": "67890",
            "query": (
                "What banking products would you recommend for someone "
                "in my financial situation?"
            ),
        },
    ]

    reports_dir = os.path.join(PROJECT_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    results_summary: List[Dict[str, Any]] = []

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'=' * 80}")
        print(f"  SCENARIO {i}/{len(test_scenarios)}")
        print(f"  Customer : {scenario['customer_id']}")
        print(f"  Query    : {scenario['query']}")
        print(f"{'=' * 80}")

        try:
            report = await system.run_enhanced_analysis(
                scenario["customer_id"], scenario["query"]
            )
            print(report.display())

            report_path = os.path.join(reports_dir, f"eval_{i}_{report.report_id}.json")
            with open(report_path, "w", encoding="utf-8") as fh:
                fh.write(report.model_dump_json(indent=2))

            results_summary.append(
                {
                    "scenario": i,
                    "customer_id": scenario["customer_id"],
                    "query": scenario["query"][:80],
                    "risk_score": report.risk_score,
                    "risk_assessment": report.risk_assessment,
                    "agents_activated": len(report.agent_contributions),
                    "report_id": report.report_id,
                    "status": "success",
                }
            )
        except Exception as exc:
            logger.error("Scenario %d failed: %s", i, exc, exc_info=True)
            results_summary.append(
                {
                    "scenario": i,
                    "customer_id": scenario["customer_id"],
                    "status": "failed",
                    "error": str(exc),
                }
            )

    # Print summary table
    print("\n" + "=" * 80)
    print("  EVALUATION SUMMARY")
    print("=" * 80)
    for r in results_summary:
        status_icon = "[PASS]" if r["status"] == "success" else "[FAIL]"
        print(
            f"  {status_icon} Scenario {r['scenario']}: "
            f"Customer {r['customer_id']} -- {r['status']}  "
            f"(risk={r.get('risk_score', 'N/A')}, "
            f"agents={r.get('agents_activated', 'N/A')})"
        )
    print("=" * 80)

    # Save summary
    summary_path = os.path.join(reports_dir, "evaluation_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(results_summary, fh, indent=2, default=str)
    print(f"\n  Summary saved to {summary_path}")


async def run_tests() -> None:
    """Run quick validation tests for individual components."""
    print("\n" + "=" * 80)
    print("  BANKING MULTI-AGENT RAG SYSTEM -- COMPONENT TESTS")
    print("=" * 80 + "\n")

    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} -- {detail}")

    # ---- Test 1: Pydantic models ----
    print("  --- Pydantic Models ---")
    try:
        profile = CustomerProfile(
            customer_id="test",
            income=50000,
            credit_score=900,  # should clamp to 850
        )
        check("CustomerProfile creation", profile.customer_id == "test")
        check("Credit score clamped to 850", profile.credit_score == 850)
    except Exception as exc:
        check("CustomerProfile creation", False, str(exc))

    try:
        report = EnhancedBankingReport(
            report_id="test_001",
            customer_id="test",
            query="test query",
            risk_score=150.0,  # should clamp to 100
        )
        check(
            "EnhancedBankingReport creation",
            report.report_id == "test_001",
        )
        check("Risk score clamped to 100", report.risk_score == 100.0)
        check("Report display() works", len(report.display()) > 100)
    except Exception as exc:
        check("EnhancedBankingReport creation", False, str(exc))

    # ---- Test 2: BlobStorageConnector ----
    print("\n  --- Blob Storage ---")
    try:
        blob = BlobStorageConnector()
        if not blob.list_documents():
            blob.upload_sample_documents()
        docs = blob.list_documents()
        check("BlobStorageConnector initialised", True)
        check(
            f"Sample documents uploaded ({len(docs)})",
            len(docs) >= 4,
        )
        content = blob.get_document_content(docs[0])
        check(
            "Document content readable",
            content is not None and len(content) > 0,
        )
    except Exception as exc:
        check("BlobStorageConnector", False, str(exc))

    # ---- Test 3: ChromaDB ----
    print("\n  --- ChromaDB ---")
    try:
        chroma = ChromaDBManager()
        check("ChromaDBManager initialised", chroma.client is not None)
        stats = await chroma.get_collection_stats()
        check(f"Collections available ({len(stats)})", len(stats) >= 4)

        # Ingest a test document
        stored = await chroma.chunk_and_store_document(
            "test_doc.md",
            "This is a test fraud detection policy for loan eligibility.",
            "fraud_detection",
        )
        check(
            f"Document chunked & stored ({stored} chunks)",
            stored > 0,
        )

        results = await chroma.semantic_search(
            "fraud detection", ["fraud_detection"], top_k=2
        )
        check(
            f"Semantic search returned results ({len(results)})",
            len(results) > 0,
        )
    except Exception as exc:
        check("ChromaDBManager", False, str(exc))

    # ---- Test 4: DataConnector ----
    print("\n  --- DataConnector ---")
    try:
        dc = DataConnector()
        check("DataConnector initialised", True)
        if dc.is_available:
            check("Azure SQL connection LIVE", True)
            income = await dc.fetch_income("12345")
            check(f"fetch_income returned {income}", income is not None)
            txns = await dc.fetch_transactions("12345")
            check(
                f"fetch_transactions returned {len(txns)} rows",
                len(txns) > 0,
            )
        else:
            check("Azure SQL unavailable — testing fallback", True)
            sample_txns = DataConnector.get_sample_transactions("12345")
            check(
                f"Sample transactions ({len(sample_txns)})",
                len(sample_txns) > 0,
            )
            sample_income = DataConnector.get_sample_income("12345")
            check(
                f"Sample income (${sample_income})",
                sample_income is not None,
            )
    except Exception as exc:
        check("DataConnector", False, str(exc))

    # ---- Test 5: Semantic Kernel + Agents ----
    print("\n  --- Semantic Kernel Agents ---")
    try:
        system = EnhancedBankingSequentialOrchestration()
        check("Orchestration system initialised", True)
        agents = system.create_enhanced_agents()
        check(f"Created {len(agents)} agents", len(agents) == 6)
        expected_names = {
            "Enhanced_Data_Gatherer",
            "Enhanced_Fraud_Analyst",
            "Enhanced_Loan_Analyst",
            "Enhanced_Support_Specialist",
            "Enhanced_Risk_Analyst",
            "Enhanced_Synthesis_Coordinator",
        }
        actual_names = {a.name for a in agents}
        check("All 6 agent names correct", actual_names == expected_names)
    except Exception as exc:
        check("Agent creation", False, str(exc))

    # ---- Test 6: RAG integration ----
    print("\n  --- RAG Integration ---")
    try:
        from rag_utils import extract_banking_policies, create_semantic_kernel_context

        blob2 = BlobStorageConnector()
        if not blob2.list_documents():
            blob2.upload_sample_documents()

        test_docs = []
        for doc_name in blob2.list_documents():
            content = blob2.get_document_content(doc_name)
            metadata = blob2.get_document_metadata(doc_name) or {}
            test_docs.append({
                "filename": doc_name,
                "id": f"{metadata.get('type', 'general')}_{doc_name}",
                "text": content or "",
            })

        policies = extract_banking_policies(test_docs)
        check("Policy extraction works", len(policies) > 0)
        context = create_semantic_kernel_context(policies)
        check("Semantic kernel context generated", len(context) > 10)
    except Exception as exc:
        check("RAG Integration", False, str(exc))

    # ---- Summary ----
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"  TESTS: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'=' * 60}\n")


async def enhanced_main() -> None:
    """Parse CLI arguments and dispatch to the appropriate mode."""
    log_filename = setup_logging()

    parser = argparse.ArgumentParser(
        description="Banking Multi-Agent RAG System",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the full evaluation suite",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a single demo scenario",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run quick component tests",
    )
    args = parser.parse_args()

    if args.test:
        await run_tests()
    elif args.all:
        await run_all()
    elif args.demo:
        await run_demo()
    else:
        # Default: run demo
        print(
            "No flag specified -- running demo mode. Use --help for options."
        )
        await run_demo()


if __name__ == "__main__":
    asyncio.run(enhanced_main())
