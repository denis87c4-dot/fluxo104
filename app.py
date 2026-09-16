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
    st.session_state.categorias = ["Alimentação", "Transporte", "Moradia", "Lazer", "Transferência", "Outros"]

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
    
    if st.session_state.lancamentos.empty:
        st.info("Nenhum lançamento cadastrado ainda. Vá na aba **Cadastro** para adicionar novos registros.")
    else:
        df_exibicao = st.session_state.lancamentos.copy()
        df_exibicao["Valor"] = pd.to_numeric(df_exibicao["Valor"], errors="coerce").fillna(0.0)
        
        # Filtros rápidos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos"] + list(df_exibicao["Tipo"].dropna().unique()))
        with col_f2:
            filtro_cat = st.selectbox("Filtrar por Categoria", ["Todas"] + list(df_exibicao["Categoria"].dropna().unique()))
            
        if filtro_tipo != "Todos":
            df_exibicao = df_exibicao[df_exibicao["Tipo"] == filtro_tipo]
        if filtro_cat != "Todas":
            df_exibicao = df_exibicao[df_exibicao["Categoria"] == filtro_cat]

        df_estilizado = df_exibicao.style.map(colorir_negativos, subset=["Valor"]).format(formatar_moeda_br, subset=["Valor"])
        st.dataframe(df_estilizado, use_container_width=True)

# ==================== CADASTRO ====================
elif aba == "Cadastro":
    st.subheader("📝 Cadastro de Lançamentos")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita", "Transferência"])
            status = st.selectbox("Status", ["Pago / Realizado", "Pendente"])
            descricao = st.text_input("Descrição")
            categoria = st.selectbox("Categoria", st.session_state.categorias)
            conta = st.text_input("Conta / Carteira", value="Conta Principal")
            conta_destino = st.text_input("Conta Destino (Apenas para Transferências)", value="")
            
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            data = st.date_input("Data", value=datetime.today())
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Boleto", "Outros"])
            parcela = st.text_input("Parcela (ex: 1/12)", value="1/1")
            regra_parcelamento = st.selectbox("Regra de Parcelamento", ["Única", "Parcelado Mensal", "Recorrente Mensal"])
            observacoes = st.text_area("Observações")
            
        submitted = st.form_submit_button("Salvar Lançamento")
        
        if submitted:
            if not descricao.strip():
                st.warning("Por favor, preencha a descrição do lançamento.")
            else:
                # Se for despesa, converte o valor para negativo para consistência financeira
                valor_final = -abs(valor) if tipo == "Despesa" else abs(valor)
                if tipo == "Transferência":
                    valor_final = abs(valor) # Transferência neutra ou conforme sua regra
                
                novo_registro = {
                    "Tipo": tipo,
                    "Status": status,
                    "Descricao": descricao,
                    "Categoria": categoria,
                    "Conta": conta,
                    "ContaDestino": conta_destino if tipo == "Transferência" else "",
                    "Valor": valor_final,
                    "Data": str(data),
                    "Parcela": parcela,
                    "RegraParcelamento": regra_parcelamento,
                    "FormaPagamento": forma_pagamento,
                    "Observacoes": observacoes
                }
                
                novo_df = pd.DataFrame([novo_registro])
                st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo_df], ignore_index=True)
                salvar_backup(mostrar_aviso=False)
                st.success("✅ Lançamento cadastrado com sucesso!")

# ==================== BACKUP ====================
elif aba == "Backup":
    st.subheader("💾 Gerenciamento de Backup e Dados")
    
    col_ b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.markdown("### Exportar Dados")
        st.write("Baixe todos os seus lançamentos e categorias em formato compactado (.zip).")
        
        if not st.session_state.lancamentos.empty:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zf:
                zf.writestr("lancamentos.csv", st.session_state.lancamentos.to_csv(index=False))
                zf.writestr("categorias.csv", pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(index=False))
            buffer.seek(0)
            
            st.download_button(
                label="📥 Baixar Backup Completo (ZIP)",
                data=buffer,
                file_name=f"backup_fluxo104_{datetime.today().strftime('%Y-%m-%d')}.zip",
                mime="application/zip"
            )
        else:
            st.info("Não há dados suficientes para exportar.")
            
    with col_b2:
        st.markdown("### Importar Dados")
        st.write("Restaure seus dados a partir de um arquivo de backup ZIP gerado anteriormente.")
        
        arquivo_upload = st.file_uploader("Enviar arquivo ZIP de backup", type=["zip"])
        if arquivo_upload is not None:
            try:
                with zipfile.ZipFile(arquivo_upload, "r") as zf:
                    if "lancamentos.csv" in zf.namelist():
                        with zf.open("lancamentos.csv") as f:
                            st.session_state.lancamentos = pd.read_csv(f)
                    if "categorias.csv" in zf.namelist():
                        with zf.open("categorias.csv") as f:
                            df_cat_imp = pd.read_csv(f)
                            st.session_state.categorias = df_cat_imp["Categoria"].tolist()
                salvar_backup(mostrar_aviso=False)
                st.success("🔄 Dados restaurados com sucesso! Atualize a página se necessário.")
            except Exception as e:
                st.error(f"Erro ao importar o arquivo: {e}")
