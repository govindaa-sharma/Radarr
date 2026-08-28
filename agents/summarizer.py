import logfire
from config.llm import get_local_llm, USE_HOSTED_LLM
from config.observability import estimate_tokens, estimate_gemini_cost
from memory.postgres import get_recent_analyses
from dotenv import load_dotenv

load_dotenv()

SUMMARIZER_PROMPT = """You are a sharp analyst writing a daily competitive intelligence brief for a fintech startup founder.

Below are the competitive intelligence signals detected in the last 24 hours, ranked by importance.
Write a clean, concise morning brief that the founder can read in under 2 minutes.

Format your brief EXACTLY like this:

RADARR — DAILY INTELLIGENCE BRIEF
=====================================

TOP SIGNAL TODAY:
[The single most important thing that happened and why it matters]

KEY DEVELOPMENTS:
1. [Competitor] — [What happened] — [Why it matters in one sentence]
2. [Competitor] — [What happened] — [Why it matters in one sentence]
3. [Competitor] — [What happened] — [Why it matters in one sentence]

WATCH OUT FOR:
[One thing the founder should keep an eye on in the coming days]

RECOMMENDED PRIORITY ACTION:
[The single most important thing the founder should do today]

=====================================

Here are today's signals:

{analyses_text}
"""

def format_analyses_for_summarizer(analyses):
    if not analyses:
        return "No significant changes detected in the last 24 hours."

    lines = []
    for i, analysis in enumerate(analyses, 1):
        lines.append(
            f"{i}. [{analysis['event_type']}] importance={analysis['importance']}/5 | "
            f"Competitor: {analysis['competitor']} | "
            f"Page: {analysis['page_type']}\n"
            f"   {analysis['summary']}\n"
        )
    return "\n".join(lines)

def run_summarizer():
    print("Fetching recent analyses from database...")
    analyses = get_recent_analyses(days=1)

    if not analyses:
        print("No analyses found in the last 24 hours.")
        return "No significant competitive activity detected in the last 24 hours."

    print(f"Found {len(analyses)} analyses. Generating brief with Llama...")

    analyses_text = format_analyses_for_summarizer(analyses)
    prompt = SUMMARIZER_PROMPT.format(analyses_text=analyses_text)

    input_tokens = estimate_tokens(prompt)
    with logfire.span(
        "summarizer_llm_call",
        model="gemini-2.5-flash-hosted" if USE_HOSTED_LLM else "llama3.1:8b-local",
        input_tokens_est=input_tokens,
        signal_count=len(analyses),
    ) as span:
        llm = get_local_llm()
        brief = llm.invoke(prompt)
        output_tokens = estimate_tokens(brief)
        span.set_attributes({
            "output_tokens_est": output_tokens,
            # $0 in local mode — that asymmetry vs. the Analyst's Gemini
            # calls is the whole point of routing this agent locally.
            "cost_usd_est": estimate_gemini_cost(input_tokens, output_tokens) if USE_HOSTED_LLM else 0.0,
        })

    print("Brief generated successfully.")
    return brief