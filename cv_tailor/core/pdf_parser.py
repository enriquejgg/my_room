"""
PDF Parser — extracts structured text from CV and Job Description PDFs.
Uses pdfplumber for accurate text extraction with positional data.
"""
import re
from typing import List, Tuple, Optional
from pathlib import Path

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("WARNING: pdfplumber not installed. Install with: pip install pdfplumber")

from core.models import CVSection


# Common CV section headings to detect
SECTION_HEADINGS = [
    r"professional\s+summary", r"summary", r"objective", r"profile",
    r"work\s+experience", r"experience", r"employment", r"employment\s+history",
    r"education", r"academic\s+background", r"qualifications",
    r"skills", r"technical\s+skills", r"core\s+competencies", r"key\s+skills",
    r"certifications?", r"licenses?", r"awards?", r"achievements?",
    r"projects?", r"publications?", r"references?", r"languages?",
    r"volunteer", r"interests?", r"hobbies", r"extracurricular",
]

# Compile combined heading pattern
_HEADING_RE = re.compile(
    r'^\s*(' + '|'.join(SECTION_HEADINGS) + r')\s*:?\s*$',
    re.IGNORECASE | re.MULTILINE
)

# Detect lines that look like section headings (ALL CAPS, short, no period)
_CAPS_HEADING_RE = re.compile(r'^[A-Z][A-Z\s&/\-]{3,40}$')


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, List[str]]:
    """
    Extract full text and per-page text from a PDF file.

    Returns:
        (full_text, pages_text) — concatenated text and list of per-page strings
    """
    if not PDF_AVAILABLE:
        raise RuntimeError("pdfplumber is not installed. Run: pip install pdfplumber")

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pages_text: List[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages_text.append(text)

    full_text = "\n".join(pages_text)
    return full_text, pages_text


def extract_text_from_txt(txt_content: str) -> str:
    """Return plain text content as-is (for pasted job descriptions)."""
    return txt_content.strip()


def parse_cv_sections(full_text: str) -> List[CVSection]:
    """
    Parse a CV's full text into structured CVSection objects.
    Detects section headings and groups content accordingly.
    """
    lines = full_text.split('\n')
    sections: List[CVSection] = []
    current_section_name = "Header"
    current_lines: List[str] = []
    char_offset = 0

    def _is_heading(line: str) -> bool:
        stripped = line.strip()
        if not stripped or len(stripped) > 60:
            return False
        # Match known headings
        if _HEADING_RE.match(stripped):
            return True
        # ALL CAPS line with no trailing punctuation
        if _CAPS_HEADING_RE.match(stripped) and not stripped.endswith('.'):
            return True
        return False

    def _flush_section(name: str, content_lines: List[str], start: int):
        """Save a completed section."""
        raw = '\n'.join(content_lines).strip()
        if raw:
            bullets = _extract_bullets(raw)
            end = start + len(raw)
            sections.append(CVSection(
                name=name,
                raw_text=raw,
                bullets=bullets,
                char_start=start,
                char_end=end
            ))

    for line in lines:
        if _is_heading(line):
            # Save previous section
            _flush_section(current_section_name, current_lines, char_offset)
            char_offset += sum(len(l) + 1 for l in current_lines)
            current_section_name = line.strip().title()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    _flush_section(current_section_name, current_lines, char_offset)

    return sections if sections else [
        CVSection(name="Full CV", raw_text=full_text,
                  bullets=_extract_bullets(full_text))
    ]


def _extract_bullets(text: str) -> List[str]:
    """
    Extract bullet points or meaningful lines from a text block.
    Handles •, -, *, numbered lists, and plain paragraphs.
    """
    bullets = []
    bullet_re = re.compile(r'^[\•\-\*\►\▸\◆\○\●]\s+(.+)', re.MULTILINE)
    numbered_re = re.compile(r'^\d+[\.\)]\s+(.+)', re.MULTILINE)

    # Try bullet extraction
    found = bullet_re.findall(text) + numbered_re.findall(text)
    if found:
        return [b.strip() for b in found if b.strip()]

    # Fall back to non-empty lines
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped and len(stripped) > 10:
            bullets.append(stripped)

    return bullets


def extract_jd_keywords(jd_text: str) -> List[str]:
    """
    Extract important keywords and skill phrases from a job description.
    Returns a deduplicated list of relevant terms.
    """
    # Common stop words to exclude
    stop_words = {
        'the', 'and', 'or', 'in', 'at', 'to', 'for', 'of', 'a', 'an',
        'is', 'are', 'was', 'were', 'will', 'be', 'with', 'on', 'by',
        'this', 'that', 'we', 'you', 'they', 'our', 'your', 'their',
        'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could',
        'should', 'would', 'may', 'might', 'must', 'shall',
        'as', 'it', 'its', 'from', 'into', 'about', 'than', 'more',
        'also', 'well', 'such', 'including', 'following', 'required',
        'preferred', 'experience', 'years', 'ability', 'knowledge',
        'strong', 'excellent', 'good', 'proven', 'demonstrated',
    }

    # Extract multi-word technical phrases first (2-3 words)
    phrase_re = re.compile(
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|[A-Z]{2,}(?:\s+[A-Z]{2,})*)\b'
    )
    phrases = phrase_re.findall(jd_text)

    # Extract single important words
    word_re = re.compile(r'\b([A-Za-z][a-z]{2,}(?:[A-Z][a-z]+)*)\b')
    words = [w for w in word_re.findall(jd_text) if w.lower() not in stop_words]

    # Combine and deduplicate, keeping longer phrases
    all_terms = list(dict.fromkeys(phrases + words))

    # Filter to reasonable length
    keywords = [t for t in all_terms if 2 < len(t) < 50]

    # Sort by length (longer phrases = more specific = more valuable)
    keywords.sort(key=len, reverse=True)

    return keywords[:80]  # Return top 80 keywords