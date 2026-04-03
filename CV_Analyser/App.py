"""
CV-Job Specification Comparator — Flask Web Application
========================================================

Overview
--------
This application accepts a candidate's CV (PDF, DOCX, or TXT) and a pasted
job description, then produces a structured match report covering:

  - Experience     (years required vs. years found in the CV)
  - Skills         (keyword + fuzzy matching, three tiers: full / partial / missing)
  - Certifications (regex-based detection, same three tiers)
  - An overall weighted score  (25% experience · 55% skills · 20% certs)

Two analysis modes are provided:

  Standard mode  — pure Python: fast, offline, no external API call.
  AI mode        — sends the (PII-masked) CV and job description to Claude
                   (Anthropic API) for deeper contextual analysis.

Privacy
-------
Before any text leaves the server (in AI mode) or is stored in memory,
CVComparator.mask_pii() replaces personally identifiable information
(email, phone, postal address, postcode, LinkedIn/GitHub URLs, and name)
with neutral placeholders such as [EMAIL] or [CANDIDATE NAME].

API Key handling
----------------
The Anthropic API key is never hard-coded.  It is read once at startup from
the environment variable ANTHROPIC_API_KEY, which can be set either via a
.env file (loaded by python-dotenv) or directly in the shell.  If no
environment key exists and AI mode is requested, the user may submit a key
through the form — it is used only for that single request and never persisted.

Project layout
--------------
  App.py            — this file; Flask app + CVComparator class
  Index.html        — Jinja2 template (served from the same folder as App.py)
  translations.json — UI string translations keyed by language code
  .env              — local secret store (never commit to version control)
  requirements.txt  — Python dependencies

Routes
------
  GET  /                — renders the main UI
  GET  /api_key_status  — JSON: whether a server-side API key is configured
  POST /compare         — standard (keyword) analysis
  POST /compare_ai      — AI-powered analysis via Claude
"""

# ── Standard library ──────────────────────────────────────────────────────────
import io
import json
import os
import re
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, Tuple

# ── Third-party ───────────────────────────────────────────────────────────────
import PyPDF2
from flask import Flask, jsonify, render_template, request

# requests + BeautifulSoup for URL job-spec extraction (soft dependency)
try:
    import requests as http_requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

# ── Optional: load a .env file into os.environ before anything else reads it ──
# python-dotenv is a soft dependency; the app works without it as long as
# ANTHROPIC_API_KEY is already present in the shell environment.
try:
    from dotenv import load_dotenv
    # __file__ is used so the path is always relative to App.py, not to the
    # current working directory (which differs when launched from an IDE).
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass  # python-dotenv not installed — rely on shell environment alone

# ── Optional: python-docx for DOCX parsing ────────────────────────────────────
try:
    import docx as python_docx
    DOCX_AVAILABLE = True
except ImportError:
    # The app still works for PDF and TXT files without this package.
    DOCX_AVAILABLE = False

# ── Flask application setup ───────────────────────────────────────────────────
# template_folder is set to the directory that contains App.py so that
# Flask's Jinja2 loader finds Index.html regardless of the working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=_HERE)

# ── API key — read once at startup ────────────────────────────────────────────
# Storing it in a module-level constant avoids repeated os.environ lookups and
# makes it easy to check whether a key is available without exposing its value.
# The key is NEVER logged, returned to clients, or embedded in responses.
_ENV_API_KEY: str = os.environ.get('ANTHROPIC_API_KEY', '').strip()


# =============================================================================
# Translations
# =============================================================================

def load_translations() -> dict:
    """
    Load the translations.json file from the same directory as this script.

    Returns a nested dict of the form::

        {
          "en": {"app_title": "CV Matcher Pro", ...},
          "fr": {"app_title": "...", ...},
          ...
        }

    Returns an empty dict (graceful fallback) if the file is missing or
    malformed, so the app does not crash — it will simply show empty UI text.
    """
    path = os.path.join(os.path.dirname(__file__), 'translations.json')
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}


TRANSLATIONS = load_translations()

# Languages offered in the UI language-selector dropdown.
# Keys are BCP-47 language codes; values are the display names shown to users.
SUPPORTED_LANGUAGES: Dict[str, str] = {
    'en': 'English',
    'fr': 'Français',
    'es': 'Español',
    'de': 'Deutsch',
    'pt': 'Português',
    'ru': '\u0420\u0443\u0441\u0441\u043a\u0438\u0439',
    'ar': '\u0627\u0644\u0639\u0631\u0628\u064a\u0629',
    'zh': '\u4e2d\u6587',
    'ja': '\u65e5\u672c\u8a9e',
    'ko': '\ud55c\uad6d\uc5b4',
    'vi': 'Ti\u1ebfng Vi\u1ec7t',
}


# =============================================================================
# Data classes
# =============================================================================

@dataclass
class ComparisonResult:
    """
    Container for the output of CVComparator.compare().

    Attributes
    ----------
    overall_score : int
        Weighted aggregate of the three sub-scores (0–100).
        Formula: experience×0.25 + skills×0.55 + certifications×0.20
    experience_match : int
        How well the candidate's years of experience meet the stated
        requirement (0–100).
    skills_match : int
        Proportion of required skills found in the CV, with partial matches
        worth 0.5 points each (0–100).
    certifications_match : int
        Proportion of required certifications found in the CV, same weighting
        as skills (0–100).
    experience_details : dict
        Keys: 'required' (float), 'candidate' (float), 'meets_requirement' (bool).
    skills_details : dict
        Keys: 'required', 'matching', 'partial', 'missing', 'candidate',
        'additional' — each a sorted list of skill strings.
    certifications_details : dict
        Keys: 'required', 'matching', 'partial', 'missing', 'candidate'
        — each a sorted list of certification strings.
    pii_masked : dict
        Maps each PII field name to the count of instances replaced,
        e.g. {'email': 1, 'phone': 2, 'name': 1}.
        Empty when mask_pii() was not called before compare().
    """
    overall_score:          int  = 0
    experience_match:       int  = 0
    skills_match:           int  = 0
    certifications_match:   int  = 0
    experience_details:     dict = field(default_factory=dict)
    skills_details:         dict = field(default_factory=dict)
    certifications_details: dict = field(default_factory=dict)
    pii_masked:             dict = field(default_factory=dict)


# =============================================================================
# CVComparator — the core analysis engine
# =============================================================================

class CVComparator:
    """
    Analyses the textual match between a CV and a job description.

    The class is stateless — all methods are pure functions with no side
    effects on instance state.  A single module-level instance (``comparator``)
    is reused across all HTTP requests without any locking concerns.

    Design overview
    ---------------
    1. Text extraction   — convert uploaded file bytes to a plain string.
    2. PII masking       — replace personal data with neutral placeholders.
    3. Skill extraction  — union of keyword-bank matching and dynamic
                           capitalised-word detection.
    4. Cert extraction   — regex patterns for known certification acronyms.
    5. Experience years  — regex patterns for "N years of experience" phrasing.
    6. Matching          — three-tier classification (full / partial / missing)
                           using exact, substring, and fuzzy string comparison.
    7. Scoring           — weighted aggregation into a single overall score.
    8. AI mode           — delegates steps 3–7 to Claude and parses JSON output.
    """

    # ── Class-level constants ─────────────────────────────────────────────────

    # SKILL_KEYWORDS is a curated set of ~120 lowercase skill tokens used for
    # the standard (non-AI) matching pass.  Words are matched case-insensitively
    # with a word-boundary-aware regex so "rust" does not match "robust".
    # Multi-word skills (e.g. 'machine learning') work because the full document
    # text is searched as a single lowercase string.
    SKILL_KEYWORDS: Set[str] = {
        # ── Programming languages ──────────────────────────────────────────
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
        'kotlin', 'swift', 'ruby', 'php', 'scala', 'r', 'matlab', 'perl',
        # ── Web frameworks & protocols ─────────────────────────────────────
        'html', 'css', 'react', 'angular', 'vue', 'node', 'nodejs', 'express',
        'django', 'flask', 'fastapi', 'spring', 'laravel', 'rails', 'graphql',
        'rest', 'restful', 'api', 'soap', 'microservices',
        # ── Data, AI & Machine Learning ────────────────────────────────────
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow',
        'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'spark', 'hadoop',
        'tableau', 'power bi', 'data analysis', 'data science', 'data engineering',
        'etl', 'big data', 'analytics', 'statistics', 'regression', 'classification',
        # ── Cloud & DevOps ─────────────────────────────────────────────────
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
        'jenkins', 'gitlab', 'github actions', 'ci/cd', 'devops', 'linux', 'bash',
        'shell scripting', 'monitoring', 'prometheus', 'grafana',
        # ── Databases ──────────────────────────────────────────────────────
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'dynamodb', 'oracle', 'sql server', 'nosql',
        # ── Project & product management ───────────────────────────────────
        'agile', 'scrum', 'kanban', 'jira', 'confluence', 'project management',
        'product management', 'stakeholder management', 'risk management',
        # ── Interpersonal / soft skills ────────────────────────────────────
        'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
        'presentation', 'negotiation', 'mentoring', 'coaching',
        # ── Finance & business tools ───────────────────────────────────────
        'excel', 'vba', 'accounting', 'budgeting', 'forecasting', 'erp', 'sap',
        'salesforce', 'crm', 'marketing', 'seo', 'content management',
        # ── Security ───────────────────────────────────────────────────────
        'cybersecurity', 'penetration testing', 'siem', 'iso 27001', 'gdpr',
        # ── Design & UX ────────────────────────────────────────────────────
        'figma', 'sketch', 'adobe', 'photoshop', 'illustrator', 'ux', 'ui',
        'user research', 'wireframing', 'prototyping',
    }

    # CERT_PATTERNS contains regex strings for professional certification names.
    # \b word boundaries prevent false positives (e.g. "CISSP" inside a longer
    # token).  (?:...) non-capturing groups match certification variants without
    # creating unnecessary capture groups in findall() results.
    CERT_PATTERNS = [
        r'\bPMP\b',       # Project Management Professional
        r'\bPrince2\b',   # Projects IN Controlled Environments
        r'\bCISSP\b',     # Certified Information Systems Security Professional
        r'\bCEH\b',       # Certified Ethical Hacker
        r'\bCISM\b',      # Certified Information Security Manager
        r'\bAWS\s+(?:Certified|Solutions|Developer|SysOps)\b',
        r'\bAzure\s+(?:Certified|Administrator|Developer|Architect)\b',
        r'\bGCP\s+(?:Certified|Professional|Associate)\b',
        r'\bCCNA\b', r'\bCCNP\b', r'\bCCIE\b',   # Cisco networking tiers
        r'\bCPA\b',   # Certified Public Accountant
        r'\bCFA\b',   # Chartered Financial Analyst
        r'\bACCA\b',  # Association of Chartered Certified Accountants
        r'\bCIMA\b',  # Chartered Institute of Management Accountants
        r'\bPHR\b', r'\bSPHR\b',  # HR certifications
        r'\bScrum\s+(?:Master|Developer|Product Owner)\b',
        r'\bCSM\b',   # Certified Scrum Master
        r'\bCSPO\b',  # Certified Scrum Product Owner
        r'\bSAFe\b',  # Scaled Agile Framework
        r'\bITIL\b',  # IT Infrastructure Library
        r'\bCOBIT\b', # Control Objectives for IT
        r'\bGoogle\s+(?:Analytics|Ads|Data\s+Studio)\b',
        r'\bSix\s+Sigma\b', r'\bLean\b',
        r'\bISO\s+\d{4,5}\b',  # e.g. ISO 27001, ISO 9001
        r'\bOCA\b', r'\bOCP\b',               # Oracle Certified Associate / Professional
        r'\bRedHat\b', r'\bRHCE\b', r'\bRHCSA\b',  # Red Hat Linux
        r'\bCKA\b', r'\bCKAD\b',              # Kubernetes Administrator / Developer
    ]

    # ── PII regular expressions (compiled once at class load time) ────────────

    # Standard email address — local-part @ domain . TLD
    EMAIL_RE = re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    )

    # Phone numbers in a variety of international formats:
    #   +44 (0)20 1234 5678  |  +1-800-555-0100  |  07700 900123
    # Allows an optional country code, optional parentheses around area code,
    # and separators of space, dash, or dot between digit groups.
    PHONE_RE = re.compile(
        r'\b(?:\+?\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}\b'
    )

    # Street addresses: a building number followed by a road-type suffix.
    # re.IGNORECASE covers "street", "Street", "STREET", etc.
    ADDRESS_RE = re.compile(
        r'\b\d{1,5}\s+[A-Za-z0-9\s,\.]+(?:'
        r'Street|St|Avenue|Ave|Road|Rd|Lane|Ln|'
        r'Drive|Dr|Court|Ct|Boulevard|Blvd|Way|'
        r'Close|Crescent|Terrace|Place|Pl)\b',
        re.IGNORECASE
    )

    # Postcodes / ZIP codes for three common national formats:
    #   UK:     SW1A 2AA
    #   US:     90210  or  90210-4321
    #   Canada: K1A 0B1
    POSTCODE_RE = re.compile(
        r'\b(?:'
        r'[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}|'   # UK
        r'\d{5}(?:-\d{4})?|'                       # US
        r'[A-Z]\d[A-Z]\s*\d[A-Z]\d'               # Canada
        r')\b',
        re.IGNORECASE
    )

    # Profile URLs — these appear on CVs and uniquely identify a person.
    LINKEDIN_RE = re.compile(r'linkedin\.com/in/[A-Za-z0-9\-_]+', re.IGNORECASE)
    GITHUB_RE   = re.compile(r'github\.com/[A-Za-z0-9\-_]+',      re.IGNORECASE)

    # ==========================================================================
    # File text extraction
    # ==========================================================================

    def extract_text_from_file(self, file_obj, filename: str) -> str:
        """
        Convert an uploaded file to a plain Unicode string.

        Dispatches to a format-specific helper based on the file extension.
        For plain-text files it tries several encodings in order of likelihood
        (UTF-8 → Latin-1 → Windows-1252) to handle older word-processor exports.

        Parameters
        ----------
        file_obj : werkzeug.datastructures.FileStorage
            The uploaded file object from Flask's request.files.
        filename : str
            Original filename — used only to determine the file extension.

        Returns
        -------
        str
            Full document text as a single Unicode string.  PDF pages are
            separated by newline characters.

        Raises
        ------
        RuntimeError
            If the file is a DOCX and python-docx is not installed.
        """
        ext     = Path(filename).suffix.lower() if filename else ''
        content = file_obj.read()  # Read raw bytes once; helpers operate on bytes

        if ext == '.pdf':
            return self._extract_pdf(content)
        elif ext == '.docx':
            return self._extract_docx(content)
        else:
            # Plain text fallback — try encodings from most to least common
            for encoding in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Last resort: UTF-8 with replacement characters for invalid bytes
            return content.decode('utf-8', errors='replace')

    def _extract_pdf(self, content: bytes) -> str:
        """
        Extract text from a PDF using PyPDF2.

        Pages are extracted individually and joined with newlines so that skills
        near page breaks are not concatenated into a single malformed token
        (e.g. "Pythonon" from "Python" at the end of one page and "on" at the
        start of the next).  Image-only (scanned) pages return no text and are
        silently skipped.

        Parameters
        ----------
        content : bytes
            Raw PDF file bytes.

        Returns
        -------
        str
            All extractable page text joined with newlines.
        """
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        pages  = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return '\n'.join(pages)

    def _extract_docx(self, content: bytes) -> str:
        """
        Extract text from a DOCX file using python-docx.

        Only paragraph text is extracted.  Text inside tables, text boxes,
        headers, and footers is not captured — for most standard CV formats
        the main content lives in paragraphs, so this is sufficient.

        Parameters
        ----------
        content : bytes
            Raw DOCX file bytes.

        Returns
        -------
        str
            All paragraph texts joined with newlines.

        Raises
        ------
        RuntimeError
            If python-docx is not installed.
        """
        if not DOCX_AVAILABLE:
            raise RuntimeError(
                'python-docx is not installed.  Run: pip install python-docx'
            )
        doc = python_docx.Document(io.BytesIO(content))
        return '\n'.join(p.text for p in doc.paragraphs)

    # ==========================================================================
    # PII masking
    # ==========================================================================

    def mask_pii(self, text: str) -> Tuple[str, dict]:
        """
        Replace personally identifiable information (PII) with neutral tokens.

        Called before any text is sent to an external AI API, ensuring the
        candidate's identity cannot be inferred from the outbound request.

        PII types detected and their replacements:

        ============  ====================  ====================================
        Type          Placeholder           Detection method
        ============  ====================  ====================================
        Email         [EMAIL]               Regex (RFC 5322 subset)
        Phone         [PHONE]               Regex (international formats)
        Street addr.  [ADDRESS]             Regex (road-type suffix)
        Postcode/ZIP  [POSTCODE]            Regex (UK / US / Canada formats)
        LinkedIn URL  [LINKEDIN]            Regex (domain match)
        GitHub URL    [GITHUB]              Regex (domain match)
        Full name     [CANDIDATE NAME]      "Title Case" in first 5 lines only
        ============  ====================  ====================================

        Name detection is intentionally conservative — it only replaces lines
        in the first 5 lines that consist solely of two or three capitalised
        words (the typical CV header layout).  This avoids false positives
        such as company names appearing in the employment history section.

        Parameters
        ----------
        text : str
            Raw CV text as extracted by extract_text_from_file().

        Returns
        -------
        masked_text : str
            A copy of the input with all detected PII replaced by placeholders.
        found : dict
            Maps each PII field name to the count of instances that were
            replaced, e.g. {'email': 1, 'phone': 2, 'name': 1}.
            Returned to the client as a transparency report so the user can
            confirm what was masked.
        """
        masked = text
        found: dict = {}

        def _replace(pattern: re.Pattern, placeholder: str, label: str) -> None:
            """Apply one substitution in-place and record the count."""
            nonlocal masked
            matches = pattern.findall(masked)
            if matches:
                found[label] = len(matches)
                masked = pattern.sub(placeholder, masked)

        # Apply patterns in a deliberate order: email before phone because some
        # email formats (e.g. user+tag@example.com) can partially satisfy the
        # phone regex if the phone pass runs first.
        _replace(self.EMAIL_RE,    '[EMAIL]',    'email')
        _replace(self.PHONE_RE,    '[PHONE]',    'phone')
        _replace(self.ADDRESS_RE,  '[ADDRESS]',  'address')
        _replace(self.POSTCODE_RE, '[POSTCODE]', 'postcode')
        _replace(self.LINKEDIN_RE, '[LINKEDIN]', 'linkedin')
        _replace(self.GITHUB_RE,   '[GITHUB]',   'github')

        # Name detection: scan only the first 5 lines for a "Firstname Lastname"
        # or "Firstname Middle Lastname" pattern — all words must be Title Case.
        lines      = masked.split('\n')
        name_re    = re.compile(r'^[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?$')
        new_lines  = []
        name_count = 0
        for i, line in enumerate(lines):
            if i < 5 and name_re.match(line.strip()):
                new_lines.append('[CANDIDATE NAME]')
                name_count += 1
            else:
                new_lines.append(line)
        if name_count:
            found['name'] = name_count
            masked = '\n'.join(new_lines)

        return masked, found

    # ==========================================================================
    # Text normalisation
    # ==========================================================================

    def _normalise(self, text: str) -> str:
        """
        Return a lowercase, whitespace-stripped copy of *text*.

        All skill and certification comparisons operate on normalised strings
        so that "Python", "python", and "PYTHON" are treated identically.
        """
        return text.lower().strip()

    # ==========================================================================
    # Skill extraction
    # ==========================================================================

    def extract_skills(self, text: str) -> Set[str]:
        """
        Return the set of skills found in *text*.

        Two complementary passes are performed and their results are unioned:

        **Pass 1 — Keyword bank**
            Each entry in SKILL_KEYWORDS is searched in the normalised
            (lowercase) text using a word-boundary-aware regex.  Lookbehind
            ``(?<![a-z])`` and lookahead ``(?![a-z])`` act as word boundaries
            that work correctly for tokens containing '+', '#', or spaces
            (e.g. 'c++', 'machine learning'), unlike the standard ``\b`` which
            treats '+' as a boundary character.

        **Pass 2 — Dynamic capitalised-word detection**
            Proper-noun style tokens not in the keyword bank (e.g. "Terraform",
            "Kubernetes", "FastAPI") are captured by matching the pattern
            ``[A-Z][a-zA-Z0-9]+`` in the *original* (un-normalised) text.
            A blocklist of common English words in Title Case is filtered out
            to prevent false positives like "The", "From", "Must".

        Parameters
        ----------
        text : str
            Document text (job description or CV body).

        Returns
        -------
        Set[str]
            All detected skill tokens as lowercase strings.
        """
        text_lower = self._normalise(text)
        found: Set[str] = set()

        # Pass 1: keyword bank
        for skill in self.SKILL_KEYWORDS:
            pattern = r'(?<![a-z])' + re.escape(skill) + r'(?![a-z])'
            if re.search(pattern, text_lower):
                found.add(skill)

        # Pass 2: capitalised tokens (technology names not in the bank)
        tech_re = re.compile(r'\b([A-Z][a-zA-Z0-9]+(?:\.[a-zA-Z]+)?)\b')

        # Title Case English words that commonly appear in job descriptions but
        # are NOT skills.  Extended as false positives are discovered.
        STOP_WORDS = {
            'The','This','That','With','From','Have','Will','Your','Our',
            'And','For','Are','You','Not','Can','Job','Role','Team','Work',
            'Year','Must','Also','Key','New','Good','Strong','Main','Both',
            'Other','Core','High','Full','Help','Able','Any','All','Has',
            'May','Own','Use','Get','Its',
        }
        for match in tech_re.finditer(text):
            word = match.group(1)
            if len(word) >= 3 and word not in STOP_WORDS:
                found.add(word.lower())

        return found

    # ==========================================================================
    # Certification extraction
    # ==========================================================================

    def extract_certifications(self, text: str) -> Set[str]:
        """
        Return the set of professional certifications mentioned in *text*.

        Each pattern in CERT_PATTERNS is applied with re.IGNORECASE so that
        "pmp", "PMP", and "Pmp" are all caught.  re.FINDALL returns all
        non-overlapping matches; adding them to a set deduplicates them.

        Parameters
        ----------
        text : str
            Document text (job description or CV body).

        Returns
        -------
        Set[str]
            Certification strings as they appear in the document
            (whitespace-stripped), e.g. {'AWS Certified', 'PMP', 'CISSP'}.
        """
        found: Set[str] = set()
        for pattern in self.CERT_PATTERNS:
            for match in re.findall(pattern, text, re.IGNORECASE):
                found.add(match.strip())
        return found

    # ==========================================================================
    # Experience year extraction
    # ==========================================================================

    def extract_experience_years(self, text: str) -> float:
        """
        Return the highest number of years of experience found in *text*.

        Phrasing variants detected include:
          - "5+ years of experience"
          - "minimum 3 years"
          - "at least 7 yrs exp"
          - "experience of 10 years"

        The *maximum* value is returned rather than the first match:
          - In a job description the largest figure is typically the total
            requirement; smaller numbers often describe sub-requirements.
          - In a CV the largest number best reflects the candidate's total
            career span rather than the duration of a single role.

        Parameters
        ----------
        text : str
            Document text (job description or CV body).

        Returns
        -------
        float
            Highest year count found, or 0.0 if no pattern matches.
            0.0 is used as a sentinel meaning "not specified".
        """
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience|exp)',
            r'(\d+)\+?\s*yrs?\s+(?:of\s+)?(?:experience|exp)',
            r'experience\s+of\s+(\d+)\+?\s*years?',
            r'minimum\s+(\d+)\+?\s*years?',
            r'at\s+least\s+(\d+)\+?\s*years?',
        ]
        years = []
        for p in patterns:
            for m in re.finditer(p, text, re.IGNORECASE):
                years.append(float(m.group(1)))
        return max(years) if years else 0.0

    # ==========================================================================
    # Matching helpers
    # ==========================================================================

    def _fuzzy_match(self, a: str, b: str) -> float:
        """
        Return a similarity ratio in [0, 1] between strings *a* and *b*.

        Uses difflib.SequenceMatcher (Ratcliff/Obershelp algorithm):
        ``2.0 * M / T`` where M is the number of matching characters and T is
        the total character count across both strings.

        Examples::

            _fuzzy_match('python', 'python3')   → ~0.92  (very similar)
            _fuzzy_match('react',  'angular')   → ~0.25  (unrelated)
            _fuzzy_match('postgres','postgresql')→ ~0.88  (near match)
        """
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _classify_skill(self, job_skill: str, cv_skills: Set[str]) -> str:
        """
        Classify a single required skill against the candidate's skill set.

        Three checks are evaluated in order; the first match short-circuits
        the remaining checks:

        1. **Exact match** — the lowercased job skill is present in cv_skills.
           Example: job="python", cv contains "python" → 'full'

        2. **Substring match** — either string is a substring of the other.
           Handles version qualifiers and compound names.
           Example: job="python 3", cv has "python"  → 'partial'
           Example: job="node",     cv has "nodejs"  → 'partial'

        3. **Fuzzy match** — _fuzzy_match() similarity exceeds 0.75.
           Catches spelling variants and common abbreviations.
           Example: job="postgresql", cv has "postgres" → 'partial'

        Parameters
        ----------
        job_skill : str
            A single skill token from the job description.
        cv_skills : Set[str]
            All skills extracted from the candidate's CV.

        Returns
        -------
        str
            One of 'full', 'partial', or 'missing'.
        """
        job_lower = job_skill.lower()

        # Check 1: exact
        if job_lower in cv_skills:
            return 'full'

        # Check 2: substring (either direction)
        for cv_skill in cv_skills:
            if cv_skill in job_lower or job_lower in cv_skill:
                return 'partial'

        # Check 3: fuzzy similarity threshold
        for cv_skill in cv_skills:
            if self._fuzzy_match(job_lower, cv_skill) > 0.75:
                return 'partial'

        return 'missing'

    # ==========================================================================
    # Main comparison pipeline (standard mode)
    # ==========================================================================

    def compare(self, job_text: str, cv_text: str) -> ComparisonResult:
        """
        Run the full keyword-based comparison and return a ComparisonResult.

        Pipeline
        --------
        1. Extract skills, certifications, and experience years from both texts.
        2. Classify each required skill / cert as full / partial / missing.
        3. Compute three sub-scores.
        4. Combine sub-scores into a weighted overall score.

        Scoring formulae
        ----------------
        Experience (0–100):
            ``min(candidate_years / required_years, 1.0) × 100``
            Defaults to 100 when no years are stated (cannot penalise an
            unstated requirement).

        Skills (0–100):
            ``(full_matches + 0.5 × partial_matches) / total_required × 100``
            Partial matches earn half a point, rewarding related experience
            without equating it to an exact qualification.

        Certifications (0–100):
            Same formula as skills.  Defaults to 100 when none are required.

        Overall (0–100):
            ``experience × 0.25 + skills × 0.55 + certifications × 0.20``
            Skills carry the highest weight because job descriptions typically
            list many more skills than certifications, making them the richest
            signal for compatibility.

        Parameters
        ----------
        job_text : str
            The pasted job description (plain text).
        cv_text  : str
            Extracted CV text, ideally already PII-masked before calling this.

        Returns
        -------
        ComparisonResult
            Fully populated dataclass with all scores and detail lists.
        """
        result = ComparisonResult()

        # ── Extract features from both documents ──────────────────────────────
        job_skills = self.extract_skills(job_text)
        cv_skills  = self.extract_skills(cv_text)
        job_certs  = self.extract_certifications(job_text)
        cv_certs   = self.extract_certifications(cv_text)
        req_years  = self.extract_experience_years(job_text)
        cand_years = self.extract_experience_years(cv_text)

        # ── Experience score ──────────────────────────────────────────────────
        if req_years == 0:
            exp_score = 100   # No requirement stated → no penalty
            meets_req = True
        else:
            # Cap the ratio at 1.5 before converting to percentage so that a
            # massively over-qualified candidate does not produce a ratio > 1.0
            # that then gets truncated — the intermediate cap gives a cleaner
            # 100% rather than an unexpected lower figure from int() rounding.
            ratio     = min(cand_years / req_years, 1.5)
            exp_score = int(min(ratio * 100, 100))
            meets_req = cand_years >= req_years

        result.experience_match   = exp_score
        result.experience_details = {
            'required':          req_years,
            'candidate':         cand_years,
            'meets_requirement': meets_req,
        }

        # ── Skills score ──────────────────────────────────────────────────────
        matched_skills = []
        partial_skills = []
        missing_skills = []

        for skill in job_skills:
            status = self._classify_skill(skill, cv_skills)
            if status == 'full':
                matched_skills.append(skill)
            elif status == 'partial':
                partial_skills.append(skill)
            else:
                missing_skills.append(skill)

        total_job_skills = len(job_skills)
        if total_job_skills == 0:
            skills_score = 0  # No skills listed → no meaningful signal
        else:
            score_pts    = len(matched_skills) + 0.5 * len(partial_skills)
            skills_score = int((score_pts / total_job_skills) * 100)

        # Skills present in the CV but not required — informational only
        additional = sorted(cv_skills - job_skills)

        result.skills_match   = min(skills_score, 100)
        result.skills_details = {
            'required':   sorted(job_skills),
            'matching':   sorted(matched_skills),
            'partial':    sorted(partial_skills),
            'missing':    sorted(missing_skills),
            'candidate':  sorted(cv_skills),
            'additional': additional[:20],  # cap at 20 to keep the UI clean
        }

        # ── Certifications score ──────────────────────────────────────────────
        cert_matched = []
        cert_partial = []
        cert_missing = []

        for cert in job_certs:
            cert_l = cert.lower()
            exact  = any(cert_l == c.lower() for c in cv_certs)
            # Slightly lower fuzzy threshold for certs (0.70 vs 0.75 for skills)
            # because acronyms are short — a one-character difference still
            # represents a closely related credential (e.g. CKA vs CKAD).
            fuzzy  = any(self._fuzzy_match(cert_l, c.lower()) > 0.70 for c in cv_certs)

            if exact:
                cert_matched.append(cert)
            elif fuzzy:
                cert_partial.append(cert)
            else:
                cert_missing.append(cert)

        total_certs = len(job_certs)
        if total_certs == 0:
            cert_score = 100  # No certs required → no penalty
        else:
            cert_pts   = len(cert_matched) + 0.5 * len(cert_partial)
            cert_score = int((cert_pts / total_certs) * 100)

        result.certifications_match   = cert_score
        result.certifications_details = {
            'required':  sorted(job_certs),
            'matching':  sorted(cert_matched),
            'partial':   sorted(cert_partial),
            'missing':   sorted(cert_missing),
            'candidate': sorted(cv_certs),
        }

        # ── Weighted overall score ────────────────────────────────────────────
        result.overall_score = int(
            exp_score    * 0.25 +   # Experience: 25%
            skills_score * 0.55 +   # Skills:     55% (richest signal)
            cert_score   * 0.20     # Certs:      20%
        )

        return result

    # ==========================================================================
    # AI-powered comparison (delegates to Claude)
    # ==========================================================================

    def compare_with_ai(self, job_text: str, cv_text: str, api_key: str) -> dict:
        """
        Perform a deep CV–job match using Claude (claude-opus-4-5).

        Unlike compare(), this delegates feature extraction and scoring to the
        language model, which understands semantic equivalence, contextual
        relevance, and nuanced phrasing that keyword matching cannot handle.
        Trade-offs: 10–20 s latency per request and Anthropic API costs.

        Privacy
        -------
        mask_pii() is called on the CV text *before* it is included in the
        API request.  The raw unmasked CV is never sent to Anthropic.
        The masking report (pii_found) is attached to the returned dict for
        transparency.

        Prompt design
        -------------
        A structured system prompt instructs Claude to return ONLY a JSON
        object with a fixed schema (no prose, no markdown).  Enumerating the
        exact schema with types in the prompt significantly reduces hallucinated
        keys and incorrect value types compared to a vague "return JSON" prompt.

        JSON fence stripping
        --------------------
        Despite the strict system prompt, Claude may wrap its output in
        ```json ... ``` fences (a common model behaviour on some sampling
        temperatures).  The two re.sub() calls strip any such fences before
        json.loads() so the caller never sees a JSONDecodeError from this
        benign formatting variation.

        Parameters
        ----------
        job_text : str   The pasted job description.
        cv_text  : str   Raw CV text — PII masking is applied internally.
        api_key  : str   A valid Anthropic API key.

        Returns
        -------
        dict
            Parsed AI response augmented with a 'pii_masked' key containing
            the masking report from mask_pii().

        Raises
        ------
        anthropic.APIError
            On authentication failure, quota exceeded, or network error.
        json.JSONDecodeError
            If the model returns unparseable text (caller handles this).
        """
        import anthropic  # Deferred import: keeps startup fast if unused

        masked_cv, pii_found = self.mask_pii(cv_text)

        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = """You are an expert HR analyst and talent acquisition specialist.
Analyse the candidate's CV against the job description and return ONLY valid JSON —
no markdown fences, no preamble, no explanation outside the JSON object.

Return this exact structure:
{
  "overall_match": <integer 0-100>,
  "experience_analysis": {
    "required_years":  <number or null>,
    "candidate_years": <number or null>,
    "score":           <integer 0-100>,
    "assessment":      "<string>"
  },
  "skills_analysis": {
    "required_skills":   ["..."],
    "matched_skills":    ["..."],
    "partial_skills":    ["..."],
    "missing_skills":    ["..."],
    "additional_skills": ["..."],
    "score":             <integer 0-100>,
    "assessment":        "<string>"
  },
  "certifications_analysis": {
    "required_certifications": ["..."],
    "matched_certifications":  ["..."],
    "partial_certifications":  ["..."],
    "missing_certifications":  ["..."],
    "score":                   <integer 0-100>,
    "assessment":              "<string>"
  },
  "strengths":        ["..."],
  "weaknesses":       ["..."],
  "recommendation":   "<string>",
  "cultural_fit":     "<string>",
  "growth_potential": "<string>"
}

Classification rules:
- matched : clearly and explicitly present in the CV
- partial : a related or overlapping skill/cert is present but not an exact match
- missing : not found in the CV in any form
"""
        user_message = (
            f"JOB DESCRIPTION:\n{job_text}\n\n"
            f"CANDIDATE CV (personal information has been masked for privacy):\n{masked_cv}"
        )

        message = client.messages.create(
            model      = "claude-opus-4-5",
            max_tokens = 4096,
            system     = system_prompt,
            messages   = [{"role": "user", "content": user_message}],
        )

        raw = message.content[0].text.strip()

        # Strip markdown fences that Claude sometimes adds despite instructions
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$',          '', raw)

        ai_result = json.loads(raw)
        ai_result['pii_masked'] = pii_found  # Attach masking report
        return ai_result


# =============================================================================
# Module-level singleton
# =============================================================================

# A single CVComparator instance shared across all HTTP requests.
# Safe because the class is fully stateless (no mutable instance attributes).
comparator = CVComparator()


# =============================================================================
# JobScraper — extract job descriptions from public URLs
# =============================================================================

class JobScraper:
    """
    Fetches and extracts plain-text job descriptions from public job-board URLs.

    Design overview
    ---------------
    1. Site-specific extraction  — bespoke CSS selectors for the most common
       job boards (LinkedIn, Indeed, Glassdoor, Reed, Totaljobs, Monster, …).
       These return the cleanest text with no boilerplate.
    2. Generic semantic fallback — looks for <article>, <main>, or the largest
       <div> block with substantial text.  Covers company career pages and
       smaller boards not in the specific list.
    3. Text cleaning             — collapses whitespace, removes navigation
       fragments, and strips cookie/GDPR banners.

    All network calls carry a realistic browser User-Agent so that sites which
    block default Python requests headers still respond normally.  A 15-second
    timeout prevents the server from hanging on slow or unresponsive pages.
    """

    # Realistic browser User-Agent to avoid 403s from bot-protection middleware
    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    # ── Site-specific selectors ───────────────────────────────────────────────
    # Maps a hostname fragment to a list of CSS selectors tried in order.
    # The first selector that returns non-empty text wins.
    SITE_SELECTORS = {
        'linkedin.com': [
            '.description__text',
            '.show-more-less-html__markup',
            '[class*="job-description"]',
            '.jobs-description',
        ],
        'indeed.com': [
            '#jobDescriptionText',
            '.jobsearch-jobDescriptionText',
            '[data-testid="job-description"]',
        ],
        'glassdoor.com': [
            '[class*="JobDetails_jobDescription"]',
            '.desc',
            '[data-test="description"]',
        ],
        'reed.co.uk': [
            '[data-qa="job-description"]',
            '.description',
            '#job-detail-description',
        ],
        'totaljobs.com': [
            '[data-automation="jobDescription"]',
            '.job-description',
        ],
        'monster.com': [
            '#JobDescription',
            '.job-description',
        ],
        'jobsite.co.uk': [
            '.job-description',
            '[data-ui="job-description"]',
        ],
        'cv-library.co.uk': [
            '#job-description',
            '.job-description-body',
        ],
        'seek.com.au': [
            '[data-automation="jobDescription"]',
            '.job-description',
        ],
        'stepstone.de': [
            '[class*="jobDescription"]',
            '.at-section-text-description',
        ],
        'xing.com': [
            '[class*="job-description"]',
            '.description',
        ],
    }

    # Text fragments that indicate navigation / cookie banners — lines
    # containing these are stripped from the extracted text.
    NOISE_FRAGMENTS = [
        'cookie', 'privacy policy', 'terms of service', 'accept all',
        'sign in', 'log in', 'create account', 'back to jobs',
        'save job', 'report job', 'share job', 'apply now',
        'similar jobs', 'you might also like',
    ]

    # Minimum character length for a block of text to be considered a job
    # description rather than a page fragment.
    MIN_JOB_TEXT_LENGTH = 200

    def fetch(self, url: str) -> dict:
        """
        Fetch and extract a job description from *url*.

        Parameters
        ----------
        url : str
            A fully qualified URL (must start with http:// or https://).

        Returns
        -------
        dict with keys:
            text        : str   — extracted job description text
            source_url  : str   — the final URL after any redirects
            site_name   : str   — human-readable site name (e.g. "LinkedIn")
            char_count  : int   — length of extracted text
            method      : str   — 'site-specific' | 'semantic' | 'full-body'

        Raises
        ------
        ValueError
            If the URL is missing, malformed, or not HTTP/HTTPS.
        RuntimeError
            If the scraping packages are not installed, the server returned
            an error status, or no usable text could be extracted.
        """
        if not SCRAPING_AVAILABLE:
            raise RuntimeError(
                'Web scraping requires the requests and beautifulsoup4 packages. '
                'Run: pip install requests beautifulsoup4 lxml'
            )

        url = url.strip()
        if not url:
            raise ValueError('URL is required.')
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            response = http_requests.get(
                url,
                headers=self.HEADERS,
                timeout=15,
                allow_redirects=True,
            )
        except http_requests.exceptions.Timeout:
            raise RuntimeError('The request timed out. The site may be slow or blocking automated access.')
        except http_requests.exceptions.ConnectionError:
            raise RuntimeError('Could not connect to the URL. Check that it is correct and publicly accessible.')
        except http_requests.exceptions.RequestException as exc:
            raise RuntimeError(f'Network error: {exc}')

        if response.status_code == 403:
            raise RuntimeError(
                'Access denied (403). This site blocks automated access. '
                'Please copy and paste the job description manually.'
            )
        if response.status_code == 404:
            raise RuntimeError('Page not found (404). Check the URL is correct and the job posting is still live.')
        if not response.ok:
            raise RuntimeError(f'The server returned HTTP {response.status_code}.')

        soup = BeautifulSoup(response.text, 'lxml')

        # Remove script, style, nav, header, footer, and cookie-banner elements
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                   'aside', 'noscript', 'iframe']):
            tag.decompose()

        final_url  = response.url
        site_name  = self._site_name(final_url)

        # Try site-specific extraction first
        text, method = self._site_specific(soup, final_url)

        # Fall back to semantic extraction
        if not text or len(text) < self.MIN_JOB_TEXT_LENGTH:
            text, method = self._semantic(soup)

        # Last resort: entire body text
        if not text or len(text) < self.MIN_JOB_TEXT_LENGTH:
            body = soup.find('body')
            text   = self._clean(body.get_text(separator='\n') if body else '')
            method = 'full-body'

        if not text or len(text) < self.MIN_JOB_TEXT_LENGTH:
            raise RuntimeError(
                'Could not extract a job description from this page. '
                'The site may require login or block automated access. '
                'Please paste the job description manually.'
            )

        return {
            'text':       text,
            'source_url': final_url,
            'site_name':  site_name,
            'char_count': len(text),
            'method':     method,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _site_name(self, url: str) -> str:
        """Return a human-readable site name from a URL."""
        for fragment in self.SITE_SELECTORS:
            if fragment in url:
                return fragment.split('.')[0].capitalize()
        # Fall back to the second-level domain
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname or ''
            parts = host.replace('www.', '').split('.')
            return parts[0].capitalize() if parts else 'Unknown'
        except Exception:
            return 'Unknown'

    def _site_specific(self, soup: 'BeautifulSoup', url: str):
        """Try each site-specific selector list and return the first hit."""
        for fragment, selectors in self.SITE_SELECTORS.items():
            if fragment in url:
                for selector in selectors:
                    el = soup.select_one(selector)
                    if el:
                        text = self._clean(el.get_text(separator='\n'))
                        if len(text) >= self.MIN_JOB_TEXT_LENGTH:
                            return text, 'site-specific'
        return '', 'none'

    def _semantic(self, soup: 'BeautifulSoup'):
        """
        Find the most content-dense block using semantic HTML elements and
        heuristics when no site-specific selector matched.
        """
        # Priority: <article> > <main> > largest <div> with text
        for tag_name in ('article', 'main'):
            el = soup.find(tag_name)
            if el:
                text = self._clean(el.get_text(separator='\n'))
                if len(text) >= self.MIN_JOB_TEXT_LENGTH:
                    return text, 'semantic'

        # Find the <div> with the most text (likely the job description container)
        best, best_len = None, 0
        for div in soup.find_all('div'):
            t = div.get_text(separator=' ', strip=True)
            if len(t) > best_len:
                best, best_len = div, len(t)

        if best and best_len >= self.MIN_JOB_TEXT_LENGTH:
            return self._clean(best.get_text(separator='\n')), 'semantic'

        return '', 'none'

    def _clean(self, raw: str) -> str:
        """
        Clean raw scraped text:
        - Collapse runs of blank lines to a single blank line
        - Strip lines that are pure navigation / cookie noise
        - Remove very short lines (< 3 chars) that are layout artefacts
        """
        lines = raw.splitlines()
        cleaned = []
        prev_blank = False
        for line in lines:
            stripped = line.strip()

            # Skip noise lines
            if any(frag in stripped.lower() for frag in self.NOISE_FRAGMENTS):
                continue
            # Skip very short artefact lines
            if stripped and len(stripped) < 3:
                continue

            is_blank = (stripped == '')
            if is_blank and prev_blank:
                continue  # collapse consecutive blanks

            cleaned.append(stripped)
            prev_blank = is_blank

        return '\n'.join(cleaned).strip()


# Singleton scraper instance
scraper = JobScraper()




@app.route('/')
def index():
    """
    Serve the main application UI (GET /).

    Query parameters
    ----------------
    lang : str, optional
        BCP-47 language code (default 'en').  Selects the translation strings
        passed to the Jinja2 template and whether RTL layout is applied.

    Template variables injected
    ---------------------------
    lang                : str   Active language code.
    translations        : dict  UI strings for the active language.
    supported_languages : dict  {code: display_name} for the dropdown.
    env_key_set         : bool  True when ANTHROPIC_API_KEY is configured.
                                The template hides the API key input and shows
                                a confirmation badge when this is True.
    """
    lang         = request.args.get('lang', 'en')
    translations = TRANSLATIONS.get(lang, TRANSLATIONS.get('en', {}))
    return render_template(
        'Index.html',
        lang                = lang,
        translations        = translations,
        all_translations    = TRANSLATIONS,
        supported_languages = SUPPORTED_LANGUAGES,
        env_key_set         = bool(_ENV_API_KEY),
    )


@app.route('/api_key_status')
def api_key_status():
    """
    Report whether a server-side Anthropic API key is configured (GET).

    Useful for frontend code that is not rendered by Jinja2 (e.g. a React
    SPA) and cannot read template variables directly.

    Response
    --------
    200 OK  →  {"configured": true}  or  {"configured": false}
    """
    return jsonify({'configured': bool(_ENV_API_KEY)})


@app.route('/fetch_job_url', methods=['POST'])
def fetch_job_url():
    """
    Fetch and extract a job description from a public URL (POST /fetch_job_url).

    Accepts JSON or form data with a single field:
      - url (str) — the job posting URL to scrape

    Uses JobScraper which tries site-specific CSS selectors first (LinkedIn,
    Indeed, Glassdoor, Reed, …) then falls back to semantic HTML extraction.

    Success response (200)
    ----------------------
    {
      "text":       str,   — extracted job description text
      "source_url": str,   — final URL after redirects
      "site_name":  str,   — human-readable site name
      "char_count": int,   — character count of extracted text
      "method":     str    — extraction method used
    }

    Error responses
    ---------------
    400 — URL missing or invalid.
    403 — Site blocked automated access.
    422 — URL fetched but no usable text could be extracted.
    500 — Unexpected server error.
    """
    try:
        # Accept both JSON body and form data
        if request.is_json:
            url = (request.json or {}).get('url', '').strip()
        else:
            url = request.form.get('url', '').strip()

        if not url:
            return jsonify({'error': 'A URL is required.'}), 400

        result = scraper.fetch(url)
        return jsonify(result)

    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except RuntimeError as exc:
        msg = str(exc)
        status = 403 if '403' in msg else 422 if 'extract' in msg.lower() else 500
        return jsonify({'error': msg}), status
    except Exception as exc:
        return jsonify({'error': f'Unexpected error: {exc}'}), 500


@app.route('/compare', methods=['POST'])
def compare():
    """
    Run the standard keyword-based CV–job comparison (POST /compare).

    Expects multipart/form-data with:
      - job_description (str)  — pasted job description text
      - cv_file         (file) — candidate's CV (PDF, DOCX, or TXT)

    Processing
    ----------
    1. Validate inputs (400 if missing).
    2. Extract text from the uploaded file.
    3. Mask PII from the CV text.
    4. Run CVComparator.compare() on job text + masked CV.
    5. Return all scores and detail lists as JSON.

    Success response (200)
    ----------------------
    {
      "overall_score":          int,
      "experience_match":       int,
      "skills_match":           int,
      "certifications_match":   int,
      "experience_details":     {required, candidate, meets_requirement},
      "skills_details":         {required, matching, partial, missing,
                                 candidate, additional},
      "certifications_details": {required, matching, partial, missing,
                                 candidate},
      "pii_masked":             {field: count, ...}
    }

    Error responses
    ---------------
    400 — Missing or empty input field (message in 'error').
    500 — Unexpected server error (message in 'error').
    """
    try:
        job_spec = request.form.get('job_description', '').strip()
        if not job_spec:
            return jsonify({'error': 'Job description text is required.'}), 400

        if 'cv_file' not in request.files or not request.files['cv_file'].filename:
            return jsonify({'error': 'CV file is required.'}), 400

        cv_file   = request.files['cv_file']
        cv_text   = comparator.extract_text_from_file(cv_file, cv_file.filename)
        masked_cv, pii_found = comparator.mask_pii(cv_text)
        result    = comparator.compare(job_spec, masked_cv)

        return jsonify({
            'overall_score':          result.overall_score,
            'experience_match':       result.experience_match,
            'skills_match':           result.skills_match,
            'certifications_match':   result.certifications_match,
            'experience_details':     result.experience_details,
            'skills_details':         result.skills_details,
            'certifications_details': result.certifications_details,
            'pii_masked':             pii_found,
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/compare_ai', methods=['POST'])
def compare_ai():
    """
    Run the AI-powered CV–job comparison via Claude (POST /compare_ai).

    API key resolution (priority order)
    ------------------------------------
    1. ANTHROPIC_API_KEY environment variable (set via .env or shell).
    2. api_key field in the POST form body (fallback for users without a
       server-side key).

    If neither provides a key a 400 is returned immediately with an actionable
    error message rather than propagating a cryptic authentication error from
    the Anthropic SDK.

    Expects multipart/form-data with:
      - job_description (str)           — pasted job description text
      - cv_file         (file)          — candidate's CV (PDF, DOCX, or TXT)
      - api_key         (str, optional) — only needed if no env key is set

    Success response (200)
    ----------------------
    {
      "success":     true,
      "ai_analysis": {
        "overall_match":              int,
        "experience_analysis":        {..., "assessment": str},
        "skills_analysis":            {..., "assessment": str},
        "certifications_analysis":    {...},
        "strengths":                  [str, ...],
        "weaknesses":                 [str, ...],
        "recommendation":             str,
        "cultural_fit":               str,
        "growth_potential":           str,
        "pii_masked":                 {field: count, ...}
      }
    }

    Error responses
    ---------------
    400 — Missing input or no API key available.
    500 — Server error or AI response could not be parsed as JSON.
    """
    try:
        # Environment key takes precedence; form key is the user-supplied fallback
        api_key = _ENV_API_KEY or request.form.get('api_key', '').strip()

        if not api_key:
            return jsonify({
                'error': (
                    'No API key found.  Set ANTHROPIC_API_KEY in your .env file '
                    'or enter it in the form.'
                )
            }), 400

        job_spec = request.form.get('job_description', '').strip()
        if not job_spec:
            return jsonify({'error': 'Job description text is required.'}), 400
        if 'cv_file' not in request.files or not request.files['cv_file'].filename:
            return jsonify({'error': 'CV file is required.'}), 400

        cv_file   = request.files['cv_file']
        cv_text   = comparator.extract_text_from_file(cv_file, cv_file.filename)
        ai_result = comparator.compare_with_ai(job_spec, cv_text, api_key)

        return jsonify({'success': True, 'ai_analysis': ai_result})

    except json.JSONDecodeError:
        # The AI returned non-JSON text — very rare but possible under load.
        # Return a user-friendly message rather than a cryptic parse error.
        return jsonify({
            'error': 'AI returned an unparseable response.  Please try again.'
        }), 500
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


# =============================================================================
# Entry point
# =============================================================================

if __name__ == '__main__':
    # Print key status at startup so the developer immediately knows whether
    # ANTHROPIC_API_KEY was picked up before making any requests.
    if _ENV_API_KEY:
        print(' * API key status : ✓ ANTHROPIC_API_KEY loaded from environment')
    else:
        print(' * API key status : ✗ ANTHROPIC_API_KEY not set — '
              'AI mode will prompt users for a key in the form')
    app.run(debug=True, port=5000)