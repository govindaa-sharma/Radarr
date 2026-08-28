# 📡 Radarr
### *Always scanning. Never missing a move.*

Radarr is an autonomous multi-agent competitive intelligence system. It monitors competitor websites 24/7, detects changes using a diff-based memory system, extracts structured intelligence using Gemini AI, and delivers a clean morning brief — completely automatically, with zero human intervention.

> Built as a final year CSE project demonstrating multi-agent AI systems, RAG, LLM orchestration, and production-grade Python engineering.

---

## 🎯 What it does

Every morning, Radarr delivers a brief like this — automatically, while you sleep:

```
RADARR — DAILY INTELLIGENCE BRIEF
=====================================

TOP SIGNAL TODAY:
Razorpay launches Agentic Payments with NPCI and Claude, integrating AI
across payment, banking, and payroll platforms.

KEY DEVELOPMENTS:
1. Cashfree — Aggressive 1.6% gateway fee — Direct pricing attack on competitors
2. Stripe — Machine Payments Protocol — Positions them ahead in agentic commerce
3. Razorpay — RazorpayX expansion — Moving upmarket with full-stack finance

WATCH OUT FOR:
Cashfree's promotional pricing may not be sustainable — watch for a reversal.

RECOMMENDED PRIORITY ACTION:
Review your pricing strategy immediately given Cashfree's aggressive move.
=====================================
```

You can also ask it anything:

> *"What is Stripe doing in AI?"*
> *"Has Razorpay changed pricing recently?"*
> *"Which competitor is hiring the most?"*
> *"What should I be most worried about competitively?"*

And it answers from its own intelligence database — grounded, cited, not hallucinated.

---

## 🏗️ Architecture

```
Data Sources (Twitter, LinkedIn, Product pages, Job boards, Blogs)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                    CRAWLER AGENT                        │
│         Playwright + httpx  │  Llama 3.1:8b            │
│    Scrapes URLs, cleans text, handles JS-rendered pages │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Diff Engine  │  ← PostgreSQL memory
              │  (difflib)    │    Only passes CHANGES
              └───────┬───────┘    downstream
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   ANALYST AGENT                         │
│                  Gemini 2.5 Flash                       │
│   Extracts: event_type, importance, headline, detail,   │
│   recommended_action — as structured JSON               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 SUMMARIZER AGENT                        │
│                  Llama 3.1:8b (local)                   │
│        Writes the daily brief — free, private           │
└─────────────────────┬───────────────────────────────────┘
                      │
              ┌───────┴────────┐
              ▼                ▼
         Slack brief     Streamlit dashboard
         (webhook)       + RAG chat interface
```

**Why three separate agents?**
Each agent has exactly one responsibility. The crawler doesn't analyse, the analyst doesn't summarise. This makes each component independently testable, replaceable, and scalable.

**Why different models per agent?**
- Crawler/Summarizer → Llama 3.1:8b (local, free, fast — task doesn't need a frontier model)
- Analyst → Gemini 2.5 Flash (hard reasoning task — structured extraction from noisy text requires a strong model)

---

## 💡 Key engineering decisions

**Diff-based memory (biggest cost saver)**
Every scraped page is compared against its last snapshot in PostgreSQL. Only genuine changes trigger the Analyst agent. In a typical run, 70-80% of URLs show no change and are skipped entirely — zero API calls, zero cost for those pages.

**Hybrid scraping**
httpx first (fast, lightweight), Playwright fallback (full headless Chromium for JavaScript-rendered pages). Automatic fallback — the system handles both static and dynamic pages transparently.

**Two memory systems working together**
- PostgreSQL — structured, queryable, stores every snapshot and analysis with timestamps
- Qdrant vector store — semantic search over all historical analyses, powers the RAG chat interface

**LangGraph for orchestration**
The pipeline is an explicit state graph: `setup → crawl → summarize → END`. Each node receives state, enriches it, passes it on. Conditional edges route to END on any error — no cascading failures.

---

## 🛠️ Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| Agent orchestration | LangGraph | Explicit state graph, better than LangChain for stateful multi-agent flows |
| Local LLM | Ollama + Llama 3.1:8b | Runs on 16GB RAM, free, private |
| Analyst LLM | Gemini 2.5 Flash | Free tier (250 req/day), strong structured extraction |
| Scraping | httpx + Playwright | Fast path + JS fallback |
| Text diffing | difflib (stdlib) | No dependencies, similarity scoring + line-level diff |
| Structured memory | PostgreSQL | Snapshot history, analysis history, time-series queries |
| Vector memory | Qdrant | Self-hosted semantic search, powers RAG chat |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | 384-dim, fast, runs locally |
| Scheduler | Celery + Redis | Nightly 7am IST cron job |
| Frontend | Streamlit | Python-native, perfect for data-heavy dashboards |
| Charts | Plotly | Timeline, pie, heatmap |
| Delivery | Slack webhooks | Morning brief in your team channel |

---

## 📁 Project structure

```
radarr/
├── agents/
│   ├── crawler.py          # Orchestrates scraping + feeds analyst
│   ├── analyst.py          # Gemini extracts structured intelligence
│   └── summarizer.py       # Llama writes the daily brief
├── tools/
│   ├── scraper.py          # httpx + Playwright with auto-fallback
│   ├── diffing.py          # Change detection + diff formatting
│   └── delivery.py         # Slack webhook delivery
├── memory/
│   ├── postgres.py         # Snapshots + analyses persistence
│   └── vector_store.py     # Qdrant semantic search + RAG
├── pipeline/
│   ├── graph.py            # LangGraph: wires everything together
│   └── scheduler.py        # Celery nightly schedule
├── dashboard/
│   └── app.py              # Streamlit: charts + RAG chat interface
├── config/
│   ├── llm.py              # LLM factory (Ollama / Gemini)
│   └── competitors.yaml    # Which competitors + URLs to track
├── .env                    # API keys (never commit)
└── docker-compose.yml      # Postgres, Redis, Qdrant
```

---

## 🚀 Getting started

### Prerequisites
- Windows with WSL2 Ubuntu (or Linux/Mac)
- Docker Desktop
- Miniconda
- 16GB RAM recommended

### 1. Clone and set up environment

```bash
git clone https://github.com/yourusername/radarr.git
cd radarr

conda create -n radarr python=3.11
conda activate radarr

pip install -r requirements.txt
playwright install chromium
```

(Or skip local setup entirely and run `docker compose up --build` — see
below.)

### 2. Install and start Ollama

```bash
# In WSL2 Ubuntu terminal
curl -fsSL https://ollama.com/install.sh | sh
OLLAMA_HOST=0.0.0.0 ollama serve   # keep this running

# In a new terminal
ollama pull llama3.1:8b
```

### 3. Start infrastructure

```bash
docker compose up -d
```

### 4. Configure environment

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

```env
GEMINI_API_KEY=your_key_from_aistudio.google.com
OLLAMA_BASE_URL=http://localhost:11434
POSTGRES_URL=postgresql://admin:password@127.0.0.1:5433/intel_db
REDIS_URL=redis://127.0.0.1:6379
QDRANT_URL=http://127.0.0.1:6333
SLACK_WEBHOOK_URL=your_slack_webhook_here
POSTGRES_PASSWORD=change_me_locally   # used by docker-compose.yml
LOGFIRE_TOKEN=                        # optional — blank is fine locally
USE_HOSTED_LLM=false                  # true only in deployed environments, see DEPLOYMENT.md
```

Get your free Gemini API key at [aistudio.google.com](https://aistudio.google.com) — no credit card needed.

### 5. Configure competitors

Edit `config/competitors.yaml` to track the competitors relevant to you:

```yaml
competitors:
  - name: Stripe
    urls:
      - url: https://stripe.com/pricing
        type: pricing
      - url: https://stripe.com/blog
        type: blog
      - url: https://stripe.com/jobs
        type: hiring
```

### 6. Run the pipeline

```bash
python -c "import asyncio; from pipeline.graph import run_pipeline; asyncio.run(run_pipeline())"
```

### 7. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

---

## 📊 Dashboard features

- **Signal timeline** — bar chart showing signals per competitor per day
- **Event type breakdown** — pie chart of PRICING_CHANGE vs PRODUCT_UPDATE vs HIRING_SURGE
- **Signals table** — sortable, with importance progress bars and full summaries
- **Morning brief generator** — one click, Llama writes the full brief locally
- **Importance heatmap** — which competitor is most active in which category
- **RAG chat interface** — ask anything, get grounded answers with source citations

---

## 💬 Example chat queries

```
"What is Stripe doing in AI?"
"Has Razorpay changed their pricing recently?"
"Which competitor is hiring the most right now?"
"What should I be most worried about competitively?"
"What new products has Cashfree launched?"
"Compare Stripe and Razorpay's recent moves"
```

Each answer is grounded in your actual intelligence database with source citations shown.

---

## 💰 Cost breakdown

| Component | Cost |
|-----------|------|
| Ollama (Llama 3.1:8b) | Free — runs locally |
| Gemini 2.5 Flash | Free tier — 250 req/day |
| PostgreSQL | Free — Docker, local |
| Qdrant | Free — self-hosted |
| Redis | Free — Docker, local |
| Playwright | Free — open source |
| **Total monthly (dev)** | **~₹0** |

The diff-based memory system ensures Gemini is only called for genuine content changes — typically 2-3 API calls per pipeline run on a stable competitor set.

---

## 🛡️ Guardrails

Scraped webpage text is untrusted input — it flows straight into an LLM
prompt with no human review, and the RAG chat's retrieved context traces
back to the same source. That's a real indirect prompt-injection surface
(OWASP LLM01), not a hypothetical one, so Radarr defends it at two layers:

- **Structured output as a contract** (`agents/analyst.py`) — the Analyst
  agent's output is constrained by a Pydantic schema (`CompetitiveSignal`):
  a closed enum for `event_type`, a `1–5` range for `importance`, and
  length-capped strings. Malformed or out-of-contract output is rejected
  before it ever reaches Postgres/Qdrant, with one retry before giving up
  cleanly — no more regex-scraping a JSON blob out of free text and hoping.
- **Explicit data/instruction boundary** (`tools/guardrails.py`) — every
  place untrusted text enters a prompt (scraped diffs in the Analyst, and
  retrieved summaries in the RAG chat) is wrapped in `<scraped_content>` /
  `<intelligence_context>` tags, with an explicit system instruction that
  content inside those tags is data, never commands. A lightweight
  heuristic scan flags instruction-like patterns ("ignore previous
  instructions", "you are now...") for an audit trail.
- Verified with two adversarial test cases in the eval harness below —
  not just described, actually measured against a live LLM call.

## 📏 Evaluation

`evals/` holds two hand-labeled eval suites so extraction quality and RAG
answer quality are measured, not assumed — see `evals/README.md` for full
details. Both support a `--mock` offline mode (deterministic stub
predictions, no API calls) for quick plumbing checks and CI, plus a live
mode that calls the real agents.

- **`evals/run_analyst_eval.py`** — 12 hand-labeled examples
  (`evals/golden_analyst_dataset.py`), including one prompt-injection
  attempt, scored on event-type accuracy, importance MAE, and whether the
  injection attempt was resisted. Runs in the main environment, no extra
  install needed.
- **`evals/run_rag_eval.py`** — RAGAS-based eval (faithfulness, answer
  relevancy, context precision) against a 5-question golden set
  (`evals/golden_rag_dataset.py`), using seeded context rather than a live
  Qdrant query so it isolates *generation* quality from *retrieval*
  quality. **Needs a separate venv** — `ragas==0.1.21` pins
  `langchain-core<0.3`, which conflicts with this project's
  `langgraph`/`langchain-core>=1.4`. See `evals/requirements-eval.txt`.

```bash
# Analyst eval — main venv
python -m evals.run_analyst_eval --mock   # offline plumbing check
python -m evals.run_analyst_eval          # live, needs GEMINI_API_KEY

# RAG eval — separate venv (see evals/README.md)
python -m venv .venv-evals && source .venv-evals/bin/activate
pip install -r evals/requirements-eval.txt
python -m evals.run_rag_eval
```

Both write a markdown table + JSON to `evals/results/` — sample output
from a mock run is already there to show the shape of the report; replace
with a live run before showcasing real numbers.

## 🔭 Observability

Every LLM call site and every LangGraph node emits a Pydantic Logfire
span — the print()-only logging is gone. `config/observability.py`
configures this once per process and works with no `LOGFIRE_TOKEN` set
(falls back to local console spans).

Tracked per call: latency, estimated input/output tokens, and estimated
cost — which makes the diff-based cost-saving design visible, not just
claimed: local Ollama calls show `$0`, Gemini Analyst calls show their
real per-call cost.

| Instrumented | Where |
|---|---|
| LangGraph pipeline nodes | `pipeline/graph.py` (`setup_node`, `crawl_node`, `summarize_node`) |
| Crawler batch run | `agents/crawler.py` |
| Analyst structured extraction | `agents/analyst.py` |
| Summarizer brief generation | `agents/summarizer.py` |
| RAG chat query | `dashboard/app.py` |

## ☁️ Deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for the full guide — Railway (or
Fly.io) for Postgres/Redis/Qdrant + the Celery worker/beat pair, Streamlit
Community Cloud for the dashboard, and a `USE_HOSTED_LLM=true` env flag
(`config/llm.py`) that swaps the local Ollama calls for Gemini Flash in
environments without a place to run Ollama — same interface, no other
code changes needed.

```bash
# Full local stack, including the app itself (not just infra)
docker compose up --build
```

## 🗺️ Roadmap

- [x] Structured-output guardrails on the Analyst agent
- [x] Prompt-injection defenses on untrusted scraped content
- [x] Evaluation harness (extraction accuracy + RAGAS RAG scoring)
- [x] Observability (Pydantic Logfire tracing across all LLM calls)
- [x] Deployment guide (Railway/Fly.io + Streamlit Cloud)
- [ ] Twitter/X mentions tracking
- [ ] G2 and App Store review monitoring
- [ ] Email digest delivery
- [ ] FastAPI backend for external integrations
- [ ] Confidence scoring on RAG answers
- [ ] Multi-language support for global competitors

---

## 🤝 Why I built this

Competitive intelligence is one of the highest-leverage activities for any startup, yet it's almost entirely manual today. Founders and product teams waste hours every week checking competitor websites, Twitter, and job boards — and the intelligence is always stale by the time they see it.

Radarr solves this with a production-grade multi-agent AI system that costs nothing to run and delivers better intelligence than a human analyst doing it manually.

---

*Built with Python, LangGraph, Gemini, Llama, Qdrant, and a lot of debugging.*