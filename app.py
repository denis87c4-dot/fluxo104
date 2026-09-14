import streamlit as st
import pandas as pd
import os
import io
import zipfile
from datetime import datetime

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(page_title="Fluxo104", page_icon="💰", layout="wide")
st.title("💰 Fluxo104 - Gestão Financeira Simplificada")

# ==================== PERSISTÊNCIA DE DADOS ====================
ARQUIVO_LANCAMENTOS = "lancamentos.csv"
ARQUIVO_CARTOES = "cartoes.csv"
ARQUIVO_CATEGORIAS = "categorias.csv"

if os.path.exists(ARQUIVO_LANCAMENTOS):
    st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
else:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo","Status","Descricao","Categoria","Conta","ContaDestino","Valor","Data","Parcela"])

if os.path.exists(ARQUIVO_CATEGORIAS):
    df_cat = pd.read_csv(ARQUIVO_CATEGORIAS)
    st.session_state.categorias = df_cat["Categoria"].tolist()
else:
    st.session_state.categorias = ["Food","Transporte","Moradia","Lazer","Transferência","Outros"]

if os.path.exists(ARQUIVO_CARTOES):
    st.session_state.cartoes = pd.read_csv(ARQUIVO_CARTOES)
else:
    st.session_state.cartoes = pd.DataFrame(columns=["Nome","Fechamento","Limite","Vencimento"])

# ==================== FUNÇÕES DE BACKUP ====================
def salvar_backup():
    st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
    pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
    st.success("💾 Backup realizado com sucesso!")

def salvar_backup_automatico():
    try:
        salvar_backup()
    except:
        pass

salvar_backup_automatico()

# ==================== NAVEGAÇÃO ====================
aba = st.sidebar.radio("Navegação", ["Lançamentos","Cadastro","Cartões","Backup"])

# ==================== LANÇAMENTOS ====================
if aba == "Lançamentos":
    st.subheader("📒 Registro de Lançamentos")
    st.dataframe(st.session_state.lancamentos, use_container_width=True)

# ==================== CADASTRO ====================
elif aba == "Cadastro":
    st.subheader("📝 Cadastro de Lançamentos")
    with st.form("form_lancamento"):
        tipo = st.selectbox("Tipo", ["Receita","Despesa","Transferência"])
        status = st.selectbox("Status", ["Efetivado","Budget"])
        descricao = st.text_input("Descrição")
        categoria = st.selectbox("Categoria", st.session_state.categorias)
        conta = st.text_input("Conta")
        conta_destino = st.text_input("Conta Destino")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data")
        parcela = st.text_input("Parcela")
        submit = st.form_submit_button("Salvar")
        if submit:
            novo = pd.DataFrame([[tipo,status,descricao,categoria,conta,conta_destino,valor,data,parcela]],
                                columns=st.session_state.lancamentos.columns)
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
            salvar_backup()
            st.success("✅ Lançamento cadastrado!")

# ==================== CARTÕES ====================
elif aba == "Cartões":
    st.subheader("💳 Gerenciamento de Cartões")
    st.dataframe(st.session_state.cartoes, use_container_width=True)

# ==================== BACKUP ====================
elif aba == "Backup":
    st.subheader("🔐 Central de Backup")
    if st.button("💾 Salvar Backup Local"):
        salvar_backup()

    arquivos_para_backup = [ARQUIVO_LANCAMENTOS, ARQUIVO_CARTOES, ARQUIVO_CATEGORIAS]
    arquivos_existentes = [f for f in arquivos_para_backup if os.path.exists(f)]
    if arquivos_existentes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for arq in arquivos_existentes:
                zip_file.write(arq)
        zip_buffer.seek(0)
        st.download_button(
            label="📥 Baixar Backup Completo (.zip)",
            data=zip_buffer,
            file_name=f"backup_fluxo104_{datetime.today().strftime('%Y-%m-%d')}.zip",
            mime="application/zip"
        )

    st.file_uploader("📤 Restaurar Backup (ZIP)", type="zip")
