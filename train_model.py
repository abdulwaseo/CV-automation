"""
train_model.py

Trains a logistic regression model to predict CV suitability using
ATA score–based labels and saves the model + TF-IDF vectorizer.

Output:
- models/ml_model.pkl
- models/tfidf_vectorizer.pkl
"""

import os
import joblib
import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from data_builder import extract_cv_text
from config import CV_FOLDER

# === Setup logging ===
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Parameters ===
ATA_THRESHOLD = 40.0
STATIC_JD_KEYWORDS = {
    "python", "sql", "java", "c++", "django", "flask", "aws", "machine learning"
}
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def calculate_ata_score(text):
    """
    Calculates ATA (Application Text Analysis) score based on static JD keywords.
    """
    text = text.lower()
    matched = sum(1 for kw in STATIC_JD_KEYWORDS if kw in text)
    total = len(STATIC_JD_KEYWORDS)
    return (matched / total) * 100 if total > 0 else 0


def load_cvs_and_labels():
    """
    Loads CVs from the CV_FOLDER, assigns binary labels based on ATA score.
    Returns:
        - texts: List of extracted CV text
        - labels: List of 0/1 labels
    """
    texts = []
    labels = []

    for filename in os.listdir(CV_FOLDER):
        if filename.endswith(('.pdf', '.docx')):
            filepath = os.path.join(CV_FOLDER, filename)
            text = extract_cv_text(filepath)
            if not text:
                continue
            ata_score = calculate_ata_score(text)
            label = 1 if ata_score >= ATA_THRESHOLD else 0
            texts.append(text)
            labels.append(label)

    return texts, labels


def train_model():
    """
    Trains the logistic regression model and saves the artifacts.
    """
    texts, labels = load_cvs_and_labels()

    if not texts:
        logger.error("❌ No valid CVs found for training.")
        return

    # === Train/Test Split ===
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    # === TF-IDF Vectorization ===
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # === Logistic Regression ===
    model = LogisticRegression(max_iter=500)
    model.fit(X_train_vec, y_train)

    # === Evaluation ===
    y_pred = model.predict(X_test_vec)
    report = classification_report(y_test, y_pred)
    logger.info("📊 Classification Report:\n%s", report)

    # === Save Model & Vectorizer ===
    joblib.dump(model, os.path.join(MODEL_DIR, "ml_model.pkl"))
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
    logger.info("✅ Model and vectorizer saved to 'models/' folder.")


if __name__ == "__main__":
    train_model()
