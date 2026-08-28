import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

USE_HOSTED_LLM = os.getenv("USE_HOSTED_LLM", "false").lower() == "true"


class _StringOutputChatWrapper:
    """
    Normalizes a LangChain chat model's .invoke()/.ainvoke() to return a
    plain string, so it's a drop-in replacement for OllamaLLM (which
    already returns strings) at call sites written before hosted-mode
    support existed: agents/summarizer.py and dashboard/app.py both do
    `llm.invoke(prompt)` and use the result directly as a string. Without
    this wrapper, swapping in ChatGoogleGenerativeAI would silently return
    an AIMessage object instead and break both call sites.
    """

    def __init__(self, chat_model):
        self._model = chat_model

    def invoke(self, prompt):
        result = self._model.invoke(prompt)
        return result.content if hasattr(result, "content") else str(result)

    async def ainvoke(self, prompt):
        result = await self._model.ainvoke(prompt)
        return result.content if hasattr(result, "content") else str(result)


def get_local_llm():
    """
    Returns the 'cheap' model used by the Summarizer agent and the RAG
    chat. Defaults to local Ollama (free, private) for local development.

    Set USE_HOSTED_LLM=true in .env (e.g. in a deployed environment with
    no GPU/RAM budget to run Ollama) to fall back to Gemini Flash instead —
    same call interface (.invoke returns a string), just hosted.
    """
    if USE_HOSTED_LLM:
        return _StringOutputChatWrapper(
            ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.1,
            )
        )
    return OllamaLLM(
        model="llama3.1:8b",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.1,
    )


def get_analyst_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.1,
    )
