import requests
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings

qdrant = QdrantClient(path="./qdrant_data")


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = requests.post(
        f"{settings.ollama_url}/api/embed",
        json={
            "model": settings.embedding_model,
            "input": texts
        },
        timeout=120
    )
    response.raise_for_status()
    data = response.json()
    return data["embeddings"]


def ensure_collection(vector_size: int):
    collections = qdrant.get_collections().collections
    existing_names = [c.name for c in collections]

    if settings.collection_name not in existing_names:
        qdrant.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )


def upsert_chunks(document_id: str, source_name: str, chunks: list[str]) -> int:
    embeddings = embed_texts(chunks)
    ensure_collection(len(embeddings[0]))

    points = []
    for chunk, vector in zip(chunks, embeddings):
        chunk_id = str(uuid4())
        points.append(
            PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "source": source_name,
                    "text": chunk
                }
            )
        )

    qdrant.upsert(
        collection_name=settings.collection_name,
        points=points
    )
    return len(points)


def search_chunks(query: str, limit: int = 5):
    query_vector = embed_texts([query])[0]
    results = qdrant.query_points(
        collection_name=settings.collection_name,
        query=query_vector,
        limit=limit
    )
    return results.points


def delete_document_chunks(document_id: str):
    qdrant.delete(
        collection_name=settings.collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
    )


def generate_answer(question: str, context_blocks: list[dict]) -> str:
    context_text = "\n\n---\n\n".join(
        [
            f"Source: {item['source']}\nChunk ID: {item['chunk_id']}\nText: {item['text']}"
            for item in context_blocks
        ]
    )

    prompt = f"""
You are a Finnish education expert assistant.
Answer ONLY from the provided context.
If the answer is not supported by the context, say:
"I cannot verify that from the uploaded research."

When possible:
1. explain clearly
2. keep the answer practical
3. avoid inventing claims
4. refer to the uploaded materials only

Context:
{context_text}

User question:
{question}
""".strip()

    response = requests.post(
        f"{settings.ollama_url}/api/generate",
        json={
            "model": settings.chat_model,
            "prompt": prompt,
            "stream": False
        },
        timeout=240
    )
    response.raise_for_status()
    data = response.json()
    return data["response"]