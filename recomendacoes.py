import streamlit as st
import polars as pl

# Funções de fallback caso o arquivo anime.py não seja encontrado
def fallback_get_top_animes(booleans, n=10):
    """Função de fallback para obter top animes"""
    # Retorna uma lista de IDs fictícios
    return list(range(1, n + 1))

def fallback_get_anime_info(top_ids):
    """Função de fallback para obter informações dos animes"""
    # Retorna um DataFrame vazio do Polars
    return pl.DataFrame({
        'Name': [],
        'Score': [],
        'Genres_combination': []
    })

# Tenta importar as funções reais, se não conseguir, usa as de fallback
try:
    from anime import get_top_animes, get_anime_info
except ImportError:
    st.warning("Arquivo anime.py não encontrado. Usando funções de fallback para recomendações.")
    get_top_animes = fallback_get_top_animes
    get_anime_info = fallback_get_anime_info

def obter_recomendacoes_por_filtros(df_clean, generos_selecionados, min_score=6.0, max_results=10):
    """
    Função auxiliar para obter recomendações baseadas em filtros locais
    quando as funções do anime.py não estão disponíveis
    """
    try:
        # Cria o filtro inicial com o primeiro gênero
        filtro_generos = pl.col("Genres").list.contains(generos_selecionados[0])

        # Adiciona os demais gêneros com OR
        for genero in generos_selecionados[1:]:
            filtro_generos = filtro_generos | pl.col("Genres").list.contains(genero)

        # Filtra animes que contenham pelo menos um dos gêneros selecionados
        df_filtrado = df_clean.filter(filtro_generos)

        # Filtra por nota mínima e ordena por score
        df_recomendacoes = df_filtrado.filter(
            pl.col("Score") >= min_score
        ).sort("Score", descending=True).head(max_results)
        
        return df_recomendacoes
    except Exception as e:
        st.error(f"Erro ao buscar recomendações locais: {str(e)}")
        return pl.DataFrame()

def mostrar_recomendacoes(df_clean, df_exploded):
    """Interface principal para recomendações de animes"""
    generos_unicos = sorted(df_exploded["Genres"].unique().to_list())

    # Título e descrição
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='color: #1abc9c; margin-bottom: 10px;'>🎬 Recomendação de Animes</h2>
        <p style='color: #bdc3c7; font-size: 1.1em;'>
            Descubra novos animes baseados nos seus gêneros favoritos
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Configurações da recomendação
    with st.expander("⚙️ Configurações de Recomendação", expanded=False):
        col_config1, col_config2 = st.columns(2)
        with col_config1:
            num_recomendacoes = st.slider("Número de recomendações", 5, 20, 10)
        with col_config2:
            nota_minima = st.slider("Nota mínima", 1.0, 10.0, 6.0, 0.5)

    # Seleção de gêneros
    st.markdown("### 📋 Selecione os gêneros desejados:")
    
    # Opções de seleção rápida
    col_select1, col_select2, col_select3 = st.columns(3)
    with col_select1:
        if st.button("🎯 Selecionar Populares"):
            populares = ["Action", "Adventure", "Comedy", "Drama", "Fantasy", "Romance"]
            for genero in populares:
                if genero in generos_unicos:
                    st.session_state[f"rec_{genero}"] = True
    
    with col_select2:
        if st.button("🧹 Limpar Seleção"):
            for genero in generos_unicos:
                if f"rec_{genero}" in st.session_state:
                    st.session_state[f"rec_{genero}"] = False
    
    with col_select3:
        if st.button("🎲 Seleção Aleatória"):
            import random
            # Seleciona 3-5 gêneros aleatórios
            num_random = random.randint(3, 5)
            random_genres = random.sample(generos_unicos, num_random)
            for genero in generos_unicos:
                st.session_state[f"rec_{genero}"] = genero in random_genres

    # Grid de checkboxes para gêneros
    num_cols = 4
    cols = st.columns(num_cols)
    generos_selecionados = []

    for idx, genero in enumerate(generos_unicos):
        with cols[idx % num_cols]:
            key_name = f"rec_{genero}"
            if st.checkbox(genero, key=key_name):
                generos_selecionados.append(genero)

    # Mostra os gêneros selecionados
    if generos_selecionados:
        mostra_badges(generos_selecionados)

    # Botão de recomendação
    if st.button("🔍 Buscar Recomendações", type="primary", use_container_width=True):
        if generos_selecionados:
            with st.spinner("🔄 Buscando os melhores animes para você..."):
                try:
                    # Tenta usar as funções do anime.py
                    booleans = [g in generos_selecionados for g in generos_unicos]
                    top_ids = get_top_animes(booleans, n=num_recomendacoes)
                    top_info = get_anime_info(top_ids)
                    
                    # Se não conseguir dados do anime.py, usa filtros locais
                    if top_info.is_empty():
                        st.info("Usando recomendações baseadas nos dados locais...")
                        top_info = obter_recomendacoes_por_filtros(
                            df_clean, generos_selecionados,
                            nota_minima, num_recomendacoes
                        )
                    
                    if not top_info.is_empty():
                        # Cabeçalho dos resultados
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #2c3e50, #34495e); 
                                   padding: 20px; 
                                   border-radius: 15px; 
                                   text-align: center; 
                                   margin: 20px 0;'>
                            <h3 style='color: #1abc9c; margin: 0;'>
                                🎬 {len(top_info)} Animes Recomendados
                            </h3>
                            <p style='color: #bdc3c7; margin: 10px 0 0 0;'>
                                Baseado nos gêneros: {', '.join(generos_selecionados)}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Exibe os animes recomendados
                        for idx, row in enumerate(top_info.iter_rows(named=True)):
                            # Calcula a cor do card baseada na nota
                            score = row['Score']
                            if score >= 8.5:
                                border_color = "#f1c40f"  # Ouro
                                score_color = "#f39c12"
                            elif score >= 7.5:
                                border_color = "#1abc9c"  # Verde
                                score_color = "#16a085"
                            elif score >= 6.5:
                                border_color = "#3498db"  # Azul
                                score_color = "#2980b9"
                            else:
                                border_color = "#95a5a6"  # Cinza
                                score_color = "#7f8c8d"
                            
                            # Cor alternada para o fundo
                            bg_color = "#2c3e50" if idx % 2 == 0 else "#34495e"
                            
                            st.markdown(f"""
                            <div style='background: {bg_color}; 
                                       border-radius: 15px; 
                                       margin: 15px 0; 
                                       padding: 25px;
                                       border-left: 5px solid {border_color};
                                       box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                                       transition: all 0.3s ease;'>
                                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;'>
                                    <h4 style='color: #ecf0f1; margin: 0; font-size: 1.3em; flex: 1;'>
                                        <span style='color: #1abc9c; font-weight: normal;'>#{idx + 1}</span> 
                                        {row['Name']}
                                    </h4>
                                    <div style='background: {score_color}; 
                                               color: white; 
                                               padding: 8px 15px; 
                                               border-radius: 25px; 
                                               font-weight: bold;
                                               font-size: 1.1em;
                                               margin-left: 15px;'>
                                        ⭐ {score:.2f}
                                    </div>
                                </div>
                                <div style='color: #bdc3c7; font-size: 0.95em; line-height: 1.4;'>
                                    <i class='fas fa-tags'></i> 
                                    <strong>Gêneros:</strong> {row['Genres_combination']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Estatísticas dos resultados
                        scores = [row['Score'] for row in top_info.iter_rows(named=True)]
                        avg_score = sum(scores) / len(scores)
                        max_score = max(scores)
                        min_score = min(scores)
                        
                        st.markdown(f"""
                        <div style='background: #34495e; 
                                   padding: 20px; 
                                   border-radius: 15px; 
                                   margin: 20px 0;'>
                            <h4 style='color: #1abc9c; margin: 0 0 15px 0;'>📊 Estatísticas das Recomendações</h4>
                            <div style='display: flex; justify-content: space-around; text-align: center;'>
                                <div>
                                    <div style='color: #f39c12; font-size: 1.5em; font-weight: bold;'>{avg_score:.2f}</div>
                                    <div style='color: #bdc3c7; font-size: 0.9em;'>Nota Média</div>
                                </div>
                                <div>
                                    <div style='color: #27ae60; font-size: 1.5em; font-weight: bold;'>{max_score:.2f}</div>
                                    <div style='color: #bdc3c7; font-size: 0.9em;'>Melhor Nota</div>
                                </div>
                                <div>
                                    <div style='color: #e74c3c; font-size: 1.5em; font-weight: bold;'>{min_score:.2f}</div>
                                    <div style='color: #bdc3c7; font-size: 0.9em;'>Menor Nota</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.markdown("""
                        <div style='background: #e74c3c; 
                                   padding: 20px; 
                                   border-radius: 15px; 
                                   text-align: center;'>
                            <h4 style='color: white; margin: 0;'>😔 Nenhum anime encontrado</h4>
                            <p style='color: #ecf0f1; margin: 10px 0 0 0;'>
                                Tente selecionar diferentes gêneros ou diminuir a nota mínima.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"Erro ao buscar recomendações: {str(e)}")
                    st.info("Tente novamente ou verifique se todos os arquivos necessários estão presentes.")
        
        else:
            st.warning("⚠️ Selecione pelo menos um gênero para obter recomendações!")

    # Seção de ajuda
    with st.expander("❓ Como funciona o sistema de recomendação?"):
        st.markdown("""
        ### 🎯 Como funciona:
        
        **1. Seleção de Gêneros:** Escolha os gêneros que mais te interessam
        
        **2. Algoritmo de Recomendação:** O sistema usa diferentes métodos:
        - **Método Principal:** Algoritmo KNN baseado em similaridade
        - **Método Auxiliar:** Filtragem por gêneros e ordenação por nota
        
        **3. Configurações Personalizáveis:**
        - Número de recomendações (5-20)
        - Nota mínima para filtrar qualidade
        
        ### 🏆 Interpretação das Cores:
        - **🟡 Ouro:** Animes excepcionais (8.5+)
        - **🟢 Verde:** Animes muito bons (7.5-8.4)
        - **🔵 Azul:** Animes bons (6.5-7.4)
        - **⚫ Cinza:** Animes medianos (abaixo de 6.5)
        
        ### 💡 Dicas:
        - Experimente diferentes combinações de gêneros
        - Use a seleção aleatória para descobrir novos gostos
        - Ajuste a nota mínima conforme sua preferência
        """)


def mostra_badges(generos_selecionados):
    st.markdown("**🎯 Gêneros selecionados:**")
    # Cria distintivos para os gêneros selecionados
    badges_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0;'>"
    for genero in generos_selecionados:
        badges_html += f"""
                <span style='background: linear-gradient(45deg, #1abc9c, #16a085); 
                           color: white; 
                           padding: 5px 12px; 
                           border-radius: 20px; 
                           display: inline-block;
                           font-size: 0.9em;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>{genero}</span>"""
    badges_html += "</div>"
    st.markdown(f"{badges_html}", unsafe_allow_html=True)