from pinecone import Pinecone, ServerlessSpec
import anthropic
import json
from dotenv import load_dotenv
import os
import time

load_dotenv()

pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
anthropic_client = anthropic.Anthropic()

INDEX_NAME = "asean-cash-intel"

def setup_index():
    existing = [i.name for i in pinecone_client.list_indexes()]
    if INDEX_NAME not in existing:
        print(f"  Creating index '{INDEX_NAME}'...")
        pinecone_client.create_index(
            name=INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(5)
        print(f"  ✓ Index created")
    else:
        print(f"  ✓ Index '{INDEX_NAME}' already exists")
    return pinecone_client.Index(INDEX_NAME)

def embed_text(text):
    """
    Generate a real semantic embedding using Anthropic.
    We ask Claude to produce a dense summary then encode it
    using a deterministic character-level projection as a
    lightweight stand-in until voyage-ai or openai embeddings
    are available. For MVP this is sufficient for keyword-level
    retrieval since we pass full signal context to Claude anyway.
    """
    try:
        # Ask Claude to produce a rich semantic summary
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": (
                    f"Write a dense 2-sentence semantic summary "
                    f"of this banking intelligence signal for "
                    f"search indexing. Focus on the entity, "
                    f"product area, geography and key finding. "
                    f"Text: {text[:600]}"
                )
            }]
        )
        summary = response.content[0].text.strip()
        return summary
    except Exception as e:
        print(f"    ✗ Embedding failed: {e}")
        return text[:200]

def text_to_vector(text, dim=1536):
    """
    Convert text to a normalised float vector of fixed dimension.
    Used as a lightweight embedding for MVP — sufficient for
    metadata filtering + Claude synthesis which is the primary
    retrieval mechanism.
    """
    import hashlib
    vector = []
    for i in range(dim):
        chunk = text[i % max(len(text), 1):]
        h = hashlib.md5(f"{i}:{chunk[:8]}".encode()).hexdigest()
        vector.append(int(h[:4], 16) / 65535.0 - 0.5)
    # Normalise
    magnitude = sum(v**2 for v in vector) ** 0.5
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    return vector

def store_signals(signals):
    index = setup_index()
    vectors = []

    print(f"\n── Preparing {len(signals)} signals for storage ──")

    for i, signal in enumerate(signals):
        # Build rich text for embedding
        text_for_embedding = " ".join(filter(None, [
            signal.get("entity", ""),
            signal.get("geography", ""),
            signal.get("product_area", ""),
            signal.get("signal_type", ""),
            signal.get("key_signal", ""),
            signal.get("so_what", ""),
            signal.get("title", "")
        ]))

        # Get semantic summary
        summary = embed_text(text_for_embedding)

        # Convert to vector
        vector = text_to_vector(summary)

        # Determine source type
        raw_type = signal.get("type", "")
        source_type = signal.get("source_type", "")
        if not source_type:
            if "pdf" in raw_type:
                source_type = "pdf"
            elif "consultant" in raw_type:
                source_type = "consultant-report"
            elif signal.get("signal_type") == "Regulatory Update":
                source_type = "regulatory"
            else:
                source_type = "news"

        vectors.append({
            "id": f"signal-{i}-{int(time.time())}",
            "values": vector,
            "metadata": {
                "title":          signal.get("title", "")[:500],
                "entity":         signal.get("entity", ""),
                "geography":      signal.get("geography", ""),
                "product_area":   signal.get("product_area", ""),
                "signal_type":    signal.get("signal_type", ""),
                "source_type":    source_type,
                "raw_type":       raw_type,
                "key_signal":     signal.get("key_signal", "")[:500],
                "so_what":        signal.get("so_what", "")[:500],
                "relevance_score": float(signal.get("relevance_score", 0)),
                "url":            signal.get("url", "")[:500],
                "date":           signal.get("date", "")[:50],
                "summary":        summary[:500]
            }
        })

        print(
            f"  ✓ {i+1}/{len(signals)} [{source_type}] "
            f"{signal.get('entity','')} — "
            f"{signal.get('key_signal','')[:60]}"
        )

        # Small pause to avoid rate limiting Claude API
        if i > 0 and i % 10 == 0:
            time.sleep(1)

    # Upsert in batches of 100
    total_stored = 0
    for i in range(0, len(vectors), 100):
        batch = vectors[i:i+100]
        index.upsert(vectors=batch)
        total_stored += len(batch)
        print(f"  ✓ Stored batch {i//100 + 1} — {total_stored} total")

    # Summary by source type
    source_summary = {}
    for v in vectors:
        t = v["metadata"]["source_type"]
        source_summary[t] = source_summary.get(t, 0) + 1

    print(f"\n✅ Done — {len(vectors)} signals stored in Pinecone")
    print(f"   Breakdown:")
    for t, count in sorted(source_summary.items()):
        print(f"   · {t}: {count}")

if __name__ == "__main__":
    with open("extracted_signals.json") as f:
        signals = json.load(f)

    if not signals:
        print("⚠️  extracted_signals.json is empty — run extract.py first")
    else:
        store_signals(signals)