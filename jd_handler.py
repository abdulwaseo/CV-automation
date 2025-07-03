import spacy
import logging

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load SpaCy model
import spacy.cli

try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    spacy.cli.download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")


# Predefined skill keywords
KNOWN_SKILLS = {
    "python", "java", "c++", "sql", "flask", "django", "aws",
    "excel", "linux", "javascript", "machine learning", "react",
    "docker", "git", "cloud", "data analysis"
}


def load_jd_text(filepath):
    """
    Loads and returns the text content from a Job Description (JD) file.

    Args:
        filepath (str): Path to the JD text file

    Returns:
        str: JD content as string, or empty string on failure
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"❌ Failed to load JD file: {e}")
        return ""


def extract_keywords_from_jd(jd_text):
    """
    Extracts relevant skill keywords from the JD text using SpaCy.

    Args:
        jd_text (str): Raw text of job description

    Returns:
        set: Set of matched known skills
    """
    doc = nlp(jd_text.lower())
    keywords = set()

    for token in doc:
        if token.is_alpha and not token.is_stop and 3 <= len(token.text) <= 20:
            lemma = token.lemma_
            if lemma in KNOWN_SKILLS:
                keywords.add(lemma)

    return keywords
