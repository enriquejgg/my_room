import os
import io
import time
import threading
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_session import Session
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# Seconds before an undeleted CV is purged automatically after download.
CV_MAX_AGE_SECONDS = 300   # 5 minutes

UPLOAD_FOLDER = "uploads"
SESSION_DIR   = "./flask_session/"

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "super_secret_key"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"]      = "filesystem"
app.config["SESSION_FILE_DIR"]  = SESSION_DIR
Session(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SESSION_DIR,   exist_ok=True)

client = OpenAI()

# ─────────────────────────────────────────────
# SERVER-SIDE AUTO-PURGE  (two independent layers)
# ─────────────────────────────────────────────

def _delete_file(filepath: str) -> None:
    """Delete a file from disk; silently ignore any errors."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass


def _sweep_stale_uploads() -> None:
    """
    Background daemon — Layer 1 (filesystem sweep).

    Runs every 60 seconds.  Deletes any file in the uploads folder whose
    last-modification time is older than CV_MAX_AGE_SECONDS.

    This is the last-resort safety net for CVs left behind when users close
    the browser tab without interacting with the deletion modal.
    """
    while True:
        try:
            cutoff = time.time() - CV_MAX_AGE_SECONDS
            for fname in os.listdir(UPLOAD_FOLDER):
                fpath = os.path.join(UPLOAD_FOLDER, fname)
                if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                    _delete_file(fpath)
        except Exception:
            pass
        time.sleep(60)


# Start background sweep as a daemon thread (dies automatically with the process)
threading.Thread(target=_sweep_stale_uploads, daemon=True).start()


@app.before_request
def _auto_purge_on_request():
    """
    Request-time auto-purge — Layer 2 (session check).

    On every incoming request, if this session holds a downloaded CV whose
    download timestamp is older than CV_MAX_AGE_SECONDS, purge it immediately.

    Catches users who are still on the page but have not responded to the
    mandatory modal within 5 minutes.
    """
    download_time = session.get("download_time")
    cv_filepath   = session.get("cv_filepath")

    if download_time and cv_filepath:
        if (time.time() - download_time) > CV_MAX_AGE_SECONDS:
            _delete_file(cv_filepath)
            session.pop("cv_filepath",   None)
            session.pop("download_time", None)


# ─────────────────────────────────────────────
# ROUTES — PAGES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    """Landing page: CV upload + job description input."""
    return render_template("index.html")


@app.route("/chat_page")
def chat_page():
    """Chat interface. Redirects home if session is missing required data."""
    if "cv_text" not in session or "job_text" not in session:
        return redirect(url_for("home"))
    return render_template("chat.html")


# ─────────────────────────────────────────────
# ROUTES — API
# ─────────────────────────────────────────────

@app.route("/initialize", methods=["POST"])
def initialize():
    """
    Receives the uploaded CV (PDF) and job description (text or URL).
    Extracts CV text, optionally scrapes the job URL, stores everything in
    the session, and returns {"status": "ready"}.
    """
    file     = request.files.get("cv")
    job_text = request.form.get("job_text", "").strip()
    job_url  = request.form.get("job_url",  "").strip()

    if not file:
        return jsonify({"error": "CV is required."})

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        reader  = PdfReader(filepath)
        cv_text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                cv_text += content
    except Exception as e:
        return jsonify({"error": f"Error reading PDF: {str(e)}"})

    if job_url:
        try:
            r    = requests.get(job_url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            job_text = soup.get_text(separator=" ")
        except Exception:
            return jsonify({"error": "Could not fetch job URL."})

    if not job_text:
        return jsonify({"error": "Job description is required."})

    session.clear()
    session["cv_text"]     = cv_text
    session["job_text"]    = job_text
    session["cv_filepath"] = filepath   # preserved for deletion

    intro_msg = (
        "Hello! I'm Trav. I've analysed your CV and the job description. "
        "To write the best cover letter, could you tell me about your availability "
        "and why you're interested in this specific role?"
    )
    session["chat_history"] = [{"role": "assistant", "content": intro_msg}]
    return jsonify({"status": "ready"})


@app.route("/chat", methods=["POST"])
def chat():
    """
    Main conversation endpoint.
    Appends the user message, calls GPT-4o-mini, returns the reply.
    """
    if "cv_text" not in session:
        return jsonify({"reply": "Session expired. Please upload your documents again."})

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please type a message."})

    chat_history = session.get("chat_history", [])
    chat_history.append({"role": "user", "content": user_message})

    system_prompt = (
        "You are Trav, a professional cover letter assistant. "
        "Your goal is to interview the candidate to gather all the details needed "
        "for a perfect, personalised cover letter. "
        "Ask about: recent relevant experience, specific training or certifications, "
        "languages spoken, availability, salary expectations if relevant, and motivation. "
        "Once you have gathered enough information, produce a complete, polished cover letter "
        "addressed to the hiring manager. "
        "When you write the cover letter, output ONLY the letter — no commentary before or after it. "
        "Start the letter with the candidate's name block, then the date, then the recipient block, "
        "then the body paragraphs, then a closing."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"CANDIDATE CV:\n{session['cv_text']}"},
        {"role": "system", "content": f"JOB DESCRIPTION:\n{session['job_text']}"},
    ] + chat_history

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Sorry, I encountered an error: {str(e)}"

    chat_history.append({"role": "assistant", "content": reply})
    session["chat_history"] = chat_history
    session["last_letter"]  = reply
    return jsonify({"reply": reply})


@app.route("/download_letter_pdf")
def download_letter_pdf():
    """
    Extracts the cover letter from the conversation, renders a clean A4 PDF,
    streams it to the browser, and records the download timestamp so both
    server-side auto-purge layers and the frontend countdown can fire.
    """
    if "chat_history" not in session:
        return "Session expired. Please start a new session.", 400

    chat_history = session.get("chat_history", [])

    # ── Extract the cover letter text via AI ─────────────────────────────────
    extraction_prompt = (
        "Below is a conversation between a job applicant and a cover letter assistant. "
        "Identify the most recent, complete cover letter and return IT AND NOTHING ELSE. "
        "No preamble, no explanation, no closing remark — just the letter. "
        "If no letter exists yet, respond with exactly: NO_LETTER_YET\n\n"
        "CONVERSATION:\n"
        + "\n".join(f"[{m['role'].upper()}]: {m['content']}" for m in chat_history)
    )

    try:
        extraction  = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0,
        )
        letter_text = extraction.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not extract cover letter: {str(e)}", 500

    if letter_text == "NO_LETTER_YET":
        return (
            "No cover letter has been generated yet. "
            "Please continue your conversation with Trav until a full letter is produced.",
            400,
        )

    # ── Build clean A4 PDF with ReportLab ────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=3*cm, rightMargin=3*cm, topMargin=3*cm, bottomMargin=3*cm,
    )
    styles     = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "CoverLetterBody", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11, leading=16,
        alignment=TA_JUSTIFY, spaceAfter=10,
    )
    story = []
    for line in letter_text.splitlines():
        if line.strip():
            safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            story.append(Paragraph(safe, body_style))
        else:
            story.append(Spacer(1, 0.4*cm))

    doc.build(story)
    buf.seek(0)

    # ── Record download time — starts both auto-purge timers ─────────────────
    session["download_time"] = time.time()

    return send_file(buf, as_attachment=True,
                     download_name="Cover_Letter.pdf", mimetype="application/pdf")


# ─────────────────────────────────────────────
# UTILITY ROUTES
# ─────────────────────────────────────────────

@app.route("/has_letter")
def has_letter():
    """
    Returns {"has_letter": bool}.
    Used by the frontend to enable the download button after a letter appears.
    """
    history        = session.get("chat_history", [])
    last_assistant = next(
        (m["content"] for m in reversed(history) if m["role"] == "assistant"), ""
    )
    return jsonify({"has_letter": len(last_assistant) > 300})


@app.route("/cv_status")
def cv_status():
    """
    Returns the current CV deletion state so the frontend modal can sync its
    countdown with the server clock — important on page refresh after a download.

    Fields:
      cv_present     — bool
      already_purged — bool
      download_time  — Unix timestamp or null
      seconds_left   — int seconds until auto-purge, or null
    """
    cv_filepath   = session.get("cv_filepath")
    download_time = session.get("download_time")

    if not cv_filepath:
        return jsonify({"cv_present": False, "already_purged": True,
                        "download_time": None, "seconds_left": None})

    if download_time is None:
        return jsonify({"cv_present": True, "already_purged": False,
                        "download_time": None, "seconds_left": None})

    seconds_left = max(0, int(CV_MAX_AGE_SECONDS - (time.time() - download_time)))
    return jsonify({
        "cv_present":     True,
        "already_purged": False,
        "download_time":  download_time,
        "seconds_left":   seconds_left,
    })


@app.route("/purge_cv", methods=["POST"])
def purge_cv():
    """
    Deletes the uploaded CV file from disk.
    Idempotent — calling it multiple times is safe.

    Returns {"status": "deleted" | "already_gone" | "error"}.
    """
    filepath = session.get("cv_filepath")
    if not filepath:
        return jsonify({"status": "already_gone"})

    try:
        _delete_file(filepath)
        session.pop("cv_filepath",   None)
        session.pop("download_time", None)
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@app.route("/reset")
def reset():
    """
    Clears the session and returns to the landing page.
    Deletes any CV file that was not already purged.
    """
    _delete_file(session.get("cv_filepath"))
    session.clear()
    return redirect(url_for("home"))


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)