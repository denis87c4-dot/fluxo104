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

if os.path.exists(ARQUIVO_CARTOES):
    st.session_state.cartoes = pd.read_csv(ARQUIVO_CARTOES)
else:
    st.session_state.cartoes = pd.DataFrame(columns=["Nome", "Fechamento", "Limite", "Vencimento"])

# ==================== FUNÇÕES DE BACKUP ====================
def salvar_backup(mostrar_aviso=True):
    st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
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

def colorir_negativos_styler(val):
    if isinstance(val, (int, float)) and val < 0:
        return "color: #ff4b4b; font-weight: bold;"
    return ""

# ==================== NAVEGAÇÃO ====================
aba = st.sidebar.radio("Navegação", ["Lançamentos", "Cadastro", "Cartões", "Backup", "Financial Summary"])

# ==================== LANÇAMENTOS ====================
if aba == "Lançamentos":
    st.subheader("📒 Registro de Lançamentos")
    df_exibicao = st.session_state.lancamentos.copy()
    
    if not df_exibicao.empty and "Valor" in df_exibicao.columns:
        df_exibicao["Valor"] = pd.to_numeric(df_exibicao["Valor"], errors="coerce").fillna(0.0)
        df_estilizado = df_exibicao.style.map(
            colorir_negativos_styler, subset=["Valor"]
        ).format(
            formatar_moeda_br, subset=["Valor"]
        )
        # ✅ Usar st.write para aplicar estilos
        st.write(df_estilizado)
    else:
        st.dataframe(df_exibicao, use_container_width=True)

# ==================== CARTÕES ====================
elif aba == "Cartões":
    st.subheader("💳 Gerenciamento de Cartões")
    df_cartoes_exib = st.session_state.cartoes.copy()
    if not df_cartoes_exib.empty and "Limite" in df_cartoes_exib.columns:
        df_cartoes_exib["Limite"] = pd.to_numeric(df_cartoes_exib["Limite"], errors="coerce").fillna(0.0)
        df_cartoes_estilizado = df_cartoes_exib.style.map(
            colorir_negativos_styler, subset=["Limite"]
        ).format(
            formatar_moeda_br, subset=["Limite"]
        )
        st.write(df_cartoes_estilizado)
    else:
        st.dataframe(df_cartoes_exib, use_container_width=True)

# ==================== BACKUP ====================
elif aba == "Backup":
    st.subheader("🔐 Central de Backup")
    if st.button("💾 Salvar Backup Local"):
        salvar_backup(mostrar_aviso=True)

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

    arquivo_upload = st.file_uploader("📤 Restaurar Backup (ZIP)", type="zip")
    if arquivo_upload is not None:
        try:
            with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
                zip_ref.extractall(".")
            st.success("✅ Dados restaurados com sucesso! Recarregue a página.")
            if st.button("🔄 Recarregar App"):
                st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao restaurar arquivo: {e}")

# ==================== FINANCIAL SUMMARY ====================
elif aba == "Financial Summary":
    st.subheader("📊 Financial Summary")
    st.markdown("Consolidated view of **Income**, **Expenses (including cards)**, **Cash Flow**, and **Cumulative Balance**.")

    df = st.session_state.lancamentos
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        status_sel = st.selectbox("Filter by Status", ["All", "Efetivado", "Budget"])
        start_date = st.date_input("Start Date", df["Data"].min().date() if not df["Data"].isna().all() else datetime.today().date())
        end_date = st.date_input("End Date", df["Data"].max().date() if not df["Data"].isna().all() else datetime.today().date())

        df_filtrado = df[(df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)]
        if status_sel != "All":
            df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]

        df_filtrado["Income"] = df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)
        df_filtrado["Expense"] = df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" else 0.0, axis=1)

        pivot = df_filtrado.pivot_table(
            index="AnoMes",
            values=["Income", "Expense"],
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        pivot = pivot.sort_values("AnoMes").reset_index(drop=True)
        
        pivot["Cash Flow"] = pd.to_numeric(pivot["Income"] - pivot["Expense"], errors="coerce").fillna(0.0)
        pivot["Cumulative"] = pd.to_numeric(pivot["Cash Flow"].cumsum(), errors="coerce").fillna(0.0)

        pivot["Month"] = pd.PeriodIndex(pivot["AnoMes"], freq="M").strftime("%m/%Y")

        pivot_exibicao = pivot[["Month", "Income", "Expense", "Cash Flow", "Cumulative"]]
        
        colunas_financeiras = ["Income", "Expense", "Cash Flow", "Cumulative"]
        
        pivot_estilizado = pivot_exibicao.style.map(
            colorir_negativos_styler, subset=colunas_financeiras
        ).format(
            formatar_moeda_br, subset=colunas_financeiras
        )

        st.write(pivot_estilizado)
    else:
        st.info("Nenhum lançamento cadastrado ainda.")
