import streamlit as st
import polars as pl
import plotly.express as px

# ---------- Pré-processamento ----------
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

# ---------- Análises ----------
df_exploded = df_clean.explode("Genres")

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

# ---------- Cabeçalho ----------
with st.container():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("static/MaoMao.png", width=100)
    with col2:
        st.markdown("## MaoMao")
        st.markdown("Dashboard de Análise de Animes")
    st.markdown("---")

# ---------- Seção 1: Gêneros ----------
st.markdown("### 🎭 Gêneros")

col1, col2 = st.columns(2)
with col1:
    fig1 = px.bar(genero_freq.to_pandas().head(15), x='Genres', y='Frequencia',
                  color_discrete_sequence=px.colors.qualitative.Alphabet)
    st.subheader("Mais Frequentes")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig8 = px.pie(genero_freq.to_pandas().head(10), values='Frequencia', names='Genres')
    st.subheader("Distribuição (Top 10)")
    st.plotly_chart(fig8, use_container_width=True)

# ---------- Seção 2: Avaliações por Gênero ----------
st.markdown("### 🎯 Avaliações por Gênero")

col3, col4 = st.columns(2)
with col3:
    fig2 = px.line(genero_score.head(15).to_pandas(), x='Genres', y='Nota Média',
                   markers=True, color_discrete_sequence=px.colors.qualitative.Bold)
    fig2.update_traces(mode='lines+markers+text', textposition='top center', texttemplate='%{y:.2f}')
    st.subheader("Top 15 Melhores Notas")
    st.plotly_chart(fig2, use_container_width=True)

with col4:
    fig3 = px.line(genero_score.tail(15).to_pandas(), x='Genres', y='Nota Média',
                   markers=True, color_discrete_sequence=px.colors.qualitative.Vivid)
    fig3.update_traces(mode='lines+markers+text', textposition='top center', texttemplate='%{y:.2f}')
    st.subheader("15 Piores Notas")
    st.plotly_chart(fig3, use_container_width=True)

# ---------- Seção 3: Combinações de Gêneros ----------
st.markdown("### 🔗 Combinações de Gêneros")

fig4 = px.bar(combo_freq.head(15).to_pandas(), x='Genres_combination', y='Frequencia',
              color_discrete_sequence=px.colors.qualitative.Pastel)
st.plotly_chart(fig4, use_container_width=True)

# ---------- Seção 4: Estúdios ----------
st.markdown("### 🏆 Estúdios com Melhores Notas Médias")

fig5 = px.bar(
    studio_avg_simples.head(15).to_pandas().sort_values("Nota Média"),
    x='Nota Média', y='Studios', orientation='h', text='Nota Média'
)
fig5.update_traces(texttemplate='%{text:.2f}', textposition='outside')
st.plotly_chart(fig5, use_container_width=True)

# ---------- Seção 5: Popularidade e Score ----------
st.markdown("### 📊 Popularidade vs Avaliação")

col5, col6 = st.columns([2, 1])
with col5:
    fig6 = px.scatter(
        relacao_popularidade_nome,
        x='Score', y='Members',
        size='Members', color='Score',
        hover_name='Name',
        color_continuous_scale='Rainbow'
    )
    st.subheader("Bolhas: Score x Popularidade")
    st.plotly_chart(fig6, use_container_width=True)

with col6:
    fig7 = px.line(score_dist.to_pandas(), x='ScoreArredondado', y='TotalMembros',
                   markers=True, color_discrete_sequence=px.colors.qualitative.Antique)
    fig7.update_traces(mode='lines+markers+text', textposition='top center', texttemplate='%{y}')
    st.subheader("Distribuição de Notas")
    st.plotly_chart(fig7, use_container_width=True)