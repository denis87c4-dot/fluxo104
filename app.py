import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt
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

# Função auxiliar para colorir números negativos de vermelho em DataFrames
def colorir_negativos(val):
    if isinstance(val, str) and "R$" in val:
        try:
            limpo = val.replace("R$", "").replace(".", "").replace(",", ".").replace("%", "").strip()
            val_num = float(limpo)
            if val_num < 0:
                return 'color: #ff4b4b; font-weight: bold;'
        except:
            pass
    elif isinstance(val, (int, float)) and val < 0:
        return 'color: #ff4b4b; font-weight: bold;'
    return ''

# Menu lateral com a nova aba dedicada de gráficos e projeções
aba = st.sidebar.radio("Navegação", ["Dashboard", "Projections & Charts", "Monthly Audit", "Financial Indicators", "Statistical Indicators", "Cadastro (Form)", "Lançamentos", "Cartões", "Gerenciar Categorias"])

if aba == "Dashboard":
    st.subheader("📊 Dashboard Financeiro")
    
    df = st.session_state.lancamentos
    
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        
        ano_atual = datetime.today().year
        mes_atual = datetime.today().month
        
        df_mes_atual = df[(df["Data"].dt.year == ano_atual) & (df["Data"].dt.month == mes_atual)]
        
        receitas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Receita") & (df_mes_atual["Status"] == "Efetivado")]["Valor"].sum()
        despesas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Despesa") & (df_mes_atual["Status"] == "Efetivado")]["Valor"].sum()
        
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

    # Comprometimento do Budget
    st.markdown("### 🎯 Comprometimento da Renda (Budget - Mês Atual)")
    renda_base = budget_receitas if budget_receitas > 0 else 1.0
    comprometimento = min((budget_despesas / renda_base) * 100, 100.0)
    
    col_b1, col_b2 = st.columns(2)
    col_b1.write(f"**Renda do Mês (Budget Income):** R$ {budget_receitas:,.2f}")
    col_b2.write(f"**Total Planejado (Budget Expenses):** R$ {budget_despesas:,.2f}")
    
    st.progress(int(comprometimento))
    st.write(f"Comprometimento do Budget: **{comprometimento:.1f}%**")

    st.markdown("---")

    # 1. CASH FLOW POR ACCOUNT (Mês Atual em R$)
    st.markdown("### 🏛️ Cash Flow por Account (Mês Atual)")
    st.markdown("Saldo detalhado por conta no período atual.")
    if not df_mes_atual.empty:
        cash_flow = df_mes_atual.groupby(["Conta", "Tipo"])["Valor"].sum().unstack(fill_value=0.0)
        if "Receita" not in cash_flow.columns:
            cash_flow["Receita"] = 0.0
        if "Despesa" not in cash_flow.columns:
            cash_flow["Despesa"] = 0.0
        cash_flow["Saldo Líquido"] = cash_flow["Receita"] - cash_flow["Despesa"]
        
        cash_flow_fmt = cash_flow.copy()
        for col in cash_flow_fmt.columns:
            cash_flow_fmt[col] = cash_flow_fmt[col].apply(lambda x: f"R$ {x:,.2f}")
            
        st.dataframe(cash_flow_fmt.style.map(colorir_negativos), use_container_width=True)
        st.bar_chart(cash_flow["Saldo Líquido"])
    else:
        st.info("Nenhuma conta movimentada neste mês atual.")

    st.markdown("---")

    # 2. BUDGET: INCOME X EXPENSES (Comparativo Mensal + Gráfico Customizado Altair)
    st.markdown("### 📊 Budget: Income x Expenses (Comparativo Mensal)")
    st.markdown("Visão planejada mês a mês (Despesas em Barras Vermelhas e Receitas em Linha Azul).")
    
    if not df.empty and not df[df["Status"] == "Budget"].empty:
        df_budget = df[df["Status"] == "Budget"].copy()
        df_budget["Data"] = pd.to_datetime(df_budget["Data"], errors="coerce")
        df_budget["AnoMes"] = df_budget["Data"].dt.to_period("M").astype(str)
        
        budget_mensal = df_budget.pivot_table(index="AnoMes", columns="Tipo", values="Valor", aggfunc="sum", fill_value=0.0)
        if "Receita" not in budget_mensal.columns:
            budget_mensal["Receita"] = 0.0
        if "Despesa" not in budget_mensal.columns:
            budget_mensal["Despesa"] = 0.0
        
        budget_mensal = budget_mensal.rename(columns={"Receita": "Budget Receitas", "Despesa": "Budget Despesas"})
        
        budget_mensal["Cash Flow Mês"] = budget_mensal["Budget Receitas"] - budget_mensal["Budget Despesas"]
        budget_mensal["Acumulado"] = budget_mensal["Cash Flow Mês"].cumsum()
        
        budget_mensal_fmt = budget_mensal.copy()
        for col in budget_mensal_fmt.columns:
            budget_mensal_fmt[col] = budget_mensal_fmt[col].apply(lambda x: f"R$ {x:,.2f}")
            
        st.dataframe(budget_mensal_fmt.style.map(colorir_negativos), use_container_width=True)
        
        df_chart = budget_mensal.reset_index()
        base = alt.Chart(df_chart).encode(x=alt.X('AnoMes:N', title='Mês'))
        
        barras_despesas = base.mark_bar(color='#ff4b4b').encode(
            y=alt.Y('Budget Despesas:Q', title='Valor (R$)'),
            tooltip=['AnoMes', 'Budget Despesas', 'Budget Receitas']
        )
        linha_receitas = base.mark_line(color='#1f77b4', strokeWidth=3).encode(y='Budget Receitas:Q')
        pontos_receitas = base.mark_point(color='#1f77b4', size=60).encode(
            y='Budget Receitas:Q',
            tooltip=['AnoMes', 'Budget Despesas', 'Budget Receitas']
        )
        
        grafico_combinado = (barras_despesas + linha_receitas + pontos_receitas).properties(height=400).interactive()
        st.altair_chart(grafico_combinado, use_container_width=True)
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
        df_recentes = df.sort_values(by="Data", ascending=False).head(5).copy()
        df_recentes["Valor"] = df_recentes["Valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_recentes.style.map(colorir_negativos), use_container_width=True)
    else:
        st.info("Nenhuma transação recente.")

elif aba == "Projections & Charts":
    st.subheader("📈 Projections & Charts (Central de Gráficos e Projeções)")
    st.markdown("Aba dedicada exclusivamente a visualizações avançadas, gráficos mistos e projeções financeiras baseadas em regressão linear ($y = ax + b$).")
    
    df = st.session_state.lancamentos
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)
        
        pivot_graf = df.pivot_table(index="AnoMes", columns="Tipo", values="Valor", aggfunc="sum", fill_value=0.0).reset_index()
        if "Receita" not in pivot_graf.columns:
            pivot_graf["Receita"] = 0.0
        if "Despesa" not in pivot_graf.columns:
            pivot_graf["Despesa"] = 0.0
        pivot_graf["CashFlow"] = pivot_graf["Receita"] - pivot_graf["Despesa"]
        pivot_graf["Acumulado"] = pivot_graf["CashFlow"].cumsum()
        
        # ==========================================
        # GRÁFICO 1: Misto (Linha e Barras) - Despesas vs Receitas Mensais
        # ==========================================
        st.markdown("### 1️⃣ Gráfico Misto: Barras de Despesas & Linha de Receitas")
        st.markdown("Combinação ideal para comparar o volume de gastos mensais (barras vermelhas) diretamente com as receitas (linha azul).")
        
        base_g1 = alt.Chart(pivot_graf).encode(x=alt.X('AnoMes:N', title='Mês'))
        barras_d = base_g1.mark_bar(color='#ff4b4b', opacity=0.7).encode(
            y=alt.Y('Despesa:Q', title='Valor (R$)'),
            tooltip=['AnoMes', 'Despesa', 'Receita']
        )
        linha_r = base_g1.mark_line(color='#1f77b4', strokeWidth=3).encode(y='Receita:Q')
        pontos_r = base_g1.mark_point(color='#1f77b4', size=70).encode(
            y='Receita:Q',
            tooltip=['AnoMes', 'Receita', 'Despesa']
        )
        chart_misto = (barras_d + linha_r + pontos_r).properties(height=380).interactive()
        st.altair_chart(chart_misto, use_container_width=True)
        
        st.markdown("---")
        
        # ==========================================
        # GRÁFICO 2: Projeção Financeira Linear (y = ax + b)
        # ==========================================
        st.markdown("### 2️⃣ Gráfico de Projeção Financeira Linear ($y = ax + b$ tipo Excel)")
        st.markdown("Calcula estatisticamente a tendência futura com base na equação de regressão linear do histórico.")
        
        col_proj1, col_proj2 = st.columns(2)
        with col_proj1:
            variavel_proj = st.selectbox("Variável para Projeção:", ["Despesa", "Receita", "CashFlow"])
        with col_proj2:
            meses_futuros = st.slider("Meses a Projetar no Futuro:", min_value=1, max_value=12, value=3)
            
        if len(pivot_graf) >= 2:
            x_vals = np.arange(len(pivot_graf))
            y_vals = pivot_graf[variavel_proj].values
            
            # Cálculo da Regressão Linear: y = a*x + b
            a, b_coef = np.polyfit(x_vals, y_vals, 1)
            
            dados_regressao = []
            for i, row in pivot_graf.iterrows():
                dados_regressao.append({
                    "Periodo": row["AnoMes"],
                    "Valor": row[variavel_proj],
                    "Tipo": "Histórico Real"
                })
                
            ultimo_periodo_str = pivot_graf["AnoMes"].max()
            ultimo_dt = datetime.strptime(ultimo_periodo_str + "-01", "%Y-%m-%d")
            
            for step in range(1, meses_futuros + 1):
                fut_dt = ultimo_dt + relativedelta(months=step)
                fut_str = fut_dt.strftime("%Y-%m")
                x_fut = len(pivot_graf) + step - 1
                y_fut = (a * x_fut) + b_coef
                
                dados_regressao.append({
                    "Periodo": fut_str,
                    "Valor": max(0.0, y_fut),
                    "Tipo": f"Projeção Linear (y = {a:.1f}x + {b_coef:.1f})"
                })
                
            df_reg = pd.DataFrame(dados_regressao)
            
            chart_proj = alt.Chart(df_reg).mark_line(strokeWidth=3, point=True).encode(
                x=alt.X('Periodo:N', title='Período (Histórico + Projeção)'),
                y=alt.Y('Valor:Q', title=f'Projeção de {variavel_proj} (R$)'),
                color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Histórico Real', f'Projeção Linear (y = {a:.1f}x + {b_coef:.1f})'], range=['#1f77b4', '#2ca02c']))
            ).properties(height=380).interactive()
            
            st.altair_chart(chart_proj, use_container_width=True)
            st.info(f"Equação de tendência aplicada: **y = {a:.2f}x + {b_coef:.2f}** (Onde 'x' é o índice do mês e 'y' é o valor estimado).")
        else:
            st.warning("É necessário ter pelo menos 2 meses de histórico registrados para gerar a projeção linear.")

        st.markdown("---")

        # ==========================================
        # GRÁFICO 3: Gráfico de Área Acumulada (Cash Flow Acumulado)
        # ==========================================
        st.markdown("### 3️⃣ Gráfico de Área: Evolução do Cash Flow Acumulado")
        st.markdown("Visualização em área destacando o saldo acumulado ao longo do tempo.")
        
        chart_area = alt.Chart(pivot_graf).mark_area(
            opacity=0.5,
            color='#2ca02c',
            line={'color': '#2ca02c', 'strokeWidth': 3}
        ).encode(
            x=alt.X('AnoMes:N', title='Mês'),
            y=alt.Y('Acumulado:Q', title='Cash Flow Acumulado (R$)'),
            tooltip=['AnoMes', 'Acumulado', 'CashFlow']
        ).properties(height=350).interactive()
        
        st.altair_chart(chart_area, use_container_width=True)

        st.markdown("---")

        # ==========================================
        # GRÁFICO 4: Dispersão / Correlação (Scatter Plot)
        # ==========================================
        st.markdown("### 4️⃣ Gráfico de Dispersão: Relação Receitas vs Despesas Mensais")
        st.markdown("Permite identificar rapidamente a proporção e pontos fora da curva entre entradas e saídas.")
        
        chart_scatter = alt.Chart(pivot_graf).mark_circle(size=120).encode(
            x=alt.X('Despesa:Q', title='Despesas do Mês (R$)'),
            y=alt.Y('Receita:Q', title='Receitas do Mês (R$)'),
            color=alt.Color('AnoMes:N', title='Mês'),
            tooltip=['AnoMes', 'Despesa', 'Receita', 'CashFlow']
        ).properties(height=350).interactive()
        
        st.altair_chart(chart_scatter, use_container_width=True)
        
    else:
        st.info("Nenhum lançamento registrado para exibir os gráficos e projeções.")

elif aba == "Monthly Audit":
    st.subheader("🔍 Monthly Audit (Auditoria do Mês Atual)")
    st.markdown("Acompanhamento estrito do mês atual por categoria: **Budget** vs **Entry (Efetivado/Realizado)** e a **Diferença**.")
    
    df = st.session_state.lancamentos
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        
        ano_atual = datetime.today().year
        mes_atual = datetime.today().month
        
        df_mes = df[(df["Data"].dt.year == ano_atual) & (df["Data"].dt.month == mes_atual) & (df["Tipo"] == "Despesa")]
        
        if not df_mes.empty:
            df_budget_mes = df_mes[df_mes["Status"] == "Budget"].groupby("Categoria")["Valor"].sum()
            df_entry_mes = df_mes[df_mes["Status"] == "Efetivado"].groupby("Categoria")["Valor"].sum()
            
            todas_categorias = sorted(list(set(df_budget_mes.index.tolist() + df_entry_mes.index.tolist())))
            
            dados_audit = []
            for cat in todas_categorias:
                b_val = df_budget_mes.get(cat, 0.0)
                e_val = df_entry_mes.get(cat, 0.0)
                dif_val = b_val - e_val
                
                if dif_val < 0:
                    status_pagamento = f"⚠️ Estourado/Pendente (R$ {abs(dif_val):,.2f} acima)"
                else:
                    status_pagamento = f"✅ Dentro do Budget (Restam R$ {dif_val:,.2f})"
                
                dados_audit.append({
                    "Categoria": cat,
                    "1. Budget (Mês)": b_val,
                    "2. Entry (Efetivado)": e_val,
                    "3. Diferença (Budget - Entry)": dif_val,
                    "Status / Alerta": status_pagamento
                })
                
            df_audit_table = pd.DataFrame(dados_audit).set_index("Categoria")
            
            df_audit_fmt = df_audit_table.copy()
            df_audit_fmt["1. Budget (Mês)"] = df_audit_fmt["1. Budget (Mês)"].apply(lambda x: f"R$ {x:,.2f}")
            df_audit_fmt["2. Entry (Efetivado)"] = df_audit_fmt["2. Entry (Efetivado)"].apply(lambda x: f"R$ {x:,.2f}")
            df_audit_fmt["3. Diferença (Budget - Entry)"] = df_audit_fmt["3. Diferença (Budget - Entry)"].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(df_audit_fmt.style.map(colorir_negativos, subset=["3. Diferença (Budget - Entry)"]), use_container_width=True)
            
            hoje_dt = pd.to_datetime(datetime.today().date())
            vencidas_mes = df_mes[(df_mes["Status"] == "Budget") & (df_mes["Data"] < hoje_dt)]
            if not vencidas_mes.empty:
                st.markdown("### ⚠️ Alerta de Contas Vencidas (Budget Pendente no Mês)")
                df_venc_fmt = vencidas_mes[["Data", "Descricao", "Categoria", "Conta", "Valor"]].copy()
                df_venc_fmt["Valor"] = df_venc_fmt["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_venc_fmt, use_container_width=True)
            else:
                st.success("🎉 Nenhuma despesa pendente/vencida neste mês atual!")
        else:
            st.info("Nenhuma despesa registrada para este mês atual.")
    else:
        st.info("Nenhum lançamento cadastrado no sistema.")

elif aba == "Financial Indicators":
    st.subheader("📈 Financial Indicators (Budget)")
    st.markdown("Indicadores financeiros calculados mês a mês com base no planejamento (Budget).")
    
    df = st.session_state.lancamentos
    if not df.empty and not df[df["Status"] == "Budget"].empty:
        df_b = df[df["Status"] == "Budget"].copy()
        df_b["Data"] = pd.to_datetime(df_b["Data"], errors="coerce")
        df_b["AnoMes"] = df_b["Data"].dt.to_period("M").astype(str)
        
        meses = sorted(df_b["AnoMes"].unique())
        
        st.markdown("### 🚀 Strategic Metrics (1 a 3)")
        dados_avancados_3 = []
        for m in meses:
            df_m = df_b[df_b["AnoMes"] == m]
            income = df_m[(df_m["Tipo"] == "Receita")]["Valor"].sum()
            expense = df_m[(df_m["Tipo"] == "Despesa")]["Valor"].sum()
            debts = df_m[(df_m["Tipo"] == "Despesa") & (df_m["Categoria"].str.contains("debt|dívida", case=False, na=False))]["Valor"].sum()
            cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []
            credit_card = df_m[(df_m["Tipo"] == "Despesa") & ((df_m["Conta"].isin(cartoes_nomes)) | (df_m["Categoria"].str.contains("credit|cartão", case=False, na=False)))]["Valor"].sum()
            
            net_cash_flow = income - expense
            burn_rate = abs(net_cash_flow) if net_cash_flow < 0 else 0.0
            burn_rate_str = f"R$ {burn_rate:,.2f} (Queima)" if burn_rate > 0 else "R$ 0,00 (Sem Queima)"
            
            df_ate_mes = df_b[df_b["AnoMes"] <= m]
            patrimonio_liquido_est = df_ate_mes[df_ate_mes["Tipo"] == "Receita"]["Valor"].sum() - df_ate_mes[df_ate_mes["Tipo"] == "Despesa"]["Valor"].sum()
            
            if burn_rate > 0:
                runway_meses = patrimonio_liquido_est / burn_rate
                runway_str = f"{runway_meses:.1f} meses" if runway_meses > 0 else "0.0 meses"
            else:
                runway_str = "Infinito (Superávit)"
                
            burn_runway_final = f"{burn_rate_str} | Runway: {runway_str}"
            
            obrigacoes_mes = debts + credit_card
            if obrigacoes_mes > 0:
                dscr_val = income / obrigacoes_mes
                dscr_final = f"{dscr_val:.2f}x (Seguro > 1.2)" if dscr_val >= 1.2 else f"{dscr_val:.2f}x (⚠️ Alerta < 1.2)"
            else:
                dscr_final = "N/A (Sem Dívidas/Cartão)"
                
            df_historico_ate_mes = df_b[(df_b["AnoMes"] <= m) & (df_b["Tipo"] == "Despesa")]
            gastos_por_mes = df_historico_ate_mes.groupby("AnoMes")["Valor"].sum()
            if len(gastos_por_mes) > 1:
                media_hist = gastos_por_mes.mean()
                desv_hist = gastos_por_mes.std()
                cv_val = (desv_hist / media_hist) * 100 if media_hist > 0 else 0.0
                cv_final = f"{cv_val:.1f}%"
            else:
                cv_final = "N/A (Requer + de 1 mês)"
                
            dados_avancados_3.append({
                "Mês": m,
                "1. Burn Rate & Runway": burn_runway_final,
                "2. DSCR (Cobertura da Dívida)": dscr_final,
                "3. Coeficiente de Variação (CV)": cv_final
            })
            
        st.dataframe(pd.DataFrame(dados_avancados_3).set_index("Mês"), use_container_width=True)

        st.markdown("---")
        st.markdown("### 🛡️ Liquidity, Savings & Risk Metrics (4 a 6)")
        dados_avancados_4_6 = []
        for m in meses:
            df_m = df_b[df_b["AnoMes"] == m]
            income = df_m[(df_m["Tipo"] == "Receita")]["Valor"].sum()
            expense = df_m[(df_m["Tipo"] == "Despesa")]["Valor"].sum()
            contas_liquidas = df_m[(df_m["Tipo"] == "Receita") & (~df_m["Conta"].isin(st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []))]["Valor"].sum()
            cash_ratio = (contas_liquidas / expense) if expense > 0 else 0.0
            cash_ratio_str = f"{cash_ratio:.2f}x (Coberto)" if cash_ratio >= 1.0 else f"{cash_ratio:.2f}x (⚠️ Ajuste Caixa)"
            net_savings = ((income - expense) / income * 100) if income > 0 else 0.0
            net_savings_str = f"{net_savings:.1f}%"
            df_hist_exp = df_b[(df_b["AnoMes"] <= m) & (df_b["Tipo"] == "Despesa")]
            series_exp_hist = df_hist_exp.groupby("AnoMes")["Valor"].sum()
            if len(series_exp_hist) > 1:
                media_exp = series_exp_hist.mean()
                desv_exp = series_exp_hist.std()
                var_95 = media_exp + (1.645 * desv_exp)
                var_str = f"R$ {var_95:,.2f}"
            else:
                var_str = "R$ 0,00 (Histórico Insuficiente)"
            dados_avancados_4_6.append({
                "Mês": m,
                "4. Cash Ratio (Liquidez Imediata)": cash_ratio_str,
                "5. Net Savings Rate (Taxa de Poupança)": net_savings_str,
                "6. Value at Risk (VaR 95%)": var_str
            })
        st.dataframe(pd.DataFrame(dados_avancados_4_6).set_index("Mês"), use_container_width=True)

        st.markdown("---")
        st.markdown("### 🏛️ Advanced Financial & Leverage Metrics (7 a 9)")
        dados_avancados_7_9 = []
        for m in meses:
            df_m = df_b[df_b["AnoMes"] == m]
            income = df_m[(df_m["Tipo"] == "Receita")]["Valor"].sum()
            expense = df_m[(df_m["Tipo"] == "Despesa")]["Valor"].sum()
            juros_mes = df_m[(df_m["Tipo"] == "Despesa") & (df_m["Categoria"].str.contains("juros|interest|financiamento", case=False, na=False))]["Valor"].sum()
            if juros_mes > 0:
                interest_coverage = income / juros_mes
                interest_cov_str = f"{interest_coverage:.2f}x (Seguro > 3.0)" if interest_coverage >= 3.0 else f"{interest_coverage:.2f}x (⚠️ Alerta < 3.0)"
            else:
                interest_cov_str = "N/A (Sem Encargos de Juros)"
            df_ate_mes = df_b[df_b["AnoMes"] <= m]
            ativos_totais = df_ate_mes[df_ate_mes["Tipo"] == "Receita"]["Valor"].sum() - df_ate_mes[df_ate_mes["Tipo"] == "Despesa"]["Valor"].sum()
            net_income_mes = income - expense
            if ativos_totais > 0:
                roa_val = (net_income_mes / ativos_totais) * 100
                roa_str = f"{roa_val:.2f}%"
            else:
                roa_str = "0.00% (Ativos Base Zerados)"
            debts = df_m[(df_m["Tipo"] == "Despesa") & (df_m["Categoria"].str.contains("debt|dívida", case=False, na=False))]["Valor"].sum()
            cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []
            credit_card = df_m[(df_m["Tipo"] == "Despesa") & ((df_m["Conta"].isin(cartoes_nomes)) | (df_m["Categoria"].str.contains("credit|cartão", case=False, na=False)))]["Valor"].sum()
            total_obrigacoes = debts + credit_card
            dti_val = (total_obrigacoes / income * 100) if income > 0 else 0.0
            dti_str = f"{dti_val:.1f}% (⚠️ Alto > 40%)" if dti_val > 40.0 else f"{dti_val:.1f}% (Saudável <= 40%)"
            dados_avancados_7_9.append({
                "Mês": m,
                "7. Interest Coverage (Cobertura de Juros)": interest_cov_str,
                "8. ROA Pessoal (Retorno sobre Ativos)": roa_str,
                "9. Debt-to-Income (Endividamento - DTI)": dti_str
            })
        st.dataframe(pd.DataFrame(dados_avancados_7_9).set_index("Mês"), use_container_width=True)
    else:
        st.info("Nenhum dado de Budget cadastrado para calcular os indicadores financeiros.")

elif aba == "Statistical Indicators":
    st.subheader("📊 Statistical Indicators (Budget)")
    st.markdown("Parâmetros estatísticos, desvio padrão, Z-score e distribuição de probabilidade em forma de sino.")
    
    df = st.session_state.lancamentos
    if not df.empty and not df[df["Status"] == "Budget"].empty:
        df_b = df[df["Status"] == "Budget"].copy()
        df_b["Data"] = pd.to_datetime(df_b["Data"], errors="coerce")
        df_b["AnoMes"] = df_b["Data"].dt.to_period("M").astype(str)
        
        pivot_mensal = df_b.pivot_table(index="AnoMes", columns="Tipo", values="Valor", aggfunc="sum", fill_value=0.0)
        if "Receita" not in pivot_mensal.columns:
            pivot_mensal["Receita"] = 0.0
        if "Despesa" not in pivot_mensal.columns:
            pivot_mensal["Despesa"] = 0.0
            
        pivot_mensal = pivot_mensal.rename(columns={"Receita": "Income", "Despesa": "Expense"})
        pivot_mensal["Cash Flow"] = pivot_mensal["Income"] - pivot_mensal["Expense"]
        pivot_mensal["Acumulado"] = pivot_mensal["Cash Flow"].cumsum()
        pivot_mensal = pivot_mensal.reset_index().sort_values("AnoMes")
        
        if len(pivot_mensal) > 0:
            valores_exp = pivot_mensal["Expense"]
            media_geral = valores_exp.mean()
            desvio_padrao = valores_exp.std() if len(valores_exp) > 1 else 0.0
            
            dados_stats = []
            for idx, row in pivot_mensal.iterrows():
                m = row["AnoMes"]
                val = row["Expense"]
                z_score = (val - media_geral) / desvio_padrao if desvio_padrao > 0 else 0.0
                
                if z_score > 1.5:
                    interpretacao = "⚠️ Alerta: Gastos muito acima da média histórica"
                elif z_score > 0.5:
                    interpretacao = "⚡ Acima da média histórica"
                elif z_score < -1.5:
                    interpretacao = "🌟 Excelente: Muito abaixo da média"
                elif z_score < -0.5:
                    interpretacao = "📉 Abaixo da média histórica"
                else:
                    interpretacao = "✅ Dentro da normalidade esperada"
                
                dados_stats.append({
                    "Mês": m,
                    "Total Expenses": f"R$ {val:,.2f}",
                    "Média Histórica": f"R$ {media_geral:,.2f}",
                    "Desvio Padrão": f"R$ {desvio_padrao:,.2f}",
                    "Z-Score": round(z_score, 2),
                    "Interpretação": interpretacao
                })
                
            st.markdown("### 📌 Z-Score e Desvio Padrão Mensal (Expenses)")
            st.dataframe(pd.DataFrame(dados_stats).set_index("Mês").style.map(colorir_negativos), use_container_width=True)
    else:
        st.info("Nenhum dado de Budget cadastrado para calcular os indicadores estatísticos.")

elif aba == "Cadastro (Form)":
    st.subheader("Novo Registro (Form)")
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
    
    cartao_selecionado_row = None
    if not st.session_state.cartoes.empty and conta_final in st.session_state.cartoes["Nome"].values:
        cartao_selecionado_row = st.session_state.cartoes[st.session_state.cartoes["Nome"] == conta_final].iloc[0]

    if conta_escolhida == "+ Incluir Novo Cartão/Conta...":
        novo_c_digitado = st.text_input("Digite o nome do novo Cartão / Conta:")
        if novo_c_digitado.strip() != "":
            conta_final = novo_c_digitado.strip()
            novo_c_df = pd.DataFrame([{"Nome": conta_final, "Fechamento": 10, "Limite": 1000.0, "Vencimento": 17}])
            st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_c_df], ignore_index=True)
            st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
            cartao_selecionado_row = novo_c_df.iloc[0]

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
            dia_fechamento_cartao = int(cartao_selecionado_row["Fechamento"]) if cartao_selecionado_row is not None and "Fechamento" in cartao_selecionado_row else 0
            
            for i in range(parcelas):
                if frequencia == "Mensal":
                    data_base_parcela = data_compra + relativedelta(months=i)
                elif frequencia == "Quinzenal":
                    data_base_parcela = data_compra + relativedelta(weeks=2*i)
                elif frequencia == "Anual":
                    data_base_parcela = data_compra + relativedelta(years=i)
                else:
                    data_base_parcela = data_compra

                data_efetiva_lancamento = data_base_parcela
                if cartao_selecionado_row is not None and dia_fechamento_cartao > 0:
                    if i == 0 and data_compra.day > dia_fechamento_cartao:
                        data_efetiva_lancamento = data_base_parcela + relativedelta(months=1)
                    elif i > 0 and data_compra.day > dia_fechamento_cartao:
                        data_efetiva_lancamento = data_base_parcela + relativedelta(months=1)

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
                    "Data": str(data_efetiva_lancamento),
                    "Parcela": f"{i+1}/{parcelas}"
                })

            df_novo = pd.DataFrame(novos_registros)
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, df_novo], ignore_index=True)
            st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
            
            if cartao_selecionado_row is not None:
                nome_c_alvo = cartao_selecionado_row["Nome"]
                idx_cartao = st.session_state.cartoes[st.session_state.cartoes["Nome"] == nome_c_alvo].index
                if not idx_cartao.empty:
                    limite_atual = float(st.session_state.cartoes.loc[idx_cartao[0], "Limite"])
                    novo_limite = max(0.0, limite_atual - valor_total)
                    st.session_state.cartoes.loc[idx_cartao[0], "Limite"] = novo_limite
                    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)

            st.success(f"{parcelas} lançamento(s) gerado(s) com sucesso!")

elif aba == "Lançamentos":
    st.subheader("Lista de Lançamentos")
    df = st.session_state.lancamentos
    if not df.empty:
        df_lanc_fmt = df.copy()
        df_lanc_fmt["Valor"] = df_lanc_fmt["Valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_lanc_fmt.style.map(colorir_negativos), use_container_width=True)
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
        limite_disponivel = st.number_input("Limite Disponível (R$)", min_value=0.0, format="%.2f", value=1000.0)
        dia_pagamento = st.number_input("Dia de Vencimento / Pagamento", min_value=1, max_value=31, value=17)
        salvar_cartao = st.form_submit_button("Salvar Cartão")
        
        if salvar_cartao:
            if nome_cartao.strip() != "":
                novo_cartao = pd.DataFrame([{
                    "Nome": nome_cartao, 
                    "Fechamento": int(dia_fechamento), 
                    "Limite": float(limite_disponivel), 
                    "Vencimento": int(dia_pagamento)
                }])
                st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_cartao], ignore_index=True)
                st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
                st.success("Cartão salvo com sucesso!")

    if not st.session_state.cartoes.empty:
        df_cartoes_fmt = st.session_state.cartoes.copy()
        if "Limite" in df_cartoes_fmt.columns:
            df_cartoes_fmt["Limite"] = df_cartoes_fmt["Limite"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_cartoes_fmt.style.map(colorir_negativos), use_container_width=True)

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
