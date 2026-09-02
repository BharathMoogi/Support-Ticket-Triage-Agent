# 📖 End-to-End Reproduction Guide

This guide provides step-by-step instructions to reproduce the entire **FlowBoard Support Ticket Triage Agent** benchmark from a clean repository clone.

---

## 🌐 Featured AI Projects & Live Deployments

- **FlowBoard Triage Agent — Dashboard**: [https://support-ticket-triage-agent-moogi-bharath-s-projects1.vercel.app/](https://support-ticket-triage-agent-moogi-bharath-s-projects1.vercel.app/)
- **Mini Content Engine**: [https://mini-content-engine.vercel.app/](https://mini-content-engine.vercel.app/)
- **AI-Powered Role-Based Candidate Screening System**: [https://vercel.com/moogi-bharath-s-projects1/ai-powered-role-based-candidate-screening-system](https://vercel.com/moogi-bharath-s-projects1/ai-powered-role-based-candidate-screening-system)

---

## 📋 System Requirements

- **Python**: 3.10, 3.11, or 3.12 (Python 3.11+ recommended)
- **Git**: Installed and available in PATH
- **Operating System**: macOS, Linux, or Windows (PowerShell / Command Prompt)
- **API Key**: Either **Anthropic Claude** (Claude Sonnet 4.5) or **Groq Cloud** (Free Tier: qwen/qwen3.8-27b)

---

## 🚀 Quick Setup from a Clean Clone

### 1. Clone the Repository

`ash
git clone https://github.com/BharathMoogi/Support-Ticket-Triage-Agent.git
cd Support-Ticket-Triage-Agent
`

### 2. Create and Activate a Virtual Environment

**macOS / Linux:**
`ash
python3 -m venv .venv
source .venv/bin/activate
`

**Windows (PowerShell):**
`powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
`

**Windows (Command Prompt):**
`cmd
python -m venv .venv
.venv\Scripts\activate.bat
`

### 3. Install Required Dependencies

`ash
pip install --upgrade pip
pip install -r requirements.txt
`

---

## 🔑 Configure Environment Variables (.env)

Copy the example environment configuration template:

`ash
cp .env.example .env
`

Open .env in any text editor and configure your preferred LLM provider:

### Option A: Anthropic Claude (Benchmark Standard)
`ini
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-copied-key
ANTHROPIC_MODEL=claude-sonnet-4-5
`

### Option B: Groq Cloud (Free Tier)
`ini
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=qwen/qwen3.8-27b
`

*(Note: If both keys are set, GROQ_API_KEY will be used if ANTHROPIC_API_KEY is empty, or you can switch between them at any time.)*

---

## 🏃 Execution Workflow

### Step 1: Run the Zero-Shot Baseline (No Tools)

Executes the unassisted zero-shot model across all 18 benchmark tickets without tool calling, documentation search, or customer context:

`ash
python baseline/baseline.py
`

- **Output files**: aseline/outputs/TKT-001.txt ... aseline/outputs/TKT-018.txt
- **Token usage log**: aseline/outputs/usage.json
- **Expected runtime**: ~25 – 45 seconds

---

### Step 2: Run the Context-Aware Triage Agent

Runs the full tool-calling triage pipeline:
1. Classifies category and urgency (gent/classify.py)
2. Retrieves relevant policy/help articles via TF-IDF search (gent/retrieval.py)
3. Looks up customer tier and history (gent/customer_context.py)
4. Composes an empathetic initial draft
5. Performs second-pass groundedness verification and automated rewrite (gent/verify.py)
6. Writes audit logs to 	rajectories/ and queued items to gent/review_queue/

`ash
python agent/main.py
`

- **Output files**: gent/outputs/TKT-001.txt ... gent/outputs/TKT-018.txt
- **Review Queue items**: gent/review_queue/TKT-001.json ... gent/review_queue/TKT-018.json
- **Trajectory audit logs**: 	rajectories/TKT-001.json ... 	rajectories/TKT-018.json
- **Expected runtime**: ~60 – 120 seconds

---

### Step 3: Interactive Human Review (CLI)

Review, approve, edit, or reject the verified AI drafts:

`ash
# Launch interactive human review CLI session
python approve_reply.py

# Or list current status of all 18 tickets
python approve_reply.py --list
`

---

### Step 4: Run the Evaluation Scoring Harness

Computes accuracy deltas, hallucination reduction, and exact token costs:

`ash
python eval/score.py
`

- **Rubric source**: eval/manual_scoring.csv
- **Generates**: Full comparison table, % groundedness delta, and cost breakdown.

---

### Step 5: Run Automated Unit Tests

Runs all 68 unit tests verifying retrieval indexing, prompt formats, verification validators, tool schemas, and review queue mechanics:

`ash
python -m pytest tests/ -v
`

---

### Step 6: Launch the Web Dashboard

Start the built-in WSGI web server to interact with tickets and review queue in a visual interface:

`ash
python server.py
`

- Open **http://localhost:8000** in your browser.
- **Review Queue Tab**: Inspect pending review cards, citations, and grounded verification summaries.
- **Test Tickets Tab**: Browse 18 synthetic benchmark tickets and run single-click on-demand triage.
- **Knowledge Base Tab**: Explore all 16 FlowBoard markdown documentation articles.
- **Scorecard Tab**: Live visual scorecard comparing Baseline vs. Agent performance.

---

## ⏱️ Expected Runtime & API Cost Breakdown

Estimates for a complete end-to-end run on the 18-ticket benchmark dataset:

| Stage | Expected Duration | Token Usage (18 Tickets) | Estimated Cost (Claude 3.5/Sonnet 4.5) | Estimated Cost (Groq Free Tier) |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline Run** (aseline/baseline.py) | ~20 – 40s | ~9,500 tokens | **~.1243** (.0069/ticket) | **.00 (Free)** |
| **Agent Triage Run** (gent/main.py) | ~60 – 90s | ~42,000 tokens | **~.4610** (.0256/ticket) | **.00 (Free)** |
| **Verification & Scoring** (eval/score.py) | < 2s | Offline / Local | **.00** | **.00** |
| **Test Suite** (pytest tests/) | ~3 – 5s | Local | **.00** | **.00** |
| **Total Full Run** | **< 3 minutes** | **~51,500 tokens** | **< .60 Total** | **.00 (Free)** |

---

## 📊 Benchmark Results Reference

| Metric | Zero-Shot Baseline (No Tools) | Agent (Tool-Calling + Grounded) | Improvement |
| :--- | :---: | :---: | :---: |
| **Factual Accuracy** | 22.2% (4/18) | **100.0% (18/18)** | **+77.8%** |
| **Hallucination Rate** | 77.8% (14/18) | **0.0% (0/18)** | **-77.8%** |
| **Classification Accuracy** | N/A | **100.0% (18/18)** | **100% Precision** |
| **Human Review Approval** | N/A | **10 Approved / 8 Polished / 0 Rejected** | **100% Production Ready** |

---

## 🛠️ Troubleshooting

1. **No module named 'agent'**:
   Ensure you run commands from the project root directory where gent/ and aseline/ reside.

2. **ModuleNotFoundError: No module named 'httpx'**:
   Run pip install -r requirements.txt to ensure all dependencies are installed.

3. **Rate Limit on Groq (TPM limit)**:
   Use GROQ_MODEL=qwen/qwen3.8-27b which has high throughput and works reliably on the free tier.
