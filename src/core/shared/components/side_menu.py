import customtkinter as ctk
from PIL import Image
try:
    from src.core.shared.utils import resource_path
except ImportError:
    def resource_path(path): return path

# Reutilizando a paleta de cores identificada no sistema
COLOR_PRIMARY = "#0F8C75"       # Verde Principal
COLOR_PRIMARY_HOVER = "#0B6B59" 
COLOR_TEXT_LIGHT = "#FFFFFF"
COLOR_BG_MENU = "#242424"       # Tom escuro para o menu lateral

class SideMenu(ctk.CTkFrame):
    def __init__(self, master, user_data, on_menu_click, **kwargs):
        super().__init__(master, corner_radius=0, fg_color=COLOR_BG_MENU, **kwargs)
        
        self.user_data = user_data
        self.on_menu_click = on_menu_click
        self.buttons = {}

        # MODIFICAÇÃO: O espaçador agora está na linha 6 para dar lugar ao novo módulo
        self.grid_rowconfigure(6, weight=1) 

        # --- LOGO / TÍTULO ---
        try:
            img_path = resource_path("assets/sgi_logo.png")
            pil_img = Image.open(img_path)
            self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(40, 40))
            self.lbl_logo = ctk.CTkLabel(self, text=" SGI - DIPLA", image=self.logo_img, compound="left", 
                                        font=("Century Gothic bold", 20), text_color=COLOR_PRIMARY)
        except:
            self.lbl_logo = ctk.CTkLabel(self, text="SGI - DIPLA", font=("Century Gothic bold", 24), text_color=COLOR_PRIMARY)
        
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=30)

        # --- INFO USUÁRIO ---
        nome_user = self.user_data.get("nome", "Usuário")
        self.lbl_user = ctk.CTkLabel(self, text=f"Olá, {nome_user.split()[0]}", 
                                    font=("Arial", 13, "bold"), text_color="#A0A0A0")
        self.lbl_user.grid(row=1, column=0, padx=20, pady=(0, 20))

        # --- BOTÕES DE NAVEGAÇÃO PADRÃO ---
        self._criar_botao("Ponto de Parada", "PONTO_PARADA", 2)
        self._criar_botao("Itinerário", "ITINERARIO", 3)
        self._criar_botao("Quadro de Horário", "QUADRO_HORARIO", 4)
        
        # MODIFICAÇÃO: Inserção do novo módulo Projetos de Mobilidade
        self._criar_botao("Projetos de Mobilidade", "PROJETOS_MOBILIDADE", 5)

        # --- BOTÃO ADMIN (CONDICIONAL) ---
        if self.user_data.get("is_admin"):
            self._criar_botao("Módulo Admin", "ADMIN", 7, fg_color="#333333", hover_color="#444444")

        # --- BOTÃO SAIR ---
        self.btn_sair = ctk.CTkButton(self, text="Sair do Sistema", fg_color="transparent", 
                                     border_width=1, border_color="#555555",
                                     hover_color="#333333", font=("Arial Bold", 13),
                                     command=lambda: self.on_menu_click("SAIR"))
        self.btn_sair.grid(row=8, column=0, padx=20, pady=20, sticky="ew")

    def _criar_botao(self, text, key, row, **custom_style):
        """Helper para criar botões padronizados no menu."""
        style = {
            "fg_color": "transparent",
            "text_color": COLOR_TEXT_LIGHT,
            "hover_color": COLOR_PRIMARY_HOVER,
            "anchor": "w",
            "font": ("Arial Bold", 14),
            "height": 45,
            "corner_radius": 8
        }
        style.update(custom_style)

        btn = ctk.CTkButton(self, text=text, command=lambda: self.on_menu_click(key), **style)
        btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
        self.buttons[key] = btn
        return btn

    def set_active_button(self, key):
        """Destaca visualmente o botão clicado."""
        for k, btn in self.buttons.items():
            if k == key:
                btn.configure(fg_color=COLOR_PRIMARY)
            else:
                original_fg = "#333333" if k == "ADMIN" else "transparent"
                btn.configure(fg_color=original_fg)