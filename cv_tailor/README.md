# CV Tailor — Smart CV Optimiser

A privacy-first desktop application that analyses your CV against a job description and generates targeted, inline improvement suggestions — without fabricating new skills or experience. Review every suggestion individually, browse the improved CV section by section, then copy or export the result as a format-preserving PDF.

---

## Features

- **CV vs JD gap analysis** — TF-IDF cosine similarity to find missing keywords and weak phrasing
- **Inline suggestions** — edits derived only from content already in your CV; nothing is invented
- **Accept / Reject per suggestion** — granular control; every change requires explicit approval
- **Editable suggestions** — modify proposed text before accepting
- **Standard mode** — fully local, zero network requests, no API key needed
- **AI-assisted mode** — deeper semantic analysis via Anthropic Claude; requires API key
- **PII masking** — name, email, phone, address, URLs replaced with placeholders before any API call
- **Section-by-section browser** — Step 4 shows the improved CV as individually navigable blocks
- **Subsection navigation** — Work Experience, Education, and Projects automatically detect and list individual entries (jobs, institutions, projects) as child links in the sidebar
- **Copy per section** — copy any section or subsection content to clipboard with one click
- **Font-preserving PDF export** — edits the original PDF in-place using PyMuPDF, reusing the exact embedded fonts, sizes, colors, and layout
- **Font fallback picker** — if embedded fonts cannot be extracted, a searchable dialog offers system fonts and 12 always-available built-in alternatives
- **Multi-language interface** — English, French, German, Spanish, Japanese, Chinese (Simplified)
- **Localised analysis** — suggestions, reasons, and AI responses are all delivered in the selected language

---

## Project Structure

```
cv_tailor/
├── main.py                       # Entry point — run this
├── requirements.txt              # Python dependencies
├── .env                          # ANTHROPIC_API_KEY (never commit this)
├── README.md
│
├── core/                         # Business logic — no UI dependencies
│   ├── models.py                 # Dataclasses: Suggestion, CVSection, CVSubSection, AnalysisResult
│   ├── i18n.py                   # All UI strings + AI prompt instructions in 6 languages
│   ├── pdf_parser.py             # PDF text extraction and CV section detection (pdfplumber)
│   ├── pii_masker.py             # Regex + heuristic PII detection and placeholder masking
│   ├── analyzer.py               # TF-IDF cosine similarity — CV vs JD gap analysis
│   ├── suggestion_engine.py      # Rule-based suggestion generation; locale-aware reason strings
│   ├── section_parser.py         # Heuristic subsection detection and splitting (jobs, degrees, projects)
│   └── pdf_generator.py          # PyMuPDF in-place PDF editor + font discovery + ReportLab fallback
│
├── ai/                           # AI integration — only invoked in AI mode
│   ├── __init__.py
│   └── ai_client.py              # Anthropic Claude API wrapper; locale-aware; PII-safe
│
└── ui/                           # tkinter GUI — 4-step wizard
    ├── styles.py                 # Colour palette, fonts, PAD constants, ttk dark theme
    ├── app.py                    # Root Tk window, step navigation, language picker, t() i18n
    ├── upload_frame.py           # Step 1 — upload CV PDF and job description
    ├── mode_frame.py             # Step 2 — standard vs AI mode; threaded analysis
    ├── review_frame.py           # Step 3 — accept/reject suggestions; sidebar list; edit before accept
    ├── preview_frame.py          # Step 4 — section browser, subsection links, copy, PDF export
    └── font_picker.py            # Modal dialog for fallback font selection on PDF export
```

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9 or higher (3.11 recommended; 3.14 supported with fixes) |
| tkinter | Bundled with Python — see Troubleshooting if missing |

### Python packages

```
anthropic>=0.25.0
pdfplumber>=0.10.0
pymupdf>=1.24.0
reportlab>=4.2.0
scikit-learn>=1.4.0
numpy>=1.26.0
python-dotenv>=1.0.0
Pillow>=10.0.0
```

Install all at once:

```bash
pip install -r requirements.txt
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

### 4. Configure your API key (optional — AI mode only)

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxx
```

> Get your key from [console.anthropic.com](https://console.anthropic.com/settings/keys).  
> The key must be on a single line with no quotes or spaces.  
> Standard mode works fully without any API key.

---

## Running the Application

```bash
python main.py
```

**In PyCharm:** open `main.py` → press **▶ Run**.  
Make sure the **working directory** in the run configuration is the project root (`cv_tailor/`).

On startup the console confirms whether the `.env` file was loaded:

```
[.env] Loaded from /path/to/cv_tailor/.env
[.env] ANTHROPIC_API_KEY found ✓
```

---

## How to Use

### Step 1 — Upload Files

- Click **Browse PDF** to upload your CV
- Paste the job description directly, or upload it as a PDF

### Step 2 — Select Processing Mode

| Mode | Description |
|---|---|
| **Standard** | Fully local. Rule-based keyword and verb analysis. No API key required. Instant results. |
| **AI-Assisted** | Deeper semantic analysis via Anthropic Claude. Requires an API key. PII is auto-masked before any data leaves your device. |

Select a mode and click **Analyse CV**. Analysis runs in a background thread so the UI stays responsive.

### Step 3 — Review Suggestions

Each suggestion card shows:

- **Original text** — the exact phrase from your CV
- **Suggested replacement** — editable before accepting
- **Reason** — why the change is recommended, in your selected language

Controls:

| Button | Action |
|---|---|
| ✓ Accept (OK) | Apply this change to the final CV |
| ✗ Reject (Cancel) | Keep the original text |
| ↺ Reset | Return a decided suggestion to pending |
| Accept All Remaining | Approve all outstanding suggestions at once |

A sidebar lists all suggestions with status indicators. Click any item to jump to it.

### Step 4 — Browse & Export

The improved CV is displayed as individually navigable blocks.

**Left sidebar — Section navigation**

- Every CV section (e.g. Formation, Compétences, Expérience Professionnelle) appears as a bold clickable link
- Sections that contain multiple entries (jobs, education, projects) show **subsection links** indented below the parent — click any one to view that entry directly
- The active item is highlighted in the sidebar

**Right panel — Content viewer**

- Title bar shows the full path of the selected block (e.g. `Expérience Professionnelle  /  Intel Inc.`)
- Content renders with accepted changes **in green** and original text in white
- **Copy Section** copies the complete block text to clipboard and confirms with a brief `✓ Copied!` badge

**Bottom navigation bar**

- **◀ Previous / Next ▶** with a `current / total` counter to step through all blocks sequentially
- **Download PDF** to export the final CV

### PDF Export — Font Handling

The export edits your **original CV PDF in-place** using PyMuPDF:

1. Each accepted suggestion is located in the PDF by text search
2. The original text is covered with a white redaction rectangle
3. The replacement text is inserted at the same position using the font bytes, size, and color extracted from the original span

If some embedded fonts cannot be extracted (e.g. `ArialMT` subsets), the **font picker dialog** appears:

- **Search bar** — filter by name
- **Category filter** — Sans-serif, Serif, Monospace
- **System fonts** — all `.ttf`/`.otf` files found on your machine, with priority given to common CV typefaces
- **Built-in fonts** — 12 always-available options (Helvetica, Times Roman, Courier in regular/bold/italic variants)

The chosen font is applied only to the edited sections. Everything else in the PDF is byte-identical to the original.

---

## Privacy & Security

| Guarantee | Detail |
|---|---|
| No fabrication | Every suggestion uses only content already present in your CV |
| PII masking | Name, email, phone, addresses, URLs masked with placeholders before any API call |
| Local by default | Standard mode makes zero external network requests |
| AI is opt-in | AI mode is never the default; requires explicit selection each session |
| No persistence | CV content is never written to disk by the application |
| Masked data only | Original unmasked personal data is never transmitted to third-party services |

---

## Supported Languages

The full interface, all suggestion reasons, and AI analysis responses are available in:

| Language | Code | Notes |
|---|---|---|
| English | `en` | Default |
| French | `fr` | |
| German | `de` | |
| Spanish | `es` | |
| Japanese | `ja` | UI uses CJK-compatible font stack |
| Chinese (Simplified) | `zh` | UI uses CJK-compatible font stack |

Use the 🌐 dropdown in the top-right of the header to switch at any time. The change takes effect immediately across all screens. In AI mode, Claude also responds in the selected language.

---

## Troubleshooting

### Window does not appear on macOS

Caused by macOS focus rules when launching from an IDE. Handled in `main.py` via `TK_SILENCE_DEPRECATION=1`, `lift()`, and a deferred `focus_force()` call. If it still occurs, run from Terminal instead of PyCharm.

### `No module named 'tkinter'`

```bash
# macOS — reinstall Python from python.org (Framework build includes tkinter)
# Linux
sudo apt install python3-tk
```

### Process finishes with exit code 0, no window shown

The `input()` call in the old dependency checker blocked silently in PyCharm's console. Fixed in the current `main.py` — missing dependencies now show a tkinter error dialog instead.

### API key rejected (401 error)

- Confirm the key starts with `sk-ant-api03-`
- Copy it fresh from [console.anthropic.com](https://console.anthropic.com/settings/keys)
- Check `.env` has no quotes or trailing spaces: `ANTHROPIC_API_KEY=sk-ant-...`
- Confirm your Anthropic account has active billing credits
- The `.env` file must use `override=True` in `load_dotenv()` — already set in `main.py`

### `invalid character '„'` SyntaxError on Python 3.14

Python 3.14 rejects typographic curly quotes (`„"«»`) in source files. Fixed in `suggestion_engine.py` — all such characters replaced with plain ASCII single quotes `'`.

### Duplicate buttons visible in the UI

Caused by using `lift()`/`lower()` for frame switching with `place` geometry — lowered frames bleed through. Fixed in `app.py` — frame switching now uses `pack_forget()`/`pack()`.

### PDF export does not match original formatting

Requires `pymupdf` (`pip install pymupdf`). Without it the app falls back to a plain ReportLab rebuild. With PyMuPDF, the original PDF is edited surgically — each accepted change is redacted and rewritten using the original embedded font bytes.

### Font picker appears unexpectedly on export

The original PDF contains fonts (commonly `ArialMT`) whose embedded subset bytes are too small to extract. The picker offers a substitute. Sections you did not edit are completely unaffected.

### Suggestions or reasons appear in the wrong language

Make sure the language is selected before clicking Analyse CV in Step 2. In Standard mode, reasons are generated at analysis time in the selected locale. In AI mode, the locale is injected into the Claude system prompt — switching language after analysis will not change already-generated reasons.

### PDF download saves inside Docker container

Add a host volume mount in `docker-compose.yml`:

```yaml
volumes:
  - ./output:/app/output
```

Then choose `/app/output/` as the save location when the dialog appears.

---

## Docker (Optional)

For containerised deployment with X11 GUI forwarding. Requires an X server on the host.

| OS | X Server |
|---|---|
| macOS | [XQuartz](https://www.xquartz.org) (`brew install --cask xquartz`) |
| Windows | [VcXsrv](https://sourceforge.net/projects/vcxsrv/) |
| Linux | Built-in X11 |

**Linux quick start:**

```bash
xhost +local:docker
docker compose up --build
```

**macOS:**

```bash
# In XQuartz Preferences → Security: enable "Allow connections from network clients"
xhost +localhost
export DISPLAY=host.docker.internal:0
docker compose up --build
```

**Dockerfile note:** the image includes `fonts-noto-cjk` so Japanese and Chinese text renders correctly inside the container.

---

## Business Rules

These constraints are enforced throughout the codebase and cannot be overridden by user input or API responses:

1. Suggestions may only use content already present in the CV
2. No new skills, qualifications, or experiences may be invented
3. Every change requires explicit user approval before being applied
4. Rejected suggestions are never applied, even partially
5. All PII must be masked before any external API call is made
6. AI processing is always opt-in — never the default mode
7. Original unmasked personal data is never transmitted to third-party services

---

## Changelog

| Version | Summary |
|---|---|
| 1.0 | Initial release — upload, analyse (Standard mode), review suggestions, plain PDF export |
| 1.1 | AI-assisted mode with Anthropic Claude API; PII masking engine |
| 1.2 | Multi-language UI and analysis — EN, FR, DE, ES, JA, ZH |
| 1.3 | Font-preserving PDF export via PyMuPDF in-place editing with embedded font extraction |
| 1.4 | Font fallback picker dialog with system font discovery and base-14 built-in alternatives |
| 1.5 | Section-by-section CV browser in Step 4 — sidebar navigation links, subsection links, per-section copy to clipboard, prev/next traversal |

---

## License

MIT License — see `LICENSE` for details.