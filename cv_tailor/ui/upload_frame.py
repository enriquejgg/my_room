"""
Upload Frame — Step 1: Upload CV (PDF) and Job Description.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import TYPE_CHECKING

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


class UploadFrame(tk.Frame):
    """Step 1: CV and Job Description upload panel."""

    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._cv_path: str = ""
        self._jd_text: str = ""
        self._build_ui()

    def on_enter(self):
        """Called when this frame becomes visible."""
        pass

    # ── Build UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Outer centering wrapper
        outer = tk.Frame(self, bg=COLORS["bg_primary"])
        outer.pack(fill="both", expand=True, padx=30, pady=16)

        # Title
        tk.Label(
            outer,
            text="Upload Your CV & Job Description",
            font=FONTS["title"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
        ).pack(pady=(0, 4))
        tk.Label(
            outer,
            text="Start by providing your CV (PDF) and the role you're targeting.",
            font=FONTS["body"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(pady=(0, PAD["lg"]))

        # Two-column layout: CV left, JD right
        cols = tk.Frame(outer, bg=COLORS["bg_primary"])
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1, uniform="col")
        cols.columnconfigure(1, weight=1, uniform="col")

        self._build_cv_panel(cols)
        self._build_jd_panel(cols)

        # Navigation
        nav = tk.Frame(outer, bg=COLORS["bg_primary"])
        nav.pack(fill="x", pady=(PAD["lg"], 0))

        ttk.Button(
            nav,
            text="Continue →",
            style="TButton",
            command=self._on_continue,
        ).pack(side="right")

    def _build_cv_panel(self, parent):
        """Left panel: CV PDF upload."""
        card = tk.Frame(parent, bg=COLORS["bg_secondary"],
                         padx=PAD["md"], pady=PAD["md"])
        card.grid(row=0, column=0, sticky="nsew", padx=(0, PAD["sm"]))

        tk.Label(
            card, text="📄  Curriculum Vitae",
            font=FONTS["heading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
        ).pack(anchor="w", pady=(0, PAD["sm"]))

        tk.Label(
            card, text="Upload your CV as a PDF file.",
            font=FONTS["small"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, PAD["md"]))

        # Drop zone
        self.cv_drop_zone = tk.Frame(
            card, bg=COLORS["bg_surface"], height=140,
            highlightthickness=2,
            highlightbackground=COLORS["border"],
        )
        self.cv_drop_zone.pack(fill="x", pady=(0, PAD["sm"]))
        self.cv_drop_zone.pack_propagate(False)

        self.cv_icon_label = tk.Label(
            self.cv_drop_zone, text="📂",
            font=("Segoe UI Emoji", 32),
            bg=COLORS["bg_surface"], fg=COLORS["text_muted"],
        )
        self.cv_icon_label.pack(expand=True)
        self.cv_drop_zone.bind("<Button-1>", lambda e: self._browse_cv())
        self.cv_icon_label.bind("<Button-1>", lambda e: self._browse_cv())

        # Status label
        self.cv_status = tk.Label(
            card, text="No file selected",
            font=FONTS["small"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_muted"],
        )
        self.cv_status.pack(anchor="w")

        ttk.Button(
            card, text="Browse PDF…", style="Ghost.TButton",
            command=self._browse_cv,
        ).pack(anchor="w", pady=(PAD["xs"], 0))

    def _build_jd_panel(self, parent):
        """Right panel: Job Description text input."""
        card = tk.Frame(parent, bg=COLORS["bg_secondary"],
                         padx=PAD["md"], pady=PAD["md"])
        card.grid(row=0, column=1, sticky="nsew", padx=(PAD["sm"], 0))

        # Header row with tab buttons
        header_row = tk.Frame(card, bg=COLORS["bg_secondary"])
        header_row.pack(fill="x", pady=(0, PAD["sm"]))

        tk.Label(
            header_row, text="📋  Job Description",
            font=FONTS["heading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
        ).pack(side="left")

        self.jd_paste_btn = tk.Button(
            header_row, text="Paste Text",
            font=FONTS["small_bold"], relief="flat",
            bg=COLORS["accent"], fg=COLORS["text_on_accent"],
            padx=8, pady=3, cursor="hand2",
            command=lambda: self._set_jd_tab("text"),
        )
        self.jd_paste_btn.pack(side="right", padx=(PAD["xs"], 0))
        self.jd_pdf_btn = tk.Button(
            header_row, text="Upload PDF",
            font=FONTS["small_bold"], relief="flat",
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            padx=8, pady=3, cursor="hand2",
            command=lambda: self._set_jd_tab("pdf"),
        )
        self.jd_pdf_btn.pack(side="right")

        # Text input
        self.jd_text_frame = tk.Frame(card, bg=COLORS["bg_secondary"])
        self.jd_text_frame.pack(fill="both", expand=True)

        tk.Label(
            self.jd_text_frame,
            text="Paste the full job description below:",
            font=FONTS["small"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, PAD["xs"]))

        text_container = tk.Frame(self.jd_text_frame, bg=COLORS["bg_surface"])
        text_container.pack(fill="both", expand=True)

        self.jd_textbox = tk.Text(
            text_container,
            font=FONTS["mono_small"],
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["accent"],
            relief="flat",
            wrap="word",
            padx=8, pady=8,
            undo=True,
        )
        jd_scroll = ttk.Scrollbar(text_container, command=self.jd_textbox.yview)
        self.jd_textbox.configure(yscrollcommand=jd_scroll.set)
        jd_scroll.pack(side="right", fill="y")
        self.jd_textbox.pack(fill="both", expand=True)

        # PDF upload alternative (hidden by default)
        self.jd_pdf_frame = tk.Frame(card, bg=COLORS["bg_secondary"])

        tk.Label(
            self.jd_pdf_frame,
            text="Upload job description as PDF:",
            font=FONTS["small"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, PAD["xs"]))

        self.jd_pdf_status = tk.Label(
            self.jd_pdf_frame, text="No file selected",
            font=FONTS["small"], bg=COLORS["bg_secondary"],
            fg=COLORS["text_muted"],
        )
        self.jd_pdf_status.pack(anchor="w")

        ttk.Button(
            self.jd_pdf_frame, text="Browse PDF…", style="Ghost.TButton",
            command=self._browse_jd_pdf,
        ).pack(anchor="w", pady=(PAD["xs"], 0))

        # Show text tab by default
        self._set_jd_tab("text")

    # ── Interactions ────────────────────────────────────────────────────────

    def _set_jd_tab(self, tab: str):
        self._jd_tab = tab
        if tab == "text":
            self.jd_pdf_frame.pack_forget()
            self.jd_text_frame.pack(fill="both", expand=True)
            self.jd_paste_btn.configure(
                bg=COLORS["accent"], fg=COLORS["text_on_accent"])
            self.jd_pdf_btn.configure(
                bg=COLORS["bg_surface"], fg=COLORS["text_secondary"])
        else:
            self.jd_text_frame.pack_forget()
            self.jd_pdf_frame.pack(fill="both", expand=True)
            self.jd_pdf_btn.configure(
                bg=COLORS["accent"], fg=COLORS["text_on_accent"])
            self.jd_paste_btn.configure(
                bg=COLORS["bg_surface"], fg=COLORS["text_secondary"])

    def _browse_cv(self):
        path = filedialog.askopenfilename(
            title="Select your CV",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            self._cv_path = path
            filename = Path(path).name
            self.cv_status.configure(
                text=f"✓  {filename}",
                fg=COLORS["success"],
            )
            self.cv_icon_label.configure(
                text="✅", fg=COLORS["success"]
            )

    def _browse_jd_pdf(self):
        path = filedialog.askopenfilename(
            title="Select Job Description PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            try:
                from core.pdf_parser import extract_text_from_pdf
                text, _ = extract_text_from_pdf(path)
                self._jd_from_pdf = text
                filename = Path(path).name
                self.jd_pdf_status.configure(
                    text=f"✓  {filename}",
                    fg=COLORS["success"],
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not read PDF:\n{e}", parent=self)

    def _on_continue(self):
        """Validate inputs and advance to step 2."""
        # CV validation
        if not self._cv_path:
            messagebox.showwarning("Missing CV", "Please upload your CV (PDF).", parent=self)
            return

        # JD validation
        if getattr(self, "_jd_tab", "text") == "text":
            jd_text = self.jd_textbox.get("1.0", "end").strip()
        else:
            jd_text = getattr(self, "_jd_from_pdf", "").strip()

        if not jd_text or len(jd_text) < 50:
            messagebox.showwarning(
                "Missing Job Description",
                "Please provide a job description (at least 50 characters).",
                parent=self
            )
            return

        # Store in app state
        self.app.set_cv_path(self._cv_path)
        self.app.set_jd_text(jd_text)
        self.app.next_step()