import asyncio
import logfire
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from agents.crawler import run_crawler
from agents.summarizer import run_summarizer
from memory.postgres import setup_database
from memory.vector_store import setup_vector_store
from config.observability import configure_observability
from dotenv import load_dotenv

load_dotenv()
configure_observability()

class PipelineState(TypedDict):
    status: str
    analyses: List[dict]
    brief: Optional[str]
    error: Optional[str]

async def setup_node(state: PipelineState) -> PipelineState:
    with logfire.span("setup_node"):
        print("\n[PIPELINE] Step 1/3 — Setting up database...")
        try:
            setup_database()
            setup_vector_store()
            return {**state, "status": "setup_complete"}
        except Exception as e:
            logfire.error("setup_node failed", error=str(e))
            return {**state, "status": "error", "error": str(e)}

async def crawl_node(state: PipelineState) -> PipelineState:
    with logfire.span("crawl_node") as span:
        print("\n[PIPELINE] Step 2/3 — Running crawler and analyst...")
        try:
            analyses = await run_crawler()
            span.set_attribute("analyses_count", len(analyses))
            return {**state, "status": "crawl_complete", "analyses": analyses}
        except Exception as e:
            logfire.error("crawl_node failed", error=str(e))
            return {**state, "status": "error", "error": str(e)}

async def summarize_node(state: PipelineState) -> PipelineState:
    with logfire.span("summarize_node"):
        print("\n[PIPELINE] Step 3/3 — Generating daily brief...")
        try:
            brief = run_summarizer()

            from tools.delivery import send_to_slack
            from memory.postgres import get_recent_analyses
            analyses = get_recent_analyses(days=1)
            with logfire.span("send_to_slack", signal_count=len(analyses)):
                await send_to_slack(brief, analyses)

            return {**state, "status": "complete", "brief": brief}
        except Exception as e:
            logfire.error("summarize_node failed", error=str(e))
            return {**state, "status": "error", "error": str(e)}


def should_continue(state: PipelineState) -> str:
    if state["status"] == "error":
        return "end"
    return "continue"

def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("setup", setup_node)
    graph.add_node("crawl", crawl_node)
    graph.add_node("summarize", summarize_node)

    graph.set_entry_point("setup")

    graph.add_conditional_edges(
        "setup",
        should_continue,
        {"continue": "crawl", "end": END}
    )
    graph.add_conditional_edges(
        "crawl",
        should_continue,
        {"continue": "summarize", "end": END}
    )
    graph.add_edge("summarize", END)

    return graph.compile()

async def run_pipeline():
    print("\n" + "="*50)
    print("RADARR — PIPELINE STARTING")
    print("="*50)

    app = build_graph()

    initial_state: PipelineState = {
        "status": "starting",
        "analyses": [],
        "brief": None,
        "error": None
    }

    final_state = await app.ainvoke(initial_state)

    print("\n" + "="*50)
    print("RADARR — PIPELINE COMPLETE")
    print("="*50)

    if final_state["status"] == "error":
        print(f"Pipeline failed: {final_state['error']}")
        return None

    print(f"Analyses generated: {len(final_state['analyses'])}")
    print("\nDAILY BRIEF:")
    print(final_state["brief"])

    return final_state


if __name__ == "__main__":
    asyncio.run(run_pipeline())
