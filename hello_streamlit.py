import streamlit as st
from anime import df_exploded, predict_score_knn

# Página inicial
st.set_page_config(page_title="DB Animes", layout="centered")
st.title("DB Animes")

# Navegação
menu = st.sidebar.selectbox("Menu", ["Início", "Dashboard", "Preditor de Nota"])

generos_lista = df_exploded['Genres'].unique().to_list()

if menu == "Início":
    st.markdown("# Bem-vindo ao DB Animes!")
    st.write("Navegue pelo menu lateral para acessar as funcionalidades.")

elif menu == "Dashboard":
    st.markdown("# Dashboard")
    st.info("Funcionalidade em desenvolvimento.")

elif menu == "Preditor de Nota":
    st.markdown("# Preditor de Nota por Gêneros e Membros")
    with st.form("form_predicao"):
        selecionados = st.multiselect("Selecione os gêneros:", generos_lista)
        membros = st.number_input("Informe o número de membros:", min_value=0, step=1)
        submit = st.form_submit_button("Prever Nota")
    if submit:
        booleans = [g in selecionados for g in generos_lista]
        predicao = predict_score_knn(membros, booleans)
        st.success(f"Gêneros selecionados: {', '.join(selecionados)}")
        st.info(f"Número de membros: {membros}")
        st.markdown(f"## Predição de nota: **{predicao}**")
