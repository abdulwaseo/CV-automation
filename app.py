from flask import Flask, request, render_template_string, send_file
import os
import logging
from datetime import datetime, timedelta
import zipfile
import io

from jd_handler import extract_keywords_from_jd
from data_builder import create_candidates_df_with_ata
from email_fetch import fetch_cvs_with_static_jd
from config import (
    CV_FOLDER, FILTERED_FOLDER,
    ATA_SCORE_THRESHOLD,
    EMAIL_ADDRESS, EMAIL_PASSWORD
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>CV Screening System</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css\" rel=\"stylesheet\">
  <style>
    body {
      background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
      color: #f8f9fa;
      font-family: 'Segoe UI', sans-serif;
      min-height: 100vh;
      padding-top: 100px;
    }

    .navbar-custom {
      background: linear-gradient(to right, #1e3c72, #2a5298);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
      border-bottom: 2px solid rgba(255, 255, 255, 0.2);
      padding: 1rem 2rem;
    }

    .navbar-brand {
      color: #fefefe;
      font-weight: 700;
      font-size: 2rem;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    .navbar-brand:hover {
      color: #a2d2ff;
    }

    .form-container {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
      border-radius: 20px;
      padding: 4rem;
      max-width: 1400px;
      width: 96%;
      margin: 70px auto;
      backdrop-filter: blur(12px);
    }

    .form-label {
      color: #dcdcdc;
      font-weight: 500;
    }

    .form-control,
    .input-group-text {
      background-color: rgba(255, 255, 255, 0.08);
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
    }

    .form-control::placeholder {
      color: #aaa;
    }

    .btn-purple {
      background: linear-gradient(to right, #8ec5fc, #e0c3fc);
      color: #1b263b;
      font-weight: bold;
      border: none;
      border-radius: 12px;
      transition: all 0.3s ease;
    }

    .btn-purple:hover {
      transform: scale(1.05);
      box-shadow: 0 0 18px rgba(255, 255, 255, 0.4);
    }

    .btn-download {
      margin-top: 1.5rem;
      border-radius: 10px;
      font-weight: 500;
    }

    .btn-success,
    .btn-secondary {
      background-color: #4db8ff;
      color: #012c2c;
      border: none;
    }

    .btn-success:hover,
    .btn-secondary:hover {
      transform: scale(1.05);
      box-shadow: 0 0 12px rgba(255,255,255,0.3);
    }

    .alert {
      margin-top: 1.5rem;
      border-radius: 12px;
    }

    .scroll-table {
      overflow-x: auto;
      white-space: nowrap;
    }

    .scroll-table table {
      background: linear-gradient(to right, #1b263b, #415a77);
      color: white;
      border-collapse: collapse;
      border-radius: 12px;
      overflow: hidden;
      width: 100%;
    }

    .scroll-table th {
      background-color: #233142;
      color: #ffffff;
      font-weight: 600;
      padding: 12px;
      text-align: center;
      border: 1px solid #4e6e81;
    }

    .scroll-table td {
      background-color: #2a3f54;
      color: white;
      padding: 10px 16px;
      border: 1px solid #4e6e81;
    }
  </style>
</head>
<body>
  <nav class=\"navbar navbar-expand-lg navbar-dark navbar-custom fixed-top\">
    <div class=\"container-fluid\">
      <a class=\"navbar-brand\" href=\"#\">⚡ CV Screening System</a>
    </div>
  </nav>

  <div class=\"form-container\">
    <form method=\"post\">
      <div class=\"mb-3\">
        <label for=\"jd_text\" class=\"form-label\">Paste Job Description</label>
        <textarea class=\"form-control\" name=\"jd_text\" rows=\"8\" placeholder=\"Paste job description here...\"></textarea>
      </div>
      <div class=\"mb-3\">
        <label for=\"ata_score\" class=\"form-label fw-bold\">Minimum ATA Score (%)</label>
        <div class=\"input-group\">
          <span class=\"input-group-text\">
            <i class=\"bi bi-bar-chart-fill\"></i>
          </span>
          <input type=\"number\" class=\"form-control\"
                 name=\"ata_score\" id=\"ata_score\" min=\"0\" max=\"100\" step=\"1\" value=\"40\"
                 placeholder=\"e.g. 40\">
        </div>
      </div>
      <div class=\"d-grid\">
        <button type=\"submit\" class=\"btn btn-purple">Submit</button>
      </div>
    </form>

    {{ feedback|safe }}

    {% if show_download %}
    <div class=\"text-center\">
      <a href=\"/download_filtered_cvs\" class=\"btn btn-success btn-download\">⬇️ Download Filtered CVs</a>
      <a href=\"/download_all_cvs\" class=\"btn btn-secondary btn-download\">📥 Download All CVs</a>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

def fetch_and_screen_cvs(jd_keywords, ata_score):
    since_date = (datetime.today() - timedelta(days=1)).strftime("%d-%b-%Y")
    logging.info("📥 Fetching CVs from email...")
    fetch_cvs_with_static_jd(EMAIL_ADDRESS, EMAIL_PASSWORD, since_date=since_date)
    logging.info("✅ Email fetch complete.")

    logging.info("🧠 Screening CVs...")
    df = create_candidates_df_with_ata(
        cv_folder=CV_FOLDER,
        jd_keywords=jd_keywords,
        filtered_folder=FILTERED_FOLDER,
        ata_score_threshold=ata_score,
        use_model=True
    )
    logging.info("✅ Screening complete.")
    return df


@app.route('/', methods=['GET', 'POST'])
def upload_jd():
    feedback = ""
    show_download = False

    if request.method == 'POST':
        logging.info("📨 Form submitted from UI")
        jd_text = request.form.get('jd_text', '').strip()
        ata_score_input = request.form.get('ata_score', '40').strip()

        if not jd_text:
            feedback = "<div class='alert alert-danger mt-4'>⚠️ Job Description cannot be empty.</div>"
            return render_template_string(TEMPLATE, feedback=feedback, show_download=show_download)

        try:
            ata_score = float(ata_score_input)
        except ValueError:
            ata_score = ATA_SCORE_THRESHOLD

        keywords = extract_keywords_from_jd(jd_text)
        if not keywords:
            feedback = "<div class='alert alert-danger mt-4'>❌ No useful keywords extracted. Check your JD content.</div>"
            return render_template_string(TEMPLATE, feedback=feedback, show_download=show_download)

        try:
            df = fetch_and_screen_cvs(keywords, ata_score)

            if df.empty:
                feedback = "<div class='alert alert-warning mt-4'>⚠️ No candidates matched the given JD.</div>"
            else:
                show_download = True
                filtered_df = df[df["ata_score"] >= ata_score]

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
                <div class='scroll-table mt-4'>
                    <h4>🟦 All Candidates:</h4>
                    {df.to_html(classes='table table-bordered table-striped table-hover table-sm', index=False, escape=False)}
                </div>
                """

                filtered_table_html = f"""
                <div class='scroll-table mt-5'>
                    <h4>✅ Filtered Candidates (ATA Score ≥ {ata_score}%):</h4>
                    {filtered_df.to_html(classes='table table-bordered table-success table-sm', index=False, escape=False)}
                </div>
                """

                feedback = all_table_html + filtered_table_html

        except Exception as e:
            logging.error(f"❌ Exception during fetch/screening: {e}")
            feedback = f"<div class='alert alert-danger mt-4'>❌ Server error: {e}</div>"

    return render_template_string(TEMPLATE, feedback=feedback, show_download=show_download)


@app.route("/download_filtered_cvs")
def download_filtered_cvs():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(FILTERED_FOLDER):
            filepath = os.path.join(FILTERED_FOLDER, filename)
            zip_file.write(filepath, arcname=filename)
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='filtered_cvs.zip'
    )


@app.route("/download_all_cvs")
def download_all_cvs():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(CV_FOLDER):
            filepath = os.path.join(CV_FOLDER, filename)
            zip_file.write(filepath, arcname=filename)
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='all_cvs.zip'
    )


if __name__ == '__main__':
    app.run(debug=True)
