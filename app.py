elif aba == "Dashboard":
    st.subheader("📊 Dashboard Financeiro")
    
    df = st.session_state.lancamentos
    
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        
        # Pega o ano e mês atuais
        ano_atual = datetime.today().year
        mes_atual = datetime.today().month
        
        # Filtro estrito para o MÊS ATUAL
        df_mes_atual = df[(df["Data"].dt.year == ano_atual) & (df["Data"].dt.month == mes_atual)]
        
        # Valores gerais efetivados do mês atual
        receitas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Receita") & (df_mes_atual["Status"] == "Efetivado")]["Valor"].sum()
        despesas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Despesa") & (df_mes_atual["Status"] == "Efetivado")]["Valor"].sum()
        
        # Budget APENAS DO MÊS ATUAL
        budget_despesas = df_mes_atual[(df_mes_atual["Tipo"] == "Despesa") & (df_mes_atual["Status"] == "Budget")]["Valor"].sum()
        budget_receitas = df_mes_atual[(df_mes_atual["Tipo"] == "Receita") & (df_mes_atual["Status"] == "Budget")]["Valor"].sum()
        
        hoje_dt = pd.to_datetime(datetime.today().date())
        despesas_vencidas = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Budget") & (df["Data"] < hoje_dt)]["Valor"].sum()
    else:
        df_mes_atual = pd.DataFrame()
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

    # Comprometimento do Budget (Considerando APENAS o mês atual)
    st.markdown("### 🎯 Comprometimento da Renda (Budget - Mês Atual)")
    renda_base = budget_receitas if budget_receitas > 0 else 1.0
    comprometimento = min((budget_despesas / renda_base) * 100, 100.0)
    
    col_b1, col_b2 = st.columns(2)
    col_b1.write(f"**Renda do Mês (Budget Income):** R$ {budget_receitas:,.2f}")
    col_b2.write(f"**Total Planejado (Budget Expenses):** R$ {budget_despesas:,.2f}")
    
    st.progress(int(comprometimento))
    st.write(f"Comprometimento do Budget: **{comprometimento:.1f}%**")

    st.markdown("---")

    # 1. CASH FLOW POR ACCOUNT (Considerando APENAS o mês atual)
    st.markdown("### 🏛️ Cash Flow por Account (Mês Atual)")
    st.markdown("Saldo detalhado por conta considerando o período atual.")
    if not df_mes_atual.empty:
        cash_flow = df_mes_atual.groupby(["Conta", "Tipo"])["Valor"].sum().unstack(fill_value=0.0)
        if "Receita" not in cash_flow.columns: cash_flow["Receita"] = 0.0
        if "Despesa" not in cash_flow.columns: cash_flow["Despesa"] = 0.0
        cash_flow["Saldo Líquido"] = cash_flow["Receita"] - cash_flow["Despesa"]
        
        st.dataframe(cash_flow[["Receita", "Despesa", "Saldo Líquido"]], use_container_width=True)
        st.bar_chart(cash_flow["Saldo Líquido"])
    else:
        st.info("Nenhuma conta movimentada neste mês atual.")

    st.markdown("---")

    # 2. BUDGET: INCOME X EXPENSES (Comparativo Mensal)
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
        st.bar_chart(budget_mensal[["Budget Receitas", "Budget Despesas"]])
    else:
        st.info("Nenhum registro de Budget cadastrado para o comparativo.")

    st.markdown("---")

    # Maiores Despesas por Categoria
    st.markdown("### 🔥 Maiores Despesas por Categoria")
    if not df_mes_atual.empty and not df_mes_atual[df_mes_atual["Tipo"] == "Despesa"].empty:
        cat_grouped = df_mes_atual[df_mes_atual["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum()
        st.bar_chart(cat_grouped)
    else:
        st.info("Nenhuma despesa registrada neste mês.")

    st.markdown("---")

    # Últimas Transações Recentes
    st.markdown("### 🕒 Últimas Transações Recentes")
    if not df.empty:
        st.dataframe(df.sort_values(by="Data", ascending=False).head(5), use_container_width=True)
    else:
        st.info("Nenhuma transação recente.")
