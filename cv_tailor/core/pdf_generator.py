"""
PDF Generator — rebuilds the final CV PDF with only accepted suggestions applied.
Preserves the original text layout as closely as possible.
Uses ReportLab for PDF generation.
"""
import re
from typing import List, Dict, Optional
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        KeepTogether, ListFlowable, ListItem
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("WARNING: reportlab not installed. Run: pip install reportlab")

from core.models import Suggestion, CVSection, SuggestionStatus


# ── Style Constants ──────────────────────────────────────────────────────────

FONT_NORMAL = "Helvetica"
FONT_BOLD   = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"

COLOR_BLACK     = colors.HexColor("#1a1a1a")
COLOR_HEADING   = colors.HexColor("#1a1a2e")
COLOR_RULE      = colors.HexColor("#4a4e69")
COLOR_HIGHLIGHT = colors.HexColor("#e8f4fd")  # Light blue for changed text


class CVPDFGenerator:
    """
    Generates a PDF from modified CV text, applying accepted suggestions.

    Strategy:
    1. Build a replacement dictionary: original_text → final_text
    2. Walk original CV sections, applying replacements
    3. Render the modified text with clean, professional formatting
    """

    def __init__(
        self,
        cv_sections: List[CVSection],
        suggestions: List[Suggestion],
        output_path: str,
    ):
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "reportlab is not installed. Run: pip install reportlab"
            )

        self.sections = cv_sections
        self.output_path = output_path

        # Build replacement map from accepted suggestions
        self.replacements: Dict[str, str] = {
            s.original_text: s.final_text
            for s in suggestions
            if s.status == SuggestionStatus.ACCEPTED
        }

    def generate(self) -> str:
        """Build and write the PDF. Returns the output path."""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = self._build_styles()
        story = []

        for section in self.sections:
            if not section.raw_text.strip():
                continue

            if section.name.lower() == "header":
                story.extend(self._render_header(section, styles))
            else:
                story.extend(self._render_section(section, styles))

            story.append(Spacer(1, 4))

        doc.build(story)
        return self.output_path

    # ── Rendering helpers ────────────────────────────────────────────────────

    def _render_header(
        self, section: CVSection, styles: dict
    ) -> list:
        """Render the CV header (name, contact info)."""
        elements = []
        lines = [l.strip() for l in section.raw_text.split('\n') if l.strip()]
        if not lines:
            return elements

        # First line = name
        name = self._apply_replacements(lines[0])
        elements.append(Paragraph(name, styles["name"]))

        # Remaining header lines = contact info
        for line in lines[1:]:
            modified = self._apply_replacements(line)
            elements.append(Paragraph(modified, styles["contact"]))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(
            width="100%", thickness=2, color=COLOR_RULE, spaceAfter=4
        ))
        return elements

    def _render_section(
        self, section: CVSection, styles: dict
    ) -> list:
        """Render a named CV section with heading and content."""
        elements = []

        # Section heading
        elements.append(Paragraph(
            section.name.upper(), styles["section_heading"]
        ))
        elements.append(HRFlowable(
            width="100%", thickness=0.5, color=COLOR_RULE, spaceAfter=4
        ))

        # Content — try to detect bullets vs paragraphs
        modified_text = self._apply_replacements(section.raw_text)
        lines = [l.strip() for l in modified_text.split('\n') if l.strip()]

        for line in lines:
            if self._is_bullet(line):
                clean = re.sub(r'^[•\-\*\►\▸\◆\○\●\d\.\)]+\s*', '', line).strip()
                elements.append(Paragraph(
                    f"• {clean}", styles["bullet"]
                ))
            elif self._is_subheading(line):
                elements.append(Paragraph(line, styles["subheading"]))
            elif len(line) < 60 and line.isupper():
                # Company / institution name
                elements.append(Paragraph(line, styles["company"]))
            else:
                elements.append(Paragraph(line, styles["body"]))

        return elements

    def _apply_replacements(self, text: str) -> str:
        """Apply accepted suggestion replacements to a text block."""
        for original, replacement in self.replacements.items():
            if original in text:
                text = text.replace(original, replacement)
        return text

    @staticmethod
    def _is_bullet(line: str) -> bool:
        return bool(re.match(r'^[•\-\*\►\▸\◆\○\●]', line))

    @staticmethod
    def _is_subheading(line: str) -> bool:
        """Short line that ends with a year range or looks like a job title."""
        if re.search(r'\b(19|20)\d{2}\b', line) and len(line) < 80:
            return True
        return False

    # ── Style builder ────────────────────────────────────────────────────────

    @staticmethod
    def _build_styles() -> dict:
        """Build and return a dict of named ParagraphStyles."""
        base = getSampleStyleSheet()

        return {
            "name": ParagraphStyle(
                "name",
                fontName=FONT_BOLD,
                fontSize=20,
                textColor=COLOR_HEADING,
                spaceAfter=2,
                alignment=TA_CENTER,
            ),
            "contact": ParagraphStyle(
                "contact",
                fontName=FONT_NORMAL,
                fontSize=9,
                textColor=colors.HexColor("#555555"),
                spaceAfter=1,
                alignment=TA_CENTER,
            ),
            "section_heading": ParagraphStyle(
                "section_heading",
                fontName=FONT_BOLD,
                fontSize=11,
                textColor=COLOR_HEADING,
                spaceBefore=10,
                spaceAfter=2,
                letterSpacing=1,
            ),
            "subheading": ParagraphStyle(
                "subheading",
                fontName=FONT_BOLD,
                fontSize=10,
                textColor=COLOR_BLACK,
                spaceBefore=6,
                spaceAfter=1,
            ),
            "company": ParagraphStyle(
                "company",
                fontName=FONT_ITALIC,
                fontSize=10,
                textColor=colors.HexColor("#444444"),
                spaceAfter=2,
            ),
            "body": ParagraphStyle(
                "body",
                fontName=FONT_NORMAL,
                fontSize=10,
                textColor=COLOR_BLACK,
                spaceAfter=3,
                leading=14,
                alignment=TA_JUSTIFY,
            ),
            "bullet": ParagraphStyle(
                "bullet",
                fontName=FONT_NORMAL,
                fontSize=10,
                textColor=COLOR_BLACK,
                leftIndent=12,
                spaceAfter=2,
                leading=13,
            ),
        }


def generate_final_pdf(
    cv_sections: List[CVSection],
    suggestions: List[Suggestion],
    output_path: str,
) -> str:
    """
    Convenience function: generate the final CV PDF.
    Returns the output file path.
    """
    generator = CVPDFGenerator(cv_sections, suggestions, output_path)
    return generator.generate()


def build_modified_text(
    cv_sections: List[CVSection],
    suggestions: List[Suggestion],
) -> str:
    """
    Build a plain-text version of the CV with accepted changes applied.
    Useful for preview before PDF generation.
    """
    replacements = {
        s.original_text: s.final_text
        for s in suggestions
        if s.status == SuggestionStatus.ACCEPTED
    }

    lines = []
    for section in cv_sections:
        if section.name.lower() != "header":
            lines.append(f"\n{'=' * 40}")
            lines.append(section.name.upper())
            lines.append('=' * 40)

        text = section.raw_text
        for orig, rep in replacements.items():
            text = text.replace(orig, rep)
        lines.append(text)

    return "\n".join(lines)