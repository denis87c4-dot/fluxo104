import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fluxo104", page_icon="💰", layout="wide")
st.title("💰 Fluxo104 - Gestão Financeira")
st.markdown("Acompanhamento financeiro em tempo real.")

aba = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro (Form)", "Lançamentos"])

if "lancamentos" not in st.session_state:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Descricao", "Categoria", "Conta", "Valor", "Data", "Parcelas"])

if aba == "Dashboard":
    st.subheader("Visão Geral")
    df = st.session_state.lancamentos
    total_receitas = df[df["Tipo"] == "Receita"]["Valor"].sum() if not df.empty else 0.0
    total_despesas = df[df["Tipo"] == "Despesa"]["Valor"].sum() if not df.empty else 0.0
    saldo = total_receitas - total_despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo em Caixa", f"R$ {saldo:,.2f}")
    col2.metric("Receitas do Mês", f"R$ {total_receitas:,.2f}")
    col3.metric("Despesas do Mês", f"R$ {total_despesas:,.2f}")

elif aba == "Cadastro (Form)":
    st.subheader("Novo Registro (Form)")
    with st.form("form_cadastro"):
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        status = st.selectbox("Status / Fase", ["Budget", "Efetivado"])
        descricao = st.text_input("Descrição", placeholder="Ex: Supermercado...")
        categoria = st.selectbox("Categoria", ["Food", "Transporte", "Outros"])
        conta = st.selectbox("Conta / Cartão", ["Cash husband", "Nubank"])
        valor = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
        data = st.date_input("Data da Compra")
        parcelas = st.number_input("Parcelas", min_value=1, max_value=24, value=1)
        enviado = st.form_submit_button("Salvar Lançamento")

        if enviado:
            novo_dado = pd.DataFrame([{"Tipo": tipo, "Descricao": descricao, "Categoria": categoria, "Conta": conta, "Valor": valor, "Data": str(data), "Parcelas": parcelas}])
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo_dado], ignore_index=True)
            st.success("Lançamento salvo com sucesso!")

elif aba == "Lançamentos":
    st.subheader("Lista de Lançamentos")
    df = st.session_state.lancamentos
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado.")
