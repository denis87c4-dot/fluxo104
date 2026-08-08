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

# Função para conectar e atualizar a estrutura do banco SQLite com os novos campos
def init_db():
    conn = sqlite3.connect("fluxo104_v2.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            descricao TEXT,
            categoria TEXT,
            conta TEXT,
            valor REAL,
            efetivado TEXT,
            transferencia TEXT,
            orcamento TEXT,
            parcelamento TEXT,
            modo_replicacao TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Cabeçalho Principal
st.title("💎 Fluxo104 | Gestão Financeira Avançada")
st.write("Painel executivo com indicadores estatísticos e controle inteligente de contas.")

# Barra lateral para novos lançamentos com todos os campos solicitados
st.sidebar.header("➕ Novo Lançamento")
with st.sidebar.form("form_transacao", clear_on_submit=True):
    data = st.date_input("Data")
    tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
    descricao = st.text_input("Descrição")
    categoria = st.selectbox("Categoria", ["Salário", "Vendas", "Alimentação", "Moradia", "Transporte", "Lazer", "Outros"])
    conta = st.selectbox("Conta (Account)", ["Conta Corrente", "Cartão de Crédito", "Dinheiro", "Investimentos"])
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    
    st.markdown("---")
    st.subheader("Parâmetros Avançados")
    efetivado = st.checkbox("Efetivado?", value=True)
    transfer = st.checkbox("É Transferência?")
    budget = st.checkbox("Incluir no Budget (Orçamento)?", value=True)
    
    parcelas = st.number_input("Parcelamento (Qtd de vezes)", min_value=1, max_value=48, value=1)
    modo_rep = st.selectbox("Ação para Parcelamento", ["Nenhum / À vista", "Dividir valor total nas parcelas", "Replicar valor integral em cada parcela"])
    
    submitted = st.form_submit_button("Salvar Lançamento")
    
    if submitted and valor > 0:
        conn = sqlite3.connect("fluxo104_v2.db")
        cursor = conn.cursor()
        
        status_efetivado = "Sim" if efetivado else "Não"
        status_transfer = "Sim" if transfer else "Não"
        status_budget = "Sim" if budget else "Não"
        
        # Lógica de parcelamento (Dividir vs Replicar)
        if parcelas > 1 and modo_rep == "Dividir valor total nas parcelas":
            valor_parcela = valor / parcelas
            for i in range(1, parcelas + 1):
                desc_parcela = f"{descricao} (Parcela {i}/{parcelas})"
                cursor.execute("""
                    INSERT INTO transacoes (data, tipo, descricao, categoria, conta, valor, efetivado, transferencia, orcamento, parcelamento, modo_replicacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(data), tipo, desc_parcela, categoria, conta, valor_parcela, status_efetivado, status_transfer, status_budget, f"{i}/{parcelas}", modo_rep))
        elif parcelas > 1 and modo_rep == "Replicar valor integral em cada parcela":
            for i in range(1, parcelas + 1):
                desc_parcela = f"{descricao} (Repetido {i}/{parcelas})"
                cursor.execute("""
                    INSERT INTO transacoes (data, tipo, descricao, categoria, conta, valor, efetivado, transferencia, orcamento, parcelamento, modo_replicacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(data), tipo, desc_parcela, categoria, conta, valor, status_efetivado, status_transfer, status_budget, f"{i}/{parcelas}", modo_rep))
        else:
            cursor.execute("""
                INSERT INTO transacoes (data, tipo, descricao, categoria, conta, valor, efetivado, transferencia, orcamento, parcelamento, modo_replicacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(data), tipo, descricao, categoria, conta, valor, status_efetivado, status_transfer, status_budget, "1/1", "À vista"))
            
        conn.commit()
        conn.close()
        st.sidebar.success("Lançamento(s) salvo(s) com sucesso!")
        st.rerun()

# Carregar dados do Banco de Dados
conn = sqlite3.connect("fluxo104_v2.db")
df = pd.read_sql_query("SELECT * FROM transacoes", conn)
conn.close()

# Se houver dados, exibe o painel analítico completo
if not df.empty:
    receitas_totais = df[df["tipo"] == "Receita"]["valor"].sum()
    despesas_totais = df[df["tipo"] == "Despesa"]["valor"].sum()
    saldo_liquido = receitas_totais - despesas_totais
    taxa_poupanca = (saldo_liquido / receitas_totais * 100) if receitas_totais > 0 else 0.0

    st.markdown("### 📊 Indicadores Executivos (KPIs)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Receita Total", value=f"R$ {receitas_totais:,.2f}")
    with col2:
        st.metric(label="Despesas Totais", value=f"R$ {despesas_totais:,.2f}")
    with col3:
        st.metric(label="Saldo Líquido", value=f"R$ {saldo_liquido:,.2f}")
    with col4:
        st.metric(label="Taxa de Poupança", value=f"{taxa_poupanca:.1f}%")

    st.markdown("---")
    st.subheader("📋 Histórico Completo de Lançamentos")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Ainda não há transações cadastradas. Utilize a barra lateral para registrar o seu primeiro lançamento!")
