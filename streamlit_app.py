import streamlit as st
import pandas as pd
import sqlite3

# -------------------------------
# Função pra conectar no banco
# -------------------------------
def get_connection():
    return sqlite3.connect("relatorios.db")

# -------------------------------
# Título do app
# -------------------------------
st.title("📊 Relatórios de Coleta")

# -------------------------------
# Upload do arquivo
# -------------------------------
uploaded_file = st.file_uploader("Suba o relatório em Excel", type=["xlsx"])

if uploaded_file is not None:
    # Ler o excel
    df = pd.read_excel(uploaded_file)

    # Mostrar preview
    st.write("Pré-visualização do arquivo:")
    st.dataframe(df.head())

    # Salvar no banco do zero
    conn = get_connection()
    cursor = conn.cursor()

    # Deleta tabela se já existir
    cursor.execute("DROP TABLE IF EXISTS relatorios")
    conn.commit()

    # Substitui a tabela completamente
    df.to_sql("relatorios", conn, if_exists="replace", index=False)
    conn.close()

    st.success("Relatório salvo no banco com sucesso ✅ (tabela recriada do zero)")

# -------------------------------
# Carregar dados do banco
# -------------------------------
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
table_exists = cursor.fetchone()

if table_exists:
    df = pd.read_sql("SELECT * FROM relatorios", conn)
else:
    df = pd.DataFrame()  # vazio se não tiver nada
conn.close()

# -------------------------------
# Só mostra interface se tiver dados
# -------------------------------
if not df.empty:
    # -------------------------------
    # Filtros globais
    # -------------------------------
    st.sidebar.header("Filtros")

    # Ajustar Data
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    # Subprefeitura
    if "Subprefeitura" in df.columns:
        subprefeituras = df["Subprefeitura"].dropna().unique()
        f_sub = st.sidebar.multiselect("Subprefeitura", subprefeituras, default=subprefeituras)
    else:
        f_sub = []

    # Período
    if "Data" in df.columns and not df["Data"].isna().all():
        data_min, data_max = df["Data"].min(), df["Data"].max()
        f_data = st.sidebar.date_input("Período", [data_min, data_max])
    else:
        f_data = []

    # Unidade
    if "Unidade" in df.columns:
        unidades = df["Unidade"].dropna().unique()
        f_unidade = st.sidebar.multiselect("Unidade", unidades, default=unidades)
    else:
        f_unidade = []

    # Tipo de Operação
    if "Tipo de Operação" in df.columns:
        tipos = df["Tipo de Operação"].dropna().unique()
        f_tipo = st.sidebar.multiselect("Tipo de Operação", tipos, default=tipos)
    else:
        f_tipo = []

    # Turno
    if "Turno" in df.columns:
        turnos = df["Turno"].dropna().unique()
        f_turno = st.sidebar.multiselect("Turno", turnos, default=turnos)
    else:
        f_turno = []

    # -------------------------------
    # Aplicar filtros
    # -------------------------------
    df_filtered = df.copy()
    if f_sub: df_filtered = df_filtered[df_filtered["Subprefeitura"].isin(f_sub)]
    if f_unidade: df_filtered = df_filtered[df_filtered["Unidade"].isin(f_unidade)]
    if f_tipo: df_filtered = df_filtered[df_filtered["Tipo de Operação"].isin(f_tipo)]
    if f_turno: df_filtered = df_filtered[df_filtered["Turno"].isin(f_turno)]
    if f_data and "Data" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["Data"].between(f_data[0], f_data[1])]

    # -------------------------------
    # Layout com abas
    # -------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Visão Geral", "🚛 Veículos", "🌍 Subprefeituras/Setores", "📏 Quilometragem", "⏱️ Horas"]
    )

    # -------------------------------
    # Abas (placeholders)
    # -------------------------------
    with tab1:
        st.header("📊 Visão Geral")
        st.write("Aqui vão os KPIs e gráficos principais da operação")
        st.dataframe(df_filtered.head())

    with tab2:
        st.header("🚛 Veículos")
        st.write("Gráficos de produtividade, ranking e eficiência de veículos")

    with tab3:
        st.header("🌍 Subprefeituras / Setores")
        st.write("Planejado vs realizado, ranking de setores, mapa (se aplicável)")

    with tab4:
        st.header("📏 Quilometragem")
        st.write("KM percorrido por dia, dentro/fora do setor, totais por unidade")

    with tab5:
        st.header("⏱️ Horas")
        st.write("Média de horas de operação, tempo de fila, variações por setor")

else:
    st.info("Nenhum relatório foi carregado ainda.")
