import streamlit as st
from recomendacoes import mostra_badges

# Se você não tiver o arquivo anime.py, aqui estão algumas funções de fallback
def fallback_predict_score_knn(booleans):
    """Função de fallback para predição de nota"""
    # Implementação simples baseada na média dos gêneros selecionados
    # Substitua pela sua implementação real
    base_score = 7.0  # Nota base
    genre_bonus = len([b for b in booleans if b]) * 0.3  # Bônus por gênero
    predicted_score = min(10.0, base_score + genre_bonus)
    return predicted_score

def fallback_get_top_animes(_, n=10):
    """Função de fallback para obter top animes"""
    # Retorna uma lista de IDs fictícios
    return list(range(1, n + 1))

def fallback_get_anime_info(_):
    """Função de fallback para obter informações dos animes"""
    # Retorna um DataFrame vazio do Polars
    import polars as pl
    return pl.DataFrame({
        'Name': [],
        'Score': [],
        'Genres_combination': []
    })

# Tenta importar as funções reais, se não conseguir, usa as de fallback
try:
    from anime import get_top_animes, get_anime_info, predict_score_knn
except ImportError:
    st.warning("Arquivo anime.py não encontrado. Usando funções de fallback.")
    predict_score_knn = fallback_predict_score_knn
    get_top_animes = fallback_get_top_animes
    get_anime_info = fallback_get_anime_info

def interface_predicao_nota(generos_unicos):
    """Interface para predição de nota de anime"""
    st.subheader("🎯 Predição de Nota")
    st.markdown("Selecione os gêneros desejados para prever a nota do anime:")
    
    # Organiza os gêneros em colunas
    num_cols = 4
    cols = st.columns(num_cols)
    generos_selecionados = []
    
    # Distribui os gêneros pelas colunas
    for idx, genero in enumerate(generos_unicos):
        col_idx = idx % num_cols
        with cols[col_idx]:
            key_name = f"pred_{genero}"
            if st.checkbox(genero, key=key_name):
                generos_selecionados.append(genero)
    
    # Mostra os gêneros selecionados
    if generos_selecionados:
        mostra_badges(generos_selecionados)
    
    # Botão de predição
    if st.button("🔮 Prever Nota", type="primary"):
        if generos_selecionados:
            # Cria o array de booleans
            booleans = [g in generos_selecionados for g in generos_unicos]
            
            try:
                # Faz a predição
                pred = predict_score_knn(booleans)
                
                # Exibe o resultado
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1abc9c, #16a085); 
                           padding: 25px; 
                           border-radius: 15px; 
                           text-align: center; 
                           margin: 20px 0;
                           box-shadow: 0 8px 25px rgba(0,0,0,0.3);'>
                    <h2 style='color: white; margin: 0; font-size: 2.2em;'>
                        ⭐ Nota Estimada: {pred:.2f}
                    </h2>
                    <p style='color: #ecf0f1; margin: 10px 0 0 0; font-size: 1.1em;'>
                        Baseado nos gêneros selecionados
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Interpretação da nota
                if pred >= 8.5:
                    interpretation = "🏆 Excelente! Anime altamente recomendado."
                elif pred >= 7.5:
                    interpretation = "👍 Muito bom! Vale a pena assistir."
                elif pred >= 6.5:
                    interpretation = "😊 Bom. Pode ser interessante."
                elif pred >= 5.5:
                    interpretation = "🤔 Mediano. Depende do seu gosto."
                else:
                    interpretation = "😕 Abaixo da média. Considere outras opções."
                
                st.info(f"**Interpretação:** {interpretation}")

                # Busca recomendações
                with st.spinner("Buscando animes recomendados..."):
                    try:
                        top_ids = get_top_animes(booleans, n=10)
                        top_info = get_anime_info(top_ids)
                        
                        if not top_info.is_empty():
                            st.markdown("### 🎬 Exemplos de Animes:")
                            st.markdown("*Baseado nos gêneros selecionados*")
                            
                            # Exibe os animes recomendados
                            for idx, row in enumerate(top_info.iter_rows(named=True)):
                                # Cor alternada para melhor visualização
                                bg_color = "#2c3e50" if idx % 2 == 0 else "#34495e"
                                
                                st.markdown(f"""
                                <div style='background: {bg_color}; 
                                           border-radius: 12px; 
                                           margin: 12px 0; 
                                           padding: 20px;
                                           border-left: 4px solid #1abc9c;
                                           box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                                    <h4 style='color: #1abc9c; margin: 0 0 10px 0;'>
                                        {idx + 1}. {row['Name']}
                                    </h4>
                                    <div style='display: flex; gap: 20px; align-items: center;'>
                                        <span style='color: #f39c12; font-size: 1.1em;'>
                                            ⭐ <b>{row['Score']:.2f}</b>
                                        </span>
                                        <span style='color: #ecf0f1; font-size: 0.9em;'>
                                            📊 {row['Genres_combination']}
                                        </span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("Nenhum anime recomendado encontrado para essa combinação de gêneros.")
                    
                    except Exception as e:
                        st.error(f"Erro ao buscar recomendações: {str(e)}")
            
            except Exception as e:
                st.error(f"Erro na predição: {str(e)}")
                st.info("Verifique se o arquivo anime.py está presente e as funções estão implementadas corretamente.")
        
        else:
            st.warning("⚠️ Selecione pelo menos um gênero antes de fazer a predição!")
    
    # Informações adicionais
    with st.expander("ℹ️ Como funciona a predição?"):
        st.markdown("""
        A predição de nota é baseada em um modelo de Machine Learning que analisa:
        
        - **Gêneros selecionados**: Cada combinação de gêneros tem características específicas
        - **Dados históricos**: O modelo foi treinado com milhares de animes
        - **Algoritmo KNN**: Utiliza k-vizinhos mais próximos para fazer a predição
        
        **Interpretação das notas:**
        - 9.0 - 10.0: Obra-prima
        - 8.0 - 8.9: Excelente
        - 7.0 - 7.9: Muito bom
        - 6.0 - 6.9: Bom
        - 5.0 - 5.9: Mediano
        - Abaixo de 5.0: Abaixo da média
        """)