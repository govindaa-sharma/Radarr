"""
Golden QA set for evaluating the dashboard's RAG chat (dashboard/app.py).

Each example provides a question, a ground-truth answer, and the
"seeded_context" — a stand-in for what memory.vector_store.search_analyses()
would retrieve from Qdrant for that question, phrased exactly like real
stored analyses (competitor / event_type / importance / summary).

Using seeded context instead of a live Qdrant query means this eval isolates
generation quality (does the LLM answer faithfully from the given context?)
from retrieval quality. Retrieval quality should be evaluated separately
once you have real production data in Qdrant, using RAGAS's context_recall
against known "the answer should have come from analysis #X" labels.
"""

GOLDEN_QA_SET = [
    {
        "id": "cashfree_pricing_cut",
        "question": "Has Cashfree changed pricing recently?",
        "ground_truth": "Yes, Cashfree cut its standard plan fee from 1.95% + GST to 1.6% + GST, an aggressive pricing move.",
        "seeded_context": [
            "[Cashfree] [PRICING_CHANGE] importance=5/5 | 2026-08-20 09:00:00\n"
            "Cashfree cut its standard plan fee from 1.95% + GST to 1.6% + GST, positioning as the lowest in the industry. "
            "This directly pressures competitors on price-sensitive merchants."
        ],
    },
    {
        "id": "stripe_ai_direction",
        "question": "What is Stripe doing in AI?",
        "ground_truth": "Stripe is expanding into agentic commerce, hiring engineers for an Agentic Commerce team and posting roles in Bangalore and Dublin.",
        "seeded_context": [
            "[Stripe] [HIRING_SURGE] importance=5/5 | 2026-08-18 09:00:00\n"
            "Stripe posted 14 new engineering roles for its Agentic Commerce team, based in Bangalore and Dublin, "
            "signalling a major push into AI-driven payment agents.",
            "[Stripe] [FEATURE_LAUNCH] importance=4/5 | 2026-08-15 09:00:00\n"
            "Stripe announced the Machine Payments Protocol, positioning them ahead in agentic commerce infrastructure.",
        ],
    },
    {
        "id": "most_active_competitor",
        "question": "Which competitor has been most active this week?",
        "ground_truth": "Razorpay has had the most signals this week, including a partnership with NPCI and a RazorpayX Payroll launch.",
        "seeded_context": [
            "[Razorpay] [PARTNERSHIP] importance=5/5 | 2026-08-21 09:00:00\n"
            "Razorpay partners with NPCI and Anthropic to launch Agentic Payments across banking and payroll platforms.",
            "[Razorpay] [FEATURE_LAUNCH] importance=4/5 | 2026-08-19 09:00:00\n"
            "Razorpay introduced RazorpayX Payroll, full-stack payroll and compliance for Indian startups.",
            "[Razorpay] [PRODUCT_UPDATE] importance=3/5 | 2026-08-17 09:00:00\n"
            "Razorpay dashboard now supports dark mode and faster settlement reports.",
        ],
    },
    {
        "id": "no_relevant_data",
        "question": "Has any competitor announced layoffs?",
        "ground_truth": "There is no information about layoffs in the available intelligence data.",
        "seeded_context": [
            "[Stripe] [HIRING_SURGE] importance=5/5 | 2026-08-18 09:00:00\n"
            "Stripe posted 14 new engineering roles for its Agentic Commerce team."
        ],
    },
    {
        "id": "leadership_change_query",
        "question": "Did Stripe make any leadership changes?",
        "ground_truth": "Yes, Stripe announced a new Chief Revenue Officer, previously VP of Sales at a Fortune 500 company.",
        "seeded_context": [
            "[Stripe] [LEADERSHIP_CHANGE] importance=4/5 | 2026-08-16 09:00:00\n"
            "Stripe announced a new Chief Revenue Officer, previously VP of Sales at a Fortune 500 company."
        ],
    },
]
