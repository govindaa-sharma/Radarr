"""
Observability setup for Radarr, using Pydantic Logfire.

Every LLM call and every pipeline stage becomes a span: latency, inputs/
outputs (with obviously sensitive fields excluded), and — for the LLM
calls — a rough token/cost estimate. This replaces the print()-only
logging that made debugging a failed nightly run mean scrolling through
raw stdout.

Safe by design: configure_observability() works with NO LOGFIRE_TOKEN set
— it just logs to the local console instead of shipping to the Logfire
dashboard. Nothing breaks in local dev or CI if the token isn't there.
"""

import logfire


_configured = False


def configure_observability(service_name: str = "radarr"):
    global _configured
    if _configured:
        return

    logfire.configure(
        service_name=service_name,
        send_to_logfire="if-token-present",
    )

    # Optional auto-instrumentation — each needs its own
    # opentelemetry-instrumentation-* extra installed (e.g.
    # `pip install 'logfire[httpx]'`). Skip quietly if missing rather than
    # crashing every import that calls configure_observability(); the
    # manual logfire.span() calls throughout the codebase work regardless.
    for instrument in ("instrument_httpx", "instrument_psycopg"):
        try:
            getattr(logfire, instrument)()
        except Exception:
            pass

    _configured = True


# Very rough token estimate (chars / 4) used only for cost-visibility in
# traces — NOT a substitute for a real tokenizer. Good enough to see the
# order of magnitude and the Gemini-vs-local-Llama cost split at a glance.
def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


# Approximate Gemini 2.5 Flash pricing (USD per 1K tokens) — update if
# pricing changes. Local Llama calls are always $0, which is the whole
# point of routing them there instead of to Gemini.
GEMINI_FLASH_COST_PER_1K_INPUT = 0.0003
GEMINI_FLASH_COST_PER_1K_OUTPUT = 0.0025


def estimate_gemini_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        (input_tokens / 1000) * GEMINI_FLASH_COST_PER_1K_INPUT
        + (output_tokens / 1000) * GEMINI_FLASH_COST_PER_1K_OUTPUT
    )
