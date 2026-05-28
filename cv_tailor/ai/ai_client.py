"""
AI Client — wraps the Anthropic API for AI-assisted CV analysis.

PRIVACY RULES (enforced here):
  • ONLY masked text is ever sent to the API.
  • The masker must be applied BEFORE calling any method in this module.
  • Raw (unmasked) personal data must never reach this layer.
"""
import json
import os
from typing import List, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("WARNING: anthropic SDK not installed. Run: pip install anthropic")

from core.models import (
    Suggestion, SuggestionType, CVSection, AnalysisResult, ProcessingMode
)
from core.pii_masker import PIIMasker


MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a professional CV coach and technical recruiter with 15+ years of experience.

Your task is to analyse a candidate's CV against a job description and suggest precise, targeted improvements.

STRICT RULES — you MUST follow these without exception:
1. Every suggestion must use ONLY content already present in the CV. Never invent new skills, certifications, or experiences.
2. You may rephrase, reorder, strengthen verbs, add metrics prompts, or surface implicit keywords — but never fabricate.
3. Return ONLY valid JSON — no preamble, no markdown code blocks, no explanation outside JSON.
4. Suggestions must reference the EXACT original text from the CV (character-for-character).
5. The PII in the CV has been masked with placeholders like [NAME_1], [EMAIL_1], [PHONE_1]. Do NOT attempt to unmask them.

Return a JSON object with this exact schema:
{
  "match_score": <0-100 integer>,
  "summary": "<2-3 sentence overall assessment>",
  "missing_keywords": ["<keyword>", ...],
  "suggestions": [
    {
      "section_name": "<section heading>",
      "type": "<strengthen_verb|add_keyword|quantify|rewrite_bullet|improve_summary|generic>",
      "original_text": "<exact text from CV>",
      "suggested_text": "<improved version using only existing content>",
      "reason": "<1-2 sentence explanation of improvement>",
      "jd_keywords": ["<relevant jd term>"]
    }
  ]
}"""


_USER_PROMPT_TEMPLATE = """
## CV (PII masked for privacy):
{cv_text}

## Job Description:
{jd_text}

Analyse the CV against this job description and return improvement suggestions as JSON.
Focus on the most impactful changes that align the CV with the role requirements.
Maximum 15 suggestions, prioritised by importance.
"""


# ── AI Client class ───────────────────────────────────────────────────────────

class AIClient:
    """
    Wraps Anthropic API calls for CV analysis.
    Requires pre-masked CV text — never accepts raw PII.
    """

    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "anthropic SDK not installed. Run: pip install anthropic"
            )
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        key = key.strip()
        if not key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )
        self._client = anthropic.Anthropic(api_key=key)

    def analyse(
        self,
        masked_cv_text: str,
        jd_text: str,
        masker: PIIMasker,
        cv_sections: List[CVSection],
        locale: str = "en",
    ) -> AnalysisResult:
        """
        Run AI-assisted analysis. Returns a populated AnalysisResult.

        Args:
            masked_cv_text: CV text with PII already replaced by placeholders.
            jd_text: Job description (PII-free).
            masker: The PIIMasker instance used for masking (for reverse mapping).
            cv_sections: Parsed CV sections (used for context mapping).
            locale: Language code for response language (en/fr/de/es/ja/zh).

        Returns:
            AnalysisResult populated with AI-generated suggestions.
        """
        from core.i18n import get_ai_language_instruction
        lang_instruction = get_ai_language_instruction(locale)

        # Build a locale-aware system prompt
        system_prompt = _SYSTEM_PROMPT + f"\n\nLANGUAGE REQUIREMENT: {lang_instruction}"

        prompt = _USER_PROMPT_TEMPLATE.format(
            cv_text=masked_cv_text[:8000],
            jd_text=jd_text[:3000],
        )

        message = self._client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )

        raw_json = message.content[0].text.strip()

        # Strip accidental markdown fences
        raw_json = raw_json.removeprefix("```json").removeprefix("```")
        raw_json = raw_json.removesuffix("```").strip()

        data = json.loads(raw_json)

        return self._parse_response(data, cv_sections, masker)

    # ── Response parsing ────────────────────────────────────────────────────

    def _parse_response(
        self,
        data: dict,
        cv_sections: List[CVSection],
        masker: PIIMasker,
    ) -> AnalysisResult:
        """Parse the AI JSON response into an AnalysisResult."""
        suggestions: List[Suggestion] = []

        for raw in data.get("suggestions", []):
            # Unmask AI-returned text (AI will use placeholders; restore originals)
            original = masker.unmask(raw.get("original_text", ""))
            suggested = masker.unmask(raw.get("suggested_text", ""))

            # Map type string to enum
            type_map = {
                "strengthen_verb": SuggestionType.STRENGTHEN_VERB,
                "add_keyword": SuggestionType.ADD_KEYWORD,
                "quantify": SuggestionType.QUANTIFY,
                "rewrite_bullet": SuggestionType.REWRITE_BULLET,
                "improve_summary": SuggestionType.IMPROVE_SUMMARY,
                "generic": SuggestionType.GENERIC,
            }
            s_type = type_map.get(
                raw.get("type", "generic"), SuggestionType.GENERIC
            )

            suggestions.append(Suggestion(
                section_name=raw.get("section_name", ""),
                suggestion_type=s_type,
                original_text=original,
                suggested_text=suggested,
                reason=raw.get("reason", ""),
                jd_keywords=raw.get("jd_keywords", []),
            ))

        return AnalysisResult(
            cv_sections=cv_sections,
            suggestions=suggestions,
            jd_keywords=data.get("missing_keywords", []),
            missing_keywords=data.get("missing_keywords", []),
            match_score=float(data.get("match_score", 0)),
            summary=data.get("summary", ""),
            processing_mode=ProcessingMode.AI_ASSISTED,
        )


def is_available() -> bool:
    """Check if the Anthropic SDK is installed and API key is set."""
    return (
        ANTHROPIC_AVAILABLE and
        bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    )