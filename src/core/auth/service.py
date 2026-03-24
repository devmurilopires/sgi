import bcrypt
import smtplib
import random
import json
import os
import psycopg2
from email.mime.text import MIMEText
from datetime import datetime
from config.database import get_db_connection

class AuthService:
    def __init__(self):
        self.caminho_login_salvo = "login_salvo.json"
        self.codigo_recuperacao = None
        self.email_recuperacao = None

    # INFRAESTRUTURA DE BASE DE DADOS
    def _executar_query(self, query, params=None, fetch_one=False, commit=False):
        """
        Método centralizado para executar as consultas (queries) na base de dados.
        Garante que a conexão abre e fecha corretamente e trata erros do PostgreSQL.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    
                    if commit:
                        conn.commit()
                        return True, None
                    
                    if fetch_one:
                        return cursor.fetchone(), None
                    
                    return cursor.fetchall(), None
                    
        except psycopg2.Error as erro_banco:
            # Captura erros nativos da base de dados (tabela inexistente, etc.)
            msg_erro = f"Erro na base de dados: {erro_banco.pgerror}"
            print(f"[LOG DB] {msg_erro}") 
            return None, "Erro técnico de conexão com a base de dados."
            
        except Exception as e:
            # Captura outros erros de execução do Python
            msg_erro = f"Erro inesperado: {str(e)}"
            print(f"[LOG APP] {msg_erro}")
            return None, "Ocorreu um erro interno no sistema."

    # AUTENTICAÇÃO E CADASTRO
    def login(self, username, senha):
        """
        Autentica o utilizador através do username ou email.
        """
        if not username or not senha:
            return False, "Por favor, preencha a Matrícula e a senha.", None

        # Procura pelos dados da Matrícula na NOVA tabela
        query_busca = """
            SELECT password_hash, tipo_perfil, nome_completo, username
            FROM common.usuarios 
            WHERE email = %s OR username = %s
        """
        resultado, erro = self._executar_query(query_busca, (username, username), fetch_one=True)

        if erro: 
            return False, erro, None
        
        if not resultado: 
            return False, "Matrícula não encontrada.", None

        senha_hash_banco, tipo_perfil, nome_completo, user_real = resultado

        try:
            # Compara a senha digitada com o Hash seguro da base de dados
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_banco.encode('utf-8')):
                dados_usuario = {
                    "username": user_real,
                    "nome": nome_completo,
                    "is_admin": tipo_perfil == "admin"
                }
                return True, "Bem-vindo!", dados_usuario
            else:
                return False, "A senha está incorreta.", None
                
        except ValueError:
            # Fallback para senhas antigas (legado) que não estão em Hash
            if senha == senha_hash_banco:
                 dados_usuario = {
                    "username": user_real,
                    "nome": nome_completo,
                    "is_admin": tipo_perfil == "admin"
                }
                 return True, "Bem-vindo (Modo Legado)!", dados_usuario
                 
            return False, "Erro na verificação da senha (formato inválido).", None

    def cadastrar_usuario(self, nome, username, email, senha, conf_senha):
        """
        Regista um novo usuario na tabela common.usuarios.
        """
        # Validações iniciais (Fail Fast)
        if not all([nome, username, email, senha, conf_senha]):
            return False, "Todos os campos são de preenchimento obrigatório."
        
        if senha != conf_senha:
            return False, "As senhas não coincidem."
        
        if len(senha) < 6:
            return False, "A senha tem de ter pelo menos 6 caracteres."

        # Verifica se a Matrícula já existem na base NOVA
        query_verificacao = "SELECT id FROM common.usuarios WHERE username = %s OR email = %s"
        resultado, erro = self._executar_query(query_verificacao, (username, email), fetch_one=True)
        
        if erro: 
            return False, erro
        if resultado: 
            return False, "A Matrícula já se encontra registada."

        # Encripta a senha e insere o registo
        try:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            query_insercao = """
                INSERT INTO common.usuarios (nome_completo, username, email, password_hash, tipo_perfil) 
                VALUES (%s, %s, %s, %s, 'comum')
            """
            parametros = (nome, username, email, senha_hash)
            
            sucesso, erro_insercao = self._executar_query(query_insercao, parametros, commit=True)
            
            if erro_insercao: 
                return False, erro_insercao
            
            return True, "Conta criada com sucesso! Já pode fazer login."
            
        except Exception as e:
            print(f"[LOG HASH] Erro ao encriptar a senha: {e}")
            return False, "Erro interno ao processar o registo."

    # RECUPERAÇÃO DE SENHA
    def enviar_codigo_recuperacao(self, email):
        """
        Valida o e-mail, gera um código de 6 dígitos e envia por SMTP.
        """
        if not email: 
            return False, "Por favor, introduza o seu e-mail."

        # Verifica se o e-mail existe
        query_busca = "SELECT id FROM common.usuarios WHERE email = %s"
        resultado, erro = self._executar_query(query_busca, (email,), fetch_one=True)
        
        if erro: 
            return False, erro
        if not resultado: 
            return False, "E-mail não encontrado no sistema."

        # Gera e guarda o código em memória
        self.codigo_recuperacao = str(random.randint(100000, 999999))
        self.email_recuperacao = email
        
        remetente = os.getenv("EMAIL_REMETENTE")
        senha_app = os.getenv("EMAIL_SENHA")

        if not remetente or not senha_app:
            return False, "Configuração em falta: O e-mail do sistema não está configurado no ficheiro .env."

        # Constrói o E-mail
        msg = MIMEText(f"O seu código de recuperação para o SIGP é: {self.codigo_recuperacao}")
        msg["Subject"] = "Recuperação de Senha - SIGP"
        msg["From"] = remetente
        msg["To"] = email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(remetente, senha_app)
                server.sendmail(remetente, [email], msg.as_string())
            return True, "O código de recuperação foi enviado para o seu e-mail!"
        except Exception as e:
            print(f"[LOG EMAIL] Falha de SMTP: {e}")
            return False, "Falha ao enviar o e-mail. Verifique a sua ligação."

    def verificar_codigo(self, codigo_digitado):
        """
        Compara o código inserido pelo utilizador com o código gerado.
        """
        if not codigo_digitado:
            return False, "Introduza o código recebido."
            
        if codigo_digitado != self.codigo_recuperacao:
            return False, "O código está incorreto."
            
        return True, "Código validado com sucesso."

    def redefinir_senha(self, nova_senha):
        """
        Atualiza o hash da senha na base de dados para o e-mail validado.
        """
        if not self.email_recuperacao:
            return False, "Acesso inválido. Solicite um novo código de recuperação."
            
        if not nova_senha or len(nova_senha) < 6:
            return False, "A nova senha tem de ter pelo menos 6 caracteres."
            
        try:
            senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            query_update = "UPDATE common.usuarios SET password_hash = %s WHERE email = %s"
            sucesso, erro = self._executar_query(query_update, (senha_hash, self.email_recuperacao), commit=True)
            
            if erro: 
                return False, erro
            
            # Limpa o estado da recuperação
            self.codigo_recuperacao = None
            self.email_recuperacao = None
            
            return True, "A sua senha foi alterada com sucesso!"
            
        except Exception as e:
            print(f"[LOG HASH] Falha a encriptar a nova senha: {e}")
            return False, "Ocorreu um erro interno ao guardar a nova senha."

    # GESTÃO DE SESSÃO LOCAL (MANTER CONECTADO)
    def salvar_sessao(self, dados_usuario):
        """
        Guarda o dicionário do utilizador num ficheiro JSON.
        """
        try:
            payload = {
                "user": dados_usuario,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            with open(self.caminho_login_salvo, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
        except Exception as e:
            print(f"[LOG FILE] Erro ao criar ficheiro de sessão: {e}")

    def ler_sessao(self):
        """
        Lê a sessão. Se a data guardada for diferente de hoje, invalida.
        """
        if not os.path.exists(self.caminho_login_salvo):
            return None
            
        try:
            with open(self.caminho_login_salvo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                
            if dados.get("date") == datetime.now().strftime("%Y-%m-%d"):
                return dados.get("user")
                
        except Exception as e:
            print(f"[LOG FILE] Ficheiro de sessão inválido ou corrompido: {e}")
            
        # Se os dados forem de ontem ou ocorrer erro de leitura, apaga o ficheiro
        self.limpar_sessao()
        return None
    
    def limpar_sessao(self):
        """
        Apaga o ficheiro local para encerrar a sessão.
        """
        if os.path.exists(self.caminho_login_salvo):
            try:
                os.remove(self.caminho_login_salvo)
            except Exception as e:
                print(f"[LOG FILE] Impossível eliminar o ficheiro de sessão: {e}")