import math
import re
from collections import Counter
from typing import List, Dict, Tuple, Any

# English stopwords for native pure-Python NLP
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can\'t', 'cannot', 'could',
    'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d', 'he\'ll', 'he\'s',
    'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i', 'i\'d', 'i\'ll', 'i\'m',
    'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s', 'me', 'more', 'most', 'mustn\'t',
    'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours',
    'ourselves', 'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d', 'she\'ll', 'she\'s', 'should', 'shouldn\'t',
    'so', 'some', 'such', 'than', 'that', 'that\'s', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there',
    'there\'s', 'these', 'they', 'they\'d', 'they\'ll', 'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve', 'were', 'weren\'t',
    'what', 'what\'s', 'when', 'when\'s', 'where', 'where\'s', 'which', 'while', 'who', 'who\'s', 'whom', 'why', 'why\'s',
    'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'you\'d', 'you\'ll', 'you\'re', 'you\'ve', 'your', 'yours', 'yourself',
    'yourselves'
}

# Optional scikit-learn import
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import AgglomerativeClustering
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def _tokenize(text: str) -> List[str]:
    words = re.findall(r'[a-zA-Z]{2,}', text.lower())
    unigrams = [w for w in words if w not in STOPWORDS]
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if words[i] not in STOPWORDS or words[i+1] not in STOPWORDS]
    return unigrams + bigrams


def extract_keywords_and_vectors(texts: List[str], top_k: int = 5) -> Tuple[Any, List[List[str]]]:
    """
    Extracts TF-IDF representations and top keywords.
    Uses sklearn if available; otherwise falls back to a zero-dependency pure-Python engine.
    """
    if SKLEARN_AVAILABLE:
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english",
                max_features=2500,
                min_df=1
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            keywords_list = []
            for idx in range(len(texts)):
                row_vector = tfidf_matrix[idx].toarray()[0]
                top_indices = row_vector.argsort()[-top_k:][::-1]
                kw = [feature_names[i] for i in top_indices if row_vector[i] > 0]
                keywords_list.append(kw)
            return tfidf_matrix, keywords_list
        except Exception:
            pass

    # Pure Python TF-IDF fallback
    N = len(texts)
    doc_tokens = [_tokenize(t) for t in texts]
    df = Counter()
    for tokens in doc_tokens:
        for t in set(tokens):
            df[t] += 1

    doc_vectors = []
    keywords_list = []
    for tokens in doc_tokens:
        tf = Counter(tokens)
        vec: Dict[str, float] = {}
        for term, count in tf.items():
            idf = math.log((1 + N) / (1 + df[term])) + 1.0
            vec[term] = count * idf
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        normalized_vec = {k: v / norm for k, v in vec.items()}
        doc_vectors.append(normalized_vec)
        sorted_kw = sorted(normalized_vec.items(), key=lambda x: x[1], reverse=True)
        keywords_list.append([k for k, _ in sorted_kw[:top_k]])

    return doc_vectors, keywords_list


def perform_clustering(vectors: Any, n_clusters: int) -> List[int]:
    """
    Clusters vector representations using cosine distance agglomerative clustering.
    Uses sklearn if available; otherwise pure-Python hierarchical clustering.
    """
    if SKLEARN_AVAILABLE and hasattr(vectors, "toarray"):
        try:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric="cosine",
                linkage="average"
            )
            labels = clustering.fit_predict(vectors.toarray())
            return list(labels)
        except Exception:
            pass

    # Pure Python agglomerative clustering
    n = len(vectors)
    if n <= 1:
        return [0] * n

    n_clusters = max(1, min(n_clusters, n))
    clusters = {i: [i] for i in range(n)}
    dists: Dict[Tuple[int, int], float] = {}

    for i in range(n):
        for j in range(i + 1, n):
            common = set(vectors[i].keys()) & set(vectors[j].keys())
            sim = sum(vectors[i][k] * vectors[j][k] for k in common)
            dists[(i, j)] = 1.0 - sim

    while len(clusters) > n_clusters:
        min_dist = float('inf')
        best_pair = None
        c_keys = list(clusters.keys())
        for i in range(len(c_keys)):
            k1 = c_keys[i]
            for j in range(i + 1, len(c_keys)):
                k2 = c_keys[j]
                avg_d = sum(dists.get((min(a, b), max(a, b)), 1.0) for a in clusters[k1] for b in clusters[k2]) / (len(clusters[k1]) * len(clusters[k2]))
                if avg_d < min_dist:
                    min_dist = avg_d
                    best_pair = (k1, k2)

        if not best_pair:
            break
        k1, k2 = best_pair
        clusters[k1].extend(clusters[k2])
        del clusters[k2]

    labels = [0] * n
    for lbl, members in enumerate(clusters.values()):
        for m in members:
            labels[m] = lbl
    return labels
