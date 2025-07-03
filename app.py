from flask import Flask, request, render_template_string
import os
import logging
from datetime import datetime, timedelta

from jd_handler import extract_keywords_from_jd
from data_builder import create_candidates_df_with_ata
from email_fetch import fetch_cvs_with_static_jd
from config import (
    CV_FOLDER, FILTERED_FOLDER,
    ATA_SCORE_THRESHOLD,
    EMAIL_ADDRESS, EMAIL_PASSWORD
)

# === App & Logger ===
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === HTML Template ===
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CV Screening System</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Segoe UI', sans-serif; }
        .card { border-radius: 12px; }
        textarea.form-control { resize: vertical; }
        .table th { background-color: #007bff; color: white; }
        h2.card-title { font-weight: bold; color: #007bff; }
        .btn-primary { background-color: #007bff; border: none; }
    </style>
</head>
<body class="bg-light">
    <div class="container my-5">
        <div class="card shadow">
            <div class="card-body">
                <h2 class="card-title mb-4 text-center">CV Screening System</h2>
                <form method="post">
                    <div class="mb-3">
                        <label for="jd_text" class="form-label">Paste Job Description</label>
                        <textarea class="form-control" name="jd_text" rows="10" placeholder="Paste job description here..."></textarea>
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">Submit</button>
                    </div>
                </form>
                {{ feedback|safe }}
            </div>
        </div>
    </div>
</body>
</html>
"""


# === Core Logic ===
def fetch_and_screen_cvs(jd_keywords):
    since_date = (datetime.today() - timedelta(days=1)).strftime("%d-%b-%Y")

    logging.info("📥 Fetching CVs from email...")
    fetch_cvs_with_static_jd(EMAIL_ADDRESS, EMAIL_PASSWORD, since_date=since_date)
    logging.info("✅ Email fetch complete.")

    logging.info("🧠 Screening CVs...")
    df = create_candidates_df_with_ata(
        cv_folder=CV_FOLDER,
        jd_keywords=jd_keywords,
        filtered_folder=FILTERED_FOLDER,
        ata_score_threshold=ATA_SCORE_THRESHOLD,
        use_model=True
    )
    logging.info("✅ Screening complete.")

    return df


@app.route('/', methods=['GET', 'POST'])
def upload_jd():
    feedback = ""

    if request.method == 'POST':
        logging.info("📨 Form submitted from UI")
        jd_text = request.form.get('jd_text', '').strip()

        if not jd_text:
            feedback = "<div class='alert alert-danger mt-4'>⚠️ Job Description cannot be empty.</div>"
            return render_template_string(TEMPLATE, feedback=feedback)

        # === Keyword Extraction ===
        keywords = extract_keywords_from_jd(jd_text)
        if not keywords:
            feedback = "<div class='alert alert-danger mt-4'>❌ No useful keywords extracted. Check your JD content.</div>"
            return render_template_string(TEMPLATE, feedback=feedback)

        try:
            df = fetch_and_screen_cvs(keywords)

            if df.empty:
                feedback = "<div class='alert alert-warning mt-4'>⚠️ No candidates matched the given JD.</div>"
            else:
                filtered_df = df[df["ata_score"] >= 40]

                # Table Styling
                table_style = """
                <style>
                    .scroll-table { overflow-x: auto; white-space: nowrap; }
                    .scroll-table table {
                        table-layout: auto;
                        width: max-content;
                        min-width: 100%;
                    }
                    .scroll-table th, .scroll-table td {
                        white-space: nowrap;
                        vertical-align: middle;
                        font-size: 14px;
                        padding: 8px 16px;
                    }
                </style>
                """

                all_table_html = f"""
                {table_style}
                <div class="scroll-table mt-4">
                    <h4>🟦 All Candidates:</h4>
                    {df.to_html(classes='table table-bordered table-striped table-hover table-sm', index=False, escape=False)}
                </div>
                """

                filtered_table_html = f"""
                <div class="scroll-table mt-5">
                    <h4>✅ Filtered Candidates (ATA Score ≥ 40):</h4>
                    {filtered_df.to_html(classes='table table-bordered table-success table-sm', index=False, escape=False)}
                </div>
                """

                feedback = all_table_html + filtered_table_html

        except Exception as e:
            logging.error(f"❌ Exception during fetch/screening: {e}")
            feedback = f"<div class='alert alert-danger mt-4'>❌ Server error: {e}</div>"

    return render_template_string(TEMPLATE, feedback=feedback)


if __name__ == '__main__':
    app.run(debug=True)  # Note: disable debug in production!
