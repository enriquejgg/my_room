"""
JD Analysis Frame — Step 2 (new intermediate step).

Shows the extracted job description keywords organised into:
  1. Requirements
     ├── Hard Skills   (tools, languages, certifications, technologies)
     ├── Soft Skills   (communication, leadership, teamwork…)
     └── Other Skills  (domain knowledge, processes, frameworks)
  2. Preferred Qualifications
  3. Responsibilities

Each keyword is displayed as a coloured chip/tag.
The user reviews the breakdown, then clicks Continue to proceed to Step 3.
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Dict

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


# ── Chip colour scheme per category ─────────────────────────────────────────

_CAT_COLORS = {
    "hard":            ("#1a3a5c", "#4fa3e0"),   # bg, fg  — blue
    "soft":            ("#1a3a1a", "#4ec94e"),   # green
    "other":           ("#3a2a1a", "#e0a84f"),   # amber
    "preferred":       ("#2a1a3a", "#c080f0"),   # purple
    "responsibilities": ("#2a1a1a", "#e07070"),  # red/salmon
}


def _chip_colors(category: str):
    return _CAT_COLORS.get(category, ("#2a2a2a", "#cccccc"))


class JDAnalysisFrame(tk.Frame):
    """Step 2 — JD keyword breakdown."""

    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._kw_data: Dict = {}
        self._build_ui()

    def _t(self, key, **kw): return self.app.t(key, **kw)

    def on_enter(self):
        """Parse JD and render keywords each time the step becomes active."""
        if not self.app.jd_text:
            return
        from core.jd_extractor import extract_jd_keywords
        self._kw_data = extract_jd_keywords(self.app.jd_text)
        self._render()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header bar
        header = tk.Frame(self, bg=COLORS["bg_secondary"],
                           padx=PAD["md"], pady=PAD["sm"])
        header.pack(fill="x")

        self.heading_lbl = tk.Label(
            header, text=self._t("jd.heading"),
            font=FONTS["heading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"])
        self.heading_lbl.pack(side="left")

        self.subtitle_lbl = tk.Label(
            header, text=self._t("jd.subtitle"),
            font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.subtitle_lbl.pack(side="left", padx=PAD["md"])

        # Scrollable content area
        wrapper = tk.Frame(self, bg=COLORS["bg_primary"])
        wrapper.pack(fill="both", expand=True,
                     padx=PAD["lg"], pady=PAD["sm"])

        canvas = tk.Canvas(wrapper, bg=COLORS["bg_primary"],
                            highlightthickness=0)
        scroll = ttk.Scrollbar(wrapper, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=COLORS["bg_primary"])
        self._canvas_win = canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>",
                          lambda e: canvas.configure(
                              scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                     lambda e: canvas.itemconfig(
                         self._canvas_win, width=e.width))

        # Mouse-wheel scrolling
        canvas.bind_all("<MouseWheel>",
                         lambda e: canvas.yview_scroll(
                             int(-1 * (e.delta / 120)), "units"))

        self._canvas = canvas

        # Bottom nav bar
        nav = tk.Frame(self, bg=COLORS["bg_secondary"],
                        padx=PAD["md"], pady=PAD["sm"])
        nav.pack(fill="x", side="bottom")

        self.back_btn = ttk.Button(
            nav, text=self._t("jd.btn.back"),
            style="Ghost.TButton", command=self.app.prev_step)
        self.back_btn.pack(side="left")

        self.continue_btn = ttk.Button(
            nav, text=self._t("jd.btn.continue"),
            style="TButton", command=self.app.next_step)
        self.continue_btn.pack(side="right")

    # ── Render keyword data ───────────────────────────────────────────────────

    def _render(self):
        """Rebuild the keyword panels from self._kw_data."""
        for w in self._inner.winfo_children():
            w.destroy()

        req = self._kw_data.get("requirements", {})
        preferred = self._kw_data.get("preferred", [])
        responsibilities = self._kw_data.get("responsibilities", [])

        # ── Section 1: Requirements ───────────────────────────────────────
        req_card = self._make_section_card(
            self._inner, "1", self._t("jd.section.requirements"),
            self._t("jd.section.requirements_desc"))

        hard = req.get("hard_skills", [])
        soft = req.get("soft_skills", [])
        other = req.get("other", [])

        if hard:
            self._make_subsection(req_card,
                                   self._t("jd.subsection.hard"),
                                   hard, "hard")
        if soft:
            self._make_subsection(req_card,
                                   self._t("jd.subsection.soft"),
                                   soft, "soft")
        if other:
            self._make_subsection(req_card,
                                   self._t("jd.subsection.other"),
                                   other, "other")

        if not hard and not soft and not other:
            tk.Label(req_card,
                     text=self._t("jd.no_keywords"),
                     font=FONTS["small"],
                     bg=COLORS["bg_secondary"],
                     fg=COLORS["text_muted"]).pack(anchor="w",
                                                   padx=PAD["sm"],
                                                   pady=PAD["xs"])

        # ── Section 2: Preferred Qualifications ───────────────────────────
        pref_card = self._make_section_card(
            self._inner, "2", self._t("jd.section.preferred"),
            self._t("jd.section.preferred_desc"))

        if preferred:
            self._make_chip_row(pref_card, preferred, "preferred")
        else:
            tk.Label(pref_card, text=self._t("jd.no_keywords"),
                     font=FONTS["small"],
                     bg=COLORS["bg_secondary"],
                     fg=COLORS["text_muted"]).pack(anchor="w",
                                                   padx=PAD["sm"],
                                                   pady=PAD["xs"])

        # ── Section 3: Responsibilities ───────────────────────────────────
        resp_card = self._make_section_card(
            self._inner, "3", self._t("jd.section.responsibilities"),
            self._t("jd.section.responsibilities_desc"))

        if responsibilities:
            self._make_responsibility_list(resp_card, responsibilities)
        else:
            tk.Label(resp_card, text=self._t("jd.no_keywords"),
                     font=FONTS["small"],
                     bg=COLORS["bg_secondary"],
                     fg=COLORS["text_muted"]).pack(anchor="w",
                                                   padx=PAD["sm"],
                                                   pady=PAD["xs"])

    # ── Widget builders ───────────────────────────────────────────────────────

    def _make_section_card(self, parent, number: str,
                            title: str, description: str) -> tk.Frame:
        """Create a numbered section card and return its content frame."""
        card = tk.Frame(parent, bg=COLORS["bg_secondary"])
        card.pack(fill="x", pady=(0, PAD["sm"]))

        # Header row with number badge + title
        hdr = tk.Frame(card, bg=COLORS["bg_secondary"],
                        padx=PAD["md"], pady=PAD["sm"])
        hdr.pack(fill="x")

        # Number badge
        badge = tk.Label(hdr, text=number,
                          font=FONTS["subheading"],
                          bg=COLORS["accent"], fg=COLORS["text_on_accent"],
                          width=3, padx=6, pady=2)
        badge.pack(side="left")

        # Title + description
        title_block = tk.Frame(hdr, bg=COLORS["bg_secondary"])
        title_block.pack(side="left", fill="x", expand=True,
                          padx=(PAD["sm"], 0))

        tk.Label(title_block, text=title,
                  font=FONTS["subheading"],
                  bg=COLORS["bg_secondary"],
                  fg=COLORS["text_primary"]).pack(anchor="w")
        tk.Label(title_block, text=description,
                  font=FONTS["small"],
                  bg=COLORS["bg_secondary"],
                  fg=COLORS["text_secondary"]).pack(anchor="w")

        ttk.Separator(card, orient="horizontal").pack(fill="x",
                                                       padx=PAD["md"])
        return card

    def _make_subsection(self, parent, label: str,
                          keywords: List[str], category: str):
        """Create a labelled sub-group with keyword chips."""
        sub = tk.Frame(parent, bg=COLORS["bg_secondary"],
                        padx=PAD["md"], pady=PAD["xs"])
        sub.pack(fill="x")

        tk.Label(sub, text=label.upper(),
                  font=FONTS["small_bold"],
                  bg=COLORS["bg_secondary"],
                  fg=COLORS["text_secondary"]).pack(anchor="w",
                                                    pady=(PAD["xs"], 2))
        self._make_chip_row(sub, keywords, category)

    def _make_chip_row(self, parent, keywords: List[str], category: str):
        """Render a wrapping row of keyword chips."""
        chip_area = tk.Frame(parent, bg=COLORS["bg_secondary"])
        chip_area.pack(fill="x", pady=(0, PAD["sm"]))

        chip_bg, chip_fg = _chip_colors(category)

        # We simulate a wrapping layout by using a canvas or just packing
        # with a frame that reflows on configure
        row_frame = tk.Frame(chip_area, bg=COLORS["bg_secondary"])
        row_frame.pack(fill="x")

        for kw in keywords:
            chip = tk.Label(
                row_frame,
                text=f"  {kw}  ",
                font=FONTS["small"],
                bg=chip_bg, fg=chip_fg,
                padx=4, pady=3,
                relief="flat",
                cursor="arrow",
            )
            chip.pack(side="left", padx=(0, 4), pady=2)

    def _make_responsibility_list(self, parent, items: List[str]):
        """Render responsibilities as a bulleted list."""
        listframe = tk.Frame(parent, bg=COLORS["bg_secondary"],
                              padx=PAD["md"], pady=PAD["sm"])
        listframe.pack(fill="x")

        chip_bg, chip_fg = _chip_colors("responsibilities")

        for item in items:
            row = tk.Frame(listframe, bg=COLORS["bg_secondary"])
            row.pack(fill="x", pady=1)

            tk.Label(row, text="▸",
                      font=FONTS["small"],
                      bg=COLORS["bg_secondary"],
                      fg=chip_fg, width=2).pack(side="left")

            tk.Label(row, text=item,
                      font=FONTS["small"],
                      bg=COLORS["bg_secondary"],
                      fg=COLORS["text_secondary"],
                      wraplength=900,
                      justify="left",
                      anchor="w").pack(side="left", fill="x")