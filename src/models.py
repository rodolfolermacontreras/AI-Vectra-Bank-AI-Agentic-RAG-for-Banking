"""
Pydantic models for the Banking Multi-Agent RAG System.

Provides structured data models with validation for banking reports,
customer profiles, and agent tracking used throughout the orchestration pipeline.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from semantic_kernel.kernel_pydantic import KernelBaseModel


class RiskLevel(str, Enum):
    """Enumeration of risk classification levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccountType(str, Enum):
    """Enumeration of customer account types."""

    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    PREMIUM_PLUS = "premium_plus"


class AgentActivation(KernelBaseModel):
    """Tracks individual agent execution within the orchestration pipeline."""

    agent_name: str = ""
    activated: bool = False
    duration_seconds: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    output_summary: str = ""


class CustomerProfile(KernelBaseModel):
    """
    Comprehensive customer profile with financial metrics and risk indicators.

    Attributes:
        customer_id: Unique identifier for the customer.
        income: Annual income in USD.
        credit_score: FICO credit score (300-850).
        account_type: Type of banking account held.
        customer_since: Date the customer relationship began.
        risk_tier: Assessed risk classification.
        recent_transactions: List of recent transaction records.
        banking_products: Active banking product subscriptions.
        last_review_date: Date of most recent account review.
        employment_status: Current employment situation.
        total_assets: Comprehensive asset valuation in USD.
        monthly_expenses: Average monthly expenditure in USD.
        debt_to_income_ratio: Financial leverage ratio (0.0-1.0).
        savings_rate: Fraction of income saved (0.0-1.0).
    """

    customer_id: str = ""
    income: float = 0.0
    credit_score: int = 0
    account_type: str = AccountType.STANDARD.value
    customer_since: str = ""
    risk_tier: str = RiskLevel.MEDIUM.value
    recent_transactions: List[Dict[str, Any]] = Field(default_factory=list)
    banking_products: List[str] = Field(default_factory=list)
    last_review_date: str = ""
    employment_status: str = "unknown"
    total_assets: float = 0.0
    monthly_expenses: float = 0.0
    debt_to_income_ratio: float = 0.0
    savings_rate: float = 0.0

    @field_validator("credit_score")
    @classmethod
    def validate_credit_score(cls, v: int) -> int:
        """Ensure credit score is within the valid FICO range."""
        return max(0, min(850, v))

    @field_validator("debt_to_income_ratio", "savings_rate")
    @classmethod
    def validate_ratio(cls, v: float) -> float:
        """Clamp ratio values to [0.0, 1.0]."""
        return max(0.0, min(1.0, v))


class EnhancedBankingReport(KernelBaseModel):
    """
    Comprehensive banking analysis report produced by the multi-agent pipeline.

    Attributes:
        report_id: Unique report identifier.
        customer_id: Customer the report pertains to.
        query: Original customer query text.
        summary: Executive summary of findings.
        key_findings: List of notable findings from agent analyses.
        risk_assessment: Qualitative risk level label.
        risk_score: Composite risk score (0.0-100.0).
        fraud_risk_level: Fraud-specific risk classification.
        loan_eligibility: Whether the customer qualifies for lending products.
        recommendations: Actionable recommendations for the customer.
        actions_taken: Steps completed during analysis.
        policy_references: Banking policies referenced during analysis.
        agent_contributions: Mapping of agent name → output text.
        agent_activations: Detailed execution tracking per agent.
        processing_metrics: Performance and operational metrics.
        compliance_status: Regulatory compliance assessment result.
        financial_health_score: Overall financial wellness (0.0-100.0).
        next_best_actions: Prioritised follow-up actions.
        generated_by: System component that produced the report.
        generated_at: Timestamp of report generation.
    """

    report_id: str = ""
    customer_id: str = ""
    query: str = ""
    summary: str = ""
    key_findings: List[str] = Field(default_factory=list)
    risk_assessment: str = RiskLevel.MEDIUM.value
    risk_score: float = 50.0
    fraud_risk_level: str = RiskLevel.LOW.value
    loan_eligibility: bool = False
    recommendations: List[str] = Field(default_factory=list)
    actions_taken: List[str] = Field(default_factory=list)
    policy_references: List[str] = Field(default_factory=list)
    agent_contributions: Dict[str, str] = Field(default_factory=dict)
    agent_activations: List[AgentActivation] = Field(default_factory=list)
    processing_metrics: Dict[str, Any] = Field(default_factory=dict)
    compliance_status: str = "compliant"
    financial_health_score: float = 50.0
    next_best_actions: List[str] = Field(default_factory=list)
    generated_by: str = "EnhancedBankingOrchestration"
    generated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("risk_score", "financial_health_score")
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """Clamp scores to the valid [0, 100] range."""
        return max(0.0, min(100.0, v))

    def display(self) -> str:
        """Return a formatted text representation of the report."""
        separator = "=" * 80
        lines = [
            separator,
            f"  ENHANCED BANKING ANALYSIS REPORT — {self.report_id}",
            separator,
            f"  Customer ID   : {self.customer_id}",
            f"  Query         : {self.query}",
            f"  Generated     : {self.generated_at:%Y-%m-%d %H:%M:%S}",
            f"  Generated By  : {self.generated_by}",
            separator,
            "",
            "  EXECUTIVE SUMMARY",
            "  " + "-" * 40,
            f"  {self.summary[:500]}",
            "",
            "  RISK PROFILE",
            "  " + "-" * 40,
            f"  Risk Assessment      : {self.risk_assessment}",
            f"  Risk Score           : {self.risk_score:.1f} / 100",
            f"  Fraud Risk Level     : {self.fraud_risk_level}",
            f"  Loan Eligibility     : {'Yes' if self.loan_eligibility else 'No'}",
            f"  Compliance Status    : {self.compliance_status}",
            f"  Financial Health     : {self.financial_health_score:.1f} / 100",
            "",
            "  KEY FINDINGS",
            "  " + "-" * 40,
        ]
        for i, finding in enumerate(self.key_findings, 1):
            lines.append(f"  {i}. {finding}")

        lines += [
            "",
            "  RECOMMENDATIONS",
            "  " + "-" * 40,
        ]
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"  {i}. {rec}")

        lines += [
            "",
            "  NEXT BEST ACTIONS",
            "  " + "-" * 40,
        ]
        for i, action in enumerate(self.next_best_actions, 1):
            lines.append(f"  {i}. {action}")

        lines += [
            "",
            "  AGENT ACTIVATIONS",
            "  " + "-" * 40,
        ]
        for activation in self.agent_activations:
            status = "[PASS]" if activation.success else "[FAIL]"
            lines.append(
                f"  {status} {activation.agent_name} -- "
                f"{activation.duration_seconds:.2f}s"
            )

        lines += [
            "",
            "  PROCESSING METRICS",
            "  " + "-" * 40,
        ]
        for key, val in self.processing_metrics.items():
            lines.append(f"  {key}: {val}")

        lines.append(separator)
        return "\n".join(lines)
