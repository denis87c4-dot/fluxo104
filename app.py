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
    if "ContaDestino" not in st.session_state.lancamentos.columns:
        st.session_state.lancamentos["ContaDestino"] = ""
else:
    st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Status", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor", "Data", "Parcela"])

if os.path.exists(ARQUIVO_CATEGORIAS):
    df_cat = pd.read_csv(ARQUIVO_CATEGORIAS)
    st.session_state.categorias = df_cat["Categoria"].tolist()
else:
    st.session_state.categorias = ["Food", "Transporte", "Moradia", "Lazer", "Transferência", "Outros"]

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

def aplicar_estilo_tabela(df_styled, subset=None):
    try:
        if hasattr(df_styled, "map"):
            return df_styled.map(colorir_negativos, subset=subset)
        else:
            return df_styled.applymap(colorir_negativos, subset=subset)
    except Exception:
        return df_styled

aba = st.sidebar.radio("Navegação", ["Dashboard", "Resumo Geral", "Projections & Charts", "Monthly Audit", "Financial Indicators", "Statistical Indicators", "Cadastro (Form)", "Lançamentos", "Cartões", "Gerenciar Categorias"])

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
        
        cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []

        despesas_conta_corrente = df_mes_atual[
            (df_mes_atual["Tipo"] == "Despesa") & 
            (df_mes_atual["Status"] == "Efetivado") & 
            (~df_mes_atual["Conta"].isin(cartoes_nomes))
        ]["Valor"].sum()

        despesas_ant_cc = df_mes_ant[
            (df_mes_ant["Tipo"] == "Despesa") & 
            (df_mes_ant["Status"] == "Efetivado") & 
            (~df_mes_ant["Conta"].isin(cartoes_nomes))
        ]["Valor"].sum()
        delta_desp = ((despesas_conta_corrente - despesas_ant_cc) / despesas_ant_cc * 100) if despesas_ant_cc > 0 else 0.0
        
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
            
        saldo_liquido_real = receitas_mes - despesas_conta_corrente

        despesas_cartao_mes = df_mes_atual[
            (df_mes_atual["Tipo"] == "Despesa") & 
            (df_mes_atual["Conta"].isin(cartoes_nomes))
        ]["Valor"].sum()

        net_savings_rate = ((receitas_mes - despesas_conta_corrente) / receitas_mes * 100) if receitas_mes > 0 else 0.0
        comprometimento_renda = (despesas_conta_corrente / receitas_mes * 100) if receitas_mes > 0 else 0.0

        contas_liquidas_mes = df_mes_atual[(df_mes_atual["Tipo"] == "Receita") & (~df_mes_atual["Conta"].isin(cartoes_nomes))]["Valor"].sum()
        cash_ratio_val = (contas_liquidas_mes / despesas_conta_corrente) if despesas_conta_corrente > 0 else 0.0
        burn_rate_val = abs(saldo_liquido_real) if saldo_liquido_real < 0 else 0.0
    else:
        df_mes_atual = pd.DataFrame()
        receitas_mes = 0.0
        despesas_conta_corrente = 0.0
        despesas_cartao_mes = 0.0
        budget_despesas = 0.0
        budget_receitas = 0.0
        despesas_vencidas = 0.0
        texto_vencidas_detalhe = "<span style='color: #2a9d8f; font-weight: bold;'>R$ 0,00</span>"
        delta_rec = 0.0
        delta_desp = 0.0
        saldo_liquido_real = 0.0
        df_vencidas = pd.DataFrame()
        mes_selecionado = datetime.today().strftime("%Y-%m")
        net_savings_rate = 0.0
        comprometimento_renda = 0.0
        cash_ratio_val = 0.0
        burn_rate_val = 0.0

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📈 RECEITAS DO MÊS", f"R$ {receitas_mes:,.2f}", delta=f"{delta_rec:+.1f}% vs mês ant.")
    with col2:
        st.metric("📉 DESPESAS (C/C)", f"R$ {despesas_conta_corrente:,.2f}", delta=f"{delta_desp:+.1f}% vs mês ant.", delta_color="inverse")
    with col3:
        st.metric("💳 PASSIVO CARTÕES (Fatura)", f"R$ {despesas_cartao_mes:,.2f}", delta="Saldo Devedor", delta_color="inverse")
    with col4:
        st.metric("💵 SALDO LÍQUIDO REAL", f"R$ {saldo_liquido_real:,.2f}", delta="Caixa Imediato", delta_color="normal")

    st.markdown("### 📌 Indicadores Executivos Adicionais")
    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
    with col_n1:
        st.metric("💰 TAXA DE POUPANÇA", f"{net_savings_rate:.1f}%", delta="Net Savings Rate", delta_color="normal")
    with col_n2:
        st.metric("📊 COMPROP. DE RENDA", f"{comprometimento_renda:.1f}%", delta="Gastos / Receitas", delta_color="inverse")
    with col_n3:
        st.metric("🛡️ CASH RATIO", f"{cash_ratio_val:.2f}x", delta="Liquidez Imediata", delta_color="normal")
    with col_n4:
        st.metric("🔥 BURN RATE", f"R$ {burn_rate_val:,.2f}", delta="Queima de Caixa", delta_color="inverse")

    st.markdown("---")

    st.markdown("### 🗓️ Histórico Consolidado por Mês")
    st.markdown("Tabela geral contemplando **Income**, **Expense (C/C)**, **Passivo Cartões** e **Cash Flow** ordenados temporalmente.")
    
    if not df.empty:
        df_hist = df.copy()
        cartoes_nomes_hist = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []
        
        df_hist["Expense_CC"] = df_hist.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] not in cartoes_nomes_hist else 0.0, axis=1)
        df_hist["Expense_Card"] = df_hist.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] in cartoes_nomes_hist else 0.0, axis=1)
        df_hist["Income_Val"] = df_hist.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)
        
        pivot_hist = df_hist.pivot_table(index="AnoMes", values=["Income_Val", "Expense_CC", "Expense_Card"], aggfunc="sum", fill_value=0.0).reset_index()
        pivot_hist = pivot_hist.rename(columns={"AnoMes": "Mês", "Income_Val": "Income", "Expense_CC": "Expense (C/C)", "Expense_Card": "Passivo Cartão"})
        pivot_hist = pivot_hist.sort_values("Mês").reset_index(drop=True)
        
        pivot_hist["Cash Flow"] = pivot_hist["Income"] - pivot_hist["Expense (C/C)"]
        pivot_hist["Acumulado"] = pivot_hist["Cash Flow"].cumsum()
        
        pivot_hist = pivot_hist[["Mês", "Income", "Expense (C/C)", "Passivo Cartão", "Cash Flow", "Acumulado"]]
        
        pivot_hist_fmt = pivot_hist.copy()
        for col in ["Income", "Expense (C/C)", "Passivo Cartão", "Cash Flow", "Acumulado"]:
            pivot_hist_fmt[col] = pivot_hist_fmt[col].apply(lambda x: f"R$ {x:,.2f}")
            
        st.dataframe(aplicar_estilo_tabela(pivot_hist_fmt.set_index("Mês").style, subset=["Cash Flow", "Acumulado"]), use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("### 📈 Gráficos Comparativos de Evolução")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### 1️⃣ Income vs Expense (C/C) vs Cartão")
            df_melt_ie = pivot_hist.melt(id_vars="Mês", value_vars=["Income", "Expense (C/C)", "Passivo Cartão"], var_name="Métrica", value_name="Valor")
            chart_ie = alt.Chart(df_melt_ie).mark_line(strokeWidth=3, point=True).encode(
                x=alt.X('Mês:N', title='Mês'),
                y=alt.Y('Valor:Q', title='Montante (R$)'),
                color=alt.Color('Métrica:N', scale=alt.Scale(domain=['Income', 'Expense (C/C)', 'Passivo Cartão'], range=['#2a9d8f', '#e76f51', '#f4a261']), title='Legenda'),
                tooltip=['Mês', 'Métrica', 'Valor']
            ).properties(height=320).interactive()
            st.altair_chart(chart_ie, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 2️⃣ Cash Flow vs Acumulado")
            df_melt_ca = pivot_hist.melt(id_vars="Mês", value_vars=["Cash Flow", "Acumulado"], var_name="Métrica", value_name="Valor")
            chart_ca = alt.Chart(df_melt_ca).mark_line(strokeWidth=3, point=True).encode(
                x=alt.X('Mês:N', title='Mês'),
                y=alt.Y('Valor:Q', title='Montante (R$)'),
                color=alt.Color('Métrica:N', scale=alt.Scale(domain=['Cash Flow', 'Acumulado'], range=['#264653', '#2a9d8f']), title='Legenda'),
                tooltip=['Mês', 'Métrica', 'Valor']
            ).properties(height=320).interactive()
            st.altair_chart(chart_ca, use_container_width=True)
            
    else:
        st.info("Nenhum lançamento registrado para exibir a tabela consolidada e os gráficos.")

elif aba == "Resumo Geral":
    st.subheader("📋 Resumo Geral - Efetivados por Mês")
    st.markdown("Visão consolidada e limpa das Entradas, Saídas e Transferências estritamente **Efetivadas** no mês selecionado.")
    
    df = st.session_state.lancamentos
    
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)
        
        meses_disponiveis = sorted(df["AnoMes"].unique().tolist(), reverse=True)
        mes_atual_padrao = datetime.today().strftime("%Y-%m")
        if mes_atual_padrao not in meses_disponiveis:
            meses_disponiveis.insert(0, mes_atual_padrao)
            
        st.markdown("### 🎛️ Célula Suspensa: Seleção de Período")
        col_sel1, col_sel2 = st.columns([2, 4])
        with col_sel1:
            mes_selecionado_rg = st.selectbox("📅 Selecione o Mês (Ano-Mês)", meses_disponiveis, key="sel_mes_resumo_geral")
        
        ano_sel, mes_sel = map(int, mes_selecionado_rg.split("-"))
        
        df_mes_efetivado = df[
            (df["Data"].dt.year == ano_sel) & 
            (df["Data"].dt.month == mes_sel) & 
            (df["Status"] == "Efetivado")
        ]
        
        cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []
        total_entradas = df_mes_efetivado[df_mes_efetivado["Tipo"] == "Receita"]["Valor"].sum()
        
        total_saidas_cc = df_mes_efetivado[
            (df_mes_efetivado["Tipo"] == "Despesa") & 
            (~df_mes_efetivado["Conta"].isin(cartoes_nomes))
        ]["Valor"].sum()

        total_passivo_cartao = df_mes_efetivado[
            (df_mes_efetivado["Tipo"] == "Despesa") & 
            (df_mes_efetivado["Conta"].isin(cartoes_nomes))
        ]["Valor"].sum()

        total_transferencias = df_mes_efetivado[df_mes_efetivado["Tipo"] == "Transferência"]["Valor"].sum()
        saldo_liquido_efetivado = total_entradas - total_saidas_cc
        
        st.markdown("---")
        
        col_rg1, col_rg2, col_rg3, col_rg4, col_rg5 = st.columns(5)
        with col_rg1:
            st.metric("🟢 Total Entradas", f"R$ {total_entradas:,.2f}", delta="Efetivado")
        with col_rg2:
            st.metric("🔴 Saídas (C/C)", f"R$ {total_saidas_cc:,.2f}", delta="Efetivado", delta_color="inverse")
        with col_rg3:
            st.metric("💳 Passivo Cartão", f"R$ {total_passivo_cartao:,.2f}", delta="Saldo Devedor", delta_color="inverse")
        with col_rg4:
            st.metric("🔵 Transferências", f"R$ {total_transferencias:,.2f}", delta="Efetivado")
        with col_rg5:
            st.metric("💰 Saldo Líquido", f"R$ {saldo_liquido_efetivado:,.2f}", delta="Caixa Real", delta_color="normal")
            
        st.markdown("---")
        st.markdown(f"### 📄 Detalhamento dos Lançamentos Efetivados ({mes_selecionado_rg})")
        
        if not df_mes_efetivado.empty:
            df_exibicao = df_mes_efetivado[["Tipo", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor", "Data", "Parcela"]].copy()
            df_exibicao["Valor"] = df_exibicao["Valor"].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(aplicar_estilo_tabela(df_exibicao.style), use_container_width=True)
        else:
            st.info(f"Nenhum lançamento com status **Efetivado** encontrado para o período de {mes_selecionado_rg}.")
    else:
        st.info("Nenhum lançamento cadastrado no sistema.")

elif aba == "Projections & Charts":
    st.subheader("📈 Projections & Charts (12 Gráficos e Parâmetros Avançados de Elite)")
    st.markdown("Central completa contendo a **Célula Suspensa** e módulos analíticos de projeção, risco e inteligência financeira.")
    
    df = st.session_state.lancamentos
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)
        
        cartoes_nomes_proj = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []
        df["Expense_CC"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] not in cartoes_nomes_proj else 0.0, axis=1)
        df["Income_Val"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)
        
        pivot_graf = df.pivot_table(index="AnoMes", values=["Income_Val", "Expense_CC"], aggfunc="sum", fill_value=0.0).reset_index()
        pivot_graf = pivot_graf.rename(columns={"Income_Val": "Receita", "Expense_CC": "Despesa"})
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
        st.progress(int(max(0, min(100, autonomia_pct))))
        
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
        tipo = st.selectbox("Tipo", ["Despesa", "Receita", "Transferência"])
    with col_b:
        status = st.selectbox("Status / Fase", ["Budget", "Efetivado"])
        
    descricao = st.text_input("Descrição", placeholder="Ex: Gas, Supermercado, Pagamento de Fatura...")
    
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

    conta_final = ""
    conta_destino_final = ""
    cartao_selecionado_row = None

    if tipo == "Transferência":
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            conta_saida_escolhida = st.selectbox("Conta Saída (Origem)", contas_base + ["+ Incluir Novo Cartão/Conta..."])
            conta_final = conta_saida_escolhida
            if conta_saida_escolhida == "+ Incluir Novo Cartão/Conta...":
                novo_c_digitado = st.text_input("Digite o nome da Conta Saída:")
                if novo_c_digitado.strip() != "":
                    conta_final = novo_c_digitado.strip()
                    novo_c_df = pd.DataFrame([{"Nome": conta_final, "Fechamento": 10, "Limite": 1000.0, "Vencimento": 17}])
                    st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_c_df], ignore_index=True)
                    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
        with col_t2:
            conta_destino_escolhida = st.selectbox("Conta Destino", contas_base + ["+ Incluir Novo Cartão/Conta..."])
            conta_destino_final = conta_destino_escolhida
            if conta_destino_escolhida == "+ Incluir Novo Cartão/Conta...":
                novo_d_digitado = st.text_input("Digite o nome da Conta Destino:")
                if novo_d_digitado.strip() != "":
                    conta_destino_final = novo_d_digitado.strip()
                    novo_d_df = pd.DataFrame([{"Nome": conta_destino_final, "Fechamento": 10, "Limite": 1000.0, "Vencimento": 17}])
                    st.session_state.cartoes = pd.concat([st.session_state.cartoes, novo_d_df], ignore_index=True)
                    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
        categoria_final = "Transferência"
    else:
        conta_escolhida = st.selectbox("Account (Conta / Cartão)", contas_base + ["+ Incluir Novo Cartão/Conta..."])
        conta_final = conta_escolhida
        
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
            
            eh_cartao = (tipo == "Despesa" and cartao_selecionado_row is not None and "Fechamento" in cartao_selecionado_row)
            dia_fechamento = int(cartao_selecionado_row["Fechamento"]) if eh_cartao else 0
            dia_vencimento = int(cartao_selecionado_row["Vencimento"]) if (eh_cartao and "Vencimento" in cartao_selecionado_row) else 10
            
            for i in range(parcelas):
                if frequencia == "Mensal":
                    data_base_parcela = data_compra + relativedelta(months=i)
                elif frequencia == "Quinzenal":
                    data_base_parcela = data_compra + relativedelta(weeks=2*i)
                elif frequencia == "Anual":
                    data_base_parcela = data_compra + relativedelta(years=i)
                else:
                    data_base_parcela = data_compra

                data_fatura_parcela = data_base_parcela
                if eh_cartao and dia_fechamento > 0:
                    if (i == 0 and data_compra.day > dia_fechamento) or (i > 0):
                        data_fatura_parcela = data_base_parcela + relativedelta(months=1) if i == 0 else data_base_parcela + relativedelta(months=1)
                    
                    try:
                        data_fatura_parcela = data_fatura_parcela.replace(day=min(dia_vencimento, 28))
                    except:
                        pass

                if modo_valor == "Dividir Total" and parcelas > 0:
                    valor_parcela = valor_total / parcelas
                else:
                    valor_parcela = valor_total

                desc_formatada = f"{descricao} ({i+1}/{parcelas})" if parcelas > 1 else descricao

                if eh_cartao:
                    novos_registros.append({
                        "Tipo": tipo,
                        "Status": "Efetivado",
                        "Descricao": f"[Compra Cartão] {desc_formatada}",
                        "Categoria": categoria_final,
                        "Conta": conta_final,
                        "ContaDestino": "",
                        "Valor": round(valor_parcela, 2),
                        "Data": str(data_compra if i == 0 else data_base_parcela),
                        "Parcela": f"{i+1}/{parcelas}"
                    })

                    novos_registros.append({
                        "Tipo": tipo,
                        "Status": "Budget",
                        "Descricao": f"[Fatura Foco] {desc_formatada}",
                        "Categoria": categoria_final,
                        "Conta": conta_final,
                        "ContaDestino": "",
                        "Valor": round(valor_parcela, 2),
                        "Data": str(data_fatura_parcela),
                        "Parcela": f"{i+1}/{parcelas}"
                    })
                else:
                    novos_registros.append({
                        "Tipo": tipo,
                        "Status": status,
                        "Descricao": desc_formatada,
                        "Categoria": categoria_final,
                        "Conta": conta_final,
                        "ContaDestino": conta_destino_final if tipo == "Transferência" else "",
                        "Valor": round(valor_parcela, 2),
                        "Data": str(data_base_parcela),
                        "Parcela": f"{i+1}/{parcelas}"
                    })

            df_novo = pd.DataFrame(novos_registros)
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, df_novo], ignore_index=True)
            st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
            
            if tipo != "Transferência" and cartao_selecionado_row is not None:
                nome_c_alvo = cartao_selecionado_row["Nome"]
                idx_cartao = st.session_state.cartoes[st.session_state.cartoes["Nome"] == nome_c_alvo].index
                if not idx_cartao.empty:
                    limite_atual = float(st.session_state.cartoes.loc[idx_cartao[0], "Limite"])
                    novo_limite = max(0.0, limite_atual - valor_total)
                    st.session_state.cartoes.loc[idx_cartao[0], "Limite"] = novo_limite
                    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)

            if tipo == "Transferência" and not st.session_state.cartoes.empty and conta_destino_final in st.session_state.cartoes["Nome"].values:
                idx_cartao_dest = st.session_state.cartoes[st.session_state.cartoes["Nome"] == conta_destino_final].index
                if not idx_cartao_dest.empty:
                    limite_atual = float(st.session_state.cartoes.loc[idx_cartao_dest[0], "Limite"])
                    novo_limite = limite_atual + valor_total
                    st.session_state.cartoes.loc[idx_cartao_dest[0], "Limite"] = novo_limite
                    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)

            st.success(f"Lançamento(s) gerado(s) com sucesso!")

elif aba == "Lançamentos":
    st.subheader("Lista de Lançamentos & Smart Search (Gerenciamento)")
    st.markdown("Utilize a ferramenta de **Smart Search** para filtrar transações instantaneamente e gerenciar cada registro (Editar ou Deletar).")
    
    df = st.session_state.lancamentos
    if not df.empty:
        col_s1, col_s2, col_s3 = st.columns([3, 2, 2])
        with col_s1:
            termo_busca = st.text_input("🔍 Smart Search (Pesquisa Inteligente)", placeholder="Digite descrição, categoria ou conta...")
        with col_s2:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Receita", "Despesa", "Transferência"])
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
            for idx, row in df_filtrado.iterrows():
                with st.expander(f"[{row['Tipo']}] {row['Data']} - {row['Descricao']} | R$ {row['Valor']:,.2f} ({row['Status']})"):
                    col_det1, col_det2 = st.columns(2)
                    with col_det1:
                        st.write(f"**Categoria:** {row['Categoria']}")
                        st.write(f"**Conta (Saída):** {row['Conta']}")
                        if row["Tipo"] == "Transferência":
                            st.write(f"**Conta Destino:** {row.get('ContaDestino', '')}")
                    with col_det2:
                        st.write(f"**Parcela:** {row['Parcela']}")
                        st.write(f"**Status:** {row['Status']}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("🗑️ Deletar Lançamento", key=f"del_{idx}", type="secondary"):
                            st.session_state.lancamentos = st.session_state.lancamentos.drop(idx).reset_index(drop=True)
                            st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
                            st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
                            st.success("Lançamento deletado com sucesso!")
                            st.rerun()
                    with col_btn2:
                        edit_key = f"editar_toggle_{idx}"
                        if st.button("✏️ Editar Lançamento", key=f"edit_btn_{idx}"):
                            st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                    
                    if st.session_state.get(f"editar_toggle_{idx}", False):
                        with st.form(key=f"form_edit_{idx}"):
                            st.markdown(f"### Editando Registro #{idx}")
                            tipos_disp = ["Despesa", "Receita", "Transferência"]
                            idx_tipo = tipos_disp.index(row["Tipo"]) if row["Tipo"] in tipos_disp else 0
                            novo_tipo = st.selectbox("Tipo", tipos_disp, index=idx_tipo, key=f"et_{idx}")
                            novo_status = st.selectbox("Status", ["Budget", "Efetivado"], index=0 if row["Status"] == "Budget" else 1, key=f"es_{idx}")
                            nova_desc = st.text_input("Descrição", value=row["Descricao"], key=f"ed_{idx}")
                            
                            idx_cat = st.session_state.categorias.index(row["Categoria"]) if row["Categoria"] in st.session_state.categorias else 0
                            nova_cat = st.selectbox("Categoria", st.session_state.categorias, index=idx_cat, key=f"ec_{idx}")
                            
                            contas_possiveis = ["Cash husband", "Nubank"]
                            if not st.session_state.cartoes.empty:
                                contas_possiveis.extend(st.session_state.cartoes["Nome"].tolist())
                            idx_conta = contas_possiveis.index(row["Conta"]) if row["Conta"] in contas_possiveis else 0
                            nova_conta = st.selectbox("Conta (Saída)", contas_possiveis, index=idx_conta, key=f"econta_{idx}")
                            
                            nova_conta_dest = ""
                            if novo_tipo == "Transferência":
                                idx_conta_dest = contas_possiveis.index(row.get("ContaDestino", "")) if row.get("ContaDestino", "") in contas_possiveis else 0
                                nova_conta_dest = st.selectbox("Conta Destino", contas_possiveis, index=idx_conta_dest, key=f"econta_dest_{idx}")

                            novo_valor = st.number_input("Valor (R$)", value=float(row["Valor"]), format="%.2f", key=f"ev_{idx}")
                            
                            try:
                                data_parsed = datetime.strptime(str(row["Data"]).split()[0], "%Y-%m-%d").date()
                            except:
                                data_parsed = datetime.today().date()
                            nova_data = st.date_input("Data", value=data_parsed, key=f"edata_{idx}")
                            
                            salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
                            if salvar_edicao:
                                st.session_state.lancamentos.loc[idx, "Tipo"] = novo_tipo
                                st.session_state.lancamentos.loc[idx, "Status"] = novo_status
                                st.session_state.lancamentos.loc[idx, "Descricao"] = nova_desc
                                st.session_state.lancamentos.loc[idx, "Categoria"] = nova_cat
                                st.session_state.lancamentos.loc[idx, "Conta"] = nova_conta
                                st.session_state.lancamentos.loc[idx, "ContaDestino"] = nova_conta_dest if novo_tipo == "Transferência" else ""
                                st.session_state.lancamentos.loc[idx, "Valor"] = float(novo_valor)
                                st.session_state.lancamentos.loc[idx, "Data"] = str(nova_data)
                                
                                st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
                                st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
                                
                                st.session_state[edit_key] = False
                                st.success("Lançamento atualizado com sucesso!")
                                st.rerun()
        else:
            st.warning("Nenhum lançamento corresponde ao filtro ou Smart Search informado.")
            
        st.markdown("---")
        if st.button("🗑️ Limpar Todos os Lançamentos"):
            st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Status", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor", "Data", "Parcela"])
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
                st.rerun()

    st.markdown("### 📋 Cartões Cadastrados e Gerenciamento")
    if not st.session_state.cartoes.empty:
        for idx, row in st.session_state.cartoes.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{row['Nome']}** | Fechamento: dia {row['Fechamento']} | Vencimento: dia {row['Vencimento']} | Limite: R$ {row['Limite']:,.2f}")
            
            tem_lancamento = False
            if not st.session_state.lancamentos.empty and "Conta" in st.session_state.lancamentos.columns:
                tem_lancamento = (st.session_state.lancamentos['Conta'] == row['Nome']).any()
            
            if col2.button("🗑️ Excluir", key=f"del_cartao_{idx}"):
                if tem_lancamento:
                    st.error(f"Não é possível excluir '{row['Nome']}': existem lançamentos vinculados a esta conta.")
                else:
                    st.session_state.cartoes = st.session_state.cartoes.drop(idx).reset_index(drop=True)
                    st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
                    st.success(f"Cartão '{row['Nome']}' removido com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum cartão ou conta cadastrado.")

elif aba == "Gerenciar Categorias":
    st.subheader("📂 Gerenciamento de Categorias")
    nova_cat = st.text_input("Nome da Nova Categorias")
    if st.button("Adicionar Categoria"):
        if nova_cat.strip() != "" and nova_cat not in st.session_state.categorias:
            st.session_state.categorias.append(nova_cat)
            pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
            st.success("Categoria adicionada e salva!")
    for cat in st.session_state.categorias:
        st.write(f"- {cat}")
