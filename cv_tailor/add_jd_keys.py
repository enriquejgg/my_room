"""
Run this script once from the project root to add the JD Analysis step keys
to your existing core/i18n.py.

    python add_jd_keys.py
"""
import ast, os, sys

TARGET = os.path.join(os.path.dirname(__file__), "core", "i18n.py")

NEW_BLOCK = '''

# ── JD Analysis step (Step 2) ─────────────────────────────────────────────────

_JD_STRINGS = {
    "en": {
        "step.2": "JD Analysis",
        "step.3": "Select Mode",
        "step.4": "Review Suggestions",
        "step.5": "Preview & Copy",
        "jd.heading":                    "Job Description Analysis",
        "jd.subtitle":                   "Keywords extracted from the job description, organised by category.",
        "jd.btn.back":                   "Back",
        "jd.btn.continue":               "Continue",
        "jd.no_keywords":                "No keywords detected in this section.",
        "jd.section.requirements":       "Requirements",
        "jd.section.requirements_desc":  "Skills and qualifications the employer considers essential.",
        "jd.section.preferred":          "Preferred Qualifications",
        "jd.section.preferred_desc":     "Nice-to-have skills that strengthen your application.",
        "jd.section.responsibilities":   "Responsibilities",
        "jd.section.responsibilities_desc": "Day-to-day duties and tasks for this role.",
        "jd.subsection.hard":            "Hard Skills",
        "jd.subsection.soft":            "Soft Skills",
        "jd.subsection.other":           "Other Skills",
    },
    "fr": {
        "step.2": "Analyse JD",
        "step.3": "Mode",
        "step.4": "Revisions",
        "step.5": "Apercu",
        "jd.heading":                    "Analyse de la description du poste",
        "jd.subtitle":                   "Mots-cles extraits de l\'offre d\'emploi, organises par categorie.",
        "jd.btn.back":                   "Retour",
        "jd.btn.continue":               "Continuer",
        "jd.no_keywords":                "Aucun mot-cle detecte dans cette section.",
        "jd.section.requirements":       "Exigences",
        "jd.section.requirements_desc":  "Competences et qualifications jugees essentielles.",
        "jd.section.preferred":          "Qualifications preferees",
        "jd.section.preferred_desc":     "Competences appreciees qui renforcent votre candidature.",
        "jd.section.responsibilities":   "Responsabilites",
        "jd.section.responsibilities_desc": "Taches et missions quotidiennes du poste.",
        "jd.subsection.hard":            "Competences techniques",
        "jd.subsection.soft":            "Competences relationnelles",
        "jd.subsection.other":           "Autres competences",
    },
    "de": {
        "step.2": "JD-Analyse",
        "step.3": "Modus",
        "step.4": "Pruefung",
        "step.5": "Vorschau",
        "jd.heading":                    "Analyse der Stellenbeschreibung",
        "jd.subtitle":                   "Schlusselworter aus der Stellenbeschreibung, nach Kategorie sortiert.",
        "jd.btn.back":                   "Zuruck",
        "jd.btn.continue":               "Weiter",
        "jd.no_keywords":                "Keine Schlusselworter erkannt.",
        "jd.section.requirements":       "Anforderungen",
        "jd.section.requirements_desc":  "Als wesentlich geltende Fahigkeiten und Qualifikationen.",
        "jd.section.preferred":          "Bevorzugte Qualifikationen",
        "jd.section.preferred_desc":     "Zusatzliche Fahigkeiten, die Ihre Bewerbung starken.",
        "jd.section.responsibilities":   "Aufgaben",
        "jd.section.responsibilities_desc": "Tagliche Tatigkeiten der Stelle.",
        "jd.subsection.hard":            "Hard Skills",
        "jd.subsection.soft":            "Soft Skills",
        "jd.subsection.other":           "Sonstige Fahigkeiten",
    },
    "es": {
        "step.2": "Analisis JD",
        "step.3": "Modo",
        "step.4": "Revision",
        "step.5": "Vista previa",
        "jd.heading":                    "Analisis de la descripcion del puesto",
        "jd.subtitle":                   "Palabras clave extraidas de la oferta, organizadas por categoria.",
        "jd.btn.back":                   "Atras",
        "jd.btn.continue":               "Continuar",
        "jd.no_keywords":                "No se detectaron palabras clave en esta seccion.",
        "jd.section.requirements":       "Requisitos",
        "jd.section.requirements_desc":  "Habilidades y cualificaciones esenciales.",
        "jd.section.preferred":          "Cualificaciones preferidas",
        "jd.section.preferred_desc":     "Habilidades adicionales que fortalecen tu candidatura.",
        "jd.section.responsibilities":   "Responsabilidades",
        "jd.section.responsibilities_desc": "Tareas y funciones diarias del puesto.",
        "jd.subsection.hard":            "Habilidades tecnicas",
        "jd.subsection.soft":            "Habilidades blandas",
        "jd.subsection.other":           "Otras habilidades",
    },
    "ja": {
        "step.2": "JD分析",
        "step.3": "モード",
        "step.4": "確認",
        "step.5": "プレビュー",
        "jd.heading":                    "求人票の分析",
        "jd.subtitle":                   "求人票から抽出されたキーワードをカテゴリ別に表示します。",
        "jd.btn.back":                   "戻る",
        "jd.btn.continue":               "次へ",
        "jd.no_keywords":                "このセクションにキーワードが見つかりませんでした。",
        "jd.section.requirements":       "要件",
        "jd.section.requirements_desc":  "採用担当者が必須と考えるスキルと資格。",
        "jd.section.preferred":          "望ましい資格",
        "jd.section.preferred_desc":     "応募を強化するあると望ましいスキル。",
        "jd.section.responsibilities":   "職務内容",
        "jd.section.responsibilities_desc": "このポジションの日常的な業務と役割。",
        "jd.subsection.hard":            "ハードスキル",
        "jd.subsection.soft":            "ソフトスキル",
        "jd.subsection.other":           "その他のスキル",
    },
    "zh": {
        "step.2": "JD分析",
        "step.3": "模式",
        "step.4": "审阅",
        "step.5": "预览",
        "jd.heading":                    "职位描述分析",
        "jd.subtitle":                   "从职位描述中提取的关键词，按类别整理展示。",
        "jd.btn.back":                   "返回",
        "jd.btn.continue":               "继续",
        "jd.no_keywords":                "此部分未检测到关键词。",
        "jd.section.requirements":       "要求",
        "jd.section.requirements_desc":  "雇主认为必备的技能和资格。",
        "jd.section.preferred":          "优先资格",
        "jd.section.preferred_desc":     "能够强化申请的加分技能。",
        "jd.section.responsibilities":   "职责",
        "jd.section.responsibilities_desc": "该职位的日常任务和工作内容。",
        "jd.subsection.hard":            "硬技能",
        "jd.subsection.soft":            "软技能",
        "jd.subsection.other":           "其他技能",
    },
}

for locale, strings in _JD_STRINGS.items():
    for k, v in strings.items():
        _T[locale][k] = v
'''

with open(TARGET, encoding="utf-8") as f:
    content = f.read()

# Check if already patched
if '"jd.heading"' in content:
    print("i18n.py already contains JD Analysis keys — nothing to do.")
    sys.exit(0)

# Insert before the get() function
marker = "\ndef get(key: str, locale: str"
if marker not in content:
    marker = "\ndef get("
if marker not in content:
    print("ERROR: Could not find insertion point in i18n.py")
    sys.exit(1)

content = content.replace(marker, NEW_BLOCK + marker)

# Also update get_steps() to return 5 steps if it currently returns 4
# The function reads from _T so no change needed — step labels come from _T

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(content)

try:
    ast.parse(content)
    print("SUCCESS: JD Analysis keys added to core/i18n.py")
    print("         Steps 2-5 labels updated for all 6 locales.")
except SyntaxError as e:
    print(f"ERROR: Syntax error introduced at line {e.lineno}: {e.msg}")
    print("       Restore i18n.py from backup and report this error.")
    sys.exit(1)


# ── Also update get_steps() if it only returns 4 entries ─────────────────────
# (run automatically as part of this patch)
if __name__ == "__main__":
    pass  # all work done above