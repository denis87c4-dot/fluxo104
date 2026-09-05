import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io
import zipfile


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

# ==================== FUNÇÕES DE BACKUP ====================
def salvar_backup():
    try:
        st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
        st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
        pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
        st.success("💾 Backup realizado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar backup: {e}")

def salvar_backup_automatico():
    try:
        st.session_state.lancamentos.to_csv(ARQUIVO_LANCAMENTOS, index=False)
        st.session_state.cartoes.to_csv(ARQUIVO_CARTOES, index=False)
        pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
    except:
        pass  # silencioso

salvar_backup_automatico()

# ==================== FUNÇÃO DE ESTILO ====================
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

# ==================== NAVEGAÇÃO ====================
aba = st.sidebar.radio("Navegação", [
    "Dashboard", "Dashboard 3", "Resumo Geral", "Projections & Charts", "Monthly Audit 3", "Monthly Audit",
    "Financial Indicators", "Statistical Indicators", "Statistical 2", "Cadastro (Form)",
    "Lançamentos", "Cartões", "Gerenciar Categorias"
])

# ==================== CENTRAL DE BACKUP ROBUSTA ====================
st.sidebar.markdown("### 🔐 Central de Backup & Segurança")

if st.sidebar.button("💾 Salvar Backup Local"):
    salvar_backup()

arquivos_para_backup = [ARQUIVO_LANCAMENTOS, ARQUIVO_CARTOES, ARQUIVO_CATEGORIAS]
arquivos_existentes = [f for f in arquivos_para_backup if os.path.exists(f)]

if arquivos_existentes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for arq in arquivos_existentes:
            zip_file.write(arq)
    zip_buffer.seek(0)
    
    st.sidebar.download_button(
        label="📥 Baixar Backup Completo (.zip)",
        data=zip_buffer,
        file_name=f"backup_fluxo104_{datetime.today().strftime('%Y-%m-%d')}.zip",
        mime="application/zip",
        help="Baixe seus arquivos CSV salvos para o seu computador."
    )

st.sidebar.markdown("---")
st.sidebar.markdown("#### 🔄 Restaurar Backup")
arquivo_upload = st.sidebar.file_uploader("Envie seu arquivo ZIP de backup", type="zip")

if arquivo_upload is not None:
    try:
        with zipfile.ZipFile(arquivo_upload, "r") as zip_ref:
            zip_ref.extractall(".")
        st.sidebar.success("✅ Dados restaurados com sucesso! Recarregue a página.")
        if st.sidebar.button("🔄 Recarregar App"):
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao restaurar arquivo: {e}")

# ==================== BLOCOS DAS ABAS ====================

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

        df_cartoes_mes = df_mes_atual[
            (df_mes_atual["Tipo"] == "Despesa") & 
            (df_mes_atual["Conta"].isin(cartoes_nomes)) &
            (df_mes_atual["Status"] == "Budget")
        ]
        despesas_por_cartao = df_cartoes_mes.groupby("Conta")["Valor"].sum() if not df_cartoes_mes.empty else pd.Series(dtype=float)
        despesas_cartao_mes = df_cartoes_mes["Valor"].sum()

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
        despesas_por_cartao = pd.Series(dtype=float)
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
        if not despesas_por_cartao.empty:
            for cartao, val in despesas_por_cartao.items():
                st.markdown(f"<small>• <b>{cartao}</b>: R$ {val:,.2f}</small>", unsafe_allow_html=True)
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
        status_opcoes = ["Todos", "Efetivado", "Budget"]
        status_selecionado = st.selectbox("📌 Filtrar por Status", status_opcoes, index=0)

        df_hist = df.copy()
        cartoes_nomes_hist = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []

        if status_selecionado != "Todos":
            df_hist = df_hist[df_hist["Status"] == status_selecionado]

        df_hist["Expense_CC"] = df_hist.apply(
            lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] not in cartoes_nomes_hist else 0.0, axis=1
        )
        df_hist["Expense_Card"] = df_hist.apply(
            lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] in cartoes_nomes_hist else 0.0, axis=1
        )
        df_hist["Income_Val"] = df_hist.apply(
            lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1
        )

        pivot_hist = df_hist.pivot_table(
            index="AnoMes",
            values=["Income_Val", "Expense_CC", "Expense_Card"],
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        pivot_hist = pivot_hist.rename(columns={
            "AnoMes": "Mês",
            "Income_Val": "Income",
            "Expense_CC": "Expense (C/C)",
            "Expense_Card": "Passivo Cartão"
        })

        pivot_hist = pivot_hist.sort_values("Mês").reset_index(drop=True)
        pivot_hist["Cash Flow"] = pivot_hist["Income"] - pivot_hist["Expense (C/C)"]
        pivot_hist["Acumulado"] = pivot_hist["Cash Flow"].cumsum()

        pivot_hist_fmt = pivot_hist.copy()
        for col in ["Income", "Expense (C/C)", "Passivo Cartão", "Cash Flow", "Acumulado"]:
            pivot_hist_fmt[col] = pivot_hist_fmt[col].apply(lambda x: f"R$ {x:,.2f}")

        st.dataframe(
            aplicar_estilo_tabela(pivot_hist_fmt.set_index("Mês").style, subset=["Cash Flow", "Acumulado"]),
            use_container_width=True
        )

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

elif aba == "Dashboard 3":
    st.subheader("📊 Dashboard 3 - Painel Executivo Pessoal de Alta Performance")
    st.markdown("Visão analítica avançada voltada para **finanças pessoais**, equipada com múltiplos filtros dinâmicos, indicadores de comportamento patrimonial e autonomia financeira.")

    df = st.session_state.lancamentos
    if not df.empty:
        # Tratamento inicial de dados
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []

        # ==================== BLOCO DE FILTROS AVANÇADOS ====================
        with st.expander("🔍 Painel de Filtros Avançados (Obrigatório: Datas e Critérios Múltiplos)", expanded=True):
            # Linha 1 de Filtros
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                status_sel = st.selectbox("📌 Status", ["Todos", "Efetivado", "Budget"], key="d3_status")
            with col_f2:
                tipo_sel = st.multiselect("📂 Tipo de Lançamento", df["Tipo"].unique().tolist(), default=df["Tipo"].unique().tolist(), key="d3_tipo")
            with col_f3:
                categoria_sel = st.multiselect("🏷️ Categoria", df["Categoria"].unique().tolist(), default=df["Categoria"].unique().tolist(), key="d3_cat")
            with col_f4:
                conta_sel = st.multiselect("🏦 Conta / Instituição", df["Conta"].unique().tolist(), default=df["Conta"].unique().tolist(), key="d3_conta")

            # Linha 2 de Filtros (Incluindo Datas e Valores)
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            with col_d1:
                data_inicio = st.date_input("📅 Data Inicial", df["Data"].min().date(), key="d3_ini")
            with col_d2:
                data_fim = st.date_input("📅 Data Final", df["Data"].max().date(), key="d3_fim")
            with col_d3:
                valor_min = st.number_input("💵 Valor Mínimo (R$)", min_value=0.0, value=0.0, step=100.0, key="d3_vmin")
            with col_d4:
                valor_max = st.number_input("💵 Valor Máximo (R$)", min_value=0.0, value=float(df["Valor"].max() if not df.empty else 1000.0), step=100.0, key="d3_vmax")

        # Aplicação rigorosa dos filtros em cascata (Filtro de datas obrigatório na raiz)
        df_filtrado = df[
            (df["Data"].dt.date >= data_inicio) &
            (df["Data"].dt.date <= data_fim) &
            (df["Tipo"].isin(tipo_sel)) &
            (df["Categoria"].isin(categoria_sel)) &
            (df["Conta"].isin(conta_sel)) &
            (df["Valor"] >= valor_min) &
            (df["Valor"] <= valor_max)
        ]
        if status_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]

        st.markdown("---")

        if not df_filtrado.empty:
            # ==================== CÁLCULO DOS KPIs ESTRATÉGICOS ====================
            entradas = df_filtrado[df_filtrado["Tipo"] == "Receita"]["Valor"].sum()
            saidas_cc = df_filtrado[(df_filtrado["Tipo"] == "Despesa") & (~df_filtrado["Conta"].isin(cartoes_nomes))]["Valor"].sum()
            cartao_passivo = df_filtrado[(df_filtrado["Tipo"] == "Despesa") & (df_filtrado["Conta"].isin(cartoes_nomes))]["Valor"].sum()
            transferencias = df_filtrado[df_filtrado["Tipo"] == "Transferência"]["Valor"].sum()
            
            total_despesas_gerais = saidas_cc + cartao_passivo
            saldo_liquido = entradas - total_despesas_gerais
            
            ticket_medio_receita = df_filtrado[df_filtrado["Tipo"] == "Receita"]["Valor"].mean() if entradas > 0 else 0.0
            ticket_medio_despesa = df_filtrado[df_filtrado["Tipo"] == "Despesa"]["Valor"].mean() if total_despesas_gerais > 0 else 0.0
            indice_cobertura = (entradas / total_despesas_gerais) if total_despesas_gerais > 0 else 0.0

            st.markdown("### 📈 KPIs Executivos Principais")
            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            col_kpi1.metric("🟢 Entradas", f"R$ {entradas:,.2f}", delta="Receitas Totais")
            col_kpi2.metric("🔴 Saídas (C/C)", f"R$ {saidas_cc:,.2f}", delta="Contas Correntes", delta_color="inverse")
            col_kpi3.metric("💳 Passivo Cartões", f"R$ {cartao_passivo:,.2f}", delta="Fatura em Aberto", delta_color="inverse")
            col_kpi4.metric("🔵 Transferências", f"R$ {transferencias:,.2f}", delta="Mov. Internas")
            col_kpi5.metric("💰 Saldo Líquido", f"R$ {saldo_liquido:,.2f}", delta="Caixa Gerado", delta_color="normal")

            # ==================== INDICADORES DE SAÚDE FINANCEIRA PESSOAL (23 KPIs) ====================
            st.markdown("### 📌 Indicadores Avançados de Finanças Pessoais & Riqueza")

            net_savings_rate = (saldo_liquido / entradas * 100) if entradas > 0 else 0.0
            comprometimento_renda = (saidas_cc / entradas * 100) if entradas > 0 else 0.0
            cash_ratio_val = (entradas / saidas_cc) if saidas_cc > 0 else 0.0
            burn_rate_val = abs(saldo_liquido) if saldo_liquido < 0 else 0.0

            # Cálculos comportamentais e de planejamento patrimonial
            maior_gasto_cat = df_filtrado[df_filtrado["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum()
            maior_gasto_valor = maior_gasto_cat.max() if not maior_gasto_cat.empty else 0.0
            peso_maior_gasto = (maior_gasto_valor / total_despesas_gerais * 100) if total_despesas_gerais > 0 else 0.0

            despesas_df = df_filtrado[df_filtrado["Tipo"] == "Despesa"]
            qtde_transacoes_despesa = len(despesas_df)
            ticket_max_despesa = despesas_df["Valor"].max() if not despesas_df.empty else 0.0
            peso_maior_transacao = (ticket_max_despesa / total_despesas_gerais * 100) if total_despesas_gerais > 0 else 0.0

            dias_periodo = max(1, (data_fim - data_inicio).days + 1)
            gasto_medio_diario = total_despesas_gerais / dias_periodo
            renda_diaria = entradas / dias_periodo
            dias_autonomia = (saldo_liquido / gasto_medio_diario) if gasto_medio_diario > 0 and saldo_liquido > 0 else 0.0

            peso_cartao_despesa = (cartao_passivo / total_despesas_gerais * 100) if total_despesas_gerais > 0 else 0.0
            indice_poupanca_bruta = max(0.0, net_savings_rate)

            # Bloco 1: Saúde e Fluxo
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            col_i1.metric("💰 Taxa de Poupança", f"{net_savings_rate:.1f}%", delta="Net Savings Rate")
            col_i2.metric("📊 Comprometimento Renda", f"{comprometimento_renda:.1f}%", delta="Gastos / Receitas", delta_color="inverse")
            col_i3.metric("🛡️ Cash Ratio", f"{cash_ratio_val:.2f}x", delta="Liquidez Corrente")
            col_i4.metric("🔥 Burn Rate Diário", f"R$ {gasto_medio_diario:,.2f} / dia", delta="Velocidade de Gasto", delta_color="inverse")

            # Bloco 2: Eficiência e Cobertura
            col_i5, col_i6, col_i7, col_i8 = st.columns(4)
            col_i5.metric("🎯 Índice de Cobertura", f"{indice_cobertura:.2f}x", delta="Entradas / Despesas")
            col_i6.metric("🏷️ Ticket Médio Receita", f"R$ {ticket_medio_receita:,.2f}", delta="Por Entrada")
            col_i7.metric("🏷️ Ticket Médio Despesa", f"R$ {ticket_medio_despesa:,.2f}", delta="Por Saída/Fatura")
            col_i8.metric("📦 Volume de Lançamentos", f"{len(df_filtrado)} un.", delta="Filtro Ativo")

            # Bloco 3: Concentração de Risco Pessoal
            col_n1, col_n2, col_n3, col_n4 = st.columns(4)
            col_n1.metric("💳 Dependência de Cartão", f"{peso_cartao_despesa:.1f}%", delta="Dos Gastos no Crédito", delta_color="inverse")
            col_n2.metric("⚠️ Concentração de Categoria", f"{peso_maior_gasto:.1f}%", delta="Peso da Maior Categoria", delta_color="inverse")
            col_n3.metric("⚡ Impacto Outlier", f"{peso_maior_transacao:.1f}%", delta="Maior Gasto vs Total", delta_color="inverse")
            col_n4.metric("⏳ Autonomia de Caixa", f"{dias_autonomia:.0f} dias", delta="Fôlego com o Saldo Atual")

            # Bloco 4: Dinâmica Diária e Esforço
            col_n5, col_n6, col_n7, col_n8 = st.columns(4)
            col_n5.metric("☀️ Geração Diária", f"R$ {renda_diaria:,.2f} / dia", delta="Entrada Média Diária")
            col_n6.metric("📉 Maior Gasto Único", f"R$ {ticket_max_despesa:,.2f}", delta="Pico de Despesa")
            col_n7.metric("🏃‍♂️ Frequência de Gastos", f"{(qtde_transacoes_despesa / (dias_periodo/30)):.1f}x", delta="Saídas por Mês (Média)")
            col_n8.metric("🌱 Índice de Retenção", f"{indice_poupanca_bruta:.1f}%", delta="Efetividade de Guardar")

            # Bloco 5: Métricas Finais de Consistência
            col_n9, col_n10, col_n11 = st.columns(3)
            col_n9.metric("📋 Média de Lanç./Dia", f"{(len(df_filtrado) / dias_periodo):.2f}", delta="Densidade de Registros")
            col_n10.metric("⚖️ Relação Transacional", f"{(len(df_filtrado[df_filtrado['Tipo']=='Receita']) / max(1, qtde_transacoes_despesa)):.2f}x", delta="Entradas vs Saídas")
            col_n11.metric("🛡️ Fator de Resiliência", f"{min(100.0, (cash_ratio_val * 50)):.1f} pts", delta="Score de Fôlego Pessoal")

            st.markdown("---")

            # ==================== ABAS DE VISUALIZAÇÃO INTERNA ====================
            tab_vis1, tab_vis2, tab_vis3, tab_vis4 = st.tabs(["📂 Consolidado Estrutural", "📊 Gráficos de Evolução", "📈 Curva ABC & Top Gastos", "📄 Detalhamento Analítico"])

            with tab_vis1:
                st.markdown("### 📂 Visão Consolidada por Categoria")
                df_cat_sum = df_filtrado.groupby(["Categoria", "Tipo"])["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
                df_cat_sum["Valor_Fmt"] = df_cat_sum["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(aplicar_estilo_tabela(df_cat_sum[["Tipo", "Categoria", "Valor_Fmt"]].style), use_container_width=True)

                st.markdown("### 🏦 Visão Consolidada por Conta / Instituição")
                df_acc_sum = df_filtrado.groupby(["Conta", "Tipo"])["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
                df_acc_sum["Valor_Fmt"] = df_acc_sum["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(aplicar_estilo_tabela(df_acc_sum[["Tipo", "Conta", "Valor_Fmt"]].style), use_container_width=True)

            with tab_vis2:
                st.markdown("### 📈 Evolução Temporal Consolidada")
                df_time = df_filtrado.groupby(["AnoMes", "Tipo"])["Valor"].sum().reset_index()
                
                chart_evolucao = alt.Chart(df_time).mark_line(strokeWidth=3, point=True).encode(
                    x=alt.X("AnoMes:N", title="Mês / Ano"),
                    y=alt.Y("Valor:Q", title="Montante (R$)"),
                    color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Receita", "Despesa", "Transferência"], range=["#2a9d8f", "#e76f51", "#264653"]), title="Tipo"),
                    tooltip=["AnoMes", "Tipo", "Valor"]
                ).properties(height=380).interactive()
                st.altair_chart(chart_evolucao, use_container_width=True)

            with tab_vis3:
                st.markdown("### 📉 Curva ABC de Despesas (Impacto Orçamentário)")
                df_abc = df_filtrado[df_filtrado["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
                if not df_abc.empty:
                    df_abc = df_abc.sort_values(by="Valor", ascending=False)
                    df_abc["Acumulado_%"] = (df_abc["Valor"].cumsum() / df_abc["Valor"].sum()) * 100

                    base_abc = alt.Chart(df_abc).encode(x=alt.X("Categoria:N", sort="-y", title="Categoria"))
                    bar_abc = base_abc.mark_bar(color="#264653").encode(y=alt.Y("Valor:Q", title="Gasto Total (R$)"), tooltip=["Categoria", "Valor"])
                    line_abc = base_abc.mark_line(strokeWidth=3, color="#e76f51", point=True).encode(y=alt.Y("Acumulado_%:Q", title="Acumulado (%)", scale=alt.Scale(domain=[0, 105])))
                    chart_abc = alt.layer(bar_abc, line_abc).resolve_scale(y="independent").properties(height=380).interactive()
                    st.altair_chart(chart_abc, use_container_width=True)
                else:
                    st.info("Não há despesas suficientes no filtro selecionado para compor a Curva ABC.")

            with tab_vis4:
                st.markdown("### 📄 Detalhamento Bruto dos Lançamentos Filtrados")
                df_detalhe = df_filtrado[["Tipo", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor", "Data", "Status"]].copy()
                df_detalhe["Valor_Fmt"] = df_detalhe["Valor"].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(aplicar_estilo_tabela(df_detalhe[["Tipo", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor_Fmt", "Data", "Status"]].style), use_container_width=True)

                # Botão de exportação rápida para CSV do filtro atual
                csv_export = df_filtrado.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Baixar Dados Filtrados (CSV)",
                    data=csv_export,
                    file_name=f"dashboard3_pessoal_{datetime.today().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados (verifique o intervalo de datas ou os critérios de busca aplicados).")
    else:
        st.info("Nenhum lançamento disponível na base de dados para exibir no Dashboard 3.")

elif aba == "Resumo Geral":
    st.subheader("📋 Resumo Geral - Visão Inteligente")
    st.markdown("Consolidação de Entradas, Saídas, Transferências e Cartões com filtro dinâmico de Status.")

    df = st.session_state.lancamentos

    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        meses_disponiveis = sorted(df["AnoMes"].unique().tolist(), reverse=True)
        mes_atual_padrao = datetime.today().strftime("%Y-%m")
        if mes_atual_padrao not in meses_disponiveis:
            meses_disponiveis.insert(0, mes_atual_padrao)

        col_sel1, col_sel2 = st.columns([2, 4])
        with col_sel1:
            mes_selecionado_rg = st.selectbox("📅 Selecione o Mês (Ano-Mês)", meses_disponiveis, key="sel_mes_resumo_geral")
        with col_sel2:
            status_opcoes = ["Todos", "Efetivado", "Budget"]
            status_selecionado = st.selectbox("📌 Filtrar por Status", status_opcoes, index=0)

        ano_sel, mes_sel = map(int, mes_selecionado_rg.split("-"))

        df_mes = df[(df["Data"].dt.year == ano_sel) & (df["Data"].dt.month == mes_sel)]
        if status_selecionado != "Todos":
            df_mes = df_mes[df_mes["Status"] == status_selecionado]

        cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []

        total_entradas = df_mes[df_mes["Tipo"] == "Receita"]["Valor"].sum()
        total_saidas_cc = df_mes[(df_mes["Tipo"] == "Despesa") & (~df_mes["Conta"].isin(cartoes_nomes))]["Valor"].sum()
        total_passivo_cartao = df_mes[(df_mes["Tipo"] == "Despesa") & (df_mes["Conta"].isin(cartoes_nomes))]["Valor"].sum()
        total_transferencias = df_mes[df_mes["Tipo"] == "Transferência"]["Valor"].sum()
        saldo_liquido = total_entradas - total_saidas_cc

        st.markdown("---")
        col_rg1, col_rg2, col_rg3, col_rg4, col_rg5 = st.columns(5)
        with col_rg1:
            st.metric("🟢 Entradas", f"R$ {total_entradas:,.2f}", delta=status_selecionado)
        with col_rg2:
            st.metric("🔴 Saídas (C/C)", f"R$ {total_saidas_cc:,.2f}", delta=status_selecionado, delta_color="inverse")
        with col_rg3:
            st.metric("💳 Passivo Cartão", f"R$ {total_passivo_cartao:,.2f}", delta="Saldo Devedor", delta_color="inverse")
        with col_rg4:
            st.metric("🔵 Transferências", f"R$ {total_transferencias:,.2f}", delta=status_selecionado)
        with col_rg5:
            st.metric("💰 Saldo Líquido", f"R$ {saldo_liquido:,.2f}", delta="Caixa Real", delta_color="normal")

        # Indicadores executivos adicionais
        st.markdown("### 📌 Indicadores Executivos")
        net_savings_rate = (saldo_liquido / total_entradas * 100) if total_entradas > 0 else 0.0
        comprometimento_renda = (total_saidas_cc / total_entradas * 100) if total_entradas > 0 else 0.0
        cash_ratio_val = (total_entradas / total_saidas_cc) if total_saidas_cc > 0 else 0.0
        burn_rate_val = abs(saldo_liquido) if saldo_liquido < 0 else 0.0

        col_n1, col_n2, col_n3, col_n4 = st.columns(4)
        with col_n1:
            st.metric("💰 Taxa de Poupança", f"{net_savings_rate:.1f}%", delta="Net Savings Rate")
        with col_n2:
            st.metric("📊 Comprom. Renda", f"{comprometimento_renda:.1f}%", delta="Gastos/Receitas", delta_color="inverse")
        with col_n3:
            st.metric("🛡️ Cash Ratio", f"{cash_ratio_val:.2f}x", delta="Liquidez")
        with col_n4:
            st.metric("🔥 Burn Rate", f"R$ {burn_rate_val:,.2f}", delta="Queima de Caixa", delta_color="inverse")

        st.markdown("---")
        st.markdown(f"### 📄 Detalhamento dos Lançamentos ({mes_selecionado_rg} - {status_selecionado})")
        if not df_mes.empty:
            df_exibicao = df_mes[["Tipo", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor", "Data", "Parcela"]].copy()
            df_exibicao["Valor"] = df_exibicao["Valor"].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(aplicar_estilo_tabela(df_exibicao.style), use_container_width=True)
        else:
            st.info(f"Nenhum lançamento encontrado para {mes_selecionado_rg} com status {status_selecionado}.")
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

elif aba == "Monthly Audit 3":
    st.subheader("📊 Monthly Audit 3 - Auditoria Detalhada por Categoria")

    df = st.session_state.lancamentos
    if not df.empty:
        # Tratamento inicial
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        # Filtros organizados
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            status_sel = st.selectbox("📌 Status", ["Todos", "Efetivado", "Budget"])
        with col_f2:
            categoria_sel = st.multiselect("🏷️ Categoria", df["Categoria"].unique().tolist(), default=df["Categoria"].unique().tolist())
        with col_f3:
            conta_sel = st.multiselect("🏦 Conta", df["Conta"].unique().tolist(), default=df["Conta"].unique().tolist())

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_inicio = st.date_input("📅 Data Inicial", df["Data"].min().date())
        with col_d2:
            data_fim = st.date_input("📅 Data Final", df["Data"].max().date())

        # Aplicação dos filtros
        df_filtrado = df[
            (df["Data"].dt.date >= data_inicio) &
            (df["Data"].dt.date <= data_fim) &
            (df["Conta"].isin(conta_sel))
        ]
        if status_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]
        if categoria_sel:
            df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(categoria_sel)]

        st.markdown("---")

        # KPIs gerais
        entradas = df_filtrado[df_filtrado["Tipo"] == "Receita"]["Valor"].sum()
        saidas = df_filtrado[df_filtrado["Tipo"] == "Despesa"]["Valor"].sum()
        transferencias = df_filtrado[df_filtrado["Tipo"] == "Transferência"]["Valor"].sum()
        saldo_liquido = entradas - saidas

        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("🟢 Entradas", f"R$ {entradas:,.2f}")
        col_kpi2.metric("🔴 Saídas", f"R$ {saidas:,.2f}", delta_color="inverse")
        col_kpi3.metric("🔵 Transferências", f"R$ {transferencias:,.2f}")
        col_kpi4.metric("💰 Saldo Líquido", f"R$ {saldo_liquido:,.2f}")

        st.markdown("---")

        # Subtotais por categoria com sparklines
        st.markdown("### 📂 Subtotais por Categoria com Tendência")
        df_cat_sum = df_filtrado.groupby("Categoria")["Valor"].sum().reset_index().sort_values("Valor", ascending=False)

        df_line_cat = df_filtrado[df_filtrado["Tipo"] == "Despesa"].copy()
        df_line_cat["AnoMes"] = df_line_cat["Data"].dt.to_period("M").astype(str)
        df_line_group_cat = df_line_cat.groupby(["AnoMes", "Categoria"])["Valor"].sum().reset_index()

        for _, row in df_cat_sum.iterrows():
            categoria = row["Categoria"]
            valor_total = row["Valor"]

            st.markdown(f"**{categoria}** — Total: R$ {valor_total:,.2f}")
            df_cat_trend = df_line_group_cat[df_line_group_cat["Categoria"] == categoria]

            chart_spark = alt.Chart(df_cat_trend).mark_line(point=True).encode(
                x=alt.X("AnoMes:N", title=""),
                y=alt.Y("Valor:Q", title=""),
                tooltip=["AnoMes", "Valor"]
            ).properties(height=80)

            st.altair_chart(chart_spark, use_container_width=True)

        st.markdown("---")

        # Indicadores executivos por categoria
        st.markdown("### 📌 Indicadores Executivos por Categoria")
        total_receitas = entradas
        total_despesas = saidas

        df_indicadores = df_filtrado[df_filtrado["Tipo"] == "Despesa"].groupby("Categoria")["Valor"].sum().reset_index()
        df_indicadores["% da Renda"] = df_indicadores["Valor"].apply(lambda x: (x / total_receitas * 100) if total_receitas > 0 else 0.0)
        df_indicadores["% das Despesas"] = df_indicadores["Valor"].apply(lambda x: (x / total_despesas * 100) if total_despesas > 0 else 0.0)

        st.dataframe(df_indicadores, use_container_width=True)

        # Ranking das categorias mais críticas
        st.markdown("### 🚨 Top 3 Categorias Críticas (Maior Impacto na Renda)")
        df_rank = df_indicadores.sort_values("% da Renda", ascending=False).head(3)
        for _, row in df_rank.iterrows():
            st.markdown(f"- **{row['Categoria']}** → {row['% da Renda']:.1f}% da renda comprometida")

        st.markdown("---")

        # Tabelas adicionais de tracking
        st.markdown("### 📊 Tabelas Adicionais de Tracking")

        # Resumo por Conta
        st.markdown("#### 🏦 Resumo por Conta")
        df_conta = df_filtrado.groupby("Conta")["Valor"].sum().reset_index().sort_values("Valor", ascending=False)
        st.dataframe(df_conta, use_container_width=True)

        # Resumo por Status
        st.markdown("#### 📌 Resumo por Status")
        df_status = df_filtrado.groupby("Status")["Valor"].sum().reset_index()
        st.dataframe(df_status, use_container_width=True)

        # Ticket médio por categoria
        st.markdown("#### 🎯 Ticket Médio por Categoria")
        df_ticket = df_filtrado.groupby("Categoria")["Valor"].mean().reset_index().sort_values("Valor", ascending=False)
        st.dataframe(df_ticket, use_container_width=True)

        # Top 10 maiores transações
        st.markdown("#### 🔝 Top 10 Maiores Transações")
        df_top10 = df_filtrado.sort_values("Valor", ascending=False).head(10)
        st.dataframe(df_top10[["Data", "Descricao", "Categoria", "Conta", "Valor"]], use_container_width=True)

        # Resumo por mês
        st.markdown("#### 📅 Resumo por Mês")
        df_mes = df_filtrado.groupby("AnoMes").agg(
            Entradas=("Valor", lambda x: df_filtrado.loc[x.index][df_filtrado["Tipo"]=="Receita"]["Valor"].sum()),
            Saidas=("Valor", lambda x: df_filtrado.loc[x.index][df_filtrado["Tipo"]=="Despesa"]["Valor"].sum())
        ).reset_index()
        df_mes["Saldo"] = df_mes["Entradas"] - df_mes["Saidas"]
        st.dataframe(df_mes, use_container_width=True)

        # Resumo por tipo
        st.markdown("#### 📂 Resumo por Tipo de Lançamento")
        df_tipo = df_filtrado.groupby("Tipo")["Valor"].sum().reset_index()
        st.dataframe(df_tipo, use_container_width=True)

        # Frequência de transações
        st.markdown("#### 🔄 Frequência de Transações por Categoria")
        df_freq = df_filtrado.groupby("Categoria")["Descricao"].count().reset_index().rename(columns={"Descricao":"Qtde Transações"})
        st.dataframe(df_freq.sort_values("Qtde Transações", ascending=False), use_container_width=True)

        # Evolução acumulada
        st.markdown("#### 📈 Evolução Acumulada")
        df_filtrado = df_filtrado.sort_values("Data")
        df_filtrado["Saldo Acumulado"] = (df_filtrado.apply(lambda r: r["Valor"] if r["Tipo"]=="Receita" else -r["Valor"], axis=1)).cumsum()
        st.dataframe(df_filtrado[["Data","Descricao","Categoria","Conta","Valor","Saldo Acumulado"]], use_container_width=True)

        # Top categorias recorrentes
        st

elif aba == "Monthly Audit":
    st.subheader("📒 Monthly Audit - Auditoria Completa")
    st.markdown("Painel robusto com **Budget vs Efetivado**, auditoria por **Conta** e **Categoria**, múltiplos filtros, indicadores percentuais, mapa visual e gráficos de linha.")

    df = st.session_state.lancamentos
    if not df.empty:
        # Preparação
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        # Filtros principais
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            meses_disponiveis = sorted(df["AnoMes"].unique().tolist(), reverse=True)
            mes_sel = st.selectbox("📅 Selecione o Mês", meses_disponiveis, index=0)
        with col_f2:
            status_opcoes = ["Todos", "Efetivado", "Budget"]
            status_sel = st.selectbox("📌 Filtrar por Status", status_opcoes, index=0)

        ano_sel, mes_num = map(int, mes_sel.split("-"))
        df_mes = df[(df["Data"].dt.year == ano_sel) & (df["Data"].dt.month == mes_num)]
        if status_sel != "Todos":
            df_mes = df_mes[df_mes["Status"] == status_sel]

        # Filtros adicionais
        col_f3, col_f4, col_f5 = st.columns(3)
        with col_f3:
            categoria_sel = st.selectbox("📂 Categoria", ["Todas"] + st.session_state.categorias)
        with col_f4:
            conta_sel = st.selectbox("🏦 Conta", ["Todas"] + df_mes["Conta"].unique().tolist())
        with col_f5:
            tipo_sel = st.selectbox("🔎 Tipo", ["Todos", "Receita", "Despesa", "Transferência"])

        if categoria_sel != "Todas":
            df_mes = df_mes[df_mes["Categoria"] == categoria_sel]
        if conta_sel != "Todas":
            df_mes = df_mes[df_mes["Conta"] == conta_sel]
        if tipo_sel != "Todos":
            df_mes = df_mes[df_mes["Tipo"] == tipo_sel]

        # Auditoria por Categoria
        st.markdown("### 📂 Auditoria por Categoria (Budget vs Efetivado)")
        df_cat = df_mes.groupby(["Categoria", "Status"])["Valor"].sum().reset_index()
        pivot_cat = df_cat.pivot_table(index="Categoria", columns="Status", values="Valor", fill_value=0.0).reset_index()
        for col in ["Budget", "Efetivado"]:
            if col not in pivot_cat.columns:
                pivot_cat[col] = 0.0
        pivot_cat["Diferença"] = pivot_cat["Budget"] - pivot_cat["Efetivado"]
        pivot_cat["% Execução"] = (pivot_cat["Efetivado"] / pivot_cat["Budget"] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        st.dataframe(aplicar_estilo_tabela(pivot_cat.style), use_container_width=True)

        # Auditoria por Conta
        st.markdown("### 🏦 Auditoria por Conta")
        audit_table = df_mes.groupby(["Conta", "Tipo", "Status"])["Valor"].sum().reset_index()
        pivot_audit = audit_table.pivot_table(index="Conta", columns=["Tipo","Status"], values="Valor", fill_value=0.0)
        pivot_audit.columns = [f"{tipo}_{status}" for tipo, status in pivot_audit.columns]
        pivot_audit = pivot_audit.reset_index()
        for col in ["Despesa_Budget", "Despesa_Efetivado", "Receita_Budget", "Receita_Efetivado"]:
            if col not in pivot_audit.columns:
                pivot_audit[col] = 0.0
        pivot_audit["% Execução Despesa"] = (pivot_audit["Despesa_Efetivado"] / pivot_audit["Despesa_Budget"] * 100).replace([np.inf,-np.inf],0).fillna(0)
        pivot_audit["% Execução Receita"] = (pivot_audit["Receita_Efetivado"] / pivot_audit["Receita_Budget"] * 100).replace([np.inf,-np.inf],0).fillna(0)
        st.dataframe(aplicar_estilo_tabela(pivot_audit.style), use_container_width=True)

        # Indicadores executivos
        st.markdown("### 📌 Indicadores Executivos")
        total_budget = df_mes[df_mes["Status"]=="Budget"]["Valor"].sum()
        total_efetivado = df_mes[df_mes["Status"]=="Efetivado"]["Valor"].sum()
        saldo_a_pagar = total_budget - total_efetivado
        taxa_execucao = (total_efetivado/total_budget*100) if total_budget>0 else 0.0
        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.metric("💰 Total Budget", f"R$ {total_budget:,.2f}")
        col_i2.metric("✅ Efetivado", f"R$ {total_efetivado:,.2f}", delta=f"{taxa_execucao:.1f}% Executado")
        col_i3.metric("📉 Saldo a Pagar", f"R$ {saldo_a_pagar:,.2f}")

        # Mapa visual de contas
        st.markdown("### 🗺️ Mapa Visual de Contas")
        for _, row in pivot_audit.iterrows():
            conta = row["Conta"]
            budget = row["Despesa_Budget"]
            efetivado = row["Despesa_Efetivado"]
            perc = (efetivado/budget*100) if budget>0 else 0
            if perc < 80:
                cor = "#2a9d8f"  # verde
            elif perc <= 100:
                cor = "#f4a261"  # amarelo
            else:
                cor = "#e76f51"  # vermelho
            st.markdown(f"<div style='background-color:{cor};padding:8px;border-radius:5px;color:white;'>"
                        f"Conta: <b>{conta}</b> | Budget: R$ {budget:,.2f} | Efetivado: R$ {efetivado:,.2f} | Execução: {perc:.1f}%"
                        "</div>", unsafe_allow_html=True)

        # Gráficos de linha
        st.markdown("### 📈 Evolução Temporal")
        df_temp = df.groupby("AnoMes")["Valor"].sum().reset_index()
        chart_temp = alt.Chart(df_temp).mark_line(point=True, strokeWidth=3).encode(
            x="AnoMes:N", y="Valor:Q", tooltip=["AnoMes","Valor"]
        ).properties(height=350).interactive()
        st.altair_chart(chart_temp, use_container_width=True)

        st.markdown("### 📊 Evolução por Categoria")
        df_cat_line = df.groupby(["AnoMes","Categoria"])["Valor"].sum().reset_index()
        chart_cat_line = alt.Chart(df_cat_line).mark_line(point=True).encode(
            x="AnoMes:N", y="Valor:Q", color="Categoria:N", tooltip=["AnoMes","Categoria","Valor"]
        ).properties(height=350).interactive()
        st.altair_chart(chart_cat_line, use_container_width=True)

        st.markdown("### 📊 Evolução por Conta")
        df_acc_line = df.groupby(["AnoMes","Conta"])["Valor"].sum().reset_index()
        chart_acc_line = alt.Chart(df_acc_line).mark_line(point=True).encode(
            x="AnoMes:N", y="Valor:Q", color="Conta:N", tooltip=["AnoMes","Conta","Valor"]
        ).properties(height=350).interactive()
        st.altair_chart(chart_acc_line, use_container_width=True)

    else:
        st.info("Nenhum lançamento cadastrado para auditoria.")

elif aba == "Financial Indicators":
    st.subheader("💹 Financial Indicators")
    st.markdown("Indicadores financeiros avançados com filtros de Tipo, Status e Período (Mensal, Trimestral, Quadrimestral).")

    df = st.session_state.lancamentos

    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)

        # Filtro de Tipo
        tipo_opcoes = ["Todos", "Receita", "Despesa"]
        tipo_selecionado = st.selectbox("📌 Filtrar por Tipo", tipo_opcoes, index=0)
        if tipo_selecionado != "Todos":
            df = df[df["Tipo"] == tipo_selecionado]

        # Filtro de Status
        status_opcoes = ["Todos", "Efetivado", "Budget"]
        status_selecionado = st.selectbox("📌 Filtrar por Status", status_opcoes, index=0)
        if status_selecionado != "Todos":
            df = df[df["Status"] == status_selecionado]

        # Filtro de Período (Mensal, Trimestral, Quadrimestral)
        periodo_opcoes = ["Mensal", "Trimestral", "Quadrimestral"]
        periodo_selecionado = st.selectbox("📅 Selecionar Período", periodo_opcoes, index=0)

        if periodo_selecionado == "Mensal":
            df["Periodo"] = df["Data"].dt.to_period("M").astype(str)
        elif periodo_selecionado == "Trimestral":
            df["Periodo"] = df["Data"].dt.to_period("Q").astype(str)
        elif periodo_selecionado == "Quadrimestral":
            df["Quadrimestre"] = ((df["Data"].dt.month - 1) // 4 + 1).astype(str)
            df["Periodo"] = df["Data"].dt.year.astype(str) + "-Qd" + df["Quadrimestre"]

        # ==================== PARÂMETROS FINANCEIROS ====================
        cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []

        df["Expense_CC"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] not in cartoes_nomes else 0.0, axis=1)
        df["Expense_Card"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] in cartoes_nomes else 0.0, axis=1)
        df["Income_Val"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)

        pivot_fin = df.pivot_table(
            index="Periodo",
            values=["Income_Val", "Expense_CC", "Expense_Card"],
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        pivot_fin = pivot_fin.rename(columns={
            "Income_Val": "Receita",
            "Expense_CC": "Despesa (C/C)",
            "Expense_Card": "Passivo Cartão"
        })

        pivot_fin["Cash Flow"] = pivot_fin["Receita"] - pivot_fin["Despesa (C/C)"]
        pivot_fin["Acumulado"] = pivot_fin["Cash Flow"].cumsum()

        # Indicadores derivados
        pivot_fin["Taxa Poupança (%)"] = ((pivot_fin["Receita"] - pivot_fin["Despesa (C/C)"]) / pivot_fin["Receita"] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        pivot_fin["Comp. Renda (%)"] = (pivot_fin["Despesa (C/C)"] / pivot_fin["Receita"] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        pivot_fin["Burn Rate"] = pivot_fin["Cash Flow"].apply(lambda x: abs(x) if x < 0 else 0)
        pivot_fin["Margem (%)"] = (pivot_fin["Cash Flow"] / pivot_fin["Receita"] * 100).replace([np.inf, -np.inf], 0).fillna(0)

        # ==================== TABELA ====================
        pivot_fmt = pivot_fin.copy()
        for col in ["Receita", "Despesa (C/C)", "Passivo Cartão", "Cash Flow", "Acumulado", "Burn Rate"]:
            pivot_fmt[col] = pivot_fmt[col].apply(lambda x: f"R$ {x:,.2f}")
        for col in ["Taxa Poupança (%)", "Comp. Renda (%)", "Margem (%)"]:
            pivot_fmt[col] = pivot_fmt[col].apply(lambda x: f"{x:.1f}%")

        st.dataframe(
            aplicar_estilo_tabela(pivot_fmt.set_index("Periodo").style, subset=["Cash Flow", "Acumulado"]),
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("### 📈 Gráficos Avançados")

        # Receita vs Despesa vs Cartão
        df_melt_ie = pivot_fin.melt(id_vars="Periodo", value_vars=["Receita", "Despesa (C/C)", "Passivo Cartão"], var_name="Métrica", value_name="Valor")
        chart_ie = alt.Chart(df_melt_ie).mark_line(strokeWidth=3, point=True).encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Valor:Q", title="Montante (R$)"),
            color=alt.Color("Métrica:N", scale=alt.Scale(domain=["Receita", "Despesa (C/C)", "Passivo Cartão"], range=["#2a9d8f", "#e76f51", "#f4a261"])),
            tooltip=["Periodo", "Métrica", "Valor"]
        ).properties(height=320).interactive()
        st.altair_chart(chart_ie, use_container_width=True)

        # Cash Flow vs Acumulado
        df_melt_ca = pivot_fin.melt(id_vars="Periodo", value_vars=["Cash Flow", "Acumulado"], var_name="Métrica", value_name="Valor")
        chart_ca = alt.Chart(df_melt_ca).mark_line(strokeWidth=3, point=True).encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Valor:Q", title="Montante (R$)"),
            color=alt.Color("Métrica:N", scale=alt.Scale(domain=["Cash Flow", "Acumulado"], range=["#264653", "#2a9d8f"])),
            tooltip=["Periodo", "Métrica", "Valor"]
        ).properties(height=320).interactive()
        st.altair_chart(chart_ca, use_container_width=True)

        # Taxa de Poupança
        chart_tp = alt.Chart(pivot_fin).mark_line(point=True, strokeWidth=3, color="#2a9d8f").encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Taxa Poupança (%):Q", title="Taxa de Poupança (%)"),
            tooltip=["Periodo", "Taxa Poupança (%)"]
        ).properties(height=320).interactive()
        st.altair_chart(chart_tp, use_container_width=True)

        # Comprometimento da Renda
        chart_cr = alt.Chart(pivot_fin).mark_line(point=True, strokeWidth=3, color="#e76f51").encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Comp. Renda (%):Q", title="Comprometimento da Renda (%)"),
            tooltip=["Periodo", "Comp. Renda (%)"]
        ).properties(height=320).interactive()
        st.altair_chart(chart_cr, use_container_width=True)

        # Burn Rate
        chart_burn = alt.Chart(pivot_fin).mark_bar(color="#e76f51").encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Burn Rate:Q", title="Burn Rate (R$)"),
            tooltip=["Periodo", "Burn Rate"]
        ).properties(height=350).interactive()
        st.altair_chart(chart_burn, use_container_width=True)

        # Margem (%)
        chart_margin = alt.Chart(pivot_fin).mark_line(point=True, strokeWidth=3, color="#f4a261").encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Margem (%):Q", title="Margem (%)"),
            tooltip=["Periodo", "Margem (%)"]
        ).properties(height=320).interactive()
        st.altair_chart(chart_margin, use_container_width=True)

    else:
        st.info("Nenhum lançamento cadastrado para análise financeira.")

elif aba == "Statistical Indicators":
    st.subheader("📊 Statistical Indicators")
    st.markdown("Indicadores estatísticos avançados com filtros de Tipo, Status e Período (Mensal, Trimestral, Quadrimestral).")

    df = st.session_state.lancamentos

    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        tipo_opcoes = ["Todos", "Receita", "Despesa"]
        tipo_selecionado = st.selectbox("📌 Filtrar por Tipo", tipo_opcoes, index=0)
        if tipo_selecionado != "Todos":
            df = df[df["Tipo"] == tipo_selecionado]

        status_opcoes = ["Todos", "Efetivado", "Budget"]
        status_selecionado = st.selectbox("📌 Filtrar por Status", status_opcoes, index=0)
        if status_selecionado != "Todos":
            df = df[df["Status"] == status_selecionado]

        periodo_opcoes = ["Mensal", "Trimestral", "Quadrimestral"]
        periodo_selecionado = st.selectbox("📅 Selecionar Período", periodo_opcoes, index=0)

        if periodo_selecionado == "Mensal":
            df["Periodo"] = df["Data"].dt.to_period("M").astype(str)
        elif periodo_selecionado == "Trimestral":
            df["Periodo"] = df["Data"].dt.to_period("Q").astype(str)
        elif periodo_selecionado == "Quadrimestral":
            df["Quadrimestre"] = ((df["Data"].dt.month - 1) // 4 + 1).astype(str)
            df["Periodo"] = df["Data"].dt.year.astype(str) + "-Qd" + df["Quadrimestre"]

        cartoes_nomes = st.session_state.cartoes["Nome"].tolist() if not st.session_state.cartoes.empty else []

        df["Expense_CC"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] not in cartoes_nomes else 0.0, axis=1)
        df["Expense_Card"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" and r["Conta"] in cartoes_nomes else 0.0, axis=1)
        df["Income_Val"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)

        pivot_stats = df.pivot_table(
            index="Periodo",
            values=["Income_Val", "Expense_CC", "Expense_Card"],
            aggfunc="sum",
            fill_value=0.0
        ).reset_index()

        pivot_stats = pivot_stats.rename(columns={
            "Income_Val": "Receita",
            "Expense_CC": "Despesa (C/C)",
            "Expense_Card": "Passivo Cartão"
        })

        pivot_stats["Cash Flow"] = pivot_stats["Receita"] - pivot_stats["Despesa (C/C)"]
        pivot_stats["Acumulado"] = pivot_stats["Cash Flow"].cumsum()

        pivot_stats["Taxa Poupança (%)"] = ((pivot_stats["Receita"] - pivot_stats["Despesa (C/C)"]) / pivot_stats["Receita"] * 100).replace([np.inf, -np.inf], 0).fillna(0)
        pivot_stats["Comp. Renda (%)"] = (pivot_stats["Despesa (C/C)"] / pivot_stats["Receita"] * 100).replace([np.inf, -np.inf], 0).fillna(0)

        pivot_fmt = pivot_stats.copy()
        for col in ["Receita", "Despesa (C/C)", "Passivo Cartão", "Cash Flow", "Acumulado"]:
            pivot_fmt[col] = pivot_fmt[col].apply(lambda x: f"R$ {x:,.2f}")
        pivot_fmt["Taxa Poupança (%)"] = pivot_fmt["Taxa Poupança (%)"].apply(lambda x: f"{x:.1f}%")
        pivot_fmt["Comp. Renda (%)"] = pivot_fmt["Comp. Renda (%)"].apply(lambda x: f"{x:.1f}%")

        st.dataframe(
            aplicar_estilo_tabela(pivot_fmt.set_index("Periodo").style, subset=["Cash Flow", "Acumulado"]),
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("### 📈 Gráficos Avançados")

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("#### 1️⃣ Receita vs Despesa vs Cartão")
            df_melt_ie = pivot_stats.melt(id_vars="Periodo", value_vars=["Receita", "Despesa (C/C)", "Passivo Cartão"], var_name="Métrica", value_name="Valor")
            chart_ie = alt.Chart(df_melt_ie).mark_line(strokeWidth=3, point=True).encode(
                x=alt.X("Periodo:N", title="Período"),
                y=alt.Y("Valor:Q", title="Montante (R$)"),
                color=alt.Color("Métrica:N", scale=alt.Scale(domain=["Receita", "Despesa (C/C)", "Passivo Cartão"], range=["#2a9d8f", "#e76f51", "#f4a261"])),
                tooltip=["Periodo", "Métrica", "Valor"]
            ).properties(height=320).interactive()
            st.altair_chart(chart_ie, use_container_width=True)

        with col_g2:
            st.markdown("#### 2️⃣ Cash Flow vs Acumulado")
            df_melt_ca = pivot_stats.melt(id_vars="Periodo", value_vars=["Cash Flow", "Acumulado"], var_name="Métrica", value_name="Valor")
            chart_ca = alt.Chart(df_melt_ca).mark_line(strokeWidth=3, point=True).encode(
                x=alt.X("Periodo:N", title="Período"),
                y=alt.Y("Valor:Q", title="Montante (R$)"),
                color=alt.Color("Métrica:N", scale=alt.Scale(domain=["Cash Flow", "Acumulado"], range=["#264653", "#2a9d8f"])),
                tooltip=["Periodo", "Métrica", "Valor"]
            ).properties(height=320).interactive()
            st.altair_chart(chart_ca, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Indicadores Derivados")
        col_i1, col_i2 = st.columns(2)

        with col_i1:
            st.markdown("#### 3️⃣ Taxa de Poupança (%)")
            chart_tp = alt.Chart(pivot_stats).mark_line(point=True, strokeWidth=3, color="#2a9d8f").encode(
                x=alt.X("Periodo:N", title="Período"),
                y=alt.Y("Taxa Poupança (%):Q", title="Taxa de Poupança (%)"),
                tooltip=["Periodo", "Taxa Poupança (%)"]
            ).properties(height=320).interactive()
            st.altair_chart(chart_tp, use_container_width=True)

        with col_i2:
            st.markdown("#### 4️⃣ Comprometimento da Renda (%)")
            chart_cr = alt.Chart(pivot_stats).mark_line(point=True, strokeWidth=3, color="#e76f51").encode(
                x=alt.X("Periodo:N", title="Período"),
                y=alt.Y("Comp. Renda (%):Q", title="Comprometimento da Renda (%)"),
                tooltip=["Periodo", "Comp. Renda (%)"]
            ).properties(height=320).interactive()
            st.altair_chart(chart_cr, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔥 Burn Rate por Período")
        pivot_stats["Burn Rate"] = pivot_stats["Cash Flow"].apply(lambda x: abs(x) if x < 0 else 0)
        chart_burn = alt.Chart(pivot_stats).mark_bar(color="#e76f51").encode(
            x=alt.X("Periodo:N", title="Período"),
            y=alt.Y("Burn Rate:Q", title="Burn Rate (R$)"),
            tooltip=["Periodo", "Burn Rate"]
        ).properties(height=350).interactive()
        st.altair_chart(chart_burn, use_container_width=True)
    else:
        st.info("Nenhum lançamento cadastrado para estatísticas.")

elif aba == "Statistical 2":
    st.subheader("📊 Statistical 2 - Estatísticas Avançadas")
    st.markdown("Exploração de estatísticas descritivas, correlações e análise de outliers.")

    df = st.session_state.lancamentos
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        # Estatísticas descritivas
        st.markdown("### 📈 Estatísticas Descritivas")
        st.dataframe(df["Valor"].describe().to_frame(), use_container_width=True)

        # Boxplot para detectar outliers
        st.markdown("### 📦 Boxplot de Valores (Outliers)")
        chart_box = alt.Chart(df).mark_boxplot(extent="min-max").encode(
            x=alt.X("Tipo:N", title="Tipo de Lançamento"),
            y=alt.Y("Valor:Q", title="Valor (R$)"),
            color="Tipo:N"
        ).properties(height=400)
        st.altair_chart(chart_box, use_container_width=True)

        # Heatmap de correlação
        st.markdown("### 🔗 Heatmap de Correlação")
        # Criar colunas auxiliares
        df["Receita"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Receita" else 0.0, axis=1)
        df["Despesa"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Despesa" else 0.0, axis=1)
        df["Transferência"] = df.apply(lambda r: r["Valor"] if r["Tipo"] == "Transferência" else 0.0, axis=1)
        df["Cartão"] = df.apply(lambda r: r["Valor"] if (r["Tipo"] == "Despesa" and r["Conta"] in st.session_state.cartoes["Nome"].tolist()) else 0.0, axis=1)

        corr_matrix = df[["Receita", "Despesa", "Transferência", "Cartão"]].corr()

        corr_df = corr_matrix.reset_index().melt(id_vars="index")
        corr_df.columns = ["Variável1", "Variável2", "Correlação"]

        chart_corr = alt.Chart(corr_df).mark_rect().encode(
            x=alt.X("Variável1:N", title=""),
            y=alt.Y("Variável2:N", title=""),
            color=alt.Color("Correlação:Q", scale=alt.Scale(scheme="redblue", domain=(-1,1))),
            tooltip=["Variável1", "Variável2", alt.Tooltip("Correlação:Q", format=".2f")]
        ).properties(height=400)
        st.altair_chart(chart_corr, use_container_width=True)
    else:
        st.info("Nenhum lançamento disponível para análise estatística.")

elif aba == "Statistical 3":
    st.subheader("📊 Statistical 3 - KPIs Avançados com Projeções e Estatísticas")
    st.markdown("Painel estatístico com filtros dinâmicos, tendências, cenários futuros, volatilidade e métricas estatísticas robustas.")

    df = st.session_state.lancamentos
    if not df.empty:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            status_sel = st.selectbox("📌 Status", ["Todos", "Efetivado", "Budget"], key="stat3_status")
        with col_f2:
            periodo_sel = st.selectbox("📅 Horizonte", ["Mensal", "Último mês", "Próximos 3 meses", "Próximos 6 meses", "Últimos 3 meses", "Últimos 6 meses", "Últimos 12 meses"], key="stat3_periodo")

        # Definir horizonte
        ultimo_mes = df["Data"].max()
        if periodo_sel == "Mensal":
            mes_sel = st.selectbox("Selecione o mês", sorted(df["AnoMes"].unique(), reverse=True))
            ano, mes = map(int, mes_sel.split("-"))
            df_filtrado = df[(df["Data"].dt.year == ano) & (df["Data"].dt.month == mes)]
        elif periodo_sel == "Último mês":
            ano, mes = ultimo_mes.year, ultimo_mes.month
            df_filtrado = df[(df["Data"].dt.year == ano) & (df["Data"].dt.month == mes)]
        elif periodo_sel == "Próximos 3 meses":
            fim = ultimo_mes + relativedelta(months=3)
            df_filtrado = df[(df["Data"] > ultimo_mes) & (df["Data"] <= fim)]
        elif periodo_sel == "Próximos 6 meses":
            fim = ultimo_mes + relativedelta(months=6)
            df_filtrado = df[(df["Data"] > ultimo_mes) & (df["Data"] <= fim)]
        else:
            meses_map = {"Últimos 3 meses": 3, "Últimos 6 meses": 6, "Últimos 12 meses": 12}
            horizonte = meses_map[periodo_sel]
            inicio_periodo = ultimo_mes - pd.DateOffset(months=horizonte)
            df_filtrado = df[df["Data"] >= inicio_periodo]

        if status_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Status"] == status_sel]

        # KPIs
        entradas = df_filtrado[df_filtrado["Tipo"] == "Receita"]["Valor"].sum()
        saidas = df_filtrado[df_filtrado["Tipo"] == "Despesa"]["Valor"].sum()
        saldo_liquido = entradas - saidas

        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Entradas", f"R$ {entradas:,.2f}")
        col2.metric("🔴 Saídas", f"R$ {saidas:,.2f}", delta_color="inverse")
        col3.metric("💰 Saldo Líquido", f"R$ {saldo_liquido:,.2f}")

        st.markdown("---")
        st.markdown("### 📈 Tendência Histórica com Projeção")

        pivot = df_filtrado.pivot_table(index="AnoMes", values="Valor", columns="Tipo", aggfunc="sum", fill_value=0).reset_index()
        pivot["CashFlow"] = pivot.get("Receita", 0) - pivot.get("Despesa", 0)

        # Projeção linear para próximos meses
        x_vals = np.arange(len(pivot))
        y_vals = pivot["CashFlow"].values
        if len(y_vals) > 1:
            a, b = np.polyfit(x_vals, y_vals, 1)
            futuros = 6
            proj_x = np.arange(len(pivot), len(pivot) + futuros)
            proj_y = a * proj_x + b

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
            
            data_fatura_base = data_compra
            if eh_cartao and dia_fechamento > 0 and data_compra.day > dia_fechamento:
                data_fatura_base = data_compra + relativedelta(months=1)
            
            if eh_cartao:
                novos_registros.append({
                    "Tipo": tipo,
                    "Status": "Efetivado",
                    "Descricao": f"[Compra Cartão] {descricao}",
                    "Categoria": categoria_final,
                    "Conta": conta_final,
                    "ContaDestino": "",
                    "Valor": round(valor_total, 2),
                    "Data": str(data_compra),
                    "Parcela": f"1/{parcelas}" if parcelas > 1 else "1/1"
                })

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
                    if dia_fechamento > 0:
                        data_fatura_parcela = data_fatura_base + relativedelta(months=i)
                        try:
                            data_fatura_parcela = data_fatura_parcela.replace(day=min(dia_vencimento, 28))
                        except:
                            pass

                    if modo_valor == "Dividir Total" and parcelas > 0:
                        valor_parcela = valor_total / parcelas
                    else:
                        valor_parcela = valor_total

                    desc_formatada = f"{descricao} ({i+1}/{parcelas})" if parcelas > 1 else descricao

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
                for i in range(parcelas):
                    if frequencia == "Mensal":
                        data_base_parcela = data_compra + relativedelta(months=i)
                    elif frequencia == "Quinzenal":
                        data_base_parcela = data_compra + relativedelta(weeks=2*i)
                    elif frequencia == "Anual":
                        data_base_parcela = data_compra + relativedelta(years=i)
                    else:
                        data_base_parcela = data_compra

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
                        "ContaDestino": conta_destino_final if tipo == "Transferência" else "",
                        "Valor": round(valor_parcela, 2),
                        "Data": str(data_base_parcela),
                        "Parcela": f"{i+1}/{parcelas}"
                    })

            df_novo = pd.DataFrame(novos_registros)
            st.session_state.lancamentos = pd.concat([st.session_state.lancamentos, df_novo], ignore_index=True)
            salvar_backup()
            
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
    
    if st.button("💾 Salvar Backup Agora"):
        salvar_backup()
        
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
                            salvar_backup()
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
                                
                                salvar_backup()
                                st.session_state.lancamentos = pd.read_csv(ARQUIVO_LANCAMENTOS)
                                
                                st.session_state[edit_key] = False
                                st.success("Lançamento atualizado com sucesso!")
                                st.rerun()
        else:
            st.warning("Nenhum lançamento corresponde ao filtro ou Smart Search informado.")
            
        st.markdown("---")
        if st.button("🗑️ Limpar Todos os Lançamentos"):
            st.session_state.lancamentos = pd.DataFrame(columns=["Tipo", "Status", "Descricao", "Categoria", "Conta", "ContaDestino", "Valor", "Data", "Parcela"])
            salvar_backup()
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
                salvar_backup()
                st.success("Cartão salvo com sucesso!")
                st.rerun()

    st.markdown("### 📋 Cartões Cadastrados e Gerenciamento")
    if not st.session_state.cartoes.empty:
        for idx, row in st.session_state.cartoes.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{row['Nome']}** | Fechamento: dia {row['Fechamento']} | Vencimento: dia {row['Vencimento']} | Limite: R$ {row['Limite']:,.2f}")
            if col2.button("🗑️ Deletar", key=f"del_cartao_{idx}"):
                st.session_state.cartoes = st.session_state.cartoes.drop(idx).reset_index(drop=True)
                salvar_backup()
                st.success("Cartão deletado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum cartão cadastrado.")

elif aba == "Gerenciar Categorias":
    st.subheader("🏷️ Gerenciar Categorias")
    st.markdown("Adicione ou remova categorias do sistema de forma rápida.")
    
    with st.form("form_nova_categoria"):
        nova_categoria = st.text_input("Nova Categoria", placeholder="Ex: Investimentos, Educação...")
        btn_add_cat = st.form_submit_button("Adicionar Categoria")
        if btn_add_cat:
            if nova_categoria.strip() != "":
                cat_limpa = nova_categoria.strip()
                if cat_limpa not in st.session_state.categorias:
                    st.session_state.categorias.append(cat_limpa)
                    pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
                    salvar_backup()
                    st.success(f"Categoria '{cat_limpa}' adicionada com sucesso!")
                    st.rerun()
                else:
                    st.warning("Esta categoria já existe.")
            else:
                st.warning("Digite um nome válido para a categoria.")
                
    st.markdown("### 📑 Categorias Atuais")
    if st.session_state.categorias:
        for idx, cat in enumerate(st.session_state.categorias):
            c1, c2 = st.columns([3, 1])
            c1.write(f"• **{cat}**")
            if c2.button("🗑️ Excluir", key=f"del_cat_{idx}"):
                if len(st.session_state.categorias) > 1:
                    st.session_state.categorias.pop(idx)
                    pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)
                    salvar_backup()
                    st.success("Categoria removida com sucesso!")
                    st.rerun()
                else:
                    st.error("Você precisa manter pelo menos uma categoria.")
