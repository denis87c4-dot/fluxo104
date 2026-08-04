import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fluxo104", page_icon="💰", layout="wide")
st.title("💰 Fluxo104 - Gestão Financeira")
st.markdown("Acompanhamento financeiro em tempo real.")

if "lancamentos" not in st.session_state:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Descricao", "Categoria", "Conta", "Valor", "Data", "Parcelas"])

if "categorias" not in st.session_state:
    st.session_state.categorias = ["Food", "Transporte", "Moradia", "Lazer", "Outros"]

if "cartoes" not in st.session_state:
    st.session_state.cartoes = pd.DataFrame(columns=["Nome", "Fechamento", "Limite", "Vencimento"])

aba = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro (Form)", "Lançamentos", "Cartões", "Gerenciar Categorias"])

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
    st.subheader("Novo Registro")
    tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    descricao = st.text_input("Descrição", placeholder="Ex: Supermercado...")
    
    lista_cat_opcao = st.session_state.categorias + ["+ Incluir Nova Categoria..."]
    cat_escolhida = st.selectbox("Categoria", lista_cat_opcao)
    
    categoria_final = cat_escolhida
    if cat_escolhida == "+ Incluir Nova Categoria...":
        nova_cat_digitada = st.text_input("Digite o nome da nova categoria:")
        if nova_cat_digitada.strip() != "":
            categoria_final = nova_cat_digitada.strip()

    contas_base = ["Cash husband", "Nubank"]
    if not st.session_state.cartoes.empty:
        contas_base.extend(st.session_state.cartoes["Nome"].tolist())
    
    conta = st.selectbox("Conta / Cartão", contas_base)
    valor = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
    data = st.date_input("Data da Compra")
    parcelas = st.number_input("Parcelas", min_value=1, max_value=24, value=1)
    
    if st.button("Salvar Lançamento", type="primary"):
        if cat_escolhida == "+ Incluir Nova Categoria..." and categoria_final not in st.session_state.categorias:
            st.session_state.categorias.append(categoria_final)

        if descricao.strip() == "":
            st.warning("Preencha a descrição.")
        else:
            novo_dado = pd.DataFrame([{
                "Tipo": tipo, "Descricao": descricao, "Categoria": categoria_final, 
                "Conta": conta, "Valor": valor, "Data": str(data), "Parcelas": parcelas
            }])
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, novo_dado], ignore_index=True)
            st.success("Salvo com sucesso!")

elif aba == "Lançamentos":
    st.subheader("Lista de Lançamentos")
    df = st.session_state.lancamentos
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado.")

elif aba == "Cartões":
    st.subheader("💳 Cadastro de Cartões")
    with st.form("form_cartao"):
        nome_cartao = st.text_input("Nome do Cartão / Banco", placeholder="Ex: Visa...")
        dia_fechamento = st.number_input("Dia de Fechamento", min_value=1, max_value=31, value=10)
        limite_disponivel = st.number_input("Limite (R$)", min_value=0.0, format="%.2f")
        dia_pagamento = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=17)
        salvar_cartao = st.form_submit_button("Salvar Cartão")
        
        if salvar_cartao:
            if nome_cartao.strip() != "":
                novo_cartao = pd.DataFrame([{"Nome": nome_cartao, "Fechamento": dia_fechamento, "Limite": limite_disponivel, "Vencimento": dia_pagamento}])
                st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_cartao], ignore_index=True)
                st.success("Cartão salvo!")

    if not st.session_state.cartoes.empty:
        st.dataframe(st.session_state.cartoes, use_container_width=True)

elif aba == "Gerenciar Categorias":
    st.subheader("📂 Gerenciamento de Categorias")
    nova_cat = st.text_input("Nova Categoria")
    if st.button("Adicionar"):
        if nova_cat.strip() != "" and nova_cat not in st.session_state.categorias:
            st.session_state.categorias.append(nova_cat)
            st.success("Adicionada!")
    for cat in st.session_state.categorias:
        st.write(f"- {cat}")

