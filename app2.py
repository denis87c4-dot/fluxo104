import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fluxo104 - Profissional V2",
    page_icon="💎",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 14px;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
    }
    .metric-value {
        font-size: 24px;
        color: #f0f6fc;
        font-weight: bold;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

def conectar_banco():
    conn = sqlite3.connect("fluxo104_v2.db", check_same_thread=False)
    return conn

def inicializar_banco():
    conn = conectar_banco()
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

inicializar_banco()

def carregar_dados():
    conn = conectar_banco()
    df = pd.read_sql("SELECT * FROM transacoes", conn)
    conn.close()
    return df

st.title("💎 Fluxo104 | Painel Financeiro Executivo")
st.markdown("Seu novo ambiente de alta performance blindado com banco de dados SQLite.")

df_transacoes = carregar_dados()

if not df_transacoes.empty:
    total_receitas = df_transacoes[df_transacoes['tipo'] == 'Receita']['valor'].sum()
    total_despesas = df_transacoes[df_transacoes['tipo'] == 'Despesa']['valor'].sum()
    saldo_liquido = total_receitas - total_despesas
else:
    total_receitas = 0.0
    total_despesas = 0.0
    saldo_liquido = 0.0

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Receita Total</div>
            <div class="metric-value" style="color: #3fb950;">R$ {total_receitas:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Despesas Totais</div>
            <div class="metric-value" style="color: #f85149;">R$ {total_despesas:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Saldo Líquido</div>
            <div class="metric-value" style="color: #58a6ff;">R$ {saldo_liquido:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

with st.sidebar:
    st.header("➕ Novo Lançamento")
    with st.form("form_novo"):
        data = st.date_input("Data")
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        categoria = st.text_input("Categoria", "Ex: Alimentação")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        
        enviar = st.form_submit_button("Salvar no Banco")
        
        if enviar:
            conn = conectar_banco()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transacoes (data, tipo, categoria, valor, descricao)
                VALUES (?, ?, ?, ?, ?)
            """, (str(data), tipo, categoria, valor, descricao))
            conn.commit()
            conn.close()
            st.success("Salvo com segurança!")
            st.rerun()

st.subheader("📋 Seus Registros")
if not df_transacoes.empty:
    st.dataframe(df_transacoes, use_container_width=True)
else:
    st.info("O banco está vazio. Adicione seu primeiro lançamento usando a barra lateral ao lado!")

