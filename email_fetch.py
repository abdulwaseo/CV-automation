import os
import logging
import imapclient
import pyzmail
import ssl, certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())

from config import EMAIL_SUBJECT_KEYWORDS  # Optional: move subject filters to config

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}


def fetch_cvs_with_static_jd(email, password, folder='INBOX', since_date=None):
    """
    Connects to Gmail via IMAP, searches for emails containing CVs or Applications
    since the given date, downloads attachments with allowed extensions (.pdf/.docx),
    and saves them to the 'CVs' folder.

    Returns:
        List of saved filenames.
    """
    try:
        logger.info("📡 Connecting to Gmail IMAP...")
        server = imapclient.IMAPClient('imap.gmail.com', ssl=True, ssl_context=ssl_context)
        server.login(email, password)
        server.select_folder(folder, readonly=True)
        logger.info("✅ Logged in and folder selected.")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return []

    search_criteria = [
        'SINCE', since_date,
        'OR',
        ['SUBJECT', 'CV'],
        ['SUBJECT', 'Application']
    ]
    logger.info(f"🔍 Email search criteria: {search_criteria}")

    try:
        messages = server.search(search_criteria)
        logger.info(f"📬 Found {len(messages)} email(s) with CV/Application.")
    except Exception as e:
        logger.warning(f"⚠️ Email search failed: {e}")
        server.logout()
        return []

    os.makedirs("CVs", exist_ok=True)
    saved_files = []

    try:
        for msg_id, message_data in server.fetch(messages, ['RFC822']).items():
            message = pyzmail.PyzMessage.factory(message_data[b'RFC822'])

            for part in message.mailparts:
                filename = part.filename
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ALLOWED_EXTENSIONS:
                        unique_name = f"{msg_id}_{filename}"
                        cv_path = os.path.join("CVs", unique_name)
                        try:
                            with open(cv_path, 'wb') as f:
                                f.write(part.get_payload())
                            saved_files.append(unique_name)
                            logger.info(f"✅ Downloaded: {unique_name}")
                        except Exception as e:
                            print(f"Failed to save attachment: {filename}", e)
    except Exception as e:
        logger.error(f"❌ Failed while fetching attachments: {e}")

    if not saved_files:
        logger.warning("⚠️ No CVs downloaded.")
    else:
        logger.info(f"📂 CVs saved in 'CVs/' folder: {saved_files}")

    server.logout()
    return saved_files
