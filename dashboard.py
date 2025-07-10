import streamlit as st
import polars as pl
import plotly.express as px

# --------------- FUNÇÃO DE GRÁFICO EM CARD ----------------
def grafico_card(title, fig):
    with st.container():
        st.markdown(f"<div class='card'><h4 style='margin-bottom:10px'>{title}</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def cria_pagina_dashboard(df_inicial, df_explodidos, generos_usados):
    total_animes = df_inicial.shape[0]
    total_membros = df_inicial.select(pl.col("Members")).sum()[0, 0]
    total_generos = len(generos_usados)
    media_nota = df_inicial.select(pl.col("Score").mean()).item()
    st.subheader("Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-eye" style="color: #1E90FF;"></i></div>
            <div class="kpi-value">{total_animes:,}</div>
            <div class="kpi-label">Total de Animes</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-star" style="color: #FFD700;"></i></div>
            <div class="kpi-value">{media_nota:.1f}</div>
            <div class="kpi-label">Nota Média</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-users" style="color: #6C3BAA;"></i></div>
            <div class="kpi-value">{int(total_membros / 1e6)}M</div>
            <div class="kpi-label">Total de Avaliações</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-chart-line" style="color: #1DBC60;"></i></div>
            <div class="kpi-value">Mais de {total_generos}</div>
            <div class="kpi-label">Gêneros Únicos</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    # --------- Análises
    genero_freq = df_explodidos.group_by("Genres").agg(pl.len().alias("Frequencia")).sort("Frequencia", descending=True)
    genero_score = df_explodidos.group_by("Genres").agg(pl.col("Score").mean().alias("Nota Média")).sort("Nota Média",
                                                                                                         descending=True)
    combo_freq = df_inicial.filter(pl.col("Genres").list.len() > 1).group_by("Genres_combination").agg(
        pl.len().alias("Frequencia")).sort("Frequencia", descending=True)
    studio_avg = df_inicial.filter(pl.col("Studios").is_not_null()).group_by("Studios").agg(
        [pl.col("Score").mean().alias("Nota Média"), pl.len().alias("Qtd")]).filter(pl.col("Qtd") >= 5).sort(
        "Nota Média", descending=True)
    studio_avg_simples = studio_avg.filter(~pl.col("Studios").str.contains(","))
    relacao_pop = df_inicial.select(['Score', 'Members', 'Name']).to_pandas()
    score_dist = df_inicial.with_columns(pl.col('Score').round(0).alias('ScoreArredondado')).group_by(
        'ScoreArredondado').agg(pl.col('Members').sum().alias('TotalMembros')).sort('ScoreArredondado')
    # --------- Gráficos
    colg1, colg2 = st.columns(2)
    with colg1:
        # Gráfico de barras com cores em sequência baseada nos valores
        fig1 = px.bar(genero_freq.to_pandas().head(15), x='Genres', y='Frequencia',
                    color='Frequencia',  # Cor baseada na frequência
                    color_continuous_scale=px.colors.sequential.Viridis_r)
        fig1.update_layout(showlegend=False)  
        grafico_card("Gêneros Mais Frequentes", fig1)

        fig3 = px.bar(studio_avg_simples.head(15).to_pandas().sort_values("Nota Média"), 
                    x='Nota Média', y='Studios',
                    orientation='h', 
                    color='Nota Média',  # Cor baseada na nota média
                    color_continuous_scale=px.colors.sequential.Viridis_r)
        fig3.update_layout(showlegend=False)
        grafico_card("Estúdios com Melhores Notas", fig3)

        fig5 = px.scatter(relacao_pop, x='Score', y='Members', 
                size='Members', 
                color='Score',  # Mantém a cor baseada no Score
                hover_name='Name',
                color_continuous_scale=px.colors.sequential.Turbo)
        fig5.update_traces(marker=dict(line=dict(width=1, color='white')))
        grafico_card("Popularidade vs Nota", fig5)

    with colg2:
            fig2 = px.line(genero_score.head(15).to_pandas(), x='Genres', y='Nota Média', 
                        markers=True,
                        color_discrete_sequence=['#FF6B6B']) 
            fig2.update_traces(mode='lines+markers+text', texttemplate='%{y:.2f}', 
                            textposition='top center',
                            line=dict(width=3),  
                            marker=dict(size=8)) 
            grafico_card("Gêneros com Melhores Notas", fig2)

            # Gráfico de pizza para combinações de gênero
            fig4 = px.pie(combo_freq.head(10).to_pandas(), 
              values='Frequencia',           
              names='Genres_combination', 
              color_discrete_sequence=px.colors.qualitative.Set3)
            fig4.update_traces(textposition='inside', textinfo='percent+label')
            fig4.update_layout(showlegend=True)
            grafico_card("Combinações de Gêneros Mais Comuns", fig4)

            # Scatter plot

            # Gráfico de linha com gradiente de cores
            fig6 = px.line(score_dist.to_pandas(), x='ScoreArredondado', y='TotalMembros', 
                        markers=True,
                        color_discrete_sequence=['#4ECDC4'])
            fig6.update_traces(marker=dict(line=dict(width=1, color='white')))
            grafico_card("Distribuição de Notas", fig6)