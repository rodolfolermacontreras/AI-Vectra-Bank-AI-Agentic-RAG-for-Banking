# Multi-Agent Systems with Azure -- Course Notes

> **Source**: Udacity "Microsoft Azure AI Foundry" Nanodegree -- Course 4
> **Enhanced by**: Team reference annotations, implementation patterns, and
> production considerations.
> **Last updated**: 2026-02-17

---

## Table of Contents

1. [What is a Multi-Agent System?](#1-what-is-a-multi-agent-system)
2. [Architecture Design](#2-architecture-design)
3. [Implementation Fundamentals](#3-implementation-fundamentals)
4. [Azure AI Foundry Setup](#4-azure-ai-foundry-setup)
5. [Orchestration Patterns](#5-orchestration-patterns)
6. [Routing and Data Flow](#6-routing-and-data-flow)
7. [Azure SQL Integration](#7-azure-sql-integration)
8. [State Management](#8-state-management)
9. [State Coordination](#9-state-coordination)
10. [Retrieval-Augmented Generation (RAG)](#10-retrieval-augmented-generation-rag)
11. [Azure Blob Storage Setup](#11-azure-blob-storage-setup)
12. [Key Terms Glossary](#12-key-terms-glossary)
13. [Implementation Checklist](#13-implementation-checklist)

---

## 1. What is a Multi-Agent System?

A multi-agent system is a computational program that receives complicated
natural language requests and responds **agentically** -- there is no strictly
defined or pre-determined sequence of checks. By defining agents with distinct
goals and personalities, we approximate the interactivity that occurs between
humans collaborating on a problem.

### The Restaurant Analogy

Think about how a restaurant operates:

| Role | Responsibility |
|------|---------------|
| Host | Greets customers, manages seating |
| Waiter | Takes orders, delivers food |
| Chef | Specialises in different cooking types |
| Busboy | Cleans up when customers leave |
| Manager | Oversees the whole operation |

Each person has a clear role and communicates with others to deliver a complete
experience. Multi-agent AI systems work the same way.

### Why This Matters for Teams

> **Enhancement -- Team Takeaway**: Multi-agent thinking lets domain experts
> focus on *what* each step should accomplish (natural language prompts) rather
> than *how* to code every algorithm. This is a paradigm shift -- we move from
> "write the formula" to "describe the expertise."

Traditional approach:
```
Business logic -> Algorithm design -> Code implementation -> Testing
```

Multi-agent approach:
```
Business logic -> Agent role definition -> Prompt engineering -> Orchestration
```

### Skills You Will Master

- Design and develop multi-agent systems for multi-step procedures.
- Approach work more abstractly through agentic prompt flows.
- Let agents handle syntax and details while you focus on the hard stuff.

---

## 2. Architecture Design

### Mental Model: The Blueprint

Before a single line of code is written for a skyscraper, an architect creates
a detailed blueprint. Building a multi-agent system is no different. You are the
architect, and your first job is to draw the blueprint.

### Two Core Architectural Patterns

#### Orchestrator Pattern (Centralised)

A single agent (the orchestrator) manages and delegates tasks to worker agents.

```
User Request
    |
    v
[ Orchestrator ]
    |
    +---> Agent A (specialist)
    +---> Agent B (specialist)
    +---> Agent C (specialist)
    |
    v
Combined Result
```

**When to use**: Structured workflows where order matters, complex processes
with dependencies, systems that need centralised logging and error handling.

**Example -- E-commerce Return System**:
1. Customer submits return request -> Orchestrator receives it.
2. Policy Agent checks eligibility requirements.
3. Inventory Agent prepares stock updates.
4. Refund Agent processes the payment return.
5. Communication Agent keeps the customer informed.

#### Peer-to-Peer Pattern (Decentralised)

Agents communicate directly with each other without a central manager. Each
agent decides which peer to talk to next.

```
Agent A <-----> Agent B
   ^               ^
   |               |
   v               v
Agent C <-----> Agent D
```

**When to use**: Flexible workflows where exact sequence is not known upfront,
systems that need to adapt dynamically, scenarios where agents have equal
authority.

### Architecture Design Checklist

Regardless of pattern, you must define:

- [ ] **Roles**: What each agent is responsible for
- [ ] **Communication protocols**: How agents exchange information
- [ ] **State management**: What data is shared and how
- [ ] **Data flow**: The path data takes through the system

> **Enhancement -- Team Takeaway**: For most enterprise use cases, **start with
> the Orchestrator pattern**. It is simpler to debug, easier to add logging, and
> gives you centralised error handling. Move to peer-to-peer only when you have
> a proven need for decentralised decision-making.

### Code Example: Orchestrator Pattern

```python
class CulturalCenterOrchestrator:
    def __init__(self):
        self.language_agent = LanguageAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.navigation_agent = NavigationAgent()

    def handle_query(self, query):
        # Step 1: Delegate to a specialist for language detection
        language = self.language_agent.detect_language(query)

        # Step 2: Make a decision based on the specialist's output
        if "directions" in query.lower():
            return self.navigation_agent.get_directions(query, language)
        else:
            return self.knowledge_agent.answer_question(query, language)
```

**Key insight**: The orchestrator knows *who* to ask based on the content of the
query. Adding a new specialist (e.g., "CafeAgent") only requires adding it to
the orchestrator and creating a routing rule -- existing agents remain untouched
(Open/Closed Principle).

### Design Exercise Template

When designing a new multi-agent system:

1. **Choose a real-world scenario** you are familiar with.
2. **Draw the architecture diagram** (boxes = agents, arrows = data flow).
3. **Define roles and responsibilities** for each agent.
4. **Label arrows** with what information is passed.
5. **Identify bottlenecks and failure points** -- add notes for each.

---

## 3. Implementation Fundamentals

### Mental Model: Job Training

Implementation is where you define an agent's "job description" (System Prompt),
give it "skills" (Tools), and establish the "communication policy"
(Serialisation).

### Agent Attributes and System Prompts

A well-crafted system prompt tells the agent four things:

| Aspect | Example |
|--------|---------|
| **Who you are** | "You are a Data Validation Agent." |
| **What you do** | "Your sole purpose is to check incoming user data against predefined schemas." |
| **What you don't do** | "You do not perform calculations or interact with external APIs." |
| **What tools you have** | "You ONLY have access to the validate_schema tool." |

> **Enhancement -- Team Takeaway**: The negative constraint ("What you don't
> do") is just as important as the positive. Without it, agents tend to
> hallucinate capabilities. Always include boundaries in your system prompts.

### Agent Tools

Tools give agents abilities beyond language processing:

- Accessing databases
- Calling APIs
- Performing calculations

**Critical**: Tool names and descriptions are metadata the LLM uses to decide
*when* and *how* to invoke the tool. Poor descriptions lead to poor tool
selection.

```python
@kernel_function(
    name="check_availability",
    description="Check if the book is available in stock"  # This description matters!
)
def check_availability(self) -> bool:
    return self.quantity > 0
```

### Serialisation and Deserialisation

When agents communicate, complex data objects must be:

1. **Serialised** -- converted to a string (usually JSON) for transmission.
2. **Deserialised** -- converted back into a usable object by the receiver.

Most modern frameworks handle this automatically, but understanding the process
is essential for debugging.

> **Enhancement -- Team Takeaway**: When debugging agent communication issues,
> always check the serialisation layer first. A common failure mode is an agent
> returning a Python object that cannot be JSON-serialised (e.g., datetime
> without a custom encoder).

### Implementation Pattern: Semantic Kernel Agents

```python
class SmartCityAgentManager:
    def __init__(self):
        # Single shared kernel instance for all agents (efficient)
        self.kernel = Kernel()

        self.kernel.add_service(
            AzureChatCompletion(...)
        )

        self.agents = {
            "traffic": ChatCompletionAgent(
                kernel=self.kernel,
                name="Traffic_Manager",
                description="Expert in urban traffic flow",
                instructions="""You are an expert in urban traffic flow
                and congestion management. Analyze traffic situations,
                provide insights on congestion patterns, and suggest
                optimization strategies. Be specific and data-driven."""
            ),
            # ... more agents
        }
```

**Key pattern**: One shared `Kernel` instance for all agents. This avoids
redundant Azure OpenAI connections and reduces resource usage.

---

## 4. Azure AI Foundry Setup

### Step-by-Step: Provisioning Azure AI Foundry

1. **Search** for "Microsoft Foundry" in the Azure portal search bar.
2. **Create a resource**:
   - Select your subscription and resource group.
   - Provide a unique name (e.g., `udacity-foundry`).
   - Name your first project (e.g., `udacity-project`).
3. Accept defaults for Network, Identity, Encryption, Tags.
4. Click **Create** on the Review + Submit page.
5. After deployment, click **Go to resource** then **Go to Foundry portal**.

### Deploying a Model

1. In Foundry portal: **My assets** -> **Models + endpoints**.
2. Click **+ Deploy model** -> **Deploy base model**.
3. Search for your model (e.g., `gpt-4o-mini` or `gpt-4o`).
4. Accept defaults (Global Standard deployment type).
5. Click **Deploy**.

### Retrieving Connection Information

After deployment, note three critical values:

| Value | Description | Environment Variable |
|-------|-------------|---------------------|
| Target URI | Your endpoint URL | `AZURE_OPENAI_ENDPOINT` |
| Key | API authentication key | `AZURE_OPENAI_API_KEY` |
| Deployment Name | The model deployment name | `AZURE_DEPLOYMENT_NAME` |

### Environment File Template

```bash
AZURE_DEPLOYMENT_NAME=gpt-4o
AZURE_DEPLOYMENT_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DEPLOYMENT_KEY=your-api-key-here
```

> **Enhancement -- Security Best Practices for Teams**:
> - **Never** commit `.env` files to version control.
> - Use `.env.example` or `env.template` with placeholder values.
> - In production, use Azure Key Vault instead of environment variables.
> - Rotate API keys regularly.
> - Use separate deployments for dev/staging/prod.

---

## 5. Orchestration Patterns

### Mental Model: The Conductor

The conductor doesn't play every instrument but controls the tempo, cues
different sections, and ensures violins and trumpets work together.

### Three Fundamental Patterns

#### Pattern 1: Sequential Execution

Tasks execute one after another. Each step builds on the previous result.

```
Agent 1 --> Agent 2 --> Agent 3 --> Final Result
  (output feeds into next agent's prompt)
```

**When to use**: Tasks with dependencies, workflows where context must
accumulate, analysis pipelines.

```python
async def run_sequential_collaboration(self, scenario: str):
    # Step 1: Traffic analysis
    traffic_response = await self.agents["traffic"].get_response(scenario)
    traffic_content = str(traffic_response.content)

    # Step 2: Energy analysis WITH traffic context
    energy_prompt = f"""Scenario: {scenario}
    Previous Analysis from Traffic Department:
    {traffic_content}"""
    energy_response = await self.agents["energy"].get_response(energy_prompt)
    energy_content = str(energy_response.content)

    # Step 3: Safety analysis WITH full context
    safety_prompt = f"""Scenario: {scenario}
    Traffic Analysis: {traffic_content}
    Energy Analysis: {energy_content}"""
    # ...
```

**Key insight**: Each agent receives the accumulated context from all prior
agents. This is how you build deep, integrated analysis.

#### Pattern 2: Parallel Execution

Tasks that don't depend on each other run simultaneously.

```
        +--> Agent A --+
        |              |
Input --+--> Agent B --+--> Combined Result
        |              |
        +--> Agent C --+
```

**When to use**: Independent analyses, time-sensitive scenarios, broad
assessments.

```python
async def run_parallel_analysis(self, scenario: str):
    tasks = {
        "Traffic": self._get_agent_response(self.agents["traffic"], scenario),
        "Energy": self._get_agent_response(self.agents["energy"], scenario),
        "Safety": self._get_agent_response(self.agents["safety"], scenario),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
```

**Key insight**: `asyncio.gather()` runs all tasks concurrently. Results are
fast but *uncoordinated* -- agents don't share context.

#### Pattern 3: Conditional Branching

The orchestrator makes decisions based on agent output.

```
Input --> Router Agent --> if condition A --> Agent A
                       --> if condition B --> Agent B
                       --> if condition C --> Agent C
```

**When to use**: Diverse request types, resource optimisation, triage systems.

```python
# Smart routing based on content analysis
request_lower = travel_request.lower()

needs_destination = any(phrase in request_lower for phrase in [
    'where should', 'recommend destination', 'place to visit'
])

needs_flights = any(phrase in request_lower for phrase in [
    'flight', 'fly', 'airline', 'airport'
])

# Execute ONLY needed agents in parallel
tasks = []
if needs_destination:
    tasks.append(self._get_agent_response(self.agents["destination"], request))
if needs_flights:
    tasks.append(self._get_agent_response(self.agents["flights"], request))

results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Comparing Patterns

| Pattern | Speed | Context Depth | Best For |
|---------|-------|--------------|----------|
| Sequential | Slowest | Deepest | Complex analysis with dependencies |
| Parallel | Fastest | Shallowest | Independent, broad assessments |
| Conditional | Variable | Targeted | Diverse request types, resource efficiency |

> **Enhancement -- Team Takeaway**: In practice, you almost always **combine
> patterns**. A typical production system might:
> 1. Use conditional routing to pick the right workflow.
> 2. Run some agents in parallel (independent data gathering).
> 3. Feed parallel results into a sequential synthesis chain.
>
> Our Project 4 uses sequential orchestration because each banking agent builds
> on the findings of the previous one -- context accumulation is critical for
> comprehensive financial analysis.

---

## 6. Routing and Data Flow

### Mental Model: The Mailroom

Routing is the mail clerk who looks at an incoming memo and decides which
department gets it. Data Flow Management is making sure the memo is in the right
format for the recipient.

### Routing Patterns

#### Content-Based Routing

Inspects message content to decide where it goes.

```python
# Routing agent with structured output
"router": ChatCompletionAgent(
    instructions="""Analyze each request and determine:
    1. Which specialist should handle it (account/loan/card/emergency)
    2. The urgency level (Low/Medium/High/Emergency)
    3. Brief reasoning

    Respond in this exact format:
    Specialist: [account/loan/card/emergency]
    Urgency: [Low/Medium/High/Emergency]
    Reasoning: [brief explanation]"""
)
```

> **Enhancement -- Team Takeaway**: Always define a **structured output format**
> for your routing agent. Free-form responses are unreliable to parse. The
> `Specialist: / Urgency: / Reasoning:` format above is easy to parse with
> simple string operations. For production, consider using Pydantic structured
> output.

#### Round-Robin Routing

Distributes workload evenly across similar agents. Useful for scaling when you
have multiple instances of the same agent type.

#### Priority-Based Routing

Processes messages based on urgency level. Critical for systems where some
requests cannot wait (e.g., fraud alerts, emergency medical triage).

### Data Flow Management

Data moving between agents may need transformation:

| Operation | Description | Example |
|-----------|-------------|---------|
| **Enhancement** | Add related information | Attach account balance to transaction query |
| **Filtering** | Remove unnecessary data | Strip PII before sending to analytics agent |
| **Reformatting** | Change structure or types | Convert datetime formats between systems |

```python
# Example: Enriching a request with database context
if specialist == "account":
    transactions = self.data_connector.get_recent_transactions(account, 3)
    balance = self.data_connector.get_account_balance(account)

    transaction_context = f"""
    ACCOUNT DATA CONTEXT:
    Account {account} (Balance: ${balance:.2f}): {transactions}"""

    full_request = f"CUSTOMER REQUEST: {request}{transaction_context}"
```

---

## 7. Azure SQL Integration

### Step-by-Step: Provisioning Azure SQL

#### Create the SQL Server

1. Azure portal -> Search "Azure SQL" -> SQL logical servers -> **Create**.
2. Configure:
   - **Server name**: Must be globally unique (e.g., `udacity-bank-txn-yourname`).
   - **Location**: Choose your preferred region (e.g., West US 2).
   - **Authentication**: SQL authentication.
   - **Admin login**: e.g., `udacity-admin`.
   - **Password**: Create a secure password.
3. **Networking tab**: Enable "Allow Azure services and resources to access
   this server" -> **Yes**.
4. Click **Create**.

#### Create the Database

1. From the server resource page, click **+ Create database**.
2. Apply the free tier offer if available.
3. Enter database name (e.g., `udacityDB`).
4. **Networking tab**: Set "Add current client IP address" -> **Yes**.
5. Click **Create**.

#### Create Tables and Load Data

Use the built-in **Query editor (preview)** in the Azure portal:

```sql
CREATE TABLE Example_Transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    account_id NVARCHAR(50) NOT NULL,
    type NVARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    date DATETIME2 NOT NULL,
    status NVARCHAR(20) NOT NULL,
    description NVARCHAR(MAX)
);
```

```sql
INSERT INTO Example_Transactions
    (account_id, type, amount, date, status, description)
VALUES
    ('ACC001', 'deposit', 1000.00, GETDATE(), 'completed', 'Initial funding'),
    ('ACC001', 'withdrawal', 150.50, GETDATE(), 'completed', 'ATM withdrawal'),
    ('ACC002', 'deposit', 500.00, GETDATE(), 'completed', 'Payroll deposit');
```

#### Get Connection String

1. Database resource -> **Settings** -> **Connection strings**.
2. Select the **ODBC** tab.
3. Copy the string and replace `{your_password_here}` with your password.

> **Enhancement -- Team Takeaway: Connection String Pattern**
>
> ```python
> # Always use parameterised queries to prevent SQL injection
> cursor.execute(
>     "SELECT * FROM transactions WHERE account_id = ?",
>     (account_id,)
> )
>
> # Always implement a fallback for when the database is unavailable
> try:
>     data = self.db_connector.get_data(account_id)
> except Exception as e:
>     logging.error(f"Database error: {e}")
>     data = self.get_sample_data()  # Graceful fallback
> ```

### ODBC Driver Requirement

Install **ODBC Driver 18 for SQL Server** on your development machine:

- **Windows**: Download from Microsoft.
- **macOS**: `brew install microsoft/mssql-release/msodbcsql18`
- **Linux**: Follow Microsoft's apt/yum instructions.

---

## 8. State Management

### Mental Model: The Shared Project Dashboard

State Management gives your agent team a collective memory -- a centralised
logbook so any agent can get up to speed.

### Two Types of State

| Type | Lifetime | Storage | Example |
|------|----------|---------|---------|
| **Ephemeral** | Single session | In-memory | Chat history, current conversation context |
| **Persistent** | Across sessions | Database/file | Customer records, order history, configuration |

### Stateful Orchestration

Agents almost never operate in isolation. The orchestrator must manage shared
state and pass relevant context to each agent.

```python
# Example: Shared state in a bookstore system
class StoreState(KernelBaseModel):
    books: Dict[str, Book] = {}
    customers: Dict[str, Customer] = {}
    orders: Dict[str, Order] = {}
    store_balance: float = 0.0
    daily_revenue: float = 0.0
```

### Exposing State via Kernel Functions

Use the `@kernel_function` decorator to make state operations available to
agents:

```python
class StoreOperationsPlugin:
    def __init__(self, store_state: StoreState):
        self.store_state = store_state

    @kernel_function(
        name="get_inventory_summary",
        description="Get current inventory summary"
    )
    def get_inventory_summary(self) -> str:
        # ... implementation
```

### Failure Handling Strategies

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Retry Logic** | Repeat the failed operation | Temporary network/API issues |
| **Fallback Paths** | Execute Plan B | When retries fail |
| **Graceful Failure Reporting** | Terminate cleanly with a clear error | Unrecoverable errors |
| **Compensating Actions** | Undo previous steps | When a later step fails after earlier steps succeeded |
| **Human-in-the-Loop** | Escalate to a human | Ambiguous or critical errors |

> **Enhancement -- Team Takeaway: Production Error Handling Pattern**
>
> ```python
> MAX_RETRIES = 3
> RETRY_DELAY = 2  # seconds
>
> async def resilient_agent_call(self, agent, prompt):
>     for attempt in range(MAX_RETRIES):
>         try:
>             response = await agent.get_response(prompt)
>             return response
>         except RateLimitError:
>             await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
>         except Exception as e:
>             if attempt == MAX_RETRIES - 1:
>                 logging.error(f"Agent failed after {MAX_RETRIES} attempts: {e}")
>                 return self.get_fallback_response(prompt)
>             await asyncio.sleep(RETRY_DELAY)
> ```

---

## 9. State Coordination

### Mental Model: Air Traffic Control

It is not just about knowing where the planes are (state management), but about
actively ensuring they don't collide when they try to use the same runway at the
same time (coordination and conflict resolution).

### Synchronisation Strategies

| Strategy | How It Works | Best For |
|----------|-------------|----------|
| **Database as Source of Truth** | Leverage DB locking and transactions | Persistent shared state |
| **State Broadcasting / Eventing** | Publish events when state changes; agents subscribe | Real-time coordination |
| **Optimistic Concurrency** | Assume conflicts are rare; check before committing | Low-contention scenarios |

### Conflict Resolution Strategies

| Strategy | Description |
|----------|-------------|
| **Predefined Rules** | Embed resolution logic directly in code |
| **Negotiation/Consensus** | Agents communicate to find resolution |
| **Rollback and Retry** | Undo and retry on conflict |
| **Human Escalation** | Escalate ambiguous/critical conflicts to a human |

> **Enhancement -- Team Takeaway**: In our Project 4, we use a combination of:
> - **SharedState** (in-memory, thread-safe via locks) for ephemeral session
>   data.
> - **ChromaDB** (persisted) for document embeddings.
> - **Azure SQL** (persistent) for customer transaction data.
>
> The orchestrator serialises agent calls sequentially, which avoids most
> concurrency conflicts. If you move to parallel agent execution in future
> projects, you **must** add proper locking or use database transactions.

### Coordination Code Pattern: Thread-Safe State

```python
import threading

class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}

    def update(self, key, value):
        with self._lock:
            self._data[key] = value

    def get(self, key):
        with self._lock:
            return self._data.get(key)
```

---

## 10. Retrieval-Augmented Generation (RAG)

### What is RAG?

RAG enhances LLM responses by retrieving relevant documents from a knowledge
base and injecting them into the prompt as context. This grounds the model's
responses in factual data rather than relying solely on its training data.

```
User Query
    |
    v
[ Vector Search ] --> Retrieve relevant documents from ChromaDB
    |
    v
[ Augmented Prompt ] = User Query + Retrieved Documents
    |
    v
[ LLM (Azure OpenAI) ] --> Grounded, accurate response
```

### Multi-Agent RAG Pipeline

Our project uses a sequential multi-agent RAG pipeline:

| Step | Agent | Responsibility |
|------|-------|---------------|
| 1 | Document Loader | Identify, prepare, and categorise documents |
| 2 | Financial Analyst | Analyse financial aspects |
| 3 | Technical Analyst | Examine technical details |
| 4 | Market Analyst | Assess market trends |
| 5 | Synthesis Coordinator | Integrate all findings into a final report |

### ChromaDB Setup: Separate Collections

```python
class ChromaDBManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.collections = {
            "financial": self.client.get_or_create_collection(
                name="financial_documents",
                metadata={"description": "Financial reports"}
            ),
            "technical": self.client.get_or_create_collection(
                name="technical_documents",
                metadata={"description": "Technical specs"}
            ),
            "market": self.client.get_or_create_collection(
                name="market_documents",
                metadata={"description": "Market research"}
            ),
        }
```

### Semantic Kernel SequentialOrchestration

```python
from semantic_kernel.agents import ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime

# Create agent pipeline
agents = [document_agent, financial_agent, technical_agent,
          market_agent, synthesis_agent]

sequential_orchestration = SequentialOrchestration(
    members=agents,
    agent_response_callback=self.agent_response_callback,
)

runtime = InProcessRuntime()

orchestration_result = await sequential_orchestration.invoke(
    task=orchestration_task,
    runtime=runtime
)

final_output = await asyncio.wait_for(
    orchestration_result.get(), timeout=120.0
)
```

### Azure Embeddings in RAG

> **Enhancement -- Critical for Production**: The course demos use ChromaDB's
> default embedding function, but for production and for the project rubric, you
> should use **Azure OpenAI text-embedding-ada-002** (or a newer model like
> `text-embedding-3-small`).
>
> This ensures:
> - Embeddings are generated by a model you control and can version.
> - Consistency between indexing and querying.
> - Enterprise-grade performance and SLA.
>
> See our implementation in `src/azure_embedding.py` for a ChromaDB-compatible
> wrapper around Azure OpenAI embeddings.

```python
# ChromaDB-compatible Azure embedding function
class AzureOpenAIEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, api_key, endpoint, deployment, api_version):
        self._client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self._deployment = deployment

    def __call__(self, input: Documents) -> Embeddings:
        response = self._client.embeddings.create(
            input=input,
            model=self._deployment
        )
        return [item.embedding for item in response.data]
```

---

## 11. Azure Blob Storage Setup

### Step-by-Step: Provisioning Blob Storage

1. Azure portal -> Search "Storage center" -> Blob Storage -> **Create**.
2. Configure:
   - **Storage account name**: Globally unique (e.g., `udacitystorageyourname`).
   - **Region**: e.g., West US.
   - **Storage type**: Azure Blob Storage or Data Lake Gen 2.
   - **Performance**: Standard.
   - **Redundancy**: LRS (for dev; use GRS for production).
3. **Networking**: Public access enabled from all networks.
4. Click **Create**.

### Create a Container

1. Inside the storage account -> **Data storage** -> **Containers**.
2. Click **+ Add container**.
3. Name it (e.g., `data`), keep access level Private.
4. Click **Create**.

### Retrieve Connection String

1. **Security + networking** -> **Access keys**.
2. Show and copy the connection string for `key1`.

> **Enhancement -- Team Takeaway**: In production:
> - Use **Managed Identity** instead of connection strings where possible.
> - Enable **soft delete** for blob data protection.
> - Use **lifecycle management** policies to auto-archive old data.
> - Enable **versioning** for critical document collections.

---

## 12. Key Terms Glossary

| Term | Definition |
|------|-----------|
| **Architecture** | Fundamental organization of a system -- components, relationships, and governing principles. |
| **Orchestrator Pattern** | Centralised architecture with a single manager agent delegating to workers. |
| **Peer-to-Peer Pattern** | Decentralised architecture where agents communicate directly without a manager. |
| **Role Specialisation** | Assigning each agent a specific, well-defined job. |
| **Data Flow** | The path data takes through the system between agents. |
| **Orchestration** | Automated configuration, coordination, and management of agents and tasks. |
| **Sequential Execution** | Tasks run one after another in a specific order. |
| **Parallel Execution** | Multiple tasks run simultaneously. |
| **Conditional Branching** | Decision points that direct flow based on conditions. |
| **Routing** | Directing messages/tasks to appropriate agents. |
| **Content-Based Routing** | Routing based on message content or metadata. |
| **Round-Robin Routing** | Even distribution of tasks across similar agents. |
| **Priority-Based Routing** | Processing based on urgency levels. |
| **State** | Information a system stores about process status at a given time. |
| **Ephemeral State** | Temporary state for a single session. |
| **Persistent State** | State saved to database/file across sessions. |
| **Synchronisation** | Keeping data consistent across agents/systems. |
| **Concurrency** | Multiple agents accessing the same resource simultaneously. |
| **Conflict Detection** | Identifying when agents produce inconsistent state. |
| **Conflict Resolution** | Logic to resolve detected conflicts. |
| **Serialisation** | Converting objects to transmittable format (usually JSON). |
| **RAG** | Retrieval-Augmented Generation -- grounding LLM responses in retrieved documents. |
| **Kernel Function** | A method decorated with `@kernel_function` that agents can invoke. |
| **KernelBaseModel** | Semantic Kernel's Pydantic-based model class for structured data. |

---

## 13. Implementation Checklist

Use this checklist when starting a new multi-agent project:

### Architecture Phase
- [ ] Identify the business process to automate
- [ ] List all specialist roles needed
- [ ] Choose pattern: Orchestrator vs. Peer-to-Peer
- [ ] Draw architecture diagram with data flow arrows
- [ ] Identify failure points and bottlenecks
- [ ] Define state management strategy (ephemeral vs. persistent)

### Azure Setup Phase
- [ ] Create Azure AI Foundry resource
- [ ] Deploy LLM model (e.g., GPT-4o)
- [ ] Deploy embedding model (e.g., text-embedding-ada-002)
- [ ] Provision Azure SQL Database (if needed)
- [ ] Provision Azure Blob Storage (if needed)
- [ ] Configure firewall rules and access
- [ ] Set up `.env` file with credentials (never commit!)

### Implementation Phase
- [ ] Create project structure (src/, docs/, data/, tests/)
- [ ] Define Pydantic models for structured data
- [ ] Implement data connectors (SQL, Blob, ChromaDB)
- [ ] Write system prompts for each agent (who/what/don't/tools)
- [ ] Implement orchestration logic (sequential/parallel/conditional)
- [ ] Add routing logic if needed
- [ ] Implement state management (SharedState, plugins)
- [ ] Add error handling (retry, fallback, escalation)
- [ ] Write unit tests

### RAG-Specific Phase
- [ ] Set up ChromaDB with appropriate collections
- [ ] Implement embedding function (Azure OpenAI recommended)
- [ ] Build document ingestion pipeline
- [ ] Implement semantic search
- [ ] Test retrieval quality before connecting to agents

### Production Readiness Phase
- [ ] Centralise logging
- [ ] Add monitoring and alerting
- [ ] Implement rate limiting for Azure API calls
- [ ] Set up CI/CD pipeline
- [ ] Document API contracts between agents
- [ ] Create runbooks for common failure scenarios
- [ ] Security review (PII handling, credential management)

---

## Appendix: How Our Project Maps to These Concepts

| Course Concept | Our Implementation (Project 4) |
|---------------|-------------------------------|
| Orchestrator Pattern | `EnhancedBankingSequentialOrchestration` in `main_starter.py` |
| Sequential Execution | 6 agents run in sequence, each building on prior findings |
| Role Specialisation | Data Gatherer, Fraud Analyst, Loan Analyst, Support Specialist, Risk Analyst, Synthesis Coordinator |
| System Prompts | Detailed instructions per agent with role boundaries |
| State Management | `SharedState` (ephemeral) + ChromaDB (persistent) + Azure SQL (persistent) |
| RAG Pipeline | ChromaDB with Azure text-embedding-ada-002 for banking policy documents |
| Data Flow | Agent outputs feed into next agent's prompt; final synthesis produces `EnhancedBankingReport` |
| Routing | Implicit in sequential chain (orchestrator decides order) |
| Failure Handling | Graceful fallbacks in data connector, embedding function, and agent creation |
| Serialisation | Pydantic models (`EnhancedBankingReport`) for structured output |
| Azure SQL | `DataConnector` for customer transaction queries |
| Azure Blob Storage | `BlobConnector` for banking policy document storage |
| Azure AI Foundry | GPT-4o for agent reasoning + text-embedding-ada-002 for RAG embeddings |

---

*These notes are maintained as a living document. Update as new patterns and
lessons emerge from implementation.*
