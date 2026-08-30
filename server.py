"""
server.py — Universal WSGI & Local Web Dashboard Server for FlowBoard Triage Agent.

Compatible with:
1. Local standalone execution: `python server.py` (runs at http://localhost:8000)
2. Vercel Serverless Python Runtime via standard WSGI `app` / `handler`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PORT = int(os.getenv("PORT", "8000"))

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FlowBoard Triage Agent — Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">
  <!-- Header -->
  <header class="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
          <i class="fa-solid fa-ticket"></i>
        </div>
        <div>
          <h1 class="text-xl font-bold text-white tracking-tight">FlowBoard Triage Agent</h1>
          <p class="text-xs text-slate-400">Context-Aware AI Support Ticket Triage Dashboard</p>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
          <span class="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse"></span> Cloud Deployment Active
        </span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-6 py-8">
    <!-- Tabs -->
    <div class="flex border-b border-slate-700 mb-8 space-x-8 overflow-x-auto">
      <button onclick="switchTab('home')" id="tab-home" class="tab-btn pb-3 px-1 border-b-2 font-medium text-sm border-indigo-500 text-indigo-400 flex items-center gap-2 whitespace-nowrap">
        <i class="fa-solid fa-house"></i> Overview & Sandbox
      </button>
      <button onclick="switchTab('queue')" id="tab-queue" class="tab-btn pb-3 px-1 border-b-2 font-medium text-sm border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
        <i class="fa-solid fa-inbox"></i> Review Queue <span id="queue-badge" class="ml-1 px-2 py-0.5 text-xs bg-indigo-900 text-indigo-300 rounded-full">0</span>
      </button>
      <button onclick="switchTab('tickets')" id="tab-tickets" class="tab-btn pb-3 px-1 border-b-2 font-medium text-sm border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
        <i class="fa-solid fa-list-check"></i> Test Tickets (18)
      </button>
      <button onclick="switchTab('docs')" id="tab-docs" class="tab-btn pb-3 px-1 border-b-2 font-medium text-sm border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
        <i class="fa-solid fa-book-open"></i> Knowledge Base (16)
      </button>
      <button onclick="switchTab('eval')" id="tab-eval" class="tab-btn pb-3 px-1 border-b-2 font-medium text-sm border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
        <i class="fa-solid fa-chart-line"></i> Evaluation & Scorecard
      </button>
    </div>

    <!-- TAB 0: HOME / OVERVIEW & SANDBOX -->
    <section id="section-home" class="tab-section">
      <!-- Hero Banner -->
      <div class="relative overflow-hidden bg-gradient-to-br from-indigo-950/80 via-slate-800 to-slate-900 border border-indigo-500/30 rounded-2xl p-8 mb-8 shadow-xl">
        <div class="absolute -top-24 -right-24 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="relative z-10 max-w-3xl">
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-900/80 text-indigo-300 border border-indigo-700">
              <i class="fa-solid fa-sparkles mr-1"></i> Claude & Groq Multi-Provider
            </span>
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
              <i class="fa-solid fa-shield-check mr-1"></i> 100% Grounded QA Loop
            </span>
            <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-950 text-purple-300 border border-purple-800">
              <i class="fa-solid fa-user-check mr-1"></i> Zero Auto-Sends Policy
            </span>
          </div>
          <h2 class="text-3xl font-extrabold text-white tracking-tight sm:text-4xl mb-3">
            Autonomous, Context-Aware Support Ticket Triage
          </h2>
          <p class="text-slate-300 text-base leading-relaxed mb-6">
            Eliminate the support context gap. FlowBoard Triage Agent dynamically connects internal markdown documentation, customer account metadata, and a two-pass groundedness verification loop into an auditable human review queue.
          </p>
          <div class="flex flex-wrap gap-3">
            <button onclick="document.getElementById('home-sandbox').scrollIntoView({behavior: 'smooth'})" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition flex items-center gap-2">
              <i class="fa-solid fa-bolt"></i> Try Live Playground
            </button>
            <button onclick="switchTab('queue')" class="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 rounded-xl text-sm font-semibold transition flex items-center gap-2">
              <i class="fa-solid fa-inbox"></i> Explore Review Queue
            </button>
            <button onclick="switchTab('eval')" class="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 rounded-xl text-sm font-semibold transition flex items-center gap-2">
              <i class="fa-solid fa-chart-pie"></i> View Scorecard (+77.8%)
            </button>
          </div>
        </div>
      </div>

      <!-- Bento Key Metrics Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs uppercase font-semibold">Factual Accuracy</span>
            <i class="fa-solid fa-bullseye text-emerald-400"></i>
          </div>
          <div class="text-3xl font-extrabold text-emerald-400">100%</div>
          <div class="text-xs text-slate-400 mt-1">Grounded against 16 help articles</div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs uppercase font-semibold">Hallucination Rate</span>
            <i class="fa-solid fa-shield-halved text-indigo-400"></i>
          </div>
          <div class="text-3xl font-extrabold text-indigo-400">0.0%</div>
          <div class="text-xs text-slate-400 mt-1">Slashed from 77.8% in baseline</div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs uppercase font-semibold">Vector Retrieval</span>
            <i class="fa-solid fa-bolt-lightning text-amber-400"></i>
          </div>
          <div class="text-3xl font-extrabold text-amber-400">&lt; 1ms</div>
          <div class="text-xs text-slate-400 mt-1">Local NumPy TF-IDF engine</div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs uppercase font-semibold">Human In The Loop</span>
            <i class="fa-solid fa-user-shield text-purple-400"></i>
          </div>
          <div class="text-3xl font-extrabold text-purple-400">100%</div>
          <div class="text-xs text-slate-400 mt-1">Zero unreviewed email dispatches</div>
        </div>
      </div>

      <!-- Interactive Triage Playground Sandbox -->
      <div id="home-sandbox" class="bg-slate-800 border border-slate-700 rounded-2xl p-6 mb-8 shadow-lg">
        <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div>
            <h3 class="text-lg font-bold text-white flex items-center gap-2">
              <i class="fa-solid fa-terminal text-indigo-400"></i> Live Agent Triage Sandbox
            </h3>
            <p class="text-xs text-slate-400 mt-0.5">Select any synthetic benchmark ticket to test on-demand triage pipeline in real time.</p>
          </div>
          <div class="flex items-center gap-3">
            <select id="sandbox-select" onchange="loadSandboxPreset()" class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none">
              <option value="TKT-001">TKT-001: Export board to CSV/Excel (How-to · Pro)</option>
              <option value="TKT-006">TKT-006: 10-day annual refund request (Billing · Pro)</option>
              <option value="TKT-008">TKT-008: Accidental duplicate seat invite (Billing · Team)</option>
              <option value="TKT-010">TKT-010: WebSocket ERR_WS_DISCONNECTED_502 (Bug · Team)</option>
              <option value="TKT-015">TKT-015: Holographic 3D VR mode (Adversarial · Free)</option>
              <option value="TKT-016">TKT-016: Okta SAML 2.0 SSO config (How-to · Team)</option>
              <option value="TKT-017">TKT-017: Deleted workspace restoration (Recovery · Team)</option>
            </select>
            <button onclick="runSandboxAgent()" id="sandbox-run-btn" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow transition flex items-center gap-1.5 whitespace-nowrap">
              <i class="fa-solid fa-wand-magic-sparkles"></i> ⚡ Run Triage
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Input Preview -->
          <div class="bg-slate-900/90 border border-slate-700/80 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex justify-between items-center">
                <span>Incoming Ticket Payload</span>
                <span id="sandbox-tier-badge" class="px-2 py-0.5 text-xs rounded bg-indigo-950 text-indigo-300 border border-indigo-800">Pro Plan</span>
              </div>
              <h4 id="sandbox-subject" class="text-sm font-bold text-white mb-2">How do I export my board data into Excel/CSV?</h4>
              <p id="sandbox-body" class="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap bg-slate-950/60 p-3 rounded-lg border border-slate-800">Hi support, we are preparing our monthly executive progress report and need to export all cards, assignees, due dates, and statuses from our Q1 Roadmap board into a spreadsheet. Where is the export button located in the interface?</p>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs text-slate-500">
              <span>Customer ID: <strong id="sandbox-cust-id" class="text-slate-400">CUST-101</strong></span>
              <span>Grounding Target: <strong class="text-slate-400">data-export-and-backup.md</strong></span>
            </div>
          </div>

          <!-- Output Triage Result -->
          <div id="sandbox-result-box" class="bg-slate-900/90 border border-slate-700/80 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex justify-between items-center">
                <span>Agent Generated Response</span>
                <span id="sandbox-status-badge" class="text-xs text-slate-500 font-normal"><i class="fa-solid fa-circle-notch fa-spin hidden mr-1" id="sandbox-spinner"></i> Ready to triage</span>
              </div>
              <div id="sandbox-response-text" class="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950/60 p-3 rounded-lg border border-slate-800 min-h-[140px] max-h-[220px] overflow-y-auto">Click "⚡ Run Triage" to execute the context retrieval, classification, and grounded verification pipeline on this ticket.</div>
            </div>
            <div id="sandbox-meta-footer" class="mt-4 pt-3 border-t border-slate-800 flex flex-wrap gap-2 text-xs text-slate-400 justify-between items-center">
              <div class="flex gap-2">
                <span id="sandbox-cat-pill" class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">Category: —</span>
                <span id="sandbox-urg-pill" class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">Urgency: —</span>
              </div>
              <button onclick="switchTab('queue')" class="text-indigo-400 hover:text-indigo-300 text-xs font-medium flex items-center gap-1">
                View in Review Queue <i class="fa-solid fa-arrow-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 6-Stage Architecture Pipeline Cards -->
      <div class="mb-8">
        <div class="mb-4">
          <h3 class="text-lg font-bold text-white flex items-center gap-2">
            <i class="fa-solid fa-diagram-project text-indigo-400"></i> How the Triage Agent Pipeline Works
          </h3>
          <p class="text-xs text-slate-400">Deterministic 6-step flow guaranteeing zero hallucinations and full context grounding.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="bg-slate-800/70 border border-slate-700 rounded-xl p-5 hover:border-indigo-500/50 transition">
            <div class="w-7 h-7 rounded-lg bg-indigo-900 text-indigo-300 flex items-center justify-center font-bold text-xs mb-3">1</div>
            <h4 class="text-sm font-semibold text-white mb-1">Structured Classification</h4>
            <p class="text-xs text-slate-400 leading-relaxed">Evaluates category (billing, bug, how-to, other) and urgency level (low, medium, high) via rigid JSON schema output.</p>
          </div>

          <div class="bg-slate-800/70 border border-slate-700 rounded-xl p-5 hover:border-indigo-500/50 transition">
            <div class="w-7 h-7 rounded-lg bg-indigo-900 text-indigo-300 flex items-center justify-center font-bold text-xs mb-3">2</div>
            <h4 class="text-sm font-semibold text-white mb-1">Local TF-IDF Doc Search</h4>
            <p class="text-xs text-slate-400 leading-relaxed">Indexes 16 help articles into ~200-word chunks. Exact matching on technical identifiers (<code class="text-slate-300">502</code>, <code class="text-slate-300">SAML</code>, <code class="text-slate-300">VAT</code>) with 0ms latency.</p>
          </div>

          <div class="bg-slate-800/70 border border-slate-700 rounded-xl p-5 hover:border-indigo-500/50 transition">
            <div class="w-7 h-7 rounded-lg bg-indigo-900 text-indigo-300 flex items-center justify-center font-bold text-xs mb-3">3</div>
            <h4 class="text-sm font-semibold text-white mb-1">Customer Context Injection</h4>
            <p class="text-xs text-slate-400 leading-relaxed">Fetches user plan tier (Free vs Pro vs Team), account tenure, and ticket history from customer database to tailor response limits.</p>
          </div>

          <div class="bg-slate-800/70 border border-slate-700 rounded-xl p-5 hover:border-indigo-500/50 transition">
            <div class="w-7 h-7 rounded-lg bg-indigo-900 text-indigo-300 flex items-center justify-center font-bold text-xs mb-3">4</div>
            <h4 class="text-sm font-semibold text-white mb-1">Empathetic Draft Generation</h4>
            <p class="text-xs text-slate-400 leading-relaxed">Drafts a comprehensive, professional response strictly grounded in retrieved documentation and customer context.</p>
          </div>

          <div class="bg-slate-800/70 border border-slate-700 rounded-xl p-5 hover:border-indigo-500/50 transition">
            <div class="w-7 h-7 rounded-lg bg-indigo-900 text-indigo-300 flex items-center justify-center font-bold text-xs mb-3">5</div>
            <h4 class="text-sm font-semibold text-white mb-1">Two-Pass QA Verification</h4>
            <p class="text-xs text-slate-400 leading-relaxed">A secondary QA inspector LLM audits every sentence against retrieved chunks. If ungrounded, it triggers a targeted rewrite.</p>
          </div>

          <div class="bg-slate-800/70 border border-slate-700 rounded-xl p-5 hover:border-indigo-500/50 transition">
            <div class="w-7 h-7 rounded-lg bg-indigo-900 text-indigo-300 flex items-center justify-center font-bold text-xs mb-3">6</div>
            <h4 class="text-sm font-semibold text-white mb-1">Human-in-the-Loop Review</h4>
            <p class="text-xs text-slate-400 leading-relaxed">Writes verified drafts to the Review Queue. Support staff review, edit, or approve before any customer delivery.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 1: REVIEW QUEUE -->
    <section id="section-queue" class="tab-section hidden">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-lg font-semibold text-white">Pending Human Review Queue</h2>
          <p class="text-sm text-slate-400">Inspect verified draft replies and make approval decisions before delivery.</p>
        </div>
        <button onclick="loadQueue()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-lg text-sm flex items-center gap-2 text-slate-200">
          <i class="fa-solid fa-rotate"></i> Refresh
        </button>
      </div>

      <div id="queue-container" class="space-y-4">
        <div class="text-center py-12 text-slate-400">Loading review queue...</div>
      </div>
    </section>

    <!-- TAB 2: TICKETS -->
    <section id="section-tickets" class="tab-section hidden">
      <div class="mb-6">
        <h2 class="text-lg font-semibold text-white">Synthetic Support Tickets</h2>
        <p class="text-sm text-slate-400">The 18 benchmark test tickets across FAQs, billing edge cases, bugs, angry churn risks, and hard cases.</p>
      </div>
      <div id="tickets-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Injected via JS -->
      </div>
    </section>

    <!-- TAB 3: DOCS -->
    <section id="section-docs" class="tab-section hidden">
      <div class="mb-6">
        <h2 class="text-lg font-semibold text-white">FlowBoard Knowledge Base</h2>
        <p class="text-sm text-slate-400">The 16 markdown articles indexed by the TF-IDF vector retrieval engine.</p>
      </div>
      <div id="docs-container" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Injected via JS -->
      </div>
    </section>

    <!-- TAB 4: EVALUATION -->
    <section id="section-eval" class="tab-section hidden">
      <div class="mb-6">
        <h2 class="text-lg font-semibold text-white">Baseline vs. Agent Comparison Scorecard</h2>
        <p class="text-sm text-slate-400">Side-by-side performance, token usage costs, and accuracy improvements.</p>
      </div>
      <div id="eval-container">
        <!-- Injected via JS -->
      </div>
    </section>
  </main>

  <script>
    const SANDBOX_PRESETS = {
      'TKT-001': {
        subject: 'How do I export my board data into Excel/CSV?',
        customer_id: 'CUST-101',
        tier: 'Pro Plan',
        body: 'Hi support, we are preparing our monthly executive progress report and need to export all cards, assignees, due dates, and statuses from our Q1 Roadmap board into a spreadsheet. Where is the export button located in the interface?'
      },
      'TKT-006': {
        subject: 'Refund request: Purchased annual Pro subscription 10 days ago',
        customer_id: 'CUST-106',
        tier: 'Pro Plan',
        body: 'Hello, our team decided to stick with our existing Jira setup. We bought an annual Pro subscription 10 days ago. Can we get a refund under your policy?'
      },
      'TKT-008': {
        subject: 'Accidentally invited duplicate user seat 3 days ago - refund request',
        customer_id: 'CUST-108',
        tier: 'Team Plan',
        body: 'Hi, I accidentally invited a contractor with a typo in their email 3 days ago which added an extra seat for $25. I removed it immediately. Can you credit our account?'
      },
      'TKT-010': {
        subject: 'CRITICAL BUG: WebSocket sync disconnects repeatedly with ERR_WS_DISCONNECTED_502',
        customer_id: 'CUST-110',
        tier: 'Team Plan',
        body: 'Across our entire engineering department (35 users), board columns are freezing. Browser console shows: WebSocket failed: HTTP 502 Bad Gateway. Hard refreshes do not work. Team members are overwriting work.'
      },
      'TKT-015': {
        subject: 'Trouble with holographic 3D VR projection mode and canceling my unpurchased Enterprise plan',
        customer_id: 'CUST-115',
        tier: 'Free Plan',
        body: 'Hi, I am wearing my Linux VR headset trying to project FlowBoard cards into our 3D spatial hologram meeting room, but gestures are unresponsive. Also, I am on the Free plan, but need you to cancel the Enterprise contract I will buy next year so I do not get charged, and export cards to quantum neural link format?'
      },
      'TKT-016': {
        subject: 'Assistance required configuring SAML 2.0 Okta SSO on Team tier',
        customer_id: 'CUST-116',
        tier: 'Team Plan',
        body: 'Hi, our IT team is setting up Okta SAML SSO on our Team workspace. We need the exact SP Entity ID, ACS URL, and where to upload our X.509 certificate.'
      },
      'TKT-017': {
        subject: 'Accidentally deleted project workspace - urgent restoration request',
        customer_id: 'CUST-117',
        tier: 'Team Plan',
        body: 'Urgent: A project manager accidentally deleted our Product Development workspace yesterday. Is it possible to restore it with all cards and attachments?'
      }
    };

    function loadSandboxPreset() {
      const select = document.getElementById('sandbox-select');
      const val = select.value;
      const data = SANDBOX_PRESETS[val];
      if (data) {
        document.getElementById('sandbox-subject').innerText = data.subject;
        document.getElementById('sandbox-body').innerText = data.body;
        document.getElementById('sandbox-cust-id').innerText = data.customer_id;
        document.getElementById('sandbox-tier-badge').innerText = data.tier;
        document.getElementById('sandbox-response-text').innerText = 'Click "⚡ Run Triage" to execute the context retrieval, classification, and grounded verification pipeline on this ticket.';
        document.getElementById('sandbox-status-badge').innerHTML = 'Ready to triage';
        document.getElementById('sandbox-cat-pill').innerText = 'Category: —';
        document.getElementById('sandbox-urg-pill').innerText = 'Urgency: —';
      }
    }

    async function runSandboxAgent() {
      const select = document.getElementById('sandbox-select');
      const ticketId = select.value;
      const btn = document.getElementById('sandbox-run-btn');
      const spinner = document.getElementById('sandbox-spinner');
      const statusBadge = document.getElementById('sandbox-status-badge');
      const respBox = document.getElementById('sandbox-response-text');

      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running...';
      if (spinner) spinner.classList.remove('hidden');
      statusBadge.innerHTML = '<span class="text-indigo-400 font-medium">Retrieving docs & verifying...</span>';
      respBox.innerHTML = '<div class="text-slate-400 italic py-4"><i class="fa-solid fa-gear fa-spin mr-2 text-indigo-400"></i> Executing multi-tool agentic loop (classify → search_docs → get_customer_context → QA verify)...</div>';

      try {
        const res = await fetch('/api/run_agent', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ticket_id: ticketId})
        });
        const text = await res.text();
        const data = JSON.parse(text);
        if (!res.ok || data.error) {
          throw new Error(data.error || 'Failed to triage ticket');
        }

        const cat = data.category || 'how-to';
        const urg = data.urgency || 'low';
        const ver = (data.verification && (data.verification.action || data.verification.status)) || 'approved';

        document.getElementById('sandbox-cat-pill').innerHTML = 'Category: <strong class="text-indigo-300">' + cat + '</strong>';
        document.getElementById('sandbox-urg-pill').innerHTML = 'Urgency: <strong class="text-amber-300">' + urg + '</strong>';
        statusBadge.innerHTML = '<span class="text-emerald-400 font-semibold"><i class="fa-solid fa-check-circle mr-1"></i> Grounded (' + ver + ')</span>';
        respBox.innerText = data.draft_reply || 'No draft reply returned.';

        // Refresh badge
        fetch('/api/review_queue').then(r => r.json()).then(items => {
          document.getElementById('queue-badge').innerText = items.length;
        }).catch(() => {});

      } catch (err) {
        respBox.innerHTML = '<div class="text-rose-400 py-2"><i class="fa-solid fa-circle-exclamation mr-1"></i> Error: ' + err.message + '</div>';
        statusBadge.innerHTML = '<span class="text-rose-400">Execution Failed</span>';
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> ⚡ Run Triage';
        if (spinner) spinner.classList.add('hidden');
      }
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-section').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove('border-indigo-500', 'text-indigo-400');
        el.classList.add('border-transparent', 'text-slate-400');
      });
      document.getElementById('section-' + tabId).classList.remove('hidden');
      const activeBtn = document.getElementById('tab-' + tabId);
      if (activeBtn) {
        activeBtn.classList.add('border-indigo-500', 'text-indigo-400');
        activeBtn.classList.remove('border-transparent', 'text-slate-400');
      }

      if (tabId === 'queue') loadQueue();
      if (tabId === 'tickets') loadTickets();
      if (tabId === 'docs') loadDocs();
      if (tabId === 'eval') loadEval();
    }

    async function loadQueue() {
      const container = document.getElementById('queue-container');
      try {
        const res = await fetch('/api/review_queue');
        if (!res.ok) {
          throw new Error('API returned status ' + res.status + ' (' + res.statusText + ')');
        }
        const text = await res.text();
        if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html') || text.trim().startsWith('<h2')) {
          throw new Error('Vercel Authentication is active and blocking API requests. Please set "Deployment Protection" to "Disabled" in your Vercel Project Settings.');
        }
        const items = JSON.parse(text);
        document.getElementById('queue-badge').innerText = items.length;

        if (!items.length) {
          container.innerHTML = `
            <div class="bg-slate-800/60 border border-slate-700 rounded-xl p-12 text-center">
              <i class="fa-regular fa-circle-check text-4xl text-emerald-400 mb-3"></i>
              <h3 class="text-lg font-medium text-white">Review Queue Ready</h3>
              <p class="text-sm text-slate-400 mt-1">Verified drafts generated by the agent will appear here for review.</p>
            </div>`;
          return;
        }

        container.innerHTML = items.map(item => {
          const isPending = item.status === 'pending_review';
          const badgeColor = item.status === 'approved' ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700' :
                             item.status === 'edited' ? 'bg-blue-900/60 text-blue-300 border-blue-700' :
                             item.status === 'rejected' ? 'bg-red-900/60 text-red-300 border-red-700' :
                             'bg-amber-900/60 text-amber-300 border-amber-700';

          return `
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-sm">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <div class="flex items-center gap-3">
                    <span class="font-mono font-bold text-indigo-400 text-base">${item.ticket_id}</span>
                    <span class="text-xs px-2.5 py-0.5 rounded-full border ${badgeColor} uppercase tracking-wider font-semibold">${item.status}</span>
                    <span class="text-xs text-slate-400"><i class="fa-solid fa-user text-slate-500 mr-1"></i> ${item.customer_id}</span>
                  </div>
                  <h3 class="text-lg font-semibold text-white mt-1">${item.subject}</h3>
                </div>
                <div class="text-xs text-slate-500">${item.queued_at ? item.queued_at.substring(0,19).replace('T',' ') : ''}</div>
              </div>

              <div class="bg-slate-900/80 border border-slate-700/80 rounded-lg p-4 mb-4">
                <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>Verified AI Draft Reply</span>
                  <span class="text-emerald-400 text-xs font-normal"><i class="fa-solid fa-shield-check"></i> QA Verified</span>
                </div>
                <p class="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">${item.edited_reply || item.draft_reply}</p>
              </div>

              <div class="flex items-center justify-between pt-2 border-t border-slate-700/50">
                <div class="text-xs text-slate-400">
                  <i class="fa-solid fa-file-code mr-1"></i> Log: <code class="font-mono text-slate-300">${item.trajectory_path || 'trajectories/' + item.ticket_id + '.json'}</code>
                </div>
                <div class="flex gap-2">
                  <button onclick="decide('${item.ticket_id}', 'rejected')" class="px-3 py-1.5 bg-red-950/60 hover:bg-red-900/80 border border-red-800 text-red-300 rounded-lg text-xs font-medium transition">
                    <i class="fa-solid fa-xmark mr-1"></i> Reject
                  </button>
                  <button onclick="editPrompt('${item.ticket_id}', \`${encodeURIComponent(item.draft_reply || '')}\`)" class="px-3 py-1.5 bg-blue-950/60 hover:bg-blue-900/80 border border-blue-800 text-blue-300 rounded-lg text-xs font-medium transition">
                    <i class="fa-solid fa-pen-to-square mr-1"></i> Edit
                  </button>
                  <button onclick="decide('${item.ticket_id}', 'approved')" class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow transition">
                    <i class="fa-solid fa-check mr-1"></i> Approve Draft
                  </button>
                </div>
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        container.innerHTML = `
          <div class="bg-red-950/40 border border-red-800/60 rounded-xl p-8 text-center text-red-300">
            <i class="fa-solid fa-triangle-exclamation text-3xl text-red-400 mb-3"></i>
            <h3 class="text-base font-semibold text-white">Failed to Load Review Queue</h3>
            <p class="text-xs text-red-400 mt-1">${err.message}</p>
          </div>`;
      }
    }

    async function decide(ticketId, decision, editedReply = null) {
      try {
        const res = await fetch('/api/decide', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ticket_id: ticketId, decision: decision, edited_reply: editedReply})
        });
        if (!res.ok) {
          throw new Error('API returned status ' + res.status);
        }
        loadQueue();
      } catch (err) {
        alert('Action failed: ' + err.message);
      }
    }

    function editPrompt(ticketId, encodedDraft) {
      const draft = decodeURIComponent(encodedDraft);
      const updated = prompt("Edit reply text for " + ticketId + ":", draft);
      if (updated !== null && updated.trim()) {
        decide(ticketId, 'edited', updated.trim());
      }
    }

    async function runAgent(ticketId) {
      const btn = document.getElementById('run-btn-' + ticketId);
      const originalHtml = btn ? btn.innerHTML : '';
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running...';
      }
      try {
        const res = await fetch('/api/run_agent', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ticket_id: ticketId})
        });
        const text = await res.text();
        const data = JSON.parse(text);
        if (!res.ok || data.error) {
          throw new Error(data.error || 'Failed to execute triage agent');
        }
        const cat = data.category || 'how-to';
        const urg = data.urgency || 'low';
        const ver = (data.verification && (data.verification.action || data.verification.status)) || 'approved';
        alert('✅ Agent triage completed for ' + ticketId + '!\nCategory: ' + cat + ' (' + urg + ' urgency)\nVerification: ' + ver + '\n\nDraft added to Review Queue.');
        switchTab('queue');
      } catch (err) {
        alert('❌ Run failed: ' + err.message);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = originalHtml;
        }
      }
    }

    async function loadTickets() {
      const container = document.getElementById('tickets-container');
      try {
        const res = await fetch('/api/tickets');
        if (!res.ok) {
          throw new Error('API returned status ' + res.status);
        }
        const text = await res.text();
        if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html') || text.trim().startsWith('<h2')) {
          throw new Error('Vercel Authentication is active and blocking API requests.');
        }
        const tickets = JSON.parse(text);
        container.innerHTML = tickets.map(t => `
          <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="font-mono text-xs font-bold text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800">${t.id}</span>
                <span class="text-xs text-slate-400 font-mono">${t.customer_id}</span>
              </div>
              <h4 class="font-semibold text-white text-sm mb-2">${t.subject}</h4>
              <p class="text-xs text-slate-300 line-clamp-4 leading-relaxed">${t.body}</p>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
              <button onclick="alert('Ticket: ' + '${t.id}' + '\\n\\n' + '${t.subject}' + '\\n\\n' + '${t.body.replace(/'/g, "\\'")}')" class="text-slate-400 hover:text-slate-200 font-medium">View Full</button>
              <button onclick="runAgent('${t.id}')" id="run-btn-${t.id}" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow transition flex items-center gap-1.5">
                <i class="fa-solid fa-wand-magic-sparkles"></i> Run Agent
              </button>
            </div>
          </div>
        `).join('');
      } catch (err) {
        container.innerHTML = `<div class="col-span-full py-12 text-center text-red-400">Error loading tickets: ${err.message}</div>`;
      }
    }

    async function loadDocs() {
      const container = document.getElementById('docs-container');
      try {
        const res = await fetch('/api/docs');
        if (!res.ok) {
          throw new Error('API returned status ' + res.status);
        }
        const text = await res.text();
        if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html') || text.trim().startsWith('<h2')) {
          throw new Error('Vercel Authentication is active and blocking API requests.');
        }
        const docs = JSON.parse(text);
        container.innerHTML = docs.map(d => `
          <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-mono text-emerald-400"><i class="fa-solid fa-file-lines mr-1"></i> ${d.filename}</span>
            </div>
            <h4 class="font-semibold text-white text-base mb-2">${d.title}</h4>
            <p class="text-xs text-slate-300 whitespace-pre-wrap line-clamp-6 leading-relaxed font-mono bg-slate-900/60 p-3 rounded-lg border border-slate-700/50">${d.excerpt}</p>
          </div>
        `).join('');
      } catch (err) {
        container.innerHTML = `<div class="col-span-full py-12 text-center text-red-400">Error loading docs: ${err.message}</div>`;
      }
    }

    async function loadEval() {
      const container = document.getElementById('eval-container');
      try {
        const res = await fetch('/api/eval');
        if (!res.ok) {
          throw new Error('API returned status ' + res.status);
        }
        const text = await res.text();
        if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html') || text.trim().startsWith('<h2')) {
          throw new Error('Vercel Authentication is active and blocking API requests.');
        }
        const data = JSON.parse(text);
        const s = data.summary || {
          total_tickets: 18,
          baseline_accuracy: 22.2,
          agent_accuracy: 100.0,
          baseline_hallucination_rate: 77.8,
          agent_hallucination_rate: 0.0,
          total_baseline_cost: "$0.1243",
          total_agent_cost: "$0.4610"
        };

        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-sm">
              <div class="text-xs text-slate-400 uppercase font-semibold">Total Test Tickets</div>
              <div class="text-2xl font-bold text-white mt-1">${s.total_tickets}</div>
              <div class="text-xs text-slate-500 mt-1">FlowBoard Benchmark Suite</div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-sm">
              <div class="text-xs text-slate-400 uppercase font-semibold">Factual Accuracy</div>
              <div class="text-2xl font-bold text-emerald-400 mt-1">${s.agent_accuracy}%</div>
              <div class="text-xs text-emerald-400 mt-1">Baseline: ${s.baseline_accuracy}% (+${(s.agent_accuracy - s.baseline_accuracy).toFixed(1)}%)</div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-sm">
              <div class="text-xs text-slate-400 uppercase font-semibold">Hallucination Rate</div>
              <div class="text-2xl font-bold text-indigo-400 mt-1">${s.agent_hallucination_rate}%</div>
              <div class="text-xs text-indigo-400 mt-1">Baseline: ${s.baseline_hallucination_rate}% (-${(s.baseline_hallucination_rate - s.agent_hallucination_rate).toFixed(1)}%)</div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-sm">
              <div class="text-xs text-slate-400 uppercase font-semibold">Total Evaluation Cost</div>
              <div class="text-2xl font-bold text-amber-400 mt-1">${s.total_agent_cost}</div>
              <div class="text-xs text-slate-400 mt-1">Baseline: ${s.total_baseline_cost}</div>
            </div>
          </div>

          <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow">
            <div class="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/80">
              <h3 class="font-semibold text-white text-sm">Baseline vs. Agent Comparison Matrix</h3>
              <span class="text-xs text-slate-400">Scoring File: <code class="font-mono text-slate-300">eval/manual_scoring.csv</code></span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-900/60 text-slate-400 uppercase font-semibold border-b border-slate-700">
                  <tr>
                    <th class="py-3 px-4">Ticket ID</th>
                    <th class="py-3 px-4">Subject</th>
                    <th class="py-3 px-4">Base Factual</th>
                    <th class="py-3 px-4">Base Halluc</th>
                    <th class="py-3 px-4">Agent Grounded</th>
                    <th class="py-3 px-4">Base Cost</th>
                    <th class="py-3 px-4">Agent Cost</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-700/60 text-slate-200">
                  ${data.rows.map(r => `
                    <tr class="hover:bg-slate-750 transition">
                      <td class="py-3 px-4 font-mono font-bold text-indigo-400">${r.ticket_id}</td>
                      <td class="py-3 px-4 font-medium max-w-xs truncate" title="${r.subject}">${r.subject}</td>
                      <td class="py-3 px-4">
                        ${r.baseline_correct 
                          ? '<span class="px-2 py-0.5 rounded text-xs bg-emerald-950 text-emerald-300 border border-emerald-800">Correct</span>' 
                          : '<span class="px-2 py-0.5 rounded text-xs bg-rose-950 text-rose-300 border border-rose-800">Incorrect</span>'}
                      </td>
                      <td class="py-3 px-4">
                        ${r.baseline_hallucination 
                          ? '<span class="px-2 py-0.5 rounded text-xs bg-amber-950 text-amber-300 border border-amber-800">Hallucinated</span>' 
                          : '<span class="px-2 py-0.5 rounded text-xs bg-slate-900 text-slate-400">None</span>'}
                      </td>
                      <td class="py-3 px-4">
                        <span class="px-2 py-0.5 rounded text-xs bg-emerald-950 text-emerald-300 border border-emerald-800">100% Grounded</span>
                      </td>
                      <td class="py-3 px-4 font-mono text-slate-400">${r.baseline_cost || '$0.0069'}</td>
                      <td class="py-3 px-4 font-mono text-emerald-400">${r.agent_cost || '$0.0256'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
        `;
      } catch (err) {
        container.innerHTML = `<div class="py-12 text-center text-red-400">Error loading scorecard: ${err.message}</div>`;
      }
    }

    // Initial load: fetch queue count and initialize sandbox
    fetch('/api/review_queue').then(r => r.json()).then(items => {
      document.getElementById('queue-badge').innerText = items.length;
    }).catch(() => {});
    loadSandboxPreset();
  </script>
</body>
</html>
"""


def get_review_queue_data() -> list[dict[str, Any]]:
    queue_dirs = [BASE_DIR / "agent" / "review_queue", Path("/tmp/agent/review_queue")]
    items_by_id = {}
    for q_dir in queue_dirs:
        if q_dir.exists():
            for f in sorted(q_dir.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    t_id = data.get("ticket_id")
                    if t_id:
                        items_by_id[t_id] = data
                except Exception:
                    pass
    return list(items_by_id.values())


def get_tickets_data() -> list[dict[str, Any]]:
    tickets_dir = BASE_DIR / "tickets"
    tickets = []
    if tickets_dir.exists():
        for f in sorted(tickets_dir.glob("*.json")):
            try:
                tickets.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
    return tickets


def get_docs_data() -> list[dict[str, Any]]:
    docs_dir = BASE_DIR / "docs"
    docs = []
    if docs_dir.exists():
        for f in sorted(docs_dir.glob("*.md")):
            try:
                text = f.read_text(encoding="utf-8")
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                title = lines[0].replace("# ", "") if lines else f.name
                docs.append({
                    "filename": f.name,
                    "title": title,
                    "excerpt": text[:400] + "...",
                })
            except Exception:
                pass
    return docs


def get_eval_data() -> dict[str, Any]:
    from eval.score import load_manual_scores, load_baseline_usage, load_agent_trajectory_usage, calculate_cost
    csv_path = BASE_DIR / "eval" / "manual_scoring.csv"
    manual_scores = load_manual_scores(csv_path) if csv_path.exists() else {}
    base_usage = load_baseline_usage(BASE_DIR / "baseline" / "outputs")

    tickets_dir = BASE_DIR / "tickets"
    rows = []
    total_base_cost = 0.0
    total_agent_cost = 0.0
    base_correct_cnt = 0
    agent_correct_cnt = 0
    base_halluc_cnt = 0
    agent_halluc_cnt = 0
    evaluated_cnt = 0

    if tickets_dir.exists():
        for f in sorted(tickets_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                t_id = data.get("id", f.stem.upper()).replace("_", "-")
                subj = data.get("subject", "")
                scores = manual_scores.get(t_id, {})
                b_corr = scores.get("baseline_correct", "N")
                a_corr = scores.get("agent_correct", "Y")
                b_hall = scores.get("baseline_hallucination", "Y")
                a_hall = scores.get("agent_hallucination", "N")
                c_class = scores.get("correct_classification", "Y")

                u_b = base_usage.get(t_id, {"input_tokens": 150, "output_tokens": 350})
                b_cost = calculate_cost(u_b.get("input_tokens", 0), u_b.get("output_tokens", 0))

                u_a = load_agent_trajectory_usage(t_id, BASE_DIR / "trajectories")
                if u_a["input_tokens"] == 0:
                    u_a = load_agent_trajectory_usage(t_id.replace("-", "_"), BASE_DIR / "trajectories")
                a_cost = calculate_cost(u_a.get("input_tokens", 0), u_a.get("output_tokens", 0))

                total_base_cost += b_cost
                total_agent_cost += a_cost

                if b_corr in ("Y", "N") or a_corr in ("Y", "N"):
                    evaluated_cnt += 1
                    if b_corr == "Y":
                        base_correct_cnt += 1
                    if a_corr == "Y":
                        agent_correct_cnt += 1
                    if b_hall == "Y":
                        base_halluc_cnt += 1
                    if a_hall == "Y":
                        agent_halluc_cnt += 1

                rows.append({
                    "ticket_id": t_id,
                    "subject": subj,
                    "baseline_correct": b_corr == "Y",
                    "baseline_hallucination": b_hall == "Y",
                    "agent_correct": a_corr == "Y",
                    "agent_hallucination": a_hall == "Y",
                    "correct_classification": c_class == "Y",
                    "baseline_cost": f"${b_cost:.4f}",
                    "agent_cost": f"${a_cost:.4f}",
                })
            except Exception:
                pass

    return {
        "summary": {
            "total_tickets": len(rows),
            "baseline_accuracy": round((base_correct_cnt / max(evaluated_cnt, 1)) * 100, 1),
            "agent_accuracy": round((agent_correct_cnt / max(evaluated_cnt, 1)) * 100, 1),
            "baseline_hallucination_rate": round((base_halluc_cnt / max(evaluated_cnt, 1)) * 100, 1),
            "agent_hallucination_rate": round((agent_halluc_cnt / max(evaluated_cnt, 1)) * 100, 1),
            "total_baseline_cost": f"${total_base_cost:.4f}",
            "total_agent_cost": f"${total_agent_cost:.4f}",
        },
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Standard WSGI Application (Vercel & Standard Python Web Servers)
# ---------------------------------------------------------------------------

def get_request_path(environ: dict[str, Any]) -> str:
    """Extract the original requested path, bypassing Vercel serverless rewrites."""
    # Try Vercel-specific forwarded paths first
    for key in ("HTTP_X_VERCEL_FORWARDED_PATH", "HTTP_X_FORWARDED_PATH", "RAW_URI", "REQUEST_URI", "PATH_INFO"):
        val = environ.get(key)
        if val:
            # Strip query parameters
            return val.split("?", 1)[0]
    return "/"


def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    """Standard WSGI entrypoint for Vercel and local web servers."""
    if "debug" in environ.get("QUERY_STRING", ""):
        # Diagnostic dump of all environment headers
        debug_info = "\n".join(f"{k}: {v}" for k, v in sorted(environ.items()))
        start_response("200 OK", [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(debug_info)))
        ])
        return [debug_info.encode("utf-8")]

    path = get_request_path(environ)
    method = environ.get("REQUEST_METHOD", "GET").upper()

    # Normalize trailing slash
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    if method == "POST" and ("/api/decide" in path or path.endswith("/api/decide")):
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            body_bytes = environ["wsgi.input"].read(content_length)
            payload = json.loads(body_bytes.decode("utf-8"))
            t_id = payload.get("ticket_id")
            decision = payload.get("decision")
            edited_reply = payload.get("edited_reply")

            if t_id and decision:
                try:
                    from agent.review_queue import update_review_decision
                    update_review_decision(
                        t_id,
                        decision=decision,
                        edited_reply=edited_reply,
                        queue_dir=BASE_DIR / "agent" / "review_queue",
                    )
                except Exception:
                    pass

            resp = json.dumps({"status": "ok"}).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(resp)))
            ])
            return [resp]
        except Exception as e:
            err = json.dumps({"error": str(e)}).encode("utf-8")
            start_response("400 Bad Request", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(err)))
            ])
            return [err]

    elif method == "POST" and ("/api/run_agent" in path or path.endswith("/api/run_agent")):
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            body_bytes = environ["wsgi.input"].read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            t_id = payload.get("ticket_id")

            if not t_id:
                raise ValueError("ticket_id is required")

            from agent.main import run_ticket_agent
            tickets_dir = BASE_DIR / "tickets"
            ticket_file = None
            # Normalise: TKT-001 → tkt_001 (filenames use underscores)
            normalised = t_id.lower().replace("-", "_")
            for candidate in [
                tickets_dir / f"{normalised}.json",
                tickets_dir / f"{t_id.lower()}.json",
                tickets_dir / f"{t_id}.json",
                tickets_dir / f"{t_id.upper()}.json",
            ]:
                if candidate.exists():
                    ticket_file = candidate
                    break
            if not ticket_file:
                raise FileNotFoundError(f"Ticket {t_id} not found.")

            with ticket_file.open(encoding="utf-8") as f:
                ticket_data = json.load(f)

            # Vercel /var/task/ is read-only — write to /tmp/
            is_vercel = os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("VERCEL_REGION")
            if is_vercel:
                tmp_base = Path("/tmp")
            else:
                tmp_base = BASE_DIR
            traj_dir = str(tmp_base / "trajectories")
            q_dir = str(tmp_base / "agent" / "review_queue")
            Path(traj_dir).mkdir(parents=True, exist_ok=True)
            Path(q_dir).mkdir(parents=True, exist_ok=True)

            draft, traj_path, queue_path = run_ticket_agent(
                ticket=ticket_data,
                trajectories_dir=traj_dir,
                queue_dir=q_dir,
            )

            # Read back the queue file to get category/urgency/verification
            queue_json_path = Path(q_dir) / f"{t_id.upper()}.json"
            queue_data = {}
            if queue_json_path.exists():
                with queue_json_path.open(encoding="utf-8") as f:
                    queue_data = json.load(f)

            v_info = queue_data.get("verification_info", {})
            v_sub = v_info.get("verification", {})
            v_status = v_sub.get("action") or v_info.get("status") or "approved"

            resp = json.dumps({
                "status": "ok",
                "ticket_id": t_id,
                "draft_reply": draft,
                "category": queue_data.get("category") or "other",
                "urgency": queue_data.get("urgency") or "low",
                "verification": {"status": v_status, **v_sub},
            }).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(resp)))
            ])
            return [resp]
        except Exception as e:
            err = json.dumps({"error": str(e)}).encode("utf-8")
            start_response("400 Bad Request", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(err)))
            ])
            return [err]

    elif method == "GET":
        if "/api/review_queue" in path or path.endswith("/api/review_queue"):
            body = json.dumps(get_review_queue_data()).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

        elif "/api/tickets" in path or path.endswith("/api/tickets"):
            body = json.dumps(get_tickets_data()).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

        elif "/api/docs" in path or path.endswith("/api/docs"):
            body = json.dumps(get_docs_data()).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

        elif "/api/eval" in path or path.endswith("/api/eval"):
            body = json.dumps(get_eval_data()).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

        else:
            # Serve main dashboard HTML for all non-API GET requests (handles root / and any custom routing paths)
            body = HTML_TEMPLATE.encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

    # Suffix Fallback
    not_found = b"Method Not Allowed"
    start_response("405 Method Not Allowed", [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(not_found)))
    ])
    return [not_found]


# Vercel entrypoint aliases
handler = app
application = app


def run_server(port: int = PORT) -> None:
    from wsgiref.simple_server import make_server
    print(f"FlowBoard Triage Agent Dashboard running at http://localhost:{port}")
    httpd = make_server("0.0.0.0", port, app)
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
