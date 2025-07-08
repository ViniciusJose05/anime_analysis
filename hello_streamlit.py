import streamlit as st
from preditor import interface_predicao_nota
from recomendacoes import mostrar_recomendacoes
from dashboard import cria_pagina_dashboard
from anime import carregar_dados_anime
import os

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
logo_path = os.path.join("static", "MaoMao.png")
if os.path.exists(logo_path):
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image(logo_path, width=80)
    with col_title:
        st.markdown("""
            <h1 style="margin-bottom: 0; font-size: 2.5em; background: linear-gradient(to right, #00ff99, #9966ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">MaoMao</h1>
            <p style='margin-top: 4px; color: #ccc;'>Analytics e Machine Learning para o mundo dos animes</p>
        """, unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 1px solid #444;' />", unsafe_allow_html=True)

# --------------- MENU LATERAL ----------------
pagina = st.sidebar.radio("Navegue:", ["Dashboard", "Predição de Nota", "Recomendações"])

# --------------- CARREGAMENTO DE DADOS ----------------
@st.cache_data
def carregar_dados():
    return carregar_dados_anime()

df_clean = carregar_dados()
df_exploded = df_clean.explode("Genres")
generos_unicos = sorted(df_exploded["Genres"].unique().to_list())


# --------------- DASHBOARD ----------------
if pagina == "Dashboard":
    cria_pagina_dashboard(df_clean, df_exploded, generos_unicos)

# --------------- PREDIÇÃO DE NOTA ----------------
elif pagina == "Predição de Nota":
    # Aqui estava o erro - agora chama a função corretamente
    interface_predicao_nota(generos_unicos)

# --------------- RECOMENDAÇÃO DE ANIMES ----------------
elif pagina == "Recomendações":
    mostrar_recomendacoes(df_clean, df_exploded)