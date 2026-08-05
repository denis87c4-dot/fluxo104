import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Fluxo104", page_icon="💰", layout="wide")
st.title("💰 Fluxo104 - Gestão Financeira Executiva")
st.markdown("Acompanhamento financeiro corporativo em tempo real com salvamento automático e inteligência preditiva.")

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

# Função auxiliar segura para aplicar estilos em dataframes (compatível com versões recentes do Pandas/Streamlit)
def aplicar_estilo_tabela(df_styled, subset_cols=None):
    try:
        if hasattr(df_styled, "map"):
            return df_styled.map(colorir_negativos, subset=subset_cols)
        else:
            return df_styled.applymap(colorir_negativos, subset=subset_cols)
    except Exception:
        return df_styled

# Menu lateral atualizado
aba = st.sidebar.radio("Navegação", ["Dashboard", "Projections & Charts", "Monthly Audit", "Financial Indicators", "Statistical Indicators", "Cadastro (Form)", "Lançamentos", "Cartões", "Gerenciar Categorias"])

if aba == "Dashboard":
    st.subheader("📊 Executive Dashboard")
    
    df = st.session_state.lancamentos
    
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)
        
        meses_disponiveis = sorted(df["AnoMes"].unique().tolist(), reverse=True)
        mes_atual_padrao = datetime.today().strftime("%Y-%m")
        if mes_atual_padrao not in meses_disponiveis:
            meses_disponiveis.insert(0, mes_atual_padrao)
            
        col_f1, col_f2 = st.columns([2, 4])
        with col_f1:
            mes_selecionado = st.selectbox("📅 Período de Análise (Mês/Ano)", meses_disponiveis, index=0)
        
        ano_sel, mes_sel = map(int, mes_selecionado.split("-"))
        
        dt_sel = datetime(ano_sel, mes_sel, 1)
        dt_ant = dt_sel - relativedelta(months=1)
        
        df_mes_atual = df[(df["Data"].dt.year == ano_sel) & (df["Data"].dt.month == mes_sel)]
        df_mes_ant = df[(df["Data"].dt.year == dt_ant.year) & (df["Data"].dt.month == dt_ant.month)]
        
        receitas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Receita") & (df_mes_atual["Status"] == "Efetivado")]["Valor"].sum()
        receitas_ant = df_mes_ant[(df_mes_ant["Tipo"] == "Receita") & (df_mes_ant["Status"] == "Efetivado")]["Valor"].sum()
        delta_rec = ((receitas_mes - receitas_ant) / receitas_ant * 100) if receitas_ant > 0 else 0.0
        
        despesas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Despesa") & (df_mes_atual["Status"] == "Efetivado")]["Valor"].sum()
        despesas_ant = df_mes_ant[(df_mes_ant["Tipo"] == "Despesa") & (df_mes_ant["Status"] == "Efetivado")]["Valor"].sum()
        delta_desp = ((despesas_mes - despesas_ant) / despesas_ant * 100) if despesas_ant > 0 else 0.0
        
        budget_despesas = df_mes_atual[(df_mes_atual["Tipo"] == "Despesa") & (df_mes_atual["Status"] == "Budget")]["Valor"].sum()
        budget_receitas = df_mes_atual[(df_mes_atual["Tipo"] == "Receita") & (df_mes_atual["Status"] == "Budget")]["Valor"].sum()
        
        hoje_dt = pd.to_datetime(datetime.today().date())
        df_vencidas = df[(df["Tipo"] == "Despesa") & (df["Status"] == "Budget") & (df["Data"] < hoje_dt)]
        despesas_vencidas = df_vencidas["Valor"].sum()
        
        if not df_vencidas.empty:
            descricoes_vencidas = ", ".join(df_vencidas["Descricao"].unique())
            texto_vencidas_detalhe = f"<span style='color: #ff4b4b; font-weight: bold;'>R$ {despesas_vencidas:,.2f} ({descricoes_vencidas})</span>"
        else:
            texto_vencidas_detalhe = f"<span style='color: #2a9d8f; font-weight: bold;'>R$ 0,00 (Nenhuma vencida)</span>"
            
        fluxo_caixa_mes = receitas_mes - despesas_mes
    else:
        df_mes_atual = pd.DataFrame()
        receitas_mes = 0.0
        despesas_mes = 0.0
        budget_despesas = 0.0
        budget_receitas = 0.0
        despesas_vencidas = 0.0
        texto_vencidas_detalhe = "<span style='color: #2a9d8f; font-weight: bold;'>R$ 0,00</span>"
        delta_rec = 0.0
        delta_desp = 0.0
        fluxo_caixa_mes = 0.0
        df_vencidas = pd.DataFrame()
        mes_selecionado = datetime.today().strftime("%Y-%m")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📈 RECEITAS DO MÊS", f"R$ {receitas_mes:,.2f}", delta=f"{delta_rec:+.1f}% vs mês ant.")
    with col2:
        st.metric("📉 DESPESAS DO MÊS", f"R$ {despesas_mes:,.2f}", delta=f"{delta_desp:+.1f}% vs mês ant.", delta_color="inverse")
    with col3:
        st.markdown(f"**⚠️ DESPESAS VENCIDAS**<br>{texto_vencidas_detalhe}", unsafe_allow_html=True)
    with col4:
        st.metric("💵 FLUXO DE CAIXA", f"R$ {fluxo_caixa_mes:,.2f}", delta="Entradas - Despesas", delta_color="normal")

    st.markdown("---")

    if not df.empty and not df_vencidas.empty:
        with st.expander("⚡ Ações Rápidas: Regularizar Despesa Vencida"):
            st.write("Selecione uma despesa vencida abaixo para efetivá-la instantaneamente:")
            opcoes_vencidas = {f"{row['Data'].strftime('%d/%m/%Y')} - {row['Descricao']} (R$ {row['Valor']:,.2f})": idx for idx, row in df_vencidas.iterrows()}
            escolha_pagar = st.selectbox("Despesa pendente:", list(opcoes_vencidas.keys()))
            if st.button("✅ Marcar como Efetivado (Pago)", type="primary"):
                idx_alvo = opcoes_vencidas[escolha_pagar]
                st.session_state.lancamentos.loc[idx_alvo, "Status"] = "Efetivado"
                st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
                st.success("Despesa atualizada para Efetivado com sucesso!")
                st.rerun()

    if not df.empty and not df_mes_atual.empty:
        gastos_por_cat = df_mes_atual[df_mes_atual["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum()
        if not gastos_por_cat.empty:
            cat_maior_gasto = gastos_por_cat.idxmax()
            val_maior_gasto = gastos_por_cat.max()
            st.info(f"💡 **Executive Insight**: No mês de **{mes_selecionado}**, a categoria com maior consumo de recursos foi **{cat_maior_gasto}**, totalizando **R$ {val_maior_gasto:,.2f}**.")

    st.markdown("---")

    st.markdown(f"### 📈 Evolução Diária do Caixa ({mes_selecionado})")
    if not df_mes_atual.empty:
        df_diario = df_mes_atual.copy()
        df_diario["Dia"] = df_diario["Data"].dt.strftime("%d/%m")
        df_diario["FluxoDiario"] = df_diario.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else -r["Valor"], axis=1)
        pivot_diario = df_diario.groupby("Dia")["FluxoDiario"].sum().cumsum().reset_index()
        
        chart_diario = alt.Chart(pivot_diario).mark_line(strokeWidth=3, color='#2a9d8f', point=True).encode(
            x=alt.X('Dia:N', title='Dia do Mês'),
            y=alt.Y('FluxoDiario:Q', title='Saldo Acumulado Diário (R$)'),
            tooltip=['Dia', 'FluxoDiario']
        ).properties(height=300).interactive()
        st.altair_chart(chart_diario, use_container_width=True)
    else:
        st.info("Nenhum lançamento registrado para o período selecionado.")

    st.markdown("---")

    st.markdown("### 🎯 Comprometimento da Renda (Budget - Período Selecionado)")
    renda_base = budget_receitas if budget_receitas > 0 else 1.0
    comprometimento = min((budget_despesas / renda_base) * 100, 100.0)
    
    col_b1, col_b2 = st.columns(2)
    col_b1.write(f"**Renda Planejada (Budget Income):** R$ {budget_receitas:,.2f}")
    col_b2.write(f"**Total Planejado (Budget Expenses):** R$ {budget_despesas:,.2f}")
    
    st.progress(int(comprometimento))
    st.write(f"Comprometimento do Budget: **{comprometimento:.1f}%**")

    st.markdown("---")

    st.markdown("### 🏛️ Cash Flow por Account (Período Selecionado)")
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
            
        st.dataframe(aplicar_estilo_tabela(cash_flow_fmt.style), use_container_width=True)
        st.bar_chart(cash_flow["Saldo Líquido"])
    else:
        st.info("Nenhuma conta movimentada neste período.")

    st.markdown("---")
    st.markdown("### 🕒 Últimas Transações Recentes")
    if not df.empty:
        df_recentes = df.sort_values(by="Data", ascending=False).head(5).copy()
        df_recentes["Valor"] = df_recentes["Valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(aplicar_estilo_tabela(df_recentes.style), use_container_width=True)
    else:
        st.info("Nenhuma transação recente.")

elif aba == "Projections & Charts":
    st.subheader("📈 Projections & Charts (16 Gráficos e Parâmetros Avançados de Elite)")
    st.markdown("Central completa contendo a **Célula Suspensa** e módulos analíticos de projeção, risco e inteligência financeira.")
    
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
        
        st.markdown("---")
        st.markdown("### 🛸 Célula Suspensa (Simulador Preditivo de Ajuste de Orçamento)")
        st.markdown("Painel flutuante interativo para testar impactos imediatos no seu fluxo de caixa futuro simulando cortes ou injeções de capital.")
        
        with st.container():
            st.info("💡 **Painel de Simulação Ativo**: Ajuste os parâmetros abaixo para projetar o impacto direto no acumulado dos próximos meses.")
            cs_col1, cs_col2, cs_col3 = st.columns(3)
            with cs_col1:
                fator_ajuste_despesa = st.slider("Ajuste Percentual em Despesas (%)", min_value=-50, max_value=50, value=0, step=5)
            with cs_col2:
                aporte_extra_mensal = st.number_input("Injeção / Retirada Fixa Mensal (R$)", value=0.0, step=100.0)
            with cs_col3:
                horizonte_simulacao = st.slider("Horizonte de Projeção (Meses)", min_value=3, max_value=24, value=6)
                
            if len(pivot_graf) > 0:
                ultima_receita = pivot_graf["Receita"].iloc[-1]
                ultima_despesa = pivot_graf["Despesa"].iloc[-1]
                despesa_ajustada = ultima_despesa * (1 + (fator_ajuste_despesa / 100.0))
                fluxo_simulado = (ultima_receita + aporte_extra_mensal) - despesa_ajustada
                
                st.metric("Projeção de Cash Flow Mensal Ajustado (Célula Suspensa)", f"R$ {fluxo_simulado:,.2f}", delta=f"{fator_ajuste_despesa:+d}% nas despesas")
        st.markdown("---")
        
        st.markdown("### 1️⃣ Projeção de Fôlego de Caixa (Runway Preditivo em Meses)")
        saldo_atual_caixa = pivot_graf["Acumulado"].iloc[-1] if not pivot_graf.empty else 0.0
        media_despesas_recente = pivot_graf["Despesa"].tail(3).mean() if len(pivot_graf) >= 3 else pivot_graf["Despesa"].mean()
        
        meses_proj_runway = np.arange(0, 13)
        if media_despesas_recente > 0:
            curva_runway = [max(0.0, saldo_atual_caixa - (media_despesas_recente * m)) for m in meses_proj_runway]
        else:
            curva_runway = [saldo_atual_caixa] * 13
            
        df_runway = pd.DataFrame({"Meses_Futuros": [f"Mês +{m}" for m in meses_proj_runway], "Saldo_Projetado": curva_runway})
        
        chart_runway = alt.Chart(df_runway).mark_area(
            color='#1f77b4', opacity=0.5, line={'color': '#0d3b66', 'strokeWidth': 3}
        ).encode(
            x=alt.X('Meses_Futuros:N', title='Horizonte de Meses'),
            y=alt.Y('Saldo_Projetado:Q', title='Patrimônio Projetado (R$)'),
            tooltip=['Meses_Futuros', 'Saldo_Projetado']
        ).properties(height=350).interactive()
        st.altair_chart(chart_runway, use_container_width=True)

        st.markdown("---")

        st.markdown("### 2️⃣ Projeção de Despesas com Banda de Confiança Estatística")
        if len(pivot_graf) >= 2:
            x_vals = np.arange(len(pivot_graf))
            y_vals = pivot_graf["Despesa"].values
            a_d, b_d = np.polyfit(x_vals, y_vals, 1)
            desvio_padrao_desp = y_vals.std() if len(y_vals) > 1 else 100.0
            
            dados_banda = []
            ultimo_dt = datetime.strptime(pivot_graf["AnoMes"].max() + "-01", "%Y-%m-%d")
            
            for step in range(1, 7):
                fut_dt = ultimo_dt + relativedelta(months=step)
                fut_str = fut_dt.strftime("%Y-%m")
                x_fut = len(pivot_graf) + step - 1
                proj_central = (a_d * x_fut) + b_d
                
                dados_banda.append({"Periodo": fut_str, "Valor": proj_central, "Tipo": "Projeção Esperada"})
                dados_banda.append({"Periodo": fut_str, "Valor": proj_central + (1.96 * desvio_padrao_desp), "Tipo": "Limite Superior (Pessimista)"})
                dados_banda.append({"Periodo": fut_str, "Valor": max(0.0, proj_central - (1.96 * desvio_padrao_desp)), "Tipo": "Limite Inferior (Otimista)"})
                
            df_banda = pd.DataFrame(dados_banda)
            chart_banda = alt.Chart(df_banda).mark_line(strokeWidth=3, point=True).encode(
                x=alt.X('Periodo:N', title='Próximos Meses'),
                y=alt.Y('Valor:Q', title='Despesa Projetada (R$)'),
                color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Projeção Esperada', 'Limite Superior (Pessimista)', 'Limite Inferior (Otimista)'], range=['#f4a261', '#e76f51', '#2a9d8f']))
            ).properties(height=350).interactive()
            st.altair_chart(chart_banda, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar a banda de confiança.")

        st.markdown("---")

        st.markdown("### 3️⃣ Simulação de Atingimento de Meta de Patrimônio (Crescimento Composto)")
        taxa_juros_anual = st.slider("Taxa de Retorno Anual Estimada dos Investimentos (% a.a.)", min_value=0.0, max_value=20.0, value=8.0, step=0.5)
        taxa_mensal = (1 + (taxa_juros_anual / 100.0))**(1/12) - 1
        
        patrimonio_base = saldo_atual_caixa
        poupanca_media_mensal = pivot_graf["CashFlow"].mean() if not pivot_graf.empty else 0.0
        
        dados_patrimonio = []
        patr_acumulado = patrimonio_base
        for m in range(1, 13):
            fut_dt = datetime.today() + relativedelta(months=m)
            patr_acumulado = (patr_acumulado * (1 + taxa_mensal)) + poupanca_media_mensal
            dados_patrimonio.append({
                "Mes": fut_dt.strftime("%Y-%m"),
                "Patrimonio_Projetado": patr_acumulado
            })
            
        df_patr = pd.DataFrame(dados_patrimonio)
        chart_patr = alt.Chart(df_patr).mark_bar(color='#2a9d8f').encode(
            x=alt.X('Mes:N', title='Mês'),
            y=alt.Y('Patrimonio_Projetado:Q', title='Patrimônio Estimado (R$)'),
            tooltip=['Mes', 'Patrimonio_Projetado']
        ).properties(height=350).interactive()
        st.altair_chart(chart_patr, use_container_width=True)

        st.markdown("---")

        st.markdown("### 4️⃣ Gráfico de Tendência de Queima de Caixa (Burn Rate Velocity)")
        pivot_graf["Variacao_Despesa"] = pivot_graf["Despesa"].diff().fillna(0.0)
        chart_burn = alt.Chart(pivot_graf).mark_bar().encode(
            x=alt.X('AnoMes:N', title='Mês'),
            y=alt.Y('Variacao_Despesa:Q', title='Variação Mensal de Gastos (R$)'),
            color=alt.condition(
                alt.datum.Variacao_Despesa > 0,
                alt.value('#e76f51'),
                alt.value('#2a9d8f')
            ),
            tooltip=['AnoMes', 'Variacao_Despesa', 'Despesa']
        ).properties(height=350).interactive()
        st.altair_chart(chart_burn, use_container_width=True)

        st.markdown("---")

        st.markdown("### 5️⃣ Curva ABC de Gastos (Foco em Categorias de Maior Impacto)")
        df_despesas_totais = df[df["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
        if not df_despesas_totais.empty:
            df_despesas_totais = df_despesas_totais.sort_values(by="Valor", ascending=False)
            df_despesas_totais["Acumulado_%"] = (df_despesas_totais["Valor"].cumsum() / df_despesas_totais["Valor"].sum()) * 100
            
            base_abc = alt.Chart(df_despesas_totais).encode(x=alt.X('Categoria:N', sort='-y', title='Categoria'))
            bar_abc = base_abc.mark_bar(color='#264653').encode(y=alt.Y('Valor:Q', title='Gasto Total (R$)'), tooltip=['Categoria', 'Valor'])
            line_abc = base_abc.mark_line(strokeWidth=3, color='#e76f51', point=True).encode(y=alt.Y('Acumulado_%:Q', title='Acumulado (%)', scale=alt.Scale(domain=[0, 105])))
            chart_abc = alt.layer(bar_abc, line_abc).resolve_scale(y='independent').properties(height=350).interactive()
            st.altair_chart(chart_abc, use_container_width=True)
        else:
            st.info("Sem despesas suficientes para calcular a Curva ABC.")

        st.markdown("---")

        st.markdown("### 6️⃣ Equilíbrio Estrutural (Custo Fixo vs Renda)")
        if "Categoria" in df.columns:
            df_fixo = df[(df["Tipo"] == "Despesa") & (df["Categoria"].str.contains("Moradia|Aluguel|Fixa|Conta|Dívida", case=False, na=False))].groupby("AnoMes")["Valor"].sum().reset_index()
            df_flex = pivot_graf[["AnoMes", "Receita"]].merge(df_fixo, on="AnoMes", how="left").fillna(0.0)
            df_flex = df_flex.rename(columns={"Valor": "CustoFixo"})
            
            if not df_flex.empty:
                chart_lev = alt.Chart(df_flex).mark_bar().encode(
                    x=alt.X('AnoMes:N', title='Mês'),
                    y=alt.Y('CustoFixo:Q', title='Valores (R$)'),
                    color=alt.value('#e9c46a'),
                    tooltip=['AnoMes', 'CustoFixo', 'Receita']
                ).properties(height=350).interactive()
                st.altair_chart(chart_lev, use_container_width=True)
        else:
            st.info("Dados insuficientes para alavancagem operacional.")

        st.markdown("---")

        st.markdown("### 7️⃣ Projeção para Independência Financeira (Milestones)")
        meta_patrimonio_indep = st.number_input("Defina sua Meta de Patrimônio para Independência (R$)", value=500000.0, step=50000.0)
        
        dados_indep = []
        patr_indep = saldo_atual_caixa
        for m in range(1, 37):
            fut_dt = datetime.today() + relativedelta(months=m)
            patr_indep = (patr_indep * (1 + taxa_mensal)) + poupanca_media_mensal
            dados_indep.append({"Mes": fut_dt.strftime("%Y-%m"), "Patrimonio": patr_indep, "Meta": meta_patrimonio_indep})
            
        df_indep = pd.DataFrame(dados_indep)
        line_patr = alt.Chart(df_indep).mark_line(strokeWidth=3, color='#2a9d8f').encode(x='Mes:N', y=alt.Y('Patrimonio:Q', title='Capital (R$)'))
        line_meta = alt.Chart(df_indep).mark_line(strokeWidth=2, strokeDash=[5,5], color='#e76f51').encode(x='Mes:N', y='Meta:Q')
        chart_milestone = alt.layer(line_patr, line_meta).properties(height=350).interactive()
        st.altair_chart(chart_milestone, use_container_width=True)

        st.markdown("---")

        st.markdown("### 8️⃣ Mapa de Calor de Sazonalidade de Despesas")
        df_heatmap = df[df["Tipo"] == "Despesa"].copy()
        if not df_heatmap.empty:
            df_heatmap["MesNum"] = df_heatmap["Data"].dt.month
            df_heatmap["MesNome"] = df_heatmap["Data"].dt.strftime("%b")
            pivot_heat = df_heatmap.pivot_table(index="Categoria", columns="MesNome", values="Valor", aggfunc="sum", fill_value=0.0).reset_index()
            df_melted = pivot_heat.melt(id_vars="Categoria", var_name="Mes", value_name="Gasto")
            
            chart_heat = alt.Chart(df_melted).mark_rect().encode(
                x=alt.X('Mes:N', title='Mês'),
                y=alt.Y('Categoria:N', title='Categoria'),
                color=alt.Color('Gasto:Q', scale=alt.Scale(scheme='orangered'), title='Volume de Gastos (R$)'),
                tooltip=['Categoria', 'Mes', 'Gasto']
            ).properties(height=350).interactive()
            st.altair_chart(chart_heat, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar o mapa de calor.")

        st.markdown("---")

        st.markdown("### 9️⃣ Simulação de Monte Carlo Pessoal (Stress Test de Volatilidade)")
        st.markdown("Simula 100 trajetórias estocásticas de caixa baseadas no desvio padrão histórico para avaliar o risco de saldo negativo.")
        if len(pivot_graf) >= 2:
            media_cf = pivot_graf["CashFlow"].mean()
            std_cf = pivot_graf["CashFlow"].std() if len(pivot_graf) > 1 else 100.0
            
            simulacoes_mc = []
            np.random.seed(42)
            for sim in range(100):
                saldo_sim = saldo_atual_caixa
                for m in range(1, 13):
                    fluxo_aleatorio = np.random.normal(media_cf, std_cf)
                    saldo_sim += fluxo_aleatorio
                    simulacoes_mc.append({"Simulacao": sim, "Mes": f"Mês +{m}", "Saldo": saldo_sim})
            
            df_mc = pd.DataFrame(simulacoes_mc)
            chart_mc = alt.Chart(df_mc).mark_line(opacity=0.2, color='#264653').encode(
                x=alt.X('Mes:N', title='Horizonte Futuro'),
                y=alt.Y('Saldo:Q', title='Simulações de Saldo (R$)'),
                detail='Simulacao:N'
            ).properties(height=350).interactive()
            st.altair_chart(chart_mc, use_container_width=True)
        else:
            st.info("Dados insuficientes para rodar a Simulação de Monte Carlo.")

        st.markdown("---")

        st.markdown("### 🔟 Índice de Resiliência de Fluxo de Caixa (Resilience Index)")
        if len(pivot_graf) > 0:
            df_res = pivot_graf.copy()
            df_res["Resiliencia"] = np.clip(((df_res["CashFlow"] / (df_res["Despesa"] + 1)) * 50) + 50, 0, 100)
            
            chart_res = alt.Chart(df_res).mark_bar().encode(
                x=alt.X('AnoMes:N', title='Mês'),
                y=alt.Y('Resiliencia:Q', title='Índice de Resiliência (0 a 100)', scale=alt.Scale(domain=[0, 100])),
                color=alt.condition(
                    alt.datum.Resiliencia >= 50,
                    alt.value('#2a9d8f'),
                    alt.value('#e76f51')
                ),
                tooltip=['AnoMes', 'Resiliencia', 'CashFlow']
            ).properties(height=350).interactive()
            st.altair_chart(chart_res, use_container_width=True)
        else:
            st.info("Dados insuficientes para calcular a resiliência.")

        st.markdown("---")

        st.markdown("### 1️⃣1️⃣ Dispersão de Despesas e Elasticidade (Valor vs Dia do Mês)")
        df_scatter = df[df["Tipo"] == "Despesa"].copy()
        if not df_scatter.empty:
            df_scatter["DiaMes"] = df_scatter["Data"].dt.day
            chart_scat = alt.Chart(df_scatter).mark_circle(size=80).encode(
                x=alt.X('DiaMes:Q', title='Dia do Mês'),
                y=alt.Y('Valor:Q', title='Valor da Despesa (R$)'),
                color=alt.Color('Categoria:N', scale=alt.Scale(scheme='tableau10')),
                tooltip=['Descricao', 'Valor', 'Categoria', 'Data']
            ).properties(height=350).interactive()
            st.altair_chart(chart_scat, use_container_width=True)
        else:
            st.info("Nenhuma despesa para exibir no gráfico de dispersão.")

        st.markdown("---")

        st.markdown("### 1️⃣2️⃣ Índice de Autonomia de Renda Passiva (Financial Freedom Gauge)")
        taxa_retorno_passivo = st.slider("Taxa de Retorno Anual para Renda Passiva (% a.a.)", min_value=1.0, max_value=15.0, value=6.0, step=0.5)
        taxa_mes_passivo = taxa_retorno_passivo / 100.0 / 12.0
        
        media_despesas_anual = pivot_graf["Despesa"].mean() if not pivot_graf.empty else 1.0
        renda_passiva_estimada = saldo_atual_caixa * taxa_mes_passivo
        autonomia_pct = min((renda_passiva_estimada / (media_despesas_anual if media_despesas_anual > 0 else 1.0)) * 100, 100.0)
        
        st.metric("Grau de Independência Atual", f"{autonomia_pct:.2f}% dos gastos cobertos", delta=f"R$ {renda_passiva_estimada:,.2f} / mês de renda passiva teórica")
        st.progress(int(autonomia_pct))
        
    else:
        st.info("Nenhum lançamento registrado para exibir os gráficos analíticos e de projeção.")

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
            
            st.dataframe(aplicar_estilo_tabela(df_audit_fmt.style, subset=["3. Diferença (Budget - Entry)"]), use_container_width=True)
            
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
    st.subheader("📊 Statistical Indicators & Advanced Econometrics")
    st.markdown("Parâmetros estatísticos avançados, assimetria, curtose e detecção de outliers.")
    
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
        pivot_mensal = pivot_mensal.reset_index().sort_values("AnoMes")
        
        if len(pivot_mensal) > 2:
            valores_exp = pivot_mensal["Expense"]
            media_geral = valores_exp.mean()
            desvio_padrao = valores_exp.std() if len(valores_exp) > 1 else 0.0
            
            n_obs = len(valores_exp)
            if desvio_padrao > 0 and n_obs > 2:
                skewness = (n_obs / ((n_obs - 1) * (n_obs - 2))) * np.sum(((valores_exp - media_geral) / desvio_padrao)**3)
                kurtosis = ((n_obs * (n_obs + 1)) / ((n_obs - 1) * (n_obs - 2) * (n_obs - 3))) * np.sum(((valores_exp - media_geral) / desvio_padrao)**4) - (3 * (n_obs - 1)**2 / ((n_obs - 2) * (n_obs - 3)))
            else:
                skewness, kurtosis = 0.0, 0.0
                
            col_stat1, col_stat2 = st.columns(2)
            col_stat1.metric("📐 Assimetria de Gastos (Skewness)", f"{skewness:.2f}", delta="> 0 indica cauda longa à direita")
            col_stat2.metric("⛰️ Curtose de Despesas (Kurtosis)", f"{kurtosis:.2f}", delta="Achatamento da distribuição")
            
            st.markdown("---")
            st.markdown("### 📌 Z-Score, Outliers e Indicadores Mensais")
            
            dados_stats = []
            for idx, row in pivot_mensal.iterrows():
                m = row["AnoMes"]
                val = row["Expense"]
                z_score = (val - media_geral) / desvio_padrao if desvio_padrao > 0 else 0.0
                
                if abs(z_score) > 2.0:
                    interpretacao = "🚨 Outlier Estatístico (Anomalia Severa)"
                elif z_score > 1.0:
                    interpretacao = "⚠️ Acima do Limiar de Confiança"
                elif z_score < -1.0:
                    interpretacao = "🌟 Otimizado (Excelente Economia)"
                else:
                    interpretacao = "✅ Dentro da Banda de Normalidade"
                
                dados_stats.append({
                    "Mês": m,
                    "Total Expenses": f"R$ {val:,.2f}",
                    "Média Histórica": f"R$ {media_geral:,.2f}",
                    "Desvio Padrão": f"R$ {desvio_padrao:,.2f}",
                    "Z-Score": round(z_score, 2),
                    "Status Analítico": interpretacao
                })
                
            st.dataframe(aplicar_estilo_tabela(pd.DataFrame(dados_stats).set_index("Mês").style), use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📈 Histograma de Densidade de Gastos Mensais")
            chart_hist = alt.Chart(pivot_mensal).mark_bar(color='#264653').encode(
                x=alt.X('Expense:Q', bin=True, title='Faixas de Despesa (R$)'),
                y=alt.Y('count()', title='Frequência de Ocorrência (Meses)'),
                tooltip=['count()']
            ).properties(height=300).interactive()
            st.altair_chart(chart_hist, use_container_width=True)
            
        else:
            st.info("Requer pelo menos 3 meses registrados para calcular métricas estatísticas avançadas (Skewness/Kurtosis).")
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
    st.subheader("Lista de Lançamentos & Smart Search")
    st.markdown("Utilize a ferramenta de **Smart Search** para filtrar transações instantaneamente por termo, categoria, conta ou status.")
    
    df = st.session_state.lancamentos
    if not df.empty:
        col_s1, col_s2, col_s3 = st.columns([3, 2, 2])
        with col_s1:
            termo_busca = st.text_input("🔍 Smart Search (Pesquisa Inteligente)", placeholder="Digite descrição, categoria ou conta...")
        with col_s2:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Receita", "Despesa"])
        with col_s3:
            filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Budget", "Efetivado"])
            
        df_filtrado = df.copy()
        
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]
        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]
            
        if termo_busca.strip() != "":
            termo = termo_busca.strip().lower()
            mask = (
                df_filtrado["Descricao"].astype(str).str.lower().str.contains(termo, na=False) |
                df_filtrado["Categoria"].astype(str).str.lower().str.contains(termo, na=False) |
                df_filtrado["Conta"].astype(str).str.lower().str.contains(termo, na=False)
            )
            df_filtrado = df_filtrado[mask]
            
        st.markdown(f"Exibindo **{len(df_filtrado)}** de **{len(df)}** registros encontrados.")
        
        if not df_filtrado.empty:
            df_lanc_fmt = df_filtrado.copy()
            df_lanc_fmt["Valor"] = df_lanc_fmt["Valor"].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(aplicar_estilo_tabela(df_lanc_fmt.style), use_container_width=True)
        else:
            st.warning("Nenhum lançamento corresponde ao filtro ou Smart Search informado.")
            
        st.markdown("---")
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
            df_cartoes_fmt["Limite"] = df_cartoes_fmt["Limite"].apply(lambda x: f5 := f"R$ {x:,.2f}")
        st.dataframe(aplicar_estilo_tabela(df_cartoes_fmt.style), use_container_width=True)

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
