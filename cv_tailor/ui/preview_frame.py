"""Preview Frame — Step 4: Preview updated CV and download as PDF. Fully i18n."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from typing import TYPE_CHECKING

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


class PreviewFrame(tk.Frame):
    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._build_ui()

    def _t(self, key, **kw): return self.app.t(key, **kw)

    def on_enter(self):
        self._render_preview()

    def _build_ui(self):
        self.stats_bar = tk.Frame(self, bg=COLORS["bg_secondary"],
                                  padx=PAD["md"], pady=PAD["sm"])
        self.stats_bar.pack(fill="x")

        self.heading_label = tk.Label(
            self.stats_bar, text=self._t("preview.heading"),
            font=FONTS["heading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"])
        self.heading_label.pack(side="left")

        self.stats_label = tk.Label(
            self.stats_bar, text="", font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.stats_label.pack(side="left", padx=PAD["md"])

        main = tk.Frame(self, bg=COLORS["bg_primary"])
        main.pack(fill="both", expand=True, padx=PAD["md"], pady=PAD["sm"])
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)

        self._build_preview_panel(main)
        self._build_summary_panel(main)
        self._build_nav()

    def _build_preview_panel(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg_secondary"],
                         padx=PAD["sm"], pady=PAD["sm"])
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, PAD["sm"]))

        self.preview_subheading = tk.Label(
            frame, text=self._t("preview.subheading"),
            font=FONTS["subheading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"])
        self.preview_subheading.pack(anchor="w", pady=(0, PAD["xs"]))

        self.preview_hint = tk.Label(
            frame, text=self._t("preview.changes_hint"),
            font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.preview_hint.pack(anchor="w", pady=(0, PAD["xs"]))

        text_container = tk.Frame(frame, bg=COLORS["bg_surface"])
        text_container.pack(fill="both", expand=True)

        self.preview_text = tk.Text(
            text_container, font=FONTS["mono_small"],
            bg=COLORS["bg_surface"], fg=COLORS["text_primary"],
            relief="flat", wrap="word", padx=10, pady=10,
            state="disabled", spacing3=2)
        self.preview_text.tag_configure(
            "changed", foreground=COLORS["success"],
            font=("Consolas", 9, "bold"))
        self.preview_text.tag_configure(
            "section_heading", foreground=COLORS["accent_light"],
            font=("Segoe UI", 10, "bold"))

        scroll = ttk.Scrollbar(text_container, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.preview_text.pack(fill="both", expand=True)

    def _build_summary_panel(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg_secondary"],
                         padx=PAD["sm"], pady=PAD["sm"])
        frame.grid(row=0, column=1, sticky="nsew")

        self.summary_title = tk.Label(
            frame, text=self._t("preview.summary"),
            font=FONTS["subheading"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"])
        self.summary_title.pack(anchor="w", pady=(0, PAD["sm"]))

        score_frame = tk.Frame(frame, bg=COLORS["bg_surface"],
                               padx=PAD["sm"], pady=PAD["sm"])
        score_frame.pack(fill="x", pady=(0, PAD["sm"]))

        self.score_label = tk.Label(
            score_frame, text="",
            font=("Segoe UI", 26, "bold"),
            bg=COLORS["bg_surface"], fg=COLORS["accent"])
        self.score_label.pack()

        self.match_score_label = tk.Label(
            score_frame, text=self._t("preview.match_score"),
            font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"])
        self.match_score_label.pack()

        self.accepted_label = tk.Label(
            frame, text="", font=FONTS["body_bold"],
            bg=COLORS["bg_secondary"], fg=COLORS["success"])
        self.accepted_label.pack(anchor="w", pady=(0, PAD["xs"]))

        self.analysis_text = tk.Text(
            frame, font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            relief="flat", wrap="word", padx=8, pady=8, height=12,
            state="disabled")
        self.analysis_text.pack(fill="both", expand=True, pady=(0, PAD["sm"]))

        self.missing_kw_label = tk.Label(
            frame, text=self._t("preview.missing_kw"),
            font=FONTS["small_bold"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.missing_kw_label.pack(anchor="w")

        self.keywords_text = tk.Text(
            frame, font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["warning"],
            relief="flat", wrap="word", padx=8, pady=6, height=5,
            state="disabled")
        self.keywords_text.pack(fill="x")

    def _build_nav(self):
        nav = tk.Frame(self, bg=COLORS["bg_secondary"],
                       padx=PAD["md"], pady=PAD["sm"])
        nav.pack(fill="x", side="bottom")

        self.back_btn = ttk.Button(
            nav, text=self._t("preview.btn.back"),
            style="Ghost.TButton", command=self.app.prev_step)
        self.back_btn.pack(side="left")

        self.download_btn = ttk.Button(
            nav, text=self._t("preview.btn.download"),
            style="TButton", command=self._download_pdf)
        self.download_btn.pack(side="right")

        self.status_label = tk.Label(
            nav, text="", font=FONTS["small"],
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
        self.status_label.pack(side="right", padx=PAD["sm"])

    def _render_preview(self):
        result = self.app.analysis_result
        if not result:
            return

        # Refresh all translatable labels in case language changed
        self.heading_label.configure(text=self._t("preview.heading"))
        self.preview_subheading.configure(text=self._t("preview.subheading"))
        self.preview_hint.configure(text=self._t("preview.changes_hint"))
        self.summary_title.configure(text=self._t("preview.summary"))
        self.match_score_label.configure(text=self._t("preview.match_score"))
        self.missing_kw_label.configure(text=self._t("preview.missing_kw"))
        self.back_btn.configure(text=self._t("preview.btn.back"))
        self.download_btn.configure(text=self._t("preview.btn.download"))

        accepted = result.accepted_count
        total = result.total_count
        self.score_label.configure(text=f"{result.match_score}%")
        self.accepted_label.configure(
            text=self._t("preview.accepted", accepted=accepted, total=total))
        self.stats_label.configure(
            text=self._t("preview.stats", score=result.match_score, accepted=accepted))

        replacements = {
            s.original_text: s.final_text
            for s in result.suggestions
            if s.status.value == "accepted"
        }

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        for section in result.cv_sections:
            if section.name.lower() != "header":
                self.preview_text.insert("end", f"\n{'─'*50}\n", "section_heading")
                self.preview_text.insert("end", f"{section.name.upper()}\n", "section_heading")
                self.preview_text.insert("end", f"{'─'*50}\n", "section_heading")
            text = section.raw_text
            last_end = 0
            for orig, repl in replacements.items():
                if orig in text:
                    start = text.find(orig)
                    self.preview_text.insert("end", text[last_end:start])
                    self.preview_text.insert("end", repl, "changed")
                    last_end = start + len(orig)
            self.preview_text.insert("end", text[last_end:] + "\n")
        self.preview_text.configure(state="disabled")

        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", result.summary or "")
        self.analysis_text.configure(state="disabled")

        self.keywords_text.configure(state="normal")
        self.keywords_text.delete("1.0", "end")
        if result.missing_keywords:
            self.keywords_text.insert("1.0", ", ".join(result.missing_keywords[:20]))
            self.keywords_text.configure(fg=COLORS["warning"])
        else:
            self.keywords_text.insert("1.0", self._t("preview.no_missing"))
            self.keywords_text.configure(fg=COLORS["success"])
        self.keywords_text.configure(state="disabled")

    def _download_pdf(self):
        result = self.app.analysis_result
        if not result:
            messagebox.showerror(self._t("preview.err.title"),
                                 self._t("preview.err.no_result"), parent=self)
            return

        output_path = filedialog.asksaveasfilename(
            title=self._t("preview.dl.save_title"),
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=self._t("preview.dl.filename"),
        )
        if not output_path:
            return

        source_pdf = getattr(self.app, "cv_path", None)

        # ── Font availability check ───────────────────────────────────────
        fallback_font = None
        if source_pdf:
            from core.pdf_generator import check_font_availability, discover_system_fonts
            font_check = check_font_availability(source_pdf)

            if not font_check["fonts_ok"]:
                # Discover available fonts on this machine
                available = discover_system_fonts()

                # Always include base-14 fonts at the top
                from core.pdf_generator import BASE14_FONTS
                all_fonts = BASE14_FONTS + [
                    f for f in available
                    if f["name"] not in {b["name"] for b in BASE14_FONTS}
                ]

                # Show picker dialog
                from ui.font_picker import ask_font
                chosen = ask_font(
                    parent=self,
                    app=self.app,
                    failed_fonts=font_check["failed_names"],
                    embedded_fonts=font_check["embedded_names"],
                    available_fonts=all_fonts,
                )
                if chosen is None:
                    # User cancelled — abort download
                    return
                fallback_font = chosen

        # ── Generate PDF ──────────────────────────────────────────────────
        self.download_btn.configure(state="disabled")
        self.status_label.configure(
            text=self._t("preview.status.gen"), fg=COLORS["info"]
        )
        threading.Thread(
            target=self._generate_pdf_thread,
            args=(result, output_path, source_pdf, fallback_font),
            daemon=True,
        ).start()

    def _generate_pdf_thread(self, result, output_path, source_pdf, fallback_font):
        try:
            if fallback_font:
                from core.pdf_generator import generate_final_pdf_with_fallback_font
                path = generate_final_pdf_with_fallback_font(
                    result.cv_sections,
                    result.suggestions,
                    output_path,
                    source_pdf_path=source_pdf,
                    fallback_font=fallback_font,
                )
            else:
                from core.pdf_generator import generate_final_pdf
                path = generate_final_pdf(
                    result.cv_sections,
                    result.suggestions,
                    output_path,
                    source_pdf_path=source_pdf,
                )
            self.after(0, lambda: self._on_pdf_done(path))
        except Exception as exc:
            error_msg = str(exc)
            self.after(0, lambda: self._on_pdf_error(error_msg))

    def _on_pdf_done(self, path):
        self.download_btn.configure(state="normal")
        self.status_label.configure(text="", fg=COLORS["text_secondary"])
        messagebox.showinfo(self._t("preview.dl.done.title"),
                            self._t("preview.dl.done.msg", path=path), parent=self)

    def _on_pdf_error(self, error_msg):
        self.download_btn.configure(state="normal")
        self.status_label.configure(text=self._t("preview.status.fail"), fg=COLORS["danger"])
        messagebox.showerror(self._t("preview.err.title"), error_msg, parent=self)