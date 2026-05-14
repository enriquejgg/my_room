"""Core data models for CV Tailor."""
from dataclasses import dataclass, field
from typing import Optional, List
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
    STRENGTHEN_VERB = "strengthen_verb"
    ADD_KEYWORD     = "add_keyword"
    QUANTIFY        = "quantify"
    REWRITE_BULLET  = "rewrite_bullet"
    EXPAND_POINT    = "expand_point"
    IMPROVE_SUMMARY = "improve_summary"
    TUNE_DOWN       = "tune_down"       # suppress overqualified content
    GENERIC         = "generic"


@dataclass
class CVSubSection:
    """A named sub-entry within a CV section (e.g. a single job or degree)."""
    title:     str
    content:   str
    anchor_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class CVSection:
    """Represents a parsed section of a CV."""
    name:        str
    raw_text:    str
    bullets:     List[str]          = field(default_factory=list)
    subsections: List[CVSubSection] = field(default_factory=list)
    page_number: int = 1
    char_start:  int = 0
    char_end:    int = 0

    def __post_init__(self):
        if not self.bullets and self.raw_text:
            self.bullets = [l.strip() for l in self.raw_text.split('\n') if l.strip()]


@dataclass
class Suggestion:
    id:              str             = field(default_factory=lambda: str(uuid.uuid4())[:8])
    section_name:    str             = ""
    suggestion_type: SuggestionType  = SuggestionType.GENERIC
    original_text:   str             = ""
    suggested_text:  str             = ""
    edited_text:     str             = ""
    reason:          str             = ""
    jd_keywords:     List[str]       = field(default_factory=list)
    status:          SuggestionStatus = SuggestionStatus.PENDING

    @property
    def final_text(self) -> str:
        if self.status == SuggestionStatus.ACCEPTED:
            return self.edited_text if self.edited_text else self.suggested_text
        return self.original_text

    def accept(self, edited: Optional[str] = None):
        self.status = SuggestionStatus.ACCEPTED
        if edited:
            self.edited_text = edited

    def reject(self):
        self.status = SuggestionStatus.REJECTED


@dataclass
class PIIMapping:
    placeholder:    str
    original_value: str
    pii_type:       str


@dataclass
class AnalysisResult:
    cv_sections:      List[CVSection]  = field(default_factory=list)
    suggestions:      List[Suggestion] = field(default_factory=list)
    jd_keywords:      List[str]        = field(default_factory=list)
    missing_keywords: List[str]        = field(default_factory=list)
    match_score:      float            = 0.0
    summary:          str              = ""
    processing_mode:  ProcessingMode   = ProcessingMode.STANDARD

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