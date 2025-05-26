
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Sistema Pós-Operatório", layout="wide")

st.title("Controle de Pacientes - Pós-Operatório")

# Inicialização de dados
if "pacientes" not in st.session_state:
    st.session_state.pacientes = []

# Função para definir cor de status
def status_cor(data_proximo_retorno):
    hoje = datetime.today().date()
    if data_proximo_retorno < hoje:
        return "🔴 Atrasado"
    elif data_proximo_retorno <= hoje + timedelta(days=2):
        return "🟡 Em breve"
    else:
        return "🟢 Ok"

# Cadastro de paciente
st.sidebar.header("Adicionar Paciente")
nome = st.sidebar.text_input("Nome")
data_cirurgia = st.sidebar.date_input("Data da cirurgia")
data_retorno = st.sidebar.date_input("Data do próximo retorno")
alta = st.sidebar.checkbox("Paciente já teve alta?")

if st.sidebar.button("Salvar paciente"):
    st.session_state.pacientes.append({
        "Nome": nome,
        "Data da cirurgia": data_cirurgia,
        "Próximo retorno": data_retorno,
        "Status": status_cor(data_retorno),
        "Alta": "Sim" if alta else "Não"
    })
    st.sidebar.success("Paciente salvo com sucesso!")

# Filtro de exibição
aba = st.radio("Visualizar pacientes:", ["Ativos", "De alta", "Todos"])

# Exibição dos pacientes
df = pd.DataFrame(st.session_state.pacientes)
if not df.empty:
    if aba == "Ativos":
        df = df[df["Alta"] == "Não"]
    elif aba == "De alta":
        df = df[df["Alta"] == "Sim"]
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
else:
    st.info("Nenhum paciente cadastrado ainda.")
