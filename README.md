# 📄 CV Screening System (Flask + ML)

[🔗 View Project on GitHub](https://github.com/abdulwaseo/CV-automation)

This project automates the process of screening CVs by...

- Fetching CVs from Gmail
- Matching keywords from the Job Description
- Ranking candidates using a Machine Learning model
- Showing results in a web interface built with Flask

---

## 🚀 Features

- 📨 Email-based CV fetching (.pdf/.docx)
- 🔍 JD keyword matching (ATA Score)
- 🤖 ML model for smart ranking (Logistic Regression)
- 🌐 Web UI with Flask for HR usage
- 📊 Output saved to `filtered.csv`

---

## ⚙️ Installation

1. Clone the repo:
```bash
git clone https://github.com/yourusername/cv-automation.git
cd cv-automation
```

2. Create .env file:
```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```
▶️ Usage

CLI Mode:
```bash
python main.py
```
Web App:
```bash
python app.py
```
Visit: http://127.0.0.1:5000

📁 File Structure
CV_automation/
├── app.py
├── main.py
├── email_fetch.py
├── data_builder.py
├── extractors.py
├── ml_model.py
├── train_model.py
├── config.py
├── jd_handler.py
├── .env.example
├── requirements.txt
├── README.md

🤖 Model Info

ML model trained on ATA-score-based logic
Model files:
models/ml_model.pkl
models/tfidf_vectorizer.pkl
Retrain using:
```bash
python train_model.py
```
🧪 Requirements

Python 3.8+
en_core_web_md spaCy model
```bash
python -m spacy download en_core_web_md
```

Made by Abdul Waseo
