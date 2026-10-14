"""
FraudShield — Flask API Backend
React (Vite) handles the frontend; Flask exposes /api/* endpoints only.
"""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import (
    SECRET_KEY, DEBUG, UPLOAD_FOLDER, MAX_CONTENT_LENGTH,
    ALLOWED_EXTENSIONS
)
from utils.database import init_db, save_analysis, get_all_analyses, get_analysis_by_id, get_stats
from utils.risk_scorer import build_summary
from utils.pdf_generator import generate_pdf

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, UPLOAD_FOLDER)
# Allow all origins in dev; tighten in production
CORS(app, resources={r"/api/*": {"origins": "*"}})

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
PDF_DIR = os.path.join(app.root_path, "reports")
os.makedirs(PDF_DIR, exist_ok=True)

# ── DB ─────────────────────────────────────────────────────────────────────────
engine, Session = init_db(app)


# ── Helpers ────────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_uploaded_file(file) -> str:
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(path)
    return path


# ── API Routes only — React handles all page routing ────────────────────────────


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.route("/api/analyze/text", methods=["POST"])
def api_analyze_text():
    try:
        data = request.get_json(force=True)
        message = (data or {}).get("message", "").strip()
        if not message:
            return jsonify({"error": "No message provided"}), 400

        from models.text_analyzer import analyze_text
        result = analyze_text(message)
        result = build_summary(result)
        saved = save_analysis(Session, result)
        return jsonify({"success": True, "analysis": saved, "redirect": f"/result/{saved['id']}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/url", methods=["POST"])
def api_analyze_url():
    try:
        data = request.get_json(force=True)
        url = (data or {}).get("url", "").strip()
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        from models.url_analyzer import analyze_url
        result = analyze_url(url)
        result = build_summary(result)
        saved = save_analysis(Session, result)
        return jsonify({"success": True, "analysis": saved, "redirect": f"/result/{saved['id']}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/image", methods=["POST"])
def api_analyze_image():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        file_path = _save_uploaded_file(file)

        from models.image_analyzer import analyze_image
        result = analyze_image(file_path)
        result = build_summary(result)
        saved = save_analysis(Session, result)
        return jsonify({"success": True, "analysis": saved, "redirect": f"/result/{saved['id']}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/qr", methods=["POST"])
def api_analyze_qr():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        file_path = _save_uploaded_file(file)

        from models.qr_analyzer import analyze_qr
        result = analyze_qr(file_path)
        result = build_summary(result)
        saved = save_analysis(Session, result)
        return jsonify({"success": True, "analysis": saved, "redirect": f"/result/{saved['id']}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/report/<int:record_id>", methods=["GET"])
def api_generate_report(record_id):
    """Generate and download PDF report for an analysis."""
    try:
        record = get_analysis_by_id(Session, record_id)
        if not record:
            return jsonify({"error": "Analysis not found"}), 404

        pdf_path = generate_pdf(record, PDF_DIR)

        # Update DB with PDF path
        from utils.database import AnalysisRecord
        session = Session()
        try:
            db_rec = session.query(AnalysisRecord).filter_by(id=record_id).first()
            if db_rec:
                db_rec.pdf_path = pdf_path
                session.commit()
        finally:
            session.close()

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"FraudShield_Report_{record_id}.pdf",
            mimetype="application/pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    records = get_all_analyses(Session, limit=100)
    stats = get_stats(Session)
    return jsonify({"records": records, "stats": stats})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(get_stats(Session))


@app.route("/api/analysis/<int:record_id>", methods=["GET"])
def api_get_analysis(record_id):
    record = get_analysis_by_id(Session, record_id)
    if not record:
        return jsonify({"error": "Not found"}), 404
    return jsonify(record)


# ── Error Handlers ──────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum 16 MB allowed."}), 413


# ── Init files ─────────────────────────────────────────────────────────────────
def create_init_files():
    for d in ["models", "utils"]:
        init_path = os.path.join(app.root_path, d, "__init__.py")
        if not os.path.exists(init_path):
            open(init_path, "w").close()


if __name__ == "__main__":
    create_init_files()
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)
