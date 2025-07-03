import re
from datetime import datetime
import spacy
import logging
from dateutil.relativedelta import relativedelta

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load spaCy model once
nlp = spacy.load("en_core_web_md")


def extract_name(text):
    """
    Extracts person's name using spaCy NER.
    """
    doc = nlp(text)
    for entity in doc.ents:
        if entity.label_ == "PERSON":
            name = entity.text.strip().split('\n')[0].strip()
            return name
    return "Unknown"


def extract_email(text):
    """
    Extracts the first email address found in the text.
    """
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return email.group(0) if email else ""


# Predefined keyword skill set
skill_list = [
    "Python", "Flask", "Django", "SQL", "AWS", "Project Management",
    "Data Analysis", "Recruiting", "HRIS", "Excel", "Machine Learning"
]

def extract_skills(text):
    """
    Extracts listed skills from the text using keyword matching.
    """
    found_skills = []
    for skill in skill_list:
        if re.search(rf'\b{re.escape(skill)}\b', text, re.IGNORECASE):
            found_skills.append(skill)
    return ", ".join(found_skills)


def extract_experience(text):
    """
    Estimates years of experience using multiple heuristics:
    1. Direct year mentions (e.g., "5+ years")
    2. Date ranges (e.g., 2018–2022 or 2015–present)
    3. Role-based clues if no duration is available

    Returns:
        float (years), 'N/A' for vague experience, or 0 if no info
    """
    try:
        text = " ".join(str(text).split()).lower()

        # Check if experience section exists
        experience_keywords = r'(?:^|\s)(work|employment|professional|experience)(?:\s*(?:history|background|section))?(?:\s|$)'
        has_experience_section = re.search(experience_keywords, text)

        # Match explicit year mentions
        year_pattern = r'(?<!\d)(?<!\w)(?:(?:over|about|approximately|around)\s+)?(\d{1,2}(?:\.\d{1,2})?)\+?\s*(?:years?|yrs?|yoe|y\/o)(?!\w)'
        year_matches = re.findall(year_pattern, text)

        valid_years = []
        for match in year_matches:
            try:
                years = float(match)
                if 0.5 <= years <= 50:
                    valid_years.append(years)
            except ValueError:
                continue

        if valid_years:
            return max(valid_years)

        # Match year ranges
        year_ranges = re.finditer(
            r'((?:19|20)\d{2})\s*[-–]\s*((?:19|20)\d{2}|present|current|now)(?:\s|$)',
            text
        )

        total_years = 0
        valid_ranges = 0
        current_year = datetime.now().year

        for match in year_ranges:
            try:
                start = int(match.group(1))
                end = match.group(2)
                end_year = current_year if end.lower() in ("present", "current", "now") else int(end)

                if 1900 <= start <= current_year and start <= end_year:
                    total_years += (end_year - start)
                    valid_ranges += 1
            except (ValueError, AttributeError):
                continue

        if valid_ranges > 0:
            avg_years = total_years / valid_ranges
            return round(avg_years, 1) if 0.5 <= avg_years <= 50 else None

        # If vague role clues exist
        if has_experience_section:
            position_pattern = r'(?:worked\s+as|position\s+of|role\s+as)\s+\w+'
            if re.search(position_pattern, text):
                return 'N/A'

        return 0

    except Exception as e:
        logger.error(f"❌ Error processing experience: {str(e)}")
        return None


def extract_education(text):
    """
    Extracts educational qualifications from the CV text.

    Filters lines that:
    - Match degree titles
    - Do not include work/skill-related keywords

    Returns:
        str: Semi-colon separated education lines
    """
    education_lines = []
    degree_keywords = r"\b(Bachelor(?:'s)?|Master(?:'s)?|Ph\.?D|MBA|BS|MS|B\.Sc|M\.Sc|B\.E|M\.E|BTech|MTech|Engineering|science)\b"
    bad_keywords = r"(developed|worked|created|experience|years|project|python|flask|skills|devops|api|certificate|certified|internship|team|training|graduation)"

    for line in text.split("\n"):
        line = line.strip().rstrip(".;")
        if len(line) < 15 or len(line) > 150:
            continue
        if re.search(degree_keywords, line, re.IGNORECASE) and not re.search(bad_keywords, line, re.IGNORECASE):
            education_lines.append(line)

    return "; ".join(education_lines)
