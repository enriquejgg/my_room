# CV Matcher Pro — Architecture & Code Reference

## Table of contents

1. [Project overview](#1-project-overview)
2. [File structure](#2-file-structure)
3. [How a request flows through the system](#3-how-a-request-flows-through-the-system)
4. [Backend — App.py](#4-backend--apppy)
   - 4.1 [Startup & configuration](#41-startup--configuration)
   - 4.2 [ComparisonResult dataclass](#42-comparisonresult-dataclass)
   - 4.3 [CVComparator — text extraction](#43-cvcomparator--text-extraction)
   - 4.4 [CVComparator — PII masking](#44-cvcomparator--pii-masking)
   - 4.5 [CVComparator — skill extraction](#45-cvcomparator--skill-extraction)
   - 4.6 [CVComparator — certification extraction](#46-cvcomparator--certification-extraction)
   - 4.7 [CVComparator — experience extraction](#47-cvcomparator--experience-extraction)
   - 4.8 [CVComparator — three-tier matching](#48-cvcomparator--three-tier-matching)
   - 4.9 [CVComparator — scoring](#49-cvcomparator--scoring)
   - 4.10 [CVComparator — AI mode](#410-cvcomparator--ai-mode)
   - 4.11 [Flask routes](#411-flask-routes)
5. [Frontend — Index.html](#5-frontend--indexhtml)
   - 5.1 [Jinja2 template variables](#51-jinja2-template-variables)
   - 5.2 [Form submission flow](#52-form-submission-flow)
   - 5.3 [Results rendering](#53-results-rendering)
6. [Configuration files](#6-configuration-files)
7. [Privacy model](#7-privacy-model)
8. [Scoring reference](#8-scoring-reference)
9. [Adding or changing things](#9-adding-or-changing-things)

---

## 1. Project overview

CV Matcher Pro compares a candidate's CV against a job description and
produces a structured match report. Two analysis modes are available:

| Mode | Speed | Accuracy | External call? | Cost |
|---|---|---|---|---|
| **Standard** | < 1 s | Good for well-formatted CVs | No | Free |
| **AI (Claude)** | 10–20 s | Understands context, synonyms | Yes (Anthropic API) | API credits |

Both modes classify each required skill and certification as one of three tiers:

- ✓ **Matched** — clearly present
- ~ **Partial** — related or overlapping
- ✗ **Missing** — not found

---

## 2. File structure

```
CV_Analyser/
├── App.py              ← Flask server + CVComparator analysis engine
├── Index.html          ← Jinja2 HTML template (UI)
├── translations.json   ← UI strings keyed by language code
├── .env                ← Secret store: ANTHROPIC_API_KEY (never commit)
├── .gitignore          ← Excludes .env, __pycache__, venv
└── requirements.txt    ← Python dependencies
```

Flask is configured with `template_folder` pointing to the same directory as
`App.py`, so `Index.html` does **not** need to be inside a `templates/`
subfolder.

---

## 3. How a request flows through the system

### Standard mode

```
Browser
  │  POST /compare
  │  body: { job_description, cv_file }
  ▼
Flask route: compare()
  │
  ├─ extract_text_from_file()   → plain text from PDF/DOCX/TXT
  ├─ mask_pii()                 → replace emails, phones, names, addresses
  ├─ compare()
  │     ├─ extract_skills()          (job + CV)
  │     ├─ extract_certifications()  (job + CV)
  │     ├─ extract_experience_years()(job + CV)
  │     ├─ _classify_skill() × N     (full / partial / missing per skill)
  │     └─ score calculation         (weighted aggregate)
  └─ jsonify(ComparisonResult)
  ▼
Browser renders score cards + tag clouds
```

### AI mode

```
Browser
  │  POST /compare_ai
  │  body: { job_description, cv_file, api_key? }
  ▼
Flask route: compare_ai()
  │
  ├─ Key resolution: env var → form field → 400 error
  ├─ extract_text_from_file()
  ├─ compare_with_ai()
  │     ├─ mask_pii()             ← runs BEFORE sending to Anthropic
  │     ├─ anthropic.messages.create()
  │     │     system: JSON schema prompt
  │     │     user:   job description + masked CV
  │     └─ json.loads(response)   ← parsed + pii_masked attached
  └─ jsonify({ success, ai_analysis })
  ▼
Browser renders AI score cards + insight panels
```

---

## 4. Backend — App.py

### 4.1 Startup & configuration

```python
# Load .env file into os.environ (soft dependency — works without it)
from dotenv import load_dotenv
load_dotenv(...)

# Template folder resolved from __file__ so IDEs launching from a
# different CWD don't cause TemplateNotFound errors
app = Flask(__name__, template_folder=_HERE)

# Read API key once — never re-read, never logged
_ENV_API_KEY: str = os.environ.get('ANTHROPIC_API_KEY', '').strip()
```

**Why `template_folder=_HERE`?**
Flask's default is `templates/` relative to the *current working directory*.
Using `os.path.abspath(__file__)` pins it to the directory containing
`App.py` regardless of where Python is launched from.

**Why read the API key once at startup?**
Avoids repeated `os.environ` lookups on every request and makes it trivial to
check `bool(_ENV_API_KEY)` to decide what to show in the UI.

---

### 4.2 ComparisonResult dataclass

```python
@dataclass
class ComparisonResult:
    overall_score:          int  = 0
    experience_match:       int  = 0
    skills_match:           int  = 0
    certifications_match:   int  = 0
    experience_details:     dict = field(default_factory=dict)
    skills_details:         dict = field(default_factory=dict)
    certifications_details: dict = field(default_factory=dict)
    pii_masked:             dict = field(default_factory=dict)
```

A plain data container — no logic, no methods. Using `@dataclass` instead of
a plain `dict` gives type hints, a clear schema, and readable attribute access.
`field(default_factory=dict)` is required for mutable default values; using
`= {}` directly would share the same dict across all instances.

---

### 4.3 CVComparator — text extraction

| Method | Input | What it does |
|---|---|---|
| `extract_text_from_file()` | `FileStorage`, filename | Dispatches by extension |
| `_extract_pdf()` | raw bytes | PyPDF2 page-by-page |
| `_extract_docx()` | raw bytes | python-docx paragraphs |
| fallback in `extract_text_from_file` | raw bytes | tries UTF-8 → latin-1 → cp1252 |

**Why read bytes then dispatch?**
`file_obj.read()` can only be called once on a Flask `FileStorage` object
(it's a stream). Reading into `content: bytes` first lets any of the three
helpers consume the data without re-reading.

**Why try multiple encodings for TXT?**
Plain-text CVs exported from older word processors often use Latin-1 or
Windows-1252. Attempting UTF-8 first (cheapest), then falling back, avoids
`UnicodeDecodeError` without requiring the user to specify an encoding.

---

### 4.4 CVComparator — PII masking

The `mask_pii(text)` method applies six regex substitutions in sequence and
then performs a heuristic name-line scan:

| Step | Pattern type | Placeholder |
|---|---|---|
| 1 | Email address | `[EMAIL]` |
| 2 | Phone number (intl.) | `[PHONE]` |
| 3 | Street address | `[ADDRESS]` |
| 4 | Postcode / ZIP | `[POSTCODE]` |
| 5 | LinkedIn URL | `[LINKEDIN]` |
| 6 | GitHub URL | `[GITHUB]` |
| 7 | Name (first 5 lines) | `[CANDIDATE NAME]` |

**Order matters for email vs phone.**
Some email addresses (e.g. `+tag@domain.com`) contain digit-like substrings.
Running the email regex first prevents the phone regex from matching part of
an already-identified email.

**Why the first-5-lines heuristic for names?**
Regex cannot reliably detect names in general text — any two Title Case words
could be a name. Restricting the scan to the first five lines (where most CVs
place the candidate's name) avoids replacing company names and job titles
further down.

The function returns `(masked_text, found_dict)`. `found_dict` is returned to
the browser as a transparency report so candidates can see exactly what was
hidden.

---

### 4.5 CVComparator — skill extraction

`extract_skills(text)` runs two complementary passes:

**Pass 1 — keyword bank (SKILL_KEYWORDS)**

~120 lowercase tokens covering programming languages, frameworks, cloud
platforms, databases, soft skills, and business tools. Each is searched with:

```python
pattern = r'(?<![a-z])' + re.escape(skill) + r'(?![a-z])'
```

Using negative lookbehind/lookahead instead of `\b` is necessary because:
- `\b` treats `+` and `#` as word boundaries, so `\bc++\b` never matches.
- `\b` treats a space in `machine learning` as a word boundary mid-term.

The custom boundary `(?<![a-z])…(?![a-z])` only checks for adjacent lowercase
letters, so multi-word and symbol-containing skills match correctly.

**Pass 2 — dynamic capitalised tokens**

Captures technology names not in the keyword bank (e.g. `Kubernetes`,
`Terraform`, `FastAPI`) by matching `[A-Z][a-zA-Z0-9]+` on the original
(mixed-case) text. A blocklist of ~30 common English words (`The`, `From`,
`Must`, …) filters out false positives.

The results of both passes are unioned into a single `Set[str]`.

---

### 4.6 CVComparator — certification extraction

`extract_certifications(text)` applies each pattern in `CERT_PATTERNS` with
`re.FINDALL` and `re.IGNORECASE`, adding all matches to a set (which
deduplicates them).

Patterns use `\b` word boundaries and `(?:...)` non-capturing groups, e.g.:

```python
r'\bAWS\s+(?:Certified|Solutions|Developer|SysOps)\b'
```

This matches "AWS Certified", "AWS Solutions", "AWS Developer", and
"AWS SysOps" but not "AWSCERT" or "pre-AWS".

---

### 4.7 CVComparator — experience extraction

`extract_experience_years(text)` applies five regex patterns covering the most
common English phrasings:

```
"5+ years of experience"
"3 yrs exp"
"experience of 10 years"
"minimum 3 years"
"at least 7 years"
```

It returns the **maximum** value found, not the first. In a job description
this captures the total requirement; in a CV it captures the candidate's full
career span rather than a single role's duration.

Returns `0.0` (not `None`) when no match is found — callers use `== 0` as the
"not specified" sentinel, which means no experience penalty is applied.

---

### 4.8 CVComparator — three-tier matching

`_classify_skill(job_skill, cv_skills)` checks three conditions in order,
short-circuiting on the first match:

```
1. Exact:     job_lower in cv_skills
              → 'full'

2. Substring: cv_skill ⊆ job_lower  OR  job_lower ⊆ cv_skill
              → 'partial'
              (catches: "python 3" vs "python", "node" vs "nodejs")

3. Fuzzy:     SequenceMatcher ratio > 0.75
              → 'partial'
              (catches: "postgresql" vs "postgres")

4. Default:   → 'missing'
```

`_fuzzy_match()` uses Python's `difflib.SequenceMatcher` which implements the
Ratcliff/Obershelp algorithm: `2M/T` where M = matching characters, T = total
characters. A 0.75 threshold was chosen empirically as the point where the
majority of true skill synonyms are captured without excessive false positives.

Certifications use a slightly lower threshold of 0.70 because acronyms are
short — a one-character difference (e.g. CKA vs CKAD) still indicates a
closely related credential.

---

### 4.9 CVComparator — scoring

| Score | Formula | Default when not stated |
|---|---|---|
| Experience | `min(candidate / required, 1.0) × 100` | 100 |
| Skills | `(full + 0.5 × partial) / total × 100` | 0 (no signal) |
| Certifications | `(full + 0.5 × partial) / total × 100` | 100 |
| **Overall** | `exp×0.25 + skills×0.55 + certs×0.20` | — |

**Why partial = 0.5?**
A partial match (e.g. "React" when "React Native" is required) represents
genuine relevant experience but not an exact qualification. Half a point
rewards this without inflating the score.

**Why skills weight = 55%?**
Job descriptions typically list 10–20 skills and only 0–3 certifications.
Skills are therefore the richest signal and deserve the highest weight.

**Why experience defaults to 100 when not stated?**
If the job description doesn't mention required years, penalising any
candidate for their experience level would be unfair.

---

### 4.10 CVComparator — AI mode

`compare_with_ai(job_text, cv_text, api_key)`:

1. Calls `mask_pii()` on `cv_text` — the masked version is sent to Anthropic;
   the original is never transmitted.
2. Constructs a system prompt that defines Claude's role and provides the exact
   JSON schema to return. Listing field names, types, and classification rules
   in the prompt significantly reduces hallucinated keys.
3. Sends a single `messages.create()` call with `model="claude-opus-4-5"` and
   `max_tokens=4096` (sufficient for a detailed analysis of even long CVs).
4. Strips any accidental markdown fences from the response using `re.sub`.
5. Parses the JSON and attaches `pii_masked` before returning.

**Why `import anthropic` inside the method?**
Deferred import keeps the server startup fast and allows the app to run in
standard mode even if the `anthropic` package is not installed.

---

### 4.11 Flask routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Render `Index.html` with translation + key-status variables |
| `/api_key_status` | GET | JSON: `{"configured": bool}` |
| `/compare` | POST | Standard keyword analysis |
| `/compare_ai` | POST | AI-powered analysis |

All `POST` routes follow the same pattern:
1. Validate inputs → return 400 with an `error` key if invalid.
2. Process → call comparator methods.
3. Return 200 JSON on success.
4. Catch all exceptions → return 500 with `error` key so the browser always
   receives parseable JSON rather than an HTML error page.

`/compare_ai` resolves the API key with:

```python
api_key = _ENV_API_KEY or request.form.get('api_key', '').strip()
```

Environment key takes precedence. The form field is only used as a fallback
when no environment key is configured.

---

## 5. Frontend — Index.html

The file is a **Jinja2 template** rendered server-side by Flask. It contains
HTML, CSS, and JavaScript — no external JS framework or build step is required.

### 5.1 Jinja2 template variables

| Variable | Type | Used for |
|---|---|---|
| `lang` | str | `<html lang="...">` + RTL attribute |
| `translations` | dict | All UI text (button labels, headings, …) |
| `supported_languages` | dict | Language selector `<option>` list |
| `env_key_set` | bool | Show/hide the API key input field |

`translations` is serialised to JavaScript with `{{ translations | tojson }}`
so JS can also access the strings (for loading messages, error text, etc.):

```javascript
const T = {{ translations | tojson }};
```

### 5.2 Form submission flow

```
User clicks "Compare CV & Job Spec"
  ↓
submit event listener (preventDefault)
  ↓
Build FormData from the <form> element
  ↓
useAI?  ──yes──→ fetch('/compare_ai', { method:'POST', body:formData })
        ──no───→ fetch('/compare',    { method:'POST', body:formData })
  ↓
await response.json()
  ↓
response.ok?  ──no──→ throw Error(data.error)  →  show errorBox
              ──yes─→ renderAI(data.ai_analysis)
                   OR renderStandard(data)
  ↓
results.scrollIntoView()
```

`FormData` is used (not `JSON.stringify`) because the CV file upload requires
`multipart/form-data` encoding. Flask reads fields with `request.form.get()`
and files with `request.files`.

### 5.3 Results rendering

Two JavaScript functions produce the results HTML:

**`renderStandard(d)`** — called for `/compare` responses.

Populates:
- Score tile values and progress bar widths from `d.experience_match`,
  `d.skills_match`, `d.certifications_match`
- `gaugeHTML(d.overall_score)` — an SVG radial gauge
- Tag clouds from `d.skills_details.matching / partial / missing / additional`
- `piiBlock(d.pii_masked)` — a privacy report if anything was masked

**`renderAI(ai)`** — called for `/compare_ai` responses.

Same structure but reads from `ai.skills_analysis.matched_skills` etc. (the
AI response uses slightly different key names reflecting Claude's output
schema). Also renders the additional AI-only sections: strengths, weaknesses,
hiring recommendation, cultural fit, and growth potential.

**`scoreColour(n)`** — returns CSS class names based on score:
- ≥ 70 → green (`var(--accent)`)
- ≥ 40 → amber (`var(--partial)`)
- < 40 → red   (`var(--warn)`)

**`makeTags(arr, cls)`** — produces a `<div class="tags">` containing one
`<span class="tag {cls}">` per item. The `cls` argument sets the colour:
`full` (green), `partial` (amber), `missing` (red), `extra` (purple).

---

## 6. Configuration files

### `.env`

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Loaded by `python-dotenv` at startup. Variables already in the shell
environment take precedence over `.env` values. Never commit this file.

### `translations.json`

```json
{
  "en": {
    "app_title": "CV Matcher Pro",
    "button_analyze": "Compare CV & Job Spec! 🚀",
    ...
  }
}
```

Add a new language by adding a new top-level key matching a BCP-47 code and
adding the same code to `SUPPORTED_LANGUAGES` in `App.py`. RTL layout is
applied automatically for `lang == 'ar'` via a Jinja2 conditional in the
template.

### `requirements.txt`

| Package | Purpose |
|---|---|
| `flask` | Web framework and Jinja2 templating |
| `PyPDF2` | Extract text from PDF files |
| `python-docx` | Extract text from DOCX files |
| `anthropic` | Claude API client |
| `python-dotenv` | Load `.env` into `os.environ` at startup |

---

## 7. Privacy model

```
CV file uploaded by browser
        │
        ▼
extract_text_from_file()   ← bytes → plain text
        │
        ▼
mask_pii()                 ← replaces: email, phone, address,
        │                              postcode, LinkedIn, GitHub, name
        │
        ├── Standard mode: masked_cv passed to compare()
        │                  (analysis stays entirely on this server)
        │
        └── AI mode:       masked_cv sent to Anthropic API
                           original cv_text never leaves the server
```

The `pii_masked` dict returned in every response lets the user verify what was
removed. It maps field names to instance counts:
`{'email': 1, 'phone': 2, 'name': 1}`.

---

## 8. Scoring reference

### Sub-score formulae

```
Experience score:
  if required_years == 0:
      score = 100
  else:
      score = min(candidate_years / required_years, 1.0) × 100

Skills score:
  if total_required == 0:
      score = 0
  else:
      score = (full_matches + 0.5 × partial_matches) / total_required × 100

Certifications score:
  if total_required == 0:
      score = 100
  else:
      score = (full_matches + 0.5 × partial_matches) / total_required × 100

Overall score:
  experience × 0.25 + skills × 0.55 + certifications × 0.20
```

### Colour thresholds (used in the UI)

| Score range | Colour | Meaning |
|---|---|---|
| 70–100 | Green | Strong match |
| 40–69 | Amber | Partial match |
| 0–39 | Red | Weak match |

---

## 9. Adding or changing things

### Add a new skill to the keyword bank

Open `App.py` and add to `CVComparator.SKILL_KEYWORDS`:

```python
'your new skill',      # add to the relevant category comment block
```

### Add a new certification pattern

Add a regex string to `CVComparator.CERT_PATTERNS`:

```python
r'\bYourCert\b',      # Brief description
```

### Add a new language

1. Add translations to `translations.json`:
   ```json
   "de": { "app_title": "CV Matcher Pro", ... }
   ```
2. Add to `SUPPORTED_LANGUAGES` in `App.py`:
   ```python
   'de': 'Deutsch',
   ```

### Change the score weights

Edit the final calculation in `CVComparator.compare()`:

```python
result.overall_score = int(
    exp_score    * 0.30 +   # increase experience weight
    skills_score * 0.50 +
    cert_score   * 0.20
)
```

Weights must sum to 1.0.

### Switch to a different Claude model

Change the `model` argument in `compare_with_ai()`:

```python
message = client.messages.create(
    model = "claude-sonnet-4-5",   # faster and cheaper than opus
    ...
)
```

Available models: `claude-opus-4-5` (most capable), `claude-sonnet-4-5`
(balanced), `claude-haiku-4-5-20251001` (fastest/cheapest).