elif aba == "Dashboard":
    st.subheader("📊 Dashboard Financeiro")
    
    df = st.session_state.lancamentos
    
    # Cálculos gerais
    if not df.empty:
        receitas_mes = df[(df["Tipo"] == "Receita") & (df["Status"] == "Efetivado")]["Valor"].sum()
        despesas_mes = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Efetivado")]["Valor"].sum()
        budget_despesas = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Budget")]["Valor"].sum()
        budget_receitas = df[(df["Tipo"] == "Receita") & (df["Status"] == "Budget")]["Valor"].sum()
        
        hoje_str = datetime.today().strftime('%Y-%m-%d')
        despesas_vencidas = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Budget") & (df["Data"] < hoje_str)]["Valor"].sum()
    else:
        receitas_mes = 0.0
        despesas_mes = 0.0
        budget_despesas = 0.0
        budget_receitas = 0.0
        despesas_vencidas = 0.0

    # Linha 1: Cards de Métricas Principais (Igual aos prints)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📈 RECEITAS DO MÊS", f"R$ {receitas_mes:,.2f}", delta="Total de entradas no período")
    with col2:
        st.metric("📉 DESPESAS DO MÊS", f"R$ {despesas_mes:,.2f}", delta="Total de saídas no período")
    with col3:
        st.metric("⚠️ DESPESAS VENCIDAS", f"R$ {despesas_vencidas:,.2f}", delta="Budget pendente anterior")

    st.markdown("---")

    # Linha 2: Comprometimento do Budget
    st.markdown("### 🎯 Comprometimento da Renda (Budget)")
    st.markdown("Despesas planejadas (Budget) do mês atual em relação à Renda.")
    
    renda_base = budget_receitas if budget_receitas > 0 else 1.0
    comprometimento = min((budget_despesas / renda_base) * 100, 100.0)
    
    col_b1, col_b2 = st.columns(2)
    col_b1.write(f"**Renda do Mês (Budget Income):** R$ {budget_receitas:,.2f}")
    col_b2.write(f"**Total Planejado (Budget Expenses):** R$ {budget_despesas:,.2f}")
    
    st.progress(int(comprometimento))
    st.write(f"Comprometimento do Budget: **{comprometimento:.1f}%**")

    st.markdown("---")

    # Linha 3: Maiores Despesas por Categoria & Cash Flow por Account
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown("### 🔥 Maiores Despesas por Categoria")
        st.markdown("Onde seu dinheiro está indo neste mês.")
        if not df.empty and not df[df["Tipo"] == "Despesa"].empty:
            df_despesas = df[df["Tipo"] == "Despesa"]
            cat_grouped = df_despesas.groupby("Categoria")["Valor"].sum().reset_index()
            st.dataframe(cat_grouped, use_container_width=True)
        else:
            st.info("Nenhuma despesa efetivada neste mês.")

    with col_d2:
        st.markdown("### 🏛️ Cash Flow por Account (Mês Atual)")
        st.markdown("Saldo detalhado por conta no período.")
        if not df.empty:
            conta_grouped = df.groupby("Conta")["Valor"].sum().reset_index()
            st.dataframe(conta_grouped, use_container_width=True)
        else:
            st.info("Nenhuma conta movimentada neste mês.")

    st.markdown("---")
    
    # Linha 4: Últimas Transações Recentes
    st.markdown("### 🕒 Últimas Transações Recentes")
    if not df.empty:
        st.dataframe(df.tail(5), use_container_width=True)
    else:
        st.write("Nenhuma transação recente.")
