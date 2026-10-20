from typing import Any, Dict, List
import json
import os
from datetime import datetime, timezone

from src.tools.search import search_papers

def evaluate_retrieval(query: str, expected_urls: List[str], k: int = 10) -> Dict[str, float]:
    """
    Measure recall@k for a given query and expected URLs.
    """
    found_urls = search_papers(query, limit=k)
    
    # Normalize URLs for comparison (simple strip)
    found_set = set(url.strip().lower() for url in found_urls)
    expected_set = set(url.strip().lower() for url in expected_urls)
    
    hits = 0
    for expected in expected_set:
        # Check for exact match or substring match (sometimes search returns different params)
        if any(expected in found or found in expected for found in found_set):
            hits += 1
            
    recall = hits / len(expected_set) if expected_set else 0.0
    
    metrics = {
        "query": query,
        "k": k,
        "expected_count": len(expected_set),
        "found_count": len(found_set),
        "hits": hits,
        "recall_at_k": recall,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    _save_metrics(metrics)
    return metrics

def _save_metrics(metrics: Dict[str, Any]):
    os.makedirs("storage/metrics", exist_ok=True)
    filename = f"storage/metrics/retrieval_{int(datetime.now(timezone.utc).timestamp())}.json"
    with open(filename, "w") as f:
        json.dump(metrics, f, indent=2)
