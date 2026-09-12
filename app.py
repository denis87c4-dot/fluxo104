from datetime import datetime
import io
import os
import zipfile
import altair as alt
import pandas as pd
import streamlit as st
import pdfplumber

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Sistema ACE - Gestão Integrada de Endemias", layout="wide"
)

st.title("🛡️ Sistema de Controle de Endemias (ACE - Painel Integrado)")

# ==================== PERSISTÊNCIA AUTOMÁTICA EM DISCO ====================
ARQUIVO_VISTORIAS = "vistorias_diarias.csv"
ARQUIVO_RECONHECIMENTO = "reconhecimento.csv"

# Inicialização de estados globais unificados com recuperação automática do disco
if "vistorias" not in st.session_state:
    if os.path.exists(ARQUIVO_VISTORIAS):
        try:
            df_v_init = pd.read_csv(ARQUIVO_VISTORIAS)
            if "Ciclo" not in df_v_init.columns:
                df_v_init["Ciclo"] = "Ciclo 1"
            st.session_state.vistorias = df_v_init.to_dict("records")
        except:
            st.session_state.vistorias = []
    else:
        st.session_state.vistorias = []

if "reconhecimento" not in st.session_state:
    if os.path.exists(ARQUIVO_RECONHECIMENTO):
        try:
            df_r_init = pd.read_csv(ARQUIVO_RECONHECIMENTO)
            st.session_state.reconhecimento = df_r_init.to_dict("records")
        except:
            st.session_state.reconhecimento = []
    else:
        st.session_state.reconhecimento = []

def salvar_estado_local():
    """Função auxiliar para salvar os dados instantaneamente no disco local"""
    if st.session_state.vistorias:
        pd.DataFrame(st.session_state.vistorias).to_csv(ARQUIVO_VISTORIAS, index=False)
    elif os.path.exists(ARQUIVO_VISTORIAS):
        os.remove(ARQUIVO_VISTORIAS)
        
    if st.session_state.reconhecimento:
        pd.DataFrame(st.session_state.reconhecimento).to_csv(ARQUIVO_RECONHECIMENTO, index=False)
    elif os.path.exists(ARQUIVO_RECONHECIMENTO):
        os.remove(ARQUIVO_RECONHECIMENTO)

# ==================== ABAS PRINCIPAIS ====================
(
    aba_cadastro,
    aba_busca,
    aba_gerenciar,
    aba_tratamentos,
    aba_fechadas,
    aba_semanal,
    aba_backup,
    aba_reconhecimento,
    aba_foto,
) = st.tabs([
    "📝 Relatório Diário",
    "🔍 Busca Avançada & Edição",
    "✏️ Gerenciar Lançamentos",
    "🧪 Análise de Tratamentos",
    "🚪 Imóveis Fechados & Recusas",
    "📈 Relatório Semanal",
    "💾 Central de Backup",
    "📊 Reconhecimento & Auditoria",
    "📸 Leitura por Foto",
])


# ==================== ABA 1: RELATÓRIO DIÁRIO ====================
with aba_cadastro:
  st.subheader("📋 Relatório Diário de Campo (Modo Rápido)")
  st.markdown(
      "⚡ **Modo de Campo Agilizado:** O sistema memoriza seus últimos dados"
      " preenchidos. Ao salvar, apenas o número da casa é limpo para a próxima"
      " vistoria!"
  )

  historico_quart = (
      sorted(list(set([str(v["Quarteirao"]) for v in st.session_state.vistorias if "Quarteirao" in v and v["Quarteirao"]])))
      if st.session_state.vistorias else []
  )
  historico_ruas = (
      sorted(list(set([str(v["Rua"]) for v in st.session_state.vistorias if "Rua" in v and v["Rua"]])))
      if st.session_state.vistorias else []
  )
  historico_agentes = (
      sorted(list(set([str(v["Agente"]) for v in st.session_state.vistorias if "Agente" in v and v["Agente"]])))
      if st.session_state.vistorias else []
  )

  with st.form("form_relatorio_diario", clear_on_submit=False):
    col1, col2, col3 = st.columns(3)

    with col1:
      data_visita = st.date_input("Data da Visita", value=datetime.today())
      semana_padrao = int(data_visita.strftime("%V"))
      num_semana = st.number_input(
          "📅 Número da Semana Epidemiológica", min_value=1, max_value=53, value=semana_padrao, step=1
      )
      ciclo_selecionado = st.selectbox(
          "🔄 Ciclo Epidemiológico", ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"]
      )
      opcoes_q = historico_quart + ["➕ Digitar novo quarteirão..."]
      sel_q = st.selectbox("Nº do Quarteirão", options=opcoes_q, key="select_quarteirao")
      if sel_q == "➕ Digitar novo quarteirão..." or not historico_quart:
        num_quarteirao = st.text_input("Digite o Novo Quarteirão", placeholder="Ex: 56", key="input_novo_quarteirao")
      else:
        num_quarteirao = sel_q

    with col2:
      lado = st.number_input("Lado do Quarteirão", min_value=1, value=1, step=1)
      opcoes_r = historico_ruas + ["➕ Digitar nova rua..."]
      sel_r = st.selectbox("Nome da Rua / Logradouro", options=opcoes_r, key="select_rua")
      if sel_r == "➕ Digitar nova rua..." or not historico_ruas:
        nome_rua = st.text_input("Digite a Nova Rua", placeholder="Ex: Rua Menino Jesus", key="input_nova_rua")
      else:
        nome_rua = sel_r
      num_casa = st.text_input("Nº / Identificação do Imóvel", placeholder="Ex: 05")

    with col3:
      tipo_imovel = st.selectbox(
          "Tipo de Imóvel",
          ["Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)", "Outros (OUT)"]
      )
      hora_entrada = st.time_input("Hora de Entrada", value=datetime.now().time())
      vistoria = st.selectbox("Condição da Vistoria", ["Normal", "Recuperada", "Fechada / Recusa"])
      opcoes_a = historico_agentes + ["➕ Digitar novo agente..."]
      sel_a = st.selectbox("Agente Responsável", options=opcoes_a, key="select_agente")
      if sel_a == "➕ Digitar novo agente..." or not historico_agentes:
        agente_resp = st.text_input("Digite o Nome do Agente", placeholder="Ex: Denison Oliveira", key="input_novo_agente")
      else:
        agente_resp = sel_a

    st.markdown("---")
    st.subheader("🔬 Dados Entomológicos e Tratamento")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: eliminados = st.number_input("Eliminados", min_value=0, value=0)
    with c2: tubitos = st.number_input("Tubitos", min_value=0, value=0)
    with c3: imoveis_tratados = st.number_input("Tratados", min_value=0, value=0)
    with c4: gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f", value=0.0)
    with c5: depositos = st.number_input("Depósitos", min_value=0, value=0)
    with c6: litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f", value=0.0)

    submitted = st.form_submit_button("💾 Salvar Registro Diário", use_container_width=True)

    if submitted:
      if not num_quarteirao or not nome_rua or not num_casa:
        st.error("⚠️ Preencha Quarteirão, Rua e Número da Casa.")
      else:
        novo_registro = {
            "Data": data_visita.strftime("%d/%m/%Y"),
            "Semana": int(num_semana),
            "Ciclo": ciclo_selecionado,
            "Quarteirao": str(num_quarteirao).strip(),
            "Lado": int(lado),
            "Rua": str(nome_rua).strip(),
            "Casa": str(num_casa).strip(),
            "Tipo Imovel": tipo_imovel,
            "Hora": hora_entrada.strftime("%H:%M"),
            "Vistoria": vistoria,
            "Agente": str(agente_resp).strip(),
            "Eliminados": int(eliminados),
            "Tubitos": int(tubitos),
            "Tratados": int(imoveis_tratados),
            "Gramas": float(gramas),
            "Depósitos": int(depositos),
            "Litros": float(litros),
        }
        st.session_state.vistorias.append(novo_registro)

        res_val, com_val, tb_val, out_val = 0, 0, 0, 0
        if "Residência" in tipo_imovel: res_val = 1
        elif "Comércio" in tipo_imovel: com_val = 1
        elif "Terreno" in tipo_imovel: tb_val = 1
        else: out_val = 1

        registro_rec = {
            "Quarteirao": str(num_quarteirao).strip(),
            "Lado": int(lado),
            "Residencias": res_val,
            "Outros": out_val,
            "TB": tb_val,
            "Comercio": com_val,
            "Total": 1,
            "Data": data_visita.strftime("%d/%m/%Y"),
            "Semana": int(num_semana),
            "Auditor": agente_resp if agente_resp else "Geral",
        }
        st.session_state.reconhecimento.append(registro_rec)
        salvar_estado_local()
        st.success(f"✅ Imóvel **{num_casa}** salvo com sucesso!")
        st.rerun()

  if st.session_state.vistorias:
    st.markdown("---")
    st.subheader("📊 Resumo Operacional Acumulado")
    df_v = pd.DataFrame(st.session_state.vistorias)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Visitas", len(df_v))
    m2.metric("Dep. Eliminados", int(df_v["Eliminados"].sum()))
    m3.metric("Tubitos Coletados", int(df_v["Tubitos"].sum()))
    m4.metric("Imóveis Tratados", int(df_v["Tratados"].sum()))
    m5.metric("Larvicida (g)", f"{df_v['Gramas'].sum():.1f}g")

# ==================== ABA 2: BUSCA AVANÇADA ====================
with aba_busca:
    st.subheader("🔍 Busca Avançada e Edição Direta (Estilo Planilha)")
    st.markdown("Use os filtros para encontrar os lançamentos. **Clique na célula que deseja alterar, digite o novo valor e pressione Enter**. Depois, clique no botão salvar abaixo!")

    if st.session_state.vistorias:
        df_base = pd.DataFrame(st.session_state.vistorias)

        for col in df_base.columns:
            if col not in ["Semana", "Lado", "Eliminados", "Tubitos", "Tratados", "Gramas", "Depósitos", "Litros"]:
                df_base[col] = df_base[col].astype(str)

        with st.expander("🎛️ Filtros Avançados", expanded=True):
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            with fc1:
                ciclos_disp = ["Todos"] + sorted(df_base["Ciclo"].unique().tolist()) if "Ciclo" in df_base.columns else ["Todos"]
                filtro_ciclo = st.selectbox("Filtrar por Ciclo", ciclos_disp, key="busca_ciclo")
            with fc2:
                semanas_disp = ["Todas"] + sorted(df_base["Semana"].astype(str).unique().tolist()) if "Semana" in df_base.columns else ["Todas"]
                filtro_semana = st.selectbox("Filtrar por Semana", semanas_disp, key="busca_semana")
            with fc3:
                quarts_disp = ["Todos"] + sorted(df_base["Quarteirao"].unique().tolist()) if "Quarteirao" in df_base.columns else ["Todos"]
                filtro_quarteirao = st.selectbox("Filtrar por Quarteirão", quarts_disp, key="busca_quarteirao")
            with fc4:
                tipos_disp = ["Todos"] + sorted(df_base["Tipo Imovel"].unique().tolist()) if "Tipo Imovel" in df_base.columns else ["Todos"]
                filtro_tipo = st.selectbox("Filtrar por Tipo de Imóvel", tipos_disp, key="busca_tipo")
            with fc5:
                cond_disp = ["Todas"] + sorted(df_base["Vistoria"].unique().tolist()) if "Vistoria" in df_base.columns else ["Todas"]
                filtro_cond = st.selectbox("Filtrar por Condição", cond_disp, key="busca_cond")

        termo = st.text_input("🔎 Pesquisa rápida por termo (Rua, Número, Agente, etc.):", placeholder="Ex: 56, Rua Menino Jesus, Denison...")

        df_filtrado = df_base.copy()
        if filtro_ciclo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Ciclo"] == filtro_ciclo]
        if filtro_semana != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Semana"].astype(str) == str(filtro_semana)]
        if filtro_quarteirao != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Quarteirao"].astype(str) == str(filtro_quarteirao)]
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo Imovel"] == filtro_tipo]
        if filtro_cond != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Vistoria"] == filtro_cond]

        if termo:
            mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo, case=False, na=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]

        st.info(f"Exibindo **{len(df_filtrado)}** registros correspondentes. Clique na célula, digite e aperte Enter:")

        df_editado = st.data_editor(
            df_filtrado,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_busca_excel"
        )

        col_b_salvar, col_b_down = st.columns(2)
        with col_b_salvar:
            if st.button("💾 Salvar Alterações Feitas na Tabela", type="primary", use_container_width=True, key="btn_salvar_tabela_busca"):
                novos_dados_filtrados = df_editado.to_dict("records")
                
                if len(df_filtrado) == len(st.session_state.vistorias):
                    st.session_state.vistorias = novos_dados_filtrados
                else:
                    indices_originais = df_filtrado.index.tolist()
                    for idx_orig, novo_row in zip(indices_originais, novos_dados_filtrados):
                        st.session_state.vistorias[idx_orig] = novo_row

                salvar_estado_local()
                st.success("✅ Alterações salvas com sucesso!")
                st.rerun()

        with col_b_down:
            csv_exp = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV Filtrado", data=csv_exp, file_name="vistorias_filtradas.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("Nenhum registro cadastrado.")

# ==================== ABA 3: GERENCIAR LANÇAMENTOS ====================
with aba_gerenciar:
    st.subheader("✏️ Gerenciamento e Edição Inteligente em Massa")
    st.markdown("Aqui você pode alterar um dado incorreto (como um quarteirão inteiro ou agente) **em todos os registros de uma só vez**, ou gerenciar lançamentos individualmente.")

    if st.session_state.vistorias:
        st.markdown("### ⚡ Alteração Rápida em Massa (Modificar todos de uma vez)")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            coluna_alvo = st.selectbox("Coluna para alterar", ["Quarteirao", "Semana", "Ciclo", "Agente", "Rua", "Data"], key="massa_coluna")
        with col_m2:
            valor_antigo = st.text_input("Valor antigo (o que está errado)", placeholder="Ex: 03", key="massa_val_antigo")
        with col_m3:
            valor_novo = st.text_input("Novo valor (o correto)", placeholder="Ex: 56", key="massa_val_novo")
        with col_m4:
            st.markdown("<br>", unsafe_allow_html=True)
            btn_aplicar_massa = st.button("🚀 Aplicar em Massa", type="primary", use_container_width=True, key="btn_massa_direto")

        if btn_aplicar_massa:
            val_ant_limpo = str(valor_antigo).strip()
            val_nov_limpo = str(valor_novo).strip()

            if not val_ant_limpo:
                st.warning("⚠️ Informe o valor antigo que deseja substituir.")
            else:
                alterados_v = 0
                for item in st.session_state.vistorias:
                    atual_str = str(item.get(coluna_alvo, "")).strip()
                    if atual_str.lower() == val_ant_limpo.lower():
                        item[coluna_alvo] = val_nov_limpo
                        alterados_v += 1
                
                alterados_r = 0
                if coluna_alvo in ["Quarteirao", "Data", "Semana"]:
                    for item_r in st.session_state.reconhecimento:
                        atual_str_r = str(item_r.get(coluna_alvo, "")).strip()
                        if atual_str_r.lower() == val_ant_limpo.lower():
                            item_r[coluna_alvo] = val_nov_limpo
                            alterados_r += 1

                if alterados_v > 0 or alterados_r > 0:
                    salvar_estado_local()
                    st.success(f"✅ Sucesso! {alterados_v} vistorias e {alterados_r} reconhecimentos tiveram a coluna **{coluna_alvo}** alterada para **'{val_nov_limpo}'**.")
                    st.rerun()
                else:
                    st.warning(f"⚠️ Nenhum registro foi encontrado com o valor exato **'{val_ant_limpo}'** na coluna **{coluna_alvo}**.")

        st.markdown("---")
        st.subheader("🔍 Gerenciamento Individual (Editar ou Excluir por Imóvel)")
        
        opcoes_lancamentos = []
        for idx, item in enumerate(st.session_state.vistorias):
            rotulo = f"[{idx}] Data: {item.get('Data')} | Quarteirão: {item.get('Quarteirao')} | Rua: {item.get('Rua')} | Nº: {item.get('Casa')} | Agente: {item.get('Agente')}"
            opcoes_lancamentos.append((idx, rotulo))

        lancamento_selecionado_label = st.selectbox(
            "🔎 Escolha o lançamento específico:",
            options=[opt[1] for opt in opcoes_lancamentos],
            key="select_gerenciar_lancamento"
        )

        idx_selecionado = next(opt[0] for opt in opcoes_lancamentos if opt[1] == lancamento_selecionado_label)
        registro_atual = st.session_state.vistorias[idx_selecionado]

        col_acoes1, col_acoes2 = st.columns(2)
        with col_acoes1:
            if st.button("🗑️ Deletar Este Lançamento Permanentemente", type="primary", use_container_width=True, key="btn_deletar_unico"):
                st.session_state.vistorias.pop(idx_selecionado)
                salvar_estado_local()
                st.success("✅ Registro excluído com sucesso!")
                st.rerun()

        with st.form("form_editar_lancamento"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                nova_data = st.text_input("Data (DD/MM/YYYY)", value=str(registro_atual.get("Data", "")))
                ciclos_opcoes = ["Ciclo 1", "Ciclo 2", "Ciclo 3", "Ciclo 4", "Ciclo 5", "Ciclo 6"]
                c_atual = registro_atual.get("Ciclo", "Ciclo 1")
                idx_c = ciclos_opcoes.index(c_atual) if c_atual in ciclos_opcoes else 0
                novo_ciclo = st.selectbox("Ciclo", ciclos_opcoes, index=idx_c)
                novo_quarteirao = st.text_input("Quarteirão", value=str(registro_atual.get("Quarteirao", "")))
                novo_lado = st.number_input("Lado", min_value=1, value=int(registro_atual.get("Lado", 1)))
            with ec2:
                nova_rua = st.text_input("Rua", value=str(registro_atual.get("Rua", "")))
                nova_casa = st.text_input("Número / Casa", value=str(registro_atual.get("Casa", "")))
                tipos_possiveis = ["Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)", "Outros (OUT)"]
                tipo_atual = registro_atual.get("Tipo Imovel", "Residência (RES)")
                idx_tipo = tipos_possiveis.index(tipo_atual) if tipo_atual in tipos_possiveis else 0
                novo_tipo = st.selectbox("Tipo de Imóvel", tipos_possiveis, index=idx_tipo)
                nova_hora = st.text_input("Hora (HH:MM)", value=str(registro_atual.get("Hora", "")))
            with ec3:
                cond_possiveis = ["Normal", "Recuperada", "Fechada / Recusa"]
                cond_atual = registro_atual.get("Vistoria", "Normal")
                idx_cond = cond_possiveis.index(cond_atual) if cond_atual in cond_possiveis else 0
                nova_cond = st.selectbox("Condição da Vistoria", cond_possiveis, index=idx_cond)
                novo_agente = st.text_input("Agente", value=str(registro_atual.get("Agente", "")))
                novos_eliminados = st.number_input("Eliminados", min_value=0, value=int(registro_atual.get("Eliminados", 0)))
                novos_tubitos = st.number_input("Tubitos", min_value=0, value=int(registro_atual.get("Tubitos", 0)))

            ec4, ec5, ec6 = st.columns(3)
            with ec4: novos_tratados = st.number_input("Tratados", min_value=0, value=int(registro_atual.get("Tratados", 0)))
            with ec5: novas_gramas = st.number_input("Gramas (g)", min_value=0.0, format="%.1f", value=float(registro_atual.get("Gramas", 0.0)))
            with ec6: novos_depositos = st.number_input("Depósitos", min_value=0, value=int(registro_atual.get("Depósitos", 0)))
            novos_litros = st.number_input("Litros (L)", min_value=0.0, format="%.1f", value=float(registro_atual.get("Litros", 0.0)))

            btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações deste Imóvel", use_container_width=True)
            if btn_salvar_edicao:
                st.session_state.vistorias[idx_selecionado] = {
                    "Data": nova_data,
                    "Semana": registro_atual.get("Semana", 1),
                    "Ciclo": novo_ciclo,
                    "Quarteirao": str(novo_quarteirao).strip(),
                    "Lado": int(novo_lado),
                    "Rua": str(nova_rua).strip(),
                    "Casa": str(nova_casa).strip(),
                    "Tipo Imovel": novo_tipo,
                    "Hora": nova_hora,
                    "Vistoria": nova_cond,
                    "Agente": str(novo_agente).strip(),
                    "Eliminados": int(novos_eliminados),
                    "Tubitos": int(novos_tubitos),
                    "Tratados": int(novos_tratados),
                    "Gramas": float(novas_gramas),
                    "Depósitos": int(novos_depositos),
                    "Litros": float(novos_litros),
                }
                salvar_estado_local()
                st.success("✅ Lançamento atualizado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum lançamento registrado para gerenciar.")

# ==================== ABA 4: ANÁLISE DE TRATAMENTOS ====================
with aba_tratamentos:
    st.subheader("🧪 Painel de Tratamentos e Comparativo entre Quarteirões")
    if st.session_state.vistorias:
        df_trat = pd.DataFrame(st.session_state.vistorias)

        with st.expander("🎛️ Filtros da Análise de Tratamento", expanded=True):
            tc1, tc2 = st.columns(2)
            with tc1:
                ciclos_t = ["Todos"] + sorted(df_trat["Ciclo"].unique().tolist()) if "Ciclo" in df_trat.columns else ["Todos"]
                filtro_ciclo_t = st.selectbox("Filtrar Ciclo", ciclos_t, key="trat_ciclo")
            with tc2:
                semanas_t = ["Todas"] + sorted(df_trat["Semana"].unique().tolist()) if "Semana" in df_trat.columns else ["Todas"]
                filtro_semana_t = st.selectbox("Filtrar Semana", semanas_t, key="trat_semana")

        if filtro_ciclo_t != "Todos":
            df_trat = df_trat[df_trat["Ciclo"] == filtro_ciclo_t]
        if filtro_semana_t != "Todas":
            df_trat = df_trat[df_trat["Semana"] == filtro_semana_t]

        tot_tratados = int(df_trat["Tratados"].sum()) if "Tratados" in df_trat.columns else 0
        tot_gramas = float(df_trat["Gramas"].sum()) if "Gramas" in df_trat.columns else 0.0
        tot_depositos = int(df_trat["Depósitos"].sum()) if "Depósitos" in df_trat.columns else 0
        tot_litros = float(df_trat["Litros"].sum()) if "Litros" in df_trat.columns else 0.0

        tm1, tm2, tm3, tm4 = st.columns(4)
        tm1.metric("🏠 Imóveis Tratados", tot_tratados)
        tm2.metric("⚖️ Larvicida Aplicado (g)", f"{tot_gramas:.1f}g")
        tm3.metric("🛢️ Depósitos Tratados", tot_depositos)
        tm4.metric("💧 Água Tratada (L)", f"{tot_litros:.1f}L")

        st.markdown("---")
        if not df_trat.empty and "Quarteirao" in df_trat.columns:
            df_agrupado_quart = df_trat.groupby("Quarteirao").agg(
                Imóveis_Tratados=("Tratados", "sum"),
                Total_Gramas=("Gramas", "sum"),
                Total_Depósitos=("Depósitos", "sum"),
                Total_Litros=("Litros", "sum"),
                Visitas=("Casa", "count")
            ).reset_index()

            chart = alt.Chart(df_agrupado_quart).mark_bar(color="#1f77b4").encode(
                x=alt.X("Quarteirao:N", title="Quarteirão", sort="-y"),
                y=alt.Y("Imóveis_Tratados:Q", title="Quantidade de Imóveis Tratados"),
                tooltip=["Quarteirao", "Imóveis_Tratados", "Total_Gramas", "Total_Depósitos", "Visitas"]
            ).properties(height=400)

            st.altair_chart(chart, use_container_width=True)
            st.dataframe(df_agrupado_quart, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.info("Nenhum lançamento registrado no sistema.")

# ==================== ABA 5: IMÓVEIS FECHADOS & RECUSAS ====================
with aba_fechadas:
  st.subheader("🚪 Painel de Imóveis Fechados e Recusas")
  if st.session_state.vistorias:
    df_v = pd.DataFrame(st.session_state.vistorias)
    df_fechados = df_v[df_v["Vistoria"].str.contains("Fechada", case=False, na=False)]
    st.metric("Total Fechadas / Recusas", len(df_fechados))
    st.dataframe(df_fechados, use_container_width=True)
  else:
    st.info("Sem dados cadastrados.")

# ==================== ABA 6: RELATÓRIO SEMANAL ====================
with aba_semanal:
  st.subheader("📈 Boletim Semanal Consolidado")
  if st.session_state.vistorias:
    df_v = pd.DataFrame(st.session_state.vistorias)
    df_agrupado = df_v.groupby("Semana").agg(Total_Visitas=("Casa", "count"), Eliminados=("Eliminados", "sum"), Tratados=("Tratados", "sum")).reset_index()
    st.dataframe(df_agrupado, use_container_width=True)
  else:
    st.info("Sem dados cadastrados.")

# ==================== ABA 7: CENTRAL DE SEGURANÇA ====================
with aba_backup:
  st.subheader("🔐 Central de Segurança, Backup e Importação Flexível")
  col_b1, col_b2 = st.columns(2)

  with col_b1:
    st.markdown("### 📤 Exportar Dados")
    salvar_estado_local()
    if os.path.exists(ARQUIVO_VISTORIAS):
      with open(ARQUIVO_VISTORIAS, "rb") as f:
        st.download_button("📥 Baixar vistorias_diarias.csv", data=f, file_name="vistorias_diarias.csv", mime="text/csv", use_container_width=True)

  with col_b2:
    st.markdown("### 📥 Importação em Massa")
    arquivo_upload = st.file_uploader("Enviar arquivo de boletim", type=["csv", "txt", "dat", "xlsx", "xls", "pdf"], key="upload_flexivel_multiformat")

    if arquivo_upload is not None:
      extensao = arquivo_upload.name.split(".")[-1].lower()
      df_novo_importado = None

      try:
        if extensao in ["csv", "txt", "dat"]:
            df_novo_importado = pd.read_csv(arquivo_upload)
        elif extensao in ["xlsx", "xls"]:
            df_novo_importado = pd.read_excel(arquivo_upload)
        elif extensao == "pdf":
            with pdfplumber.open(arquivo_upload) as pdf:
                tabelas_extraidas = []
                for pagina in pdf.pages:
                    t = pagina.extract_tables()
                    if t:
                        for tabela in t:
                            tabelas_extraidas.extend(tabela)
                if tabelas_extraidas and len(tabelas_extraidas) > 1:
                    df_novo_importado = pd.DataFrame(tabelas_extraidas[1:], columns=tabelas_extraidas[0])
        
        if df_novo_importado is not None and not df_novo_importado.empty:
            st.success("✅ Arquivo lido com sucesso!")
            st.dataframe(df_novo_importado.head(5), use_container_width=True)

            if st.button("🔄 Confirmar e Inserir na Base do Sistema", type="primary", use_container_width=True):
              registros_novos = df_novo_importado.to_dict("records")
              for r in registros_novos:
                reg_formatado = {
                    "Data": str(r.get("Data", datetime.today().strftime("%d/%m/%Y"))),
                    "Semana": int(r.get("Semana", 1)),
                    "Ciclo": str(r.get("Ciclo", "Ciclo 1")),
                    "Quarteirao": str(r.get("Quarteirao", r.get("Quarteirão", "0"))).strip(),
                    "Lado": int(r.get("Lado", 1)),
                    "Rua": str(r.get("Rua", r.get("Logradouro", "Rua Principal"))).strip(),
                    "Casa": str(r.get("Casa", r.get("Nº Imóvel", r.get("Nº", "0")))).strip(),
                    "Tipo Imovel": str(r.get("Tipo Imovel", "Residência (RES)")),
                    "Hora": str(r.get("Hora", "08:00")),
                    "Vistoria": str(r.get("Vistoria", "Normal")),
                    "Agente": str(r.get("Agente", "Desconhecido")).strip(),
                    "Eliminados": int(r.get("Eliminados", 0) if pd.notna(r.get("Eliminados", 0)) else 0),
                    "Tubitos": int(r.get("Tubitos", 0) if pd.notna(r.get("Tubitos", 0)) else 0),
                    "Tratados": int(r.get("Tratados", 0) if pd.notna(r.get("Tratados", 0)) else 0),
                    "Gramas": float(r.get("Gramas", 0.0) if pd.notna(r.get("Gramas", 0.0)) else 0.0),
                    "Depósitos": int(r.get("Depósitos", 0) if pd.notna(r.get("Depósitos", 0)) else 0),
                    "Litros": float(r.get("Litros", 0.0) if pd.notna(r.get("Litros", 0.0)) else 0.0),
                }
                st.session_state.vistorias.append(reg_formatado)
                
                tipo_imovel = reg_formatado["Tipo Imovel"]
                res_val, com_val, tb_val, out_val = 0, 0, 0, 0
                if "Residência" in tipo_imovel: res_val = 1
                elif "Comércio" in tipo_imovel: com_val = 1
                elif "Terreno" in tipo_imovel: tb_val = 1
                else: out_val = 1

                st.session_state.reconhecimento.append({
                    "Quarteirao": reg_formatado["Quarteirao"],
                    "Lado": reg_formatado["Lado"],
                    "Residencias": res_val,
                    "Outros": out_val,
                    "TB": tb_val,
                    "Comercio": com_val,
                    "Total": 1,
                    "Data": reg_formatado["Data"],
                    "Semana": reg_formatado["Semana"],
                    "Auditor": reg_formatado["Agente"],
                })

              salvar_estado_local()
              st.success(f"✅ {len(registros_novos)} registros importados com sucesso!")
              st.rerun()
      except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")

  st.markdown("---")
  confirmar_limpeza = st.checkbox("Confirmo que desejo apagar absolutamente todos os lançamentos.", key="chk_confirmar_limpeza")
  if st.button("🗑️ Deletar TODOS os Lançamentos do Sistema", type="primary", use_container_width=True):
      if confirmar_limpeza:
          st.session_state.vistorias = []
          st.session_state.reconhecimento = []
          if os.path.exists(ARQUIVO_VISTORIAS): os.remove(ARQUIVO_VISTORIAS)
          if os.path.exists(ARQUIVO_RECONHECIMENTO): os.remove(ARQUIVO_RECONHECIMENTO)
          st.success("🧹 Dados apagados!")
          st.rerun()
      else:
          st.warning("⚠️ Marque a caixa de confirmação acima.")

# ==================== ABA 8: RECONHECIMENTO GEOGRÁFICO ====================
with aba_reconhecimento:
    st.subheader("📊 Reconhecimento Geográfico (Comparativo e Auditoria)")
    if st.session_state.reconhecimento:
        df_rec = pd.DataFrame(st.session_state.reconhecimento)
        with st.expander("🎛️ Filtros", expanded=True):
            rc1, rc2, rc3 = st.columns(3)
            with rc1: filtro_data_rec = st.selectbox("📅 Data", ["Todas"] + sorted(df_rec["Data"].unique().tolist()), key="rec_filtro_data")
            with rc2: filtro_semana_rec = st.selectbox("📆 Semana", ["Todas"] + sorted(df_rec["Semana"].unique().tolist()), key="rec_filtro_semana")
            with rc3: filtro_quart_rec = st.selectbox("🏘️ Quarteirão", ["Todos"] + sorted(df_rec["Quarteirao"].unique().tolist()), key="rec_filtro_quart")

        if filtro_data_rec != "Todas": df_rec = df_rec[df_rec["Data"] == filtro_data_rec]
        if filtro_semana_rec != "Todas": df_rec = df_rec[df_rec["Semana"] == filtro_semana_rec]
        if filtro_quart_rec != "Todos": df_rec = df_rec[df_rec["Quarteirao"] == filtro_quart_rec]

        if not df_rec.empty:
            df_rec_agrupado = df_rec.groupby(["Quarteirao", "Data", "Semana"]).agg(
                Residencias=("Residencias", "sum"),
                Outros=("Outros", "sum"),
                TB=("TB", "sum"),
                Comercio=("Comercio", "sum"),
                Total=("Total", "sum")
            ).reset_index().sort_values(by="Quarteirao")

            st.dataframe(df_rec_agrupado, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum registro encontrado.")
    else:
        st.info("Sem dados de reconhecimento geográfico.")

# ==================== ABA 9: LEITURA INTELIGENTE POR FOTO ====================
with aba_foto:
    st.subheader("📸 Leitura Inteligente de Boletim por Foto (IA)")
    api_key_input = st.text_input("🔑 Chave de API do Gemini", type="password", key="input_gemini_key_foto")
    foto_boletim = st.file_uploader("Foto do boletim", type=["png", "jpg", "jpeg"], key="upload_foto_boletim_ia")

    if foto_boletim is not None:
        st.image(foto_boletim, caption="Boletim enviado", use_container_width=True)
        if st.button("🚀 Processar Foto e Gerar Arquivo", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("Insira sua chave de API do Gemini.")
            else:
                try:
                    import json
                    import base64
                    import requests

                    with st.spinner("🤖 Lendo boletim e estruturando os dados..."):
                        image_bytes = foto_boletim.getvalue()
                        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                        mime_type = foto_boletim.type if foto_boletim.type else "image/jpeg"

                        prompt_extracao = """
                        Analise esta imagem de um Resumo Diário de Serviço Antivetorial preenchido à mão.
                        Extraia todas as linhas de vistorias. Retorne um array JSON com objetos contendo exatamente estes campos:
                        - "Data": string DD/MM/YYYY
                        - "Semana": inteiro
                        - "Ciclo": string (ex: "Ciclo 1")
                        - "Quarteirao": string
                        - "Lado": inteiro
                        - "Rua": string
                        - "Casa": string
                        - "Tipo Imovel": "Residência (RES)", "Comércio (COM)", "Terreno Baldio (TB)", "Ponto Estratégico (PE)" ou "Outros (OUT)"
                        - "Hora": string HH:MM
                        - "Vistoria": "Normal", "Recuperada", ou "Fechada / Recusa"
                        - "Agente": string
                        - "Eliminados": inteiro
                        - "Tubitos": inteiro
                        - "Tratados": inteiro
                        - "Gramas": float
                        - "Depósitos": inteiro
                        - "Litros": float
                        Retorne APENAS o JSON puro sem markdown extra.
                        """

                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key_input}"
                        payload = {
                            "contents": [{"parts": [{"text": prompt_extracao}, {"inline_data": {"mime_type": mime_type, "data": image_base64}}]}]
                        }
                        response = requests.post(url, json=payload)
                        
                        if response.status_code == 200:
                            texto_resp = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                            if texto_resp.startswith("```json"): texto_resp = texto_resp[7:-3].strip()
                            elif texto_resp.startswith("```"): texto_resp = texto_resp[3:-3].strip()
                            
                            lista_regs = json.loads(texto_resp)
                            df_lido = pd.DataFrame(lista_regs)
                            
                            st.success("✅ Leitura realizada com sucesso abaixo!")
                            st.dataframe(df_lido, use_container_width=True)

                            csv_data = df_lido.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Baixar Arquivo do Boletim (Para Importar na Central de Backup)",
                                data=csv_data,
                                file_name="boletim_lido.csv",
                                mime="text/csv",
                                type="primary"
                            )
                        else:
                            st.error(f"Erro na API: {response.text}")
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
