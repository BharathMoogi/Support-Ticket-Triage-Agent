# 🎫 FlowBoard Support Ticket Triage Agent

> **Hackathon Submission**: An intelligent, context-grounded support ticket triage agent built with the Anthropic Claude & Groq APIs, pure-Python TF-IDF vector retrieval, automated factual verification, and a human-in-the-loop approval queue.

---

## 🌐 Featured AI Projects & Live Deployments

| Project | Live App / Demo URL | Description |
| :--- | :--- | :--- |
| **FlowBoard Triage Agent** | [FlowBoard Triage Agent — Dashboard](https://support-ticket-triage-agent-moogi-bharath-s-projects1.vercel.app/) | Context-aware support ticket triage agent with TF-IDF retrieval, two-pass verification, and human review queue. |
| **Mini Content Engine** | [Mini Content Engine](https://mini-content-engine.vercel.app/) | AI-powered multichannel content generation and optimization engine for structured copy creation. |
| **Candidate Screening System** | [AI-Powered Role-Based Candidate Screening](https://vercel.com/moogi-bharath-s-projects1/ai-powered-role-based-candidate-screening-system) | Intelligent resume evaluation, technical competence scoring, and automated candidate-role alignment. |

---

## 📌 Problem Statement

### Who Has the Problem?
Fast-growing B2B SaaS companies (like our fictional project management tool, **FlowBoard**) handling thousands of customer support inquiries monthly across billing inquiries, bug reports, workspace permissions, SSO integrations, and refund requests.

### What is the Bottleneck?
**The Context Gap.** 
Frontline support agents and standard zero-shot LLM chatbots frequently answer tickets without consulting:
1. **Internal Help Documentation**: Hallucinating refund terms (e.g. quoting a 30-day cash refund on monthly plans when the policy strictly allows 14 days for initial purchases only) or inventing non-existent UI flows.
2. **Customer Account Context**: Treating an Enterprise/Team client with custom SSO and SLA terms the same as a Free tier user with a 3-board limit.
3. **Product Boundaries**: Blindly accepting contradictory or fictional feature requests (e.g., holographic 3D VR projection modes) rather than politely grounding the customer in supported capabilities.

### Business Value
- **Zero Hallucinated Policies**: 100% of factual claims (refund windows, tier quotas, troubleshooting commands) are grounded in retrieved documentation.
- **Context-Aware Personalization**: Responses adapt automatically to customer plan tier (Free vs Pro vs Team), account age, and past ticket history.
- **Safety by Design**: Zero automated sends. Every verified draft is queued for human review with an interactive CLI.
- **Auditability**: Complete step-by-step reasoning, tool inputs/outputs, and verification logs saved per ticket in `/trajectories`.

---

## 🏗️ Architecture Overview

```
Incoming Support Ticket (JSON)
              │
              ▼
┌──────────────────────────────────────────────────────────┐
│                   Agent Pipeline                         │
│                                                          │
│  1. Classify Ticket (Category & Urgency via JSON Schema) │
│  2. Documentation Search (TF-IDF over docs/*.md)         │
│  3. Customer Context Lookup (data/customer_context.csv)  │
│  4. Initial Draft Generation                             │
│  5. Second-Pass Groundedness Verification (QA Inspector) │
│  6. Targeted Rewrite (if ungrounded claims detected)     │
└─────────────────────────────┬────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
  trajectories/{id}.json           agent/review_queue/{id}.json
  (Full Step Trace + Usage)        (Pending Human Review)
                                              │
                                              ▼
                                    approve_reply.py CLI
                                    (Approve / Edit / Reject)
                                              │
                                              ▼
                                       eval/score.py
                                 (Baseline vs Agent Eval)
```

---

## ⚡ Quick Start & Setup Instructions

Assuming a fresh environment, follow these exact commands to install dependencies, run the pipeline, and score the results.

### 1. Clone & Set Up Virtual Environment

```bash
# Clone or navigate to the repository
cd "Ticket Triage Agent"

# Create and activate a Python 3.11 virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example environment file
cp .env.example .env
```

Open `.env` in any editor and configure your preferred LLM provider:

**Option A: Anthropic Claude (Benchmark Standard)**
```ini
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-5
```

**Option B: Groq Cloud (Free Tier)**
```ini
GROQ_API_KEY=gsk_...
GROQ_MODEL=qwen/qwen3.8-27b
```

### 3. Run the Zero-Shot Baseline

Generates direct ungrounded replies without tools or doc access for all 18 tickets:
```bash
python baseline/baseline.py
```
*Outputs saved to `baseline/outputs/{ticket_id}.txt` and token usage to `baseline/outputs/usage.json`.*

### 4. Run the Tool-Calling Triage Agent

Runs the full retrieval, context lookup, drafting, and two-pass verification loop:
```bash
python agent/main.py
```
*Outputs saved to `agent/outputs/{ticket_id}.txt`, review queue items to `agent/review_queue/{ticket_id}.json`, and execution traces to `trajectories/{ticket_id}.json`.*

### 5. Human-in-the-Loop Review (CLI)

Inspect, approve, edit, or reject the AI-generated drafts:
```bash
# Launch interactive review session
python approve_reply.py

# Or list all items in the queue
python approve_reply.py --list
```

### 6. Run Evaluation & Scoring

Calculate cost comparison, load manual rubric entries, and print the improvement scorecard:
```bash
python eval/score.py
```

### 7. Launch the Web Dashboard

Start the built-in WSGI server to interact with tickets and review queue in a visual interface:
```bash
python server.py
```
*Open [http://localhost:8000](http://localhost:8000) or view the live cloud deployment on [Vercel](https://support-ticket-triage-agent-moogi-bharath-s-projects1.vercel.app).*

> 📖 For a detailed walkthrough, see [**REPRODUCTION.md**](REPRODUCTION.md).

---

## ⏱️ Expected Runtime & API Cost

Estimates for running the full 18-ticket synthetic evaluation benchmark:

| Pipeline Stage | Expected Runtime | Estimated Token Usage | Estimated API Cost (Claude Sonnet 4.5) | Estimated API Cost (Groq Free Tier) |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline Run** (`baseline/baseline.py`) | ~20 – 40 seconds | ~9,500 total tokens | **~$0.1243** ($0.0069/tkt) | **$0.00 (Free)** |
| **Agent Run** (`agent/main.py`) | ~60 – 90 seconds | ~42,000 total tokens | **~$0.4610** ($0.0256/tkt) | **$0.00 (Free)** |
| **Scoring & Verification** (`eval/score.py`) | < 2 seconds | Local / Offline | **$0.00** | **$0.00** |
| **Total Evaluation Suite** | **< 3 minutes** | **~51,500 tokens** | **< $0.60 total** | **$0.00 (Free)** |

---

## 📂 Repository Layout

```text
Ticket Triage Agent/
├── docs/                       # 16 FlowBoard help-center articles (Markdown)
├── tickets/                    # 18 synthetic test tickets (JSON files)
├── data/                       # Customer context metadata (customer_context.csv)
├── agent/                      # Core agent implementation
│   ├── retrieval.py            # TF-IDF doc chunking & in-memory vector search
│   ├── classify.py             # Structured JSON ticket classification
│   ├── customer_context.py     # Customer account context lookup
│   ├── verify.py               # Two-pass factual QA verification & auto-rewrite
│   ├── review_queue.py         # File-based review queue manager
│   ├── trajectory.py           # JSON audit logger with usage tracking
│   ├── main.py                 # Full agent loop runner
│   └── outputs/                # Verified agent drafts (.txt)
├── baseline/                   # No-tools baseline
│   ├── baseline.py             # Zero-shot runner
│   └── outputs/                # Baseline drafts (.txt) & usage.json
├── review_queue/               # Runtime review items (.json)
├── trajectories/               # Per-ticket run audit logs (.json)
├── eval/                       # Evaluation framework
│   ├── score.py                # Rubric comparison & cost calculator
│   └── manual_scoring.csv      # Human-scored rubric criteria
├── approve_reply.py            # Interactive human review CLI
├── requirements.txt            # anthropic, numpy, python-dotenv, rich, pytest
├── .env.example                # Secrets & configuration template
└── README.md                   # Project documentation
```

---

## 🔬 Improvement Changelog

| Stage | What I Tried & Why | Evidence | Decision / Learning |
| :--- | :--- | :--- | :--- |
| **1. Zero-Shot Baseline** | Sent raw ticket subject and body to LLM with generic prompt (`"You are a support agent..."`) to establish unassisted baseline. | **Factual Accuracy: 22.2% (4/18)**<br>**Hallucination Rate: 77.8% (14/18)**<br>Cost: $0.1243 ($0.0069/tkt) | Baseline hallucinated non-existent refund policies (e.g. 30-day refund for monthly users), invented wrong Okta SSO URLs, and failed customer tier awareness. |
| **2. TF-IDF Documentation Retrieval** | Implemented heading-aware chunking (~200 words) and local NumPy TF-IDF search to ground responses with zero API roundtrip latency. | **Retrieval Top-3 Precision: 100% (18/18)**<br>Factual Accuracy jumped **22.2% → 88.9% (16/18)** | Exact technical keyword matching (`ERR_WS_DISCONNECTED_502`, `14-day`, `VAT`, `SAML`) performed with 0ms network latency and deterministic ranking. |
| **3. Customer Context Grounding** | Integrated `get_customer_context` tool to dynamically inject plan tier (Free/Pro/Team), signup date, and past ticket volume. | **Tier Awareness: 100% (18/18)**<br>Prevented plan misattribution across all 18 tickets. | Agent stopped suggesting Pro features to Free users without explaining upgrade paths, and prioritized Team tier SLAs accurately (<4h). |
| **4. Two-Pass Verification & Auto-Rewrite** | Built secondary QA inspector LLM call in `verify.py` that cross-examines draft sentences against retrieved docs and triggers targeted rewrite if ungrounded. | **Hallucination Rate: 0.0% (0/18)**<br>Hallucination Reduction: **-77.8%** (14/18 → 0/18)<br>Final Groundedness: **100% (18/18)** | Successfully caught edge cases (e.g., non-existent VR headset feature in TKT-015) and corrected unverified assertions before saving. |
| **5. [REMOVED EXPERIMENT] External Embeddings API (Voyage/OpenAI)** | Experimented with dense semantic embeddings via remote API instead of local TF-IDF for knowledge retrieval. | **Latency increased +1.8s/ticket**.<br>Mishandled exact alphanumeric error codes (`ERR_WS_DISCONNECTED_502`) and short numbers (`14-day`, `502`). | **Removed & Reverted:** Replaced with pure NumPy TF-IDF which is 100% offline, zero-cost, zero-latency, and superior on technical identifiers. |
| **6. Human-in-the-Loop Review Queue** | Replaced direct automated sending with an append-only JSON review queue (`/agent/review_queue`) and built interactive CLI and web dashboard. | **10 Approved (55.6%)**<br>**8 Edited/Polished (44.4%)**<br>**0 Rejected (0.0%)** | Guarantees 100% human oversight before customer delivery, satisfying strict security, compliance, and empathy standards. |

---

## 🧪 Running the Test Suite

To verify all unit tests, schemas, retrieval engines, and review queue modules:

```bash
python -m pytest tests/ -v
```
*(68 unit tests passing across all components).*
