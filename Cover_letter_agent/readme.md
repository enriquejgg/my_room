# Trav — AI Cover Letter Assistant

Trav is a Flask web application that helps job candidates write personalised cover letters.
It reads the candidate's CV and a target job description, holds a guided conversation to gather
extra context, and produces a polished, downloadable cover letter PDF.

---

## Features

- **CV parsing** — upload a PDF; text is extracted automatically with PyPDF2
- **Job description input** — paste text directly or supply a URL (Trav scrapes it)
- **Guided interview** — GPT-4o-mini plays the role of Trav and asks targeted questions
- **Clean PDF export** — only the cover letter text is included; chat history is stripped
- **Mandatory CV deletion** — a blocking modal requires the user to confirm CV deletion after download
- **Three-layer auto-purge** — if the user does not confirm within 5 minutes, the CV is deleted automatically

---

## Project Structure

```
.
├── app.py              # Flask backend — routes, AI calls, auto-purge logic
├── requirements.txt    # Python dependencies
├── templates/
│   ├── index.html      # Landing page: CV upload + job description form
│   └── chat.html       # Chat interface and deletion modal
├── static/
│   └── style.css       # Shared styles for both pages
├── uploads/            # Temporary CV storage (auto-created at startup)
├── flask_session/      # Server-side session files (auto-created at startup)
└── chat_history.json   # Seed prompt for a separate travel bot ("Iter") — not used by Trav
```

---

## Prerequisites

- Python 3.9+
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/trav.git
cd trav
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate.bat     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."        # macOS / Linux
$env:OPENAI_API_KEY = "sk-..."        # Windows PowerShell
```

Or add it to a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

### 5. Run the app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

---

## How It Works

### Step 1 — Upload (`/` → `/initialize`)

1. The user uploads their CV as a PDF and provides a job description (text or URL).
2. `/initialize` extracts the CV text with **PyPDF2** and optionally scrapes the job URL with
   **BeautifulSoup**.
3. Both texts are stored in a server-side session alongside an empty chat history.
4. The CV file path is saved in the session (`session["cv_filepath"]`) so it can be deleted later.

### Step 2 — Chat (`/chat_page` → `/chat`)

1. Every user message is sent to `/chat`, which prepends the CV and job description as system
   context and calls **GPT-4o-mini**.
2. The full conversation history is maintained in the session and sent with every request.
3. After each assistant reply, the frontend polls `/has_letter` to check whether a cover letter
   has been produced (heuristic: last assistant message > 300 characters).

### Step 3 — Download (`/download_letter_pdf`)

1. The full chat history is sent to GPT-4o-mini with a strict extraction prompt:
   *"Return only the most recent complete cover letter — nothing else."*
2. The extracted text is rendered as a clean **A4 PDF** (Times-Roman 11pt, justified,
   3 cm margins, section spacing preserved).
3. The server records `session["download_time"] = time.time()` — this timestamp starts all
   three auto-purge layers simultaneously.

### Step 4 — Mandatory deletion modal

Immediately after the PDF download completes, a **full-screen blocking modal** appears:

- It **cannot be dismissed** — there is no X button and clicking outside does nothing.
- It shows a **circular 5-minute countdown** that ticks in real time.
- The only action available is **"OK — Delete my CV now"**, which calls `POST /purge_cv`.
- If the user refreshes the page before deleting, the modal reappears and the countdown
  resumes from wherever the server clock says it is (via `/cv_status`).

---

## Three-Layer Auto-Purge

If the user does not click the confirmation button, the CV is deleted automatically by
three independent mechanisms, each acting as a fallback for the previous one.

### Layer 1 — Frontend countdown (client-side timer)

A JavaScript `setInterval` counts down from 5:00 in the modal. When it reaches 0:00 it
automatically calls `POST /purge_cv`, updates the modal to read *"CV deleted automatically"*,
and shows a close button.

**Covers:** users who are looking at the screen but ignoring the modal.

### Layer 2 — `before_request` hook (request-time session check)

On every Flask request, the `_auto_purge_on_request` function checks whether
`session["download_time"]` is set and whether `time.time() - download_time > 300`.
If both are true, the file is deleted from disk and the session keys are cleared.

**Covers:** users who are still interacting with the page (typing, scrolling) but have not
clicked the deletion button.

### Layer 3 — Background daemon thread (filesystem sweep)

A daemon thread (`_sweep_stale_uploads`) wakes every 60 seconds and scans the `uploads/`
folder. Any file whose `mtime` is more than 5 minutes old is deleted.

**Covers:** users who closed the browser tab immediately after downloading, bypassing both
the frontend timer and any further server requests.

---

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Landing page |
| GET | `/chat_page` | Chat interface (redirects home if session is missing) |
| POST | `/initialize` | Upload CV + job description; initialise session |
| POST | `/chat` | Send a message, receive Trav's reply |
| GET | `/download_letter_pdf` | Extract cover letter → clean PDF; sets `download_time` |
| GET | `/has_letter` | `{"has_letter": bool}` — enables the download button |
| GET | `/cv_status` | `{cv_present, already_purged, download_time, seconds_left}` |
| POST | `/purge_cv` | Delete the uploaded CV from disk (idempotent) |
| GET | `/reset` | Clear session + delete any remaining CV → redirect home |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | Web framework |
| `flask-session` | Server-side session storage |
| `python-dotenv` | Load `.env` variables |
| `openai` | GPT-4o-mini API client |
| `PyPDF2` | Extract text from uploaded CV PDFs |
| `requests` | Fetch job descriptions from URLs |
| `beautifulsoup4` | Parse and clean scraped HTML |
| `reportlab` | Generate clean, formatted PDF cover letters |

---

## Privacy & Data Retention

| Data | Where stored | When deleted |
|------|--------------|--------------|
| CV file (PDF) | `uploads/` folder | On user confirmation, auto-purge after 5 min, or session reset — whichever comes first |
| CV text (extracted) | Server-side session | On session reset or expiry |
| Job description | Server-side session | On session reset or expiry |
| Chat history | Server-side session | On session reset or expiry |
| Cover letter text | Never written to disk | Lives only in memory during the request |

Neither CV text nor job description is stored anywhere other than the OpenAI API call payload.

---

## Development Notes

- Change `app.secret_key` to a long random value before deploying to production.
- Add a cron job or `atexit` handler to flush `uploads/` and `flask_session/` on restarts,
  in case the background thread had not yet swept a file before the process was killed.
- For production, replace `app.run(debug=True)` with a WSGI server:
  ```bash
  gunicorn -w 4 app:app
  ```
- The `CV_MAX_AGE_SECONDS` constant (currently 300) is the single source of truth for the
  timeout. Changing it affects the frontend modal countdown, the `before_request` check,
  and the background sweep simultaneously.

---

## License

MIT