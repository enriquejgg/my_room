"""
Upload Frame — Step 1: Upload CV (PDF) and Job Description.
Supports both click-to-browse AND drag-and-drop from the OS file manager.
Drag-and-drop requires tkinterdnd2 (pip install tkinterdnd2); if unavailable,
the browse button is the only upload method and the drop zone shows a notice.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import TYPE_CHECKING

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp

# Import DND constants — same try/except as app.py so both stay in sync
try:
    from tkinterdnd2 import DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False


def _clean_dnd_path(raw: str) -> str:
    """
    Normalise a path string returned by the DnD engine.
    On macOS/Linux, paths with spaces are wrapped in curly braces: {/my path/file.pdf}
    On Windows, multiple files are space-separated; we take only the first.
    """
    raw = raw.strip()
    # Multiple files — take the first only
    if raw.startswith('{'):
        raw = raw[1:raw.index('}')]
    else:
        raw = raw.split()[0]
    return raw.strip()


class UploadFrame(tk.Frame):
    """Step 1: CV and Job Description upload panel with drag-and-drop."""

    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._cv_path: str = ""
        self._jd_text: str = ""
        self._jd_tab: str = "text"
        self._jd_from_pdf: str = ""
        self._build_ui()

    def _t(self, key, **kw): return self.app.t(key, **kw)

    def on_enter(self):
        pass

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self, bg=COLORS["bg_primary"])
        outer.pack(fill="both", expand=True, padx=30, pady=16)

        # Title
        tk.Label(outer, text=self._t("upload.title"),
                 font=FONTS["title"], bg=COLORS["bg_primary"],
                 fg=COLORS["text_primary"]).pack(pady=(0, 4))
        tk.Label(outer, text=self._t("upload.subtitle"),
                 font=FONTS["body"], bg=COLORS["bg_primary"],
                 fg=COLORS["text_secondary"]).pack(pady=(0, PAD["lg"]))

        # Two-column layout
        cols = tk.Frame(outer, bg=COLORS["bg_primary"])
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="col")
        cols.columnconfigure(1, weight=1, uniform="col")

        self._build_cv_panel(cols)
        self._build_jd_panel(cols)

        # Navigation
        nav = tk.Frame(outer, bg=COLORS["bg_primary"])
        nav.pack(fill="x", pady=(PAD["lg"], 0))
        ttk.Button(nav, text=self._t("upload.continue"),
                   style="TButton",
                   command=self._on_continue).pack(side="right")

    # ── CV panel ──────────────────────────────────────────────────────────────

    def _build_cv_panel(self, parent):
        card = tk.Frame(parent, bg=COLORS["bg_secondary"],
                         padx=PAD["md"], pady=PAD["md"])
        card.grid(row=0, column=0, sticky="nsew", padx=(0, PAD["sm"]))

        tk.Label(card, text=self._t("upload.cv.heading"),
                 font=FONTS["heading"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_primary"]
                 ).pack(anchor="w", pady=(0, PAD["xs"]))
        tk.Label(card, text=self._t("upload.cv.hint"),
                 font=FONTS["small"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"]
                 ).pack(anchor="w", pady=(0, PAD["sm"]))

        # ── Drop zone ─────────────────────────────────────────────────────
        self.cv_drop_zone = tk.Frame(
            card, bg=COLORS["bg_surface"], height=160,
            highlightthickness=2,
            highlightbackground=COLORS["border"],
        )
        self.cv_drop_zone.pack(fill="x", pady=(0, PAD["sm"]))
        self.cv_drop_zone.pack_propagate(False)

        # Inner content
        inner = tk.Frame(self.cv_drop_zone, bg=COLORS["bg_surface"])
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self.cv_icon_lbl = tk.Label(inner, text="📂",
                                     font=("Segoe UI Emoji", 28),
                                     bg=COLORS["bg_surface"],
                                     fg=COLORS["text_muted"])
        self.cv_icon_lbl.pack()

        if _DND_AVAILABLE:
            drop_hint = self._t("upload.cv.drop_hint")
        else:
            drop_hint = self._t("upload.cv.drop_hint_unavailable")

        self.cv_drop_lbl = tk.Label(inner, text=drop_hint,
                                     font=FONTS["small"],
                                     bg=COLORS["bg_surface"],
                                     fg=COLORS["text_muted"])
        self.cv_drop_lbl.pack(pady=(4, 0))

        # Click-to-browse on the whole zone
        for widget in (self.cv_drop_zone, inner,
                       self.cv_icon_lbl, self.cv_drop_lbl):
            widget.bind("<Button-1>", lambda e: self._browse_cv())

        # Drag-and-drop registration
        if _DND_AVAILABLE:
            self.cv_drop_zone.drop_target_register(DND_FILES)
            self.cv_drop_zone.dnd_bind('<<Drop>>', self._on_cv_drop)
            self.cv_drop_zone.dnd_bind('<<DragEnter>>', self._on_cv_drag_enter)
            self.cv_drop_zone.dnd_bind('<<DragLeave>>', self._on_cv_drag_leave)

        # Status label
        self.cv_status = tk.Label(card, text=self._t("upload.cv.none"),
                                   font=FONTS["small"],
                                   bg=COLORS["bg_secondary"],
                                   fg=COLORS["text_muted"])
        self.cv_status.pack(anchor="w")

        ttk.Button(card, text=self._t("upload.cv.browse"),
                   style="Ghost.TButton",
                   command=self._browse_cv).pack(anchor="w", pady=(PAD["xs"], 0))

    # ── JD panel ──────────────────────────────────────────────────────────────

    def _build_jd_panel(self, parent):
        card = tk.Frame(parent, bg=COLORS["bg_secondary"],
                         padx=PAD["md"], pady=PAD["md"])
        card.grid(row=0, column=1, sticky="nsew", padx=(PAD["sm"], 0))

        # Header with tab buttons
        hdr = tk.Frame(card, bg=COLORS["bg_secondary"])
        hdr.pack(fill="x", pady=(0, PAD["sm"]))

        tk.Label(hdr, text=self._t("upload.jd.heading"),
                 font=FONTS["heading"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_primary"]
                 ).pack(side="left")

        self.jd_paste_btn = tk.Button(
            hdr, text=self._t("upload.jd.paste_btn"),
            font=FONTS["small_bold"], relief="flat",
            bg=COLORS["accent"], fg=COLORS["text_on_accent"],
            padx=8, pady=3, cursor="hand2",
            command=lambda: self._set_jd_tab("text"))
        self.jd_paste_btn.pack(side="right", padx=(PAD["xs"], 0))

        self.jd_pdf_btn = tk.Button(
            hdr, text=self._t("upload.jd.pdf_btn"),
            font=FONTS["small_bold"], relief="flat",
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            padx=8, pady=3, cursor="hand2",
            command=lambda: self._set_jd_tab("pdf"))
        self.jd_pdf_btn.pack(side="right")

        # ── Paste-text tab ────────────────────────────────────────────────
        self.jd_text_frame = tk.Frame(card, bg=COLORS["bg_secondary"])
        tk.Label(self.jd_text_frame,
                 text=self._t("upload.jd.paste_hint"),
                 font=FONTS["small"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"]
                 ).pack(anchor="w", pady=(0, PAD["xs"]))

        txt_wrap = tk.Frame(self.jd_text_frame, bg=COLORS["bg_surface"])
        txt_wrap.pack(fill="both", expand=True)
        self.jd_textbox = tk.Text(
            txt_wrap, font=FONTS["mono_small"],
            bg=COLORS["bg_surface"], fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            relief="flat", wrap="word", padx=8, pady=8, undo=True)
        jd_scroll = ttk.Scrollbar(txt_wrap, command=self.jd_textbox.yview)
        self.jd_textbox.configure(yscrollcommand=jd_scroll.set)
        jd_scroll.pack(side="right", fill="y")
        self.jd_textbox.pack(fill="both", expand=True)

        # ── Upload-PDF tab ────────────────────────────────────────────────
        self.jd_pdf_frame = tk.Frame(card, bg=COLORS["bg_secondary"])
        tk.Label(self.jd_pdf_frame,
                 text=self._t("upload.jd.pdf_hint"),
                 font=FONTS["small"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"]
                 ).pack(anchor="w", pady=(0, PAD["xs"]))

        # JD drop zone (also supports drag-and-drop)
        self.jd_drop_zone = tk.Frame(
            self.jd_pdf_frame, bg=COLORS["bg_surface"], height=120,
            highlightthickness=2,
            highlightbackground=COLORS["border"])
        self.jd_drop_zone.pack(fill="x", pady=(0, PAD["sm"]))
        self.jd_drop_zone.pack_propagate(False)

        jd_inner = tk.Frame(self.jd_drop_zone, bg=COLORS["bg_surface"])
        jd_inner.place(relx=0.5, rely=0.5, anchor="center")

        self.jd_icon_lbl = tk.Label(jd_inner, text="📋",
                                     font=("Segoe UI Emoji", 22),
                                     bg=COLORS["bg_surface"],
                                     fg=COLORS["text_muted"])
        self.jd_icon_lbl.pack()

        jd_drop_hint = (self._t("upload.jd.drop_hint") if _DND_AVAILABLE
                         else self._t("upload.cv.drop_hint_unavailable"))
        self.jd_drop_hint_lbl = tk.Label(jd_inner, text=jd_drop_hint,
                                          font=FONTS["small"],
                                          bg=COLORS["bg_surface"],
                                          fg=COLORS["text_muted"])
        self.jd_drop_hint_lbl.pack(pady=(4, 0))

        for widget in (self.jd_drop_zone, jd_inner,
                       self.jd_icon_lbl, self.jd_drop_hint_lbl):
            widget.bind("<Button-1>", lambda e: self._browse_jd_pdf())

        if _DND_AVAILABLE:
            self.jd_drop_zone.drop_target_register(DND_FILES)
            self.jd_drop_zone.dnd_bind('<<Drop>>', self._on_jd_drop)
            self.jd_drop_zone.dnd_bind('<<DragEnter>>', self._on_jd_drag_enter)
            self.jd_drop_zone.dnd_bind('<<DragLeave>>', self._on_jd_drag_leave)

        self.jd_pdf_status = tk.Label(
            self.jd_pdf_frame, text=self._t("upload.jd.none"),
            font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_muted"])
        self.jd_pdf_status.pack(anchor="w")

        ttk.Button(self.jd_pdf_frame,
                   text=self._t("upload.jd.browse"),
                   style="Ghost.TButton",
                   command=self._browse_jd_pdf).pack(anchor="w",
                                                      pady=(PAD["xs"], 0))

        self._set_jd_tab("text")

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _set_jd_tab(self, tab: str):
        self._jd_tab = tab
        if tab == "text":
            self.jd_pdf_frame.pack_forget()
            self.jd_text_frame.pack(fill="both", expand=True)
            self.jd_paste_btn.configure(bg=COLORS["accent"],
                                         fg=COLORS["text_on_accent"])
            self.jd_pdf_btn.configure(bg=COLORS["bg_surface"],
                                       fg=COLORS["text_secondary"])
        else:
            self.jd_text_frame.pack_forget()
            self.jd_pdf_frame.pack(fill="both", expand=True)
            self.jd_pdf_btn.configure(bg=COLORS["accent"],
                                       fg=COLORS["text_on_accent"])
            self.jd_paste_btn.configure(bg=COLORS["bg_surface"],
                                         fg=COLORS["text_secondary"])

    # ── Browse actions ────────────────────────────────────────────────────────

    def _browse_cv(self):
        path = filedialog.askopenfilename(
            title="Select your CV",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if path:
            self._set_cv(path)

    def _browse_jd_pdf(self):
        path = filedialog.askopenfilename(
            title="Select Job Description PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if path:
            self._set_jd_pdf(path)

    # ── Drag-and-drop handlers — CV ───────────────────────────────────────────

    def _on_cv_drop(self, event):
        path = _clean_dnd_path(event.data)
        self._on_cv_drag_leave(None)   # restore normal border
        if not path.lower().endswith('.pdf'):
            messagebox.showwarning(
                "PDF Only",
                "Please drop a PDF file for your CV.",
                parent=self)
            return
        self._set_cv(path)

    def _on_cv_drag_enter(self, event):
        self.cv_drop_zone.configure(
            highlightbackground=COLORS["accent"],
            highlightthickness=3)

    def _on_cv_drag_leave(self, event):
        self.cv_drop_zone.configure(
            highlightbackground=COLORS["border"],
            highlightthickness=2)

    # ── Drag-and-drop handlers — JD ───────────────────────────────────────────

    def _on_jd_drop(self, event):
        path = _clean_dnd_path(event.data)
        self._on_jd_drag_leave(None)
        if not path.lower().endswith('.pdf'):
            messagebox.showwarning(
                "PDF Only",
                "Please drop a PDF file for the job description.",
                parent=self)
            return
        self._set_jd_pdf(path)

    def _on_jd_drag_enter(self, event):
        self.jd_drop_zone.configure(
            highlightbackground=COLORS["accent"],
            highlightthickness=3)

    def _on_jd_drag_leave(self, event):
        self.jd_drop_zone.configure(
            highlightbackground=COLORS["border"],
            highlightthickness=2)

    # ── State setters ─────────────────────────────────────────────────────────

    def _set_cv(self, path: str):
        """Accept a validated CV path and update the UI."""
        self._cv_path = path
        filename = Path(path).name
        self.cv_status.configure(
            text=f"✓  {filename}", fg=COLORS["success"])
        self.cv_icon_lbl.configure(text="✅")
        self.cv_drop_lbl.configure(
            text=filename, fg=COLORS["success"])
        self.cv_drop_zone.configure(
            highlightbackground=COLORS["success"])

    def _set_jd_pdf(self, path: str):
        """Accept a validated JD PDF path, extract text, and update the UI."""
        try:
            from core.pdf_parser import extract_text_from_pdf
            text, _ = extract_text_from_pdf(path)
            self._jd_from_pdf = text
            filename = Path(path).name
            self.jd_pdf_status.configure(
                text=f"✓  {filename}", fg=COLORS["success"])
            self.jd_icon_lbl.configure(text="✅")
            self.jd_drop_hint_lbl.configure(
                text=filename, fg=COLORS["success"])
            self.jd_drop_zone.configure(
                highlightbackground=COLORS["success"])
            # Auto-switch to PDF tab if user dropped on it
            self._set_jd_tab("pdf")
        except Exception as e:
            messagebox.showerror("Error",
                                  f"Could not read PDF:\n{e}", parent=self)

    # ── Validation & navigation ───────────────────────────────────────────────

    def _on_continue(self):
        if not self._cv_path:
            messagebox.showwarning(
                self._t("upload.warn.title_cv"),
                self._t("upload.warn.no_cv"), parent=self)
            return

        if self._jd_tab == "text":
            jd_text = self.jd_textbox.get("1.0", "end").strip()
        else:
            jd_text = self._jd_from_pdf.strip()

        if not jd_text or len(jd_text) < 50:
            messagebox.showwarning(
                self._t("upload.warn.title_jd"),
                self._t("upload.warn.no_jd"), parent=self)
            return

        self.app.set_cv_path(self._cv_path)
        self.app.set_jd_text(jd_text)
        self.app.next_step()