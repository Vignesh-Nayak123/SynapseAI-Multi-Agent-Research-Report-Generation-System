import pytest
from src.tools.ranking import rank_documents, chunk_text

def test_chunk_text():
    text = "1234567890"
    chunks = chunk_text(text, chunk_size=5, overlap=2)
    # 12345
    #    45678
    #       7890
    assert len(chunks) == 3
    assert chunks[0] == "12345"
    assert chunks[1] == "45678"
    assert chunks[2] == "7890"

def test_rank_documents():
    documents = [
        {"source": "doc1", "content": "apple banana"},
        {"source": "doc2", "content": "orange grape"},
        {"source": "doc3", "content": "apple apple"}
    ]
    
    query = "apple"
    ranked = rank_documents(query, documents, top_k=2)
    
    assert len(ranked) == 2
    assert ranked[0]["source"] == "doc3"  # More apples
    assert ranked[1]["source"] == "doc1"
