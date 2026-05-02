"""
Core data models for CV Tailor application.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
import uuid


class ProcessingMode(Enum):
    STANDARD = "standard"
    AI_ASSISTED = "ai_assisted"


class SuggestionStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class SuggestionType(Enum):
    STRENGTHEN_VERB = "strengthen_verb"       # Replace weak verb with stronger one
    ADD_KEYWORD = "add_keyword"               # Add JD keyword naturally
    QUANTIFY = "quantify"                     # Prompt to add metrics
    REWRITE_BULLET = "rewrite_bullet"         # Rewrite for impact
    REORDER_SKILLS = "reorder_skills"         # Reorder to match JD priority
    EXPAND_POINT = "expand_point"             # Expand a vague bullet point
    IMPROVE_SUMMARY = "improve_summary"       # Improve professional summary
    GENERIC = "generic"                       # General improvement


@dataclass
class CVSection:
    """Represents a parsed section of a CV."""
    name: str                     # Section heading (e.g., "Work Experience")
    raw_text: str                 # Full raw text of the section
    bullets: List[str]            # Bullet points or paragraphs within section
    page_number: int = 1
    char_start: int = 0           # Character offset in full CV text
    char_end: int = 0

    def __post_init__(self):
        if not self.bullets and self.raw_text:
            # Split into lines, filter blanks
            self.bullets = [
                line.strip() for line in self.raw_text.split('\n')
                if line.strip()
            ]


@dataclass
class Suggestion:
    """A single improvement suggestion for a CV item."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    section_name: str = ""
    suggestion_type: SuggestionType = SuggestionType.GENERIC

    original_text: str = ""       # The exact text being improved
    suggested_text: str = ""      # The suggested replacement
    edited_text: str = ""         # User-edited version (if modified)
    reason: str = ""              # Why this improvement is recommended
    jd_keywords: List[str] = field(default_factory=list)  # Relevant JD terms

    status: SuggestionStatus = SuggestionStatus.PENDING

    @property
    def final_text(self) -> str:
        """Returns the text that should be used in the final CV."""
        if self.status == SuggestionStatus.ACCEPTED:
            return self.edited_text if self.edited_text else self.suggested_text
        return self.original_text

    @property
    def is_pending(self) -> bool:
        return self.status == SuggestionStatus.PENDING

    def accept(self, edited: Optional[str] = None):
        self.status = SuggestionStatus.ACCEPTED
        if edited:
            self.edited_text = edited

    def reject(self):
        self.status = SuggestionStatus.REJECTED


@dataclass
class PIIMapping:
    """Stores PII masking mappings for re-injection."""
    placeholder: str      # e.g., "[NAME_1]"
    original_value: str   # e.g., "John Smith"
    pii_type: str         # e.g., "name", "email", "phone"


@dataclass
class AnalysisResult:
    """Full result of a CV vs JD analysis."""
    cv_sections: List[CVSection] = field(default_factory=list)
    suggestions: List[Suggestion] = field(default_factory=list)
    jd_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    match_score: float = 0.0      # 0-100 overall match score
    summary: str = ""             # Human-readable analysis summary
    processing_mode: ProcessingMode = ProcessingMode.STANDARD

    @property
    def accepted_suggestions(self) -> List[Suggestion]:
        return [s for s in self.suggestions if s.status == SuggestionStatus.ACCEPTED]

    @property
    def pending_suggestions(self) -> List[Suggestion]:
        return [s for s in self.suggestions if s.status == SuggestionStatus.PENDING]

    @property
    def total_count(self) -> int:
        return len(self.suggestions)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_suggestions)