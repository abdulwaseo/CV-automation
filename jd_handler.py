import logging
import os
from typing import Set, List

import spacy
from keybert import KeyBERT  # contextual keyword extractor

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------------------------------------------------------------
# SpaCy model loading (download on‑the‑fly if missing)
# ---------------------------------------------------------------------------
import spacy.cli

try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    logger.info("SpaCy model 'en_core_web_md' not found. Downloading now …")
    spacy.cli.download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

# ---------------------------------------------------------------------------
# Instantiate KeyBERT once (Sentence‑Transformers MiniLM by default)
# ---------------------------------------------------------------------------
kw_model = KeyBERT()

# ---------------------------------------------------------------------------
# Static skill lexicon – extend freely or load from a YAML / DB later
# ---------------------------------------------------------------------------
KNOWN_SKILLS: Set[str] = {
    "python", "java", "c++", "sql", "flask", "django", "aws",
    "excel", "linux", "javascript", "machine learning", "react",
    "docker", "git", "cloud", "data analysis", "ci/cd", "azure",
    "kubernetes", "terraform", "pandas", "numpy"
}

# ===========================================================================
# Helper functions
# ===========================================================================

def load_jd_text(filepath: str) -> str:
    """Read a JD text file and return its content (UTF‑8).

    Args:
        filepath: Path to the JD .txt file.

    Returns:
        File content or an empty string on failure.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception as exc:
        logger.error("❌ Failed to load JD file %s – %s", filepath, exc)
        return ""


# ===========================================================================
# Core keyword‑extraction routine – *Option B*: KeyBERT‑centric
# ===========================================================================

def extract_keywords_from_jd(
    jd_text: str,
    *,
    top_n: int = 12,
    include_static: bool = True,
    include_noun_chunks: bool = True,
) -> Set[str]:
    """Return a set of relevant keywords / skills extracted from the JD.

    The function fuses up to three independent signals:
        1. **Static skill matches** – Known skills appearing anywhere in the JD (optional).
        2. **Noun‑chunk exact matches** – Phrases from spaCy noun chunks that are in the lexicon (optional).
        3. **KeyBERT keyphrases** – Contextual keyphrases (1‑ to 3‑grams) ranked by MiniLM embeddings (always on).

    Args:
        jd_text: Raw job‑description text.
        top_n: Number of KeyBERT keyphrases to retrieve.
        include_static: Whether to add skills that match anywhere in the raw JD text.
        include_noun_chunks: Whether to add noun‑chunks that exactly match the lexicon.

    Returns:
        Set of lower‑cased keyword strings.
    """
    if not jd_text:
        return set()

    jd_lower = jd_text.lower()
    doc = nlp(jd_lower) if (include_static or include_noun_chunks) else None

    extracted: Set[str] = set()

    # -------------------------------------------------------------------
    # (1) Static lexicon matches anywhere in the JD
    # -------------------------------------------------------------------
    if include_static:
        extracted.update({kw for kw in KNOWN_SKILLS if kw in jd_lower})

    # -------------------------------------------------------------------
    # (2) Noun‑chunk exact lexicon matches
    # -------------------------------------------------------------------
    if include_noun_chunks and doc is not None:
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip().lower()
            if phrase in KNOWN_SKILLS:
                extracted.add(phrase)

    # -------------------------------------------------------------------
    # (3) KeyBERT contextual keyphrases
    # -------------------------------------------------------------------
    kb_phrases: List[tuple[str, float]] = kw_model.extract_keywords(
        jd_text,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        top_n=top_n,
    )
    extracted.update(phrase.lower() for phrase, _ in kb_phrases)

    return extracted


# ---------------------------------------------------------------------------
# Quick CLI sanity check (python -m jd_handler)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = (
        "We are seeking a backend engineer with strong Python, Flask, and AWS experience. "
        "Bonus points for Docker, CI/CD pipelines, and familiarity with React or JavaScript."
    )
    print("Detected keywords:", extract_keywords_from_jd(sample))
