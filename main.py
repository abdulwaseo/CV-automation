import logging
from datetime import datetime, timedelta
from time import time
import os
import sys

from config import (
    EMAIL_ADDRESS, EMAIL_PASSWORD,
    ATA_SCORE_THRESHOLD,
    CV_FOLDER, FILTERED_FOLDER
)
from email_fetch import fetch_cvs_with_static_jd
from data_builder import create_candidates_df_with_ata
from directory_utils import manage_directories
from jd_handler import load_jd_text, extract_keywords_from_jd


def run_pipeline():
    start_time = time()
    logging.info("🚀 CV Automation Pipeline Started")

    # === Step 0: Clean folders ===
    manage_directories(cv_folder=CV_FOLDER, filtered_folder=FILTERED_FOLDER)

    # === Step 1: Fetch CVs from email ===
    try:
        since_date = (datetime.today() - timedelta(days=14)).strftime("%d-%b-%Y")
        fetch_cvs_with_static_jd(
            EMAIL_ADDRESS, EMAIL_PASSWORD, since_date=since_date
        )
    except Exception as e:
        logging.error(f"❌ Failed to fetch CVs via IMAP: {e}")

    # === Step 2: Load JD and extract keywords ===
    GENERIC_STOPWORDS = {
        "cloud", "backend", "frontend", "software", "development",
        "technology", "engineering", "team", "project", "experience"
    }
    jd_path = os.path.join(os.path.dirname(__file__), "jd.txt")
    jd_text = load_jd_text(jd_path)
    jd_keywords = extract_keywords_from_jd(jd_text)
    jd_keywords = {kw for kw in jd_keywords if kw not in GENERIC_STOPWORDS}
    if not jd_keywords:
        logging.error("❌ No keywords extracted from jd.txt. Check file content.")
        sys.exit("❌ No keywords found in JD. Terminating.")

    # === Step 3: Process CVs and rank ===
    try:
        df = create_candidates_df_with_ata(
            cv_folder=CV_FOLDER,
            jd_keywords=jd_keywords,
            filtered_folder=FILTERED_FOLDER,
            ata_score_threshold=ATA_SCORE_THRESHOLD,
            use_model=True
        )
    except Exception as e:
        logging.error(f"❌ Failed during CV processing: {e}")
        df = None

    # === Step 4: Display or Save Output ===
    if df is None or df.empty:
        msg = "⚠️ No candidates matched or no CVs were processed."
        logging.warning(msg)
        print("\n" + msg)
    else:
        df["ata_score"] = df["ata_score"].astype(str) + "%"
        df.to_csv("filtered.csv", index=False)
        output_path = os.path.abspath("filtered.csv")
        logging.info(f"✅ Results saved to filtered.csv at {output_path}")

        print(f"\n✅ Extracted CV Information with Ranking:\n")
        print(df[["name", "email", "ata_score", "matched_keywords"]])
        print(f"\n📁 Saved filtered.csv to: {output_path}")

    end_time = time()
    duration = round(end_time - start_time, 2)
    logging.info(f"✅ Pipeline Completed in {duration} seconds")


if __name__ == "__main__":
    run_pipeline()
