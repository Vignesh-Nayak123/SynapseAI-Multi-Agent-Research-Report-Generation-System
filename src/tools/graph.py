import networkx as nx
from typing import List, Dict, Any
from collections import Counter
import re

from src.agents.state import DocumentPayload

def build_citation_graph(documents: List[DocumentPayload]) -> Dict[str, Any]:
    """
    Construct a graph where nodes are documents and edges represent shared concepts/keywords.
    Returns a JSON-serializable format: {"nodes": [...], "links": [...]}
    """
    G = nx.Graph()
    
    # Add document nodes
    for i, doc in enumerate(documents):
        node_id = f"S{i+1}"
        G.add_node(node_id, type="paper", label=f"Source {i+1}", url=doc["source"])
        
    # Extract keywords for each document
    doc_keywords = {}
    for i, doc in enumerate(documents):
        node_id = f"S{i+1}"
        keywords = _extract_keywords(doc["content"])
        doc_keywords[node_id] = keywords
        
    # Add edges based on shared keywords (Jaccard similarity)
    nodes = list(G.nodes())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            u, v = nodes[i], nodes[j]
            k1 = doc_keywords[u]
            k2 = doc_keywords[v]
            
            intersection = k1 & k2
            union = k1 | k2
            if not union:
                continue
                
            jaccard = len(intersection) / len(union)
            if jaccard > 0.1:  # Threshold
                G.add_edge(u, v, weight=jaccard)
                
    return nx.node_link_data(G)

def _extract_keywords(text: str, top_k: int = 20) -> set:
    # Simple keyword extraction: remove common words, keep capitalized or frequent words
    words = re.findall(r'\b\w{4,}\b', text.lower())
    # Filter stop words (very basic list)
    stop_words = {"this", "that", "with", "from", "have", "were", "which", "their", "they", "will", "also", "these"}
    words = [w for w in words if w not in stop_words]
    
    counter = Counter(words)
    return set(word for word, _ in counter.most_common(top_k))
