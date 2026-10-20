import math
import re
from collections import Counter
from typing import List, Dict

from src.agents.state import DocumentPayload

def rank_documents(query: str, documents: List[DocumentPayload], top_k: int = 5) -> List[DocumentPayload]:
    """
    Rank documents based on cosine similarity of TF-IDF vectors between query and document content.
    """
    if not documents:
        return []
        
    # Preprocess query
    query_tokens = _tokenize(query)
    if not query_tokens:
        return documents[:top_k]
        
    # Preprocess documents
    doc_tokens_list = [_tokenize(doc["content"]) for doc in documents]
    
    # Calculate IDF
    N = len(documents)
    idf: Dict[str, float] = {}
    all_tokens = set(query_tokens)
    for tokens in doc_tokens_list:
        all_tokens.update(tokens)
        
    for token in all_tokens:
        doc_count = sum(1 for tokens in doc_tokens_list if token in tokens)
        idf[token] = math.log(1 + (N / (1 + doc_count)))
        
    # Calculate Query Vector
    query_vec = _compute_tfidf(query_tokens, idf)
    
    # Calculate Document Vectors and Similarity
    scores = []
    for i, doc_tokens in enumerate(doc_tokens_list):
        doc_vec = _compute_tfidf(doc_tokens, idf)
        score = _cosine_similarity(query_vec, doc_vec)
        scores.append((score, documents[i]))
        
    # Sort by score descending
    scores.sort(key=lambda x: x[0], reverse=True)
    
    return [doc for _, doc in scores[:top_k]]

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into chunks with overlap."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    # Trim trailing chunks that are only overlap leftovers (no new content)
    while len(chunks) > 1 and len(chunks[-1]) <= overlap:
        chunks.pop()
        
    return chunks

def _tokenize(text: str) -> List[str]:
    text = text.lower()
    return re.findall(r'\b\w+\b', text)

def _compute_tfidf(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = Counter(tokens)
    total_tokens = len(tokens)
    if total_tokens == 0:
        return {}
        
    vec = {}
    for token, count in tf.items():
        if token in idf:
            vec[token] = (count / total_tokens) * idf[token]
    return vec

def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)
    
    sum1 = sum(vec1[x]**2 for x in vec1)
    sum2 = sum(vec2[x]**2 for x in vec2)
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    if denominator == 0:
        return 0.0
    return numerator / denominator
