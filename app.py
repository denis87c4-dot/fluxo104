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

def colorir_negativos(val):
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
        df_estilizado = df_exibicao.style.map(colorir_negativos, subset=["Valor"]).format(formatar_moeda_br, subset=["Valor"])
        st.dataframe(df_estilizado, use_container_width=True)
    else:
        st.dataframe(df_exibicao, use_container_width=True)

# ==================== CADASTRO ====================
elif aba == "Cadastro":
    st.subheader("📝 Cadastro de Lançamentos")
    with st.form("form_lancamento"):
        tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Transferência"])
        status = st.selectbox("Status", ["Efetivado", "Budget"])
        descricao = st.text_input("Descrição *")

        nova_categoria = st.text_input("Adicionar nova categoria (opcional)")
        categoria = st.selectbox("Categoria", st.session_state.categorias)
        if nova_categoria:
            if nova_categoria not in st.session_state.categorias:
                st.session_state.categorias.append(nova_categoria)
                salvar_backup(mostrar_aviso=True)
                st.success(f"✅ Nova categoria adicionada: {nova_categoria}")
            categoria = nova_categoria

        if not st.session_state.lancamentos.empty and "Conta" in st.session_state.lancamentos.columns:
            contas_existentes = st.session_state.lancamentos["Conta"].dropna().unique().tolist()
        else:
            contas_existentes = []
            
        conta = st.selectbox("Conta", contas_existentes + ["Adicionar nova"])
        if conta == "Adicionar nova":
            conta = st.text_input("Nova Conta")

        conta_destino = st.text_input("Conta Destino")
        valor = st.number_input("Valor (R$) *", min_value=0.0, step=0.01)
        data = st.date_input("Data *")
        num_parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
        
        regra_parcelamento = st.selectbox("Forma de Parcelamento", ["Replicar Integralmente", "Parcelado"])
        forma_pagamento = st.selectbox("Forma de Pagamento", ["Conta Corrente", "Cartão", "Pix", "Outros"])
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
                        str(tipo), str(status), str(descricao), str(categoria), str(conta), str(conta_destino),
                        float(valor_parcela), data_parcela.strftime("%Y-%m-%d"), str(f"{i+1}/{num_parcelas}"), 
                        str(regra_parcelamento), str(forma_pagamento), str(observacoes)
                    ])

                novo = pd.DataFrame(registros, columns=colunas_lancamentos)
                
                if st.session_state.lancamentos.empty:
                    st.session_state.lancamentos = novo
                else:
                    st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo], ignore_index=True)
                
                salvar_backup(mostrar_aviso=True)
                st.success(f"✅ {num_parcelas} lançamento(s) cadastrado(s) com sucesso!")

# ==================== CARTÕES ====================
elif aba == "Cartões":
    st.subheader("💳 Gerenciamento de Cartões")
    df_cartoes_exib = st.session_state.cartoes.copy()
    if not df_cartoes_exib.empty and "Limite" in df_cartoes_exib.columns:
        df_cartoes_exib["Limite"] = pd.to_numeric(df_cartoes_exib["Limite"], errors="coerce").fillna(0.0)
        df_cartoes_estilizado = df_cartoes_exib.style.map(colorir_negativos, subset=["Limite"]).format(formatar_moeda_br, subset=["Limite"])
        st.dataframe(df_cartoes_estilizado, use_container_width=True)
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
            st.error(f
