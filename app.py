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
ARQUIVO_CATEGORIAS = "categorias.csv"

colunas_lancamentos = [
    "Tipo", "Status", "Descricao", "Categoria", "Conta", "ContaDestino", 
    "Valor", "Data", "Parcela", "RegraParcelamento", "FormaPagamento", "Observacoes"
]

if os.path.exists(ARQUIVO_LANCAMENTOS):
    st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
else:
    st.session_state.lancamentos = pd.DataFrame(columns=colunas_lancamentos)

if os.path.exists(ARQUIVO_CATEGORIAS):
    df_cat = pd.read_csv(ARQUIVO_CATEGORIAS)
    st.session_state.categorias = df_cat["Categoria"].tolist()
else:
    st.session_state.categorias = ["Food", "Transporte", "Moradia", "Lazer", "Transferência", "Outros"]

# ==================== FUNÇÕES DE BACKUP ====================
def salvar_backup(mostrar_aviso=True):
    st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
    pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
    if mostrar_aviso:
        st.success("💾 Backup realizado com sucesso!")

def salvar_backup_automatico():
    try:
        salvar_backup(mostrar_aviso=False)
    except:
        pass

salvar_backup_automatico()

# ==================== FUNÇÕES DE FORMATAÇÃO ====================
def formatar_moeda_br(val):
    if pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def colorir_negativos(val):
    if isinstance(val, (int, float)) and val < 0:
        return "color: #ff4b4b; font-weight: bold;"
    return ""

# ==================== NAVEGAÇÃO ====================
aba = st.sidebar.radio("Navegação", ["Lançamentos", "Cadastro", "Backup"])

# ==================== LANÇAMENTOS ====================
if aba == "Lançamentos":
    st.subheader("📒 Registro de Lançamentos")
    df_exibicao = st.session_state.lancamentos.copy()
    
    if not df_exibicao.empty and "Valor" in df_exibicao.columns:
        df_exibicao["Valor"] = pd.to_numeric(df_exibicao["Valor"], errors="coerce").fillna(0.0)
        df_estilizado = df_exibicao.style.map(colorir_negativos, subset=["Valor"]).format(formatar_moeda_br, subset=["Valor"])
        st.dataframe(df_estilizado, use_container_width=True)
    else:
        st.dataframe(df_exibicao, use_container_width=True)

# ==================== CADASTRO ====================
elif aba == "Cadastro":
    st.subheader("📝 Cadastro de Lançamentos")
    with st.form
