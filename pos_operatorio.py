
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
with col5:
    opcoes = ["", "Trocar senha", "Sair do sistema"]
    if st.session_state.admin:
        opcoes.insert(1, "Criar novo usuário")
    escolha = st.selectbox("Ajustes", opcoes)
    if escolha == "Trocar senha":
        st.session_state.pagina = "trocar_senha"
    elif escolha == "Criar novo usuário":
        st.session_state.pagina = "novo_usuario"
    elif escolha == "Sair do sistema":
        st.session_state.logado = False
        st.rerun()

# Página de criação de novo usuário
if st.session_state.pagina == "novo_usuario":
    st.markdown("### Criar Novo Usuário")
    novo_usuario = st.text_input("Usuário")
    nova_senha = st.text_input("Senha", type="password")
    confirmar = st.text_input("Confirmar senha", type="password")
    novo_admin = st.checkbox("Administrador")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Criar usuário"):
            if novo_usuario and nova_senha == confirmar:
                st.session_state.usuarios[novo_usuario] = {
                    "senha": hash_senha(nova_senha),
                    "admin": novo_admin
                }
                salvar_usuarios(st.session_state.usuarios)
                st.success("Usuário criado com sucesso.")
            else:
                st.error("Verifique os campos.")
    with col_b:
        if st.button("Cancelar"):
            st.session_state.pagina = "principal"
            st.rerun()
    st.stop()

# Página de troca de senha
if st.session_state.pagina == "trocar_senha":
    st.markdown("### Trocar Senha")
    senha_atual = st.text_input("Senha atual", type="password")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar = st.text_input("Confirmar nova senha", type="password")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar nova senha"):
            if hash_senha(senha_atual) == st.session_state.usuarios[st.session_state.usuario]["senha"]:
                if nova_senha == confirmar and nova_senha != "":
                    st.session_state.usuarios[st.session_state.usuario]["senha"] = hash_senha(nova_senha)
                    salvar_usuarios(st.session_state.usuarios)
                    st.success("Senha atualizada com sucesso!")
                else:
                    st.error("As senhas não coincidem ou estão vazias.")
            else:
                st.error("Senha atual incorreta.")
    with col2:
        if st.button("Cancelar"):
            st.session_state.pagina = "principal"
            st.rerun()
    st.stop()

# Página de cadastro de novo paciente
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

# Página principal - exibição de pacientes
st.markdown("### Lista de Pacientes")
df = st.session_state.pacientes.copy()
if st.session_state.filtro == "Ativos":
    df = df[df["Alta"] == "Não"]
elif st.session_state.filtro == "De alta":
    df = df[df["Alta"] == "Sim"]

st.dataframe(df.reset_index(drop=True), use_container_width=True)
