# CV Tailor — Smart CV Optimiser

A privacy-first desktop application that analyses your CV against a job description and provides targeted, inline improvement suggestions — without fabricating new skills or experience.

---

## Features

- **CV vs JD gap analysis** — semantic comparison using TF-IDF to identify missing keywords and weak phrasing
- **Inline suggestions** — targeted edits derived only from content already in your CV
- **Accept / Reject control** — review every suggestion individually before any change is applied
- **Editable suggestions** — modify suggested text before accepting
- **Standard mode** — fully local, no API calls, no data leaves your device
- **AI-assisted mode** — deeper semantic analysis via Anthropic Claude API
- **PII masking** — name, email, phone, addresses and URLs are automatically masked before any API call
- **Final PDF export** — download a clean PDF with only approved changes applied
- **Multi-language UI and analysis** — English, French, German, Spanish, Japanese, Chinese

---

## Project Structure

```
cv_tailor/
├── main.py                  # Entry point — run this
├── requirements.txt
├── .env                     # API key (not committed to version control)
│
├── core/
│   ├── models.py            # Data classes: Suggestion, CVSection, AnalysisResult
│   ├── pdf_parser.py        # PDF text extraction and CV section detection
│   ├── pii_masker.py        # PII detection and placeholder masking
│   ├── analyzer.py          # TF-IDF cosine similarity gap analysis
│   ├── suggestion_engine.py # Rule-based suggestion generation
│   ├── pdf_generator.py     # Final CV PDF generation with accepted edits
│   └── i18n.py              # All UI strings and AI prompts in 6 languages
│
├── ai/
│   └── ai_client.py         # Anthropic API wrapper (AI mode only)
│
└── ui/
    ├── styles.py            # Colour palette, fonts, ttk theme
    ├── app.py               # Root Tk window, navigation, language picker
    ├── upload_frame.py      # Step 1 — upload CV and job description
    ├── mode_frame.py        # Step 2 — select mode and run analysis
    ├── review_frame.py      # Step 3 — accept/reject suggestions
    └── preview_frame.py     # Step 4 — preview changes and download PDF
```

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9 or higher (3.11 recommended) |
| tkinter | Included with Python (see notes below) |

### Python packages

```
anthropic>=0.25.0
pdfplumber>=0.10.0
reportlab>=4.2.0
scikit-learn>=1.4.0
numpy>=1.26.0
python-dotenv>=1.0.0
Pillow>=10.0.0
```

---

## Installation

### 1. Clone or download the project

```bash
git clone https://github.com/yourname/cv_tailor.git
cd cv_tailor
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key (optional — only needed for AI mode)

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxx
```

> Get your key from [console.anthropic.com](https://console.anthropic.com/settings/keys).  
> The app works without this key in Standard mode.

---

## Running the Application

```bash
python main.py
```

Or in PyCharm: open `main.py` and press **▶ Run**.

---

## How to Use

The app guides you through four steps:

### Step 1 — Upload Files
- Upload your **CV as a PDF**
- Paste or upload the **job description** (text or PDF)

### Step 2 — Select Mode

| Mode | Description |
|---|---|
| **Standard** | Fully local. Rule-based keyword and verb analysis. No API key needed. |
| **AI-Assisted** | Uses Anthropic Claude for deeper semantic analysis. Requires API key. PII is auto-masked before any data is sent. |

Click **Analyse CV** to run the analysis.

### Step 3 — Review Suggestions

Each suggestion shows:
- The **original text** from your CV
- The **suggested replacement** (editable before accepting)
- The **reason** for the change

Use **Accept (OK)** or **Reject (Cancel)** for each one individually.  
Use **Accept All Remaining** to approve everything at once.

### Step 4 — Preview & Download
- Review the full CV with accepted changes **highlighted in green**
- Check the match score and missing keywords
- Click **Download Final CV (PDF)** to save

---

## Privacy & Security

| Guarantee | Detail |
|---|---|
| No fabrication | Every suggestion is derived from content already in your CV |
| PII masking | Name, email, phone, address and URLs are replaced with placeholders before any API call |
| Local by default | Standard mode makes zero network requests |
| AI is opt-in | AI mode is never the default and requires explicit selection |
| No persistence | CV data is never written to disk or logged |

---

## Supported Languages

The full interface and all analysis output are available in:

| Language | Code |
|---|---|
| English | `en` |
| French | `fr` |
| German | `de` |
| Spanish | `es` |
| Japanese | `ja` |
| Chinese (Simplified) | `zh` |

Use the 🌐 dropdown in the top-right corner to switch language at any time.

---

## Troubleshooting

### Window does not appear on macOS
This is a macOS focus issue with apps launched from an IDE. The fix is already in `main.py` (`TK_SILENCE_DEPRECATION=1` and `lift()`/`focus_force()`). If it still happens, try running from Terminal instead of PyCharm.

### `No module named 'tkinter'`
tkinter is not included in all Python builds.

```bash
# macOS — reinstall Python from python.org (the Framework build includes tkinter)
# Linux
sudo apt install python3-tk
```

### API key rejected (401 error)
- Make sure the key starts with `sk-ant-api03-`
- Copy it fresh from [console.anthropic.com](https://console.anthropic.com/settings/keys)
- Check there are no extra spaces or quotes in your `.env` file
- Confirm your account has active credits

### `invalid character` SyntaxError
Caused by typographic quotes (`„"«»`) in source files on Python 3.14. Download the latest `suggestion_engine.py` from the project — all curly quotes have been replaced with plain ASCII quotes.

### PDF download saves inside the container (Docker)
Add a volume mount in `docker-compose.yml`:
```yaml
volumes:
  - ./output:/app/output
```
Then save your PDF to the `/app/output` path when prompted.

---

## Docker (Optional)

See the [Docker setup guide](docs/docker.md) for running with X11 forwarding on macOS, Linux, and Windows.

Quick start on Linux:

```bash
xhost +local:docker
docker compose up --build
```

---

## Business Rules

These constraints are enforced throughout the application:

1. Suggestions may only use content already present in the CV
2. No new skills, qualifications, or experience may be invented
3. Each change requires explicit user approval before being applied
4. Rejected suggestions are never applied
5. PII must be masked before any external API call
6. AI processing is always opt-in, never the default

---

## License

MIT License — see `LICENSE` for details.
