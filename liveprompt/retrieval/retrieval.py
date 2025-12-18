import math
import re
import hashlib
import logging


logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _hash_embedding(text: str, *, dims: int = 512) -> list[float]:
    vec = [0.0] * dims
    for tok in _tokenize(text):
        h = hashlib.md5(tok.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % dims
        vec[idx] += 1.0

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vector sizes do not match")
    return sum(x * y for x, y in zip(a, b))


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a.intersection(b))
    union = len(a.union(b))
    if union == 0:
        return 0.0
    return inter / union


def _retrieve_relevant_paragraphs(
    *,
    paragraph_index: list[dict],
    query: str | None = None,
    queries: list[str] | None = None,
    current_chapter: int | None = None,
    top_k: int = 6,
    min_score: float = 0.10,
    max_chars_per_item: int = 700,
) -> list[dict]:
    if not paragraph_index:
        return []

    if queries is None:
        if not query:
            return []
        queries = [query]

    # Precompute query representations.
    q_vecs: list[list[float]] = []
    q_tokens: list[set[str]] = []
    for q in queries:
        if not isinstance(q, str) or not q.strip():
            continue
        q_vecs.append(_hash_embedding(q))
        q_tokens.append(set(_tokenize(q)))
    if not q_vecs:
        return []

    n = len(paragraph_index)
    scored: list[tuple[float, int, dict]] = []
    for idx, item in enumerate(paragraph_index):
        text = item.get("text")
        tv = item.get("_vec")
        if not isinstance(text, str) or not text.strip() or not isinstance(tv, list):
            continue

        # Semantic similarity: max over queries.
        sem = 0.0
        for qv in q_vecs:
            try:
                sem = max(sem, _cosine_similarity(qv, tv))
            except Exception:
                continue

        # Lexical overlap: max over queries.
        doc_tokens = set(_tokenize(text))
        lex = 0.0
        for qt in q_tokens:
            lex = max(lex, _jaccard_similarity(qt, doc_tokens))

        # Recency boost: gently prefer later items (more recent context).
        recency = 0.0
        if n > 1:
            recency = idx / (n - 1)

        # Chapter distance boost: prefer near chapters if we know current.
        ch_boost = 0.0
        if current_chapter is not None:
            try:
                item_ch = int(item.get("chapter"))
                dist = abs(int(current_chapter) - item_ch)
                # dist=0 => 1.0, dist=1 => 0.7, dist>=4 => ~0.25
                ch_boost = 1.0 / (1.0 + 0.5 * float(dist))
            except Exception:
                ch_boost = 0.0

        # Weighted score. Semantic is primary, lexical helps catch exact entities.
        score = (0.72 * sem) + (0.20 * lex) + (0.05 * recency) + (0.03 * ch_boost)
        if score >= min_score:
            scored.append((score, idx, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Diversify by chapter: don't let one chapter dominate the context.
    per_chapter_cap = 2
    counts: dict[int, int] = {}
    results: list[dict] = []
    for score, _idx, item in scored:
        if len(results) >= top_k:
            break
        try:
            ch = int(item.get("chapter"))
        except Exception:
            ch = -1

        if ch != -1:
            if counts.get(ch, 0) >= per_chapter_cap:
                continue
            counts[ch] = counts.get(ch, 0) + 1

        text = item.get("text", "")
        if not isinstance(text, str):
            continue
        results.append(
            {
                "chapter": item.get("chapter"),
                "paragraph": item.get("paragraph"),
                "score": round(float(score), 4),
                "text": text[:max_chars_per_item],
            }
        )

    return results


