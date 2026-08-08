elif aba == "Cadastro (Form)":
    st.subheader("📝 Novo Registro (Formulário Executivo)")
    st.markdown("Preencha os dados abaixo para registrar uma nova **Despesa**, **Receita** ou **Transferência** com suporte a parcelamento e cartões de crédito.")

    with st.form("form_cadastro_executivo", clear_on_submit=False):
        col_a, col_b = st.columns(2)
        with col_a:
            tipo = st.selectbox("Tipo de Lançamento", ["Despesa", "Receita", "Transferência"])
        with col_b:
            status = st.selectbox("Status / Fase", ["Budget", "Efetivado"])
            
        descricao = st.text_input("Descrição", placeholder="Ex: Assinatura Software, Supermercado, Salário...")
        
        # Gerenciamento de Categorias
        lista_cat_opcao = st.session_state.categorias + ["+ Incluir Nova Categoria..."]
        cat_escolhida = st.selectbox("Categoria", lista_cat_opcao)
        categoria_final = cat_escolhida
        if cat_escolhida == "+ Incluir Nova Categoria...":
            nova_cat_digitada = st.text_input("Digite o nome da nova categoria:")
            if nova_cat_digitada.strip() != "":
                categoria_final = nova_cat_digitada.strip()

        # Contas e Cartões
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

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", step=10.0)
        with col_v2:
            data_compra = st.date_input("Data da Transação", value=datetime.today())
        
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            parcelas = st.number_input("Parcelas", min_value=1, max_value=48, value=1)
        with col_p2:
            frequencia = st.selectbox("Frequência", ["Mensal", "Quinzenal", "Anual", "Única"])
        with col_p3:
            modo_valor = st.selectbox("Modo de Valor", ["Dividir Total", "Replicar Integral"])
        
        submitted = st.form_submit_button("💾 Salvar Lançamento", type="primary")
        
        if submitted:
            if cat_escolhida == "+ Incluir Nova Categoria..." and categoria_final not in st.session_state.categorias:
                st.session_state.categorias.append(categoria_final)
                pd.DataFrame({"Categoria": st.session_state.categorias}).to_csv(ARQUIVO_CATEGORIAS, index=False)

            if descricao.strip() == "":
                st.warning("Por favor, preencha a descrição do lançamento.")
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

                st.success("Lançamento(s) gerado(s) e salvo(s) com sucesso!")
