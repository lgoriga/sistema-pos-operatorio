
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
        return pd.read_csv(pacientes_path, parse_dates=["Data da cirurgia", "Próximo retorno"])
    return pd.DataFrame(columns=["Nome", "Data da cirurgia", "Próximo retorno", "Status", "Alta"])

def salvar_pacientes(df):
    df.to_csv(pacientes_path, index=False)

def autenticar(usuario, senha, usuarios):
    return usuario in usuarios and usuarios[usuario]["senha"] == hash_senha(senha)

def status_cor(data_proximo_retorno):
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

# Barra superior com layout mais ajustado
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
with col5:
    if st.button("Ajustes"):
        st.session_state.pagina = "ajustes"

# Ajustes: troca de senha e gestão de usuários (admin)
if st.session_state.pagina == "ajustes":
    st.markdown("### Ajustes")
    with st.expander("Trocar Senha"):
        senha_atual = st.text_input("Senha atual", type="password")
        nova_senha = st.text_input("Nova senha", type="password")
        confirmar = st.text_input("Confirmar nova senha", type="password")
        if st.button("Atualizar senha"):
            if hash_senha(senha_atual) == st.session_state.usuarios[st.session_state.usuario]["senha"]:
                if nova_senha == confirmar and nova_senha != "":
                    st.session_state.usuarios[st.session_state.usuario]["senha"] = hash_senha(nova_senha)
                    salvar_usuarios(st.session_state.usuarios)
                    st.success("Senha atualizada com sucesso!")
                else:
                    st.error("As senhas não coincidem ou estão vazias.")
            else:
                st.error("Senha atual incorreta.")

    if st.session_state.admin:
        st.markdown("---")
        st.markdown("### Criar Novo Usuário")
        novo_usuario = st.text_input("Novo usuário")
        nova_senha_usuario = st.text_input("Senha do novo usuário", type="password")
        confirmar_senha_usuario = st.text_input("Confirmar senha", type="password")
        novo_admin = st.checkbox("Conceder privilégios de administrador")
        if st.button("Criar usuário"):
            if novo_usuario and nova_senha_usuario == confirmar_senha_usuario:
                st.session_state.usuarios[novo_usuario] = {
                    "senha": hash_senha(nova_senha_usuario),
                    "admin": novo_admin
                }
                salvar_usuarios(st.session_state.usuarios)
                st.success("Usuário criado com sucesso!")
            else:
                st.error("Verifique os campos do novo usuário.")
    st.markdown("---")
    if st.button("Sair do sistema"):
        st.session_state.logado = False
        st.rerun()
    st.stop()

# Cadastro de novo paciente
if st.session_state.pagina == "novo_paciente":
    with st.form("form_paciente", clear_on_submit=True):
        st.subheader("Novo Paciente")
        nome = st.text_input("Nome do paciente")
        data_cirurgia = st.date_input("Data da cirurgia")
        data_retorno = st.date_input("Data do próximo retorno")
        alta = st.checkbox("Paciente teve alta?")
        if st.form_submit_button("Salvar"):
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
            st.success("Paciente salvo!")
            st.session_state.pagina = "principal"
            st.rerun()
    st.stop()

# Exibição de pacientes
st.markdown("### Lista de Pacientes")
df = st.session_state.pacientes.copy()
if st.session_state.filtro == "Ativos":
    df = df[df["Alta"] == "Não"]
elif st.session_state.filtro == "De alta":
    df = df[df["Alta"] == "Sim"]

st.dataframe(df.reset_index(drop=True), use_container_width=True)
