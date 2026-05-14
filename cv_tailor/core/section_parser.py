"""
Section parser - detects subsections within each CV section.

For a section like "Work Experience", each job entry is a subsection.
For "Education", each institution is a subsection.
For "Projects", each project is a subsection.

Subsection titles are identified by heuristics:
  - Short lines (< 80 chars) that are not bullet points
  - Contain a year, OR follow a blank line, OR are bold-style ALL CAPS
  - Followed by substantive content lines
"""
import re
from typing import List
from core.models import CVSection, CVSubSection


# Sections where we try to detect subsections
_SUBSECTION_SECTIONS = {
    "work experience", "experience", "employment", "employment history",
    "expérience professionnelle", "expérience", "emploi",
    "berufserfahrung", "erfahrung",
    "experiencia profesional", "experiencia",
    "職務経歴", "实习经历", "工作经历",
    "education", "formation", "ausbildung", "educación", "学歴", "教育经历",
    "projects", "projets", "projekte", "proyectos", "プロジェクト", "项目",
    "certifications", "certifications", "zertifizierungen",
    "certificaciones", "資格", "证书",
    "publications", "publications", "veröffentlichungen",
    "publicaciones", "出版物", "发表作品",
}

# Date patterns inside a line that suggest a heading
_DATE_RE = re.compile(
    r'\b(19|20)\d{2}\b'                    # year
    r'|(\d{1,2}[/-]\d{4})'                # MM/YYYY
    r'|(\d{4}\s*[-–]\s*(\d{4}|present|current|aujourd\'hui|heute|actualidad|現在|至今))',
    re.IGNORECASE,
)

# Lines that are clearly bullet content (not titles)
_BULLET_RE = re.compile(r'^[•\-\*\►\▸\◆\○\●\d\.]\s+')


def _is_subsection_title(line: str, next_lines: List[str]) -> bool:
    """Heuristically decide if a line is a subsection heading."""
    stripped = line.strip()
    if not stripped or len(stripped) < 3 or len(stripped) > 100:
        return False
    if _BULLET_RE.match(stripped):
        return False
    # Contains a year
    if _DATE_RE.search(stripped):
        return True
    # ALL CAPS short line (company or institution name)
    if stripped.isupper() and len(stripped) < 60:
        return True
    # Title-case, short, followed by bullet content
    words = stripped.split()
    if len(words) <= 8:
        has_content_below = any(
            _BULLET_RE.match(l.strip()) or (l.strip() and len(l.strip()) > 20)
            for l in next_lines[:3]
        )
        if has_content_below and stripped[0].isupper():
            return True
    return False


def detect_subsections(section: CVSection) -> List[CVSubSection]:
    """
    Parse a section's raw_text and detect subsections within it.
    Returns a list of CVSubSection objects.
    """
    section_lower = section.name.lower().strip()
    if not any(s in section_lower for s in _SUBSECTION_SECTIONS):
        return []

    lines = [l for l in section.raw_text.split('\n')]
    subsections: List[CVSubSection] = []
    current_title = ""
    current_lines: List[str] = []

    def _flush(title: str, content_lines: List[str]):
        content = '\n'.join(l for l in content_lines).strip()
        if content:
            subsections.append(CVSubSection(
                title=title or section.name,
                content=content,
            ))

    for i, line in enumerate(lines):
        next_lines = lines[i+1:i+4]
        if _is_subsection_title(line, next_lines):
            if current_title or current_lines:
                _flush(current_title, current_lines)
            current_title = line.strip()
            current_lines = []
        else:
            if line.strip():
                current_lines.append(line)

    # Flush last subsection
    if current_title or current_lines:
        _flush(current_title, current_lines)

    return subsections


def enrich_sections_with_subsections(sections: List[CVSection]) -> List[CVSection]:
    """
    Detect and attach subsections to every CVSection in-place.
    Returns the same list for chaining.
    """
    for section in sections:
        if not section.subsections:
            section.subsections = detect_subsections(section)
    return sections