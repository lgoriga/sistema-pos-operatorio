
import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

# Caminhos de arquivos
usuarios_path = Path("usuarios.json")
pacientes_path = Path("pacientes.csv")

# Funções de segurança
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Carrega usuários salvos
def carregar_usuarios():
    if usuarios_path.exists():
        with open(usuarios_path, "r") as f:
            return json.load(f)
    return {}

# Salva usuários
def salvar_usuarios(dados):
    with open(usuarios_path, "w") as f:
        json.dump(dados, f)

# Carrega pacientes salvos
def carregar_pacientes():
    if pacientes_path.exists():
        return pd.read_csv(pacientes_path, parse_dates=["Data da cirurgia", "Próximo retorno"])
    return pd.DataFrame(columns=["Nome", "Data da cirurgia", "Próximo retorno", "Status", "Alta"])

# Salva pacientes
def salvar_pacientes(df):
    df.to_csv(pacientes_path, index=False)

# Verifica login
def autenticar(usuario, senha, usuarios):
    return usuario in usuarios and usuarios[usuario]["senha"] == hash_senha(senha)

# Inicializa usuários
if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

# Página de login
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.admin = False

if not st.session_state.logado:
    st.title("Login - Sistema Pós-Operatório")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if autenticar(usuario, senha, st.session_state.usuarios):
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.admin = st.session_state.usuarios[usuario]["admin"]
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# Área logada
st.sidebar.write(f"Usuário logado: {st.session_state.usuario}")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.experimental_rerun()

# Gerenciamento de usuários (admin)
if st.session_state.admin:
    st.sidebar.subheader("Gerenciar usuários")
    novo_usuario = st.sidebar.text_input("Novo usuário")
    nova_senha = st.sidebar.text_input("Nova senha", type="password")
    novo_admin = st.sidebar.checkbox("Administrador")
    if st.sidebar.button("Adicionar usuário"):
        if novo_usuario and nova_senha:
            st.session_state.usuarios[novo_usuario] = {
                "senha": hash_senha(nova_senha),
                "admin": novo_admin
            }
            salvar_usuarios(st.session_state.usuarios)
            st.sidebar.success("Usuário criado com sucesso.")
    excluir_usuario = st.sidebar.selectbox("Excluir usuário", [""] + list(st.session_state.usuarios.keys()))
    if st.sidebar.button("Excluir"):
        if excluir_usuario:
            st.session_state.usuarios.pop(excluir_usuario, None)
            salvar_usuarios(st.session_state.usuarios)
            st.sidebar.success("Usuário excluído.")

# Função para definir cor de status
def status_cor(data_proximo_retorno):
    hoje = datetime.today().date()
    if data_proximo_retorno < hoje:
        return "🔴 Atrasado"
    elif data_proximo_retorno <= hoje + timedelta(days=2):
        return "🟡 Em breve"
    else:
        return "🟢 Ok"

# Carrega pacientes
if "pacientes" not in st.session_state:
    st.session_state.pacientes = carregar_pacientes()

# Interface principal
st.title("Controle de Pacientes - Pós-Operatório")

with st.form("cadastro_paciente"):
    st.subheader("Adicionar Novo Paciente")
    nome = st.text_input("Nome do paciente")
    data_cirurgia = st.date_input("Data da cirurgia")
    data_retorno = st.date_input("Data do próximo retorno")
    alta = st.checkbox("Paciente teve alta?")
    if st.form_submit_button("Salvar paciente"):
        status = status_cor(data_retorno)
        novo = pd.DataFrame([{
            "Nome": nome,
            "Data da cirurgia": data_cirurgia,
            "Próximo retorno": data_retorno,
            "Status": status,
            "Alta": "Sim" if alta else "Não"
        }])
        st.session_state.pacientes = pd.concat([st.session_state.pacientes, novo], ignore_index=True)
        salvar_pacientes(st.session_state.pacientes)
        st.success("Paciente salvo com sucesso.")

# Filtro de visualização
st.subheader("Lista de Pacientes")
filtro = st.radio("Filtrar por", ["Todos", "Ativos", "De alta"])

df = st.session_state.pacientes.copy()
if filtro == "Ativos":
    df = df[df["Alta"] == "Não"]
elif filtro == "De alta":
    df = df[df["Alta"] == "Sim"]

st.dataframe(df.reset_index(drop=True), use_container_width=True)
