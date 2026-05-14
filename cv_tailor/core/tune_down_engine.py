"""
Tune-Down Engine — detects areas where the candidate's CV is more advanced
than the job description requires, and generates optional suggestions to
suppress or simplify that content so the candidate doesn't appear overqualified.

BUSINESS RULE:
    These suggestions are ALWAYS optional and user-initiated.
    The engine is only invoked after the user explicitly confirms they want
    tune-down analysis via the TuneDownDialog.
    No content is altered without user approval of each individual suggestion.
"""
import re
from typing import List, Dict, Tuple
from core.models import (
    Suggestion, SuggestionType, CVSection, AnalysisResult
)


# ── Seniority signal words ────────────────────────────────────────────────────

# Signals in the CV that suggest a more senior level than may be needed
_CV_SENIOR_SIGNALS = {
    # Leadership
    "director", "vp", "vice president", "head of", "c-suite", "cto", "ceo",
    "coo", "chief", "principal", "staff engineer", "distinguished",
    # Management
    "managed a team", "managed team", "team lead", "tech lead",
    "leading a team", "led a team", "oversaw", "supervised",
    "direct reports", "people management", "hiring",
    # Scale
    "billion", "global", "enterprise-wide", "organisation-wide",
    "company-wide", "multinational",
    # Advanced tech
    "architect", "architecture", "designed the system", "greenfield",
    "from scratch", "built from scratch",
}

# Signals in the JD that suggest a junior/mid level
_JD_JUNIOR_SIGNALS = {
    "junior", "graduate", "entry level", "entry-level", "intern",
    "associate", "assistant", "support", "assist", "help desk",
    "1-2 years", "1 year", "2 years", "0-2 years", "fresh",
    "recent graduate", "newly", "beginner", "basic knowledge",
    "familiar with", "exposure to", "understanding of",
}

# Skills in the CV that are clearly more advanced than what the JD mentions
_ADVANCED_SKILL_MARKERS = {
    "tensorflow", "pytorch", "cuda", "gpu", "kubernetes", "k8s",
    "terraform", "ansible", "puppet", "chef",
    "microservices", "distributed systems", "real-time",
    "machine learning", "deep learning", "neural network",
    "blockchain", "cryptography",
    "c++", "rust", "assembly", "fpga",
    "phd", "research", "published", "patent",
}


class TuneDownEngine:
    """
    Analyses CV sections vs job description to find overqualified content.
    Generates Suggestion objects with SuggestionType.TUNE_DOWN.
    """

    def __init__(self, analysis: AnalysisResult, jd_text: str,
                 locale: str = "en"):
        self.analysis   = analysis
        self.jd_text    = jd_text
        self.jd_lower   = jd_text.lower()
        self.locale     = locale
        self._reasons   = _TUNE_DOWN_REASONS

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_overqualified_areas(self) -> List[Dict]:
        """
        Return a list of detected overqualification signals for display in the
        dialog BEFORE the user decides to proceed.

        Returns:
            [{"area": str, "detail": str, "severity": "high"|"medium"|"low"}]
        """
        findings = []

        # 1. Seniority mismatch
        seniority_gap = self._seniority_gap()
        if seniority_gap:
            findings.append({
                "area":     self._t("tunedown.area.seniority"),
                "detail":   seniority_gap,
                "severity": "high",
            })

        # 2. Skills not in JD
        extra_skills = self._skills_not_in_jd()
        if extra_skills:
            findings.append({
                "area":   self._t("tunedown.area.extra_skills"),
                "detail": ", ".join(extra_skills[:6]),
                "severity": "medium",
            })

        # 3. Years of experience mismatch
        exp_gap = self._experience_gap()
        if exp_gap:
            findings.append({
                "area":   self._t("tunedown.area.experience"),
                "detail": exp_gap,
                "severity": "medium",
            })

        return findings

    def generate_tune_down_suggestions(self) -> List[Suggestion]:
        """
        Generate TUNE_DOWN suggestions for the AnalysisResult.
        Appends them to analysis.suggestions and returns the new ones only.
        """
        new_suggestions: List[Suggestion] = []

        for section in self.analysis.cv_sections:
            name_lower = section.name.lower()

            # Check each bullet for overqualification signals
            for bullet in section.bullets:
                sugg = self._check_bullet(bullet, section.name)
                if sugg:
                    new_suggestions.append(sugg)

            # Section-level: skills section with irrelevant advanced tech
            if any(k in name_lower for k in ("skill", "competenc", "technolog")):
                sugg = self._check_skills_section(section)
                if sugg:
                    new_suggestions.append(sugg)

        # Append to existing suggestions (after CV-order sort they'll be mixed in)
        self.analysis.suggestions.extend(new_suggestions)

        # Re-sort so tune-down suggestions appear in CV order alongside others
        from core.suggestion_engine import sort_suggestions_by_cv_position
        sort_suggestions_by_cv_position(self.analysis)

        return new_suggestions

    # ── Detection helpers ─────────────────────────────────────────────────────

    def _seniority_gap(self) -> str:
        """Return a description of seniority mismatch if found, else ''."""
        cv_full = " ".join(
            s.raw_text.lower() for s in self.analysis.cv_sections
        )
        cv_has_senior = any(sig in cv_full for sig in _CV_SENIOR_SIGNALS)
        jd_has_junior = any(sig in self.jd_lower for sig in _JD_JUNIOR_SIGNALS)

        if cv_has_senior and jd_has_junior:
            found_cv = [sig for sig in _CV_SENIOR_SIGNALS if sig in cv_full][:3]
            found_jd = [sig for sig in _JD_JUNIOR_SIGNALS if sig in self.jd_lower][:2]
            return self._t(
                "tunedown.detail.seniority",
                cv_signals=", ".join(found_cv),
                jd_signals=", ".join(found_jd),
            )
        return ""

    def _skills_not_in_jd(self) -> List[str]:
        """Return advanced skills present in CV but absent from JD."""
        cv_full = " ".join(
            s.raw_text.lower() for s in self.analysis.cv_sections
        )
        return [
            skill for skill in _ADVANCED_SKILL_MARKERS
            if skill in cv_full and skill not in self.jd_lower
        ]

    def _experience_gap(self) -> str:
        """Detect if CV years of experience significantly exceeds JD requirement."""
        # Extract years mentioned in JD requirement
        jd_years = re.findall(
            r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:experience|exp)', self.jd_lower
        )
        # Extract total career years from CV (rough heuristic: date range span)
        cv_full = " ".join(s.raw_text for s in self.analysis.cv_sections)
        cv_years_raw = re.findall(r'\b(20\d{2}|19\d{2})\b', cv_full)

        if not jd_years or not cv_years_raw:
            return ""

        try:
            jd_max = max(int(y) for y in jd_years)
            cv_year_ints = [int(y) for y in cv_years_raw]
            cv_span = max(cv_year_ints) - min(cv_year_ints)
            if cv_span > jd_max + 4:    # more than 4 years above requirement
                return self._t(
                    "tunedown.detail.experience",
                    cv_years=cv_span,
                    jd_years=jd_max,
                )
        except ValueError:
            pass
        return ""

    def _check_bullet(self, bullet: str, section_name: str
                       ) -> Optional[Suggestion]:
        """Check a single bullet for overqualification and return a suggestion."""
        b_lower = bullet.lower()

        # Senior signal present in bullet AND not referenced in JD
        matched_signals = [
            sig for sig in _CV_SENIOR_SIGNALS
            if sig in b_lower and sig not in self.jd_lower
        ]
        if not matched_signals:
            return None

        # Generate a toned-down version: shorten to first sentence / clause
        toned = self._tone_down_bullet(bullet)
        if toned == bullet:
            return None  # no meaningful change possible

        return Suggestion(
            section_name=section_name,
            suggestion_type=SuggestionType.TUNE_DOWN,
            original_text=bullet,
            suggested_text=toned,
            reason=self._t(
                "tunedown.reason.bullet",
                signals=", ".join(f"'{s}'" for s in matched_signals[:2]),
            ),
        )

    def _check_skills_section(self, section: CVSection
                               ) -> Optional[Suggestion]:
        """Suggest removing specific advanced skills absent from the JD."""
        extra = [
            skill for skill in _ADVANCED_SKILL_MARKERS
            if skill in section.raw_text.lower()
            and skill not in self.jd_lower
        ]
        if len(extra) < 2:
            return None

        # Suggest a note to consider removing
        original_snippet = section.raw_text[:200] + (
            "…" if len(section.raw_text) > 200 else ""
        )
        suggested = (
            original_snippet.rstrip()
            + "\n[Consider removing or de-emphasising: "
            + ", ".join(extra[:5]) + "]"
        )
        return Suggestion(
            section_name=section.name,
            suggestion_type=SuggestionType.TUNE_DOWN,
            original_text=original_snippet,
            suggested_text=suggested,
            reason=self._t(
                "tunedown.reason.skills",
                skills=", ".join(extra[:5]),
            ),
        )

    @staticmethod
    def _tone_down_bullet(bullet: str) -> str:
        """
        Attempt to produce a shorter, less senior-sounding version of a bullet.
        Strips leadership prefixes and trims to the most factual core.
        """
        remove_prefixes = [
            r'^(led|directed|oversaw|supervised|managed)\s+a\s+team\s+of\s+\d+[^,;\.]*[,;\.]\s*',
            r'^(led|directed|oversaw)\s+[^,;\.]{5,40}[,;\.]\s*',
        ]
        result = bullet
        for pattern in remove_prefixes:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE).strip()
            if result and result != bullet:
                # Capitalise first letter
                result = result[0].upper() + result[1:]
                break

        # If no prefix was removed, try trimming after a semicolon
        if result == bullet and ';' in bullet:
            result = bullet.split(';')[0].strip().rstrip(',')

        return result if result != bullet and len(result) > 20 else bullet

    def _t(self, key: str, **kwargs) -> str:
        """Look up i18n string."""
        try:
            from core.i18n import get
            return get(key, self.locale, **kwargs)
        except Exception:
            return key


# ── i18n reason templates (fallback if i18n not loaded) ─────────────────────

_TUNE_DOWN_REASONS: Dict = {}   # populated via i18n


# ── Public convenience function ───────────────────────────────────────────────

def detect_overqualification(analysis: AnalysisResult,
                              jd_text: str,
                              locale: str = "en") -> List[Dict]:
    """
    Run detection only (no suggestions generated).
    Returns findings list for display in the dialog.
    """
    engine = TuneDownEngine(analysis, jd_text, locale)
    return engine.detect_overqualified_areas()


def generate_tune_down_suggestions(analysis: AnalysisResult,
                                    jd_text: str,
                                    locale: str = "en") -> List[Suggestion]:
    """
    Generate and attach tune-down suggestions to the analysis result.
    Returns only the newly added suggestions.
    """
    engine = TuneDownEngine(analysis, jd_text, locale)
    return engine.generate_tune_down_suggestions()