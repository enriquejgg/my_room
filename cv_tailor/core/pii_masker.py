"""
PII Masking Engine — detects and masks Personally Identifiable Information
before any text is sent to external AI APIs.

Masking is reversible only within the same session via an in-memory mapping.
Masked text must NEVER be transmitted to third parties with original values.
"""
import re
from typing import Dict, List, Tuple
from core.models import PIIMapping

# ── Regex patterns ──────────────────────────────────────────────────────────

_PATTERNS: Dict[str, re.Pattern] = {
    "email": re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    ),
    "phone": re.compile(
        r'(?<!\d)(\+?[\d][\d\s\-\.\(\)]{6,14}\d)(?!\d)'
    ),
    "linkedin": re.compile(
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?',
        re.IGNORECASE
    ),
    "github": re.compile(
        r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?',
        re.IGNORECASE
    ),
    "url": re.compile(
        r'https?://[^\s<>"\']+',
        re.IGNORECASE
    ),
    "uk_postcode": re.compile(
        r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',
        re.IGNORECASE
    ),
    "us_zipcode": re.compile(
        r'\b\d{5}(?:-\d{4})?\b'
    ),
    "national_insurance": re.compile(
        r'\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-Z]\b',
        re.IGNORECASE
    ),
    "ssn": re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    ),
}

# Common first/last name patterns for heuristic name detection
# (Very first non-blank line of a CV is usually the candidate's name)
_NAME_LINE_RE = re.compile(
    r'^([A-Z][a-z]+(?:\s+[A-Z]\.?\s+)?[A-Z][a-z]+)\s*$',
    re.MULTILINE
)


class PIIMasker:
    """
    Masks PII in CV text, stores a reversible mapping in memory.

    Usage:
        masker = PIIMasker()
        masked_text = masker.mask(cv_text)
        # ... send masked_text to AI ...
        original_restored = masker.unmask(ai_response)
        mappings = masker.get_mappings()   # for audit
    """

    def __init__(self):
        self._mappings: List[PIIMapping] = []
        self._counters: Dict[str, int] = {}

    # ── Public API ─────────────────────────────────────────────────────────

    def mask(self, text: str) -> str:
        """
        Detect and replace all PII with labelled placeholders.
        Returns masked text; mapping stored in self._mappings.
        """
        self._mappings.clear()
        self._counters.clear()

        # 1. Detect candidate name (first substantive line)
        text = self._mask_name(text)

        # 2. Apply regex-based patterns in order of specificity
        for pii_type, pattern in _PATTERNS.items():
            text = self._apply_pattern(text, pattern, pii_type)

        return text

    def unmask(self, text: str) -> str:
        """
        Restore original PII values in text returned by AI.
        Only applicable within the same session.
        """
        for mapping in self._mappings:
            text = text.replace(mapping.placeholder, mapping.original_value)
        return text

    def get_mappings(self) -> List[PIIMapping]:
        """Return the current PII mapping table (in-memory only)."""
        return list(self._mappings)

    def clear(self):
        """Purge all stored mappings (call when session ends)."""
        self._mappings.clear()
        self._counters.clear()

    def get_summary(self) -> str:
        """Human-readable summary of what was masked."""
        if not self._mappings:
            return "No PII detected."
        lines = [f"  [{m.pii_type.upper()}] masked: {m.placeholder}"
                 for m in self._mappings]
        return "Masked PII:\n" + "\n".join(lines)

    # ── Private helpers ────────────────────────────────────────────────────

    def _apply_pattern(self, text: str, pattern: re.Pattern,
                       pii_type: str) -> str:
        """Replace all matches of `pattern` with typed placeholders."""

        def replacer(match: re.Match) -> str:
            original = match.group(0)
            # Check if this exact value was already mapped
            existing = next(
                (m for m in self._mappings if m.original_value == original),
                None
            )
            if existing:
                return existing.placeholder

            idx = self._next_index(pii_type)
            placeholder = f"[{pii_type.upper()}_{idx}]"
            self._mappings.append(PIIMapping(
                placeholder=placeholder,
                original_value=original,
                pii_type=pii_type
            ))
            return placeholder

        return pattern.sub(replacer, text)

    def _mask_name(self, text: str) -> str:
        """
        Heuristically detect the candidate name from the first line.
        CVs typically start with the person's full name.
        """
        lines = text.strip().split('\n')
        for line in lines[:5]:  # Check first 5 lines
            stripped = line.strip()
            if not stripped:
                continue
            # Looks like a proper name: 2+ capitalized words, no digits
            if _NAME_LINE_RE.match(stripped) and not any(c.isdigit() for c in stripped):
                placeholder = "[NAME_1]"
                self._mappings.append(PIIMapping(
                    placeholder=placeholder,
                    original_value=stripped,
                    pii_type="name"
                ))
                self._counters["name"] = 1
                text = text.replace(stripped, placeholder, 1)
                break
        return text

    def _next_index(self, pii_type: str) -> int:
        """Increment and return the counter for a given PII type."""
        self._counters[pii_type] = self._counters.get(pii_type, 0) + 1
        return self._counters[pii_type]


# ── Module-level convenience instance ──────────────────────────────────────

_default_masker = PIIMasker()


def mask_text(text: str) -> Tuple[str, PIIMasker]:
    """
    Convenience function: mask PII in text and return (masked_text, masker).
    The masker is needed to unmask AI responses later.
    """
    masker = PIIMasker()
    masked = masker.mask(text)
    return masked, masker