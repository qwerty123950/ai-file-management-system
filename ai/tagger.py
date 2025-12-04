# ai/tagger.py

import re
from collections import Counter
from typing import List

# Very small stopword list; you can expand later
STOPWORDS = {
    "the", "and", "for", "that", "with", "this", "from", "have", "will",
    "your", "about", "there", "their", "what", "which", "when", "where",
    "then", "them", "they", "into", "been", "were", "such", "than",
    "also", "only", "some", "more", "most", "like", "very", "just",
    "over", "into", "because", "while", "shall", "should", "could",
    "would", "can", "cannot", "cant", "dont", "doesnt", "isnt", "wasnt",
    "are", "is", "am", "be", "on", "in", "of", "to", "as", "by", "at",
    "or", "an", "a", "it", "its", "we", "you", "i"
}


def generate_tags(text: str, max_tags: int = 8) -> List[str]:
    """
    Very simple tag generator:
    - takes the summary/content text
    - tokenizes into words
    - removes stopwords and short tokens
    - counts frequency
    - returns top N as tags
    """
    if not text:
        return []

    # Lowercase + keep only alphabetic tokens
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    if not words:
        return []

    filtered = [w for w in words if w not in STOPWORDS]

    if not filtered:
        return []

    freq = Counter(filtered)
    # sort by frequency desc, then alphabetically
    common = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    tags = [w for (w, _) in common[:max_tags]]
    return tags
