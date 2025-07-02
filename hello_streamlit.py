import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from anime import predict_score_knn, df_exploded

# ---------- Configuração da página ----------
st.set_page_config(page_title="MaoMao - Análise de Animes", layout="wide")

# ---------- Cabeçalho ----------
with st.container():
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("static/MaoMao.png", width=100)
    with col_title:
        st.markdown("## MaoMao")
        st.markdown("Dashboard de Análise de Animes")
    st.markdown("---")

# ---------- Seleção de Página ----------
pagina = st.sidebar.radio("Escolha a página:", ["Dashboard", "Overview de Genêros"])

@st.cache_data
def carregar_dados():
    df = pl.read_csv("databases/anime.csv", null_values="Unknown")
    df = df.filter(pl.col('Score').is_not_null() & pl.col('Genres').is_not_null())
    df = df.with_columns([
        pl.col('Genres').str.split(', ').alias('Genres')
    ])
    df = df.with_columns([
        pl.col('Genres').list.eval(
            pl.when(pl.element() == pl.lit("Hentai")).then(pl.lit("+18")).otherwise(pl.element())
        ).alias("Genres")
    ])
    df = df.with_columns(
        pl.col("Genres").map_elements(lambda genres: ", ".join(sorted(genres))).alias("Genres_combination")
    )
    return df

df_clean = carregar_dados()
df_exploded = df_clean.explode("Genres")

generos_unicos = sorted(df_exploded["Genres"].unique().to_list())

if pagina == "Dashboard":
    # ---------- KPIs em estilo de cards ----------
    total_animes = df_clean.shape[0]
    total_membros = df_clean.select(pl.col("Members")).sum()[0, 0]
    total_generos = len(generos_unicos)
    estudios_unicos = df_clean.select(pl.col("Studios")).unique().drop_nulls().shape[0]

    st.markdown("### 📊 Visão Geral da Base")
    card1, card2 = st.columns(2)

    with card1:
        st.markdown(f"""
        <div style='background-color:#202020;padding:20px;border-radius:10px;'>
            <h3 style='color:white;'>Total de Animes</h3>
            <h1 style='color:#4CAF50'>{total_animes:,}</h1>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color:#202020;padding:20px;border-radius:10px;margin-top:15px;'>
            <h3 style='color:white;'>Total de Membros</h3>
            <h1 style='color:#03A9F4'>{total_membros:,}</h1>
        </div>""", unsafe_allow_html=True)

    with card2:
        st.markdown(f"""
        <div style='background-color:#202020;padding:20px;border-radius:10px;'>
            <h3 style='color:white;'>Gênros Distintos</h3>
            <h1 style='color:#FF9800'>{total_generos}</h1>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color:#202020;padding:20px;border-radius:10px;margin-top:15px;'>
            <h3 style='color:white;'>Estúdios Distintos</h3>
            <h1 style='color:#E91E63'>{estudios_unicos}</h1>
        </div>""", unsafe_allow_html=True)

    # ---------- Análises ----------
    genero_freq = (
        df_exploded.group_by("Genres")
        .agg(pl.count().alias("Frequencia"))
        .sort("Frequencia", descending=True)
    )

    genero_score = (
        df_exploded.group_by("Genres")
        .agg(pl.col("Score").mean().alias("Nota Média"))
        .sort("Nota Média", descending=True)
    )

    combo_freq = (
        df_clean.filter(pl.col("Genres").list.len() > 1)
        .group_by("Genres_combination")
        .agg(pl.count().alias("Frequencia"))
        .sort("Frequencia", descending=True)
    )

    studio_avg = (
        df_clean.filter(pl.col("Studios").is_not_null())
        .group_by("Studios")
        .agg([
            pl.col("Score").mean().alias("Nota Média"),
            pl.count().alias("Qtd")
        ])
        .filter(pl.col("Qtd") >= 5)
        .sort("Nota Média", descending=True)
    )

    studio_avg_simples = studio_avg.filter(~pl.col("Studios").str.contains(","))

    relacao_popularidade_nome = df_clean.select(['Score', 'Members', 'Name']).to_pandas()

    df_scores_distrib = df_clean.with_columns(pl.col('Score').round(0).alias('ScoreArredondado'))
    score_dist = (
        df_scores_distrib
        .group_by('ScoreArredondado')
        .agg(pl.col('Members').sum().alias('TotalMembros'))
        .sort('ScoreArredondado')
    )

    # ---------- Layout Estilo Três Colunas ----------
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.subheader("🌽 Gênros Mais Frequentes")
        fig1 = px.bar(genero_freq.to_pandas().head(15), x='Genres', y='Frequencia',
                      color_discrete_sequence=px.colors.qualitative.Alphabet)
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("🍕 Distribuição de Gênros")
        fig8 = px.pie(genero_freq.to_pandas().head(10), values='Frequencia', names='Genres')
        st.plotly_chart(fig8, use_container_width=True)

    with col2:
        st.subheader("📊 Popularidade vs Nota")
        fig6 = px.scatter(
            relacao_popularidade_nome,
            x='Score', y='Members',
            size='Members', color='Score',
            hover_name='Name',
            color_continuous_scale='Rainbow'
        )
        st.plotly_chart(fig6, use_container_width=True)

        st.subheader("📈 Distribuição de Notas")
        fig7 = px.line(score_dist.to_pandas(), x='ScoreArredondado', y='TotalMembros',
                       markers=True, color_discrete_sequence=px.colors.qualitative.Antique)
        fig7.update_traces(mode='lines+markers+text', textposition='top center', texttemplate='%{y}')
        st.plotly_chart(fig7, use_container_width=True)

    with col3:
        st.subheader("🏆 Estúdios com Melhores Notas")
        fig5 = px.bar(
            studio_avg_simples.head(15).to_pandas().sort_values("Nota Média"),
            x='Nota Média', y='Studios', orientation='h', text='Nota Média'
        )
        fig5.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        st.plotly_chart(fig5, use_container_width=True)

        st.subheader("🔗 Combinações de Gênros")
        fig4 = px.bar(combo_freq.head(15).to_pandas(), x='Genres_combination', y='Frequencia',
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig4, use_container_width=True)
else:  # Preditor de Notas
    st.markdown("### 🔮 Overview de Genêros")
    st.markdown("Selecione os gêneros que você quer analisar:")

    # Lista de gêneros únicos
    generos_unicos = sorted(df_exploded['Genres'].unique().to_list())

    # Criando colunas para os checkboxes de gêneros
    st.markdown("### Selecione os Gêneros:")
    cols = st.columns(4)
    generos_selecionados = []

    for idx, genero in enumerate(generos_unicos):
        with cols[idx % 4]:
            if st.checkbox(genero, key=genero):
                generos_selecionados.append(genero)

    if st.button("Predizer Nota"):
        if generos_selecionados:
            # Criar lista booleana para todos os gêneros
            booleans = [g in generos_selecionados for g in generos_unicos]
            predicao = predict_score_knn(booleans)

            # Exibir resultado em destaque
            st.markdown("---")
            st.markdown(f"""
            <div style='background-color: #1abc1a; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: white;'>Nota Predita: {predicao:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Por favor, selecione pelo menos um gênero.")
