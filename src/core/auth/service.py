import bcrypt
import smtplib
import random
import json
import os
from email.mime.text import MIMEText
from datetime import datetime
from src.core.auth.repository import AuthRepository

class AuthService:
    def __init__(self):
        self.repo = AuthRepository()
        self.caminho_login_salvo = "login_salvo.json"
        self.codigo_recuperacao = None
        self.email_recuperacao = None

    def login(self, username, senha):
        if not username or not senha: return False, "Preencha a Matrícula e a senha.", None
        
        sucesso, resultado = self.repo.buscar_usuario(username)
        if not sucesso: return False, "Erro técnico de conexão com o banco de dados.", None
        if not resultado: return False, "Matrícula não encontrada.", None

        senha_hash_banco, tipo_perfil, nome_completo, user_real, is_admin, is_ativo = resultado

        if not is_ativo: return False, "Esta conta está inativada. Contacte o administrador.", None

        try:
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_banco.encode('utf-8')):
                dados_usuario = {"username": user_real, "nome": nome_completo, "is_admin": is_admin, "tipo_perfil": tipo_perfil}
                return True, "Bem-vindo!", dados_usuario
            return False, "A senha está incorreta.", None
        except ValueError:
            # Fallback para senhas Legado
            if senha == senha_hash_banco:
                return True, "Bem-vindo (Modo Legado)!", {"username": user_real, "nome": nome_completo, "is_admin": is_admin, "tipo_perfil": tipo_perfil}
            return False, "Erro na verificação da senha (formato inválido).", None

    def cadastrar_usuario(self, nome, username, email, senha, conf_senha, perfil):
        if not all([nome, username, email, senha, conf_senha, perfil]): return False, "Preencha todos os campos."
        if senha != conf_senha: return False, "As senhas não coincidem."
        if len(senha) < 6: return False, "A senha deve ter pelo menos 6 caracteres."

        sucesso, resultado = self.repo.verificar_existencia(username, email)
        if not sucesso: return False, "Erro de conexão com o banco."
        if resultado: return False, "Matrícula ou E-mail já registado."

        try:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            ok, erro = self.repo.criar_usuario(nome, username, email, senha_hash, perfil)
            if not ok: return False, "Erro ao gravar informações no banco de dados."
            return True, "Conta criada com sucesso! Já pode fazer login."
        except Exception:
            return False, "Erro interno ao processar o registo."

    def enviar_codigo_recuperacao(self, email):
        if not email: return False, "Introduza o seu e-mail."
        
        sucesso, resultado = self.repo.buscar_email(email)
        if not sucesso or not resultado: return False, "E-mail não encontrado no sistema."

        self.codigo_recuperacao = str(random.randint(100000, 999999))
        self.email_recuperacao = email
        
        remetente, senha_app = os.getenv("EMAIL_REMETENTE"), os.getenv("EMAIL_SENHA")
        if not remetente or not senha_app: return False, "Serviço de e-mail não configurado."

        msg = MIMEText(f"O seu código de recuperação para o SIGP é: {self.codigo_recuperacao}")
        msg["Subject"] = "Recuperação de Senha - SIGP"
        msg["From"], msg["To"] = remetente, email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(remetente, senha_app)
                server.sendmail(remetente, [email], msg.as_string())
            return True, "Código enviado para o seu e-mail!"
        except Exception:
            return False, "Falha ao conectar com o provedor de e-mail."

    def verificar_codigo(self, codigo_digitado):
        if not codigo_digitado: return False, "Introduza o código recebido."
        if codigo_digitado != self.codigo_recuperacao: return False, "Código incorreto."
        return True, "Código validado."

    def redefinir_senha(self, nova_senha):
        if not self.email_recuperacao: return False, "Acesso inválido."
        if not nova_senha or len(nova_senha) < 6: return False, "A nova senha deve ter no mínimo 6 caracteres."
        
        try:
            senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            ok, erro = self.repo.atualizar_senha(self.email_recuperacao, senha_hash)
            if not ok: return False, "Erro ao atualizar a senha no banco."
            
            self.codigo_recuperacao = None
            self.email_recuperacao = None
            return True, "Sua senha foi alterada com sucesso!"
        except Exception:
            return False, "Erro interno."

    def salvar_sessao(self, dados_usuario):
        try:
            with open(self.caminho_login_salvo, "w", encoding="utf-8") as f:
                json.dump({"user": dados_usuario, "date": datetime.now().strftime("%Y-%m-%d")}, f, ensure_ascii=False)
        except: pass

    def ler_sessao(self):
        if not os.path.exists(self.caminho_login_salvo): return None
        try:
            with open(self.caminho_login_salvo, "r", encoding="utf-8") as f: dados = json.load(f)
            if dados.get("date") == datetime.now().strftime("%Y-%m-%d"): return dados.get("user")
        except: pass
        self.limpar_sessao()
        return None
    
    def limpar_sessao(self):
        if os.path.exists(self.caminho_login_salvo):
            try: os.remove(self.caminho_login_salvo)
            except: pass