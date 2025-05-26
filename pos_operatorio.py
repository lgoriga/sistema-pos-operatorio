
import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

# Caminhos para arquivos
usuarios_path = Path("usuarios.json")
pacientes_path = Path("pacientes.csv")
log_path = Path("log_edicoes.json")

# Utilitários
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

# Inicialização de sessão
if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.admin = False
    st.session_state.pagina = "principal"
    st.session_state.modo_interface = "Desktop"
    st.session_state.filtro = "Todos"
    st.session_state.pacientes = carregar_pacientes()
    st.session_state.log = carregar_log()

# Página de login
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

# Interface principal
# Barra superior
col0, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col0:
    if st.button("Voltar à lista"):
        st.session_state.pagina = "principal"
        st.rerun()
with col2:
    st.session_state.modo_interface = st.selectbox("Modo", ["Desktop", "Mobile"], index=["Desktop", "Mobile"].index(st.session_state.modo_interface))
with col3:
    st.session_state.filtro = st.selectbox("Filtro", ["Todos", "Ativos", "De alta"], index=["Todos", "Ativos", "De alta"].index(st.session_state.filtro))
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

# Página principal
if st.session_state.pagina == "principal":
    st.markdown("### Lista de Pacientes")
    df = st.session_state.pacientes.copy()

    if st.session_state.filtro == "Ativos":
        df = df[df["Alta"] == "Não"]
    elif st.session_state.filtro == "De alta":
        df = df[df["Alta"] == "Sim"]

    if df.empty:
        st.info("Nenhum paciente cadastrado.")
    else:
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



# Página novo paciente
if st.session_state.pagina == "novo_paciente":
    with st.form("form_paciente", clear_on_submit=True):
        st.subheader("Novo Paciente")
        nome = st.text_input("Nome do paciente")
        data_nascimento = st.date_input("Data de nascimento")
        telefone = st.text_input("Telefone (ex: +55 31999999999)", value="+55")
        data_cirurgia = st.date_input("Data da cirurgia")
        data_retorno = data_cirurgia + timedelta(days=7)
        st.markdown(f"**Data do próximo retorno:** {data_retorno.strftime('%d/%m/%y')}")

        salvar = st.form_submit_button("Salvar")
    if salvar:
        novo = pd.DataFrame([{
            "Nome": nome,
            "Data da cirurgia": data_cirurgia.strftime("%d/%m/%y"),
            "Próximo retorno": data_retorno.strftime("%d/%m/%y"),
            "Status": "🟡 Pendente",
            "Alta": "Não",
            "Nascimento": data_nascimento.strftime("%d/%m/%Y"),
            "Telefone": telefone
        }])
        st.session_state.pacientes = pd.concat([st.session_state.pacientes, novo], ignore_index=True)
        salvar_pacientes(st.session_state.pacientes)
        st.success("Paciente salvo com sucesso!")
        st.session_state.pagina = "principal"
        st.rerun()
    if st.button("Cancelar"):
        st.session_state.pagina = "principal"
        st.rerun()


# Página trocar senha
if st.session_state.pagina == "trocar_senha":
    st.subheader("Trocar Senha")
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha atual", type="password")
        nova = st.text_input("Nova senha", type="password")
        confirmar = st.text_input("Confirmar nova senha", type="password")
        col1, col2 = st.columns(2)
        with col1:
            salvar = st.form_submit_button("Salvar")
        with col2:
            cancelar = st.form_submit_button("Cancelar")
    if salvar:
        if hash_senha(senha_atual) == st.session_state.usuarios[st.session_state.usuario]["senha"]:
            if nova and nova == confirmar:
                st.session_state.usuarios[st.session_state.usuario]["senha"] = hash_senha(nova)
                salvar_usuarios(st.session_state.usuarios)
                st.success("Senha atualizada com sucesso.")
                st.session_state.pagina = "principal"
                st.rerun()
            else:
                st.error("As novas senhas não coincidem ou estão em branco.")
        else:
            st.error("Senha atual incorreta.")
    elif cancelar:
        st.session_state.pagina = "principal"
        st.rerun()

# Página novo usuário
if st.session_state.pagina == "novo_usuario":
    st.subheader("Criar Novo Usuário")
    with st.form("form_usuario"):
        novo_usuario = st.text_input("Novo usuário")
        senha = st.text_input("Senha", type="password")
        confirmar = st.text_input("Confirmar senha", type="password")
        admin = st.checkbox("Administrador")
        col1, col2 = st.columns(2)
        with col1:
            criar = st.form_submit_button("Criar")
        with col2:
            cancelar = st.form_submit_button("Cancelar")
    if criar:
        if novo_usuario and senha == confirmar:
            st.session_state.usuarios[novo_usuario] = {"senha": hash_senha(senha), "admin": admin}
            salvar_usuarios(st.session_state.usuarios)
            st.success("Usuário criado com sucesso.")
            st.session_state.pagina = "principal"
            st.rerun()
        else:
            st.error("Verifique se o nome foi preenchido e as senhas coincidem.")
    elif cancelar:
        st.session_state.pagina = "principal"
        st.rerun()
