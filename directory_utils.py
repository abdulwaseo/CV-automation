import os
import shutil
import time
import logging

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Configuration flags ===
CLEAN_BEFORE_RUN = True         # Delete previous CVs before run
ARCHIVE_OLD_FILTERED = True     # Backup filtered CVs before deletion


def manage_directories(cv_folder="CVs", filtered_folder="filtered_cvs"):
    """
    Prepares necessary directories for CV processing.

    Actions:
    - Removes old CVs if CLEAN_BEFORE_RUN is True
    - Archives previous filtered CVs if ARCHIVE_OLD_FILTERED is True
    - Recreates empty 'CVs' and 'filtered_cvs' folders

    Args:
        cv_folder (str): Folder where CVs are stored temporarily
        filtered_folder (str): Folder for shortlisted CVs

    Returns:
        Optional[str]: Archive folder path (if created), else None
    """
    archive_path = None

    # === Handle CV Folder ===
    if CLEAN_BEFORE_RUN:
        if os.path.exists(cv_folder):
            shutil.rmtree(cv_folder)
            logger.info(f"🧹 Cleaned old CV folder: {cv_folder}")
        os.makedirs(cv_folder)
        logger.info(f"📁 Created new CV folder: {cv_folder}")
    else:
        os.makedirs(cv_folder, exist_ok=True)

    # === Handle Filtered Folder ===
    if os.path.exists(filtered_folder):
        if ARCHIVE_OLD_FILTERED:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            archive_path = f"{filtered_folder}_{timestamp}"
            shutil.copytree(filtered_folder, archive_path)
            logger.info(f"📦 Archived old filtered CVs to: {archive_path}")
        shutil.rmtree(filtered_folder)
        logger.info(f"🗑️ Removed old filtered folder: {filtered_folder}")

    os.makedirs(filtered_folder)
    logger.info(f"📁 Created new filtered folder: {filtered_folder}")

    return archive_path
