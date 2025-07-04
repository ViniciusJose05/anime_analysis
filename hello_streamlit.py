import streamlit as st
import polars as pl
import plotly.express as px
from anime import predict_score_knn, get_top_animes, get_anime_info

# --------------- CONFIG DA PÁGINA ----------------
st.set_page_config(page_title="MaoMao - Análise de Animes", layout="wide")

# --------------- CSS CUSTOMIZADO ----------------
st.markdown("""
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

<style>
body, .main {
    background: linear-gradient(180deg, #0e0a1c, #1b1135);
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #1b1135;
    color: white;
}

.gradient-title {
    font-size: 2.8rem;
    font-weight: bold;
    background: linear-gradient(to right, #00ff99, #9966ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2em;
}

.card {
    background-color: #241b3a;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    margin-bottom: 1rem;
}

.kpi-icon {
    font-size: 1.8rem;
    margin-bottom: 8px;
    color: #66ffd9;
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: bold;
}

.kpi-label {
    font-size: 1rem;
    color: #ccc;
}

hr {
    border: none;
    border-top: 1px solid #444;
    margin: 2em 0;
}
</style>
""", unsafe_allow_html=True)

# --------------- LOGO E TÍTULO ----------------
with st.container():
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 20px; margin-bottom: 10px;'>
        <img src="static/MaoMao.png" width="80" style="border-radius: 10px;" />
        <div>
            <h1 style="margin-bottom: 0; font-size: 5 em; background: linear-gradient(to right, #00ff99, #9966ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">MaoMao</h1>
            <p style='margin-top: 4px; color: #ccc;'>Analytics e Machine Learning para o mundo dos animes</p>
        </div>
    </div>
    <hr style='border-top: 1px solid #444;' />
    """, unsafe_allow_html=True)

# --------------- MENU LATERAL ----------------
pagina = st.sidebar.radio("Navegue:", ["Dashboard", "Predição de Nota"])

# --------------- CARREGAMENTO DE DADOS ----------------
@st.cache_data
def carregar_dados():
    df = pl.read_csv("databases/anime.csv", null_values="Unknown")
    df = df.filter(pl.col('Score').is_not_null() & pl.col('Genres').is_not_null())
    df = df.with_columns([
        pl.col('Genres').str.split(', ').alias('Genres')
    ])
    df = df.with_columns([
        pl.col('Genres').list.eval(
            pl.when(pl.element() == pl.lit("Hentai")).then(pl.lit("Adult Content")).otherwise(pl.element())
        ).alias("Genres")
    ])
    df = df.with_columns(
        pl.col("Genres").map_elements(lambda genres: ", ".join(sorted(genres))).alias("Genres_combination")
    )
    return df

df_clean = carregar_dados()
df_exploded = df_clean.explode("Genres")
generos_unicos = sorted(df_exploded["Genres"].unique().to_list())

# --------------- FUNÇÃO DE GRÁFICO EM CARD ----------------
def grafico_card(title, fig):
    with st.container():
        st.markdown(f"<div class='card'><h4 style='margin-bottom:10px'>{title}</h4>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --------------- DASHBOARD ----------------
if pagina == "Dashboard":
    total_animes = df_clean.shape[0]
    total_membros = df_clean.select(pl.col("Members")).sum()[0, 0]
    total_generos = len(generos_unicos)
    media_nota = df_clean.select(pl.col("Score").mean()).item()

    st.subheader("Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-eye"></i></div>
            <div class="kpi-value">{total_animes:,}</div>
            <div class="kpi-label">Total de Animes</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-star"></i></div>
            <div class="kpi-value">{media_nota:.1f}</div>
            <div class="kpi-label">Nota Média</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-users"></i></div>
            <div class="kpi-value">{int(total_membros / 1e6)}M</div>
            <div class="kpi-label">Membros Ativos</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-icon"><i class="fas fa-chart-line"></i></div>
            <div class="kpi-value">Mais de {total_generos}</div>
            <div class="kpi-label">Gêneros Únicos</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # --------- Análises
    genero_freq = df_exploded.group_by("Genres").agg(pl.count().alias("Frequencia")).sort("Frequencia", descending=True)
    genero_score = df_exploded.group_by("Genres").agg(pl.col("Score").mean().alias("Nota Média")).sort("Nota Média", descending=True)
    combo_freq = df_clean.filter(pl.col("Genres").list.len() > 1).group_by("Genres_combination").agg(pl.count().alias("Frequencia")).sort("Frequencia", descending=True)
    studio_avg = df_clean.filter(pl.col("Studios").is_not_null()).group_by("Studios").agg([pl.col("Score").mean().alias("Nota Média"), pl.count().alias("Qtd")]).filter(pl.col("Qtd") >= 5).sort("Nota Média", descending=True)
    studio_avg_simples = studio_avg.filter(~pl.col("Studios").str.contains(","))

    relacao_pop = df_clean.select(['Score', 'Members', 'Name']).to_pandas()
    score_dist = df_clean.with_columns(pl.col('Score').round(0).alias('ScoreArredondado')).group_by('ScoreArredondado').agg(pl.col('Members').sum().alias('TotalMembros')).sort('ScoreArredondado')

    # --------- Gráficos
    colg1, colg2 = st.columns(2)
    with colg1:
        fig1 = px.bar(genero_freq.to_pandas().head(15), x='Genres', y='Frequencia', color_discrete_sequence=px.colors.sequential.Viridis_r)
        grafico_card("Gêneros Mais Frequentes", fig1)

        fig3 = px.bar(studio_avg_simples.head(15).to_pandas().sort_values("Nota Média"), x='Nota Média', y='Studios', orientation='h', color_discrete_sequence=px.colors.sequential.Viridis_r)
        grafico_card("Estúdios com Melhores Notas", fig3)

    with colg2:
        fig2 = px.line(genero_score.head(15).to_pandas(), x='Genres', y='Nota Média', markers=True, color_discrete_sequence=px.colors.sequential.Viridis_r)
        fig2.update_traces(mode='lines+markers+text', texttemplate='%{y:.2f}', textposition='top center')
        grafico_card("Gêneros com Melhores Notas", fig2)

        fig4 = px.bar(combo_freq.head(15).to_pandas(), x='Genres_combination', y='Frequencia', color_discrete_sequence=px.colors.sequential.Viridis_r)
        grafico_card("Combinações de Gêneros Mais Comuns", fig4)

    fig5 = px.scatter(relacao_pop, x='Score', y='Members', size='Members', color='Score', hover_name='Name', color_continuous_scale=px.colors.sequential.Viridis_r)
    grafico_card("Popularidade vs Nota", fig5)

    fig6 = px.line(score_dist.to_pandas(), x='ScoreArredondado', y='TotalMembros', markers=True, color_discrete_sequence=px.colors.sequential.Viridis_r)
    grafico_card("Distribuição de Notas", fig6)

# --------------- PREDIÇÃO DE NOTA ----------------
else:
    st.subheader("Predição de Nota")
    membros = st.number_input("Informe o número de membros:", min_value=1, step=1000)
    st.markdown("Selecione os gêneros desejados:")
    cols = st.columns(4)
    generos_selecionados = []
    for idx, genero in enumerate(generos_unicos):
        with cols[idx % 4]:
            if st.checkbox(genero, key=genero):
                generos_selecionados.append(genero)

    if st.button("Prever Nota"):
        if membros > 0 and generos_selecionados:
            booleans = [g in generos_selecionados for g in generos_unicos]
            pred = predict_score_knn(membros, booleans)
            st.markdown(f"""
            <div style='background-color:#1abc1a; padding:20px; border-radius:10px; text-align:center;'>
                <h2 style='color:white;'>Nota Estimada: {pred:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)

            top_ids = get_top_animes(booleans, n=10)
            top_info = get_anime_info(top_ids)
            if top_info.is_empty():
                st.info("Nenhum anime encontrado.")
            else:
                st.markdown("### \ud83c\udfae Recomendados:")
                for row in top_info.iter_rows(named=True):
                    st.markdown(f"""
                    <div style='background:#222; border-radius: 10px; margin:12px 0; padding:16px;'>
                        <h4 style='color:#1abc1a'>{row['Name']}</h4>
                        <span style='color:#fff;'>Nota: <b>{row['Score']:.2f}</b></span><br>
                        <span style='color:#ccc;'>Gêneros: {row['Genres_combination']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("Preencha todos os campos antes de predizer.")
