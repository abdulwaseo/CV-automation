import os
import logging
from dotenv import load_dotenv

# === Load .env variables ===
load_dotenv()

# === Logging setup ===
logging.basicConfig(
    filename='cv_automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# === Email Credentials ===
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    logging.warning("⚠️ EMAIL_ADDRESS or EMAIL_PASSWORD not set in .env")

# === Folder Paths ===
BASE_DIR = os.path.dirname(__file__)
CV_FOLDER = os.path.join(BASE_DIR, "CVs")
FILTERED_FOLDER = os.path.join(BASE_DIR, "filtered_cvs")

# === Static JD Keywords (used when JD is not provided dynamically) ===
STATIC_JD_KEYWORDS = {
    "python", "sql", "java", "c++"
}

# === Matching & Filtering Parameters ===
ATA_SCORE_THRESHOLD = 30.0  # Min score to pass filtering
EMAIL_SUBJECT_KEYWORDS = ["CV", "Application"]  # Used in email_fetch filter
