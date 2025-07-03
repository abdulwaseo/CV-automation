import os
import logging
import shutil
import pandas as pd
from datetime import datetime
from docx import Document
from pdfminer.high_level import extract_text

from extractors import (
    extract_name,
    extract_email,
    extract_skills,
    extract_experience,
    extract_education
)
from config import CV_FOLDER, FILTERED_FOLDER, STATIC_JD_KEYWORDS, ATA_SCORE_THRESHOLD

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.makedirs("rejected_cvs", exist_ok=True)  # Save rejected CVs separately


def extract_cv_text(filepath):
    """
    Extracts plain text from PDF or DOCX file.
    """
    try:
        if filepath.endswith('.pdf'):
            return extract_text(filepath)
        elif filepath.endswith('.docx'):
            doc = Document(filepath)
            return "\n".join(para.text for para in doc.paragraphs)
        else:
            logger.warning(f"⚠️ Unsupported file type: {filepath}")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to extract text from {filepath} - {e}")
        return None


def extract_cv_data(filepath):
    """
    Extracts structured fields from the CV using NLP and regex.
    """
    text = extract_cv_text(filepath)
    if not text:
        return None

    return {
        'name': extract_name(text),
        'email': extract_email(text),
        'skills': extract_skills(text),
        'experience': extract_experience(text),
        'education': extract_education(text),
        'text': text  # Needed for ML and scoring
    }


def create_candidates_df_with_ata(cv_folder=CV_FOLDER,
                                  jd_keywords=STATIC_JD_KEYWORDS,
                                  filtered_folder=FILTERED_FOLDER,
                                  ata_score_threshold=ATA_SCORE_THRESHOLD,
                                  use_model=True):
    """
    Processes CVs from the specified folder, extracts data, calculates ATA score,
    predicts ML score (if enabled), and saves results into a filtered folder.

    Returns:
        pd.DataFrame: Ranked candidate data
    """
    from ml_model import predict_suitability  # Avoid circular imports

    os.makedirs(filtered_folder, exist_ok=True)
    candidates = []

    for filename in os.listdir(cv_folder):
        if not filename.endswith(('.pdf', '.docx')):
            continue

        filepath = os.path.join(cv_folder, filename)
        data = extract_cv_data(filepath)

        if not data:
            logger.warning(f"⚠️ Skipping unreadable file: {filename}")
            continue

        # ATA Scoring
        cv_text = data['text'].lower()
        matched_keywords = [kw for kw in jd_keywords if kw.lower() in cv_text]
        matched_count = len(matched_keywords)
        total_keywords = len(jd_keywords)
        ata_score = round((matched_count / total_keywords) * 100, 1) if total_keywords > 0 else 0

        data.update({
            'filename': filename,
            'ata_score': ata_score,
            'matched_count': matched_count,
            'total_keywords': total_keywords,
            'matched_keywords': ", ".join(matched_keywords)
        })

        candidates.append(data)

        # Save or Reject CV
        if ata_score >= ata_score_threshold:
            shutil.copy(filepath, os.path.join(filtered_folder, filename))
            logger.info(f"✅ Matched (ATA Score: {ata_score}%) → {filename}")
        else:
            shutil.copy(filepath, os.path.join("rejected_cvs", filename))
            logger.info(f"🗄️ Archived (ATA Score: {ata_score}%) → {filename}")

    # ML Prediction (Optional)
    if use_model:
        all_texts = [c["text"].lower() for c in candidates if "text" in c]
        predictions = predict_suitability(all_texts)
        for i, pred in enumerate(predictions):
            candidates[i]["ml_score"] = round(pred * 100, 1)
    else:
        for c in candidates:
            c["ml_score"] = None

    # Final processing
    for c in candidates:
        if "text" in c:
            del c["text"]

    df = pd.DataFrame(candidates)
    if df.empty:
        logger.warning("⚠️ No valid CVs were matched after processing.")
        return df

    df["ata_score"] = pd.to_numeric(df["ata_score"], errors='coerce')
    df = df.sort_values(by="ata_score", ascending=False)
    df.drop_duplicates(subset=["email", "name"], inplace=True)
    df["education"] = df["education"].str.replace(";", "\n")

    # Column ordering
    expected_cols = [
        "filename", "name", "email", "skills", "experience", "education",
        "ata_score", "ml_score", "matched_count", "total_keywords", "matched_keywords"
    ]
    df = df[[col for col in expected_cols if col in df.columns]]

    logger.info(f"📊 Summary: {len(candidates)} CVs processed, {len(df)} matched and saved.")
    return df
