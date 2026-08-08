import sqlite3
import pandas as pd
import streamlit as st

# Configuração inicial da página com layout largo profissional
st.set_page_config(
    page_title="Fluxo104 - Painel Executivo",
    page_icon="💎",
    layout="wide"
)

# Estilização visual limpa (Dark Mode Executivo)
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Função para conectar e criar a tabela no banco SQLite
def init_db():
    conn = sqlite3.connect("fluxo104_v2.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            valor REAL,
            descricao TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Cabeçalho Principal
st.title("💎 Fluxo104 | Gestão Financeira Avançada")
st.write("Painel executivo com indicadores estatísticos e controle inteligente.")

# Barra lateral para novos lançamentos
st.sidebar.header("➕ Nova Transação")
with st.sidebar.form("form_transacao", clear_on_submit=True):
    data = st.date_input("Data")
    tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
    categoria = st.selectbox("Categoria", ["Salário", "Vendas", "Alimentação", "Moradia", "Transporte", "Outros"])
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    descricao = st.text_input("Descrição / Observação")
    
    submitted = st.form_submit_button("Salvar Lançamento")
    
    if submitted and valor > 0:
        conn = sqlite3.connect("fluxo104_v2.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transacoes (data, tipo, categoria, valor, descricao)
            VALUES (?, ?, ?, ?, ?)
        """, (str(data), tipo, categoria, valor, descricao))
        conn.commit()
        conn.close()
        st.sidebar.success("Lançamento salvo com sucesso!")
        st.rerun()

# Carregar dados do Banco de Dados
conn = sqlite3.connect("fluxo104_v2.db")
df = pd.read_sql_query("SELECT * FROM transacoes", conn)
conn.close()

# Se houver dados, exibe o painel analítico da Fase 1
if not df.empty:
    # Conversões e cálculos estatísticos
    receitas_totais = df[df["tipo"] == "Receita"]["valor"].sum()
    despesas_totais = df[df["tipo"] == "Despesa"]["valor"].sum()
    saldo_liquido = receitas_totais - despesas_totais
    
    # Parâmetro Avançado: Taxa de Poupança (quanto sobra das receitas)
    taxa_poupanca = (saldo_liquido / receitas_totais * 100) if receitas_totais > 0 else 0.0

    st.markdown("### 📊 Indicadores Executivos (KPIs)")
    
    # Layout de Cartões em Colunas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Receita Total", value=f"R$ {receitas_totais:,.2f}")
    with col2:
        st.metric(label="Despesas Totais", value=f"R$ {despesas_totais:,.2f}", delta=f"-R$ {despesas_totais:,.2f}" if despesas_totais > 0 else None, delta_color="inverse")
    with col3:
        st.metric(label="Saldo Líquido", value=f"R$ {saldo_liquido:,.2f}")
    with col4:
        st.metric(label="Taxa de Poupança", value=f"{taxa_poupanca:.1f}%")

    st.markdown("---")
    
    # Seção de Dados Detalhados
    st.subheader("📋 Histórico de Lançamentos")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Ainda não há transações cadastradas. Utilize a barra lateral à esquerda para registrar o seu primeiro lançamento!")
