import streamlit as st
import polars as pl
import plotly.express as px
from anime import predict_score_knn, get_top_animes, get_anime_info

# ---------- CONFIGURAÇÃO DE PÁGINA ----------
st.set_page_config(page_title="MaoMao - Análise de Animes", layout="wide")

# ---------- CSS CUSTOMIZADO ----------
st.markdown("""
<style>
body, .main {
    background: linear-gradient(180deg, #1b1135, #0e0a1c);
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #1b1135;
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

.metric-card {
    background-color: #251944;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    text-align: center;
}

.metric-card:hover {
    transform: scale(1.02);
}

.metric-icon {
    font-size: 2.5rem;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #66ffd9;
}

.metric-label {
    font-size: 1rem;
    color: #999;
}

h1, h2, h3, h4, h5 {
    color: #ffffff;
}

hr {
    border: none;
    border-top: 1px solid #444;
    margin: 2em 0;
}            

section[data-testid="stSidebar"] {
    background-color: #1b1b30;
    color: white;
}

.stButton>button {
    background: linear-gradient(to right, #9933ff, #ff33cc);
    color: white;
    border: none;
    padding: 0.5em 1em;
    font-weight: bold;
    border-radius: 8px;
}

.stButton>button:hover {
    background: linear-gradient(to right, #ff33cc, #9933ff);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------- CABEÇALHO ----------
with st.container():
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("static/MaoMao.png", width=90)
    with col_title:
        st.markdown("<div class='gradient-title'>MaoMao</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#ccc;'>Analytics e Machine Learning para o mundo dos animes</p>", unsafe_allow_html=True)
    st.markdown("---")

# ---------- MENU LATERAL ----------
pagina = st.sidebar.radio("Navegue:", ["Dashboard", "Preditor de Nota"])

# ---------- DADOS ----------
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

# ---------- DASHBOARD ----------
if pagina == "Dashboard":
    # KPIs
    total_animes = df_clean.shape[0]
    total_membros = df_clean.select(pl.col("Members")).sum()[0, 0]
    total_generos = len(generos_unicos)
    estudios_unicos = df_clean.select(pl.col("Studios")).unique().drop_nulls().shape[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🎬</div>
            <div class="metric-value">{total_animes:,}</div>
            <div class="metric-label">Total de Animes</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        media_nota = df_clean.select(pl.col("Score").mean()).item()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">⭐</div>
            <div class="metric-value">{media_nota:.2f}</div>
            <div class="metric-label">Nota Média</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{int(total_membros/1e6)}M</div>
            <div class="metric-label">Membros Ativos</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{total_generos}</div>
            <div class="metric-label">Gêneros Únicos</div>
        </div>""", unsafe_allow_html=True)

    # ---------- ANÁLISES E GRÁFICOS ----------
    genero_freq = df_exploded.group_by("Genres").agg(pl.count().alias("Frequencia")).sort("Frequencia", descending=True)
    genero_score = df_exploded.group_by("Genres").agg(pl.col("Score").mean().alias("Nota Média")).sort("Nota Média", descending=True)
    combo_freq = df_clean.filter(pl.col("Genres").list.len() > 1).group_by("Genres_combination").agg(pl.count().alias("Frequencia")).sort("Frequencia", descending=True)
    studio_avg = df_clean.filter(pl.col("Studios").is_not_null()).group_by("Studios").agg([pl.col("Score").mean().alias("Nota Média"), pl.count().alias("Qtd")]).filter(pl.col("Qtd") >= 5).sort("Nota Média", descending=True)
    studio_avg_simples = studio_avg.filter(~pl.col("Studios").str.contains(","))
    relacao_pop = df_clean.select(['Score', 'Members', 'Name']).to_pandas()
    score_dist = df_clean.with_columns(pl.col('Score').round(0).alias('ScoreArredondado')).group_by('ScoreArredondado').agg(pl.col('Members').sum().alias('TotalMembros')).sort('ScoreArredondado')

    st.markdown("### 🔎 Análises Visuais")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("🎭 Gêneros Mais Frequentes")
        fig1 = px.bar(genero_freq.to_pandas().head(15), x='Genres', y='Frequencia', color_discrete_sequence=px.colors.sequential.Rainbow)
        st.plotly_chart(fig1, use_container_width=True)
    with col_g2:
        st.subheader("📈 Gêneros com Melhores Notas")
        fig2 = px.line(genero_score.head(15).to_pandas(), x='Genres', y='Nota Média', markers=True,  color_discrete_sequence=px.colors.sequential.Turbo )
        fig2.update_traces(mode='lines+markers+text', texttemplate='%{y:.2f}', textposition='top center')
        st.plotly_chart(fig2, use_container_width=True)

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.subheader("🏆 Estúdios com Melhores Notas")
        fig3 = px.bar(studio_avg_simples.head(15).to_pandas().sort_values("Nota Média"), x='Nota Média', y='Studios', orientation='h')
        st.plotly_chart(fig3, use_container_width=True)
    with col_g4:
        st.subheader("🔗 Combinações de Gêneros Mais Comuns")
        fig4 = px.bar(combo_freq.head(15).to_pandas(), x='Genres_combination', y='Frequencia', color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("📊 Popularidade vs Nota")
    fig5 = px.scatter(relacao_pop, x='Score', y='Members', size='Members', color='Score', hover_name='Name', color_continuous_scale='Viridis')
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("📉 Distribuição de Notas")
    fig6 = px.line(score_dist.to_pandas(), x='ScoreArredondado', y='TotalMembros', markers=True)
    st.plotly_chart(fig6, use_container_width=True)

# ---------- PREDITORA ----------
else:
    st.markdown("### 🔮 Predição de Nota com KNN")
    membros = st.number_input("Número de Membros", min_value=1, step=1000)
    st.markdown("Selecione os gêneros:")
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
            st.markdown(f"<div style='background-color:#1abc1a; padding:20px; border-radius:10px; text-align:center;'><h2 style='color:white;'>Nota Estimada: {pred:.2f}</h2></div>", unsafe_allow_html=True)
            top_ids = get_top_animes(booleans, n=10)
            top_info = get_anime_info(top_ids)
            if top_info.is_empty():
                st.info("Nenhum anime encontrado.")
            else:
                st.markdown("### 📺 Animes Recomendados")
                for row in top_info.iter_rows(named=True):
                    st.markdown(f"""
                    <div style='background:#222; border-radius:10px; margin:12px 0; padding:16px;'>
                        <h4 style='color:#1abc1a'>{row['Name']}</h4>
                        <span style='color:#fff;'>Nota: <b>{row['Score']:.2f}</b></span><br>
                        <span style='color:#ccc;'>Gêneros: {row['Genres_combination']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("Preencha os campos antes de predizer.")