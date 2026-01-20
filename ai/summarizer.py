# ai/summarizer.py

from typing import Tuple
from typing import Any, Dict, List

import re

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# Summarization model
MODEL_NAME = "google/pegasus-xsum"
# If you want a long-doc model later:
# MODEL_NAME = "pszemraj/long-t5-tglobal-base-16384-book-summary"

# Load tokenizer + model explicitly
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

# Safe upper bound for tokens per call
DEFAULT_MAX_TOKENS = 800  # Pegasus supports ~1k+, 800 is a safe chunk size

config_max_pos = getattr(model.config, "max_position_embeddings", None)
if isinstance(config_max_pos, int) and config_max_pos > 0:
    MAX_INPUT_TOKENS = min(DEFAULT_MAX_TOKENS, config_max_pos - 10)
else:
    MAX_INPUT_TOKENS = DEFAULT_MAX_TOKENS


def _token_chunks(text: str, max_tokens: int) -> List[str]:
    """
    Split text into multiple chunks, each at most `max_tokens` tokens long.
    Uses the model's tokenizer, so we are guaranteed to stay within limits.
    """
    input_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    chunks: List[str] = []

    for i in range(0, len(input_ids), max_tokens):
        chunk_ids = input_ids[i:i + max_tokens]
        chunk_text = tokenizer.decode(
            chunk_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )
        chunks.append(chunk_text)

    return chunks


def _dynamic_lengths(mode: str, input_token_len: int) -> Tuple[int, int]:
    """
    Decide (max_length, min_length) based on:
    - desired mode: 'short' | 'medium' | 'long'
    - input length in tokens
    """
    # Base factors by mode
    if mode == "short":
        target_ratio = 0.25   # 25% of input length
        max_cap = 80
    elif mode == "long":
        target_ratio = 0.7    # 70% of input length
        max_cap = 260
    else:  # "medium"
        target_ratio = 0.4    # 40% of input length
        max_cap = 160

    # Compute target max length w.r.t input
    max_len = int(input_token_len * target_ratio)
    max_len = max(16, min(max_cap, max_len))  # clamp

    # Min length: about 1/3 of max, but at least 10
    min_len = max(10, int(max_len / 3))

    return max_len, min_len


def _dedupe_sentences(text: str) -> str:
    """
    Remove duplicate or near-duplicate sentences while preserving order.
    Uses simple token-based similarity (no external libs).
    """
    text = text.strip()
    if not text:
        return text

    # Split on sentence boundaries: ., ?, !
    parts = re.split(r'(?<=[.!?])\s+', text)
    unique: list[str] = []

    def too_similar(a: str, b: str) -> bool:
        # Lowercase, keep only word chars
        wa = re.findall(r"\w+", a.lower())
        wb = re.findall(r"\w+", b.lower())
        if not wa or not wb:
            return False
        sa, sb = set(wa), set(wb)
        if not sa or not sb:
            return False
        # How much of the *shorter* sentence's words are shared?
        overlap = len(sa & sb) / min(len(sa), len(sb))
        return overlap >= 0.8  # 80%+ of shorter sentence's words overlap

    for s in parts:
        s_clean = s.strip()
        if not s_clean:
            continue

        # Compare with already accepted sentences
        is_dup = False
        for u in unique:
            if too_similar(s_clean, u):
                is_dup = True
                break

        if not is_dup:
            unique.append(s_clean)

    return " ".join(unique)



def _summarize_single(text: str, mode: str = "medium") -> str:
    """
    Summarize a single piece of text that already fits into the model capacity.
    """
    # tokenize to compute sensible lengths
    input_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    input_len = len(input_ids)

    max_length, min_length = _dynamic_lengths(mode, input_len)

    # Run pipeline
    output = summarizer(
        text,
        max_length=max_length,
        min_length=min_length,
        do_sample=False,
        num_beams=4,
        no_repeat_ngram_size=4,
    )

    # 🔒 Normalize pipeline output (list | generator → list)
    normalized = _normalize_pipeline_output(output)
    if not normalized:
        return ""

    raw_summary = normalized[0].get("summary_text", "")
    if not isinstance(raw_summary, str):
        raw_summary = str(raw_summary)

    cleaned = _dedupe_sentences(raw_summary)
    return cleaned

def _normalize_pipeline_output(result: Any) -> List[Dict[str, str]]:
    """
    Normalize HuggingFace pipeline output to List[Dict[str, str]].
    Works around weak pipeline typing.
    """
    if result is None:
        return []

    # Generator / iterator → list
    if hasattr(result, "__iter__") and not isinstance(result, list):
        result = list(result)

    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]

    return []
def summarize_text(text: str, mode: str = "medium") -> str:
    """
    Safe summarization that:
    - returns original text if it's very short
    - chunks long texts by tokens
    - summarizes each chunk
    - summarizes the concatenation of partial summaries
    - never exceeds MAX_INPUT_TOKENS in a single model call
    """
    text = text.strip()
    if not text:
        return ""

    # Very short content: don't bother summarizing
    if len(text.split()) < 50:
        return text

    # Check total token length
    input_ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)

    # Case 1: fits in a single model call
    if len(input_ids) <= MAX_INPUT_TOKENS:
        return _summarize_single(text, mode=mode)

    # Case 2: too long → chunk by tokens
    chunks = _token_chunks(text, MAX_INPUT_TOKENS)
    partial_summaries: List[str] = []

    for chunk in chunks:
        summary_chunk = _summarize_single(chunk, mode=mode)
        partial_summaries.append(summary_chunk)

    # Combine chunk summaries and compress again
    combined = " ".join(partial_summaries)

    # For the combined summary, we can reuse the same logic
    final_summary = _summarize_single(combined, mode=mode)
    return final_summary


def summarize_with_sentence_limit(text: str, sentences: int) -> str:
    """
    Generate a summary, then trim it to a specific number of sentences.
    sentences:
        1 -> short
        2 -> medium
        4 -> long
    """
    if sentences <= 0:
        sentences = 1

    if sentences == 1:
        mode = "short"
    elif sentences == 2:
        mode = "medium"
    else:
        mode = "long"

    base = summarize_text(text, mode=mode).strip()
    if not base:
        return base

    parts = re.split(r'(?<=[.!?])\s+', base)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return base

    return " ".join(parts[:sentences])
