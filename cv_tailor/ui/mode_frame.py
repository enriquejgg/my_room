"""Mode Frame — Step 2, fully i18n."""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import TYPE_CHECKING
from ui.styles import COLORS, FONTS, PAD
from core.models import ProcessingMode
if TYPE_CHECKING:
    from ui.app import CVTailorApp


class ModeFrame(tk.Frame):
    def __init__(self, parent, app: "CVTailorApp"):
        super().__init__(parent, bg=COLORS["bg_primary"])
        self.app = app
        self._selected_mode = ProcessingMode.STANDARD
        self._api_key_var = tk.StringVar()
        self._resolved_api_key = ""
        self._build_ui()

    def _t(self, key, **kw): return self.app.t(key, **kw)

    def on_enter(self):
        self._check_ai_availability()

    def _check_ai_availability(self):
        env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if env_key:
            self._api_key_var.set(env_key)
            if hasattr(self, "api_key_source_label"):
                self.api_key_source_label.configure(
                    text=self._t("mode.api.loaded"), fg=COLORS["success"])
        else:
            if hasattr(self, "api_key_source_label"):
                self.api_key_source_label.configure(
                    text=self._t("mode.api.not_loaded"), fg=COLORS["warning"])

    def _build_ui(self):
        outer = tk.Frame(self, bg=COLORS["bg_primary"])
        outer.pack(fill="both", expand=True, padx=40, pady=20)

        tk.Label(outer, text=self._t("mode.title"), font=FONTS["title"],
                 bg=COLORS["bg_primary"], fg=COLORS["text_primary"]).pack(pady=(0, 4))
        tk.Label(outer, text=self._t("mode.subtitle"), font=FONTS["body"],
                 bg=COLORS["bg_primary"], fg=COLORS["text_secondary"]).pack(pady=(0, PAD["xl"]))

        cards_row = tk.Frame(outer, bg=COLORS["bg_primary"])
        cards_row.pack(fill="x")
        cards_row.columnconfigure(0, weight=1, uniform="mode")
        cards_row.columnconfigure(1, weight=1, uniform="mode")
        self._build_standard_card(cards_row)
        self._build_ai_card(cards_row)

        # API key panel (hidden until AI mode selected)
        self.api_key_frame = tk.Frame(outer, bg=COLORS["bg_secondary"],
                                      padx=PAD["md"], pady=PAD["md"])

        tk.Label(self.api_key_frame, text=self._t("mode.api.heading"),
                 font=FONTS["subheading"], bg=COLORS["bg_secondary"],
                 fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, PAD["xs"]))
        tk.Label(self.api_key_frame, text=self._t("mode.api.hint"),
                 font=FONTS["small"], bg=COLORS["bg_secondary"],
                 fg=COLORS["text_secondary"], justify="left").pack(anchor="w", pady=(0, PAD["sm"]))

        key_row = tk.Frame(self.api_key_frame, bg=COLORS["bg_secondary"])
        key_row.pack(fill="x")
        self.api_key_entry = ttk.Entry(key_row, textvariable=self._api_key_var,
                                       show="•", font=FONTS["mono"], width=52)
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, PAD["xs"]))
        tk.Button(key_row, text="👁", relief="flat", bg=COLORS["bg_surface"],
                  fg=COLORS["text_secondary"], font=FONTS["body"], cursor="hand2",
                  command=self._toggle_key_visibility).pack(side="left")

        self.api_key_source_label = tk.Label(self.api_key_frame, text="",
                                             font=FONTS["small_bold"],
                                             bg=COLORS["bg_secondary"], fg=COLORS["text_muted"])
        self.api_key_source_label.pack(anchor="w", pady=(4, 0))

        pii_frame = tk.Frame(self.api_key_frame, bg=COLORS["bg_surface"], padx=10, pady=8)
        pii_frame.pack(fill="x", pady=(PAD["sm"], 0))
        tk.Label(pii_frame, text=self._t("mode.pii.notice"), font=FONTS["small"],
                 bg=COLORS["bg_surface"], fg=COLORS["info"], justify="left").pack(anchor="w")

        # Status area
        self.status_frame = tk.Frame(outer, bg=COLORS["bg_primary"])
        self.status_frame.pack(fill="x", pady=(PAD["lg"], 0))
        self.status_label = tk.Label(self.status_frame, text="", font=FONTS["body"],
                                     bg=COLORS["bg_primary"], fg=COLORS["text_secondary"])
        self.status_label.pack()
        self.progress_bar = ttk.Progressbar(self.status_frame, mode="indeterminate", length=400)

        # Navigation
        nav = tk.Frame(outer, bg=COLORS["bg_primary"])
        nav.pack(fill="x", pady=(PAD["md"], 0))
        ttk.Button(nav, text=self._t("mode.btn.back"), style="Ghost.TButton",
                   command=self.app.prev_step).pack(side="left")
        self.analyse_btn = ttk.Button(nav, text=self._t("mode.btn.analyse"),
                                      style="TButton", command=self._start_analysis)
        self.analyse_btn.pack(side="right")

    def _build_standard_card(self, parent):
        self.std_card = tk.Frame(parent, bg=COLORS["bg_secondary"],
                                 highlightthickness=2, highlightbackground=COLORS["accent"],
                                 padx=PAD["md"], pady=PAD["md"], cursor="hand2")
        self.std_card.grid(row=0, column=0, sticky="nsew", padx=(0, PAD["sm"]), pady=(0, PAD["sm"]))
        self.std_card.bind("<Button-1>", lambda e: self._select_mode(ProcessingMode.STANDARD))

        tk.Label(self.std_card, text=self._t("mode.std.heading"), font=FONTS["heading"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, PAD["xs"]))

        for key in ["mode.std.f1", "mode.std.f2", "mode.std.f3", "mode.std.f4", "mode.std.f5"]:
            tk.Label(self.std_card, text=self._t(key), font=FONTS["small"],
                     bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                     justify="left").pack(anchor="w", pady=1)

        self.std_selected = tk.Label(self.std_card, text=self._t("mode.selected"),
                                     font=FONTS["small_bold"],
                                     bg=COLORS["bg_secondary"], fg=COLORS["accent_light"])
        self.std_selected.pack(anchor="e", pady=(PAD["sm"], 0))

    def _build_ai_card(self, parent):
        self.ai_card = tk.Frame(parent, bg=COLORS["bg_secondary"],
                                highlightthickness=2, highlightbackground=COLORS["border"],
                                padx=PAD["md"], pady=PAD["md"], cursor="hand2")
        self.ai_card.grid(row=0, column=1, sticky="nsew", padx=(PAD["sm"], 0), pady=(0, PAD["sm"]))
        self.ai_card.bind("<Button-1>", lambda e: self._select_mode(ProcessingMode.AI_ASSISTED))

        tk.Label(self.ai_card, text=self._t("mode.ai.heading"), font=FONTS["heading"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, PAD["xs"]))

        for key in ["mode.ai.f1", "mode.ai.f2", "mode.ai.f3", "mode.ai.f4", "mode.ai.f5"]:
            text = self._t(key)
            color = COLORS["warning"] if text.startswith("⚠") else COLORS["text_secondary"]
            tk.Label(self.ai_card, text=text, font=FONTS["small"],
                     bg=COLORS["bg_secondary"], fg=color, justify="left").pack(anchor="w", pady=1)

        self.ai_selected = tk.Label(self.ai_card, text="", font=FONTS["small_bold"],
                                    bg=COLORS["bg_secondary"], fg=COLORS["accent_light"])
        self.ai_selected.pack(anchor="e", pady=(PAD["sm"], 0))

    def _select_mode(self, mode):
        self._selected_mode = mode
        if mode == ProcessingMode.STANDARD:
            self.std_card.configure(highlightbackground=COLORS["accent"])
            self.ai_card.configure(highlightbackground=COLORS["border"])
            self.std_selected.configure(text=self._t("mode.selected"))
            self.ai_selected.configure(text="")
            self.api_key_frame.pack_forget()
        else:
            self.ai_card.configure(highlightbackground=COLORS["accent"])
            self.std_card.configure(highlightbackground=COLORS["border"])
            self.ai_selected.configure(text=self._t("mode.selected"))
            self.std_selected.configure(text="")
            self.api_key_frame.pack(fill="x", pady=(PAD["lg"], 0))
            self._check_ai_availability()

    def _toggle_key_visibility(self):
        show = self.api_key_entry.cget("show")
        self.api_key_entry.configure(show="" if show else "•")

    def _set_status(self, msg, color=None):
        self.status_label.configure(text=msg, fg=color or COLORS["text_secondary"])

    def _start_analysis(self):
        self._resolved_api_key = ""
        if self._selected_mode == ProcessingMode.AI_ASSISTED:
            key = self._api_key_var.get().strip() or os.environ.get("ANTHROPIC_API_KEY", "").strip()
            if not key:
                messagebox.showwarning(self._t("mode.warn.title_key"),
                                       self._t("mode.warn.no_key"), parent=self)
                return
            if not key.startswith("sk-ant-"):
                messagebox.showwarning(self._t("mode.warn.title_fmt"),
                                       self._t("mode.warn.bad_key_fmt"), parent=self)
                return
            self._resolved_api_key = key

        self.app.set_mode(self._selected_mode)
        self.analyse_btn.configure(state="disabled")
        self.progress_bar.pack(pady=(PAD["xs"], 0))
        self.progress_bar.start(12)
        self._set_status(self._t("mode.status.extracting"), COLORS["info"])
        threading.Thread(target=self._run_analysis, daemon=True).start()

    def _run_analysis(self):
        try:
            from core.pdf_parser import extract_text_from_pdf, parse_cv_sections
            from core.analyzer import analyse_cv_vs_jd
            from core.suggestion_engine import generate_suggestions

            self.after(0, lambda: self._set_status(self._t("mode.status.extracting")))
            cv_text, _ = extract_text_from_pdf(self.app.cv_path)
            cv_sections = parse_cv_sections(cv_text)
            jd_text = self.app.jd_text

            if self._selected_mode == ProcessingMode.AI_ASSISTED:
                self.after(0, lambda: self._set_status(self._t("mode.status.masking"), COLORS["warning"]))
                from core.pii_masker import mask_text
                masked_cv, masker = mask_text(cv_text)

                self.after(0, lambda: self._set_status(self._t("mode.status.sending"), COLORS["info"]))
                from ai.ai_client import AIClient
                client = AIClient(api_key=self._resolved_api_key)
                result = client.analyse(masked_cv, jd_text, masker, cv_sections,
                                        locale=self.app.locale)
            else:
                self.after(0, lambda: self._set_status(self._t("mode.status.analysing"), COLORS["info"]))
                result = analyse_cv_vs_jd(cv_sections, jd_text)
                generate_suggestions(result, jd_text, locale=self.app.locale)

            self.after(0, lambda: self._on_analysis_complete(result))
        except Exception as exc:
            error_msg = str(exc)
            self.after(0, lambda: self._on_analysis_error(error_msg))

    def _on_analysis_complete(self, result):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.analyse_btn.configure(state="normal")
        n = len(result.suggestions)
        s = "s" if n != 1 else ""
        self._set_status(self._t("mode.status.done", n=n, s=s), COLORS["success"])
        self.app.set_analysis_result(result)
        self.app.next_step()

    def _on_analysis_error(self, error_msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.analyse_btn.configure(state="normal")
        self._set_status(self._t("mode.status.failed"), COLORS["danger"])
        if "401" in error_msg or "authentication_error" in error_msg or "invalid x-api-key" in error_msg:
            display = self._t("mode.err.401", err=error_msg)
        else:
            display = error_msg
        messagebox.showerror(self._t("mode.err.title"), display, parent=self)