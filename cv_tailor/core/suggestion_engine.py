"""
Suggestion Engine - generates targeted, inline improvement suggestions.

CRITICAL BUSINESS RULE:
    All suggestions must be derived ONLY from existing CV content.
    No new skills, experiences, or qualifications may be invented.
"""
import re
from typing import List, Optional

from core.models import (
    CVSection, AnalysisResult, Suggestion, SuggestionType
)
from core.analyzer import WEAK_VERBS, VERB_UPGRADES


_HAS_METRIC_RE = re.compile(
    r'\b(\d+[\.,]?\d*\s*(%|percent|million|billion|k|m|users?|clients?|'
    r'projects?|team|members?|employees?|staff|months?|weeks?|days?|hours?|'
    r'x|times|fold))\b',
    re.IGNORECASE
)

_QUANTIFIABLE_RE = re.compile(
    r'\b(improved|increased|reduced|grew|cut|saved|generated|raised|'
    r'boosted|enhanced|accelerated|delivered|achieved|completed|managed)\b',
    re.IGNORECASE
)


class SuggestionEngine:
    """
    Generates suggestions for improving a CV against a job description.
    Supports locale-aware reason strings.
    """

    _REASONS = {
        "weak_verb": {
            "en": "Replace weak opener '{weak}' with stronger action verb '{strong}' to demonstrate proactive impact.",
            "fr": "Remplacez le verbe faible '{weak}' par le verbe d'action plus fort '{strong}' pour demontrer un impact proactif.",
            "de": "Ersetzen Sie das schwache Verb '{weak}' durch das staerkere Aktionsverb '{strong}', um proaktive Wirkung zu zeigen.",
            "es": "Reemplaza el verbo debil '{weak}' por el verbo de accion mas fuerte '{strong}' para demostrar impacto proactivo.",
            "ja": "弱い動詞 '{weak}' をより力強いアクション動詞 '{strong}' に置き換えて、積極的なインパクトを示しましょう。",
            "zh": "将弱动词 '{weak}' 替换为更有力的行动动词 '{strong}'，以展示积极主动的影响力。",
        },
        "quantify": {
            "en": "This bullet uses '{verb}' but lacks a metric. Quantifying achievements (%, numbers, time saved) significantly strengthens impact.",
            "fr": "Ce point utilise '{verb}' mais manque de chiffre. Quantifier les realisations (%, chiffres, temps economise) renforce considerablement l'impact.",
            "de": "Dieser Punkt verwendet '{verb}', enthaelt aber keine Kennzahl. Das Quantifizieren von Leistungen (%, Zahlen, gesparte Zeit) staerkt die Wirkung erheblich.",
            "es": "Este punto usa '{verb}' pero no tiene metrica. Cuantificar los logros (%, cifras, tiempo ahorrado) fortalece considerablemente el impacto.",
            "ja": "この箇条書きは '{verb}' を使用していますが、数値がありません。成果を定量化する（%、数字、節約時間など）ことでインパクトが大幅に向上します。",
            "zh": "此要点使用了 '{verb}'，但缺乏量化指标。量化成就（百分比、数字、节省的时间）可以显著增强影响力。",
        },
        "keyword": {
            "en": "'{keyword}' appears in the job description and is implied by your experience. Making it explicit increases ATS visibility.",
            "fr": "'{keyword}' figure dans l'offre d'emploi et est implicite dans votre experience. Le rendre explicite augmente la visibilite ATS.",
            "de": "'{keyword}' erscheint in der Stellenbeschreibung und ist in Ihrer Erfahrung impliziert. Es explizit zu machen erhoet die ATS-Sichtbarkeit.",
            "es": "'{keyword}' aparece en la descripcion del puesto y esta implicito en tu experiencia. Hacerlo explicito aumenta la visibilidad en ATS.",
            "ja": "'{keyword}' は求人票に記載されており、あなたの経験からも示唆されています。明示することでATSの可視性が向上します。",
            "zh": "'{keyword}' 出现在职位描述中，且与您的经验相关。明确说明可提高ATS可见性。",
        },
        "section_keyword": {
            "en": "These JD keywords appear in your CV but are not explicitly listed in your Skills section: {keywords}. Adding them improves ATS matching.",
            "fr": "Ces mots-cles de l'offre apparaissent dans votre CV mais ne sont pas listes dans la section Competences : {keywords}. Les ajouter ameliore la correspondance ATS.",
            "de": "Diese Schlusselworter der Stellenbeschreibung sind in Ihrem Lebenslauf enthalten, aber nicht explizit im Abschnitt Fahigkeiten aufgefuhrt: {keywords}. Das Hinzufugen verbessert das ATS-Matching.",
            "es": "Estas palabras clave del puesto aparecen en tu CV pero no estan listadas explicitamente en la seccion de Habilidades: {keywords}. Anadirlas mejora la coincidencia ATS.",
            "ja": "これらの求人キーワードはCVに含まれていますが、スキルセクションに明示されていません：{keywords}。追加することでATSマッチングが向上します。",
            "zh": "这些职位关键词出现在您的简历中，但未在技能部分明确列出：{keywords}。添加后可提高ATS匹配度。",
        },
        "quantify_placeholder": {
            "en": " [add specific metric, e.g. by X% or for N clients]",
            "fr": " [ajoutez une metrique specifique, ex. de X% ou pour N clients]",
            "de": " [spezifische Kennzahl hinzufugen, z.B. um X% oder fur N Kunden]",
            "es": " [anade una metrica especifica, p.ej. un X% o para N clientes]",
            "ja": " [具体的な数値を追加、例：X%向上、Nクライアント対応]",
            "zh": " [添加具体指标，例如：提升X%或服务N名客户]",
        },
        "keyword_inject": {
            "en": ", utilising {keyword}.",
            "fr": ", en utilisant {keyword}.",
            "de": ", unter Verwendung von {keyword}.",
            "es": ", utilizando {keyword}.",
            "ja": "（{keyword}を活用）。",
            "zh": "，运用{keyword}。",
        },
    }

    def __init__(self, analysis: AnalysisResult, jd_text: str, locale: str = "en"):
        self.analysis = analysis
        self.jd_text = jd_text
        self.jd_lower = jd_text.lower()
        self.locale = locale
        self.suggestions: List[Suggestion] = []

    def _reason(self, key: str, **kwargs) -> str:
        """Return localised reason string for a check type."""
        templates = self._REASONS.get(key, {})
        template = templates.get(self.locale) or templates.get("en", "")
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def generate(self) -> List[Suggestion]:
        """Run all heuristic checks and populate suggestions list."""
        self.suggestions.clear()

        for section in self.analysis.cv_sections:
            if section.name in ("Header", "References", "Interests", "Hobbies"):
                continue

            for bullet in section.bullets:
                if len(bullet.strip()) < 15:
                    continue
                self._check_weak_verb(bullet, section.name)
                self._check_quantification(bullet, section.name)
                self._check_keyword_opportunity(bullet, section.name)

            self._check_section_keywords(section)

        # Remove duplicates (same original_text)
        seen: set = set()
        unique: List[Suggestion] = []
        for s in self.suggestions:
            if s.original_text not in seen:
                seen.add(s.original_text)
                unique.append(s)

        self.analysis.suggestions = unique
        return unique

    def _check_weak_verb(self, bullet: str, section_name: str):
        """Replace weak opening verbs with stronger action verbs."""
        bullet_lower = bullet.lower().strip()
        for weak, strong in VERB_UPGRADES.items():
            pattern = re.compile(r'^(' + re.escape(weak) + r')\b', re.IGNORECASE)
            match = pattern.match(bullet_lower)
            if match:
                original_verb = bullet[:len(match.group(0))]
                suggested_verb = strong.capitalize() if bullet[0].isupper() else strong
                suggested_text = suggested_verb + bullet[len(original_verb):]
                self.suggestions.append(Suggestion(
                    section_name=section_name,
                    suggestion_type=SuggestionType.STRENGTHEN_VERB,
                    original_text=bullet,
                    suggested_text=suggested_text,
                    reason=self._reason("weak_verb", weak=weak, strong=strong),
                ))
                break

    def _check_quantification(self, bullet: str, section_name: str):
        """Flag bullets with impact language but no numbers."""
        if _HAS_METRIC_RE.search(bullet):
            return
        match = _QUANTIFIABLE_RE.search(bullet)
        if not match:
            return
        verb_used = match.group(0)
        placeholder = self._reason("quantify_placeholder")
        suggested = bullet.rstrip('.') + placeholder
        self.suggestions.append(Suggestion(
            section_name=section_name,
            suggestion_type=SuggestionType.QUANTIFY,
            original_text=bullet,
            suggested_text=suggested,
            reason=self._reason("quantify", verb=verb_used),
        ))

    def _check_keyword_opportunity(self, bullet: str, section_name: str):
        """Surface JD keywords that are implied but not explicit in a bullet."""
        bullet_lower = bullet.lower()
        implication_map = {
            r'\b(agile|scrum|sprint|kanban|standup|retrospective)\b': "Agile methodology",
            r'\b(ci/cd|pipeline|deployment|jenkins|github.action|circleci)\b': "CI/CD",
            r'\b(sql|postgres|mysql|oracle|database|query|schema)\b': "SQL",
            r'\b(aws|azure|gcp|cloud|s3|ec2|lambda|kubernetes|docker)\b': "cloud infrastructure",
            r'\b(stakeholder|executive|director|board|c-suite)\b': "stakeholder management",
            r'\b(presentation|deck|report|briefing|communicate|present)\b': "communication",
            r'\b(budget|cost|revenue|p&l|profit|margin|roi)\b': "financial management",
            r'\b(team|people|manage|mentor|coach|performance review)\b': "people management",
            r'\b(cross.functional|cross.team|interdepartmental|collaborate)\b': "cross-functional collaboration",
        }
        for pattern_str, keyword_hint in implication_map.items():
            if re.search(pattern_str, bullet_lower):
                if keyword_hint and keyword_hint.lower() in self.jd_lower:
                    if keyword_hint.lower() not in bullet_lower:
                        suggested = self._inject_keyword(bullet, keyword_hint)
                        if suggested != bullet:
                            self.suggestions.append(Suggestion(
                                section_name=section_name,
                                suggestion_type=SuggestionType.ADD_KEYWORD,
                                original_text=bullet,
                                suggested_text=suggested,
                                reason=self._reason("keyword", keyword=keyword_hint),
                                jd_keywords=[keyword_hint],
                            ))
                        break

    def _inject_keyword(self, bullet: str, keyword: str) -> str:
        """Naturally incorporate a keyword into an existing bullet."""
        suffix = self._reason("keyword_inject", keyword=keyword)
        return bullet.rstrip('.') + suffix

    def _check_section_keywords(self, section: CVSection):
        """Flag Skills sections missing important JD keywords."""
        if section.name.lower() not in ("skills", "technical skills", "competencies"):
            return
        missing = self.analysis.missing_keywords
        if len(missing) <= 3:
            return
        top_missing = missing[:5]
        in_cv = [
            kw for kw in top_missing
            if any(kw.lower() in s.raw_text.lower() for s in self.analysis.cv_sections)
        ]
        if in_cv:
            original = section.raw_text[:200] + ("..." if len(section.raw_text) > 200 else "")
            suggested = (
                original.rstrip() +
                "\n[Consider listing explicitly: " + ", ".join(in_cv) + "]"
            )
            self.suggestions.append(Suggestion(
                section_name=section.name,
                suggestion_type=SuggestionType.ADD_KEYWORD,
                original_text=original,
                suggested_text=suggested,
                reason=self._reason("section_keyword", keywords=", ".join(in_cv)),
                jd_keywords=in_cv,
            ))


def generate_suggestions(analysis: AnalysisResult,
                          jd_text: str,
                          locale: str = "en") -> List[Suggestion]:
    """
    Generate improvement suggestions using local heuristic engine.
    Populates analysis.suggestions and returns the list.
    """
    engine = SuggestionEngine(analysis, jd_text, locale=locale)
    return engine.generate()