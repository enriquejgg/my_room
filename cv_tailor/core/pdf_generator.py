"""
PDF Generator - surgically edits the ORIGINAL CV PDF in-place.

Preserves 100% of the original:
  - Font typefaces (Verdana, Times New Roman, etc. extracted from the PDF itself)
  - Font sizes, weights, and colors (red headings, bold names, colored links)
  - Two-column layout, spacing, margins, images, decorative elements

Strategy per accepted suggestion:
  1. Search for original_text across all pages.
  2. Sample exact font name, size, and color from the matching span.
  3. Extract the embedded font bytes from the PDF to a temp file.
  4. Redact (white-box) the original text area.
  5. Re-insert replacement text using fontfile= with the extracted bytes.

Requires: pymupdf >= 1.24  (pip install pymupdf)
Fallback:  reportlab plain rebuild when pymupdf is unavailable.
"""
import os
import tempfile
from typing import List, Dict, Tuple, Optional

from core.models import Suggestion, CVSection, SuggestionStatus

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _int_to_rgb(color_int: int) -> Tuple[float, float, float]:
    r = ((color_int >> 16) & 0xFF) / 255.0
    g = ((color_int >>  8) & 0xFF) / 255.0
    b = ( color_int        & 0xFF) / 255.0
    return (r, g, b)


def _normalise_name(basename: str) -> str:
    """Strip PDF subset prefix e.g. 'AAAAAF+Verdana' -> 'verdana'."""
    return basename.split('+')[-1].lower().replace('-', '').replace(' ', '')


# ─────────────────────────────────────────────────────────────────────────────
# Font registry - extracts all embedded fonts to temp files once per document
# ─────────────────────────────────────────────────────────────────────────────

class FontRegistry:
    """
    Extracts every embedded font from the source PDF to temporary files.
    Provides lookup by font name or xref.
    All temp files are deleted on cleanup().
    """

    def __init__(self, doc: "fitz.Document"):
        self._doc = doc
        self._xref_to_path: Dict[int, str] = {}   # xref -> temp file path
        self._name_to_path: Dict[str, str] = {}   # normalised name -> temp file path
        self._extract_all()

    def _extract_all(self):
        seen = set()
        for page_num in range(len(self._doc)):
            for font_tuple in self._doc.get_page_fonts(page_num):
                xref     = font_tuple[0]
                ext      = font_tuple[1]   # 'ttf', 'otf', etc.
                basename = font_tuple[3]   # e.g. 'AAAAAF+Verdana'

                if xref in seen:
                    continue
                seen.add(xref)

                try:
                    font_data = self._doc.extract_font(xref)
                    buf = font_data[3]
                    if not buf or len(buf) < 500:
                        continue

                    suffix = '.' + (ext if ext else 'ttf')
                    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                    tmp.write(buf)
                    tmp.close()

                    self._xref_to_path[xref] = tmp.name

                    norm = _normalise_name(basename)
                    # Keep the largest file for each name (most complete subset)
                    if norm not in self._name_to_path:
                        self._name_to_path[norm] = tmp.name
                    elif os.path.getsize(tmp.name) > os.path.getsize(self._name_to_path[norm]):
                        self._name_to_path[norm] = tmp.name

                except Exception:
                    continue

    def path_for_name(self, font_name: str) -> Optional[str]:
        """Return temp file path for the best matching font name."""
        norm = _normalise_name(font_name)
        # Exact
        if norm in self._name_to_path:
            return self._name_to_path[norm]
        # Substring match
        for key, path in self._name_to_path.items():
            if key in norm or norm in key:
                return path
        # Style fallback
        is_bold = 'bold' in norm
        for key, path in self._name_to_path.items():
            if is_bold and 'bold' in key:
                return path
            if not is_bold and 'bold' not in key:
                return path
        return next(iter(self._name_to_path.values()), None)

    def cleanup(self):
        """Delete all temporary font files."""
        deleted = set()
        for path in list(self._xref_to_path.values()) + list(self._name_to_path.values()):
            if path not in deleted and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass
                deleted.add(path)


# ─────────────────────────────────────────────────────────────────────────────
# Span style sampler
# ─────────────────────────────────────────────────────────────────────────────

class SpanStyle:
    __slots__ = ("font_name", "size", "color_rgb")

    def __init__(self, font_name: str, size: float, color_int: int):
        self.font_name  = font_name
        self.size       = size
        self.color_rgb  = _int_to_rgb(color_int)


def _sample_style(page: "fitz.Page", rect: "fitz.Rect") -> SpanStyle:
    """Return the style of the span best overlapping rect."""
    best_area = 0.0
    best = SpanStyle("Verdana", 10.0, 0)
    try:
        blocks = page.get_text(
            "dict",
            clip=rect.inflate(4),
            flags=fitz.TEXT_PRESERVE_WHITESPACE
        )["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    sr = fitz.Rect(span["bbox"])
                    inter = sr & rect
                    if inter.is_empty:
                        continue
                    area = inter.get_area()
                    if area > best_area:
                        best_area = area
                        best = SpanStyle(
                            font_name=span.get("font", "Verdana"),
                            size=span.get("size", 10.0),
                            color_int=span.get("color", 0),
                        )
    except Exception:
        pass
    return best


def _sample_style_by_text(page: "fitz.Page", words: List[str]) -> SpanStyle:
    """Walk all page spans to find one whose text contains any of `words`."""
    try:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = " ".join(s.get("text", "") for s in line.get("spans", []))
                if any(w in line_text for w in words):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            return SpanStyle(
                                font_name=span.get("font", "Verdana"),
                                size=span.get("size", 10.0),
                                color_int=span.get("color", 0),
                            )
    except Exception:
        pass
    return SpanStyle("Verdana", 10.0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Text insertion using real font file
# ─────────────────────────────────────────────────────────────────────────────

def _insert_text_with_font(page: "fitz.Page", rect: "fitz.Rect",
                            text: str, style: SpanStyle,
                            font_path: Optional[str]):
    """
    Insert text at rect using:
      - font_path (real embedded or system font file) if provided, OR
      - style.alias (base-14 name) if style is a _SpanStyleWithAlias, OR
      - _base14_for(style.font_name) as last resort
    """
    r = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1 + 3)
    origin = fitz.Point(r.x0, r.y1 - 1.5)

    # Case 1: real font file available
    if font_path and os.path.exists(font_path):
        try:
            rc = page.insert_text(
                origin, text,
                fontfile=font_path,
                fontsize=style.size,
                color=style.color_rgb,
            )
            if rc >= 0:
                return
        except Exception:
            pass

    # Case 2: base-14 alias (user-chosen or override)
    alias = getattr(style, "alias", None) or _base14_for(style.font_name)
    try:
        page.insert_text(
            origin, text,
            fontname=alias,
            fontsize=style.size,
            color=style.color_rgb,
        )
    except Exception:
        pass


def _base14_for(font_name: str) -> str:
    n = font_name.lower()
    if "bold" in n and ("italic" in n or "oblique" in n):
        return "helv-bo"
    if "bold" in n:
        return "helv-b"
    if "italic" in n or "oblique" in n:
        return "helv-o"
    if "times" in n or "roman" in n:
        return "tiro"
    if "courier" in n or "mono" in n:
        return "cour"
    return "helv"


# ─────────────────────────────────────────────────────────────────────────────
# Style override helper
# ─────────────────────────────────────────────────────────────────────────────

class _SpanStyleWithAlias(SpanStyle):
    """SpanStyle that carries a base-14 alias for use when no font file exists."""
    def __init__(self, original: SpanStyle, alias: str):
        super().__init__(original.font_name, original.size,
                         int(original.color_rgb[0]*255) << 16 |
                         int(original.color_rgb[1]*255) << 8 |
                         int(original.color_rgb[2]*255))
        self.alias = alias


# ─────────────────────────────────────────────────────────────────────────────
# In-place editor
# ─────────────────────────────────────────────────────────────────────────────

class InPlacePDFEditor:

    def __init__(self, source_pdf_path: str, suggestions: List[Suggestion],
                 override_font: Optional[Dict] = None):
        self.source_path = source_pdf_path
        self.override_font = override_font   # {"name", "alias", "path"} or None
        self.replacements: Dict[str, str] = {
            s.original_text: s.final_text
            for s in suggestions
            if s.status == SuggestionStatus.ACCEPTED
               and s.original_text != s.final_text
        }

    def generate(self, output_path: str) -> str:
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("pymupdf required. Run: pip install pymupdf")

        import shutil
        if not self.replacements:
            shutil.copy2(self.source_path, output_path)
            return output_path

        doc = fitz.open(self.source_path)
        fonts = FontRegistry(doc)

        # Resolve override font path once upfront
        override_path = None
        if self.override_font:
            override_path = self.override_font.get("path")  # None = base-14

        try:
            for page in doc:
                for original, replacement in self.replacements.items():
                    self._replace_on_page(page, fonts, original, replacement,
                                          override_path)

            doc.save(output_path, garbage=4, deflate=True, clean=True)
        finally:
            doc.close()
            fonts.cleanup()

        return output_path

    def _replace_on_page(self, page: "fitz.Page", fonts: FontRegistry,
                          original: str, replacement: str,
                          override_path: Optional[str] = None):
        """
        Find original text on page, redact it, re-insert replacement.
        If override_path is set, use that font file instead of the embedded one.
        """
        # ── Direct search ─────────────────────────────────────────────────
        rects = page.search_for(original, quads=False)
        if rects:
            for rect in rects:
                style = _sample_style(page, rect)
                # Use override font if provided, else embedded font
                font_path = override_path if override_path is not None \
                            else fonts.path_for_name(style.font_name)
                # If override is a base-14 font (path=None), pass its alias
                if self.override_font and override_path is None:
                    style = _SpanStyleWithAlias(style,
                                                self.override_font.get("alias", "helv"))
                page.add_redact_annot(rect, fill=(1, 1, 1))
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
                _insert_text_with_font(page, rect, replacement, style, font_path)
            return

        # ── Fragment search (text split across multiple PDF spans) ────────
        sig_words = [w for w in original.split() if len(w) > 4][:5]
        if not sig_words:
            return

        hit_rects = []
        for word in sig_words:
            hit_rects.extend(page.search_for(word))

        if not hit_rects:
            return

        x0 = min(r.x0 for r in hit_rects)
        y0 = min(r.y0 for r in hit_rects)
        x1 = max(r.x1 for r in hit_rects)
        y1 = max(r.y1 for r in hit_rects)
        combined = fitz.Rect(x0, y0, x1, y1)

        style = _sample_style(page, combined)
        if style.font_name == "Verdana" and style.color_rgb == (0.0, 0.0, 0.0):
            style = _sample_style_by_text(page, sig_words[:2])

        font_path = override_path if override_path is not None \
                    else fonts.path_for_name(style.font_name)
        if self.override_font and override_path is None:
            style = _SpanStyleWithAlias(style,
                                        self.override_font.get("alias", "helv"))
        page.add_redact_annot(combined, fill=(1, 1, 1))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        _insert_text_with_font(page, combined, replacement, style, font_path)


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: ReportLab plain rebuild
# ─────────────────────────────────────────────────────────────────────────────

class FallbackPDFGenerator:
    def __init__(self, cv_sections: List[CVSection], suggestions: List[Suggestion]):
        self.sections = cv_sections
        self.replacements = {
            s.original_text: s.final_text
            for s in suggestions
            if s.status == SuggestionStatus.ACCEPTED
        }

    def generate(self, output_path: str) -> str:
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("Neither pymupdf nor reportlab is installed.\n"
                               "Run: pip install pymupdf")
        body = ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10, leading=14,
            spaceAfter=4, alignment=TA_JUSTIFY)
        head = ParagraphStyle(
            "head", fontName="Helvetica-Bold", fontSize=11,
            spaceBefore=10, spaceAfter=4)
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        story = []
        for section in self.sections:
            if section.name.lower() != "header":
                story.append(Paragraph(section.name.upper(), head))
            text = section.raw_text
            for orig, repl in self.replacements.items():
                text = text.replace(orig, repl)
            for line in text.split("\n"):
                if line.strip():
                    story.append(Paragraph(line.strip(), body))
            story.append(Spacer(1, 6))
        doc.build(story)
        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_final_pdf(
    cv_sections: List[CVSection],
    suggestions: List[Suggestion],
    output_path: str,
    source_pdf_path: Optional[str] = None,
) -> str:
    """
    Generate the final CV PDF with accepted suggestions applied.

    With source_pdf_path + pymupdf:
        Edits original PDF in-place — preserves all fonts, colors, layout.
    Otherwise:
        Falls back to a plain ReportLab rebuild.
    """
    if source_pdf_path and PYMUPDF_AVAILABLE:
        return InPlacePDFEditor(source_pdf_path, suggestions).generate(output_path)
    return FallbackPDFGenerator(cv_sections, suggestions).generate(output_path)


def build_modified_text(
    cv_sections: List[CVSection],
    suggestions: List[Suggestion],
) -> str:
    replacements = {
        s.original_text: s.final_text
        for s in suggestions
        if s.status == SuggestionStatus.ACCEPTED
    }
    lines = []
    for section in cv_sections:
        if section.name.lower() != "header":
            lines.append(f"\n{'='*40}\n{section.name.upper()}\n{'='*40}")
        text = section.raw_text
        for orig, rep in replacements.items():
            text = text.replace(orig, rep)
        lines.append(text)
    return "\n".join(lines)


# =============================================================================
# Font discovery — called by the UI to populate the font picker
# =============================================================================

# Base-14 fonts built into every PyMuPDF install (no file path required)
BASE14_FONTS = [
    {"name": "Helvetica",              "alias": "helv",    "category": "Sans-serif",  "path": None},
    {"name": "Helvetica Bold",         "alias": "helv-b",  "category": "Sans-serif",  "path": None},
    {"name": "Helvetica Oblique",      "alias": "helv-o",  "category": "Sans-serif",  "path": None},
    {"name": "Helvetica Bold Oblique", "alias": "helv-bo", "category": "Sans-serif",  "path": None},
    {"name": "Times Roman",            "alias": "tiro",    "category": "Serif",       "path": None},
    {"name": "Times Bold",             "alias": "tibo",    "category": "Serif",       "path": None},
    {"name": "Times Italic",           "alias": "tiit",    "category": "Serif",       "path": None},
    {"name": "Times Bold Italic",      "alias": "tibi",    "category": "Serif",       "path": None},
    {"name": "Courier",                "alias": "cour",    "category": "Monospace",   "path": None},
    {"name": "Courier Bold",           "alias": "cour-b",  "category": "Monospace",   "path": None},
    {"name": "Courier Oblique",        "alias": "cour-o",  "category": "Monospace",   "path": None},
    {"name": "Courier Bold Oblique",   "alias": "cour-bo", "category": "Monospace",   "path": None},
]

# Priority system font names to look for (shown first when found)
_PRIORITY_FONTS = {
    "arial", "arialmt", "arialbold", "arialnarrow",
    "calibri", "calibribold",
    "cambria", "cambriabold",
    "georgia", "georgiabold",
    "garamond",
    "trebuchetms", "trebuchetmsbold",
    "verdana", "verdanabold",
    "tahoma", "tahomabd",
    "futura",
    "gillsans",
    "optima",
    "palatino", "palatinolinotype",
    "bookantiqua",
    "centuryschoolbook",
    "franklingothicmedium",
    "dejavu sans", "dejavusans", "dejavusansbold",
    "liberation sans", "liberationsans",
    "freesans", "freeserif",
    "noto sans", "notosans",
    "carlito",
    "caladea",
    "linuxlibertine",
}


def _system_font_dirs() -> List[str]:
    """Return OS-appropriate directories to scan for fonts."""
    import platform
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Darwin":
        return [
            "/Library/Fonts",
            "/System/Library/Fonts",
            os.path.join(home, "Library", "Fonts"),
        ]
    if system == "Windows":
        return [
            os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
        ]
    # Linux / other
    return [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.join(home, ".fonts"),
        os.path.join(home, ".local", "share", "fonts"),
    ]


def discover_system_fonts() -> List[Dict]:
    """
    Scan OS font directories and return a list of usable font dicts:
        [{"name": str, "alias": None, "category": str, "path": str}, ...]
    Only includes fonts that PyMuPDF can actually open.
    Priority fonts (common CV-appropriate typefaces) are sorted first.
    """
    if not PYMUPDF_AVAILABLE:
        return []

    found: Dict[str, Dict] = {}

    for directory in _system_font_dirs():
        if not os.path.isdir(directory):
            continue
        for root, _, files in os.walk(directory):
            for filename in files:
                if not filename.lower().endswith((".ttf", ".otf")):
                    continue
                path = os.path.join(root, filename)
                try:
                    font_obj = fitz.Font(fontfile=path)
                    raw_name = font_obj.name or ""
                    if not raw_name or raw_name == "(null)":
                        # Fall back to filename stem
                        raw_name = os.path.splitext(filename)[0].replace("-", " ").replace("_", " ")
                    if raw_name in found:
                        continue
                    category = _guess_category(raw_name, filename)
                    found[raw_name] = {
                        "name":     raw_name,
                        "alias":    None,
                        "category": category,
                        "path":     path,
                    }
                except Exception:
                    continue

    # Sort: priority fonts first (alphabetically within each group), then rest
    priority, rest = [], []
    for entry in found.values():
        key = entry["name"].lower().replace(" ", "").replace("-", "")
        if any(p in key for p in _PRIORITY_FONTS):
            priority.append(entry)
        else:
            rest.append(entry)

    priority.sort(key=lambda e: e["name"].lower())
    rest.sort(key=lambda e: e["name"].lower())
    return priority + rest


def _guess_category(name: str, filename: str) -> str:
    """Heuristically classify a font as Sans-serif, Serif, or Monospace."""
    text = (name + " " + filename).lower()
    if any(w in text for w in ("mono", "courier", "console", "code", "typewriter", "fixedsys")):
        return "Monospace"
    if any(w in text for w in ("serif", "roman", "times", "garamond", "palatino",
                                "georgia", "book antiqua", "cambria", "century",
                                "caladea", "linux libertine", "freeserif", "noto serif")):
        return "Serif"
    return "Sans-serif"


def check_font_availability(source_pdf_path: str) -> Dict:
    """
    Check whether the embedded fonts in the PDF can be extracted and used.

    Returns:
        {
            "fonts_ok":        bool,   # True = embedded fonts work fine
            "embedded_names":  [str],  # font names found in the PDF
            "failed_names":    [str],  # fonts that could not be extracted
            "reason":          str,    # human-readable explanation if fonts_ok=False
        }
    """
    if not PYMUPDF_AVAILABLE or not source_pdf_path:
        return {"fonts_ok": False, "embedded_names": [], "failed_names": [],
                "reason": "PyMuPDF not installed"}

    try:
        doc = fitz.open(source_pdf_path)
    except Exception as e:
        return {"fonts_ok": False, "embedded_names": [], "failed_names": [],
                "reason": str(e)}

    embedded_names = []
    failed_names = []
    seen = set()

    for page_num in range(len(doc)):
        for font_tuple in doc.get_page_fonts(page_num):
            xref     = font_tuple[0]
            basename = font_tuple[3]
            if xref in seen:
                continue
            seen.add(xref)
            clean = basename.split("+")[-1]
            try:
                fd  = doc.extract_font(xref)
                buf = fd[3]
                if not buf or len(buf) < 500:
                    failed_names.append(clean)
                    continue
                # Try writing to temp file and opening
                tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
                tmp.write(buf)
                tmp.close()
                try:
                    test = fitz.Font(fontfile=tmp.name)
                    if not test.is_writable:
                        failed_names.append(clean)
                    else:
                        embedded_names.append(clean)
                except Exception:
                    failed_names.append(clean)
                finally:
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
            except Exception:
                failed_names.append(clean)

    doc.close()

    fonts_ok = len(embedded_names) > 0 and len(failed_names) == 0
    reason = ""
    if not fonts_ok:
        if not embedded_names and failed_names:
            reason = (f"None of the {len(failed_names)} embedded font(s) could be "
                      f"extracted: {', '.join(failed_names[:4])}.")
        elif failed_names:
            reason = (f"{len(failed_names)} of {len(embedded_names)+len(failed_names)} "
                      f"embedded font(s) failed to extract: {', '.join(failed_names[:4])}.")

    return {
        "fonts_ok":       fonts_ok,
        "embedded_names": embedded_names,
        "failed_names":   failed_names,
        "reason":         reason,
    }


def generate_final_pdf_with_fallback_font(
    cv_sections: List[CVSection],
    suggestions: List[Suggestion],
    output_path: str,
    source_pdf_path: str,
    fallback_font: Dict,          # {"name": str, "alias": str|None, "path": str|None}
) -> str:
    """
    Generate the final PDF using a user-chosen fallback font instead of the
    embedded fonts from the original PDF.
    """
    if not PYMUPDF_AVAILABLE:
        return FallbackPDFGenerator(cv_sections, suggestions).generate(output_path)

    editor = InPlacePDFEditor(source_pdf_path, suggestions,
                              override_font=fallback_font)
    return editor.generate(output_path)