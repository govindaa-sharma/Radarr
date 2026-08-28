import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import uuid

load_dotenv()

COLLECTION_NAME = "intel_analyses"
VECTOR_SIZE = 384

_model = None


def get_model():
    """Load the embedding model only when semantic search is actually used."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_client():
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))

def setup_vector_store():
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created Qdrant collection: {COLLECTION_NAME}")
    else:
        print(f"Qdrant collection already exists: {COLLECTION_NAME}")


def collection_exists(client) -> bool:
    return any(c.name == COLLECTION_NAME for c in client.get_collections().collections)

def embed_text(text):
    return get_model().encode(text).tolist()

def store_analysis(competitor, page_type, event_type, importance, summary, analysed_at):
    client = get_client()
    if not collection_exists(client):
        setup_vector_store()

    full_text = f"{competitor} {page_type} {event_type} {summary}"
    vector = embed_text(full_text)

    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload={
            "competitor": competitor,
            "page_type": page_type,
            "event_type": event_type,
            "importance": importance,
            "summary": summary,
            "analysed_at": str(analysed_at)
        }
    )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )

def search_analyses(query, top_k=5, competitor_filter=None):
    client = get_client()
    if not collection_exists(client):
        return []
    query_vector = embed_text(query)

    search_filter = None
    if competitor_filter:
        search_filter = Filter(
            must=[FieldCondition(
                key="competitor",
                match=MatchValue(value=competitor_filter)
            )]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True
    ).points

    return [
        {
            "score": round(r.score, 3),
            "competitor": r.payload["competitor"],
            "event_type": r.payload["event_type"],
            "importance": r.payload["importance"],
            "summary": r.payload["summary"],
            "analysed_at": r.payload["analysed_at"]
        }
        for r in results
    ]

def sync_postgres_to_qdrant():
    from memory.postgres import get_connection
    from psycopg2.extras import RealDictCursor

    print("Syncing all analyses from PostgreSQL to Qdrant...")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT competitor, page_type, event_type, importance, summary, analysed_at
        FROM analyses
        ORDER BY analysed_at ASC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    setup_vector_store()

    for row in rows:
        store_analysis(
            competitor=row["competitor"],
            page_type=row["page_type"],
            event_type=row["event_type"],
            importance=row["importance"],
            summary=row["summary"],
            analysed_at=row["analysed_at"]
        )

    print(f"Synced {len(rows)} analyses to Qdrant.")
    return len(rows)

def clear_and_resync():
    client = get_client()
    if collection_exists(client):
        client.delete_collection(COLLECTION_NAME)
        print("Cleared existing collection.")
    setup_vector_store()
    sync_postgres_to_qdrant()
