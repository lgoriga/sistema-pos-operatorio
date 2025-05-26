
import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

usuarios_path = Path("usuarios.json")
pacientes_path = Path("pacientes.csv")

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    if usuarios_path.exists():
        with open(usuarios_path, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(dados):
    with open(usuarios_path, "w") as f:
        json.dump(dados, f)

def carregar_pacientes():
    if pacientes_path.exists():
        df = pd.read_csv(pacientes_path, parse_dates=["Data da cirurgia", "Próximo retorno"], dayfirst=True)
        df["Data da cirurgia"] = df["Data da cirurgia"].dt.strftime("%d/%m/%y")
        df["Próximo retorno"] = df["Próximo retorno"].dt.strftime("%d/%m/%y")
        return df
    return pd.DataFrame(columns=["Nome", "Data da cirurgia", "Próximo retorno", "Status", "Alta"])

def salvar_pacientes(df):
    df_to_save = df.copy()
    df_to_save["Data da cirurgia"] = pd.to_datetime(df_to_save["Data da cirurgia"], dayfirst=True)
    df_to_save["Próximo retorno"] = pd.to_datetime(df_to_save["Próximo retorno"], dayfirst=True)
    df_to_save.to_csv(pacientes_path, index=False)

def autenticar(usuario, senha, usuarios):
    return usuario in usuarios and usuarios[usuario]["senha"] == hash_senha(senha)

def status_cor(data_proximo_retorno):
    if isinstance(data_proximo_retorno, str):
        data_proximo_retorno = datetime.strptime(data_proximo_retorno, "%d/%m/%y").date()
    hoje = datetime.today().date()
    if data_proximo_retorno < hoje:
        return "🔴 Atrasado"
    elif data_proximo_retorno <= hoje + timedelta(days=2):
        return "🟡 Em breve"
    else:
        return "🟢 Ok"

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.admin = False
    st.session_state.pagina = "principal"
    st.session_state.modo = "Desktop"
    st.session_state.filtro = "Todos"
    st.session_state.pacientes = carregar_pacientes()

# Login
if not st.session_state.logado:
    st.title("Login - Sistema Pós-Operatório")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if autenticar(usuario, senha, st.session_state.usuarios):
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.admin = st.session_state.usuarios[usuario]["admin"]
            st.session_state.pagina = "principal"
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# Barra superior
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
with col1:
    st.markdown("### Sistema Pós-Operatório")
with col2:
    st.selectbox("Modo", ["Desktop", "Mobile"], key="modo")
with col3:
    st.selectbox("Filtro", ["Todos", "Ativos", "De alta"], key="filtro")
with col4:
    if st.button("Adicionar Paciente"):
        st.session_state.pagina = "novo_paciente"
        st.rerun()
with col5:
    with st.expander("Ajustes"):
        if st.button("Trocar senha"):
            st.session_state.pagina = "trocar_senha"
            st.rerun()
        if st.session_state.admin:
            if st.button("Criar novo usuário"):
                st.session_state.pagina = "novo_usuario"
                st.rerun()
        if st.button("Sair"):
            st.session_state.logado = False
            st.session_state.pagina = "principal"
            st.rerun()

# Página criar novo usuário
if st.session_state.pagina == "novo_usuario":
    st.markdown("### Criar Novo Usuário")
    with st.form("criar_usuario"):
        novo_usuario = st.text_input("Usuário")
        nova_senha = st.text_input("Senha", type="password")
        confirmar = st.text_input("Confirmar senha", type="password")
        novo_admin = st.checkbox("Administrador")
        col1, col2 = st.columns(2)
        with col1:
            criar = st.form_submit_button("Criar usuário")
        with col2:
            cancelar = st.form_submit_button("Cancelar")

    if criar:
        if novo_usuario and nova_senha == confirmar:
            st.session_state.usuarios[novo_usuario] = {
                "senha": hash_senha(nova_senha),
                "admin": novo_admin
            }
            salvar_usuarios(st.session_state.usuarios)
            st.success("Usuário criado com sucesso.")
        else:
            st.error("Verifique os campos.")
    elif cancelar:
        st.session_state.pagina = "principal"
        st.rerun()
    st.stop()

# Página trocar senha
if st.session_state.pagina == "trocar_senha":
    st.markdown("### Trocar Senha")
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha atual", type="password")
        nova_senha = st.text_input("Nova senha", type="password")
        confirmar = st.text_input("Confirmar nova senha", type="password")
        col1, col2 = st.columns(2)
        with col1:
            salvar = st.form_submit_button("Salvar nova senha")
        with col2:
            cancelar = st.form_submit_button("Cancelar")

    if salvar:
        if hash_senha(senha_atual) == st.session_state.usuarios[st.session_state.usuario]["senha"]:
            if nova_senha == confirmar and nova_senha != "":
                st.session_state.usuarios[st.session_state.usuario]["senha"] = hash_senha(nova_senha)
                salvar_usuarios(st.session_state.usuarios)
                st.success("Senha atualizada com sucesso!")
            else:
                st.error("As senhas não coincidem ou estão vazias.")
        else:
            st.error("Senha atual incorreta.")
    elif cancelar:
        st.session_state.pagina = "principal"
        st.rerun()
    st.stop()

# Página novo paciente
if st.session_state.pagina == "novo_paciente":
    with st.form("form_paciente", clear_on_submit=True):
        st.subheader("Novo Paciente")
        nome = st.text_input("Nome do paciente")
        data_cirurgia = st.date_input("Data da cirurgia", format="DD/MM/YY")
        data_retorno = st.date_input("Data do próximo retorno", format="DD/MM/YY")
        alta = st.checkbox("Paciente teve alta?")
        if st.form_submit_button("Salvar"):
            status = status_cor(data_retorno)
            novo = pd.DataFrame([{
                "Nome": nome,
                "Data da cirurgia": data_cirurgia.strftime("%d/%m/%y"),
                "Próximo retorno": data_retorno.strftime("%d/%m/%y"),
                "Status": status,
                "Alta": "Sim" if alta else "Não"
            }])
            st.session_state.pacientes = pd.concat([st.session_state.pacientes, novo], ignore_index=True)
            salvar_pacientes(st.session_state.pacientes)
            st.success("Paciente salvo!")
            st.session_state.pagina = "principal"
            st.rerun()
    st.stop()

# Página principal
st.markdown("### Lista de Pacientes")
df = st.session_state.pacientes.copy()
if st.session_state.filtro == "Ativos":
    df = df[df["Alta"] == "Não"]
elif st.session_state.filtro == "De alta":
    df = df[df["Alta"] == "Sim"]

st.dataframe(df.reset_index(drop=True), use_container_width=True)
