"""
Analysis Engine — compares CV content against a job description.
Uses TF-IDF cosine similarity for semantic gap detection.
Works in both standard (local) and AI-assisted modes.
"""
import re
import math
from typing import List, Dict, Tuple, Set
from collections import Counter

from core.models import CVSection, AnalysisResult, ProcessingMode


# ── Weak verb lists ─────────────────────────────────────────────────────────

WEAK_VERBS = {
    "helped", "assisted", "worked", "did", "made", "got", "went",
    "was responsible for", "responsible for", "duties included",
    "involved in", "participated in", "tasked with", "part of",
    "contributed to", "supported", "aided", "worked on", "did work",
    "handled", "dealt with", "worked with",
}

STRONG_VERBS = {
    "achieved", "accelerated", "built", "created", "delivered", "designed",
    "developed", "directed", "drove", "engineered", "established", "executed",
    "generated", "grew", "implemented", "improved", "increased", "initiated",
    "launched", "led", "managed", "optimised", "orchestrated", "owned",
    "pioneered", "reduced", "resolved", "scaled", "spearheaded", "streamlined",
    "transformed", "architected", "automated", "championed", "collaborated",
    "coordinated", "cultivated", "defined", "deployed", "enhanced",
    "facilitated", "formulated", "identified", "influenced", "mentored",
}

# Verbs worth replacing mapped to better alternatives
VERB_UPGRADES: Dict[str, str] = {
    "helped": "contributed to",
    "assisted": "supported",
    "worked on": "delivered",
    "was responsible for": "owned",
    "responsible for": "led",
    "duties included": "achieved",
    "involved in": "drove",
    "participated in": "contributed to",
    "tasked with": "executed",
    "handled": "managed",
    "dealt with": "resolved",
    "made": "developed",
    "did": "executed",
    "got": "achieved",
}


# ── Simple TF-IDF implementation (no heavy ML dependency) ──────────────────

def _tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric tokens, 2+ chars."""
    return re.findall(r'\b[a-z][a-z0-9\+\#]{1,}\b', text.lower())


def _tf(tokens: List[str]) -> Dict[str, float]:
    counts = Counter(tokens)
    total = max(len(tokens), 1)
    return {word: count / total for word, count in counts.items()}


def _idf(word: str, all_docs: List[List[str]]) -> float:
    n_docs = len(all_docs)
    n_containing = sum(1 for doc in all_docs if word in doc)
    return math.log((n_docs + 1) / (n_containing + 1)) + 1


def _tfidf_vector(tokens: List[str],
                   all_docs: List[List[str]]) -> Dict[str, float]:
    tf = _tf(tokens)
    return {word: tf[word] * _idf(word, all_docs) for word in tf}


def _cosine_similarity(vec_a: Dict[str, float],
                        vec_b: Dict[str, float]) -> float:
    shared = set(vec_a) & set(vec_b)
    if not shared:
        return 0.0
    dot = sum(vec_a[w] * vec_b[w] for w in shared)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Main analysis class ─────────────────────────────────────────────────────

class CVAnalyzer:
    """
    Performs semantic gap analysis between a CV and a job description.
    Produces a scored AnalysisResult with per-section coverage.
    """

    def __init__(self, cv_sections: List[CVSection], jd_text: str):
        self.cv_sections = cv_sections
        self.jd_text = jd_text
        self.jd_tokens = _tokenize(jd_text)
        self.cv_full_text = "\n".join(s.raw_text for s in cv_sections)
        self.cv_tokens = _tokenize(self.cv_full_text)

    def analyse(self) -> AnalysisResult:
        """Run full analysis and return structured results."""
        # 1. Build TF-IDF vectors
        jd_vec = _tfidf_vector(
            self.jd_tokens,
            [self.jd_tokens, self.cv_tokens]
        )
        cv_vec = _tfidf_vector(
            self.cv_tokens,
            [self.jd_tokens, self.cv_tokens]
        )

        # 2. Overall match score
        match_score = round(_cosine_similarity(jd_vec, cv_vec) * 100, 1)

        # 3. Extract JD keywords and find which are missing
        jd_keywords = self._extract_jd_keywords()
        missing_keywords = self._find_missing_keywords(jd_keywords)

        # 4. Section-level analysis
        section_scores = self._score_sections(jd_vec)

        # 5. Build result
        result = AnalysisResult(
            cv_sections=self.cv_sections,
            jd_keywords=jd_keywords,
            missing_keywords=missing_keywords,
            match_score=match_score,
            processing_mode=ProcessingMode.STANDARD,
        )

        # 6. Generate analysis summary
        result.summary = self._build_summary(match_score, missing_keywords,
                                               section_scores)
        return result

    # ── Private helpers ────────────────────────────────────────────────────

    def _extract_jd_keywords(self) -> List[str]:
        """Extract meaningful skill/requirement keywords from JD."""
        stop_words = {
            'the', 'and', 'or', 'in', 'at', 'to', 'for', 'of', 'a', 'an',
            'is', 'are', 'will', 'be', 'with', 'on', 'by', 'we', 'you',
            'have', 'has', 'can', 'should', 'would', 'may', 'must',
            'our', 'your', 'this', 'that', 'from', 'into', 'about',
            'including', 'required', 'preferred', 'experience', 'ability',
            'strong', 'excellent', 'good', 'proven', 'demonstrated',
            'work', 'working', 'role', 'team', 'company', 'position',
            'responsibilities', 'requirements', 'qualifications',
        }
        tokens = _tokenize(self.jd_text)
        freq = Counter(tokens)
        # Keep words appearing 2+ times that aren't stop words
        keywords = [
            w for w, c in freq.most_common(60)
            if c >= 1 and w not in stop_words and len(w) > 3
        ]
        # Also grab quoted phrases and capitalised terms
        phrase_re = re.compile(r'"([^"]{3,40})"')
        phrases = phrase_re.findall(self.jd_text)
        return list(dict.fromkeys(phrases + keywords))[:50]

    def _find_missing_keywords(self, jd_keywords: List[str]) -> List[str]:
        """Find JD keywords not present in the CV."""
        cv_lower = self.cv_full_text.lower()
        return [kw for kw in jd_keywords if kw.lower() not in cv_lower]

    def _score_sections(self, jd_vec: Dict[str, float]) -> Dict[str, float]:
        """Score each CV section against the JD vector."""
        scores = {}
        for section in self.cv_sections:
            tokens = _tokenize(section.raw_text)
            if not tokens:
                continue
            s_vec = _tfidf_vector(tokens, [self.jd_tokens, tokens])
            scores[section.name] = round(
                _cosine_similarity(s_vec, jd_vec) * 100, 1
            )
        return scores

    def _build_summary(self, score: float, missing: List[str],
                        section_scores: Dict[str, float]) -> str:
        """Build a plain-English summary of the analysis."""
        lines = [f"Overall CV-to-JD match score: {score}%\n"]

        if score >= 70:
            lines.append("✓ Your CV has strong alignment with this role.")
        elif score >= 45:
            lines.append("△ Your CV has moderate alignment — targeted improvements will help.")
        else:
            lines.append("✗ Your CV has low alignment with this role — significant tailoring needed.")

        if missing:
            top_missing = missing[:8]
            lines.append(
                f"\nKey terms from JD not found in CV:\n  "
                + ", ".join(top_missing)
            )

        low_sections = [
            name for name, sc in section_scores.items()
            if sc < 30 and name not in ("Header", "References")
        ]
        if low_sections:
            lines.append(
                f"\nSections needing most improvement:\n  "
                + ", ".join(low_sections)
            )

        return "\n".join(lines)


def analyse_cv_vs_jd(cv_sections: List[CVSection],
                      jd_text: str) -> AnalysisResult:
    """
    Convenience function: run standard (local) analysis.
    Returns an AnalysisResult (without suggestions — call suggestion engine next).
    """
    analyser = CVAnalyzer(cv_sections, jd_text)
    return analyser.analyse()