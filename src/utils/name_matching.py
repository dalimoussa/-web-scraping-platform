"""
Name matching and normalization utilities for cross-dataset matching.
Uses fuzzy matching, normalization, and optional semantic similarity.
"""

from typing import List, Tuple, Optional, Dict
import re
import unicodedata

from ..core.logger import get_logger


logger = get_logger(__name__)


def normalize_name(name: str) -> str:
    """
    Normalize name for matching.
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name
    """
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common suffixes/prefixes
    suffixes_to_remove = [
        'inc.', 'inc', 'ltd.', 'ltd', 'llc', 'corp', 'corporation',
        '株式会社', '有限会社', '合同会社', '氏', '様', '先生', '議員',
        'co.', 'company', 'group', 'holdings',
    ]
    
    for suffix in suffixes_to_remove:
        name = re.sub(rf'\b{re.escape(suffix)}\b', '', name, flags=re.IGNORECASE)
    
    # Remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    
    # Normalize unicode (convert fullwidth to halfwidth, etc.)
    name = unicodedata.normalize('NFKC', name)
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def fuzzy_match(
    query: str,
    candidates: List[str],
    threshold: float = 85.0,
    limit: int = 5,
) -> List[Tuple[str, float]]:
    """
    Fuzzy match query against candidates.
    
    Args:
        query: Query string
        candidates: List of candidate strings
        threshold: Minimum similarity score (0-100)
        limit: Maximum number of results
        
    Returns:
        List of (match, score) tuples
    """
    try:
        from rapidfuzz import process, fuzz
        
        # Use token_sort_ratio for better handling of word order
        results = process.extract(
            query,
            candidates,
            scorer=fuzz.token_sort_ratio,
            limit=limit,
        )
        
        # Filter by threshold
        filtered = [(match, score, idx) for match, score, idx in results if score >= threshold]
        
        logger.debug(f"Fuzzy match for '{query}': found {len(filtered)} matches above {threshold}")
        
        return [(match, score) for match, score, idx in filtered]
        
    except ImportError:
        logger.warning("rapidfuzz not installed. Install with: pip install rapidfuzz")
        
        # Fallback to simple exact matching
        matches = []
        query_norm = normalize_name(query)
        
        for candidate in candidates:
            if normalize_name(candidate) == query_norm:
                matches.append((candidate, 100.0))
        
        return matches[:limit]


def match_names_batch(
    queries: List[str],
    candidates: List[str],
    threshold: float = 85.0,
) -> Dict[str, Optional[str]]:
    """
    Match multiple queries against candidates.
    
    Args:
        queries: List of query names
        candidates: List of candidate names
        threshold: Minimum similarity score
        
    Returns:
        Dict mapping query to best match (or None)
    """
    results = {}
    
    for query in queries:
        matches = fuzzy_match(query, candidates, threshold=threshold, limit=1)
        
        if matches:
            results[query] = matches[0][0]  # Best match
        else:
            results[query] = None
    
    return results


def semantic_match(
    query: str,
    candidates: List[str],
    threshold: float = 0.7,
    limit: int = 5,
) -> List[Tuple[str, float]]:
    """
    Semantic similarity matching using sentence transformers.
    
    Args:
        query: Query string
        candidates: List of candidate strings
        threshold: Minimum cosine similarity (0.0-1.0)
        limit: Maximum number of results
        
    Returns:
        List of (match, similarity) tuples
    """
    try:
        from sentence_transformers import SentenceTransformer, util
        import torch
        
        # Load model (cached after first load)
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Encode
        query_emb = model.encode(query, convert_to_tensor=True)
        candidate_embs = model.encode(candidates, convert_to_tensor=True)
        
        # Compute similarities
        similarities = util.pytorch_cos_sim(query_emb, candidate_embs)[0]
        
        # Get top matches
        scores = similarities.cpu().numpy()
        top_indices = scores.argsort()[-limit:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] >= threshold:
                results.append((candidates[idx], float(scores[idx])))
        
        logger.debug(f"Semantic match for '{query}': found {len(results)} matches above {threshold}")
        
        return results
        
    except ImportError:
        logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
        logger.info("Falling back to fuzzy matching")
        
        # Fallback to fuzzy matching
        fuzzy_results = fuzzy_match(query, candidates, threshold=threshold * 100, limit=limit)
        return [(match, score / 100.0) for match, score in fuzzy_results]


def create_name_index(names: List[str]) -> Dict[str, List[str]]:
    """
    Create normalized name index for fast lookups.
    
    Args:
        names: List of names
        
    Returns:
        Dict mapping normalized name to list of original names
    """
    index = {}
    
    for name in names:
        normalized = normalize_name(name)
        if normalized not in index:
            index[normalized] = []
        index[normalized].append(name)
    
    return index


def find_exact_match(
    query: str,
    name_index: Dict[str, List[str]],
) -> Optional[str]:
    """
    Find exact match using normalized name index.
    
    Args:
        query: Query name
        name_index: Pre-built name index
        
    Returns:
        First matching original name or None
    """
    normalized = normalize_name(query)
    matches = name_index.get(normalized, [])
    
    return matches[0] if matches else None


def match_with_fallback(
    query: str,
    candidates: List[str],
    fuzzy_threshold: float = 85.0,
    semantic_threshold: float = 0.7,
    use_semantic: bool = False,
) -> Optional[Tuple[str, float, str]]:
    """
    Match with multiple fallback strategies.
    
    Args:
        query: Query name
        candidates: Candidate names
        fuzzy_threshold: Threshold for fuzzy matching
        semantic_threshold: Threshold for semantic matching
        use_semantic: Whether to use semantic matching
        
    Returns:
        Tuple of (match, score, method) or None
    """
    # 1. Try exact match (normalized)
    name_index = create_name_index(candidates)
    exact_match = find_exact_match(query, name_index)
    
    if exact_match:
        logger.debug(f"Exact match found for '{query}': {exact_match}")
        return (exact_match, 100.0, 'exact')
    
    # 2. Try fuzzy match
    fuzzy_matches = fuzzy_match(query, candidates, threshold=fuzzy_threshold, limit=1)
    
    if fuzzy_matches:
        match, score = fuzzy_matches[0]
        logger.debug(f"Fuzzy match found for '{query}': {match} (score: {score})")
        return (match, score, 'fuzzy')
    
    # 3. Try semantic match (if enabled and available)
    if use_semantic:
        semantic_matches = semantic_match(query, candidates, threshold=semantic_threshold, limit=1)
        
        if semantic_matches:
            match, similarity = semantic_matches[0]
            logger.debug(f"Semantic match found for '{query}': {match} (similarity: {similarity})")
            return (match, similarity * 100, 'semantic')
    
    logger.debug(f"No match found for '{query}'")
    return None
