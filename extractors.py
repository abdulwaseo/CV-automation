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
    # Programming Languages
    "Python", "Java", "C", "C++", "C#", "JavaScript", "TypeScript",
    "Ruby", "Go", "R", "PHP", "Swift", "Kotlin", "Perl", "Scala",
    "Rust", "Shell Scripting", "Bash", "MATLAB", "HTML", "CSS", "SQL",

    # Frameworks & Libraries
    "Flask", "Django", "FastAPI", "Spring Boot", "React", "Angular", "Vue.js",
    "Next.js", "Express.js", "jQuery", "Bootstrap", "Tailwind CSS",
    "TensorFlow", "Keras", "PyTorch", "Scikit-learn", "NLTK", "OpenCV",
    "Hugging Face", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",

    # Databases
    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server",
    "MariaDB", "Redis", "Cassandra", "Firebase", "Elasticsearch", "BigQuery",

    # Cloud Platforms & Services
    "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP", "DigitalOcean",
    "Heroku", "Firebase", "Cloudflare", "Netlify", "Docker", "Kubernetes",
    "Terraform", "Ansible", "Jenkins", "CI/CD", "Serverless", "S3", "EC2",
    "Lambda", "Cloud Functions", "Kinesis", "CloudWatch", "Route 53", "VPC",

    # DevOps & Tools
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Trello", "Slack",
    "Postman", "Figma", "VS Code", "IntelliJ", "PyCharm", "Eclipse", "Notion",
    "Linux", "Unix", "Zsh", "Apache", "Nginx", "GraphQL", "REST API",
    "SOAP", "Webpack", "Babel", "Agile", "Scrum", "Kanban", "CI/CD",

    # Data Science & Analytics
    "Data Analysis", "Data Visualization", "Data Cleaning", "Data Wrangling",
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "AI",
    "Predictive Modeling", "Clustering", "Classification", "Regression",
    "NLP", "Natural Language Processing", "EDA", "Business Intelligence",
    "Power BI", "Tableau", "Looker", "Excel", "Advanced Excel", "Google Sheets",
    "Statistical Analysis", "A/B Testing", "Time Series", "Big Data", "Hadoop",
    "Spark", "ETL", "Data Engineering",

    # Cybersecurity & Networking
    "Cybersecurity", "Network Security", "Penetration Testing", "VAPT",
    "Firewalls", "Wireshark", "VPN", "IDS", "IPS", "OWASP", "SSL", "TLS",

    # Soft Skills & Other
    "Project Management", "Leadership", "Team Management", "Recruiting",
    "Communication", "Critical Thinking", "Problem Solving", "Creativity",
    "Negotiation", "Adaptability", "Time Management", "Conflict Resolution",
    "Decision Making", "Teamwork", "Collaboration", "Presentation", "Public Speaking",

    # HR & Business
    "HRIS", "HR Analytics", "Talent Acquisition", "Compensation", "Payroll",
    "ATS", "Onboarding", "Employee Engagement", "Learning and Development",
    "Business Strategy", "Market Research", "Salesforce", "CRM", "ERP",
    "SAP", "Zoho", "HubSpot", "Excel Macros", "Pivot Tables"
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

def extract_education(text: str) -> str:
    """
    Extract degree lines; skips lines with bad or informal keywords.
    """
    degree_keywords = re.compile(r"""
        \b(
            Bachelor(?:'s)?\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology)? |
            Master(?:'s)?\s+(?:of\s+)?(?:Science|Arts|Engineering|Technology)? |
            B(?:\.|achelor)?\s?(?:Sc|A|E|Tech|IT|Eng)? |
            M(?:\.|aster)?\s?(?:Sc|A|E|Tech|IT|Eng)? |
            Ph\.?D |
            MBA |
            B\.?Sc | M\.?Sc | BSc | MSc |
            B\.?E | M\.?E | BTech | MTech |
            BS | MS |
            Information\s+Technology |
            Computer\s+Science | Software | Science
        )\b
    """, re.I | re.VERBOSE)

    bad_keywords = re.compile(r"""
        \b(
            developed | worked | created | designed | implemented |
            experience | years | project | built |
            python | java | flask | django | react | node |
            skills | devops | api | rest | fastapi | graphql |
            certificate | certified | certification |
            internship | team | collaboration | scrum | agile |
            graduation | education | training | deployment |
            cloud | aws | azure | gcp | docker | kubernetes |
            seminar | attended | workshop | bootcamp | course | short\s+course | webinar |
            i\s+think | don't\s+remember | clutch | master | god | lol |
            haha | kinda | maybe | unsure | don't\s+know | no\s+idea |
            guess | random | fake | test | References | continuing | ongoing 
        )\b
    """, re.I | re.VERBOSE)

    results = []
    for line in text.splitlines():
        line = line.strip().rstrip(".;")
        if 15 <= len(line) <= 150 \
           and degree_keywords.search(line) \
           and not bad_keywords.search(line):
            results.append(line)

    return "; ".join(results)
