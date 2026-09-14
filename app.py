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
    st.session_state.lancamentos = pd.DataFrame(columns=[
        "Tipo","Status","Descricao","Categoria","Conta","ContaDestino","Valor","Data","Parcela",
        "RegraParcelamento","FormaPagamento","Observacoes"
    ])

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
aba = st.sidebar.radio("Navegação", ["Lançamentos","Cadastro","Cartões","Backup","Financial Summary"])

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
        descricao = st.text_input("Descrição *")

        # 🔽 Categoria com opção de adicionar nova
        nova_categoria = st.text_input("Adicionar nova categoria (opcional)")
        categoria = st.selectbox("Categoria", st.session_state.categorias)
        if nova_categoria:
            if nova_categoria not in st.session_state.categorias:
                st.session_state.categorias.append(nova_categoria)
                salvar_backup()
                st.success(f"✅ Nova categoria adicionada: {nova_categoria}")
            categoria = nova_categoria

        # 🔽 Dropdown inteligente para contas
        contas_existentes = st.session_state.lancamentos["Conta"].dropna().unique().tolist()
        conta = st.selectbox("Conta", contas_existentes + ["Adicionar nova"])
        if conta == "Adicionar nova":
            conta = st.text_input("Nova Conta")

        conta_destino = st.text_input("Conta Destino")
        valor = st.number_input("Valor (R$) *", min_value=0.0, step=0.01)
        data = st.date_input("Data *")
        num_parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
        
        regra_parcelamento = st.selectbox("Forma de Parcelamento", ["Replicar Integralmente", "Parcelado"])
        forma_pagamento = st.selectbox("Forma de Pagamento", ["Conta Corrente","Cartão","Pix","Outros"])
        observacoes = st.text_area("Observações (opcional)")

        submit = st.form_submit_button("Salvar")
        if submit:
            if descricao.strip() == "" or valor <= 0:
                st.error("⚠️ Preencha os campos obrigatórios (Descrição e Valor).")
            else:
                registros = []
                for i in range(num_parcelas):
                    if regra_parcelamento == "Parcelado":
                        valor_parcela = valor / num_parcelas
                    else:
                        valor_parcela = valor

                    data_parcela = pd.to_datetime(data) + pd.DateOffset(months=i)
                    registros.append([
                        tipo, status, descricao, categoria, conta, conta_destino,
                        float(valor_parcela), data_parcela.strftime("%Y-%m-%d"), f"{i+1}/{num_parcelas}", regra_parcelamento, forma_pagamento, observacoes
                    ])

                novo = pd.DataFrame(registros, columns=st.session_state.lancamentos.columns)
                st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
                salvar_backup()
                st.success(f"✅ {num_parcelas} lançamento(s) cadastrado(s) com sucesso!")

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

    arquivo_upload = st.file_uploader("📤 Restaurar Backup (ZIP)", type="zip")
    if arquivo_upload is not None:
        try:
            with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
                zip_ref.extractall(".")
            st.success("✅ Dados restaurados com sucesso! Recarregue a página.")
            if st.button("🔄 Recarregar App"):
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao restaurar arquivo: {e}")

# ==================== FINANCIAL SUMMARY ====================
elif aba == "Financial Summary":
    st.subheader("📊 Financial Summary")
    st.markdown("Consolidated view of **Income**, **Expenses (including cards)**, **Cash Flow**, and **Cumulative Balance**.")

    df = st.session_state.lancamentos
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        # Filters
        status_sel = st.selectbox("Filter by Status", ["All","Efetivado","Budget"])
        start_date = st.date_input("Start Date", df["Data"].min().date())
        end_date = st.date_input("End Date", df["Data"].max().date())

        df_filtrado = df[(df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)]
        if status_sel != "All":
            df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]

        # Consolidation
        df_filtrado["Income"] = df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"]=="Receita" else 0.0, axis=1)
        df_filtrado["Expense"] = df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"]=="Despesa" else 0.0, axis=1)

        pivot = df_filtrado.pivot_table(
            index="AnoMes",
            values=["Income","Expense"],
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        pivot = pivot.sort_values("AnoMes").reset_index(drop=True)
        pivot["Cash Flow"] = pivot["Income"] - pivot["Expense"]
        pivot["Cumulative"] = pivot["Cash Flow"].cumsum()

        pivot["Month"] = pd.PeriodIndex(pivot["AnoMes"], freq="M").strftime("%m/%Y")

        st.dataframe(pivot, use_container_width=True)
