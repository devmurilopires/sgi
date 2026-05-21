import tkinter as tk
import customtkinter as ctk
from src.modulos.admin.parametros.service import ParametrosService


class CtkParametrosComboBox(ctk.CTkFrame):
    """
    Dropdown moderno com popup na largura exata do campo,
    navegação por setas do teclado, scroll interno e visual clean.
    Drop-in replacement do CTkComboBox original.
    """

    def __init__(
        self,
        master,
        setor=None,
        campo=None,
        values=None,
        incluir_todos=False,
        placeholder="– Selecione –",
        command=None,
        width=200,
        height=38,
        fg_color="#FFFFFF",
        border_color="#CCD9E8",
        text_color="#2D3748",
        font=("Segoe UI", 12),
        dropdown_fg_color="#FFFFFF",
        dropdown_text_color="#4A5568",
        dropdown_hover_color="#1982FC",
        dropdown_hover_text_color="#FFFFFF",
        dropdown_font=("Segoe UI", 10),
        max_visible_items=8,
        state="normal",
        **kwargs,
    ):
        # Limpa kwargs que não pertencem ao CTkFrame
        for k in (
            "button_color", "button_hover_color",
            "dropdown_fg_color", "dropdown_text_color",
            "dropdown_hover_color", "dropdown_font",
        ):
            kwargs.pop(k, None)

        super().__init__(
            master,
            fg_color=fg_color,
            border_color=border_color,
            border_width=1,
            corner_radius=6,
            width=width,
            height=height,
            **kwargs,
        )

        # ── configuração interna ──────────────────────────────────────
        self._cfg = dict(
            width=width,
            height=height,
            font=font,
            text_color=text_color,
            fg_color=fg_color,
            border_color=border_color,
            dropdown_fg_color=dropdown_fg_color,
            dropdown_text_color=dropdown_text_color,
            dropdown_hover_color=dropdown_hover_color,
            dropdown_hover_text_color=dropdown_hover_text_color,
            dropdown_font=dropdown_font,
            placeholder=placeholder,
            max_visible_items=max_visible_items,
        )
        self._command = command
        self._state = state
        self._combo_options: list[str] = []
        self._selected_index = -1
        self._popup: tk.Toplevel | None = None
        self._popup_open = False
        self._item_height = 36
        self._item_labels: list[tk.Label] = []
        self._popup_canvas: tk.Canvas | None = None

        # ── layout ───────────────────────────────────────────────────
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._label = ctk.CTkLabel(
            self,
            text=placeholder,
            font=font,
            text_color="#A0AEC0",
            anchor="w",
            cursor="hand2",
        )
        self._label.grid(row=0, column=0, sticky="ew", padx=(12, 0))

        self._arrow_lbl = ctk.CTkLabel(
            self,
            text="▼",
            font=("Segoe UI", 10),
            text_color="#718096",
            width=30,
            cursor="hand2",
        )
        self._arrow_lbl.grid(row=0, column=1, padx=(0, 8))

        # ── bindings ─────────────────────────────────────────────────
        for w in (self, self._label, self._arrow_lbl):
            w.bind("<Button-1>", self._toggle_popup)

        self.bind("<KeyPress>", self._on_keypress)
        self.bind("<FocusIn>", lambda _: self.configure(border_color="#1982FC"))
        self.bind(
            "<FocusOut>",
            lambda _: self.configure(border_color=self._cfg["border_color"]),
        )

        # ── dados ─────────────────────────────────────────────────────
        if setor and campo:
            self._service = ParametrosService()
            self._routing = self._service.obter_roteamento(setor, campo)
            self._incluir_todos = incluir_todos
            self.atualizar_opcoes()
            self.after(100, self._registrar_ouvinte)
        elif values:
            self._set_options(values)

    # ─────────────────────────────────────────────────────────────────
    # API pública (compatível com CTkComboBox)
    # ─────────────────────────────────────────────────────────────────

    def get(self) -> str:
        text = self._label.cget("text")
        return "" if text == self._cfg["placeholder"] else text

    def set(self, value: str) -> None:
        if value in self._combo_options:
            self._label.configure(text=value, text_color=self._cfg["text_color"])
        elif not value or value == self._cfg["placeholder"]:
            self._label.configure(
                text=self._cfg["placeholder"], text_color="#A0AEC0"
            )
        else:
            self._label.configure(text=value, text_color=self._cfg["text_color"])

    def configure(self, **kw) -> None:
        if "values" in kw:
            self._set_options(kw.pop("values"))
        if "state" in kw:
            self._state = kw.pop("state")
        if "command" in kw:
            self._command = kw.pop("command")
        if kw:
            super().configure(**kw)

    def cget(self, key: str):
        if key == "values":
            return self._combo_options
        return super().cget(key)

    # ─────────────────────────────────────────────────────────────────
    # Opções
    # ─────────────────────────────────────────────────────────────────

    def _set_options(self, options: list[str]) -> None:
        self._combo_options = list(options)

    # ─────────────────────────────────────────────────────────────────
    # Popup
    # ─────────────────────────────────────────────────────────────────

    def _toggle_popup(self, _event=None) -> None:
        if self._state == "disabled":
            return
        self.focus_set()
        if self._popup_open:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self) -> None:
        if self._popup_open or not self._combo_options:
            return

        self._popup_open = True
        self._arrow_lbl.configure(text="▲")

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)

        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        w = self.winfo_width()

        n_visible = min(len(self._combo_options), self._cfg["max_visible_items"])
        popup_h = n_visible * self._item_height + 4

        self._popup.geometry(f"{w}x{popup_h}+{x}+{y}")
        self._popup.configure(bg=self._cfg["border_color"])

        # borda via Frame externo
        outer = tk.Frame(
            self._popup,
            bg=self._cfg["dropdown_fg_color"],
            bd=0,
        )
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # Canvas + Scrollbar
        self._popup_canvas = tk.Canvas(
            outer,
            bg=self._cfg["dropdown_fg_color"],
            highlightthickness=0,
            bd=0,
        )
        sb = tk.Scrollbar(outer, orient="vertical", command=self._popup_canvas.yview)
        self._popup_canvas.configure(yscrollcommand=sb.set)

        # Scrollbar só aparece quando necessário
        if len(self._combo_options) > self._cfg["max_visible_items"]:
            sb.pack(side="right", fill="y")

        self._popup_canvas.pack(side="left", fill="both", expand=True)

        items_frame = tk.Frame(self._popup_canvas, bg=self._cfg["dropdown_fg_color"])
        win_id = self._popup_canvas.create_window((0, 0), window=items_frame, anchor="nw")

        self._item_labels = []
        current = self.get()

        for i, opt in enumerate(self._combo_options):
            selected = opt == current
            bg = "#EBF4FF" if selected else self._cfg["dropdown_fg_color"]
            fg = self._cfg["dropdown_hover_color"] if selected else self._cfg["dropdown_text_color"]

            lbl = tk.Label(
                items_frame,
                text=opt,
                font=self._cfg["dropdown_font"],
                bg=bg,
                fg=fg,
                anchor="w",
                padx=12,
                pady=8,
                cursor="hand2",
            )
            lbl.pack(fill="x")
            self._item_labels.append(lbl)

            lbl.bind("<Enter>", lambda e, l=lbl, idx=i: self._item_hover(l, idx, True))
            lbl.bind("<Leave>", lambda e, l=lbl, idx=i: self._item_hover(l, idx, False))
            lbl.bind("<Button-1>", lambda e, o=opt: self._select_option(o))

        # atualiza scrollregion após renderizar
        items_frame.update_idletasks()
        self._popup_canvas.configure(scrollregion=self._popup_canvas.bbox("all"))
        self._popup_canvas.itemconfigure(win_id, width=self._popup_canvas.winfo_width())
        self._popup_canvas.bind(
            "<Configure>",
            lambda e: self._popup_canvas.itemconfigure(win_id, width=e.width),
        )

        # scroll com mouse (Windows/macOS/Linux)
        for widget in (self._popup, self._popup_canvas, items_frame):
            widget.bind("<MouseWheel>", self._on_mousewheel)
            widget.bind("<Button-4>", lambda e: self._popup_canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: self._popup_canvas.yview_scroll(1, "units"))

        # scroll para item selecionado
        if current in self._combo_options:
            idx = self._combo_options.index(current)
            self._selected_index = idx
            total = len(self._combo_options)
            if total > self._cfg["max_visible_items"]:
                self._popup_canvas.yview_moveto(idx / total)
        else:
            self._selected_index = -1

        # fechar ao clicar fora
        self.winfo_toplevel().bind("<Button-1>", self._on_click_outside, add="+")

    def _close_popup(self) -> None:
        try:
            self.winfo_toplevel().unbind("<Button-1>")
        except Exception:
            pass
        if self._popup:
            self._popup.destroy()
            self._popup = None
        self._popup_open = False
        self._item_labels = []
        self._popup_canvas = None
        self._arrow_lbl.configure(text="▼")

    # ─────────────────────────────────────────────────────────────────
    # Interação com itens
    # ─────────────────────────────────────────────────────────────────

    def _item_hover(self, label: tk.Label, idx: int, entering: bool) -> None:
        current = self.get()
        selected = self._combo_options[idx] == current
        if entering:
            label.configure(
                bg=self._cfg["dropdown_hover_color"],
                fg=self._cfg["dropdown_hover_text_color"],
            )
            self._selected_index = idx
        else:
            label.configure(
                bg="#EBF4FF" if selected else self._cfg["dropdown_fg_color"],
                fg=self._cfg["dropdown_hover_color"] if selected else self._cfg["dropdown_text_color"],
            )

    def _select_option(self, option: str) -> None:
        self.set(option)
        self._close_popup()
        if self._command:
            self._command(option)

    def _on_mousewheel(self, event) -> None:
        if self._popup_canvas:
            self._popup_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_click_outside(self, event) -> None:
        try:
            w = str(event.widget)
            if self._popup and w.startswith(str(self._popup)):
                return
            if w.startswith(str(self)):
                return
        except Exception:
            pass
        self._close_popup()

    # ─────────────────────────────────────────────────────────────────
    # Teclado
    # ─────────────────────────────────────────────────────────────────

    def _on_keypress(self, event) -> None:
        key = event.keysym

        if not self._popup_open:
            if key in ("Return", "space", "Down", "Up"):
                self._open_popup()
            return

        if key == "Escape":
            self._close_popup()
        elif key == "Return":
            if 0 <= self._selected_index < len(self._combo_options):
                self._select_option(self._combo_options[self._selected_index])
        elif key == "Down":
            self._navigate(1)
        elif key == "Up":
            self._navigate(-1)

    def _navigate(self, direction: int) -> None:
        if not self._combo_options or not self._item_labels:
            return

        n = len(self._combo_options)
        prev = self._selected_index
        new = max(0, min(prev + direction, n - 1))

        # restaura cor do anterior
        if 0 <= prev < len(self._item_labels):
            selected = self._combo_options[prev] == self.get()
            self._item_labels[prev].configure(
                bg="#EBF4FF" if selected else self._cfg["dropdown_fg_color"],
                fg=self._cfg["dropdown_hover_color"] if selected else self._cfg["dropdown_text_color"],
            )

        # destaca novo
        self._selected_index = new
        self._item_labels[new].configure(
            bg=self._cfg["dropdown_hover_color"],
            fg=self._cfg["dropdown_hover_text_color"],
        )

        # scroll para manter visível
        if self._popup_canvas and n > self._cfg["max_visible_items"]:
            self._popup_canvas.yview_moveto(new / n)

    # ─────────────────────────────────────────────────────────────────
    # Integração com ParametrosService (lógica original mantida)
    # ─────────────────────────────────────────────────────────────────

    def _registrar_ouvinte(self) -> None:
        try:
            self.winfo_toplevel().bind(
                "<<ParametrosAtualizados>>", self._on_atualizacao, add="+"
            )
        except Exception as e:
            print(f"Aviso: Não foi possível registrar o ouvinte: {e}")

    def _on_atualizacao(self, _event=None) -> None:
        self.atualizar_opcoes()

    def atualizar_opcoes(self) -> None:
        try:
            valor_atual = self.get()
            dados = self._service.listar_parametros(self._routing)
            opcoes = [item["valor"] for item in dados]

            if not opcoes:
                opcoes = ["Nenhuma opção cadastrada"]

            if self._incluir_todos:
                opcoes.insert(0, "Todos")

            self._set_options(opcoes)

            self.set(valor_atual if valor_atual in opcoes else opcoes[0])

        except Exception as e:
            print(f"Erro ao carregar opções: {e}")
            self._set_options(["Erro ao carregar"])
            self.set("Erro ao carregar")