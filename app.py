import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Fluxo104", page_icon="💰", layout="wide")
st.title("💰 Fluxo104 - Gestão Financeira")
st.markdown("Acompanhamento financeiro em tempo real com salvamento automático.")

# ==================== PERSISTÊNCIA DE DADOS (CSV) ====================
ARQUIVO_LANCAMENTOS = "lancamentos.csv"
ARQUIVO_CARTOES = "cartoes.csv"
ARQUIVO_CATEGORIAS = "categorias.csv"

if os.path.exists(ARQUIVO_LANCAMENTOS):
    st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
else:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Status", "Descricao", "Categoria", "Conta", "Valor", "Data", "Parcela"])

if os.path.exists(ARQUIVO_CATEGORIAS):
    df_cat = pd.read_csv(ARQUIVO_CATEGORIAS)
    st.session_state.categorias = df_cat["Categoria"].tolist()
else:
    st.session_state.categorias = ["Food", "Transporte", "Moradia", "Lazer", "Outros"]

if os.path.exists(ARQUIVO_CARTOES):
    st.session_state.cartoes = pd.read_csv(ARQUIVO_CARTOES)
else:
    st.session_state.cartoes = pd.DataFrame(columns=["Nome", "Fechamento", "Limite", "Vencimento"])

# Menu lateral
aba = st.sidebar.radio("Navegação", ["Dashboard", "Cadastro (Form)", "Lançamentos", "Cartões", "Gerenciar Categorias"])

if aba == "Dashboard":
    st.subheader("📊 Dashboard Financeiro")
    
    df = st.session_state.lancamentos
    
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        
        receitas_mes = df[(df["Tipo"] == "Receita") & (df["Status"] == "Efetivado")]["Valor"].sum()
        despesas_mes = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Efetivado")]["Valor"].sum()
        budget_despesas = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Budget")]["Valor"].sum()
        budget_receitas = df[(df["Tipo"] == "Receita") & (df["Status"] == "Budget")]["Valor"].sum()
        
        hoje_dt = pd.to_datetime(datetime.today().date())
        despesas_vencidas = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Budget") & (df["Data"] < hoje_dt)]["Valor"].sum()
    else:
        receitas_mes = 0.0
        despesas_mes = 0.0
        budget_despesas = 0.0
        budget_receitas = 0.0
        despesas_vencidas = 0.0

    # Cards de Métricas Principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📈 RECEITAS DO MÊS", f"R$ {receitas_mes:,.2f}", delta="Total efetivado")
    with col2:
        st.metric("📉 DESPESAS DO MÊS", f"R$ {despesas_mes:,.2f}", delta="Total efetivado")
    with col3:
        st.metric("⚠️ DESPESAS VENCIDAS", f"R$ {despesas_vencidas:,.2f}", delta="Budget pendente anterior")

    st.markdown("---")

    # Comprometimento do Budget
    st.markdown("### 🎯 Comprometimento da Renda (Budget)")
    renda_base = budget_receitas if budget_receitas > 0 else 1.0
    comprometimento = min((budget_despesas / renda_base) * 100, 100.0)
    
    col_b1, col_b2 = st.columns(2)
    col_b1.write(f"**Renda do Mês (Budget Income):** R$ {budget_receitas:,.2f}")
    col_b2.write(f"**Total Planejado (Budget Expenses):** R$ {budget_despesas:,.2f}")
    
    st.progress(int(comprometimento))
    st.write(f"Comprometimento do Budget: **{comprometimento:.1f}%**")

    st.markdown("---")

    # 1. CASH FLOW POR ACCOUNT (Considerando Entry / Efetivado e geral)
    st.markdown("### 🏛️ Cash Flow por Account (Mês Atual)")
    st.markdown("Saldo detalhado por conta considerando entradas e saídas.")
    if not df.empty:
        # Agrupa por conta considerando o tipo (Receita soma, Despesa subtrai ou exibe o fluxo)
        cash_flow = df.groupby(["Conta", "Tipo"])["Valor"].sum().unstack(fill_value=0.0)
        if "Receita" not in cash_flow.columns: cash_flow["Receita"] = 0.0
        if "Despesa" not in cash_flow.columns: cash_flow["Despesa"] = 0.0
        cash_flow["Saldo Líquido"] = cash_flow["Receita"] - cash_flow["Despesa"]
        
        st.dataframe(cash_flow[["Receita", "Despesa", "Saldo Líquido"]], use_container_width=True)
        st.bar_chart(cash_flow["Saldo Líquido"])
    else:
        st.info("Nenhuma conta movimentada neste período.")

    st.markdown("---")

    # 2. BUDGET: INCOME X EXPENSES (Comparativo Mensal - Somente Budget)
    st.markdown("### 📊 Budget: Income x Expenses (Comparativo Mensal)")
    st.markdown("Visão planejada mês a mês entre Budget de Receitas e Despesas.")
    
    if not df.empty and not df[df["Status"] == "Budget"].empty:
        df_budget = df[df["Status"] == "Budget"].copy()
        df_budget["AnoMes"] = df_budget["Data"].dt.to_period("M").astype(str)
        
        budget_mensal = df_budget.pivot_table(index="AnoMes", columns="Tipo", values="Valor", aggfunc="sum", fill_value=0.0)
        if "Receita" not in budget_mensal.columns: budget_mensal["Receita"] = 0.0
        if "Despesa" not in budget_mensal.columns: budget_mensal["Despesa"] = 0.0
        
        budget_mensal = budget_mensal.rename(columns={"Receita": "Budget Receitas", "Despesa": "Budget Despesas"})
        
        st.dataframe(budget_mensal, use_container_width=True)
        # Gráfico colorido comparativo
        st.bar_chart(budget_mensal[["Budget Receitas", "Budget Despesas"]])
    else:
        st.info("Nenhum registro de Budget cadastrado para o comparativo mensal.")

    st.markdown("---")

    # Maiores Despesas por Categoria
    st.markdown("### 🔥 Maiores Despesas por Categoria")
    if not df.empty and not df[df["Tipo"] == "Despesa"].empty:
        df_despesas = df[df["Tipo"] == "Despesa"]
        cat_grouped = df_despesas.groupby("Categoria")["Valor"].sum()
        st.bar_chart(cat_grouped)
    else:
        st.info("Nenhuma despesa registrada.")

    st.markdown("---")

    # Últimas Transações Recentes
    st.markdown("### 🕒 Últimas Transações Recentes")
    if not df.empty:
        st.dataframe(df.sort_values(by="Data", ascending=False).head(5), use_container_width=True)
    else:
        st.info("Nenhuma transação recente.")

elif aba == "Cadastro (Form)":
    st.subheader("Novo Registro (Form)")
    st.markdown("Preencha os campos abaixo para cadastrar uma nova movimentação.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    with col_b:
        status = st.selectbox("Status / Fase", ["Budget", "Efetivado"])
        
    descricao = st.text_input("Descrição", placeholder="Ex: Gas, Supermercado, Debts...")
    
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
    lista_conta_opcao = contas_base + ["+ Incluir Novo Cartão/Conta..."]
    conta_escolhida = st.selectbox("Account (Conta / Cartão)", lista_conta_opcao)
    conta_final = conta_escolhida
    if conta_escolhida == "+ Incluir Novo Cartão/Conta...":
        novo_c_digitado = st.text_input("Digite o nome do novo Cartão / Conta:")
        if novo_c_digitado.strip() != "":
            conta_final = novo_c_digitado.strip()
            novo_c_df = pd.DataFrame([{"Nome": conta_final, "Fechamento": 10, "Limite": 0.0, "Vencimento": 17}])
            st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_c_df], ignore_index=True)
            st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)

    valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
    data_compra = st.date_input("Data da Compra", value=datetime.today())
    
    parcelas = st.number_input("Installments (Parcelas)", min_value=1, max_value=48, value=1)
    frequencia = st.selectbox("Frequência", ["Mensal", "Quinzenal", "Anual", "Única"])
    modo_valor = st.selectbox("Modo de Valor", ["Dividir Total", "Replicar Integral"])
    
    if st.button("Salvar Lançamento", type="primary"):
        if cat_escolhida == "+ Incluir Nova Categoria..." and categoria_final not in st.session_state.categorias:
            st.session_state.categorias.append(categoria_final)
            pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)

        if descricao.strip() == "":
            st.warning("Preencha a descrição.")
        else:
            novos_registros = []
            for i in range(parcelas):
                if frequencia == "Mensal":
                    data_parcela = data_compra + relativedelta(months=i)
                elif frequencia == "Quinzenal":
                    data_parcela = data_compra + relativedelta(weeks=2*i)
                elif frequencia == "Anual":
                    data_parcela = data_compra + relativedelta(years=i)
                else:
                    data_parcela = data_compra

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
            st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
            st.success(f"{parcelas} lançamento(s) gerado(s) e salvos com sucesso!")

elif aba == "Lançamentos":
    st.subheader("Lista de Lançamentos")
    df = st.session_state.lancamentos
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        if st.button("🗑️ Limpar Todos os Lançamentos"):
            st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Status", "Descricao", "Categoria", "Conta", "Valor", "Data", "Parcela"])
            st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
            st.rerun()
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
                st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
                st.success("Cartão salvo com sucesso!")

    if not st.session_state.cartoes.empty:
        st.dataframe(st.session_state.cartoes, use_container_width=True)

elif aba == "Gerenciar Categorias":
    st.subheader("📂 Gerenciamento de Categorias")
    nova_cat = st.text_input("Nome da Nova Categoria")
    if st.button("Adicionar Categoria"):
        if nova_cat.strip() != "" and nova_cat not in st.session_state.categorias:
            st.session_state.categorias.append(nova_cat)
            pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
            st.success("Categoria adicionada e salva!")
    for cat in st.session_state.categorias:
        st.write(f"- {cat}")
