# 🛡️ Investor Ops & Intelligence Suite
### *Bridging Customer Feedback and Operational Appointment Workflows*

[![Project Status](https://img.shields.io/badge/Status-Operational-success)](https://github.com/nish1502/investor-ops-intelligence-suite)
[![AI Workflows](https://img.shields.io/badge/Stack-Groq%20|%20FastAPI%20|%20MCP-blue)](https://github.com/nish1502/investor-ops-intelligence-suite)
[![Role Focus](https://img.shields.io/badge/Focus-AI%20Ops%20|%20Workflow%20Automation-orange)](https://github.com/nish1502/investor-ops-intelligence-suite)

---

## 🎯 Overview

Fintech product teams and frontline support agents often operate in information silos. While product analysts monitor user feedback trends, client-facing advisors rarely have access to that live context before dial-in. This gap leads to operational inefficiencies and reactive problem-solving.

The **Investor Ops Intelligence Suite** bridges this gap by connecting live user analytics directly to appointment setup. By syncing **Sentiment Analytics**, **High-Precision Knowledge Search**, and an **Orchestrated Voice Agent**, the system automatically populates advisor briefings with actionable client context before the call ever begins.

---

## 🗺️ Workflow Architecture

A visual look at how data flows from incoming feedback to final automated operational actions:

```mermaid
graph LR
    %% Nodes
    A[📩 Raw Reviews] --> B(🔍 Pulse Analytics)
    B --> C{🔥 Hot Theme}
    
    D[📄 PDF Docs] --> E(🧠 RAG Engine)
    E --> F{✅ Verified Fact}

    C --> G[🎙️ Voice Assistant]
    F --> G

    G --> H[🤖 MCP Actions]
    
    H --> I[📅 Calendar Hold]
    H --> J[✉️ Gmail Draft]
    H --> K[📝 Log Entry]

    %% Styling
    style C fill:#ffebcc,stroke:#f90,stroke-width:1px
    style F fill:#e6f3ff,stroke:#007acc,stroke-width:1px
    style G fill:#f2e6ff,stroke:#9933ff,stroke-width:2px
    style H fill:#e6ffe6,stroke:#00cc00,stroke-width:2px
```

---

## 🔄 Operational Workflow Flow

Data moves across connected workflows to reduce operational delays:

1.  **Data Ingestion**: Aggregates customer reviews and redacts sensitive PII using deterministic logic.
2.  **Trend Identification**: Evaluates feedback clusters to define the current active alert theme.
3.  **Context Awareness**: The **Voice Agent** adapts to this runtime state, injecting the active trend context into advisor conversations.
4.  **Workflow Automation**: Upon user confirmation, the orchestrator triggers operational workflows via MCP: generating tentative calendar events, logging audit trails, and drafting pre-briefs.
5.  **Advisor Handoff**: The frontline agent opens their inbox to find a prepopulated **Gmail Draft** with the exact client and market details needed for the call.

---

## 🌐 Active Interfaces
You can interact with the live endpoints of the platform here:

*   **🖥️ Unified Dashboard**: [https://investor-ops-intelligence-suite.vercel.app](https://investor-ops-intelligence-suite.vercel.app) 
*   **🧠 Knowledge API**: [https://m1-rag-faq.onrender.com](https://m1-rag-faq.onrender.com/docs)
*   **🎙️ Scheduling Hub**: [https://m3-orchestrator.onrender.com](https://m3-orchestrator.onrender.com)

---

## 🏗️ System Pillars

### 🧬 Pillar 1: High-Precision Knowledge (RAG)
*Retrieves factual answers anchored strictly within authorized institutional PDFs.*
- **Operational Bottleneck**: Advisors lose time manually sourcing complex fee schemas hidden in PDFs.
- **The Fix**: A retrieval system enforcing strict metadata pre-filtering before vector searches, preventing cross-document hallucination errors.

### 📈 Pillar 2: The Intel Engine (Pulse)
*Transforms chaotic qualitative datasets into structured tracking alerts.*
- **Operational Bottleneck**: Manually quantifying thousands of qualitative app reviews creates bottlenecks.
- **The Fix**: A periodic analytics backend summarizing trending metrics and caching the summary artifact for low-latency cross-system reading.

### 🤖 Pillar 3: Orchestrated Actions (Scheduler)
*Utilizes event handlers to synchronize conversational state with workplace tools.*
- **Operational Bottleneck**: Confirmed bookings require repetitive manual admin setup across systems.
- **The Fix**: An intent-driven handler utilizing the **Model Context Protocol (MCP)** to trigger calendar, logging, and messaging workflows automatically.

---

## ⚙️ Technical Rationale
Design decisions tied directly to fintech stability and reliability:

*   **Why Enforce Metadata Constraints?** 
    Semantic similarity alone can inadvertently pull from adjacent funds. Filtering strictly by source ID first guarantees data integrity.
*   **Why Utilize FastMCP Integration?**
    Standardizing tool definitions speeds up development cycle-time and decreases maintenance overhead compared to bespoke client SDK wrapping.
*   **Why Implement Draft-Only Automation (HITL)?**
    Fully autonomous external communication creates compliance risk. Staging drafts ensures a **Human-In-The-Loop** reviews output before submission.

---

## 🛡️ Reliability & Safety Suitability
Evaluated behavior constraints verified through standardized checks:

| Category | Logic & Handling | Observed Reliability |
| :--- | :--- | :--- |
| **Source Fidelity** | Citation Anchoring. | Consistently maintains faithfulness to provided links in testing. |
| **Compliance** | Prompt Refusal Hooks. | Evaluated successfully to decline investment-buying advice triggers. |
| **Structural Fit** | Format Sanitizers. | Ensures predictable, well-formed response schemas every time. |

---

## 🛠️ Technology Stack
- **Frameworks**: Python 3.10, FastAPI, React, Next.js.
- **Databases**: PostgreSQL (pgvector), Cached JSON artifacts.
- **Intelligence**: Groq (Llama 3) chosen for low-latency inference response times.
- **Protocols**: Model Context Protocol (MCP) bridging Google Workspace workflows.

---

## 📂 Repository Map
```text
├── dashboard/                   # Operational control plane
├── indmoney-pulse/              # The analysis & redact layer (M2)
├── mf-rag-faq-indmoney/         # Retrieval & Search layer (M1)
├── multi-agent-appointment.../  # Automated workflow engine (M3)
├── docs/                        # Architecture & Specs
├── SOURCES.md                   # Approved URL Manifests
└── EVALS.md                     # Reliability validation report
```

---

# 🏗️ High-Level System Structure

The platform was intentionally separated into independent operational layers instead of one monolithic AI application.

```text
investor-ops-intelligence-suite/
│
├── dashboard/                           
│   ├── app/page.tsx
│   ├── app/api/m2/route.ts
│   └── app/api/run-analysis/
│
├── mf-rag-faq-indmoney/                
│   ├── retrieval.py
│   ├── embedding.py
│   ├── scraper.py
│   ├── api.py
│   └── architecture.md
│
├── indmoney-pulse/                     
│   ├── backend/main.py
│   ├── backend/src/phase1_ingestion/
│   ├── backend/src/phase2_theme_engine/
│   ├── backend/src/phase3_pulse_generator/
│   └── ARCHITECTURE.md
│
├── multi-agent-appointment-orchestrator/
│   ├── production/server.py
│   ├── production/orchestrator.py
│   ├── production/booking_logic.py
│   ├── production/nlu_engine.py
│   ├── production/mcp_server.py
│   └── production/google_calendar_auth.py
│
├── EVALS.md
├── run_evals.py
└── README.md
```

---

# 🔹 Retrieval Layer (M1 — RAG System)

### Purpose
Grounded financial retrieval using official AMC, SEBI, and AMFI documents.

### Important Files

| File | Responsibility |
|---|---|
| `scraper.py` | Collects official financial documents |
| `embedding.py` | Converts chunks into vector embeddings |
| `retrieval.py` | Retrieves contextually relevant chunks |
| `api.py` | Exposes retrieval endpoints |
| `architecture.md` | Documents RAG workflow architecture |

### Design Goal
Reduce hallucinations using retrieval-first grounded generation.

---

# 🔹 Operational Intelligence Layer (M2 — Pulse Engine)

### Purpose
Transforms customer reviews into operational insights and trend summaries.

### Important Files

| File / Folder | Responsibility |
|---|---|
| `main.py` | Main analytics workflow controller |
| `phase1_ingestion/` | Cleans and ingests review datasets |
| `phase2_theme_engine/` | Clusters reviews into operational themes |
| `phase3_pulse_generator/` | Generates summaries and recommendations |
| `ARCHITECTURE.md` | Pulse system architecture notes |

### Design Goal
Convert large-scale qualitative feedback into structured operational intelligence.

---

# 🔹 Workflow Orchestration Layer (M3)

### Purpose
Converts conversational requests into operational workflows.

### Important Files

| File | Responsibility |
|---|---|
| `server.py` | FastAPI orchestration backend |
| `orchestrator.py` | Workflow coordination and state management |
| `booking_logic.py` | Slot validation and operational rules |
| `nlu_engine.py` | Intent detection and entity extraction |
| `mcp_server.py` | Gmail, Docs, and Calendar integrations |
| `google_calendar_auth.py` | OAuth authentication flows |

### Design Goal
Separate AI interpretation from deterministic operational execution.

---

# 🔹 Unified Dashboard Layer

### Purpose
Acts as the centralized operational control plane.

### Important Files

| File | Responsibility |
|---|---|
| `page.tsx` | Unified operational dashboard |
| `route.ts` | Analytics API integration |
| `run-analysis/` | Workflow trigger endpoints |

### Design Goal
Provide one interface across retrieval, analytics, and orchestration systems.

---

# 🔹 Evaluation & Reliability Layer

### Important Files

| File | Responsibility |
|---|---|
| `EVALS.md` | Evaluation methodology |
| `run_evals.py` | Retrieval and compliance testing |

### Evaluation Focus
- retrieval relevance
- grounded responses
- refusal behavior
- PII protection
- operational reliability

---

# 🛡️ Design Philosophy

The platform was designed around:
- modular architecture
- deterministic workflow control
- compliance-aware automation
- human-in-the-loop approvals
- operational reliability
- failure isolation

The goal was not building isolated AI demos, but creating a connected operational workflow platform.

---

## 🚀 System Launch
1. **Clone**: `git clone https://github.com/nish1502/investor-ops-intelligence-suite.git`
2. **Credentials**: Define security tokens in the local `.env` files.
3. **Backends**: Run FastAPI instance commands stored within M1 and M3 subdirectories.
4. **Interface**: Navigate to `/dashboard` and execute `npm install && npm run dev`.



