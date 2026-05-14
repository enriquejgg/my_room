"""
Main Application Window — top-level Tk window and navigation controller.
Manages application state, step progression, language, and inter-frame communication.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from ui.styles import COLORS, FONTS, PAD, apply_theme
from core import i18n
from core.models import AnalysisResult, ProcessingMode


class CVTailorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CV Tailor — Smart CV Optimiser")
        self.geometry("1280x820")
        self.minsize(900, 650)
        self.resizable(True, True)

        apply_theme(self)

        self.cv_path: Optional[str] = None
        self.jd_text: str = ""
        self.processing_mode: ProcessingMode = ProcessingMode.STANDARD
        self.analysis_result: Optional[AnalysisResult] = None
        self.current_step: int = 1
        self.locale: str = "en"

        self._build_header()
        self._build_stepper()

        self.content_area = tk.Frame(self, bg=COLORS["bg_primary"])
        self.content_area.pack(fill="both", expand=True,
                               padx=PAD["lg"], pady=(0, PAD["md"]))

        self._init_frames()
        self._show_step(0)          # Start on the welcome screen

        self.update_idletasks()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Handle window close button cleanly."""
        try:
            self.destroy()
        except Exception:
            pass

    # ── Translation ─────────────────────────────────────────────────────────

    def t(self, key: str, **kwargs) -> str:
        return i18n.get(key, self.locale, **kwargs)

    # ── Frames ──────────────────────────────────────────────────────────────

    def _init_frames(self):
        from ui.welcome_frame import WelcomeFrame
        from ui.upload_frame import UploadFrame
        from ui.mode_frame import ModeFrame
        from ui.review_frame import ReviewFrame
        from ui.preview_frame import PreviewFrame

        self.frames = {
            0: WelcomeFrame(self.content_area, app=self),
            1: UploadFrame(self.content_area, app=self),
            2: ModeFrame(self.content_area, app=self),
            3: ReviewFrame(self.content_area, app=self),
            4: PreviewFrame(self.content_area, app=self),
        }

    def _rebuild_frames(self):
        for frame in self.frames.values():
            frame.destroy()
        self._init_frames()
        self._rebuild_stepper()
        self._show_step(self.current_step)

    # ── Header ──────────────────────────────────────────────────────────────

    def _build_header(self):
        self.header = tk.Frame(self, bg=COLORS["bg_secondary"], height=60)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        tk.Frame(self.header, bg=COLORS["accent"], width=8).pack(side="left", fill="y")

        # ── Home button ────────────────────────────────────────────────────
        self._home_btn = tk.Button(
            self.header,
            text=self.t("home.btn"),
            font=FONTS["small_bold"],
            bg=COLORS["bg_surface"],
            fg=COLORS["text_secondary"],
            activebackground=COLORS["bg_hover"],
            activeforeground=COLORS["text_primary"],
            relief="flat",
            padx=10, pady=6,
            cursor="hand2",
            command=self.go_home,
        )
        self._home_btn.pack(side="left", padx=(PAD["sm"], 0))

        self.header_title = tk.Label(
            self.header, text=self.t("app.title"),
            font=FONTS["title"], bg=COLORS["bg_secondary"], fg=COLORS["text_primary"],
        )
        self.header_title.pack(side="left", padx=PAD["md"])

        self.header_subtitle = tk.Label(
            self.header, text=self.t("app.subtitle"),
            font=FONTS["body"], bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
        )
        self.header_subtitle.pack(side="left")

        privacy_frame = tk.Frame(self.header, bg=COLORS["bg_surface"], padx=10, pady=4)
        privacy_frame.pack(side="right", padx=PAD["md"])
        self.privacy_label = tk.Label(
            privacy_frame, text=self.t("app.privacy_badge"),
            font=FONTS["small"], bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
        )
        self.privacy_label.pack()

        self._build_lang_picker()

    def _build_lang_picker(self):
        lang_frame = tk.Frame(self.header, bg=COLORS["bg_secondary"])
        lang_frame.pack(side="right", padx=(0, PAD["sm"]))

        tk.Label(lang_frame, text="🌐", font=FONTS["body"],
                 bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                 ).pack(side="left", padx=(0, 4))

        self._lang_options = {
            f"{meta['flag']} {meta['label']}": code
            for code, meta in i18n.LANGUAGES.items()
        }
        display_list = list(self._lang_options.keys())
        self._lang_var = tk.StringVar(value=display_list[0])

        lang_menu = ttk.Combobox(
            lang_frame, textvariable=self._lang_var,
            values=display_list, state="readonly", width=14, font=FONTS["small"],
        )
        lang_menu.pack(side="left")
        lang_menu.bind("<<ComboboxSelected>>", self._on_language_change)

    def _on_language_change(self, event=None):
        selected = self._lang_var.get()
        new_locale = self._lang_options.get(selected, "en")
        if new_locale == self.locale:
            return
        self.locale = new_locale
        self.header_title.configure(text=self.t("app.title"))
        self.header_subtitle.configure(text=self.t("app.subtitle"))
        self.privacy_label.configure(text=self.t("app.privacy_badge"))
        self._home_btn.configure(text=self.t("home.btn"))
        self._rebuild_frames()

    # ── Stepper ─────────────────────────────────────────────────────────────

    def _build_stepper(self):
        self.stepper_outer = tk.Frame(self, bg=COLORS["bg_secondary"], height=56)
        self.stepper_outer.pack(fill="x")
        self.stepper_outer.pack_propagate(False)
        self.stepper_inner = tk.Frame(self.stepper_outer, bg=COLORS["bg_secondary"])
        self.stepper_inner.pack(expand=True)
        self.step_labels = {}
        self._render_stepper_items()

    def _rebuild_stepper(self):
        for w in self.stepper_inner.winfo_children():
            w.destroy()
        self.step_labels.clear()
        self._render_stepper_items()
        self._update_stepper(self.current_step)

    def _render_stepper_items(self):
        steps = i18n.get_steps(self.locale)
        for i, (num, label) in enumerate(steps):
            if i > 0:
                tk.Frame(self.stepper_inner, bg=COLORS["border"],
                         height=2, width=40).pack(side="left", pady=22)
            container = tk.Frame(self.stepper_inner, bg=COLORS["bg_secondary"])
            container.pack(side="left", padx=4)
            circle = tk.Label(container, text=num, width=3,
                              font=FONTS["small_bold"],
                              bg=COLORS["bg_surface"], fg=COLORS["text_muted"])
            circle.pack(side="left")
            lbl = tk.Label(container, text=label,
                           font=FONTS["small_bold"],
                           bg=COLORS["bg_secondary"], fg=COLORS["text_muted"])
            lbl.pack(side="left", padx=(4, 0))
            self.step_labels[i + 1] = (circle, lbl)

    def _update_stepper(self, active_step: int):
        for step, (circle, lbl) in self.step_labels.items():
            if step == active_step:
                circle.configure(bg=COLORS["accent"], fg=COLORS["text_on_accent"])
                lbl.configure(fg=COLORS["text_primary"])
            elif step < active_step:
                circle.configure(bg=COLORS["success"], fg=COLORS["text_on_accent"])
                lbl.configure(fg=COLORS["text_secondary"])
            else:
                circle.configure(bg=COLORS["bg_surface"], fg=COLORS["text_muted"])
                lbl.configure(fg=COLORS["text_muted"])

    # ── Navigation ──────────────────────────────────────────────────────────

    def _show_step(self, step: int):
        self.current_step = step
        # Hide the progress stepper on the welcome screen
        if step == 0:
            self.stepper_outer.pack_forget()
        else:
            self.stepper_outer.pack(fill="x", after=self.header)
            self._update_stepper(step)
        for s, frame in self.frames.items():
            if s == step:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self.frames[step].on_enter()

    def go_home(self):
        """Return to the welcome screen, prompting if a session is active."""
        if self.current_step == 0:
            return
        if self.analysis_result is not None or self.cv_path:
            from tkinter import messagebox
            confirmed = messagebox.askyesno(
                self.t("home.confirm.title"),
                self.t("home.confirm.msg"),
                parent=self,
            )
            if not confirmed:
                return
        self._reset_session()
        self._show_step(0)

    def _reset_session(self):
        """Clear all session state so a fresh analysis can begin."""
        self.cv_path = None
        self.jd_text = ""
        self.processing_mode = ProcessingMode.STANDARD
        self.analysis_result = None
        # Re-initialise frames so upload/mode/review start clean
        for frame in self.frames.values():
            frame.destroy()
        self._init_frames()

    def go_to_step(self, step: int):
        self._show_step(step)

    def next_step(self):
        if self.current_step < 4:
            self.go_to_step(self.current_step + 1)

    def prev_step(self):
        if self.current_step > 1:
            self.go_to_step(self.current_step - 1)

    # ── State ───────────────────────────────────────────────────────────────

    def set_cv_path(self, path: str):
        self.cv_path = path
        print(f"[app] CV path set: {path}")
    def set_jd_text(self, text: str): self.jd_text = text
    def set_mode(self, mode: ProcessingMode): self.processing_mode = mode
    def set_analysis_result(self, result: AnalysisResult): self.analysis_result = result
    def show_error(self, title: str, message: str): messagebox.showerror(title, message, parent=self)
    def show_info(self, title: str, message: str): messagebox.showinfo(title, message, parent=self)