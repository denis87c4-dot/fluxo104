import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Fluxo104", page_icon="💰", layout="wide")
st.title("💰 Fluxo104 - Gestão Financeira")
st.markdown("Acompanhamento financeiro em tempo real.")

if "lancamentos" not in st.session_state:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Status", "Descricao", "Categoria", "Conta", "Valor", "Data", "Parcela"])

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
    st.subheader("Novo Registro (Form)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    with col_b:
        status = st.selectbox("Status / Fase", ["Budget", "Efetivado"])
        
    descricao = st.text_input("Descrição", placeholder="Ex: Gas, Supermercado, Debts...")
    
    # Categorias com opção de inclusão dinâmica
    lista_cat_opcao = st.session_state.categorias + ["+ Incluir Nova Categoria..."]
    cat_escolhida = st.selectbox("Categoria", lista_cat_opcao)
    categoria_final = cat_escolhida
    if cat_escolhida == "+ Incluir Nova Categoria...":
        nova_cat_digitada = st.text_input("Digite o nome da nova categoria:")
        if nova_cat_digitada.strip() != "":
            categoria_final = nova_cat_digitada.strip()

    # Contas / Cartões com opção dinâmica
    contas_base = ["Cash husband", "Nubank"]
    if not st.session_state.cartoes.empty:
        contas_base.extend(st.session_state.cartoes["Nome"].tolist())
    lista_conta_opcao = contas_base + ["+ Incluir Novo Cartão/Conta..."]
    conta_escolhida = st.selectbox("Account (Conta / Cartão)", lista_conta_opcao)
    conta_final = conta_escolhida
    if conta_escolhida == "+ Incluir Novo Cartão/Conta...":
        novo_c_digitado = st.text_input("Digite o nome do novo Cartão / Conta:")
        if novo_c_digitado.strip() != "":
            conta_final = novo_c_digitado.strip()
            novo_c_df = pd.DataFrame([{"Nome": conta_final, "Fechamento": 10, "Limite": 0.0, "Vencimento": 17}])
            st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_c_df], ignore_index=True)

    valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
    data_compra = st.date_input("Data da Compra", value=datetime.today())
    
    # Campos baseados no seu print do CodePen
    parcelas = st.number_input("Installments (Parcelas)", min_value=1, max_value=48, value=1)
    frequencia = st.selectbox("Frequência", ["Mensal", "Quinzenal", "Anual", "Única"])
    modo_valor = st.selectbox("Modo de Valor", ["Dividir Total", "Replicar Integral"])
    
    if st.button("Salvar Lançamento", type="primary"):
        if cat_escolhida == "+ Incluir Nova Categoria..." and categoria_final not in st.session_state.categorias:
            st.session_state.categorias.append(categoria_final)

        if descricao.strip() == "":
            st.warning("Preencha a descrição.")
        else:
            novos_registros = []
            
            for i in range(parcelas):
                # Calcula a data de cada parcela baseada na frequência
                if frequencia == "Mensal":
                    data_parcela = data_compra + relativedelta(months=i)
                elif frequencia == "Quinzenal":
                    data_parcela = data_compra + relativedelta(weeks=2*i)
                elif frequencia == "Anual":
                    data_parcela = data_compra + relativedelta(years=i)
                else:
                    data_parcela = data_compra

                # Define o valor de acordo com o modo escolhido
                if modo_valor == "Dividir Total" and parcelas > 0:
                    valor_parcela = valor_total / parcelas
                else:
                    valor_parcela = valor_total

                desc_formatada = f"{descricao} ({i+1}/{parcelas})" if parcelas > 1 else descricao

                novos_registros.append({
                    "Tipo": tipo,
                    "Status": status,
                    "Descricao": desc_formatada,
                    "Categoria": categoria_final,
                    "Conta": conta_final,
                    "Valor": round(valor_parcela, 2),
                    "Data": str(data_parcela),
                    "Parcela": f"{i+1}/{parcelas}"
                })

            df_novo = pd.DataFrame(novos_registros)
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, df_novo], ignore_index=True)
            st.success(f"{parcelas} lançamento(s) gerado(s) com sucesso!")

elif aba == "Lançamentos":
    st.subheader("Lista de Lançamentos")
    df = st.session_state.lancamentos
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado.")

elif aba == "Cartões":
    st.subheader("💳 Cadastro de Cartões e Contas")
    with st.form("form_cartao"):
        nome_cartao = st.text_input("Nome do Cartão / Banco", placeholder="Ex: Visa Itaú...")
        dia_fechamento = st.number_input("Dia de Fechamento da Fatura", min_value=1, max_value=31, value=10)
        limite_disponivel = st.number_input("Limite Disponível (R$)", min_value=0.0, format="%.2f")
        dia_pagamento = st.number_input("Dia de Vencimento / Pagamento", min_value=1, max_value=31, value=17)
        salvar_cartao = st.form_submit_button("Salvar Cartão")
        
        if salvar_cartao:
            if nome_cartao.strip() != "":
                novo_cartao = pd.DataFrame([{"Nome": nome_cartao, "Fechamento": dia_fechamento, "Limite": limite_disponivel, "Vencimento": dia_pagamento}])
                st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_cartao], ignore_index=True)
                st.success("Cartão salvo com sucesso!")

    if not st.session_state.cartoes.empty:
        st.dataframe(st.session_state.cartoes, use_container_width=True)

elif aba == "Gerenciar Categorias":
    st.subheader("📂 Gerenciamento de Categorias")
    nova_cat = st.text_input("Nome da Nova Categoria")
    if st.button("Adicionar Categoria"):
        if nova_cat.strip() != "" and nova_cat not in st.session_state.categorias:
            st.session_state.categorias.append(nova_cat)
            st.success("Categoria adicionada!")
    for cat in st.session_state.categorias:
        st.write(f"- {cat}")
