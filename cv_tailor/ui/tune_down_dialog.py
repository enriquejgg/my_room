"""
Tune-Down Dialog — asks the user whether they want to suppress overqualified
content to better match the seniority level of the job description.

Shown automatically after analysis when overqualification signals are detected.
The user can:
  - See a summary of what was detected
  - Choose Yes (generate tune-down suggestions added to the review queue)
  - Choose No (skip tune-down entirely, go straight to Step 3)
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Dict, Optional

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


# Severity → colour mapping
_SEVERITY_COLOR = {
    "high":   "#ef4444",   # red
    "medium": "#f59e0b",   # amber
    "low":    "#38bdf8",   # blue
}
_SEVERITY_ICON = {
    "high":   "⚠",
    "medium": "△",
    "low":    "ℹ",
}


class TuneDownDialog(tk.Toplevel):
    """
    Modal dialog presenting overqualification findings and asking for user consent.
    self.user_agreed is True if the user clicked "Yes, tune it down", False otherwise.
    """

    def __init__(self, parent: tk.Widget, app: "CVTailorApp",
                 findings: List[Dict]):
        super().__init__(parent)
        self.app = app
        self.findings = findings
        self.user_agreed: bool = False

        self.title(self._t("tunedown.dialog.title"))
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()

        self._build_ui()
        self._center(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_no)

    def _t(self, key, **kw):
        return self.app.t(key, **kw)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg_surface"],
                           padx=PAD["lg"], pady=PAD["md"])
        header.pack(fill="x")

        tk.Label(
            header,
            text="🎯  " + self._t("tunedown.dialog.heading"),
            font=FONTS["heading"],
            bg=COLORS["bg_surface"], fg=COLORS["text_primary"],
        ).pack(anchor="w")

        tk.Label(
            header,
            text=self._t("tunedown.dialog.intro"),
            font=FONTS["body"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            wraplength=520, justify="left",
        ).pack(anchor="w", pady=(PAD["xs"], 0))

        # ── Findings list ─────────────────────────────────────────────────
        findings_frame = tk.Frame(self, bg=COLORS["bg_primary"],
                                   padx=PAD["lg"], pady=PAD["md"])
        findings_frame.pack(fill="x")

        tk.Label(
            findings_frame,
            text=self._t("tunedown.dialog.findings_label"),
            font=FONTS["small_bold"],
            bg=COLORS["bg_primary"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, PAD["xs"]))

        for finding in self.findings:
            severity = finding.get("severity", "low")
            color    = _SEVERITY_COLOR.get(severity, COLORS["warning"])
            icon     = _SEVERITY_ICON.get(severity, "•")

            row = tk.Frame(findings_frame, bg=COLORS["bg_secondary"],
                            padx=PAD["sm"], pady=PAD["sm"])
            row.pack(fill="x", pady=2)

            # Icon + area title
            top = tk.Frame(row, bg=COLORS["bg_secondary"])
            top.pack(fill="x")

            tk.Label(top, text=icon, font=FONTS["body_bold"],
                     bg=COLORS["bg_secondary"], fg=color,
                     width=2).pack(side="left")
            tk.Label(top, text=finding.get("area", ""),
                     font=FONTS["body_bold"],
                     bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
                     anchor="w").pack(side="left")

            # Detail
            detail = finding.get("detail", "")
            if detail:
                tk.Label(row, text=detail,
                         font=FONTS["small"],
                         bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                         wraplength=500, justify="left",
                         anchor="w").pack(anchor="w", padx=(22, 0))

        # ── Privacy notice ────────────────────────────────────────────────
        notice = tk.Frame(self, bg=COLORS["bg_surface"],
                           padx=PAD["lg"], pady=PAD["sm"])
        notice.pack(fill="x")

        tk.Label(
            notice,
            text="🔒  " + self._t("tunedown.dialog.privacy_note"),
            font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["info"],
            wraplength=520, justify="left",
        ).pack(anchor="w")

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=COLORS["bg_primary"],
                            padx=PAD["lg"], pady=PAD["md"])
        btn_row.pack(fill="x")

        ttk.Button(
            btn_row,
            text=self._t("tunedown.dialog.btn.no"),
            style="Ghost.TButton",
            command=self._on_no,
        ).pack(side="left")

        ttk.Button(
            btn_row,
            text=self._t("tunedown.dialog.btn.yes"),
            style="TButton",
            command=self._on_yes,
        ).pack(side="right")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_yes(self):
        self.user_agreed = True
        self.destroy()

    def _on_no(self):
        self.user_agreed = False
        self.destroy()

    def _center(self, parent: tk.Widget):
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()  // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w  = self.winfo_width()
        h  = self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")


def ask_tune_down(parent: tk.Widget, app: "CVTailorApp",
                  findings: List[Dict]) -> bool:
    """
    Show the tune-down dialog and return True if the user agreed, False otherwise.
    """
    dlg = TuneDownDialog(parent, app, findings)
    parent.wait_window(dlg)
    return dlg.user_agreed