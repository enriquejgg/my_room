"""
Preview Frame — Step 4: Side-by-side Before / After section viewer.

Layout:
  Left sidebar   — clickable section/subsection links (unchanged from before)
  Right area     — two equal panels:
      BEFORE panel  — original text; changed spans shown in red strikethrough
      AFTER  panel  — edited text;   changed spans shown in green bold
  Bottom bar     — ◀ Prev · counter · Next ▶ · ← Back to Review
  (PDF download removed — this step is read/copy only)
"""
import tkinter as tk
from tkinter import ttk
import re
from typing import TYPE_CHECKING, List, Dict, Optional, Tuple

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


# ── Subsection detection (kept local so frame is self-contained) ──────────────

_DATE_RE = re.compile(
    r'\b(19|20)\d{2}\b'
    r'|(\d{1,2}[/\-]\d{4})'
    r'|(\d{4}\s*[-–]\s*(\d{4}|present|current|aujourd\'hui|heute|actualidad|現在|至今))',
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r'^[•\-\*\►\▸\◆\○\●\d\.]\s+')

_SUBSECTION_SECTIONS = {
    "work experience", "experience", "employment", "employment history",
    "expérience professionnelle", "expérience", "emploi",
    "berufserfahrung", "erfahrung",
    "experiencia profesional", "experiencia",
    "education", "formation", "ausbildung", "educación",
    "projects", "projets", "projekte", "proyectos",
    "certifications", "zertifizierungen", "certificaciones",
}


def _is_subsection_title(line: str, next_lines: List[str]) -> bool:
    s = line.strip()
    if not s or len(s) < 3 or len(s) > 100:
        return False
    if _BULLET_RE.match(s):
        return False
    if _DATE_RE.search(s):
        return True
    if s.isupper() and len(s) < 60:
        return True
    words = s.split()
    if len(words) <= 8 and s[0].isupper():
        has_content = any(
            _BULLET_RE.match(l.strip()) or len(l.strip()) > 20
            for l in next_lines[:3]
        )
        if has_content:
            return True
    return False


def _detect_subsections(section_name: str,
                         raw_text: str) -> List[Tuple[str, str]]:
    if not any(s in section_name.lower() for s in _SUBSECTION_SECTIONS):
        return []
    lines = raw_text.split('\n')
    results: List[Tuple[str, str]] = []
    cur_title, cur_lines = "", []

    def flush():
        content = '\n'.join(cur_lines).strip()
        if content:
            results.append((cur_title, content))

    for i, line in enumerate(lines):
        if _is_subsection_title(line, lines[i+1:i+4]):
            if cur_title or cur_lines:
                flush()
            cur_title = line.strip()
            cur_lines = []
        else:
            if line.strip():
                cur_lines.append(line)
    if cur_title or cur_lines:
        flush()
    return results


# ── Diff helpers ──────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Collapse all whitespace runs to a single space for fuzzy matching."""
    return re.sub(r'\s+', ' ', text).strip()


def _find_span(content: str, target: str):
    """
    Find `target` in `content`, trying exact match first, then whitespace-
    normalised match.  Returns (start, end) char indices into `content`,
    or None if not found.
    """
    # 1. Exact match
    idx = content.find(target)
    if idx != -1:
        return idx, idx + len(target)

    # 2. Normalised match — find where the normalised target sits inside the
    #    normalised content, then map back to original indices.
    norm_target  = _norm(target)
    norm_content = _norm(content)
    nidx = norm_content.find(norm_target)
    if nidx == -1:
        return None

    # Walk through content, building up a mapping from
    # normalised-position -> original-position.
    orig_pos = 0
    norm_pos = 0
    start_orig = None
    end_orig   = None

    while orig_pos < len(content):
        # Skip leading whitespace in original, collapse to one space in norm
        if content[orig_pos].isspace():
            if norm_pos < len(norm_content) and norm_content[norm_pos] == ' ':
                if norm_pos == nidx:
                    start_orig = orig_pos
                norm_pos += 1
            orig_pos += 1
            continue
        if norm_pos == nidx and start_orig is None:
            start_orig = orig_pos
        if norm_pos == nidx + len(norm_target):
            end_orig = orig_pos
            break
        norm_pos += 1
        orig_pos += 1

    if end_orig is None:
        end_orig = orig_pos

    if start_orig is None:
        return None

    return start_orig, end_orig


def _before_segments(text: str,
                     replacements: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Produce (fragment, tag) segments for the BEFORE panel.
    Changed spans are tagged "removed" (red strikethrough).
    """
    if not replacements:
        return [(text, "plain")]

    # Collect all (start, end) spans for changed text
    spans = []
    for orig in replacements:
        span = _find_span(text, orig)
        if span:
            spans.append(span)

    if not spans:
        return [(text, "plain")]

    # Merge / sort spans, then emit segments
    spans.sort(key=lambda s: s[0])
    segments: List[Tuple[str, str]] = []
    cursor = 0
    for start, end in spans:
        if start > cursor:
            segments.append((text[cursor:start], "plain"))
        segments.append((text[start:end], "removed"))
        cursor = end
    if cursor < len(text):
        segments.append((text[cursor:], "plain"))
    return segments


def _after_segments(text: str,
                    replacements: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Produce (fragment, tag) segments for the AFTER panel.
    Replacement text is tagged "added" (green bold).
    """
    if not replacements:
        return [(text, "plain")]

    # Work on a copy, replacing matched spans with replacement text
    segments: List[Tuple[str, str]] = []
    remaining = text

    for orig, repl in replacements.items():
        span = _find_span(remaining, orig)
        if not span:
            continue
        start, end = span
        if start > 0:
            segments.append((remaining[:start], "plain"))
        segments.append((repl, "added"))
        remaining = remaining[end:]

    if remaining:
        segments.append((remaining, "plain"))

    return segments if segments else [(text, "plain")]


def _render_segments(widget: tk.Text,
                      segments: List[Tuple[str, str]]):
    """Write (fragment, tag) pairs into a disabled Text widget."""
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    for fragment, tag in segments:
        widget.insert("end", fragment, tag)
    widget.configure(state="disabled")


# ── Main frame ────────────────────────────────────────────────────────────────

class PreviewFrame(tk.Frame):

    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._nav_items: List[Dict] = []
        self._replacements: Dict[str, str] = {}
        self._current_item: Optional[Dict] = None
        self._link_labels: List[Tuple] = []
        self._build_ui()

    def _t(self, key, **kw): return self.app.t(key, **kw)

    def on_enter(self):
        self._build_nav()
        if self._nav_items:
            self._show_item(self._nav_items[0])

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Stats bar
        self.stats_bar = tk.Frame(self, bg=COLORS["bg_secondary"],
                                  padx=PAD["md"], pady=PAD["sm"])
        self.stats_bar.pack(fill="x")

        self.heading_lbl = tk.Label(
            self.stats_bar, text=self._t("preview.heading"),
            font=FONTS["heading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"])
        self.heading_lbl.pack(side="left")

        self.stats_lbl = tk.Label(
            self.stats_bar, text="", font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.stats_lbl.pack(side="left", padx=PAD["md"])

        self.score_badge = tk.Label(
            self.stats_bar, text="",
            font=FONTS["subheading"],
            bg=COLORS["bg_surface"], fg=COLORS["accent"],
            padx=10, pady=2)
        self.score_badge.pack(side="right", padx=PAD["sm"])

        # Body: sidebar + comparison panel
        body = tk.Frame(self, bg=COLORS["bg_primary"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_comparison_panel(body)
        self._build_nav_bar()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=COLORS["bg_secondary"], width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text=self._t("preview.nav.heading"),
            font=FONTS["small_bold"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"], padx=PAD["sm"], pady=PAD["xs"]
        ).pack(anchor="w")
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x")

        canvas = tk.Canvas(sidebar, bg=COLORS["bg_secondary"],
                           highlightthickness=0)
        scroll = ttk.Scrollbar(sidebar, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        self._link_inner = tk.Frame(canvas, bg=COLORS["bg_secondary"])
        win = canvas.create_window((0, 0), window=self._link_inner, anchor="nw")
        self._link_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        self._nav_canvas = canvas

    # ── Comparison panel ──────────────────────────────────────────────────────

    def _build_comparison_panel(self, parent):
        right = tk.Frame(parent, bg=COLORS["bg_primary"])
        right.pack(side="left", fill="both", expand=True,
                   padx=PAD["sm"], pady=PAD["sm"])

        # Section path title + copy AFTER button
        title_bar = tk.Frame(right, bg=COLORS["bg_secondary"],
                              padx=PAD["md"], pady=PAD["sm"])
        title_bar.pack(fill="x")

        self.section_title_lbl = tk.Label(
            title_bar, text="",
            font=FONTS["heading"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"], anchor="w")
        self.section_title_lbl.pack(side="left", fill="x", expand=True)

        # Two-panel comparison area
        compare = tk.Frame(right, bg=COLORS["bg_primary"])
        compare.pack(fill="both", expand=True, pady=(PAD["xs"], 0))
        compare.columnconfigure(0, weight=1, uniform="panel")
        compare.columnconfigure(1, weight=1, uniform="panel")

        self._before_box = self._build_text_panel(
            compare, col=0,
            label=self._t("preview.panel.before"),
            label_color=COLORS["danger"],
            show_copy=False,
            tags={
                "plain":   {"foreground": COLORS["text_primary"]},
                "removed": {"foreground": COLORS["danger"],
                            "overstrike": True,
                            "font": FONTS["body"]},
            }
        )

        # Thin divider between panels
        tk.Frame(compare, bg=COLORS["border"], width=2).grid(
            row=0, column=0, sticky="nse", padx=(0, 2))

        self._after_box = self._build_text_panel(
            compare, col=1,
            label=self._t("preview.panel.after"),
            label_color=COLORS["success"],
            show_copy=True,
            tags={
                "plain": {"foreground": COLORS["text_primary"]},
                "added": {"foreground": COLORS["success"],
                          "font": FONTS["body_bold"]},
            }
        )

        # "No changes" notice (shown when section has no edits)
        self._no_changes_frame = tk.Frame(right, bg=COLORS["bg_surface"],
                                           padx=PAD["md"], pady=PAD["sm"])
        self._no_changes_lbl = tk.Label(
            self._no_changes_frame,
            text=self._t("preview.no_changes"),
            font=FONTS["body"],
            bg=COLORS["bg_surface"],
            fg=COLORS["text_muted"])
        self._no_changes_lbl.pack()

    def _build_text_panel(self, parent, col: int, label: str,
                           label_color: str, tags: Dict,
                           show_copy: bool = False) -> tk.Text:
        """Build one labelled, scrollable text panel in the comparison grid."""
        frame = tk.Frame(parent, bg=COLORS["bg_secondary"])
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0 if col == 0 else PAD["xs"], 0))

        # Panel header
        hdr = tk.Frame(frame, bg=COLORS["bg_surface"],
                        padx=PAD["sm"], pady=4)
        hdr.pack(fill="x")

        tk.Label(hdr, text="■", font=FONTS["small_bold"],
                 bg=COLORS["bg_surface"], fg=label_color).pack(side="left")
        tk.Label(hdr, text=f"  {label}",
                 font=FONTS["small_bold"],
                 bg=COLORS["bg_surface"],
                 fg=COLORS["text_secondary"]).pack(side="left")

        if show_copy:
            # Confirmation flash label
            self.copy_confirm = tk.Label(
                hdr, text="", font=FONTS["small"],
                bg=COLORS["bg_surface"], fg=COLORS["success"])
            self.copy_confirm.pack(side="right", padx=(0, PAD["xs"]))

            # Copy button sits directly in the panel header
            self.copy_btn = tk.Button(
                hdr,
                text=self._t("preview.btn.copy"),
                font=FONTS["small_bold"],
                bg=COLORS["accent"],
                fg=COLORS["text_on_accent"],
                activebackground=COLORS["accent_light"],
                activeforeground=COLORS["text_on_accent"],
                relief="flat",
                padx=10, pady=2,
                cursor="hand2",
                command=self._copy_after,
            )
            self.copy_btn.pack(side="right")

        # Scrollable text area
        wrap = tk.Frame(frame, bg=COLORS["bg_surface"])
        wrap.pack(fill="both", expand=True)

        txt = tk.Text(
            wrap,
            font=FONTS["body"],
            bg=COLORS["bg_surface"], fg=COLORS["text_primary"],
            relief="flat", wrap="word",
            padx=PAD["sm"], pady=PAD["sm"],
            state="disabled", spacing3=3,
            cursor="arrow",
        )
        for tag_name, cfg in tags.items():
            txt.tag_configure(tag_name, **cfg)

        scroll = ttk.Scrollbar(wrap, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        return txt

    # ── Nav bar ───────────────────────────────────────────────────────────────

    def _build_nav_bar(self):
        nav = tk.Frame(self, bg=COLORS["bg_secondary"],
                        padx=PAD["md"], pady=PAD["sm"])
        nav.pack(fill="x", side="bottom")

        ttk.Button(nav, text=self._t("preview.btn.back"),
                   style="Ghost.TButton",
                   command=self.app.prev_step).pack(side="left")

        self.prev_btn = ttk.Button(
            nav, text=self._t("preview.btn.prev_section"),
            style="Ghost.TButton", command=self._prev_item)
        self.prev_btn.pack(side="left", padx=(PAD["xs"], 0))

        self.section_nav_lbl = tk.Label(
            nav, text="", font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.section_nav_lbl.pack(side="left", padx=PAD["sm"])

        self.next_btn = ttk.Button(
            nav, text=self._t("preview.btn.next_section"),
            style="Ghost.TButton", command=self._next_item)
        self.next_btn.pack(side="left")

    # ── Navigation building ───────────────────────────────────────────────────

    def _build_nav(self):
        result = self.app.analysis_result
        if not result:
            return

        self._replacements = {
            s.original_text: s.final_text
            for s in result.suggestions
            if s.status.value == "accepted" and s.original_text != s.final_text
        }

        accepted = sum(1 for s in result.suggestions
                       if s.status.value == "accepted")
        total = len(result.suggestions)
        self.score_badge.configure(text=f"{result.match_score}%")
        self.stats_lbl.configure(
            text=self._t("preview.stats",
                         score=result.match_score, accepted=accepted))
        self.heading_lbl.configure(text=self._t("preview.heading"))

        self._nav_items = []
        for w in self._link_inner.winfo_children():
            w.destroy()
        self._link_labels = []

        for section in result.cv_sections:
            if section.name.lower() == "header":
                continue
            subs = _detect_subsections(section.name, section.raw_text)
            self._add_link(section.name, section.name, None,
                           level=0, has_children=len(subs) > 0)
            for sub_title, _ in subs:
                display = (sub_title[:33] + "…"
                           if len(sub_title) > 35 else sub_title)
                self._add_link(display, section.name, sub_title, level=1)

    def _add_link(self, label: str, section_name: str,
                  subsection_title: Optional[str],
                  level: int = 0, has_children: bool = False):
        item = {
            "label": label,
            "section_name": section_name,
            "subsection_title": subsection_title,
            "level": level,
            "index": len(self._nav_items),
        }
        self._nav_items.append(item)

        indent = PAD["md"] + level * 16
        row = tk.Frame(self._link_inner, bg=COLORS["bg_secondary"],
                        cursor="hand2")
        row.pack(fill="x", padx=(indent, 0))

        prefix = ("▸ " if has_children else "  ") if level == 0 else "· "
        fg = (COLORS["text_primary"] if level == 0
              else COLORS["text_secondary"])
        font = FONTS["small_bold"] if level == 0 else FONTS["small"]

        lbl = tk.Label(row, text=prefix + label,
                        font=font, fg=fg,
                        bg=COLORS["bg_secondary"],
                        anchor="w", cursor="hand2",
                        padx=2, pady=2)
        lbl.pack(fill="x")

        idx = item["index"]
        for w in (row, lbl):
            w.bind("<Button-1>",
                   lambda e, i=idx: self._show_item(self._nav_items[i]))
            w.bind("<Enter>",
                   lambda e, r=row, l=lbl: (
                       r.configure(bg=COLORS["bg_hover"]),
                       l.configure(bg=COLORS["bg_hover"])))
            w.bind("<Leave>",
                   lambda e, r=row, l=lbl, f=fg: (
                       r.configure(bg=COLORS["bg_secondary"]),
                       l.configure(bg=COLORS["bg_secondary"], fg=f)))

        self._link_labels.append((row, lbl, item))

    # ── Item display ──────────────────────────────────────────────────────────

    def _show_item(self, item: Dict):
        self._current_item = item
        result = self.app.analysis_result
        if not result:
            return

        # Find section
        section = next(
            (s for s in result.cv_sections
             if s.name == item["section_name"]), None)
        if not section:
            return

        # Resolve content
        sub_title = item.get("subsection_title")
        if sub_title:
            subs = _detect_subsections(section.name, section.raw_text)
            content = next((c for t, c in subs if t == sub_title), "")
            display_title = f"{section.name}  /  {sub_title}"
        else:
            content = section.raw_text
            display_title = section.name

        self.section_title_lbl.configure(text=display_title)

        # Determine which replacements apply to this content block
        local_replacements = {
            orig: repl
            for orig, repl in self._replacements.items()
            if _find_span(content, orig) is not None
        }

        has_changes = bool(local_replacements)

        # Hide/show no-changes notice
        if has_changes:
            self._no_changes_frame.pack_forget()
        else:
            self._no_changes_frame.pack(fill="x", pady=(PAD["xs"], 0))
            self._no_changes_lbl.configure(
                text=self._t("preview.no_changes"))

        # Render BEFORE panel
        _render_segments(
            self._before_box,
            _before_segments(content, local_replacements),
        )

        # Render AFTER panel
        _render_segments(
            self._after_box,
            _after_segments(content, local_replacements),
        )

        # Sync both scrollbars
        self._before_box.yview_moveto(0)
        self._after_box.yview_moveto(0)

        self._highlight_link(item["index"])
        self.copy_confirm.configure(text="")

        idx = item["index"]
        total = len(self._nav_items)
        self.section_nav_lbl.configure(text=f"{idx + 1} / {total}")
        self.prev_btn.configure(state="normal" if idx > 0 else "disabled")
        self.next_btn.configure(
            state="normal" if idx < total - 1 else "disabled")

    def _highlight_link(self, active_idx: int):
        for row, lbl, item in self._link_labels:
            if item["index"] == active_idx:
                row.configure(bg=COLORS["bg_hover"])
                lbl.configure(bg=COLORS["bg_hover"],
                               fg=COLORS["accent_light"])
            else:
                fg = (COLORS["text_primary"] if item["level"] == 0
                      else COLORS["text_secondary"])
                row.configure(bg=COLORS["bg_secondary"])
                lbl.configure(bg=COLORS["bg_secondary"], fg=fg)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _prev_item(self):
        if self._current_item and self._current_item["index"] > 0:
            self._show_item(
                self._nav_items[self._current_item["index"] - 1])

    def _next_item(self):
        if self._current_item:
            idx = self._current_item["index"]
            if idx < len(self._nav_items) - 1:
                self._show_item(self._nav_items[idx + 1])

    def _copy_after(self):
        """Copy the AFTER (edited) panel content to clipboard."""
        self._after_box.configure(state="normal")
        text = self._after_box.get("1.0", "end").strip()
        self._after_box.configure(state="disabled")
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_confirm.configure(text=self._t("preview.copied"))
        self.after(2000, lambda: self.copy_confirm.configure(text=""))