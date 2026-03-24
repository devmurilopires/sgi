import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import webbrowser
from src.auth.service import AuthService

try:
    from src.shared.utils import resource_path
except ImportError:
    def resource_path(path): return path

# --- PALETA DE CORES DA ETUFOR ---
COLOR_PRIMARY = "#0F8C75"       # Verde Principal
COLOR_PRIMARY_HOVER = "#0B6B59" 
COLOR_SECONDARY = "#F24822"     # Laranja/Vermelho
COLOR_TERTIARY = "#14A1D9"      # Azul
COLOR_BG_RIGHT = "#FFFFFF"      # Fundo Branco para o lado direito (Sem card, fundo direto)
COLOR_TEXT = "#333333"          # Texto Escuro
COLOR_PLACEHOLDER = "#8A8A8A"   # Texto de Dica

class LoginView(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.auth = AuthService()
        self.on_login_success = on_login_success
        self.active_frame = None

        # --- CONFIGURAÇÃO DA JANELA ---
        self.title("SIGP - Sistema Integrado de Gerenciamento e Produtividade")
        self.configure(fg_color=COLOR_BG_RIGHT)
        
        # Garante Tela Cheia / Maximizada logo ao abrir
        try:
            self.after(0, lambda: self.state("zoomed")) 
            self.iconbitmap(resource_path("assets/sigp_logo.ico"))
        except:
            self.geometry("1366x768")

        # --- LAYOUT RESPONSIVO (60% / 40%) GRUDADO ---
        self.grid_columnconfigure(0, weight=6) # Esquerda (60%)
        self.grid_columnconfigure(1, weight=4) # Direita (40%)
        self.grid_rowconfigure(0, weight=1)

        # 1. PAINEL ESQUERDO (Imagem - 60%)
        self.left_panel = ctk.CTkFrame(self, fg_color="#F2F2F2", corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=1) 
        self.left_panel.grid_columnconfigure(0, weight=1)

        try:
            # Carrega a Logo Maior
            img_path = resource_path("assets/sigp_logo.png")
            pil_img = Image.open(img_path)
            # Aumentando a imagem para preencher bem os 60%
            self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(600, 600))
            ctk.CTkLabel(self.left_panel, text="", image=self.logo_img).grid(row=0, column=0)
        except Exception as e:
            print(f"Aviso - Imagem não encontrada: {e}")
            ctk.CTkLabel(self.left_panel, text="SIGP", font=("Arial Black", 80), text_color="white").grid(row=0, column=0)

        # 2. PAINEL DIREITO (Formulários - 40%)
        self.right_panel = ctk.CTkFrame(self, fg_color=COLOR_BG_RIGHT, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Configuração para o rodapé ficar fixo embaixo
        self.right_panel.grid_rowconfigure(0, weight=1) # Espaço do formulário
        self.right_panel.grid_rowconfigure(1, weight=0) # Espaço do rodapé
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Constrói o Rodapé
        self._construir_rodape()

        # Verifica sessão
        sessao = self.auth.ler_sessao()
        if sessao:
            self.on_login_success(sessao)
            return

        self.mostrar_login()

    def _construir_rodape(self):
            """Rodapé fixo na parte inferior com elementos centralizados."""
            footer_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
            footer_frame.grid(row=1, column=0, pady=20)

            # LinkedIn na Esquerda do centro
            btn_linkedin = ctk.CTkButton(
                footer_frame, 
                text="in", 
                font=("Arial Black", 16),
                width=35, height=35, 
                corner_radius=8,
                fg_color="#0A66C2", 
                hover_color="#004182",
                command=lambda: webbrowser.open("https://www.linkedin.com/in/murilo-pires-713275257/")
            )
            # pack(side="left") coloca ele e já permite o próximo item ficar do lado
            btn_linkedin.pack(side="left", padx=(0, 8)) 

            # Copyright na Direita do botão
            ctk.CTkLabel(
                footer_frame, 
                text="© 2026 devmurilopires", 
                font=("Arial", 14, "bold"), 
                text_color="#A0A0A0"
            ).pack(side="left")

    def _resetar_frame_ativo(self):
        """Cria o container centralizado perfeitamente no meio do painel direito."""
        if self.active_frame:
            self.active_frame.destroy()
        
        # Frame transparente ancorado no centro
        self.active_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.active_frame.place(relx=0.5, rely=0.5, anchor="center")

    def _criar_campo_senha(self, parent, placeholder):
        """Método auxiliar para criar campos de senha com o olho mágico embutido."""
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, width=380, height=50, show="*", font=("Arial", 14), corner_radius=8, border_width=2, border_color=COLOR_PRIMARY)
        entry.pack(pady=7)
        
        # O Ícone agora é maior: font=("Arial", 20)
        btn_eye = ctk.CTkButton(
            entry, text="👁️", width=35, height=35, 
            fg_color="transparent", text_color="#666666", 
            font=("Arial", 18), hover=False
        )
        btn_eye.place(relx=0.96, rely=0.5, anchor="e")

        def toggle():
            if entry.cget("show") == "*":
                entry.configure(show="")
                btn_eye.configure(text="🔒")
            else:
                entry.configure(show="*")
                btn_eye.configure(text="👁️")
                
        btn_eye.configure(command=toggle)
        return entry

    # TELA DE LOGIN
    def mostrar_login(self):
        self._resetar_frame_ativo()

        ctk.CTkLabel(self.active_frame, text="BEM-VINDO", font=("Century Gothic bold", 36), text_color=COLOR_PRIMARY).pack(pady=(0, 5))
        ctk.CTkLabel(self.active_frame, text="Por favor, faça login na sua conta.", font=("Arial", 15), text_color=COLOR_PLACEHOLDER).pack(pady=(0, 35))

        self.entry_user = ctk.CTkEntry(self.active_frame, placeholder_text="👤 Matrícula", width=380, height=50, font=("Arial", 14), corner_radius=8, border_width=2, border_color=COLOR_PRIMARY)
        self.entry_user.pack(pady=7)

        # Chama a função que cria o campo de senha já com o olho
        self.entry_pass = self._criar_campo_senha(self.active_frame, "🔒 Senha")

        options_frame = ctk.CTkFrame(self.active_frame, fg_color="transparent", width=380)
        options_frame.pack(fill="x", pady=(5, 30))
        
        self.chk_manter = ctk.CTkCheckBox(options_frame, text="Lembrar-me", font=("Arial", 13), fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT)
        self.chk_manter.pack(side="left")

        btn_esqueci = ctk.CTkLabel(options_frame, text="Esqueceu a senha?", font=("Arial bold", 13), text_color=COLOR_TERTIARY, cursor="hand2")
        btn_esqueci.pack(side="right")
        btn_esqueci.bind("<Button-1>", lambda e: self.mostrar_recuperacao())

        ctk.CTkButton(self.active_frame, text="ENTRAR", width=380, height=50, corner_radius=8, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, font=("Arial bold", 16), command=self.acao_login).pack(pady=10)
        
        ctk.CTkLabel(self.active_frame, text="──────────────── OU ────────────────", font=("Arial", 12), text_color="#D1D1D1").pack(pady=10)

        ctk.CTkButton(self.active_frame, text="Criar nova conta", width=380, height=50, corner_radius=8, fg_color="transparent", border_width=2, border_color=COLOR_PRIMARY, text_color=COLOR_PRIMARY, hover_color="#E6F2F0", font=("Arial bold", 16), command=self.mostrar_cadastro).pack(pady=10)

    def acao_login(self):
        self.focus()
        ok, msg, dados = self.auth.login(self.entry_user.get(), self.entry_pass.get())
        if ok:
            if self.chk_manter.get(): self.auth.salvar_sessao(dados)
            else: self.auth.limpar_sessao()
            self.on_login_success(dados)
        else:
            messagebox.showerror("Acesso Negado", msg)

    # TELA DE CADASTRO
    def mostrar_cadastro(self):
        self._resetar_frame_ativo()

        ctk.CTkLabel(self.active_frame, text="NOVA CONTA", font=("Century Gothic bold", 32), text_color=COLOR_PRIMARY).pack(pady=(0, 20))

        # Campos de Cadastro
        self.cad_nome = ctk.CTkEntry(self.active_frame, placeholder_text="Nome Completo", width=380, height=45, font=("Arial", 14), corner_radius=8, border_width=2, border_color=COLOR_PRIMARY)
        self.cad_nome.pack(pady=6)

        self.cad_user = ctk.CTkEntry(self.active_frame, placeholder_text="Usuário (Login)", width=380, height=45, font=("Arial", 14), corner_radius=8, border_width=2, border_color=COLOR_PRIMARY)
        self.cad_user.pack(pady=6)

        self.cad_email = ctk.CTkEntry(self.active_frame, placeholder_text="E-mail", width=380, height=45, font=("Arial", 14), corner_radius=8, border_width=2, border_color=COLOR_PRIMARY)
        self.cad_email.pack(pady=6)

        # Campos de Senha
        self.cad_senha = self._criar_campo_senha(self.active_frame, "Senha (mín. 6 caracteres)")
        self.cad_conf = self._criar_campo_senha(self.active_frame, "Confirmar Senha")

        ctk.CTkButton(self.active_frame, text="FINALIZAR CADASTRO", width=380, height=50, corner_radius=8, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, font=("Arial bold", 16), command=self.acao_cadastrar).pack(pady=(20, 10))
        
        btn_voltar = ctk.CTkLabel(self.active_frame, text="← Voltar ao Login", font=("Arial bold", 14), text_color=COLOR_SECONDARY, cursor="hand2")
        btn_voltar.pack(pady=10)
        btn_voltar.bind("<Button-1>", lambda e: self.mostrar_login())

    def acao_cadastrar(self):
        ok, msg = self.auth.cadastrar_usuario(
            self.cad_nome.get(), self.cad_user.get(), self.cad_email.get(),
            self.cad_senha.get(), self.cad_conf.get()
        )
        if ok:
            messagebox.showinfo("Sucesso", msg)
            self.mostrar_login()
        else:
            messagebox.showwarning("Atenção", msg)

    # TELA DE RECUPERAÇÃO DE SENHA
    def mostrar_recuperacao(self):
        self._resetar_frame_ativo()

        ctk.CTkLabel(self.active_frame, text="RECUPERAÇÃO", font=("Century Gothic bold", 32), text_color=COLOR_PRIMARY).pack(pady=(0, 10))
        ctk.CTkLabel(self.active_frame, text="Informe seu e-mail para receber o código.", font=("Arial", 14), text_color=COLOR_PLACEHOLDER).pack(pady=(0, 30))

        self.rec_email = ctk.CTkEntry(self.active_frame, placeholder_text="✉️ Seu e-mail cadastrado", width=380, height=50, font=("Arial", 14), corner_radius=8, border_width=2, border_color=COLOR_PRIMARY)
        self.rec_email.pack(pady=10)

        self.btn_env_cod = ctk.CTkButton(self.active_frame, text="ENVIAR CÓDIGO", width=380, height=50, corner_radius=8, fg_color=COLOR_PRIMARY, font=("Arial bold", 16), command=self.acao_enviar_cod)
        self.btn_env_cod.pack(pady=10)

        self.frame_validacao = ctk.CTkFrame(self.active_frame, fg_color="transparent")
        
        self.rec_cod_input = ctk.CTkEntry(self.frame_validacao, placeholder_text="Código recebido (6 dígitos)", width=380, height=50, font=("Arial", 14), corner_radius=8)
        self.rec_cod_input.pack(pady=10)
        
        # Campo de Nova Senha com Olho Mágico
        self.rec_nova_senha = self._criar_campo_senha(self.frame_validacao, "Nova Senha")

        ctk.CTkButton(self.frame_validacao, text="SALVAR NOVA SENHA", width=380, height=50, corner_radius=8, fg_color=COLOR_TERTIARY, font=("Arial bold", 16), command=self.acao_redefinir).pack(pady=10)

        btn_voltar = ctk.CTkLabel(self.active_frame, text="← Voltar ao Login", font=("Arial bold", 14), text_color=COLOR_SECONDARY, cursor="hand2")
        btn_voltar.pack(pady=20)
        btn_voltar.bind("<Button-1>", lambda e: self.mostrar_login())

    def acao_enviar_cod(self):
        ok, msg = self.auth.enviar_codigo_recuperacao(self.rec_email.get())
        if ok:
            messagebox.showinfo("E-mail Enviado", "Verifique seu e-mail e digite o código.")
            self.btn_env_cod.pack_forget() 
            self.rec_email.configure(state="disabled") 
            self.frame_validacao.pack() 
        else:
            messagebox.showerror("Erro", msg)

    def acao_redefinir(self):
        if not self.auth.verificar_codigo(self.rec_cod_input.get()):
            messagebox.showerror("Erro", "Código incorreto.")
            return
        
        ok, msg = self.auth.redefinir_senha(self.rec_nova_senha.get())
        if ok:
            messagebox.showinfo("Sucesso", msg)
            self.mostrar_login()
        else:
            messagebox.showerror("Erro", msg)

if __name__ == "__main__":
    app = LoginView(lambda dados: print(f">>> LOGIN SUCESSO! User: {dados}"))
    app.mainloop()