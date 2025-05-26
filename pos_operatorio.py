
import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

usuarios_path = Path("usuarios.json")
pacientes_path = Path("pacientes.csv")
log_path = Path("log_edicoes.json")

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

def carregar_log():
    if log_path.exists():
        with open(log_path, "r") as f:
            return json.load(f)
    return []

def salvar_log(logs):
    with open(log_path, "w") as f:
        json.dump(logs, f)

def carregar_pacientes():
    if pacientes_path.exists():
        try:
            df = pd.read_csv(pacientes_path, parse_dates=["Data da cirurgia", "Próximo retorno"], dayfirst=True)
            df["Data da cirurgia"] = df["Data da cirurgia"].dt.strftime("%d/%m/%y")
            df["Próximo retorno"] = df["Próximo retorno"].dt.strftime("%d/%m/%y")
            return df
        except Exception:
            return pd.DataFrame(columns=["Nome", "Data da cirurgia", "Próximo retorno", "Status", "Alta"])
    return pd.DataFrame(columns=["Nome", "Data da cirurgia", "Próximo retorno", "Status", "Alta"])

def salvar_pacientes(df):
    df_to_save = df.copy()
    df_to_save["Data da cirurgia"] = pd.to_datetime(df_to_save["Data da cirurgia"], dayfirst=True)
    df_to_save["Próximo retorno"] = pd.to_datetime(df_to_save["Próximo retorno"], dayfirst=True)
    df_to_save.to_csv(pacientes_path, index=False)

def status_cor(data_proximo_retorno):
    if isinstance(data_proximo_retorno, str):
        data_proximo_retorno = datetime.strptime(data_proximo_retorno, "%d/%m/%y").date()
    hoje = datetime.today().date()
    if data_proximo_retorno < hoje:
        return "🔴 Atrasado"
    elif data_proximo_retorno <= hoje + timedelta(days=2):
        return "🟡 Pendente"
    else:
        return "🟢 Agendado"

# Sessões
if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.admin = False
    st.session_state.pagina = "principal"
    st.session_state.pacientes = carregar_pacientes()
    st.session_state.log = carregar_log()

# Login
if not st.session_state.logado:
    st.title("Login - Sistema Pós-Operatório")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in st.session_state.usuarios and st.session_state.usuarios[usuario]["senha"] == hash_senha(senha):
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.admin = st.session_state.usuarios[usuario]["admin"]
            st.session_state.pagina = "principal"
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# Página principal
if st.session_state.pagina == "principal":
    
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

    st.markdown("### Lista de Pacientes")
    df = st.session_state.pacientes.copy()

    if df.empty:
        st.info("Nenhum paciente cadastrado.")

    df.insert(0, "Nº", range(1, len(df) + 1))
    df["Status de agendamento"] = df["Próximo retorno"].apply(status_cor)

    for i, row in df.iterrows():
        cols = st.columns([0.5, 1.5, 3, 2, 1])
        cols[0].write(f"{row['Nº']}")
        cols[1].write(f"{row['Status de agendamento']}")
        cols[2].write(row["Nome"])
        cols[3].write(row["Data da cirurgia"])
        if cols[4].button("Editar", key=f"editar_{i}"):
            st.session_state.paciente_editando = i
            st.session_state.pagina = "editar_paciente"
            st.rerun()
    st.stop()
