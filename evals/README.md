# Radarr eval harness

Two separate evals, because the pipeline has two separate LLM tasks:

| Eval | Target | Metrics | Deps |
|---|---|---|---|
| `run_analyst_eval.py` | `agents/analyst.py` extraction | event_type accuracy, importance MAE, injection-resistance check | main `requirements.txt` — no extra install needed |
| `run_rag_eval.py` | dashboard RAG chat generation | RAGAS faithfulness, answer relevancy, context precision | separate `evals/requirements-eval.txt` (see below) |

## Why the RAG eval needs a separate venv

`ragas==0.1.21` pins `langchain-core<0.3`; this project's `langgraph==0.2.60`
needs `langchain-core>=1.4`. They can't coexist in one environment. Set up
a second venv just for RAG evals:

```bash
python -m venv .venv-evals
source .venv-evals/bin/activate
pip install -r evals/requirements-eval.txt
python -m evals.run_rag_eval          # live, needs GEMINI_API_KEY in .env
deactivate
```

The analyst eval has no such conflict and runs fine in your normal app venv.

## Running

```bash
# Analyst extraction eval (normal venv)
python -m evals.run_analyst_eval --mock   # offline plumbing check, no API calls
python -m evals.run_analyst_eval          # live, needs GEMINI_API_KEY

# RAG chat eval (.venv-evals)
python -m evals.run_rag_eval --mock       # generates answers offline, skips RAGAS scoring
python -m evals.run_rag_eval              # live, full RAGAS scoring
```

Both write a markdown table + JSON to `evals/results/`, which is what gets
linked/screenshotted into the main README.

## Growing the golden sets

`evals/golden_analyst_dataset.py` and `evals/golden_rag_dataset.py` are
small (12 and 5 examples) and hand-labeled on purpose — trustworthy labels
matter more than volume at this stage. The highest-value way to grow them:
whenever the Analyst or the RAG chat gets something wrong in real use, turn
that exact case into a new golden example with the correct expected answer,
so regressions get caught automatically going forward.
