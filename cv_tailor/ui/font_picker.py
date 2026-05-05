"""
Font Picker Dialog — shown when embedded fonts in the original CV PDF
cannot be extracted, offering the user a choice of available alternatives.

Shows:
  - Which fonts from the original PDF failed
  - A searchable list of system fonts grouped by category
  - A preview of the selected font name
  - Confirm / Cancel buttons
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, TYPE_CHECKING

from ui.styles import COLORS, FONTS, PAD

if TYPE_CHECKING:
    from ui.app import CVTailorApp


class FontPickerDialog(tk.Toplevel):
    """
    Modal dialog that lets the user choose a replacement font.
    Sets self.chosen_font to the selected font dict on confirm, or None on cancel.
    """

    def __init__(self, parent: tk.Widget, app: "CVTailorApp",
                 failed_fonts: List[str],
                 embedded_fonts: List[str],
                 available_fonts: List[Dict]):
        super().__init__(parent)
        self.app = app
        self.failed_fonts = failed_fonts
        self.embedded_fonts = embedded_fonts
        self.available_fonts = available_fonts   # [{name, alias, category, path}]
        self.chosen_font: Optional[Dict] = None

        self._filtered: List[Dict] = list(available_fonts)
        self._selected_index: Optional[int] = None

        # ── Window setup ───────────────────────────────────────────────────
        self.title(self._t("fontpicker.title"))
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(False, False)
        self.grab_set()          # modal
        self.focus_set()

        self._build_ui()
        self._center_on_parent(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _t(self, key: str, **kw) -> str:
        return self.app.t(key, **kw)

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Warning banner ─────────────────────────────────────────────────
        banner = tk.Frame(self, bg=COLORS["bg_surface"],
                          padx=PAD["md"], pady=PAD["sm"])
        banner.pack(fill="x")

        tk.Label(
            banner,
            text="⚠  " + self._t("fontpicker.warn.title"),
            font=FONTS["subheading"],
            bg=COLORS["bg_surface"], fg=COLORS["warning"],
        ).pack(anchor="w")

        failed_str = ", ".join(self.failed_fonts[:6]) or "—"
        tk.Label(
            banner,
            text=self._t("fontpicker.warn.body", fonts=failed_str),
            font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
            wraplength=520, justify="left",
        ).pack(anchor="w", pady=(4, 0))

        if self.embedded_fonts:
            tk.Label(
                banner,
                text=self._t("fontpicker.warn.ok_fonts",
                              fonts=", ".join(self.embedded_fonts[:4])),
                font=FONTS["small"],
                bg=COLORS["bg_surface"], fg=COLORS["success"],
                wraplength=520, justify="left",
            ).pack(anchor="w", pady=(2, 0))

        # ── Search bar ─────────────────────────────────────────────────────
        search_row = tk.Frame(self, bg=COLORS["bg_primary"],
                              padx=PAD["md"], pady=PAD["sm"])
        search_row.pack(fill="x")

        tk.Label(
            search_row,
            text=self._t("fontpicker.search_label"),
            font=FONTS["small_bold"],
            bg=COLORS["bg_primary"], fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, PAD["xs"]))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_list())
        search_entry = ttk.Entry(
            search_row,
            textvariable=self._search_var,
            font=FONTS["body"],
            width=34,
        )
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.focus_set()

        # Category filter
        self._cat_var = tk.StringVar(value="All")
        for cat in ("All", "Sans-serif", "Serif", "Monospace"):
            tk.Radiobutton(
                search_row,
                text=cat,
                variable=self._cat_var,
                value=cat,
                command=self._filter_list,
                bg=COLORS["bg_primary"], fg=COLORS["text_secondary"],
                selectcolor=COLORS["bg_surface"],
                activebackground=COLORS["bg_primary"],
                font=FONTS["small"],
                relief="flat",
            ).pack(side="left", padx=(PAD["xs"], 0))

        # ── Font list ──────────────────────────────────────────────────────
        list_frame = tk.Frame(self, bg=COLORS["bg_primary"],
                              padx=PAD["md"])
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            font=FONTS["body"],
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            selectbackground=COLORS["accent"],
            selectforeground=COLORS["text_on_accent"],
            activestyle="none",
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=COLORS["border"],
            height=14,
            width=54,
        )
        list_scroll = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=list_scroll.set)
        list_scroll.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self._on_confirm())

        # ── Preview strip ──────────────────────────────────────────────────
        preview_frame = tk.Frame(self, bg=COLORS["bg_surface"],
                                  padx=PAD["md"], pady=PAD["sm"])
        preview_frame.pack(fill="x", padx=PAD["md"], pady=(PAD["xs"], 0))

        tk.Label(
            preview_frame,
            text=self._t("fontpicker.preview_label"),
            font=FONTS["small_bold"],
            bg=COLORS["bg_surface"], fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        self._preview_label = tk.Label(
            preview_frame,
            text=self._t("fontpicker.preview_placeholder"),
            font=FONTS["body"],
            bg=COLORS["bg_surface"], fg=COLORS["text_muted"],
            anchor="w",
        )
        self._preview_label.pack(fill="x")

        self._selected_name_label = tk.Label(
            preview_frame,
            text="",
            font=FONTS["small"],
            bg=COLORS["bg_surface"], fg=COLORS["accent_light"],
        )
        self._selected_name_label.pack(anchor="w")

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=COLORS["bg_primary"],
                            padx=PAD["md"], pady=PAD["md"])
        btn_row.pack(fill="x")

        ttk.Button(
            btn_row,
            text=self._t("fontpicker.btn.cancel"),
            style="Ghost.TButton",
            command=self._on_cancel,
        ).pack(side="left")

        self._confirm_btn = ttk.Button(
            btn_row,
            text=self._t("fontpicker.btn.confirm"),
            style="TButton",
            command=self._on_confirm,
            state="disabled",
        )
        self._confirm_btn.pack(side="right")

        # Count label
        self._count_label = tk.Label(
            btn_row, text="",
            font=FONTS["small"],
            bg=COLORS["bg_primary"], fg=COLORS["text_muted"],
        )
        self._count_label.pack(side="right", padx=PAD["sm"])

        # Initial population
        self._filter_list()

    # ── List management ────────────────────────────────────────────────────

    def _filter_list(self):
        """Re-filter listbox based on search text and category."""
        query = self._search_var.get().strip().lower()
        cat   = self._cat_var.get()

        self._filtered = [
            f for f in self.available_fonts
            if (not query or query in f["name"].lower())
            and (cat == "All" or f["category"] == cat)
        ]

        self.listbox.delete(0, "end")
        prev_cat = None
        for entry in self._filtered:
            # Category separator
            if entry["category"] != prev_cat:
                self.listbox.insert("end", f"── {entry['category']} ──")
                self.listbox.itemconfig("end",
                                        fg=COLORS["text_muted"],
                                        selectbackground=COLORS["bg_surface"],
                                        selectforeground=COLORS["text_muted"])
                prev_cat = entry["category"]
            self.listbox.insert("end", f"  {entry['name']}")

        self._count_label.configure(
            text=f"{len(self._filtered)} {self._t('fontpicker.fonts_found')}"
        )
        self._selected_index = None
        self._confirm_btn.configure(state="disabled")

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        raw = self.listbox.get(sel[0])
        if raw.startswith("──"):
            # Separator row — skip
            self._confirm_btn.configure(state="disabled")
            return

        name = raw.strip()
        match = next((f for f in self._filtered if f["name"] == name), None)
        if not match:
            return

        self._selected_index = sel[0]
        self.chosen_font = match

        # Update preview
        self._preview_label.configure(
            text=self._t("fontpicker.preview_text"),
            fg=COLORS["text_primary"],
        )
        src = self._t("fontpicker.source_system") if match["path"] \
              else self._t("fontpicker.source_builtin")
        self._selected_name_label.configure(
            text=f"{match['name']}  ·  {match['category']}  ·  {src}"
        )
        self._confirm_btn.configure(state="normal")

    # ── Actions ────────────────────────────────────────────────────────────

    def _on_confirm(self):
        if self.chosen_font:
            self.destroy()

    def _on_cancel(self):
        self.chosen_font = None
        self.destroy()

    # ── Utilities ──────────────────────────────────────────────────────────

    def _center_on_parent(self, parent: tk.Widget):
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()  // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{pw - w//2}+{ph - h//2}")


def ask_font(parent: tk.Widget, app: "CVTailorApp",
             failed_fonts: List[str],
             embedded_fonts: List[str],
             available_fonts: List[Dict]) -> Optional[Dict]:
    """
    Show the font picker dialog and return the chosen font dict,
    or None if the user cancelled.
    """
    dlg = FontPickerDialog(parent, app, failed_fonts, embedded_fonts,
                           available_fonts)
    parent.wait_window(dlg)
    return dlg.chosen_font