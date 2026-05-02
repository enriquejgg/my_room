"""
UI Styles — colour palette, fonts, and widget configuration for CV Tailor.
Applies a clean, professional dark-accented theme using tkinter ttk styles.
"""
import tkinter as tk
from tkinter import ttk


# ── Colour Palette ────────────────────────────────────────────────────────────

COLORS = {
    # Backgrounds
    "bg_primary":    "#0f1117",   # App background (near-black)
    "bg_secondary":  "#1a1d27",   # Card / panel background
    "bg_surface":    "#242736",   # Input fields, list backgrounds
    "bg_hover":      "#2e3148",   # Hover state

    # Accents
    "accent":        "#6c63ff",   # Primary action (indigo-purple)
    "accent_light":  "#8b85ff",
    "accent_dark":   "#4f46c8",
    "success":       "#22c55e",   # Accept / OK
    "danger":        "#ef4444",   # Reject / Cancel
    "warning":       "#f59e0b",   # Warning / pending
    "info":          "#38bdf8",   # Info text

    # Text
    "text_primary":  "#e8eaf6",   # Main text
    "text_secondary":"#9fa3c7",   # Muted labels
    "text_muted":    "#5c6080",   # Very subtle
    "text_on_accent":"#ffffff",

    # Borders
    "border":        "#2e3148",
    "border_light":  "#3a3f5c",
}

FONTS = {
    "title":      ("Segoe UI", 18, "bold"),
    "heading":    ("Segoe UI", 13, "bold"),
    "subheading": ("Segoe UI", 11, "bold"),
    "body":       ("Segoe UI", 10),
    "body_bold":  ("Segoe UI", 10, "bold"),
    "small":      ("Segoe UI", 9),
    "small_bold": ("Segoe UI", 9, "bold"),
    "mono":       ("Consolas", 10),
    "mono_small": ("Consolas", 9),
    "button":     ("Segoe UI", 10, "bold"),
}

PAD = {
    "xs": 4,
    "sm": 8,
    "md": 14,
    "lg": 20,
    "xl": 32,
}


# ── Step definitions ──────────────────────────────────────────────────────────

STEPS = [
    ("1", "Upload Files"),
    ("2", "Select Mode"),
    ("3", "Review Suggestions"),
    ("4", "Preview & Download"),
]


# ── Style setup function ──────────────────────────────────────────────────────

def apply_theme(root: tk.Tk):
    """
    Apply the dark theme to a Tk root window and configure ttk styles.
    Must be called once after creating the root window.
    """
    root.configure(bg=COLORS["bg_primary"])

    style = ttk.Style(root)
    style.theme_use("clam")

    # ── Frame ──────────────────────────────────────────────────────────────
    style.configure(
        "TFrame",
        background=COLORS["bg_primary"],
    )
    style.configure(
        "Card.TFrame",
        background=COLORS["bg_secondary"],
        relief="flat",
    )
    style.configure(
        "Surface.TFrame",
        background=COLORS["bg_surface"],
    )

    # ── Label ──────────────────────────────────────────────────────────────
    style.configure(
        "TLabel",
        background=COLORS["bg_primary"],
        foreground=COLORS["text_primary"],
        font=FONTS["body"],
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["bg_primary"],
        foreground=COLORS["text_primary"],
        font=FONTS["title"],
    )
    style.configure(
        "Heading.TLabel",
        background=COLORS["bg_secondary"],
        foreground=COLORS["text_primary"],
        font=FONTS["heading"],
    )
    style.configure(
        "Muted.TLabel",
        background=COLORS["bg_secondary"],
        foreground=COLORS["text_secondary"],
        font=FONTS["small"],
    )
    style.configure(
        "Accent.TLabel",
        background=COLORS["bg_secondary"],
        foreground=COLORS["accent_light"],
        font=FONTS["body_bold"],
    )
    style.configure(
        "Success.TLabel",
        background=COLORS["bg_secondary"],
        foreground=COLORS["success"],
        font=FONTS["body"],
    )
    style.configure(
        "Danger.TLabel",
        background=COLORS["bg_secondary"],
        foreground=COLORS["danger"],
        font=FONTS["body"],
    )
    style.configure(
        "Warning.TLabel",
        background=COLORS["bg_secondary"],
        foreground=COLORS["warning"],
        font=FONTS["body"],
    )

    # ── Button ─────────────────────────────────────────────────────────────
    style.configure(
        "TButton",
        background=COLORS["accent"],
        foreground=COLORS["text_on_accent"],
        font=FONTS["button"],
        borderwidth=0,
        focusthickness=0,
        padding=(16, 8),
        relief="flat",
    )
    style.map(
        "TButton",
        background=[("active", COLORS["accent_light"]),
                    ("disabled", COLORS["bg_surface"])],
        foreground=[("disabled", COLORS["text_muted"])],
    )
    style.configure(
        "Success.TButton",
        background=COLORS["success"],
        foreground="#ffffff",
        font=FONTS["button"],
        padding=(14, 8),
    )
    style.map("Success.TButton",
              background=[("active", "#16a34a")])

    style.configure(
        "Danger.TButton",
        background=COLORS["danger"],
        foreground="#ffffff",
        font=FONTS["button"],
        padding=(14, 8),
    )
    style.map("Danger.TButton",
              background=[("active", "#dc2626")])

    style.configure(
        "Ghost.TButton",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_secondary"],
        font=FONTS["button"],
        padding=(14, 8),
    )
    style.map("Ghost.TButton",
              background=[("active", COLORS["bg_hover"])],
              foreground=[("active", COLORS["text_primary"])])

    # ── Entry / Text ────────────────────────────────────────────────────────
    style.configure(
        "TEntry",
        fieldbackground=COLORS["bg_surface"],
        foreground=COLORS["text_primary"],
        insertcolor=COLORS["accent"],
        borderwidth=1,
        relief="flat",
        font=FONTS["body"],
    )

    # ── Scrollbar ──────────────────────────────────────────────────────────
    style.configure(
        "TScrollbar",
        background=COLORS["bg_surface"],
        troughcolor=COLORS["bg_secondary"],
        borderwidth=0,
        arrowsize=12,
    )
    style.map("TScrollbar",
              background=[("active", COLORS["border_light"])])

    # ── Progressbar ────────────────────────────────────────────────────────
    style.configure(
        "TProgressbar",
        background=COLORS["accent"],
        troughcolor=COLORS["bg_surface"],
        borderwidth=0,
        thickness=6,
    )

    # ── Separator ──────────────────────────────────────────────────────────
    style.configure(
        "TSeparator",
        background=COLORS["border"],
    )

    # ── Notebook ───────────────────────────────────────────────────────────
    style.configure(
        "TNotebook",
        background=COLORS["bg_primary"],
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_secondary"],
        padding=(12, 6),
        font=FONTS["small_bold"],
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["bg_secondary"])],
        foreground=[("selected", COLORS["accent_light"])],
    )