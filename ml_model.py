# ml_model.py

import os
import joblib
import logging

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Paths to model and vectorizer ===
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "ml_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "models", "tfidf_vectorizer.pkl")


def load_model_and_vectorizer():
    """
    Loads the trained ML model and its corresponding TF-IDF vectorizer.

    Returns:
        model: Trained scikit-learn model
        vectorizer: TF-IDF vectorizer

    Raises:
        FileNotFoundError or joblib loading errors
    """
    try:
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        return model, vectorizer
    except Exception as e:
        logger.error(f"❌ Failed to load ML model/vectorizer: {e}")
        raise


def predict_suitability(cv_texts):
    """
    Predicts suitability score (probability) for each CV using the ML model.

    Args:
        cv_texts (List[str]): Preprocessed CV texts

    Returns:
        List[float]: Probabilities for positive class (suitability)
    """
    model, vectorizer = load_model_and_vectorizer()
    X = vectorizer.transform(cv_texts)
    predictions = model.predict_proba(X)[:, 1]  # probability for class 1
    return predictions
