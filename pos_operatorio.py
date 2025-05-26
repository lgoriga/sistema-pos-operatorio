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
    st.session_state.modo_interface = st.selectbox("Modo", ["Desktop", "Mobile 1", "Mobile 2"], index=["Desktop", "Mobile"].index(st.session_state.modo_interface))
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

    modo = st.session_state.modo_interface

    if df.empty:
        st.info("Nenhum paciente cadastrado.")
    else:
        dias_retornos = [7, 14, 21, 30, 60, 90, 180, 365]

        if modo == "Desktop":
            st.markdown("#### Pacientes")
            cabecalho = st.columns([0.5, 2.5, 1.5, 1.5, 1.5, 1, 1])
            cabecalho[0].markdown("**Nº**")
            cabecalho[1].markdown("**Nome**")
            cabecalho[2].markdown("**Data da cirurgia**")
            cabecalho[3].markdown("**Data do retorno**")
            cabecalho[4].markdown("**Status**")
            cabecalho[5].markdown("**Atendido?**")
            cabecalho[6].markdown("**Editar**")

            for i, row in df.iterrows():
                nome = row["Nome"]
                data_cirurgia = datetime.strptime(row["Data da cirurgia"], "%d/%m/%y")
                for j, dias in enumerate(dias_retornos):
                    data_retorno = data_cirurgia + timedelta(days=dias)
                    key_check = f"check_atendido_{i}_{j}"
                    atendido = st.session_state.get(key_check, False)
                    status = "🟢 Agendado" if atendido else "🟡 Pendente"
                    linha = st.columns([0.5, 2.5, 1.5, 1.5, 1.5, 1, 1])
                    if j == 0:
                        linha[0].write(f"{i+1}")
                        linha[1].write(nome)
                        linha[2].write(data_cirurgia.strftime("%d/%m/%y"))
                    else:
                        linha[0].write("")
                        linha[1].write("")
                        linha[2].write("")
                    linha[3].write(data_retorno.strftime("%d/%m/%Y"))
                    linha[4].write(status)
                    linha[5].checkbox("", key=key_check, value=atendido, label_visibility="collapsed")
                    if j == 0:
                        if linha[6].button("Editar", key=f"editar_{i}"):
                            st.session_state.paciente_editando = i
                            st.session_state.pagina = "editar_paciente"
                            st.rerun()
                    else:
                        linha[6].write("")
                    st.markdown("<hr style='margin:0.2rem 0;'>", unsafe_allow_html=True)

        elif modo == "Mobile 1":
            for i, row in df.iterrows():
                nome = row["Nome"]
                data_cirurgia = datetime.strptime(row["Data da cirurgia"], "%d/%m/%y")
                st.markdown(f"**Paciente {i+1}: {nome}**")
                st.write(f"Data da cirurgia: {data_cirurgia.strftime('%d/%m/%y')}")
                for j, dias in enumerate(dias_retornos):
                    data_retorno = data_cirurgia + timedelta(days=dias)
                    key_check = f"check_atendido_{i}_{j}"
                    atendido = st.session_state.get(key_check, False)
                    status = "🟢 Agendado" if atendido else "🟡 Pendente"
                    st.write(f"- Retorno {j+1}: {data_retorno.strftime('%d/%m/%Y')} | {status}")
                    st.checkbox("Atendido?", key=key_check)
                if st.button("Editar", key=f"editar_{i}"):
                    st.session_state.paciente_editando = i
                    st.session_state.pagina = "editar_paciente"
                    st.rerun()
                st.markdown("---")

        elif modo == "Mobile 2":
            for i, row in df.iterrows():
                nome = row["Nome"]
                data_cirurgia = row["Data da cirurgia"]
                proximo = row["Próximo retorno"]
                status = row["Status"]
                st.markdown(f"**{nome}**")
                st.write(f"Cirurgia: {data_cirurgia} | Retorno: {proximo} | Status: {status}")
                if st.button("Editar", key=f"editar_{i}"):
                    st.session_state.paciente_editando = i
                    st.session_state.pagina = "editar_paciente"
                    st.rerun()
                st.markdown("---")


# Página novo paciente
if st.session_state.pagina == "novo_paciente":
    st.subheader("Novo Paciente")
    nome = st.text_input("Nome do paciente")
    data_nascimento = st.date_input("Data de nascimento")
    telefone = st.text_input("Telefone (ex: +55 31999999999)", value="+55")
    data_cirurgia = st.date_input("Data da cirurgia", key="data_cirurgia_novo")

    st.markdown("### Retornos programados")
    dias_retornos = [7, 14, 21, 30, 60, 90, 180, 365]
    datas_retornos = []

    for i, dias in enumerate(dias_retornos):
        padrao = data_cirurgia + timedelta(days=dias)
        col1, col2 = st.columns([1, 3])
        key_check = f"check_retorno_{i}"
        key_data = f"data_retorno_{i}"
        if key_check not in st.session_state:
            st.session_state[key_check] = False
        marcado = col1.checkbox(f"Retorno {i+1}", value=st.session_state[key_check], key=key_check)
        if marcado:
            data_editada = col2.date_input(f"Data Retorno {i+1}", value=padrao, key=key_data)
            datas_retornos.append((True, data_editada))
        else:
            col2.date_input(f"Data Retorno {i+1}", value=padrao, key=key_data, disabled=True)
            datas_retornos.append((False, padrao))

    if st.button("Salvar"):
        proximo_retorno = next((data for marcado, data in datas_retornos if marcado), datas_retornos[0][1])
        novo = pd.DataFrame([{
            "Nome": nome,
            "Data da cirurgia": data_cirurgia.strftime("%d/%m/%y"),
            "Próximo retorno": proximo_retorno.strftime("%d/%m/%y"),
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


# Página editar paciente
if st.session_state.pagina == "editar_paciente":
    idx = st.session_state.paciente_editando
    paciente = st.session_state.pacientes.iloc[idx]
    st.subheader(f"Editar Paciente: {paciente['Nome']}")

    with st.form("form_edicao_paciente"):
        nome = st.text_input("Nome", value=paciente["Nome"])
        nascimento = st.date_input("Data de nascimento", value=datetime.strptime(paciente["Nascimento"], "%d/%m/%Y"))
        telefone = st.text_input("Telefone", value=paciente["Telefone"])
        data_cirurgia = st.date_input("Data da cirurgia", value=datetime.strptime(paciente["Data da cirurgia"], "%d/%m/%y"))
        retorno = st.date_input("Próximo retorno", value=datetime.strptime(paciente["Próximo retorno"], "%d/%m/%y"))
        alta = st.selectbox("Teve alta?", ["Não", "Sim"], index=0 if paciente["Alta"] == "Não" else 1)
        salvar = st.form_submit_button("Salvar alterações")

    if salvar:
        log_textos = []
        df = st.session_state.pacientes

        def log_alteracao(campo, antigo, novo):
            if antigo != novo:
                log_textos.append(f"{campo} de {antigo} para {novo}")
                df.at[idx, campo] = novo

        log_alteracao("Nome", paciente["Nome"], nome)
        log_alteracao("Nascimento", paciente["Nascimento"], nascimento.strftime("%d/%m/%Y"))
        log_alteracao("Telefone", paciente["Telefone"], telefone)
        log_alteracao("Data da cirurgia", paciente["Data da cirurgia"], data_cirurgia.strftime("%d/%m/%y"))
        log_alteracao("Próximo retorno", paciente["Próximo retorno"], retorno.strftime("%d/%m/%y"))
        log_alteracao("Alta", paciente["Alta"], alta)

        df.at[idx, "Status"] = status_cor(retorno)
        salvar_pacientes(df)
        st.session_state.pacientes = df

        if log_textos:
            agora = datetime.now().strftime("%d/%m/%y %H:%M")
            for log_item in log_textos:
                st.session_state.log.append(f"{agora} {st.session_state.usuario} modificou {log_item}")
            salvar_log(st.session_state.log)

        st.success("Alterações salvas.")
        st.session_state.pagina = "principal"
        st.rerun()

    if st.button("Cancelar"):
        st.session_state.pagina = "principal"
        st.rerun()

    st.markdown("### Histórico de edições:")
    nome_original = paciente["Nome"]
    for log in reversed(st.session_state.log):
        if nome_original in log:
            st.markdown(f"- {log}")
        elif f"modificou Nome de" in log and nome_original in log:
            st.markdown(f"- {log}")
    for log in reversed(st.session_state.log):
        if paciente["Nome"] in log:
            st.markdown(f"- {log}")
