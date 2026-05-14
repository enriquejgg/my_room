"""
Welcome Frame — the home screen shown at startup and when the Home button is clicked.
Provides a brief overview of the app and a single "Get Started" button.
"""
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


# Feature cards shown on the home screen
_FEATURES = [
    ("📄", "upload.feat.title",   "upload.feat.body"),
    ("🔍", "analyze.feat.title",  "analyze.feat.body"),
    ("✍",  "review.feat.title",   "review.feat.body"),
    ("📋", "browse.feat.title",   "browse.feat.body"),
    ("🔒", "privacy.feat.title",  "privacy.feat.body"),
    ("🌐", "lang.feat.title",     "lang.feat.body"),
]


class WelcomeFrame(tk.Frame):
    """Step 0 — landing / home screen."""

    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._build_ui()

    def _t(self, key, **kw): return self.app.t(key, **kw)

    def on_enter(self):
        """Refresh all text labels whenever language changes or home is revisited."""
        self._refresh_labels()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer scroll-safe container
        outer = tk.Frame(self, bg=COLORS["bg_primary"])
        outer.place(relx=0.5, rely=0.5, anchor="center",
                    relwidth=0.90, relheight=0.95)

        # ── Hero section ──────────────────────────────────────────────────
        hero = tk.Frame(outer, bg=COLORS["bg_primary"])
        hero.pack(fill="x", pady=(0, PAD["xl"]))

        # Accent bar left of title
        accent_bar = tk.Frame(hero, bg=COLORS["accent"], width=6)
        accent_bar.pack(side="left", fill="y", padx=(0, PAD["md"]))

        title_block = tk.Frame(hero, bg=COLORS["bg_primary"])
        title_block.pack(side="left", fill="x", expand=True)

        self._hero_title = tk.Label(
            title_block,
            text=self._t("welcome.title"),
            font=("Segoe UI", 28, "bold"),
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
            anchor="w",
        )
        self._hero_title.pack(anchor="w")

        self._hero_sub = tk.Label(
            title_block,
            text=self._t("welcome.subtitle"),
            font=FONTS["heading"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
            anchor="w",
            wraplength=700,
            justify="left",
        )
        self._hero_sub.pack(anchor="w", pady=(4, 0))

        # Get Started button
        btn_frame = tk.Frame(hero, bg=COLORS["bg_primary"])
        btn_frame.pack(side="right", padx=PAD["lg"])

        self._start_btn = ttk.Button(
            btn_frame,
            text=self._t("welcome.btn.start"),
            style="TButton",
            command=self._on_start,
        )
        self._start_btn.pack()

        # ── Feature grid (2 × 3) ─────────────────────────────────────────
        grid = tk.Frame(outer, bg=COLORS["bg_primary"])
        grid.pack(fill="both", expand=True)

        for col in range(3):
            grid.columnconfigure(col, weight=1, uniform="feat")

        self._feat_widgets = []     # (icon_lbl, title_lbl, body_lbl, key_title, key_body)
        for idx, (icon, title_key, body_key) in enumerate(_FEATURES):
            row, col = divmod(idx, 3)
            card = tk.Frame(
                grid,
                bg=COLORS["bg_secondary"],
                padx=PAD["md"], pady=PAD["md"],
            )
            card.grid(row=row, column=col, sticky="nsew",
                      padx=PAD["xs"], pady=PAD["xs"])

            top_row = tk.Frame(card, bg=COLORS["bg_secondary"])
            top_row.pack(anchor="w", fill="x")

            icon_lbl = tk.Label(
                top_row, text=icon,
                font=("Segoe UI Emoji", 18),
                bg=COLORS["bg_secondary"], fg=COLORS["accent_light"],
            )
            icon_lbl.pack(side="left", padx=(0, PAD["xs"]))

            title_lbl = tk.Label(
                top_row,
                text=self._t(title_key),
                font=FONTS["subheading"],
                bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
            )
            title_lbl.pack(side="left")

            body_lbl = tk.Label(
                card,
                text=self._t(body_key),
                font=FONTS["small"],
                bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                wraplength=260,
                justify="left",
            )
            body_lbl.pack(anchor="w", pady=(PAD["xs"], 0))

            self._feat_widgets.append((title_lbl, body_lbl, title_key, body_key))

        # ── Footer strip ─────────────────────────────────────────────────
        footer = tk.Frame(outer, bg=COLORS["bg_surface"],
                           padx=PAD["md"], pady=PAD["sm"])
        footer.pack(fill="x", pady=(PAD["lg"], 0))

        self._footer_lbl = tk.Label(
            footer,
            text=self._t("welcome.footer"),
            font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["text_muted"],
            justify="center",
        )
        self._footer_lbl.pack()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_start(self):
        self.app.go_to_step(1)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh_labels(self):
        self._hero_title.configure(text=self._t("welcome.title"))
        self._hero_sub.configure(text=self._t("welcome.subtitle"))
        self._start_btn.configure(text=self._t("welcome.btn.start"))
        self._footer_lbl.configure(text=self._t("welcome.footer"))
        for title_lbl, body_lbl, title_key, body_key in self._feat_widgets:
            title_lbl.configure(text=self._t(title_key))
            body_lbl.configure(text=self._t(body_key))