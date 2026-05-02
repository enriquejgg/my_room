"""
Review Frame — Step 3: Inline suggestion review with Accept / Reject per item.

This is the core UX of the application.
Users see each suggestion one at a time:
  - Original text (highlighted in context)
  - Suggested replacement (editable)
  - Reason for the change
  - OK (Accept) / Cancel (Reject) controls
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Optional

from ui.styles import COLORS, FONTS, PAD
from core.models import Suggestion, SuggestionStatus, SuggestionType

if TYPE_CHECKING:
    from ui.app import CVTailorApp


# ── Type → display mapping ────────────────────────────────────────────────────

TYPE_LABELS = {
    SuggestionType.STRENGTHEN_VERB: ("💪", "Stronger Verb",    COLORS["accent"]),
    SuggestionType.ADD_KEYWORD:     ("🔑", "Add Keyword",      COLORS["info"]),
    SuggestionType.QUANTIFY:        ("📊", "Add Metric",       COLORS["warning"]),
    SuggestionType.REWRITE_BULLET:  ("✍", "Rewrite Bullet",   COLORS["accent_light"]),
    SuggestionType.IMPROVE_SUMMARY: ("📝", "Improve Summary",  COLORS["success"]),
    SuggestionType.GENERIC:         ("💡", "Improvement",      COLORS["text_secondary"]),
}


class ReviewFrame(tk.Frame):
    """Step 3: Sequential suggestion review."""

    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._suggestions: List[Suggestion] = []
        self._current_index: int = 0
        self._build_ui()

    def on_enter(self):
        """Load suggestions when this frame becomes active."""
        result = self.app.analysis_result
        if result:
            self._suggestions = result.suggestions
            self._current_index = 0
            self._refresh_summary()
            if self._suggestions:
                self._show_suggestion(0)
            else:
                self._show_no_suggestions()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Left sidebar: suggestion list
        self.sidebar = tk.Frame(self, bg=COLORS["bg_secondary"], width=240)
        self.sidebar.pack(side="left", fill="y", padx=(0, 1))
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Main review area
        main = tk.Frame(self, bg=COLORS["bg_primary"])
        main.pack(side="left", fill="both", expand=True)
        self._build_main_area(main)

    def _build_sidebar(self):
        """Left panel: summary stats + suggestion list."""
        # Summary header
        self.summary_frame = tk.Frame(self.sidebar, bg=COLORS["bg_secondary"],
                                       padx=PAD["sm"], pady=PAD["sm"])
        self.summary_frame.pack(fill="x")

        tk.Label(
            self.summary_frame, text="Suggestions",
            font=FONTS["heading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
        ).pack(anchor="w")

        self.summary_stats = tk.Label(
            self.summary_frame, text="",
            font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
            justify="left",
        )
        self.summary_stats.pack(anchor="w")

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x")

        # Scrollable suggestion list
        list_container = tk.Frame(self.sidebar, bg=COLORS["bg_secondary"])
        list_container.pack(fill="both", expand=True)

        self.list_canvas = tk.Canvas(
            list_container,
            bg=COLORS["bg_secondary"],
            highlightthickness=0,
        )
        list_scroll = ttk.Scrollbar(
            list_container, orient="vertical",
            command=self.list_canvas.yview
        )
        self.list_canvas.configure(yscrollcommand=list_scroll.set)
        list_scroll.pack(side="right", fill="y")
        self.list_canvas.pack(fill="both", expand=True)

        self.list_inner = tk.Frame(self.list_canvas, bg=COLORS["bg_secondary"])
        self.list_canvas_window = self.list_canvas.create_window(
            (0, 0), window=self.list_inner, anchor="nw"
        )
        self.list_inner.bind("<Configure>", self._on_list_resize)
        self.list_canvas.bind("<Configure>", self._on_canvas_resize)

        self._list_items: List[tk.Frame] = []

    def _build_main_area(self, parent):
        """Right area: suggestion detail card + navigation."""
        # Score bar at top
        self.score_bar = tk.Frame(parent, bg=COLORS["bg_secondary"], padx=PAD["md"], pady=PAD["sm"])
        self.score_bar.pack(fill="x")
        self.score_label = tk.Label(
            self.score_bar, text="",
            font=FONTS["body"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
        )
        self.score_label.pack(side="left")
        self.mode_badge = tk.Label(
            self.score_bar, text="",
            font=FONTS["small_bold"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            padx=8, pady=3,
        )
        self.mode_badge.pack(side="right")

        # Scrollable content area
        content_wrapper = tk.Frame(parent, bg=COLORS["bg_primary"])
        content_wrapper.pack(fill="both", expand=True, padx=PAD["md"], pady=PAD["md"])

        self.content_canvas = tk.Canvas(
            content_wrapper, bg=COLORS["bg_primary"], highlightthickness=0
        )
        content_scroll = ttk.Scrollbar(
            content_wrapper, orient="vertical",
            command=self.content_canvas.yview
        )
        self.content_canvas.configure(yscrollcommand=content_scroll.set)
        content_scroll.pack(side="right", fill="y")
        self.content_canvas.pack(fill="both", expand=True)

        self.content_inner = tk.Frame(self.content_canvas, bg=COLORS["bg_primary"])
        self.content_canvas.create_window(
            (0, 0), window=self.content_inner, anchor="nw"
        )
        self.content_inner.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )

        # Empty state placeholder
        self.empty_label = tk.Label(
            self.content_inner,
            text="No suggestions to display.",
            font=FONTS["body"],
            bg=COLORS["bg_primary"], fg=COLORS["text_muted"],
        )

        # Navigation bar
        nav = tk.Frame(parent, bg=COLORS["bg_secondary"], padx=PAD["md"], pady=PAD["sm"])
        nav.pack(fill="x", side="bottom")

        ttk.Button(
            nav, text="← Back", style="Ghost.TButton",
            command=self.app.prev_step,
        ).pack(side="left")

        self.prev_btn = ttk.Button(
            nav, text="◀ Prev", style="Ghost.TButton",
            command=self._prev_suggestion,
        )
        self.prev_btn.pack(side="left", padx=(PAD["xs"], 0))

        self.nav_label = tk.Label(
            nav, text="",
            font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
        )
        self.nav_label.pack(side="left", padx=PAD["sm"])

        self.next_btn = ttk.Button(
            nav, text="Next ▶", style="Ghost.TButton",
            command=self._next_suggestion,
        )
        self.next_btn.pack(side="left")

        ttk.Button(
            nav, text="Accept All Remaining",
            style="Success.TButton",
            command=self._accept_all,
        ).pack(side="right", padx=(PAD["xs"], 0))

        ttk.Button(
            nav, text="Finish Review →",
            style="TButton",
            command=self._finish_review,
        ).pack(side="right")

    # ── Suggestion card rendering ────────────────────────────────────────────

    def _show_suggestion(self, index: int):
        """Render the suggestion at the given index in the main area."""
        self._current_index = index
        self._update_nav_state()

        # Clear content area
        for widget in self.content_inner.winfo_children():
            widget.destroy()

        if not self._suggestions:
            self._show_no_suggestions()
            return

        s = self._suggestions[index]
        emoji, type_label, type_color = TYPE_LABELS.get(
            s.suggestion_type, ("💡", "Improvement", COLORS["text_secondary"])
        )

        # ── Suggestion header ──────────────────────────────────────────────
        header = tk.Frame(self.content_inner, bg=COLORS["bg_secondary"],
                           padx=PAD["md"], pady=PAD["sm"])
        header.pack(fill="x", pady=(0, PAD["sm"]))

        tk.Label(
            header,
            text=f"{emoji}  {type_label}",
            font=FONTS["subheading"],
            bg=COLORS["bg_secondary"], fg=type_color,
        ).pack(side="left")

        section_badge = tk.Label(
            header, text=f"  {s.section_name}  ",
            font=FONTS["small_bold"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            padx=4,
        )
        section_badge.pack(side="right")

        # Status indicator
        if s.status == SuggestionStatus.ACCEPTED:
            status_text, status_color = "✓ Accepted", COLORS["success"]
        elif s.status == SuggestionStatus.REJECTED:
            status_text, status_color = "✗ Rejected", COLORS["danger"]
        else:
            status_text, status_color = "● Pending", COLORS["warning"]

        tk.Label(
            header, text=status_text,
            font=FONTS["small_bold"],
            bg=COLORS["bg_secondary"], fg=status_color,
        ).pack(side="right", padx=PAD["sm"])

        # ── Reason box ────────────────────────────────────────────────────
        reason_frame = tk.Frame(self.content_inner, bg=COLORS["bg_surface"],
                                 padx=PAD["sm"], pady=PAD["sm"])
        reason_frame.pack(fill="x", pady=(0, PAD["sm"]))

        tk.Label(
            reason_frame, text="WHY THIS MATTERS",
            font=FONTS["small_bold"],
            bg=COLORS["bg_surface"], fg=COLORS["text_muted"],
        ).pack(anchor="w")
        tk.Label(
            reason_frame, text=s.reason,
            font=FONTS["body"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            wraplength=700, justify="left",
        ).pack(anchor="w")

        # ── Original text ─────────────────────────────────────────────────
        orig_frame = tk.Frame(self.content_inner, bg=COLORS["bg_secondary"],
                               padx=PAD["md"], pady=PAD["sm"])
        orig_frame.pack(fill="x", pady=(0, PAD["xs"]))

        tk.Label(
            orig_frame, text="ORIGINAL",
            font=FONTS["small_bold"],
            bg=COLORS["bg_secondary"], fg=COLORS["danger"],
        ).pack(anchor="w")

        orig_text_frame = tk.Frame(orig_frame, bg=COLORS["bg_surface"],
                                    padx=8, pady=6,
                                    highlightthickness=1,
                                    highlightbackground=COLORS["danger"])
        orig_text_frame.pack(fill="x")

        tk.Label(
            orig_text_frame, text=s.original_text,
            font=FONTS["mono"],
            bg=COLORS["bg_surface"], fg=COLORS["text_primary"],
            wraplength=700, justify="left", anchor="w",
        ).pack(fill="x")

        # ── Suggested text (editable) ─────────────────────────────────────
        sugg_frame = tk.Frame(self.content_inner, bg=COLORS["bg_secondary"],
                               padx=PAD["md"], pady=PAD["sm"])
        sugg_frame.pack(fill="x", pady=(0, PAD["sm"]))

        tk.Label(
            sugg_frame, text="SUGGESTED  (click to edit)",
            font=FONTS["small_bold"],
            bg=COLORS["bg_secondary"], fg=COLORS["success"],
        ).pack(anchor="w")

        text_edit_frame = tk.Frame(sugg_frame, bg=COLORS["bg_surface"],
                                    highlightthickness=1,
                                    highlightbackground=COLORS["success"])
        text_edit_frame.pack(fill="x")

        self.edit_textbox = tk.Text(
            text_edit_frame,
            font=FONTS["mono"],
            bg=COLORS["bg_surface"],
            fg=COLORS["success"],
            insertbackground=COLORS["success"],
            relief="flat",
            wrap="word",
            height=4,
            padx=8, pady=6,
        )
        self.edit_textbox.insert("1.0", s.edited_text or s.suggested_text)
        self.edit_textbox.pack(fill="x")

        # ── Accept / Reject buttons ───────────────────────────────────────
        action_row = tk.Frame(self.content_inner, bg=COLORS["bg_primary"])
        action_row.pack(fill="x", pady=(PAD["sm"], 0))

        ttk.Button(
            action_row,
            text="✓  Accept (OK)",
            style="Success.TButton",
            command=lambda idx=index: self._accept_suggestion(idx),
        ).pack(side="left", padx=(0, PAD["xs"]))

        ttk.Button(
            action_row,
            text="✗  Reject (Cancel)",
            style="Danger.TButton",
            command=lambda idx=index: self._reject_suggestion(idx),
        ).pack(side="left")

        if s.status != SuggestionStatus.PENDING:
            ttk.Button(
                action_row,
                text="↺ Reset to Pending",
                style="Ghost.TButton",
                command=lambda idx=index: self._reset_suggestion(idx),
            ).pack(side="left", padx=(PAD["xs"], 0))

        # Highlight in sidebar
        self._highlight_list_item(index)

    def _show_no_suggestions(self):
        for widget in self.content_inner.winfo_children():
            widget.destroy()
        tk.Label(
            self.content_inner,
            text=(
                "🎉  No improvements needed!\n\n"
                "Your CV is already well-aligned with the job description.\n"
                "Proceed to the preview to download your CV."
            ),
            font=FONTS["heading"],
            bg=COLORS["bg_primary"], fg=COLORS["success"],
            justify="center",
        ).pack(expand=True, pady=60)

    # ── Sidebar list ─────────────────────────────────────────────────────────

    def _rebuild_list(self):
        """Rebuild the sidebar suggestion list."""
        for widget in self.list_inner.winfo_children():
            widget.destroy()
        self._list_items.clear()

        for i, s in enumerate(self._suggestions):
            emoji, _, color = TYPE_LABELS.get(
                s.suggestion_type, ("💡", "Improvement", COLORS["text_secondary"])
            )

            if s.status == SuggestionStatus.ACCEPTED:
                status_mark, status_color = "✓", COLORS["success"]
            elif s.status == SuggestionStatus.REJECTED:
                status_mark, status_color = "✗", COLORS["danger"]
            else:
                status_mark, status_color = "●", COLORS["warning"]

            item = tk.Frame(
                self.list_inner, bg=COLORS["bg_secondary"],
                padx=PAD["sm"], pady=PAD["xs"],
                cursor="hand2",
            )
            item.pack(fill="x")

            row = tk.Frame(item, bg=COLORS["bg_secondary"])
            row.pack(fill="x")

            tk.Label(
                row, text=status_mark,
                font=FONTS["small_bold"],
                bg=COLORS["bg_secondary"], fg=status_color,
                width=2,
            ).pack(side="left")

            tk.Label(
                row, text=emoji,
                font=FONTS["small"],
                bg=COLORS["bg_secondary"], fg=color,
            ).pack(side="left")

            preview = (s.original_text[:35] + "…"
                       if len(s.original_text) > 35 else s.original_text)
            tk.Label(
                row, text=preview,
                font=FONTS["small"],
                bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                anchor="w",
            ).pack(side="left", fill="x")

            # Click to jump to suggestion
            idx = i
            for widget in [item, row] + list(row.winfo_children()):
                widget.bind("<Button-1>", lambda e, n=idx: self._show_suggestion(n))

            self._list_items.append(item)

    def _highlight_list_item(self, index: int):
        """Visually highlight the active list item."""
        for i, item in enumerate(self._list_items):
            bg = COLORS["bg_hover"] if i == index else COLORS["bg_secondary"]
            item.configure(bg=bg)
            for child in item.winfo_children():
                child.configure(bg=bg)
                for grandchild in child.winfo_children():
                    try:
                        grandchild.configure(bg=bg)
                    except Exception:
                        pass

    # ── Actions ─────────────────────────────────────────────────────────────

    def _accept_suggestion(self, index: int):
        s = self._suggestions[index]
        edited = self.edit_textbox.get("1.0", "end").strip()
        s.accept(edited if edited != s.suggested_text else None)
        self._post_action(index)

    def _reject_suggestion(self, index: int):
        self._suggestions[index].reject()
        self._post_action(index)

    def _reset_suggestion(self, index: int):
        from core.models import SuggestionStatus
        s = self._suggestions[index]
        s.status = SuggestionStatus.PENDING
        s.edited_text = ""
        self._post_action(index)

    def _post_action(self, index: int):
        """After any accept/reject, refresh UI and auto-advance."""
        self._rebuild_list()
        self._refresh_summary()
        # Auto-advance to next pending suggestion
        next_pending = self._find_next_pending(index + 1)
        if next_pending is not None:
            self._show_suggestion(next_pending)
        else:
            self._show_suggestion(index)  # Stay but refresh

    def _find_next_pending(self, start: int) -> Optional[int]:
        """Find the next PENDING suggestion at or after start."""
        for i in range(start, len(self._suggestions)):
            if self._suggestions[i].status == SuggestionStatus.PENDING:
                return i
        # Wrap around
        for i in range(0, start):
            if self._suggestions[i].status == SuggestionStatus.PENDING:
                return i
        return None

    def _accept_all(self):
        """Accept all remaining pending suggestions."""
        for s in self._suggestions:
            if s.status == SuggestionStatus.PENDING:
                s.accept()
        self._rebuild_list()
        self._refresh_summary()
        if self._suggestions:
            self._show_suggestion(0)

    def _prev_suggestion(self):
        if self._current_index > 0:
            self._show_suggestion(self._current_index - 1)

    def _next_suggestion(self):
        if self._current_index < len(self._suggestions) - 1:
            self._show_suggestion(self._current_index + 1)

    def _finish_review(self):
        self.app.next_step()

    # ── State ────────────────────────────────────────────────────────────────

    def _refresh_summary(self):
        result = self.app.analysis_result
        if not result:
            return

        total = result.total_count
        accepted = result.accepted_count
        pending = len(result.pending_suggestions)

        self.summary_stats.configure(
            text=(
                f"Total: {total}\n"
                f"Accepted: {accepted}\n"
                f"Pending: {pending}"
            )
        )

        mode_text = (
            "🤖 AI Mode" if result.processing_mode.value == "ai_assisted"
            else "⚡ Standard Mode"
        )
        self.mode_badge.configure(text=mode_text)
        self.score_label.configure(
            text=f"Match Score: {result.match_score}%  —  {result.summary.split(chr(10))[1] if chr(10) in result.summary else ''}",
            fg=COLORS["info"],
        )
        self._rebuild_list()
        self._update_nav_state()

    def _update_nav_state(self):
        n = len(self._suggestions)
        if n == 0:
            self.nav_label.configure(text="0 / 0")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            return

        idx = self._current_index
        self.nav_label.configure(text=f"{idx + 1} / {n}")
        self.prev_btn.configure(state="normal" if idx > 0 else "disabled")
        self.next_btn.configure(state="normal" if idx < n - 1 else "disabled")

    # ── Canvas scrolling helpers ─────────────────────────────────────────────

    def _on_list_resize(self, event):
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.list_canvas.itemconfig(
            self.list_canvas_window, width=event.width
        )