# Banking Multi-Agent RAG System - Student Implementation Guide

## Student Implementation Tasks

### Task 1: Agent Implementations with Azure AI Foundry

**TODO**: Implement specialized banking agents with proper reasoning capabilities

**Hints**:
- Each agent should have clear, banking-specific instructions
- Use `AzureChatCompletion` service from the kernel
- Focus on domain expertise: fraud detection, loan evaluation, risk assessment, etc.
- Ensure agents build upon previous analyses in the sequential workflow

**Example Agent Structure**:
```python
agent = ChatCompletionAgent(
    name="Specialized_Agent_Name",
    instructions="""
    You are a [banking domain] expert with capabilities in:
    - [Specific capability 1]
    - [Specific capability 2]
    - [Specific capability 3]
    
    Your responsibilities:
    1. [Primary task]
    2. [Secondary task]
    3. [Tertiary task]
    
    Focus on [specific banking outcomes]
    Provide [expected output format]
    """,
    service=self.kernel.get_service("enhanced_banking_chat")
)
```

### Task 2: Azure SQL Database Integration

**TODO**: Implement data retrieval from Azure SQL Database

**Hints**:
- Use `pyodbc` for database connectivity
- Create proper connection string management
- Implement async methods for data fetching
- Handle connection errors gracefully
- Convert SQL results to appropriate Python data structures

**Key Methods to Implement**:
- `fetch_income(customer_id)`
- `fetch_transactions(customer_id)` 
- `get_db_connection()` context manager
- Connection testing and error handling

### Task 3: Pydantic Model Enhancement

**TODO**: Enhance data models with comprehensive validation

**EnhancedBankingReport Attributes to Consider**:
- `customer_segment`: Customer classification (premium, standard, basic)
- `financial_health_score`: Overall financial wellness (0.0-1.0)
- `compliance_status`: Regulatory compliance assessment
- `opportunity_areas`: Potential banking product opportunities
- `customer_sentiment`: Analysis of customer query sentiment
- `next_best_actions`: Recommended follow-up actions
- `regulatory_flags`: Any compliance issues identified

**CustomerProfile Attributes to Consider**:
- `employment_status`: Current employment situation
- `total_assets`: Comprehensive asset valuation
- `monthly_expenses`: Regular expenditure patterns
- `debt_to_income_ratio`: Financial leverage assessment
- `savings_rate`: Savings behavior analysis
- `investment_portfolio`: Current investment holdings
- `life_stage`: Customer demographic classification
- `banking_tenure`: Relationship duration with bank
- `product_affinity`: Likelihood to use different banking products

## Implementation Checklist

- [ ] DataConnector class with Azure SQL integration
- [ ] Enhanced Pydantic models with validation
- [ ] Specialized banking agents with Azure AI Foundry
- [ ] Comprehensive risk scoring algorithm
- [ ] Policy context preparation
- [ ] Error handling and fallback mechanisms
- [ ] Performance metrics tracking
- [ ] Test scenarios covering all banking domains

## Success Criteria

- All 6 agents properly implemented with banking expertise
- Successful connection to Azure SQL Database
- Comprehensive customer data loading and analysis
- Proper risk assessment and scoring
- Meaningful banking recommendations
- Error-free execution of test scenarios
- Detailed logging and performance tracking

Good luck with your implementation!